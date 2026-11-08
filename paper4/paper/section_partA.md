# Paper 4 — Part A (what to measure): status and outline

Draft of 2026-11-08. **Part A has not been run.** This file holds the outline of the section and what exists so
far. No number of Part A enters the paper before its pre-registration (`protocol/paper4/P4A.md`) is signed and
its frozen record (`CONGELAMENTO_4A.md`) is generated.

---

## Part A — what does a loop detector measure of congestion?

**Question (RQ1).** Against an independent speed reference, what does a loop detector measure of congestion:
its level, its occurrence, or both? How much of the disagreement on urban arterials is spatial matching, and
what does lane aggregation hide?

**Perimeter** (protocol §2.2, frozen):

- Madrid arterials, 2021: loop–probe pairs, June–December 2021;
- the M30 ring, 2024: sensors measuring flow, occupancy and speed on the same device;
- Austin: signalised sections, per lane.

**What exists.**

- Tables 64–65 of the deliverable (co-located validation of loops against probe speeds) were regenerated in
  Phase 1 and reproduce exactly (register of corrections, item 5; `protocol/paper4/fase1/CROSSVAL_rigenerato.md`).
  They enter the paper through `CONGELAMENTO_4A.md`, not from the Phase 1 record.
- Table 66 is out of the perimeter (no generator).

**What remains, in order.**

1. Draft `protocol/paper4/P4A.md`: the regeneration of Tables 67–69 with fingerprints, and the three
   corrections of protocol §2.2:
   - M30 threshold chosen on one half of the sensors and reported on the other, over 5 random splits;
   - block bootstrap over sensors for every figure of Tables 67–69, and an interval on the Gini split;
   - lanes–AUC relation as a rank correlation over sections, with a bootstrap over sections.
2. Signature, run, `CONGELAMENTO_4A.md`.
3. This section, the answer to RQ1 in the introduction, contribution 4, and the Part A paragraphs of the
   discussion, limits and conclusion.

**Outline of the section** (to be written on the frozen record):

- level against occurrence: agreement of classes against detection of congested episodes (Tables 64–65, 67);
- the share of disagreement due to spatial matching (Gini decomposition, Table 68);
- what lane aggregation hides (Austin, Table 69).
