#!/usr/bin/env python3
"""
E10-pred — does placement change what is forecastable on the uncovered segments? (`protocol/paper4/E10pred.md`)
==============================================================================================================
Imports `p4b.py`, `e9.py`, the resample of `genera_congelamento_e9.py` and the per-node sums of
`genera_congelamento_e11.py` unchanged. The only new rule is the uniform node set:

  observed        round(0.2·K) segments drawn uniformly with default_rng([seed, 7]) (streams 1-6 of p4b unchanged)
  validation/test the remaining segments, in whole cells of E9's grid, by E9's deficit rule on 0.2·K and 0.6·K, in
                  the order of stream 1

The Setup is E9's (f = 20%) with its node sets replaced; every statistic that depends on them (class weights,
normalisation, historical mean, observed cells) is recomputed by p4b's own methods. Per-batch input masks are
p4b's; their realised share of observed segments in input is recorded for every batch (wrapper on the instance,
p4b unchanged), and recomputed for the E9 runs by replaying their mask stream (default_rng([seed, 2])).

    selftest      uniform node-set rule on synthetic cells; mask-share replay equals the recorded shares
    preflight     controls 1-7 of E10pred.md, reading no test target
    cost          one isolated run per arm (G0, G1) on Madrid, seed 0, uniform placement, U = 1,000
    run           after the signature: 3 cities × 5 seeds × (G0, G1), U = 1,000, E9's checkpoints and selection;
                  thresholds on validation saved with fingerprint; per-cell predictions as in E9
    check-inputs  after run: 30 folders, fingerprints, code, keys (no metric read)
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E10pred.md and e10pred_risultati.json

Usage: $PY paper4/code/e10pred.py selftest | preflight | cost | run [--only city:seed:arm] | check-inputs
       | selftest-e2e <tmpdir> | freeze
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
from e12bis import v_cell, summary, MARGIN  # noqa: E402
from genera_congelamento_e9 import runs_by_key, B, BOOT  # noqa: E402
from genera_congelamento_e11 import node_sums, wce_from  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E10pred.md"
RUNS = e9.RUNS / "e10pred"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
F = 0.2
U = 1000
CHECKPOINTS = [round(U * i / 11) for i in range(1, 12)]
ARMS = ("G0", "G1")
K_UNIFORM = 7
ISOLATED = {"G0": 89.0, "G1": 169.0}                        # E9.md, cost table (Madrid, f = 40%), seconds


# ---------------------------------------------------------------- node sets ----------------------------

def uniform_sets(cells, K, seed, f=F):
    """Label per node (0 observed, 1 validation-hidden, 2 test-hidden): observed uniform with stream 7; the rest in
    whole cells by deficit on (0.2·K, (0.8 − f)·K), cell order from stream 1."""
    lab = np.full(K, -1, np.int8)
    obs = p4b.rng(seed, K_UNIFORM).choice(K, int(round(f * K)), replace=False)
    lab[obs] = 0
    rest = lab < 0
    order = p4b.rng(seed, p4b.K_SETS).permutation(np.unique(cells[rest]))
    tgt = np.array([0.2, 0.8 - f]) * K; cur = np.zeros(2)
    for c in order:
        sel = (cells == c) & rest
        j = int(np.argmax(tgt - cur))
        lab[sel] = 1 + j; cur[j] += sel.sum()
    return lab


def uniform_setup(city, seed):
    """E9's Setup at f = 20% with the node sets replaced by the uniform rule; statistics recomputed."""
    su = e9.setup(city, F, seed)
    su.lab = uniform_sets(su.cells, su.K, seed)
    su.obs, su.val, su.test = (su.lab == 0), (su.lab == 1), (su.lab == 2)
    su.obs_cells = np.unique(su.cells[su.obs])
    su._stats(); su._tensors()
    return su


def record_masks(su):
    """Wrap su.batch_mask on the instance: the realised share of observed segments in input, per batch."""
    shares = []; orig = su.batch_mask

    def wrapped(r):
        inp, tgt, u = orig(r)
        shares.append(float(inp.sum() / su.obs.sum()))
        return inp, tgt, u
    su.batch_mask = wrapped
    return shares


def replay_masks(su, seed, n=U):
    """The input masks p4b.train draws for `seed`, without training: stream K_MASKS consumed only by batch_mask."""
    r = p4b.rng(seed, p4b.K_MASKS)
    return [float(su.batch_mask(r)[0].sum() / su.obs.sum()) for _ in range(n)]


def mask_summary(x):
    x = np.asarray(x); return {"mean": float(x.mean()), "p5": float(np.percentile(x, 5)), "p95": float(np.percentile(x, 95))}


def design_record(su):
    geo = su.geometry()
    return {"median_test_to_observed_m": geo["test_to_nearest_observed_m"]["median"],
            "cells_with_observed": int(len(su.obs_cells)), "test_blocks": int(len(np.unique(su.cells[su.test]))),
            "shares": su.shares(), "counts": geo["counts"]}


# ---------------------------------------------------------------- self-test ----------------------------

def selftest():
    ok = True
    g = np.random.default_rng(0)
    for K, G in ((828, 11), (587, 15), (97, 6)):
        coords = g.uniform(0, 5000, (K, 2)); cells = p4b.grid_cells(coords, G)
        for seed in range(3):
            lab = uniform_sets(cells, K, seed)
            ok &= bool((lab >= 0).all())
            ok &= (lab == 0).sum() == int(round(F * K))
            for c in np.unique(cells[lab > 0]):                     # hidden labels constant within a cell
                ok &= len(np.unique(lab[(cells == c) & (lab > 0)])) == 1
            ok &= bool(np.array_equal(lab, uniform_sets(cells, K, seed)))
            sh = np.bincount(lab, minlength=3) / K
            ok &= abs(sh[1] - 0.2) < 0.1 and abs(sh[2] - 0.6) < 0.1
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def code_fp():
    here = Path(__file__).resolve().parent
    return {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
            "genera_congelamento_e9.py": p4b.sha256(here / "genera_congelamento_e9.py", 16),
            "genera_congelamento_e11.py": p4b.sha256(here / "genera_congelamento_e11.py", 16),
            "e10pred.py": p4b.sha256(Path(__file__), 16)}


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e10pred_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E10-pred preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, by = runs_by_key(E9RUNS)
    sets_ok = leak_ok = streams_ok = e9_ok = common_ok = True; info = {}
    for city in e9.CITIES:
        for s in e9.SEEDS:
            su = uniform_setup(city, s); ref = e9.setup(city, F, s)
            K = su.K; n = np.bincount(su.lab, minlength=3)
            sets_ok &= abs(n[0] / K - F) <= 0.005 and n.sum() == K and (su.lab >= 0).all()
            for cc in np.unique(su.cells[su.lab > 0]):
                sets_ok &= len(np.unique(su.lab[(su.cells == cc) & (su.lab > 0)])) == 1
            # streams: origins, cells and the mask stream are E9's; only the observed draw differs
            streams_ok &= bool(np.array_equal(su.tr, ref.tr) and np.array_equal(su.va, ref.va) and np.array_equal(su.te, ref.te)
                               and np.array_equal(su.cells, ref.cells))
            # no hidden index in input or loss, on 200 batches of the mask stream
            r = p4b.rng(s, p4b.K_MASKS)
            for _ in range(200):
                inp, tgt, _u = su.batch_mask(r)
                leak_ok &= not (inp & ~su.obs).any() and not (tgt & ~su.obs).any()
            leak_ok &= float(su.HA[~su.obs].sum()) == 0.0
            # E9 runs at f = 20% present, files with the fingerprints of their run records
            for arm in ARMS:
                rec = by.get((city, F, s), {}).get(arm)
                if rec is None:
                    e9_ok = False; continue
                d = E9RUNS / rec["config_fingerprint"]
                for k, v in rec["files"].items():
                    e9_ok &= p4b.sha256(d / v["file"], 16) == v["sha256"]
                e9_ok &= rec["setup"] == ref.fingerprints()
            common = su.test & ref.test
            nb = len(np.unique(su.cells[common]))
            common_ok &= common.sum() > 0
            if s == 0:
                info[city] = {"uniform": design_record(su), "blocks": design_record(ref), "common_segments": int(common.sum()),
                              "common_blocks": nb, "mask_share_uniform": mask_summary(replay_masks(su, s, 200)),
                              "mask_share_blocks": mask_summary(replay_masks(ref, s, 200))}
            else:
                info[city]["common_blocks_seed" + str(s)] = nb
    log.check("1", "uniform node sets: observed share 0.2 ± 0.005 of K; validation and test unions of whole cells; the three "
              "sets disjoint and covering K (3 cities × 5 seeds)", sets_ok)
    log.check("2", "no hidden index in input or loss on 200 batches of the mask stream; historical mean zero on hidden "
              "segments (3 × 5)", leak_ok)
    log.check("3", "origins and grid cells identical to E9's setup; the mask stream is E9's (k = 2); only the observed draw "
              "(k = 7) differs", streams_ok)
    log.check("4", "E9 runs at f = 20% (G0, G1) present for the 15 (city, seed), files with the fingerprints of their run "
              "records, setup equal to E9's", e9_ok)
    log.check("5", "the common test-hidden set (uniform ∩ blocks) is non-empty in every (city, seed)", common_ok)
    sel = selftest() == 0
    log.check("5b", "uniform rule on synthetic grids: deterministic, shares, whole hidden cells (selftest)", sel)
    su = uniform_setup("madrid", 0); A, _ = e9.adjacency(su, "G1")
    o1 = p4b.train(su, "G1", A, U=30, checkpoints=[10, 20, 30]); o2 = p4b.train(uniform_setup("madrid", 0), "G1", A, U=30,
                                                                              checkpoints=[10, 20, 30])
    dmax = max(float((o1["net"].state_dict()[k].float() - o2["net"].state_dict()[k].float()).abs().max())
               for k in o1["net"].state_dict())
    log.check("6", f"no hidden segment in the 30 training batches (hidden_in_batches = {o1['hidden_in_batches']}); two "
              f"identical G1 runs give max |Δ parameter| = {dmax:.3e}", o1["hidden_in_batches"] == 0 and dmax < 1e-4)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("7", "test metrics refused while the E10-pred signature line is blank; the run saves the validation "
              "thresholds with fingerprint before predicting test", guard)
    log("descriptive, seed 0 (no target read): per design, median distance test-hidden → observed, cells with an observed "
        "segment, test blocks, realised share of observed segments in input over 200 batches; common segments and blocks:")
    for city, v in info.items():
        log(f"  {city}: {json.dumps(v)}")
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def cost(args):
    import os
    path = e9.RUNS / "e10pred_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    rows = []; load0 = os.getloadavg()
    for arm in ARMS:
        su = uniform_setup("madrid", 0)
        o = p4b.train(su, arm, e9.adjacency(su, arm)[0], U=U, checkpoints=CHECKPOINTS)
        rows.append({"arm": arm, "K": su.K, "updates": U, "seconds": round(o["seconds"], 1)}); print(rows[-1], flush=True)
    out = {"machine": "Mac M3 Max, MPS, one process", "load_average_at_start": load0, "load_average_at_end": os.getloadavg(),
           "rows": rows, "campaign_estimate_hours_upper": round(sum(r["seconds"] for r in rows) * 15 / 3600, 2),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def one_run(city, seed, arm):
    cfg = {"experiment": "E10-pred", "city": city, "f": F, "seed": seed, "arm": arm, "U": U, "checkpoints": CHECKPOINTS,
           "grid": e9.GRID[city], "observed": "uniform, stream 7", "frozen_code": {k: v for k, v in code_fp().items()
                                                                                   if k != "e10pred.py"}}
    d = RUNS / p4b.fingerprint(cfg)
    if (d / "run.json").exists():
        return "skipped", d
    if d.exists():
        raise SystemExit(f"STOP: {d} exists without run.json: interrupted run, to be reported, not repaired")
    d.mkdir(parents=True)
    t0 = time.perf_counter()
    su = uniform_setup(city, seed); shares = record_masks(su)
    A, info = e9.adjacency(su, arm)
    o = p4b.train(su, arm, A, U=U, checkpoints=CHECKPOINTS)
    if o["updates"] != U or o["hidden_in_batches"] != 0 or len(shares) != U:
        raise SystemExit(f"STOP: {city} s{seed} {arm}: updates {o['updates']}, hidden {o['hidden_in_batches']}, masks {len(shares)}")
    if not (0.2 * ISOLATED[arm] <= o["seconds"] <= 10 * ISOLATED[arm]):
        raise SystemExit(f"STOP: {city} s{seed} {arm}: training time {o['seconds']:.1f} s outside [0.2x, 10x] of {ISOLATED[arm]} s")
    o["net"].load_state_dict(o["states"][o["selected"]])
    files = {}
    P, Y = p4b.predict(o["net"], su, o["A"], su.va, su.obs, su.val)
    np.savez_compressed(d / "val_hidden.npz", p=P.astype("float32"), y=Y.astype("int8"), origins=su.va.astype("int32"),
                        nodes=np.where(su.val)[0].astype("int32"))
    files["val_hidden"] = {"file": "val_hidden.npz", "sha256": p4b.sha256(d / "val_hidden.npz", 16)}
    vn = np.where(su.val)[0]; pv = P[:, vn][..., 2]; yv = Y[:, vn]; neg = pv[(yv >= 0) & (yv != 2)]
    (d / "thresholds.json").write_text(json.dumps({"red_5pct_fa": float(np.quantile(neg, 0.95)) if neg.size else 1.0}))
    (d / "thresholds.fingerprint").write_text(json.dumps({"sha256": p4b.sha256(d / "thresholds.json", 16),
                                                         "written": datetime.now(timezone.utc).isoformat()}))
    p4b.require_signed(PREREG)
    for name, origins, tgt in (("test_hidden", su.te, su.test), ("test_observed", su.te, su.obs)):
        P, Y = p4b.predict(o["net"], su, o["A"], origins, su.obs, tgt)
        np.savez_compressed(d / f"{name}.npz", p=P.astype("float32"), y=Y.astype("int8"), origins=origins.astype("int32"),
                            nodes=np.where(tgt)[0].astype("int32"))
        files[name] = {"file": f"{name}.npz", "sha256": p4b.sha256(d / f"{name}.npz", 16)}
    ref = e9.setup(city, F, seed)
    rec = {"config": cfg, "config_fingerprint": p4b.fingerprint(cfg), "K": su.K, "grid": su.G, "design": design_record(su),
           "design_blocks_e9": design_record(ref), "lab_fingerprint": p4b.fingerprint(su.lab), "setup": su.fingerprints(),
           "class_weights": su.W.tolist(), "mask_share": mask_summary(shares), "mask_share_e9_replay": mask_summary(replay_masks(ref, seed)),
           "mask_shares": shares, "graph": info, "trajectory": o["trajectory"], "selected_update": o["selected"],
           "init_seed": o["init_seed"], "train_seconds": o["seconds"], "run_seconds": time.perf_counter() - t0,
           "thresholds_sha256": p4b.sha256(d / "thresholds.json", 16), "files": files, "code": code_fp()}
    p4b.record(d, rec)
    return "done", d


def run(args):
    p4b.require_signed(PREREG); RUNS.mkdir(parents=True, exist_ok=True)
    plan = [(c, s, a) for c in e9.CITIES for s in e9.SEEDS for a in ARMS]
    if args.only:
        c, s, a = args.only.split(":"); plan = [(c, int(s), a)]
    for k, (c, s, a) in enumerate(plan, 1):
        st, d = one_run(c, s, a)
        print(f"{datetime.now(timezone.utc).isoformat()} [{k}/{len(plan)}] {st} {c} seed {s} {a} -> {d.name}", flush=True)
    return 0


# ---------------------------------------------------------------- freeze -------------------------------

def load(runs_dir):
    """{(city, seed, arm): (record, test_hidden arrays)} for the uniform design and the E9 design at f = 20%."""
    _, byu = runs_by_key(runs_dir); _, by9 = runs_by_key(E9RUNS); out = {}
    for city in e9.CITIES:
        for s in e9.SEEDS:
            for arm in ARMS:
                for design, by, base in (("uniform", byu, runs_dir), ("blocks", by9, E9RUNS)):
                    rec = by[(city, F, s)][arm]; d = Path(base) / rec["config_fingerprint"]
                    if p4b.sha256(d / "test_hidden.npz", 16) != rec["files"]["test_hidden"]["sha256"]:
                        raise SystemExit(f"STOP: {d}/test_hidden.npz fingerprint differs")
                    z = np.load(d / "test_hidden.npz")
                    out[(design, city, s, arm)] = (rec, z["p"], z["y"], z["nodes"])
    return out


_CELLS = {}


def city_cells(city):
    """Grid cells of the segments (they depend on the coordinates and the grid only, not on the seed)."""
    if city not in _CELLS:
        _CELLS[city] = e9.setup(city, F, 0).cells
    return _CELLS[city]


def cell_for(data, city, design_arms, nodes_of=None):
    """Seeds × arms of per-node sums (global node indices); nodes_of(s) restricts to a node set (the common
    segments). Every arm of a seed uses the same nodes, in the same order."""
    cell = {"seeds": {}}
    for s in e9.SEEDS:
        arms = {}; keep = None
        for name, (design, arm) in design_arms.items():
            rec, p, y, nodes = data[(design, city, s, arm)]
            k = nodes if nodes_of is None else np.intersect1d(nodes, nodes_of(s))
            if keep is not None and not np.array_equal(k, keep):
                raise SystemExit(f"STOP: {city} s{s}: arms of one cell on different nodes")
            keep = k
            S, Wn, *_ = node_sums(p, y, keep, rec["class_weights"])
            arms[name] = (S, Wn)
        cell["seeds"][s] = {"blocks": city_cells(city)[keep], "arms": arms}
    return cell


def freeze(args, runs_dir=None):
    runs_dir = Path(runs_dir or RUNS)
    if (OUT / "CONGELAMENTO_E10pred.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E10pred.md exists; regenerate only on purpose, after moving it")
    data = load(runs_dir); rows = {}
    for ci, city in enumerate(e9.CITIES):
        g = [BOOT, 100 + ci]
        cu = cell_for(data, city, {"G0": ("uniform", "G0"), "G1": ("uniform", "G1")})
        cb = cell_for(data, city, {"G0": ("blocks", "G0"), "G1": ("blocks", "G1")})
        row = {"V_uniform": summary(*v_cell(cu, np.random.default_rng(g), "G1")),
               "V_blocks": summary(*v_cell(cb, np.random.default_rng(g), "G1")),
               "V_uniform_per_horizon": {f"{15 * h} min": summary(*v_cell(cu, np.random.default_rng(g), "G1", hz=k))
                                         for k, h in enumerate(p4b.HORIZONS)},
               "wce": {d_: {a: float(np.mean([wce_from(*c["seeds"][s]["arms"][a]) for s in e9.SEEDS])) for a in ARMS}
                       for d_, c in (("uniform", cu), ("blocks", cb))}}
        common = lambda s: np.intersect1d(data[("uniform", city, s, "G1")][3], data[("blocks", city, s, "G1")][3])  # noqa: E731
        cc = cell_for(data, city, {"G1u": ("uniform", "G1"), "G1b": ("blocks", "G1"), "G0u": ("uniform", "G0"),
                                   "G0b": ("blocks", "G0")}, nodes_of=common)
        nb = [len(np.unique(cc["seeds"][s]["blocks"])) for s in e9.SEEDS]
        row["common"] = {"segments": [int(len(cc["seeds"][s]["blocks"])) for s in e9.SEEDS], "min_blocks": int(min(nb)),
                         "delta_G1": summary(*v_cell(cc, np.random.default_rng(g + [1]), "G1u", ref="G1b")),
                         "delta_G0": summary(*v_cell(cc, np.random.default_rng(g + [1]), "G0u", ref="G0b"))}
        if min(nb) < 3:
            row["common"]["note"] = "fewer than 3 common blocks in some seed: no interval read"
        recs = [data[("uniform", city, s, a)][0] for s in e9.SEEDS for a in ARMS]
        row["design"] = {"uniform": {k: float(np.mean([r["design"][k] for r in recs])) for k in
                                     ("median_test_to_observed_m", "cells_with_observed", "test_blocks")},
                         "blocks": {k: float(np.mean([r["design_blocks_e9"][k] for r in recs])) for k in
                                    ("median_test_to_observed_m", "cells_with_observed", "test_blocks")},
                         "mask_share_uniform": float(np.mean([r["mask_share"]["mean"] for r in recs])),
                         "mask_share_blocks": float(np.mean([r["mask_share_e9_replay"]["mean"] for r in recs]))}
        rows[city] = row
    hits = [c for c, r in rows.items() if r["V_uniform"]["L"] > 0 and r["V_uniform"]["V"] >= MARGIN]
    if len(hits) >= 2:
        st = "placement changes what is forecastable (" + ", ".join(hits) + ")"
    elif all(r["V_uniform"]["U"] < MARGIN for r in rows.values()):
        st = "placement does not change what is forecastable"
    else:
        st = "undetermined"
    write(rows, st, hits)
    return 0


def write(rows, st, hits):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    res = {"rows": rows, "summary_statement": st, "cities_hit": hits, "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e10pred_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: f"{x:+.2f}"  # noqa: E731
    cv = lambda e: f"{fm(e['V'])} [{fm(e['L'])}; {fm(e['U'])}]"  # noqa: E731
    L = ["# CONGELAMENTO_E10pred — does placement change what is forecastable?\n",
         f"Generated by `paper4/code/e10pred.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E10pred.md` ({res['prereg_fingerprint']}). Inputs: 30 runs "
         f"under `paper4/runs/e10pred/` (uniform placement) and the E9 runs at f = 20% (blocks), fingerprints checked. V in "
         f"points of the G0 wCE, positive = G1 better. Intervals: 95%, {B} replicates, seeds × blocks.\n",
         f"## Summary statement\n\n**{st}** — cities where V(G1) with uniform placement is favourable and ≥ 3 points: "
         f"{len(hits)} of 3.\n", "## V(G1) by design, on each design's test-hidden segments\n",
         "| City | Uniform | Blocks (E9, f = 20%) | wCE G0 / G1, uniform | wCE G0 / G1, blocks |", "|---|---|---|---|---|"]
    for city, r in rows.items():
        w = r["wce"]
        L.append(f"| {city} | {cv(r['V_uniform'])} | {cv(r['V_blocks'])} | {w['uniform']['G0']:.4f} / {w['uniform']['G1']:.4f} | "
                 f"{w['blocks']['G0']:.4f} / {w['blocks']['G1']:.4f} |")
    L += ["\n## Secondary: the common test-hidden segments (hidden in both designs)\n",
          "Δ = 100·(wCE_blocks − wCE_uniform)/wCE_blocks, positive when uniform placement forecasts them better.\n",
          "| City | Segments per seed | Min blocks | Δ G1 | Δ G0 |", "|---|---|---|---|---|"]
    for city, r in rows.items():
        cm = r["common"]; mark = " *" if "note" in cm else ""
        L.append(f"| {city} | {' / '.join(map(str, cm['segments']))} | {cm['min_blocks']} | {cv(cm['delta_G1'])}{mark} | "
                 f"{cv(cm['delta_G0'])}{mark} |")
    L += ["\n## Reported without a criterion\n",
          "| City | Median test-hidden → observed (m), uniform / blocks | Cells with an observed segment, uniform / blocks | "
          "Test blocks, uniform / blocks | Share of observed in input per batch, uniform / blocks | V(G1) per horizon 15 / 30 / 60 / 120 min, uniform |",
          "|---|---|---|---|---|---|"]
    for city, r in rows.items():
        u, b = r["design"]["uniform"], r["design"]["blocks"]
        ph = " / ".join(fm(v["V"]) for v in r["V_uniform_per_horizon"].values())
        L.append(f"| {city} | {u['median_test_to_observed_m']:.0f} / {b['median_test_to_observed_m']:.0f} | "
                 f"{u['cells_with_observed']:.0f} / {b['cells_with_observed']:.0f} | {u['test_blocks']:.0f} / {b['test_blocks']:.0f} | "
                 f"{r['design']['mask_share_uniform']:.3f} / {r['design']['mask_share_blocks']:.3f} | {ph} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Node sets by the uniform rule (stream 7) on E9's grid and origins; no hidden segment in any training batch; "
          "validation thresholds saved with fingerprint before test predictions (checked by the run).",
          "2. The input masks under uniform placement are close to a uniform draw of observed segments; their realised share "
          "is recorded per batch and set against the replayed masks of E9 (table above)."]
    mp = OUT / "CONGELAMENTO_E10pred.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def check_inputs(args):
    recs, by = runs_by_key(RUNS); bad = []; code_now = code_fp()
    for city in e9.CITIES:
        for s in e9.SEEDS:
            for arm in ARMS:
                r = by.get((city, F, s), {}).get(arm)
                if r is None:
                    bad.append(f"{city} s{s} {arm}: missing"); continue
                d = RUNS / r["config_fingerprint"]
                for k, v in r["files"].items():
                    if p4b.sha256(d / v["file"], 16) != v["sha256"]:
                        bad.append(f"{d.name}: {k} fingerprint")
                th = p4b.sha256(d / "thresholds.json", 16)
                if th != r["thresholds_sha256"] or th != json.loads((d / "thresholds.fingerprint").read_text())["sha256"]:
                    bad.append(f"{d.name}: thresholds fingerprint")
                if r["code"] != code_now:
                    bad.append(f"{d.name}: code {r['code']}")
                if len(r["mask_shares"]) != U or set(r["files"]) != {"val_hidden", "test_hidden", "test_observed"}:
                    bad.append(f"{d.name}: masks or files")
    print(f"runs found: {len(recs)} of 30; inconsistencies: {len(bad)}")
    for b in bad[:20]:
        print("  -", b)
    ok = len(recs) == 30 and not bad
    print("CHECK-INPUTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest_e2e(args):
    """freeze end to end on synthetic folders, without the data: per-node sums are replaced by planted arrays.
    Uniform: G1 5% better than G0 in Madrid and London, equal in Melbourne; blocks: equal. The statement must name
    Madrid and London; V_uniform in Madrid must be 5."""
    global cell_for, load
    from e12bis import v_cell as vc
    g = np.random.default_rng(3)
    def fake_cell(city, design_arms, nodes_of=None):
        cell = {"seeds": {}}
        for s in e9.SEEDS:
            n = 40; W0 = g.uniform(50, 100, (n, 4)); S0 = W0 * 1.08; arms = {}
            for name, (design, arm) in design_arms.items():
                better = design == "uniform" and arm == "G1" and city != "melbourne"
                arms[name] = (S0 * (0.95 if better else 1.0), W0)
            cell["seeds"][s] = {"blocks": np.repeat(np.arange(10), 4), "arms": arms}
        return cell
    saved = (cell_for, load, globals()["OUT"])
    cell_for = lambda data, city, da, nodes_of=None: fake_cell(city, da, nodes_of)  # noqa: E731
    load = lambda runs_dir: {}  # noqa: E731
    tmp = Path(args.tmpdir); globals()["OUT"] = tmp
    rec = {"design": {"median_test_to_observed_m": 1.0, "cells_with_observed": 1.0, "test_blocks": 1.0},
           "design_blocks_e9": {"median_test_to_observed_m": 1.0, "cells_with_observed": 1.0, "test_blocks": 1.0},
           "mask_share": {"mean": 0.7}, "mask_share_e9_replay": {"mean": 0.7}}
    class D(dict):
        def __missing__(self, k):
            return (rec, None, None, np.arange(40))
    load = lambda runs_dir: D()  # noqa: E731
    try:
        freeze(None, runs_dir=tmp)
        res = json.loads((tmp / "e10pred_risultati.json").read_text())
    finally:
        cell_for, load, globals()["OUT"] = saved
    v = res["rows"]["madrid"]["V_uniform"]["V"]; st = res["summary_statement"]
    print(f"synthetic statement: {st}; V(G1) uniform in Madrid = {v:.4f} (expected 5)")
    ok = st == "placement changes what is forecastable (madrid, london)" and abs(v - 5) < 1e-9
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E10-pred")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("selftest", "preflight", "cost", "check-inputs", "freeze"):
        sp.add_parser(cmd)
    r = sp.add_parser("run"); r.add_argument("--only")
    e2 = sp.add_parser("selftest-e2e"); e2.add_argument("tmpdir")
    a = ap.parse_args()
    return {"selftest": lambda a: selftest(), "preflight": preflight, "cost": cost, "run": run, "freeze": freeze,
            "check-inputs": check_inputs, "selftest-e2e": selftest_e2e}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
