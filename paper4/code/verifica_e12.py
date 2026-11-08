#!/usr/bin/env python3
"""
E12 — checks around the frozen `e12.py` (3ec453d15372b217), which is imported and never changed.
================================================================================================
    --check-inputs        after `e12.py run`: the 60 (city, f, seed) folders under paper4/runs/e12/ exist, each
                          run.json matches its sums.npz and thresholds.json fingerprints, the thresholds were
                          saved before the test (their fingerprint file exists and matches), the code
                          fingerprints recorded in run.json equal the frozen ones, the setup equals E9's, and the
                          arrays have the expected keys and shapes. No metric is read.
    --selftest-e2e TMPDIR `e12.py freeze` end to end on 60 synthetic (city, f, seed) folders in TMPDIR, with a
                          planted signal (P-nn better than G0 by 5% of wCE at f >= 40%, nothing elsewhere); the
                          derived statement must name P-nn at 40% and 60%. TMPDIR is removed at the end.

Usage (from the worktree root):
    $PY paper4/code/verifica_e12.py --check-inputs
    $PY paper4/code/verifica_e12.py --selftest-e2e <tmpdir>
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import e9  # noqa: E402
import e12  # noqa: E402
from genera_congelamento_e9 import runs_by_key  # noqa: E402

FROZEN = {"e12.py": "3ec453d15372b217", "p4b.py": "926061038a7472a3"}
PAIRS = [(c, f, s) for c in e9.CITIES for f in e9.LEVELS for s in e9.SEEDS]
KEYS = {f"{nm}|{k}" for nm in e12.ALL for k in ("S", "Wn", "Su", "Wu")} | {"G0|S", "G0|Wn", "G1|S", "G1|Wn", "blocks"}


def check_inputs():
    here = Path(__file__).resolve().parent
    bad = [f"{n} fingerprint differs from the frozen one" for n, fp in FROZEN.items() if p4b.sha256(here / n, 16) != fp]
    _, by = runs_by_key(e12.E9RUNS)
    found = 0
    for city, f, s in PAIRS:
        d = e12.RUNS / f"{city}_{int(f * 100)}_s{s}"
        if not (d / "run.json").exists():
            bad.append(f"{d.name}: run.json missing"); continue
        found += 1
        r = json.loads((d / "run.json").read_text())
        if p4b.sha256(d / "sums.npz", 16) != r["sums_sha256"]:
            bad.append(f"{d.name}: sums.npz fingerprint differs")
        th = p4b.sha256(d / "thresholds.json", 16)
        if th != r["thresholds_sha256"] or th != json.loads((d / "thresholds.fingerprint").read_text())["sha256"]:
            bad.append(f"{d.name}: thresholds fingerprint differs")
        if r["code"] != FROZEN:
            bad.append(f"{d.name}: run made with code {r['code']}")
        if r["setup"] != by[(city, f, s)]["G0"]["setup"]:
            bad.append(f"{d.name}: setup differs from E9")
        with np.load(d / "sums.npz") as z:
            if set(z.files) != KEYS:
                bad.append(f"{d.name}: keys {sorted(set(z.files) ^ KEYS)}")
            else:
                n = len(z["blocks"])
                if any(z[k].shape != (n, len(e12.H)) for k in KEYS if k != "blocks"):
                    bad.append(f"{d.name}: array shapes inconsistent")
    print(f"runs found: {found} of {len(PAIRS)}; inconsistencies: {len(bad)}")
    for b in bad[:20]:
        print("  -", b)
    ok = found == len(PAIRS) and not bad
    print("CHECK-INPUTS:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def selftest_e2e(tmp):
    tmp = Path(tmp)
    if tmp.exists():
        shutil.rmtree(tmp)
    runs = tmp / "e12"; runs.mkdir(parents=True)
    g = np.random.default_rng(3)
    for city, f, s in PAIRS:
        d = runs / f"{city}_{int(f * 100)}_s{s}"; d.mkdir()
        n = 40; blocks = np.repeat(np.arange(10), 4)
        W0 = g.uniform(50, 100, (n, len(e12.H))); S0 = W0 * g.uniform(1.05, 1.10, (n, 1))
        arr = {"G0|S": S0, "G0|Wn": W0, "G1|S": S0.copy(), "G1|Wn": W0, "blocks": blocks}
        for nm in e12.ALL:
            fac = 0.95 if (nm == "P-nn" and f >= 0.4) else 1.0
            arr[f"{nm}|S"] = S0 * fac; arr[f"{nm}|Wn"] = W0; arr[f"{nm}|Su"] = S0 * fac; arr[f"{nm}|Wu"] = W0
        np.savez_compressed(d / "sums.npz", **arr)
        rec = {"city": city, "f": f, "seed": s, "sums_sha256": p4b.sha256(d / "sums.npz", 16),
               "prior": [0.45, 0.4, 0.15], "share_test_hidden_without_observed_within_500m": 0.3,
               "concordance": {b: {"pairs": 1000, "agree": 400, "segments": 10} for b in e12.BIN_LABELS},
               "predictors": {nm: {"red_recall": 0.05, "false_alarm_rate": 0.05, "fallbacks": 0} for nm in e12.ALL}}
        (d / "run.json").write_text(json.dumps(rec))
    e12.RUNS, e12.OUT = runs, tmp / "congelamenti"
    e12.freeze(argparse.Namespace(compare_with=None))
    res = json.loads((tmp / "congelamenti" / "e12_risultati.json").read_text())
    st = res["summary_statement"]
    print(f"synthetic statement: {st}")
    v = res["rows"]["madrid 0.4"]["P-nn"]
    print(f"V(P-nn) madrid 40% = {v['V']:.4f} [{v['L']:.4f}; {v['U']:.4f}] (expected 5); "
          f"V(P-idw4) = {res['rows']['madrid 0.4']['P-idw4']['V']:.4f} (expected 0)")
    ok = (st == "a spatial signal is present, recoverable by P-nn at f = 40%, 60%" and abs(v["V"] - 5) < 1e-9
          and abs(res["rows"]["madrid 0.4"]["P-idw4"]["V"]) < 1e-9 and (tmp / "congelamenti" / "CONGELAMENTO_E12.md").exists())
    shutil.rmtree(tmp)
    print("SELFTEST-E2E:", "PASS" if ok else "FAIL", "(temporary folder removed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="E12 checks")
    ap.add_argument("--check-inputs", action="store_true")
    ap.add_argument("--selftest-e2e", metavar="TMPDIR")
    a = ap.parse_args()
    if a.check_inputs:
        return check_inputs()
    if a.selftest_e2e:
        return selftest_e2e(a.selftest_e2e)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
