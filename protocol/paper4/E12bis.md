# E12-bis — Does the label signal buy wCE once it is calibrated?

**Pre-registration.** Date _______ · commit _______ (code _______) · launched by Fabio Palomba (Mac M3 Max,
CPU) · preflight __/__ · cost _______.

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (11:40). No training. **No computation
on test before the signature**, except the preflight, which reads no test target.

## Question

E12 found that the labels of hidden segments agree with their nearest instrumented neighbour more often than
chance within about 250 m. Agreement there is 0.51–0.54 against 0.38–0.43 expected in Madrid and London. Yet
the neighbours' classes, used as they are, make the forecast worse than G0 by 9 to 144 points. The loss is a
calibration effect: a copied class is stated with probability close to 0.95 and is right about half the time.

E12-bis asks whether the same signal, calibrated on the instrumented segments alone, beats G0. It asks this
overall and, above all, within 250 m.

## Design

**Perimeter: identical to E9 and E12.** Three cities, *f* ∈ {10, 20, 40, 60}%, seeds 0–4. Node sets, admissible
origins, split and test-hidden segments are rebuilt as in E12 and checked against the E9 fingerprints. G0 and G1
come from the E9 runs of the same (city, *f*, seed).

**Calibration table, from observed segments only.** For each (city, *f*, seed):

- each observed segment *i* is paired with its nearest **other** observed segment *j* that has a valid class at
  origin *t*;
- pairs come from the training-period origins only (≤ the last training origin, as for the class weights);
- the counts are tabulated as *n*(*y_i*(*t* + *h*) = *a* | *y_j*(*t*) = *b*, bin of *d*(*i*, *j*), *h*), giving
  one 3 × 3 table per distance bin and per horizon *h*;
- distance bins: 0–250, 250–500, 500–1,000, > 1,000 m;
- the table row is the conditional distribution *q*(·| *b*, bin, *h*);
- a row with no count in a bin falls back to the prior, and the fallbacks are counted.

**Prediction for a hidden segment.** At origin *t* and horizon *h*:

- take its nearest observed segment with a valid class *b* at *t*, at distance *d*;
- read *q* = *q*(·| *b*, bin(*d*), *h*);
- apply the same transformation as E12: *q*′ = 0.95·*q* + 0.05·prior, then *p* ∝ W·*q*′;
- the unweighted *q*′ is kept as a secondary column.

The only quantities estimated from data are the table, the prior and the class weights, all from the training
period of the observed segments. Nothing is fitted on validation or test.

## Metrics and resample

As in E12:

- wCE on test-hidden segments, mean over the four horizons;
- V = mean over seeds of 100·(wCE(G0) − wCE)/wCE(G0), positive when E12-bis is better than G0;
- 4,000 replicates, seeds × corridor blocks, with E9's replicate indices (`default_rng([20261106, index of
  (city, f)])`).

**V is computed overall and per distance bin.** The bin of a hidden segment is the distance to its nearest
observed segment, fixed per segment (the segment's static nearest neighbour). Per-bin V uses the test-hidden
segments of that bin and the blocks that hold them. A bin with fewer than 3 blocks in some seed is reported
without interval and marked.

## Criterion, with threshold

**"The label signal buys wCE"** if V is favourable (L > 0) and V ≥ 3 points **in the 0–250 m bin**, in at least
2 of the 3 cities, at some level *f*.

**Derived statement:**

| Statement | Condition |
|---|---|
| **"the label signal buys wCE within 250 m at f"** | the criterion holds; the levels *f* are named |
| **"the calibrated label signal does not buy wCE within 250 m"** | in the 0–250 m bin, U < 3 in every city and at every *f* |
| **"undetermined"** | every other case, reported with the counts |

There is no correction for multiple comparisons; this is declared, as in E12.

**Secondary:**

- V(E12-bis) − V(G1 of E9), overall and in the 0–250 m bin;
- V overall and in the other bins, with both reading scales.

**Reported without a criterion:**

- the calibration tables themselves (diagonal mass per bin and horizon);
- the share of test-hidden segments in each bin;
- V per horizon;
- the unweighted column;
- red recall at 5% false alarms with the realised false-alarm rate. Because the prediction takes at most
  3 × 4 × 4 distinct values per segment, the 5% target may not be met, as in E12; the realised rate is reported
  next to it and recall is not read as discrimination when the two coincide.

## Mandatory controls (preflight, reading no test target)

1. Node sets, origins and class weights identical to the E9 fingerprints for the 60 (city, *f*, seed) pairs.
2. The calibration pairs contain observed segments only, on both sides, and training-period origins only.
   Noise on hidden segments and on every value after the last training origin leaves the tables identical
   to the bit.
3. Causality of the prediction: noise after *t* and on hidden segments leaves *q* at *t* identical.
4. Every *p* is a probability on a sample of validation cells.
5. Synthetic test with a planted signal: hidden classes copied from the nearest observed segment with
   probability 0.9 within 250 m and 0.4 beyond. The calibrated predictor must beat the prior in the 0–250 m
   bin and must do so more strongly than in the outer bins.
6. The red-recall threshold is chosen on validation-hidden segments and saved with fingerprint before any test
   metric; the run refuses to compute a test metric without it.

## What invalidates the experiment

- the bins, ε, the neighbour rule or the transformation changed after any test number;
- any table cell estimated from hidden segments or from validation or test periods;
- node sets or origins different from E9's;
- a G0 other than the E9 run of the same (city, *f*, seed).

## Cost

No training; one pass over training origins (tables) and test origins (prediction) for 60 pairs, on CPU.
Measured in the preflight.

## What changes in the paper

- **"Buys wCE within 250 m":** the short-range label signal is usable once calibrated, and the learned
  propagation leaves it on the table. The value of a nearby sensor is then measurable, and E10-geo says how many
  uncovered segments placement can bring within that radius.
- **"Does not buy wCE":** the agreement measured in E12 is too weak, once calibrated, to improve on the model
  without spatial exchange. The neighbour signal is then a property of the labels, not a forecasting resource.
- **"Undetermined":** reported with the counts.

## Files

- **Inputs:** as E12 (E9 campaign, targets, sensors, road graphs).
- **Code:** `paper4/code/e12bis.py`, written after the approval of this draft; it imports `p4b.py`, `e9.py` and
  `e12.py` unchanged.
- **Outputs:** `paper4/runs/e12bis/`; `CONGELAMENTO_E12bis.md` generated by script.

## Deviations

None.
