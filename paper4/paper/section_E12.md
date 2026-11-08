# Paper 4 — draft of the E12 section (is there a spatial signal?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_E12.md` (frozen record of E12,
commit 085bda7, fingerprint 0be136a3886173bc). E12 trains nothing. It uses the hidden segments, origins and node
sets of E9, and the G0 of E9 as reference.

---

## E12 — do the labels carry a spatial signal, and can simple predictors use it?

E9 left two readings open:

- the hidden segments carry no signal their instrumented neighbours could pass on;
- or the learned propagation does not use a signal that is there.

E12 looks at the labels themselves first, and then at four predictors that need no training.

**The labels carry a short-range signal.** The table gives the share of pairs (hidden segment, nearest
instrumented segment) in the same congestion class at the same instant, by distance between the two (test
period, pooled over five seeds). The last column is the agreement expected if the two classes were independent
draws from the instrumented segments' class frequencies (Σπ²).

| City | *f* | 0–250 m | 250–500 m | 500–1,000 m | > 1,000 m | Expected (Σπ²) |
|---|---|---|---|---|---|---|
| Madrid | 10% | 0.511 | 0.439 | 0.445 | 0.453 | 0.433 |
| Madrid | 20% | 0.528 | 0.461 | 0.431 | 0.414 | 0.423 |
| Madrid | 40% | 0.522 | 0.454 | 0.449 | 0.539 | 0.424 |
| Madrid | 60% | 0.544 | 0.457 | 0.434 | — | 0.424 |
| London | 10% | 0.519 | 0.463 | 0.442 | 0.422 | 0.413 |
| London | 20% | 0.518 | 0.455 | 0.433 | 0.447 | 0.385 |
| London | 40% | 0.526 | 0.451 | 0.437 | 0.484 | 0.393 |
| London | 60% | 0.536 | 0.441 | 0.438 | — | 0.379 |
| Melbourne | 10% | 0.761 | 0.801 | 0.761 | 0.624 | 0.647 |
| Melbourne | 20% | 0.755 | 0.771 | 0.769 | 0.629 | 0.576 |
| Melbourne | 40% | 0.771 | 0.715 | 0.710 | 0.652 | 0.579 |
| Melbourne | 60% | 0.792 | 0.794 | 0.745 | 0.611 | 0.596 |

Each cell pools between 8,596 and 2.7 million pairs; the counts are in the frozen record. Bins above 1,000 m
with fewer than 51,000 pairs (Madrid and London at 40%) are the least stable.

Within 250 m, agreement exceeds the independence level by 8–12 points in Madrid and 11–16 in London. It then
falls to within a few points of it beyond 250 m. In Melbourne agreement is high at every distance below
1,000 m (0.71–0.80, against 0.58–0.65), and drops beyond 1,000 m, where most pairs lie. A hidden segment's class
is therefore more often that of a close instrumented neighbour than chance would give. The signal is real, and
short.

**Simple predictors turn it into a loss.** Four predictors were compared with G0 on the same hidden segments:

- the class of the nearest instrumented neighbour, persisted to the horizon;
- two inverse-distance averages of the neighbours' current classes (4 nearest; all within 500 m);
- the neighbours' class frequencies by weekly slot.

The class estimate is mixed with the class prior (ε = 0.05) and reweighted by the class weights. **No
non-learned predictor beats G0**: V favourable and ≥ 3 points in 0 of 12 (city, *f*) pairs for every predictor.

| Predictor | V range against G0 |
|---|---|
| P-nn and P-idw4 | −58 to −144 points |
| P-hist4 | −9 to −21 points in Madrid and London; −32 to −61 in Melbourne |
| P-idw500 | close to the prior wherever it falls back on it (−49 to +2.3 points) |

P-nn and P-idw4 copy a class with probability close to 0.95 and are right about half the time.

The class prior itself lies 1.4–4.5 points below G0 in Madrid and London: what G0 adds over the prior is the
calendar. In Melbourne the prior is within ±3.4 points of G0.

The pre-registered statement is "undetermined" only because the interval of P-idw500 in Melbourne at 10%
reaches +7.2 (+2.28 [−3.10; +7.20]). There, 98% of hidden segments have no instrumented segment within 500 m,
and the predictor falls back to the prior.

The size of these losses is a calibration effect, not an absence of signal. A predictor that copies a
neighbour's class is right about half the time within 250 m, but with ε = 0.05 it states that class with
probability close to 0.95. The weighted cross-entropy penalises the confident errors more than it rewards the
correct calls. The same holds at every horizon: V barely changes from 15 to 120 min.

**Operational reading, with a caveat.** For predictors whose probabilities take few distinct values, the
threshold for 5% false alarms on validation cannot be met on test. Realised false-alarm rates range from 3% to
100%, and red recall follows them. The prior and the fallbacks of P-idw500 give recall = false alarms = 1.000.
These recall figures are not read as discrimination.

> **The labels of segments without a sensor agree with their nearest instrumented neighbour more often than
> chance, but only within about 250 m; used as they are, the neighbours' classes make the forecast worse than
> the model without spatial exchange.**

**With block placement, almost no hidden segment lies within the radius of the signal.** The share of hidden
segments with no instrumented segment within 500 m is 65% at 10% coverage and 24% at 40% in Madrid; in
Melbourne it is 85–98% at every coverage.

Whether a calibrated use of the same signal buys wCE is the question of E12-bis. How far placement can bring
uncovered segments within that radius is the question of E10-geo.
