# Register of corrections (English translation)

Corrections made to the pipeline, and two to the manuscript, during the study. **The Italian
originals are the record.** Each correction is dated, in Italian, in the protocol or frozen record of
the experiment it concerns (column "Italian record"), and the consolidated register in Italian is kept
with the authors' notes of the manuscript. This file translates entries 1–27; where it differs from an
Italian original, the original prevails. In the last column, "—" means that no dated Italian correction was located in
this repository for that entry; its text comes from the register of the manuscript. The paper refers to these entries by number.

How they were found: 1–16 by assertions, preflight checks or fingerprint comparisons; 17 by reading a
frozen record against the manuscript; 19 and 20 by the regeneration script (`analysis/main.py`); 21
while describing the network from the checkpoint weights; 22 by regeneration on a second machine; 23
while generating a supplementary table from the class-weight files actually loaded; 24 by a control of
E4 during the sensitivity experiment; 25 by regeneration from scratch; 26 by reading the E14 record
against its own tables; 27 in the second external review; none by inspecting the code for its own sake.
Entries 17b and 18 are errors of the manuscript, not of the pipeline.

| # | Defect | Correction and measured effect | Italian record |
|---|---|---|---|
| 1 | one batch per epoch presented as an epoch | 35 updates = 15 % of a pass; the ordering of models changed at an adequate budget | `evoluzione/RETTIFICA_BUDGET.md` |
| 2 | checkpoint selection on 32 fixed validation instants (2 %) | selection on the full validation set | `evoluzione/RETTIFICA_BUDGET.md` |
| 3 | a clamp assigning a class to missing targets | affected 40 % of London targets; masked | `CONGELAMENTO_RACCORDO.md` |
| 4 | static branch and heads misaligned across variants (640 extra draws) | canonical artefact by fingerprint | — |
| 5 | windows built by index across calendar gaps | horizon without its declared meaning; 2.6 % of origins excluded as non-admissible | `CONGELAMENTO_E_F_PIPELINE_PRECEDENTE.md` |
| 6 | t₀ row included in adaptation | 77 origins instead of 78 | — |
| 7 | descriptor trained on a non-causal end-of-period snapshot | causal variant pre-registered, not executed (paper, Limitations) | — |
| 8 | node population 900/900/594 against the documented 828/774/587 | declared | `evoluzione/RETTIFICA_POPOLAZIONE.md` |
| 9 | arms declared in six places; four missed when adding an arm | single arm-property table, 36-check test | — |
| 10 | R-orig and R-mon routed into the adaptation branch | 216 runs, found by wall time, quarantined with index | — |
| 11 | a phase summary overwritten by a later launch | outputs written per launch | `CONGELAMENTO_E3.md` |
| 12 | feasibility script rounding partitions to 27 instead of 26 sensors | corrected before launch | — |
| 13 | a nine-channel predictor built whatever the source | failed on PEMS; cities unchanged | — |
| 14 | a non-discriminating post-hoc criterion proposed in review of the coverage experiment | corrected before use | — |
| 15 | a reading branch of the operational-metrics generator writing "not distinguishable" for "above at some level, never below" | corrected before commit | `CONGELAMENTO_E8.md` |
| 16 | `np.trapz` absent in the environment | explicit trapezoids | `CONGELAMENTO_E8.md` |
| 17a | E3-bis generator: "at least 6×" divided the median of R-orig(1 wk) over the nine cells of the three cities by the only F′(1 wk) timed in isolation (Melbourne) | timings per context from the single session (`costi_tabella_sessione.json`); ratio only within the same city; E3-bis record regenerated (fingerprint `174d8e2d1808516c`) | `CONGELAMENTO_E3bis.md` |
| 17b | in a draft of the manuscript, the timings 36.8 s and 35.7 s were attributed to F′(1 wk) in Madrid and London; they are the timings of gated(48 h) in E4 | manuscript corrected with the paired timings per city | manuscript (authors' notes) |
| 18 | a citation in a draft of the manuscript did not match the reference it pointed to | citation removed; the reference cited with its own title | manuscript (authors' notes) |
| 19 | E3 revisit count took from the registry every completed run of R, R-orig and R-mon, including the 9 isolated re-measurements made for the cost table (117 instead of 108) | launch defined by the 108 manifests per arm, listed by fingerprint in `analisi_e3.json`; each cell counts only the run that produced the registered wCE; re-measurements labelled separately; record regenerated, not edited by hand; numbers in the paper unchanged | `CONGELAMENTO_E3.md` |
| 20 | a sentence of the E5 record on E3-bis depended on which experiments existed when it was generated; found different on regeneration (identical numbers) | sentence made stable over time; record regenerated, not edited by hand | `CONGELAMENTO_E5.md` |
| 21 | static branch fed with the sensor's whole-series coverage, including test | effect measured by E14: confined to arms without a learned identity for the sensor, arm wCE moved by ≤ 0.007; the only three-episode reading that changes does so in the paper's favour; the five statements re-established end-to-end with causal inputs by E15; code made causal by default after the study (`--statica=congelata` reproduces the frozen campaign) | `protocol/E14.md`, `CONGELAMENTO_E14.md`, `CONGELAMENTO_E14B.md`, `CONGELAMENTO_E15.md` |
| 22 | data-identity check in the E2 pairing verification compared float32 recomputed aggregates at rtol 10⁻¹²; failed across architectures (max element deviation 4.9 × 10⁻⁹) | tolerance set to 10⁻⁷; found by regeneration on a second machine | — |
| 23 | the frozen descriptive table of class frequencies (E6, `frequenze_classi.json`) was computed from an earlier set of class-weight files (index-based campaign) and from 3 of the 6 PEMS08 partitions, not from the files loaded by the experiments | table rebuilt from the files actually loaded, with fingerprints; no effect on results; three descriptive bounds change (cities: congested class up to 15.9 % instead of 15.7 %; Madrid 9.0–9.5 %; London 15.4–15.9 %) | `protocol/E6.md` (dated correction) |
| 24 | `adatta_F` built its own static vector instead of taking the cell's; under the E14 variants F was adapted with the frozen scalar and evaluated with the variant one; no effect on frozen numbers (the two coincided there) | caught by E4 control 3 during stage B (deviations 10⁻⁴–10⁻³); fixed (commit `8f9afbf`), F re-adapted, E4 re-run | — |
| 25 | the stage-B orchestrator (`esegui_e14b.sh`) ran the E6 "origins" phase before E6a, whose predictions it reads; no effect on numbers; `main.py` not involved | found by regeneration from scratch; phase moved after E6a | — |
| 26 | the E14-B generator compared the whole PEMS (τ, N) selection record, including the validation wCE that differs by ~10⁻⁹ between machines, and flagged identical (τ, N) as "different" | documentation only, no effect on numbers; generator compares (τ, N) and reports the wCE difference separately; record regenerated with a dated correction (commit `109aca5`, fingerprint `864b21c7796aefb2`) | `CONGELAMENTO_E14B.md` |
| 27 | in `esegui_e16.py` every arm was evaluated on all origins after t₁; for F′(1 wk) this includes the first week, in which the adapted embedding uses data up to t₀ + 1 week, so the F′(1 wk) rows of the E16 tables are on a non-causal window for that arm; the blocking check compared with the frozen aggregate summed over the three age bands and could not detect it; the calibration share s of F₀ − C is not affected | correction in progress (E18, part C): F′(1 wk) rows recomputed on origins older than one week for both arms, calibration parameters unchanged | `protocol/E18.md` §3 |
