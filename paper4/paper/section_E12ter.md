# Paper 4 — draft of the E12-ter section (does the neighbour add to the calendar?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_E12ter.md`. That is the frozen
record of E12-ter, commit dda3b8f, fingerprint ec03ebf339d7deb4. Numbers of E12-bis and E12 come from their own
frozen records (`CONGELAMENTO_E12bis.md`, 11e89874e3b100b8; `CONGELAMENTO_E12.md`, 0be136a3886173bc). E12-ter
trains nothing. It uses the hidden segments, origins and node sets of E9, the G0 of E9 as reference, and the pairs
of E12-bis.

V is in points of the G0 wCE, positive when the predictor is better than G0. Intervals are 95%, from the joint
resample of seeds and corridor blocks. Differences between two predictors are paired on the same replicates.

---

## E12-ter — does the neighbour add anything once the calendar is known?

The calibrated table of E12-bis knew the nearest instrumented neighbour's class and its distance, but not the
time of day. G0 knows the calendar, and E12 showed that the calendar is what G0 adds over the class prior.
E12-ter builds two tables from the same pairs of instrumented segments in the training period:

- **calendar and neighbour:** the own class at *t* + *h* given the hour of the week of *t* + *h*, the
  neighbour's class at *t* and the distance bin;
- **calendar only:** the own class at *t* + *h* given the hour of the week of *t* + *h* alone.

The hour of the week comes from the timestamp of the target time, which is known at *t*. Both tables are
applied to the hidden segments as in E12-bis. The difference between them is the value of the neighbour net of
the calendar.

**The calendar alone is G0.** Against G0, the calendar-only table is within 1.62 points in Madrid and London
(−1.62 to −0.05 overall), and no interval excludes zero. In Melbourne it is ahead of G0 by 1.43 to 4.11
points; the advantage is favourable at 20% coverage only (+4.11 [+1.42; +6.11]). A table of class frequencies
by hour of the week, estimated on the instrumented segments, forecasts a segment without a sensor as well as
the trained model without spatial exchange.

**Net of the calendar, the neighbour is worth zero within 250 m and less than zero beyond.**

| City | *f* | V(calendar and neighbour) − V(calendar), 0–250 m | same, 250–500 m | same, overall |
|---|---|---|---|---|
| Madrid | 10% | −0.29 [−1.17; +0.40] | −9.15 [−22.77; +0.62] | −9.66 [−16.52; −3.75] |
| Madrid | 20% | −0.01 [−0.60; +0.82] | −6.41 [−8.70; −4.85] | −9.92 [−14.77; −6.01] |
| Madrid | 40% | −0.12 [−0.50; +0.30] | −9.54 [−13.52; −6.02] | −5.01 [−7.39; −2.95] |
| Madrid | 60% | +0.31 [−0.34; +0.90] | −12.67 [−19.92; −5.76] | −3.94 [−7.12; −1.33] |
| London | 10% | −0.34 [−1.72; +1.11] | −10.85 [−18.51; −3.24] | −17.32 [−24.58; −9.90] |
| London | 20% | −0.63 [−1.96; +0.92] | −10.43 [−16.13; −4.23] | −11.81 [−16.40; −6.70] |
| London | 40% | +0.57 [−0.57; +1.74] | −19.34 [−25.46; −12.93] | −11.42 [−16.08; −7.25] |
| London | 60% | +1.26 [−0.29; +3.04] | −7.57 [−12.30; −1.46] | −2.15 [−4.97; +0.95] |

- **Within 250 m**, in Madrid and London, the neighbour adds between −0.63 and +1.26 points to the calendar.
  All eight intervals contain zero.
- **Between 250 and 500 m**, it removes 6.41 to 19.34 points, and seven of the eight intervals lie below zero.
- **Overall**, it removes 2.15 to 17.32 points in Madrid and London. In Melbourne it removes 22.76 to 38.35
  points, most of it beyond 1,000 m, where 59–93% of the hidden segments lie.
- In Melbourne the 0–250 m bin is again unreadable: empty in some seed at 20% and 60%, fewer than 3 blocks at
  10% and 40%.

Beyond 250 m, a row conditioned on a distant neighbour's class rests on few instrumented pairs that far apart,
and states a class that the calendar does not support. Within 250 m the rows are full: at most 9.8% of the
lookups fall back to the table of E12-bis. There the neighbour simply has nothing to add.

**The criterion.** With the calendar, the neighbour's class beats G0 within 250 m in none of the 12 pairs.

- In Madrid and London V within 250 m lies between −1.22 and +0.43, and no interval reaches above +1.70.
  A 3-point gain is excluded in all eight pairs.
- The pre-registered statement is "undetermined", only because the 0–250 m bin cannot be read in Melbourne,
  as in E12-bis.

**The surplus of agreement was shared calendar.** E12 found that within 250 m a hidden segment shares its
nearest instrumented neighbour's class 8–16 points more often than independent draws would. E12-bis turned
that agreement into a calibrated forecast, which stayed 1.06–2.82 points below G0 within 250 m in Madrid and
London. E12-ter decomposes it:

- the calendar added to the neighbour gains 0.75 to 1.74 points within 250 m in Madrid and London (favourable
  in seven of the eight pairs);
- the neighbour added to the calendar gains nothing.

What a nearby sensor tells about a segment without one, for a forecast at 15–120 minutes, is what the hour of
the week already says. Two close segments agree more often than chance because both follow the same weekly
rhythm, not because one carries information about the other that the calendar does not.

**Reported without a criterion.**

- V of the table of calendar and neighbour per horizon shows no systematic trend from 15 to 120 minutes.
- Without the reweighting by the class weights, the table of calendar and neighbour loses 11 to 142 points.
- Red recall at 5% false alarms on validation is 0.049–0.165 for the calendar and neighbour, with realised
  false-alarm rates of 0.045–0.093. For the calendar alone it is 0.070–0.177, with rates of 0.045–0.062. These
  figures are descriptive: the forecasts take few distinct values.

> **On segments without a sensor, the hour of the week forecasts as well as the model without spatial
> exchange; net of the calendar, the class of the nearest instrumented neighbour is worth nothing within 250 m
> and less than nothing beyond. The agreement of nearby labels is shared calendar.**

**Limits stated with the result:**

- E12-ter conditions on the class of one neighbour at *t*, not on the 3-hour trajectories of several
  neighbours. That richer input is what the learned graph model of E9 had, and it gained nothing over G0 either.
- E12's agreement was measured at the same instant, while E12-ter forecasts from *t* to *t* + *h*. The reading
  "shared calendar" holds for forecasting at 15–120 minutes. It is not a decomposition of the same-instant
  agreement.
- The hour of the week is the only calendar used. Holidays and events are not modelled.
