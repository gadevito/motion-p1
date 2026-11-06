#!/usr/bin/env python3
"""
E9 — coverage curve (`protocol/paper4/E9.md`). Before the signature; no command here computes a test metric.
=============================================================================================================
    preflight   the E11 assertions adapted to whole cities and to every f, plus the E9 controls: road graph
                connected, grid equal to the rule, node sets (no empty set, shares within ±15 points, at least
                8 test blocks) for every (city, f, seed), geometry covariates written;
    pilot       G0 and G1 on Madrid, f = 40%, seed 0, 8,000 updates, validation every 250; U by the rule of
                E11; validation only;
    cost        one isolated run per arm (G0, G1, G1-rand(deg)) on Madrid, f = 40%, seed 0, U updates.

The shared pipeline `p4b.py` is used unchanged (frozen for E11). The campaign command is written after the
signature. Usage (from the worktree root):

    $PY paper4/code/e9.py preflight
    $PY paper4/code/e9.py pilot
    $PY paper4/code/e9.py cost --updates U
"""
import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
from e11 import Log, cadence_ok, block_halfwidth  # noqa: E402
from e9_potenza import grid_for_blocks  # noqa: E402

ROOT = p4b.ROOT
RUNS = ROOT / "paper4" / "runs"
PREREG = ROOT / "protocol" / "paper4" / "E9.md"
D = p4b.T4C
p4b.CITY.setdefault("london", {"targets": D / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
                               "sensors": D / "LONDON_2022/gomo_fmt/t4cmad_sensors.csv",
                               "roads": D / "LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl"})
CITIES = ("madrid", "london", "melbourne")
LEVELS = (0.1, 0.2, 0.4, 0.6)
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("G0", "G1", "G1-rand(deg)")
GRID = {"madrid": 11, "london": 11, "melbourne": 15}       # E9.md, Grid: the rule computed on 2026-11-06
MIN_TEST_BLOCKS = 8


def targets(f):
    return (f, 0.2, 0.8 - f)


def setup(city, f, seed):
    return p4b.Setup(city, p4b.CITY[city]["roads"], seed=seed, grid=GRID[city], targets=targets(f))


def adjacency(su, arm):
    g1 = su.al["graph"]
    if arm == "G0":
        return None, {}
    if arm == "G1":
        A, sg = p4b.kernel_adjacency(g1, su.kept)
        return A, {"sigma": sg, "edges": g1.number_of_edges()}
    h, info = p4b.randomise_degree(g1, su.seed)
    A, sg = p4b.kernel_adjacency(h, su.kept)
    info.update({"sigma": sg, "edges": h.number_of_edges(), "connected": nx.is_connected(h),
                 "mean_geo_length_m": float(p4b.geo_lengths(h, su.kept, su.al["coords"]).mean())})
    return A, info


def preflight(args):
    RUNS.mkdir(parents=True, exist_ok=True)
    log = Log(RUNS / "e9_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E9 preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(__file__), 16)} · "
        f"torch {torch.__version__} · mps {torch.backends.mps.is_available()}")

    # graphs and grid ------------------------------------------------------------------------------------
    g_ok, grid_ok, lines = True, True, []
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); g = al["graph"]
        G = grid_for_blocks(al["coords"], MIN_TEST_BLOCKS)
        g_ok &= nx.is_connected(g); grid_ok &= G == GRID[city]
        lines.append(f"{city:9s} K {len(al['kept'])}, edges {g.number_of_edges()}, self-loops removed {al['loops_removed']}, "
                     f"connected {nx.is_connected(g)}, grid by the rule {G} (declared {GRID[city]})")
    for ln in lines:
        log("        " + ln)
    log.check("graph", "road graph connected after alignment in the three cities; self-loops removed and logged", g_ok)
    log.check("grid", "grid of each city equal to the rule (smallest G ≥ 6 with ≥ 8 test blocks, no empty set, "
              "shares within ±15 for every f and seed)", grid_ok)

    # node sets and covariates for every (city, f, seed) --------------------------------------------------
    bad, geo = 0, {}
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); cells = p4b.grid_cells(al["coords"], GRID[city])
        for f in LEVELS:
            t = np.array(targets(f))
            for s in SEEDS:
                lab = p4b.node_sets(cells, s, targets=tuple(t)); n = np.bincount(lab, minlength=3)
                tb = len(np.unique(cells[lab == 2]))
                bad += int((n == 0).any() or np.abs(n / n.sum() - t).max() > 0.15 or tb < MIN_TEST_BLOCKS)
                gr = p4b.geometry_record(al["coords"], cells, GRID[city], lab); gr["test_blocks"] = tb
                geo[f"{city} {f:.1f} seed {s}"] = gr
    (RUNS / "e9_insiemi_geometria.json").write_text(json.dumps(geo, indent=1))
    log.check("sets", "no empty set, shares within ±15 points and ≥ 8 test blocks for every (city, f, seed) (60 pairs)",
              bad == 0, f"{bad} of 60 outside; covariates in e9_insiemi_geometria.json")

    su = setup("madrid", 0.4, 0)
    log(f"configuration madrid f = 40%, seed 0: K = {su.K}, grid {su.G}x{su.G}, shares {json.dumps(su.shares())}, "
        f"origins nominal {su.n_nominal} admissible {su.n_admissible} → train {len(su.tr)} val {len(su.va)} "
        f"test {len(su.te)}, purged {su.purged}")

    # 1 --------------------------------------------------------------------------------------------------
    whole = all(len(np.unique(su.lab[su.cells == c])) == 1 for c in np.unique(su.cells))
    log.check("1a", "three node sets disjoint, non-empty, unions of whole cells", whole and su.obs.any() and su.val.any()
              and su.test.any(), f"observed {int(su.obs.sum())}, validation-hidden {int(su.val.sum())}, test-hidden {int(su.test.sum())}")
    r = p4b.rng(0, p4b.K_MASKS); bm = bt_ = 0; hidden = torch.as_tensor(~su.obs, device=su.dev)
    for _ in range(100):
        inp, tgt, _ = su.batch_mask(r)
        bm += int((inp & ~su.obs).sum() + (tgt & ~su.obs).sum())
        x, y, m = su.batch(su.tr[:32], inp, tgt)
        bt_ += int(x[:, :4][:, :, hidden].abs().sum().item() > 0) + int(x[:, 10][:, hidden].abs().sum().item() > 0) \
            + int(m[:, hidden].abs().sum().item() > 0)
    log.check("1b", "no hidden index in the input or loss mask of 100 batches", bm == 0)
    log.check("1c", "hidden nodes zero in the dynamic input channels, flag channel and loss tensor", bt_ == 0)

    # 2, 3 -----------------------------------------------------------------------------------------------
    allo = np.concatenate([su.tr, su.va, su.te]); gap = max(p4b.HORIZONS) + p4b.T_IN - 1
    log.check("2a", "every origin admissible", all(cadence_ok(su.ts, int(t)) for t in allo),
              f"{len(allo)} origins; {su.n_nominal - su.n_admissible} nominal origins excluded")
    log.check("2b", "no target of a period overlaps an input of the next",
              bool(su.tr.max() + gap < su.va.min() and su.va.max() + gap < su.te.min()))
    bt = su.tr[100:132]; inp, tgt, _ = su.batch_mask(p4b.rng(0, 99)); x0, _, _ = su.batch(bt, inp, tgt)
    sv = {k: getattr(su, k).clone() for k in ("Rf", "FL", "OC", "HAs")}; tmax = int(bt.max())
    gen = torch.Generator(device="cpu").manual_seed(7)
    for k in sv:
        t_ = getattr(su, k); t_[tmax + 1:] = torch.randn(t_[tmax + 1:].shape, generator=gen).to(su.dev)
    x1, _, _ = su.batch(bt, inp, tgt)
    for k, v in sv.items():
        setattr(su, k, v)
    log.check("2c", "causality: noise after the origin leaves the inputs identical to the bit", bool(torch.equal(x0, x1)))
    pert = copy.copy(su); nz = np.random.default_rng(11)
    for k in ("r", "flow", "occ"):
        a = getattr(su, k).copy(); a[su.reg_end:] = nz.normal(size=a[su.reg_end:].shape)
        a[:, ~su.obs] = nz.normal(size=a[:, ~su.obs].shape); setattr(pert, k, a)
    C2 = su.C.copy(); C2[su.reg_end:] = nz.integers(1, 4, size=C2[su.reg_end:].shape)
    C2[:, ~su.obs] = nz.integers(1, 4, size=C2[:, ~su.obs].shape); pert.C = C2; pert._stats()
    log.check("2d", "noise after the training period and on hidden nodes leaves class weights, normalisation and "
              "historical average identical to the bit",
              bool(np.array_equal(pert.W, su.W) and [pert.fmu, pert.fsd, pert.omu, pert.osd] == [su.fmu, su.fsd, su.omu, su.osd]
                   and np.array_equal(pert.HA, su.HA)))
    f_ = np.bincount(su.C[:su.reg_end][:, su.obs].ravel(), minlength=4)[1:].astype("float64")
    log.check("3", "class weights recomputed independently from observed training cells",
              bool(np.array_equal((f_.sum() / (np.maximum(f_, 1) * 3)).astype("float32"), su.W)),
              f"W = {np.round(su.W, 4).tolist()}")

    # 5, 5-bis on the road graphs --------------------------------------------------------------------------
    g5 = w5 = True; info0 = {}
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); g1 = al["graph"]
        _, s1 = p4b.kernel_adjacency(g1, al["kept"]); w1 = np.array(sorted(a["weight"] for *_, a in g1.edges(data=True)))
        for s in SEEDS:
            h, info = p4b.randomise_degree(g1, s)
            g5 &= dict(h.degree()) == dict(g1.degree()) and nx.is_connected(h) and nx.number_of_selfloops(h) == 0
            wh = np.array(sorted(a["weight"] for *_, a in h.edges(data=True))); _, sh = p4b.kernel_adjacency(h, al["kept"])
            w5 &= bool(np.array_equal(wh, w1) and wh.sum() == w1.sum() and sh == s1)
            if s == 0:
                info0[city] = info
    log.check("5", "G1-rand(deg): same degree sequence node by node, connected and simple (3 cities × 5 seeds)", g5,
              json.dumps(info0))
    log.check("5-bis", "G1-rand(deg) weights a permutation of G1's: multisets, sums and σ identical", w5)

    # 6 ----------------------------------------------------------------------------------------------------
    fps = []
    for arm in ARMS:
        s_arm = setup("madrid", 0.4, 0); adjacency(s_arm, arm); fps.append(s_arm.fingerprints())
    log.check("6", "node sets, origins, class weights, normalisation and historical average identical across arms",
              all(fp == fps[0] for fp in fps), json.dumps(fps[0]))

    # 7, 8, 9, determinism, guards -----------------------------------------------------------------------
    A1 = adjacency(su, "G1")[0]
    out = p4b.train(su, "G1", A1, U=30, checkpoints=[10, 20, 30])
    log.check("7a", "optimiser updates equal U (30) exactly; no hidden node ever in a batch",
              out["updates"] == 30 and out["hidden_in_batches"] == 0)
    P, Y = p4b.predict(out["net"], su, out["A"], su.va, su.obs, su.val)
    log.check("7b", "validation evaluates all admissible validation origins × validation-hidden nodes",
              P.shape[0] == len(su.va) and int((Y[:, ~su.val] >= 0).sum()) == 0, f"{len(su.va)} × {int(su.val.sum())}")
    d = RUNS / "e9_preflight_cells"; d.mkdir(exist_ok=True)
    np.savez_compressed(d / "val_G1_s0.npz", p=P, y=Y, origins=su.va)
    z = np.load(d / "val_G1_s0.npz")
    log.check("8", "per-cell file reconstructs the aggregate wCE within 1e-9",
              abs(p4b.wce_np(z["p"], z["y"], su.W) - out["trajectory"][-1]["val_wce"]) < 1e-9)
    cfg = {"preflight": "E9 run-dir test", "stamp": datetime.now(timezone.utc).isoformat()}
    p4b.run_dir(RUNS / "e9_preflight_dirs", cfg)
    try:
        p4b.run_dir(RUNS / "e9_preflight_dirs", cfg); blocked = False
    except FileExistsError:
        blocked = True
    log.check("9", "an existing run folder blocks the launch", blocked)
    out2 = p4b.train(su, "G1", A1, U=30, checkpoints=[10, 20, 30])
    dmax = max(float((out["net"].state_dict()[k].float() - out2["net"].state_dict()[k].float()).abs().max())
               for k in out["net"].state_dict())
    log(f"[INFO] det    two identical G1 runs (30 updates, Madrid whole city): max |Δ parameter| = {dmax:.3e}"
        + (" (bitwise identical)" if dmax == 0 else " (residual MPS non-determinism, declared)"))
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E9 signature line is blank", guard)
    log(f"PREFLIGHT: {log.fail} failure(s)")
    log.save()
    return 0 if log.fail == 0 else 1


def pilot(args):
    path = RUNS / "e9_pilota.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    su = setup("madrid", 0.4, 0); L = 8000; cks = list(range(0, L + 1, 250)); res = {}
    for arm in ("G0", "G1"):
        res[arm] = p4b.train(su, arm, adjacency(su, arm)[0], U=L, checkpoints=cks, log=print)
    first = {}
    for arm, o in res.items():
        v = np.array([x["val_wce"] for x in o["trajectory"]]); u = np.array([x["update"] for x in o["trajectory"]])
        first[arm] = int(u[np.argmax(v <= 1.01 * v.min())])
    U = int(np.ceil(max(first.values()) / 500) * 500)
    def order(k):
        a = next(x["val_wce"] for x in res["G0"]["trajectory"] if x["update"] == k)
        b = next(x["val_wce"] for x in res["G1"]["trajectory"] if x["update"] == k)
        return "G0<G1" if a < b else "G1<=G0"
    doubled = order(U) != order(2 * U)
    if doubled:
        U *= 2
    adequate = 2 * U <= L and order(U) == order(2 * U)
    for arm, o in res.items():
        o["net"].load_state_dict(o["states"][U])
    pa = p4b.predict(res["G1"]["net"], su, res["G1"]["A"], su.va, su.obs, su.val)
    pb = p4b.predict(res["G0"]["net"], su, res["G0"]["A"], su.va, su.obs, su.val)
    hw, nb = block_halfwidth(pa[0], pb[0], pb[1], su.cells, su.val, su.W)
    c, dirty = p4b.git_commit()
    out = {"protocol": "protocol/paper4/E9.md", "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "configuration": "madrid whole city, f = 40%", "seed": 0, "grid": su.G, "K": su.K, "shares": su.shares(),
           "geometry": su.geometry(), "fingerprints": su.fingerprints(), "length": L, "evaluation_every": 250,
           "first_within_1pct": first, "U": U, "U_doubled": doubled, "adequacy_order_same_at_U_and_2U": adequate,
           "expected_halfwidth_points": round(hw, 3), "halfwidth_blocks": nb,
           "trajectories": {a: o["trajectory"] for a, o in res.items()}, "seconds": {a: o["seconds"] for a, o in res.items()},
           "commit": c, "code_dirty": dirty, "code_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("first_within_1pct", "U", "U_doubled", "adequacy_order_same_at_U_and_2U",
                                          "expected_halfwidth_points", "halfwidth_blocks")}, indent=1))
    print(f"pilot -> {path} ({p4b.sha256(path, 16)})")
    return 0


def cost(args):
    import os
    path = RUNS / "e9_costi.json"
    if path.exists():
        raise FileExistsError(f"{path} exists")
    U = args.updates; cks = [round(U * i / 11) for i in range(1, 12)]; rows = []
    load0 = os.getloadavg()
    for arm in ARMS:
        su = setup("madrid", 0.4, 0)
        o = p4b.train(su, arm, adjacency(su, arm)[0], U=U, checkpoints=cks)
        rows.append({"arm": arm, "K": su.K, "updates": U, "seconds": round(o["seconds"], 1),
                     "seconds_per_update": o["seconds"] / U})
        print(rows[-1], flush=True)
    c, dirty = p4b.git_commit()
    out = {"machine": "Mac M3 Max, MPS, one process", "load_average_at_start": load0, "U": U, "rows": rows,
           "commit": c, "code_dirty": dirty, "written": datetime.now(timezone.utc).isoformat(),
           "note": "Madrid is the largest city; London (774 nodes) and Melbourne (587) cost at most as much"}
    out["E9_campaign_estimate_hours_upper"] = round(sum(r["seconds"] for r in rows) * 4 * 5 * 3 / 3600, 2)
    path.write_text(json.dumps(out, indent=1))
    print(f"cost -> {path} ({p4b.sha256(path, 16)}); E9 campaign ≤ {out['E9_campaign_estimate_hours_upper']} h")
    return 0


def main():
    ap = argparse.ArgumentParser(description="E9 — preflight, pilot, cost")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("preflight"); sp.add_parser("pilot")
    c = sp.add_parser("cost"); c.add_argument("--updates", type=int, required=True)
    a = ap.parse_args()
    return {"preflight": preflight, "pilot": pilot, "cost": cost}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
