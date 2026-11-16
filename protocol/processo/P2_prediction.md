# P2 — Prediction before the invitation (P0 §10)

**Purpose.** Record the authors' expectations before inviting the reviewers, for subsequent comparison with the audit outcome. This document is not a target for reviewers and is not part of their audit package.

**Scope fixed by P0 §10.** Implementation correctness of the authentic code exported at `paper1-freeze-20261103q` (Paper 1) and `paper4-freeze-20261110a` (Paper 4), with the pre-registrations but without git history, registers, regeneration reports or manuscripts. Three reviewers from two partner organisations: P2-01 and P2-02 (Frontiere), P2-03 (Mediacom), 8–16 declared hours each. No defect is re-inserted. Experimental validity, provenance, licences and judgement defects remain outside scope.

**Knowledge used in preparing the prediction.** The resolved coding contains 108 counted problems: 102 defects, five deviations and one violation. Of these, 67 are assigned to Paper 1 and 41 to Paper 4; the Paper 1 allocation includes shared problems and is not a count of Paper-1-only problems. The corpus is historical, not a list of 108 defects still present at the audit tags. Its type distribution includes 30 provenance/traceability cases and nine documentary cases, many of which cannot yield an in-scope implementation finding.

The available phase-6 delivery notes and agreement summary were consulted. The summary reports primary-type agreement of 29/33 (κ = 0.87), status agreement of 33/33 (κ = 1.00), and introduction-phase agreement of 30/33 (κ = 0.83). These describe classification agreement on a historical sample; they do not establish the correctness of the frozen code or calibrate its residual defect count. 

Preparation included a targeted reading of frozen code for temporal grids, weighted evaluation, static features, common-weight comparisons, neighbour/calendar fallbacks and external input checks. This was not a complete audit or a rerun of the experiments. The executor copy and private manuscripts were not used as substitutes for the audit tags.

---

## 1. Number of reports

The ranges are subjective plausible ranges, not statistical confidence intervals. The central values form one illustrative, internally consistent outcome. Zero confirmed findings remains plausible and would not establish that no defects remain.

**Counting convention for this prediction.** A report is an individual issue submission; submissions bundling several issues are separated for counting. Confirmed problems are distinct problems after deduplication across reviewers and papers, following P0 §4. Repeated reports of the same problem do not add problems. False-positive, out-of-scope and unresolved counts below refer to submissions. Consequently, these rows cannot simply be added without accounting for duplicates.

| Quantity | Prediction | Rationale |
| --- | --- | --- |
| Reports per reviewer, all validity classes | 3 to 7; central 4 | Eight to sixteen hours should permit focused inspection of several components, but not exhaustive tracing of the full pipelines. |
| Distinct confirmed problems, total over the three reviewers | 0 to 6; central 2 | Earlier corrections and explicit checks reduce expected yield; integration and boundary cases remain plausible. |
| Of which already registered in the corpus | 0 to 2; central 0 | Many historical defects have been corrected or supplemented by later controls. No particular historical defect is assumed to persist in an operative path. |
| Of which new, not in the corpus | 0 to 4; central 2 | A small number of local implementation defects is plausible, especially at array, time-window and fallback boundaries. |
| False-positive submissions, total | 2 to 6; central 4 | Historical modes, diagnostic alternatives and safeguards implemented in callers or companion scripts can initially look defective. |
| Out-of-scope submissions, total | 2 to 6; central 4 | Methodological choices, historical provenance and dependencies/licences may attract comments without satisfying the implementation scope. |
| Unresolved submissions, total | 0 to 2; central 1 | Some alleged effects may require unavailable data or execution evidence. Unresolved is retained as a separate validity class under P0 §10. |
| Additional confirmed submissions duplicating an already counted problem | 0 to 3; central 1 | Reviewers may independently inspect the same prominent components. |

Central accounting: 12 submissions = 2 first reports of distinct confirmed problems + 1 duplicate confirmed report + 4 false positives + 4 out-of-scope reports + 1 unresolved report. Both distinct confirmed problems are new. The range endpoints are not intended to describe a single simultaneous outcome.

## 2. Types of the new problems (P0 §5.3)

These are central predicted counts of distinct new confirmed problems across all three reviewers. They sum to **2**, matching §1. Apply the pre-specified primary-type precedence rules; do not double-count secondary types.

| Type | Expected | Where in the code, if there is an expectation |
| --- | ---: | --- |
| 1 leakage | 0 | Inspect training/validation/test boundaries and static-feature variants, but do not assume that an explicitly retained historical mode is a new defect. |
| 2 indexing and alignment | 1 | Paper 1 temporal origins, acquisition endpoints and node populations; Paper 4 joins between nodes, blocks, horizons and target-time calendar slots. |
| 3 silent loss | 1 | Missing-target masks, zero or empty groups, and fallback selection/aggregation, especially in the E12 family. A fallback correctly implementing its declared rule is not itself a defect. |
| 4 metric (a/b/c) | 0 | Per-horizon wCE aggregation and shared-weight comparisons remain likely inspection targets. Type 4b concerns about a faithfully implemented methodological choice are outside this audit's scope. |
| 5 budget, selection and convergence | 0 | Training loops and checkpoint/threshold selection may be inspected; no specific new mismatch is predicted. |
| 7 provenance and traceability | 0 | Provenance concerns are explicitly excluded by P0 §10; report them separately as out of scope. |
| 8 defective control | 0 | Companion checkers and synthetic tests may attract reports, but omission from one module alone does not establish an absent workflow control. |
| 10 environment and dependencies | 0 | No new in-scope implementation defect of this type is predicted. Licence concerns are out of scope; environment complaints require a demonstrated implementation mismatch before confirmation. |
| 11 other | 0 | No specific residual mechanism outside the listed categories is predicted. |

Types **6 and 9: 0**. The package excludes manuscript text and process history, and this audit does not assess manuscript claims or procedural compliance. A zero central prediction is not a prohibition on observing an eligible finding.

## 3. Severity of the new problems (scale fixed in P0 §10)

| Severity | Expected number of distinct new problems |
| --- | ---: |
| No effect on the numbers | 1 |
| Within the tolerance of the regeneration | 0 |
| Changes a number of the paper | 1 |
| Changes a reading (sign, ordering, conclusion) | 0 |

Total: **2**. The working expectation is one edge-path defect without an effect on the reported numbers and one defect affecting a number without changing its substantive reading. These are hypotheses. Actual effects must be established through the pre-registered correction and regeneration required by P0 §10; they cannot be inferred from code inspection alone. Use the highest applicable severity per problem, so a change of reading is not also counted in the preceding row.

## 4. Where reviewers are expected to look, and what they may miss

**Files or components most likely to yield reports:**

- Paper 1: `evoluzione/componente/griglia.py`, `evoluzione/componente/valutazione.py`, `evoluzione/esperimenti/inserimento.py`, and their callers. These combine time boundaries, missing-cell masks, horizon-specific denominators and static-feature variants. E18 analysis and table-generation paths are secondary targets for checking consistency between implemented aggregates and protocol definitions.
- Paper 4: `paper4/code/e10pred.py`, `paper4/code/e10predbis.py`, the `paper4/code/e12*.py` family, and `paper4/code/genera_congelamento_e11.py`. Likely inspection points are common-node intersections, weight selection, array axes, distance bins, target-time slots and fallback counters. `paper4/code/verifica_e12.py` must be considered alongside the module it checks.

**Fragile components whose effects may be missed by reading alone:** actual calendar discontinuities and missingness patterns; rare empty node/class/horizon combinations; the realised use of calendar fallbacks; consistency of saved arrays across campaigns; small floating-point differences across machines; and runtime-dependent interactions between experiment stages. The corpus provides historical examples of these mechanisms, but their recurrence at the audit tags is not asserted. Quantifying their effect requires concrete inputs and, often, execution.

**Known corpus problems potentially recognised again:** no specific ID is confidently predicted to be confirmed again in an operative defective path; the central count is zero. Conditional recognition candidates are:

- **P1-035:** full-series static coverage. `inserimento.py` retains the non-causal `congelata` option and explicitly sets `espansiva` as the default. Recognising the historical mechanism does not show that a path required to be causal still uses it.
- **P4-001:** configuration-specific weights in E10-pred. `e10predbis.py` explicitly implements the subsequent common-weight comparison. Reviewers may recognise the original mechanism; confirmation requires establishing the applicability of that original path under the supplied protocols.
- **P4-031 and P4-032:** checks absent from frozen E12 itself. `verifica_e12.py` supplies external input checking and an end-to-end synthetic test. Reviewers may report the local omissions, but a claim that the complete workflow lacks those controls must account for this companion script.

These IDs are a recognition shortlist, not four predicted confirmed defects. A report of an intentionally preserved historical implementation, a corrected mechanism or an excluded methodological concern is adjudicated on its merits; resemblance to a corpus entry alone is insufficient.

## 5. Differences between Paper 1 and Paper 4 code

**More reports expected on: Paper 1**, assuming roughly comparable reviewer attention to each paper.

Paper 1 exposes numerous experiment stages, static-feature variants, adaptation paths and analysis/table interfaces. These offer several places where a local reading can miss a condition imposed elsewhere. Paper 4 also contains substantial integration complexity, particularly in the E12 sequence, but many of its historical corpus items concern provenance and deliverable records outside this audit. The historical 67/41 allocation supports context only; it is not a defect-density comparison, and no exposure-normalised rate is predicted. Unequal reviewer time could reverse the report-count ordering.

## 6. What would surprise the authors

The outcome most contrary to this proposed expectation would be a newly confirmed implementation defect in an operative frozen-code path that survives the existing checks and, after correction and regeneration, reverses a principal sign, ordering or conclusion—especially if the same mechanism occurs in both papers.

---

## Signature

Responsible author: Gabriele De Vito, date 2026-11-15 (Europe/Rome). Co-authors consulted: Fabio Palomba and Filomena Ferrucci. The commit immediately before this file is its parent commit in the history of `main`. The invitation to P2-01, P2-02 and P2-03 is sent only after this file is committed and pushed; the commit hash of the invitation e-mail's attachments is recorded in P2_INVITATION.md.
