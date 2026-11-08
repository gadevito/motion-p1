# Paper 4 — draft of the E9 section (coverage curve: how many sensors?)

Draft of 2026-11-08. Every number comes from `paper4/congelamenti/CONGELAMENTO_E9.md` (frozen record of E9,
commit 1d97a94, fingerprint 0237d28dee3b7c4d). V is in points of the G0 wCE, positive when the graph model is
better, with 95% intervals from a joint resample of seeds and corridor blocks (grid cells). It is read on the
scale set out in the paragraph on the inductive regime (E11 section).

---

## E9 — does propagation pay at some coverage?

E9 asks how many sensors it takes before instrumented neighbours start to inform the segments without one.

- **Cities:** Madrid, London and Melbourne, whole networks of 828, 774 and 587 segments.
- **Coverage:** the instrumented fraction *f* takes four levels, 10, 20, 40 and 60%.
- **Corridors:** observed, validation-hidden and test-hidden segments are whole grid cells (11×11, 11×11 and
  15×15). At every level, the test-hidden segments fall in at least 8 cells.
- **Arms:** the model without spatial exchange (G0); the same model with the road graph (G1); and G1 on a
  degree-preserving randomisation of the road graph with the same weights (G1-rand(deg)).
- **Runs:** five seeds, 180 trainings (13.5 h of machine time on a Mac M3, two concurrent processes, not
  isolated).

**No level of coverage makes propagation pay.** Propagation "helps" at a level if V(G1) has an interval above
zero and a point estimate of at least 3 points. This happens in none of the 12 (city, *f*) pairs (0/3 cities at
every *f*). The pre-registered statement requires the 3-point advantage to be excluded everywhere; it is
excluded in 11 of 12 pairs. The exception is Melbourne at 60%, where the test-hidden nodes lie in only 8 cells
and the interval is −0.92 [−5.51; +3.25]. The derived statement is therefore "undetermined".

Every other interval lies within ±3 points, and most within ±1:

- the median half-width of V(G1) is 0.35 points;
- the two intervals that exclude zero are unfavourable to the graph (Madrid 10%, −0.39 [−0.94; −0.03];
  London 20%, −0.26 [−0.55; −0.00]).

**The curve V(f) is flat.** With a city term, a constant fits the 12 points better than a line (AIC −16.06
against −14.06) and better than a step (−12.25). The linear slope is +0.001 points per unit of *f*
[−2.970; +2.827]. Coverage changes the distance from a hidden segment to the nearest instrumented one by a
factor of four to five, from 794 m at 10% to 171 m at 60% in Madrid, without moving V.

**Absolute levels.** On segments without a sensor, the forecast stays close to the uniform predictor at every
coverage:

| City | wCE of G1 on test-hidden segments | Below ln 3 = 1.0986 |
|---|---|---|
| Madrid | 1.075–1.087 | 1.1–2.2% |
| London | 1.050–1.059 | 3.6–4.4% |
| Melbourne | 1.081–1.134 | from −3.2% to +1.6% |

In Melbourne at 10% and 20% coverage, both G0 and G1 are *above* ln 3, worse than predicting the three classes
with equal probability. There the instrumented segments lie 2.8–5.3 km, in median, from the hidden ones.

**Operational reading.** At 5% false alarms on validation, red recall on the hidden segments is 0.05–0.06 in
Madrid and 0.06–0.08 in London, against realised false-alarm rates of 0.04–0.06: congestion is not separated
from free flow. In Melbourne recall rises to 0.11–0.15 at 40–60% coverage, against false alarms of about 0.05,
for every arm including G0.

**Which neighbours.** The comparison with the degree-preserving randomisation (secondary) finds no geometry
effect of 3 points or more. Such an advantage is excluded in 11 of 12 pairs, and the exception is again
Melbourne at 60%. In Melbourne at 10% and 40% the road graph is ahead of its randomisation by +1.02
[+0.25; +1.76] and +1.19 [+0.21; +2.27], while neither beats G0.

> **At 10–60% coverage, on whole cities, propagation from instrumented neighbours gives no measurable gain over
> the no-graph model for these models.**

**Limits stated with the result:**

- the same inductive regime and fixed budget as E11 (training input 60–95% of the observed set);
- no static attribute;
- the margin of 3 points is a convention;
- at 60% coverage the test-hidden segments lie in 8–9 cells, and in Melbourne the interval is wide;
- the comparison of hidden with observed segments is biased against the observed ones (frozen record, item 4);
- machine time comes from concurrent processes.

What E9 rules out is a learned propagation that pays at some coverage. Whether a spatial signal exists that
simpler, non-learned predictors could recover is the question of E12.
