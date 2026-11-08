#!/usr/bin/env python3
"""
E12-quinquies — how much of the same-instant agreement remains once the hour is known? (`protocol/paper4/
E12quinquies.md`). No training, descriptive.
=========================================================================================================
Imports `p4b.py`, `e9.py`, `e12.py`, `e12ter.py` and the resample of `genera_congelamento_e9.py` unchanged.

Pairs as E12's concordance: at every test origin t, (test-hidden segment i, nearest observed segment j), both with a
valid class; distance bin of d(i, j). Per (city, f, bin), pooled over seeds as in E12:

  A         share of pairs with y_i(t) = y_j(t)
  E         Σ_k π_k², π = class shares of the observed segments over the training period (E12's reference)
  E_slot    Σ over pairs of Σ_k π_k(s)², / pairs; s = hour of the week of t (168 slots); π_k(s) from the observed
            segments over the training period in slot s; a slot with fewer than N_MIN = 20 valid cells uses π
  E'_slot   secondary: Σ_k π_k(s)·ρ_k(s), ρ_k(s) = class shares of the test-hidden segments over the test period in s
  R         (A − E_slot) / (A − E); R' with E'_slot. Not reported where A − E < 0.02.

Intervals: 4,000 replicates, seeds × corridor blocks of the test-hidden segments, E12's replicate indices
(default_rng([20261106, index of (city, f), 1 + bin])); numerators and denominators pooled over the drawn seeds.

    selftest      planted calendar without copy (R ≈ 0) and planted copy without calendar (R ≈ 1)
    preflight     controls 1-5 of E12quinquies.md, reading no test target
    cost          one (city, f, seed) on validation origins, scaled to the test origins
    run           after the signature: per (city, f, seed) per-node sums on test origins, A checked against E12
    check-inputs  after run: 60 folders, fingerprints, code, setup, keys (no metric read)
    selftest-e2e  freeze end to end on synthetic folders
    freeze        CONGELAMENTO_E12quinquies.md and e12quinquies_risultati.json

Usage: $PY paper4/code/e12quinquies.py selftest | preflight | cost | run [--only city:f:seed] | check-inputs
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
from e12 import neighbours, training_stats, BINS, BIN_LABELS, B, BOOT  # noqa: E402
from e12ter import slot168, NS  # noqa: E402
from genera_congelamento_e9 import runs_by_key, multiplicities  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E12quinquies.md"
RUNS = e9.RUNS / "e12quinquies"
E12RUNS = e9.RUNS / "e12"
E9RUNS = e9.RUNS / "e9"
OUT = p4b.ROOT / "paper4" / "congelamenti"
NB = len(BIN_LABELS)
N_MIN = 20
MIN_EXCESS = 0.02
KEYS = ("pairs", "agree", "e_prior", "e_slot", "e_sec")


# ---------------------------------------------------------------- quantities ---------------------------

def slot_shares(C, cols, rows, sl, fallback):
    """π_k(s) (NS, 3) from the cells C[rows][:, cols] by slot of the row; slots with fewer than N_MIN valid cells
    take `fallback` (counted). Returns shares and the list of slots that fell back."""
    c = C[rows][:, cols]; s = np.broadcast_to(sl[rows][:, None], c.shape)
    cnt = np.zeros((NS, 3))
    for k in (1, 2, 3):
        m = c == k
        np.add.at(cnt[:, k - 1], s[m], 1)
    tot = cnt.sum(1); low = tot < N_MIN
    sh = np.where(low[:, None], fallback[None, :], cnt / np.maximum(tot, 1)[:, None])
    return sh, [int(x) for x in np.where(low)[0]]


def node_sums(C, origins, obs, tgt, coords, sl, prior, pi_s, rho_s):
    """Per target segment: pairs, agreements, and the sums over its valid pairs of Σπ², Σπ(s)², Σπ(s)ρ(s);
    static distance bin of its nearest observed segment (E12's concordance rule)."""
    obs_idx = np.where(obs)[0]; tgt_idx = np.where(tgt)[0]
    order, dist = neighbours(coords, obs_idx, tgt_idx)
    nn = obs_idx[order[:, 0]]; d = dist[:, 0]
    a = C[origins][:, tgt_idx]; b = C[origins][:, nn]
    v = (a > 0) & (b > 0); agree = (a == b) & v
    s = sl[origins]
    es = (pi_s ** 2).sum(1)[s]; ee = (pi_s * rho_s).sum(1)[s]
    out = {"pairs": v.sum(0).astype(np.int64), "agree": agree.sum(0).astype(np.int64),
           "e_prior": v.sum(0) * float((prior ** 2).sum()),
           "e_slot": (v * es[:, None]).sum(0), "e_sec": (v * ee[:, None]).sum(0)}
    sbin = np.zeros(len(tgt_idx), np.int64)
    for k, (lo, hi) in enumerate(zip(BINS[:-1], BINS[1:])):
        sbin[(d >= lo) & (d < hi)] = k
    return out, tgt_idx, sbin


def ratios(t):
    """A, E, E_slot, E'_slot, R, R' from pooled sums."""
    A = t["agree"] / t["pairs"]; E = t["e_prior"] / t["pairs"]; Es = t["e_slot"] / t["pairs"]; Ee = t["e_sec"] / t["pairs"]
    with np.errstate(divide="ignore", invalid="ignore"):
        R = (A - Es) / (A - E); Rs = (A - Ee) / (A - E)
    return {"A": A, "E": E, "E_slot": Es, "E_sec": Ee, "R": R, "R_sec": Rs}


def pooled(cell, r):
    """Point (all seeds pooled) and replicates (seeds × blocks, pooled over the drawn seeds) of the sums."""
    seeds, sidx, mult = multiplicities(cell, r)
    pt = {k: float(sum(cell["seeds"][s][k].sum() for s in seeds)) for k in KEYS}
    rep = {}
    for k in KEYS:
        X = np.stack([mult[s] @ cell["seeds"][s][k].astype(float) for s in seeds])        # (nS seeds, B, nS slots)
        rep[k] = np.take_along_axis(X.transpose(1, 2, 0), sidx[..., None], -1)[..., 0].sum(-1)
    return pt, rep


def interval(x):
    x = x[np.isfinite(x)]
    if x.size < 0.9 * B:
        return None, None
    lo, hi = np.percentile(x, [2.5, 97.5]); return float(lo), float(hi)


def reading(R, L, U):
    if R is None or L is None:
        return "not read"
    if U < 0.5:
        return "most of the excess agreement is calendar"
    if L > 0.5:
        return "most of the excess agreement is not calendar"
    return "undetermined"


# ---------------------------------------------------------------- self-test ----------------------------

def synthetic(copy, calendar, seed=0):
    """N segments on a line, observed every other one, hidden at 50 m from an observed one; 5,040 steps of 15 min
    (30 weeks). calendar: the class shares depend strongly on the hour of the week; copy: a hidden segment takes its
    neighbour's class w.p. 0.8."""
    g = np.random.default_rng(seed)
    N = 120; T = 96 * 7 * 30 // 4
    coords = np.c_[np.arange(N) * 50.0, np.zeros(N)]
    obs = np.arange(N) % 2 == 0
    ts = np.datetime64("2022-01-03T00:00") + np.arange(T) * np.timedelta64(15, "m")
    sl = slot168(ts)
    if calendar:
        peak = (np.isin(sl % 24, (7, 8, 17, 18)) & (sl // 24 < 5))
        P = np.where(peak[:, None], [0.05, 0.15, 0.80], [0.85, 0.10, 0.05])
    else:
        P = np.broadcast_to([0.5, 0.3, 0.2], (T, 3))
    C = np.zeros((T, N), np.int64)
    for t in range(T):
        C[t] = g.choice(3, N, p=P[t]) + 1
    if copy:
        hid = np.where(~obs)[0]; take = g.random((T, len(hid))) < 0.8
        C[:, hid] = np.where(take, C[:, hid - 1], C[:, hid])
    return C, coords, obs, sl


def selftest():
    ok = True; res = {}
    for name, copy, cal in (("calendar, no copy", False, True), ("copy, no calendar", True, False)):
        C, coords, obs, sl = synthetic(copy, cal)
        T = len(C); reg_end = T // 2; te = np.arange(reg_end, T)
        prior = training_stats(C, obs, reg_end)
        pi_s, low = slot_shares(C, np.where(obs)[0], np.arange(reg_end), sl, prior)
        rho_s, _ = slot_shares(C, np.where(~obs)[0], te, sl, prior)
        sm, _, sbin = node_sums(C, te, obs, ~obs, coords, sl, prior, pi_s, rho_s)
        t = {k: float(sm[k][sbin == 0].sum()) for k in KEYS}; q = ratios(t); res[name] = q
        ok &= bool((sbin == 0).all()) and not low
        one = {k: float(v) for k, v in t.items()}
        # one slot only: E_slot = E to the bit
        pi1, _ = slot_shares(C, np.where(obs)[0], np.arange(reg_end), np.zeros_like(sl), prior)
        s1, _, _ = node_sums(C, te, obs, ~obs, coords, np.zeros_like(sl), prior, pi1, pi1)
        ok &= bool(np.allclose(s1["e_slot"], s1["e_prior"], rtol=1e-12, atol=1e-9)) or not np.allclose(pi1[0], prior)
        print(f"{name}: A {q['A']:.3f}, E {q['E']:.3f}, E_slot {q['E_slot']:.3f}, R {q['R']:.3f}, R' {q['R_sec']:.3f}; "
              f"pairs {int(one['pairs'])}")
    ok &= res["calendar, no copy"]["R"] < 0.25 and res["copy, no calendar"]["R"] > 0.9
    # with one slot the slot shares are the prior computed on the same cells: E_slot = E exactly
    C, coords, obs, sl = synthetic(True, True); T = len(C); reg_end = T // 2
    prior = training_stats(C, obs, reg_end)
    pi1, _ = slot_shares(C, np.where(obs)[0], np.arange(reg_end), np.zeros(T, np.int64), prior)
    ok &= bool(np.allclose(pi1[0], prior, rtol=0, atol=1e-15))
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- preflight ----------------------------

def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e12quinquies_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E12-quinquies preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(" · ".join(f"{k} {v}" for k, v in code_fp().items()))
    _, by = runs_by_key(E9RUNS)
    fp_ok = e12_ok = one_ok = noise_ok = conc_ok = True; low_log = {}
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for s in e9.SEEDS:
                su = e9.setup(city, f, s)
                fp_ok &= su.fingerprints() == by[(city, f, s)]["G0"]["setup"]
                e12_ok &= (E12RUNS / f"{city}_{int(f * 100)}_s{s}" / "run.json").exists()
                if s != 0:
                    continue
                sl = slot168(su.ts); obs_idx = np.where(su.obs)[0]
                prior = training_stats(su.C, su.obs, su.reg_end)
                pi_s, low = slot_shares(su.C, obs_idx, np.arange(su.reg_end), sl, prior)
                low_log[f"{city} {int(f * 100)}%"] = low
                pi1, _ = slot_shares(su.C, obs_idx, np.arange(su.reg_end), np.zeros_like(sl), prior)
                one_ok &= bool(np.allclose(pi1[0], prior, rtol=0, atol=1e-15))
                C2 = su.C.copy(); C2[:, ~su.obs] = 1; C2[su.reg_end:] = 1
                pi2, _ = slot_shares(C2, obs_idx, np.arange(su.reg_end), sl, prior)
                noise_ok &= bool(np.array_equal(pi_s, pi2))
                # A on validation origins equals E12's concordance code on the same origins (test-hidden segments,
                # validation period: no test-period target is read)
                sm, _, sbin = node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, prior, pi_s, pi_s)
                ref = e12.concordance(su, su.va)
                for b, lab in enumerate(BIN_LABELS):
                    conc_ok &= (int(sm["pairs"][sbin == b].sum()) == ref[lab]["pairs"]
                                and int(sm["agree"][sbin == b].sum()) == ref[lab]["agree"])
    log.check("1", "node sets, origins and nearest-neighbour pairs: setup identical to the E9 run records (60 pairs); E12 "
              "run records present for the 60 pairs", fp_ok and e12_ok)
    log.check("2", "with one slot only, π(s) equals the prior to the bit, so E_slot = E (12 city × f, seed 0)", one_ok)
    log.check("3", "π_k(s) from observed segments and training-period cells only: noise on hidden segments and after the "
              "last training cell leaves it identical (12 city × f, seed 0)", noise_ok)
    log.check("4", "synthetic: a planted calendar without copy gives R near 0, a planted copy without calendar R near 1 "
              "(selftest)", selftest() == 0)
    log.check("5", "pairs and agreements on validation origins equal E12's concordance code, per bin (12 city × f, seed 0)",
              conc_ok)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "test-period computation refused while the E12-quinquies signature line is blank", guard)
    log(f"descriptive, no target read: slots with fewer than {N_MIN} valid observed training cells (fall back to π), seed 0:")
    for k, v in low_log.items():
        log(f"  {k}: {len(v)} of {NS}" + (f" ({v[:12]}{' …' if len(v) > 12 else ''})" if v else ""))
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def cost(args):
    import os
    su = e9.setup("madrid", 0.4, 0); sl = slot168(su.ts)
    up0 = subprocess.check_output(["uptime"], text=True).strip(); t0 = time.perf_counter()
    prior = training_stats(su.C, su.obs, su.reg_end)
    pi_s, _ = slot_shares(su.C, np.where(su.obs)[0], np.arange(su.reg_end), sl, prior)
    node_sums(su.C, su.va, su.obs, su.test, su.al["coords"], sl, prior, pi_s, pi_s)
    t_val = time.perf_counter() - t0
    est = t_val * (1 + len(su.te) / len(su.va))
    out = {"seconds_validation": round(t_val, 2), "seconds_per_pair_estimate": round(est, 2),
           "campaign_estimate_hours": round(est * 60 / 3600, 3), "uptime_before": up0,
           "uptime_after": subprocess.check_output(["uptime"], text=True).strip(), "loadavg": os.getloadavg(),
           "commit": p4b.git_commit()[0], "written": datetime.now(timezone.utc).isoformat()}
    path = e9.RUNS / "e12quinquies_costo.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    path.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


# ---------------------------------------------------------------- run (after the signature) -------------

def code_fp():
    return {"p4b.py": p4b.sha256(Path(p4b.__file__), 16), "e9.py": p4b.sha256(Path(e9.__file__), 16),
            "e12.py": p4b.sha256(Path(e12.__file__), 16), "e12ter.py": p4b.sha256(Path(e12ter.__file__), 16),
            "e12quinquies.py": p4b.sha256(Path(__file__), 16)}


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
    obs_idx = np.where(su.obs)[0]
    prior = training_stats(su.C, su.obs, su.reg_end)
    pi_s, low = slot_shares(su.C, obs_idx, np.arange(su.reg_end), sl, prior)
    p4b.require_signed(PREREG)
    rho_s, low_rho = slot_shares(su.C, np.where(su.test)[0], su.te, sl, prior)
    sm, tgt_idx, sbin = node_sums(su.C, su.te, su.obs, su.test, su.al["coords"], sl, prior, pi_s, rho_s)
    re12 = json.loads((E12RUNS / d.name / "run.json").read_text())["concordance"]
    for b, lab in enumerate(BIN_LABELS):
        if (int(sm["pairs"][sbin == b].sum()), int(sm["agree"][sbin == b].sum())) != (re12[lab]["pairs"], re12[lab]["agree"]):
            raise SystemExit(f"STOP: {d.name} {lab}: pairs or agreements differ from E12")
    np.savez_compressed(d / "sums.npz", blocks=su.cells[tgt_idx], static_bin=sbin, **sm)
    rec = {"city": city, "f": f, "seed": seed, "slots": NS, "n_min": N_MIN, "prior": prior.tolist(),
           "slots_to_prior": low, "hidden_slots_to_prior": low_rho, "sums_sha256": p4b.sha256(d / "sums.npz", 16),
           "setup": su.fingerprints(), "code": code_fp(), "commit": p4b.git_commit()[0],
           "written": datetime.now(timezone.utc).isoformat()}
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
    if (OUT / "CONGELAMENTO_E12quinquies.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E12quinquies.md exists; regenerate only on purpose, after moving it")
    rows = {}
    for ci, (city, f) in enumerate([(c, f) for c in e9.CITIES for f in e9.LEVELS]):
        seeds, recs = {}, []
        for s in e9.SEEDS:
            d = RUNS / f"{city}_{int(f * 100)}_s{s}"; rec = json.loads((d / "run.json").read_text()); recs.append(rec)
            if p4b.sha256(d / "sums.npz", 16) != rec["sums_sha256"]:
                raise SystemExit(f"STOP: {d}/sums.npz fingerprint differs")
            z = np.load(d / "sums.npz"); seeds[s] = {k: z[k] for k in KEYS + ("blocks", "static_bin")}
        row = {"by_bin": {}, "slots_to_prior": [len(r["slots_to_prior"]) for r in recs]}
        for b, lab in enumerate(BIN_LABELS):
            sub = {"seeds": {}}; nblocks = []
            for s, e in seeds.items():
                m = e["static_bin"] == b
                if m.sum() == 0:
                    continue
                sub["seeds"][s] = {"blocks": e["blocks"][m], **{k: e[k][m] for k in KEYS}}
                nblocks.append(len(np.unique(e["blocks"][m])))
            if len(sub["seeds"]) < len(seeds):
                row["by_bin"][lab] = {"note": "bin empty in some seed"}; continue
            pt, rep = pooled(sub, np.random.default_rng([BOOT, ci, 1 + b]))
            q = ratios(pt); qr = ratios(rep)
            e_ = {k: float(v) for k, v in q.items()}; e_["pairs"] = int(pt["pairs"]); e_["min_blocks"] = int(min(nblocks))
            e_["excess"] = e_["A"] - e_["E"]
            if e_["excess"] < MIN_EXCESS:
                e_["R"] = e_["R_sec"] = None; e_["note"] = f"A − E < {MIN_EXCESS}: R not reported"
            elif min(nblocks) < 3:
                e_["note"] = "fewer than 3 blocks in some seed: no interval read"
            if e_["R"] is not None and "note" not in e_:
                e_["R_L"], e_["R_U"] = interval(qr["R"]); e_["Rsec_L"], e_["Rsec_U"] = interval(qr["R_sec"])
                e_["A_L"], e_["A_U"] = interval(qr["A"]); e_["Eslot_L"], e_["Eslot_U"] = interval(qr["E_slot"])
            e_["reading"] = reading(e_.get("R"), e_.get("R_L"), e_.get("R_U")) if "note" not in e_ else "not read"
            row["by_bin"][lab] = e_
        rows[(city, f)] = row
    write(rows)
    return 0


def write(rows):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    inner = BIN_LABELS[0]
    readings = {f"{k[0]} {k[1]}": r["by_bin"][inner].get("reading", "not read") for k, r in rows.items() if k[0] != "melbourne"}
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "readings_inner_bin_madrid_london": readings,
           "commit": c, "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16),
           "generator_fingerprint": p4b.sha256(Path(__file__), 16), "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e12quinquies_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    f3 = lambda x: "—" if x is None else f"{x:.3f}"  # noqa: E731
    def cell(e):
        if "A" not in e:
            return "— (" + e["note"] + ")"
        r = "—" if e.get("R") is None else f3(e["R"]) + (f" [{f3(e.get('R_L'))}; {f3(e.get('R_U'))}]" if e.get("R_L") is not None else " *")
        return f"A {f3(e['A'])}, E {f3(e['E'])}, E_slot {f3(e['E_slot'])}; R {r}"
    L = ["# CONGELAMENTO_E12quinquies — same-instant agreement within the hour of the week (descriptive)\n",
         f"Generated by `paper4/code/e12quinquies.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E12quinquies.md` ({res['prereg_fingerprint']}). Inputs: 60 "
         f"(city, f, seed) runs under `paper4/runs/e12quinquies/`, pairs and agreements checked against the E12 run records. "
         f"Slots: hour of the week of t (168), N_min = {N_MIN} valid observed training cells per slot. R = (A − E_slot)/(A − E), "
         f"not reported where A − E < {MIN_EXCESS}. Intervals: 95%, {B} replicates, seeds × corridor blocks, pooled over the drawn "
         f"seeds. **Descriptive**: the reading threshold 0.5 is a declared convention.\n",
         "## Readings in the 0–250 m bin (Madrid and London)\n",
         "| City | f | Reading |", "|---|---|---|"]
    for k, v in readings.items():
        city, f = k.split(); L.append(f"| {city} | {int(float(f) * 100)}% | {v} |")
    L += ["\n## A, E, E_slot and R by distance bin\n", "| City | f | " + " | ".join(BIN_LABELS) + " |", "|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        L.append(f"| {city} | {int(f * 100)}% | " + " | ".join(cell(r["by_bin"][b]) for b in BIN_LABELS) + " |")
    L += ["\n\\* fewer than 3 blocks in some seed: interval not read.\n",
          "## Secondary reference (marginals preserved): R′ = (A − E′_slot)/(A − E)\n",
          "| City | f | " + " | ".join(BIN_LABELS) + " |", "|---|---|" + "---|" * NB]
    for (city, f), r in rows.items():
        cs = []
        for b in BIN_LABELS:
            e = r["by_bin"][b]
            cs.append("—" if e.get("R_sec") is None else f3(e["R_sec"]) + (f" [{f3(e.get('Rsec_L'))}; {f3(e.get('Rsec_U'))}]" if e.get("Rsec_L") is not None else ""))
        L.append(f"| {city} | {int(f * 100)}% | " + " | ".join(cs) + " |")
    L += ["\n## Pairs and slots\n", "| City | f | Pairs by bin | Slots below N_min, per seed |", "|---|---|---|---|"]
    for (city, f), r in rows.items():
        pr = " / ".join(str(r["by_bin"][b].get("pairs", "—")) for b in BIN_LABELS)
        L.append(f"| {city} | {int(f * 100)}% | {pr} | {' / '.join(map(str, r['slots_to_prior']))} |")
    L += ["\n## Controls, deviations and defects\n",
          "1. π_k(s) from observed segments and training-period cells only; pairs and agreements identical to the E12 run "
          "records (checked by the run).",
          "2. The secondary reference uses the class shares of the test-hidden segments over the test period: admissible "
          "only because the analysis is descriptive; it never changes a reading."]
    mp = OUT / "CONGELAMENTO_E12quinquies.md"; mp.write_text("\n".join(L) + "\n")
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
    """freeze end to end on 60 synthetic folders: in the 0-250 m bin A = 0.60, E = 0.40, E_slot = 0.55 in Madrid
    (R = 0.25, "calendar") and E_slot = 0.42 in London (R = 0.90, "not calendar"); outer bins A − E = 0.01 (not reported)."""
    import shutil
    global RUNS, OUT
    tmp = Path(args.tmpdir)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12quinquies"; runs.mkdir(parents=True)
    for city, f, s in [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 60; blocks = np.repeat(np.arange(15), 4); sb = np.tile(np.arange(NB), 15)
        pairs = np.full(n, 1000); inner = sb == 0
        es = {"madrid": 0.55, "london": 0.42, "melbourne": 0.50}[city]
        sm = {"pairs": pairs, "agree": np.where(inner, 600, 410), "e_prior": pairs * 0.40,
              "e_slot": pairs * np.where(inner, es, 0.40), "e_sec": pairs * np.where(inner, es, 0.40)}
        np.savez_compressed(d / "sums.npz", blocks=blocks, static_bin=sb, **sm)
        (d / "run.json").write_text(json.dumps({"sums_sha256": p4b.sha256(d / "sums.npz", 16), "slots_to_prior": []}))
    RUNS, OUT = runs, tmp / "congelamenti"
    freeze(None)
    res = json.loads((OUT / "e12quinquies_risultati.json").read_text())
    m = res["rows"]["madrid 0.4"]["by_bin"][BIN_LABELS[0]]; lo = res["rows"]["london 0.4"]["by_bin"][BIN_LABELS[0]]
    out = res["rows"]["madrid 0.4"]["by_bin"][BIN_LABELS[1]]
    print(f"synthetic: Madrid R = {m['R']:.4f} ({m['reading']}), London R = {lo['R']:.4f} ({lo['reading']}), "
          f"outer bin R = {out['R']} ({out.get('note')})")
    ok = (abs(m["R"] - 0.25) < 1e-9 and m["reading"] == "most of the excess agreement is calendar"
          and abs(lo["R"] - 0.90) < 1e-9 and lo["reading"] == "most of the excess agreement is not calendar"
          and out["R"] is None)
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12-quinquies")
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
