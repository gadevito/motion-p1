#!/usr/bin/env python3
"""
E11 — geometry under protocol (`protocol/paper4/E11.md`).
==========================================================
Three commands, all before the signature and none of them computing a test metric:

    preflight   the assertions of E11 "Mandatory controls" (1-9, 5-bis) plus a determinism check;
    pilot       G0 and G1 on Madrid comp_q5050, seed 0, 8,000 updates, validation every 250 updates;
                fixes U and estimates the order of magnitude of the half-width of I_c;
    cost        isolated trainings for the cost table: G1 on the whole of Madrid at f = 40%
                (road graph), and each E11 arm on the pilot configuration, U updates each.

The campaign command is added after the signature. Usage (from the worktree root):

    $PY paper4/code/e11.py preflight
    $PY paper4/code/e11.py pilot
    $PY paper4/code/e11.py cost --updates U
"""
import argparse
import copy
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402

ROOT = p4b.ROOT
RUNS = ROOT / "paper4" / "runs"
PREREG = ROOT / "protocol" / "paper4" / "E11.md"
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("G0", "G1", "G1-rand(deg)", "G1-rand(edges)")
BOOT_SEED = 20261106

# E11.md, Design: the 12 configurations and the real N printed in OLD/log/geo_campagna.log
CONFIGS = [
    ("madrid", "comp_q2050", 81), ("madrid", "comp_q2080", 93), ("madrid", "comp_q5020", 93),
    ("madrid", "comp_q5050", 95), ("madrid", "comp_q5080", 85), ("madrid", "comp_q8020", 98),
    ("madrid", "comp_q8050", 97), ("madrid", "comp_q8080", 91),
    ("melbourne", "comp_q2080", 99), ("melbourne", "comp_q5080", 99),
    ("melbourne", "comp_q8020", 97), ("melbourne", "comp_q8050", 96),
]
PILOT = ("madrid", "comp_q5050")


def graph_path(city, tag):
    return ROOT / "geo_sweep" / f"{city}_{tag}.pkl"


def adjacency(su, arm):
    """Adjacency of an arm for one Setup: None for G0, the kNN kernel for G1, the kernel of a randomised
    graph (G1's weights permuted) for G1-rand. Returns (A, info)."""
    g1 = su.al["graph"]
    if arm == "G0":
        return None, {}
    if arm == "G1":
        A, sg = p4b.kernel_adjacency(g1, su.kept)
        return A, {"sigma": sg, "edges": g1.number_of_edges()}
    h, info = (p4b.randomise_degree if arm == "G1-rand(deg)" else p4b.randomise_edges)(g1, su.seed)
    A, sg = p4b.kernel_adjacency(h, su.kept)
    geo = p4b.geo_lengths(h, su.kept, su.al["coords"])
    w = np.array(sorted(a["weight"] for *_, a in h.edges(data=True)))
    info.update({"sigma": sg, "edges": h.number_of_edges(), "connected": nx.is_connected(h),
                 "weights_fingerprint": p4b.fingerprint(w), "mean_geo_length_m": float(geo.mean()),
                 "degree_fingerprint": p4b.fingerprint(sorted(dict(h.degree()).items()))})
    return A, info, h


# ---------------------------------------------------------------- preflight --------------------------

class Log:
    def __init__(s, path):
        s.path, s.lines, s.fail = path, [], 0

    def __call__(s, msg):
        print(msg, flush=True); s.lines.append(msg)

    def check(s, n, label, ok, detail=""):
        s(f"[{'PASS' if ok else 'FAIL'}] {n:<6} {label}" + (f" — {detail}" if detail else ""))
        s.fail += 0 if ok else 1

    def save(s):
        Path(s.path).write_text("\n".join(s.lines) + "\n")


def cadence_ok(ts, t):
    w = ts[t - (p4b.T_IN - 1): t + max(p4b.HORIZONS) + 1].astype("datetime64[m]")
    return bool(np.all(np.diff(w) == p4b.STEP))


def preflight(args):
    RUNS.mkdir(parents=True, exist_ok=True)
    log = Log(RUNS / "e11_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E11 preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e11.py {p4b.sha256(Path(__file__), 16)} · "
        f"torch {torch.__version__} · mps {torch.backends.mps.is_available()}")
    city, tag = PILOT
    su = p4b.Setup(city, graph_path(city, tag), seed=0)
    log(f"configuration {city} {tag}, seed 0: K = {su.K}, shares {json.dumps(su.shares())}, "
        f"origins nominal {su.n_nominal} admissible {su.n_admissible} → train {len(su.tr)} val {len(su.va)} "
        f"test {len(su.te)}, purged {su.purged}")

    # 1 ------------------------------------------------------------------------------------------------
    whole = all(len(np.unique(su.lab[su.cells == c])) == 1 for c in np.unique(su.cells))
    sizes = (su.obs.sum() > 0, su.val.sum() > 0, su.test.sum() > 0, len(su.obs_cells) >= 2)
    log.check("1a", "three node sets disjoint, non-empty, unions of whole cells", whole and all(sizes),
              f"observed {int(su.obs.sum())}, validation-hidden {int(su.val.sum())}, test-hidden {int(su.test.sum())}")
    r = p4b.rng(0, p4b.K_MASKS); bad_mask = bad_tensor = 0; us = []
    hidden = torch.as_tensor(~su.obs, device=su.dev)
    for _ in range(300):
        inp, tgt, u = su.batch_mask(r); us.append(u)
        bad_mask += int((inp & ~su.obs).sum() + (tgt & ~su.obs).sum())
        x, y, m = su.batch(su.tr[:32], inp, tgt)
        bad_tensor += int(x[:, :4][:, :, hidden].abs().sum().item() > 0) + int(x[:, 10][:, hidden].abs().sum().item() > 0)
        bad_tensor += int(m[:, hidden].abs().sum().item() > 0)
    log.check("1b", "no hidden index in the input mask or loss mask of 300 batches", bad_mask == 0)
    log.check("1c", "hidden nodes zero in dynamic input channels, flag channel and loss tensor", bad_tensor == 0,
              f"u in [{min(us):.3f}, {max(us):.3f}]")

    # 2 ------------------------------------------------------------------------------------------------
    allo = np.concatenate([su.tr, su.va, su.te])
    adm = all(cadence_ok(su.ts, int(t)) for t in allo)
    gap = max(p4b.HORIZONS) + p4b.T_IN - 1
    purge = su.tr.max() + gap < su.va.min() and su.va.max() + gap < su.te.min()
    log.check("2a", "every origin admissible (15-min cadence from first input to last target)", adm,
              f"{len(allo)} origins; {su.n_nominal - su.n_admissible} nominal origins excluded")
    log.check("2b", "no target of a period overlaps an input of the next", bool(purge))
    bt = su.tr[100:132]; inp, tgt, _ = su.batch_mask(p4b.rng(0, 99))
    x0, _, _ = su.batch(bt, inp, tgt)
    sv = {k: getattr(su, k).clone() for k in ("Rf", "FL", "OC", "HAs")}
    tmax = int(bt.max())
    g = torch.Generator(device="cpu").manual_seed(7)
    for k in sv:
        t = getattr(su, k); noise = torch.randn(t[tmax + 1:].shape, generator=g).to(su.dev)
        t[tmax + 1:] = noise
    x1, _, _ = su.batch(bt, inp, tgt)
    for k, v in sv.items():
        setattr(su, k, v)
    log.check("2c", "causality: noise on every value after the origin leaves the inputs identical to the bit",
              bool(torch.equal(x0, x1)))
    pert = copy.copy(su)
    nz = np.random.default_rng(11)
    for k in ("r", "flow", "occ"):
        a = getattr(su, k).copy()
        a[su.reg_end:] = nz.normal(size=a[su.reg_end:].shape)
        a[:, ~su.obs] = nz.normal(size=a[:, ~su.obs].shape)
        setattr(pert, k, a)
    C2 = su.C.copy(); C2[su.reg_end:] = nz.integers(1, 4, size=C2[su.reg_end:].shape)
    C2[:, ~su.obs] = nz.integers(1, 4, size=C2[:, ~su.obs].shape); pert.C = C2
    pert._stats()
    same = (np.array_equal(pert.W, su.W) and [pert.fmu, pert.fsd, pert.omu, pert.osd] == [su.fmu, su.fsd, su.omu, su.osd]
            and np.array_equal(pert.HA, su.HA))
    log.check("2d", "noise after the training period and on hidden nodes leaves class weights, normalisation "
              "and historical average identical to the bit", bool(same))

    # 3 ------------------------------------------------------------------------------------------------
    ctr = su.C[:su.reg_end][:, su.obs].ravel()
    f = np.bincount(ctr, minlength=4)[1:].astype("float64")
    W_ind = (f.sum() / (np.maximum(f, 1) * 3)).astype("float32")
    fl = su.flow[:su.reg_end][:, su.obs]; fl = fl[np.isfinite(fl)]
    ok3 = np.array_equal(W_ind, su.W) and abs(fl.mean() - su.fmu) < 1e-6 * max(1, abs(su.fmu))
    log.check("3", "class weights and normalisation recomputed independently from observed training cells",
              bool(ok3), f"W = {np.round(su.W, 4).tolist()}, class shares {np.round(f / f.sum(), 4).tolist()}")

    # 4, 5, 5-bis -------------------------------------------------------------------------------------
    rows, n_ok, g_ok, w_ok = [], True, True, True
    for city_c, tag_c, n_real in CONFIGS:
        al = p4b.align_graph(city_c, graph_path(city_c, tag_c))
        g1 = al["graph"]
        n_ok &= len(al["kept"]) == n_real
        _, s1 = p4b.kernel_adjacency(g1, al["kept"])
        w1 = np.array(sorted(a["weight"] for *_, a in g1.edges(data=True)))
        geo1 = p4b.geo_lengths(g1, al["kept"], al["coords"]).mean()
        line = (f"{city_c:9s} {tag_c:10s} N {len(al['kept']):3d} (real {n_real}) loops removed {al['loops_removed']} "
                f"edges {g1.number_of_edges()} connected {nx.is_connected(g1)} mean edge {geo1:6.1f} m")
        g_ok &= nx.is_connected(g1)
        for seed in SEEDS:
            hd, info_d = p4b.randomise_degree(g1, seed)
            he, info_e = p4b.randomise_edges(g1, seed)
            deg_same = dict(hd.degree()) == dict(g1.degree())
            g_ok &= deg_same and nx.is_connected(hd) and nx.is_connected(he) and \
                he.number_of_edges() == g1.number_of_edges() and nx.number_of_selfloops(hd) == 0 and \
                nx.number_of_selfloops(he) == 0
            for h in (hd, he):
                wh = np.array(sorted(a["weight"] for *_, a in h.edges(data=True)))
                _, sh = p4b.kernel_adjacency(h, al["kept"])
                w_ok &= np.array_equal(wh, w1) and wh.sum() == w1.sum() and sh == s1
            if seed == 0:
                line += (f" | seed 0: swaps {info_d['swaps_done']}/{info_d['swaps_requested']}, "
                         f"edge-rand rejected {info_e['rejected']}, mean geo length deg "
                         f"{p4b.geo_lengths(hd, al['kept'], al['coords']).mean():6.1f} m, edges "
                         f"{p4b.geo_lengths(he, al['kept'], al['coords']).mean():6.1f} m")
        rows.append(line)
    for line in rows:
        log("        " + line)
    log.check("4", "N after alignment equals the real N of the Design table, 12 configurations", bool(n_ok))
    log.check("5", "G1 connected; G1-rand(deg) same degree sequence, node by node; G1-rand(edges) same edge "
              "count; all randomised graphs connected and simple (12 configurations × 5 seeds)", bool(g_ok))
    log.check("5-bis", "randomised weights a permutation of G1's: sorted multisets and sums identical, "
              "σ identical (12 × 5 × 2 graphs)", bool(w_ok))

    # node-set shares over the whole campaign -----------------------------------------------------------
    empty, table = 0, []
    for city_c, tag_c, _ in CONFIGS:
        al = p4b.align_graph(city_c, graph_path(city_c, tag_c))
        cells = p4b.grid_cells(al["coords"])
        sh = []
        for seed in SEEDS:
            n = np.bincount(p4b.node_sets(cells, seed), minlength=3)
            empty += int((n == 0).any()); sh.append("/".join(f"{100 * x / n.sum():.0f}" for x in n))
        table.append(f"{city_c:9s} {tag_c:10s} occupied cells {len(np.unique(cells)):2d}, largest "
                     f"{np.bincount(np.unique(cells, return_inverse=True)[1]).max():2d} | shares obs/val/test by seed: "
                     + "  ".join(sh))
    for line in table:
        log("        " + line)
    log.check("sets", "observed, validation-hidden and test-hidden non-empty in all 12 configurations × 5 seeds",
              empty == 0, f"{empty} of 60 (configuration, seed) pairs with an empty set")

    # 6 ------------------------------------------------------------------------------------------------
    fps = []
    for arm in ARMS:
        s_arm = p4b.Setup(city, graph_path(city, tag), seed=0)
        adjacency(s_arm, arm)
        fps.append(s_arm.fingerprints())
    log.check("6", "node sets, origins, class weights, normalisation and historical average identical "
              "across the four arms of a seed", all(fp == fps[0] for fp in fps), json.dumps(fps[0]))

    # 7, 8 ---------------------------------------------------------------------------------------------
    A1, _ = adjacency(su, "G1")[:2]
    out = p4b.train(su, "G1", A1, U=60, checkpoints=[20, 40, 60])
    log.check("7a", "optimiser updates equal U (60) exactly; no hidden node ever in a batch",
              out["updates"] == 60 and out["hidden_in_batches"] == 0)
    P, Y = p4b.predict(out["net"], su, out["A"], su.va, su.obs, su.val)
    pairs = int(P.shape[0] * su.val.sum())
    log.check("7b", "validation evaluates the calendar: all admissible validation origins × validation-hidden nodes",
              P.shape[0] == len(su.va) and pairs == len(su.va) * int(su.val.sum()) and
              int((Y[:, ~su.val] >= 0).sum()) == 0, f"{len(su.va)} × {int(su.val.sum())} = {pairs}")
    d = RUNS / "e11_preflight_cells"; d.mkdir(exist_ok=True)
    np.savez_compressed(d / "val_G1_s0.npz", p=P, y=Y, origins=su.va)
    z = np.load(d / "val_G1_s0.npz")
    w_file = p4b.wce_np(z["p"], z["y"], su.W)
    log.check("8", "per-cell prediction file exists and reconstructs the aggregate wCE within 1e-9",
              abs(w_file - out["trajectory"][-1]["val_wce"]) < 1e-9,
              f"|Δ| = {abs(w_file - out['trajectory'][-1]['val_wce']):.2e}")

    # 9 ------------------------------------------------------------------------------------------------
    cfg = {"preflight": "run-dir test", "stamp": datetime.now(timezone.utc).isoformat()}
    p4b.run_dir(RUNS / "e11_preflight_dirs", cfg)
    try:
        p4b.run_dir(RUNS / "e11_preflight_dirs", cfg); blocked = False
    except FileExistsError:
        blocked = True
    log.check("9", "run folder named by the configuration fingerprint; an existing name blocks the launch", blocked)

    # determinism and guards ------------------------------------------------------------------------------
    out2 = p4b.train(su, "G1", A1, U=60, checkpoints=[20, 40, 60])
    dmax = max(float((out["net"].state_dict()[k].float() - out2["net"].state_dict()[k].float()).abs().max())
               for k in out["net"].state_dict())
    dv = abs(out["trajectory"][-1]["val_wce"] - out2["trajectory"][-1]["val_wce"])
    log(f"[INFO] det    two identical G1 runs (60 updates): max |Δ parameter| = {dmax:.3e}, |Δ val wCE| = {dv:.3e}"
        + (" (bitwise identical)" if dmax == 0 else " (residual MPS non-determinism, declared)"))
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E11 signature line is blank", guard)
    log.check("guard", "no training origin in the validation or test period",
              bool(su.tr.max() < su.va.min() and su.va.max() < su.te.min()))
    log(f"PREFLIGHT: {log.fail} failure(s)")
    log.save()
    return 0 if log.fail == 0 else 1


# ---------------------------------------------------------------- pilot ------------------------------

def block_halfwidth(Pa, Pb, Y, cells, mask, W, B=4000, seed=BOOT_SEED):
    """Half-width of the 95% interval of D(G1, G0) = 100·(wCE_G0 − wCE_G1)/wCE_G0 under a resample of
    validation-hidden corridor blocks with multiplicities (one seed only: an order of magnitude)."""
    idx = np.where(mask)[0]; blocks = np.unique(cells[idx])
    W64 = W.astype("float64")

    def per_node(P):
        S = np.zeros(len(mask)); Wn = np.zeros(len(mask))
        Yt = Y.transpose(1, 0, 2).reshape(len(mask), -1); Pt = P.transpose(1, 0, 2, 3).reshape(len(mask), -1, 3)
        for n in idx:
            v = Yt[n] >= 0
            pt = np.clip(Pt[n][v, Yt[n][v]], 1e-7, 1).astype("float64"); w = W64[Yt[n][v]]
            S[n] = np.sum(w * -np.log(pt)); Wn[n] = np.sum(w)
        return S, Wn
    Sa, Wa = per_node(Pa); Sb, Wb = per_node(Pb)
    r = np.random.default_rng(seed); reps = []
    for _ in range(B):
        pick = r.choice(blocks, len(blocks), replace=True)
        mult = np.zeros(len(mask))
        for c in pick:
            mult[(cells == c) & mask] += 1
        wa = (mult * Sa).sum() / (mult * Wa).sum(); wb = (mult * Sb).sum() / (mult * Wb).sum()
        reps.append(100 * (wb - wa) / wb)
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return float((hi - lo) / 2), int(len(blocks))


def pilot(args):
    RUNS.mkdir(parents=True, exist_ok=True)
    city, tag = PILOT
    su = p4b.Setup(city, graph_path(city, tag), seed=0)
    L = args.length; cks = list(range(0, L + 1, 250))
    res = {}
    for arm in ("G0", "G1"):
        A = adjacency(su, arm)[0]
        res[arm] = p4b.train(su, arm, A, U=L, checkpoints=cks, log=print)
    first = {}
    for arm, o in res.items():
        v = np.array([d["val_wce"] for d in o["trajectory"]]); u = np.array([d["update"] for d in o["trajectory"]])
        first[arm] = int(u[np.argmax(v <= 1.01 * v.min())])
    U = int(np.ceil(max(first.values()) / 500) * 500)
    def val_at(arm, k):
        return next(d["val_wce"] for d in res[arm]["trajectory"] if d["update"] == k)
    def order(k):
        return "G0<G1" if val_at("G0", k) < val_at("G1", k) else "G1<=G0"
    doubled = False
    if 2 * U <= L and order(U) != order(2 * U):
        U *= 2; doubled = True
    adequate = 2 * U <= L and order(U) == order(2 * U)
    preds = {}
    for arm, o in res.items():
        net = o["net"]; net.load_state_dict(o["states"][U])
        preds[arm] = p4b.predict(net, su, o["A"], su.va, su.obs, su.val)
    hw, nb = block_halfwidth(preds["G1"][0], preds["G0"][0], preds["G0"][1], su.cells, su.val, su.W)
    out = {"protocol": "protocol/paper4/E11.md", "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "configuration": f"{city} {tag}", "seed": 0, "length": L, "evaluation_every": 250,
           "K": su.K, "shares": su.shares(), "fingerprints": su.fingerprints(),
           "first_within_1pct": first, "U": U, "U_doubled": doubled, "adequacy_order_same_at_U_and_2U": adequate,
           "expected_halfwidth_points": round(hw, 3), "halfwidth_blocks": nb,
           "halfwidth_note": "D(G1, G0) on validation-hidden nodes at update U, block resample of one seed; "
                             "order of magnitude only, not a criterion",
           "trajectories": {a: o["trajectory"] for a, o in res.items()},
           "seconds": {a: o["seconds"] for a, o in res.items()}, "init_seeds": {a: o["init_seed"] for a, o in res.items()}}
    c, dirty = p4b.git_commit(); out.update({"commit": c, "code_dirty": dirty,
                                             "code_fingerprint": p4b.sha256(Path(p4b.__file__), 16),
                                             "written": datetime.now(timezone.utc).isoformat()})
    path = RUNS / "e11_pilota.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("first_within_1pct", "U", "U_doubled", "adequacy_order_same_at_U_and_2U",
                                          "expected_halfwidth_points", "halfwidth_blocks", "seconds")}, indent=1))
    print(f"pilot -> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- cost -------------------------------

def cost(args):
    U = args.updates; cks = [round(U * i / 11) for i in range(1, 12)]
    rows = []
    su_m = p4b.Setup("madrid", p4b.CITY["madrid"]["roads"], seed=0)
    A, _ = p4b.kernel_adjacency(su_m.al["graph"], su_m.kept)
    o = p4b.train(su_m, "G1", A, U=U, checkpoints=cks)
    rows.append({"what": "cost unit: G1, Madrid whole city (road graph), f = 40%", "K": su_m.K, "updates": U,
                 "seconds": round(o["seconds"], 1), "seconds_per_update": o["seconds"] / U})
    print(rows[-1], flush=True)
    city, tag = PILOT
    for arm in ARMS:
        su = p4b.Setup(city, graph_path(city, tag), seed=0)
        Aa = adjacency(su, arm)[0]
        o = p4b.train(su, arm, Aa, U=U, checkpoints=cks)
        rows.append({"what": f"E11 {arm}, {city} {tag}, seed 0", "K": su.K, "updates": U,
                     "seconds": round(o["seconds"], 1), "seconds_per_update": o["seconds"] / U})
        print(rows[-1], flush=True)
    import os
    out = {"machine": "Mac M3 Max, MPS, one process", "load_average_at_start": os.getloadavg(),
           "U": U, "checkpoints": cks, "rows": rows, "written": datetime.now(timezone.utc).isoformat()}
    c, dirty = p4b.git_commit(); out.update({"commit": c, "code_dirty": dirty})
    e11 = [r["seconds"] for r in rows[1:]]
    out["E11_campaign_estimate_hours"] = round(sum(e11) / 4 * 240 / 3600, 2)
    path = RUNS / "e11_costi.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    path.write_text(json.dumps(out, indent=1))
    print(f"cost -> {path} ({p4b.sha256(path, 16)}); E11 campaign ≈ {out['E11_campaign_estimate_hours']} h")
    return 0


def main():
    ap = argparse.ArgumentParser(description="E11 — preflight, pilot, cost")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("preflight")
    p = sp.add_parser("pilot"); p.add_argument("--length", type=int, default=8000)
    c = sp.add_parser("cost"); c.add_argument("--updates", type=int, required=True)
    a = ap.parse_args()
    return {"preflight": preflight, "pilot": pilot, "cost": cost}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
