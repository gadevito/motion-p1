# Paper 4 — draft of the E11 section (geometry under protocol)

Draft of 2026-11-06. Every number comes from `paper4/congelamenti/CONGELAMENTO_E11.md` (frozen record of
E11; regenerated version, commit _______) or from the pilot of `protocol/paper4/E11.md`. Validation numbers are
labelled as such. Numbers are in points of the G0 wCE, positive when the first arm is better, with 95%
intervals from a joint resample of seeds and corridor blocks.

---

## The inductive regime and the positive control

All results of Part B are read on one scale, and the reader should see it before the results. A hidden
segment never enters the model: not as input, not as a training target, not in the normalisation or in the
class weights. The model must therefore forecast a segment it has never seen, from its instrumented
neighbours and from the calendar alone.

In this regime the forecast is close to the uniform predictor. On the pilot configuration of E11 (Madrid,
compact sub-network of 95 nodes, validation-hidden nodes), the best validation wCE of the no-graph model and of
the graph model was 1.066–1.071, about 3% below ln 3 = 1.099 (E11.md, pilot, variants D1 and D3). The given
graph did not improve on the no-graph model there.

The pipeline is not what limits it. In a positive control, the hidden nodes of the same configuration entered
the loss as training targets, never as input: the condition of the deliverable's severe regime. The same model
then reached 0.94 (E11.md, pilot, D2-bis), with a monotone curve, against 1.07 when the hidden nodes are truly
unseen. The deliverable's figures for propagation came from that condition: its hidden nodes were training
targets (RICOGNIZIONE §0.4; internal review D1).

## E11 — does it matter which neighbours the graph connects?

E11 repeats, under protocol, the deliverable's negative control of the geometry:

- 12 compact sub-networks (Madrid and Melbourne, 81–99 nodes, realised spacing 43–397 m);
- 5 seeds;
- four arms: no graph (G0), the k-nearest-neighbour graph (G1), and the same graph after degree- and
  connectivity-preserving edge swaps with G1's weights permuted (G1-rand(deg)), plus the deliverable's
  edge-count-only randomisation (secondary).

The 240 trainings took 1.12 h on a Mac M3.

**The negative control does not decide.** For D = V(G1) − V(G1-rand(deg)), no configuration shows proximity
prevailing (D ≥ 3 with an interval above zero). An advantage of 3 points or more is excluded in 7 of 12, and 5
are not discriminating. The derived statement is therefore "undetermined" (0 / 7 / 5). Every interval contains
zero; the median half-width is 2.5 points, with about 8 test blocks per configuration.

**The graph does not beat no graph.** V(G1) is favourable in none of the 12 configurations, and unfavourable in
3 (Madrid `comp_q2050`, −0.14 [−0.30; −0.02]; Madrid `comp_q5080`, −2.42 [−6.13; −0.00]; Melbourne
`comp_q5080`, −2.29 [−5.72; −0.02]). The question of which neighbours the graph should connect is therefore
empty in E11: the comparison with a randomised graph cannot show a geometry effect where the graph itself
gives none.

**Spacing and distance.** Neither explains V(G1). With a city term, the slope on realised spacing is
−0.009 points/m [−0.023; +0.017]: the trend is not supported. The two-line form does not beat the linear one
(slope difference +0.054 [−0.020; +0.185]). Replacing spacing with the median distance from a hidden node to the
nearest observed one, the declared sensitivity analysis, gives −0.003 points/m [−0.008; +0.007].

**Operational reading.** At 5% false alarms (threshold chosen on validation-hidden nodes), red recall on hidden
nodes is 0.04–0.08 in Madrid, close to the false-alarm rate itself. In Melbourne it is 0.07–0.25, with no arm
consistently ahead. On segments never seen, none of the arms separates congestion from free flow in Madrid.

> **On compact sub-networks, with the hidden nodes never in input, propagation from instrumented neighbours
> gives no measurable gain, and which neighbours the graph connects cannot matter where the graph itself does
> not.**

**Limits stated with the result:**

- about 8 test blocks per configuration, hence wide intervals;
- the margin of 3 points is a convention (±3% relative), not a power calculation;
- the training input covers 60–95% of the observed nodes, against 100% at evaluation;
- the budget of 1,000 updates acts as an early stop set on validation, because the curve on unseen nodes has no
  plateau;
- `max_speed` was removed after it acted as a node identifier;
- the deliverable's negative-control numbers (Tables 34–35) appear only in the appendix of its defects
  (register of corrections, items 4 and 7).
