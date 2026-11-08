# Paper 4 — draft of the discussion

Draft of 2026-11-08, on the decision of the internal review of 2026-11-08 (14:30). Every number comes from
one of the six frozen records of Part B or from the frozen record of Part A (`paper4/paper/paper_order.md`).

---

## Discussion

**Why no further model.** One could object that the graph model of E9 is one model among many. A better
architecture might extract what Graph WaveNet did not. The analyses without training answer this objection
from the data rather than from the model.

- The calendar table of E12-ter uses the hour of the week of the target time and nothing else. It forecasts a
  segment without a sensor as well as the trained model without spatial exchange, in Madrid and London, and
  slightly better in Melbourne.
- Adding the nearest instrumented neighbour's class to that table adds nothing within 250 m. Every interval
  there contains zero, and a 3-point gain is excluded.
- Beyond 250 m, adding the neighbour makes the forecast worse.

A learned model can only exploit a dependence that the data contain. The dependence between a segment without
a sensor and its neighbours, net of the calendar, is measured here as zero within the only radius where the
labels agree. A second learned model would have to find a signal that neither the learned propagation (E9,
E11) nor the calibrated tables (E12-bis, E12-ter) found. We therefore did not train one.

The argument has a stated perimeter. Two uses of the neighbours were tested:
- the calibrated class of a single neighbour (E12-bis, E12-ter);
- a learned aggregation of several neighbours over three hours (G1 in E9).

Neither gained over the model without spatial exchange, on labels in three classes at 15–120 minutes.
Continuous speeds, incidents and events were not tested.

**What the agreement of nearby labels is.** Two segments within 250 m share a class more often than chance.
The natural reading is that congestion spreads along a corridor, so a sensor tells about its unmeasured
neighbours. The forecasts say otherwise. Net of the hour of the week, the neighbour's class tells nothing about
the segment's class 15 to 120 minutes later. Nearby segments agree because both are congested at the same hours
of the same days. The calendar is common knowledge: it needs no sensor nearby.

**What placement can and cannot do.** The rule that chooses instrumented segments changes proximity by a large
factor:

- contiguous blocks leave most uncovered segments far from any sensor;
- uniform placement brings almost all of them within 250 m from 20% coverage in Madrid and London, and 43–82%
  in Melbourne;
- density-stratified placement matches uniform placement.

If proximity had forecasting value, these differences would translate into accuracy. Since it has none beyond
the calendar, the choice of placement should be made for the segments a sensor covers: where a measurement is
needed for control, enforcement or detection. It should not be made for what the sensor might predict
elsewhere.

**The operator's decision.** What a sensor buys is the measurement at its own segment. The question of what
that measurement should be therefore becomes the main one, and it is the subject of Part A.

For the most common urban sensor, Part A gives a consistent answer. A loop detector says whether a segment is
congested, not how congested it is: its reconstruction ranks levels poorly and separates congested cells almost
perfectly, with a threshold that transfers between sensors. Its low agreement with probe speeds on arterials is
about half a matter of matching a loop to a segment some 30 m away, so it says less about the loop than it
seems. Per lane, detection is as good as on the ring; averaged over the lanes of a section, it loses the
episodes that occur on one lane only, whatever the device. A target defined on the section mean therefore
discards part of what the sensor measures. The definition of the target matters as much as the device.

**Relation to propagation results in the literature.** Graph models for traffic are usually evaluated on
sensors whose own history is in training or in the input [wu2019gwnet]. Kriging methods estimate unobserved
locations from simultaneous observations, not forecasts at 15–120 minutes [wu2021ignnk]. The deliverable that
preceded this work found propagation gains with hidden segments that were training targets. Our positive
control reproduces that condition and the gain that comes with it. Our negative result does not contradict
those findings: it concerns a stricter regime, the one an operator faces for a segment that has never had a
sensor. [ref: placement and coverage studies, to be chosen.]
