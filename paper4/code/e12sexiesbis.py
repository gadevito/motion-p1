#!/usr/bin/env python3
"""
E12-sexies-bis — unnormalised excesses of the neighbour's and the segment's own agreement (`protocol/paper4/
E12sexiesbis.md`). No training, descriptive, no reading rule.
==============================================================================================================
Imports `p4b.py`, `e9.py`, `e12.py`, `e12ter.py`, `e12quinquies.py`, `e12sexies.py` and the resample of
`genera_congelamento_e9.py` unchanged. Pairs, slots, lags, bins and replicate draws as E12-sexies.

For each lag h, on the cells (i, t) where y_j(t), y_i(t) and y_i(t + h) are all valid:
  A(h) = share with y_i(t+h) = y_j(t);  P(h) = share with y_i(t+h) = y_i(t);  E×(h) = Σ_k π_k(s_t)·π_k(s_{t+h})
  X_nb(h) = A(h) − E×(h);  X_own(h) = P(h) − E×(h);  X_nb − X_own = A − P (paired in each replicate)

    selftest      memoryless and persistent neighbour (control 5)
    preflight     controls 1-6 of E12sexiesbis.md, reading no test target
    cost          one (city, f, seed) on validation origins, scaled to the test origins
    run           after the signature: per (city, f, seed) per-node sums on test origins, h = 0 checked against E12-sexies
    check-inputs  after run: 60 folders, fingerprints, code, setup, keys
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E12sexiesbis.md and e12sexiesbis_risultati.json

Usage: $PY paper4/code/e12sexiesbis.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
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
import e12  # noqa: E402
import e12ter  # noqa: E402
import e12quinquies as q5  # noqa: E402
import e12sexies as s6  # noqa: E402
from e12 import neighbours, training_stats, BINS, BIN_LABELS, B, BOOT  # noqa: E402
from e12ter import slot168, NS  # noqa: E402
from e12quinquies import slot_shares, interval, N_MIN  # noqa: E402
from e12sexies import LAGS, minutes  # noqa: E402
from genera_congelamento_e9 import runs_by_key, multiplicities  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12sexiesbis.md"
RUNS = e9.RUNS / "e12sexiesbis"
S6RUNS = e9.RUNS / "e12sexies"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
NB = len(BIN_LABELS)
PER_LAG = ("cells", "nb_agree", "own_agree", "e_x")
KEYS = tuple(f"{k}_{h}" for h in LAGS for k in PER_LAG)


# ---------------------------------------------------------------- quantities ---------------------------

def node_sums(C, origins, obs, tgt, coords, sl, pi_s):
    """Per target segment and lag, on the cells where y_j(t), y_i(t), y_i(t+h) are valid: cells, neighbour and own
    agreements, Σ π(s_t)·π(s_{t+h}). Static distance bin of the nearest observed segment (E12's rule)."""
    obs_idx = np.where(obs)[0]; tgt_idx = np.where(tgt)[0]
    order, dist = neighbours(coords, obs_idx, tgt_idx)
    nn = obs_idx[order[:, 0]]; d = dist[:, 0]
    b = C[origins][:, nn]; a0 = C[origins][:, tgt_idx]; s0 = sl[origins]
    out = {}
    for h in LAGS:
        a = C[origins + h][:, tgt_idx]; sh = sl[origins + h]
        v = (a > 0) & (b > 0) & (a0 > 0)
        ex = (pi_s[s0] * pi_s[sh]).sum(1)
        out.update({f"cells_{h}": v.sum(0).astype(np.int64), f"nb_agree_{h}": ((a == b) & v).sum(0).astype(np.int64),
                    f"own_agree_{h}": ((a == a0) & v).sum(0).astype(np.int64), f"e_x_{h}": (v * ex[:, None]).sum(0)})
    sbin = np.zeros(len(tgt_idx), np.int64)
    for k, (lo, hi) in enumerate(zip(BINS[:-1], BINS[1:])):
        sbin[(d >= lo) & (d < hi)] = k
    return out, tgt_idx, sbin


def ratios(t):
    r = {}
    for h in LAGS:
        n = t[f"cells_{h}"]
        r[f"A_{h}"] = t[f"nb_agree_{h}"] / n; r[f"P_{h}"] = t[f"own_agree_{h}"] / n; r[f"Ex_{h}"] = t[f"e_x_{h}"] / n
        r[f"Xnb_{h}"] = r[f"A_{h}"] - r[f"Ex_{h}"]; r[f"Xown_{h}"] = r[f"P_{h}"] - r[f"Ex_{h}"]
        r[f"Xdiff_{h}"] = r[f"A_{h}"] - r[f"P_{h}"]
    return r


def pooled(cell, rng):
    seeds, sidx, mult = multiplicities(cell, rng)
    pt = {k: float(sum(cell["seeds"][s][k].sum() for s in seeds)) for k in KEYS}
    rep = {}
    for k in KEYS:
        X = np.stack([mult[s] @ cell["seeds"][s][k].astype(float) for s in seeds])
        rep[k] = np.take_along_axis(X.transpose(1, 2, 0), sidx[..., None], -1)[..., 0].sum(-1)
    return pt, rep


# ---------------------------------------------------------------- self-test ----------------------------

def synth(stay):
    C, coords, obs, sl = s6.synthetic(stay)
    T = len(C); reg_end = T // 2; te = np.arange(reg_end, T - max(LAGS))
    prior = training_stats(C, obs, reg_end)
    pi_s, _ = slot_shares(C, np.where(obs)[0], np.arange(reg_end), sl, prior)
    sm, _, sbin = node_sums(C, te, obs, ~obs, coords, sl, pi_s)
    return ratios({k: float(sm[k][sbin == 0].sum()) for k in KEYS}), bool((sbin == 0).all())


def selftest():
    ok = True; res = {}
    for name, stay in (("memoryless neighbour", 0.0), ("persistent neighbour", 0.95)):
        q, inner = synth(stay); res[name] = q; ok &= inner
        ok &= q["P_0"] == 1.0 and q["Xown_0"] == 1.0 - q["Ex_0"]
        print(f"{name}: " + ", ".join(f"X_nb({minutes(h)}) {q[f'Xnb_{h}']:+.3f}" for h in LAGS) + "; "
              + ", ".join(f"X_own({minutes(h)}) {q[f'Xown_{h}']:+.3f}" for h in LAGS))
    ok &= abs(res["memoryless neighbour"]["Xnb_1"]) < 0.01 and res["persistent neighbour"]["Xnb_1"] > 0.2
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def code_fp():
    return {k: p4b.sha256(Path(m.__file__), 16) for k, m in
            (("p4b.py", p4b), ("e9.py", e9), ("e12.py", e12), ("e12ter.py", e12ter), ("e12quinquies.py", q5),
             ("e12sexies.py", s6), ("e12sexiesbis.py", sys.modules[__name__]))}


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12sexiesbis_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-sexies-bis preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, by = runs_by_key(E9RUNS)
    fp_ok = runs_ok = h0_ok = sub_ok = noise_ok = True; counts = {}
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                runs_ok &= (S6RUNS / f"{city}_{int(f * 100)}_s{s}" / "run.json").exists()
                if s != 0:
                    continue
                sl = slot168(su.ts); obs_idx = np.where(su.obs)[0]
                prior = training_stats(su.C, su.obs, su.reg_end)
                pi_s, _ = slot_shares(su.C, obs_idx, np.arange(su.reg_end), sl, prior)
                C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end:] = 1
                noise_ok &= bool(np.array_equal(pi_s, slot_shares(C2, obs_idx, np.arange(su.reg_end), sl, prior)[0]))
                sm, tgt, sbin = node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, pi_s)
                q, tgt6, sbin6 = s6.node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, pi_s, pi_s)
                h0_ok &= bool(np.array_equal(tgt, tgt6) and np.array_equal(sbin, sbin6))
                h0_ok &= bool(np.array_equal(sm["cells_0"], q["pairs_0"]) and np.array_equal(sm["nb_agree_0"], q["agree_0"])
                              and np.array_equal(sm["e_x_0"], q["e_cross_0"]) and np.array_equal(sm["own_agree_0"], sm["cells_0"]))
                ref = e12.concordance(su, su.va)
                for b, lab in enumerate(BIN_LABELS):
                    h0_ok &= int(sm["nb_agree_0"][sbin == b].sum()) == ref[lab]["agree"]
                for h in LAGS[1:]:
                    sub_ok &= bool((sm[f"cells_{h}"] <= q[f"pairs_{h}"]).all() and (sm[f"cells_{h}"] <= q[f"own_cells_{h}"]).all())
                    a = su.C[su.va + h][:, tgt]; b_ = su.C[su.va][:, obs_idx[neighbours(su.al["coords"], obs_idx, tgt)[0][:, 0]]]
                    a0 = su.C[su.va][:, tgt]
                    sub_ok &= bool(np.array_equal(sm[f"cells_{h}"], (((a > 0) & (b_ > 0)) & ((a > 0) & (a0 > 0))).sum(0)))
                counts[f"{city} {int(f * 100)}%"] = [int(sm[f"cells_{h}"].sum()) for h in LAGS]
    log.check("1", "node sets, origins and pairs: setup identical to the E9 run records (60 pairs); E12-sexies run records "
              "present for the 60 pairs", fp_ok and runs_ok)
    log.check("2", "h = 0 on validation origins: cells, agreements and E× equal E12-sexies' code per segment to the bit, "
              "agreements equal E12's concordance per bin, P(0) = 1 (12 city × f, seed 0)", h0_ok)
    log.check("3", "h > 0 on validation origins: the cells are those where E12-sexies' neighbour pair and own pair are both "
              "valid, and not more than either (12 city × f, seed 0)", sub_ok)
    log.check("4", "π_k(s) from observed segments and training-period cells only: noise on hidden segments and after the "
              "last training cell leaves it identical (12 city × f, seed 0)", noise_ok)
    log.check("5", "synthetic: memoryless neighbour X_nb(15) near 0, persistent neighbour X_nb(15) > 0.2; X_own(0) = "
              "1 − E×(0) exactly (selftest)", selftest() == 0)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("6", "test-period computation refused while the E12-sexies-bis signature line is blank", guard)
    log("descriptive, no target read: common valid cells on validation origins by lag (h = "
        + ", ".join(str(minutes(h)) for h in LAGS) + " min), seed 0:")
    for k, v in counts.items():
        log(f"  {k}: {' / '.join(map(str, v))}")
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def cost(args):
    import os
    su = e9.setup("madrid", 0.4, 0); sl = slot168(su.ts)
    up0 = subprocess.check_output(["uptime"], text=True).strip(); t0 = time.perf_counter()
    prior = training_stats(su.C, su.obs, su.reg_end)
    pi_s, _ = slot_shares(su.C, np.where(su.obs)[0], np.arange(su.reg_end), sl, prior)
    node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, pi_s)
    t_val = time.perf_counter() - t0; est = t_val * (1 + len(su.te) / len(su.va))
    out = {"seconds_validation": round(t_val, 2), "seconds_per_pair_estimate": round(est, 2),
           "campaign_estimate_hours": round(est * 60 / 3600, 3), "uptime_before": up0,
           "uptime_after": subprocess.check_output(["uptime"], text=True).strip(), "loadavg": os.getloadavg(),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12sexiesbis_costo.json"
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
    su = e9.setup(city, f, seed); sl = slot168(su.ts)
    if su.fingerprints() != e12.e9_record(city, f, seed, "G0")["setup"]:
        raise SystemExit(f"STOP: {city} {f} {seed}: setup differs from E9")
    prior = training_stats(su.C, su.obs, su.reg_end)
    pi_s, low = slot_shares(su.C, np.where(su.obs)[0], np.arange(su.reg_end), sl, prior)
    p4b.require_signed(PREREG)
    sm, tgt_idx, sbin = node_sums(su.C, su.te, su.obs, su.test, su.al["coords"], sl, pi_s)
    with np.load(S6RUNS / d.name / "sums.npz") as z:
        if not (np.array_equal(z["pairs_0"], sm["cells_0"]) and np.array_equal(z["agree_0"], sm["nb_agree_0"])
                and np.array_equal(z["e_cross_0"], sm["e_x_0"]) and np.array_equal(z["blocks"], su.cells[tgt_idx])
                and np.array_equal(z["static_bin"], sbin)):
            raise SystemExit(f"STOP: {d.name}: h = 0 differs from E12-sexies")
        for h in LAGS[1:]:
            if (sm[f"cells_{h}"] > z[f"pairs_{h}"]).any() or (sm[f"cells_{h}"] > z[f"own_cells_{h}"]).any():
                raise SystemExit(f"STOP: {d.name}: h = {h}: more cells than E12-sexies")
    np.savez_compressed(d / "sums.npz", blocks=su.cells[tgt_idx], static_bin=sbin, **sm)
    rec = {"city": city, "f": f, "seed": seed, "lags_steps": list(LAGS), "slots": NS, "n_min": N_MIN, "slots_to_prior": low,
           "sums_sha256": p4b.sha256(d / "sums.npz", 16), "setup": su.fingerprints(), "code": code_fp(),
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
    if (OUT / "CONGELAMENTO_E12sexiesbis.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12sexiesbis.md exists; regenerate only on purpose, after moving it")
    rows = {}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds = {}
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"; rec = json.loads((d / "run.json").read_text())
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz"); seeds[s] = {k: z[k] for k in KEYS + ("blocks", "static_bin")}
        row = {}
        for b, lab in enumerate(BIN_LABELS):
            sub = {"seeds": {}}; nblocks = []
            for s, e in seeds.items():
                m = e["static_bin"] == b
                if m.sum() == 0:
                    continue
                sub["seeds"][s] = {"blocks": e["blocks"][m], **{k: e[k][m] for k in KEYS}}
                nblocks.append(len(np.unique(e["blocks"][m])))
            if len(sub["seeds"]) < len(seeds):
                row[lab] = {"note": "bin empty in some seed"}; continue
            pt, rep = pooled(sub, np.random.default_rng([BOOT, ci, 1 + b]))
            q = ratios(pt); qr = ratios(rep)
            e_ = {k: float(v) for k, v in q.items()}
            e_["cells"] = [int(pt[f"cells_{h}"]) for h in LAGS]; e_["min_blocks"] = int(min(nblocks))
            if min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            else:
                for h in LAGS:
                    for k in ("Xnb", "Xown", "Xdiff", "A", "P"):
                        e_[f"{k}_{h}_L"], e_[f"{k}_{h}_U"] = interval(qr[f"{k}_{h}"])
            row[lab] = e_
        rows[(city, f)] = row
    write(rows)
    return 0


def write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    mins = [minutes(h) for h in LAGS]
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "lags_minutes": mins, "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12sexiesbis_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))

    def pts(e, k, h):
        v = 100 * e[f"{k}_{h}"]; lo = e.get(f"{k}_{h}_L")
        return f"{v:+.1f}" + (f" [{100 * lo:+.1f}; {100 * e[f'{k}_{h}_U']:+.1f}]" if lo is not None else " *")
    L = ["# CONGELAMENTO_E12sexiesbis — unnormalised excesses of the neighbour's and the segment's own agreement "
         "(descriptive)\n",
         f"Generated by `paper4/code/e12sexiesbis.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit "
         f"{c} (code dirty: {dirty}). Pre-registration `protocol/paper4/E12sexiesbis.md` ({res['prereg_fingerprint']}). Inputs: 60 "
         f"(city, f, seed) runs under `paper4/runs/e12sexiesbis/`, h = 0 checked against E12-sexies. Cells: y_j(t), y_i(t) and "
         f"y_i(t + h) all valid. X_nb = A − E×, X_own = P − E×, E× = Σ_k π_k(s_t)·π_k(s_t+h); in points. Intervals: 95%, {B} "
         f"replicates, seeds × corridor blocks, the same draws for every h. **Descriptive**: no reading rule.\n"]
    for title, key in (("X_nb(h): the neighbour's excess agreement, points", "Xnb"),
                       ("X_own(h): the segment's own excess agreement, points", "Xown"),
                       ("X_nb(h) − X_own(h) = A(h) − P(h), points", "Xdiff")):
        L += [f"\n## {title}\n", "| City | f | Bin | " + " | ".join(f"{m} min" for m in mins) + " |",
              "|---|---|---|" + "---|" * len(mins)]
        for (city, f), r in rows.items():
            for lab in BIN_LABELS:
                e = r[lab]
                if "A_0" not in e:
                    L.append(f"| {city} | {int(f * 100)}% | {lab} | — ({e['note']}) |" + " |" * (len(mins) - 1)); continue
                L.append(f"| {city} | {int(f * 100)}% | {lab} | " + " | ".join(pts(e, key, h) for h in LAGS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed: interval not read.\n", "## A(h), P(h), E×(h) and cells, 0–250 m\n",
          "| City | f | h (min) | A | P | E× | Cells |", "|---|---|---|---|---|---|---|"]
    for (city, f), r in rows.items():
        e = r[BIN_LABELS[0]]
        if "A_0" not in e:
            continue
        for i, h in enumerate(LAGS):
            L.append(f"| {city} | {int(f * 100)}% | {mins[i]} | {e[f'A_{h}']:.3f} | {e[f'P_{h}']:.3f} | {e[f'Ex_{h}']:.3f} | {e['cells'][i]} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. π_k(s) from observed segments and training-period cells only; at h = 0 cells, agreements and E× identical to the "
          "E12-sexies run records (checked by the run); for h > 0 the cells are a subset of both E12-sexies cell sets.",
          "2. No reading rule: a common component or propagation is not identified by these quantities."]
    mp = OUT / "CONGELAMENTO_E12sexiesbis.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


def check_inputs(args):
    _, by = runs_by_key(E9RUNS); bad, found = [], 0; code_now = code_fp()
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = RUNS / f"{city}_{int(f * 100)}_s{s}"
        if not (d / "run.json").exists():
            bad.append(f"{d.name}: run.json missing"); continue
        found += 1; r = json.loads((d / "run.json").read_text())
        if p4b.sha256(d / "sums.npz", 16) != r["sums_sha256"]:
            bad.append(f"{d.name}: sums fingerprint")
        if r["code"] != code_now:
            bad.append(f"{d.name}: code {r['code']}")
        if r["setup"] != by[(city, f, s)]["G0"]["setup"]:
            bad.append(f"{d.name}: setup differs from E9")
        with np.load(d / "sums.npz") as z:
            if set(z.files) != set(KEYS) | {"blocks", "static_bin"}:
                bad.append(f"{d.name}: keys")
    print(f"runs found: {found} of 60; inconsistencies: {len(bad)}")
    for b in bad[:20]:
        print("  -", b)
    ok = found == 60 and not bad
    print("CHECK-INPUTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest_e2e(args):
    """freeze end to end on 60 synthetic folders: 0-250 m, at every lag 1000 cells per segment, E× = 0.40;
    A(0) = 0.60, P(0) = 1; A(15) = 0.50, P(15) = 0.55 -> X_nb(15) = +10.0, X_own(15) = +15.0, X_nb − X_own = −5.0."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12sexiesbis"; runs.mkdir(parents=True)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15)
        cells = np.full(n, 1000); sm = {}
        for h in LAGS:
            a, p = (600, 1000) if h == 0 else ((500, 550) if h == 1 else (450, 500))
            sm.update({f"cells_{h}": cells, f"nb_agree_{h}": np.full(n, a), f"own_agree_{h}": np.full(n, p),
                       f"e_x_{h}": cells * 0.40})
        np.savez_compressed(d / "sums.npz", blocks=blocks, static_bin=sb, **sm)
        (d / "run.json").write_text(json.dumps({"sums_sha256": p4b.sha256(d / "sums.npz", 16)}))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(None)
    res = json.loads((OUT / "e12sexiesbis_risultati.json").read_text())
    m = res["rows"]["madrid 0.4"][BIN_LABELS[0]]
    print(f"synthetic: X_nb(15) = {100 * m['Xnb_1']:+.4f}, X_own(15) = {100 * m['Xown_1']:+.4f}, "
          f"difference {100 * m['Xdiff_1']:+.4f}, X_own(0) = {100 * m['Xown_0']:+.4f}")
    ok = (abs(m["Xnb_1"] - 0.10) < 1e-9 and abs(m["Xown_1"] - 0.15) < 1e-9 and abs(m["Xdiff_1"] + 0.05) < 1e-9
          and abs(m["Xown_0"] - 0.60) < 1e-9 and m["Xdiff_1_L"] is not None)
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-sexies-bis")
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
