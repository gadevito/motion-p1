# Pre-Registered Criterion — Geometric Condition (v2)

Established before the experimental campaign. No outcome data had been observed at the
time of writing: the preliminary measurements used for the design concern only graph
geometry (spacing, connectivity), never performance.

## Variables and Experimental Setup

* Independent variable: mean length of the realized edges in each graph, treated as a continuous variable.
* Dependent variable: (wCE_none - wCE_fixed) / wCE_none, averaged across the four prediction horizons.
* `fixed` arm only, never `adaptive`: the latter contains 20 learned parameters per
  node (E1/E2), which would confound propagation with node identity.
* Five random seeds; bootstrap confidence intervals obtained by jointly resampling
  seeds and sensor blocks; the point estimate is the sample mean, with the interval
  centered on it.
* Full connectivity = giant component fraction >= 0.99. Graphs below this threshold
  (Madrid q20/20 at 0.93; Melbourne q20/20, q20/50, q50/20, q50/50, q80/80)
  are still generated but EXCLUDED from the primary arm.
* The twelve points in the primary arm span 42–396 m, forming three clusters
  (42–88, 95–127, 383–396 m): the 130–380 m interval is unsampled. This limits
  estimation of the breakpoint in the secondary hypothesis, exactly as anticipated by
  its own admissibility condition.
* Common N = 99 for both cities (verified: 8 fully connected points in Madrid,
  4 in Melbourne, spanning 42–396 m (mean realized edge length; considering only the
  distance to the k nearest neighbors would instead give 36–350 m)).

## 1 — Primary Arm: Compact Blocks

Twelve fully connected points, constant N.

Model: spacing slope estimated in a single model with an additive city term
(applicable because N is shared).

Two thresholds, both to be reported:

* DETECTABILITY: difference between the two extremes > bootstrap interval width at the
  densest point. This depends on the observed variance: it indicates whether the effect
  is distinguishable, not whether it is practically useful.
* DESIGN THRESHOLD: difference between the two extremes >= 3 percentage points.
  Pre-specified: for a typical gain of 10–15%, three percentage points correspond to a
  relative change of 20–30%, i.e., the magnitude that changes the engineering decision
  of whether installing one additional sensor is worthwhile.

SUPPORTED if the slope is negative, its confidence interval excludes zero, AND both
thresholds are exceeded. If the detectability threshold is exceeded but the design
threshold is not, the relationship is considered real but too small to be practically
useful—the slope is reported, but no installation threshold is claimed.

## 2 — Supporting Arm: Decimation Sweep on Melbourne

SUPPORTS the hypothesis if the slope has the same sign as in the primary arm, its
confidence interval excludes zero, AND connectivity does not rank the levels in the
same order as the observed advantage. The already measured non-monotonic pattern
(0.59 / 0.24 / 0.27 / 0.39) provides only a partial safeguard, not a formal control.

## 3 — Transferability Across Cities

Because N is common, the additive city term must not be statistically significant.

## 4 — Negative Control (Randomized Adjacency Graph)

A graph with the same number of nodes and the same degree as the corresponding k-NN
graph, but with connected node pairs selected at random; edge weights are the actual
Euclidean distances between the connected nodes.

DESIGN NOTE: the control originally proposed—same topology, same edge lengths,
swapped node positions—is not constructible. For a fixed set of points, the distances
between connected nodes *are* the geometry: preserving edge lengths while swapping
positions is an incompatible requirement. The adopted control destroys geographic
proximity while preserving node degree and edge count, thereby testing the question:
does propagation require connected neighbors to be geographically close?

Applied to the two extremes of the fully connected primary arm:
the densest point (Madrid, ~42 m) as a power control, and the sparsest point
(Melbourne, ~396 m), where randomization is expected to have the greatest effect.

* randomized graph performs worse than the true graph by at least the bootstrap
  interval width of the true graph
  -> propagation exploits geographic proximity;
* randomized graph performs worse, but by less than that
  -> geometry is NOT DISTINGUISHABLE from topology under this design
  (a reportable outcome, distinct from both confirmation and refutation);
* randomized graph performs as well as or better than the true graph
  -> propagation does not exploit geographic proximity:
  the geometric condition is REFUTED, regardless of the outcomes of the other arms.

## 5 — Secondary Hypothesis: Threshold Behavior

The advantage may remain approximately constant up to a critical spacing and then
collapse beyond it.

Statistical test: segmented linear regression with the breakpoint searched on a grid;
comparison with the linear model using an information criterion; bootstrap confidence
interval for the breakpoint.

SUPPORTED if the segmented model is preferred, the two slopes differ with
non-overlapping confidence intervals, and the breakpoint confidence interval is
narrower than the explored spacing range.

Subordinate to Criterion 1, WITH ONE EXCEPTION (see the fifth row below).

## 6 — Outcomes of the Primary × Supporting Arm Combination

| Primary          | Supporting       | Conclusion                                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| supports         | supports         | Supported over 42–1159 m; explains the variability mechanism observed in R3.                                                                                                                                                                                                                                                                                                                                      |
| supports         | does not support | Supported over 42–396 m under controlled connectivity; not generalizable to the sparse regime. The sweep does not contradict the hypothesis—it is simply unable to test it.                                                                                                                                                                                                                                       |
| does not support | supports         | Not supported: by design, the clean primary arm takes precedence.                                                                                                                                                                                                                                                                                                                                                 |
| does not support | does not support | Refuted within the tested regime.                                                                                                                                                                                                                                                                                                                                                                                 |
| **FIFTH CASE**   |                  | The linear slope confidence interval includes zero BUT the segmented model is preferred AND the two slopes have non-overlapping confidence intervals -> SUPPORTED AS A THRESHOLD EFFECT; the linear model is rejected as misspecified. This is the only case in which the secondary hypothesis overrides Criterion 1. The 3-percentage-point design threshold applies to the difference between the two segments. |

## 7 — What Does *Not* Count as Confirmation

No conclusion is declared after inspecting the run outcomes. An anomalous compact
configuration remains in the analysis. Any exclusion that changes the sign of the
estimated coefficient is not reportable.

