#!/usr/bin/env python3
"""
Investigation I2 of the A0.2 failures (E13, dated note of 2026-11-19): where is the information of the observed neighbours
lost between the inputs and the predictions of masked nodes? Three diagnostic conditions, requiring four trainings, on the
dependent synthetic control of version 2 (Madrid seed 0, regime I0, configuration C1, 2 000 updates, checkpoint every 500,
initialisation stream p4b.K_INIT, as in A0.2). The A0.2 report `e13_a0_synth.json` (G0 and G1 of the same control and budget,
committed fingerprint checked) is the reference and is not re-run. The A0.2 generator is not modified; R3 uses a separate,
declared investigation control.

  R1  G0, OWN DYNAMIC READINGS RESTORED: starting from the ordinary batch, the three dynamic channels (r, flow, occupancy)
      of the target nodes are restored from their own readings; the historical-average channel and the input indicator are
      left as in the ordinary batch. In training the targets are the masked observed cells; at validation, the
      validation-hidden nodes. Not a history-free run.
  R2  G0 + EXPLICIT GRAPH FEATURE: a 12th input channel, for every node and step of the window, = mean of the input nodes'
      factor r propagated along the adjacency of G1 for RECEPTIVE_HOPS steps, normalised by the propagated indicator of the
      input nodes (exact division by the propagated mass, computed in double precision; zero only where no input node is
      reachable). Computed from the input nodes of the batch only: history-free. No graph convolution. Before training the
      feature is checked against the computation of `e13.tabular_diagnostic` on the same window.
  R3  G1 and a companion G0 on a dependent control with GREATER SPATIAL REGULARITY: the version-2 process with the smoothing
      bandwidth raised from 800 m to 3 000 m (a declared investigation control, not a revision of the A0.2 generator).

Criterion for each condition (as in A0.2): best checkpoint = checkpoint >= 500 with minimal validation wCE of the run; V =
100 (wCE_ref - wCE_run)/wCE_ref at the same checkpoint, reference = the A0.2 G0 trajectory (R1, R2) or the companion G0 (R3).
Diagnostic thresholds fixed before the run (note): R1 +10, R2 +3, R3 +3; the result of each condition is 'diagnostic
threshold reached' or 'not reached', followed by the prudent interpretation of the note. A reached threshold identifies a
condition under which an advantage emerges; a missed one does not by itself establish that the corresponding link fails.
None of these results is a performance statement, none unblocks A1, none amends A0.2.

Freezing checks before any fit: clean working tree; the expected tag reachable from HEAD; `e13.py`, `p4b.py`, `e9.py`,
`e11.py`, `protocol/paper4/E13.md` and this script identical to the tag; expected fingerprint of the reference report.
The output `paper4/runs/e13_a0_invest_I2.json` is written at start (status 'started') and after each condition, so an
interrupted attempt stays identifiable; the script refuses to run if the file exists. Run from the repository root:
PYTHONPATH=paper4/code python3 paper4/code/e13_a0_invest2.py
"""
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd, torch
import p4b, e9, e13

OUT = Path("paper4/runs/e13_a0_invest_I2.json"); REF = Path("paper4/runs/e13_a0_synth.json")
EXPECTED_TAG = "paper4-E13-20261119a"; EXPECTED_REF_SHA16 = "bffd39aaca1d6c9f"
THIS = Path(__file__).resolve(); THIS_REL = "paper4/code/e13_a0_invest2.py"
CAP, CK = 2_000, 500; THRESH = {"R1": 10.0, "R2": 3.0, "R3": 3.0}


def freezing_checks():
    if OUT.exists():
        sys.exit(f"{OUT} exists: the investigation is recorded once (an incomplete attempt is identifiable by its status)")
    if not e13.git_clean():
        sys.exit("working tree not clean")
    tag = e13.frozen_tag()
    if tag != EXPECTED_TAG:
        sys.exit(f"nearest E13 tag is {tag!r}, expected {EXPECTED_TAG}")
    if subprocess.run(["git", "diff", "--quiet", tag, "HEAD", "--", *e13.FROZEN_PATHS, THIS_REL], cwd=e13.ROOT).returncode != 0:
        sys.exit("frozen files or this script differ from the tag")
    if not REF.exists() or p4b.sha256(REF, 16) != EXPECTED_REF_SHA16:
        sys.exit(f"reference report {REF} missing or fingerprint differs from the committed one ({EXPECTED_REF_SHA16})")
    return tag


class OwnReadingsRestored(e13.SetupE13):
    """R1: the target nodes' dynamic channels (0 r, 1 flow, 2 occupancy) come from their own readings; all else unchanged."""
    def batch(s, origins, inp, tgt, static=False):
        x, y, m = super().batch(origins, inp, tgt, static)
        xp, _, _ = super().batch(origins, inp | tgt, tgt, static)
        tm = torch.as_tensor(tgt, device=s.dev).view(1, 1, -1, 1)
        x = x.clone(); x[:, 0:3] = torch.where(tm, xp[:, 0:3], x[:, 0:3])
        return x, y, m


class WithGraphFeature(e13.SetupE13):
    """R2: 12th channel = input nodes' factor r propagated along the G1 adjacency within the receptive field."""
    def set_propagation(s, A, hops):
        A = np.asarray(A, dtype="float64"); M = np.zeros_like(A); P = np.eye(len(A))
        for _ in range(hops):
            P = P @ A; M = M + P
        s.M64 = M                                                                               # (K, K) float64, kept on CPU

    def _fix_cin(s):
        s.c_in = 12

    def feature(s, r_in, inp):
        """r_in (B, K, T) float32 = r * input mask, on the device; returns (B, K, T) float32 on the device."""
        r64 = r_in.detach().cpu().double().numpy(); om = inp.astype("float64")
        num = np.einsum("nm,bmt->bnt", s.M64, r64); den = s.M64 @ om                           # exact masses in float64
        reach = den > 0
        feat = np.zeros_like(num); feat[:, reach, :] = num[:, reach, :] / den[reach][None, :, None]
        return torch.tensor(feat.astype("float32"), device=s.dev)

    def batch(s, origins, inp, tgt, static=False):
        x, y, m = super().batch(origins, inp, tgt, static)
        return torch.cat([x, s.feature(x[:, 0], inp).unsqueeze(1)], 1), y, m

    def check_against_diagnostic(s, z, origins):
        """With inp = all observed nodes, the feature at the origin step must equal the diagnostic's propagated mean."""
        x, _, _ = s.batch(origins, s.obs, s.val)
        f = x[:, 11, :, -1].cpu().numpy()                                                       # (B, K) at the origin
        Mo = s.M64[:, s.obs]; den = Mo.sum(1); num = np.asarray(z, dtype="float64")[origins][:, s.obs] @ Mo.T
        ref = np.where(den[None, :] > 0, num / np.where(den > 0, den, 1.0)[None, :], 0.0)
        return float(np.abs(f - ref).max()), int((den > 0).sum())


def synth_regular(su, kind, seed, ell=3000.0):
    """R3 control: version-2 generator with the smoothing bandwidth as a parameter (3 000 m); otherwise identical."""
    r = np.random.default_rng([seed, 2]); T, K = len(su.ts), su.K
    q = (pd.DatetimeIndex(su.ts).hour.to_numpy() * 4 + pd.DatetimeIndex(su.ts).minute.to_numpy() // 15) / 96.0
    prof = 1.0 - 0.45 * np.exp(-((q - 0.35) ** 2) / 0.004) - 0.45 * np.exp(-((q - 0.73) ** 2) / 0.004)
    xy = np.asarray(su.al["coords"], dtype="float64"); D = np.linalg.norm(xy[:, None] - xy[None], axis=-1)
    S = np.exp(-(D / ell) ** 2); S = S / S.sum(1, keepdims=True)
    amp = r.uniform(0.6, 1.2, K); eta = r.normal(0.0, 1.0, (T, K)); rho = 0.97
    if kind == "dependent":
        amp = S @ amp; eta = eta @ S.T; eta = eta / eta.std()
    u = np.zeros((T, K)); sc = np.sqrt(1 - rho ** 2)
    for t in range(1, T):
        u[t] = rho * u[t - 1] + sc * eta[t]
    z = np.clip(prof[:, None] * amp[None, :] + 0.4 * u + r.normal(0, 0.03, (T, K)), 0.0, 1.6)
    C = np.where(z >= 0.8, 1, np.where(z >= 0.4, 2, 3)).astype("int64")
    flow = (300 * (1.6 - z) + r.normal(0, 20, (T, K))).astype("float32"); occ = (60 * (1.6 - z) / 1.6 + r.normal(0, 3, (T, K))).astype("float32")
    return z.astype("float32"), flow, occ, C


def best_and_V(traj, ref_traj):
    g = {t["update"]: t["val_wce"] for t in traj}; best = min((u for u in g if u >= 500), key=lambda u: (g[u], u))
    return best, 100 * (ref_traj[best] - g[best]) / ref_traj[best]


def fit(su, arm, A):
    o = e13.train_e13(su, arm, A, CAP, e13.CONFIGS["C1"], p4b.K_INIT, ck_every=CK, save_states=False, log=print)
    return {"trajectory": o["trajectory"], "seconds": o["seconds"], "init_seed": o["init_seed"], "hidden_in_batches": o["hidden_in_batches"]}


def save(out):
    OUT.write_text(json.dumps(out, indent=1))


tag = freezing_checks()
ref = json.loads(REF.read_text()); ref_g0 = {t["update"]: t["val_wce"] for t in ref["kinds"]["dependent"]["trajectories"]["G0"]}
out = {"investigation": "I2 (where the neighbours' information is lost)", "status": "started", "cap": CAP, "ck_every": CK, "config": "C1",
       "init_stream": p4b.K_INIT, "thresholds": THRESH, "frozen_tag": tag, "head": e13.head_commit(), "script_sha16": p4b.sha256(THIS, 16),
       "reference": {"file": str(REF), "sha16": p4b.sha256(REF, 16), "G0_dependent": ref_g0,
                     "G1_dependent": {t["update"]: t["val_wce"] for t in ref["kinds"]["dependent"]["trajectories"]["G1"]}},
       "started": datetime.now(timezone.utc).isoformat(), "environment": e13.environment(), "runs": {}}
save(out)

# R1
su = OwnReadingsRestored("madrid", 0, "I0"); z, flow, occ, C = e13.synth_processes(su, "dependent", 20261118); su.inject(z, flow, occ, C)
out["device"] = str(su.dev); save(out)
r = fit(su, "G0", None); best, V = best_and_V(r["trajectory"], ref_g0)
r.update({"best_checkpoint": best, "V_vs_A02_G0": V, "threshold": THRESH["R1"], "result": "diagnostic threshold reached" if V >= THRESH["R1"] else "diagnostic threshold not reached"})
out["runs"]["R1_G0_own_readings_restored"] = r; save(out); print("R1:", r["result"], "V", round(V, 2), "at", best)

# R2
su = WithGraphFeature("madrid", 0, "I0"); z, flow, occ, C = e13.synth_processes(su, "dependent", 20261118); su.inject(z, flow, occ, C)
A1, _ = e9.adjacency(su, "G1"); su.set_propagation(A1, e13.RECEPTIVE_HOPS)
maxdiff, n_reach = su.check_against_diagnostic(z, np.asarray(su.va)[:64])
out["runs"]["R2_feature_check"] = {"max_abs_diff_vs_diagnostic": maxdiff, "nodes_reachable_from_observed": n_reach, "origins_checked": 64}; save(out)
print(f"R2 feature check: max |diff| vs diagnostic {maxdiff:.2e} over 64 validation origins; nodes reachable from the observed set {n_reach}/{su.K}")
if maxdiff > 1e-4:
    out["status"] = "aborted: R2 feature differs from the diagnostic"; save(out); sys.exit(out["status"])
r = fit(su, "G0", None); assert r["hidden_in_batches"] == 0
best, V = best_and_V(r["trajectory"], ref_g0)
r.update({"hops": e13.RECEPTIVE_HOPS, "best_checkpoint": best, "V_vs_A02_G0": V, "threshold": THRESH["R2"], "result": "diagnostic threshold reached" if V >= THRESH["R2"] else "diagnostic threshold not reached"})
out["runs"]["R2_G0_graph_feature"] = r; save(out); print("R2:", r["result"], "V", round(V, 2), "at", best)

# R3
res3 = {"bandwidth_m": 3000.0}
for arm in ("G0", "G1"):
    su = e13.SetupE13("madrid", 0, "I0"); z, flow, occ, C = synth_regular(su, "dependent", 20261118); su.inject(z, flow, occ, C)
    A, _ = e9.adjacency(su, arm)
    if arm == "G1":
        d = e13.tabular_diagnostic(su, z, C, A=A); res3["tabular_diagnostic_graph"] = d
        res3["class_shares"] = (np.bincount(C.ravel(), minlength=4)[1:] / C.size).tolist()
        print("R3 control, tabular diagnostic on the graph feature: mean V", round(d["mean_V"], 1), "class shares", np.round(res3["class_shares"], 3))
    res3[arm] = fit(su, arm, A); assert res3[arm]["hidden_in_batches"] == 0
    out["runs"]["R3_regular_control"] = res3; save(out)
g0i = {t["update"]: t["val_wce"] for t in res3["G0"]["trajectory"]}; best, V = best_and_V(res3["G1"]["trajectory"], g0i)
res3.update({"best_checkpoint_G1": best, "V_G1_vs_G0": V, "threshold": THRESH["R3"], "result": "diagnostic threshold reached" if V >= THRESH["R3"] else "diagnostic threshold not reached"})
out["runs"]["R3_regular_control"] = res3; print("R3:", res3["result"], "V", round(V, 2), "at", best)

out["status"] = "complete"; out["written"] = datetime.now(timezone.utc).isoformat(); c, dirty = p4b.git_commit(); out["commit"] = c; out["code_dirty"] = dirty
save(out); print("->", OUT, p4b.sha256(OUT, 16))
