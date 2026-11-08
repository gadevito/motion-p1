#!/usr/bin/env python3
"""
E12-ter — calibrated neighbour with the calendar (`protocol/paper4/E12ter.md`). No training.
==========================================================================================
Imports `p4b.py`, `e9.py`, `e12.py`, `e12bis.py` and the resample of `genera_congelamento_e9.py` unchanged.

    selftest      planted calendar and planted short-range copy; tables, slots, prediction, bins
    preflight     controls 1-7 of E12ter.md, reading no test target
    cost          tables and validation predictions for Madrid f = 40% seed 0, scaled to the test origins
    run           after the signature: per (city, f, seed) tables from observed->observed pairs in training,
                  thresholds on validation saved with fingerprint, then per-node sums on test-hidden segments
    check-inputs  after run: 60 folders, fingerprints, code, setup, keys (no metric read)
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E12ter.md and e12ter_risultati.json from paper4/runs/e12ter/

Slot: hour of the week of the TARGET time t + h, 24 × 7 = 168 slots, from the timestamps alone
(slot = day of week · 24 + hour). The pairs and the neighbour rule are those of E12-bis. Two tables from the
same observed->observed pairs of the training period:

  E12-ter    n(y_i(t+h) = a | slot(t+h), y_j(t) = b, distance bin of d(i, j), h)
  Calendar   n(y_i(t+h) = a | slot(t+h), h)          (same cells, neighbour class ignored)

Prediction for a hidden segment at origin t: nearest observed segment with a valid class b at t, at distance d.
E12-ter row (slot(t+h), b, bin(d), h); if it holds fewer than N_MIN = 20 pairs -> the E12-bis row (b, bin(d), h)
(counted); if that is empty or no neighbour is valid -> prior (counted). Calendar row (slot(t+h), h); fewer than
N_MIN pairs -> prior (counted). Then q' = 0.95 q + 0.05 prior, p ∝ W·q', as in E12 and E12-bis.

Usage: $PY paper4/code/e12ter.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
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
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
import e12  # noqa: E402
import e12bis  # noqa: E402
from e12 import neighbours, labels, sums, transform, training_stats, BIN_LABELS  # noqa: E402
from e12bis import bin_of, v_cell, summary, NB, B, BOOT, MARGIN  # noqa: E402
from genera_congelamento_e11 import node_sums  # noqa: E402
from genera_congelamento_e9 import runs_by_key  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12ter.md"
RUNS = e9.RUNS / "e12ter"
BISRUNS = e9.RUNS / "e12bis"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
H = p4b.HORIZONS
NS = 168
N_MIN = 20
NAME, CAL, BIS = "E12-ter", "Calendar", "E12-bis"


def slot168(ts):
    """Hour of the week from the timestamps only (Monday 00:00-00:59 = 0)."""
    d = pd.DatetimeIndex(ts)
    return (d.dayofweek.to_numpy() * 24 + d.hour.to_numpy()).astype(np.int64)


# ---------------------------------------------------------------- tables and prediction ----------------

def tables(C, obs_idx, coords, origins, sl):
    """cnt (NS, NB, H, 3, 3): [slot of t+h, bin, horizon, neighbour class b, own class a] and
    cal (NS, H, 3): [slot of t+h, horizon, own class a], from the same observed->observed pairs as E12-bis."""
    cnt = np.zeros((NS, NB, len(H), 3, 3)); cal = np.zeros((NS, len(H), 3))
    order, dist = neighbours(coords, obs_idx, obs_idx)
    for ii, i in enumerate(obs_idx):
        keep = obs_idx[order[ii]] != i                       # exclude the segment itself
        cand = obs_idx[order[ii][keep]]; dd = dist[ii][keep]
        cobs = C[origins][:, cand]; valid = cobs > 0
        anyv = valid.any(1); first = valid.argmax(1)
        b = cobs[np.arange(len(origins)), first]; bn = bin_of(dd[first])
        for hi, h in enumerate(H):
            a = C[origins + h, i]; s = sl[origins + h]
            m = anyv & (a > 0)
            np.add.at(cnt, (s[m], bn[m], hi, b[m] - 1, a[m] - 1), 1)
            np.add.at(cal, (s[m], hi, a[m] - 1), 1)
    return cnt, cal


def q_ter(C, origins, obs_idx, order_n, d_n, cnt, cnt_bis, prior, sl):
    """q (T, H, 3) of E12-ter for one hidden segment; fallbacks (to the E12-bis row, to the prior)."""
    cobs = C[origins][:, obs_idx[order_n]]; valid = cobs > 0
    anyv = valid.any(1); first = valid.argmax(1)
    b = np.clip(cobs[np.arange(len(origins)), first] - 1, 0, 2); bn = bin_of(d_n[first])
    q = np.zeros((len(origins), len(H), 3)); fb_bis = fb_prior = 0
    for hi, h in enumerate(H):
        rows = cnt[sl[origins + h], bn, hi, b]; tot = rows.sum(1)
        rb = cnt_bis[bn, hi, b]; tb = rb.sum(1)
        use_t = anyv & (tot >= N_MIN)
        use_b = anyv & ~use_t & (tb > 0)
        q[use_t, hi] = rows[use_t] / tot[use_t, None]
        q[use_b, hi] = rb[use_b] / tb[use_b, None]
        rest = ~(use_t | use_b); q[rest, hi] = prior
        fb_bis += int(use_b.sum()); fb_prior += int(rest.sum())
    return q, (fb_bis, fb_prior)


def q_cal(origins, cal, prior, sl):
    q = np.zeros((len(origins), len(H), 3)); fb = 0
    for hi, h in enumerate(H):
        rows = cal[sl[origins + h], hi]; tot = rows.sum(1); ok = tot >= N_MIN
        q[ok, hi] = rows[ok] / tot[ok, None]; q[~ok, hi] = prior; fb += int((~ok).sum())
    return q, fb


def predict_set(su, origins, tgt_mask, cnt, cal, prior, sl):
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    cnt_bis = cnt.sum(0)
    qc, fb_cal = q_cal(origins, cal, prior, sl)
    pc = transform(qc, prior, su.W)
    out = {k: {"S": [], "Wn": [], "red_pos": [], "red_neg": []} for k in (NAME, CAL)}
    Su, Wu, fb_bis, fb_prior, bins_fb = [], [], 0, 0, np.zeros((NB, 2), np.int64)
    sbin = bin_of(dist[:, 0])
    for i, n in enumerate(tgt_idx):
        y = labels(su.C, origins, n); v = y >= 0
        q, (fb1, fb2) = q_ter(su.C, origins, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
        fb_bis += fb1; fb_prior += fb2; bins_fb[sbin[i]] += (fb1, fb2)
        p = transform(q, prior, su.W); pu = transform(q, prior, su.W, weighted=False)
        for k, pp in ((NAME, p), (CAL, pc)):
            s, w = sums(pp, y, su.W); out[k]["S"].append(s); out[k]["Wn"].append(w)
            out[k]["red_pos"].append(pp[..., 2][v & (y == 2)]); out[k]["red_neg"].append(pp[..., 2][v & (y != 2)])
        s, w = sums(pu, y, su.W); Su.append(s); Wu.append(w)
    for k in out:
        o = out[k]; o["S"] = np.array(o["S"]); o["Wn"] = np.array(o["Wn"])
        o["red_pos"] = np.concatenate(o["red_pos"]); o["red_neg"] = np.concatenate(o["red_neg"])
    lookups = len(origins) * len(H)
    return {"arms": out, "Su": np.array(Su), "Wu": np.array(Wu), "tgt_idx": tgt_idx, "static_bin": sbin,
            "fallbacks": {"to_E12bis_row": fb_bis, "to_prior": fb_prior, "calendar_to_prior": fb_cal * len(tgt_idx),
                          "lookups": lookups * len(tgt_idx),
                          "by_bin": {BIN_LABELS[b]: {"to_E12bis_row": int(bins_fb[b, 0]), "to_prior": int(bins_fb[b, 1]),
                                                     "lookups": int((sbin == b).sum()) * lookups} for b in range(NB)}}}


def fallback_shares(su, origins, tgt_mask, cnt, prior, sl):
    """Share of lookups that fall back to the E12-bis row, by static bin; reads no target."""
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx); cnt_bis = cnt.sum(0)
    sbin = bin_of(dist[:, 0]); acc = np.zeros((NB, 2))
    for i in range(len(tgt_idx)):
        _, (fb1, _) = q_ter(su.C, origins, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
        acc[sbin[i]] += (fb1, len(origins) * len(H))
    return {BIN_LABELS[b]: (round(acc[b, 0] / acc[b, 1], 3) if acc[b, 1] else None) for b in range(NB)}


# ---------------------------------------------------------------- self-test ----------------------------

def synthetic_world(seed=0):
    """Clusters of radius ~60 m share a persistent class; new draws come from a slot-dependent prior (planted
    calendar: weekday 7-9 h and 17-19 h lean to red); a node copies its cluster's class w.p. 0.9."""
    g = np.random.default_rng(seed)
    T0, nc, N = 8000, 160, 480
    ts = np.datetime64("2026-01-05T00:00") + np.arange(T0) * p4b.STEP          # a Monday
    sl = slot168(ts)
    calm, peak = np.array([0.7, 0.25, 0.05]), np.array([0.05, 0.25, 0.7])
    hour, dow = sl % 24, sl // 24
    is_peak = (dow < 5) & (((hour >= 7) & (hour < 10)) | ((hour >= 17) & (hour < 20)))
    pr = np.where(is_peak[:, None], peak, calm)
    centres = g.uniform(0, 20000, (nc, 2)); member = g.integers(0, nc, N)
    coords = centres[member] + g.normal(0, 60, (N, 2))
    def draw(p, n):
        return 1 + (g.uniform(size=n)[:, None] > np.cumsum(p)[None, :-1]).sum(1)
    cl = np.zeros((T0, nc), np.int64); cl[0] = draw(pr[0], nc)
    for t in range(1, T0):
        stay = g.uniform(size=nc) < 0.95
        cl[t] = np.where(stay, cl[t - 1], draw(pr[t], nc))
    own = np.stack([draw(pr[t], N) for t in range(T0)])
    C = np.where(g.uniform(size=(T0, N)) < 0.9, cl[:, member], own)
    obs = np.zeros(N, bool); obs[g.permutation(N)[:N // 4]] = True
    return C, coords, obs, ts, sl


def selftest():
    C, coords, obs, ts, sl = synthetic_world(); ok = True
    obs_idx = np.where(obs)[0]; hid = np.where(~obs)[0]
    reg_end = 5000; tr = np.arange(20, reg_end - max(H)); te = np.arange(5200, len(ts) - max(H))
    prior = training_stats(C, obs, reg_end); W = (1 / (3 * prior)).astype("float32")
    cnt, cal = tables(C, obs_idx, coords, tr, sl)
    ok &= bool(np.array_equal(cnt.sum(0), e12bis.tables(C, obs_idx, coords, tr)))      # same pairs as E12-bis
    ok &= bool(np.array_equal(cal, cnt.sum((1, 3)))) and cal.sum() == cnt.sum()
    C2 = C.copy(); C2[:, hid] = 1; C2[reg_end:] = 1
    c2, k2 = tables(C2, obs_idx, coords, tr, sl)
    ok &= bool(np.array_equal(cnt, c2) and np.array_equal(cal, k2))
    ok &= bool(np.array_equal(slot168(ts), sl))
    order, dist = neighbours(coords, obs_idx, hid); cnt_bis = cnt.sum(0)
    gain_tc, acc = {}, {}
    C3 = C.copy(); C3[te.max() + 1:] = 2; C3[:, hid] = 3
    for i in range(len(hid)):
        y = labels(C, te, hid[i]); b = int(bin_of(dist[i, 0]))
        q, _ = q_ter(C, te, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
        qc, _ = q_cal(te, cal, prior, sl)
        q3, _ = q_ter(C3, te, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
        ok &= bool(np.array_equal(q, q3))
        r = acc.setdefault(b, np.zeros(6))
        for k, qq in enumerate((q, qc, np.broadcast_to(prior, q.shape))):
            p = transform(qq, prior, W)
            ok &= bool(np.isfinite(p).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
            s, w = sums(p, y, W); r[2 * k] += s.sum(); r[2 * k + 1] += w.sum()
    tot = sum(acc.values())
    gain_cp = 100 * (tot[4] / tot[5] - tot[2] / tot[3]) / (tot[4] / tot[5])
    for b, r in sorted(acc.items()):
        if r[1] > 0:
            gain_tc[BIN_LABELS[b]] = 100 * (r[2] / r[3] - r[0] / r[1]) / (r[2] / r[3])
    print(f"gain of the calendar over the prior: {gain_cp:.1f}; gain of E12-ter over the calendar by bin:",
          {k: round(v, 1) for k, v in gain_tc.items()})
    inner = gain_tc.get(BIN_LABELS[0], -1e9); outer = [v for k, v in gain_tc.items() if k != BIN_LABELS[0]]
    ok &= gain_cp > 2 and inner > 10 and len(outer) >= 1 and all(inner > v for v in outer)
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def slot_checks(su, sl):
    """Slots from timestamps only; every target time t + h of every origin is exactly h steps after t, so
    slot(t + h) is the calendar of the target, never a value read from the data."""
    ok = bool(np.array_equal(sl, slot168(su.ts)) and np.array_equal(sl, su.slot // 4))
    for orig in (su.tr, su.va, su.te):
        for h in H:
            ok &= bool(((su.ts[orig + h] - su.ts[orig]) == h * p4b.STEP).all())
    return ok


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12ter_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-ter preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · "
        f"e12.py {p4b.sha256(Path(e12.__file__), 16)} · e12bis.py {p4b.sha256(Path(e12bis.__file__), 16)} · "
        f"e12ter.py {p4b.sha256(Path(__file__), 16)}")
    _, by = runs_by_key(E9RUNS)
    fp_ok = tab_ok = slot_ok = caus = prob = bis_ok = True; shares = {}
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                d = BISRUNS / f"{city}_{int(f * 100)}_s{s}"
                rb = json.loads((d / "run.json").read_text())
                bis_ok &= p4b.sha256(d / "sums.npz", 16) == rb["sums_sha256"] and rb["setup"] == su.fingerprints()
                if s != 0:
                    continue
                sl = slot168(su.ts); slot_ok &= slot_checks(su, sl)
                obs_idx = np.where(su.obs)[0]
                cnt, cal = tables(su.C, obs_idx, su.al["coords"], su.tr, sl)
                tab_ok &= bool(np.array_equal(cnt.sum(0), e12bis.tables(su.C, obs_idx, su.al["coords"], su.tr)))
                C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end + max(H):] = 1
                c2, k2 = tables(C2, obs_idx, su.al["coords"], su.tr, sl)
                tab_ok &= bool(np.array_equal(cnt, c2) and np.array_equal(cal, k2))
                tab_ok &= bool(su.tr.max() + max(H) < su.va.min())
                prior = training_stats(su.C, su.obs, su.reg_end)
                shares[f"{city} {int(f * 100)}%"] = fallback_shares(su, su.va, su.val, cnt, prior, sl)
                if city == "madrid" and f == 0.4:
                    vidx = np.where(su.val)[0]; orig = su.va[:200]; cnt_bis = cnt.sum(0)
                    order, dist = neighbours(su.al["coords"], obs_idx, vidx)
                    C3 = su.C.copy(); C3[orig.max() + 1:] = 2; C3[:, ~su.obs] = 3
                    qc, _ = q_cal(orig, cal, prior, sl)
                    for i in range(0, len(vidx), 20):
                        q, _ = q_ter(su.C, orig, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
                        q3, _ = q_ter(C3, orig, obs_idx, order[i], dist[i], cnt, cnt_bis, prior, sl)
                        caus &= bool(np.array_equal(q, q3))
                        for qq in (q, qc):
                            p = transform(qq, prior, su.W)
                            prob &= bool(np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
    log.check("1", "node sets, origins, class weights identical to the E9 run records (60 pairs)", fp_ok)
    log.check("2", "tables from observed->observed pairs, training origins only (targets before validation); summed over "
              "slots they equal the E12-bis tables to the bit; noise on hidden segments and after training leaves both "
              "tables identical (12 city × f, seed 0)", tab_ok)
    log.check("3", "slots from the timestamps of t + h only (day of week · 24 + hour), equal to the 15-min weekly slot "
              "of p4b divided by 4; t + h is exactly h steps after t for every training, validation and test origin "
              "(12 city × f, seed 0)", slot_ok)
    log.check("4", "causality of the prediction: noise after t and on hidden segments leaves q identical (Madrid 40%)", caus)
    log.check("5", "every p (E12-ter and calendar) is a probability on a sample of validation cells", prob)
    log.check("6", "synthetic world with a planted calendar and a planted short-range copy: the calendar beats the "
              "prior, E12-ter beats the calendar most within 250 m (selftest)", selftest() == 0)
    try:
        e12.require_thresholds(RUNS / "nonexistent"); th = False
    except SystemExit:
        th = True
    log.check("7", "a test metric is refused without the validation-threshold file and its fingerprint; E12-bis run "
              "records present with matching sums fingerprints and setup for the 60 pairs", th and bis_ok)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E12-ter signature line is blank", guard)
    log(f"descriptive, no target read: share of validation-hidden lookups falling back to the E12-bis row (fewer than "
        f"{N_MIN} pairs in the slot row), by static bin {' / '.join(BIN_LABELS)}, seed 0:")
    for k, v in shares.items():
        log(f"  {k}: " + " / ".join("—" if x is None else f"{x:.3f}" for x in v.values()))
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def cost(args):
    import os
    su = e9.setup("madrid", 0.4, 0); sl = slot168(su.ts)
    up0 = subprocess.check_output(["uptime"], text=True).strip(); t0 = time.perf_counter()
    obs_idx = np.where(su.obs)[0]
    cnt, cal = tables(su.C, obs_idx, su.al["coords"], su.tr, sl); t_tab = time.perf_counter() - t0
    prior = training_stats(su.C, su.obs, su.reg_end)
    predict_set(su, su.va, su.val, cnt, cal, prior, sl); t_val = time.perf_counter() - t0 - t_tab
    scale = (len(su.te) * su.test.sum()) / (len(su.va) * su.val.sum())
    est = t_tab + t_val * (1 + scale)
    out = {"seconds_tables": round(t_tab, 1), "seconds_validation": round(t_val, 1), "seconds_per_pair_estimate": round(est, 1),
           "campaign_estimate_hours": round(est * 60 / 3600, 2), "uptime_before": up0,
           "uptime_after": subprocess.check_output(["uptime"], text=True).strip(), "loadavg": os.getloadavg(),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12ter_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def code_fp():
    return {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e12.py": p4b.sha256(Path(e12.__file__), 16),
            "e12bis.py": p4b.sha256(Path(e12bis.__file__), 16), "e12ter.py": p4b.sha256(Path(__file__), 16)}


def run_pair(city, f, seed):
    d = RUNS / f"{city}_{int(f * 100)}_s{seed}"
    if (d / "run.json").exists():
        return "skipped", d
    if d.exists():
        raise SystemExit(f"STOP: {d} exists without run.json: interrupted, to be reported")
    d.mkdir(parents=True)
    su = e9.setup(city, f, seed); sl = slot168(su.ts)
    if su.fingerprints() != e12.e9_record(city, f, seed, "G0")["setup"]:
        raise SystemExit(f"STOP: {city} {f} {seed}: setup differs from E9")
    if not slot_checks(su, sl):
        raise SystemExit(f"STOP: {city} {f} {seed}: slot check failed")
    obs_idx = np.where(su.obs)[0]
    cnt, cal = tables(su.C, obs_idx, su.al["coords"], su.tr, sl)
    prior = training_stats(su.C, su.obs, su.reg_end)
    val = predict_set(su, su.va, su.val, cnt, cal, prior, sl)
    th = {k: float(np.quantile(val["arms"][k]["red_neg"], 0.95)) for k in (NAME, CAL)}
    (d / "thresholds.json").write_text(json.dumps(th, indent=1))
    (d / "thresholds.fingerprint").write_text(json.dumps({"sha256": p4b.sha256(d / "thresholds.json", 16),
                                                         "written": datetime.now(timezone.utc).isoformat()}))
    th = e12.require_thresholds(d)
    p4b.require_signed(PREREG)
    tst = predict_set(su, su.te, su.test, cnt, cal, prior, sl)
    arr = {f"{NAME}|Su": tst["Su"], f"{NAME}|Wu": tst["Wu"], "blocks": su.cells[tst["tgt_idx"]], "static_bin": tst["static_bin"]}
    for k in (NAME, CAL):
        arr[f"{k}|S"] = tst["arms"][k]["S"]; arr[f"{k}|Wn"] = tst["arms"][k]["Wn"]
    for arm in ("G0", "G1"):
        r = e12.e9_record(city, f, seed, arm)
        with np.load(E9RUNS / r["config_fingerprint"] / "test_hidden.npz") as z:
            if not np.array_equal(z["nodes"], tst["tgt_idx"]):
                raise SystemExit(f"STOP: {city} {f} {seed} {arm}: test-hidden nodes differ from E9")
            S, Wn, *_ = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"])
        arr[f"{arm}|S"] = S; arr[f"{arm}|Wn"] = Wn
    db = BISRUNS / d.name; rb = json.loads((db / "run.json").read_text())
    if p4b.sha256(db / "sums.npz", 16) != rb["sums_sha256"]:
        raise SystemExit(f"STOP: {db}/sums.npz fingerprint differs")
    with np.load(db / "sums.npz") as z:
        if not (np.array_equal(z["blocks"], arr["blocks"]) and np.array_equal(z["static_bin"], arr["static_bin"])):
            raise SystemExit(f"STOP: {d.name}: blocks or bins differ from E12-bis")
        arr[f"{BIS}|S"] = z[f"{BIS}|S"]; arr[f"{BIS}|Wn"] = z[f"{BIS}|Wn"]
    np.savez_compressed(d / "sums.npz", **arr)
    rec = {"city": city, "f": f, "seed": seed, "slots": NS, "n_min": N_MIN, "prior": prior.tolist(),
           "fallbacks": tst["fallbacks"],
           "calendar_table": cal.tolist(),
           "red": {k: {"recall": float((tst["arms"][k]["red_pos"] >= th[k]).mean()) if tst["arms"][k]["red_pos"].size else float("nan"),
                       "false_alarm_rate": float((tst["arms"][k]["red_neg"] >= th[k]).mean()) if tst["arms"][k]["red_neg"].size else float("nan")}
                   for k in (NAME, CAL)},
           "share_by_bin": {BIN_LABELS[b]: float((tst["static_bin"] == b).mean()) for b in range(NB)},
           "thresholds_sha256": p4b.sha256(d / "thresholds.json", 16), "sums_sha256": p4b.sha256(d / "sums.npz", 16),
           "e12bis_sums_sha256": rb["sums_sha256"], "setup": su.fingerprints(), "code": code_fp(),
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

def diff(cell, rng_seed, a, b):
    """D = V(a) − V(b), with replicates paired through the same generator."""
    pa, ra = v_cell(cell, np.random.default_rng(rng_seed), a)
    pb, rb = v_cell(cell, np.random.default_rng(rng_seed), b)
    lo, hi = np.percentile(ra - rb, [2.5, 97.5])
    return {"D": pa - pb, "L": float(lo), "U": float(hi)}


def freeze(args):
    if (OUT / "CONGELAMENTO_E12ter.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12ter.md exists; regenerate only on purpose, after moving it")
    rows = {}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds, recs = {}, []
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"; rec = json.loads((d / "run.json").read_text()); recs.append(rec)
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz")
            arms = {a: (z[f"{a}|S"], z[f"{a}|Wn"]) for a in (NAME, CAL, BIS, "G0", "G1")}
            arms[f"{NAME} (unweighted)"] = (z[f"{NAME}|Su"], z[f"{NAME}|Wu"])
            seeds[s] = {"blocks": z["blocks"], "arms": arms, "bin": z["static_bin"]}
        cell = {"seeds": seeds}; row = {}
        row["overall"] = summary(*v_cell(cell, np.random.default_rng([BOOT, ci]), NAME))
        row["calendar"] = summary(*v_cell(cell, np.random.default_rng([BOOT, ci]), CAL))
        row["minus_calendar"] = diff(cell, [BOOT, ci], NAME, CAL)
        row["minus_E12bis"] = diff(cell, [BOOT, ci], NAME, BIS)
        row["unweighted"] = summary(*v_cell(cell, np.random.default_rng([BOOT, ci]), f"{NAME} (unweighted)"))
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
            g = [BOOT, ci, 1 + b]
            e_ = summary(*v_cell(sub, np.random.default_rng(g), NAME)); e_["min_blocks"] = int(min(nblocks))
            e_["calendar"] = summary(*v_cell(sub, np.random.default_rng(g), CAL))
            e_["minus_calendar"] = diff(sub, g, NAME, CAL)
            e_["minus_E12bis"] = diff(sub, g, NAME, BIS)
            if min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            row["by_bin"][lab] = e_
        row["share_by_bin"] = {lab: float(np.mean([r["share_by_bin"][lab] for r in recs])) for lab in BIN_LABELS}
        row["red"] = {k: {q: float(np.nanmean([r["red"][k][q] for r in recs])) for q in ("recall", "false_alarm_rate")}
                      for k in (NAME, CAL)}
        fb = [r["fallbacks"] for r in recs]
        row["fallbacks"] = {"to_E12bis_row": sum(x["to_E12bis_row"] for x in fb) / sum(x["lookups"] for x in fb),
                            "to_prior": sum(x["to_prior"] for x in fb) / sum(x["lookups"] for x in fb),
                            "calendar_to_prior": sum(x["calendar_to_prior"] for x in fb) / sum(x["lookups"] for x in fb),
                            "inner_to_E12bis_row": (sum(x["by_bin"][BIN_LABELS[0]]["to_E12bis_row"] for x in fb)
                                                    / max(sum(x["by_bin"][BIN_LABELS[0]]["lookups"] for x in fb), 1))}
        rows[(city, f)] = row
    inner = BIN_LABELS[0]
    def holds(r):
        e = r["by_bin"][inner]
        return e.get("V") is not None and "note" not in e and e["L"] > 0 and e["V"] >= MARGIN
    hits = [(c, f) for (c, f), r in rows.items() if holds(r)]
    levels = sorted({f for (c, f) in hits if sum(1 for (c2, f2) in hits if f2 == f) >= 2})
    if levels:
        st = "neighbour and calendar buy wCE within 250 m at f = " + ", ".join(f"{int(x * 100)}%" for x in levels)
    elif all(r["by_bin"][inner].get("V") is not None and r["by_bin"][inner]["U"] < MARGIN for r in rows.values()):
        st = "neighbour and calendar do not buy wCE within 250 m"
    else:
        st = "undetermined"
    write(rows, st, len(hits))
    if args.compare_with:
        old = json.loads(Path(args.compare_with).read_text()); new = json.loads((OUT / "e12ter_risultati.json").read_text())
        dk = [k for k in old if k not in ("commit", "code_dirty", "generator_fingerprint", "written") and old[k] != new.get(k)]
        print("comparison:", "every number identical" if not dk else f"DIFFERENT keys: {dk}")
        return 0 if not dk else 3
    return 0


def write(rows, st, nhits):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "summary_statement": st, "pairs_inner_bin_hit": nhits,
           "commit": c, "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "generator_fingerprint": p4b.sha256(Path(__file__), 16), "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12ter_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: "—" if x is None else f"{x:+.2f}"  # noqa: E731
    def cv(e):
        if e is None or e.get("V") is None:
            return "—"
        return f"{fm(e['V'])} [{fm(e['L'])}; {fm(e['U'])}]" + (" *" if "note" in e else "")
    def cd(e, mark=False):
        return "—" if e is None else f"{fm(e['D'])} [{fm(e['L'])}; {fm(e['U'])}]" + (" *" if mark else "")
    L = ["# CONGELAMENTO_E12ter — calibrated neighbour with the calendar\n",
         f"Generated by `paper4/code/e12ter.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12ter.md` ({res['prereg_fingerprint']}). Inputs: 60 (city, f, "
         f"seed) runs under `paper4/runs/e12ter/`; G0 and G1 from the E9 campaign; E12-bis sums from `paper4/runs/e12bis/`. "
         f"Slots: hour of the week of t + h (168). V in points of the G0 wCE, positive = better than G0. Intervals: 95%, {B} "
         f"replicates, seeds × corridor blocks; overall with the E9 replicate indices, per bin with default_rng([20261106, "
         f"index of (city, f), 1 + bin]); differences paired on the same replicates.\n",
         f"## Summary statement (criterion on the 0–250 m bin, as E12-bis)\n\n**{st}** — (city, f) pairs where V(E12-ter) in "
         f"the 0–250 m bin is favourable and ≥ 3 points: {nhits} of 12.\n",
         "## V(E12-ter) against G0, overall and by distance bin of the hidden segment\n",
         "| City | f | Overall | " + " | ".join(BIN_LABELS) + " | Share of hidden segments by bin |",
         "|---|---|---|" + "---|" * NB + "---|"]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cv(r['overall'])} | " + " | ".join(cv(r["by_bin"][b]) for b in BIN_LABELS)
                 + " | " + " / ".join(f"{r['share_by_bin'][b]:.2f}" for b in BIN_LABELS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed: interval not read.\n",
          "## Secondary: value of the neighbour net of the calendar\n",
          "V(E12-ter) − V(calendar only), same replicates. Positive = the neighbour's class adds to the calendar.\n",
          "| City | f | V(calendar) overall | V(E12-ter) − V(calendar), overall | " + " | ".join(f"V(E12-ter) − V(calendar), {b}" for b in BIN_LABELS) + " |",
          "|---|---|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        cells = []
        for b in BIN_LABELS:
            e = r["by_bin"][b]
            cells.append("—" if e.get("V") is None else cd(e["minus_calendar"], "note" in e))
        L.append(f"| {city} | {int(f * 100)}% | {cv(r['calendar'])} | {cd(r['minus_calendar'])} | " + " | ".join(cells) + " |")
    L += ["\n## Reported without a criterion\n",
          "| City | f | V(calendar), 0–250 m | V(E12-ter) − V(E12-bis), overall | V(E12-ter) − V(E12-bis), 0–250 m | V unweighted (q′ only) | V per horizon 15 / 30 / 60 / 120 min |",
          "|---|---|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        e = r["by_bin"][BIN_LABELS[0]]
        ph = " / ".join(fm(v["V"]) for v in r["per_horizon"].values())
        L.append(f"| {city} | {int(f * 100)}% | {cv(e.get('calendar')) if e.get('V') is not None else '—'} | {cd(r['minus_E12bis'])} | "
                 + (cd(e["minus_E12bis"], "note" in e) if e.get("V") is not None else "—")
                 + f" | {fm(r['unweighted']['V'])} | {ph} |")
    L += ["\n| City | f | Lookups to the E12-bis row (all / 0–250 m) | Lookups to the prior | Calendar lookups to the prior | Red recall at 5% FA (realised FA), E12-ter; calendar — descriptive |",
          "|---|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        fb = r["fallbacks"]; rd = r["red"]
        L.append(f"| {city} | {int(f * 100)}% | {fb['to_E12bis_row']:.3f} / {fb['inner_to_E12bis_row']:.3f} | {fb['to_prior']:.3f} | "
                 f"{fb['calendar_to_prior']:.3f} | {rd[NAME]['recall']:.3f} ({rd[NAME]['false_alarm_rate']:.3f}); "
                 f"{rd[CAL]['recall']:.3f} ({rd[CAL]['false_alarm_rate']:.3f}) |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Both tables from observed→observed pairs in the training period only; slots from the timestamps of t + h; "
          "thresholds on validation saved with fingerprint before any test metric; node sets, origins, test-hidden nodes, "
          "blocks and bins identical to E9 and E12-bis (checked by the run).",
          "2. Red recall is descriptive: the predictions take few distinct values, so the 5% false-alarm target may not be met on test.",
          "3. Cells without a valid target excluded from every mean, as in E9."]
    mp = OUT / "CONGELAMENTO_E12ter.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def check_inputs(args):
    """After `run`: 60 folders, fingerprints of sums and thresholds, code recorded, setup equal to E9, keys.
    No metric is read."""
    _, by = runs_by_key(E9RUNS); bad, found = [], 0
    keys = {f"{NAME}|S", f"{NAME}|Wn", f"{NAME}|Su", f"{NAME}|Wu", f"{CAL}|S", f"{CAL}|Wn", f"{BIS}|S", f"{BIS}|Wn",
            "G0|S", "G0|Wn", "G1|S", "G1|Wn", "blocks", "static_bin"}
    code_now = code_fp()
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
        if r["e12bis_sums_sha256"] != p4b.sha256(BISRUNS / d.name / "sums.npz", 16):
            bad.append(f"{d.name}: E12-bis sums changed")
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
    """freeze end to end on 60 synthetic folders: within 0-250 m E12-ter is 5% of wCE better than G0 at f >= 40%,
    the calendar equals G0 and E12-bis is 2% better there; nothing elsewhere. The statement must name 40% and 60%,
    V − V(calendar) within 250 m at Madrid 40% must be 5 and V − V(E12-bis) must be 3."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12ter"; runs.mkdir(parents=True); g = np.random.default_rng(5)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15)
        W0 = g.uniform(50, 100, (n, len(H))); S0 = W0 * g.uniform(1.05, 1.1, (n, 1))
        inner = ((sb == 0) & (f >= 0.4))[:, None]
        fac = np.where(inner, 0.95, 1.0); fb = np.where(inner, 0.98, 1.0)
        arr = {f"{NAME}|S": S0 * fac, f"{NAME}|Wn": W0, f"{NAME}|Su": S0 * fac, f"{NAME}|Wu": W0,
               f"{CAL}|S": S0, f"{CAL}|Wn": W0, f"{BIS}|S": S0 * fb, f"{BIS}|Wn": W0,
               "G0|S": S0, "G0|Wn": W0, "G1|S": S0, "G1|Wn": W0, "blocks": blocks, "static_bin": sb}
        np.savez_compressed(d / "sums.npz", **arr)
        z = {"to_E12bis_row": 0, "to_prior": 0, "lookups": 1}
        rec = {"sums_sha256": p4b.sha256(d / "sums.npz", 16), "share_by_bin": {b: 0.25 for b in BIN_LABELS},
               "red": {k: {"recall": 0.05, "false_alarm_rate": 0.05} for k in (NAME, CAL)},
               "fallbacks": {**z, "calendar_to_prior": 0, "by_bin": {b: z for b in BIN_LABELS}}}
        (d / "run.json").write_text(json.dumps(rec))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(argparse.Namespace(compare_with=None))
    res = json.loads((OUT / "e12ter_risultati.json").read_text()); st = res["summary_statement"]
    e = res["rows"]["madrid 0.4"]["by_bin"][BIN_LABELS[0]]
    v, dc, db = e["V"], e["minus_calendar"]["D"], e["minus_E12bis"]["D"]
    print(f"synthetic statement: {st}; within 250 m at madrid 40%: V = {v:.4f} (expected 5), V − V(calendar) = {dc:.4f} "
          f"(expected 5), V − V(E12-bis) = {db:.4f} (expected 3)")
    ok = (st == "neighbour and calendar buy wCE within 250 m at f = 40%, 60%" and abs(v - 5) < 1e-9
          and abs(dc - 5) < 1e-9 and abs(db - 3) < 1e-9)
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-ter")
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
