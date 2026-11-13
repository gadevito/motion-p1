#!/usr/bin/env python3
"""Phase 6 of P0 — sample and packages for the external verifier EXT-01 (P0 §8 phase 6).

  make      draws a random sample of at least 30% of the counted problems (seed declared on
            the command line and written in the output), and writes:
              EXT01_sample_anonymised.json   id, summary, candidates' verbatim text and
                                             artefact-free locators; NO stage, detector,
                                             roles, phase, dates, commits or coder values
              EXT01_sample_provenance.json   the same ids with the commits, dates and record
                                             references of their candidates; NO coder values
              EXT01_form_type_status.json    form for (a): primary_type, status, notes
              EXT01_form_phase.json          form for (b): phase_of_introduction, notes
            plus EXT01_SAMPLE.md with the seed, the ids and the fingerprints.
  validate  checks a filled EXT-01 form (allowed values, completeness, copied fields).
  compare   κ between EXT-01 and the resolved coding on the sample, per form.

Anonymisation rule: hashes, dates, author lines, person names and role words (executor,
reviewer, drafting, responsible author, coordination, external …) are replaced by <hash>,
<date>, <name>, <role> in the texts and summaries of the anonymised package. From candidates.json only the `text` of register rows, deviations and
record notes is passed; commit messages are passed with hashes, dates and author lines
removed; tag-diff and report-flag candidates are listed by class and count only. Summaries
are passed as in CORPUS.json (they describe what happened, not who found it).

Usage (from the OR3 working copy):
  python3 protocol/processo/analisi/external_sample.py make --corpus protocol/processo/corpus/CORPUS.json \
      --candidates protocol/processo/corpus/candidates.json --seed 20261113 --fraction 0.30 \
      --out protocol/processo/corpus/ext01
  python3 protocol/processo/analisi/external_sample.py validate --form EXT01_form_type_status.json
  python3 protocol/processo/analisi/external_sample.py compare --resolved protocol/processo/corpus/CODING_RESOLVED.json \
      --type-form EXT01_form_type_status.json --phase-form EXT01_form_phase.json
"""
import argparse, collections, hashlib, json, random, re, sys
from pathlib import Path

TYPES = ["1 leakage", "2 indexing and alignment", "3 silent loss", "4a metric declared != implemented",
         "4b inadequate metric implemented faithfully", "4c scoring not comparable across configurations",
         "5 budget, selection and convergence", "6 unsupported statement in the text",
         "7 provenance and traceability", "7d documentary", "8a defective control: false positive",
         "8b defective control: false negative or blind", "9 procedural violation",
         "10 environment and dependencies", "11 other"]
STATUS = ["defect", "deviation", "violation"]
PHASES = ["deliverable", "regeneration", "manuscript preparation", "preliminary reconstruction", "unknown"]
EVID = ["documented", "attributed recollection", "hypothesis", "conflict"]
HASH = re.compile(r"\b[0-9a-f]{7,40}\b")
ROLE = re.compile(r"\b(esecutor[ei]|executor(s)?|revisor[ei]|reviewer(s)?|revisione interna|internal review|stesura|drafting role|drafting|responsabile|responsible author|coordinamento|coordination role|coordination|referee|author'?s?|autor[ei]|partner|external|esterno)\b", re.I)
NAMES = re.compile(r"\b(De Vito|Devito|Palomba|Gravino|De Lucia|Ferrucci|Catolino|Di Nucci|Gabriele|Fabio|Carmine|Andrea|Filomena|Gemma|Dario|Varriale)\b")
DATE = re.compile(r"\b20\d\d-\d\d-\d\d(?:[T ]\d\d:\d\d(?::\d\d)?(?:[+-]\d\d:?\d\d|Z)?)?\b")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def scrub(text):
    out = []
    for l in text.splitlines():
        if re.match(r"^\s*(Author|Date|Signed-off-by|Co-authored-by|commit)\b", l, re.I):
            continue
        l = HASH.sub("<hash>", l)
        l = DATE.sub("<date>", l)
        l = NAMES.sub("<name>", l)
        l = ROLE.sub("<role>", l)
        out.append(l)
    return "\n".join(out).strip()


def make(a):
    corpus = json.loads(Path(a.corpus).read_text(encoding="utf-8"))
    cands = {c["id"]: c for c in json.loads(Path(a.candidates).read_text(encoding="utf-8"))["candidates"]}
    probs = [p for p in corpus if p["status"] in STATUS]
    n = max(1, -(-len(probs) * a.fraction // 1))
    n = int(n)
    rng = random.Random(a.seed)
    ids = sorted(rng.sample([p["id"] for p in probs], n), key=lambda s: (s[:2], int(s[3:])))
    byid = {p["id"]: p for p in probs}
    anon, prov, f_type, f_phase = [], [], [], []
    for i in ids:
        p = byid[i]
        texts, counts, provenance = [], collections.Counter(), []
        for cid in p["candidates"]:
            c = cands.get(cid)
            if not c:
                continue
            cls = c["class"]
            if cls in ("register row", "deviation", "record note"):
                texts.append({"class": cls, "text": scrub(c["text"])})
                provenance.append({"candidate": cid, "class": cls, "path": c["path"], "locator": c["locator"],
                                   "commit": c["commit"], "text": c["text"]})
            elif cls == "git commit":
                texts.append({"class": cls, "text": scrub(c["text"])})
                provenance.append({"candidate": cid, "class": cls, "locator": c["locator"], "text": c["text"],
                                   "register_ref": c.get("register_ref")})
            else:
                counts[cls] += 1
                provenance.append({"candidate": cid, "class": cls, "path": c.get("path", ""), "locator": c["locator"]})
        anon.append({"id": i, "summary": scrub(p["summary"]), "texts": texts, "other_candidates": dict(counts)})
        prov.append({"id": i, "summary": p["summary"], "provenance": provenance})
        f_type.append({"id": i, "primary_type": "", "status": "", "evidence_status": "", "notes": ""})
        f_phase.append({"id": i, "phase_of_introduction": "", "evidence_status": "", "notes": ""})
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    meta = {"seed": a.seed, "fraction": a.fraction, "n": n, "of": len(probs), "ids": ids,
            "corpus_sha256": sha(Path(a.corpus).read_bytes()), "candidates_sha256": sha(Path(a.candidates).read_bytes())}
    files = {"EXT01_sample_anonymised.json": {"meta": {k: meta[k] for k in ("seed", "n", "of")}, "problems": anon},
             "EXT01_sample_provenance.json": {"meta": {k: meta[k] for k in ("seed", "n", "of")}, "problems": prov},
             "EXT01_form_type_status.json": {"verifier": "EXT-01", "part": "a: type and status on the anonymised sample",
                                             "_allowed": {"primary_type": TYPES, "status": STATUS, "evidence_status": EVID},
                                             "date_started": "", "date_delivered": "", "problems": f_type},
             "EXT01_form_phase.json": {"verifier": "EXT-01", "part": "b: phase of introduction on the provenance package",
                                       "_allowed": {"phase_of_introduction": PHASES, "evidence_status": EVID},
                                       "date_started": "", "date_delivered": "", "problems": f_phase}}
    fps = {}
    for name, obj in files.items():
        b = json.dumps(obj, indent=1, ensure_ascii=False).encode()
        (out / name).write_bytes(b); fps[name] = sha(b)
    md = ["# EXT-01 sample (P0 §8, phase 6)", "",
          f"Seed {a.seed}; fraction {a.fraction}; {n} of {len(probs)} counted problems. "
          f"Drawn from `CORPUS.json` sha256 `{meta['corpus_sha256']}` with `candidates.json` sha256 `{meta['candidates_sha256']}`.", "",
          "| File | sha256 |", "| --- | --- |"] + [f"| `{k}` | `{v}` |" for k, v in fps.items()] + ["", "Sampled ids: " + ", ".join(ids), "",
          "Part (a) is coded on the anonymised sample only; part (b) on the provenance package, after (a) is delivered. "
          "EXT-01 receives no coder values and no AGREEMENT/MINUTES files until both parts are delivered."]
    (out / "EXT01_SAMPLE.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"sample {n}/{len(probs)} seed {a.seed}; " + "; ".join(f"{k} {v[:12]}" for k, v in fps.items()))


def validate(a):
    f = json.loads(Path(a.form).read_text(encoding="utf-8"))
    errs = []
    allowed = f["_allowed"]
    for e in f["problems"]:
        for k, vals in allowed.items():
            if e.get(k, "") not in vals:
                errs.append(f"{e['id']}: {k} = {e.get(k)!r} not allowed")
    for d in ("date_started", "date_delivered"):
        if not f.get(d):
            errs.append(f"{d} empty")
    if errs:
        print(f"NOT VALID: {len(errs)}"); [print("  " + x) for x in errs[:100]]; return 1
    print(f"VALID: {len(f['problems'])} problems, sha256 {sha(Path(a.form).read_bytes())}"); return 0


def kappa(pairs):
    n = len(pairs); po = sum(1 for x, y in pairs if x == y) / n
    ca, cb = collections.Counter(x for x, _ in pairs), collections.Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, pe, (po - pe) / (1 - pe) if pe < 1 else 1.0


def compare(a):
    R = {e["id"]: e for e in json.loads(Path(a.resolved).read_text(encoding="utf-8"))["problems"]}
    T = json.loads(Path(a.type_form).read_text(encoding="utf-8"))["problems"]
    P = json.loads(Path(a.phase_form).read_text(encoding="utf-8"))["problems"]
    for name, form, field in (("primary_type", T, "primary_type"), ("status", T, "status"), ("phase_of_introduction", P, "phase_of_introduction")):
        pairs = [(e[field], R[e["id"]][field]) for e in form]
        po, pe, k = kappa(pairs)
        print(f"{name}: raw {sum(1 for x, y in pairs if x == y)}/{len(pairs)}, chance {pe:.2f}, kappa {k:.2f}")
        for e in form:
            if e[field] != R[e["id"]][field]:
                print(f"  {e['id']}: EXT-01 {e[field]!r} vs resolved {R[e['id']][field]!r}")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make"); m.add_argument("--corpus", required=True); m.add_argument("--candidates", required=True)
    m.add_argument("--seed", type=int, required=True); m.add_argument("--fraction", type=float, default=0.30); m.add_argument("--out", required=True)
    v = sub.add_parser("validate"); v.add_argument("--form", required=True)
    c = sub.add_parser("compare"); c.add_argument("--resolved", required=True); c.add_argument("--type-form", required=True); c.add_argument("--phase-form", required=True)
    a = ap.parse_args()
    return {"make": make, "validate": validate, "compare": compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
