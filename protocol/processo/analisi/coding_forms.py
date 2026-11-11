#!/usr/bin/env python3
"""Phase 5 of P0 — coding forms and validator (P0 §5.1, §8 phase 5).

  make      builds one coding form per coder from the frozen CORPUS.json: the 108 counted
            problems (status defect, deviation, violation), each with its id, paper, status,
            summary and candidates copied from the corpus, and every P0 §5.1 field empty;
            the allowed values are written in the form itself (`_allowed`).
  validate  checks a filled form: every counted problem present and none added; every field
            filled with an allowed value (or "unknown" where admitted); free-text fields
            non-empty; evidence status given for every coded field; copied fields unchanged.

Usage (from the OR3 working copy):
  python3 protocol/processo/analisi/coding_forms.py make --corpus protocol/processo/corpus/CORPUS.json \
      --out protocol/processo/corpus --coders COD-01 COD-02
  python3 protocol/processo/analisi/coding_forms.py validate --corpus protocol/processo/corpus/CORPUS.json \
      --form CODING_COD-01.json
"""
import argparse, hashlib, json, sys
from pathlib import Path

ALLOWED = {
    "phase_of_introduction": ["deliverable", "regeneration", "manuscript preparation",
                              "preliminary reconstruction", "unknown"],
    "artefact": ["code", "protocol", "record", "manuscript", "register or note", "environment/repository"],
    "primary_type": ["1 leakage", "2 indexing and alignment", "3 silent loss", "4a metric declared != implemented",
                     "4b inadequate metric implemented faithfully", "4c scoring not comparable across configurations",
                     "5 budget, selection and convergence", "6 unsupported statement in the text",
                     "7 provenance and traceability", "7d documentary", "8a defective control: false positive",
                     "8b defective control: false negative or blind", "9 procedural violation",
                     "10 environment and dependencies", "11 other"],
    "secondary_type": ["none"] + [],  # filled below with the primary list
    "stage_of_detection": ["pre-registration", "preflight", "execution", "freeze", "regeneration",
                           "internal review", "text check", "submission", "preliminary reconstruction", "unknown"],
    "first_observed_detector": ["drafting", "execution", "internal review", "protocol review", "responsible author",
                                "mechanical control", "regeneration on another machine", "external", "unknown"],
    "detection_capability_of_other_controls": ["corroborated", "hypothesised", "not applicable"],
    "observed_effect": ["numbers changed", "none", "not measured"],
    "assistant_at_introduction": ["yes", "no", "unknown"],
    "assistant_at_detection": ["yes", "no", "unknown"],
}
ALLOWED["secondary_type"] = ["none"] + ALLOWED["primary_type"]
EVIDENCE = ["documented", "attributed recollection", "hypothesis", "conflict"]
CODED = ["phase_of_introduction", "artefact", "primary_type", "secondary_type", "stage_of_detection",
         "first_observed_detector", "detection_capability_of_other_controls", "observed_effect",
         "assistant_at_introduction", "assistant_at_detection"]
FREE = {"mechanical_control_which": "name and version of the control when first_observed_detector is "
                                    "'mechanical control', else 'not applicable'",
        "controls_available_at_the_time": "list: control, version or date, run / not run / added later; "
                                          "'none known' if none",
        "observed_effect_detail": "which numbers, by how much; 'none' or 'not measured'",
        "potential_impact": "what would have reached the paper; never 'consequence averted'",
        "measured_resources": "machine hours, repeated runs, tags, days, from logs and timestamps; 'none recorded' if none",
        "other_reason": "reason when primary_type is '11 other', else 'not applicable'",
        "notes": "boundary cases, precedence rule applied (i–vii), sources read; may be empty"}
COPIED = ["id", "paper", "status", "summary", "candidates"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def counted(corpus):
    return [p for p in corpus if p["status"] in ("defect", "deviation", "violation")]


def make(a):
    corpus = json.loads(Path(a.corpus).read_text(encoding="utf-8"))
    probs = counted(corpus)
    for coder in a.coders:
        form = {"coder": coder, "corpus_sha256": sha(a.corpus), "p0_commit": "2ab032b",
                "date_started": "", "date_delivered": "",
                "_allowed": ALLOWED, "_evidence_status_values": EVIDENCE, "_free_text_fields": FREE,
                "problems": []}
        for p in probs:
            e = {k: p[k] for k in COPIED}
            for f in CODED:
                e[f] = ""
            for f in FREE:
                e[f] = ""
            e["evidence_status"] = {f: "" for f in CODED}
            form["problems"].append(e)
        out = Path(a.out) / f"CODING_{coder}.json"
        out.write_text(json.dumps(form, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{out}: {len(probs)} problems, sha256 {sha(out)}")


def validate(a):
    corpus = json.loads(Path(a.corpus).read_text(encoding="utf-8"))
    probs = {p["id"]: p for p in counted(corpus)}
    form = json.loads(Path(a.form).read_text(encoding="utf-8"))
    errors = []
    if form.get("corpus_sha256") != sha(a.corpus):
        errors.append("corpus_sha256 does not match the frozen CORPUS.json")
    ids = [e["id"] for e in form["problems"]]
    if set(ids) != set(probs):
        errors.append(f"problem set differs: missing {sorted(set(probs) - set(ids))}, extra {sorted(set(ids) - set(probs))}")
    if len(ids) != len(set(ids)):
        errors.append("duplicate problem ids in the form")
    for e in form["problems"]:
        pid = e["id"]
        p = probs.get(pid)
        if p and any(e.get(k) != p[k] for k in COPIED):
            errors.append(f"{pid}: copied fields changed")
        for f in CODED:
            v = e.get(f, "")
            if v not in ALLOWED[f]:
                errors.append(f"{pid}: {f} = {v!r} not allowed")
            es = e.get("evidence_status", {}).get(f, "")
            if es not in EVIDENCE:
                errors.append(f"{pid}: evidence_status[{f}] = {es!r} not allowed")
        for f in FREE:
            if f != "notes" and not str(e.get(f, "")).strip():
                errors.append(f"{pid}: {f} empty")
        if e.get("first_observed_detector") == "mechanical control" and e.get("mechanical_control_which", "").strip().lower() in ("", "not applicable"):
            errors.append(f"{pid}: mechanical control not named")
        if e.get("primary_type") == "11 other" and e.get("other_reason", "").strip().lower() in ("", "not applicable"):
            errors.append(f"{pid}: '11 other' without reason")
        if e.get("primary_type") and e.get("secondary_type") == e.get("primary_type"):
            errors.append(f"{pid}: secondary_type equals primary_type")
    for d in ("date_started", "date_delivered"):
        if not form.get(d):
            errors.append(f"{d} empty")
    if errors:
        print(f"NOT VALID: {len(errors)} error(s)")
        for x in errors[:200]:
            print("  " + x)
        return 1
    print(f"VALID: {len(ids)} problems, form sha256 {sha(a.form)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("--corpus", required=True); m.add_argument("--out", required=True)
    m.add_argument("--coders", nargs="+", default=["COD-01", "COD-02"])
    v = sub.add_parser("validate"); v.add_argument("--corpus", required=True); v.add_argument("--form", required=True)
    a = ap.parse_args()
    return make(a) if a.cmd == "make" else validate(a)


if __name__ == "__main__":
    sys.exit(main())
