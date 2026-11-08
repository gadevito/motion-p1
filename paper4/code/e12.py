#!/usr/bin/env python3
"""
E12 — non-learned spatial predictors on the hidden segments of E9 (`protocol/paper4/E12.md`).
==============================================================================================
No training. Imports `p4b.py`, `e9.py` and the resample of `genera_congelamento_e9.py` unchanged.

    selftest    synthetic data with a planted spatial signal; predictors, transformation and statement
    preflight   controls 1-9 of E12.md, reading no test target (validation origins and segments only)
    cost        isolated timing of one (city, f, seed) on validation origins, scaled to the test origins
    run         after the signature: for every (city, f, seed), thresholds on validation saved with fingerprint,
                then per-node sums on test-hidden segments for every predictor, E9's G0 and G1, red recall and
                realised false alarms, spatial concordance of the labels, written to paper4/runs/e12/
    freeze      generates paper4/congelamenti/CONGELAMENTO_E12.md and e12_risultati.json from paper4/runs/e12/

Predictors (q for each hidden segment, origin t and horizon h; only observed segments, values at time t, and
training-period statistics of observed segments):
    P-nn      one-hot class at t of the nearest observed segment with a valid class at t, persisted
    P-idw4    1/d² average of the one-hot classes at t of the 4 nearest observed segments with a valid class at t
    P-idw500  the same over observed segments within 500 m with a valid class at t; none -> prior (counted)
    P-hist4   1/d² average over the 4 nearest observed segments of their class frequencies in the weekly slot of
              t + h over the training period (neighbours without counts in the slot are skipped; none -> prior)
    Prior     class frequencies of the observed segments over the training period
Transformation, identical for every predictor, no fitted parameter: q' = 0.95 q + 0.05 prior; p ∝ W·q'. The
unweighted q' is kept as a secondary column.

Usage (from the worktree root):
    $PY paper4/code/e12.py selftest | preflight | cost
    $PY paper4/code/e12.py run [--only city:f:seed]
    $PY paper4/code/e12.py freeze [--compare-with <previous e12_risultati.json>]
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
from genera_congelamento_e11 import node_sums, wce_from, readings  # noqa: E402
from genera_congelamento_e9 import multiplicities, pick, runs_by_key  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12.md"
RUNS = e9.RUNS / "e12"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
H = p4b.HORIZONS
EPS = 0.05
RADIUS = 500.0
K_NN = 4
PREDICTORS = ("P-nn", "P-idw4", "P-idw500", "P-hist4")
REFERENCE = "Prior"
ALL = PREDICTORS + (REFERENCE,)
BINS = (0, 250, 500, 1000, np.inf)
BIN_LABELS = ("0-250 m", "250-500 m", "500-1,000 m", "> 1,000 m")
B, BOOT, MARGIN = 4000, 20261106, 3.0


# ---------------------------------------------------------------- predictors ---------------------------

def training_stats(C, obs, reg_end):
    """Prior (class shares of observed training cells) and weekly-slot class counts of observed segments."""
    c = C[:reg_end][:, obs]
    f = np.array([(c == k).sum() for k in (1, 2, 3)], dtype="float64")
    return f / f.sum()


def slot_counts(C, obs_idx, reg_end, slot):
    cnt = np.zeros((len(obs_idx), 672, 3))
    c = C[:reg_end][:, obs_idx]; sl = np.broadcast_to(slot[:reg_end][:, None], c.shape)
    j = np.broadcast_to(np.arange(len(obs_idx)), c.shape)
    for k in (1, 2, 3):
        m = c == k
        np.add.at(cnt[:, :, k - 1], (j[m], sl[m]), 1)
    return cnt


def neighbours(coords, obs_idx, tgt_idx):
    D = np.sqrt(((coords[tgt_idx][:, None, :] - coords[obs_idx][None, :, :]) ** 2).sum(-1))
    order = np.argsort(D, 1, kind="stable")
    return order, np.maximum(np.take_along_axis(D, order, 1), 1.0)


def q_node(name, C, origins, obs_idx, order_n, d_n, prior, cnt=None, slot=None):
    """q (T, H, 3) for one hidden segment, from observed segments only. Returns q and a fallback count."""
    T = len(origins)
    if name == "Prior":
        return np.broadcast_to(prior, (T, len(H), 3)).copy(), 0
    if name == "P-hist4":
        J = order_n[:K_NN]; w = 1.0 / d_n[:K_NN] ** 2
        q = np.zeros((T, len(H), 3)); fb = 0
        for hi, h in enumerate(H):
            c = cnt[J][:, slot[origins + h], :]                        # (4, T, 3)
            tot = c.sum(-1)                                             # (4, T)
            has = tot > 0
            fr = np.divide(c, tot[..., None], out=np.zeros_like(c), where=has[..., None])
            ww = w[:, None] * has
            den = ww.sum(0)
            qq = (ww[..., None] * fr).sum(0) / np.maximum(den, 1e-300)[:, None]
            none = den == 0; qq[none] = prior; fb += int(none.sum())
            q[:, hi] = qq
        return q, fb
    cobs = C[origins][:, obs_idx[order_n]]                              # (T, n_obs) sorted by distance
    valid = cobs > 0
    if name == "P-nn":
        anyv = valid.any(1); first = valid.argmax(1)
        cls = cobs[np.arange(T), first]
        q1 = np.zeros((T, 3)); q1[anyv, cls[anyv] - 1] = 1.0; q1[~anyv] = prior
        return np.repeat(q1[:, None, :], len(H), 1), int((~anyv).sum())
    if name == "P-idw4":
        sel = valid & (np.cumsum(valid, 1) <= K_NN)
    elif name == "P-idw500":
        sel = valid & (d_n <= RADIUS)[None, :]
    else:
        raise ValueError(name)
    w = sel / d_n[None, :] ** 2
    den = w.sum(1)
    q1 = np.stack([(w * (cobs == k)).sum(1) for k in (1, 2, 3)], 1) / np.maximum(den, 1e-300)[:, None]
    none = den == 0; q1[none] = prior
    return np.repeat(q1[:, None, :], len(H), 1), int(none.sum())


def transform(q, prior, W, weighted=True):
    q2 = (1 - EPS) * q + EPS * prior
    if not weighted:
        return q2
    p = q2 * np.asarray(W, dtype="float64")
    return p / p.sum(-1, keepdims=True)


def labels(C, origins, n):
    y = np.stack([C[origins + h, n] for h in H], 1).astype(np.int64)    # (T, H)
    return np.where(y > 0, y - 1, -1)


def sums(p, y, W):
    """Per-horizon S = Σ W[y]·(−log p_y), Wn = Σ W[y] over valid cells of one segment."""
    W = np.asarray(W, dtype="float64"); v = y >= 0; yc = np.where(v, y, 0)
    py = np.take_along_axis(p, yc[..., None], -1)[..., 0]
    w = np.where(v, W[yc], 0.0)
    return (w * -np.log(np.clip(py, 1e-7, 1))).sum(0), w.sum(0)


def predict_set(su, origins, tgt_mask, names=ALL, keep_red=True):
    """For target segments (validation- or test-hidden): per predictor, per-node sums (weighted and unweighted),
    p(red) on valid cells split by label, fallbacks, labels' validity. Reads targets only to score."""
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    prior = training_stats(su.C, su.obs, su.reg_end)
    cnt = slot_counts(su.C, obs_idx, su.reg_end, su.slot)
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    out = {nm: {"S": [], "Wn": [], "Su": [], "Wu": [], "red_pos": [], "red_neg": [], "fallbacks": 0} for nm in names}
    for i, n in enumerate(tgt_idx):
        y = labels(su.C, origins, n)
        for nm in names:
            q, fb = q_node(nm, su.C, origins, obs_idx, order[i], dist[i], prior, cnt, su.slot)
            p = transform(q, prior, su.W); pu = transform(q, prior, su.W, weighted=False)
            S, Wn = sums(p, y, su.W); Su, Wu = sums(pu, y, su.W)
            o = out[nm]; o["S"].append(S); o["Wn"].append(Wn); o["Su"].append(Su); o["Wu"].append(Wu)
            o["fallbacks"] += fb
            if keep_red:
                v = y >= 0
                o["red_pos"].append(p[..., 2][v & (y == 2)]); o["red_neg"].append(p[..., 2][v & (y != 2)])
    for nm in names:
        o = out[nm]
        for k in ("S", "Wn", "Su", "Wu"):
            o[k] = np.array(o[k])
        if keep_red:
            o["red_pos"] = np.concatenate(o["red_pos"]); o["red_neg"] = np.concatenate(o["red_neg"])
    return out, {"prior": prior, "nearest_distance": dist[:, 0], "tgt_idx": tgt_idx}


def concordance(su, origins):
    """Share of (test-hidden, nearest observed) pairs with the same class at the same instant, by distance bin."""
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(su.test)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    nn = obs_idx[order[:, 0]]; d = dist[:, 0]
    a = su.C[origins][:, tgt_idx]; b = su.C[origins][:, nn]
    v = (a > 0) & (b > 0); agree = (a == b) & v
    res = {}
    for lo, hi, lab in zip(BINS[:-1], BINS[1:], BIN_LABELS):
        m = (d >= lo) & (d < hi)
        res[lab] = {"pairs": int(v[:, m].sum()), "agree": int(agree[:, m].sum()), "segments": int(m.sum())}
    return res


# ---------------------------------------------------------------- self-test ----------------------------

def selftest():
    """Planted spatial signal: every hidden segment copies, with probability 0.9, the class of its nearest
    observed segment at the same instant. P-nn must beat the Prior by a large margin; without the signal it
    must not. Plus: q is a probability, causality, statement logic."""
    g = np.random.default_rng(0); ok = True
    T0, n_o, n_h = 3000, 30, 20
    coords = np.concatenate([g.uniform(0, 1000, (n_o, 2)), g.uniform(0, 1000, (n_h, 2))])
    obs_idx = np.arange(n_o); tgt_idx = np.arange(n_o, n_o + n_h)
    prior = np.array([0.5, 0.35, 0.15]); W = np.array([0.67, 0.95, 2.2])
    for signal in (0.9, 0.0):
        C = g.choice([1, 2, 3], p=prior, size=(T0, n_o + n_h))
        order, dist = neighbours(coords, obs_idx, tgt_idx)
        for i, n in enumerate(tgt_idx):
            copy = g.uniform(size=T0) < signal
            C[copy, n] = C[copy, obs_idx[order[i, 0]]]
        origins = np.arange(20, T0 - 10)
        res = {}
        for nm in ("P-nn", "Prior"):
            S = Wn = 0
            for i, n in enumerate(tgt_idx):
                q, _ = q_node(nm, C, origins, obs_idx, order[i], dist[i], prior)
                p = transform(q, prior, W)
                ok &= bool(np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
                # same instant: compare with the class at t (h = 0) by scoring labels at t
                y = np.repeat((C[origins, n] - 1)[:, None], len(H), 1)
                s, w = sums(p, y, W); S = S + s.sum(); Wn = Wn + w.sum()
            res[nm] = S / Wn
        gain = 100 * (res["Prior"] - res["P-nn"]) / res["Prior"]
        print(f"signal {signal}: wCE P-nn {res['P-nn']:.4f}, Prior {res['Prior']:.4f}, gain {gain:+.1f} points")
        ok &= (gain > 20) if signal else (gain < 0)
    # causality: noise after t and on hidden segments leaves q at t unchanged
    C2 = C.copy(); t = 500; C2[t + 1:] = g.integers(0, 4, size=C2[t + 1:].shape); C2[:, tgt_idx] = g.integers(0, 4, size=(T0, n_h))
    for nm in ("P-nn", "P-idw4", "P-idw500"):
        q1, _ = q_node(nm, C, np.array([t]), obs_idx, order[0], dist[0], prior)
        q2, _ = q_node(nm, C2, np.array([t]), obs_idx, order[0], dist[0], prior)
        ok &= bool(np.array_equal(q1, q2))
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def e9_record(city, f, seed, arm):
    _, by = runs_by_key(E9RUNS)
    return by[(city, f, seed)][arm]


def preflight(args):
    from e11 import Log
    e9.RUNS.mkdir(parents=True, exist_ok=True)
    log = Log(e9.RUNS / "e12_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12 preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · "
        f"e12.py {p4b.sha256(Path(__file__), 16)}")
    _, by = runs_by_key(E9RUNS)
    fp_ok = files_ok = nb_ok = stat_ok = prob_ok = True; n = 0
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s); n += 1
                rec0 = by[(city, f, s)]["G0"]
                fp_ok &= su.fingerprints() == rec0["setup"] and list(map(float, su.W)) == list(map(float, rec0["class_weights"]))
                for arm in ("G0", "G1"):
                    r = by[(city, f, s)][arm]; d = E9RUNS / r["config_fingerprint"]
                    files_ok &= p4b.sha256(d / "test_hidden.npz", 16) == r["files"]["test_hidden"]["sha256"]
                obs_idx = np.where(su.obs)[0]
                order, _ = neighbours(su.al["coords"], obs_idx, np.where(~su.obs)[0])
                nb_ok &= bool(np.isin(obs_idx[order], obs_idx).all())
                pr = training_stats(su.C, su.obs, su.reg_end)
                c_ = su.C[:su.reg_end][:, su.obs].ravel(); ind = np.bincount(c_, minlength=4)[1:] / (c_ > 0).sum()
                stat_ok &= bool(np.allclose(pr, ind, atol=0, rtol=1e-12))
                C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end:] = 1
                stat_ok &= bool(np.array_equal(pr, training_stats(C2, su.obs, su.reg_end)))
                cnt = slot_counts(su.C, obs_idx, su.reg_end, su.slot)
                stat_ok &= bool(np.array_equal(cnt, slot_counts(C2, obs_idx, su.reg_end, su.slot)))
                if city == "madrid" and f == 0.4 and s == 0:
                    orig = su.va[:200]; vidx = np.where(su.val)[0]
                    order_v, dist_v = neighbours(su.al["coords"], obs_idx, vidx)
                    caus = True
                    C3 = su.C.copy(); t = int(orig.max()); C3[t + 1:] = 2; C3[:, ~su.obs] = 3
                    for nm in ALL:
                        for i in range(0, len(vidx), 25):
                            q, _ = q_node(nm, su.C, orig, obs_idx, order_v[i], dist_v[i], pr, cnt, su.slot)
                            p = transform(q, pr, su.W)
                            prob_ok &= bool(np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
                            if nm != "P-hist4":                      # P-hist4 reads training counts and the slot only
                                q3, _ = q_node(nm, C3, orig, obs_idx, order_v[i], dist_v[i], pr, cnt, su.slot)
                                caus &= bool(np.array_equal(q, q3))
                    log.check("2", "causality: noise after t and on every hidden segment leaves q at t identical (Madrid 40%, seed 0)", caus)
                    log.check("5", "every p is a probability on a sample of validation origins and segments", prob_ok)
    log.check("1", "node sets, origins, class weights identical to the E9 run records (60 pairs)", fp_ok, f"{n} setups rebuilt")
    log.check("3", "prior and weekly-slot counts from observed training cells only; independent recomputation and "
              "perturbation of hidden segments and later periods leave them identical", stat_ok)
    log.check("4", "E9 G0 and G1 test-hidden files found for 60 pairs with fingerprints matching their run.json", files_ok)
    log.check("6", "synthetic planted signal recovered (selftest)", selftest() == 0)
    log.check("7", "neighbour lists of every hidden segment contain observed segments only", nb_ok)
    log.check("8", "no fitted parameter: only the prior and the weekly-slot counts are computed from data", True,
              f"ε = {EPS}, radius {RADIUS} m, k = {K_NN}, transformation p ∝ W·q', all fixed in E12.md")
    th_guard = True
    try:
        require_thresholds(RUNS / "nonexistent")
        th_guard = False
    except SystemExit:
        pass
    log.check("9", "a test metric is refused without the validation-threshold file and its fingerprint", th_guard)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E12 signature line is blank", guard)
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


# ---------------------------------------------------------------- cost ---------------------------------

def cost(args):
    import os
    su = e9.setup("madrid", 0.4, 0)
    up0 = subprocess.check_output(["uptime"], text=True).strip(); t0 = time.perf_counter()
    predict_set(su, su.va, su.val)
    sec = time.perf_counter() - t0; up1 = subprocess.check_output(["uptime"], text=True).strip()
    scale = (len(su.te) * su.test.sum()) / (len(su.va) * su.val.sum())
    est = sec * (1 + scale)
    out = {"what": "E12 predictors, Madrid f = 40% seed 0, validation origins and segments", "seconds_validation": round(sec, 1),
           "scale_to_test": float(scale), "seconds_per_pair_estimate": round(est, 1),
           "campaign_estimate_hours": round(est * 60 / 3600, 2), "uptime_before": up0, "uptime_after": up1,
           "loadavg_before": os.getloadavg(), "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def require_thresholds(d):
    p = Path(d) / "thresholds.json"
    if not p.exists():
        raise SystemExit(f"STOP: {p} missing: no test metric without the validation thresholds")
    rec = json.loads((Path(d) / "thresholds.fingerprint").read_text())
    if p4b.sha256(p, 16) != rec["sha256"]:
        raise SystemExit(f"STOP: {p} fingerprint differs")
    return json.loads(p.read_text())


def run_pair(city, f, seed):
    d = RUNS / f"{city}_{int(f * 100)}_s{seed}"
    if (d / "run.json").exists():
        return "skipped", d
    if d.exists():
        raise SystemExit(f"STOP: {d} exists without run.json: interrupted, to be reported")
    d.mkdir(parents=True)
    su = e9.setup(city, f, seed)
    rec0 = e9_record(city, f, seed, "G0")
    if su.fingerprints() != rec0["setup"]:
        raise SystemExit(f"STOP: {city} {f} {seed}: setup differs from E9")
    # 1. thresholds on validation, saved with fingerprint before any test metric
    val, _ = predict_set(su, su.va, su.val)
    th = {nm: float(np.quantile(val[nm]["red_neg"], 0.95)) for nm in ALL}
    (d / "thresholds.json").write_text(json.dumps(th, indent=1))
    (d / "thresholds.fingerprint").write_text(json.dumps({"sha256": p4b.sha256(d / "thresholds.json", 16),
                                                         "written": datetime.now(timezone.utc).isoformat()}))
    th = require_thresholds(d)
    # 2. test
    p4b.require_signed(PREREG)
    t0 = time.perf_counter()
    tst, info = predict_set(su, su.te, su.test)
    arrays, rec = {}, {"city": city, "f": f, "seed": seed, "predictors": {}}
    for nm in ALL:
        o = tst[nm]
        for k in ("S", "Wn", "Su", "Wu"):
            arrays[f"{nm}|{k}"] = o[k]
        rec["predictors"][nm] = {"red_recall": float((o["red_pos"] >= th[nm]).mean()) if o["red_pos"].size else float("nan"),
                                 "false_alarm_rate": float((o["red_neg"] >= th[nm]).mean()) if o["red_neg"].size else float("nan"),
                                 "fallbacks": o["fallbacks"]}
    for arm in ("G0", "G1"):
        r = e9_record(city, f, seed, arm); fdir = E9RUNS / r["config_fingerprint"]
        with np.load(fdir / "test_hidden.npz") as z:
            if not np.array_equal(z["nodes"], info["tgt_idx"]):
                raise SystemExit(f"STOP: {city} {f} {seed} {arm}: test-hidden nodes differ from E9")
            yy = z["y"][:, z["nodes"]]
            mine = np.stack([labels(su.C, su.te, n_) for n_ in info["tgt_idx"]], 1)
            if not np.array_equal(yy.astype(np.int64), mine):
                raise SystemExit(f"STOP: {city} {f} {seed} {arm}: labels differ from E9")
            S, Wn, *_ = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"])
        arrays[f"{arm}|S"] = S; arrays[f"{arm}|Wn"] = Wn
    arrays["blocks"] = su.cells[info["tgt_idx"]]
    np.savez_compressed(d / "sums.npz", **arrays)
    rec.update({"concordance": concordance(su, su.te), "prior": info["prior"].tolist(),
                "share_test_hidden_without_observed_within_500m": float((info["nearest_distance"] > RADIUS).mean()),
                "geometry": su.geometry(), "thresholds_sha256": p4b.sha256(d / "thresholds.json", 16),
                "sums_sha256": p4b.sha256(d / "sums.npz", 16), "seconds_test": time.perf_counter() - t0,
                "setup": su.fingerprints(), "code": {"p4b.py": p4b.sha256(Path(p4b.__file__), 16),
                                                      "e12.py": p4b.sha256(Path(__file__), 16)},
                "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()})
    (d / "run.json").write_text(json.dumps(rec, indent=1))
    return "done", d


def run(args):
    p4b.require_signed(PREREG)
    RUNS.mkdir(parents=True, exist_ok=True)
    pairs = [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]
    if args.only:
        c, f, s = args.only.split(":"); pairs = [(c, float(f), int(s))]
    for k, (c, f, s) in enumerate(pairs, 1):
        st, d = run_pair(c, f, s)
        print(f"{datetime.now(timezone.utc).isoformat()} [{k}/{len(pairs)}] {st} {c} f={f} seed {s} -> {d.name}", flush=True)
    return 0


# ---------------------------------------------------------------- freeze -------------------------------

def freeze(args):
    if (OUT / "CONGELAMENTO_E12.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12.md exists; regenerate only on purpose, after moving it")
    rows, conc, extra = {}, {}, {"fallbacks": {}, "red": {}, "no_obs_500": {}}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds = {}
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"
            rec = json.loads((d / "run.json").read_text())
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz")
            arms = {nm: (z[f"{nm}|S"], z[f"{nm}|Wn"]) for nm in ALL + ("G0", "G1")}
            arms.update({f"{nm} (unweighted)": (z[f"{nm}|Su"], z[f"{nm}|Wu"]) for nm in ALL})
            seeds[s] = {"blocks": z["blocks"], "arms": arms}
            for b, v in rec["concordance"].items():
                cc = conc.setdefault((city, f), {}).setdefault(b, {"pairs": 0, "agree": 0})
                cc["pairs"] += v["pairs"]; cc["agree"] += v["agree"]
            conc[(city, f)]["expected_from_prior"] = conc[(city, f)].get("expected_from_prior", []) + [float(np.sum(np.square(rec["prior"])))]
            for nm, v in rec["predictors"].items():
                extra["red"].setdefault((city, f, nm), []).append((v["red_recall"], v["false_alarm_rate"]))
                extra["fallbacks"][(city, f, nm)] = extra["fallbacks"].get((city, f, nm), 0) + v["fallbacks"]
            extra["no_obs_500"].setdefault((city, f), []).append(rec["share_test_hidden_without_observed_within_500m"])
        cell = {"seeds": seeds}
        r = np.random.default_rng([BOOT, ci])
        sd, sidx, mult = multiplicities(cell, r)
        names = list(seeds[sd[0]]["arms"])
        w_pt = {a: np.array([[wce_from(*seeds[s]["arms"][a]) for s in sd]]) for a in names}
        w_rep = {a: np.stack([wce_from(*seeds[s]["arms"][a], mult[s]) for s in sd]) for a in names}
        hw_pt = {a: np.array([seeds[s]["arms"][a][0].sum(0) / seeds[s]["arms"][a][1].sum(0) for s in sd]) for a in names}
        hw_rep = {a: np.stack([(mult[s] @ seeds[s]["arms"][a][0]) / (mult[s] @ seeds[s]["arms"][a][1]) for s in sd]) for a in names}
        row = {}
        for a in names:
            if a in ("G0",):
                continue
            vpt = float(np.mean(100 * (w_pt["G0"] - w_pt[a]) / w_pt["G0"]))
            vrep = pick(100 * (w_rep["G0"] - w_rep[a]) / w_rep["G0"], sidx)
            lo, hi = np.percentile(vrep, [2.5, 97.5])
            e = {"V": vpt, "L": float(lo), "U": float(hi), "readings": readings(vpt, lo, hi),
                 "wce": float(np.mean(w_pt[a]))}
            if a in PREDICTORS:
                g1 = pick(100 * (w_rep["G0"] - w_rep["G1"]) / w_rep["G0"], sidx)
                g1pt = float(np.mean(100 * (w_pt["G0"] - w_pt["G1"]) / w_pt["G0"]))
                dl, dh = np.percentile(vrep - g1, [2.5, 97.5])
                e["minus_G1"] = {"D": vpt - g1pt, "L": float(dl), "U": float(dh)}
                e["per_horizon"] = {}
                for hi_, h in enumerate(H):
                    vp = float(np.mean(100 * (hw_pt["G0"][:, hi_] - hw_pt[a][:, hi_]) / hw_pt["G0"][:, hi_]))
                    vr = pick(100 * (hw_rep["G0"][..., hi_] - hw_rep[a][..., hi_]) / hw_rep["G0"][..., hi_], sidx)
                    l2, h2 = np.percentile(vr, [2.5, 97.5])
                    e["per_horizon"][f"{15 * h} min"] = {"V": vp, "L": float(l2), "U": float(h2)}
            row[a] = e
        row["G0_wce"] = float(np.mean(w_pt["G0"]))
        rows[(city, f)] = row
    hits = {nm: [(c, f) for c in e9.CITIES for f in e9.LEVELS
                 if rows[(c, f)][nm]["L"] > 0 and rows[(c, f)][nm]["V"] >= MARGIN] for nm in PREDICTORS}
    signal = {nm: sorted({f for (c, f) in hits[nm] if sum(1 for (c2, f2) in hits[nm] if f2 == f) >= 2}) for nm in PREDICTORS}
    if any(signal.values()):
        statement = "a spatial signal is present, recoverable by " + "; ".join(
            f"{nm} at f = {', '.join(f'{int(x * 100)}%' for x in fs)}" for nm, fs in signal.items() if fs)
    elif all(rows[(c, f)][nm]["U"] < MARGIN for nm in PREDICTORS for c in e9.CITIES for f in e9.LEVELS):
        statement = "no spatial signal recoverable by these predictors at 10-60% coverage"
    else:
        statement = "undetermined"
    counts = {nm: {"favourable_and_3": len(hits[nm]),
                   "U_below_3": sum(rows[(c, f)][nm]["U"] < MARGIN for c in e9.CITIES for f in e9.LEVELS)} for nm in PREDICTORS}
    write_freeze(rows, conc, extra, statement, counts)
    if args.compare_with:
        old = json.loads(Path(args.compare_with).read_text()); new = json.loads((OUT / "e12_risultati.json").read_text())
        diff = [k for k in old if k not in ("commit", "code_dirty", "generator_fingerprint", "written") and old[k] != new.get(k)]
        print("comparison:", "every number identical" if not diff else f"DIFFERENT keys: {diff}")
        return 0 if not diff else 3
    return 0


def write_freeze(rows, conc, extra, statement, counts):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    key = lambda k: f"{k[0]} {k[1]}"  # noqa: E731
    res = {"rows": {key(k): v for k, v in rows.items()}, "concordance": {key(k): v for k, v in conc.items()},
           "red_recall_and_false_alarms": {f"{k[0]} {k[1]} {k[2]}": v for k, v in extra["red"].items()},
           "fallbacks": {f"{k[0]} {k[1]} {k[2]}": v for k, v in extra["fallbacks"].items()},
           "share_without_observed_within_500m": {key(k): float(np.mean(v)) for k, v in extra["no_obs_500"].items()},
           "summary_statement": statement, "counts": counts, "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: f"{x:+.2f}"  # noqa: E731
    L = ["# CONGELAMENTO_E12 — non-learned spatial predictors on the hidden segments of E9\n",
         f"Generated by `paper4/code/e12.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12.md` ({res['prereg_fingerprint']}). Inputs: 60 (city, f, "
         f"seed) runs under `paper4/runs/e12/`, each checked against its fingerprint; G0 and G1 from the E9 campaign. V in points "
         f"of the G0 wCE, positive = the predictor is better than G0. Intervals: 95%, {B} replicates, seeds × corridor blocks "
         f"(grid cells), the same replicate indices as E9.\n",
         f"## Summary statement\n\n**{statement}** — per predictor, (city, f) pairs with V favourable and ≥ 3 points / pairs "
         "with U < 3: " + "; ".join(f"{nm} {v['favourable_and_3']} / {v['U_below_3']}" for nm, v in counts.items()) + " (of 12).\n",
         "## V of each predictor against G0 (weighted transformation, primary)\n",
         "| City | f | G0 wCE | " + " | ".join(f"{nm} V [L; U]" for nm in ALL) + " |",
         "|---|---|---|" + "---|" * len(ALL)]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {r['G0_wce']:.4f} | " +
                 " | ".join(f"{fm(r[nm]['V'])} [{fm(r[nm]['L'])}; {fm(r[nm]['U'])}]" for nm in ALL) + " |")
    L += ["\n## Secondary column: V without the reweighting (q' only)\n",
          "| City | f | " + " | ".join(f"{nm}" for nm in ALL) + " |", "|---|---|" + "---|" * len(ALL)]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | " + " | ".join(fm(r[f"{nm} (unweighted)"]["V"]) for nm in ALL) + " |")
    L += ["\n## Reported without a criterion\n", "### Spatial concordance of the labels (test origins, pooled over seeds)\n",
          "| City | f | " + " | ".join(BIN_LABELS) + " | expected from the prior (Σπ²) |", "|---|---|" + "---|" * (len(BIN_LABELS) + 1)]
    for (city, f), v in conc.items():
        cells = [f"{v[b]['agree'] / v[b]['pairs']:.3f} ({v[b]['pairs']:,})" if v[b]["pairs"] else "—" for b in BIN_LABELS]
        L.append(f"| {city} | {int(f * 100)}% | " + " | ".join(cells) + f" | {np.mean(v['expected_from_prior']):.3f} |")
    L += ["\n### V(P) − V(G1 of E9), and V(P) per horizon (15 / 30 / 60 / 120 min)\n",
          "| City | f | Predictor | V(P) − V(G1) [L; U] | per horizon |", "|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        for nm in PREDICTORS:
            m = r[nm]["minus_G1"]; ph = r[nm]["per_horizon"]
            L.append(f"| {city} | {int(f * 100)}% | {nm} | {fm(m['D'])} [{fm(m['L'])}; {fm(m['U'])}] | " +
                     " / ".join(f"{fm(v['V'])} [{fm(v['L'])}; {fm(v['U'])}]" for v in ph.values()) + " |")
    L += ["\n### Red recall at 5% false alarms (threshold on validation-hidden segments) and realised false-alarm rate on test\n",
          "| City | f | " + " | ".join(ALL) + " |", "|---|---|" + "---|" * len(ALL)]
    for (city, f) in rows:
        cells = []
        for nm in ALL:
            v = np.array([x for x in extra["red"][(city, f, nm)]], dtype=float)
            cells.append(f"{np.nanmean(v[:, 0]):.3f} ({np.nanmean(v[:, 1]):.3f})")
        L.append(f"| {city} | {int(f * 100)}% | " + " | ".join(cells) + " |")
    L += ["\nIn each cell: recall (realised false-alarm rate).\n", "### Coverage and fallbacks\n",
          "| City | f | Share of test-hidden segments with no observed segment within 500 m | Fallbacks to the prior: P-nn / P-idw4 / P-idw500 / P-hist4 (cells) |",
          "|---|---|---|---|"]
    for (city, f) in rows:
        fb = " / ".join(f"{extra['fallbacks'][(city, f, nm)]:,}" for nm in PREDICTORS)
        L.append(f"| {city} | {int(f * 100)}% | {np.mean(extra['no_obs_500'][(city, f)]):.3f} | {fb} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Thresholds of the red recall chosen on validation-hidden segments and saved with fingerprint before any test "
          "metric, in every run folder (`thresholds.json`, `thresholds.fingerprint`).",
          "2. Node sets, origins, class weights and test-hidden labels of every run identical to the E9 records (checked by the run).",
          "3. Cells without a valid target excluded from every mean, as in E9."]
    mp = OUT / "CONGELAMENTO_E12.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def main():
    ap = argparse.ArgumentParser(description="E12")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("selftest", "preflight", "cost"):
        sp.add_parser(c)
    r = sp.add_parser("run"); r.add_argument("--only", help="city:f:seed")
    fz = sp.add_parser("freeze"); fz.add_argument("--compare-with")
    a = ap.parse_args()
    return {"selftest": lambda a: selftest(), "preflight": preflight, "cost": cost, "run": run, "freeze": freeze}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
