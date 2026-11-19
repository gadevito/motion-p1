# P4R — Revision 1 of the strengthening campaign (comparisons, statistical families, budget, order of blocks)

**Signature.** Date 2026-11-19 14:51 (Europe/Rome) · commit: the one recorded in the dated note of `P4R.md` that incorporates this revision by reference (path, commit, sha256) and in `P4R_RECEIPT.md` · signed: Gabriele De Vito (responsible author) · internal review: Filomena Ferrucci (draft 3 approved for ratification 14:48, with the editorial change applied in draft 4) · ratified by: Fabio Palomba (written, 14:50) · deposited with DEP-01 (receipt in `P4R_RECEIPT.md`).

Draft 4 of 2026-11-19 (draft 3 approved for ratification by the internal review on 2026-11-19 14:48 with one editorial change: S0 named in the dedicated–calendar contrast only; draft 2 revised: F2 keeps the original E14 contrasts — dynamic benefit without and with coordinates and their interaction —, no regression margin, nominal bootstrap control, FR in the order of blocks, replication conditioned on controls and frozen recipes, explicit replacement of E13B's Holm wording; draft 1 revised on the internal review: closed table of confirmatory hypotheses with α allocated to every family including the replications; one joint procedure per family; linkage to the gate by reference from P4R.md; budget wording), coordination role. The signed P4R (`ed66840`, 2026-11-18) is not modified; this revision is the document that the collegial decision of 2026-11-19 (P4R, dated note; video call 11:35, De Vito, Ferrucci, Palomba; confirmed 11:54) mandated, and it is referenced from P4R by a dated note. It is a requirement for starting B1 of E13B (`E13B.md`, Order 4(d); gate `p4r-revision`). It fixes, before any new result on real targets: which pre-registered comparisons are kept, withdrawn or suspended; the statistical families and their correction; the budget in fits and measured hours; the order of blocks. Nothing here is a result.

## 1. Comparisons: kept, withdrawn, suspended

| P4R block | Comparisons as signed | Status after this revision |
| --- | --- | --- |
| A1 (E13) — classification, G0/G1 × I0/I1, 60 cells | 6 contrasts: V_c(G1, I0), V_c(G1, I1), three cities | **Withdrawn, not executed.** E13 closed without A1 (positive control not passed twice; cause unresolved; `E13.md`, notes of 2026-11-18/19). Kept on record as planned and not executed. Development evidence A0.2, I1–I3 reported in the paper. |
| **B1 (E13B)** — classification, GF variant, D1/D0, I0, 30 cells | 3 contrasts: V_c(D1), three cities (`E13B.md`, signed 2026-11-19 13:57, B0.2 passed 14:25) | **Kept as the sole classification comparison on the three cities.** Not a comparison with G1: the variant is informed by the investigations and is not a repair of G1. |
| A3 (E14) — dedicated model, coordinates × dynamic readings 2×2 (regression, MAE) | 4 cells per city, contrasts as E14 will fix | **Kept with priority**, subject to E14's own controls (its positive control and its structural measurement on the dedicated model's propagation, which I3 did not cover). |
| A2 (E14) — dedicated model vs calendar-reg | contrast per city | **Kept.** |
| A2 (E14) — dedicated model vs G1-reg (and G0-reg) | contrasts per city | **G1-reg suspended**: the original GWN spatial path is not admitted as a primary comparator without a validation of its own (it inherits the reach property measured by I3); no new fit of G1-reg or G0-reg is authorised by this revision. Any regression comparison with a GWN-type arm is defined in E14's revised matrix, without summing all old and new arms. |
| A4 (E15) — replication on NDW-Rotterdam, both tasks, 10 arms × 5 splits | contrasts as E15 will fix | **Kept for validated, frozen recipes only.** The classification replication depends on the outcome of B1 (E13B); the regression replication on the outcome of E14. |

The P4R family of 24 contrasts no longer exists as such: 6 withdrawn (A1), the A2 G1-reg/G0-reg members suspended, the rest redefined by block below.

## 2. Confirmatory hypotheses, families and correction (closed now, before any new result)

The campaign-wide α = 0.05 is split **before any result** among three families; the table of confirmatory hypotheses is closed here, the operational details (metrics, cells, estimators) stay in the block protocols, which may not add, remove or replace a confirmatory hypothesis. Within each family a **single joint procedure** controls every confirmatory statement the family may produce: a two-sided **sup-t simultaneous band** at level 1 − α_family over the family's contrasts, from the pre-registered block bootstrap with shared multiplicities; every statement is a deterministic function of that band, so the family-wise error of all statements together is ≤ α_family **nominally** — the bootstrap control is asymptotic and conditional on the observed fits, not an exact finite-sample guarantee (P4R §7), and the paper says so. Holm is not used (two procedures on one family would not be jointly controlled). **This revision replaces the Holm wording of E13B.md** (condition (a) of its positive statement: "the one-sided positive test ... significant after the correction of the pre-registered family") with the F1 band at level 0.98: condition (a) is met where the lower simultaneous bound exceeds 0; `e13b.py analysis` stays provisional and unchanged.

| Family | Confirmatory hypotheses (members) | α | Statements derived from the band (all at once) |
| --- | --- | ---: | --- |
| **F1 — E13B** | H1.c: V_c(D1) for c ∈ {Madrid, London, Melbourne} (3) | **0.020** | *helps*: lower bound > 0 in ≥ 2 cities, point estimate ≥ 3 there, adequacy (c) of E13B.md; *at least 3*: lower bound ≥ 3 (stated separately where it holds); *below the margin*: upper bound < 3 in all three cities and adequacy; otherwise *undetermined* |
| **F2 — E14 (regression, dedicated model)** | H2.1.c: dedicated model on schema S0 vs calendar-reg (3); H2.2.c: **dynamic benefit without coordinates** (dynamic readings on vs off, coordinates off) (3); H2.3.c: **dynamic benefit with coordinates** (dynamic on vs off, coordinates on) (3); H2.4.c: interaction between the two benefits (3) — 12, the original E14 contrasts of P4R preserved; the effect of coordinates is secondary and descriptive | **0.020** | same construction on MAE contrasts, **on the sign only** (lower bound > 0 = benefit; upper bound < 0 = detriment; otherwise undetermined): no regression margin exists, so no statement of equivalence or negligible benefit is made in F2 unless a margin is justified and approved separately; the classification margin does not transfer; E14.md fixes estimators and cells and may not change the members |
| **FR — E15 replication (NDW-Rotterdam)** | HR.1: D1 vs D0, classification (1); HR.2–HR.5: the four F2 contrasts replicated (4) — at most 5; a member is dropped (not replaced) if its recipe was not executed and frozen under the corresponding protocol with its controls passed | **0.010** | same construction; HR.1 on the two scales as F1 (the classification margin is E11's convention and applies to the classification task only), HR.2–HR.5 on the sign only; E15.md fixes estimators and cells; a dropped member releases no α to the others |
| descriptive | reached/unreached contrasts, selected configurations, I3 tables, D0 vs any table baseline, seed-to-seed spreads | — | reported with marginal intervals, labelled, no confirmatory statement |

Sum of allocations: 0.050. `e13b.py analysis` keeps reporting marginal 95 % intervals and unadjusted p-values with the PROVISIONAL label and its mechanical reading; the confirmatory statements of F1 are produced only by the campaign-wide analysis script, which rebuilds the F1 band at level 0.98 from the same replicates and is pre-registered here. The inclusion rules of FR are fixed now: a replication member exists if and only if the corresponding recipe (arm, configuration selection rule, cap) was executed and locked in B1 or E14 under its protocol **with that protocol's controls passed** — the replication depends on passed controls and frozen recipes, **not on the significance or the sign of the benefit found**; no member is added or replaced after any result.

## 3. Budget (fits and measured hours)

| Block | Fits as signed | Fits after this revision | Measured cost | Machine |
| --- | ---: | ---: | --- | --- |
| A1 (E13) | 300 | **0** (withdrawn) | — | — |
| B1 (E13B) | — | **150** (120 development + 30 final), full grid, reduction rule not applied | D1 0.286 s/update, D0 0.270 s/update (E13B-pre, MPS); ≈ 120–125 h of process time | Mac |
| B0 (E13B) | — | 4 trainings of 2 000 (done, 14:25) + B0.1 and benchmark (done) | ≈ 40 min + 560 updates | Mac |
| A3/A2 dedicated model (E14) | 300 | ≤ 300, to be confirmed by E14-pre on the adapted model | to be measured (E14-pre) | Spark |
| A2 G0-reg/G1-reg (E14) | 150 | **0 authorised now** (suspended; E14's matrix may define a validated arm, with its own fits counted there) | — | Spark |
| A4 (E15) | 50 | ≤ 50, validated recipes only | to be measured | Mac / Spark |
| **nominal planned ceiling** | 800 | **≤ 500** (150 + ≤ 300 + ≤ 50), subject to the authorisation of each block by its own signed protocol and controls | | |

The E13 budget is not transferred automatically. B1's 150 fits become executable only after this revision is ratified, deposited and recorded (`p4r-revision`); E14's and E15's fits only after their own protocols and controls. Extensions (20 development trajectories to 20 000 plus 5 finals per extended (city, arm)), reproductions, registered retries, A0/B0 checks and benchmarks are counted separately when they occur, as in P4R §8.

## 3-bis. Linkage to the gate of E13B

`e13b.py p4r-revision` verifies and records the fingerprint of `protocol/paper4/P4R.md`, not of this file. Therefore the dated note appended to `P4R.md` **incorporates this revision by reference**: path `protocol/paper4/rafforzamento/P4R_REV1.md`, commit of the signed version and its sha256. The receipt in `P4R_RECEIPT.md` identifies the same signed version (path, commit, fingerprint) together with the P4R.md that references it; the gate then checks that P4R.md is committed unchanged and equal to the recorded fingerprint.

## 4. Order of blocks

1. **E13B B1** (executable once this revision is ratified, deposited and recorded): development of the 30 cells on the Mac, extension if the adequacy rule requires it, finals, lock, test, provisional analysis.
2. **E14 drafted** during B1: dedicated model adapter reviewed; E14's own positive control and structural measurement of the dedicated model's propagation designed; revised regression matrix; F2 enumerated; **E14-pre** (cost of the adapted model on Spark) under its own signed protocol.
3. **E14** signed, deposited, run on Spark.
4. **E15** designed from the frozen recipes of E13B and E14 whose controls passed, with FR's members determined by the inclusion rule above; G-data closed (site set, layers, limits, distances, hours, partitions and fingerprints frozen before any model run); run.
5. **Campaign-wide analysis**: the F1, F2 and FR bands at their allotted levels, confirmatory statements, paper.

## 5. What goes into the paper whatever the outcomes

The closure of E13 (failed positive controls, investigations I1–I2, cause unresolved) and, kept distinct, the structural property measured by I3 (reachability and reference mass of the GWN spatial path at f = 0.20 in the frozen E9/E11 design), next to the E9/E11 results, with the per-city/per-seed tables in the appendix; the comparisons planned and not executed; the development/verification separation (A0.2, I1–I3 as development evidence; B0.2 on new realisations as verification of the variant's pipeline); the B1 result with the share of unreachable nodes, the selected budgets and configurations, the validation curves and the adequacy diagnostics; the suspension of G1-reg and its reason.

## 6. Roles and rules unchanged

Everything of P4R not touched above stays as signed: roles (internal review assigned per protocol, note of 2026-11-18), DEP-01 deposits, frozen-version gates, dated notes, the stopping rule of the collegial decision (a failed pre-registered control blocks real fits; no automatic change of generator, neighbourhood or architecture; further investigation requires a new collegial decision), hidden-site rules, data perimeter.
