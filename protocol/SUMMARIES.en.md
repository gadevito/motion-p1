# Summaries of the pre-registered experiments (English)

English summaries of the protocols and frozen records of E3–E18. **The Italian protocols and frozen
records are the record**; where a summary differs from them, the original prevails. Each section ends
with the fingerprints (first 16 hex digits of the SHA-256) of its originals. Short Italian quotations
are given with their translation. Notes marked "[unclear in source: ...]" flag points that the
originals do not settle; they are not corrections. There are no experiments E9–E13 in this repository.

Notation (see `GLOSSARY.en.md`): C identity-free model; A oracle trained with the new sensor present;
E identity model on the initial sensors; F0 = E with the mean embedding; E′ = E with the unknown-node
token; F0′ = E′ with the token; F(L), F′(L) embedding adapted on the first L hours; R naive
retraining; R-orig retraining uniform per origin; gated(τ, N) serves F0′ until age τ, then F′(τ) for
sensors with at least N valid targets; C_A identity-free model trained on the oracle's data. All
differences are in wCE (class-weighted cross-entropy) unless stated; intervals are 95 % joint-bootstrap
intervals (partitions × seeds × sensor positions).

## E3 — Fair retraining

- **Scope:** naive R is worse than C by +0.13; is that only per-node sampling? E3 builds a retraining baseline a reviewer cannot dismiss.
- **Arms:** R (uniform per node), R-orig (uniform per origin), R-mon (R-orig with checkpoint selection also watching the new sensors' last 6 of their 24 h); same 2,290-update budget, A's architecture, 108 runs per arm.
- **Criterion:** R-orig − C with an interval excluding zero: negative = fair retraining pays; positive = it does not pay at this budget. Secondary: R-orig − R, R-mon − R-orig. Checks: revisit ratio per origin, initial sensors before/after, wall time in isolation.
- **Outcome:** "Esito eterogeneo per citta'" (heterogeneous by city), no aggregation: R-orig − C Madrid −0.014 [−0.023, −0.004] (pays), London +0.049 [+0.034, +0.067] (does not pay), Melbourne +0.011 [−0.011, +0.035] (inconclusive).
- R-orig − R < 0 in all three cities; revisit ratio 1.000; no degradation of the existing network; R-mon coincides with R-orig in 3/3 (null by construction); R-orig costs 36.8 min at insertion against 15.6 s for F (142×).
- **Deviations:** first launch invalid (arms routed into the F branch), quarantined; equal-weight R-mon reselection added (2/10), secondary; correction of 2026-10-10 (register entry 19, revisit count).

Original: `protocol/E3.md` (245085de8a909ca8); record: `CONGELAMENTO_E3.md` (110ec4be3f3f9151)

## E3-bis — Fair retraining with one week of data

- **Scope:** in E4 the cost comparison was asymmetric (R-orig 24 h of data, F′ one week); E3-bis repeats R-orig with one week of acquisition, (t0, t0 + 672], on the main episode.
- **Arm:** R-orig(1 wk), budget 2,290, selection on the initial network, 108 runs; compared with F′(1 wk), C, A, R-orig(24 h).
- **Criterion** (a section of `protocol/E5.md`; a reading, not a threshold): if R-orig(1 wk) − F′(1 wk) includes zero or is positive, retraining buys nothing even with the same data. If not run before submission, the paper declares the asymmetry.
- **Outcome:** "equivalente all'adattamento entro ±3 % in 3 citta' su 3" (equivalent to adaptation within ±3 % in 3 of 3 cities): R-orig(1 wk) − F′(1 wk) Madrid −0.003 [−0.006, −0.001], London −0.002 [−0.005, +0.000], Melbourne −0.013 [−0.020, −0.007]. R-orig(1 wk) − R-orig(24 h) < 0 in 3/3.
- Compute ratio at equal data, measured in Melbourne only: 3.7× (1489 s / 406 s).
- **Deviations:** one parameter (`--acquisizione-passi`) added to the E3 runners; correction of 2026-10-10 (entry 17a): "almeno 6×" (at least 6×) replaced by a same-city ratio.

Original: no `protocol/E3bis.md` (pre-registered in `protocol/E5.md`, 3dd706bcf3ddd899); record: `CONGELAMENTO_E3bis.md` (174d8e2d1808516c)

## E4 — F against C, and the gated policy

- **Scope:** no new training. F − C and F′ − C directly; the age at which identity should be switched on; a policy that never degrades the single model hosting it (F0′).
- **Arms:** C, F0, F, F0′, F′, gated(τ, N); adaptation curve L ∈ {6 h, 12 h, 24 h, 48 h, 1 wk}; grids closed in advance τ ∈ {24 h, 48 h, 1 wk, never}, N ∈ {0, 77, 154, 231}, chosen per city on the validation episode (ties: larger N, then never, then smaller τ).
- **Criterion:** primary gated − F0′ ≤ 0 in all cities, with a 95 % interval not including positive values beyond 0.005; gated − C always reported next to F0′ − C.
- **Outcome:** criterion "SODDISFATTO" (satisfied), 3/3: gated − F0′ Madrid −0.030 [−0.038, −0.022], London −0.009 [−0.016, −0.003], Melbourne −0.024 [−0.027, −0.020].
- Selected (τ, N), written to `e4_scelta_gated.json` before the test: Madrid (48 h, 77), London (48 h, 154), Melbourne (1 wk, 154). Against C the policy pays in Madrid and Melbourne, level in London. Validation-to-test transfer of (τ, N) imperfect in London and Melbourne; the registered choice was kept.
- **Deviations:** curve grid changed before launch; PEMS04 deferred to E6; cost estimate wrong (11.3 h with 8 processes against "< 10 process-hours"), not a deviation since no parameter changed.

Original: `protocol/E4.md` (e275daec5945c26b); record: `CONGELAMENTO_E4.md` (4a8784708a246265)

## E5 — More insertion episodes

- **Scope:** does E4 depend on the installation date? The t0-dependent arms are repeated on two earlier episodes per city, with the E4 (τ, N) applied without reselection.
- **Arms:** C, A, E′ trained per episode (seeds 201–206); F0′, F′(24 h), F′(1 wk), gated; secondary F′(24 h, k) with k chosen on the extended validation episode.
- **Criterion** (reading rule): each claim — (a) F0′ − C > 0, (b) gated − F0′ < 0, (c) F′(1 wk) − C < 0, (d) sign of F′(24 h) − C, (e) F′(1 wk) − A — must keep its interval sign in all three episodes of a city; otherwise it is reported as episode-dependent, with no mean across episodes.
- **Outcome:** "7 affermazioni su 15" (7 of 15 claims) keep their sign in all three episodes; the rest are episode-dependent. Claim (c) holds in 3/3 cities. Over nine episodes gated − F0′ has a maximum upper bound of +0.004 (≤ 0.005), below zero in 7 of 9.
- Threshold N acted in London (all episodes) and Melbourne (episodes 2–3) and "ha trattenuto adattamenti che avrebbero pagato" (held back adaptations that would have paid).
- **Deviations:** six seeds instead of eight (confirmed by the reviewer on 4/10); cost corrected before launch to 324 trainings; the E4 validation episode falls inside episode 2's evaluation period (Limitation 7).

Original: `protocol/E5.md` (3dd706bcf3ddd899); record: `CONGELAMENTO_E5.md` (069509f0570bbc0a)

## E6 — External replication on PEMS04 and PEMS08 (with E6-bis)

- **Scope:** does the one-week thesis hold outside Traffic4cast? Part A completes the old PEMS04 campaign with the final arms (168 common origins per partition); part B is a replication on PEMS08 (6 partitions × 6 seeds, test ≥ 21 days). E6-bis: does the mean-embedding cost exist on PEMS08?
- **Arms:** C, A (PEMS08), E′, F0′, F′(24 h), F′(48 h), F′(1 wk), gated (E4 rule) with an N = 0 variant, R-orig(24 h), R-orig(1 wk) (PEMS08). E6-bis: E without token, F0, F(24 h), F(1 wk).
- **Criterion:** Δ with respect to C with an interval excluding zero, whatever the sign; claims (a)–(e) reported with the cities and their agreement. E6-bis: no threshold.
- **Outcome (PEMS08):** the thesis "regge" (holds): (c) F′(1 wk) − C = −0.091 [−0.131, −0.042]; signs agree with the cities for "1 affermazione su 5" (1 claim of 5); R-orig(1 wk) ≡ F′(1 wk) within ±3 % not concluded. **PEMS04:** (c) −0.033 [−0.047, −0.019], sign agrees; (e) not reportable (no A).
- **E6-bis:** F0 − C = +0.156 [+0.066, +0.242]; the cost "esiste anche su PEMS08" (also exists on PEMS08).
- **Deviations:** nine-channel predictor defect corrected (entry 13, commit `6629f40`); correction of 2026-10-13 (entry 23, class-frequency table, no effect on results).
- [unclear in source: the record cites `protocol/E6.md` with fingerprint c7a6583897215545, the current file is 90818c7597925712; the protocol was changed afterwards by the dated correction of 2026-10-13 and by register entry 28 (2026-10-29).]

Original: `protocol/E6.md` (90818c7597925712), `protocol/E6bis.md` (1d74950bf0f0ba9a); record: `CONGELAMENTO_E6.md` (f5e5d941ba4b7a4d)

## E7 — Coverage and adaptation, in two stages

- **Scope:** how much does a sensor's coverage in its first 24 h explain the benefit of adaptation, and does one-week adaptation pay below the threshold N?
- **Design:** stage 1 at zero cost from the E5 files; stages 2a and 2b conditional. Per sensor Δ1 = F′(1 wk) − C, Δ2 = F′(24 h) − C, Δ3 = F′(24 h, k) − C, against coverage v (24 h) and v7 (one week): groups below/above N (≥ 10 sensors) and rank correlations.
- **Criterion:** hypothesis Δ1 < 0 with an interval excluding zero in the v < N group of every (episode, city) where it exists. Stage 2a runs iff the hypothesis fails somewhere and ρ(v, Δ1) (or ρ(v7, Δ1)) < 0 excluding zero in at least two cities of episode 1, or two cities in each of two episodes.
- **Outcome:** the hypothesis "VALE" (holds) in all 4 below-threshold groups (London episodes 1–3: −0.030, −0.030, −0.032; Melbourne episode 2: −0.029); stage 2a not run, hence neither 2b. Positive ρ excluding zero declared as anomalies (London ep. 2, Melbourne ep. 2).
- Recommendation: "dopo una settimana, adattare tutti i nodi; la soglia serve solo a chi adatta prima" (after one week, adapt all sensors; the threshold only serves those who adapt earlier).
- **Deviations:** section 5b post hoc, requested by the reviewer after the freeze, zero cost; it does not explain the anomalies.

Original: `protocol/E7.md` (07db021e85236235); record: `CONGELAMENTO_E7.md` (a3f62bf4816f5aa0)

## E8 — Operational metrics (with E8-bis)

- **Scope:** descriptive and post hoc. E8 translates wCE differences into recall on the congested class, precision, false-alarm rate and F1-macro; E8-bis separates discrimination from calibration with recall–false-alarm curves.
- **Arms:** C, A, F0, F0′, F′(24 h), F′(48 h), F′(1 wk), gated (not in E8-bis), R-orig(1 wk); cities (episode 1), PEMS08, PEMS04. Rules: threshold maximising congested-class F1 on validation (primary), false-alarm parity with C, argmax.
- **Criterion:** none; the protocol declares no success criterion and no decision. If recall and wCE diverge, both are reported and no metric is chosen.
- **Outcome (E8):** false-alarm parity imposed on validation held on the test in 3 of 5 contexts; six wCE–recall divergences, all in Madrid and London. F′(1 wk) − C under parity: Madrid +16.1 recall points and London −6.2 (parity did not hold in either), PEMS04 +7.1; not distinguishable in Melbourne and PEMS08.
- **Outcome (E8-bis):** one-week adaptation dominates C "a ogni punto operativo esaminato (0,5–10 % di falsi allarmi)" (at every operating point examined, 0.5–10 % false alarms) in 5 of 5 contexts; of the mean-embedding cost under argmax, a well-placed threshold recovers "il 77–92 %" in the 4 contexts with A/F0.
- [unclear in source: the per-context figures printed are 92 %, 81 % and 80 % for the cities; the context giving 77 % is not shown.]
- **Deviations:** A cannot be evaluated on validation and inherits C's thresholds (9/10); episodes 2–3 excluded after the time pilot; R-orig control perimeter corrected; a generator reading branch fixed before commit (entry 15).

Original: `protocol/E8.md` (611d3541a6086e19), `protocol/E8bis.md` (0323686ceb957117); record: `CONGELAMENTO_E8.md` (e0d9f02b0f653d1d)

## E14 — Sensitivity to the non-causal static input (entry 21; stages 0, A, B)

- **Scope:** the static input carried a sensor's coverage over the whole series, test included. E14 measures the effect without retraining, with causal variants: (a) the new sensor's first 24 h; (b) the mean coverage of the initial sensors; (c) (amendment 12/10) a permutation among sensors of the same role.
- **Arms (stage A):** C, A, F0, F0′, F′(1 wk) (adaptation redone), R-orig(1 wk); episode 1 of each city, PEMS08 as zero-gap control.
- **Criteria:** stage 0: if the 90th percentile of |Δ| < 0.01 everywhere for (a), use (a) only. Stage A: a claim is insensitive if |Δ| < 0.002 and the interval keeps its sign; any sensitive claim triggers stage B. Stage B: if a verdict of (a)–(e) changes, causal code and full retraining, by "decisione del revisore" (reviewer's decision) with costs.
- **Outcome:** stage 0 "NON verificato" (not met); Δ = 0 for every PEMS sensor. Stage A: 8 of 72 claims sensitive, 0 sign changes, "almeno una sensibile → stadio B" (at least one sensitive → stage B).
- **Stage B** (`CONGELAMENTO_E14B.md`): variant (c) 16 of 54 claims sensitive, 1 verdict changes (Madrid ep. 3, (b), 0 → −); variant (a) 4 sensitive, 1 change (Melbourne ep. 2, (e), + → 0); the E7 decision does not change; PEMS controls max gap 6.0e-08. Full retraining followed as E15.
- **Deviations:** stage 0 recomputed on 13/10 with the correct critical class; correction of 2026-10-15 (entry 26).
- [unclear in source: stage B ran variants (c) and (a) only; the record cites "mandato del revisore 13/10" (reviewer's mandate of 13/10) without stating why (b) was left out.]

Original: `protocol/E14.md` (b30984ca153d3e5d); records: `CONGELAMENTO_E14.md` (9b1f7816addc51dd), `CONGELAMENTO_E14B.md` (58e774413c805d58)

## E15 — End-to-end causal campaign

- **Scope:** retrain with a causal static input and check the main claims. Initial sensors use coverage on [0, t0); a new sensor uses an expanding window from t0 to the origin (minimum 24 h). Three cities, episode 1, 3 partitions × seeds 201–206.
- **Arms:** trained E, E′, C, A, C_A (270 trainings); from the checkpoints F0, F0′, F′(1 wk), secondary F′(1 wk; k).
- **Criterion:** for the five claims (F0 − C, F0′ − C, F′(1 wk) − C, F′(1 wk) − A, A − C) the causal category (interval sign) is set next to the frozen one; "confirmed" if it coincides. If all five are confirmed, the causal campaign becomes the main result. A − C_A and C_A − C always reported.
- **Outcome:** "Le cinque dichiarazioni sono confermate in tutte e tre le citta'" (the five claims are confirmed in all three cities); the causal campaign is primary, the frozen one goes to the supplement.
- A − C_A: Madrid −0.0382 [−0.0431, −0.0335], London −0.0332 [−0.0374, −0.0290], Melbourne −0.0367 [−0.0467, −0.0256] ("l'identita' vale da sola", identity has value on its own); share of A − C explained by the extra data 0.048, 0.035, 0.186; zero-gap control 0.000e+00.
- **Deviations:** protocol readings of 27/10 transcribed (A and C_A use coverage on [0, t0)); record regenerated on 28/10 with an analysis-only addendum (7-bis) and the timing logs (7-ter), earlier numbers unchanged.
- [unclear in source: the per-city tables label the frozen column "54 celle" (54 cells); each city has 18 cells (54 over the three cities).]

Original: `protocol/E15.md` (31d731567da30bb4); record: `CONGELAMENTO_E15.md` (7577cec5134dbd38)

## E16 — Calibration (analysis only)

- **Scope:** how much of the transfer cost F0 − C is calibration? Inputs: per-cell probabilities of C, F0, F0′, F′(1 wk), A on the cities (episode 1) and PEMS08.
- **Methods:** post-hoc temperature scaling and vector scaling, fitted on validation only, each with two objectives (log-loss, wCE) reported separately; reliability diagrams, per-class ECE, log-loss, Brier, wCE.
- **Criterion:** calibration share s = 1 − (F0ᶜᵃˡ − Cᶜᵃˡ)/(F0 − C). "Calibration first, discrimination second" stands only if the lower bound of s exceeds 0.5 in all three cities; otherwise the reviewer's formulation is used. "Calibration alone" on PEMS08 is dropped in any case.
- **Outcome:** criterion not met for any of the four methods (temperature/vector × log-loss/wCE); s is reported.
- [unclear in source: the replacement wording ("the reviewer's formulation") is not given in the protocol or the record.]
- **Deviations:** A has no embeddings for validation sensors and is not calibrated; "A − C" after calibration uses raw A against calibrated C. The F′(1 wk) rows were later found to include the first week, non-causal for that arm (entry 27; corrected in E18, part C).

Original: `protocol/E16.md` (d37208e5fbb17d84); record: `CONGELAMENTO_E16.md` (1df4d91ef930bc95)

## E17 — Integrated policy, recovery and margins (analysis only)

- **Scope:** evaluate gated(1 wk, 0) — the token until one week, then F′(1 wk) for every sensor — as a complete policy, on episodes 2 and 3 (which did not formulate it), with episode 1 as reference and PEMS08/PEMS04 as extra rows; reclassify frozen verdicts; recovery; minimum equivalence margins.
- **Arms:** gated(1 wk, 0), gated(τ, N) as selected, F0′, C, F′(1 wk), A, R-orig(1 wk).
- **Criterion:** no pass/fail. Categories declared for the whole paper: superiority (interval below zero); non-inferiority (upper bound < δ, δ = 0.005 wCE); inconclusive. Measures: recovery (L_C − L_F′(1 wk))/(L_C − L_A); the smallest margin for R-orig(1 wk) ≡ F′(1 wk).
- **Outcome:** gated(1 wk, 0) − F0′ superiority in 11 of 11 contexts. Frozen gated(τ, N) − F0′: 8 superiority, 2 non-inferiority (Madrid ep. 3, Melbourne ep. 2), 1 inconclusive (PEMS08).
- Minimum equivalence margin (wCE): Madrid 0.0059, London 0.0049, Melbourne 0.0199, PEMS08 0.0792.
- **Deviations:** none declared. (E18 later qualifies δ as fixed after results; see below.)

Original: `protocol/E17.md` (dcacf323f9f5defb); record: `CONGELAMENTO_E17.md` (6b9e7e7634211a4c)

## E18 — Verification analyses from the second external review

Analysis of frozen artefacts only; pre-registered 28/10/2026, frozen 29/10/2026.

- **Part A, empirical ROC and pAUC:** per-cell ROC from the E16 probabilities, all distinct scores as thresholds (checked against `sklearn.metrics.roc_curve`: zero deviation); AUC, pAUC on FPR ∈ [0, 0.10], recall at FPR 0.5/1/2/5/10 %; it replaces the 19-threshold AUC of E8-bis. PEMS04 reconstructed (C, F0′, F′(1 wk) only); 13.1 machine-hours in all.
- **Outcome A:** A1 ΔAUC(F0 − C) < 0 confirmed in the three cities, PEMS08 includes zero; A2 ΔAUC(F0′ − F0) > 0 confirmed in the cities, not on PEMS08; A3 F′(1 wk) above C in recall at 1–10 % false alarms in the cities (0.5 % includes zero), at 5–10 % on PEMS08, at all five levels on PEMS04; A4 share of the argmax recall loss recovered at 5 % false alarms 0.918 / 0.839 / 0.802 (Madrid / London / Melbourne); A5 pAUC descriptive.
- **Part B, sensor-level bootstrap:** physical sensor IDs resampled with shared weights, 4,000 replicates; current intervals stay primary. Two category changes: Madrid ep. 3, F′(1 wk) − A, inferiority → inconclusive; PEMS08, gated(1 wk, 0) − F0′, superiority → inconclusive. The two non-inferiorities of gated(τ, N) − F0′ (Madrid ep. 3, Melbourne ep. 2) are unchanged. Smallest equivalence margins of R-orig(1 wk) ≡ F′(1 wk), current / sensor-level: 0.0059 / 0.0061, 0.0049 / 0.0049, 0.0199 / 0.0204, PEMS08 0.0792 / 0.0998.
- **Part C, correction 27:** F′(1 wk) rows of the E16 tables recomputed on origins older than one week for both arms, calibration parameters unchanged; blocking check passed (largest relative deviation 8.66e-07, threshold 1e-06).
- **Part D, policy provenance:** first written formulation of gated(1 wk, 0) on 2026-10-22; the eleven contexts were first observed on 2026-09-23 (episode 1), 2026-10-06 (episodes 2–3) and 2026-10-08 (PEMS08, PEMS04). Verdict: "valutazione post hoc descrittiva, senza conferma prospettica" (post hoc descriptive evaluation, without prospective confirmation).
- **TOST note:** minimum margins from 95 % bounds = TOST at α = 0.025 per side; δ = 0.005 was fixed when the upper bounds were known, so the two non-inferiorities are secondary post hoc analyses; the confirmatory synthesis is superiority in 8 of 11 contexts.
- **Deviations:** two E16 cells rebuilt on the Mac after a cross-machine deviation of 1.4–1.6e-06 (originals kept); PEMS04 has no E or A, so A1, A2 and A4 are not defined there.
- **Register entry 29:** the replacement of the 19-threshold claims is entry 29 (the protocol called it 28, a number already assigned); deviation declared in the record, §6. Part C was completed on 29/10 with per-class ECE, log-loss and Brier score on the same window; the part-A timings printed in the record come from `protocol/e18/tempi_parte_A.json` (first execution), as for E15; part D searches the history only up to the signature of the protocol (OR3 `964e4f5`, manuscript `ae12921`).

Original: `protocol/E18.md` (42da14831a4e982c); record: `CONGELAMENTO_E18.md` (2e56a7202de95383)
