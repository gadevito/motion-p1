**PRE-REGISTERED CRITERION — Equivalence within the Top Tier**

**MARGIN:** ±1% in wCE.
Proposed before the width of the top tier was known (documented in the exchange history).
The rationale is operational and derived from the document's data rather than from the dispersion across random seeds: within each context, one percentage point of wCE corresponds to 0.008–0.016 recall on the critical class (median 0.009, across six contexts, considering all available models). Thus, a 1% margin corresponds to fewer than one additional (or one fewer) critical event detected per hundred, which is below the threshold that would alter the decision of which predictor to deploy. This is a threshold of **PRACTICAL RELEVANCE**, not of detectability; the width of the bootstrap interval is reported separately and does not enter into the definition of the equivalence margin.

**DECLARATION:** The margin is fixed with knowledge of the widths of the 15-minute top tier (0.52%–3.40% across contexts), while ignoring both the test outcomes and the tier widths under the aggregation adopted here (mean across the four forecasting horizons).

**PRIMARY COMPARISON:** For each context, the best versus the worst among the four models in the top tier (*gwn_adaptive*, *gwn_none*, *STAEformer*, *AGCRN*), evaluated on the **MEAN ACROSS THE FOUR HORIZONS**, consistent with the aggregation used for R1–R3. The remaining five pairwise comparisons are provided as supplementary material.

**PAIR SELECTION:** The extreme pair is selected based on the observed outcomes. Consequently, the test is **CONSERVATIVE FOR EQUIVALENCE**—if the two extremes are equivalent, then all intermediate pairs are necessarily equivalent—and **ANTI-CONSERVATIVE FOR DIFFERENCE**, because it maximizes the observed separation. Therefore, evidence of equivalence is particularly strong, whereas evidence of difference should be interpreted with this reservation.

**STATISTICAL PROCEDURE:** Two One-Sided Tests (TOST) on the paired differences, using five random seeds. Confidence intervals are obtained by bootstrap with joint resampling of seeds and sensor blocks. The point estimate is the sample mean, and the interval is centered on this estimate.

**POSSIBLE OUTCOMES AND THEIR IMPLICATIONS FOR THE PAPER'S CLAIM:**

* **EQUIVALENCE** (confidence interval entirely within ±1%) in all contexts
  → *"The top tier is indistinguishable within the pre-specified equivalence margin."*
  This is the current claim, now formally tested.

* **MIXED** (equivalence in some contexts, difference in others)
  → *"The top tier is indistinguishable in N out of six contexts; in the remaining contexts, the extreme models differ by more than the equivalence margin."*
  The general claim no longer holds universally and becomes conditional.

* **PREDOMINANTLY INCONCLUSIVE** (confidence interval wider than the margin and including zero)
  → *"Equivalence cannot be established with the current experimental setup: uncertainty at the data level exceeds the practical relevance margin."*
  The claim remains descriptive and must be presented as such.

* **DIFFERENCE** in all contexts
  → The claim must be withdrawn.

No outcome is declared after inspecting the individual run results. If a context appears anomalous, it remains in the analysis; any exclusion that would change the verdict is not considered reportable.
