#!/usr/bin/env python3
"""
Generator of the E11 frozen record (`protocol/paper4/E11.md`, signed 2026-11-06, commit 22e7fe8).
==================================================================================================
Reads only the campaign files under paper4/runs/e11/ (240 run.json + per-cell .npz) and writes

    paper4/congelamenti/CONGELAMENTO_E11.md     every number of E11, derived by this script
    paper4/congelamenti/e11_risultati.json      the same numbers, machine-readable

Nothing is written by hand. The verdicts are derived mechanically from the criteria of E11.md.

Procedure, as pre-registered:
  * wCE_{c,s}(a) on test-hidden nodes: per horizon, sum over valid cells of W[y]·(−log p_y) over the sum of
    W[y] (p clipped at 1e-7, W = class weights of the run), then mean over the four horizons;
  * V_c(a) = mean over seeds of 100·(wCE(G0) − wCE(a))/wCE(G0); D_c(a, b) = V_c(a) − V_c(b);
  * intervals: 4,000 replicates, joint resample of seeds (with replacement) and, inside each drawn seed, of
    the corridor blocks (grid cells) holding test-hidden nodes (with replacement, multiplicities kept); the
    same replicate indices for every arm of a configuration; 95% percentiles; generator
    default_rng([20261106, configuration index]);
  * two reading scales (sign, margin of 3 points) and the verdicts of criterion 1; the summary statement;
    the secondary comparison; criteria 2 and 3 with the city term; the declared distance sensitivity.

Dated note (2026-11-06), on the warning `p4b.py:367: Mean of empty slice` printed once per run (240 times):
it comes from the historical-average table (node x weekly slot) built from observed nodes only, whose rows
are empty for every hidden node by construction (D1). The empty row mean is replaced by the global mean on
the next line and the hidden rows are then set to zero, so no NaN reaches the inputs, the predictions or the
targets. Independently of that, this generator excludes from every mean the cells without a valid target
(label -1) and reports their count, and excludes, with their count, nodes without any valid target in the
period (none expected: 0 of 8,932 test-hidden node-runs at the check of 2026-11-06).

Usage (from the worktree root):

    $PY paper4/code/genera_congelamento_e11.py --selftest     # synthetic data with a known effect
    $PY paper4/code/genera_congelamento_e11.py --check-inputs # campaign files, without reading predictions
    $PY paper4/code/genera_congelamento_e11.py --selftest-e2e /tmp/e11_e2e   # whole pipeline, random p
    $PY paper4/code/genera_congelamento_e11.py                # the frozen record from paper4/runs/e11/
"""
import argparse
import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e11  # noqa: E402

B = 4000
BOOT = 20261106
MARGIN = 3.0
ARMS = e11.ARMS
OUT = p4b.ROOT / "paper4" / "congelamenti"
RUNS = e11.RUNS / "e11"


# ---------------------------------------------------------------- per-node sums -----------------------

def node_sums(p, y, nodes, W):
    """Per target node and horizon: S = Σ W[y]·(−log p_y) and Wn = Σ W[y] over valid cells, plus counts."""
    W = np.asarray(W, dtype="float64")
    yy = y[:, nodes, :].astype(np.int64)                     # (origins, n, H)
    pp = p[:, nodes, :, :].astype("float64")                 # (origins, n, H, 3)
    valid = yy >= 0
    yc = np.where(valid, yy, 0)
    py = np.take_along_axis(pp, yc[..., None], -1)[..., 0]
    w = np.where(valid, W[yc], 0.0)
    S = (w * -np.log(np.clip(py, 1e-7, 1))).sum(0)           # (n, H)
    Wn = w.sum(0)
    return S, Wn, int((~valid).sum()), int(valid.size), int((valid.sum((0, 2)) == 0).sum())


def wce_from(S, Wn, mult=None):
    """Mean over horizons of Σ m·S / Σ m·W; `mult` (..., n) multiplicities, None = all ones."""
    if mult is None:
        return float(np.mean(S.sum(0) / Wn.sum(0)))
    num = mult @ S; den = mult @ Wn                          # (..., H)
    return (num / den).mean(-1)


def red_recall(vp, vy, vnodes, tp, ty, tnodes, fa=0.05):
    """Red recall on test at the threshold that gives `fa` false alarms on validation (pooled over horizons).
    p: (origins, K, H, 3), y: (origins, K, H). Node selection first, then the class: indexing p[:, nodes, :, 2]
    in one step would move the node axis to the front (numpy advanced indexing)."""
    pv = vp[:, vnodes][..., 2]; yv = vy[:, vnodes]
    neg = pv[(yv >= 0) & (yv != 2)]
    t = float(np.quantile(neg, 1 - fa)) if neg.size else 1.0
    pt = tp[:, tnodes][..., 2]; yt = ty[:, tnodes]
    pos = pt[yt == 2]
    return (float((pos >= t).mean()) if pos.size else float("nan")), t


# ---------------------------------------------------------------- readings ----------------------------

def readings(D, L, U):
    sign = "favourable" if L > 0 else "unfavourable" if U < 0 else "inconclusive"
    if L >= MARGIN:
        margin = "reached"
    elif -MARGIN < L and U < MARGIN:
        margin = "effect >= 3 excluded in either direction"
    elif U < MARGIN:
        margin = "advantage >= 3 excluded"
    else:
        margin = "not excluded"
    return sign, margin


def verdict_c1(D, L, U):
    if L > 0 and D >= MARGIN:
        return "proximity prevails"
    if U < MARGIN:
        return "geometry advantage >= 3 points excluded" + (" (randomised >= real)" if (U < 0 or D <= 0) else "")
    return "not discriminating"


def summary_statement(rows):
    prev = {}
    for r in rows:
        if r["c1_verdict"] == "proximity prevails":
            prev[r["city"]] = prev.get(r["city"], 0) + 1
    n_prev = sum(prev.values())
    n_excl = sum(r["c1_verdict"].startswith("geometry advantage") for r in rows)
    n_nd = sum(r["c1_verdict"] == "not discriminating" for r in rows)
    if any(v >= 2 for v in prev.values()):
        s = "geometry matters"
    elif n_excl >= 10 and n_prev == 0:
        s = "no evidence that geometry matters in 42-396 m"
    else:
        s = "undetermined"
    return s, {"prevails": n_prev, "excluded": n_excl, "not discriminating": n_nd}


# ---------------------------------------------------------------- regressions -------------------------

def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    rss = float(((y - X @ beta) ** 2).sum())
    return beta, rss


def design(x, city, with_city=True):
    cols = [np.ones_like(x), x] + ([(city == "melbourne").astype(float)] if with_city else [])
    return np.column_stack(cols)


def aic(rss, n, k):
    return n * np.log(max(rss, 1e-300) / n) + 2 * k


def threshold_fit(x, y, city):
    """Continuous two-line model with city term: y = a + c·city + b1·x + b2·max(0, x − k); k over the observed
    values with at least 3 configurations on each side. Returns (k, b1, b2, rss)."""
    xs = np.sort(x); best = None
    for k in xs[2:-3]:
        X = np.column_stack([np.ones_like(x), (city == "melbourne").astype(float), x, np.maximum(0, x - k)])
        beta, rss = ols(X, y)
        if best is None or rss < best[3]:
            best = (float(k), float(beta[2]), float(beta[3]), rss)
    return best


# ---------------------------------------------------------------- core ---------------------------------

def analyse(configs, rep_rng):
    """configs: list of dicts {city, tag, spacing, distance, seeds: {s: {"blocks": array (n,), arms: {a: (S, Wn)}}}}.
    Returns per-configuration point estimates, replicate arrays and readings."""
    rows, reps_all = [], []
    for ci, c in enumerate(configs):
        r = rep_rng(ci)
        seeds = sorted(c["seeds"])
        nS = len(seeds)
        sidx = r.integers(0, nS, size=(B, nS))
        mult = {}
        for s in seeds:
            blocks = c["seeds"][s]["blocks"]; ub = np.unique(blocks)
            draws = r.integers(0, len(ub), size=(B, nS, len(ub)))
            M = np.zeros((B, nS, len(blocks)))
            for bi, b in enumerate(ub):
                M[:, :, blocks == b] += (draws == bi).sum(-1)[..., None]
            mult[s] = M
        point = {a: np.mean([100 * (wce_from(*c["seeds"][s]["arms"]["G0"]) - wce_from(*c["seeds"][s]["arms"][a]))
                             / wce_from(*c["seeds"][s]["arms"]["G0"]) for s in seeds]) for a in ARMS}
        rep_v = {}
        for a in ARMS:
            vals = np.zeros((nS, B, nS))
            for k, s in enumerate(seeds):
                w0 = wce_from(*c["seeds"][s]["arms"]["G0"], mult[s])
                wa = wce_from(*c["seeds"][s]["arms"][a], mult[s])
                vals[k] = 100 * (w0 - wa) / w0
            rep_v[a] = np.take_along_axis(vals.transpose(1, 2, 0), sidx[..., None], -1)[..., 0].mean(-1)
        def diff(a, b):
            d = point[a] - point[b]; q = np.percentile(rep_v[a] - rep_v[b], [2.5, 97.5])
            return float(d), float(q[0]), float(q[1])
        D, L, U = diff("G1", "G1-rand(deg)")
        row = {"city": c["city"], "configuration": c["tag"], "spacing_m": c["spacing"], "distance_m": c["distance"],
               "cell_side_m": c.get("cell_side"), "test_blocks_median": c.get("test_blocks"),
               "V": {a: float(point[a]) for a in ARMS},
               "c1": {"D": D, "L": L, "U": U, "halfwidth": (U - L) / 2, "readings": readings(D, L, U)},
               "c1_verdict": verdict_c1(D, L, U)}
        for a, b, key in (("G1", "G0", "G1_vs_G0"), ("G1-rand(deg)", "G0", "rand_deg_vs_G0"),
                          ("G1-rand(edges)", "G0", "rand_edges_vs_G0"), ("G1", "G1-rand(edges)", "G1_vs_rand_edges"),
                          ("G1-rand(deg)", "G1-rand(edges)", "rand_deg_vs_rand_edges")):
            if b == "G0":
                d = float(point[a]); q = np.percentile(rep_v[a], [2.5, 97.5])
            else:
                d, *q = diff(a, b)
            row[key] = {"D": d, "L": float(q[0]), "U": float(q[1]), "readings": readings(d, q[0], q[1])}
        rows.append(row); reps_all.append(rep_v)
    return rows, reps_all


def regressions(rows, reps_all):
    x = np.array([r["spacing_m"] for r in rows]); dist = np.array([r["distance_m"] for r in rows])
    city = np.array([r["city"] for r in rows]); y = np.array([r["V"]["G1"] for r in rows])
    yrep = np.stack([rv["G1"] for rv in reps_all], 1)        # (B, 12)
    out = {}
    for name, xx in (("spacing", x), ("distance_sensitivity", dist)):
        beta, _ = ols(design(xx, city), y)
        slopes = np.array([ols(design(xx, city), yrep[b])[0][1] for b in range(B)])
        lo, hi = np.percentile(slopes, [2.5, 97.5])
        fitted = abs(beta[1]) * (xx.max() - xx.min())
        out[name] = {"slope_per_m": float(beta[1]), "L": float(lo), "U": float(hi),
                     "fitted_difference_points": float(fitted),
                     "supported": bool((lo > 0 or hi < 0) and fitted >= MARGIN) if name == "spacing" else None}
        bs, _ = ols(design(xx, city, with_city=False), y)
        out[name]["slope_without_city"] = float(bs[1])
    n = len(y)
    _, rss0 = ols(np.column_stack([np.ones(n), (city == "melbourne").astype(float)]), y)
    _, rss1 = ols(design(x, city), y)
    k, b1, b2, rss2 = threshold_fit(x, y, city)
    a0, a1, a2 = aic(rss0, n, 2), aic(rss1, n, 3), aic(rss2, n, 5)
    b2r, kr = [], []
    for b in range(B):
        fit = threshold_fit(x, yrep[b], city); b2r.append(fit[2]); kr.append(fit[0])
    lo, hi = np.percentile(b2r, [2.5, 97.5]); klo, khi = np.percentile(kr, [2.5, 97.5])
    wins = bool(a2 <= min(a0, a1) - 2 and (lo > 0 or hi < 0))
    out["threshold"] = {"AIC_constant": float(a0), "AIC_linear": float(a1), "AIC_threshold": float(a2),
                        "breakpoint_m": k, "breakpoint_L": float(klo), "breakpoint_U": float(khi),
                        "slope_difference": b2, "slope_difference_L": float(lo), "slope_difference_U": float(hi),
                        "wins": wins, "breakpoint_in_unsampled_130_380": bool(130 < k < 380)}
    return out


# ---------------------------------------------------------------- campaign files ----------------------

def load_campaign():
    recs = [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(RUNS / "*" / "run.json")))]
    if len(recs) != 240:
        raise SystemExit(f"STOP: {len(recs)} run.json found, 240 expected")
    by = {}
    counts = {"missing_cells": 0, "cells": 0, "nodes_without_target": 0}
    obs_counts = {"missing_cells": 0, "cells": 0}
    extra = {}
    for r in recs:
        cfg = r["config"]; d = RUNS / r["config_fingerprint"]
        if p4b.fingerprint(cfg) != r["config_fingerprint"] or cfg["U"] != 1000:
            raise SystemExit(f"STOP: configuration fingerprint mismatch in {d}")
        for k, f in r["files"].items():
            if p4b.sha256(d / f["file"], 16) != f["sha256"]:
                raise SystemExit(f"STOP: {d}/{f['file']} fingerprint differs from run.json")
        key = (cfg["city"], cfg["configuration"], cfg["seed"])
        by.setdefault(key, {})[cfg["arm"]] = (r, d)
    configs, red, cost, per_h, hours = [], {}, {}, {}, 0.0
    for city, tag, _ in e11.CONFIGS:
        al = p4b.align_graph(city, e11.graph_path(city, tag))
        G = p4b.adaptive_grid(al["coords"]); cells = p4b.grid_cells(al["coords"], G)
        c = {"city": city, "tag": tag, "seeds": {}}
        sp, di, side, nb = [], [], [], []
        for s in e11.SEEDS:
            arms = by[(city, tag, s)]
            if sorted(arms) != sorted(ARMS):
                raise SystemExit(f"STOP: {city} {tag} seed {s}: arms {sorted(arms)}")
            fps = {json.dumps(arms[a][0]["setup"], sort_keys=True) for a in ARMS}
            if len(fps) != 1:
                raise SystemExit(f"STOP: {city} {tag} seed {s}: setup fingerprints differ between arms")
            lab = p4b.node_sets(cells, s)
            entry = {"arms": {}}
            for a in ARMS:
                r, d = arms[a]; hours += r["train_seconds"] / 3600
                z = np.load(d / "test_hidden.npz")
                if not np.array_equal(z["nodes"], np.where(lab == 2)[0]):
                    raise SystemExit(f"STOP: {d}: test-hidden nodes differ from the recomputed node sets")
                S, Wn, miss, tot, zero = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"])
                counts["missing_cells"] += miss; counts["cells"] += tot; counts["nodes_without_target"] += zero
                keep = Wn.sum(1) > 0
                entry["arms"][a] = (S[keep], Wn[keep]); entry["blocks"] = cells[z["nodes"]][keep]
                per_h.setdefault((city, tag, a), []).append((S.sum(0) / Wn.sum(0)).tolist())
                v = np.load(d / "val_hidden.npz")
                rec_, _ = red_recall(v["p"], v["y"], v["nodes"], z["p"], z["y"], z["nodes"])
                red.setdefault((city, tag, a), []).append(rec_)
                if a == "G1":
                    o = np.load(d / "test_observed.npz")
                    So, Wo, mo, to, _ = node_sums(o["p"], o["y"], o["nodes"], r["class_weights"])
                    obs_counts["missing_cells"] += mo; obs_counts["cells"] += to
                    cost.setdefault((city, tag), []).append(wce_from(S, Wn) - wce_from(So, Wo))
                    sp.append(r["graph"]["mean_geo_length_m"])
                    di.append(r["geometry"]["test_to_nearest_observed_m"]["median"])
                    side.append(r["geometry"]["cell_side_m"]); nb.append(len(np.unique(entry["blocks"])))
            c["seeds"][s] = entry
        c.update({"spacing": float(np.mean(sp)), "distance": float(np.mean(di)), "cell_side": float(np.mean(side)),
                  "test_blocks": float(np.median(nb))})
        configs.append(c)
    extra = {"counts_test_hidden": counts, "counts_test_observed_G1": obs_counts, "machine_hours": hours,
             "red_recall_5pct": {f"{k[0]} {k[1]} {k[2]}": float(np.nanmean(v)) for k, v in red.items()},
             "cost_of_not_having_the_sensor": {f"{k[0]} {k[1]}": float(np.mean(v)) for k, v in cost.items()},
             "per_horizon_wce": {f"{k[0]} {k[1]} {k[2]}": np.mean(v, 0).tolist() for k, v in per_h.items()},
             "n_runs": len(recs), "run_index_fingerprint": p4b.fingerprint(sorted(r["config_fingerprint"] for r in recs))}
    return configs, extra


# ---------------------------------------------------------------- writing -----------------------------

def fmt(x, n=2):
    return f"{x:+.{n}f}"


def write(rows, reg, extra, statement, counts):
    OUT.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    hw = float(np.median([r["c1"]["halfwidth"] for r in rows]))
    res = {"rows": rows, "regressions": reg, "summary_statement": statement, "verdict_counts": counts,
           "median_halfwidth_c1": hw, **extra, "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(e11.PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e11_risultati.json"; jp.write_text(json.dumps(res, indent=1))
    L = []
    L.append("# CONGELAMENTO_E11 — geometry under protocol\n")
    L.append(f"Generated by `paper4/code/genera_congelamento_e11.py` ({res['generator_fingerprint']}) on "
             f"{res['written'][:19]} UTC, commit {c} (code dirty: {dirty}). Pre-registration `protocol/paper4/E11.md` "
             f"({res['prereg_fingerprint']}), signed at 22e7fe8. Inputs: {extra['n_runs']} runs under `paper4/runs/e11/`, "
             f"index fingerprint {extra['run_index_fingerprint']}; every per-cell file checked against its run.json. "
             f"Machine time: {extra['machine_hours']:.2f} h of training (Mac M3, MPS). Numbers in percentage points of the "
             f"G0 wCE; positive = the first arm is better. Intervals: 95%, {B} replicates, seeds × corridor blocks.\n")
    L.append(f"## Summary statement (criterion 1, derived)\n\n**{statement}** — prevails {counts['prevails']}, "
             f"excluded {counts['excluded']}, not discriminating {counts['not discriminating']} (of 12). "
             f"Median half-width of I_c: {hw:.2f} points.\n")
    L.append("## Criterion 1 — negative control, D = V(G1) − V(G1-rand(deg))\n")
    L.append("| City | Configuration | Spacing (m) | Cell side (m) | Median distance test→observed (m) | Test blocks | D [L; U] | Sign | Margin | Verdict |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        q = r["c1"]
        L.append(f"| {r['city']} | {r['configuration']} | {r['spacing_m']:.1f} | {r['cell_side_m']:.0f} | {r['distance_m']:.0f} | "
                 f"{r['test_blocks_median']:.0f} | {fmt(q['D'])} [{fmt(q['L'])}; {fmt(q['U'])}] | {q['readings'][0]} | "
                 f"{q['readings'][1]} | {r['c1_verdict']} |")
    L.append("\n## Secondary — does the graph beat no graph? and the other arms\n")
    L.append("| City | Configuration | V(G1) [L; U] | sign | V(G1-rand(deg)) | V(G1-rand(edges)) | D(G1, rand(edges)) [L; U] | D(rand(deg), rand(edges)) [L; U] |")
    L.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        a, e, f = r["G1_vs_G0"], r["G1_vs_rand_edges"], r["rand_deg_vs_rand_edges"]
        L.append(f"| {r['city']} | {r['configuration']} | {fmt(a['D'])} [{fmt(a['L'])}; {fmt(a['U'])}] | {a['readings'][0]} | "
                 f"{fmt(r['V']['G1-rand(deg)'])} | {fmt(r['V']['G1-rand(edges)'])} | {fmt(e['D'])} [{fmt(e['L'])}; {fmt(e['U'])}] | "
                 f"{fmt(f['D'])} [{fmt(f['L'])}; {fmt(f['U'])}] |")
    fav = sum(r["G1_vs_G0"]["readings"][0] == "favourable" for r in rows)
    L.append(f"\nV(G1) favourable in {fav} of 12 configurations"
             + (": the question \"which geometry\" is empty in E11 and criterion 1 is not read as an answer to it." if fav == 0 else ".") + "\n")
    s, d, t = reg["spacing"], reg["distance_sensitivity"], reg["threshold"]
    L.append("## Criterion 2 — trend (secondary) and distance sensitivity (declared, not a criterion)\n")
    L.append(f"- V(G1) on realised spacing with city term: slope {s['slope_per_m']:+.5f} points/m [{s['L']:+.5f}; {s['U']:+.5f}], "
             f"fitted difference over the range {s['fitted_difference_points']:.2f} points; supported: **{s['supported']}**. "
             f"Without the city term: {s['slope_without_city']:+.5f} points/m.")
    L.append(f"- Sensitivity, median distance test→observed in place of spacing: slope {d['slope_per_m']:+.5f} points/m "
             f"[{d['L']:+.5f}; {d['U']:+.5f}]; without the city term {d['slope_without_city']:+.5f}.\n")
    L.append("## Criterion 3 — threshold form (secondary)\n")
    L.append(f"AIC constant {t['AIC_constant']:.2f}, linear {t['AIC_linear']:.2f}, threshold {t['AIC_threshold']:.2f}; "
             f"breakpoint {t['breakpoint_m']:.1f} m [{t['breakpoint_L']:.1f}; {t['breakpoint_U']:.1f}]; slope difference "
             f"{t['slope_difference']:+.5f} [{t['slope_difference_L']:+.5f}; {t['slope_difference_U']:+.5f}]; threshold form wins: "
             f"**{t['wins']}**" + ("; breakpoint in the unsampled 130–380 m range: not identifiable." if t["breakpoint_in_unsampled_130_380"] else ".") + "\n")
    L.append("## Reported without a criterion\n")
    L.append("| City | Configuration | Cost of not having the sensor, wCE(G1, test-hidden) − wCE(G1, test-observed) | Red recall at 5% false alarms, G0 / G1 / rand(deg) / rand(edges) |")
    L.append("|---|---|---|---|")
    for r in rows:
        k = f"{r['city']} {r['configuration']}"
        rr = " / ".join(f"{extra['red_recall_5pct'][k + ' ' + a]:.3f}" for a in ARMS)
        L.append(f"| {r['city']} | {r['configuration']} | {extra['cost_of_not_having_the_sensor'][k]:+.4f} | {rr} |")
    L.append("\nPer-horizon wCE (15/30/60/120 min) per configuration and arm: `e11_risultati.json`, key `per_horizon_wce`.\n")
    ct, co = extra["counts_test_hidden"], extra["counts_test_observed_G1"]
    L.append("## Deviations and defects\n")
    L.append(f"1. Cells without a valid target (label −1) are excluded from every mean: test-hidden {ct['missing_cells']:,} of "
             f"{ct['cells']:,} cells ({100 * ct['missing_cells'] / ct['cells']:.2f}%); test-observed (G1) {co['missing_cells']:,} of "
             f"{co['cells']:,}. Test-hidden node-runs without any valid target, excluded: {ct['nodes_without_target']}.")
    L.append("2. Dated note, 2026-11-06: the warning `p4b.py:367: Mean of empty slice`, printed once per run (240), comes from "
             "the historical-average table built on observed nodes only; its rows are empty for every hidden node by "
             "construction (D1). The empty mean is replaced by the global mean and hidden rows are set to zero before any "
             "input is built: no NaN reaches inputs, predictions or targets.")
    L.append("3. The frozen preflight, re-run on the signed version, reports one expected failure: its guard asserts that "
             "test metrics are refused while the signature line is blank. The campaign accepted that line only "
             "(`e11_campagna.py`, commit 885cc40).")
    L.append("4. The cost of not having the sensor compares test-hidden nodes with observed nodes whose own data are in "
             "input; in training, targets never have their own input, so this difference is biased against the "
             "observed nodes. It is reported without a criterion, with this caveat.")
    L.append("5. D4 (dropout 0.3) was discarded by the rule fixed before its launch; D2 was replaced by D2-bis as the "
             "positive control (E11.md, Pilot).")
    L.append(f"6. With about {np.median([r['test_blocks_median'] for r in rows]):.0f} test blocks per configuration the "
             f"intervals are wide (median half-width of I_c {hw:.2f} points), as declared in E11.md.")
    L.append("7. Defect of this generator, found at its first run on 2026-11-06 and corrected before any output was "
             "written: the red-recall step indexed `p[:, nodes, :, 2]` in one step, which numpy reorders to "
             "(nodes, origins, horizons) and which stopped with an IndexError. Node selection and class selection are "
             "now separate (`red_recall`), covered by the self-test with origins != nodes.")
    mp = OUT / "CONGELAMENTO_E11.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")


# ---------------------------------------------------------------- self-test ---------------------------

def selftest():
    """Synthetic configurations with a known effect: in config 0 G1 beats G1-rand(deg) by 6% of wCE in every
    seed and node; in config 1 they are identical. The procedure must recover D and the verdicts."""
    g = np.random.default_rng(0)
    cfgs = []
    for ci, gain in enumerate((6.0, 0.0)):
        seeds = {}
        for s in range(5):
            n, H = 40, 4
            blocks = np.repeat(np.arange(8), 5)
            W0 = g.uniform(50, 100, (n, H)); w0 = g.uniform(1.05, 1.10, (n, 1))
            S0 = W0 * w0
            arms = {"G0": (S0, W0), "G1": (S0 * 0.90, W0), "G1-rand(deg)": (S0 * 0.90 * (1 + gain / 100 / 0.90), W0),
                    "G1-rand(edges)": (S0 * 0.95, W0)}
            seeds[s] = {"blocks": blocks, "arms": arms}
        cfgs.append({"city": "madrid", "tag": f"synthetic{ci}", "spacing": 50.0 + 10 * ci, "distance": 100.0,
                     "seeds": seeds})
    rows, _ = analyse(cfgs, lambda ci: np.random.default_rng([BOOT, ci]))
    ok = True
    for r, want_d, want_v in ((rows[0], 6.0, "proximity prevails"), (rows[1], 0.0, None)):
        d = r["c1"]["D"]
        print(f"{r['configuration']}: D = {d:.4f} (expected {want_d}), interval [{r['c1']['L']:.4f}; {r['c1']['U']:.4f}], "
              f"V(G1) = {r['V']['G1']:.4f} (expected 10), verdict {r['c1_verdict']}")
        ok &= abs(d - want_d) < 1e-9 and abs(r["V"]["G1"] - 10.0) < 1e-9
        if want_v:
            ok &= r["c1_verdict"] == want_v
        else:
            ok &= r["c1_verdict"].startswith("geometry advantage") and r["c1"]["L"] <= 0 <= r["c1"]["U"]
    # noisy case: per-node and per-seed heterogeneity, true D = 6 on average; the interval must contain the
    # point estimate, exclude zero and have positive width
    noisy = []
    for ci in range(12):
        seeds = {}
        for s in range(5):
            n, H = 36, 4
            blocks = np.repeat(np.arange(9), 4)
            W0 = g.uniform(50, 100, (n, H)); S0 = W0 * g.uniform(1.0, 1.15, (n, 1))
            f1 = 0.90 + g.normal(0, 0.02, (n, 1)); fr = f1 + 0.06 + g.normal(0, 0.02, (n, 1))
            seeds[s] = {"blocks": blocks, "arms": {"G0": (S0, W0), "G1": (S0 * f1, W0), "G1-rand(deg)": (S0 * fr, W0),
                                                    "G1-rand(edges)": (S0 * fr, W0)}}
        noisy.append({"city": "madrid" if ci < 8 else "melbourne", "tag": f"noisy{ci}", "spacing": 40.0 + 30 * ci,
                      "distance": 80.0 + 10 * ci, "seeds": seeds})
    rows_n, reps_n = analyse(noisy, lambda ci: np.random.default_rng([BOOT, ci]))
    c = rows_n[0]["c1"]
    width_ok = c["L"] < c["D"] < c["U"] and c["U"] - c["L"] > 0 and c["L"] > 0 and 4.5 < c["D"] < 7.5
    print(f"noisy0: D = {c['D']:.3f} [{c['L']:.3f}; {c['U']:.3f}] (true mean 6), verdict {rows_n[0]['c1_verdict']}")
    reg = regressions(rows_n, reps_n)
    print(f"regressions run: slope {reg['spacing']['slope_per_m']:+.5f} [{reg['spacing']['L']:+.5f}; {reg['spacing']['U']:+.5f}], "
          f"threshold wins {reg['threshold']['wins']}")
    ok &= width_ok and reg["spacing"]["L"] <= reg["spacing"]["U"]
    # node_sums against p4b.wce_np on random probabilities with missing labels
    pr = g.dirichlet(np.ones(3), size=(50, 7, 4)).astype("float32"); yv = g.integers(-1, 3, size=(50, 7, 4))
    Wc = np.array([0.8, 0.7, 2.7], dtype="float32"); nodes = np.arange(7)
    S, Wn, miss, tot, zero = node_sums(pr, yv, nodes, Wc)
    agg = float((S.sum() / Wn.sum()))
    ref = p4b.wce_np(pr, yv, Wc)
    print(f"node_sums aggregate {agg:.12f} vs p4b.wce_np {ref:.12f}; missing {miss} of {tot}")
    ok &= abs(agg - ref) < 1e-9 and miss == int((yv < 0).sum())
    # red recall: shapes with origins != nodes, and a known answer. Validation: non-red probabilities uniform
    # on [0, 1); test: red cells with p(red) = 0.97 (above the 5%-false-alarm threshold ~0.95) for half of
    # them and 0.5 for the other half -> recall 0.5
    K, Ov, Ot, H = 20, 997, 400, 4
    vnodes = np.arange(3, 17); tnodes = np.array([0, 1, 2, 17, 18, 19])
    vp = np.zeros((Ov, K, H, 3), "float32"); vp[..., 2] = g.uniform(0, 1, (Ov, K, H))
    vy = np.full((Ov, K, H), -1, "int8"); vy[:, vnodes] = 0
    tp = np.zeros((Ot, K, H, 3), "float32"); ty = np.full((Ot, K, H), -1, "int8")
    ty[:, tnodes] = 2; tp[:Ot // 2, :, :, 2] = 0.97; tp[Ot // 2:, :, :, 2] = 0.5
    rr, t = red_recall(vp, vy, vnodes, tp, ty, tnodes)
    print(f"red recall: {rr:.4f} (expected 0.5000), threshold {t:.4f} (expected ~0.95)")
    ok &= abs(rr - 0.5) < 1e-9 and 0.94 < t < 0.96
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def check_inputs():
    """Checks on the campaign files that read no prediction: run count, configuration and file fingerprints,
    arms per (configuration, seed), identical setups across arms, test-hidden nodes equal to the recomputed node
    sets, keys of every per-cell file, labels without a valid target."""
    recs = [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(RUNS / "*" / "run.json")))]
    print(f"run.json found: {len(recs)} (expected 240)")
    by, bad = {}, 0
    for r in recs:
        cfg = r["config"]; d = RUNS / r["config_fingerprint"]
        bad += int(p4b.fingerprint(cfg) != r["config_fingerprint"])
        for k, f in r["files"].items():
            bad += int(p4b.sha256(d / f["file"], 16) != f["sha256"])
        by.setdefault((cfg["city"], cfg["configuration"], cfg["seed"]), {})[cfg["arm"]] = (r, d)
    miss = tot = zero = 0
    for city, tag, _ in e11.CONFIGS:
        al = p4b.align_graph(city, e11.graph_path(city, tag))
        cells = p4b.grid_cells(al["coords"], p4b.adaptive_grid(al["coords"]))
        for s in e11.SEEDS:
            arms = by.get((city, tag, s), {})
            bad += int(sorted(arms) != sorted(ARMS))
            bad += int(len({json.dumps(arms[a][0]["setup"], sort_keys=True) for a in arms}) != 1)
            lab = p4b.node_sets(cells, s)
            for a, (r, d) in arms.items():
                for k in ("val_hidden", "test_hidden", "test_observed"):
                    with np.load(d / f"{k}.npz") as z:
                        bad += int(sorted(z.files) != ["nodes", "origins", "p", "y"])
                        if k == "test_hidden":
                            bad += int(not np.array_equal(z["nodes"], np.where(lab == 2)[0]))
                            yy = z["y"][:, z["nodes"]]
                            miss += int((yy < 0).sum()); tot += int(yy.size)
                            zero += int(((yy >= 0).sum((0, 2)) == 0).sum())
    print(f"inconsistencies: {bad}; test-hidden cells without a valid target {miss:,} of {tot:,} "
          f"({100 * miss / max(tot, 1):.2f}%); test-hidden node-runs without any valid target: {zero}")
    print("CHECK-INPUTS:", "PASS" if bad == 0 and len(recs) == 240 else "FAIL")
    return 0 if bad == 0 and len(recs) == 240 else 1


def selftest_e2e(tmp):
    """End-to-end run of load_campaign, analyse, regressions and write on a synthetic copy of the campaign:
    same run.json, labels, nodes and origins, but random probabilities, in a temporary folder outside the
    repository. No real prediction is read; the synthetic numbers are meaningless and are not kept."""
    global RUNS, OUT
    import shutil
    tmp = Path(tmp); runs = tmp / "e11"; out = tmp / "congelamenti"
    if tmp.exists():
        shutil.rmtree(tmp)
    runs.mkdir(parents=True)
    g = np.random.default_rng(1)
    for f in sorted(glob.glob(str(RUNS / "*" / "run.json"))):
        r = json.loads(Path(f).read_text()); src = Path(f).parent; dst = runs / src.name; dst.mkdir()
        for k, fi in r["files"].items():
            with np.load(src / fi["file"]) as z:
                y, nodes, origins = z["y"], z["nodes"], z["origins"]
                shape = z["p"].shape
            p = g.dirichlet(np.ones(3), size=shape[:-1]).astype("float32")
            np.savez_compressed(dst / fi["file"], p=p, y=y, origins=origins, nodes=nodes)
            fi["sha256"] = p4b.sha256(dst / fi["file"], 16)
        (dst / "run.json").write_text(json.dumps(r))
    RUNS, OUT = runs, out
    configs, extra = load_campaign()
    rows, reps = analyse(configs, lambda ci: np.random.default_rng([BOOT, ci]))
    statement, counts = summary_statement(rows)
    reg = regressions(rows, reps)
    write(rows, reg, extra, statement, counts)
    ok = (out / "CONGELAMENTO_E11.md").exists() and (out / "e11_risultati.json").exists() and len(rows) == 12
    print(f"synthetic statement (meaningless): {statement} {counts}; files written in {out}")
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary copy removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E11 frozen record")
    ap.add_argument("--selftest-e2e", metavar="TMPDIR", help="end-to-end run on a synthetic copy (random p)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-inputs", action="store_true", help="checks that read no prediction")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.selftest_e2e:
        return selftest_e2e(a.selftest_e2e)
    if a.check_inputs:
        return check_inputs()
    if (OUT / "CONGELAMENTO_E11.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E11.md exists; regenerate only on purpose, after moving it")
    configs, extra = load_campaign()
    rows, reps = analyse(configs, lambda ci: np.random.default_rng([BOOT, ci]))
    statement, counts = summary_statement(rows)
    reg = regressions(rows, reps)
    write(rows, reg, extra, statement, counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
