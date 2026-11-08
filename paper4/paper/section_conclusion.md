# Paper 4 — draft of the conclusion

Draft of 2026-11-08. Numbers come from the six frozen records of Part B (`paper4/paper/paper_order.md`).
Part A is marked **[Part A]**.

---

## Conclusion

We asked what an operator can buy with traffic sensors for the segments of the network that have none. Every
experiment was pre-registered and frozen, on three cities, at 15–120 minutes.

On segments without a sensor, these data carry no forecastable spatial information beyond the calendar:

- a learned graph model gains nothing over the same model without its graph, at any spacing and any coverage
  tested;
- the labels of nearby segments agree, but only within about 250 m;
- calibrated, that agreement does not beat the model without spatial exchange;
- net of the hour of the week, it is worth nothing.

Placement decides how many uncovered segments lie near a sensor: in Madrid and London at 10% coverage, one in
seven with contiguous blocks and six in seven with uniform placement. It does not decide how well they are
forecast.

What a sensor buys is the measurement at its own segment. The choice that matters is therefore what to
measure. **[Part A]** What a loop detector measures of congestion, to be stated once Part A is frozen.

Two directions remain open:

- inputs that neither the models nor the tables had: speeds rather than classes, incidents, events;
- the same inductive regime on other networks and other measurement technologies.

The pre-registrations, frozen records, per-cell predictions and the script that regenerates every number are
released with the paper.
