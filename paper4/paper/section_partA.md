# Paper 4 — draft of the Part A section (what does a loop detector measure of congestion?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_4A.md`. That is the frozen record
of P4A, commit a0b76dc, fingerprint 7304d9639f91ec81 (numbers in `p4a_risultati.json`, cbf52e3c811f05a0). P4A
trains nothing. Intervals are 95%, from a block bootstrap with 2,000 replicates over sensors (arterials: loops;
Austin: sections).

**Every statement of this section is descriptive.** The reading rules of the pre-registration were fixed knowing
the in-sample values of the deliverable, so they are declared rules for reading the intervals, not tests.

Open points, waiting for the executor's causes (register of corrections, items 18–20): the green class of
Table 67, the neighbour bands of Table 68, and the Austin section counts. They are marked **[cause: item n]**.

---

## Part A — what does a loop detector measure of congestion?

Part B found that a sensor buys the measurement at its own segment, and nothing beyond it. Part A asks what that
measurement is, for the most common urban sensor. A loop detector measures flow and occupancy; congestion is
reconstructed as their ratio, relative to its free-flow value.

Three datasets give an independent speed reference:

- **the M30 ring of Madrid, 2024:** 279 sensors that measure flow, occupancy and speed on the same device;
- **the Madrid arterials, 2021:** 399 loops matched to probe-speed road segments, a median of 33 m away;
- **Austin:** radar detectors at signalised intersections, with volume, occupancy and speed per lane.

Every number of the deliverable that preceded this work was regenerated and compared. Where a number had no
source, it was recomputed with a declared definition (register of corrections, items 14–17). Three corrections
are applied to the deliverable's analysis:

- the congestion threshold is chosen out of sample;
- every figure gets an interval from a block bootstrap;
- the effect of the number of lanes is measured as a rank correlation with an interval.

### The loop detects congestion but does not measure its level

On the M30 ring, on the 4,199,040 cells where the occupancy rule does not impute the value, reconstructed and
measured congestion agree poorly in level:

- the overall rank correlation is +0.249 [+0.208; +0.290];
- it changes sign with occupancy, from −0.112 [−0.136; −0.086] at 5–10% occupancy to +0.463 [+0.284; +0.620]
  above 40%;
- within the measured classes it is +0.012 [−0.019; +0.044] on free flow, +0.458 [+0.320; +0.617] on slowed
  traffic and +0.632 [+0.543; +0.718] on congestion. **[cause: item 18]** The deliverable's +0.033 on free flow
  counts 2,989,877 cells, where we count 3,432,842. The conserved script, on the same inputs, prints our value.

The same reconstruction separates congested cells from the others almost perfectly. The area under the curve
for congestion against the rest is 0.984 [0.979; 0.988]. For slowed or congested against free flow it is
0.752 [0.706; 0.804].

**Correction 1: the threshold transfers between sensors.** The deliverable chose its threshold (0.30) on the same
cells on which it reported precision and recall. We reproduce its in-sample figures (precision 0.498, recall
0.891, F1 0.639). We then chose the threshold on half of the sensors and reported it on the other half, over 5
random splits.

| Reading | Thresholds chosen (5 splits) | F1 | Precision | Recall |
|---|---|---|---|---|
| between sensors, whole year (primary) | 0.28–0.29 | 0.640 [0.539; 0.725] | 0.512 [0.397; 0.621] | 0.853 [0.760; 0.926] |
| in time, January–March → April–December (secondary) | 0.23–0.32 | 0.644 [0.539; 0.733] | 0.541 [0.404; 0.666] | 0.810 [0.616; 0.960] |

- The chosen thresholds lie close to the deliverable's 0.30, and the F1 obtained on unseen sensors equals the
  in-sample value.
- With the threshold set for 5% false alarms on the first half, recall on the second half is 0.983
  [0.949; 0.999], with a realised false-alarm rate of 0.050 [0.034; 0.083].
- The reading in time carries the seasonality of the year as a limit.

Under the declared reading rules (rank correlation below 0.5, transferred F1 above 0.5, area under the curve
above 0.9, each on its interval), the reading is descriptive:

> **A loop detector says whether a segment is congested, not how congested it is. A threshold chosen on some
> sensors transfers to others.**

### Matching to road segments accounts for about half of the arterial gap

On the Madrid arterials, loops and probe speeds barely agree:

- the median over pairs of the per-pair area under the curve is 0.506 [0.504; 0.508], over 394 pairs;
- the median rank correlation is +0.040 [+0.032; +0.048], over 399 pairs.

The deliverable's area under the curve of 0.542 has no source (item 14). Its two values of the rank
correlation, +0.001 in the table and +0.071 in the text, disagree (item 15). On the pooled cells of the pairs we
obtain 0.525 [0.517; 0.534] and +0.072 [+0.057; +0.089].

On the M30 ring the reference can be moved away from the loop while keeping regime and technology. When it is
taken from a neighbouring sensor, discrimination falls with distance:

| Reference | Sensors | Median distance | Area under the curve | Gini |
|---|---|---|---|---|
| the same sensor | 279 | 0 m | 0.984 [0.979; 0.988] | 0.968 [0.958; 0.976] |
| a neighbour within 0–20 m | 191 | 14 m | 0.789 [0.723; 0.853] | 0.579 [0.447; 0.707] |
| a neighbour within 19–72 m (band built a posteriori by the deliverable) | 181 | 31 m | 0.724 [0.660; 0.795] | 0.448 [0.321; 0.591] |
| a neighbour within 20–60 m | 156 | 31 m | 0.764 [0.699; 0.826] | 0.528 [0.398; 0.653] |
| a neighbour within 60–200 m | 165 | 96 m | 0.593 [0.539; 0.655] | 0.187 [0.079; 0.310] |

**[cause: item 19]** The neighbour rows differ from the deliverable's by 0.001–0.009. The conserved script, on
the same inputs, prints our values.

The Gini scale (twice the area under the curve, minus one) is additive, so the arterial gap can be split. A
reference 31 m away removes 0.968 − 0.448 of the Gini on the ring. Against the gap down to the arterials
(Gini 0.012), that is a share of 0.544 [0.395; 0.676] (0.566 [0.411; 0.705] with the pooled arterial value).
The rest belongs jointly to the regime and the technology, which the data cannot separate: the ring is observed
in 2024 and the arterials in 2021.

The interval includes one half, so under the reading rule the statement is "undetermined". Matching explains
between two fifths and two thirds of the gap. The deliverable's 58% lies inside that interval, but rests on
the untraced 0.542.

### Aggregating lanes hides single-lane episodes

In Austin, per lane, reconstruction behaves as on the ring:

- the median within-lane rank correlation is +0.706 [+0.666; +0.764];
- the median within-lane area under the curve is 0.991 [0.983; 0.998].

The deliverable reported the interquartile range of the latter (0.965–0.998 here) as an interval (item 17).

When the lanes of a section are aggregated, the reconstructed factor must detect an episode on any one of them:

| Lanes per section | Sections | Cells | Median area under the curve | Interquartile range | Difference of prevalence (points) |
|---|---|---|---|---|---|
| 2 | 22 | 1,432,457 | 0.990 [0.985; 0.997] | 0.982–0.997 | +0.19 [+0.08; +0.33] |
| 3 | 6 | 433,660 | 0.755 [0.461; 0.997] | 0.489–0.995 | +18.62 [+3.87; +33.35] |
| 4 | 2 | 154,380 | 0.664 (2 sections, no interval) | 0.533–0.796 | +9.88 (no interval) |

*Sections with ≥ 2 lanes: 30 (22/6/2); rank correlation over 29.* One two-lane section has 20 or fewer
aggregated cells either with or without a congested lane. Its area under the curve is undefined under the
script's rule, which requires more than 20 of each. **[cause: item 20]** The section is to be named. After the
script's filters there are 40 sections, 10 of them with one lane, where nothing is aggregated. The brief counted
31; its criterion of inclusion is to be stated.

The difference of prevalence is the share of cells in which at least one lane is congested but the section as a
whole is not. It is the part of the episodes that the aggregated target itself hides, whatever the device.

**Correction 3.** Over the 29 sections, the rank correlation between the number of lanes and the section's area
under the curve is −0.441 [−0.714; −0.072]. Under the reading rule (interval below zero):

> **The more lanes are aggregated, the worse the reconstructed factor detects an episode on one of them.**

The data still found no lane threshold. Three and four lanes rest on 6 and 2 sections.

The deliverable also stated that aggregation lowers the rank correlation between volume and occupancy, from
+0.7241 to +0.2999 (item 16; no generator). With a declared definition, over the 8 sections with at least 3
lanes, we obtain +0.735 [+0.678; +0.829] per lane and +0.739 [+0.582; +0.902] aggregated. The fall is not
reproduced.

### What this means for an operator

- A loop is a detector of congested episodes, not a meter of their level.
- Its threshold can be set on some sensors and used on others.
- Matching a loop to a road segment some 30 m away costs about half of the apparent disagreement with probe
  data. Low agreement on arterials therefore says less about the loop than it seems.
- Averaging across lanes hides episodes on one lane, whatever the sensor. The target definition matters as much
  as the device.

**Limits stated with the result:**

- the three datasets do not overlap in time or space;
- the free-flow references use the whole year, as built in the deliverable's targets. This is a comparison of
  measurements, not a forecast;
- the reading rules were fixed knowing the deliverable's in-sample values, so every statement is descriptive;
- the 19–72 m band was built a posteriori by the deliverable, and the Gini split depends on it;
- Austin has 2 four-lane and 6 three-lane sections.
