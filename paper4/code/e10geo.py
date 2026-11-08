#!/usr/bin/env python3
"""
E10-geo — where, geometric (`protocol/paper4/E10geo.md`). Coordinates only; no traffic data, no training.
=========================================================================================================
Imports `p4b.py` and `e9.py` unchanged.

    preflight   controls 1-4 of E10geo.md (populations, blocks = E9 for draws 0-4, same number of sensors
                across rules and no duplicates, determinism); computes no reported quantity
    run         after the signature: for every city, f and rule, 20 draws; writes paper4/runs/e10geo/results.json
    freeze      CONGELAMENTO_E10geo.md, e10geo_risultati.json and the curve e10geo_curva.svg

Rules (same number n of instrumented segments in a draw):
    blocks      observed set of the E9 node-set rule (grid 11/11/15, deficit on (f, 20%, 80% − f)), seed = draw
    uniform     n segments uniformly without replacement
    stratified  five strata by local density (segments within 500 m, quintiles); n split equally, remainder to the
                densest strata; a stratum smaller than its share is filled and the excess goes to the next densest
Generators: default_rng([20261108, rule index (1 uniform, 2 stratified), city index, level index, draw]).

Usage: $PY paper4/code/e10geo.py preflight | run | freeze
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
from genera_congelamento_e9 import runs_by_key  # noqa: E402

PREREG = p4b.ROOT / "protocol" / "paper4" / "E10geo.md"
RUNS = e9.RUNS / "e10geo"
OUT = p4b.ROOT / "paper4" / "congelamenti"
DRAWS = 20
RULES = ("blocks", "uniform", "stratified")
RADII = (250.0, 500.0)
POP = {"madrid": 828, "london": 774, "melbourne": 587}


def population(city):
    al = p4b.align_graph(city, p4b.CITY[city]["roads"])
    return al["coords"], p4b.grid_cells(al["coords"], e9.GRID[city]), al["kept"]


def strata(coords):
    tree = cKDTree(coords)
    dens = np.array([len(x) - 1 for x in tree.query_ball_point(coords, 500.0)])
    edges = np.quantile(dens, [0.2, 0.4, 0.6, 0.8])
    return np.digitize(dens, edges, right=True), dens          # 0 sparsest ... 4 densest


def choose(rule, coords, cells, st, f, draw, ci, li):
    if rule == "blocks":
        return p4b.node_sets(cells, draw, targets=e9.targets(f)) == 0
    n = int(choose("blocks", coords, cells, st, f, draw, ci, li).sum())
    r = np.random.default_rng([20261108, RULES.index(rule), ci, li, draw])
    K = len(coords); obs = np.zeros(K, bool)
    if rule == "uniform":
        obs[r.choice(K, n, replace=False)] = True
        return obs
    alloc = np.full(5, n // 5)
    for k in range(n % 5):
        alloc[4 - k] += 1                                     # remainder to the densest strata
    size = np.array([(st == k).sum() for k in range(5)])
    for k in range(4, -1, -1):                                # overflow to the next densest
        if alloc[k] > size[k]:
            extra = alloc[k] - size[k]; alloc[k] = size[k]
            for j in list(range(4, -1, -1)):
                if j != k and alloc[j] < size[j]:
                    take = min(extra, size[j] - alloc[j]); alloc[j] += take; extra -= take
                if extra == 0:
                    break
    for k in range(5):
        idx = np.where(st == k)[0]
        obs[r.choice(idx, alloc[k], replace=False)] = True
    return obs


def measures(coords, obs):
    d = cKDTree(coords[obs]).query(coords[~obs], k=1)[0]
    return {"within_250": float((d <= RADII[0]).mean()), "within_500": float((d <= RADII[1]).mean()),
            "median_distance": float(np.median(d)), "instrumented_share": float(obs.mean()), "n": int(obs.sum())}


def compute(cities=e9.CITIES, levels=e9.LEVELS, draws=DRAWS):
    out = {}
    for ci, city in enumerate(e9.CITIES):
        if city not in cities:
            continue
        coords, cells, _ = population(city); st, _ = strata(coords)
        for li, f in enumerate(e9.LEVELS):
            if f not in levels:
                continue
            for rule in RULES:
                rows = [measures(coords, choose(rule, coords, cells, st, f, k, ci, li)) for k in range(draws)]
                out[f"{city} {f} {rule}"] = rows
    return out


def preflight(args):
    from e11 import Log
    log = Log(e9.RUNS / "e10geo_preflight.log")
    c, dirty = p4b.git_commit()
    log(f"E10-geo preflight — {datetime.now(timezone.utc).isoformat()} — commit {c} (code dirty: {dirty})")
    log(f"code p4b.py {p4b.sha256(Path(p4b.__file__), 16)} · e9.py {p4b.sha256(Path(e9.__file__), 16)} · e10geo.py {p4b.sha256(Path(__file__), 16)}")
    _, by = runs_by_key(e9.RUNS / "e9")
    pop_ok = blocks_ok = same_ok = True
    for ci, city in enumerate(e9.CITIES):
        coords, cells, kept = population(city); st, dens = strata(coords)
        pop_ok &= len(kept) == POP[city]
        log(f"        {city}: K {len(kept)}, local density (segments within 500 m) median {np.median(dens):.0f}, "
            f"stratum sizes {[int((st == k).sum()) for k in range(5)]}")
        for li, f in enumerate(e9.LEVELS):
            for draw in range(5):
                lab = p4b.node_sets(cells, draw, targets=e9.targets(f))
                blocks_ok &= p4b.fingerprint(lab) == by[(city, f, draw)]["G0"]["setup"]["node_sets"]
            for draw in range(DRAWS):
                sets = [choose(rule, coords, cells, st, f, draw, ci, li) for rule in RULES]
                same_ok &= len({int(x.sum()) for x in sets}) == 1
    log.check("1", "populations equal to E9 (828 / 774 / 587 aligned segments)", pop_ok)
    log.check("2", "blocks rule reproduces the E9 node sets for draws 0-4 (fingerprints of the E9 run records)", blocks_ok)
    log.check("3", "in every draw the three rules instrument the same number of segments; no segment twice (boolean sets)", same_ok)
    a = compute(cities=("madrid",), levels=(0.4,), draws=2); b = compute(cities=("madrid",), levels=(0.4,), draws=2)
    log.check("4", "determinism: two runs with the same generators give identical results (Madrid 40%, 2 draws)", a == b)
    try:
        p4b.require_signed(PREREG); guard = False
    except PermissionError:
        guard = True
    log.check("guard", "the run refuses to start while the E10-geo signature line is blank", guard)
    log(f"PREFLIGHT: {log.fail} failure(s)"); log.save()
    return 0 if log.fail == 0 else 1


def run(args):
    p4b.require_signed(PREREG)
    RUNS.mkdir(parents=True, exist_ok=True); path = RUNS / "results.json"
    if path.exists():
        raise SystemExit(f"STOP: {path} exists")
    res = {"draws": DRAWS, "results": compute(), "code": p4b.sha256(Path(__file__), 16), "commit": p4b.git_commit()[0],
           "written": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(res, indent=1)); print(f"-> {path} ({p4b.sha256(path, 16)})")
    return 0


def svg_curve(table, path):
    """Share of uncovered segments within 250 m against f: one panel per city, one line per rule."""
    W_, H_, pad = 260, 200, 36; colours = {"blocks": "#1f77b4", "uniform": "#d62728", "stratified": "#2ca02c"}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{3 * W_ + 20}" height="{H_ + 50}" font-family="sans-serif" font-size="11">']
    for ci, city in enumerate(e9.CITIES):
        x0 = 10 + ci * W_
        parts.append(f'<text x="{x0 + W_ / 2}" y="14" text-anchor="middle">{city}</text>')
        X = lambda f: x0 + pad + (f - 0.1) / 0.5 * (W_ - pad - 10)  # noqa: E731
        Y = lambda v: 20 + (1 - v) * (H_ - 20)  # noqa: E731
        parts.append(f'<line x1="{x0 + pad}" y1="{Y(0)}" x2="{x0 + W_ - 10}" y2="{Y(0)}" stroke="#888"/>')
        parts.append(f'<line x1="{x0 + pad}" y1="{Y(0)}" x2="{x0 + pad}" y2="{Y(1)}" stroke="#888"/>')
        for v in (0, 0.5, 1):
            parts.append(f'<text x="{x0 + pad - 4}" y="{Y(v) + 4}" text-anchor="end">{v:.1f}</text>')
        for f in e9.LEVELS:
            parts.append(f'<text x="{X(f)}" y="{Y(0) + 14}" text-anchor="middle">{int(f * 100)}%</text>')
        for rule in RULES:
            pts = [(X(f), Y(table[f"{city} {f} {rule}"]["within_250"]["mean"])) for f in e9.LEVELS]
            parts.append('<polyline fill="none" stroke="{}" stroke-width="2" points="{}"/>'.format(
                colours[rule], " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)))
    for k, rule in enumerate(RULES):
        parts.append(f'<rect x="{20 + k * 110}" y="{H_ + 32}" width="12" height="4" fill="{colours[rule]}"/>'
                     f'<text x="{36 + k * 110}" y="{H_ + 38}">{rule}</text>')
    parts.append(f'<text x="{3 * W_ - 10}" y="{H_ + 38}" text-anchor="end">share of uncovered segments within 250 m of a sensor</text></svg>')
    Path(path).write_text("\n".join(parts))


def freeze(args):
    if (OUT / "CONGELAMENTO_E10geo.md").exists():
        raise SystemExit("STOP: CONGELAMENTO_E10geo.md exists; regenerate only on purpose, after moving it")
    src = RUNS / "results.json"; raw = json.loads(src.read_text())
    table = {}
    for key, rows in raw["results"].items():
        table[key] = {m: {"mean": float(np.mean([r[m] for r in rows])), "lo": float(np.percentile([r[m] for r in rows], 2.5)),
                          "hi": float(np.percentile([r[m] for r in rows], 97.5))}
                      for m in ("within_250", "within_500", "median_distance", "instrumented_share")}
    OUT.mkdir(parents=True, exist_ok=True); c, dirty = p4b.git_commit()
    res = {"table": table, "source": str(src.relative_to(p4b.ROOT)), "source_sha256": p4b.sha256(src, 16), "commit": c,
           "code_dirty": dirty, "prereg_fingerprint": p4b.sha256(PREREG, 16), "generator_fingerprint": p4b.sha256(Path(__file__), 16),
           "written": datetime.now(timezone.utc).isoformat()}
    jp = OUT / "e10geo_risultati.json"; jp.write_text(json.dumps(res, indent=1))
    sp = OUT / "e10geo_curva.svg"; svg_curve(table, sp)
    L = ["# CONGELAMENTO_E10geo — where, geometric\n",
         f"Generated by `paper4/code/e10geo.py freeze` ({res['generator_fingerprint']}) on {res['written'][:19]} UTC, commit {c} "
         f"(code dirty: {dirty}). Pre-registration `protocol/paper4/E10geo.md` ({res['prereg_fingerprint']}). Input "
         f"`{res['source']}` ({res['source_sha256']}). {DRAWS} draws per (city, f, rule); mean and 2.5–97.5% range. "
         f"Descriptive, no criterion. Curve: `e10geo_curva.svg` ({p4b.sha256(sp, 16)}).\n",
         "| City | f | Rule | Instrumented share | Uncovered within 250 m | Uncovered within 500 m | Median distance (m) |",
         "|---|---|---|---|---|---|---|"]
    for city in e9.CITIES:
        for f in e9.LEVELS:
            for rule in RULES:
                t = table[f"{city} {f} {rule}"]
                L.append(f"| {city} | {int(f * 100)}% | {rule} | {t['instrumented_share']['mean']:.3f} | "
                         f"{t['within_250']['mean']:.3f} [{t['within_250']['lo']:.3f}; {t['within_250']['hi']:.3f}] | "
                         f"{t['within_500']['mean']:.3f} [{t['within_500']['lo']:.3f}; {t['within_500']['hi']:.3f}] | "
                         f"{t['median_distance']['mean']:.0f} [{t['median_distance']['lo']:.0f}; {t['median_distance']['hi']:.0f}] |")
    mp = OUT / "CONGELAMENTO_E10geo.md"; mp.write_text("\n".join(L) + "\n")
    print(f"frozen record -> {mp} ({p4b.sha256(mp, 16)}); numbers -> {jp} ({p4b.sha256(jp, 16)}); curve -> {sp}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="E10-geo")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for c in ("preflight", "run", "freeze"):
        sp.add_parser(c)
    a = ap.parse_args()
    return {"preflight": preflight, "run": run, "freeze": freeze}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
