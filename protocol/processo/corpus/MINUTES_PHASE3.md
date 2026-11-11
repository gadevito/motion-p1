# Phase 3 — separation and deduplication minutes

Date: 2026-11-11 (Europe/Rome). Participants: **COD-01** and **COD-02**, working together in presence. 

Working commit: **af66067**, full ID `af660674c176ce356a52d6607928ce4fd670c4ae`, in both supplied clones. **The split clarification of commit 8449986, supplied verbatim by De Vito, is applied.** 

Candidate source: unchanged `protocol/processo/analisi/extract_candidates.py` and frozen inventory at the working commit. The generated `candidates.json` and `CANDIDATES.md` were absent from the checkout; they were reproduced into temporary working storage without changing repository sources. The reproduced candidate SHA-256 exactly matches the frozen value:

`ca536a86ef157201923bf80010348c662057785044922a32aedb532420b30173`

Inventory SHA-256: `187f7cde9b1858b67494d44aaa4a41cc2172a31b5bfd9cbc5fddd2573c45dfd6`. Signed P0 read at `2ab032b`, SHA-256 `9c448ef792fcbd2c2ac36fdfeba2668cf6ef5f9fa26671704e6ef94e898bfea6`; the deposited receipt and its later corrections were read at the working commit. P0 sections 4 and 8 govern the problem unit. Frozen source snapshots:

- Paper 1: `aa9f478b3fa8c53113eb6a39ca6f8b005b45f7d4`.
- Paper 4: `ef31396c28cfa931b429dfc339043f176e7e2f84`.

## Clarification and representation

Question sent by COD-01: the instruction sheet permits splitting one candidate into distinct problems but also requires exact-once candidate membership, unlike P0 section 4. May repeated memberships be used for documented splits?

Author’s answer, applied: “Yes. A split candidate is listed under every problem it supports; each repetition must match a split into n line in the minutes naming that ID. The check becomes coverage (every ID at least once; repeats only with a split line; excluded IDs nowhere else).” The author also instructed us to retain af66067 and record the clarification attributed to 8449986.

Problem IDs are allocated within P1, P4 and PC by first appearance of their earliest candidate in the actual generated **CANDIDATES.md** (its display order groups main deviations, commits, records, registers, report, then tags, followed by paper4). Ties within a split follow the order of the distinct outcomes in the review. IDs therefore need not equal register-item numbers. The register crosswalk below makes those references explicit. `paper` is paper1 or paper4; shared PC entries use paper1, where these three problems were first registered, and `shared_with` names the other paper’s register item.

A repeated candidate may be a multi-problem register row or a trace that documents several already-distinct problems (for example, a consolidated register commit). “split into n” records its n memberships without claiming n new defects. Excluded candidates occur once, including block entries. Mixed commits with a correction and routine additions are attached to the correction(s); the routine portion does not receive a second excluded entry. Pure renames are excluded as changes, even when the moved script originally corrected a problem.

We read register sources, protocol context, the unregistered commits and relevant patches, report contexts, the two required sections, tag-pair changes and their intervening commit messages. We did not consult incident-card contents to decide statuses. Candidate commit messages and register citations that mention cards remain admissible traces; no card is used as evidence for a status. Original-language source statements are paraphrased in English. No phase-5 type, introduction phase, detector or cause is assigned.

## Candidate decisions

Every repeated candidate has its own split line below. Single-candidate exclusions and nontrivial associations are explicit; uncomplicated one-problem register rows are implied by CORPUS.json.

| Candidate ID(s) | Decision | Reason | Problem ID(s) |
|---|---|---|---|
| C-main-GIT-002 | split into 2 | P1-005: Paper 1 register item 33 attributed the pairing discrepancy to two same-architecture MacBooks based on recollection; item 34 retracted that claim against the cited Spark artifacts; documents P1-006.; P1-006: The E2 pairing identity check used rtol 1e-12 on float32 aggregates and failed across machines at a maximum element difference of 4.9e-9. | P1-005, P1-006 |
| C-main-GIT-003 | split into 2 | P4-001: E10-pred compared placements using each design’s own class-weight vector.; P4-002: Item 23 and E10predbis dated the review 15:15 rather than 14:38; documents P4-001. | P4-001, P4-002 |
| C-main-GIT-006 | split into 3 | P1-008: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039.; P1-009: The manuscript congestion-threshold description did not match the Traffic4cast per-segment reference and 0.8/0.4 classes or the PEMS training-only reference and 0.8/0.5 classes.; P1-010: The manuscript-number verifier did not read section files after the manuscript was split into input files; recursive expansion was added. | P1-008, P1-009, P1-010 |
| C-main-GIT-012 | split into 3 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-013: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015. | P1-007, P1-013, P1-014 |
| C-main-GIT-013 | split into 3 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-013: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015. | P1-007, P1-013, P1-014 |
| C-main-GIT-014 | split into 3 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-013: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015. | P1-007, P1-013, P1-014 |
| C-main-GIT-020 | split into 3 | P1-006: The E2 pairing identity check used rtol 1e-12 on float32 aggregates and failed across machines at a maximum element difference of 4.9e-9.; P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-015: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week. | P1-006, P1-007, P1-015 |
| C-main-GIT-021 | split into 28 | Consolidated first register publication contains items 1–27, including separate 17a and 17b. These are distinct existing defects, not a single defect or only the regex range endpoints. All supported problems are listed in the final column. | P1-006, P1-015, P1-016, P1-017, P1-018, P1-019, PC-002, P1-020, P1-021, PC-003, P1-022, P1-023, P1-024, P1-025, P1-026, P1-027, P1-028, P1-029, P1-030, P1-031, P1-032, P1-033, P1-034, P1-035, P1-036, P1-037, P1-038, P1-039 |
| C-main-GIT-024 | split into 2 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-015: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week. | P1-007, P1-015 |
| C-main-GIT-029 | split into 2 | P1-041: The regeneration comparison rejected small numerical and printed-document differences within the adopted combined tolerance; numeric and document comparisons were aligned.; P1-042: The fingerprint index attributed a shared fingerprint to the first filesystem traversal match, yielding different source filenames on Mac and Spark. | P1-041, P1-042 |
| C-main-GIT-033 | split into 3 | P1-030: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x.; P1-031: The manuscript attributed 36.8 s and 35.7 s to F-prime at Madrid and London; they were E4 gated(48 h) times.; P1-034: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers. | P1-030, P1-031, P1-034 |
| C-main-GIT-043 | split into 4 | P1-016: One optimizer update per epoch was presented as a full epoch; 35 updates covered about 15% of one pass.; P1-017: Checkpoints were selected on the first 32 validation instants, about 2% of the validation period.; P1-044: MoGERNN runtime and profiling were measured while eight phase-E processes occupied the machine; the absolute timings and derived campaign estimates were retracted.; P1-045: Initial-state filenames omitted city and partition; nine runs with the same seed overwrote different states in one file and left manifest references pointing to replaced contents. | P1-016, P1-017, P1-044, P1-045 |
| C-main-GIT-044 | split into 3 | P1-016: One optimizer update per epoch was presented as a full epoch; 35 updates covered about 15% of one pass.; P1-017: Checkpoints were selected on the first 32 validation instants, about 2% of the validation period.; PC-003: Paper 1 used 900/900/594 nodes against documented 828/774/587; Paper 4 recorded the same discrepancy between target-file and aligned-graph populations. | P1-016, P1-017, PC-003 |
| C-main-GIT-048 | split into 4 | P1-018: A clamp assigned a valid class to missing targets, affecting 40% of London test targets.; P1-049: The first raccordo campaign trained with unweighted cross-entropy although the protocol prescribed weighted cross-entropy; the campaign was invalidated and retrained.; P1-050: The first raccordo campaign did not record its evaluation weights: reg.metrica was never called; a shared fingerprinted weight artifact and logging were added.; P1-051: The raccordo deterioration rule used the lower bound of the bilateral 90% interval without that criterion being specified in the frozen protocol; the record declared it non-preregistered. | P1-018, P1-049, P1-050, P1-051 |
| C-main-GIT-049 | split into 3 | P1-049: The first raccordo campaign trained with unweighted cross-entropy although the protocol prescribed weighted cross-entropy; the campaign was invalidated and retrained.; P1-050: The first raccordo campaign did not record its evaluation weights: reg.metrica was never called; a shared fingerprinted weight artifact and logging were added.; P1-052: The raccordo resampling reused initialization draws across repeated occurrences of a partition; the correction drew independently for each occurrence. | P1-049, P1-050, P1-052 |
| C-main-REC-006 | split into 2 | P1-013: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015. | P1-013, P1-014 |
| C-main-REG-030 | split into 4 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-013: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015.; P1-058: Regenerating E18 reproduced the analysis numbers but changed the printed part-A timings; the generator was changed to read the first-run timing register. | P1-007, P1-013, P1-014, P1-058 |
| C-main-RPT-001 | split into 2 | P1-059: At tag l-pub2 the E18 generator added a parenthesis absent from the frozen record, causing two differing text lines with all 12,299 numbers within tolerance; the parenthesis was removed at l-pub3.; P1-060: During the l-pub2 regeneration a second run was started by mistake and stopped after 35 seconds; separate workspaces left the real results unchanged. | P1-059, P1-060 |
| C-main-TAG-014 | split into 10 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-012: The E18TER regeneration phase ran only livelli, omitted wce16 and rewrote F17 with the E16 wCE; the command was changed to all parts.; P1-015: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week.; P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced.; P1-041: The regeneration comparison rejected small numerical and printed-document differences within the adopted combined tolerance; numeric and document comparisons were aligned.; P1-042: The fingerprint index attributed a shared fingerprint to the first filesystem traversal match, yielding different source filenames on Mac and Spark.; P1-043: Choice-file timestamps and timestamp-dependent fingerprints changed the supposedly deterministic comparison report between otherwise equivalent runs.; P1-058: Regenerating E18 reproduced the analysis numbers but changed the printed part-A timings; the generator was changed to read the first-run timing register.; P1-063: A second solo_testo function replaced the phase-comparison helper; regeneration stopped with AttributeError on a list argument.; P1-064: When regeneration stopped with a table KeyError, main.py did not write its comparison and report; exception handling was added to emit NON CONCLUSO. | P1-007, P1-012, P1-015, P1-035, P1-041, P1-042, P1-043, P1-058, P1-063, P1-064 |
| C-main-TAG-015 | split into 7 | P1-012: The E18TER regeneration phase ran only livelli, omitted wce16 and rewrote F17 with the E16 wCE; the command was changed to all parts.; P1-034: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers.; P1-041: The regeneration comparison rejected small numerical and printed-document differences within the adopted combined tolerance; numeric and document comparisons were aligned.; P1-042: The fingerprint index attributed a shared fingerprint to the first filesystem traversal match, yielding different source filenames on Mac and Spark.; P1-043: Choice-file timestamps and timestamp-dependent fingerprints changed the supposedly deterministic comparison report between otherwise equivalent runs.; P1-063: A second solo_testo function replaced the phase-comparison helper; regeneration stopped with AttributeError on a list argument.; P1-065: A reviewer manually added a note to generated CONFRONTO.md despite its explicit instruction not to edit by hand. | P1-012, P1-034, P1-041, P1-042, P1-043, P1-063, P1-065 |
| C-main-TAG-016 | split into 4 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-010: The manuscript-number verifier did not read section files after the manuscript was split into input files; recursive expansion was added.; P1-015: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week.; P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. | P1-007, P1-010, P1-015, P1-035 |
| C-main-TAG-017 | split into 7 | P1-007: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores.; P1-014: The first E18 part-C record reported only wCE and omitted the per-class ECE, log-loss and Brier measures required by protocol section 3; documents P1-015.; P1-015: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week.; P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced.; P1-066: F17 absolute wCE pooled weights across horizons instead of averaging the separately normalised per-horizon losses used by the manuscript.; P1-067: The F17 caption claimed every class ECE was below 0.04; it was replaced with the observed maximum computed from the printed entries.; P1-068: The E15 cost-table generator formatted absent timing values as decimal numbers; missing timing entries were changed to --. | P1-007, P1-014, P1-015, P1-035, P1-066, P1-067, P1-068 |
| C-main-TAG-043 | split into 2 | P1-072: The E14-B maximum-difference report interchanged the causal and permuted variant labels; its numerical values and locations were already correct; documents P1-035.; P1-073: The E14-B maximum-difference report omitted F0-prime and F-prime(24 h) from absolute levels and differences. | P1-072, P1-073 |
| C-main-TAG-101 | split into 2 | P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced.; P1-062: The E6 frozen report claimed every number was calculated from result files, but its PEMS04 common-origin count of 168 was hardcoded in the generator. | P1-035, P1-062 |
| C-main-TAG-105 | split into 2 | P1-033: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs.; P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. | P1-033, P1-035 |
| C-main-TAG-107 | split into 2 | P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced.; P1-037: adatta_F built its own static vector; E14 variants adapted F using the frozen vector and evaluated it using the variant vector. | P1-035, P1-037 |
| C-main-TAG-111 | split into 2 | P1-035: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced.; P1-037: adatta_F built its own static vector; E14 variants adapted F using the frozen vector and evaluated it using the variant vector. | P1-035, P1-037 |
| C-main-TAG-124 | split into 2 | P1-008: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039.; P1-009: The manuscript congestion-threshold description did not match the Traffic4cast per-segment reference and 0.8/0.4 classes or the PEMS training-only reference and 0.8/0.5 classes. | P1-008, P1-009 |
| C-main-TAG-128 | split into 2 | P1-072: The E14-B maximum-difference report interchanged the causal and permuted variant labels; its numerical values and locations were already correct; documents P1-035.; P1-073: The E14-B maximum-difference report omitted F0-prime and F-prime(24 h) from absolute levels and differences. | P1-072, P1-073 |
| C-paper4-DEV-003 | split into 2 | P4-005: P4A wrote results.json and screen outputs instead of the per-figure CSVs announced in the signed protocol.; P4-006: Frozen P4A code lacked a post-run input check; an external checker was added before the run. | P4-005, P4-006 |
| C-paper4-GIT-004 | split into 2 | P4-008: The project checker rejected hand-written biographies.tex because it had no generated-source header.; P4-009: The project checker did not recognise the supplement’s composite Markdown-and-register header without a single fingerprint. | P4-008, P4-009 |
| C-paper4-GIT-012 | split into 7 | P4-016: The Table 67 green class omitted 442,965 cells clipped at 1.5; its printed class count and correlation differed from regeneration.; P4-017: The overall Table 67 correlation +0.255 was not reproduced by the preserved script or tested cell sets.; P4-018: Table 68 neighbour-band statistics differed by 0.001–0.009 from regeneration; no preserved version or tested filter reproduced them.; P4-019: The brief counted 31 Austin sections; filtering gave 40, with 30 multi-lane sections and 29 multi-lane sections with defined AUC.; P4-020: The Austin lane–AUC correlation −0.541 (p=0.002) was not reproduced over the stated 31 sections or the corrected 29.; P4-021: The reported excluded Austin section at −45.1 prevalence points did not exist under the preserved code, whose differences were nonnegative.; P4-022: Austin 3-/4-lane prevalence differences +18.35/+9.93 were untraced and regenerated as +18.62/+9.88. | P4-016, P4-017, P4-018, P4-019, P4-020, P4-021, P4-022 |
| C-paper4-GIT-013 | split into 7 | P4-016: The Table 67 green class omitted 442,965 cells clipped at 1.5; its printed class count and correlation differed from regeneration.; P4-017: The overall Table 67 correlation +0.255 was not reproduced by the preserved script or tested cell sets.; P4-018: Table 68 neighbour-band statistics differed by 0.001–0.009 from regeneration; no preserved version or tested filter reproduced them.; P4-019: The brief counted 31 Austin sections; filtering gave 40, with 30 multi-lane sections and 29 multi-lane sections with defined AUC.; P4-020: The Austin lane–AUC correlation −0.541 (p=0.002) was not reproduced over the stated 31 sections or the corrected 29.; P4-021: The reported excluded Austin section at −45.1 prevalence points did not exist under the preserved code, whose differences were nonnegative.; P4-022: Austin 3-/4-lane prevalence differences +18.35/+9.93 were untraced and regenerated as +18.62/+9.88. | P4-016, P4-017, P4-018, P4-019, P4-020, P4-021, P4-022 |
| C-paper4-GIT-014 | split into 2 | P4-005: P4A wrote results.json and screen outputs instead of the per-figure CSVs announced in the signed protocol.; P4-006: Frozen P4A code lacked a post-run input check; an external checker was added before the run. | P4-005, P4-006 |
| C-paper4-GIT-015 | split into 4 | P4-023: The arterial AUC 0.542 was hard-coded without a source, including the derived Gini and 58%/42% gap split.; P4-024: The arterial rank correlation appeared as +0.001 in Table 68 and +0.071 in text, neither computed.; P4-025: Austin lane/section volume–occupancy correlations +0.7241/+0.2999 had no preserved generator.; P4-026: Austin AUC interquartile ranges were presented as intervals. | P4-023, P4-024, P4-025, P4-026 |
| C-paper4-GIT-016 | split into 5 | P4-023: The arterial AUC 0.542 was hard-coded without a source, including the derived Gini and 58%/42% gap split.; P4-024: The arterial rank correlation appeared as +0.001 in Table 68 and +0.071 in text, neither computed.; P4-025: Austin lane/section volume–occupancy correlations +0.7241/+0.2999 had no preserved generator.; P4-026: Austin AUC interquartile ranges were presented as intervals.; P4-027: No preserved generator computed the raw-input/reconstructed-factor correlation ratio of Table 66. | P4-023, P4-024, P4-025, P4-026, P4-027 |
| C-paper4-GIT-017 | split into 6 | P4-004: The first two isolated E9 cost measurements ran during Spotlight indexing and were replaced with idle-machine measurements.; P4-028: Three Melbourne E11 node partitions fell outside the prescribed share tolerance; preflight passed 22 of 23 checks.; P4-029: The first E11 record reported test red recall without the realised test false-alarm rate.; P4-030: The E12-bis synthetic test populated only the nearest distance bin and met its between-bin condition vacuously.; P4-031: Frozen E12 code lacked the post-run input check later supplied by verifica_e12.py.; P4-032: Frozen E12 code lacked an end-to-end self-test of its record generator. | P4-004, P4-028, P4-029, P4-030, P4-031, P4-032 |
| C-paper4-GIT-018 | split into 2 | P4-004: The first two isolated E9 cost measurements ran during Spotlight indexing and were replaced with idle-machine measurements.; P4-033: The E9 pre-registration launch field named Gabriele De Vito and was changed to Fabio Palomba. | P4-004, P4-033 |
| C-paper4-GIT-019 | split into 2 | P4-034: The E11 manuscript’s pilot wCE range ended at 1.073; corrected to 1.071.; P4-035: The E9 protocol stated that E11 recall was near the false-alarm rate without restricting that statement to Madrid. | P4-034, P4-035 |
| C-paper4-GIT-023 | split into 3 | P4-038: The geometry script searched graph names for knn and found no true/randomised pairs.; P4-039: The geometry script sought geo_<graph>_s<seed>.csv instead of the preserved city-prefixed filenames.; P4-040: The deliverable called the first Madrid geometry-control run a refutation although its 1.96-point margin made it inconclusive under the script’s rule. | P4-038, P4-039, P4-040 |
| C-paper4-GIT-024 | split into 2 | P4-041: Randomised geometry-control graphs used their new geographic distances and their own kernel scale as weights.; P4-042: The three preserved randomised geometry-control graphs were disconnected. | P4-041, P4-042 |
| C-paper4-GIT-025 | split into 3 | PC-002: Windows built by row index crossed calendar gaps; 2.6% of origins were excluded by the corrected admissibility rule.; PC-003: Paper 1 used 900/900/594 nodes against documented 828/774/587; Paper 4 recorded the same discrepancy between target-file and aligned-graph populations.; P4-043: Loop-context free-flow reference used the speed percentile of the whole year, including the test period. | PC-002, PC-003, P4-043 |
| C-paper4-REC-003 | split into 4 | P4-023: The arterial AUC 0.542 was hard-coded without a source, including the derived Gini and 58%/42% gap split.; P4-024: The arterial rank correlation appeared as +0.001 in Table 68 and +0.071 in text, neither computed.; P4-025: Austin lane/section volume–occupancy correlations +0.7241/+0.2999 had no preserved generator.; P4-026: Austin AUC interquartile ranges were presented as intervals. | P4-023, P4-024, P4-025, P4-026 |
| C-paper4-REC-004 | split into 2 | P4-016: The Table 67 green class omitted 442,965 cells clipped at 1.5; its printed class count and correlation differed from regeneration.; P4-017: The overall Table 67 correlation +0.255 was not reproduced by the preserved script or tested cell sets. | P4-016, P4-017 |
| C-paper4-REC-005 | split into 4 | P4-019: The brief counted 31 Austin sections; filtering gave 40, with 30 multi-lane sections and 29 multi-lane sections with defined AUC.; P4-020: The Austin lane–AUC correlation −0.541 (p=0.002) was not reproduced over the stated 31 sections or the corrected 29.; P4-021: The reported excluded Austin section at −45.1 prevalence points did not exist under the preserved code, whose differences were nonnegative.; P4-022: Austin 3-/4-lane prevalence differences +18.35/+9.93 were untraced and regenerated as +18.62/+9.88. | P4-019, P4-020, P4-021, P4-022 |
| C-paper4-REG-004 | split into 2 | P4-038: The geometry script searched graph names for knn and found no true/randomised pairs.; P4-039: The geometry script sought geo_<graph>_s<seed>.csv instead of the preserved city-prefixed filenames. | P4-038, P4-039 |
| C-paper4-REG-005 | split into 2 | P4-027: No preserved generator computed the raw-input/reconstructed-factor correlation ratio of Table 66.; P4-046: The --exclude-empty and --max-dist 30 cross-validation outputs were not preserved. | P4-027, P4-046 |
| C-paper4-REG-006 | split into 2 | P4-047: The rand_k1, rand_k2 and identity Madrid graphs had no generator in the searched repository or histories.; P4-048: The ten rand-k runs named in randk.log had no preserved result CSVs. | P4-047, P4-048 |
| C-paper4-REG-007 | split into 2 | P4-041: Randomised geometry-control graphs used their new geographic distances and their own kernel scale as weights.; P4-042: The three preserved randomised geometry-control graphs were disconnected. | P4-041, P4-042 |
| C-paper4-REG-013 | split into 2 | P4-031: Frozen E12 code lacked the post-run input check later supplied by verifica_e12.py.; P4-032: Frozen E12 code lacked an end-to-end self-test of its record generator. | P4-031, P4-032 |
| C-paper4-REG-018 | split into 2 | P4-016: The Table 67 green class omitted 442,965 cells clipped at 1.5; its printed class count and correlation differed from regeneration.; P4-017: The overall Table 67 correlation +0.255 was not reproduced by the preserved script or tested cell sets. | P4-016, P4-017 |
| C-paper4-REG-020 | split into 4 | P4-019: The brief counted 31 Austin sections; filtering gave 40, with 30 multi-lane sections and 29 multi-lane sections with defined AUC.; P4-020: The Austin lane–AUC correlation −0.541 (p=0.002) was not reproduced over the stated 31 sections or the corrected 29.; P4-021: The reported excluded Austin section at −45.1 prevalence points did not exist under the preserved code, whose differences were nonnegative.; P4-022: Austin 3-/4-lane prevalence differences +18.35/+9.93 were untraced and regenerated as +18.62/+9.88. | P4-019, P4-020, P4-021, P4-022 |
| C-paper4-RPT-001 | split into 2 | P4-008: The project checker rejected hand-written biographies.tex because it had no generated-source header.; P4-009: The project checker did not recognise the supplement’s composite Markdown-and-register header without a single fingerprint. | P4-008, P4-009 |
| C-main-GIT-008 | excluded | Adds the optional text-only verification mode; no existing mismatch established by this commit. | P1-011 |
| C-main-GIT-022 | excluded | Adds English documentation and register translations; no new correction. | P1-040 |
| C-main-GIT-045 | excluded | Adds final audit qualification and engineering interpretation; no demonstrated prior incorrect result. | P1-046 |
| C-main-GIT-046 | excluded | Records a new confirmation result, including an inconclusive context; failing a scientific criterion is not a defect. | P1-047 |
| C-main-REC-001, C-main-REC-015 | excluded, block | Known extraction residues in NOTE_CANDIDATES.md; the E8 deviation is represented by DEV-005/REC-016. | P1-054 |
| C-main-REC-007 | excluded | Explicit protocol-conforming applicability note; no defect, deviation or violation. | P1-056 |
| C-main-TAG-001..C-main-TAG-501 (statuses [A] only; 426 IDs individually enumerated below) | excluded, block | Addition-only tag traces, not corrections. The inspected list includes seven frozen records and seven experiment protocols; these are additions too. Problems described by their contents are considered through the other candidates and required section reads. | P1-061 |
| C-main-TAG-018 | excluded | No correction: adds an input-scope clarification without a changed analysis. | P1-069 |
| C-main-TAG-023, C-main-TAG-024, C-main-TAG-033, C-main-TAG-034 | excluded, block | No correction: presentation and notation updates; no changed computation or stated prior false outcome. | P1-070 |
| C-main-TAG-041, C-main-TAG-042, C-main-TAG-498, C-main-TAG-499 | excluded, block | No correction: normal packaging of the next release and optional tooling. | P1-071 |
| C-main-TAG-046, C-main-TAG-049, C-main-TAG-050, C-main-TAG-051, C-main-TAG-052, C-main-TAG-053, C-main-TAG-054, C-main-TAG-060, C-main-TAG-061, C-main-TAG-062, C-main-TAG-063, C-main-TAG-067, C-main-TAG-070, C-main-TAG-071, C-main-TAG-073, C-main-TAG-074, C-main-TAG-075, C-main-TAG-076, C-main-TAG-077 | excluded, block | No correction in these tag changes: pure relocations of existing patch scripts, whose underlying fixes are not counted again. | P1-074 |
| C-paper4-DEV-001 | excluded | Cross-reference only; real cost episode is DEV-002 / REG-011. Instruction example reverses IDs. | P4-003 |
| C-paper4-GIT-008 | excluded | Pre-signature specification refinements; no run or contrary result described. | P4-012 |
| C-paper4-GIT-010 | excluded | Editorial organisation, bibliography and build changes. register_ref 1/13 is a regex artefact of ranges 1–3 and 8–13, not a new fix to items 1 and 13. | P4-014 |
| C-paper4-GIT-011 | excluded | Routine drafting/typesetting and status update; commit does not correct a distinct prior defect. | P4-015 |
| C-paper4-GIT-022 | excluded | Fixed means established in advance; planned diagnostic extension, not a defect correction. | P4-037 |
| C-paper4-REC-002 | excluded | Successful prescribed control; the new out-of-sample evaluation is a specification change with no established contrary outcome in this candidate. | P4-044 |
| C-paper4-REC-007 | excluded | Documented diagnostic confirms expected empty hidden rows, not a defective output. | P4-045 |
| C-paper4-REG-021 | excluded | Declared existing design choice; no requirement to persist weights established. The false checkpoint claim is counted separately from GIT-009. | P4-049 |
| C-main-DEV-005, C-main-GIT-041, C-main-REC-016 | 1 problem | Despite the deviation label, the pilot outcome contradicted the prescribed validation; classify the underlying mismatch as defect. | P1-004 |
| C-main-GIT-001, C-main-GIT-002, C-main-REG-034, C-main-REG-035 | 1 problem | One documentary defect in item 33, retracted by item 34; separate from the pairing check in P1-006. | P1-005 |
| C-main-GIT-003, C-paper4-GIT-001, C-paper4-REG-026 | 1 problem | Paper 4 GIT-001 corrects the documentary review time, not the scoring calculation; main GIT-003 also names the scoring problem and is split between the two. | P4-002 |
| C-main-GIT-005, C-main-REG-033, C-paper4-GIT-002, C-paper4-REG-025 | shared with | Shared with Paper 4 register item 25; both registers explicitly identify the same problem. | PC-001 |
| C-main-GIT-006 and associated traces in CORPUS.json | 1 problem | Historical tool-name wording in register item 30 is propagation of item 28, not a second defect. Register item 30 also describes removing an old manuscript copy: publication cleanup, not an additional problem; no excluded entry shares the retained candidate. | P1-008 |
| C-main-GIT-006, C-main-TAG-016 | 1 problem | Recursive source expansion now includes sections; output formatting refinements in same diff do not add defects. | P1-010 |
| C-main-GIT-011, C-main-TAG-014, C-main-TAG-015 | 1 problem | TAG014 actual fix, TAG015 records successful full regeneration at 217624d. | P1-012 |
| C-main-GIT-012, C-main-GIT-013, C-main-GIT-014, C-main-REC-006, C-main-REG-030, C-main-TAG-017 | 1 problem | F17 missing metrics filled when medie_settimana available | P1-014 |
| C-main-GIT-018 and associated traces in CORPUS.json | 1 problem | Existing P1-015; supplementary causal-window replacements explicitly labelled correction27. | P1-015 |
| C-main-GIT-021, C-main-REC-017, C-main-REG-005, C-paper4-GIT-025, C-paper4-REG-001 | shared with | Shared with Paper 4 register item 1; both registers explicitly identify the same problem. | PC-002 |
| C-main-GIT-021, C-main-GIT-044, C-main-REG-008, C-paper4-GIT-025, C-paper4-REG-003 | shared with | Shared with Paper 4 register item 3; both registers explicitly identify the same problem. The registers describe opposite sides of the same explicitly shared target-versus-aligned population difference; no additional contradiction is inferred. | PC-003 |
| C-main-GIT-021 and associated traces in CORPUS.json | 1 problem | TAG015 first diff replaces DIVERSO E5 text rows with identical regenerated reference. This is a further trace of the same correction. | P1-034 |
| C-main-GIT-021 and associated traces in CORPUS.json | 1 problem | Integration and tables of E14/E15 correction; not a new problem for every added table. | P1-035 |
| C-main-GIT-029, C-main-TAG-014, C-main-TAG-015 | 1 problem | TAG013 is hash-only, do not attach tolerance there. | P1-041 |
| C-main-GIT-029, C-main-TAG-013, C-main-TAG-014, C-main-TAG-015 | 1 problem | TAG013 contains actual source-priority fix, TAG014 integration and TAG015 report changes. | P1-042 |
| C-main-GIT-032, C-main-TAG-014, C-main-TAG-015 | 1 problem | The commit calls this a choice, but its before/after evidence describes failure of the deterministic-report output; defect under P0 section 4. Before report explicitly promised no volatile metadata; commit choice label does not override observed mismatch. | P1-043 |
| C-main-GIT-043 | 1 problem | c25495c canonico.py documents different-content overwrites; separate from state-register and phase-summary overwrites. | P1-045 |
| C-main-GIT-047 | 1 problem | Different output and launch from register item 11: state-index overwrite versus phase-summary overwrite. | P1-048 |
| C-main-GIT-048 | 1 problem | Declared added criterion, with no claimed preregistration; distinct from the invalidated training campaigns. | P1-051 |
| C-main-REC-005 | 1 problem | Separate E16 protocol/calibration mismatch from the E8 threshold problem; E16 source section 1 specified validation probabilities for A. | P1-055 |
| C-main-REG-030, C-main-TAG-014 | 1 problem | Timing metadata treatment in main.py accompanies recorded timing correction; source time tables remain separate from computed quantities. | P1-058 |
| C-main-RPT-001 | 1 problem | Separate erroneous launch explicitly recorded in the report dated note, distinct from the prose mismatch. | P1-060 |
| C-main-TAG-012, C-main-TAG-101 | 1 problem | The original universal provenance claim contradicts the literal 168 in genera_congelamento_e6.py; the correction reads a new result-derived JSON. Value remains 168; this is a provenance defect, not a wrong numeric count. Later checker coverage additions alone remain enhancements. | P1-062 |
| C-main-TAG-014, C-main-TAG-015 | 1 problem | Explicit failed run and corrective rename in commit and audit patch; TAG015 records corrected 6403e7a verification. Distinct from adding text-only mode. | P1-063 |
| C-main-TAG-014 | 1 problem | Commit explicitly records interrupted 29 October run and adds required report generation; missing-input preflight introduced alongside it is preventive enhancement, not separate defect. | P1-064 |
| C-main-TAG-015 | 1 problem | The existing header says non modificare a mano and added text identifies itself as nota aggiunta a mano. Unchanged numbers do not remove the process-rule breach. | P1-065 |
| C-main-TAG-017 | 1 problem | Explicit before/after definition in table caption and frozen CONGELAMENTO_E18TER §3; distinct from P1-015 causal-window defect and E18TER command omission. | P1-066 |
| C-main-TAG-017 | 1 problem | protocol/E18ter §2 explicitly calls replacement valore vero; same correction confirmed frozen record §2. Figures unchanged does not exclude erroneous caption. | P1-067 |
| C-main-TAG-017 | 1 problem | Before code formats None with :.1f, after code explicitly handles missing logs. Distinct from estimating cost or measuring under load. | P1-068 |
| C-paper4-DEV-002, C-paper4-GIT-017, C-paper4-GIT-018, C-paper4-REC-008, C-paper4-REG-011 | 1 problem | The original isolated-cost outcome was contaminated; a dated correction is not by itself a deviation. | P4-004 |
| C-paper4-DEV-003, C-paper4-GIT-014 | 1 problem | Dated choice recorded after signature and before run; output representation changed, all figures still recorded. | P4-005 |
| C-paper4-DEV-003, C-paper4-GIT-014 | 1 problem | Distinct missing control from the declared CSV representation change; same pattern as E12 but separate frozen implementation. | P4-006 |
| C-paper4-GIT-003 | 1 problem | Before/after parsing correction documented by commit fe81f459; supplementary provenance checks added alongside it are enhancements, not extra defects. | P4-007 |
| C-paper4-GIT-004, C-paper4-RPT-001 | 1 problem | False positive: identical manuscript passes 16 seconds later after headerless files are accepted. | P4-008 |
| C-paper4-GIT-004, C-paper4-RPT-001 | 1 problem | Distinct header grammar case: optional and-the-register and dash fingerprint handling; same manuscript passes corrected checker. | P4-009 |
| C-paper4-GIT-009 | 1 problem | False documentary claim corrected separately from the legitimate unsaved-state design choice. | P4-013 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-004, C-paper4-REG-018 | 1 problem | One boundary omission explains both green-class outcomes; overall correlation does not follow from this correction. | P4-016 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-004, C-paper4-REG-018 | 1 problem | Separate unreproduced overall statistic, not resolved by the green-class boundary. | P4-017 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REG-019 | 1 problem | Keep one comparison discrepancy; no evidence supports separate underlying errors for each statistic or band. | P4-018 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-005, C-paper4-REG-020 | 1 problem | Population-definition discrepancy separated from unreproduced values. | P4-019 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-001, C-paper4-REC-005, C-paper4-REG-020 | 1 problem | Correlation recomputation distinct from section count and prevalence quantities. | P4-020 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-005, C-paper4-REG-020 | 1 problem | Distinct impossible exclusion claim, not a correlation or population count. | P4-021 |
| C-paper4-GIT-012, C-paper4-GIT-013, C-paper4-REC-005, C-paper4-REG-020 | 1 problem | One paired prevalence-table discrepancy; separate correction from correlation/exclusion claim. | P4-022 |
| C-paper4-GIT-015, C-paper4-GIT-016, C-paper4-REC-003, C-paper4-REG-014 | 1 problem | Derived Gini and gap split propagate the same untraced AUC; do not multiply. | P4-023 |
| C-paper4-GIT-015, C-paper4-GIT-016, C-paper4-REC-003, C-paper4-REG-015 | 1 problem | Two contradictory values of one quantity corrected by one declared recomputation. | P4-024 |
| C-paper4-GIT-015, C-paper4-GIT-016, C-paper4-REC-003, C-paper4-REG-016 | 1 problem | One undocumented lane-to-section correlation comparison, recomputed jointly. | P4-025 |
| C-paper4-GIT-016, C-paper4-REG-005 | 1 problem | Generator absent; distinct from missing outputs of existing commands. | P4-027 |
| C-paper4-GIT-017, C-paper4-REG-013 | 1 problem | Separate check-inputs command from end-to-end self-test. | P4-031 |
| C-paper4-GIT-017, C-paper4-REG-013 | 1 problem | Separate test command and distinct coverage from the post-run input check. | P4-032 |
| C-paper4-GIT-018 | 1 problem | Separate attribution correction in the same commit as cost remeasurement; no role violation inferred. | P4-033 |
| C-paper4-GIT-019 | 1 problem | Numeric statement changed; not merely routine wording. | P4-034 |
| C-paper4-GIT-019 | 1 problem | Correction narrows the empirical claim to the city supported by the record. | P4-035 |
| C-paper4-GIT-023, C-paper4-REG-004 | 1 problem | Separate graph-matching predicate and CSV-path fixes. | P4-038 |
| C-paper4-GIT-023, C-paper4-REG-004 | 1 problem | Separate CSV lookup defect from graph pairing. | P4-039 |
| C-paper4-GIT-023 | 1 problem | Distinct reading of the result; graph/CSV pairing fixes reproduce the numbers and do not resolve this interpretation mismatch. | P4-040 |
| C-paper4-GIT-024, C-paper4-REG-007 | 1 problem | Weight matching and connectivity require distinct corrections. | P4-041 |
| C-paper4-GIT-024, C-paper4-REG-007 | 1 problem | Connectivity preservation is separate from replacing weights. | P4-042 |
| C-paper4-REG-005 | 1 problem | Existing commands were rerun to restore outputs; Table 66 still lacked a generator. | P4-046 |
| C-paper4-REG-006 | 1 problem | One missing generation provenance covering related graph files. | P4-047 |
| C-paper4-REG-006 | 1 problem | Missing result files are separate from graph-generator provenance. | P4-048 |
| C-main-DEV-002 | duplicate of | Same problem: E4 declared an adaptation-duration grid of 6 h, 12 h, 24 h, 48 h and one week instead of durations including 1 h and 4 h. Source: protocol/E4.md, line 52 (text pattern). | P1-002 |
| C-main-DEV-003 | duplicate of | Same problem: E5 used six rather than eight seeds, confirmed by the reviewer on 4 October after the precision comparison. Source: protocol/E5.md, line 142 (text pattern). | P1-003 |
| C-main-DEV-004 | duplicate of | Same problem: E5 used six rather than eight seeds, confirmed by the reviewer on 4 October after the precision comparison. Source: protocol/E5.md, line 150 (text pattern). | P1-003 |
| C-main-DEV-005 | duplicate of | Same problem: E8 prescribed evaluating A on validation nodes, but A had embeddings only for initial and test nodes; the pilot raised NodoNonRegistrato and A inherited C thresholds. Source: protocol/E8.md, line 85 (text pattern). | P1-004 |
| C-main-GIT-001 | duplicate of | Same problem: Paper 1 register item 33 attributed the pairing discrepancy to two same-architecture MacBooks based on recollection; item 34 retracted that claim against the cited Spark artifacts; documents P1-006. Source: git history, commit 207f23f435b1, 2026-11-10T16:38:36+01:00. | P1-005 |
| C-main-GIT-004 | duplicate of | Same problem: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores. Source: git history, commit ca99ef25c2f1, 2026-11-10T15:49:23+01:00. | P1-007 |
| C-main-GIT-005 | duplicate of | Same problem: The public repository tracked the complete MoGERNN third-party code although its upstream repository declared no licence; the tracked copy was removed. Source: git history, commit 0a4a33a786e2, 2026-11-10T12:28:49+01:00. | PC-001 |
| C-main-GIT-007 | duplicate of | Same problem: The manuscript congestion-threshold description did not match the Traffic4cast per-segment reference and 0.8/0.4 classes or the PEMS training-only reference and 0.8/0.5 classes. Source: git history, commit b4ab62a8c3b0, 2026-11-03T12:38:32+01:00. | P1-009 |
| C-main-GIT-009 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit 8b177d20dc11, 2026-10-31T21:00:56+01:00. | P1-008 |
| C-main-GIT-010 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit f0431247e5ef, 2026-10-31T11:42:55+01:00. | P1-008 |
| C-main-GIT-011 | duplicate of | Same problem: The E18TER regeneration phase ran only livelli, omitted wce16 and rewrote F17 with the E16 wCE; the command was changed to all parts. Source: git history, commit 217624d6f28c, 2026-10-30T13:51:10+01:00. | P1-012 |
| C-main-GIT-015 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit 7d5aa3fa7547, 2026-10-29T10:36:04+01:00. | P1-008 |
| C-main-GIT-016 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit 1a3381f57999, 2026-10-29T10:30:15+01:00. | P1-008 |
| C-main-GIT-017 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit 2d4bb450213b, 2026-10-29T10:29:31+01:00. | P1-008 |
| C-main-GIT-018 | duplicate of | Same problem: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week. Source: git history, commit 30e15b872607, 2026-10-29T10:17:03+01:00. | P1-015 |
| C-main-GIT-019 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: git history, commit db06fa303df5, 2026-10-29T10:14:34+01:00. | P1-008 |
| C-main-GIT-023 | duplicate of | Same problem: E16 evaluated F-prime(1 week) on origins in its first week despite the embedding using that week of data; E18 recomputed on origins older than one week. Source: git history, commit d7b9f509ce6f, 2026-10-28T21:32:53+01:00. | P1-015 |
| C-main-GIT-025 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: git history, commit cc286a819da1, 2026-10-15T08:59:04+02:00. | P1-035 |
| C-main-GIT-026 | duplicate of | Same problem: The E6 class-frequency table used an earlier weight-file set and only three of six PEMS08 partitions. Source: git history, commit 6f672454afe7, 2026-10-15T08:14:26+02:00. | P1-036 |
| C-main-GIT-027 | duplicate of | Same problem: The E14-B generator marked identical (tau,N) choices different because it also compared validation wCE values differing by about 1e-9. Source: git history, commit 1ce57696561d, 2026-10-15T08:06:02+02:00. | P1-039 |
| C-main-GIT-028 | duplicate of | Same problem: The E6 class-frequency table used an earlier weight-file set and only three of six PEMS08 partitions. Source: git history, commit f90ceafe78b0, 2026-10-13T21:13:16+02:00. | P1-036 |
| C-main-GIT-030 | duplicate of | Same problem: The E2 pairing identity check used rtol 1e-12 on float32 aggregates and failed across machines at a maximum element difference of 4.9e-9. Source: git history, commit 3a20a945b1c1, 2026-10-12T22:09:05+02:00. | P1-006 |
| C-main-GIT-031 | duplicate of | Same problem: The E2 pairing identity check used rtol 1e-12 on float32 aggregates and failed across machines at a maximum element difference of 4.9e-9. Source: git history, commit 01af3f7ac40e, 2026-10-12T20:05:54+02:00. | P1-006 |
| C-main-GIT-032 | duplicate of | Same problem: Choice-file timestamps and timestamp-dependent fingerprints changed the supposedly deterministic comparison report between otherwise equivalent runs. Source: git history, commit c58df00f376b, 2026-10-12T08:21:10+02:00. | P1-043 |
| C-main-GIT-034 | duplicate of | Same problem: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers. Source: git history, commit 25af2ef00a9c, 2026-10-11T22:03:39+02:00. | P1-034 |
| C-main-GIT-035 | duplicate of | Same problem: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers. Source: git history, commit 03bcece3ecf2, 2026-10-11T22:03:39+02:00. | P1-034 |
| C-main-GIT-036 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: git history, commit e824dbee4dc2, 2026-10-10T18:15:50+02:00. | P1-033 |
| C-main-GIT-037 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: git history, commit db9f8f3b1c24, 2026-10-10T18:15:50+02:00. | P1-033 |
| C-main-GIT-038 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: git history, commit d8ef81299651, 2026-10-10T18:09:49+02:00. | P1-033 |
| C-main-GIT-039 | duplicate of | Same problem: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x. Source: git history, commit 416be4e23c1e, 2026-10-10T16:19:45+02:00. | P1-030 |
| C-main-GIT-040 | duplicate of | Same problem: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x. Source: git history, commit 05b1be7ccc2b, 2026-10-10T16:01:25+02:00. | P1-030 |
| C-main-GIT-041 | duplicate of | Same problem: E8 prescribed evaluating A on validation nodes, but A had embeddings only for initial and test nodes; the pilot raised NodoNonRegistrato and A inherited C thresholds. Source: git history, commit d90f9e09aab6, 2026-10-09T16:36:13+02:00. | P1-004 |
| C-main-GIT-042 | duplicate of | Same problem: The predictor was constructed with nine channels regardless of source and failed on PEMS. Source: git history, commit 6629f40fd549, 2026-10-08T07:25:20+02:00. | P1-026 |
| C-main-REC-002 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: CONGELAMENTO_E14.md, line 118. | P1-035 |
| C-main-REC-003 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: CONGELAMENTO_E14B.md, line 5. | P1-008 |
| C-main-REC-004 | duplicate of | Same problem: The E14-B generator marked identical (tau,N) choices different because it also compared validation wCE values differing by about 1e-9. Source: CONGELAMENTO_E14B.md, line 342. | P1-039 |
| C-main-REC-008 | duplicate of | Same problem: E18 section 1 referred to register item 28 for the 19-threshold AUC correction, although that number was assigned to role-name notes; the correction is item 29; documents P1-007. Source: CONGELAMENTO_E18.md, line 343. | P1-013 |
| C-main-REC-009 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: CONGELAMENTO_E3.md, line 102. | P1-033 |
| C-main-REC-010 | duplicate of | Same problem: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x. Source: CONGELAMENTO_E3bis.md, line 47. | P1-030 |
| C-main-REC-011 | duplicate of | Same problem: E4 declared an adaptation-duration grid of 6 h, 12 h, 24 h, 48 h and one week instead of durations including 1 h and 4 h. Source: CONGELAMENTO_E4.md, line 121. | P1-002 |
| C-main-REC-013 | duplicate of | Same problem: E5 used six rather than eight seeds, confirmed by the reviewer on 4 October after the precision comparison. Source: CONGELAMENTO_E5.md, line 129. | P1-003 |
| C-main-REC-014 | duplicate of | Same problem: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers. Source: CONGELAMENTO_E5.md, line 136. | P1-034 |
| C-main-REC-016 | duplicate of | Same problem: E8 prescribed evaluating A on validation nodes, but A had embeddings only for initial and test nodes; the pilot raised NodoNonRegistrato and A inherited C thresholds. Source: CONGELAMENTO_E8.md, line 274. | P1-004 |
| C-main-REC-017 | duplicate of | Same problem: Windows built by row index crossed calendar gaps; 2.6% of origins were excluded by the corrected admissibility rule. Source: CONGELAMENTO_E_F_PIPELINE_PRECEDENTE.md, line 3. | PC-002 |
| C-main-REG-005 | shared with | Same problem: Windows built by row index crossed calendar gaps; 2.6% of origins were excluded by the corrected admissibility rule. Source: protocol/REGISTRO_CORREZIONI.md, line 27, item 5. | PC-002 |
| C-main-REG-008 | shared with | Same problem: Paper 1 used 900/900/594 nodes against documented 828/774/587; Paper 4 recorded the same discrepancy between target-file and aligned-graph populations. Source: protocol/REGISTRO_CORREZIONI.md, line 30, item 8. | PC-003 |
| C-main-REG-033 | shared with | Same problem: The public repository tracked the complete MoGERNN third-party code although its upstream repository declared no licence; the tracked copy was removed. Source: protocol/REGISTRO_CORREZIONI.md, line 55, item 32. | PC-001 |
| C-main-REG-035 | duplicate of | Same problem: Paper 1 register item 33 attributed the pairing discrepancy to two same-architecture MacBooks based on recollection; item 34 retracted that claim against the cited Spark artifacts; documents P1-006. Source: protocol/REGISTRO_CORREZIONI.md, line 57, item 34. | P1-005 |
| C-main-TAG-002 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: CONGELAMENTO_E14B.md, 2 tag pair(s). | P1-008 |
| C-main-TAG-009 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: CONGELAMENTO_E3.md, 1 tag pair(s). | P1-033 |
| C-main-TAG-010 | duplicate of | Same problem: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x. Source: CONGELAMENTO_E3bis.md, 1 tag pair(s). | P1-030 |
| C-main-TAG-011 | duplicate of | Same problem: The E5 record sentence about E3-bis changed with the experiments present when regenerated, despite identical numbers. Source: CONGELAMENTO_E5.md, 1 tag pair(s). | P1-034 |
| C-main-TAG-012 | duplicate of | Same problem: The E6 frozen report claimed every number was calculated from result files, but its PEMS04 common-origin count of 168 was hardcoded in the generator. Source: CONGELAMENTO_E6.md, 1 tag pair(s). | P1-062 |
| C-main-TAG-013 | duplicate of | Same problem: The fingerprint index attributed a shared fingerprint to the first filesystem traversal match, yielding different source filenames on Mac and Spark. Source: analysis/impronte.py, 4 tag pair(s). | P1-042 |
| C-main-TAG-020 | duplicate of | Same problem: Correction notes named a working tool rather than the role that found the defect; the role wording was propagated through the historical versions; documents corrections including P1-035, P1-036 and P1-039. Source: evoluzione/analisi/analizza_e18.py, 2 tag pair(s). | P1-008 |
| C-main-TAG-022 | duplicate of | Same problem: E3 visit counts included nine isolated timing remeasurements, reporting 117 rather than 108 runs. Source: evoluzione/analisi/analizza_e3.py, 1 tag pair(s). | P1-033 |
| C-main-TAG-031 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/analisi/figura2_51.py, 3 tag pair(s). | P1-035 |
| C-main-TAG-035 | duplicate of | Same problem: The E6 class-frequency table used an earlier weight-file set and only three of six PEMS08 partitions. Source: evoluzione/analisi/frequenze_classi.py, 1 tag pair(s). | P1-036 |
| C-main-TAG-039 | duplicate of | Same problem: The E2 pairing identity check used rtol 1e-12 on float32 aggregates and failed across machines at a maximum element difference of 4.9e-9. Source: evoluzione/analisi/verifica_appaiamento.py, 1 tag pair(s). | P1-006 |
| C-main-TAG-079 | duplicate of | Same problem: At tag p, predizioni_e18quater was classified as other and excluded from the regeneration archive manifest despite being an input to regeneration. Source: evoluzione/audit/ripartizione_results.py, 2 tag pair(s). | P1-075 |
| C-main-TAG-081 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/componente/bracci.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-082 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/componente/episodio.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-083 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/componente/valutazione.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-084 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/addestramento.py, 2 tag pair(s). | P1-035 |
| C-main-TAG-085 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/collauda_bracci.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-086 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/collauda_protocolli.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-088 | duplicate of | Same problem: The E3-bis generator divided the pooled-city R-orig median by the Melbourne-only F-prime time and reported at least 6x. Source: evoluzione/esperimenti/costi_appaiati.py, 3 tag pair(s). | P1-030 |
| C-main-TAG-089 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/costi_e4.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-092 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_E.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-096 | duplicate of | Same problem: E8-bis AUC was computed on 19 fixed thresholds; E18 reevaluated the claims on the empirical ROC over all distinct scores. Source: evoluzione/esperimenti/esegui_e16.py, 2 tag pair(s). | P1-007 |
| C-main-TAG-098 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_e2.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-099 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_e4.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-100 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_e5.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-102 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_e6a.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-103 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_e8.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-104 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_f0.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-106 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/esegui_refresh.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-112 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/riselezione_rmon_test.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-113 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/seleziona_F.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-114 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/sensibilita_rho_e2.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-115 | duplicate of | Same problem: The static branch used sensor coverage over the full series, including test data; causal inputs were introduced. Source: evoluzione/esperimenti/veterani_e3.py, 1 tag pair(s). | P1-035 |
| C-main-TAG-123 | duplicate of | Same problem: The E6 class-frequency table used an earlier weight-file set and only three of six PEMS08 partitions. Source: protocol/E6.md, 1 tag pair(s). | P1-036 |
| C-main-TAG-500 | duplicate of | Same problem: At tag p, predizioni_e18quater was classified as other and excluded from the regeneration archive manifest despite being an input to regeneration. Source: protocol/zenodo/RIPARTIZIONE_RESULTS.md, 2 tag pair(s). | P1-075 |
| C-main-TAG-501 | duplicate of | Same problem: At tag p, predizioni_e18quater was classified as other and excluded from the regeneration archive manifest despite being an input to regeneration. Source: protocol/zenodo/RIPARTIZIONE_RESULTS_spark.md, 2 tag pair(s). | P1-075 |
| C-paper4-DEV-002 | duplicate of | Same problem: The first two isolated E9 cost measurements ran during Spotlight indexing and were replaced with idle-machine measurements. Source: protocol/paper4/E9.md, line 288 (heading). | P4-004 |
| C-paper4-GIT-001 | duplicate of | Same problem: Item 23 and E10predbis dated the review 15:15 rather than 14:38; documents P4-001. Source: git history, commit ef31396c28cf, 2026-11-10T16:19:14+01:00. | P4-002 |
| C-paper4-GIT-002 | duplicate of | Same problem: The public repository tracked the complete MoGERNN third-party code although its upstream repository declared no licence; the tracked copy was removed. Source: git history, commit a9710f1701d1, 2026-11-10T12:31:19+01:00. | PC-001 |
| C-paper4-GIT-005 | duplicate of | Same problem: Section VI lacked a provenance list identifying the versions of its supporting files. Source: git history, commit 17ad609cd0e9, 2026-11-10T09:14:05+01:00. | P4-010 |
| C-paper4-GIT-006 | duplicate of | Same problem: E10-pred compared placements using each design’s own class-weight vector. Source: git history, commit b05df6edf9dd, 2026-11-09T15:18:25+01:00. | P4-001 |
| C-paper4-GIT-007 | duplicate of | Same problem: E12-ter fallback removed the calendar from the neighbour table while retaining it in the calendar-only comparator. Source: git history, commit 9421197566bf, 2026-11-09T14:39:10+01:00. | P4-011 |
| C-paper4-GIT-020 | duplicate of | Same problem: The E11 record generator reordered axes during red-recall indexing and stopped with IndexError before producing output. Source: git history, commit 4fd7fe173feb, 2026-11-06T21:38:31+01:00. | P4-036 |
| C-paper4-GIT-021 | duplicate of | Same problem: The E11 record generator reordered axes during red-recall indexing and stopped with IndexError before producing output. Source: git history, commit b2863c98c07d, 2026-11-06T19:02:25+01:00. | P4-036 |
| C-paper4-REC-001 | duplicate of | Same problem: The Austin lane–AUC correlation −0.541 (p=0.002) was not reproduced over the stated 31 sections or the corrected 29. Source: paper4/congelamenti/CONGELAMENTO_4A.md, line 59. | P4-020 |
| C-paper4-REC-006 | duplicate of | Same problem: E10-pred compared placements using each design’s own class-weight vector. Source: paper4/congelamenti/CONGELAMENTO_E10predbis.md, line 34. | P4-001 |
| C-paper4-REC-008 | duplicate of | Same problem: The first two isolated E9 cost measurements ran during Spotlight indexing and were replaced with idle-machine measurements. Source: paper4/congelamenti/CONGELAMENTO_E9.md, line 89. | P4-004 |
| C-paper4-REG-001 | shared with | Same problem: Windows built by row index crossed calendar gaps; 2.6% of origins were excluded by the corrected admissibility rule. Source: protocol/paper4/REGISTRO_CORREZIONI.md, line 17, item 1. | PC-002 |
| C-paper4-REG-003 | shared with | Same problem: Paper 1 used 900/900/594 nodes against documented 828/774/587; Paper 4 recorded the same discrepancy between target-file and aligned-graph populations. Source: protocol/paper4/REGISTRO_CORREZIONI.md, line 19, item 3. | PC-003 |
| C-paper4-REG-025 | shared with | Same problem: The public repository tracked the complete MoGERNN third-party code although its upstream repository declared no licence; the tracked copy was removed. Source: protocol/paper4/REGISTRO_CORREZIONI.md, line 41, item 25. | PC-001 |

## Joint discussion and boundary decisions

- E8’s label “deviation” does not govern status: its pilot failed the prescribed A-validation operation. E16 separately prescribed A-validation probabilities and calibration again (protocol/E16.md lines 7–9); its uncalibrated-A output is a distinct discrepancy. Both coders agreed on defect status. E4’s two declared scope/grid choices and E5’s six-seed choice remain deviations.
- E18 register item 29 contains the 19-threshold AUC problem, a documentary number collision, omitted required metrics, and unstable printed timing values. These require distinct corrections. Limiting the historical search to the protocol signature was a later specification refinement: the protocol originally fixed no cutoff and the reported outcome was unchanged; no extra defect is inferred.
- Historical tool-name wording in Paper 1 item 30 propagates the correction in item 28 and is merged with it. Removing the old manuscript copy is publication cleanup without evidence of an incorrect manuscript outcome; that portion is discussed here rather than duplicating the retained IDs in an excluded entry.
- The E6 origins-count change was initially considered a coverage enhancement because 168/1423 did not change. Joint inspection of abf7c1e and the generator showed that the E6 document claimed every number came from result files while 168 was literal in its generator. Both coders retained one narrow provenance defect, not a wrong numerical count; subsequent checker expansion is not another problem.
- Paper 4 geometry matching and CSV filenames have distinct corrections. Missing graph generators and missing result CSVs have distinct absent artifacts. Weight matching and graph connectivity have separate corrective requirements. E12 post-run input checking and end-to-end self-testing are separate missing checks. Paper 4 item 20 is separated into section count, unreproduced correlation, nonexistent excluded-section claim, and untraced prevalence differences.
- Paper 4’s unsaved model states are an explicitly declared design choice; the separate README assertion that checkpoints existed is a defect. The P4A output-format choice is a deviation; its absent post-run input check is a separate defect. The E9 cost remeasurements correct contaminated isolated measurements, even though their protocol section is titled Deviations.
- The in-sample M30 threshold was discussed as a potential defect. The sources establish a new out-of-sample specification and a successful threshold control, but not a contrary original prescribed outcome. Both coders excluded REC-002; the P4A commit remains attached to the register problems it documents.
- A failed scientific confirmation, an expected empty-slice warning with verified finite outputs, presentation changes, additional analyses and prospective checks are not automatically defects. Conversely, unchanged numerical results do not exclude a documentary error or the explicit manual-edit violation in the generated report.
- Main GIT-003 is a cross-branch trace: its message concerns Paper 4 scoring and review-time rectification. Both references are attached to Paper 4 problems; the incident card was not read. The retracted Paper 1 item 33 and retraction item 34 form one documentary defect, separate from the E2 check.
No disagreement remained after joint discussion; no conflict entry was needed.

## Required full-section reads

| Candidate / section | Decision | Reason | Problem ID(s) |
|---|---|---|---|
| CONGELAMENTO_E15.md at aa9f478b3fa8, section 7-bis, lines 119–128 | excluded | Read in full: adds causal-recovery and token-cost-reduction measures from the same replicates; explicitly leaves the other section numbers unchanged. Additional descriptive analysis, not another defect. TAG-003 remains an addition-only trace. | — |
| CONGELAMENTO_E18TER.md at aa9f478b3fa8, section 4, lines 161–165 | excluded | Read in full: levels on the older-than-one-week window and intervals are added as declared in the protocol. These paragraphs do not describe another correction. Separate F17 metric/caption corrections elsewhere are retained through TAG-017. TAG-008 remains an addition-only trace. | — |

No new synthetic candidate ID was needed for these sections.

## Register crosswalk

| Paper | Register item | Candidate | Problem ID(s) |
|---|---|---|---|
| Paper 1 | 1 | C-main-REG-001 | P1-016 |
| Paper 1 | 2 | C-main-REG-002 | P1-017 |
| Paper 1 | 3 | C-main-REG-003 | P1-018 |
| Paper 1 | 4 | C-main-REG-004 | P1-019 |
| Paper 1 | 5 | C-main-REG-005 | PC-002 |
| Paper 1 | 6 | C-main-REG-006 | P1-020 |
| Paper 1 | 7 | C-main-REG-007 | P1-021 |
| Paper 1 | 8 | C-main-REG-008 | PC-003 |
| Paper 1 | 9 | C-main-REG-009 | P1-022 |
| Paper 1 | 10 | C-main-REG-010 | P1-023 |
| Paper 1 | 11 | C-main-REG-011 | P1-024 |
| Paper 1 | 12 | C-main-REG-012 | P1-025 |
| Paper 1 | 13 | C-main-REG-013 | P1-026 |
| Paper 1 | 14 | C-main-REG-014 | P1-027 |
| Paper 1 | 15 | C-main-REG-015 | P1-028 |
| Paper 1 | 16 | C-main-REG-016 | P1-029 |
| Paper 1 | 17a | C-main-REG-017 | P1-030 |
| Paper 1 | 17b | C-main-REG-018 | P1-031 |
| Paper 1 | 18 | C-main-REG-019 | P1-032 |
| Paper 1 | 19 | C-main-REG-020 | P1-033 |
| Paper 1 | 20 | C-main-REG-021 | P1-034 |
| Paper 1 | 21 | C-main-REG-022 | P1-035 |
| Paper 1 | 22 | C-main-REG-023 | P1-006 |
| Paper 1 | 23 | C-main-REG-024 | P1-036 |
| Paper 1 | 24 | C-main-REG-025 | P1-037 |
| Paper 1 | 25 | C-main-REG-026 | P1-038 |
| Paper 1 | 26 | C-main-REG-027 | P1-039 |
| Paper 1 | 27 | C-main-REG-028 | P1-015 |
| Paper 1 | 28 | C-main-REG-029 | P1-008 |
| Paper 1 | 29 | C-main-REG-030 | P1-007, P1-013, P1-014, P1-058 |
| Paper 1 | 30 | C-main-REG-031 | P1-008 |
| Paper 1 | 31 | C-main-REG-032 | P1-009 |
| Paper 1 | 32 | C-main-REG-033 | PC-001 |
| Paper 1 | 33 | C-main-REG-034 | P1-005 |
| Paper 1 | 34 | C-main-REG-035 | P1-005 |
| Paper 4 | 1 | C-paper4-REG-001 | PC-002 |
| Paper 4 | 2 | C-paper4-REG-002 | P4-043 |
| Paper 4 | 3 | C-paper4-REG-003 | PC-003 |
| Paper 4 | 4 | C-paper4-REG-004 | P4-038, P4-039 |
| Paper 4 | 5 | C-paper4-REG-005 | P4-027, P4-046 |
| Paper 4 | 6 | C-paper4-REG-006 | P4-047, P4-048 |
| Paper 4 | 7 | C-paper4-REG-007 | P4-041, P4-042 |
| Paper 4 | 8 | C-paper4-REG-008 | P4-036 |
| Paper 4 | 9 | C-paper4-REG-009 | P4-028 |
| Paper 4 | 10 | C-paper4-REG-010 | P4-029 |
| Paper 4 | 11 | C-paper4-REG-011 | P4-004 |
| Paper 4 | 12 | C-paper4-REG-012 | P4-030 |
| Paper 4 | 13 | C-paper4-REG-013 | P4-031, P4-032 |
| Paper 4 | 14 | C-paper4-REG-014 | P4-023 |
| Paper 4 | 15 | C-paper4-REG-015 | P4-024 |
| Paper 4 | 16 | C-paper4-REG-016 | P4-025 |
| Paper 4 | 17 | C-paper4-REG-017 | P4-026 |
| Paper 4 | 18 | C-paper4-REG-018 | P4-016, P4-017 |
| Paper 4 | 19 | C-paper4-REG-019 | P4-018 |
| Paper 4 | 20 | C-paper4-REG-020 | P4-019, P4-020, P4-021, P4-022 |
| Paper 4 | 21 | C-paper4-REG-021 | P4-049 |
| Paper 4 | 22 | C-paper4-REG-022 | P4-011 |
| Paper 4 | 23 | C-paper4-REG-023 | P4-001 |
| Paper 4 | 24 | C-paper4-REG-024 | P4-010 |
| Paper 4 | 25 | C-paper4-REG-025 | PC-001 |
| Paper 4 | 26 | C-paper4-REG-026 | P4-002 |

## Added-file audit

The exact 426 candidates with statuses equal to [A] are listed below. Contrary to the instruction example, this list contains seven root frozen records (E14, E15, E16, E17, E18, E18QUATER, E18TER) and seven experiment protocols (E14, E15, E16, E17, E18, E18quater, E18ter). None is an addition-only correction register: REGISTRO_CORREZIONI.md is TAG-124 with A/M and is handled above. The timing folder contributes 272 files: 270 training markers plus two run/pilot JSON files. They are all checked as paths in the frozen candidate inventory.

Exclusion means that the **addition event** is not itself a correction; it does not assert that the contents contain no problems. Those contents are considered through the other extracted candidates and required section reads. All 19 rename candidates were independently verified as R100, with byte-identical contents.

| Candidate | Added-only path |
|---|---|
| C-main-TAG-001 | `CONGELAMENTO_E14.md` |
| C-main-TAG-003 | `CONGELAMENTO_E15.md` |
| C-main-TAG-004 | `CONGELAMENTO_E16.md` |
| C-main-TAG-005 | `CONGELAMENTO_E17.md` |
| C-main-TAG-006 | `CONGELAMENTO_E18.md` |
| C-main-TAG-007 | `CONGELAMENTO_E18QUATER.md` |
| C-main-TAG-008 | `CONGELAMENTO_E18TER.md` |
| C-main-TAG-019 | `evoluzione/analisi/analizza_e17.py` |
| C-main-TAG-021 | `evoluzione/analisi/analizza_e18ter.py` |
| C-main-TAG-025 | `evoluzione/analisi/architettura_ck.py` |
| C-main-TAG-026 | `evoluzione/analisi/classi_per_sensore.py` |
| C-main-TAG-027 | `evoluzione/analisi/correzione_difetto_23.py` |
| C-main-TAG-028 | `evoluzione/analisi/e14_stadio0.py` |
| C-main-TAG-029 | `evoluzione/analisi/e14b_fascio.py` |
| C-main-TAG-030 | `evoluzione/analisi/e14b_livelli.py` |
| C-main-TAG-032 | `evoluzione/analisi/figura_cronologia.py` |
| C-main-TAG-036 | `evoluzione/analisi/riproducibilita_spark.py` |
| C-main-TAG-037 | `evoluzione/analisi/scheda_fatti.py` |
| C-main-TAG-038 | `evoluzione/analisi/stile_paper.py` |
| C-main-TAG-040 | `evoluzione/audit/METADATI_AUDIT.md` |
| C-main-TAG-044 | `evoluzione/audit/metadati_audit.py` |
| C-main-TAG-045 | `evoluzione/audit/patch/README.md` |
| C-main-TAG-047 | `evoluzione/audit/patch/patch_e14_massimi.py` |
| C-main-TAG-048 | `evoluzione/audit/patch/patch_e14_massimi_2.py` |
| C-main-TAG-055 | `evoluzione/audit/patch/patch_e18quater_cat.py` |
| C-main-TAG-056 | `evoluzione/audit/patch/patch_e18quater_main.py` |
| C-main-TAG-057 | `evoluzione/audit/patch/patch_e18ter_main.py` |
| C-main-TAG-058 | `evoluzione/audit/patch/patch_e18ter_tabellaV.py` |
| C-main-TAG-059 | `evoluzione/audit/patch/patch_e18ter_tabelle.py` |
| C-main-TAG-064 | `evoluzione/audit/patch/patch_g18_21.py` |
| C-main-TAG-065 | `evoluzione/audit/patch/patch_g23.py` |
| C-main-TAG-066 | `evoluzione/audit/patch/patch_l_didascalie.py` |
| C-main-TAG-068 | `evoluzione/audit/patch/patch_main_solo_testo.py` |
| C-main-TAG-069 | `evoluzione/audit/patch/patch_manifesto_nota.py` |
| C-main-TAG-072 | `evoluzione/audit/patch/patch_registro_31.py` |
| C-main-TAG-078 | `evoluzione/audit/patch/patch_zenodo_regola.py` |
| C-main-TAG-080 | `evoluzione/audit/verifica_ingressi_e18.py` |
| C-main-TAG-087 | `evoluzione/esperimenti/collauda_statica_espansiva.py` |
| C-main-TAG-090 | `evoluzione/esperimenti/costi_sessione.py` |
| C-main-TAG-091 | `evoluzione/esperimenti/e14b_prepara_copia.sh` |
| C-main-TAG-093 | `evoluzione/esperimenti/esegui_e14.py` |
| C-main-TAG-094 | `evoluzione/esperimenti/esegui_e14b.sh` |
| C-main-TAG-095 | `evoluzione/esperimenti/esegui_e15.py` |
| C-main-TAG-097 | `evoluzione/esperimenti/esegui_e18quater.py` |
| C-main-TAG-108 | `evoluzione/esperimenti/pilota_tempi_e15.py` |
| C-main-TAG-109 | `evoluzione/esperimenti/ricognizione_paper4.sh` |
| C-main-TAG-110 | `evoluzione/esperimenti/ricognizione_paper4_log.sh` |
| C-main-TAG-116 | `protocol/E14.md` |
| C-main-TAG-117 | `protocol/E15.md` |
| C-main-TAG-118 | `protocol/E16.md` |
| C-main-TAG-119 | `protocol/E17.md` |
| C-main-TAG-120 | `protocol/E18.md` |
| C-main-TAG-121 | `protocol/E18quater.md` |
| C-main-TAG-122 | `protocol/E18ter.md` |
| C-main-TAG-125 | `protocol/RISCRITTURA_STORIA.md` |
| C-main-TAG-126 | `protocol/SUMMARIES.en.md` |
| C-main-TAG-127 | `protocol/e14_stadio0.json` |
| C-main-TAG-129 | `protocol/e14b/a/analisi_e3.json` |
| C-main-TAG-130 | `protocol/e14b/a/congelamento_e2.json` |
| C-main-TAG-131 | `protocol/e14b/a/congelamento_e3.json` |
| C-main-TAG-132 | `protocol/e14b/a/congelamento_e3bis.json` |
| C-main-TAG-133 | `protocol/e14b/a/congelamento_e4.json` |
| C-main-TAG-134 | `protocol/e14b/a/congelamento_e5.json` |
| C-main-TAG-135 | `protocol/e14b/a/congelamento_e7.json` |
| C-main-TAG-136 | `protocol/e14b/a/copertura_e4.json` |
| C-main-TAG-137 | `protocol/e14b/a/curve_e8bis_punti.json` |
| C-main-TAG-138 | `protocol/e14b/a/e14b_livelli_a.json` |
| C-main-TAG-139 | `protocol/e14b/a/e3bis_risultati.json` |
| C-main-TAG-140 | `protocol/e14b/a/e4_griglia_test.json` |
| C-main-TAG-141 | `protocol/e14b/a/e4_risultati.json` |
| C-main-TAG-142 | `protocol/e14b/a/e4_scelta_gated.json` |
| C-main-TAG-143 | `protocol/e14b/a/e5_k_secondaria.json` |
| C-main-TAG-144 | `protocol/e14b/a/e5_risultati.json` |
| C-main-TAG-145 | `protocol/e14b/a/e5_settimana_vs_A.json` |
| C-main-TAG-146 | `protocol/e14b/a/e6_origini_comuni.json` |
| C-main-TAG-147 | `protocol/e14b/a/e6_risultati.json` |
| C-main-TAG-148 | `protocol/e14b/a/e6_scelta_gated.json` |
| C-main-TAG-149 | `protocol/e14b/a/e6a_risultati.json` |
| C-main-TAG-150 | `protocol/e14b/a/e6a_scelta_gated.json` |
| C-main-TAG-151 | `protocol/e14b/a/e6bis_risultati.json` |
| C-main-TAG-152 | `protocol/e14b/a/e7_posthoc.json` |
| C-main-TAG-153 | `protocol/e14b/a/e7_stadio1.json` |
| C-main-TAG-154 | `protocol/e14b/a/e8_risultati.json` |
| C-main-TAG-155 | `protocol/e14b/a/e8_soglie.json` |
| C-main-TAG-156 | `protocol/e14b/a/e8bis_risultati.json` |
| C-main-TAG-157 | `protocol/e14b/a/manifesto.json` |
| C-main-TAG-158 | `protocol/e14b/a/predizioni_e2/controllo_e2.json` |
| C-main-TAG-159 | `protocol/e14b/a/predizioni_f0/controllo_f0.json` |
| C-main-TAG-160 | `protocol/e14b/a/predizioni_fase3/controllo_A.json` |
| C-main-TAG-161 | `protocol/e14b/a/predizioni_fase3/controllo_C.json` |
| C-main-TAG-162 | `protocol/e14b/a/predizioni_fase3/controllo_F.json` |
| C-main-TAG-163 | `protocol/e14b/a/predizioni_fase3/controllo_P.json` |
| C-main-TAG-164 | `protocol/e14b/a/predizioni_fase3/controllo_R-mon.json` |
| C-main-TAG-165 | `protocol/e14b/a/predizioni_fase3/controllo_R-orig.json` |
| C-main-TAG-166 | `protocol/e14b/a/predizioni_fase3/controllo_R.json` |
| C-main-TAG-167 | `protocol/e14b/a/predizioni_fase3_672/controllo_R-orig.json` |
| C-main-TAG-168 | `protocol/e14b/a/riselezione_rmon_test.json` |
| C-main-TAG-169 | `protocol/e14b/a/veterani_e3.json` |
| C-main-TAG-170 | `protocol/e14b/c/analisi_e3.json` |
| C-main-TAG-171 | `protocol/e14b/c/congelamento_e2.json` |
| C-main-TAG-172 | `protocol/e14b/c/congelamento_e3.json` |
| C-main-TAG-173 | `protocol/e14b/c/congelamento_e3bis.json` |
| C-main-TAG-174 | `protocol/e14b/c/congelamento_e4.json` |
| C-main-TAG-175 | `protocol/e14b/c/congelamento_e5.json` |
| C-main-TAG-176 | `protocol/e14b/c/congelamento_e7.json` |
| C-main-TAG-177 | `protocol/e14b/c/copertura_e4.json` |
| C-main-TAG-178 | `protocol/e14b/c/curve_e8bis_punti.json` |
| C-main-TAG-179 | `protocol/e14b/c/e14b_livelli_c.json` |
| C-main-TAG-180 | `protocol/e14b/c/e3bis_risultati.json` |
| C-main-TAG-181 | `protocol/e14b/c/e4_griglia_test.json` |
| C-main-TAG-182 | `protocol/e14b/c/e4_risultati.json` |
| C-main-TAG-183 | `protocol/e14b/c/e4_scelta_gated.json` |
| C-main-TAG-184 | `protocol/e14b/c/e5_k_secondaria.json` |
| C-main-TAG-185 | `protocol/e14b/c/e5_risultati.json` |
| C-main-TAG-186 | `protocol/e14b/c/e5_settimana_vs_A.json` |
| C-main-TAG-187 | `protocol/e14b/c/e6_origini_comuni.json` |
| C-main-TAG-188 | `protocol/e14b/c/e6_risultati.json` |
| C-main-TAG-189 | `protocol/e14b/c/e6_scelta_gated.json` |
| C-main-TAG-190 | `protocol/e14b/c/e6a_risultati.json` |
| C-main-TAG-191 | `protocol/e14b/c/e6a_scelta_gated.json` |
| C-main-TAG-192 | `protocol/e14b/c/e6bis_risultati.json` |
| C-main-TAG-193 | `protocol/e14b/c/e7_posthoc.json` |
| C-main-TAG-194 | `protocol/e14b/c/e7_stadio1.json` |
| C-main-TAG-195 | `protocol/e14b/c/e8_risultati.json` |
| C-main-TAG-196 | `protocol/e14b/c/e8_soglie.json` |
| C-main-TAG-197 | `protocol/e14b/c/e8bis_risultati.json` |
| C-main-TAG-198 | `protocol/e14b/c/manifesto.json` |
| C-main-TAG-199 | `protocol/e14b/c/predizioni_e2/controllo_e2.json` |
| C-main-TAG-200 | `protocol/e14b/c/predizioni_f0/controllo_f0.json` |
| C-main-TAG-201 | `protocol/e14b/c/predizioni_fase3/controllo_A.json` |
| C-main-TAG-202 | `protocol/e14b/c/predizioni_fase3/controllo_C.json` |
| C-main-TAG-203 | `protocol/e14b/c/predizioni_fase3/controllo_F.json` |
| C-main-TAG-204 | `protocol/e14b/c/predizioni_fase3/controllo_P.json` |
| C-main-TAG-205 | `protocol/e14b/c/predizioni_fase3/controllo_R-mon.json` |
| C-main-TAG-206 | `protocol/e14b/c/predizioni_fase3/controllo_R-orig.json` |
| C-main-TAG-207 | `protocol/e14b/c/predizioni_fase3/controllo_R.json` |
| C-main-TAG-208 | `protocol/e14b/c/predizioni_fase3_672/controllo_R-orig.json` |
| C-main-TAG-209 | `protocol/e14b/c/riselezione_rmon_test.json` |
| C-main-TAG-210 | `protocol/e14b/c/veterani_e3.json` |
| C-main-TAG-211 | `protocol/e14b/congelata/e14b_livelli_congelata.json` |
| C-main-TAG-212 | `protocol/e15/e15_risultati.json` |
| C-main-TAG-213 | `protocol/e15/tempi/A/A_Londra_p0_s201.json.fatto` |
| C-main-TAG-214 | `protocol/e15/tempi/A/A_Londra_p0_s202.json.fatto` |
| C-main-TAG-215 | `protocol/e15/tempi/A/A_Londra_p0_s203.json.fatto` |
| C-main-TAG-216 | `protocol/e15/tempi/A/A_Londra_p0_s204.json.fatto` |
| C-main-TAG-217 | `protocol/e15/tempi/A/A_Londra_p0_s205.json.fatto` |
| C-main-TAG-218 | `protocol/e15/tempi/A/A_Londra_p0_s206.json.fatto` |
| C-main-TAG-219 | `protocol/e15/tempi/A/A_Londra_p1_s201.json.fatto` |
| C-main-TAG-220 | `protocol/e15/tempi/A/A_Londra_p1_s202.json.fatto` |
| C-main-TAG-221 | `protocol/e15/tempi/A/A_Londra_p1_s203.json.fatto` |
| C-main-TAG-222 | `protocol/e15/tempi/A/A_Londra_p1_s204.json.fatto` |
| C-main-TAG-223 | `protocol/e15/tempi/A/A_Londra_p1_s205.json.fatto` |
| C-main-TAG-224 | `protocol/e15/tempi/A/A_Londra_p1_s206.json.fatto` |
| C-main-TAG-225 | `protocol/e15/tempi/A/A_Londra_p2_s201.json.fatto` |
| C-main-TAG-226 | `protocol/e15/tempi/A/A_Londra_p2_s202.json.fatto` |
| C-main-TAG-227 | `protocol/e15/tempi/A/A_Londra_p2_s203.json.fatto` |
| C-main-TAG-228 | `protocol/e15/tempi/A/A_Londra_p2_s204.json.fatto` |
| C-main-TAG-229 | `protocol/e15/tempi/A/A_Londra_p2_s205.json.fatto` |
| C-main-TAG-230 | `protocol/e15/tempi/A/A_Londra_p2_s206.json.fatto` |
| C-main-TAG-231 | `protocol/e15/tempi/A/A_Madrid_p0_s201.json.fatto` |
| C-main-TAG-232 | `protocol/e15/tempi/A/A_Madrid_p0_s202.json.fatto` |
| C-main-TAG-233 | `protocol/e15/tempi/A/A_Madrid_p0_s203.json.fatto` |
| C-main-TAG-234 | `protocol/e15/tempi/A/A_Madrid_p0_s204.json.fatto` |
| C-main-TAG-235 | `protocol/e15/tempi/A/A_Madrid_p0_s205.json.fatto` |
| C-main-TAG-236 | `protocol/e15/tempi/A/A_Madrid_p0_s206.json.fatto` |
| C-main-TAG-237 | `protocol/e15/tempi/A/A_Madrid_p1_s201.json.fatto` |
| C-main-TAG-238 | `protocol/e15/tempi/A/A_Madrid_p1_s202.json.fatto` |
| C-main-TAG-239 | `protocol/e15/tempi/A/A_Madrid_p1_s203.json.fatto` |
| C-main-TAG-240 | `protocol/e15/tempi/A/A_Madrid_p1_s204.json.fatto` |
| C-main-TAG-241 | `protocol/e15/tempi/A/A_Madrid_p1_s205.json.fatto` |
| C-main-TAG-242 | `protocol/e15/tempi/A/A_Madrid_p1_s206.json.fatto` |
| C-main-TAG-243 | `protocol/e15/tempi/A/A_Madrid_p2_s201.json.fatto` |
| C-main-TAG-244 | `protocol/e15/tempi/A/A_Madrid_p2_s202.json.fatto` |
| C-main-TAG-245 | `protocol/e15/tempi/A/A_Madrid_p2_s203.json.fatto` |
| C-main-TAG-246 | `protocol/e15/tempi/A/A_Madrid_p2_s204.json.fatto` |
| C-main-TAG-247 | `protocol/e15/tempi/A/A_Madrid_p2_s205.json.fatto` |
| C-main-TAG-248 | `protocol/e15/tempi/A/A_Madrid_p2_s206.json.fatto` |
| C-main-TAG-249 | `protocol/e15/tempi/A/A_Melbourne_p0_s201.json.fatto` |
| C-main-TAG-250 | `protocol/e15/tempi/A/A_Melbourne_p0_s202.json.fatto` |
| C-main-TAG-251 | `protocol/e15/tempi/A/A_Melbourne_p0_s203.json.fatto` |
| C-main-TAG-252 | `protocol/e15/tempi/A/A_Melbourne_p0_s204.json.fatto` |
| C-main-TAG-253 | `protocol/e15/tempi/A/A_Melbourne_p0_s205.json.fatto` |
| C-main-TAG-254 | `protocol/e15/tempi/A/A_Melbourne_p0_s206.json.fatto` |
| C-main-TAG-255 | `protocol/e15/tempi/A/A_Melbourne_p1_s201.json.fatto` |
| C-main-TAG-256 | `protocol/e15/tempi/A/A_Melbourne_p1_s202.json.fatto` |
| C-main-TAG-257 | `protocol/e15/tempi/A/A_Melbourne_p1_s203.json.fatto` |
| C-main-TAG-258 | `protocol/e15/tempi/A/A_Melbourne_p1_s204.json.fatto` |
| C-main-TAG-259 | `protocol/e15/tempi/A/A_Melbourne_p1_s205.json.fatto` |
| C-main-TAG-260 | `protocol/e15/tempi/A/A_Melbourne_p1_s206.json.fatto` |
| C-main-TAG-261 | `protocol/e15/tempi/A/A_Melbourne_p2_s201.json.fatto` |
| C-main-TAG-262 | `protocol/e15/tempi/A/A_Melbourne_p2_s202.json.fatto` |
| C-main-TAG-263 | `protocol/e15/tempi/A/A_Melbourne_p2_s203.json.fatto` |
| C-main-TAG-264 | `protocol/e15/tempi/A/A_Melbourne_p2_s204.json.fatto` |
| C-main-TAG-265 | `protocol/e15/tempi/A/A_Melbourne_p2_s205.json.fatto` |
| C-main-TAG-266 | `protocol/e15/tempi/A/A_Melbourne_p2_s206.json.fatto` |
| C-main-TAG-267 | `protocol/e15/tempi/C/C_Londra_p0_s201.json.fatto` |
| C-main-TAG-268 | `protocol/e15/tempi/C/C_Londra_p0_s202.json.fatto` |
| C-main-TAG-269 | `protocol/e15/tempi/C/C_Londra_p0_s203.json.fatto` |
| C-main-TAG-270 | `protocol/e15/tempi/C/C_Londra_p0_s204.json.fatto` |
| C-main-TAG-271 | `protocol/e15/tempi/C/C_Londra_p0_s205.json.fatto` |
| C-main-TAG-272 | `protocol/e15/tempi/C/C_Londra_p0_s206.json.fatto` |
| C-main-TAG-273 | `protocol/e15/tempi/C/C_Londra_p1_s201.json.fatto` |
| C-main-TAG-274 | `protocol/e15/tempi/C/C_Londra_p1_s202.json.fatto` |
| C-main-TAG-275 | `protocol/e15/tempi/C/C_Londra_p1_s203.json.fatto` |
| C-main-TAG-276 | `protocol/e15/tempi/C/C_Londra_p1_s204.json.fatto` |
| C-main-TAG-277 | `protocol/e15/tempi/C/C_Londra_p1_s205.json.fatto` |
| C-main-TAG-278 | `protocol/e15/tempi/C/C_Londra_p1_s206.json.fatto` |
| C-main-TAG-279 | `protocol/e15/tempi/C/C_Londra_p2_s201.json.fatto` |
| C-main-TAG-280 | `protocol/e15/tempi/C/C_Londra_p2_s202.json.fatto` |
| C-main-TAG-281 | `protocol/e15/tempi/C/C_Londra_p2_s203.json.fatto` |
| C-main-TAG-282 | `protocol/e15/tempi/C/C_Londra_p2_s204.json.fatto` |
| C-main-TAG-283 | `protocol/e15/tempi/C/C_Londra_p2_s205.json.fatto` |
| C-main-TAG-284 | `protocol/e15/tempi/C/C_Londra_p2_s206.json.fatto` |
| C-main-TAG-285 | `protocol/e15/tempi/C/C_Madrid_p0_s201.json.fatto` |
| C-main-TAG-286 | `protocol/e15/tempi/C/C_Madrid_p0_s202.json.fatto` |
| C-main-TAG-287 | `protocol/e15/tempi/C/C_Madrid_p0_s203.json.fatto` |
| C-main-TAG-288 | `protocol/e15/tempi/C/C_Madrid_p0_s204.json.fatto` |
| C-main-TAG-289 | `protocol/e15/tempi/C/C_Madrid_p0_s205.json.fatto` |
| C-main-TAG-290 | `protocol/e15/tempi/C/C_Madrid_p0_s206.json.fatto` |
| C-main-TAG-291 | `protocol/e15/tempi/C/C_Madrid_p1_s201.json.fatto` |
| C-main-TAG-292 | `protocol/e15/tempi/C/C_Madrid_p1_s202.json.fatto` |
| C-main-TAG-293 | `protocol/e15/tempi/C/C_Madrid_p1_s203.json.fatto` |
| C-main-TAG-294 | `protocol/e15/tempi/C/C_Madrid_p1_s204.json.fatto` |
| C-main-TAG-295 | `protocol/e15/tempi/C/C_Madrid_p1_s205.json.fatto` |
| C-main-TAG-296 | `protocol/e15/tempi/C/C_Madrid_p1_s206.json.fatto` |
| C-main-TAG-297 | `protocol/e15/tempi/C/C_Madrid_p2_s201.json.fatto` |
| C-main-TAG-298 | `protocol/e15/tempi/C/C_Madrid_p2_s202.json.fatto` |
| C-main-TAG-299 | `protocol/e15/tempi/C/C_Madrid_p2_s203.json.fatto` |
| C-main-TAG-300 | `protocol/e15/tempi/C/C_Madrid_p2_s204.json.fatto` |
| C-main-TAG-301 | `protocol/e15/tempi/C/C_Madrid_p2_s205.json.fatto` |
| C-main-TAG-302 | `protocol/e15/tempi/C/C_Madrid_p2_s206.json.fatto` |
| C-main-TAG-303 | `protocol/e15/tempi/C/C_Melbourne_p0_s201.json.fatto` |
| C-main-TAG-304 | `protocol/e15/tempi/C/C_Melbourne_p0_s202.json.fatto` |
| C-main-TAG-305 | `protocol/e15/tempi/C/C_Melbourne_p0_s203.json.fatto` |
| C-main-TAG-306 | `protocol/e15/tempi/C/C_Melbourne_p0_s204.json.fatto` |
| C-main-TAG-307 | `protocol/e15/tempi/C/C_Melbourne_p0_s205.json.fatto` |
| C-main-TAG-308 | `protocol/e15/tempi/C/C_Melbourne_p0_s206.json.fatto` |
| C-main-TAG-309 | `protocol/e15/tempi/C/C_Melbourne_p1_s201.json.fatto` |
| C-main-TAG-310 | `protocol/e15/tempi/C/C_Melbourne_p1_s202.json.fatto` |
| C-main-TAG-311 | `protocol/e15/tempi/C/C_Melbourne_p1_s203.json.fatto` |
| C-main-TAG-312 | `protocol/e15/tempi/C/C_Melbourne_p1_s204.json.fatto` |
| C-main-TAG-313 | `protocol/e15/tempi/C/C_Melbourne_p1_s205.json.fatto` |
| C-main-TAG-314 | `protocol/e15/tempi/C/C_Melbourne_p1_s206.json.fatto` |
| C-main-TAG-315 | `protocol/e15/tempi/C/C_Melbourne_p2_s201.json.fatto` |
| C-main-TAG-316 | `protocol/e15/tempi/C/C_Melbourne_p2_s202.json.fatto` |
| C-main-TAG-317 | `protocol/e15/tempi/C/C_Melbourne_p2_s203.json.fatto` |
| C-main-TAG-318 | `protocol/e15/tempi/C/C_Melbourne_p2_s204.json.fatto` |
| C-main-TAG-319 | `protocol/e15/tempi/C/C_Melbourne_p2_s205.json.fatto` |
| C-main-TAG-320 | `protocol/e15/tempi/C/C_Melbourne_p2_s206.json.fatto` |
| C-main-TAG-321 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s201.json.fatto` |
| C-main-TAG-322 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s202.json.fatto` |
| C-main-TAG-323 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s203.json.fatto` |
| C-main-TAG-324 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s204.json.fatto` |
| C-main-TAG-325 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s205.json.fatto` |
| C-main-TAG-326 | `protocol/e15/tempi/C_A/C_A_Londra_p0_s206.json.fatto` |
| C-main-TAG-327 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s201.json.fatto` |
| C-main-TAG-328 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s202.json.fatto` |
| C-main-TAG-329 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s203.json.fatto` |
| C-main-TAG-330 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s204.json.fatto` |
| C-main-TAG-331 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s205.json.fatto` |
| C-main-TAG-332 | `protocol/e15/tempi/C_A/C_A_Londra_p1_s206.json.fatto` |
| C-main-TAG-333 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s201.json.fatto` |
| C-main-TAG-334 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s202.json.fatto` |
| C-main-TAG-335 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s203.json.fatto` |
| C-main-TAG-336 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s204.json.fatto` |
| C-main-TAG-337 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s205.json.fatto` |
| C-main-TAG-338 | `protocol/e15/tempi/C_A/C_A_Londra_p2_s206.json.fatto` |
| C-main-TAG-339 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s201.json.fatto` |
| C-main-TAG-340 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s202.json.fatto` |
| C-main-TAG-341 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s203.json.fatto` |
| C-main-TAG-342 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s204.json.fatto` |
| C-main-TAG-343 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s205.json.fatto` |
| C-main-TAG-344 | `protocol/e15/tempi/C_A/C_A_Madrid_p0_s206.json.fatto` |
| C-main-TAG-345 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s201.json.fatto` |
| C-main-TAG-346 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s202.json.fatto` |
| C-main-TAG-347 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s203.json.fatto` |
| C-main-TAG-348 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s204.json.fatto` |
| C-main-TAG-349 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s205.json.fatto` |
| C-main-TAG-350 | `protocol/e15/tempi/C_A/C_A_Madrid_p1_s206.json.fatto` |
| C-main-TAG-351 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s201.json.fatto` |
| C-main-TAG-352 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s202.json.fatto` |
| C-main-TAG-353 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s203.json.fatto` |
| C-main-TAG-354 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s204.json.fatto` |
| C-main-TAG-355 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s205.json.fatto` |
| C-main-TAG-356 | `protocol/e15/tempi/C_A/C_A_Madrid_p2_s206.json.fatto` |
| C-main-TAG-357 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s201.json.fatto` |
| C-main-TAG-358 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s202.json.fatto` |
| C-main-TAG-359 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s203.json.fatto` |
| C-main-TAG-360 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s204.json.fatto` |
| C-main-TAG-361 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s205.json.fatto` |
| C-main-TAG-362 | `protocol/e15/tempi/C_A/C_A_Melbourne_p0_s206.json.fatto` |
| C-main-TAG-363 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s201.json.fatto` |
| C-main-TAG-364 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s202.json.fatto` |
| C-main-TAG-365 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s203.json.fatto` |
| C-main-TAG-366 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s204.json.fatto` |
| C-main-TAG-367 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s205.json.fatto` |
| C-main-TAG-368 | `protocol/e15/tempi/C_A/C_A_Melbourne_p1_s206.json.fatto` |
| C-main-TAG-369 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s201.json.fatto` |
| C-main-TAG-370 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s202.json.fatto` |
| C-main-TAG-371 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s203.json.fatto` |
| C-main-TAG-372 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s204.json.fatto` |
| C-main-TAG-373 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s205.json.fatto` |
| C-main-TAG-374 | `protocol/e15/tempi/C_A/C_A_Melbourne_p2_s206.json.fatto` |
| C-main-TAG-375 | `protocol/e15/tempi/E/ck_E_Londra_p0_s1150248972.pt.fatto` |
| C-main-TAG-376 | `protocol/e15/tempi/E/ck_E_Londra_p0_s1157715887.pt.fatto` |
| C-main-TAG-377 | `protocol/e15/tempi/E/ck_E_Londra_p0_s1592395901.pt.fatto` |
| C-main-TAG-378 | `protocol/e15/tempi/E/ck_E_Londra_p0_s399595374.pt.fatto` |
| C-main-TAG-379 | `protocol/e15/tempi/E/ck_E_Londra_p0_s643310434.pt.fatto` |
| C-main-TAG-380 | `protocol/e15/tempi/E/ck_E_Londra_p0_s682647013.pt.fatto` |
| C-main-TAG-381 | `protocol/e15/tempi/E/ck_E_Londra_p1_s1150248972.pt.fatto` |
| C-main-TAG-382 | `protocol/e15/tempi/E/ck_E_Londra_p1_s1157715887.pt.fatto` |
| C-main-TAG-383 | `protocol/e15/tempi/E/ck_E_Londra_p1_s1592395901.pt.fatto` |
| C-main-TAG-384 | `protocol/e15/tempi/E/ck_E_Londra_p1_s399595374.pt.fatto` |
| C-main-TAG-385 | `protocol/e15/tempi/E/ck_E_Londra_p1_s643310434.pt.fatto` |
| C-main-TAG-386 | `protocol/e15/tempi/E/ck_E_Londra_p1_s682647013.pt.fatto` |
| C-main-TAG-387 | `protocol/e15/tempi/E/ck_E_Londra_p2_s1150248972.pt.fatto` |
| C-main-TAG-388 | `protocol/e15/tempi/E/ck_E_Londra_p2_s1157715887.pt.fatto` |
| C-main-TAG-389 | `protocol/e15/tempi/E/ck_E_Londra_p2_s1592395901.pt.fatto` |
| C-main-TAG-390 | `protocol/e15/tempi/E/ck_E_Londra_p2_s399595374.pt.fatto` |
| C-main-TAG-391 | `protocol/e15/tempi/E/ck_E_Londra_p2_s643310434.pt.fatto` |
| C-main-TAG-392 | `protocol/e15/tempi/E/ck_E_Londra_p2_s682647013.pt.fatto` |
| C-main-TAG-393 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s1150248972.pt.fatto` |
| C-main-TAG-394 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s1157715887.pt.fatto` |
| C-main-TAG-395 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s1592395901.pt.fatto` |
| C-main-TAG-396 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s399595374.pt.fatto` |
| C-main-TAG-397 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s643310434.pt.fatto` |
| C-main-TAG-398 | `protocol/e15/tempi/E/ck_E_Madrid_p0_s682647013.pt.fatto` |
| C-main-TAG-399 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s1150248972.pt.fatto` |
| C-main-TAG-400 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s1157715887.pt.fatto` |
| C-main-TAG-401 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s1592395901.pt.fatto` |
| C-main-TAG-402 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s399595374.pt.fatto` |
| C-main-TAG-403 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s643310434.pt.fatto` |
| C-main-TAG-404 | `protocol/e15/tempi/E/ck_E_Madrid_p1_s682647013.pt.fatto` |
| C-main-TAG-405 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s1150248972.pt.fatto` |
| C-main-TAG-406 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s1157715887.pt.fatto` |
| C-main-TAG-407 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s1592395901.pt.fatto` |
| C-main-TAG-408 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s399595374.pt.fatto` |
| C-main-TAG-409 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s643310434.pt.fatto` |
| C-main-TAG-410 | `protocol/e15/tempi/E/ck_E_Madrid_p2_s682647013.pt.fatto` |
| C-main-TAG-411 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1150248972.pt.fatto` |
| C-main-TAG-412 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1157715887.pt.fatto` |
| C-main-TAG-413 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s1592395901.pt.fatto` |
| C-main-TAG-414 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s399595374.pt.fatto` |
| C-main-TAG-415 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s643310434.pt.fatto` |
| C-main-TAG-416 | `protocol/e15/tempi/E/ck_E_Melbourne_p0_s682647013.pt.fatto` |
| C-main-TAG-417 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1150248972.pt.fatto` |
| C-main-TAG-418 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1157715887.pt.fatto` |
| C-main-TAG-419 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s1592395901.pt.fatto` |
| C-main-TAG-420 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s399595374.pt.fatto` |
| C-main-TAG-421 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s643310434.pt.fatto` |
| C-main-TAG-422 | `protocol/e15/tempi/E/ck_E_Melbourne_p1_s682647013.pt.fatto` |
| C-main-TAG-423 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1150248972.pt.fatto` |
| C-main-TAG-424 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1157715887.pt.fatto` |
| C-main-TAG-425 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s1592395901.pt.fatto` |
| C-main-TAG-426 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s399595374.pt.fatto` |
| C-main-TAG-427 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s643310434.pt.fatto` |
| C-main-TAG-428 | `protocol/e15/tempi/E/ck_E_Melbourne_p2_s682647013.pt.fatto` |
| C-main-TAG-429 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1150248972.pt.fatto` |
| C-main-TAG-430 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1157715887.pt.fatto` |
| C-main-TAG-431 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s1592395901.pt.fatto` |
| C-main-TAG-432 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s399595374.pt.fatto` |
| C-main-TAG-433 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s643310434.pt.fatto` |
| C-main-TAG-434 | `protocol/e15/tempi/E1/ck_E1_Londra_p0_s682647013.pt.fatto` |
| C-main-TAG-435 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1150248972.pt.fatto` |
| C-main-TAG-436 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1157715887.pt.fatto` |
| C-main-TAG-437 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s1592395901.pt.fatto` |
| C-main-TAG-438 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s399595374.pt.fatto` |
| C-main-TAG-439 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s643310434.pt.fatto` |
| C-main-TAG-440 | `protocol/e15/tempi/E1/ck_E1_Londra_p1_s682647013.pt.fatto` |
| C-main-TAG-441 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1150248972.pt.fatto` |
| C-main-TAG-442 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1157715887.pt.fatto` |
| C-main-TAG-443 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s1592395901.pt.fatto` |
| C-main-TAG-444 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s399595374.pt.fatto` |
| C-main-TAG-445 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s643310434.pt.fatto` |
| C-main-TAG-446 | `protocol/e15/tempi/E1/ck_E1_Londra_p2_s682647013.pt.fatto` |
| C-main-TAG-447 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1150248972.pt.fatto` |
| C-main-TAG-448 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1157715887.pt.fatto` |
| C-main-TAG-449 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s1592395901.pt.fatto` |
| C-main-TAG-450 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s399595374.pt.fatto` |
| C-main-TAG-451 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s643310434.pt.fatto` |
| C-main-TAG-452 | `protocol/e15/tempi/E1/ck_E1_Madrid_p0_s682647013.pt.fatto` |
| C-main-TAG-453 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1150248972.pt.fatto` |
| C-main-TAG-454 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1157715887.pt.fatto` |
| C-main-TAG-455 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s1592395901.pt.fatto` |
| C-main-TAG-456 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s399595374.pt.fatto` |
| C-main-TAG-457 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s643310434.pt.fatto` |
| C-main-TAG-458 | `protocol/e15/tempi/E1/ck_E1_Madrid_p1_s682647013.pt.fatto` |
| C-main-TAG-459 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1150248972.pt.fatto` |
| C-main-TAG-460 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1157715887.pt.fatto` |
| C-main-TAG-461 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s1592395901.pt.fatto` |
| C-main-TAG-462 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s399595374.pt.fatto` |
| C-main-TAG-463 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s643310434.pt.fatto` |
| C-main-TAG-464 | `protocol/e15/tempi/E1/ck_E1_Madrid_p2_s682647013.pt.fatto` |
| C-main-TAG-465 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1150248972.pt.fatto` |
| C-main-TAG-466 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1157715887.pt.fatto` |
| C-main-TAG-467 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s1592395901.pt.fatto` |
| C-main-TAG-468 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s399595374.pt.fatto` |
| C-main-TAG-469 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s643310434.pt.fatto` |
| C-main-TAG-470 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p0_s682647013.pt.fatto` |
| C-main-TAG-471 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1150248972.pt.fatto` |
| C-main-TAG-472 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1157715887.pt.fatto` |
| C-main-TAG-473 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s1592395901.pt.fatto` |
| C-main-TAG-474 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s399595374.pt.fatto` |
| C-main-TAG-475 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s643310434.pt.fatto` |
| C-main-TAG-476 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p1_s682647013.pt.fatto` |
| C-main-TAG-477 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1150248972.pt.fatto` |
| C-main-TAG-478 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1157715887.pt.fatto` |
| C-main-TAG-479 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s1592395901.pt.fatto` |
| C-main-TAG-480 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s399595374.pt.fatto` |
| C-main-TAG-481 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s643310434.pt.fatto` |
| C-main-TAG-482 | `protocol/e15/tempi/E1/ck_E1_Melbourne_p2_s682647013.pt.fatto` |
| C-main-TAG-483 | `protocol/e15/tempi/esito_e15.json` |
| C-main-TAG-484 | `protocol/e15/tempi/pilota_tempi_16.json` |
| C-main-TAG-485 | `protocol/e16/e16_risultati.json` |
| C-main-TAG-486 | `protocol/e18/COPIA_INGRESSI_MAC.md` |
| C-main-TAG-487 | `protocol/e18/tempi_parte_A.json` |
| C-main-TAG-488 | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md` |
| C-main-TAG-489 | `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md` |
| C-main-TAG-490 | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md` |
| C-main-TAG-491 | `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub2.md` |
| C-main-TAG-492 | `protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md` |
| C-main-TAG-493 | `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| C-main-TAG-494 | `protocol/spark/CONFRONTO_paper1-freeze-20261101n.md` |
| C-main-TAG-495 | `protocol/spark/CONFRONTO_paper1-freeze-20261101o.md` |
| C-main-TAG-496 | `protocol/spark/CONFRONTO_paper1-freeze-20261103p.md` |
| C-main-TAG-497 | `protocol/spark/NOTA_20261101n.md` |

## Validation and hand-back

Input: 672 unique candidate IDs — 61 register rows, 8 deviations, 75 commits, 25 record notes, 2 report flags, 501 tag-file candidates. Tag classes: 426 A-only, 36 M-only, 20 A/M and 19 R-only.

Output: 127 entries — 102 defect, 5 deviation, 1 violation, 19 excluded, 0 conflict. Excluded entries are audit records, not counted problems. Shared problems have one PC entry each.

All 672 IDs are covered. 53 candidate IDs have repeated memberships, each covered by an individual split-into-n line matching its exact number of problem memberships. Every excluded ID appears exactly once and nowhere else. Entry IDs are unique; all entries have exactly the seven required fields; reasons are populated only for excluded/conflict; summaries are single-line English source paraphrases.

Working copies remain at af66067 with no source edits or commits. The only deliverables are MINUTES_PHASE3.md and CORPUS.json, handed back outside the repositories in Downloads. This is a Phase 3 hand-back, not a Phase 4 freeze.

CORPUS.json SHA-256 (delivery integrity, not a Phase 4 freeze): `916391655be2aeba47e888fbcb034cd22becf2f8d15cf16b8331991749cf76f7`.

COD-01 — reviewed and signed, 2026-11-10.
COD-02 — reviewed and signed, 2026-11-10.
