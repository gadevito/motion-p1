# E10-pred — Does placement change what is forecastable on the uncovered segments?

**Pre-registration.** Date ____ · commit 53911d0 (code `e10pred.py` c1575d5f166b980e, `p4b.py` 926061038a7472a3,
`e9.py` 4dd5628af8879511, `genera_congelamento_e9.py` 6b9a0552efea3af6, `genera_congelamento_e11.py`
05b321ed3f946141; preflight log `e10pred_preflight.log` 6f3427abe71b7543) · launched by Fabio Palomba (Mac M3 Max,
MPS) · preflight 8/8 · cost: measured by the executor before the signature with `e10pred.py cost` (G0 and G1
isolated, Madrid, *f* = 20%, uniform placement, uptime before and after in `e10pred_costo.json` ____); upper bound
from the isolated costs of E9, ≈ 1.1 h.

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (21:45, item 4); approved at 22:00 with
the declaration of the input masks and their realised share. **30 trainings. No
computation on test before the signature**, except the preflight, which reads no test target.

signed: ____

## Question

E10-geo showed that uniform placement brings far more uncovered segments within 250 m of a sensor than block
placement. The paper inferred that this proximity buys no forecast from E9 and E12-bis/E12-ter, which were all run
on block placements; that transfer assumes that only the distance to the nearest sensor changes, not the
composition of the neighbours, the topology or the data. E10-pred tests it directly: **with the observed segments
drawn uniformly, does the graph model gain over the model without spatial exchange, and are the uncovered
segments forecast better than with blocks?**

## Design

**Perimeter.** Madrid, London and Melbourne; *f* = 20%; seeds 0–4; arms G0 and G1 (road graph), as in E9;
U = 1,000 updates, the E9 budget, with E9's checkpoints and selection on validation-hidden segments. 3 cities × 5
seeds × 2 arms = **30 trainings**.

**Node sets (the one change).**

1. **Observed:** round(0.2·K) segments drawn uniformly at random among the K segments, with a new stream
   `default_rng([seed, 7])` (k = 7; streams 1–6 of `p4b.py` unchanged).
2. **Validation-hidden and test-hidden:** the remaining segments, assigned in whole cells of E9's grid
   (11 × 11, 11 × 11, 15 × 15) by E9's deficit rule, with targets 0.2 and 0.6 of K (E9 at *f* = 20%), in the
   order of stream 1.
3. Per-batch input masks as in E9: a share *u* ~ U(0.6, 0.95) of the cells that hold observed segments, in whole
   cells, restricted to observed segments. **Declared:** with uniform observed segments most cells hold 1–3 of
   them, so this mask is close to a uniform draw of observed segments, while in E9 it draws whole corridors. The
   realised share of observed segments in input is recorded for every batch of every run, and the same quantity is
   recomputed for the E9 runs at *f* = 20% by replaying their mask stream (`default_rng([seed, 2])`, no training),
   so that the comparison with E9 has no hidden factor.

Everything else is `p4b.py` and `e9.py` unchanged: inputs, class weights and normalisation from observed segments
in the training period, origins, model, training, wCE.

**Before the signature** (preflight, seed 0, no target read): with uniform placement the median distance from a
test-hidden segment to the nearest observed one is 57, 76 and 162 m in Madrid, London and Melbourne, against 461,
327 and 2,213 m with the blocks of E9; observed segments occupy 41, 35 and 33 grid cells against 11, 9 and 12. The
mean share of observed segments in input per batch is the same in the two designs (0.76–0.78; 5–95% range 0.57–0.95
uniform, 0.49–0.97 blocks). The common test-hidden segments are 344, 332 and 221, in 21, 25 and 29 blocks.

**References from E9.** The E9 runs at *f* = 20% (blocks), same cities and seeds, arms G0 and G1, with their
per-cell predictions.

## Metrics and resample

wCE on test-hidden segments, mean over the four horizons; V(G1) = mean over seeds of
100·(wCE_G0 − wCE_G1)/wCE_G0; 4,000 replicates, seeds × blocks (the cells of the test-hidden sets).

**Primary (each design on its own test-hidden segments):** V(G1) with uniform placement, per city.

**Secondary (common segments):** the segments that are test-hidden in both the uniform and the block design of the
same seed. On them, paired by segment: wCE of G1 (and of G0) with uniform placement against blocks,
Δ = 100·(wCE_blocks − wCE_uniform)/wCE_blocks, positive when uniform placement forecasts them better. A city with
fewer than 3 common blocks in some seed is reported without interval and marked.

## Criterion, with threshold

**"Placement changes what is forecastable"** if, with uniform placement, V(G1) is favourable (L > 0) and V ≥ 3
points in at least 2 of the 3 cities.

| Statement | Condition |
|---|---|
| **"placement changes what is forecastable"** | the criterion holds; the cities are named |
| **"placement does not change what is forecastable"** | U < 3 for V(G1) in every city |
| **"undetermined"** | every other case, reported with the counts |

No correction for multiple comparisons, declared. Δ on the common segments is read on the two scales (sign of the
interval; 3-point margin) without a derived statement.

**Reported without a criterion:** wCE of G0 and G1 per design; V per horizon; per design, the median distance
from a test-hidden segment to the nearest observed one (to set against E10-geo), the number of grid cells with at
least one observed segment, and the realised share of observed segments in input per batch (mean and 5–95%
range); red recall at 5% false alarms with the realised false-alarm rate.

## Mandatory controls (preflight, reading no test target)

1. Realised observed share 0.2 ± 0.005 of K; validation and test sets are unions of whole cells; the three sets
   are disjoint and cover K.
2. No hidden index enters input, loss, normalisation, historical mean or class weights (the E9 preflight assertion,
   on every batch of the preflight run).
3. Streams 1–6 give the same values as in E9 for the same seed; stream 7 changes only the observed draw.
4. The E9 runs at *f* = 20% are present, with the fingerprints of the E9 frozen record.
5. The common test-hidden set is non-empty in every (city, seed), and its block counts are logged.
6. Determinism: two runs of the preflight configuration give identical weights.
7. Red-recall thresholds chosen on validation-hidden segments and saved with fingerprint before any test metric.

## What invalidates the experiment

The observed draw, the grid, the targets, U or the selection rule changed after any test number; any hidden
segment in input, loss or statistics; references other than the E9 runs of the same seeds.

## Cost

30 trainings; from the isolated costs of E9 on Madrid (G0 ≈ 89 s, G1 ≈ 169 s), at most 15 × (89 + 169) s ≈ 1.1 h.
Measured again in the preflight.

## What changes in the paper

- **"Changes what is forecastable":** placement matters for the uncovered segments; §III-D and the conclusion say
  so, with V and Δ; the sentence "not how well they are forecast" is withdrawn.
- **"Does not change":** the sentence stands, now measured on uniform placement, with Δ on the common segments.
- **"Undetermined":** the sentence is withdrawn and E10-geo is reported as a geometric result only.

## Files

- **Inputs:** as E9, plus the E9 runs at *f* = 20%.
- **Code:** `paper4/code/e10pred.py`, importing `p4b.py` and `e9.py` unchanged; the uniform node-set rule is in
  `e10pred.py`.
- **Outputs:** `paper4/runs/e10pred/`; `CONGELAMENTO_E10pred.md` generated by script.

## Deviations

None.
