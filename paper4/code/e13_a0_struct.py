#!/usr/bin/env python3
"""
Investigation I3 (E13, dated note of 2026-11-19): structural measurement, without any training and without loading any
target series, of how often the masked nodes are reachable from the available readings through the adjacency G1 receives
(`p4b.kernel_adjacency` on the aligned road graph, as `e9.adjacency` builds it) and how much mass the REFERENCE propagation
operator M_h = sum_{k=1..h} A^k assigns to them from the input nodes, for h = 6 (the receptive field of the predictions of
`p4b.GWN`), 8 and 12. M_h is a linear reference operator: the network combines learned convolutions, activations, residuals,
normalisation and skip branches, so these quantities describe reachability and path mass in the adjacency, not the amplitude
of the signal in the predictions. They may contribute to explaining the observed failures; they do not establish their cause.

For every city and seed at f = 0.20 (the adjacency does not depend on the regime), from graph, coordinates, grid cells and
node sets only (`align_graph_ids_only`, a replica of `p4b.align_graph` that reads only `sensor_ids` from the target archive;
`p4b.grid_cells`, `p4b.node_sets` with the E9 grid and targets; `batch_mask` replicated verbatim on the seed's masking stream): validation-hidden nodes and test-hidden nodes with inputs = observed nodes (node
sets only); training targets with inputs = the input cells of 20 draws of `batch_mask`; observed nodes for reference.
Reported per combination: median and quartiles of the mass (scientific notation), shares of nodes with mass > 0.1, > 0.01,
in (0, 1e-6], and exactly 0 (exact zero = no path within h steps), hop distance to the nearest input node (BFS along the
propagation direction), edge-length and weight statistics. All 15 combinations are reported; no decision threshold.

Freezing checks before writing anything: clean working tree, expected tag reachable from HEAD, frozen files and this script
identical to the tag. Refuses to run if an output exists. Records tag, commit, fingerprints of this script, p4b.py, e9.py
and e13.py, fingerprints of the structural inputs (road graph, sensor registry, target archive — only `sensor_ids` read —, identifier
sequence, kept sequence), environment and time. Writes paper4/runs/e13_a0_struct.log and .json. Run from the repository root:
PYTHONPATH=paper4/code python3 paper4/code/e13_a0_struct.py
"""
import hashlib, json, pickle, subprocess, sys
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd, networkx as nx
from scipy.spatial import cKDTree
import p4b, e9, e13

EXPECTED_TAG = "paper4-E13-20261119b"; THIS = Path(__file__).resolve(); THIS_REL = "paper4/code/e13_a0_struct.py"
LOG, JS = Path("paper4/runs/e13_a0_struct.log"), Path("paper4/runs/e13_a0_struct.json")
HOPS = (6, 8, 12); SEEDS = range(5); DRAWS = 20; F = e13.F

if LOG.exists() or JS.exists():
    sys.exit("output exists: the measurement is recorded once")
if not e13.git_clean():
    sys.exit("working tree not clean")
tag = e13.frozen_tag()
if tag != EXPECTED_TAG:
    sys.exit(f"nearest E13 tag is {tag!r}, expected {EXPECTED_TAG}")
if subprocess.run(["git", "diff", "--quiet", tag, "HEAD", "--", *e13.FROZEN_PATHS, THIS_REL], cwd=e13.ROOT).returncode != 0:
    sys.exit("frozen files or this script differ from the tag")

lines = []
def say(m):
    print(m); lines.append(m)


def align_graph_ids_only(city, graph_path):
    """Replica of p4b.align_graph that reads from the target archive ONLY `sensor_ids` (np.load of an .npz reads one member
    per key access; no other member is touched): same node order (target order), same geographic association (nearest
    sensor within ALIGN_M), same graph construction (simple graph on the kept nodes, self-loops removed, edge weight)."""
    with np.load(p4b.CITY[city]["targets"], allow_pickle=True) as z:
        sids = z["sensor_ids"].astype(str)
    with open(graph_path, "rb") as f:
        rg = pickle.load(f)
    sens = pd.read_csv(p4b.CITY[city]["sensors"], dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    tree = cKDTree(sens[["utm_x", "utm_y"]].to_numpy())
    nodes = list(rg.nodes)
    nxy = np.array([[rg.nodes[n]["utm_x"], rg.nodes[n]["utm_y"]] for n in nodes])
    dist, idx = tree.query(nxy, k=1)
    ids = sens["id"].to_numpy()
    rg = nx.relabel_nodes(rg, {nodes[i]: ids[idx[i]] for i in range(len(nodes)) if dist[i] <= p4b.ALIGN_M}, copy=True)
    kept = [x for x in sids if x in rg.nodes]
    wattr = "distance" if any("distance" in a for *_, a in list(rg.edges(data=True))[:50]) else "weight"
    g = nx.Graph(); g.add_nodes_from(kept); loops = 0
    for u, v, a in rg.subgraph(kept).edges(data=True):
        if u == v:
            loops += 1; continue
        g.add_edge(u, v, weight=float(a[wattr]))
    smeta = sens.drop_duplicates("id").set_index("id")
    coords = smeta.loc[kept, ["utm_x", "utm_y"]].to_numpy("float64")
    return {"graph": g, "kept": kept, "loops_removed": loops, "weight_attr": wattr, "coords": coords, "sensor_ids": sids}


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


class LightSetup:
    """Graph, coordinates, grid cells and node sets of (city, seed) at f = 0.20 — no target series is loaded."""
    def __init__(s, city, seed):
        s.al = align_graph_ids_only(city, p4b.CITY[city]["roads"]); s.kept = s.al["kept"]; s.K = len(s.kept); s.seed = int(seed)
        s.G = int(e9.GRID[city]); s.cells = p4b.grid_cells(s.al["coords"], s.G)
        s.lab = p4b.node_sets(s.cells, seed, e9.targets(F))
        s.obs, s.val, s.test = (s.lab == 0), (s.lab == 1), (s.lab == 2)
        s.obs_cells = np.unique(s.cells[s.obs])
        s.A, s.sigma = p4b.kernel_adjacency(s.al["graph"], s.kept)

    def batch_mask(s, r):
        """Verbatim replica of p4b.Setup.batch_mask (same stream, same draws)."""
        n = len(s.obs_cells)
        u = r.uniform(0.6, 0.95)
        k = int(np.clip(round(u * n), 1, n - 1))
        chosen = r.choice(s.obs_cells, k, replace=False)
        inp = np.isin(s.cells, chosen) & s.obs
        return inp, s.obs & ~inp, u


def hop_dist(A, inp):
    n = len(A); fwd = [np.flatnonzero(A[:, m] > 0) for m in range(n)]; d = np.full(n, -1); q = deque()
    for m in np.flatnonzero(inp):
        d[m] = 0; q.append(m)
    while q:
        m = q.popleft()
        for k in fwd[m]:
            if d[k] < 0:
                d[k] = d[m] + 1; q.append(k)
    return d


def summary(den):
    den = np.asarray(den, dtype="float64")
    return {"n": int(den.size), "median": float(np.median(den)), "p25": float(np.percentile(den, 25)), "p75": float(np.percentile(den, 75)),
            "share_gt_0.1": float((den > 0.1).mean()), "share_gt_0.01": float((den > 0.01).mean()),
            "share_tiny_0_to_1e-6": float(((den > 0) & (den <= 1e-6)).mean()), "share_exact_zero": float((den == 0).mean())}


def fmt(s):
    return (f"median {s['median']:.3e} [p25 {s['p25']:.3e}, p75 {s['p75']:.3e}]; >0.1: {100*s['share_gt_0.1']:.1f} %, >0.01: {100*s['share_gt_0.01']:.1f} %, "
            f"(0, 1e-6]: {100*s['share_tiny_0_to_1e-6']:.1f} %, exactly 0 (no path): {100*s['share_exact_zero']:.1f} %")


out = {"investigation": "I3 (reachability and reference propagation mass)", "hops": list(HOPS), "draws": DRAWS, "f": F, "frozen_tag": tag, "head": e13.head_commit(),
       "fingerprints": {"e13_a0_struct.py": p4b.sha256(THIS, 16), "p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16), "e13.py": p4b.sha256(Path(e13.__file__), 16)},
       "environment": e13.environment(), "started": datetime.now(timezone.utc).isoformat(), "cities": {}}
say(f"I3 — {out['started']} — tag {tag}, HEAD {out['head']}, script {out['fingerprints']['e13_a0_struct.py']}")
for city in e13.CITIES:
    out["cities"][city] = {"seeds": {}}
    for seed in SEEDS:
        s = LightSetup(city, seed); A = np.asarray(s.A, dtype="float64")
        if seed == 0:
            g = s.al["graph"]; L = np.array([a["weight"] for *_, a in g.edges(data=True)]); off = A - np.diag(np.diag(A))
            out["cities"][city]["graph"] = {"K": int(s.K), "edges": int(g.number_of_edges()), "grid": s.G, "length_median_m": float(np.median(L)), "length_mean_m": float(L.mean()),
                                            "sigma_m": float(s.sigma), "length_p90_m": float(np.percentile(L, 90)), "diag_mean": float(A.diagonal().mean()),
                                            "offdiag_mean": float(off[off > 0].mean()), "neighbour_share_of_row_mass_mean": float((off.sum(1) / A.sum(1)).mean())}
            out["cities"][city]["inputs"] = {"roads_graph": str(p4b.CITY[city]["roads"]), "roads_graph_sha16": sha_file(p4b.CITY[city]["roads"]),
                                             "sensors_csv": str(p4b.CITY[city]["sensors"]), "sensors_csv_sha16": sha_file(p4b.CITY[city]["sensors"]),
                                             "targets_archive": str(p4b.CITY[city]["targets"]), "targets_archive_sha16": sha_file(p4b.CITY[city]["targets"]),
                                             "sensor_ids_sequence_sha16": hashlib.sha256("\n".join(s.al["sensor_ids"]).encode()).hexdigest()[:16],
                                             "kept_sequence_sha16": hashlib.sha256("\n".join(s.kept).encode()).hexdigest()[:16], "loops_removed": int(s.al["loops_removed"]),
                                             "weight_attr": s.al["weight_attr"]}
            say(f"   inputs: graph {out['cities'][city]['inputs']['roads_graph_sha16']}, sensors {out['cities'][city]['inputs']['sensors_csv_sha16']}, "
                f"archive {out['cities'][city]['inputs']['targets_archive_sha16']} (only sensor_ids read), id sequence {out['cities'][city]['inputs']['sensor_ids_sequence_sha16']}, kept {out['cities'][city]['inputs']['kept_sequence_sha16']}")
            say(f"{city}: K {s.K}, edges {g.number_of_edges()}, grid {s.G}, edge length m median {np.median(L):.0f} mean {L.mean():.0f} sigma {s.sigma:.0f} p90 {np.percentile(L, 90):.0f}; "
                f"diagonal mean {A.diagonal().mean():.3f}, off-diagonal weight mean {off[off > 0].mean():.3f}, neighbours' share of row mass {(off.sum(1) / A.sum(1)).mean():.3f}")
        Ms = {}; P = np.eye(len(A)); M = np.zeros_like(A)
        for k in range(1, max(HOPS) + 1):
            P = P @ A; M = M + P
            if k in HOPS:
                Ms[k] = M.copy()
        rec = {"observed": int(s.obs.sum()), "validation_hidden": int(s.val.sum()), "test_hidden": int(s.test.sum())}
        hd = hop_dist(A, s.obs)
        rec["hop_distance_validation_hidden"] = {str(k): int(v) for k, v in zip(*np.unique(hd[s.val], return_counts=True))}
        rec["hop_distance_test_hidden"] = {str(k): int(v) for k, v in zip(*np.unique(hd[s.test], return_counts=True))}
        r = p4b.rng(s.seed, p4b.K_MASKS); draws = [s.batch_mask(r)[:2] for _ in range(DRAWS)]
        say(f"  seed {seed}: observed {s.obs.sum()}, validation-hidden {s.val.sum()}, test-hidden {s.test.sum()}; hop distance of validation-hidden to the nearest observed: "
            f"{rec['hop_distance_validation_hidden']} (-1 = no path)")
        for h in HOPS:
            Mh = Ms[h]; mo = Mh[:, s.obs].sum(1)
            tr = np.concatenate([Mh[:, inp].sum(1)[tgt] for inp, tgt in draws])
            rec[f"mass_{h}hops"] = {"validation_hidden": summary(mo[s.val]), "test_hidden": summary(mo[s.test]), "training_targets": summary(tr), "observed_self": summary(mo[s.obs])}
            say(f"    {h:2d} hops | validation-hidden: {fmt(rec[f'mass_{h}hops']['validation_hidden'])}")
            say(f"            | test-hidden:       {fmt(rec[f'mass_{h}hops']['test_hidden'])}")
            say(f"            | training targets:  {fmt(rec[f'mass_{h}hops']['training_targets'])}")
            if h == HOPS[0]:
                say(f"            | observed (self):   {fmt(rec[f'mass_{h}hops']['observed_self'])}")
        out["cities"][city]["seeds"][str(seed)] = rec
out["written"] = datetime.now(timezone.utc).isoformat()
LOG.parent.mkdir(parents=True, exist_ok=True); LOG.write_text("\n".join(lines) + "\n"); JS.write_text(json.dumps(out, indent=1))
print("->", LOG, p4b.sha256(LOG, 16), JS, p4b.sha256(JS, 16))
