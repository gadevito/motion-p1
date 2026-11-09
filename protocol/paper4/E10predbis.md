# E10-pred-bis — The placement comparison of E10-pred under common class weights (correction)

**Pre-registration.** Date 2026-11-09 · commit 89a0cb7 (code `e10predbis.py` a44a24bf84fe56c8, `e10pred.py` c1575d5f166b980e, `e12bis.py`
27adfe03f24647e8, `genera_congelamento_e11.py` 05b321ed3f946141, `genera_congelamento_e9.py` 6b9a0552efea3af6,
`p4b.py` 926061038a7472a3, `e9.py` 4dd5628af8879511; preflight log `e10predbis_preflight.log` d0893bb1c7a5b178) ·
launched by Fabio Palomba (Mac M3 Max, CPU) · preflight 5/5 · cost: no training, one scoring pass over the 60 saved
prediction files, as the freeze of E10-pred (minutes).

Draft of 2026-11-09, on the decision of the internal review of 2026-11-09 (15:15, item 1; register of corrections,
item 23). No training: the saved per-cell predictions of E10-pred and of E9 at *f* = 20% are scored again. **No
computation on test before the signature**, except the preflight, which reads no test target.

signed: Gabriele De Vito; internal review, 2026-11-09

## Why

E10-pred scored each design with the class weights of its own configuration (`e10pred.py`, `cell_for`:
`node_sums(p, y, keep, rec["class_weights"])`), computed from the observed segments of that design. On the common
test-hidden segments the two placements were therefore judged by different functions: in Melbourne, seed 0, the
weights are about (0.455, 1.544, 6.552) under uniform placement and (0.474, 1.450, 4.969) with blocks. Δ mixed the
change of predictions with the change of the score. V(G1) within one design is not affected (G0 and G1 of a design
share its weights).

## Design

**Inputs: unchanged.** The 30 runs of E10-pred and the 30 runs of E9 at *f* = 20% (`test_hidden.npz`, fingerprints
checked against their run records); the same common test-hidden segments (hidden in both designs, per seed), the
same seeds × corridor blocks and the same replicate draws as E10-pred (`default_rng([20261106, 100 + city])` for V,
with `[…, 1]` for Δ); 4,000 replicates.

**Common class weights, one vector per city.** w_k = N / (3·N_k), with N_k the number of cells of class *k* over the
training period (the cells before the first validation origin, as `p4b`'s `reg_end`) on **all segments** of the city,
observed and hidden, and N = Σ N_k. They depend on neither the design, nor the seed, nor any validation or test
cell; the training period is the same in both designs and every seed (checked).

**Quantities, per city.**

| Quantity | Definition |
|---|---|
| Δ_G0, Δ_G1 (primary) | 100·(wCE_blocks − wCE_uniform)/wCE_blocks on the common segments, both scored with the common weights; positive when uniform placement forecasts them better |
| V(G1) per design (control) | V of E10-pred on each design's own test-hidden segments, scored with the common weights |
| Δ and V with the design weights | recomputed by the same code and required to equal the frozen record of E10-pred to the bit (a check, not a result) |

**Reading (declared, descriptive), per city and model on Δ:** "uniform placement forecasts the common segments
better" if L > 0; "worse" if U < 0; "no difference detected" otherwise. No threshold, no criterion; the 3-point
scale of E10-pred is reported as in E10-pred for V(G1).

**Before the signature** (preflight, no target read): the common weights (free flow, slowed, congested) are
(0.719, 0.744, 3.758) in Madrid, (0.757, 0.823, 2.155) in London and (0.446, 1.620, 7.138) in Melbourne; at seed 0
the design weights are (0.709, 0.755, 3.784) / (0.688, 0.778, 3.831), (0.770, 0.818, 2.089) / (0.824, 0.765, 2.084)
and (0.455, 1.544, 6.552) / (0.474, 1.450, 4.969), uniform / blocks. The difference is largest on the congested
class in Melbourne.

## Mandatory controls (preflight, reading no test target)

1. The 60 run records present, with the fingerprints of their `test_hidden.npz` (files not opened); setups equal
   to E9's (blocks) and to E10-pred's uniform rule.
2. `reg_end` and the common weights identical for the five seeds and the two designs of a city; computed from the
   training period only: noise after `reg_end` leaves them identical; positive and finite.
3. The design weights stored in the run records equal those recomputed by `p4b` for each design (so the check of
   the run compares like with like).
4. Synthetic: with identical predictions under the two designs Δ = 0 whatever the weights; with the design weights
   the new scoring function reproduces `e10pred.cell_for` to the bit; changing only the weights of one design changes
   Δ while leaving the other design's V(G1) unchanged.
5. A test metric is refused while the E10-pred-bis signature line is blank.

## What changes in the paper

§III-D and Table IV report Δ with the common weights, in place of the Δ of E10-pred; V(G1) within each design stays
as in E10-pred, with the control column beside it. The text separates "the graph gains nothing under uniform
placement" (V(G1)) from "placement changes, or does not change, the forecasts" (Δ).

## Files

- **Code:** `paper4/code/e10predbis.py`, importing `e10pred.py`, `e12bis.py`, `genera_congelamento_e11.py`,
  `genera_congelamento_e9.py`, `p4b.py` and `e9.py` unchanged.
- **Output:** `CONGELAMENTO_E10predbis.md` and `e10predbis_risultati.json`, generated by script.

## Deviations

None.
