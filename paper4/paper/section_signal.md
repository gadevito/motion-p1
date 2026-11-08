# Paper 4 — draft of the section on the spatial signal (E12, E12-bis, E12-ter in one argument)

Draft of 2026-11-08, after the internal review of the full draft (item 2): the three analyses without training
are one argument in three steps, with one table. Numbers come from `CONGELAMENTO_E12.md` (085bda7,
0be136a3886173bc), `CONGELAMENTO_E12bis.md` (40adfc9, 11e89874e3b100b8) and `CONGELAMENTO_E12ter.md` (dda3b8f,
ec03ebf339d7deb4). None of the three trains a model; all use the hidden segments, origins, node sets and resample
of E9, with G0 of E9 as reference.

---

## The spatial signal, decomposed (E12, E12-bis, E12-ter)

E9 leaves two readings open: the hidden segments carry no signal that their neighbours could pass on, or the
learned propagation does not use a signal that is there. We separate them without a model, in three steps on the
same segments: does the signal exist; what is it worth once calibrated; what is it worth once the calendar is
known.

**A calibration effect, not an absence of signal.** Copied as they are, the neighbours' classes lose heavily to
G0. The class of the nearest instrumented neighbour, persisted to the horizon, and an inverse-distance average of
the four nearest lose 58 to 144 points; the neighbours' class frequencies by weekly slot lose 9 to 21 points in
Madrid and London. A predictor that copies a neighbour's class is right about half the time within 250 m, but
states that class with probability close to 0.95 (mixed with the prior at ε = 0.05). The weighted cross-entropy
penalises the confident errors more than it rewards the correct calls. The size of these losses says that the
copy is miscalibrated, not that the signal is absent, and this is why the signal must be calibrated before it is
judged.

**Step 1: the labels carry a short-range signal (E12).** The share of pairs (hidden segment, nearest
instrumented segment) in the same class at the same instant exceeds the agreement of independent draws (Σπ²)
by 8–12 points in Madrid and 11–16 in London within 250 m (first column of the table of this section), and falls to within a few
points of it beyond. A hidden segment's class is more often that of a close instrumented neighbour than chance
would give. The signal is real, and short.

**Step 2: calibrated, it comes close to G0 and does not pass it (E12-bis).** A table estimated on the
instrumented segments alone gives p(own class at *t* + *h* | nearest instrumented neighbour's class at *t*,
distance bin, horizon), from pairs of instrumented segments in the training period, and is applied to the
hidden segments. Within 250 m it puts 0.47–0.50 of its mass on the neighbour's class in Madrid and London, which
is what step 1 measured. Overall it loses 2.3 to 8.4 points in Madrid and 4.8 to 17.0 in London; within 250 m it
comes within 1–3 points of G0, with no interval above +0.8 and a 3-point gain excluded in all eight pairs.

**Step 3: once the calendar is known, the neighbour adds nothing (E12-ter).** Two tables are built from the same
pairs: the own class given the hour of the week of *t* + *h* alone (calendar only), and given the hour of the
week, the neighbour's class and the distance bin. The calendar-only table is G0: within 1.62 points of it in
Madrid and London, with no interval excluding zero. The difference between the two tables is the value of the
neighbour net of the calendar. Within 250 m it lies between −0.63 and +1.26 points, and all eight intervals
contain zero; between 250 and 500 m it removes 6.41 to 19.34 points.

| City | *f* | Agreement, 0–250 m (independence) | Calibrated neighbour, 0–250 m | Calendar only, overall | Neighbour net of the calendar, 0–250 m | same, 250–500 m |
|---|---|---|---|---|---|---|
| Madrid | 10% | 0.511 (0.433) | −1.06 [−1.95; +0.09] | −0.13 [−0.54; +0.36] | −0.29 [−1.17; +0.40] | −9.15 [−22.77; +0.62] |
| Madrid | 20% | 0.528 (0.423) | −1.41 [−2.03; −0.58] | −0.18 [−0.62; +0.17] | −0.01 [−0.60; +0.82] | −6.41 [−8.70; −4.85] |
| Madrid | 40% | 0.522 (0.424) | −1.51 [−2.34; −0.65] | −0.15 [−0.49; +0.19] | −0.12 [−0.50; +0.30] | −9.54 [−13.52; −6.02] |
| Madrid | 60% | 0.544 (0.424) | −1.40 [−2.00; −0.69] | −0.05 [−0.23; +0.14] | +0.31 [−0.34; +0.90] | −12.67 [−19.92; −5.76] |
| London | 10% | 0.519 (0.413) | −1.93 [−4.36; +0.00] | −1.62 [−3.63; +0.27] | −0.34 [−1.72; +1.11] | −10.85 [−18.51; −3.24] |
| London | 20% | 0.518 (0.385) | −2.82 [−3.97; −1.42] | −0.58 [−1.51; +0.11] | −0.63 [−1.96; +0.92] | −10.43 [−16.13; −4.23] |
| London | 40% | 0.526 (0.393) | −1.23 [−2.87; +0.47] | −0.25 [−0.65; +0.05] | +0.57 [−0.57; +1.74] | −19.34 [−25.46; −12.93] |
| London | 60% | 0.536 (0.379) | −1.24 [−2.87; +0.78] | −0.91 [−2.18; +0.12] | +1.26 [−0.29; +3.04] | −7.57 [−12.30; −1.46] |
| Melbourne | 10% | 0.761 (0.647) | — | +1.81 [−0.93; +3.95] | — | — |
| Melbourne | 20% | 0.755 (0.576) | — | +4.11 [+1.42; +6.11] | — | — |
| Melbourne | 40% | 0.771 (0.579) | — | +1.43 [−1.89; +4.32] | — | — |
| Melbourne | 60% | 0.792 (0.596) | — | +2.25 [−1.45; +4.53] | — | — |

*Agreement: share of (hidden, nearest instrumented) pairs in the same class at the same instant; in brackets,
the agreement of independent draws (Σπ²). Other columns: V in points of the G0 wCE, with 95% intervals. In
Melbourne the 0–250 m bin is empty in some seed or has fewer than 3 blocks, and is not read.*

**The surplus of agreement was shared calendar.** Within 250 m in Madrid and London, the calendar added to the
calibrated neighbour gains 0.75 to 1.74 points, while the neighbour added to the calendar gains nothing. Two
close segments agree more often than chance because both follow the same weekly rhythm, not because one carries
information about the other that the hour of the week does not. Beyond 250 m, a row conditioned on a distant
neighbour's class rests on few instrumented pairs that far apart and states a class the calendar does not
support, hence the losses.

For each step the pre-registered statement is "undetermined", only because the 0–250 m bin cannot be read in
Melbourne (§V); where the bin can be read, no step gains over G0.

> **On segments without a sensor, the hour of the week forecasts as well as the model without spatial exchange;
> net of the calendar, the class of the nearest instrumented neighbour is worth nothing within 250 m and less
> than nothing beyond. The agreement of nearby labels is shared calendar.**
