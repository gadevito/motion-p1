#!/usr/bin/env python3
"""
E12-sexies — how long does the same-instant signal last? (`protocol/paper4/E12sexies.md`). No training, descriptive.
================================================================================================================
Imports `p4b.py`, `e9.py`, `e12.py`, `e12ter.py`, `e12quinquies.py` and the resample of `genera_congelamento_e9.py`
unchanged.

Pairs as E12's concordance: test-hidden segment i, nearest observed segment j (static), at every test origin t; distance
bin of d(i, j). Lags h ∈ {0, 1, 2, 4, 8} steps (0, 15, 30, 60, 120 min). Per (city, f, bin, h), pooled over seeds:

  A(h)       share of pairs with y_i(t + h) = y_j(t), over pairs where both are valid (A(0) = E12's agreement)
  E_slot(h)  Σ_k π_k(s)², s = hour of the week of t + h, averaged over the same pairs (E_slot(0) = E12-quinquies')
  E×(h)      reported: Σ_k π_k(s_t)·π_k(s_{t+h}), independence with the slots of both times (E×(0) = E_slot(0))
  E'(h)      secondary: Σ_k π_k(s_t)·ρ_k(s_{t+h}), ρ from the test-hidden segments over the test period
  R(h)       (A(h) − E_slot(h)) / (A(0) − E_slot(0)); R×(h), R'(h) likewise with E×, E'. Not reported where
             A(0) − E_slot(0) < 0.02
  P(h)       own persistence of the hidden segment, share of (i, t) with y_i(t + h) = y_i(t)
  R_own(h)   (P(h) − E_slot(h)) / (1 − E_slot(0)), E_slot on the own-persistence cells

Intervals: 4,000 replicates, seeds × corridor blocks of the test-hidden segments, E12's replicate indices
(default_rng([20261106, index of (city, f), 1 + bin])), the same draws for every h.

    selftest      memoryless neighbour (R(15) ≈ 0) and persistent neighbour (R(15) > 0.8)
    preflight     controls 1-5 of E12sexies.md, reading no test target
    cost          one (city, f, seed) on validation origins, scaled to the test origins
    run           after the signature: per (city, f, seed) per-node sums on test origins, h = 0 checked against E12 and
                  E12-quinquies
    check-inputs  after run: 60 folders, fingerprints, code, setup, keys (no metric read)
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E12sexies.md and e12sexies_risultati.json

Usage: $PY paper4/code/e12sexies.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
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
from e12 import neighbours, training_stats, BINS, BIN_LABELS, B, BOOT  # noqa: E402
from e12ter import slot168, NS  # noqa: E402
from e12quinquies import slot_shares, interval, N_MIN  # noqa: E402
from genera_congelamento_e9 import runs_by_key, multiplicities  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12sexies.md"
RUNS = e9.RUNS / "e12sexies"
E12RUNS = e9.RUNS / "e12"
Q5RUNS = e9.RUNS / "e12quinquies"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
NB = len(BIN_LABELS)
LAGS = (0,) + tuple(p4b.HORIZONS)                     # steps: 0, 1, 2, 4, 8
MIN_SIGNAL = 0.02
PER_LAG = ("pairs", "agree", "e_slot", "e_cross", "e_sec", "own_cells", "own_agree", "own_e_slot")
KEYS = tuple(f"{k}_{h}" for h in LAGS for k in PER_LAG)


def minutes(h):
    return int(h * p4b.STEP / np.timedelta64(1, "m"))


# ---------------------------------------------------------------- quantities ---------------------------

def node_sums(C, origins, obs, tgt, coords, sl, pi_s, rho_s):
    """Per target segment and lag: pairs and agreements (y_i(t+h) vs y_j(t)), Σ π(s_{t+h})², Σ π(s_t)·ρ(s_{t+h});
    own-persistence cells and agreements (y_i(t+h) vs y_i(t)) and Σ π(s_{t+h})² on them. Static distance bin of the
    nearest observed segment (E12's concordance rule)."""
    obs_idx = np.where(obs)[0]; tgt_idx = np.where(tgt)[0]
    order, dist = neighbours(coords, obs_idx, tgt_idx)
    nn = obs_idx[order[:, 0]]; d = dist[:, 0]
    b = C[origins][:, nn]; a0 = C[origins][:, tgt_idx]; s0 = sl[origins]
    sq = (pi_s ** 2).sum(1)
    out = {}
    for h in LAGS:
        a = C[origins + h][:, tgt_idx]; sh = sl[origins + h]
        v = (a > 0) & (b > 0); agree = (a == b) & v
        es = sq[sh]; ex = (pi_s[s0] * pi_s[sh]).sum(1); ee = (pi_s[s0] * rho_s[sh]).sum(1)
        w = (a > 0) & (a0 > 0); own = (a == a0) & w
        out.update({f"pairs_{h}": v.sum(0).astype(np.int64), f"agree_{h}": agree.sum(0).astype(np.int64),
                    f"e_slot_{h}": (v * es[:, None]).sum(0), f"e_cross_{h}": (v * ex[:, None]).sum(0),
                    f"e_sec_{h}": (v * ee[:, None]).sum(0),
                    f"own_cells_{h}": w.sum(0).astype(np.int64), f"own_agree_{h}": own.sum(0).astype(np.int64),
                    f"own_e_slot_{h}": (w * es[:, None]).sum(0)})
    sbin = np.zeros(len(tgt_idx), np.int64)
    for k, (lo, hi) in enumerate(zip(BINS[:-1], BINS[1:])):
        sbin[(d >= lo) & (d < hi)] = k
    return out, tgt_idx, sbin


def ratios(t):
    """A(h), E_slot(h), E'(h), P(h), R(h), R'(h), R_own(h) from pooled sums (scalars or replicate arrays)."""
    r = {}
    for h in LAGS:
        r[f"A_{h}"] = t[f"agree_{h}"] / t[f"pairs_{h}"]
        r[f"Es_{h}"] = t[f"e_slot_{h}"] / t[f"pairs_{h}"]
        r[f"Ex_{h}"] = t[f"e_cross_{h}"] / t[f"pairs_{h}"]
        r[f"Ee_{h}"] = t[f"e_sec_{h}"] / t[f"pairs_{h}"]
        r[f"P_{h}"] = t[f"own_agree_{h}"] / t[f"own_cells_{h}"]
        r[f"Eo_{h}"] = t[f"own_e_slot_{h}"] / t[f"own_cells_{h}"]
    with np.errstate(divide="ignore", invalid="ignore"):
        for h in LAGS:
            r[f"R_{h}"] = (r[f"A_{h}"] - r[f"Es_{h}"]) / (r["A_0"] - r["Es_0"])
            r[f"Rx_{h}"] = (r[f"A_{h}"] - r[f"Ex_{h}"]) / (r["A_0"] - r["Ex_0"])
            r[f"Rsec_{h}"] = (r[f"A_{h}"] - r[f"Ee_{h}"]) / (r["A_0"] - r["Ee_0"])
            r[f"Rown_{h}"] = (r[f"P_{h}"] - r[f"Eo_{h}"]) / (r["P_0"] - r["Eo_0"])
    return r


def pooled(cell, rng):
    """Point (all seeds pooled) and replicates (seeds × blocks, pooled over the drawn seeds) of every sum; one draw
    of multiplicities for all keys, as E12-quinquies."""
    seeds, sidx, mult = multiplicities(cell, rng)
    pt = {k: float(sum(cell["seeds"][s][k].sum() for s in seeds)) for k in KEYS}
    rep = {}
    for k in KEYS:
        X = np.stack([mult[s] @ cell["seeds"][s][k].astype(float) for s in seeds])
        rep[k] = np.take_along_axis(X.transpose(1, 2, 0), sidx[..., None], -1)[..., 0].sum(-1)
    return pt, rep


def reading(L, U):
    if L is None:
        return "not read"
    if U < 0.5:
        return "the same-instant signal decays within 15 minutes"
    if L > 0.5:
        return "the signal persists at 15 minutes and the methods evaluated do not use it"
    return "undetermined"


# ---------------------------------------------------------------- self-test ----------------------------

def synthetic(stay, seed=0):
    """N segments on a line, observed every other one, hidden at 50 m from an observed one; 30 weeks of 15-min steps.
    Calendar: class shares depend on the hour of the week. Observed segments: with probability `stay` keep their
    previous class, otherwise draw from the calendar shares (stay = 0: no memory beyond the calendar). Hidden
    segments copy their left neighbour's class at the same instant w.p. 0.8, else draw from the calendar."""
    g = np.random.default_rng(seed)
    N = 120; T = 96 * 7 * 30 // 4
    coords = np.c_[np.arange(N) * 50.0, np.zeros(N)]
    obs = np.arange(N) % 2 == 0
    ts = np.datetime64("2022-01-03T00:00") + np.arange(T) * np.timedelta64(15, "m")
    sl = slot168(ts)
    peak = (np.isin(sl % 24, (7, 8, 17, 18)) & (sl // 24 < 5))
    P = np.where(peak[:, None], [0.10, 0.25, 0.65], [0.70, 0.20, 0.10])
    C = np.zeros((T, N), np.int64)
    for t in range(T):
        draw = (P[t].cumsum()[None, :] < g.random(N)[:, None]).sum(1) + 1
        C[t] = draw if t == 0 else np.where(g.random(N) < stay, C[t - 1], draw)
    hid = np.where(~obs)[0]
    fresh = (P[:, None, :].cumsum(-1) < g.random((T, len(hid)))[..., None]).sum(-1) + 1
    C[:, hid] = np.where(g.random((T, len(hid))) < 0.8, C[:, hid - 1], fresh)
    return C, coords, obs, sl


def synth_ratios(stay):
    C, coords, obs, sl = synthetic(stay)
    T = len(C); reg_end = T // 2; te = np.arange(reg_end, T - max(LAGS))
    prior = training_stats(C, obs, reg_end)
    pi_s, _ = slot_shares(C, np.where(obs)[0], np.arange(reg_end), sl, prior)
    rho_s, _ = slot_shares(C, np.where(~obs)[0], te, sl, prior)
    sm, _, sbin = node_sums(C, te, obs, ~obs, coords, sl, pi_s, rho_s)
    t = {k: float(sm[k][sbin == 0].sum()) for k in KEYS}
    return ratios(t), bool((sbin == 0).all())


def selftest():
    ok = True; res = {}
    for name, stay in (("memoryless neighbour", 0.0), ("persistent neighbour", 0.95)):
        q, inner = synth_ratios(stay); res[name] = q; ok &= inner
        ok &= q["R_0"] == 1.0 and q["P_0"] == 1.0
        print(f"{name}: " + ", ".join(f"R({minutes(h)}) {q[f'R_{h}']:.3f}" for h in LAGS)
              + "; " + ", ".join(f"R×({minutes(h)}) {q[f'Rx_{h}']:.3f}" for h in LAGS[1:])
              + "; " + ", ".join(f"R_own({minutes(h)}) {q[f'Rown_{h}']:.3f}" for h in LAGS[1:]))
    ok &= abs(res["memoryless neighbour"]["R_1"]) < 0.1 and res["persistent neighbour"]["R_1"] > 0.8
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def code_fp():
    return {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
            "e12.py": p4b.sha256(Path(e12.__file__), 16), "e12ter.py": p4b.sha256(Path(e12ter.__file__), 16),
            "e12quinquies.py": p4b.sha256(Path(q5.__file__), 16), "e12sexies.py": p4b.sha256(Path(__file__), 16)}


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12sexies_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-sexies preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, by = runs_by_key(E9RUNS)
    fp_ok = runs_ok = h0_ok = lag_ok = noise_ok = True; counts = {}
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                nm = f"{city}_{int(f * 100)}_s{s}"
                runs_ok &= (E12RUNS / nm / "run.json").exists() and (Q5RUNS / nm / "run.json").exists()
                for orig in (su.va, su.te):
                    for h in LAGS:
                        lag_ok &= bool(((su.ts[orig + h] - su.ts[orig]) == h * p4b.STEP).all())
                        lag_ok &= bool(np.array_equal(slot168(su.ts)[orig + h], slot168(su.ts[orig + h])))
                if s != 0:
                    continue
                sl = slot168(su.ts); obs_idx = np.where(su.obs)[0]
                prior = training_stats(su.C, su.obs, su.reg_end)
                pi_s, _ = slot_shares(su.C, obs_idx, np.arange(su.reg_end), sl, prior)
                C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end:] = 1
                pi2, _ = slot_shares(C2, obs_idx, np.arange(su.reg_end), sl, prior)
                noise_ok &= bool(np.array_equal(pi_s, pi2))
                # h = 0 on validation origins (test-hidden segments, validation period: no test-period target is read);
                # π(s) stands in for ρ(s), as in E12-quinquies' preflight, only to compare the two codes
                sm, tgt, sbin = node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, pi_s, pi_s)
                q, tgt5, sbin5 = q5.node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, prior, pi_s, pi_s)
                h0_ok &= bool(np.array_equal(tgt, tgt5) and np.array_equal(sbin, sbin5))
                for k5, k6 in (("pairs", "pairs_0"), ("agree", "agree_0"), ("e_slot", "e_slot_0"), ("e_sec", "e_sec_0")):
                    h0_ok &= bool(np.array_equal(q[k5], sm[k6]))
                h0_ok &= bool(np.array_equal(sm["own_agree_0"], sm["own_cells_0"]))
                h0_ok &= bool(np.allclose(sm["e_cross_0"], sm["e_slot_0"], rtol=1e-12, atol=0))
                ref = e12.concordance(su, su.va)
                for b, lab in enumerate(BIN_LABELS):
                    h0_ok &= (int(sm["pairs_0"][sbin == b].sum()) == ref[lab]["pairs"]
                              and int(sm["agree_0"][sbin == b].sum()) == ref[lab]["agree"])
                counts[f"{city} {int(f * 100)}%"] = [int(sm[f"pairs_{h}"].sum()) for h in LAGS]
    log.check("1", "node sets, origins and nearest-neighbour pairs: setup identical to the E9 run records (60 pairs); E12 "
              "and E12-quinquies run records present for the 60 pairs", fp_ok and runs_ok)
    log.check("2", "h = 0 on validation origins: pairs and agreements equal E12's concordance code per bin; pairs, "
              "agreements, E_slot and E' sums equal E12-quinquies' code to the bit; P(0) = 1 (12 city × f, seed 0)", h0_ok)
    log.check("3", "for every validation and test origin and every lag, t + h is exactly h steps after t and its slot is "
              "the hour of the week of t + h (timestamps only; 60 pairs)", lag_ok)
    log.check("4", "π_k(s) from observed segments and training-period cells only: noise on hidden segments and after the "
              "last training cell leaves it identical (12 city × f, seed 0)", noise_ok)
    log.check("5", "synthetic: memoryless neighbour gives R(15) near 0, persistent neighbour (stay 0.95) R(15) > 0.8; "
              "R(0) = P(0) = 1 exactly (selftest)", selftest() == 0)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test-period computation refused while the E12-sexies signature line is blank", guard)
    log("descriptive, no target read: valid pairs on validation origins by lag (h = " + ", ".join(str(minutes(h)) for h in LAGS)
        + " min), seed 0:")
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
    node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, pi_s, pi_s)
    t_val = time.perf_counter() - t0
    est = t_val * (1 + len(su.te) / len(su.va))
    out = {"seconds_validation": round(t_val, 2), "seconds_per_pair_estimate": round(est, 2),
           "campaign_estimate_hours": round(est * 60 / 3600, 3), "uptime_before": up0,
           "uptime_after": subprocess.check_output(["uptime"], text=True).strip(), "loadavg": os.getloadavg(),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12sexies_costo.json"
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
    rho_s, low_rho = slot_shares(su.C, np.where(su.test)[0], su.te, sl, prior)
    sm, tgt_idx, sbin = node_sums(su.C, su.te, su.obs, su.test, su.al["coords"], sl, pi_s, rho_s)
    re12 = json.loads((E12RUNS / d.name / "run.json").read_text())["concordance"]
    for b, lab in enumerate(BIN_LABELS):
        if (int(sm["pairs_0"][sbin == b].sum()), int(sm["agree_0"][sbin == b].sum())) != (re12[lab]["pairs"], re12[lab]["agree"]):
            raise SystemExit(f"STOP: {d.name} {lab}: pairs or agreements at h = 0 differ from E12")
    with np.load(Q5RUNS / d.name / "sums.npz") as z:
        for k5 in ("pairs", "agree", "e_slot", "e_sec"):
            if not np.array_equal(z[k5], sm[f"{k5}_0"]):
                raise SystemExit(f"STOP: {d.name}: {k5} at h = 0 differs from E12-quinquies")
        if not (np.array_equal(z["blocks"], su.cells[tgt_idx]) and np.array_equal(z["static_bin"], sbin)):
            raise SystemExit(f"STOP: {d.name}: blocks or bins differ from E12-quinquies")
    np.savez_compressed(d / "sums.npz", blocks=su.cells[tgt_idx], static_bin=sbin, **sm)
    rec = {"city": city, "f": f, "seed": seed, "lags_steps": list(LAGS), "slots": NS, "n_min": N_MIN,
           "prior": prior.tolist(), "slots_to_prior": low, "hidden_slots_to_prior": low_rho,
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
    if (OUT / "CONGELAMENTO_E12sexies.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12sexies.md exists; regenerate only on purpose, after moving it")
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
            e_["pairs"] = [int(pt[f"pairs_{h}"]) for h in LAGS]; e_["min_blocks"] = int(min(nblocks))
            e_["signal"] = e_["A_0"] - e_["Es_0"]
            if e_["signal"] < MIN_SIGNAL:
                for h in LAGS:
                    e_[f"R_{h}"] = e_[f"Rx_{h}"] = e_[f"Rsec_{h}"] = None
                e_["note"] = f"A(0) − E_slot(0) < {MIN_SIGNAL}: R not reported"
            elif min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            if "note" not in e_:
                for h in LAGS[1:]:
                    for k in ("R", "Rx", "Rsec", "Rown", "A", "P"):
                        e_[f"{k}_{h}_L"], e_[f"{k}_{h}_U"] = interval(qr[f"{k}_{h}"])
            e_["reading"] = reading(e_.get("R_1_L"), e_.get("R_1_U")) if "note" not in e_ else "not read"
            row[lab] = e_
        rows[(city, f)] = row
    write(rows)
    return 0


def write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    inner = BIN_LABELS[0]
    readings = {f"{k[0]} {k[1]}": r[inner].get("reading", "not read") for k, r in rows.items() if k[0] != "melbourne"}
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "readings_inner_bin_madrid_london": readings,
           "lags_minutes": [minutes(h) for h in LAGS], "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12sexies_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    f3 = lambda x: "—" if x is None else f"{x:.3f}"  # noqa: E731
    mins = [minutes(h) for h in LAGS]

    def ci(e, k, h):
        v = e.get(f"{k}_{h}")
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return "—"
        lo = e.get(f"{k}_{h}_L")
        return f3(v) + (f" [{f3(lo)}; {f3(e.get(f'{k}_{h}_U'))}]" if lo is not None else (" *" if "note" in e else ""))

    L = ["# CONGELAMENTO_E12sexies — persistence of the same-instant signal (descriptive)\n",
         f"Generated by `paper4/code/e12sexies.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12sexies.md` ({res['prereg_fingerprint']}). Inputs: 60 "
         f"(city, f, seed) runs under `paper4/runs/e12sexies/`, h = 0 checked against the E12 and E12-quinquies run records. "
         f"Lags h = {', '.join(map(str, mins))} min. R(h) = (A(h) − E_slot(h))/(A(0) − E_slot(0)), slot of t + h, N_min = {N_MIN}; "
         f"not reported where A(0) − E_slot(0) < {MIN_SIGNAL}. Intervals: 95%, {B} replicates, seeds × corridor blocks, the same "
         f"draws for every h. **Descriptive**: the reading threshold 0.5 on R(15) is a declared convention.\n",
         "## Readings in the 0–250 m bin (Madrid and London), on R(15)\n", "| City | f | Reading |", "|---|---|---|"]
    for k, v in readings.items():
        city, f = k.split(); L.append(f"| {city} | {int(float(f) * 100)}% | {v} |")
    for title, key in (("R(h): share of the same-instant signal surviving at lag h", "R"),
                       ("R×(h), reference with the slots of both t and t + h", "Rx"),
                       ("R′(h), secondary reference with both marginals preserved", "Rsec"),
                       ("R_own(h): own persistence of the hidden segment beyond the calendar", "Rown"),
                       ("A(h) = P(y_i(t + h) = y_j(t))", "A"), ("E_slot(h)", "Es"), ("P(h) = P(y_i(t + h) = y_i(t))", "P")):
        L += [f"\n## {title}\n", "| City | f | Bin | " + " | ".join(f"{m} min" for m in mins) + " |",
              "|---|---|---|" + "---|" * len(mins)]
        for (city, f), r in rows.items():
            for lab in BIN_LABELS:
                e = r[lab]
                if "A_0" not in e:
                    L.append(f"| {city} | {int(f * 100)}% | {lab} | — ({e['note']}) |" + " |" * (len(mins) - 1)); continue
                L.append(f"| {city} | {int(f * 100)}% | {lab} | " + " | ".join(ci(e, key, h) for h in LAGS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed, or A(0) − E_slot(0) below the threshold: interval not read.\n",
          "## Pairs by lag\n", "| City | f | Bin | " + " | ".join(f"{m} min" for m in mins) + " |", "|---|---|---|" + "---|" * len(mins)]
    for (city, f), r in rows.items():
        for lab in BIN_LABELS:
            p = r[lab].get("pairs")
            L.append(f"| {city} | {int(f * 100)}% | {lab} | " + (" | ".join(map(str, p)) if p else "—" + " |" * (len(mins) - 1)) + " |")
    L += ["\n## Controls, deviations and defects\n",
          "1. π_k(s) from observed segments and training-period cells only; at h = 0, pairs and agreements identical to the "
          "E12 run records and E_slot, E′ sums identical to the E12-quinquies run records (checked by the run).",
          "2. The secondary reference uses the class shares of the test-hidden segments over the test period: admissible "
          "only because the analysis is descriptive; it never changes a reading."]
    mp = OUT / "CONGELAMENTO_E12sexies.md"; mp.write_text("\n".join(L) + "\n")
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
    """freeze end to end on 60 synthetic folders. 0-250 m: A(0) = 0.60, E_slot = 0.40 at every lag; A(15 min) = 0.45 in
    Madrid (R(15) = 0.25, "decays") and 0.56 in London (R(15) = 0.80, "persists"); outer bins A(0) − E_slot(0) = 0.01
    (not reported)."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12sexies"; runs.mkdir(parents=True)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15); inner = sb == 0
        pairs = np.full(n, 1000); a15 = {"madrid": 450, "london": 560, "melbourne": 500}[city]
        sm = {}
        for h in LAGS:
            a = {0: 600, 1: a15}.get(h, 420)
            sm.update({f"pairs_{h}": pairs, f"agree_{h}": np.where(inner, a, 410), f"e_slot_{h}": pairs * 0.40,
                       f"e_cross_{h}": pairs * 0.40, f"e_sec_{h}": pairs * 0.40, f"own_cells_{h}": pairs,
                       f"own_agree_{h}": pairs if h == 0 else np.full(n, 700), f"own_e_slot_{h}": pairs * 0.40})
        np.savez_compressed(d / "sums.npz", blocks=blocks, static_bin=sb, **sm)
        (d / "run.json").write_text(json.dumps({"sums_sha256": p4b.sha256(d / "sums.npz", 16)}))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(None)
    res = json.loads((OUT / "e12sexies_risultati.json").read_text())
    m = res["rows"]["madrid 0.4"][BIN_LABELS[0]]; lo = res["rows"]["london 0.4"][BIN_LABELS[0]]
    out = res["rows"]["madrid 0.4"][BIN_LABELS[1]]
    print(f"synthetic: Madrid R(15) = {m['R_1']:.4f} ({m['reading']}), London R(15) = {lo['R_1']:.4f} ({lo['reading']}), "
          f"R_own(15) = {m['Rown_1']:.4f}, outer bin R(15) = {out['R_1']} ({out.get('note')})")
    ok = (abs(m["R_1"] - 0.25) < 1e-9 and m["reading"] == "the same-instant signal decays within 15 minutes"
          and abs(lo["R_1"] - 0.80) < 1e-9
          and lo["reading"] == "the signal persists at 15 minutes and the methods evaluated do not use it"
          and abs(m["Rown_1"] - 0.5) < 1e-9 and out["R_1"] is None)
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-sexies")
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
