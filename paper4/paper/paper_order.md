# Paper 4 — order of the paper

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (14:30).

| Order | Section | File | Frozen record (commit, fingerprint) | Status |
|---|---|---|---|---|
| 0 | Title, abstract, keywords | `section_abstract.md` | all frozen records | draft (working title) |
| 1 | Introduction, research questions, contributions | `section_introduction.md` | — | draft |
| 2 | Part A — what to measure | `section_partA.md` | P4A: a0b76dc, 7304d9639f91ec81 (dated note appended, 130e2e4) | draft |
| 3a | Part B — lead (order of reading) | `section_partB.md` | — | draft |
| 3 | Part B — the inductive regime; E11 (which neighbours) | `section_E11.md` | E11: 4e04ba7, 459b43ee3e649a31 | draft |
| 4 | E9 (how many) | `section_E9.md` | E9: 1d97a94, 0237d28dee3b7c4d | draft |
| 5 | E12 (is there a signal?) | `section_E12.md` | E12: 085bda7, 0be136a3886173bc | draft |
| 6 | E12-bis (the signal calibrated) | `section_E12bis.md` | E12-bis: 40adfc9, 11e89874e3b100b8 | draft |
| 7 | E12-ter (the signal net of the calendar) | `section_E12ter.md` | E12-ter: dda3b8f, ec03ebf339d7deb4 | draft |
| 8 | E10-geo (where) | `section_E10geo.md` | E10-geo: 85cd9e8, bafddd2709919092 | draft |
| 9 | Discussion | `section_discussion.md` | all of the above | draft |
| 10 | Limits | `section_limits.md` | all of the above | draft |
| 11 | Conclusion | `section_conclusion.md` | all of the above | draft |

Part B reads in the order of `part_B_order.md`. `paper4/manuscript/build.py` typesets the files in this order into one PDF, with the register of corrections as supplement. Every number of these files is checked by
`paper4/analysis/main.py` (step 3) against the frozen records each file declares as its sources.
