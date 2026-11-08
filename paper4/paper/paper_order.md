# Paper 4 — order of the paper

Draft of 2026-11-08, revised after the internal review of the full draft (Part B before Part A; E12, E12-bis and
E12-ter in one section; limits collected in §VI; register of corrections and provenance in the supplement).

| Order | Section | File | Frozen record (commit, fingerprint) | Status |
|---|---|---|---|---|
| 0 | Title, abstract, keywords | `section_abstract.md` | all frozen records | draft (working title) |
| I | Introduction, research questions, contributions | `section_introduction.md` | all | draft |
| II | Setting and protocol | `section_setting.md` | E11, E9; pilot of E11 | draft |
| III | Part B — lead | `section_partB.md` | — | draft |
| III-A | Which neighbours (E11) | `section_E11.md` | E11: 4e04ba7, 459b43ee3e649a31 | draft |
| III-B | How many (E9) | `section_E9.md` | E9: 1d97a94, 0237d28dee3b7c4d | draft |
| III-C | The spatial signal, decomposed | `section_signal.md` | E12: 085bda7, 0be136a3886173bc; E12-bis: 40adfc9, 11e89874e3b100b8; E12-ter: dda3b8f, ec03ebf339d7deb4 | draft |
| III-D | Where (E10-geo) | `section_E10geo.md` | E10-geo: 85cd9e8, bafddd2709919092 | draft |
| IV | Part A — what to measure | `section_partA.md` | P4A: a0b76dc, 7304d9639f91ec81 | draft |
| V | Discussion | `section_discussion.md` | all | draft |
| VI | Limits | `section_limits.md` | all | draft |
| VII | Conclusion | `section_conclusion.md` | all | draft |
| — | Data and Code Availability | `section_availability.md` | — | draft (Zenodo record to be created) |
| S1 | Register of corrections (items 1–3, 8–13) | `protocol/paper4/REGISTRO_CORREZIONI.md` | — | generated |
| S2 | Frozen records and provenance | `supplement_records.md` | all | draft |

Every number of these files is checked by `paper4/analysis/main.py` (step 3) against the frozen records each file
declares as its sources. `paper4/manuscript/build.py` typesets them in this order into `main.tex` with one file
per section in `paper4/manuscript/sections/`, compiles `main.pdf`, and writes the Overleaf package
`paper4_overleaf.zip` (compiler: XeLaTeX).
