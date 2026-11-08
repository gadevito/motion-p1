#!/usr/bin/env python3
"""
E12-bis — calibrated neighbour (`protocol/paper4/E12bis.md`). No training.
===========================================================================
Imports `p4b.py`, `e9.py`, `e12.py` and the resample of `genera_congelamento_e9.py` unchanged.

    selftest    planted signal (copy within 250 m much stronger than beyond); tables, prediction, bins
    preflight   controls 1-6 of E12bis.md, reading no test target
    cost        tables and validation predictions for Madrid f = 40% seed 0, scaled to the test origins
    run         after the signature: per (city, f, seed) tables from observed->observed pairs in training,
                thresholds on validation saved with fingerprint, then per-node sums on test-hidden segments
    freeze      CONGELAMENTO_E12bis.md and e12bis_risultati.json from paper4/runs/e12bis/

Calibration table: for every observed segment i and training origin t, its nearest OTHER observed segment j
with a valid class at t; counts n(y_i(t+h) = a | y_j(t) = b, distance bin of d(i, j), h), bins 0-250, 250-500,
500-1,000, > 1,000 m. Prediction for a hidden segment: nearest observed segment with a valid class b at t, at
distance d; q = row (b, bin(d), h); empty row -> prior (counted); q' = 0.95 q + 0.05 prior; p ∝ W·q'.

Usage: $PY paper4/code/e12bis.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
       | selftest-e2e <tmpdir> | freeze [--compare-with J]
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
import e12  # noqa: E402
from e12 import neighbours, labels, sums, transform, training_stats, BINS, BIN_LABELS, EPS  # noqa: E402
from genera_congelamento_e11 import node_sums, wce_from, readings  # noqa: E402
from genera_congelamento_e9 import multiplicities, pick, runs_by_key  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12bis.md"
RUNS = e9.RUNS / "e12bis"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
H = p4b.HORIZONS
NB = len(BIN_LABELS)
B, BOOT, MARGIN = 4000, 20261106, 3.0
NAME = "E12-bis"


def bin_of(d):
    return np.clip(np.digitize(d, BINS[1:-1]), 0, NB - 1)


# ---------------------------------------------------------------- tables and prediction ----------------

def tables(C, obs_idx, coords, origins):
    """counts (NB, H, 3, 3): [bin, horizon, neighbour class b, own class a], from observed->observed pairs."""
    cnt = np.zeros((NB, len(H), 3, 3))
    order, dist = neighbours(coords, obs_idx, obs_idx)
    for ii, i in enumerate(obs_idx):
        keep = obs_idx[order[ii]] != i                       # exclude the segment itself
        cand = obs_idx[order[ii][keep]]; dd = dist[ii][keep]
        cobs = C[origins][:, cand]; valid = cobs > 0
        anyv = valid.any(1); first = valid.argmax(1)
        b = cobs[np.arange(len(origins)), first]; bn = bin_of(dd[first])
        for hi, h in enumerate(H):
            a = C[origins + h, i]
            m = anyv & (a > 0)
            np.add.at(cnt, (bn[m], hi, b[m] - 1, a[m] - 1), 1)
    return cnt


def q_node(C, origins, obs_idx, order_n, d_n, cnt, prior):
    cobs = C[origins][:, obs_idx[order_n]]; valid = cobs > 0
    anyv = valid.any(1); first = valid.argmax(1)
    b = cobs[np.arange(len(origins)), first]; bn = bin_of(d_n[first])
    q = np.zeros((len(origins), len(H), 3)); fb = 0
    for hi in range(len(H)):
        rows = cnt[bn, hi, np.clip(b - 1, 0, 2)]              # (T, 3)
        tot = rows.sum(1)
        ok = anyv & (tot > 0)
        q[ok, hi] = rows[ok] / tot[ok, None]
        q[~ok, hi] = prior; fb += int((~ok).sum())
    return q, fb


def predict_set(su, origins, tgt_mask, cnt, prior):
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    S, Wn, Su, Wu, pos, neg, fb = [], [], [], [], [], [], 0
    for i, n in enumerate(tgt_idx):
        y = labels(su.C, origins, n)
        q, f_ = q_node(su.C, origins, obs_idx, order[i], dist[i], cnt, prior); fb += f_
        p = transform(q, prior, su.W); pu = transform(q, prior, su.W, weighted=False)
        s, w = sums(p, y, su.W); S.append(s); Wn.append(w)
        s, w = sums(pu, y, su.W); Su.append(s); Wu.append(w)
        v = y >= 0; pos.append(p[..., 2][v & (y == 2)]); neg.append(p[..., 2][v & (y != 2)])
    return {"S": np.array(S), "Wn": np.array(Wn), "Su": np.array(Su), "Wu": np.array(Wu),
            "red_pos": np.concatenate(pos), "red_neg": np.concatenate(neg), "fallbacks": fb,
            "tgt_idx": tgt_idx, "static_bin": bin_of(dist[:, 0])}


# ---------------------------------------------------------------- self-test ----------------------------

def selftest():
    """Clusters of radius ~60 m share a persistent class (stay 0.97); a node copies its cluster's class w.p. 0.9.
    Pairs within 250 m share clusters, farther pairs do not. Calibrated prediction must beat the prior in the
    0-250 m bin by more than in the outer bins; p must be a probability; tables must ignore hidden segments."""
    g = np.random.default_rng(0); ok = True
    T0, nc, N = 4000, 160, 480
    prior_true = np.array([0.5, 0.35, 0.15])
    centres = g.uniform(0, 20000, (nc, 2)); member = g.integers(0, nc, N)
    coords = centres[member] + g.normal(0, 60, (N, 2))
    cl = np.zeros((T0, nc), np.int64); cl[0] = g.choice([1, 2, 3], p=prior_true, size=nc)
    for t in range(1, T0):
        stay = g.uniform(size=nc) < 0.97
        cl[t] = np.where(stay, cl[t - 1], g.choice([1, 2, 3], p=prior_true, size=nc))
    C = np.where(g.uniform(size=(T0, N)) < 0.9, cl[:, member], g.choice([1, 2, 3], p=prior_true, size=(T0, N)))
    obs = np.zeros(N, bool); obs[g.permutation(N)[:N // 4]] = True
    obs_idx = np.where(obs)[0]; hid = np.where(~obs)[0]
    tr = np.arange(20, 2500); te = np.arange(2600, T0 - 10)
    prior = training_stats(C, obs, 2500); W = (1 / (3 * prior)).astype("float32")
    cnt = tables(C, obs_idx, coords, tr)
    C2 = C.copy(); C2[:, hid] = 1; C2[2500 + 10:] = 1
    ok &= bool(np.array_equal(cnt, tables(C2, obs_idx, coords, tr)))
    order, dist = neighbours(coords, obs_idx, hid)
    gain = {}
    for b in range(NB):
        idx = np.where(bin_of(dist[:, 0]) == b)[0]
        if len(idx) < 5:
            continue
        sq = wq = sp = wp = 0
        for i in idx:
            y = labels(C, te, hid[i])
            q, _ = q_node(C, te, obs_idx, order[i], dist[i], cnt, prior)
            p = transform(q, prior, W)
            ok &= bool(np.isfinite(p).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
            s, w = sums(p, y, W); sq += s.sum(); wq += w.sum()
            s, w = sums(transform(np.broadcast_to(prior, q.shape), prior, W), y, W); sp += s.sum(); wp += w.sum()
        gain[BIN_LABELS[b]] = 100 * (sp / wp - sq / wq) / (sp / wp)
    print("gain over the prior by bin:", {k: round(v, 1) for k, v in gain.items()})
    inner = gain.get(BIN_LABELS[0], -1e9); outer = [v for k, v in gain.items() if k != BIN_LABELS[0]]
    ok &= inner > 10 and len(outer) >= 1 and all(inner > v for v in outer)
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12bis_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-bis preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · "
        f"e12.py {p4b.sha256(Path(e12.__file__), 16)} · e12bis.py {p4b.sha256(Path(__file__), 16)}")
    _, by = runs_by_key(E9RUNS)
    fp_ok = tab_ok = caus = prob = True
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                if s == 0:
                    obs_idx = np.where(su.obs)[0]
                    cnt = tables(su.C, obs_idx, su.al["coords"], su.tr)
                    C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end + max(H):] = 1
                    tab_ok &= bool(np.array_equal(cnt, tables(C2, obs_idx, su.al["coords"], su.tr)))
                    tab_ok &= bool(su.tr.max() + max(H) < su.va.min())
                    if city == "madrid" and f == 0.4:
                        prior = training_stats(su.C, su.obs, su.reg_end)
                        vidx = np.where(su.val)[0]; orig = su.va[:200]
                        order, dist = neighbours(su.al["coords"], obs_idx, vidx)
                        C3 = su.C.copy(); C3[orig.max() + 1:] = 2; C3[:, ~su.obs] = 3
                        for i in range(0, len(vidx), 20):
                            q, _ = q_node(su.C, orig, obs_idx, order[i], dist[i], cnt, prior)
                            q3, _ = q_node(C3, orig, obs_idx, order[i], dist[i], cnt, prior)
                            caus &= bool(np.array_equal(q, q3))
                            p = transform(q, prior, su.W)
                            prob &= bool(np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
    log.check("1", "node sets, origins, class weights identical to the E9 run records (60 pairs)", fp_ok)
    log.check("2", "calibration pairs observed->observed, training origins only (targets before validation); noise on "
              "hidden segments and after training leaves the tables identical (12 city × f, seed 0)", tab_ok)
    log.check("3", "causality of the prediction: noise after t and on hidden segments leaves q identical (Madrid 40%)", caus)
    log.check("4", "every p is a probability on a sample of validation cells", prob)
    log.check("5", "synthetic planted signal: calibrated prediction beats the prior most within 250 m (selftest)",
              selftest() == 0)
    try:
        e12.require_thresholds(RUNS / "nonexistent"); th = False
    except SystemExit:
        th = True
    log.check("6", "a test metric is refused without the validation-threshold file and its fingerprint", th)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E12-bis signature line is blank", guard)
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def cost(args):
    import os
    su = e9.setup("madrid", 0.4, 0)
    up0 = subprocess.check_output(["uptime"], text=True).strip(); t0 = time.perf_counter()
    obs_idx = np.where(su.obs)[0]
    cnt = tables(su.C, obs_idx, su.al["coords"], su.tr); t_tab = time.perf_counter() - t0
    prior = training_stats(su.C, su.obs, su.reg_end)
    predict_set(su, su.va, su.val, cnt, prior); t_val = time.perf_counter() - t0 - t_tab
    scale = (len(su.te) * su.test.sum()) / (len(su.va) * su.val.sum())
    est = t_tab + t_val * (1 + scale)
    out = {"seconds_tables": round(t_tab, 1), "seconds_validation": round(t_val, 1), "seconds_per_pair_estimate": round(est, 1),
           "campaign_estimate_hours": round(est * 60 / 3600, 2), "uptime_before": up0,
           "uptime_after": subprocess.check_output(["uptime"], text=True).strip(), "loadavg": os.getloadavg(),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12bis_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def run_pair(city, f, seed):
    d = RUNS / f"{city}_{int(f * 100)}_s{seed}"
    if (d / "run.json").exists():
        return "skipped", d
    if d.exists():
        raise SystemExit(f"STOP: {d} exists without run.json: interrupted, to be reported")
    d.mkdir(parents=True)
    su = e9.setup(city, f, seed)
    if su.fingerprints() != e12.e9_record(city, f, seed, "G0")["setup"]:
        raise SystemExit(f"STOP: {city} {f} {seed}: setup differs from E9")
    obs_idx = np.where(su.obs)[0]
    cnt = tables(su.C, obs_idx, su.al["coords"], su.tr)
    prior = training_stats(su.C, su.obs, su.reg_end)
    val = predict_set(su, su.va, su.val, cnt, prior)
    th = {NAME: float(np.quantile(val["red_neg"], 0.95))}
    (d / "thresholds.json").write_text(json.dumps(th, indent=1))
    (d / "thresholds.fingerprint").write_text(json.dumps({"sha256": p4b.sha256(d / "thresholds.json", 16),
                                                         "written": datetime.now(timezone.utc).isoformat()}))
    th = e12.require_thresholds(d)
    p4b.require_signed(PREREG)
    tst = predict_set(su, su.te, su.test, cnt, prior)
    arr = {f"{NAME}|S": tst["S"], f"{NAME}|Wn": tst["Wn"], f"{NAME}|Su": tst["Su"], f"{NAME}|Wu": tst["Wu"],
           "blocks": su.cells[tst["tgt_idx"]], "static_bin": tst["static_bin"]}
    for arm in ("G0", "G1"):
        r = e12.e9_record(city, f, seed, arm)
        with np.load(E9RUNS / r["config_fingerprint"] / "test_hidden.npz") as z:
            if not np.array_equal(z["nodes"], tst["tgt_idx"]):
                raise SystemExit(f"STOP: {city} {f} {seed} {arm}: test-hidden nodes differ from E9")
            S, Wn, *_ = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"])
        arr[f"{arm}|S"] = S; arr[f"{arm}|Wn"] = Wn
    np.savez_compressed(d / "sums.npz", **arr)
    diag = {BIN_LABELS[b]: [float(np.trace(cnt[b, hi]) / max(cnt[b, hi].sum(), 1)) for hi in range(len(H))] for b in range(NB)}
    rec = {"city": city, "f": f, "seed": seed, "table_counts": cnt.tolist(), "table_diagonal_share": diag,
           "prior": prior.tolist(), "fallbacks": tst["fallbacks"],
           "red_recall": float((tst["red_pos"] >= th[NAME]).mean()) if tst["red_pos"].size else float("nan"),
           "false_alarm_rate": float((tst["red_neg"] >= th[NAME]).mean()) if tst["red_neg"].size else float("nan"),
           "share_by_bin": {BIN_LABELS[b]: float((tst["static_bin"] == b).mean()) for b in range(NB)},
           "thresholds_sha256": p4b.sha256(d / "thresholds.json", 16), "sums_sha256": p4b.sha256(d / "sums.npz", 16),
           "setup": su.fingerprints(), "code": {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e12.py": p4b.sha256(Path(e12.__file__), 16),
                                                 "e12bis.py": p4b.sha256(Path(__file__), 16)},
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    (d / "run.json").write_text(json.dumps(rec, indent=1))
    return "done", d


def run(args):
    p4b.require_signed(PREREG); RUNS.mkdir(parents=True, exist_ok=True)
    pairs = [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]
    if args.only:
        c, f, s = args.only.split(":"); pairs = [(c, float(f), int(s))]
    for k, (c, f, s) in enumerate(pairs, 1):
        st, d = run_pair(c, f, s)
        print(f"{datetime.now(timezone.utc).isoformat()} [{k}/{len(pairs)}] {st} {c} f={f} seed {s} -> {d.name}", flush=True)
    return 0


# ---------------------------------------------------------------- freeze -------------------------------

def v_cell(cell, r, a, ref="G0", hz=None):
    """Point and replicates of V(a) = mean over seeds of 100·(wCE(ref) − wCE(a))/wCE(ref)."""
    sd, sidx, mult = multiplicities(cell, r)
    def w(arm, s, M=None):
        S, Wn = cell["seeds"][s]["arms"][arm]
        if hz is not None:
            S, Wn = S[:, [hz]], Wn[:, [hz]]
        return wce_from(S, Wn, M)
    pt = float(np.mean([100 * (w(ref, s) - w(a, s)) / w(ref, s) for s in sd]))
    rep = pick(np.stack([100 * (w(ref, s, mult[s]) - w(a, s, mult[s])) / w(ref, s, mult[s]) for s in sd]), sidx)
    return pt, rep


def summary(pt, rep):
    lo, hi = np.percentile(rep, [2.5, 97.5])
    return {"V": pt, "L": float(lo), "U": float(hi), "readings": readings(pt, lo, hi)}


def freeze(args):
    if (OUT / "CONGELAMENTO_E12bis.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12bis.md exists; regenerate only on purpose, after moving it")
    rows = {}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds, recs = {}, []
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"; rec = json.loads((d / "run.json").read_text()); recs.append(rec)
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz")
            arms = {a: (z[f"{a}|S"], z[f"{a}|Wn"]) for a in (NAME, "G0", "G1")}
            arms[f"{NAME} (unweighted)"] = (z[f"{NAME}|Su"], z[f"{NAME}|Wu"])
            seeds[s] = {"blocks": z["blocks"], "arms": arms, "bin": z["static_bin"]}
        cell = {"seeds": seeds}
        row = {}
        pt, rep = v_cell(cell, np.random.default_rng([BOOT, ci]), NAME); row["overall"] = summary(pt, rep)
        g1pt, g1rep = v_cell(cell, np.random.default_rng([BOOT, ci]), "G1")
        lo, hi = np.percentile(rep - g1rep, [2.5, 97.5]); row["minus_G1"] = {"D": pt - g1pt, "L": float(lo), "U": float(hi)}
        ptu, repu = v_cell(cell, np.random.default_rng([BOOT, ci]), f"{NAME} (unweighted)"); row["unweighted"] = summary(ptu, repu)
        row["per_horizon"] = {f"{15 * h} min": summary(*v_cell(cell, np.random.default_rng([BOOT, ci]), NAME, hz=k))
                              for k, h in enumerate(H)}
        row["by_bin"] = {}
        for b, lab in enumerate(BIN_LABELS):
            sub = {"seeds": {}}; nblocks = []
            for s, e in seeds.items():
                m = e["bin"] == b
                if m.sum() == 0:
                    continue
                sub["seeds"][s] = {"blocks": e["blocks"][m], "arms": {a: (v[0][m], v[1][m]) for a, v in e["arms"].items()}}
                nblocks.append(len(np.unique(e["blocks"][m])))
            if len(sub["seeds"]) < len(seeds):
                row["by_bin"][lab] = {"V": None, "note": "bin empty in some seed"}; continue
            ptb, repb = v_cell(sub, np.random.default_rng([BOOT, ci, 1 + b]), NAME)
            e_ = summary(ptb, repb); e_["min_blocks"] = int(min(nblocks))
            g1b, g1r = v_cell(sub, np.random.default_rng([BOOT, ci, 1 + b]), "G1")
            l2, h2 = np.percentile(repb - g1r, [2.5, 97.5]); e_["minus_G1"] = {"D": ptb - g1b, "L": float(l2), "U": float(h2)}
            if min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            row["by_bin"][lab] = e_
        row["share_by_bin"] = {lab: float(np.mean([r["share_by_bin"][lab] for r in recs])) for lab in BIN_LABELS}
        row["diagonal_share"] = {lab: np.mean([r["table_diagonal_share"][lab] for r in recs], 0).tolist() for lab in BIN_LABELS}
        row["red"] = {"recall": float(np.nanmean([r["red_recall"] for r in recs])),
                      "false_alarm_rate": float(np.nanmean([r["false_alarm_rate"] for r in recs]))}
        row["fallbacks"] = int(sum(r["fallbacks"] for r in recs))
        rows[(city, f)] = row
    inner = BIN_LABELS[0]
    def holds(r):
        e = r["by_bin"][inner]
        return e.get("V") is not None and "note" not in e and e["L"] > 0 and e["V"] >= MARGIN
    hits = [(c, f) for (c, f), r in rows.items() if holds(r)]
    levels = sorted({f for (c, f) in hits if sum(1 for (c2, f2) in hits if f2 == f) >= 2})
    if levels:
        st = "the label signal buys wCE within 250 m at f = " + ", ".join(f"{int(x * 100)}%" for x in levels)
    elif all(r["by_bin"][inner].get("V") is not None and r["by_bin"][inner]["U"] < MARGIN for r in rows.values()):
        st = "the calibrated label signal does not buy wCE within 250 m"
    else:
        st = "undetermined"
    write(rows, st, len(hits))
    if args.compare_with:
        old = json.loads(Path(args.compare_with).read_text()); new = json.loads((OUT / "e12bis_risultati.json").read_text())
        diff = [k for k in old if k not in ("commit", "code_dirty", "generator_fingerprint", "written") and old[k] != new.get(k)]
        print("comparison:", "every number identical" if not diff else f"DIFFERENT keys: {diff}")
        return 0 if not diff else 3
    return 0


def write(rows, st, nhits):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "summary_statement": st, "pairs_inner_bin_hit": nhits,
           "commit": c, "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "generator_fingerprint": p4b.sha256(Path(__file__), 16), "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12bis_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: "—" if x is None else f"{x:+.2f}"  # noqa: E731
    def cellfmt(e):
        if e.get("V") is None:
            return "—"
        s = f"{fm(e['V'])} [{fm(e['L'])}; {fm(e['U'])}]"
        return s + (" *" if "note" in e else "")
    L = ["# CONGELAMENTO_E12bis — calibrated neighbour\n",
         f"Generated by `paper4/code/e12bis.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12bis.md` ({res['prereg_fingerprint']}). Inputs: 60 (city, f, "
         f"seed) runs under `paper4/runs/e12bis/`; G0 and G1 from the E9 campaign. V in points of the G0 wCE, positive = better "
         f"than G0. Intervals: 95%, {B} replicates, seeds × corridor blocks; overall with the E9 replicate indices, per bin with "
         f"default_rng([20261106, index of (city, f), 1 + bin]).\n",
         f"## Summary statement (criterion on the 0–250 m bin)\n\n**{st}** — (city, f) pairs where V in the 0–250 m bin is "
         f"favourable and ≥ 3 points: {nhits} of 12.\n",
         "## V against G0, overall and by distance bin of the hidden segment\n",
         "| City | f | Overall | " + " | ".join(BIN_LABELS) + " | Share of hidden segments by bin |",
         "|---|---|---|" + "---|" * NB + "---|"]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cellfmt(r['overall'])} | " + " | ".join(cellfmt(r["by_bin"][b]) for b in BIN_LABELS)
                 + " | " + " / ".join(f"{r['share_by_bin'][b]:.2f}" for b in BIN_LABELS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed: interval not read.\n",
          "## Secondary\n", "| City | f | V − V(G1), overall [L; U] | V − V(G1), 0–250 m [L; U] | V unweighted (q′ only) |",
          "|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        m = r["minus_G1"]; mi = r["by_bin"][BIN_LABELS[0]].get("minus_G1")
        L.append(f"| {city} | {int(f * 100)}% | {fm(m['D'])} [{fm(m['L'])}; {fm(m['U'])}] | "
                 + (f"{fm(mi['D'])} [{fm(mi['L'])}; {fm(mi['U'])}]" if mi else "—") + f" | {fm(r['unweighted']['V'])} |")
    L += ["\n## Reported without a criterion\n", "| City | f | V per horizon 15 / 30 / 60 / 120 min | Diagonal share of the tables at 15 min, by bin | Red recall at 5% FA (realised FA), descriptive | Fallbacks |",
          "|---|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        ph = " / ".join(fm(v["V"]) for v in r["per_horizon"].values())
        dg = " / ".join(f"{r['diagonal_share'][b][0]:.2f}" for b in BIN_LABELS)
        L.append(f"| {city} | {int(f * 100)}% | {ph} | {dg} | {r['red']['recall']:.3f} ({r['red']['false_alarm_rate']:.3f}) | {r['fallbacks']:,} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Calibration tables from observed→observed pairs in the training period only; thresholds on validation saved with "
          "fingerprint before any test metric; node sets, origins and test-hidden nodes identical to E9 (checked by the run).",
          "2. Red recall is descriptive: the prediction takes few distinct values, so the 5% false-alarm target is not met on test.",
          "3. Cells without a valid target excluded from every mean, as in E9."]
    mp = OUT / "CONGELAMENTO_E12bis.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def check_inputs(args):
    """After `run`: 60 folders, fingerprints of sums and thresholds, code recorded, setup equal to E9, keys and
    shapes. No metric is read."""
    _, by = runs_by_key(E9RUNS); bad, found = [], 0
    keys = {f"{NAME}|S", f"{NAME}|Wn", f"{NAME}|Su", f"{NAME}|Wu", "G0|S", "G0|Wn", "G1|S", "G1|Wn", "blocks", "static_bin"}
    code_now = {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e12.py": p4b.sha256(Path(e12.__file__), 16),
                "e12bis.py": p4b.sha256(Path(__file__), 16)}
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = RUNS / f"{city}_{int(f * 100)}_s{s}"
        if not (d / "run.json").exists():
            bad.append(f"{d.name}: run.json missing"); continue
        found += 1; r = json.loads((d / "run.json").read_text())
        if p4b.sha256(d / "sums.npz", 16) != r["sums_sha256"]:
            bad.append(f"{d.name}: sums fingerprint")
        th = p4b.sha256(d / "thresholds.json", 16)
        if th != r["thresholds_sha256"] or th != json.loads((d / "thresholds.fingerprint").read_text())["sha256"]:
            bad.append(f"{d.name}: thresholds fingerprint")
        if r["code"] != code_now:
            bad.append(f"{d.name}: code {r['code']}")
        if r["setup"] != by[(city, f, s)]["G0"]["setup"]:
            bad.append(f"{d.name}: setup differs from E9")
        with np.load(d / "sums.npz") as z:
            if set(z.files) != keys:
                bad.append(f"{d.name}: keys")
    print(f"runs found: {found} of 60; inconsistencies: {len(bad)}")
    for b in bad[:20]:
        print("  -", b)
    ok = found == 60 and not bad
    print("CHECK-INPUTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest_e2e(args):
    """freeze end to end on 60 synthetic folders: within 0-250 m the predictor is 5% of wCE better than G0 at
    f >= 40%, nothing elsewhere; the statement must name 40% and 60%."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12bis"; runs.mkdir(parents=True); g = np.random.default_rng(5)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15)
        W0 = g.uniform(50, 100, (n, len(H))); S0 = W0 * g.uniform(1.05, 1.1, (n, 1))
        fac = np.where((sb == 0) & (f >= 0.4), 0.95, 1.0)[:, None]
        arr = {f"{NAME}|S": S0 * fac, f"{NAME}|Wn": W0, f"{NAME}|Su": S0 * fac, f"{NAME}|Wu": W0,
               "G0|S": S0, "G0|Wn": W0, "G1|S": S0, "G1|Wn": W0, "blocks": blocks, "static_bin": sb}
        np.savez_compressed(d / "sums.npz", **arr)
        rec = {"sums_sha256": p4b.sha256(d / "sums.npz", 16), "share_by_bin": {b: 0.25 for b in BIN_LABELS},
               "table_diagonal_share": {b: [0.5] * len(H) for b in BIN_LABELS}, "red_recall": 0.05,
               "false_alarm_rate": 0.05, "fallbacks": 0}
        (d / "run.json").write_text(json.dumps(rec))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(argparse.Namespace(compare_with=None))
    res = json.loads((OUT / "e12bis_risultati.json").read_text()); st = res["summary_statement"]
    v = res["rows"]["madrid 0.4"]["by_bin"][BIN_LABELS[0]]["V"]
    print(f"synthetic statement: {st}; V within 250 m at madrid 40% = {v:.4f} (expected 5)")
    ok = st == "the label signal buys wCE within 250 m at f = 40%, 60%" and abs(v - 5) < 1e-9
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-bis")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("selftest", "preflight", "cost"):
        sp.add_parser(c)
    r = sp.add_parser("run"); r.add_argument("--only")
    fz = sp.add_parser("freeze"); fz.add_argument("--compare-with")
    sp.add_parser("check-inputs")
    e2 = sp.add_parser("selftest-e2e"); e2.add_argument("tmpdir")
    a = ap.parse_args()
    return {"selftest": lambda a: selftest(), "preflight": preflight, "cost": cost, "run": run, "freeze": freeze,
            "check-inputs": check_inputs, "selftest-e2e": selftest_e2e}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
