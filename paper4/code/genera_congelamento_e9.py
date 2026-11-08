#!/usr/bin/env python3
"""
Generator of the E9 frozen record (`protocol/paper4/E9.md`, signed 2026-11-07, commit efbecae).
================================================================================================
Reads only the campaign files under paper4/runs/e9/ (180 run.json + per-cell .npz) and writes

    paper4/congelamenti/CONGELAMENTO_E9.md     every number of E9, derived by this script
    paper4/congelamenti/e9_risultati.json      the same numbers, machine-readable

Nothing is written by hand; the verdicts are derived mechanically from the criteria of E9.md. The run code
(p4b.py, e9.py, e9_campagna.py) is imported, never changed. The building blocks already verified for E11
(per-node sums, wCE, reading scales, red recall, realised false alarms, OLS) are imported from
`genera_congelamento_e11.py`.

Procedure, as pre-registered:
  * wCE_{c,f,s}(a) on test-hidden nodes: per horizon Σ W[y]·(−log p_y) / Σ W[y] over valid cells, then mean over
    the four horizons; W = class weights of the run;
  * V_{c,f}(a) = mean over seeds of 100·(wCE(G0) − wCE(a))/wCE(G0); D(a, b) = V(a) − V(b);
  * intervals: 4,000 replicates, seeds with replacement and, inside each drawn seed, the corridor blocks (grid
    cells) holding test-hidden nodes, multiplicities kept; the same replicate indices for every arm of a
    (city, f); generator default_rng([20261106, index of (city, f)]) in the order cities × levels;
  * (a) propagation at f; (b) absolute level against ln 3 and G0; (c) step / linear / constant on V(G1) with a
    city term; (d) D(G1, G1-rand(deg)) with the E11 verdict; the derived summary statement;
  * reported without a criterion: red recall at 5% false alarms with the realised false-alarm rate, wCE of G1
    on observed nodes, per-horizon wCE;
  * covariates per (city, f): cell side, median distance test-hidden -> observed, test blocks, realised shares;
  * controls: the `p4b.py:367` empty-slice control recomputed on every rebuilt setup, finite probabilities on
    target nodes in every per-cell file, cells and nodes without a valid target excluded with their counts.

Usage (from the worktree root):

    $PY paper4/code/genera_congelamento_e9.py --selftest
    $PY paper4/code/genera_congelamento_e9.py --check-inputs
    $PY paper4/code/genera_congelamento_e9.py --selftest-e2e <tmpdir>
    $PY paper4/code/genera_congelamento_e9.py [--compare-with <previous e9_risultati.json>]
"""
import argparse
import glob
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
from genera_congelamento_e11 import (node_sums, wce_from, readings, red_recall,  # noqa: E402
                                     realised_false_alarms, ols, aic)

B = 4000
BOOT = 20261106
MARGIN = 3.0
LN3 = float(np.log(3))
ARMS = e9.ARMS
CITIES = e9.CITIES
LEVELS = e9.LEVELS
STEPS = (0.15, 0.30, 0.50)
OUT = p4b.ROOT / "paper4" / "congelamenti"
RUNS = e9.RUNS / "e9"


# ---------------------------------------------------------------- resample per (city, f) ---------------

def multiplicities(cell, r):
    """Seed draws (B, nS) and, per seed, block multiplicities (B, nS, n) for the test-hidden nodes."""
    seeds = sorted(cell["seeds"]); nS = len(seeds)
    sidx = r.integers(0, nS, size=(B, nS))
    mult = {}
    for s in seeds:
        blocks = cell["seeds"][s]["blocks"]; ub = np.unique(blocks)
        draws = r.integers(0, len(ub), size=(B, nS, len(ub)))
        M = np.zeros((B, nS, len(blocks)))
        for bi, b in enumerate(ub):
            M[:, :, blocks == b] += (draws == bi).sum(-1)[..., None]
        mult[s] = M
    return seeds, sidx, mult


def pick(vals, sidx):
    """vals (nS seeds, B, nS slots) -> per replicate, mean over the drawn seed of each slot."""
    return np.take_along_axis(vals.transpose(1, 2, 0), sidx[..., None], -1)[..., 0].mean(-1)


def analyse_cell(cell, r):
    seeds, sidx, mult = multiplicities(cell, r)
    arms = {s: cell["seeds"][s]["arms"] for s in seeds}
    w_pt = {a: [wce_from(*arms[s][a]) for s in seeds] for a in ARMS}
    w_rep = {a: np.stack([wce_from(*arms[s][a], mult[s]) for s in seeds]) for a in ARMS}   # (nS, B, nS)
    out = {"wce": {}, "V": {}, "D": {}}
    for a in ARMS:
        pt = float(np.mean(w_pt[a])); rep = pick(w_rep[a], sidx)
        lo, hi = np.percentile(rep, [2.5, 97.5])
        d = 100 * (LN3 - pt) / LN3; dr = 100 * (LN3 - rep) / LN3
        dlo, dhi = np.percentile(dr, [2.5, 97.5])
        out["wce"][a] = {"wce": pt, "L": float(lo), "U": float(hi), "below_ln3_pct": float(d),
                         "below_ln3_L": float(dlo), "below_ln3_U": float(dhi)}
    v_pt = {a: float(np.mean([100 * (w_pt["G0"][k] - w_pt[a][k]) / w_pt["G0"][k] for k in range(len(seeds))]))
            for a in ARMS}
    v_rep = {a: pick(100 * (w_rep["G0"] - w_rep[a]) / w_rep["G0"], sidx) for a in ARMS}
    for a in ("G1", "G1-rand(deg)"):
        lo, hi = np.percentile(v_rep[a], [2.5, 97.5])
        out["V"][a] = {"V": v_pt[a], "L": float(lo), "U": float(hi), "readings": readings(v_pt[a], lo, hi)}
    d = v_pt["G1"] - v_pt["G1-rand(deg)"]; lo, hi = np.percentile(v_rep["G1"] - v_rep["G1-rand(deg)"], [2.5, 97.5])
    out["D"] = {"D": float(d), "L": float(lo), "U": float(hi), "readings": readings(d, lo, hi), "verdict": verdict_d(d, lo, hi)}
    v = out["V"]["G1"]
    out["helps"] = bool(v["L"] > 0 and v["V"] >= MARGIN)
    out["margin_not_excluded"] = bool(v["U"] >= MARGIN)
    out["halfwidth_V_G1"] = float((v["U"] - v["L"]) / 2)
    return out, v_rep["G1"]


def verdict_d(D, L, U):
    if L > 0 and D >= MARGIN:
        return "proximity prevails"
    if U < MARGIN:
        return "geometry advantage >= 3 points excluded" + (" (randomised >= real)" if (U < 0 or D <= 0) else "")
    return "not discriminating"


def summary_statement(rows):
    H = {f: sum(rows[(c, f)]["helps"] for c in CITIES) for f in LEVELS}
    fstar = None
    for k, f in enumerate(LEVELS):
        if all(H[g] >= 2 for g in LEVELS[k:]):
            fstar = f; break
    if fstar is not None:
        s = ("propagation helps at every f <= 60%" if fstar == LEVELS[0] else f"propagation helps at f >= {int(fstar * 100)}%")
    elif all(rows[(c, f)]["V"]["G1"]["U"] < MARGIN for c in CITIES for f in LEVELS) and not any(H.values()):
        s = "no measurable propagation at any f <= 60%"
    else:
        s = "undetermined"
    n_open = sum(rows[(c, f)]["margin_not_excluded"] for c in CITIES for f in LEVELS)
    return s, {"H": {f"{int(f * 100)}%": H[f] for f in LEVELS}, "f_star": fstar, "pairs_margin_not_excluded": n_open}


# ---------------------------------------------------------------- criterion (c) --------------------------

def city_dummies(city):
    return np.column_stack([(city == c).astype(float) for c in CITIES[1:]])


def step_fit(f, y, city):
    best = None
    for fs in STEPS:
        X = np.column_stack([np.ones_like(f), city_dummies(city), (f > fs).astype(float)])
        beta, rss = ols(X, y)
        if best is None or rss < best[2]:
            best = (fs, float(beta[-1]), rss)
    return best


def criterion_c(keys, y, yrep):
    f = np.array([k[1] for k in keys]); city = np.array([k[0] for k in keys]); n = len(y)
    X0 = np.column_stack([np.ones(n), city_dummies(city)]); X1 = np.column_stack([X0, f])
    _, rss0 = ols(X0, y); b1, rss1 = ols(X1, y)
    fs, bstep, rss2 = step_fit(f, y, city)
    a0, a1, a2 = aic(rss0, n, X0.shape[1]), aic(rss1, n, X1.shape[1]), aic(rss2, n, X0.shape[1] + 2)
    br, fr, sl = [], [], []
    for b in range(yrep.shape[0]):
        fit = step_fit(f, yrep[b], city); br.append(fit[1]); fr.append(fit[0])
        sl.append(ols(X1, yrep[b])[0][-1])
    lo, hi = np.percentile(br, [2.5, 97.5]); slo, shi = np.percentile(sl, [2.5, 97.5])
    dist = {f"{int(x * 100)}%": float(np.mean(np.array(fr) == x)) for x in STEPS}
    wins = bool(a2 <= min(a0, a1) - 2 and (lo > 0 or hi < 0))
    return {"AIC_constant": float(a0), "AIC_linear": float(a1), "AIC_step": float(a2), "linear_slope_per_unit_f": float(b1[-1]),
            "linear_slope_L": float(slo), "linear_slope_U": float(shi), "step_at": fs, "step_size": bstep,
            "step_size_L": float(lo), "step_size_U": float(hi), "step_at_bootstrap": dist, "step_wins": wins}


# ---------------------------------------------------------------- campaign files ------------------------

def runs_by_key(runs_dir):
    recs = [json.loads(Path(p).read_text()) for p in sorted(glob.glob(str(Path(runs_dir) / "*" / "run.json")))]
    by = {}
    for r in recs:
        c = r["config"]
        by.setdefault((c["city"], float(c["f"]), int(c["seed"])), {})[c["arm"]] = r
    return recs, by


def load_campaign(runs_dir=None):
    runs_dir = Path(runs_dir or RUNS)
    recs, by = runs_by_key(runs_dir)
    if len(recs) != 180:
        raise SystemExit(f"STOP: {len(recs)} run.json found, 180 expected")
    for r in recs:
        if p4b.fingerprint(r["config"]) != r["config_fingerprint"] or r["config"]["U"] != 1000:
            raise SystemExit(f"STOP: configuration fingerprint mismatch in {r['config_fingerprint']}")
        d = runs_dir / r["config_fingerprint"]
        for fi in r["files"].values():
            if p4b.sha256(d / fi["file"], 16) != fi["sha256"]:
                raise SystemExit(f"STOP: {d}/{fi['file']} fingerprint differs from run.json")
    ctrl = {"setups": 0, "setups_with_nonfinite_HA": 0, "empty_rows_min": None, "empty_rows_max": None,
            "empty_rows_equal_hidden": True, "observed_without_training_data": 0,
            "runs_with_nonfinite_p_on_targets": 0, "files_checked": 0}
    counts = {"missing_cells": 0, "cells": 0, "nodes_without_target": 0}
    obs_counts = {"missing_cells": 0, "cells": 0}
    cells_by, extra_red, extra_fa, extra_obs, per_h, cov, hours = {}, {}, {}, {}, {}, {}, 0.0
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); cells = p4b.grid_cells(al["coords"], e9.GRID[city])
        for f in LEVELS:
            cell = {"seeds": {}}; geo = []
            for s in e9.SEEDS:
                arms = by.get((city, f, s), {})
                if sorted(arms) != sorted(ARMS):
                    raise SystemExit(f"STOP: {city} f={f} seed {s}: arms {sorted(arms)}")
                if len({json.dumps(arms[a]["setup"], sort_keys=True) for a in ARMS}) != 1:
                    raise SystemExit(f"STOP: {city} f={f} seed {s}: setup fingerprints differ between arms")
                lab = p4b.node_sets(cells, s, targets=e9.targets(f))
                su = e9.setup(city, f, s) if not getattr(load_campaign, "skip_setup", False) else None
                if su is not None:
                    has = np.isfinite(su.r[:su.reg_end]).any(0)
                    empty = int((~(su.obs & has)).sum()); hidden = int((~su.obs).sum())
                    ctrl["setups"] += 1; ctrl["setups_with_nonfinite_HA"] += int(not np.isfinite(su.HA).all())
                    ctrl["empty_rows_min"] = empty if ctrl["empty_rows_min"] is None else min(ctrl["empty_rows_min"], empty)
                    ctrl["empty_rows_max"] = empty if ctrl["empty_rows_max"] is None else max(ctrl["empty_rows_max"], empty)
                    ctrl["empty_rows_equal_hidden"] &= empty == hidden
                    ctrl["observed_without_training_data"] += int((su.obs & ~has).sum())
                    if not np.array_equal(su.lab, lab):
                        raise SystemExit(f"STOP: {city} f={f} seed {s}: node sets of the rebuilt Setup differ")
                entry = {"arms": {}}
                for a in ARMS:
                    r = arms[a]; d = runs_dir / r["config_fingerprint"]; hours += r["train_seconds"] / 3600
                    bad = 0
                    for fname in ("val_hidden", "test_hidden", "test_observed"):
                        with np.load(d / f"{fname}.npz") as q:
                            bad += int(not np.isfinite(q["p"][:, q["nodes"]]).all()); ctrl["files_checked"] += 1
                    ctrl["runs_with_nonfinite_p_on_targets"] += int(bad > 0)
                    z = np.load(d / "test_hidden.npz")
                    if not np.array_equal(z["nodes"], np.where(lab == 2)[0]):
                        raise SystemExit(f"STOP: {d}: test-hidden nodes differ from the recomputed node sets")
                    S, Wn, miss, tot, zero = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"])
                    counts["missing_cells"] += miss; counts["cells"] += tot; counts["nodes_without_target"] += zero
                    keep = Wn.sum(1) > 0
                    entry["arms"][a] = (S[keep], Wn[keep]); entry["blocks"] = cells[z["nodes"]][keep]
                    per_h.setdefault((city, f, a), []).append((S.sum(0) / Wn.sum(0)).tolist())
                    v = np.load(d / "val_hidden.npz")
                    rec_, thr = red_recall(v["p"], v["y"], v["nodes"], z["p"], z["y"], z["nodes"])
                    extra_red.setdefault((city, f, a), []).append(rec_)
                    extra_fa.setdefault((city, f, a), []).append(realised_false_alarms(z["p"], z["y"], z["nodes"], thr))
                    if a == "G1":
                        o = np.load(d / "test_observed.npz")
                        So, Wo, mo, to, _ = node_sums(o["p"], o["y"], o["nodes"], r["class_weights"])
                        obs_counts["missing_cells"] += mo; obs_counts["cells"] += to
                        extra_obs.setdefault((city, f), []).append(wce_from(So, Wo))
                        geo.append({"side": r["geometry"]["cell_side_m"], "dist": r["geometry"]["test_to_nearest_observed_m"]["median"],
                                    "blocks": r["geometry"]["test_blocks"], "obs_share": r["shares"]["observed"]})
                cell["seeds"][s] = entry
            cells_by[(city, f)] = cell
            cov[(city, f)] = {"cell_side_m": float(np.mean([g["side"] for g in geo])),
                              "median_distance_test_to_observed_m": float(np.median([g["dist"] for g in geo])),
                              "test_blocks_min": int(min(g["blocks"] for g in geo)),
                              "test_blocks_median": float(np.median([g["blocks"] for g in geo])),
                              "realised_observed_share": float(np.mean([g["obs_share"] for g in geo]))}
    extra = {"empty_slice_control": ctrl, "counts_test_hidden": counts, "counts_test_observed_G1": obs_counts,
             "machine_hours": hours, "n_runs": len(recs),
             "run_index_fingerprint": p4b.fingerprint(sorted(r["config_fingerprint"] for r in recs)),
             "red_recall_5pct": {f"{k[0]} {k[1]} {k[2]}": float(np.nanmean(v)) for k, v in extra_red.items()},
             "false_alarm_rate_test_5pct": {f"{k[0]} {k[1]} {k[2]}": float(np.nanmean(v)) for k, v in extra_fa.items()},
             "wce_G1_test_observed": {f"{k[0]} {k[1]}": float(np.mean(v)) for k, v in extra_obs.items()},
             "per_horizon_wce": {f"{k[0]} {k[1]} {k[2]}": np.mean(v, 0).tolist() for k, v in per_h.items()},
             "covariates": {f"{k[0]} {k[1]}": v for k, v in cov.items()}}
    return cells_by, extra


def analyse_all(cells_by):
    rows, reps, keys = {}, [], []
    for ci, (city, f) in enumerate([(c, f) for c in CITIES for f in LEVELS]):
        out, rep = analyse_cell(cells_by[(city, f)], np.random.default_rng([BOOT, ci]))
        rows[(city, f)] = out; reps.append(rep); keys.append((city, f))
    y = np.array([rows[k]["V"]["G1"]["V"] for k in keys])
    crit_c = criterion_c(keys, y, np.stack(reps, 1))
    statement, info = summary_statement(rows)
    return rows, crit_c, statement, info


# ---------------------------------------------------------------- writing -------------------------------

def fmt(x, n=2):
    return f"{x:+.{n}f}"


def write(rows, crit_c, statement, info, extra, out_dir=None):
    out_dir = Path(out_dir or OUT); out_dir.mkdir(parents=True, exist_ok=True)
    c, dirty = p4b.git_commit()
    hw = float(np.median([rows[k]["halfwidth_V_G1"] for k in rows]))
    res = {"rows": {f"{k[0]} {k[1]}": v for k, v in rows.items()}, "criterion_c": crit_c, "summary_statement": statement,
           "summary_info": info, "median_halfwidth_V_G1": hw, **extra, "commit": c, "code_dirty": dirty,
           "prereg_fingerprint": p4b.sha256(e9.PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = out_dir / "e9_risultati.json"; jp.write_text(json.dumps(res, indent=1, default=float))
    L = ["# CONGELAMENTO_E9 — coverage curve: how many sensors?\n"]
    L.append(f"Generated by `paper4/code/genera_congelamento_e9.py` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, "
             f"commit {c} (code dirty: {dirty}). Pre-registration `protocol/paper4/E9.md` ({res['prereg_fingerprint']}), signed at "
             f"efbecae. Inputs: {extra['n_runs']} runs under `paper4/runs/e9/`, index fingerprint {extra['run_index_fingerprint']}; every "
             f"per-cell file checked against its run.json. Machine time: {extra['machine_hours']:.2f} h of training (Mac M3, MPS, two "
             f"concurrent processes; not isolated). V and D in points of the G0 wCE, positive = the first arm is better. Intervals: 95%, "
             f"{B} replicates, seeds × corridor blocks (grid cells).\n")
    L.append(f"## Summary statement (derived from criterion a)\n\n**{statement}** — cities where propagation helps, by f: "
             + ", ".join(f"{k} {v}/3" for k, v in info["H"].items())
             + f"; (city, f) pairs where an advantage of 3 points is not excluded: {info['pairs_margin_not_excluded']} of 12. "
             f"Median half-width of V(G1): {hw:.2f} points.\n")
    L.append("## (a) Propagation at f, and covariates\n")
    L.append("| City | f | Realised observed share | Cell side (m) | Median distance test→observed (m) | Test blocks (min) | V(G1) [L; U] | Sign | Margin | Propagation helps |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for (city, f), r in rows.items():
        v = r["V"]["G1"]; cv = extra["covariates"][f"{city} {f}"]
        L.append(f"| {city} | {int(f * 100)}% | {cv['realised_observed_share']:.3f} | {cv['cell_side_m']:.0f} | "
                 f"{cv['median_distance_test_to_observed_m']:.0f} | {cv['test_blocks_min']} | {fmt(v['V'])} [{fmt(v['L'])}; {fmt(v['U'])}] | "
                 f"{v['readings'][0]} | {v['readings'][1]} | {'yes' if r['helps'] else 'no'} |")
    L.append("\n## (b) Absolute level on test-hidden nodes\n")
    L.append("| City | f | wCE G0 [L; U] | below ln 3 (%) | wCE G1 [L; U] | below ln 3 (%) [L; U] | wCE G1-rand(deg) |")
    L.append("|---|---|---|---|---|---|---|")
    for (city, f), r in rows.items():
        g0, g1, gr = r["wce"]["G0"], r["wce"]["G1"], r["wce"]["G1-rand(deg)"]
        L.append(f"| {city} | {int(f * 100)}% | {g0['wce']:.4f} [{g0['L']:.4f}; {g0['U']:.4f}] | {g0['below_ln3_pct']:.2f} | "
                 f"{g1['wce']:.4f} [{g1['L']:.4f}; {g1['U']:.4f}] | {g1['below_ln3_pct']:.2f} [{g1['below_ln3_L']:.2f}; {g1['below_ln3_U']:.2f}] | "
                 f"{gr['wce']:.4f} |")
    L.append(f"\nln 3 = {LN3:.4f} (uniform predictor).\n")
    t = crit_c
    L.append("## (c) Coverage threshold (secondary)\n")
    L.append(f"V(G1) at the 12 points with a city term: AIC constant {t['AIC_constant']:.2f}, linear {t['AIC_linear']:.2f}, step "
             f"{t['AIC_step']:.2f}. Linear slope {t['linear_slope_per_unit_f']:+.3f} points per unit of f [{t['linear_slope_L']:+.3f}; "
             f"{t['linear_slope_U']:+.3f}]. Best step at f > {int(t['step_at'] * 100)}%, size {t['step_size']:+.2f} [{t['step_size_L']:+.2f}; "
             f"{t['step_size_U']:+.2f}]; bootstrap distribution of the step position "
             + ", ".join(f"{k} {v:.2f}" for k, v in t["step_at_bootstrap"].items())
             + f". Step form wins: **{t['step_wins']}**.\n")
    L.append("## (d) Geometry at f: D = V(G1) − V(G1-rand(deg)) (secondary)\n")
    L.append("| City | f | D [L; U] | Sign | Margin | Verdict | V(G1-rand(deg)) [L; U] |")
    L.append("|---|---|---|---|---|---|---|")
    for (city, f), r in rows.items():
        dd, vr = r["D"], r["V"]["G1-rand(deg)"]
        L.append(f"| {city} | {int(f * 100)}% | {fmt(dd['D'])} [{fmt(dd['L'])}; {fmt(dd['U'])}] | {dd['readings'][0]} | {dd['readings'][1]} | "
                 f"{dd['verdict']} | {fmt(vr['V'])} [{fmt(vr['L'])}; {fmt(vr['U'])}] |")
    L.append("\n## Reported without a criterion\n")
    L.append("| City | f | Red recall at 5% false alarms, G0 / G1 / G1-rand(deg) | Realised false-alarm rate on test, same order | wCE G1 on observed nodes (test) |")
    L.append("|---|---|---|---|---|")
    for (city, f) in rows:
        k = f"{city} {f}"
        rr = " / ".join(f"{extra['red_recall_5pct'][k + ' ' + a]:.3f}" for a in ARMS)
        ff = " / ".join(f"{extra['false_alarm_rate_test_5pct'][k + ' ' + a]:.3f}" for a in ARMS)
        L.append(f"| {city} | {int(f * 100)}% | {rr} | {ff} | {extra['wce_G1_test_observed'][k]:.4f} |")
    L.append("\nPer-horizon wCE per (city, f, arm): `e9_risultati.json`, key `per_horizon_wce`.\n")
    ct, co, k = extra["counts_test_hidden"], extra["counts_test_observed_G1"], extra["empty_slice_control"]
    L.append("## Controls, deviations and defects\n")
    L.append(f"1. Cells without a valid target (label −1) are excluded from every mean: test-hidden {ct['missing_cells']:,} of "
             f"{ct['cells']:,} cells ({100 * ct['missing_cells'] / max(ct['cells'], 1):.2f}%); test-observed (G1) {co['missing_cells']:,} of "
             f"{co['cells']:,}. Test-hidden node-runs without any valid target, excluded: {ct['nodes_without_target']}.")
    L.append("2. Control of the warning `p4b.py:367: Mean of empty slice` (as in E11): it comes from the historical-average table "
             "(node × weekly slot), built on observed nodes only (D1); the empty rows lie on the node axis. Checked by this generator "
             f"on the {k['setups']} rebuilt setups (city × f × seed; the arms of a seed share them): empty rows "
             f"{k['empty_rows_min']}–{k['empty_rows_max']} per setup, equal to the hidden nodes in every setup: {k['empty_rows_equal_hidden']}; "
             f"observed nodes without training data: {k['observed_without_training_data']}; setups with a non-finite value in the "
             f"historical average: {k['setups_with_nonfinite_HA']}. Per-cell files with a non-finite probability on target nodes: "
             f"{k['runs_with_nonfinite_p_on_targets']} runs of 180 ({k['files_checked']} files checked). No NaN enters the means or the "
             "resample, which use per-node sums over valid cells only (item 1).")
    L.append("3. Cost measurement (E9.md, Deviations 1): the two first isolated measurements of G1-rand(deg) were taken during "
             "Spotlight indexing and are not used; the cost table uses the measurement with Spotlight idle.")
    L.append("4. The wCE of G1 on observed nodes is reported with the caveat of E11: in training, targets never have their own "
             "input, so the comparison with hidden nodes is biased against the observed nodes.")
    L.append(f"5. The campaign ran in two concurrent processes (`--shard 1/2`, `2/2`); machine time {extra['machine_hours']:.2f} h is not "
             "an isolated cost.")
    mp = out_dir / "CONGELAMENTO_E9.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)})")
    return mp, jp


# ---------------------------------------------------------------- checks and self-tests -----------------

def check_inputs(runs_dir=None):
    runs_dir = Path(runs_dir or RUNS)
    recs, by = runs_by_key(runs_dir)
    print(f"run.json found: {len(recs)} (expected 180)")
    bad = miss = tot = zero = 0
    for r in recs:
        d = runs_dir / r["config_fingerprint"]
        bad += int(p4b.fingerprint(r["config"]) != r["config_fingerprint"])
        bad += sum(int(p4b.sha256(d / fi["file"], 16) != fi["sha256"]) for fi in r["files"].values())
    for city in CITIES:
        al = p4b.align_graph(city, p4b.CITY[city]["roads"]); cells = p4b.grid_cells(al["coords"], e9.GRID[city])
        for f in LEVELS:
            for s in e9.SEEDS:
                arms = by.get((city, f, s), {})
                bad += int(sorted(arms) != sorted(ARMS))
                bad += int(len({json.dumps(arms[a]["setup"], sort_keys=True) for a in arms}) != 1)
                lab = p4b.node_sets(cells, s, targets=e9.targets(f))
                bad += int(len(np.unique(cells[lab == 2])) < e9.MIN_TEST_BLOCKS)
                for a, r in arms.items():
                    d = runs_dir / r["config_fingerprint"]
                    for k in ("val_hidden", "test_hidden", "test_observed"):
                        with np.load(d / f"{k}.npz") as z:
                            bad += int(sorted(z.files) != ["nodes", "origins", "p", "y"])
                            if k == "test_hidden":
                                bad += int(not np.array_equal(z["nodes"], np.where(lab == 2)[0]))
                                yy = z["y"][:, z["nodes"]]
                                miss += int((yy < 0).sum()); tot += int(yy.size); zero += int(((yy >= 0).sum((0, 2)) == 0).sum())
    print(f"inconsistencies: {bad}; test-hidden cells without a valid target {miss:,} of {tot:,} ({100 * miss / max(tot, 1):.2f}%); "
          f"test-hidden node-runs without any valid target: {zero}")
    ok = bad == 0 and len(recs) == 180
    print("CHECK-INPUTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest():
    """Synthetic (city, f) cells with a known effect. Case A: V(G1) = 6 at f >= 40% in every city, 0 below ->
    "propagation helps at f >= 40%" and a step after 30% that wins. Case B: V(G1) = 0 everywhere, no noise ->
    "no measurable propagation". Case C: noise between nodes, true V = 5 at every f -> interval contains the
    point, excludes zero, statement "propagation helps at every f <= 60%". Plus the per-node sums against p4b."""
    g = np.random.default_rng(0); ok = True

    def make(effect, noise):
        cells_by = {}
        for city in CITIES:
            for f in LEVELS:
                seeds = {}
                for s in e9.SEEDS:
                    n, H = 60, 4; blocks = np.repeat(np.arange(12), 5)
                    W0 = g.uniform(50, 100, (n, H)); S0 = W0 * g.uniform(1.0, 1.1, (n, 1))
                    e = effect(f) / 100
                    f1 = (1 - e) + (g.normal(0, noise, (n, 1)) if noise else 0)
                    fr = (1 - e / 2) + (g.normal(0, noise, (n, 1)) if noise else 0)
                    seeds[s] = {"blocks": blocks, "arms": {"G0": (S0, W0), "G1": (S0 * f1, W0), "G1-rand(deg)": (S0 * fr, W0)}}
                cells_by[(city, f)] = {"seeds": seeds}
        return cells_by
    rows, c, st, info = analyse_all(make(lambda f: 6.0 if f >= 0.4 else 0.0, 0.0))
    print(f"A: statement '{st}', H {info['H']}; V(G1) at 40% = {rows[('madrid', 0.4)]['V']['G1']['V']:.4f}; step at "
          f"{c['step_at']}, size {c['step_size']:.3f}, wins {c['step_wins']}")
    ok &= st == "propagation helps at f >= 40%" and abs(rows[("madrid", 0.4)]["V"]["G1"]["V"] - 6) < 1e-9 and c["step_at"] == 0.30
    rows, c, st, info = analyse_all(make(lambda f: 0.0, 0.0))
    print(f"B: statement '{st}'"); ok &= st == "no measurable propagation at any f <= 60%"
    rows, c, st, info = analyse_all(make(lambda f: 5.0, 0.02))
    v = rows[("london", 0.2)]["V"]["G1"]
    print(f"C: statement '{st}'; V(G1) london 20% = {v['V']:.3f} [{v['L']:.3f}; {v['U']:.3f}]")
    ok &= v["L"] < v["V"] < v["U"] and v["L"] > 0 and st == "propagation helps at every f <= 60%"
    pr = g.dirichlet(np.ones(3), size=(40, 9, 4)).astype("float32"); yv = g.integers(-1, 3, size=(40, 9, 4))
    Wc = np.array([0.7, 0.75, 3.9], dtype="float32")
    S, Wn, *_ = node_sums(pr, yv, np.arange(9), Wc)
    ok &= abs(float(S.sum() / Wn.sum()) - p4b.wce_np(pr, yv, Wc)) < 1e-9
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest_e2e(tmp):
    """Whole pipeline on a synthetic copy: same run.json, labels, nodes and origins; probabilities set to a
    structured function of the label (compressible), with G1 better than G0 at f >= 40%. No real prediction is
    read; the synthetic numbers are meaningless and are removed."""
    tmp = Path(tmp)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e9"; runs.mkdir(parents=True)
    for p in sorted(glob.glob(str(RUNS / "*" / "run.json"))):
        r = json.loads(Path(p).read_text()); src = Path(p).parent; dst = runs / src.name; dst.mkdir()
        q = 0.40 + (0.05 if (r["config"]["arm"] == "G1" and r["config"]["f"] >= 0.4) else 0.0)
        for fi in r["files"].values():
            with np.load(src / fi["file"]) as z:
                y, nodes, origins = z["y"], z["nodes"], z["origins"]; shape = z["p"].shape
            pr = np.full(shape, (1 - q) / 2, dtype="float32")
            lab = np.where(y >= 0, y, 0).astype(np.int64)
            np.put_along_axis(pr, lab[..., None], np.float32(q), -1)
            np.savez_compressed(dst / fi["file"], p=pr, y=y, origins=origins, nodes=nodes)
            fi["sha256"] = p4b.sha256(dst / fi["file"], 16)
        (dst / "run.json").write_text(json.dumps(r))
    cells_by, extra = load_campaign(runs)
    rows, c, st, info = analyse_all(cells_by)
    write(rows, c, st, info, extra, out_dir=tmp / "congelamenti")
    ok = (tmp / "congelamenti" / "CONGELAMENTO_E9.md").exists() and len(rows) == 12
    print(f"synthetic statement: {st} (expected 'propagation helps at f >= 40%')")
    ok &= st == "propagation helps at f >= 40%"
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary copy removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E9 frozen record")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--check-inputs", action="store_true", help="checks that read no prediction")
    ap.add_argument("--selftest-e2e", metavar="TMPDIR")
    ap.add_argument("--compare-with", metavar="JSON", help="previous e9_risultati.json: every number must be identical")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.check_inputs:
        return check_inputs()
    if a.selftest_e2e:
        return selftest_e2e(a.selftest_e2e)
    if (OUT / "CONGELAMENTO_E9.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E9.md exists; regenerate only on purpose, after moving it")
    cells_by, extra = load_campaign()
    rows, c, st, info = analyse_all(cells_by)
    write(rows, c, st, info, extra)
    if a.compare_with:
        old = json.loads(Path(a.compare_with).read_text()); new = json.loads((OUT / "e9_risultati.json").read_text())
        diff = [k for k in old if k not in ("commit", "code_dirty", "generator_fingerprint", "written") and old[k] != new.get(k)]
        print("comparison:", "every number identical" if not diff else f"DIFFERENT keys: {diff}")
        return 0 if not diff else 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
