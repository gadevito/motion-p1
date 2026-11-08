# Paper 4 — draft of the E9 section (how many)

Draft of 2026-11-08, revised after the internal review of the full draft (items 1–3, 8). Every number comes
from `paper4/congelamenti/CONGELAMENTO_E9.md` (commit 1d97a94, fingerprint 0237d28dee3b7c4d).

---

## How many: the coverage curve on whole cities (E9)

E9 asks how many sensors it takes before instrumented neighbours start to inform the segments without one. On
the whole networks of the three cities, the instrumented fraction *f* takes four levels (10, 20, 40 and 60%);
the corridors of observed, validation-hidden and test-hidden segments are whole grid cells, and at every level
the test-hidden segments fall in at least 8 cells. The arms are G0, G1 and G1 on a degree-preserving
randomisation of the road graph (G1-rand(deg)), with five seeds: 180 trainings.

**No level of coverage makes propagation pay.** Propagation "helps" at a level if V(G1) has an interval above
zero and a point estimate of at least 3 points. This happens in none of the 12 (city, *f*) pairs. A 3-point
advantage is excluded in 11 of 12; the exception is Melbourne at 60%, −0.92 [−5.51; +3.25], so the
pre-registered statement is "undetermined". The median half-width of V(G1) is 0.35 points, and the two
intervals that exclude zero are unfavourable to the graph (Madrid 10%, −0.39 [−0.94; −0.03]; London 20%,
−0.26 [−0.55; −0.00]).

**The curve is flat.** With a city term, a constant fits the 12 points better than a line (AIC −16.06 against
−14.06) and better than a step (−12.25). Coverage changes the median distance from a hidden segment to the
nearest instrumented one from 794 m at 10% to 171 m at 60% in Madrid, without moving V.

| City | wCE of G1 on test-hidden segments | Below ln 3 = 1.0986 |
|---|---|---|
| Madrid | 1.075–1.087 | 1.1–2.2% |
| London | 1.050–1.059 | 3.6–4.4% |
| Melbourne | 1.081–1.134 | from −3.2% to +1.6% |

On segments without a sensor the forecast stays close to the uniform predictor at every coverage, and red recall
at 5% false alarms is 0.05–0.08 in Madrid and London, against realised false-alarm rates of 0.04–0.06. The
degree-preserving randomisation finds no geometry effect of 3 points or more (excluded in 11 of 12 pairs).

> **At 10–60% coverage, on whole cities, propagation from instrumented neighbours gives no measurable gain over
> the model without spatial exchange.**
