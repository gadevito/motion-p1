# E12-sexies — How long does the same-instant signal last? (descriptive)

**Pre-registration.** Date 2026-11-09 · commit 51405aa (code `e12sexies.py` b63818d20231b388, `e12quinquies.py`
f26030d81d8bbadd, `e12ter.py` e8c8d17e99e4008b, `e12.py` 3ec453d15372b217, `p4b.py` 926061038a7472a3, `e9.py`
4dd5628af8879511; preflight log `e12sexies_preflight.log` 0466f504c339c15a; the earlier preflight on 4d6e7a0, with R primary, kept
as `e12sexies_preflight_4d6e7a0.log`) · launched by Fabio Palomba (Mac M3 Max, CPU) · preflight 6/6 · cost ≤ 0.4 s per (city, *f*, seed), ≈ 0.006 h for the 60 pairs (`e12sexies_costo.json`
48256fd6fbb82090, measured on 4d6e7a0, before the reference change, which computes the same number of sums; load average
3.2–3.4: an upper bound).

Draft of 2026-11-09, on the decision of the internal review of 2026-11-09 (12:15), after the frozen records of
E12-quater, E12-quinquies and E10-pred; reference changed the same day on the decision of the internal review (R×
primary, R secondary). No training, **descriptive**: no criterion and no statement of the paper
depends on a threshold. **No computation on test before the signature**, except the preflight, which reads no
test target.

signed: Gabriele De Vito; internal review, 2026-11-09

## Question

E12-quinquies measured that, within 250 m, most of the same-instant excess agreement between a hidden segment and
its nearest instrumented neighbour is not explained by the hour of the week (R 0.74–0.86 in Madrid and London;
R′ 0.80–0.95). E12-ter and E12-quater found that, for forecasts at 15–120 minutes, the neighbour adds no
consistent gain over the calendar, and E9, E11 and E10-pred found the same for learned models. E12-sexies asks
why: **how much of the same-instant signal survives when the neighbour's class at *t* is compared with the hidden
segment's class at *t* + *h*?** If it decays within 15 minutes, there is nothing for a forecaster to use; if it
persists, the methods evaluated do not use it.

## Design

**Perimeter, pairs and replicates: identical to E12 and E12-quinquies.** Three cities, *f* ∈ {10, 20, 40, 60}%,
seeds 0–4; node sets and origins of E9; pairs (test-hidden segment *i*, nearest observed segment *j*) at every
test origin *t*; static distance bin of *d*(*i*, *j*) as in E12 (0–250, 250–500, 500–1,000 and > 1,000 m); pooled
over the five seeds; E12's replicate indices.

**Lags.** *h* ∈ {0, 15, 30, 60, 120} min (0 and the forecasting horizons 1, 2, 4, 8 steps). Every *t* + *h* is a
step of the record (*t* + 8 is admissible for every origin by construction of E9).

**Slots.** The hour of the week (168 slots), from the timestamps alone, as in E12-ter and E12-quinquies; π_k(s)
are the class shares of the observed segments over the training period in slot *s* (E12-quinquies' function,
N_min = 20, fallback to π).

**Quantities, per (city, *f*, bin, *h*).**

| Symbol | Definition |
|---|---|
| A(*h*) | share of pairs with *y_i*(*t* + *h*) = *y_j*(*t*), over the pairs where both are valid. A(0) is E12's agreement |
| E×(*h*) | **primary reference:** Σ_k π_k(s_t)·π_k(s_{t+h}), with the slot of *t* for the neighbour's class and the slot of *t* + *h* for the hidden segment's, averaged over the same pairs: the agreement of two independent draws, each from the calendar of its own time. E×(0) is E12-quinquies' E_slot |
| R×(*h*) | **primary:** (A(*h*) − E×(*h*)) / (A(0) − E×(0)): the share of the same-instant signal that survives at lag *h*. R×(0) = 1 |
| E_slot(*h*), R(*h*) | **secondary:** Σ_k π_k(s)² with s = slot of *t* + *h* for both classes; R as R× with E_slot. It ignores the change of calendar between *t* and *t* + *h*, so it understates the independence agreement where the class shares change between the two slots: in the synthetic test without any signal, R(*h*) = −0.03 at 15 min and −0.22 at 120 min, R×(*h*) −0.01 and −0.00 |
| P(*h*) | own persistence of the hidden segment: share of (*i*, *t*) with *y_i*(*t* + *h*) = *y_i*(*t*), over the cells where both are valid; P(0) = 1 |
| R_own(*h*) | (P(*h*) − E×(*h*)) / (1 − E×(0)), with E× on the own-persistence cells: the comparison |

**Secondary reference** (preserves both marginals, as R′ in E12-quinquies): E′(*h*) = Σ_k π_k(s_t)·ρ_k(s_{t+h}),
with ρ_k(s) the class shares of the test-hidden segments over the test period in slot *s*; R′(*h*) = (A(*h*) −
E′(*h*)) / (A(0) − E′(0)). It uses test labels of hidden segments, admissible only because the analysis is
descriptive; it is reported beside R×, never in place of it, and never changes a reading. E′(0) is E12-quinquies'
E′_slot.

**Interval.** 4,000 replicates, seeds × corridor blocks, with E12's replicate indices (the same draws for every
*h*, so R×(*h*) is a ratio within one replicate). **Readable cells:** A(0) − E×(0) ≥ 0.02 and at least 3 blocks
in every seed; elsewhere R× is not reported or reported without interval, and marked. **Declared in advance:**
from E12-quinquies, A(0) − E×(0) (= A − E_slot there) within 250 m is 6–10 points in Madrid and 8–13 in London; at 250–500 m it is
1–2 points in Madrid and 2–4 in London, so R×(*h*) is read only within 250 m in those two cities; in Melbourne it
stays at 10–19 points up to 1,000 m (reported, without reading).

## Reading rule (declared, descriptive)

In the 0–250 m bin, for Madrid and London (8 cells), on R×(15):

| Reading | Condition |
|---|---|
| "the same-instant signal decays within 15 minutes" | U(R×(15)) < 0.5 |
| "the signal persists at 15 minutes and the methods evaluated do not use it" | L(R×(15)) > 0.5 |
| "undetermined" | otherwise |

The threshold 0.5 is a declared convention (internal review, 2026-11-09), as in E12-quinquies, not a test; the
rule is fixed knowing E12, E12-ter, E12-quater, E12-quinquies and E10-pred. R×(30), R×(60), R×(120), R(*h*), R′(*h*)
and R_own(*h*) are reported without a reading.

**Before the signature** (preflight, seed 0, validation origins, no test target read): valid pairs fall by 1–9%
from *h* = 0 to *h* = 120 min (Madrid 1–2%, London 3–9%, Melbourne 4–5%), so the five lags are computed on nearly
the same pairs.

## Mandatory controls (preflight, reading no test target)

1. Node sets, origins and nearest-neighbour pairs identical to E9 and E12 (fingerprints); E12 and E12-quinquies
   run records present for the 60 pairs.
2. At *h* = 0, on validation origins, pairs and agreements equal E12's concordance code per bin, the sums of
   E_slot and E′ equal E12-quinquies' code to the bit, and E× = E_slot.
3. For every validation and test origin, *t* + *h* is exactly *h* steps after *t* (timestamps only) and its slot is
   the hour of the week of *t* + *h*.
4. π_k(s) from observed segments and training-period cells only: noise on hidden segments and after the last
   training cell leaves it identical.
5. Synthetic test: a planted same-instant copy of a neighbour whose class has no memory beyond the calendar must
   give R×(*h*) close to 0 (|R×| < 0.05) at every lag; a planted copy of a persistent neighbour (stay probability
   0.95 per step) must give R×(15) above 0.8; in both, R×(0) = R(0) = 1 and P(0) = 1 exactly. End to end, the
   reading follows R× where R and R× disagree.

## What invalidates the experiment

The lags, the slot definition, the bins or the references changed after any test number; π_k(s) estimated from
hidden segments or from validation or test periods (except the declared secondary reference).

## Cost

No training; one pass over the test origins for 60 pairs and 5 lags, on CPU. Measured before the signature.

## What changes in the paper

- **Decays within 15 minutes:** the paper states that nearby labels carry a same-instant spatial signal that does
  not outlive the shortest forecasting horizon, which explains why it has no forecasting value at 15–120 minutes.
- **Persists:** the paper states that the signal is still present at 15 minutes and that neither the learned
  models (E9, E11, E10-pred) nor the calibrated tables (E12-bis, -ter, -quater) turn it into forecasting value; the
  reason is left as an open question.
- **Undetermined:** R×(*h*) is reported and the question stays open.

In every case R×(*h*) and R_own(*h*) are reported side by side in Table II.

## Files

- **Inputs:** as E12, plus the E12 and E12-quinquies run records.
- **Code:** `paper4/code/e12sexies.py`, importing `e12quinquies.py`, `e12ter.py`, `e12.py`, `p4b.py` and `e9.py`
  unchanged.
- **Outputs:** `paper4/runs/e12sexies/`; `CONGELAMENTO_E12sexies.md` generated by script.

## Deviations

None.
