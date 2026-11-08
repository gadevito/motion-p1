#!/usr/bin/env python3
"""
E12-quater — the neighbour net of the calendar, with a symmetric fallback (`protocol/paper4/E12quater.md`).
=========================================================================================================
No training. Imports `p4b.py`, `e9.py`, `e12.py`, `e12bis.py`, `e12ter.py` and the resample of
`genera_congelamento_e9.py` unchanged. Everything is E12-ter except the fallback chain of the table with the
neighbour:

  link 1  neighbour row (slot(t+h), b, bin(d), h)    if a valid neighbour exists and the row holds >= N_MIN pairs
  link 2  calendar row (slot(t+h), h)                otherwise, if it holds >= N_MIN pairs
  link 3  prior                                      otherwise

The calendar-only table uses links 2 and 3 (as in E12-ter). Wherever link 1 is not used, E12-quater and the
calendar give the same forecast; their difference D' comes only from rows that carry the neighbour.

    selftest      planted calendar and short-range copy; the three links against E12-ter, the calendar and the prior
    preflight     controls 1-7 of E12quater.md, reading no test target
    cost          tables and validation predictions for Madrid f = 40% seed 0, scaled to the test origins
    run           after the signature: per (city, f, seed) tables (checked against the E12-ter run records),
                  thresholds on validation saved with fingerprint, then per-node sums on test-hidden segments
    check-inputs  after run: 60 folders, fingerprints, code, setup, keys (no metric read)
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E12quater.md and e12quater_risultati.json from paper4/runs/e12quater/

Usage: $PY paper4/code/e12quater.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
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
import e12bis  # noqa: E402
import e12ter  # noqa: E402
from e12 import neighbours, labels, sums, transform, training_stats, BIN_LABELS  # noqa: E402
from e12bis import bin_of, v_cell, summary, NB, B, BOOT, MARGIN  # noqa: E402
from e12ter import slot168, tables, q_ter, q_cal, slot_checks, diff, synthetic_world, N_MIN, NS  # noqa: E402
from genera_congelamento_e9 import runs_by_key  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12quater.md"
RUNS = e9.RUNS / "e12quater"
TERRUNS = e9.RUNS / "e12ter"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
H = p4b.HORIZONS
NAME, CAL, TER = "E12-quater", "Calendar", "E12-ter"
LINKS = ("neighbour row", "calendar row", "prior")


# ---------------------------------------------------------------- prediction ---------------------------

def q_quater(C, origins, obs_idx, order_n, d_n, cnt, cal, prior, sl):
    """q (T, H, 3) of E12-quater for one hidden segment, and the link used for every lookup (T, H): 1, 2, 3."""
    cobs = C[origins][:, obs_idx[order_n]]; valid = cobs > 0
    anyv = valid.any(1); first = valid.argmax(1)
    b = np.clip(cobs[np.arange(len(origins)), first] - 1, 0, 2); bn = bin_of(d_n[first])
    q = np.zeros((len(origins), len(H), 3)); link = np.zeros((len(origins), len(H)), np.int8)
    for hi, h in enumerate(H):
        s = sl[origins + h]
        rows = cnt[s, bn, hi, b]; tot = rows.sum(1)
        crow = cal[s, hi]; ctot = crow.sum(1)
        u1 = anyv & (tot >= N_MIN)
        u2 = ~u1 & (ctot >= N_MIN)
        u3 = ~(u1 | u2)
        q[u1, hi] = rows[u1] / tot[u1, None]
        q[u2, hi] = crow[u2] / ctot[u2, None]
        q[u3, hi] = prior
        link[u1, hi] = 1; link[u2, hi] = 2; link[u3, hi] = 3
    return q, link


def predict_set(su, origins, tgt_mask, cnt, cal, prior, sl):
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    qc, _ = q_cal(origins, cal, prior, sl)
    pc = transform(qc, prior, su.W)
    out = {k: {"S": [], "Wn": [], "red_pos": [], "red_neg": []} for k in (NAME, CAL)}
    Su, Wu = [], []
    sbin = bin_of(dist[:, 0]); links = np.zeros((NB, 3), np.int64)
    for i, n in enumerate(tgt_idx):
        y = labels(su.C, origins, n); v = y >= 0
        q, link = q_quater(su.C, origins, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
        links[sbin[i]] += [(link == k).sum() for k in (1, 2, 3)]
        p = transform(q, prior, su.W); pu = transform(q, prior, su.W, weighted=False)
        for k, pp in ((NAME, p), (CAL, pc)):
            s, w = sums(pp, y, su.W); out[k]["S"].append(s); out[k]["Wn"].append(w)
            out[k]["red_pos"].append(pp[..., 2][v & (y == 2)]); out[k]["red_neg"].append(pp[..., 2][v & (y != 2)])
        s, w = sums(pu, y, su.W); Su.append(s); Wu.append(w)
    for k in out:
        o = out[k]; o["S"] = np.array(o["S"]); o["Wn"] = np.array(o["Wn"])
        o["red_pos"] = np.concatenate(o["red_pos"]); o["red_neg"] = np.concatenate(o["red_neg"])
    return {"arms": out, "Su": np.array(Su), "Wu": np.array(Wu), "tgt_idx": tgt_idx, "static_bin": sbin,
            "links": {BIN_LABELS[b]: {LINKS[k]: int(links[b, k]) for k in range(3)} for b in range(NB)}}


def link_checks(C, origins, obs_idx, order_n, d_n, cnt, cal, prior, sl):
    """Controls 2-4 for one segment: link 1 = E12-ter row, link 2 = calendar row, link 3 = prior, to the bit;
    the three links cover every lookup. Returns (ok1, ok2, ok3, cover, counts)."""
    q, link = q_quater(C, origins, obs_idx, order_n, d_n, cnt, cal, prior, sl)
    qt, _ = q_ter(C, origins, obs_idx, order_n, d_n, cnt, cnt.sum(0), prior, sl)
    qc, _ = q_cal(origins, cal, prior, sl)
    m1, m2, m3 = link == 1, link == 2, link == 3
    ok1 = bool(np.array_equal(q[m1], qt[m1]))
    ok2 = bool(np.array_equal(q[m2], qc[m2]))
    ok3 = bool(np.array_equal(q[m3], np.broadcast_to(prior, q[m3].shape)) and
               np.array_equal(qc[m3], np.broadcast_to(prior, qc[m3].shape)))
    cover = bool((m1 | m2 | m3).all() and not (m1 & m2).any() and not (m1 & m3).any() and not (m2 & m3).any())
    return ok1, ok2, ok3, cover, (int(m1.sum()), int(m2.sum()), int(m3.sum()))


# ---------------------------------------------------------------- self-test ----------------------------

def selftest():
    """E12-ter's synthetic world (planted calendar, planted copy within ~60 m), with N_MIN raised in a copy of the
    tables so that all three links occur. Checks: links 1-3 to the bit, coverage, probabilities, causality, and
    E12-quater beats the calendar most within 250 m."""
    C, coords, obs, ts, sl = synthetic_world(); ok = True
    obs_idx = np.where(obs)[0]; hid = np.where(~obs)[0]
    reg_end = 5000; tr = np.arange(20, reg_end - max(H)); te = np.arange(5200, len(ts) - max(H))
    prior = training_stats(C, obs, reg_end); W = (1 / (3 * prior)).astype("float32")
    cnt, cal = tables(C, obs_idx, coords, tr, sl)
    cal_thin = cal.copy(); cal_thin[::3] = 0                       # some calendar rows below N_MIN: link 3 occurs
    order, dist = neighbours(coords, obs_idx, hid)
    seen = np.zeros(3, np.int64); acc = {}
    C3 = C.copy(); C3[te.max() + 1:] = 2; C3[:, hid] = 3
    for i in range(len(hid)):
        for cl in (cal, cal_thin):
            o1, o2, o3, cov, n = link_checks(C, te, obs_idx, order[i], dist[i], cnt, cl, prior, sl)
            ok &= o1 and o2 and o3 and cov; seen += n
        q, _ = q_quater(C, te, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
        q3, _ = q_quater(C3, te, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
        ok &= bool(np.array_equal(q, q3))
        y = labels(C, te, hid[i]); b = int(bin_of(dist[i, 0]))
        qc, _ = q_cal(te, cal, prior, sl)
        r = acc.setdefault(b, np.zeros(4))
        for k, qq in enumerate((q, qc)):
            p = transform(qq, prior, W)
            ok &= bool(np.isfinite(p).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
            s, w = sums(p, y, W); r[2 * k] += s.sum(); r[2 * k + 1] += w.sum()
    ok &= bool((seen > 0).all())
    gain = {BIN_LABELS[b]: 100 * (r[2] / r[3] - r[0] / r[1]) / (r[2] / r[3]) for b, r in sorted(acc.items()) if r[1] > 0}
    print("lookups per link (neighbour row / calendar row / prior):", seen.tolist(),
          "; gain of E12-quater over the calendar by bin:", {k: round(v, 1) for k, v in gain.items()})
    inner = gain.get(BIN_LABELS[0], -1e9); outer = [v for k, v in gain.items() if k != BIN_LABELS[0]]
    ok &= inner > 10 and len(outer) >= 1 and all(inner > v for v in outer)
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def link_shares(su, origins, tgt_mask, cnt, cal, prior, sl):
    """Share of lookups served by each link, by static bin; reads no target."""
    obs_idx = np.where(su.obs)[0]; tgt_idx = np.where(tgt_mask)[0]
    order, dist = neighbours(su.al["coords"], obs_idx, tgt_idx)
    sbin = bin_of(dist[:, 0]); acc = np.zeros((NB, 3))
    for i in range(len(tgt_idx)):
        _, link = q_quater(su.C, origins, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
        acc[sbin[i]] += [(link == k).sum() for k in (1, 2, 3)]
    return {BIN_LABELS[b]: (tuple(np.round(acc[b] / acc[b].sum(), 3)) if acc[b].sum() else None) for b in range(NB)}


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12quater_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-quater preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, by = runs_by_key(E9RUNS)
    fp_ok = ter_ok = l1 = l2 = l3 = cov = caus = prob = slot_ok = True; shares = {}
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                d = TERRUNS / f"{city}_{int(f * 100)}_s{s}"
                rt = json.loads((d / "run.json").read_text())
                ter_ok &= p4b.sha256(d / "sums.npz", 16) == rt["sums_sha256"] and rt["setup"] == su.fingerprints()
                if s != 0:
                    continue
                sl = slot168(su.ts); slot_ok &= slot_checks(su, sl)
                obs_idx = np.where(su.obs)[0]
                cnt, cal = tables(su.C, obs_idx, su.al["coords"], su.tr, sl)
                ter_ok &= bool(np.array_equal(cal, np.array(rt["calendar_table"])))
                prior = training_stats(su.C, su.obs, su.reg_end)
                shares[f"{city} {int(f * 100)}%"] = link_shares(su, su.va, su.val, cnt, cal, prior, sl)
                vidx = np.where(su.val)[0]; orig = su.va[:200]
                order, dist = neighbours(su.al["coords"], obs_idx, vidx)
                for i in range(0, len(vidx), 25):
                    o1, o2, o3, cv, _ = link_checks(su.C, orig, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
                    l1 &= o1; l2 &= o2; l3 &= o3; cov &= cv
                    if city == "madrid" and f == 0.4:
                        C3 = su.C.copy(); C3[orig.max() + 1:] = 2; C3[:, ~su.obs] = 3
                        q, _ = q_quater(su.C, orig, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
                        q3, _ = q_quater(C3, orig, obs_idx, order[i], dist[i], cnt, cal, prior, sl)
                        caus &= bool(np.array_equal(q, q3))
                        p = transform(q, prior, su.W)
                        prob &= bool(np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(-1), 1, atol=1e-6))
    log.check("1", "node sets, origins, class weights identical to the E9 run records; E12-ter run records present with "
              "matching sums fingerprints and setup (60 pairs); calendar table equal to the one recorded by E12-ter "
              "(12 city × f, seed 0)", fp_ok and ter_ok)
    log.check("2", "link 1: where the neighbour row is used, E12-quater = E12-ter to the bit (validation cells, 12 city × f, "
              "seed 0, every 25th segment, 200 origins)", l1)
    log.check("3", "link 2: where the neighbour row is not used and the calendar row is, E12-quater = calendar to the bit", l2)
    log.check("4", "link 3: where neither is used, E12-quater and the calendar both equal the prior to the bit; the three "
              "links cover every lookup and are disjoint", l3 and cov)
    log.check("6", "slots from the timestamps of t + h only, checked for every origin (12 city × f, seed 0); causality: noise "
              "after t and on hidden segments leaves q identical (Madrid 40%); every p is a probability", slot_ok and caus and prob)
    log.check("6b", "synthetic world (planted calendar and short-range copy, thin calendar rows): links to the bit, all "
              "three links used, E12-quater beats the calendar most within 250 m (selftest)", selftest() == 0)
    try:
        e12.require_thresholds(RUNS / "nonexistent"); th = False
    except SystemExit:
        th = True
    log.check("7", "a test metric is refused without the validation-threshold file and its fingerprint", th)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test metrics refused while the E12-quater signature line is blank", guard)
    log(f"control 5, descriptive, no target read: share of validation-hidden lookups served by each link "
        f"({' / '.join(LINKS)}), by static bin {' | '.join(BIN_LABELS)}, seed 0:")
    for k, v in shares.items():
        log(f"  {k}: " + " | ".join("—" if x is None else " / ".join(f"{y:.3f}" for y in x) for x in v.values()))
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
    path = e9.RUNS / "e12quater_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def code_fp():
    return {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
            "e12.py": p4b.sha256(Path(e12.__file__), 16), "e12bis.py": p4b.sha256(Path(e12bis.__file__), 16),
            "e12ter.py": p4b.sha256(Path(e12ter.__file__), 16), "e12quater.py": p4b.sha256(Path(__file__), 16)}


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
    dt = TERRUNS / d.name; rt = json.loads((dt / "run.json").read_text())
    if p4b.sha256(dt / "sums.npz", 16) != rt["sums_sha256"] or rt["setup"] != su.fingerprints():
        raise SystemExit(f"STOP: {dt}: E12-ter record differs")
    obs_idx = np.where(su.obs)[0]
    cnt, cal = tables(su.C, obs_idx, su.al["coords"], su.tr, sl)
    if not np.array_equal(cal, np.array(rt["calendar_table"])):
        raise SystemExit(f"STOP: {d.name}: calendar table differs from E12-ter")
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
    with np.load(dt / "sums.npz") as z:
        if not (np.array_equal(z["blocks"], arr["blocks"]) and np.array_equal(z["static_bin"], arr["static_bin"])):
            raise SystemExit(f"STOP: {d.name}: blocks or bins differ from E12-ter")
        if not (np.array_equal(z[f"{CAL}|S"], arr[f"{CAL}|S"]) and np.array_equal(z[f"{CAL}|Wn"], arr[f"{CAL}|Wn"])):
            raise SystemExit(f"STOP: {d.name}: calendar sums differ from E12-ter")
        for a in (TER, "G0", "G1"):
            arr[f"{a}|S"] = z[f"{a}|S"]; arr[f"{a}|Wn"] = z[f"{a}|Wn"]
    np.savez_compressed(d / "sums.npz", **arr)
    rec = {"city": city, "f": f, "seed": seed, "slots": NS, "n_min": N_MIN, "prior": prior.tolist(), "links": tst["links"],
           "ter_fallbacks": rt["fallbacks"],
           "red": {k: {"recall": float((tst["arms"][k]["red_pos"] >= th[k]).mean()) if tst["arms"][k]["red_pos"].size else float("nan"),
                       "false_alarm_rate": float((tst["arms"][k]["red_neg"] >= th[k]).mean()) if tst["arms"][k]["red_neg"].size else float("nan")}
                   for k in (NAME, CAL)},
           "share_by_bin": {BIN_LABELS[b]: float((tst["static_bin"] == b).mean()) for b in range(NB)},
           "thresholds_sha256": p4b.sha256(d / "thresholds.json", 16), "sums_sha256": p4b.sha256(d / "sums.npz", 16),
           "e12ter_sums_sha256": rt["sums_sha256"], "setup": su.fingerprints(), "code": code_fp(),
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

def freeze(args):
    if (OUT / "CONGELAMENTO_E12quater.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12quater.md exists; regenerate only on purpose, after moving it")
    rows = {}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds, recs = {}, []
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"; rec = json.loads((d / "run.json").read_text()); recs.append(rec)
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz")
            arms = {a: (z[f"{a}|S"], z[f"{a}|Wn"]) for a in (NAME, CAL, TER, "G0", "G1")}
            arms[f"{NAME} (unweighted)"] = (z[f"{NAME}|Su"], z[f"{NAME}|Wu"])
            seeds[s] = {"blocks": z["blocks"], "arms": arms, "bin": z["static_bin"]}
        cell = {"seeds": seeds}; row = {}
        g = [BOOT, ci]
        row["overall"] = summary(*v_cell(cell, np.random.default_rng(g), NAME))
        row["calendar"] = summary(*v_cell(cell, np.random.default_rng(g), CAL))
        row["Dq"] = diff(cell, g, NAME, CAL)                      # D' = V(E12-quater) − V(calendar)
        row["D"] = diff(cell, g, TER, CAL)                        # D of E12-ter, same replicates
        row["Dq_minus_D"] = diff(cell, g, NAME, TER)              # D' − D = V(E12-quater) − V(E12-ter)
        row["unweighted"] = summary(*v_cell(cell, np.random.default_rng(g), f"{NAME} (unweighted)"))
        row["per_horizon"] = {f"{15 * h} min": summary(*v_cell(cell, np.random.default_rng(g), NAME, hz=k))
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
            gb = [BOOT, ci, 1 + b]
            e_ = summary(*v_cell(sub, np.random.default_rng(gb), NAME)); e_["min_blocks"] = int(min(nblocks))
            e_["Dq"] = diff(sub, gb, NAME, CAL); e_["D"] = diff(sub, gb, TER, CAL); e_["Dq_minus_D"] = diff(sub, gb, NAME, TER)
            if min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            row["by_bin"][lab] = e_
        row["share_by_bin"] = {lab: float(np.mean([r["share_by_bin"][lab] for r in recs])) for lab in BIN_LABELS}
        row["red"] = {k: {q: float(np.nanmean([r["red"][k][q] for r in recs])) for q in ("recall", "false_alarm_rate")}
                      for k in (NAME, CAL)}
        row["links"] = {}
        for lab in BIN_LABELS + ("all",):
            labs = BIN_LABELS if lab == "all" else (lab,)
            tot = {k: sum(r["links"][x][k] for r in recs for x in labs) for k in LINKS}
            n = sum(tot.values())
            row["links"][lab] = {k: (tot[k] / n if n else None) for k in LINKS}
        tf = [r["ter_fallbacks"] for r in recs]
        row["ter_to_E12bis_row"] = sum(x["to_E12bis_row"] for x in tf) / sum(x["lookups"] for x in tf)
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
        old = json.loads(Path(args.compare_with).read_text()); new = json.loads((OUT / "e12quater_risultati.json").read_text())
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
    jp = OUT / "e12quater_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    fm = lambda x: "—" if x is None else f"{x:+.2f}"  # noqa: E731
    def cv(e):
        if e is None or e.get("V") is None:
            return "—"
        return f"{fm(e['V'])} [{fm(e['L'])}; {fm(e['U'])}]" + (" *" if "note" in e else "")
    def cd(e, mark=False):
        return "—" if e is None else f"{fm(e['D'])} [{fm(e['L'])}; {fm(e['U'])}]" + (" *" if mark else "")
    def bin_d(r, key):
        return [("—" if r["by_bin"][b].get("V") is None else cd(r["by_bin"][b][key], "note" in r["by_bin"][b])) for b in BIN_LABELS]
    L = ["# CONGELAMENTO_E12quater — the neighbour net of the calendar, with a symmetric fallback\n",
         f"Generated by `paper4/code/e12quater.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12quater.md` ({res['prereg_fingerprint']}). Inputs: 60 "
         f"(city, f, seed) runs under `paper4/runs/e12quater/`; G0 and G1 of E9 and the E12-ter sums, copied from "
         f"`paper4/runs/e12ter/` with their fingerprints. Fallback chain: neighbour row → calendar row → prior (N_min = {N_MIN}). "
         f"V in points of the G0 wCE, positive = better than G0. Intervals: 95%, {B} replicates, seeds × corridor blocks, with "
         f"E12-ter's replicate indices; differences paired on the same replicates.\n",
         f"## Summary statement (criterion on the 0–250 m bin, as E12-ter)\n\n**{st}** — (city, f) pairs where V(E12-quater) in "
         f"the 0–250 m bin is favourable and ≥ 3 points: {nhits} of 12.\n",
         "## V(E12-quater) against G0, overall and by distance bin of the hidden segment\n",
         "| City | f | Overall | " + " | ".join(BIN_LABELS) + " |", "|---|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cv(r['overall'])} | " + " | ".join(cv(r["by_bin"][b]) for b in BIN_LABELS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed: interval not read.\n",
          "## Secondary: D′ = V(E12-quater) − V(calendar), beside D of E12-ter\n",
          "| City | f | D′ overall | " + " | ".join(f"D′ {b}" for b in BIN_LABELS) + " |", "|---|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cd(r['Dq'])} | " + " | ".join(bin_d(r, "Dq")) + " |")
    L += ["\n| City | f | D (E12-ter) overall | " + " | ".join(f"D {b}" for b in BIN_LABELS) + " |", "|---|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cd(r['D'])} | " + " | ".join(bin_d(r, "D")) + " |")
    L += ["\n| City | f | D′ − D overall | " + " | ".join(f"D′ − D {b}" for b in BIN_LABELS) + " |", "|---|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | {cd(r['Dq_minus_D'])} | " + " | ".join(bin_d(r, "Dq_minus_D")) + " |")
    L += ["\n## Fallback chain: share of test lookups served by each link (neighbour row / calendar row / prior)\n",
          "| City | f | All | " + " | ".join(BIN_LABELS) + " | E12-ter: lookups to the E12-bis row |", "|---|---|---|" + "---|" * NB + "---|"]
    for (city, f), r in rows.items():
        fmt = lambda x: "—" if x[LINKS[0]] is None else " / ".join(f"{x[k]:.3f}" for k in LINKS)  # noqa: E731
        L.append(f"| {city} | {int(f * 100)}% | {fmt(r['links']['all'])} | " + " | ".join(fmt(r["links"][b]) for b in BIN_LABELS)
                 + f" | {r['ter_to_E12bis_row']:.3f} |")
    L += ["\n## Reported without a criterion\n",
          "| City | f | V(calendar) overall | V unweighted (q′ only) | V per horizon 15 / 30 / 60 / 120 min | Red recall at 5% FA (realised FA), E12-quater; calendar — descriptive |",
          "|---|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        ph = " / ".join(fm(v["V"]) for v in r["per_horizon"].values()); rd = r["red"]
        L.append(f"| {city} | {int(f * 100)}% | {cv(r['calendar'])} | {fm(r['unweighted']['V'])} | {ph} | "
                 f"{rd[NAME]['recall']:.3f} ({rd[NAME]['false_alarm_rate']:.3f}); {rd[CAL]['recall']:.3f} ({rd[CAL]['false_alarm_rate']:.3f}) |")
    L += ["\n## Controls, deviations and defects\n",
          "1. Tables from observed→observed pairs in the training period only, calendar table equal to E12-ter's; slots from "
          "the timestamps of t + h; thresholds on validation saved with fingerprint before any test metric; node sets, "
          "origins, test-hidden nodes, blocks, bins and calendar sums identical to E9 and E12-ter (checked by the run).",
          "2. Red recall is descriptive: the predictions take few distinct values.",
          "3. Cells without a valid target excluded from every mean, as in E9."]
    mp = OUT / "CONGELAMENTO_E12quater.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def check_inputs(args):
    """After `run`: 60 folders, fingerprints of sums and thresholds, code recorded, setup equal to E9, E12-ter sums
    unchanged, keys. No metric is read."""
    _, by = runs_by_key(E9RUNS); bad, found = [], 0
    keys = {f"{NAME}|S", f"{NAME}|Wn", f"{NAME}|Su", f"{NAME}|Wu", f"{CAL}|S", f"{CAL}|Wn", f"{TER}|S", f"{TER}|Wn",
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
        if r["e12ter_sums_sha256"] != p4b.sha256(TERRUNS / d.name / "sums.npz", 16):
            bad.append(f"{d.name}: E12-ter sums changed")
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
    """freeze end to end on 60 synthetic folders: within 0-250 m E12-quater is 5% of wCE better than G0 at f >= 40%,
    the calendar equals G0 and E12-ter is 2% better there; nothing elsewhere. The statement must name 40% and 60%; at
    Madrid 40% within 250 m D' must be 5, D 2 and D' − D 3."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12quater"; runs.mkdir(parents=True); g = np.random.default_rng(5)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15)
        W0 = g.uniform(50, 100, (n, len(H))); S0 = W0 * g.uniform(1.05, 1.1, (n, 1))
        inner = ((sb == 0) & (f >= 0.4))[:, None]
        fq = np.where(inner, 0.95, 1.0); ft = np.where(inner, 0.98, 1.0)
        arr = {f"{NAME}|S": S0 * fq, f"{NAME}|Wn": W0, f"{NAME}|Su": S0 * fq, f"{NAME}|Wu": W0,
               f"{CAL}|S": S0, f"{CAL}|Wn": W0, f"{TER}|S": S0 * ft, f"{TER}|Wn": W0,
               "G0|S": S0, "G0|Wn": W0, "G1|S": S0, "G1|Wn": W0, "blocks": blocks, "static_bin": sb}
        np.savez_compressed(d / "sums.npz", **arr)
        lk = {b: {k: 1 for k in LINKS} for b in BIN_LABELS}
        rec = {"sums_sha256": p4b.sha256(d / "sums.npz", 16), "share_by_bin": {b: 0.25 for b in BIN_LABELS},
               "red": {k: {"recall": 0.05, "false_alarm_rate": 0.05} for k in (NAME, CAL)}, "links": lk,
               "ter_fallbacks": {"to_E12bis_row": 0, "lookups": 1}}
        (d / "run.json").write_text(json.dumps(rec))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(argparse.Namespace(compare_with=None))
    res = json.loads((OUT / "e12quater_risultati.json").read_text()); st = res["summary_statement"]
    e = res["rows"]["madrid 0.4"]["by_bin"][BIN_LABELS[0]]
    dq, dd, dqd = e["Dq"]["D"], e["D"]["D"], e["Dq_minus_D"]["D"]
    print(f"synthetic statement: {st}; within 250 m at madrid 40%: D′ = {dq:.4f} (expected 5), D = {dd:.4f} (expected 2), "
          f"D′ − D = {dqd:.4f} (expected 3)")
    ok = (st == "neighbour and calendar buy wCE within 250 m at f = 40%, 60%" and abs(dq - 5) < 1e-9
          and abs(dd - 2) < 1e-9 and abs(dqd - 3) < 1e-9)
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-quater")
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
