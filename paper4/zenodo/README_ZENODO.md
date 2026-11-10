# What a Traffic Sensor Buys: Measurement at Its Segment, Little from Its Neighbours — data and code archive

**DOI:** https://doi.org/10.5281/zenodo.24059573
**Authors:** Gabriele De Vito, Gemma Catolino, Dario Di Nucci, Fabio Palomba, Carmine Gravino, Andrea De Lucia, Filomena Ferrucci (Department of Computer Science, University of Salerno, Fisciano (SA), Italy).
**Licence:** CC-BY-4.0
**Repository:** https://github.com/gadevito/motion-p1, commit `251527052d4ce48bf0ee70a3bfc3c94d7d0ed4c2`, tag `paper4-freeze-20261110a`.

This record holds what is needed to verify and regenerate every number of the paper: the code, pre-registrations,
protocols and frozen records of Paper 4 at the commit above, and the run folders from which the frozen records are
generated. `MANIFEST_ZENODO.tsv` lists every file of every archive with its size and SHA-256.

## Archives

| Archive | Content | Files | Size |
|---|---|---:|---:|
| `paper4_code_records.tar` | code, protocols, frozen records | 160 | 0.00 GB |
| `paper4_runs_part1.tar` | run folders, E11 and E10-pred predictions | 2,706 | 6.82 GB |
| `paper4_runs_part2.tar` | E9 predictions | 540 | 20.97 GB |

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
