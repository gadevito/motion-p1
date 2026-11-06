"""
Paper 4, Part B — shared pipeline for E9, E10 and E11.
=======================================================
Derived from `models/gomo_sparse.py` (main `abbe5a6`, SHA-256 c82ca3fa74f805ab). Changes, all fixed by
`protocol/paper4/PROTOCOLLO.md` §2.3 and `protocol/paper4/E11.md`:

  * admissible origins only (15-min cadence over window and targets), split 70/10/20 in time order,
    with a purge so that no target of one period overlaps an input of the next (RC 1);
  * three disjoint node sets made of whole grid cells: observed, validation-hidden, test-hidden, assigned
    by deficit on 40/20/40. Hidden nodes never enter input, loss, normalisation, historical average or
    class weights (D1). E11 sub-networks use the smallest grid G >= 6 with >= 20 occupied cells;
  * per-batch masks drawn among observed cells only, share u ~ U(0.6, 0.95) in whole cells;
  * fixed number of updates, no early stopping, 11 checkpoints, selection on validation-hidden nodes;
  * static feature max_speed only (lanes and capacity dropped);
  * one random stream per purpose, default_rng([seed, k]);
  * randomised graphs change the topology only: they receive G1's weight multiset, permuted.

Test metrics are refused unless the pre-registration carries a filled signature line (`require_signed`).
"""
import hashlib
import json
import os
import pickle
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]                    # worktree root
DATA = Path(os.environ.get("P4_DATA", ROOT.parent / "OR3" / "data_collection"))
T4C = DATA / "traffic4cast"
CITY = {
    "madrid": {"targets": T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
               "sensors": T4C / "MADRID_2022/gomo_fmt/t4cmad_sensors.csv",
               "roads": T4C / "MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl"},
    "melbourne": {"targets": T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                  "sensors": T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_sensors.csv",
                  "roads": T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl"},
}
T_IN = 12
HORIZONS = (1, 2, 4, 8)
STEP = np.timedelta64(15, "m")
GRID = 6
ALIGN_M = 20.0

# random streams: default_rng([seed, k])
K_SETS, K_MASKS, K_ORDER, K_TOPOLOGY, K_WEIGHTS, K_INIT = 1, 2, 3, 4, 5, 6


def rng(seed, k):
    return np.random.default_rng([int(seed), int(k)])


def sha256(path, n=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n] if n else h.hexdigest()


def fingerprint(obj):
    """16-hex fingerprint of a JSON-serialisable object or of a numpy array."""
    if isinstance(obj, np.ndarray):
        b = np.ascontiguousarray(obj).tobytes() + str(obj.dtype).encode() + str(obj.shape).encode()
    else:
        b = json.dumps(obj, sort_keys=True, default=str).encode()
    return hashlib.sha256(b).hexdigest()[:16]


def git_commit():
    try:
        c = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        dirty = bool(subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain", "--",
                                              "paper4/code"], text=True).strip())
        return c, dirty
    except Exception:  # noqa: BLE001
        return "unknown", True


# ---------------------------------------------------------------- data -------------------------------

_TARGETS = {}


def load_targets(city):
    if city not in _TARGETS:
        z = np.load(CITY[city]["targets"], allow_pickle=True)
        _TARGETS[city] = {k: z[k] for k in ("timestamps", "sensor_ids", "r_emp", "flow", "occupancy",
                                             "congestion_emp")}
    return _TARGETS[city]


def align_graph(city, graph_path):
    """The deliverable's alignment (`gomo_sparse.py:75-90`): every graph node is relabelled to the nearest
    sensor within 20 m; coincident sensors merge. Returns the simple graph on the kept nodes, the kept ids
    (in target order), their target indices and the number of self-loops removed."""
    z = load_targets(city)
    sids = z["sensor_ids"].astype(str)
    with open(graph_path, "rb") as f:
        rg = pickle.load(f)
    sens = pd.read_csv(CITY[city]["sensors"], dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    tree = cKDTree(sens[["utm_x", "utm_y"]].to_numpy())
    nodes = list(rg.nodes)
    nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodes])
    dist, idx = tree.query(nxy, k=1)
    ids = sens["id"].to_numpy()
    rg = nx.relabel_nodes(rg, {nodes[i]: ids[idx[i]] for i in range(len(nodes)) if dist[i] <= ALIGN_M},
                          copy=True)
    kept = [s for s in sids if s in rg.nodes]
    pos = {s: i for i, s in enumerate(sids)}
    kidx = np.array([pos[s] for s in kept])
    wattr = "distance" if any("distance" in a for *_, a in list(rg.edges(data=True))[:50]) else "weight"
    g = nx.Graph()
    g.add_nodes_from(kept)
    loops = 0
    for u, v, a in rg.subgraph(kept).edges(data=True):
        if u == v:
            loops += 1
            continue
        g.add_edge(u, v, weight=float(a[wattr]))
    smeta = sens.drop_duplicates("id").set_index("id")
    coords = smeta.loc[kept, ["utm_x", "utm_y"]].to_numpy("float64")
    maxspd = pd.to_numeric(smeta.loc[kept, "max_speed"], errors="coerce").to_numpy("float64")
    return {"graph": g, "kept": kept, "kidx": kidx, "loops_removed": loops, "weight_attr": wattr,
            "coords": coords, "max_speed": maxspd}


def admissible_origins(ts):
    """Origin t is admissible iff every step from t-11 to t+8 is exactly 15 min (Paper 1 §3)."""
    ok = (np.diff(ts.astype("datetime64[m]")) == STEP).astype(np.int64)      # ok[i]: step i -> i+1
    c = np.concatenate([[0], np.cumsum(ok)])
    t = np.arange(T_IN - 1, len(ts) - max(HORIZONS))
    lo, hi = t - (T_IN - 1), t + max(HORIZONS)                               # steps lo..hi-1
    return t[(c[hi] - c[lo]) == (hi - lo)]


def split_origins(orig):
    """70/10/20 in time order, then purge: the last target of a period precedes the first input of the
    next one. Returns (train, val, test, purged)."""
    n = len(orig)
    tr, va, te = orig[:int(n * .7)], orig[int(n * .7):int(n * .8)], orig[int(n * .8):]
    gap = max(HORIZONS) + T_IN - 1
    tr2 = tr[tr + gap < va[0]]
    va2 = va[va + gap < te[0]]
    return tr2, va2, te, {"train": int(len(tr) - len(tr2)), "val": int(len(va) - len(va2))}


def grid_cells(coords, G=GRID):
    """`gomo_sparse.py:100-104`: a G x G grid on the extent of the nodes' UTM coordinates."""
    xs, ys = coords[:, 0], coords[:, 1]
    gx = np.clip(((xs - xs.min()) / (np.ptp(xs) + 1e-9) * G).astype(int), 0, G - 1)
    gy = np.clip(((ys - ys.min()) / (np.ptp(ys) + 1e-9) * G).astype(int), 0, G - 1)
    return gx * G + gy


def adaptive_grid(coords, g0=GRID, min_occupied=20):
    """E11: the smallest G >= g0 with at least `min_occupied` occupied cells (review, 2026-11-06)."""
    G = g0
    while len(np.unique(grid_cells(coords, G))) < min_occupied:
        G += 1
    return G


def node_sets(cells, seed, targets=(0.4, 0.2, 0.4)):
    """Whole cells in the order of stream K_SETS; each cell goes to the set with the largest deficit
    (target share x K minus nodes already assigned). Label per node: 0 observed, 1 validation-hidden,
    2 test-hidden."""
    K = len(cells)
    order = rng(seed, K_SETS).permutation(np.unique(cells))
    lab = np.zeros(K, dtype=np.int8)
    cur = np.zeros(3)
    for c in order:
        sel = cells == c
        j = int(np.argmax(np.asarray(targets) * K - cur))
        lab[sel] = j
        cur[j] += sel.sum()
    return lab


def geometry_record(coords, cells, G, lab):
    """Covariates registered for every (configuration, seed): grid, occupancy, cell side and the distance of
    each test-hidden node from the nearest observed node."""
    n_per = np.bincount(np.unique(cells, return_inverse=True)[1])
    sx, sy = np.ptp(coords[:, 0]) / G, np.ptp(coords[:, 1]) / G
    obs, test = coords[lab == 0], coords[lab == 2]
    d = cKDTree(obs).query(test, k=1)[0] if len(obs) and len(test) else np.array([np.nan])
    q1, med, q3 = np.percentile(d, [25, 50, 75])
    return {"G": int(G), "occupied_cells": int(len(n_per)), "nodes_per_cell_min": int(n_per.min()),
            "nodes_per_cell_median": float(np.median(n_per)), "nodes_per_cell_max": int(n_per.max()),
            "cell_side_x_m": float(sx), "cell_side_y_m": float(sy), "cell_side_m": float(np.sqrt(sx * sy)),
            "test_to_nearest_observed_m": {"median": float(med), "q1": float(q1), "q3": float(q3)},
            "counts": {k: int((lab == i).sum()) for i, k in enumerate(("observed", "validation_hidden",
                                                                        "test_hidden"))}}


# ---------------------------------------------------------------- graphs -----------------------------

def kernel_adjacency(g, kept):
    """`gomo_sparse.py:146-152`: Gaussian kernel on edge length with sigma = std of the graph's own edge
    lengths, diagonal zero, plus identity, symmetric normalisation."""
    A = nx.to_numpy_array(g, nodelist=kept, weight="weight").astype("float32")
    A[A > 0] = np.maximum(A[A > 0], 1.0)
    m = A > 0
    sg = float(np.sort(A[m]).std())        # on the sorted multiset: sigma depends on the weights only
    Aff = np.where(m, np.exp(-(A / sg) ** 2), 0.0).astype("float32")
    np.fill_diagonal(Aff, 0.0)
    Aff = Aff + np.eye(len(kept), dtype="float32")
    d = 1 / np.sqrt(np.maximum(Aff.sum(1), 1e-6))
    return (Aff * d[:, None]) * d[None, :], sg


def _permute_weights(h, g1, seed):
    w = np.array(sorted(a["weight"] for *_, a in g1.edges(data=True)))
    edges = sorted(tuple(sorted(e)) for e in h.edges())
    perm = rng(seed, K_WEIGHTS).permutation(w)
    for (u, v), x in zip(edges, perm):
        h[u][v]["weight"] = float(x)
    return h


def randomise_degree(g1, seed):
    """Degree- and connectivity-preserving edge swaps (10·|E| requested), then G1's weights permuted."""
    h = nx.Graph()
    h.add_nodes_from(g1.nodes)
    h.add_edges_from(g1.edges())
    want = 10 * h.number_of_edges()
    s = int(rng(seed, K_TOPOLOGY).integers(2 ** 31))
    done = nx.connected_double_edge_swap(h, nswap=want, seed=s)
    return _permute_weights(h, g1, seed), {"swaps_requested": want, "swaps_done": int(done)}


def randomise_edges(g1, seed, max_draws=1000):
    """The deliverable's rule (`make_geo_sweep.py`, mode `randomizzato`): same number of edges, uniform
    pairs; disconnected draws are rejected. Then G1's weights permuted."""
    nodes = list(g1.nodes)
    n, E = len(nodes), g1.number_of_edges()
    r = rng(seed, K_TOPOLOGY)
    for draw in range(1, max_draws + 1):
        h = nx.Graph()
        h.add_nodes_from(nodes)
        while h.number_of_edges() < E:
            a, b = int(r.integers(n)), int(r.integers(n))
            if a != b:
                h.add_edge(nodes[a], nodes[b])
        if nx.is_connected(h):
            return _permute_weights(h, g1, seed), {"draws": draw, "rejected": draw - 1}
    raise RuntimeError(f"no connected edge-count randomisation in {max_draws} draws")


def geo_lengths(h, kept, coords):
    pos = {s: i for i, s in enumerate(kept)}
    return np.array([float(np.hypot(*(coords[pos[u]] - coords[pos[v]]))) for u, v in h.edges()])


# ---------------------------------------------------------------- model ------------------------------

class GTCN(nn.Module):
    def __init__(s, c, k, d):
        super().__init__(); s.pad = (k - 1) * d
        s.f = nn.Conv2d(c, c, (1, k), dilation=(1, d)); s.g = nn.Conv2d(c, c, (1, k), dilation=(1, d))

    def forward(s, x):
        x = F.pad(x, (s.pad, 0)); return torch.tanh(s.f(x)) * torch.sigmoid(s.g(x))


class GCN(nn.Module):
    def __init__(s, c, order=2):
        super().__init__(); s.order = order; s.mlp = nn.Conv2d(c * (order + 1), c, (1, 1))

    def forward(s, x, A):
        out, xk = [x], x
        for _ in range(s.order):
            xk = torch.einsum("nm,bcmt->bcnt", A, xk); out.append(xk)
        return s.mlp(torch.cat(out, 1))


class Block(nn.Module):
    def __init__(s, c, d, graph):
        super().__init__(); s.tcn = GTCN(c, 2, d); s.gcn = GCN(c) if graph else None
        s.skip = nn.Conv2d(c, c, (1, 1)); s.bn = nn.BatchNorm2d(c)

    def forward(s, x, A):
        res = x; x = s.tcn(x); sk = s.skip(x)
        if s.gcn is not None:
            x = s.gcn(x, A)
        return s.bn(x + res), sk


class GWN(nn.Module):
    """`gomo_sparse.py` GWN, inductive, without coordinates: `none` (G0) or `fixed` (G1 and G1-rand)."""

    def __init__(s, c_in, graph, hidden=32, blocks=4):
        super().__init__(); s.graph = graph
        s.start = nn.Conv2d(c_in, hidden, (1, 1))
        s.blocks = nn.ModuleList([Block(hidden, 2 ** i, graph) for i in range(blocks)])
        s.e1 = nn.Conv2d(hidden, hidden, (1, 1)); s.e2 = nn.Conv2d(hidden, len(HORIZONS) * 3, (1, 1))

    def forward(s, x, A):
        B, _, N, _ = x.shape
        x = s.start(x); skip = 0
        for b in s.blocks:
            x, sk = b(x, A); skip = skip + sk[..., -1:]
        h = F.relu(s.e1(F.relu(skip)))
        return s.e2(h).squeeze(-1).permute(0, 2, 1).contiguous().reshape(B, N, len(HORIZONS), 3)


# ---------------------------------------------------------------- run setup --------------------------

class Setup:
    """Everything an arm needs for one (configuration, seed): tensors, node sets, origins, weights.
    Built only from observed nodes in the training period; arm-independent by construction."""

    def __init__(s, city, graph_path, seed, grid="adaptive", targets=(0.4, 0.2, 0.4), device=None):
        s.city, s.graph_path, s.seed = city, str(graph_path), int(seed)
        s.dev = torch.device(device or ("mps" if torch.backends.mps.is_available() else "cpu"))
        z = load_targets(city)
        al = align_graph(city, graph_path)
        s.al = al; s.kept = al["kept"]; s.K = K = len(s.kept)
        s.ts = z["timestamps"]
        k = al["kidx"]
        s.r = z["r_emp"][:, k].astype("float32"); s.flow = z["flow"][:, k].astype("float32")
        s.occ = z["occupancy"][:, k].astype("float32"); s.C = z["congestion_emp"][:, k].astype("int64")
        s.G = adaptive_grid(al["coords"]) if grid == "adaptive" else int(grid)
        s.cells = grid_cells(al["coords"], s.G)
        s.lab = node_sets(s.cells, seed, targets)
        s.obs, s.val, s.test = (s.lab == 0), (s.lab == 1), (s.lab == 2)
        s.obs_cells = np.unique(s.cells[s.obs])
        orig = admissible_origins(s.ts)
        s.n_nominal = int(len(s.ts) - max(HORIZONS) - (T_IN - 1))
        s.tr, s.va, s.te, s.purged = split_origins(orig)
        s.n_admissible = int(len(orig))
        s.reg_end = int(s.tr[-1]) + 1                                         # training-period cells
        s._stats()
        s._tensors()

    def _stats(s):
        reg, o = slice(0, s.reg_end), s.obs
        ctr = s.C[reg][:, o]
        freq = np.array([(ctr == c).sum() for c in (1, 2, 3)], dtype="float64")
        s.W = (freq.sum() / (np.maximum(freq, 1) * 3)).astype("float32")
        s.freq = freq

        def zst(a):
            v = a[reg][:, o]; v = v[np.isfinite(v)]
            return float(v.mean()), float(v.std() + 1e-6)
        s.fmu, s.fsd = zst(s.flow); s.omu, s.osd = zst(s.occ)
        slot = (pd.DatetimeIndex(s.ts).dayofweek.to_numpy() * 96 + pd.DatetimeIndex(s.ts).hour.to_numpy() * 4
                + pd.DatetimeIndex(s.ts).minute.to_numpy() // 15)
        s.slot = slot
        hs = np.zeros((s.K, 672)); hc = np.zeros((s.K, 672))
        rv = s.r[reg]; vv = np.isfinite(rv) & o[None, :]
        si = np.broadcast_to(np.arange(s.K), rv.shape); sl = np.broadcast_to(slot[reg][:, None], rv.shape)
        np.add.at(hs, (si[vv], sl[vv]), rv[vv]); np.add.at(hc, (si[vv], sl[vv]), 1)
        ht = np.divide(hs, hc, out=np.full_like(hs, np.nan), where=hc > 0)
        gm = float(np.nanmean(ht[o]))
        sm = np.nanmean(np.where(np.isfinite(ht), ht, np.nan), 1)
        sm = np.where(np.isfinite(sm), sm, gm)
        HA = np.nan_to_num(np.where(np.isfinite(ht), ht, sm[:, None]), nan=gm).astype("float32")
        HA[~o] = 0.0                                                          # hidden: never input anyway
        s.HA = HA
        ms = s.al["max_speed"]
        s.maxsp = np.nan_to_num((ms - np.nanmean(ms)) / (np.nanstd(ms) + 1e-6), nan=0.0).astype("float32")

    def _tensors(s):
        T = lambda a: torch.tensor(a, device=s.dev)  # noqa: E731
        s.Rf = T(np.where(np.isfinite(s.r), s.r, 1.0).astype("float32"))
        s.FL = T(np.where(np.isfinite(s.flow), (s.flow - s.fmu) / s.fsd, 0.0).astype("float32"))
        s.OC = T(np.where(np.isfinite(s.occ), (s.occ - s.omu) / s.osd, 0.0).astype("float32"))
        s.HAs = T(s.HA[:, s.slot].T.copy())
        q = (pd.DatetimeIndex(s.ts).hour.to_numpy() * 4 + pd.DatetimeIndex(s.ts).minute.to_numpy() // 15) / 96.0
        dow = pd.DatetimeIndex(s.ts).dayofweek.to_numpy()
        s.TIME = [T(np.sin(2 * np.pi * q).astype("float32")), T(np.cos(2 * np.pi * q).astype("float32")),
                  T(np.sin(2 * np.pi * dow / 7).astype("float32")), T(np.cos(2 * np.pi * dow / 7).astype("float32")),
                  T((dow >= 5).astype("float32"))]
        s.MAXSP = T(s.maxsp)
        s.Cy = T(np.where(s.C > 0, s.C - 1, 0).astype("int64")); s.Cm = T((s.C > 0).astype("float32"))
        s.Wt = T(s.W)
        s.c_in = 11

    def fingerprints(s):
        return {"node_sets": fingerprint(s.lab), "origins": fingerprint(np.concatenate([s.tr, s.va, s.te])),
                "class_weights": fingerprint(s.W), "normalisation": fingerprint([s.fmu, s.fsd, s.omu, s.osd]),
                "historical_average": fingerprint(s.HA)}

    def geometry(s):
        return geometry_record(s.al["coords"], s.cells, s.G, s.lab)

    def shares(s):
        return {"observed": float(s.obs.mean()), "validation_hidden": float(s.val.mean()),
                "test_hidden": float(s.test.mean())}

    # ---------------------------------------------------------- batches ---------------------------------
    def batch(s, origins, inp, tgt, static=True):
        """inp, tgt: boolean node masks (numpy). Input channels are zero outside `inp`; the loss mask is
        Cm restricted to `tgt`. static=False zeroes the max_speed channel (diagnostic only)."""
        bt = torch.as_tensor(np.asarray(origins), device=s.dev); B = len(bt); K = s.K
        om = torch.as_tensor(inp.astype("float32"), device=s.dev).view(1, K, 1)

        def wn(M):
            return torch.stack([M[bt - k] for k in reversed(range(T_IN))], -1)

        def wg(g):
            return torch.stack([g[bt - k] for k in reversed(range(T_IN))], -1).unsqueeze(1).expand(-1, K, -1)
        st = lambda v: v.view(1, K, 1).expand(B, K, T_IN)  # noqa: E731
        ch = [wn(s.Rf) * om, wn(s.FL) * om, wn(s.OC) * om, wn(s.HAs) * om] + [wg(g) for g in s.TIME] + \
             [st(s.MAXSP if static else torch.zeros_like(s.MAXSP)), om.expand(B, K, T_IN)]
        x = torch.stack(ch, 1)
        y = torch.stack([s.Cy[bt + h] for h in HORIZONS], -1)
        tm = torch.as_tensor(tgt.astype("float32"), device=s.dev).view(1, K, 1)
        m = torch.stack([s.Cm[bt + h] for h in HORIZONS], -1) * tm
        return x, y, m

    def batch_mask(s, r):
        """Per-batch input cells among observed cells: share u ~ U(0.6, 0.95), whole cells, at least one
        input cell and one target cell."""
        n = len(s.obs_cells)
        u = r.uniform(0.6, 0.95)
        k = int(np.clip(round(u * n), 1, n - 1))
        chosen = r.choice(s.obs_cells, k, replace=False)
        inp = np.isin(s.cells, chosen) & s.obs
        return inp, s.obs & ~inp, u


def loss_fn(lg, y, m, W):
    lp = F.log_softmax(lg, -1); nll = -lp.gather(-1, y.unsqueeze(-1)).squeeze(-1)
    return (nll * W[y] * m).sum() / (W[y] * m).sum().clamp_min(1)


def wce_np(P, Y, W):
    """Aggregate wCE in float64 over valid cells (Y >= 0)."""
    P = P.reshape(-1, 3).astype("float64"); Y = Y.reshape(-1); v = Y >= 0
    pt = np.clip(P[v][np.arange(v.sum()), Y[v]], 1e-7, 1)
    w = W.astype("float64")[Y[v]]
    return float(np.sum(w * -np.log(pt)) / np.sum(w))


# ---------------------------------------------------------------- training ---------------------------

def predict(net, su, A, origins, inp, tgt, bs=256, static=True):
    """Probabilities (n_orig, K, H, 3) and labels (-1 where not a target)."""
    net.eval(); P, Y = [], []
    with torch.no_grad():
        for i in range(0, len(origins), bs):
            x, y, m = su.batch(origins[i:i + bs], inp, tgt, static)
            P.append(F.softmax(net(x, A), -1).float().cpu().numpy())
            Y.append(np.where(m.cpu().numpy() > 0, y.cpu().numpy(), -1))
    return np.concatenate(P), np.concatenate(Y)


def train(su, arm, A, U, checkpoints, log=None, lr=1e-3, static=True, input_extra=None, target_extra=None):
    """Fixed number of updates U; `checkpoints` = sorted update counts at which validation-hidden wCE is
    computed (input = all observed nodes). Returns the selected state (min validation wCE among the
    checkpoints), the trajectory and counters. Never touches test origins.

    Diagnostic options (pilot only, never in the campaign): lr; static=False drops max_speed;
    input_extra = nodes always in input and never targets; target_extra = nodes always targets in training
    and never input. The trajectory also records the mean training loss since the previous checkpoint."""
    graph = arm != "G0"
    s6 = int(rng(su.seed, K_INIT).integers(2 ** 31))
    torch.manual_seed(s6)
    net = GWN(su.c_in, graph).to(su.dev)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    xin = np.zeros(su.K, bool) if input_extra is None else input_extra
    xtg = np.zeros(su.K, bool) if target_extra is None else target_extra
    run_loss = []
    At = torch.tensor(A, device=su.dev) if graph else None
    r_mask, r_order = rng(su.seed, K_MASKS), rng(su.seed, K_ORDER)
    perm, pi = r_order.permutation(su.tr), 0
    traj, states, steps, t0 = [], {}, 0, time.perf_counter()
    cks = set(int(c) for c in checkpoints)
    seen_hidden = 0

    def checkpoint():
        P, Y = predict(net, su, At, su.va, su.obs | xin, su.val, static=static)
        v = wce_np(P, Y, su.W)
        tl = float(np.mean(run_loss)) if run_loss else None
        run_loss.clear()
        traj.append({"update": steps, "val_wce": v, "train_loss": tl, "seconds": time.perf_counter() - t0})
        states[steps] = {k: t.detach().cpu().clone() for k, t in net.state_dict().items()}
        if log:
            log(f"[{arm}] update {steps:6d}  val wCE {v:.5f}")
    if 0 in cks:
        checkpoint()
    while steps < U:
        if pi + 32 > len(perm):
            perm, pi = r_order.permutation(su.tr), 0
        bt = perm[pi:pi + 32]; pi += 32
        inp, tgt, _ = su.batch_mask(r_mask)
        seen_hidden += int(inp[~su.obs].sum() + tgt[~su.obs].sum())
        x, y, m = su.batch(bt, inp | xin, tgt | xtg, static)
        net.train(); opt.zero_grad()
        loss = loss_fn(net(x, At), y, m, su.Wt); loss.backward(); opt.step(); steps += 1
        run_loss.append(float(loss.item()))
        if steps in cks:
            checkpoint()
    best = min(traj, key=lambda d: d["val_wce"])
    return {"net": net, "A": At, "states": states, "trajectory": traj, "selected": best["update"],
            "updates": steps, "hidden_in_batches": seen_hidden, "seconds": time.perf_counter() - t0,
            "init_seed": s6}


def require_signed(prereg):
    """Test metrics only after the signature: no blank field may remain in the signature line."""
    head = Path(prereg).read_text().split("\n\n")[1]
    if "____" in head or "__/__" in head:
        raise PermissionError(f"{prereg}: signature line not filled; test metrics are not allowed")


def run_dir(base, config):
    """Folder named by the fingerprint of the full configuration; an existing name blocks the launch."""
    d = Path(base) / fingerprint(config)
    if d.exists():
        raise FileExistsError(f"{d} exists: launch blocked")
    d.mkdir(parents=True)
    return d


def record(d, payload):
    c, dirty = git_commit()
    payload = {"commit": c, "code_dirty": dirty, "written": datetime.now(timezone.utc).isoformat(),
               "device": str(torch.backends.mps.is_available() and "mps" or "cpu"),
               "code_fingerprint": sha256(Path(__file__), 16), **payload}
    (Path(d) / "run.json").write_text(json.dumps(payload, indent=1, default=str))
    return payload
