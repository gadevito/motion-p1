#!/usr/bin/env python3
"""
P4A — input check after the run, outside the frozen `p4a.py` (ff3204dee7064a27). Reads no metric.
=================================================================================================
Imports `p4a.py` unchanged. After `run`, before `freeze`, it checks:

  - the frozen code: p4a.py and p4b.py have the fingerprints of the signature (commit f99b765);
  - results.json: present, written by that code, with the inputs of P4A.md and a clean commit;
  - the screen outputs of the deliverable scripts: present, with the fingerprints recorded in results.json;
  - the three CSVs of t4c_crossval.py: identical to Phase 1;
  - the threshold file of correction 1: present, its fingerprint equal to the recorded one and to results.json;
  - the keys of results.json expected by `freeze`.

Usage: $PYA paper4/code/verifica_p4a.py check-inputs
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import p4b  # noqa: E402
import p4a  # noqa: E402

FROZEN = {"p4a.py": "ff3204dee7064a27", "p4b.py": "926061038a7472a3"}
KEYS = {"crossval", "m30_counts", "table67", "table68", "arterials", "gini_split", "correction1", "austin", "correction3",
        "screen_outputs", "inputs", "code", "commit", "code_dirty", "thresholds_sha256"}


def check_inputs(args):
    bad = []
    code = {"p4a.py": p4b.sha256(Path(p4a.__file__), 16), "p4b.py": p4b.sha256(Path(p4b.__file__), 16)}
    if code != FROZEN:
        bad.append(f"code differs from the signed version: {code}")
    rp = p4a.RUNS / "results.json"
    if not rp.exists():
        print("results.json missing"); print("CHECK-INPUTS: FAIL"); return 1
    r = json.loads(rp.read_text())
    if not KEYS <= set(r):
        bad.append(f"keys missing: {sorted(KEYS - set(r))}")
    if r.get("code") != FROZEN:
        bad.append(f"code recorded in results.json: {r.get('code')}")
    if r.get("code_dirty"):
        bad.append("results.json written with uncommitted code")
    exp = {str(p.relative_to(p4b.ROOT.parent)): fp for p, fp in p4a.INPUTS.items()}
    exp[str(p4a.SPEED_DIR.relative_to(p4b.ROOT.parent))] = p4a.SPEED_DIR_FP
    if r.get("inputs") != exp:
        bad.append("inputs recorded in results.json differ from P4A.md")
    bad += [f"input or script: {b}" for b in p4a.check_fingerprints()]
    for name, fp in r.get("screen_outputs", {}).items():
        if not (p4a.RUNS / name).exists() or p4b.sha256(p4a.RUNS / name, 16) != fp:
            bad.append(f"screen output {name}")
    want = {"crossval_base.txt", "crossval_noempty.txt", "crossval_d30.txt", "script_anello.txt", "script_accoppiamento.txt",
            "script_austin.txt"}
    if set(r.get("screen_outputs", {})) != want:
        bad.append(f"screen outputs: {sorted(r.get('screen_outputs', {}))}")
    for v, fp in p4a.PHASE1_CSV.items():
        f = p4a.RUNS / f"crossval_{v}.csv"
        if not f.exists() or p4b.sha256(f, 16) != fp:
            bad.append(f"crossval {v} CSV differs from Phase 1")
    d = p4a.RUNS / "thresholds"
    try:
        p4a.require_thresholds(d)
        if p4b.sha256(d / "thresholds.json", 16) != r.get("thresholds_sha256"):
            bad.append("threshold file differs from the one recorded in results.json")
    except SystemExit as e:
        bad.append(str(e))
    print(f"results.json {p4b.sha256(rp, 16)}; inconsistencies: {len(bad)}")
    for b in bad:
        print("  -", b)
    print("CHECK-INPUTS:", "PASS" if not bad else "FAIL")
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser(description="P4A input check")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("check-inputs")
    return {"check-inputs": check_inputs}[ap.parse_args().cmd](None)


if __name__ == "__main__":
    sys.exit(main())
