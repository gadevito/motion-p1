# E12-quinquies — How much of the same-instant agreement remains once the hour is known? (descriptive)

**Pre-registration.** Date ____ · commit ____ (code `e12quinquies.py` ____, `e12.py` 3ec453d15372b217,
`p4b.py` 926061038a7472a3, `e9.py` 4dd5628af8879511; preflight log `e12quinquies_preflight.log` ____) · launched
by ____ (Mac M3 Max, CPU) · preflight ____ · cost ____.

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (21:45, item 3). No training,
**descriptive**: no criterion and no statement of the paper depends on a threshold. **No computation on test
before the signature**, except the preflight, which reads no test target.

signed: ____

## Question

E12 measured that, within 250 m, a hidden segment and its nearest instrumented neighbour are in the same class
at the same instant 8–16 points more often than independent draws from the instrumented segments' class
frequencies (Σ_k π_k²). E12-ter found that, for forecasts at 15–120 minutes, the neighbour adds no consistent gain
once the hour of the week is known. The paper reads the agreement as compatible with a shared calendar, but the
agreement is a same-instant quantity. E12-quinquies measures it directly: **how much of the excess agreement
remains when the independence reference is taken within each hour of the week?**

## Design

**Perimeter and pairs: identical to E12.** Three cities, *f* ∈ {10, 20, 40, 60}%, seeds 0–4; node sets and
origins of E9; pairs (test-hidden segment *i*, nearest observed segment *j* with a valid class at *t*) at every
test origin *t*; distance bins 0–250, 250–500, 500–1,000 and > 1,000 m; pooled over the five seeds as in E12.

**Slot.** The hour of the week of *t* (168 slots, day of week · 24 + hour), from the timestamp alone, as in
E12-ter.

**Quantities, per (city, *f*, bin).**

| Symbol | Definition |
|---|---|
| A | share of pairs with *y_i*(*t*) = *y_j*(*t*) (E12's agreement, recomputed and checked against E12) |
| E | Σ_k π_k², with π_k the class frequencies of the observed segments over the training period (E12's reference) |
| E_slot | Σ_s w_s Σ_k π_k(s)², with π_k(s) the class frequencies of the observed segments over the training period in slot *s*, and w_s the share of the bin's pairs in slot *s* |
| R | (A − E_slot) / (A − E): the share of the excess agreement that remains once the hour is known |

**Secondary reference** (preserves both marginals): E′_slot = Σ_s w_s Σ_k π_k(s)·ρ_k(s), with ρ_k(s) the class
frequencies of the hidden segments themselves in slot *s* over the test period. It uses test labels of hidden
segments, which is admissible only because the analysis is descriptive and A itself uses them; it is reported
beside E_slot, never in place of it. R′ is defined as R with E′_slot.

**Interval.** 4,000 replicates, seeds × corridor blocks, with E12's replicate indices; A, E_slot and R are
recomputed on each replicate (E from the training period is fixed). A bin with fewer than 3 blocks in some seed
is reported without interval and marked; R is not reported where A − E < 0.02.

## Reading rules (declared, descriptive)

In the 0–250 m bin, for Madrid and London:

| Reading | Condition |
|---|---|
| "most of the excess agreement is calendar" | U(R) < 0.5 |
| "most of the excess agreement is not calendar" | L(R) > 0.5 |
| "undetermined" | otherwise |

These rules are fixed knowing E12 and E12-ter; every statement is descriptive.

## Mandatory controls (preflight, reading no test target)

1. Node sets, origins and nearest-neighbour pairs identical to E12's on validation origins (fingerprints).
2. With one slot only, E_slot = E to the bit.
3. π_k(s) from observed segments and training-period origins only; noise on hidden segments and after the last
   training origin leaves them identical.
4. Synthetic test: a planted calendar with no spatial copy must give R close to 0; a planted copy with no calendar
   must give R close to 1.
5. A recomputed on validation origins equals the E12 code's agreement on the same origins.

## What invalidates the experiment

The slot definition, the bins or the references changed after any test number; π_k(s) estimated from hidden
segments or from validation or test periods (except the declared secondary reference).

## Cost

No training; one pass over test origins for 60 pairs, on CPU. Measured in the preflight.

## What changes in the paper

- **R small within 250 m:** the sentence "compatible with a shared calendar" becomes a measured decomposition of
  the same-instant agreement, with R.
- **R large:** most of the same-instant agreement is not calendar; the paper states that it does not translate
  into forecasting value at 15–120 minutes (E12-ter), and the two are reported side by side.
- **Undetermined:** the interpretation stays an interpretation, with R reported.

## Files

- **Inputs:** as E12, plus the E12 run records.
- **Code:** `paper4/code/e12quinquies.py`, importing `e12.py`, `p4b.py` and `e9.py` unchanged.
- **Outputs:** `paper4/runs/e12quinquies/`; `CONGELAMENTO_E12quinquies.md` generated by script.

## Deviations

None.
