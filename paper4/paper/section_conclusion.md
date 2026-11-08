# Paper 4 — draft of the conclusion

Draft of 2026-11-08, revised after the internal review of the full draft (item 12). Numbers come from the frozen
records of `paper4/paper/paper_order.md`.

---

## Conclusion

We asked what an operator can buy with traffic sensors for the segments of the network that have none. On three
cities, at 15–120 minutes, with every experiment pre-registered and frozen, these data carry no forecastable
spatial information beyond the calendar: a learned graph model gains nothing over the same model without its
graph, at any spacing and coverage tested; nearby labels agree only within about 250 m; calibrated, that
agreement does not beat the model without spatial exchange; net of the hour of the week, it is worth nothing.
Placement decides how many uncovered segments lie near a sensor (in Madrid and London at 10% coverage, one in
seven with contiguous blocks and six in seven with uniform placement), not how well they are forecast.

What a sensor buys is the measurement at its own segment, and the choice that matters is what to measure. A loop
detector measures the occurrence of congestion rather than its level, with a threshold that transfers between
sensors; about half of its disagreement with probe speeds on arterials comes from matching it to a segment some
30 m away; and averaging its lanes hides the episodes that occur on one of them.

Three directions remain open:

- inputs that neither the models nor the tables had: speeds rather than classes, incidents, events;
- the same inductive regime on other networks and other measurement technologies;
- other inductive models. We did not train them here because the signal measured without models is zero within
  the radius where labels agree: a model can only exploit a dependence the data contain. Where the inputs above
  carry such a dependence, the question reopens.
