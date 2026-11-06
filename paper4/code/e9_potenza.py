#!/usr/bin/env python3
"""
E9 — power calculation from the dispersion of E11 (internal review, 2026-11-06 20:45).
=======================================================================================
Reads the E11 campaign (frozen and accepted): test-hidden per-node sums of G0 and G1. For every E11
configuration it estimates

  * the variance between seeds of V_s = 100·(wCE_s(G0) − wCE_s(G1)) / wCE_s(G0);
  * the variance within a seed from a block resample (1,000 replicates), turned into a per-block unit
    u = variance × number of test blocks.

For E9 (whole cities, 6x6 grid, test-hidden share 0.8 − f) the expected half-width of V(G1) − V(G0) with
n_s seeds and n_b test blocks is 1.96·sqrt(σ²_seed/n_s + u/(n_b·n_s)), with σ²_seed and u taken as the median
over the E11 configurations. Two versions: "unscaled" (u as in E11, conservative) and "scaled by block size"
(u × nodes per E11 block / nodes per E9 block, if node-level noise were independent). The number of test blocks
of E9 is computed from the node sets of the E9 design (no training). Order of magnitude, not a criterion.

Usage: $PY paper4/code/e9_potenza.py      (writes paper4/runs/e9_potenza.json)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e11  # noqa: E402
from genera_congelamento_e11 import node_sums, wce_from  # noqa: E402

LEVELS = (0.1, 0.2, 0.4, 0.6)
CITIES = ("madrid", "london", "melbourne")
D = p4b.T4C
ROADS = {"madrid": D / "MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl",
         "london": D / "LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl",
         "melbourne": D / "MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl"}
p4b.CITY.setdefault("london", {"targets": D / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
                               "sensors": D / "LONDON_2022/gomo_fmt/t4cmad_sensors.csv", "roads": ROADS["london"]})


def e11_components():
    recs = [json.loads(p.read_text()) for p in sorted((e11.RUNS / "e11").glob("*/run.json"))]
    by = {}
    for r in recs:
        c = r["config"]
        if c["arm"] in ("G0", "G1"):
            by.setdefault((c["city"], c["configuration"]), {}).setdefault(c["seed"], {})[c["arm"]] = r
    rng = np.random.default_rng(20261106)
    out = []
    for (city, tag), seeds in sorted(by.items()):
        al = p4b.align_graph(city, e11.graph_path(city, tag))
        cells = p4b.grid_cells(al["coords"], p4b.adaptive_grid(al["coords"]))
        vs, units, npb = [], [], []
        for s, arms in sorted(seeds.items()):
            sums = {}
            for a, r in arms.items():
                with np.load(e11.RUNS / "e11" / r["config_fingerprint"] / "test_hidden.npz") as z:
                    S, Wn, *_ = node_sums(z["p"], z["y"], z["nodes"], r["class_weights"]); nodes = z["nodes"]
                sums[a] = (S, Wn)
            blocks = cells[nodes]; ub = np.unique(blocks)
            w0, w1 = wce_from(*sums["G0"]), wce_from(*sums["G1"])
            vs.append(100 * (w0 - w1) / w0)
            draws = rng.integers(0, len(ub), size=(1000, len(ub)))
            M = np.zeros((1000, len(blocks)))
            for bi, b in enumerate(ub):
                M[:, blocks == b] += (draws == bi).sum(1)[:, None]
            r0, r1 = wce_from(*sums["G0"], M), wce_from(*sums["G1"], M)
            units.append(float(np.var(100 * (r0 - r1) / r0) * len(ub)))
            npb.append(len(blocks) / len(ub))
        out.append({"city": city, "configuration": tag, "seed_variance": float(np.var(vs, ddof=1)),
                    "block_unit_variance": float(np.median(units)), "nodes_per_block": float(np.mean(npb))})
    return out


def e9_blocks():
    res = {}
    for city in CITIES:
        al = p4b.align_graph(city, ROADS[city]); cells = p4b.grid_cells(al["coords"], 6)
        for f in LEVELS:
            nb, npb = [], []
            for s in range(5):
                lab = p4b.node_sets(cells, s, targets=(f, 0.2, 0.8 - f))
                tb = np.unique(cells[lab == 2]); nb.append(len(tb)); npb.append((lab == 2).sum() / len(tb))
            res[f"{city} {f:.1f}"] = {"test_blocks_median": float(np.median(nb)), "test_blocks_min": int(min(nb)),
                                      "nodes_per_block": float(np.mean(npb)), "K": len(al["kept"]),
                                      "occupied_cells": int(len(np.unique(cells)))}
    return res


def main():
    comp = e11_components()
    s2 = float(np.median([c["seed_variance"] for c in comp])); u = float(np.median([c["block_unit_variance"] for c in comp]))
    npb11 = float(np.median([c["nodes_per_block"] for c in comp]))
    blocks = e9_blocks()
    proj = {}
    for k, b in blocks.items():
        for ns in (5, 8, 12):
            nb = b["test_blocks_min"]
            hw_u = 1.96 * np.sqrt(s2 / ns + u / (nb * ns))
            hw_s = 1.96 * np.sqrt(s2 / ns + u * (npb11 / b["nodes_per_block"]) / (nb * ns))
            proj[f"{k} seeds {ns}"] = {"halfwidth_unscaled": round(float(hw_u), 2), "halfwidth_scaled": round(float(hw_s), 2),
                                       "test_blocks_min": nb}
    out = {"source": "E11 campaign, test-hidden G0 and G1 (frozen record ba8b19a)", "seed_variance_median": s2,
           "block_unit_variance_median": u, "e11_nodes_per_block_median": npb11, "e11_components": comp,
           "e9_blocks": blocks, "projection": proj, "written": datetime.now(timezone.utc).isoformat(),
           "commit": p4b.git_commit()[0]}
    path = e11.RUNS / "e9_potenza.json"; path.write_text(json.dumps(out, indent=1))
    print(f"E11: median seed variance {s2:.3f}, median per-block unit {u:.3f}, nodes per block {npb11:.1f}")
    for k, b in blocks.items():
        print(f"{k}: K {b['K']}, occupied {b['occupied_cells']}, test blocks median {b['test_blocks_median']:.0f} (min {b['test_blocks_min']}), "
              f"nodes/block {b['nodes_per_block']:.0f} | half-width 5 seeds: unscaled {proj[k + ' seeds 5']['halfwidth_unscaled']}, "
              f"scaled {proj[k + ' seeds 5']['halfwidth_scaled']}; 8 seeds {proj[k + ' seeds 8']['halfwidth_unscaled']}/"
              f"{proj[k + ' seeds 8']['halfwidth_scaled']}; 12 seeds {proj[k + ' seeds 12']['halfwidth_unscaled']}/{proj[k + ' seeds 12']['halfwidth_scaled']}")
    print(f"-> {path} ({p4b.sha256(path, 16)})")


if __name__ == "__main__":
    main()
