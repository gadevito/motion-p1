# Paper 4 — draft of the limits

Draft of 2026-11-08. The limits stated with each result in the sections of Part A and Part B are collected
here. Numbers come from the frozen records listed in `paper4/paper/paper_order.md`.

---

## Limits

**Task and data.**

- One task: three congestion classes, 15–120 minutes ahead, from measured speeds of three Traffic4cast cities.
  Other targets (speed, travel time), longer horizons and other data sources are not tested.
- The cities' series are one-week blocks separated by gaps; only origins whose window and targets respect the
  15-minute cadence are used (register of corrections, item 1).
- The classes come from a congestion factor relative to free flow, with thresholds inherited from the
  deliverable.

**Models.**

- One architecture, Graph WaveNet, with and without its graph, inherited and not tuned. The training budget is
  fixed by a pilot (1,000 updates) and checked at twice that budget.
- No static attribute of the segments (number of lanes, capacity, speed limit). In Madrid and London these
  attributes are missing, and in the E11 pilot the speed limit acted as an identifier of the node.
- The training input covers 60–95% of the observed set, while evaluation uses all of it. The shift is the same
  at every coverage.

**Design.**

- Hidden segments are drawn as whole blocks of a grid. At 60% coverage the test-hidden segments lie in 8–9
  blocks, and in Melbourne the intervals are wide.
- In Melbourne the 0–250 m bin of the analyses without training is empty or has too few blocks at every
  coverage. The statements of E12-bis and E12-ter are "undetermined" for that reason alone.
- The 3-point margin is a convention, inherited from the earlier study. No correction for multiple comparisons
  is applied; this is declared in each pre-registration.

**The analyses without training.**

- **Perimeter of the negative result.** Two ways of using the neighbours were tested, and neither gained over
  the model without spatial exchange:
  - the calibrated class of a single neighbour (E12-bis, E12-ter);
  - a learned aggregation of several neighbours over three hours (G1, E9).

  Both concern labels in three classes at 15–120 minutes. Continuous speeds, incidents and events were not
  tested.
- The calendar is the hour of the week. Holidays and events are not modelled.
- The agreement of nearby labels was measured at the same instant, and its value net of the calendar was
  measured as a forecast at 15–120 minutes. The reading "shared calendar" is a reading of the forecasts, not a
  decomposition of the same-instant agreement.
- Distances are straight-line between segment coordinates, not along the road.

**Placement.**

- The value of proximity was measured on the block placements of E9. That a hidden segment's value depends
  only on its distance to the nearest sensor, and not on the rule that placed the sensors, is an assumption.
- Placement rules that use traffic data (for example, instrumenting the most congested segments) are not
  compared. With no forecasting value in proximity, they could only change which segments are measured.

**Part A.**

- The three datasets do not overlap in time or space. Regime and technology cannot be separated: the ring is
  observed in 2024, the arterials in 2021.
- The reading rules were fixed knowing the deliverable's in-sample values, so every statement of Part A is
  descriptive.
- The free-flow references use the whole year, as built in the deliverable's targets. Part A compares
  measurements; it does not forecast.
- The 19–72 m band was built a posteriori by the deliverable, and the matching share depends on it.
- Austin has 6 three-lane and 2 four-lane sections; no lane threshold is identified.
- Several printed values of the deliverable have no conserved generator (register of corrections, items 14–20).
  They are reported as such; every number of Part A is regenerated.

**Reproducibility.** Costs are measured on one machine (Mac M3 Max); the campaign times are from concurrent
processes and are not isolated costs. The regeneration script reruns every analysis from the per-cell
predictions; it does not retrain the models.
