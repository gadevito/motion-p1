#!/usr/bin/env python3
"""Phase 5 of P0 — agreement between the two independent codings (P0 §8 phase 5).

Reads the two validated forms and writes:
  AGREEMENT.md        Cohen's kappa and raw agreement per coded field, the marginal
                      distributions of each coder, and the list of disagreements per problem
  disagreements.json  the same list, machine-readable, for the resolution minutes

Kappa is computed on the 108 counted problems, per field, with the standard formula
(observed agreement minus chance agreement from the two marginals). No weighting.

Usage:
  python3 protocol/processo/analisi/agreement.py --a CODING_COD-01.json --b CODING_COD-02.json --out protocol/processo/corpus
"""
import argparse, collections, hashlib, json
from pathlib import Path

CODED = ["phase_of_introduction", "artefact", "primary_type", "secondary_type", "stage_of_detection",
         "first_observed_detector", "detection_capability_of_other_controls", "observed_effect",
         "assistant_at_introduction", "assistant_at_detection"]


def kappa(pairs):
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return po, pe, k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); ap.add_argument("--out", required=True)
    x = ap.parse_args()
    A = json.loads(Path(x.a).read_text(encoding="utf-8")); B = json.loads(Path(x.b).read_text(encoding="utf-8"))
    sa = hashlib.sha256(Path(x.a).read_bytes()).hexdigest(); sb = hashlib.sha256(Path(x.b).read_bytes()).hexdigest()
    pa = {e["id"]: e for e in A["problems"]}; pb = {e["id"]: e for e in B["problems"]}
    assert set(pa) == set(pb)
    ids = [e["id"] for e in A["problems"]]
    lines = ["# Agreement between the two independent codings (P0 §8, phase 5)", "",
             f"Forms: `{A['coder']}` sha256 `{sa}`; `{B['coder']}` sha256 `{sb}`. {len(ids)} problems. "
             "Cohen's κ per field, unweighted; raw agreement = fraction of problems coded identically.", "",
             "## κ per field", "", "| Field | Raw agreement | Expected by chance | κ |", "| --- | --- | --- | --- |"]
    dis = []
    for f in CODED:
        pairs = [(pa[i][f], pb[i][f]) for i in ids]
        po, pe, k = kappa(pairs)
        agree = sum(1 for a, b in pairs if a == b)
        lines.append(f"| {f} | {agree}/{len(ids)} | {pe:.2f} | {k:.2f} |")
        for i in ids:
            if pa[i][f] != pb[i][f]:
                dis.append({"id": i, "field": f, A["coder"]: pa[i][f], B["coder"]: pb[i][f],
                            "evidence_" + A["coder"]: pa[i]["evidence_status"][f],
                            "evidence_" + B["coder"]: pb[i]["evidence_status"][f]})
    es_pairs = [(pa[i]["evidence_status"][f], pb[i]["evidence_status"][f]) for i in ids for f in CODED]
    po, pe, k = kappa(es_pairs)
    lines.append(f"| evidence_status (all coded fields) | {sum(1 for a, b in es_pairs if a == b)}/{len(es_pairs)} | {pe:.2f} | {k:.2f} |")
    lines += ["", "## Marginal distributions", ""]
    for f in CODED:
        ca = collections.Counter(pa[i][f] for i in ids); cb = collections.Counter(pb[i][f] for i in ids)
        lines.append(f"**{f}**"); lines.append("")
        lines.append(f"| Value | {A['coder']} | {B['coder']} |"); lines.append("| --- | --- | --- |")
        for v in sorted(set(ca) | set(cb)):
            lines.append(f"| {v} | {ca[v]} | {cb[v]} |")
        lines.append("")
    byid = collections.Counter(d["id"] for d in dis)
    lines += [f"## Disagreements: {len(dis)} field-level, on {len(byid)} of {len(ids)} problems", "",
              "| Problem | Field | " + A["coder"] + " | " + B["coder"] + " | evidence " + A["coder"] + " / " + B["coder"] + " |",
              "| --- | --- | --- | --- | --- |"]
    for d in dis:
        lines.append(f"| {d['id']} | {d['field']} | {d[A['coder']]} | {d[B['coder']]} | {d['evidence_' + A['coder']]} / {d['evidence_' + B['coder']]} |")
    lines += ["", "Problems with no disagreement on any field: " + str(len(ids) - len(byid)) + ".",
              "Resolution: discussion between the coders with minutes (`MINUTES_PHASE5.md`); the two delivered forms stay unchanged; the resolved coding is `CODING_RESOLVED.json`; unresolved disagreements stay `conflict`."]
    out = Path(x.out); out.mkdir(parents=True, exist_ok=True)
    (out / "AGREEMENT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "disagreements.json").write_text(json.dumps(dis, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"disagreements {len(dis)} on {len(byid)} problems")
    for l in lines[6:6 + len(CODED) + 3]:
        print(l)


if __name__ == "__main__":
    main()
