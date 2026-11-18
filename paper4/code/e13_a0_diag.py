#!/usr/bin/env python3
"""
A0.2 exploratory diagnosis (E13, dated note of 2026-11-18) of the synthetic positive control, Madrid seed 0, with
`e13.tabular_diagnostic` (PRIVILEGED: class tables estimated on the historical labels of the validation-hidden nodes; it
measures the gain of a chosen tabular predictor from a spatial feature, not a bound on any model) on two features: 'geo5'
(5 nearest observed nodes by UTM distance) and 'graph' (observed values propagated along the adjacency G1 receives, within
the receptive field of its predictions, 6 hops). Also reports the hop distance of the validation-hidden nodes to the nearest observed node
on that adjacency. Version 1 of the generator (tag `paper4-E13-20261118`, failed A0.2 with V(G1) = +0.27) is kept here
verbatim as `synth_v1`; version 2 is `e13.synth_processes`. No neural-network training, no test node. Writes
`paper4/runs/e13_a0_diag.log` and `.json`. Run from the repository root: PYTHONPATH=paper4/code python3 paper4/code/e13_a0_diag.py
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
import p4b, e9, e13
from collections import deque


def synth_v1(su, kind, seed):
    """Generator version 1, verbatim from e13.py at tag paper4-E13-20261118 (consensus dynamics along the kernel adjacency)."""
    r = np.random.default_rng([seed, 2]); T, K = len(su.ts), su.K
    q = (pd.DatetimeIndex(su.ts).hour.to_numpy() * 4 + pd.DatetimeIndex(su.ts).minute.to_numpy() // 15) / 96.0
    prof = 1.0 - 0.45 * np.exp(-((q - 0.35) ** 2) / 0.004) - 0.45 * np.exp(-((q - 0.73) ** 2) / 0.004)
    base = prof[:, None] * r.uniform(0.6, 1.2, K)[None, :]
    A, _ = p4b.kernel_adjacency(su.al["graph"], su.kept); An = A / np.maximum(A.sum(1, keepdims=True), 1e-9)
    z = np.empty((T, K)); z[0] = base[0]; eps = r.normal(0, 0.08, (T, K))
    for t in range(1, T):
        z[t] = 0.7 * (An @ z[t - 1]) + 0.3 * base[t] + eps[t] if kind == "dependent" else 0.6 * z[t - 1] + 0.4 * base[t] + eps[t]
    z = np.clip(z, 0.0, 1.6)
    C = np.where(z >= 0.8, 1, np.where(z >= 0.4, 2, 3)).astype("int64")
    flow = (300 * (1.6 - z) + r.normal(0, 20, (T, K))).astype("float32"); occ = (60 * (1.6 - z) / 1.6 + r.normal(0, 3, (T, K))).astype("float32")
    return z.astype("float32"), flow, occ, C


lines = []
def say(m):
    print(m); lines.append(m)

def hop_distances(A, obs):
    """BFS hop distance from the observed nodes along the direction of propagation of the model: p4b.GCN computes
    out[n] = sum_m A[n, m] x[m], so m influences n when A[n, m] > 0; the step is from m to every n with A[n, m] > 0."""
    A = np.asarray(A); n = len(A); fwd = [np.flatnonzero(A[:, m] > 0) for m in range(n)]; d = np.full(n, -1); q = deque()
    for m in np.flatnonzero(obs):
        d[m] = 0; q.append(m)
    while q:
        m = q.popleft()
        for k in fwd[m]:
            if d[k] < 0:
                d[k] = d[m] + 1; q.append(k)
    return d

out = {}
su0 = e13.SetupE13("madrid", 0, "I0"); A1, _ = e9.adjacency(su0, "G1"); hd = hop_distances(np.asarray(A1), su0.obs)[su0.val]
Aa = np.asarray(A1); R = e13.RECEPTIVE_HOPS
say(f"adjacency passed to G1: {A1.shape}, nonzero {int((Aa > 0).sum())}, symmetric {bool(np.allclose(Aa, Aa.T))}, row sums min/max {Aa.sum(1).min():.3f}/{Aa.sum(1).max():.3f}; "
    f"receptive field of the predictions {R} hops (skip branches, 3 graph convolutions of order 2); hop distance of the {int(su0.val.sum())} validation-hidden nodes "
    f"from the nearest observed node along the propagation direction: {dict(zip(*[x.tolist() for x in np.unique(hd, return_counts=True)]))} (-1 = no path); "
    f"within {R} hops: {int(((hd >= 0) & (hd <= R)).sum())} of {len(hd)} ({100 * ((hd >= 0) & (hd <= R)).mean():.1f} %)")
out["hop_distance_counts"] = {str(k): int(v) for k, v in zip(*np.unique(hd, return_counts=True))}
for version, gen in (("v1", synth_v1), ("v2", e13.synth_processes)):
    for kind in ("dependent", "independent"):
        su = e13.SetupE13("madrid", 0, "I0"); z, flow, occ, C = gen(su, kind, 20261118); su.inject(z, flow, occ, C)
        A1, _ = e9.adjacency(su, "G1"); sh = np.bincount(C.ravel(), minlength=4)[1:] / C.size
        say(f"{version} {kind}: class shares {np.round(sh, 3).tolist()}; W {np.round(np.asarray(su.W), 2).tolist()}; spatial sd of z {z.std(1).mean():.3f}; sd of node means {z.mean(0).std():.3f}")
        res = {}
        for name, d in (("geo5", e13.tabular_diagnostic(su, z, C)), ("graph", e13.tabular_diagnostic(su, z, C, A=A1))):
            extra = f", hidden reached {d['hidden_reached_share']:.3f}" if "hidden_reached_share" in d else ""
            say(f"   {name:5s}: " + "  ".join(f"h={h} V={d[str(h)]['V']:+.1f}" for h in p4b.HORIZONS) + f"  | mean V = {d['mean_V']:+.1f} points{extra}")
            res[name] = d
        out[f"{version}_{kind}"] = {"tabular_diagnostic": res, "class_shares": sh.tolist()}
Path("paper4/runs").mkdir(parents=True, exist_ok=True)
Path("paper4/runs/e13_a0_diag.log").write_text("\n".join(lines) + "\n"); Path("paper4/runs/e13_a0_diag.json").write_text(json.dumps(out, indent=1))
print("-> paper4/runs/e13_a0_diag.log, e13_a0_diag.json")
