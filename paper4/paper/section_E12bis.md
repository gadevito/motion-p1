# Paper 4 — draft of the E12-bis section (what is the label signal worth once calibrated?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_E12bis.md`. That is the frozen
record of E12-bis, commit 40adfc9, fingerprint 11e89874e3b100b8. E12-bis trains nothing. It uses the hidden
segments, origins and node sets of E9, and the G0 and G1 of E9 as references.

V is in points of the G0 wCE, positive when the predictor is better than G0. Intervals are 95%, from the joint
resample of seeds and corridor blocks.

---

## E12-bis — does the neighbour's class buy wCE once it is calibrated?

E12 found a label signal that is real but short: within about 250 m, a hidden segment shares its nearest
instrumented neighbour's class more often than chance. Copied as they are, the neighbours' classes lost to G0 by
58 to 144 points, because a class right about half the time was stated with probability close to 0.95.

E12-bis replaces the copy with a calibrated table, estimated on the instrumented segments alone:

- in the training period, each instrumented segment is paired with its nearest other instrumented segment;
- the pairs are counted as "own class at *t* + *h* given the neighbour's class at *t*", by distance bin
  (0–250, 250–500, 500–1,000, > 1,000 m) and horizon;
- for a hidden segment, the row of its nearest instrumented neighbour's class, at that neighbour's distance, is
  the forecast;
- it is mixed with the prior (ε = 0.05) and reweighted by the class weights, as in E12.

**The tables confirm E12's agreement, and no more.** In Madrid and London, within 250 m, the calibrated table
puts 0.47–0.50 of its mass at 15 minutes on the neighbour's class. In Melbourne it puts 0.66–0.70. The
predictor therefore says, for a hidden segment next to a sensor, "probably the neighbour's class, about one
time in two", which is what E12 measured.

**Calibration removes most of the loss, but not all of it.** Overall, against G0, V lies between −2.3 and −8.4
points in Madrid, −4.8 and −17.0 in London, and −6.0 and −12.8 in Melbourne. All 12 intervals lie below zero.
E12's copy lost 58 to 144 points. Calibrated, the same information loses about ten times less, but it still loses.

**Within 250 m the predictor comes closest to G0 and does not pass it.**

| City | *f* | V within 250 m | Share of hidden segments within 250 m |
|---|---|---|---|
| Madrid | 10% | −1.06 [−1.95; +0.09] | 0.17 |
| Madrid | 20% | −1.41 [−2.03; −0.58] | 0.25 |
| Madrid | 40% | −1.51 [−2.34; −0.65] | 0.41 |
| Madrid | 60% | −1.40 [−2.00; −0.69] | 0.68 |
| London | 10% | −1.93 [−4.36; +0.00] | 0.14 |
| London | 20% | −2.82 [−3.97; −1.42] | 0.30 |
| London | 40% | −1.23 [−2.87; +0.47] | 0.41 |
| London | 60% | −1.24 [−2.87; +0.78] | 0.66 |

- **Madrid and London.** No interval within 250 m reaches above +0.8 points. Four pairs are unfavourable and
  four inconclusive. A 3-point gain is excluded in all eight.
- **Beyond 250 m** the loss grows to 2.7–23 points.
- **Melbourne.** Only 1–9% of the hidden segments lie within 250 m of an instrumented one. The bin is empty in
  some seed at 20% and 60%, and has fewer than 3 blocks at 10% and 40%, so no interval is read there.

The pre-registered statement is "undetermined" (0 of 12 pairs pass the criterion). That is only because the
0–250 m bin cannot be read in Melbourne. Where the bin can be read, the calibrated neighbour does not buy wCE.

**Against the learned propagation.** Within 250 m, E12-bis is 0.1–2.3 points behind G1 in Madrid and London.
Overall it is behind G1 everywhere, by 2.4 to 16.3 points. Neither the learned propagation nor the calibrated
table turns the short-range signal into a gain over G0.

**The class weights do the work, not the neighbour.** Without the reweighting by the class weights, the same
table loses 15 to 126 points. The reweighting is the decision rule that the weighted cross-entropy rewards. G0
has it through its loss; a predictor that skips it is far behind.

**Reported without a criterion.**

- V barely changes across horizons (15 to 120 min).
- Some lookups fall back to the prior, because no instrumented pair lies at the distance of the hidden segment's
  neighbour: 1.9 million in Madrid at 10% and 140,000 in London at 10%. These are hidden segments beyond 1,000 m,
  where no instrumented pair is that far apart.
- At 5% false alarms on validation, red recall on test is 0.06–0.18, with realised false-alarm rates of
  0.05–0.12. These figures are descriptive: the forecast takes few distinct values.

> **Calibrated on the instrumented segments, the nearest neighbour's class comes within 1–3 points of the model
> without spatial exchange inside 250 m, and does not pass it; farther away it loses more.**

**What it leaves open.** The calibrated table knows the neighbour and the distance, but not the time of day,
which is what G0 adds over the prior (E12). Whether the neighbour still adds something once the calendar is in
the table is the question of E12-ter. How many uncovered segments a placement rule can bring within 250 m is the
question of E10-geo.
