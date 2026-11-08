# Paper 4 — draft of the E10-geo section (where: how close can placement bring uncovered segments?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_E10geo.md`. That is the frozen
record of E10-geo, commit 85cd9e8, fingerprint bafddd2709919092. The figure is
`paper4/congelamenti/e10geo_curva.svg` (a4edbde30583b455). E10-geo uses only the coordinates of the segments of E9.
It is descriptive and has no criterion.

---

## E10-geo — how close can placement bring uncovered segments to a sensor?

E12 located the label signal within about 250 m of an instrumented segment. Placement can matter only through
how many uncovered segments it puts within that radius. E10-geo measures this for three rules, with the same
number of sensors and 20 draws each:

- **blocks:** the whole-cell corridors of E9;
- **uniform:** segments drawn at random;
- **density-stratified:** equal numbers drawn from five strata of local density, which oversamples sparse areas.

**Figure — Share of uncovered segments with an instrumented segment within 250 m, against coverage.** One panel
per city; one line per rule (blocks, uniform, density-stratified); mean over 20 draws.
(`paper4/congelamenti/e10geo_curva.svg`)

**Placement changes proximity by a large factor.** Share of uncovered segments within 250 m of a sensor (mean
over 20 draws, with the 2.5–97.5% range):

| City | *f* | Blocks | Uniform | Density-stratified |
|---|---|---|---|---|
| Madrid | 10% | 0.155 [0.078; 0.217] | 0.874 [0.785; 0.937] | 0.879 [0.810; 0.939] |
| Madrid | 20% | 0.267 [0.149; 0.320] | 0.962 [0.936; 0.982] | 0.965 [0.953; 0.981] |
| Madrid | 40% | 0.481 [0.315; 0.586] | 0.991 [0.985; 0.998] | 0.990 [0.979; 0.997] |
| Madrid | 60% | 0.659 [0.453; 0.832] | 0.996 [0.991; 1.000] | 0.993 [0.983; 1.000] |
| London | 10% | 0.153 [0.056; 0.225] | 0.853 [0.779; 0.929] | 0.856 [0.794; 0.929] |
| London | 20% | 0.282 [0.199; 0.348] | 0.947 [0.917; 0.975] | 0.955 [0.929; 0.976] |
| London | 40% | 0.465 [0.324; 0.603] | 0.988 [0.974; 0.997] | 0.987 [0.975; 0.996] |
| London | 60% | 0.619 [0.493; 0.740] | 0.995 [0.989; 1.000] | 0.995 [0.986; 1.000] |
| Melbourne | 10% | 0.012 [0.002; 0.023] | 0.429 [0.343; 0.494] | 0.436 [0.375; 0.515] |
| Melbourne | 20% | 0.018 [0.003; 0.031] | 0.602 [0.558; 0.668] | 0.595 [0.563; 0.650] |
| Melbourne | 40% | 0.044 [0.022; 0.081] | 0.746 [0.702; 0.771] | 0.717 [0.671; 0.749] |
| Melbourne | 60% | 0.063 [0.027; 0.104] | 0.821 [0.757; 0.862] | 0.773 [0.739; 0.804] |

**Madrid and London.**

- At 10% coverage, uniform placement puts 85–87% of the uncovered segments within 250 m of a sensor. That is
  more than block placement reaches at 60% (62–66%).
- The median distance from an uncovered segment to the nearest sensor falls from 775–786 m with blocks to
  94–109 m with uniform placement.
- From 20% coverage, uniform placement brings at least 94.7% of the uncovered segments within the radius.

**Melbourne.**

- Block placement leaves almost every uncovered segment beyond 250 m: 1–6% are within it, with median
  distances of 1.2–4.2 km.
- Uniform placement brings 43–82% within 250 m.

**Oversampling sparse areas buys nothing in proximity.** The density-stratified rule matches the uniform one
within 0.01 in Madrid and London. In Melbourne it is 3–5 points below it at 40–60% coverage, because the sensors
it moves to sparse areas leave the dense ones farther apart.

> **At the same number of sensors, the placement rule decides whether one uncovered segment in seven or six in
> seven lies within 250 m of a sensor in Madrid and London. Between uniform and density-stratified placement
> there is no difference.**

**What this proximity is worth.** E12-bis measured the value of a sensor within 250 m on the segments of E9. A
calibrated predictor that uses it stays 1–3 points behind G0 in Madrid and London, and does not pass it. The
label signal reached by placement therefore buys no forecast that the model without spatial exchange does not
already give. E12-ter tests whether this still holds once the calendar is added to the neighbour.

**The answer to "where".** Placement decides where the network measures: which segments carry a sensor and
which lie next to one. On these data it does not decide how well the segments without a sensor are forecast
elsewhere. A placement rule is chosen for the segments it covers, not for what it predicts on the others.

**Limits stated with the result:**

- distances are straight-line between segment coordinates, not along the road;
- the value of proximity comes from E12-bis on the block sets of E9, where the hidden segments within 250 m lie
  at the edges of corridors. That a hidden segment's value depends only on its distance to the nearest sensor,
  and not on the rule that placed the sensors, is an assumption, not a measurement;
- 250 m is the radius found by E12 with its distance bins; the 500 m shares are in the frozen record.
