# P4R — Scope, gates, roles and budget of the strengthening campaign of Paper 4

Signed version, 2026-11-18. Prepared by the coordination role (drafts 1–5 of 2026-11-16/18, each revised on the responsible author's review). Formalises the plan discussed with the co-authors (`rafforzamento/piano/PIANO_RAFFORZAMENTO_PAPER4.md`, 2026-11-16, and the revised plan v3 of the same day, both after two internal adversarial reviews) and records the dataset audit of 2026-11-16/18. **No training run is authorised by this document: each block starts only with its own signed and deposited protocol (§10).** The frozen results of Paper 4 (tag `paper4-freeze-20261110a`, commit `251527052d4c`) are not modified by anything below; they remain the first study of the paper.

Planning record, committed unchanged under `protocol/paper4/rafforzamento/piano/` on branch `paper4` (commits `bc42751`, `4f97724`, `ab546c1`, `58ab8e9`, 2026-11-18): `EXPERIMENT_PLAN_20261116.txt` (v3), `EXPERIMENT_FEASIBILITY_20261116.txt`, `EXPERIMENT_ADVERSARIAL_20261116.txt`, `EXPERIMENT_READER_20261116.txt`, `SCOPUS_SEARCH_20261116.json`, `P4R_REVISED_PLAN_20261116.txt`, `PIANO_RAFFORZAMENTO_PAPER4.md`, `DATASET_AUDIT.md`, `FATTIBILITA_HERE_BARONISSI_20261116.md`. Where this document and the plans differ, this document prevails once signed; where it is silent, the revised plan v3 applies.

## 1. Question and contribution

**Question.** When, and by how much, do the dynamic readings of observed sensors improve the forecast at sites without history, beyond calendar regularities and the static information available?

**Contribution claimed.** A controlled separation of these information sources, verified with a dedicated inductive model, adequate training, and a replication on a different data source. We do not claim a new algorithm, the first history-free forecasting, or a causal account of traffic. Novelty is subordinate to the comparison with the closest works (§3, gate G-lit) and is not produced by adding experiments.

Forecasting is the core. Placement and local measurement keep their historical results and limits as complementary evidence, fixed now; no ranking of local versus remote sensor value.

**Definitions.** G0: the Graph WaveNet variant without spatial exchange; G1: with convolutions on a fixed graph. wCE: the weighted cross-entropy of the historical three-class task. Continuous factor: measured speed over a free-flow reference. I0/I1: original inputs / original inputs plus coordinates. The new factorial manipulates **additional coordinates × dynamic readings**; topology is present in every cell.

**Pre-stated outcomes**, all informative (plan v3 §11): a precise positive dynamic benefit → conditions and size, no general negative headline; benefit dependent on coordinates → interaction supported only by the direct contrast; benefit only static → contrasts described, no claim that dynamics are irrelevant without a justified margin; small and precisely estimated gain → conclusion limited to task, models, coverage and data; discordant replication → heterogeneity, no post-hoc choice of explanation; inadequate training or wide intervals → inconclusive, feasibility limit.

The regression track (§6) is a **declared extension with a new estimand** (MAE of the continuous factor). It does not re-analyse the wCE results and does not explain the historical classification result causally. The classification keeps the G0/G1 family: it is strengthened by tuning, coordinates and replication, not validated on a second dedicated architecture; a reviewer's "single architecture" objection on classification is answered in the text with this division, written before the results.

## 2. Blocks and order

| Block | Content | Protocol | Deposit |
| --- | --- | --- | --- |
| G-lit | literature matrix at full text; co-authors ratify the gap and the comparison | this document, §3 | — |
| A0 | correctness: code, inputs, masks, scalers, calendar, decoder, loss; synthetic checks; adequacy rules — before the corresponding development campaign | E13 | yes |
| A1 | classification: G0/G1 × I0/I1, 3 cities, coverage 20 %, 5 outer splits, nested tuning | E13 | yes |
| A2 | regression: dedicated model vs G0-reg, G1-reg, calendar-reg on schema S0 | E14 | yes |
| A3 | dedicated model 2×2: dynamic readings {present, absent} × coordinates {absent, present} | E14 | yes |
| A4 | replication on NDW-Rotterdam, both tasks, frozen recipes | E15 | yes |
| A5, A6, shuffle | out of the core; separate decisions, if ever | — | — |

Order of work: G-lit and ratification → E13-pre microbenchmark (G0, G1 and the original dedicated model: confirms the cost of the classification campaign and gives a preliminary estimate for the dedicated model) → E13 signed → A0, A1 development → E14 drafted, adapter reviewed → E14-pre (adapted model: confirms the cost of the regression campaign **before** A2/A3 development) → E14 signed → A2/A3 development → analysis script frozen → final fits A1–A3 → E15 signed → A4 → frozen analysis → double internal review → paper, new manuscript tag, Zenodo package. The overall budget (§8) is subject to both microbenchmarks.

## 3. Gate G-lit — contribution before cost

A matrix of the closest works, completed at full text from the Scopus record of 2026-11-16 (MoGERNN 2025, UIGNN 2023, V-DCRNN 2025, Ding et al. 2025, SIML/MSIGN 2026, Math et al. 2025, TA-ANP 2026, SLPF, Ermagun 2017, Climatology 2026). Columns: future forecasting vs contemporaneous reconstruction; target history allowed; static/dynamic inputs; calendar baseline; training controls; component comparisons; replication; code; verified at full text yes/no. The search is not called exhaustive. Before the extended campaign the co-authors approve in writing: the documented gap, the experimental comparison that addresses it, the expected added value. If a work already contains the comparison under equivalent conditions, the value of the replication or the core design is reconsidered before any cost is incurred.

## 4. Outcome and data for the replication (A4)

**Outcome decision (before the dataset, plan §2).** In the three cities the free-flow reference comes from the provider; in a loop dataset a reference computed from the hidden site's own history is not operationally available. The replication therefore uses, as its primary outcome, the **speed normalised by the posted limit** of the site, with class thresholds for this outcome fixed and justified in E15 before any experiment; the thresholds 0.8/0.4 of the original factor are **not** inherited, because the two references are not interchangeable. This is a replication of the comparison between information sources on a different outcome, not an exact replication of the original factor. Alternative, secondary: a reference estimated from observed-training sites only, with a common rule for all models. A reference from the hidden site's history may define an offline outcome only if declared and kept out of inputs and normalisation.

**Dataset.** The audit sheet `rafforzamento/piano/DATASET_AUDIT.md` states the criteria C1–C6 and the decision rule; its criteria and decision rule were written on 2026-11-16 before the first probe; the sheet is in the planning record (first committed version `bc42751`; version with the acquisition and the licence check `ab546c1`; dated notes on the C3 deviation and the day count `58ab8e9`). Chosen: **NDW-Rotterdam**, the only urban candidate. Acquired and frozen on 2026-11-18: 1 June – 31 December 2025 (214 days, plus the two minutes 23:58–23:59 UTC of 2025-05-31 at the head of the first export, which the verification counts as a 215th "day with data"; the cities cover Madrid 2021-06-01 → 2021-12-31, London 2019-07-01 → 2020-01-31, Melbourne 2020-06-01 → 2020-12-30: comparable length, no claim of seasonal equivalence). **Deviation from the audit criterion C3, declared:** the audit sheet of 2026-11-16 set a minimum duration of 9 months; the acquisition covers 7, chosen after the candidates were examined so that the replication has the same extent as the original studies and not more training data than they had. The criterion is not rewritten; the deviation is recorded with this date in the audit sheet and here, and the alternative (extending to 9 months with 13 further exports) is the responsible author's decision at signature: **deviation accepted** (2026-11-18). 1-minute flow and speed from the NDW Dexter open-data export, filtered to the bbox 51.85–51.98 N, 4.35–4.60 E: 1 625 sites with data, of which 359 urban (municipality, metropolitan region, port, neighbouring municipalities) and 1 266 on the motorway ring. Package `pacchetto_ndw_rotterdam_2025/` (kept outside the repository; its `MANIFEST.tsv`, `PROVENIENZA.md` and scripts go under `data_collection/ndw_rotterdam/` at E15): the object hashed is the single file `ndw_rotterdam_2025-06-01_2025-12-31.csv.gz`, 3 142 264 167 bytes, 402 509 566 rows, sha256 `16acf38e13c4ff780bdb94bdc335f89875c5b4901b166f301ad9e01c8a4d82a6`; every other file of the package is listed with its sha256 in `MANIFEST.tsv`. Licence CC0 1.0 (NDW open-data terms of use, checked 2026-11-18, `NOTA_2026-11-18_licenza.md`). Never used by us; not a benchmark of the candidate model (METR-LA and PEMS only, `evoluzione/audit/AUDIT_MoGERNN.md`).

**What the audit did and did not do.** The preliminary audit inspected metadata and measurement availability: presence of each site per minute, share of minutes with a valid speed, missingness by hour of day, counts of sites meeting availability thresholds, and the operator's data-quality sheet for 20 sites. No forecasting performance was evaluated; no target, class or threshold statistic was computed. Further outcome-distribution analyses and all model evaluations are deferred to the signed E15 protocol. The selection of sites by availability and speed validity over the whole period is a **retrospective definition of the sample**, distinct from any choice learned on training data, and is declared as such.

Known properties, documented: the export omits 00:00–01:59 local until 25 October and 00:00–00:59 local from 26 October (fixed nightly gap; the T4C cities cover ~12 h/day); ~320 motorway sites start publishing in late October (urban sites present throughout: 357/359 ≥ 90 % of minutes); about 8 % of the 1-minute speeds are missing, mostly at night when no vehicle passes in the minute. E15 defines the aggregation to 15 min, the minimum number of valid observations per bin, and the handling of bins that remain missing.

Rules fixed now, applied only in E15: site selection = presence ≥ 90 % of the period's minutes and valid speed ≥ 70 % (273 urban sites with these thresholds); **the primary replication uses the eligible urban sites; the motorway layer is excluded from the core campaign** — any analysis of that layer requires a separately specified scope, analysis family and budget, not covered by the 800 fits; hours of day restricted to those covered by the T4C cities; per-site posted limits from the NDW traffic-signs dataset or OSM `maxspeed`, frozen with their source; road-network distances from OSM; coverage, windows and horizons as in the cities, any frequency adaptation defined before the test. No statistic of the targets is computed before E15 is signed.

WebTRIS (England, M6/M42/M5 around Birmingham, 188 motorway sites with ≥ 90 % of good days in 2025, open API) is verified and archived as the second replication **only if the co-authors fund it** (+50 final fits); Madrid M-30 2024 is the reserve (already used in P4A for the measurement comparison). HERE Baronissi excluded (variable segment set, interruptions).

## 5. A0, A1 — correctness and classification

A0 before the corresponding development campaign (some benchmarks and checks have a cost of their own, counted outside the 800 fits): audit of code, inputs, masks, scalers, calendar, decoder and loss; no dynamic reading of test-hidden sites in training, selection or inference; validation-hidden used only for authorised selection, test-hidden only in the final evaluation; no selection transferred between splits that exposes a split's test labels; coordinates and topology may be known, target history never. Synthetic checks with and without a known dependence; invariance to perturbation of excluded data; the full model must exploit an available spatial signal. A failed check blocks interpretation; it is not a negative result. MoGERNN (commit `86b153fb4bf9…`) is the dedicated model, UIGNN the technical reserve named before any outcome; explicit masks (no inference of sensor presence from numeric values); autoregressive recurrence kept, teacher forcing disabled consistently in all regression arms.

A1: three cities, five existing outer splits, coverage 20 %; G0/G1 × I0/I1; four development configurations per arm and split with nested tuning, one development initialisation per configuration, one distinct final initialisation; family-specific grids with a documented reference configuration and equal selection opportunity; adequacy rule on validation curves fixed before the test; failures handled on development/validation only, registered, re-frozen. No preventive halving of the dedicated model's budget.

## 6. A2, A3 — regression and the 2×2

A2: dedicated model, G0-reg, G1-reg and calendar-reg on the common schema S0 (observed factor history in the dynamic arms, calendar, topology, explicit masks; no coordinates as features; no target-specific embeddings). MAE primary, RMSE secondary; calendar-reg = per-slot median of observed-training sites only, global observed-training fallback; mean variant for RMSE, secondary.

A3, in the dedicated model: {full S0, no-dynamic S0, full S1, no-dynamic S1}; S1 = S0 + coordinates with a shared encoding. Full S0 is the A2 fit (planned reuse, conditional on identical schema, masks, loss and training policy, checked in A0). Dynamic suppression removes every dynamic reading from the input, not topology nor observed-training supervision; masks and layout unchanged. Estimands: dynamic benefit in S0, in S1, their paired difference, and the static benefit at fixed dynamics. Interpretation limited to the incremental value of input availability in the trained pipeline. G0-reg/G1-reg with coordinates are not in the core.

## 7. Analysis plan (frozen before the final fits)

Paired differences on the same targets/origins/masks; no pseudo-replication of rows; resampling that preserves spatial and temporal dependence and the overlap of the five splits; uncertainty declared conditional on the observed fits. Primary family on the historical data: A1 six contrasts (G1−G0 per city × {I0, I1}), A2 nine (dedicated S0 vs three baselines per city), A3 nine (two dynamic benefits and one interaction per city) = **24**, mean over the pre-specified horizons, Holm within the family; marginal intervals labelled as such, simultaneous bounds for simultaneous exclusions. Replication: a separate family of eight analogous contrasts (two A1, three A2, three A3). Static contrasts and extra horizons secondary, declared. No regression equivalence margin imported from the wCE 3-point convention; without a justified margin, estimates and uncertainty are reported with no equivalence claim; a wide interval is inconclusive. Precision checked on training/validation before the test; no sample extension decided by significance.

## 8. Budget and machines

| Component | Neural fits (development + final) |
| --- | ---: |
| A1 classification: 4 arms × 3 cities × 5 splits × (4 + 1) | 300 |
| A3/A2 dedicated model, four cells | 300 |
| A2 G0-reg, G1-reg | 150 |
| A4 NDW-Rotterdam, both tasks: 10 arms × 5 splits, frozen recipes, checkpoint by the frozen rule on external validation | 50 |
| **total** | **800** |

Plus calendar estimates (classification and regression, counted separately), A0 checks, benchmarks, registered retries, inference and analysis; not a total cost and not a promise of hours. WebTRIS, if funded: +50.

Machines: **Mac (M3 Max, MPS): A1 and the external classification. Spark (CUDA): the whole regression comparison, including G0-reg/G1-reg and the external regression.** Putting only the dedicated model on Spark would confound architecture and backend in the direct A2 contrasts. Spark carries 480 of 800 fits, the slow ones; E13-pre (classification, original dedicated model) and E14-pre (adapted model) measure the two loads, and the budget is subject to both. Every fit records machine, backend, library versions, all seeds, deterministic flags and what remains non-deterministic. Three distinct checks: regeneration of frozen numbers from recorded outputs (declared tolerances); implementation correctness (A0 tests); variability of new trainings across machines (measured on a pre-declared subset, reported as variability). No training is called "reproduced" because two machines give similar numbers; times are not compared across machines.

Reduction rule, before any outcome: grid from four to two configurations **uniformly** for both machines and all families → 500 fits, preserving arms, cities, splits and the adequacy check. Never reduce only the dedicated model's training; if even 500 is unsustainable, renegotiate scope before the test.

## 9. Roles and repository rules

| Role | Who | Does |
| --- | --- | --- |
| responsible author | G. De Vito | reviews and modifies drafts; signs; freezes code by tag; **launches all runs**; commits, pushes, tags |
| coordination | internal, under the responsible author | drafts protocols, code and analysis scripts; validates records; keeps the register |
| internal reviewer | F. Palomba | reviews each protocol, the adapter and the frozen analysis before signature / before the paper changes |
| co-authors | Catolino, Di Nucci, Gravino, De Lucia, Ferrucci | ratify G-lit, scope, outcome, machine assignment and budget |

The author/executor separation of the first study is not kept and is declared in the paper. Replacing it: every run reads code at a signed tag pushed to the public repository before the first launch; outputs record tag, machine, backend, seeds, environment; a code change after the tag is a registered deviation with a new tag and a restarted run; frozen records are generated by script; the analysis script is frozen before the final fits; historical runs and superseded runs are kept; corrections go to the register of corrections (items from 27), never into a frozen record. Work on branch `paper4` in the `repo-paper4` worktree only; run outputs under `paper4/runs/` are not committed (manifests and fingerprints are).

## 10. Deposit and gates

P4R, once signed, is deposited with DEP-01 (the Mediacom custodian whose corrected assignment is recorded in `protocol/processo/P0_RECEIPT.md`, after checking availability and that the person has no role in this campaign), with the sha256 of the signed file; receipt in `P4R_RECEIPT.md`. **Each operational protocol (E13-pre, E13, E14-pre, E14, E15) and each later modification is deposited the same way before the executions it applies to**, in addition to its signature and public push.

| Gate | Closed by |
| --- | --- |
| G-lit | literature matrix at full text + written ratification by the co-authors |
| G-scope | signature of this document |
| G-outcome | thresholds and reference for the replication outcome, justified, in E15 |
| G-data | site set, layers, limits, distances, hours, partitions and fingerprints frozen in E15 before any model run |
| G-candidate | MoGERNN commit, full text and code read; UIGNN reserve with reason (E13) |
| G-schema | one manifest of channels, S0 and S1, shared by all arms (E14) |
| G-masks | explicit masks identical across arms; invariance tests pass (E14, A0 report) |
| G-tuning | nested per split; split_id, init_seed, tuning_seed distinct (E13/E14) |
| G-stats | estimands, resampling, families, Holm, margins or none, frozen before the final fits (E13/E14/E15) |
| G-compute | E13-pre done: classification cost confirmed or reduced; E14-pre done after the adapter review and **before A2/A3 development**: regression cost confirmed or reduced; the overall budget subject to both (dated notes to P4R) |

## 11. What does not change

Tag `paper4-freeze-20261110a`, its records and registers: untouched; still the object of the P2 audit of the process study. Zenodo record `10.5281/zenodo.24059573`: stays a draft; the package is rebuilt at the end for the new tag. The process study (P0): its window closed at the P0 snapshot; this campaign is outside its corpus and is said so in one line of the process paper. The manuscript: changed by the responsible author only, after the frozen analysis and the double review, on Overleaf; new manuscript tag.

## Signature

Responsible author: Gabriele De Vito, 2026-11-18 09:47 (Europe/Rome). Co-authors consulted: Filomena Ferrucci. Decisions ratified: regression track as the main multi-architecture comparison; outcome speed/limit for the replication; coordinates × dynamic readings factorial; machine assignment and 800-fit budget (subject to E13-pre and E14-pre); NDW-Rotterdam urban sites as the replication dataset, motorway layer excluded; WebTRIS not funded; C3 deviation accepted. Commits of the planning record and of the audit sheet: `bc42751`, `4f97724`, `ab546c1`, `58ab8e9`. Deposited with DEP-01: date and time in `P4R_RECEIPT.md`.

## Dated notes after signature

**2026-11-18 — E13-pre executed; gate G-compute, part 1 (classification): outcome (a), full grid.** Protocol `E13pre.md` (tag `paper4-E13pre-20261118`, commit `032752e`, deposited 10:19). Runs from clean worktrees of the tag on both machines; reports under `paper4/runs/e13pre_mac/` and `paper4/runs/e13pre_spark/` (`report_<device>.json|md`, committed). Madrid, f = 0.20, seed 0, K = 828 nodes, grid 11, batch 32; seconds per update as (t60 − t10)/50, median of three.

| Machine, backend | G0 s/update | G1 s/update | A1 hours (150 fits per arm): U = 1 000 / 5 000 / 10 000 |
| --- | --- | --- | --- |
| Mac M3 Max, MPS | 0.062 | 0.131 | 9 / 41 / 81 |
| Mac, CPU (reference) | 0.859 | 1.600 | 115 / 525 / 1 037 |
| Spark GB10, CUDA | 0.076 | 0.116 | 9 / 41 / 81 |
| Spark, CPU (reference) | 0.568 | 1.067 | 74 / 346 / 687 |

Classification (A1, 300 fits) on the Mac in MPS: within the calendar at the full grid of four configurations for any U up to 10 000 → **outcome (a)**; no reduction. CUDA brings no gain on G0/G1 (small models); the assignment of P4R §8 (classification on the Mac, regression on Spark) stands.

Dedicated model, original code (`86b153f`), MPS, 828 synthetic nodes, batch 32, audited benchmark unchanged, run in the Paper 1 environment because `einops` is absent from `ENV.txt` (declared): 1.12 s per full update (min 1.07, max 1.14, n = 10), inference 0.65 s, CPU/MPS agreement 10⁻⁷–10⁻⁸. Preliminary estimate only: 300 dedicated fits at U = 10 000 would be ≈ 930 h on MPS; the regression campaign depends on Spark, whose cost for the **adapted** model is measured by E14-pre (the audited benchmark accepts `cpu|mps` only; not modified).

Checks: London data files differ from Madrid's on both machines (prerequisite to E13); code not dirty; Spark environment = root poetry env (torch 2.12.1+cu130, numpy 2.5.1 vs 2.5.0 in `ENV.txt`), recorded in the reports. Load average on the Mac during the MPS run 3–3.7 on 14 cores (background load present, declared); Spark idle.

**2026-11-18 — Internal review assigned per protocol.** The internal review of each operational protocol, adapter and frozen analysis (§ roles: F. Palomba) is carried out by one of the coauthors F. Palomba or F. Ferrucci, chosen by availability; the name is written in the protocol's signature line (`internal review:`) before the signature and is binding for that protocol. The reviewer of a protocol does not launch its runs. E13: reviewed by F. Ferrucci (three reviews of the protocol and three of the code, 2026-11-18; approval of draft 6 at 16:51).
