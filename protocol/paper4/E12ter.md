# E12-ter — Does the neighbour add to the calendar?

**Pre-registration.** Date _______ · commit _______ (code `e12ter.py` _______, `e12bis.py` 27adfe03f24647e8,
`e12.py` 3ec453d15372b217, `p4b.py` 926061038a7472a3, `e9.py` 4dd5628af8879511; preflight log `e12ter_preflight.log`
_______) · launched by Fabio Palomba (Mac M3 Max, CPU) · preflight _/_ · cost _______.

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (13:00). No training. **No computation
on test before the signature**, except the preflight, which reads no test target.

signed: _______

## Question

E12-bis calibrated the nearest instrumented neighbour's class on the instrumented segments, by distance bin and
horizon. It did not beat G0: within 250 m, V lies between −2.8 and −1.1 points in Madrid and London. The
calibrated table knows the neighbour but not the time of day. G0 knows the calendar, and E12 showed that the
calendar is what G0 adds over the class prior.

E12-ter gives the table the calendar too. It asks two things:

- does the neighbour's class, calibrated **together with the weekly slot**, beat G0 within 250 m?
- how much does the neighbour add to a table that knows the calendar alone?

The difference between the two tables isolates the value of the neighbour net of the calendar, with an interval.

## Design

**Perimeter: identical to E9, E12 and E12-bis.** Three cities, *f* ∈ {10, 20, 40, 60}%, seeds 0–4.

- Node sets, admissible origins, split and test-hidden segments are rebuilt as in E12-bis and checked against
  the E9 fingerprints.
- G0 and G1 come from the E9 runs of the same (city, *f*, seed).
- The E12-bis sums of the same (city, *f*, seed) are read from `paper4/runs/e12bis/`, with fingerprint.

**Slot: hour of the week of the target time *t* + *h*, 168 slots** (24 hours × 7 days; slot = day of week · 24 +
hour). This is the choice the review asked to declare. The finer 15-minute weekly slot (672) is not used, since
it would split the table four times further. The slot comes from the timestamp of *t* + *h* alone. The
admissible origins guarantee that *t* + *h* lies exactly *h* steps of 15 minutes after *t*, so the slot is the
calendar of the target, known at *t*. No value of a hidden segment, and no value after *t*, enters it.

**Two tables, from the same pairs.** The pairs are those of E12-bis:

- each observed segment *i* is paired with its nearest **other** observed segment *j* that has a valid class at
  origin *t*;
- origins come from the training period only;
- distance bins are 0–250, 250–500, 500–1,000 and > 1,000 m.

From the same pairs (same cells, same validity mask), two tables:

| Table | Counts | Row |
|---|---|---|
| **E12-ter** | *n*(*y_i*(*t* + *h*) = *a* \| slot(*t* + *h*), *y_j*(*t*) = *b*, bin of *d*(*i*, *j*), *h*) | *q*(·\| slot, *b*, bin, *h*) |
| **Calendar only** | *n*(*y_i*(*t* + *h*) = *a* \| slot(*t* + *h*), *h*) | *q*(·\| slot, *h*) |

Summed over slots, the E12-ter table is the E12-bis table, to the bit. The two tables differ only by the
neighbour's class and distance bin.

**Rows with few pairs.** A row of either table with fewer than **N_min = 20** pairs is not used:

- an E12-ter row falls back to the E12-bis row (*b*, bin, *h*), and that one to the prior if it is empty (the
  E12-bis rule);
- a calendar row falls back to the prior.

Every fallback is counted and reported, overall and in the 0–250 m bin.

N_min was set before the signature, from the counts of the training tables and the lookups made by the
validation-hidden segments. These read only the classes of observed segments. In the 0–250 m bin, 1–6% of the
validation lookups fall below 20 pairs, and the median row holds 160–5,000 pairs. In the outer bins of Madrid
and London most rows hold fewer than 20 pairs, so the outer bins of E12-ter mostly reproduce E12-bis there. The
preflight log reports these shares for every (city, *f*), seed 0.

**Prediction for a hidden segment.** At origin *t* and horizon *h*:

- take its nearest observed segment with a valid class *b* at *t*, at distance *d*;
- read *q* = *q*(·\| slot(*t* + *h*), *b*, bin(*d*), *h*) for E12-ter, or *q* = *q*(·\| slot(*t* + *h*), *h*) for the
  calendar;
- apply the same transformation as E12 and E12-bis: *q*′ = 0.95·*q* + 0.05·prior, then *p* ∝ W·*q*′;
- the unweighted *q*′ of E12-ter is kept as a secondary column.

The only quantities estimated from data are the two tables, the prior and the class weights, all from the
training period of the observed segments. Nothing is fitted on validation or test.

## Metrics and resample

As in E12-bis:

- wCE on test-hidden segments, mean over the four horizons;
- V = mean over seeds of 100·(wCE(G0) − wCE)/wCE(G0), positive when the predictor is better than G0;
- 4,000 replicates, seeds × corridor blocks. Overall V uses E9's replicate indices (`default_rng([20261106,
  index of (city, f)])`); per-bin V uses `default_rng([20261106, index of (city, f), 1 + bin])`.

**V is computed overall and per distance bin.** The bin of a hidden segment is the distance to its nearest
observed segment, fixed per segment, as in E12-bis. A bin with fewer than 3 blocks in some seed is reported
without interval and marked.

**Differences** between two predictors are computed on the same replicates (paired). The difference of V is
the difference of mean relative wCE gains over G0.

## Criterion, with threshold (identical to E12-bis)

**"Neighbour and calendar buy wCE"** if V(E12-ter) is favourable (L > 0) and V ≥ 3 points **in the 0–250 m bin**,
in at least 2 of the 3 cities, at some level *f*.

| Statement | Condition |
|---|---|
| **"neighbour and calendar buy wCE within 250 m at f"** | the criterion holds; the levels *f* are named |
| **"neighbour and calendar do not buy wCE within 250 m"** | in the 0–250 m bin, U < 3 in every city and at every *f* |
| **"undetermined"** | every other case, reported with the counts |

There is no correction for multiple comparisons; this is declared, as in E12 and E12-bis.

**Secondary: the value of the neighbour net of the calendar.**

- D = V(E12-ter) − V(calendar only), overall and per bin, with paired interval;
- V(calendar only) against G0, overall.

D is read on the two scales:

| Reading | Condition |
|---|---|
| the neighbour adds to the calendar | L > 0 |
| it removes from it | U < 0 |
| inconclusive | otherwise |

The 3-point margin is attained if D ≥ 3, and excluded if U < 3. No statement is derived from D; it is reported
per (city, *f*) and bin.

**Reported without a criterion:**

- V(calendar only) in the 0–250 m bin;
- V(E12-ter) − V(E12-bis), overall and in the 0–250 m bin, paired: what the calendar adds to the neighbour;
- V per horizon;
- the unweighted column;
- the fallback shares;
- red recall at 5% false alarms, **descriptive only**, for E12-ter and the calendar, always with the realised
  false-alarm rate next to it (thresholds on validation-hidden segments).

## Mandatory controls (preflight, reading no test target)

1. Node sets, origins and class weights identical to the E9 fingerprints for the 60 (city, *f*, seed) pairs.
2. Both tables come from observed→observed pairs and training-period origins only.
   - Summed over slots, the E12-ter table equals the E12-bis table to the bit.
   - Noise on hidden segments and on every value after the last training origin leaves both tables identical.
3. **Slots from *t* + *h*, never from data.**
   - The slot is computed from the timestamps alone and equals the 15-minute weekly slot of `p4b.py` divided
     by 4.
   - For every training, validation and test origin and every *h*, the timestamp of *t* + *h* is exactly *h*
     steps after that of *t*.
   - The run repeats this check for each (city, *f*, seed) and stops if it fails.
4. Causality of the prediction: noise after *t* and on hidden segments leaves *q* at *t* identical.
5. Every *p*, of E12-ter and of the calendar, is a probability on a sample of validation cells.
6. Synthetic test with a planted calendar and a planted short-range copy. Weekday peaks (7–10 h and 17–20 h) lean
   towards red. Hidden classes are copied from a cluster shared within about 60 m with probability 0.9. The
   checks:
   - the calendar must beat the prior;
   - E12-ter must beat the calendar in the 0–250 m bin, and more strongly than in the outer bins.
7. The red-recall thresholds are chosen on validation-hidden segments and saved with fingerprint before any test
   metric; the run refuses to compute a test metric without them. The E12-bis run records of the 60 pairs are
   present, with matching sums fingerprints and setup.

## What invalidates the experiment

- the slot definition, N_min, the bins, ε, the neighbour rule or the transformation changed after any test
  number;
- any table cell estimated from hidden segments or from validation or test periods;
- a slot computed from anything but the timestamp of *t* + *h*;
- node sets or origins different from E9's;
- a G0 other than the E9 run of the same (city, *f*, seed).

## Cost

No training; one pass over training origins (tables) and test origins (prediction) for 60 pairs, on CPU, as
E12-bis. Measured in the preflight.

## What changes in the paper

- **"Buy wCE within 250 m":** the label signal is a forecasting resource once it is calibrated with the
  calendar. A sensor within 250 m is then worth a measurable gain on the uncovered segment. E10-geo says how many
  uncovered segments each placement rule brings within that radius.
- **"Do not buy wCE":** even calibrated with the calendar, a nearby instrumented neighbour does not improve on the
  model without spatial exchange. D says how much of the little the neighbour carries survives the calendar.
- **"Undetermined":** reported with the counts, and D read on its own.

## Files

- **Inputs:** as E12-bis, plus the E12-bis runs.
- **Code:** `paper4/code/e12ter.py`, written after the review's decision of 2026-11-08 (13:00); it imports
  `p4b.py`, `e9.py`, `e12.py` and `e12bis.py` unchanged.
- **Outputs:** `paper4/runs/e12ter/`; `CONGELAMENTO_E12ter.md` generated by script.

## Deviations

None.
