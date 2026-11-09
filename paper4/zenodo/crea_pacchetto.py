#!/usr/bin/env python3
"""
Paper 4 — the Zenodo package: three tar archives, MANIFEST_ZENODO.tsv and README_ZENODO.md.
=============================================================================================
Follows the partition of `protocol/paper4/zenodo/RIPARTIZIONE_RUNS.md` (rules of `analisi/ripartizione_runs.py`),
extended to the run folders added after it (E12-quater, E12-quinquies, E12-sexies, E12-sexies-bis, E10-pred):

  1. paper4_code_records.tar   the repository files of Paper 4 at the given commit, taken with `git archive` (not
                               from the working tree): paper4/ (code, analysis, frozen records, figures, reports,
                               CONFRONTO.md), protocol/paper4/, the modules of the earlier analysis that P4A imports or
                               fingerprints, the E11 graphs (geo_sweep/), and both poetry environments
  2. paper4_runs_part1.tar     paper4/runs/: every file of the groups "rigenerazione" and "pilota", and the per-cell
                               predictions of E11 and of E10-pred
  3. paper4_runs_part2.tar     paper4/runs/: the per-cell predictions of E9

A file of paper4/runs/ that no rule takes stops the script (as "altro" in the partition). MANIFEST_ZENODO.tsv lists
every file of every archive: archive, path, bytes, sha256, commit, tag. README_ZENODO.md gives DOI, title, authors,
licence, contents and the regeneration. Nothing is uploaded.

    python3 paper4/zenodo/crea_pacchetto.py --dry-run [--commit C]           manifest and README only, sizes estimated
    python3 paper4/zenodo/crea_pacchetto.py --commit C --tag T --license L   the three archives, manifest and README

Output folder: --out (default ../paper4-zenodo, outside the repository). An existing archive stops the script.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS_REL = "paper4/runs"
DOI = "10.5281/zenodo.24059573"
TITLE = "What a Traffic Sensor Buys: Measurement at Its Segment, Little from Its Neighbours"
AUTHORS = ["Gabriele De Vito", "Gemma Catolino", "Dario Di Nucci", "Fabio Palomba", "Carmine Gravino",
           "Andrea De Lucia", "Filomena Ferrucci"]
AFFILIATION = "Department of Computer Science, University of Salerno, Fisciano (SA), Italy"
REPO_URL = "https://github.com/gadevito/motion-p1"
LIMIT = 50 * 10 ** 9                                   # Zenodo: 50 GB per record

CODE_PATHS = ["paper4", "protocol/paper4", "analisi/validazione_colocalizzata.py", "analisi/p4_fase1_crossval.py",
              "analisi/p4a_fasce_appaiate.py", "analisi/p4a_cause.py", "analisi/ripartizione_runs.py", "geo_sweep",
              "models/pyproject.toml", "models/poetry.lock", "pyproject.toml", "poetry.lock"]
ARCHIVES = {"code": "paper4_code_records.tar", "part1": "paper4_runs_part1.tar", "part2": "paper4_runs_part2.tar"}

# Rules of analisi/ripartizione_runs.py, extended to the run folders added after the partition (2026-11-09).
PILOTA = re.compile(r"^([^/]*_(pilota|preflight|diagnosi|potenza|lancio).*|[^/]+/campagna_shard[^/]*\.log|p4a_run\.log)$")
RIGEN = re.compile(r"^((e9|e11|e10pred)/[^/]+/run\.json|(e12|e12bis|e12ter|e12quater|e12quinquies|e12sexies|e12sexiesbis)/[^/]+/[^/]+|"
                   r"e10pred/[^/]+/thresholds\.(json|fingerprint)|e10geo/results\.json|p4a/.*|MANIFEST\.tsv|"
                   r"[^/]*_costo[^/]*\.json|[^/]*_costi[^/]*|[^/]*_insiemi_geometria\.json)$")
PRED = re.compile(r"^(e9|e11|e10pred)/[^/]+/[^/]+\.npz$")
PART = {"rigenerazione": "part1", "pilota": "part1", "predizioni_e11": "part1", "predizioni_e10pred": "part1",
        "predizioni_e9": "part2"}


def group(rel):
    if PILOTA.match(rel):
        return "pilota"
    m = PRED.match(rel)
    if m:
        return f"predizioni_{m.group(1)}"
    if RIGEN.match(rel):
        return "rigenerazione"
    return "altro"


def git(*args, binary=False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode().strip()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tar_bytes(sizes):
    """Size of an uncompressed ustar/pax archive: a 512-byte header per file (plus one pax block for long names, an
    upper bound), the content padded to 512 bytes, and the two closing blocks, rounded to the 10,240-byte record."""
    n = sum(512 + 512 + -(-s // 512) * 512 for s in sizes) + 1024
    return -(-n // 10240) * 10240


# ---------------------------------------------------------------- inventory ----------------------------

def code_files(commit):
    """(path, bytes, sha256) of every file of CODE_PATHS in the commit, from the git objects."""
    out = []
    lines = git("ls-tree", "-r", "-l", commit, "--", *CODE_PATHS).splitlines()
    missing = [p for p in CODE_PATHS if not any(ln.split("\t", 1)[1] == p or ln.split("\t", 1)[1].startswith(p + "/")
                                                for ln in lines)]
    if missing:
        raise SystemExit(f"STOP: not in {commit}: {missing}")
    for ln in lines:
        meta, path = ln.split("\t", 1)
        mode, kind, obj, size = meta.split()
        if kind != "blob":
            continue
        data = git("cat-file", "blob", obj, binary=True)
        out.append((path, int(size), hashlib.sha256(data).hexdigest()))
    return out


def run_files(runs):
    """(path, bytes, sha256, part) of every file under paper4/runs/ (symbolic links followed)."""
    out, other = [], []
    files = [Path(d) / x for d, _, fs in os.walk(runs, followlinks=True) for x in fs]   # run folders are symbolic links
    for f in sorted(files):
        if not f.is_file():
            continue
        rel = f.relative_to(runs).as_posix(); g = group(rel)
        if g == "altro":
            other.append(rel); continue
        out.append((f"{RUNS_REL}/{rel}", f.stat().st_size, sha_file(f), PART[g], g))
    if other:
        raise SystemExit("STOP: files of paper4/runs/ that no rule takes:\n  " + "\n  ".join(other))
    return out


# ---------------------------------------------------------------- archives -----------------------------

def write_code_tar(commit, dest):
    data = git("archive", "--format=tar", commit, "--", *CODE_PATHS, binary=True)
    dest.write_bytes(data)


def write_runs_tar(rows, dest, mtime):
    def norm(ti):
        ti.uid = ti.gid = 0; ti.uname = ti.gname = ""; ti.mtime = mtime; ti.mode = 0o644
        return ti
    with tarfile.open(dest, "w", format=tarfile.PAX_FORMAT, dereference=True) as tf:
        for path, size, sha, *_ in rows:
            src = ROOT / path
            ti = norm(tf.gettarinfo(str(src), arcname=path))
            if ti.size != size:
                raise SystemExit(f"STOP: {path} changed size while archiving")
            with open(src, "rb") as f:
                tf.addfile(ti, f)


# ---------------------------------------------------------------- README -------------------------------

def readme(commit, tag, license_, sizes, built):
    rows = "\n".join(f"| `{ARCHIVES[k]}` | {desc} | {n:,} | {b / 1e9:.2f} GB{'' if built else ' (estimated)'} |"
                     for k, desc, n, b in sizes)
    return f"""# {TITLE} — data and code archive

**DOI:** https://doi.org/{DOI}
**Authors:** {", ".join(AUTHORS)} ({AFFILIATION}).
**Licence:** {license_}
**Repository:** {REPO_URL}, commit `{commit}`{f", tag `{tag}`" if tag else ""}.

This record holds what is needed to verify and regenerate every number of the paper: the code, pre-registrations,
protocols and frozen records of Paper 4 at the commit above, and the run folders from which the frozen records are
generated. `MANIFEST_ZENODO.tsv` lists every file of every archive with its size and SHA-256.

## Archives

| Archive | Content | Files | Size |
|---|---|---:|---:|
{rows}

- `paper4_code_records.tar`: `paper4/` (code, analysis, frozen records, figures, regeneration reports and
  `CONFRONTO.md`), `protocol/paper4/` (pre-registrations, protocol, register of corrections), the modules of the
  earlier analysis that Part A imports or fingerprints (`analisi/`), the E11 graphs (`geo_sweep/`), and the two
  poetry environments (`models/poetry.lock` for Part B, the root `poetry.lock` for Part A).
- `paper4_runs_part1.tar`: `paper4/runs/`, the regeneration inputs of every frozen record, the pilot and preflight
  files, and the per-cell predictions of E11 and E10-pred.
- `paper4_runs_part2.tar`: `paper4/runs/e9/`, the per-cell predictions of E9.

Model states are not saved: the frozen code keeps checkpoints in memory for validation-based selection and writes
only per-cell predictions. External data (the Traffic4cast benchmark, the Madrid loop and Austin radar data) are not
redistributed; the repository records the fingerprint of every input file.

## Regeneration

Extract the three archives in one folder (they share the layout of the repository), then create the two
environments with poetry (`models/poetry.lock` for Part B, the root `poetry.lock` for Part A). From that folder:

```
PY=<interpreter of models/poetry.lock>
PYA=<interpreter of the root poetry.lock>
$PY paper4/analysis/main.py --text-only --manoscritto <manuscript folder>   # fingerprints and text (archive 1 only)
P4A_PYTHON=$PYA $PY paper4/analysis/main.py                                   # complete regeneration
```

`paper4/analysis/main.py` checks the fingerprint of every frozen record and generator, runs each generator unchanged
on `paper4/runs/` into a work folder, and compares every number with the frozen record; the outcome of the last
complete run is in `paper4/analysis/CONFRONTO.md`. The generators of E9, E10-pred and E10-pred-bis also rebuild the
node sets from the Traffic4cast data (environment variable `P4_DATA`, default `../OR3/data_collection`); the other
generators read only `paper4/runs/`. The text check needs the manuscript's `paper/*.md`, which are not part of this
record; without them, `main.py --text-only` still checks every fingerprint.
"""


# ---------------------------------------------------------------- main ---------------------------------

def main():
    ap = argparse.ArgumentParser(description="Paper 4 Zenodo package")
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--tag", default="")
    ap.add_argument("--license", default="")
    ap.add_argument("--runs", type=Path, default=ROOT / RUNS_REL)
    ap.add_argument("--out", type=Path, default=ROOT.parent / "paper4-zenodo")
    ap.add_argument("--dry-run", action="store_true", help="manifest and README only; archive sizes estimated")
    a = ap.parse_args()
    commit = git("rev-parse", a.commit)
    if not a.dry_run and not (a.tag and a.license):
        raise SystemExit("STOP: --tag and --license are required to build the archives")
    if a.tag and git("rev-parse", f"{a.tag}^{{commit}}") != commit:
        raise SystemExit(f"STOP: tag {a.tag} does not point to {commit}")
    a.out.mkdir(parents=True, exist_ok=True)
    if not a.dry_run:
        for name in ARCHIVES.values():
            if (a.out / name).exists():
                raise SystemExit(f"STOP: {a.out / name} exists")

    code = code_files(commit)
    runs = run_files(a.runs)
    parts = {"code": [(p, b, s) for p, b, s in code],
             "part1": [r for r in runs if r[3] == "part1"], "part2": [r for r in runs if r[3] == "part2"]}
    desc = {"code": "code, protocols, frozen records", "part1": "run folders, E11 and E10-pred predictions",
            "part2": "E9 predictions"}

    built = {}
    if not a.dry_run:
        mtime = int(git("show", "-s", "--format=%ct", commit))
        write_code_tar(commit, a.out / ARCHIVES["code"])
        write_runs_tar(parts["part1"], a.out / ARCHIVES["part1"], mtime)
        write_runs_tar(parts["part2"], a.out / ARCHIVES["part2"], mtime)
        for k, name in ARCHIVES.items():
            built[k] = ((a.out / name).stat().st_size, sha_file(a.out / name))
        # the code archive must hold exactly the files of the manifest
        with tarfile.open(a.out / ARCHIVES["code"]) as tf:
            names = sorted(m.name for m in tf.getmembers() if m.isfile())
        if names != sorted(p for p, *_ in parts["code"]):
            raise SystemExit("STOP: the code archive and its manifest list different files")

    sizes = []
    for k in ARCHIVES:
        n = len(parts[k]); b = built[k][0] if k in built else tar_bytes([r[1] for r in parts[k]])
        sizes.append((k, desc[k], n, b))
    total = sum(s[3] for s in sizes)

    tag = a.tag or ("(dry run, no tag)" if a.dry_run else "")
    man = ["archive\tpath\tbytes\tsha256\tcommit\ttag"]
    for k in ARCHIVES:
        for r in parts[k]:
            man.append(f"{ARCHIVES[k]}\t{r[0]}\t{r[1]}\t{r[2]}\t{commit}\t{tag}")
    for k, (b, s) in built.items():
        man.append(f"{ARCHIVES[k]}\t(archive)\t{b}\t{s}\t{commit}\t{tag}")
    (a.out / "MANIFEST_ZENODO.tsv").write_text("\n".join(man) + "\n")
    (a.out / "README_ZENODO.md").write_text(readme(commit, a.tag, a.license or "(to be set at the tag)", sizes,
                                                   bool(built)))

    print(f"commit {commit}{' (dry run: no archive written)' if a.dry_run else ''}; output {a.out}")
    for k, d, n, b in sizes:
        print(f"  {ARCHIVES[k]:<26} {n:>6,} files  {b / 1e9:8.3f} GB{'' if built else ' (estimated)'}  — {d}")
    print(f"  total {total / 1e9:.3f} GB against the Zenodo limit of {LIMIT / 1e9:.0f} GB per record: "
          f"{'within' if total < LIMIT else 'ABOVE'}")
    by = {}
    for r in runs:
        by.setdefault(r[4], [0, 0]); by[r[4]][0] += r[1]; by[r[4]][1] += 1
    print("  paper4/runs/ by group: " + "; ".join(f"{g} {v[0] / 2 ** 30:.2f} GiB ({v[1]:,} files)" for g, v in sorted(by.items())))
    print(f"  manifest {a.out / 'MANIFEST_ZENODO.tsv'} ({len(man) - 1:,} rows), README {a.out / 'README_ZENODO.md'}; "
          f"generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return 0 if total < LIMIT else 1


if __name__ == "__main__":
    sys.exit(main())
