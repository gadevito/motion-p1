#!/usr/bin/env python3
"""P2 — export of the authentic frozen code for the partner reviewers (P0 §10).

Builds, for each paper, a zip of the repository at its freeze tag with `git archive`,
then removes everything P0 §10 says the reviewers must not receive, and writes a
manifest (path, size, sha256) and the list of exclusion rules applied.

Included: code and configuration (analysis scripts, experiment code, environments), the
pre-registered protocols (`protocol/E*.md`, `protocol/paper4/E*.md`, `P4A.md`,
`PROTOCOLLO.md`), LICENSE.
Excluded: git history (git archive has none); registers of corrections; frozen records
(`CONGELAMENTO_*`, `paper4/congelamenti/`); regeneration reports and comparisons;
Spark and Zenodo folders; the process folder; every Markdown note under `evoluzione/`
(working notes of Paper 1, rectifications, notes to the authors); results and data;
third-party code (`evoluzione/MoGERNN-main/`, present at the Paper 1 tag and removed
later); READMEs and summaries that describe corrections.

Usage (from the OR3 working copy):
  python3 protocol/processo/analisi/p2_export.py --tag paper1-freeze-20261103q --paper paper1 --out ../p2-export
  python3 protocol/processo/analisi/p2_export.py --tag paper4-freeze-20261110a --paper paper4 --out ../p2-export
"""
import argparse, fnmatch, hashlib, io, json, os, re, subprocess, sys, tarfile, zipfile
from pathlib import Path

EXCLUDE = [
    "protocol/REGISTRO_CORREZIONI.md", "protocol/register_of_corrections.en.md", "protocol/paper4/REGISTRO_CORREZIONI.md",
    "protocol/RISCRITTURA_STORIA.md", "protocol/SUMMARIES.en.md", "protocol/paper4/SUMMARIES.en.md",
    "protocol/spark/*", "protocol/zenodo/*", "protocol/processo/*", "protocol/paper4/zenodo/*",
    "protocol/paper4/fase1/*", "protocol/paper4/fase2/*", "protocol/e14b/*", "protocol/e18/*", "protocol/e15/*",
    "CONGELAMENTO_*", "genera_congelamento_*.py", "paper4/congelamenti/*", "paper4/zenodo/*",
    "analysis/rigenerazione/*", "paper4/analysis/regeneration/*", "paper4/analysis/rigenerazione/*", "analysis/CONFRONTO.md", "paper4/analysis/CONFRONTO.md", "paper4/analysis/reports/*",
    "evoluzione/*.md", "evoluzione/**/*.md", "evoluzione/MoGERNN-main/*", "evoluzione/audit/*",
    "results/*", "data_collection/*", "paper4/runs/*", "paper4/manuscript/*", "paper1/*",
    "README.md", "README.it.md", "GLOSSARY.en.md", "NOTE_PER_GLI_AUTORI.md", "inventario.py",
]
PAPER_SCOPE = {
    "paper1": ["analysis/", "evoluzione/", "protocol/", "pyproject.toml", "poetry.lock", "LICENSE"],
    "paper4": ["paper4/", "protocol/paper4/", "protocol/PROTOCOLLO.md", "geo_sweep/", "analisi/", "models/pyproject.toml",
               "models/poetry.lock", "pyproject.toml", "poetry.lock", "LICENSE"],
}


PROTOCOL_MD = re.compile(r"^protocol/(paper4/)?(E\d+[a-z]*\.md|P4A\.md|PROTOCOLLO\.md)$")


def excluded(path):
    # Markdown is admitted only if it is a pre-registered protocol: every other note, README,
    # record or report is dropped whatever its folder (2026-11-16: added after the first run
    # let through paper4/DOMANDE.md, MODIFICHE_AL_CODICE.md, RICOGNIZIONE.md, README.md and a
    # regeneration report under paper4/analysis/regeneration/).
    if path.endswith(".md") and not PROTOCOL_MD.match(path):
        return True
    if path == "paper4/ENV.txt":
        return False  # software environment of the Paper 4 runs: configuration, admitted
    if path.endswith(".txt") or path.endswith(".tsv") or path.endswith(".log"):
        return True
    return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.rstrip("*") + "**") for pat in EXCLUDE)


def in_scope(path, paper):
    return any(path == s or path.startswith(s) for s in PAPER_SCOPE[paper])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True); ap.add_argument("--paper", choices=["paper1", "paper4"], required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    commit = subprocess.run(["git", "rev-parse", f"{a.tag}^{{commit}}"], check=True, capture_output=True, text=True).stdout.strip()
    tar_bytes = subprocess.run(["git", "archive", "--format=tar", a.tag], check=True, capture_output=True).stdout
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    zname = out / f"P2_{a.paper}_{a.tag}.zip"
    manifest, dropped = [], []
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tf, zipfile.ZipFile(zname, "w", zipfile.ZIP_DEFLATED) as zf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            p = m.name
            if not in_scope(p, a.paper) or excluded(p):
                dropped.append(p); continue
            data = tf.extractfile(m).read()
            zi = zipfile.ZipInfo(p, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, data)
            manifest.append({"path": p, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    meta = {"paper": a.paper, "tag": a.tag, "commit": commit, "files": len(manifest), "excluded": len(dropped),
            "exclusion_rules": EXCLUDE, "scope": PAPER_SCOPE[a.paper]}
    (out / f"P2_{a.paper}_MANIFEST.json").write_text(json.dumps({"meta": meta, "files": manifest}, indent=1), encoding="utf-8")
    (out / f"P2_{a.paper}_EXCLUDED.txt").write_text("\n".join(sorted(dropped)) + "\n", encoding="utf-8")
    zsha = hashlib.sha256(zname.read_bytes()).hexdigest()
    print(f"{zname.name}: {len(manifest)} files, {len(dropped)} excluded, commit {commit[:12]}, sha256 {zsha}")
    md = [p for p in (x["path"] for x in manifest) if p.endswith(".md")]
    print("markdown kept (should be protocols only):"); [print("  " + p) for p in md]


if __name__ == "__main__":
    sys.exit(main())
