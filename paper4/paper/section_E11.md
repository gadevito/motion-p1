# Paper 4 — draft of the E11 section (which neighbours)

Draft of 2026-11-08, revised after the internal review of the full draft (items 1–3). Every number comes from
`paper4/congelamenti/CONGELAMENTO_E11.md` (commit 4e04ba7, fingerprint 459b43ee3e649a31).

---

## Which neighbours: geometry on compact sub-networks (E11)

E11 asks whether the geometry of the road graph matters, against a randomised graph with the same degrees and
weights, as the spacing of the network changes. It uses 12 compact sub-networks of Madrid and Melbourne (81–99
nodes, realised spacing 43–397 m), five seeds and four arms: G0, the k-nearest-neighbour graph G1, the same graph
after degree- and connectivity-preserving edge swaps with its weights permuted (G1-rand(deg)), and an
edge-count-only randomisation (secondary).

**The graph does not beat no graph.** V(G1) is favourable in none of the 12 configurations, and unfavourable in
3 (for example one Madrid sub-network with a spacing of 84 m, −2.42 [−6.13; −0.00]). Which neighbours the graph connects cannot matter
where the graph itself gives nothing.

**The geometry control does not decide.** For D = V(G1) − V(G1-rand(deg)), no configuration shows the true
geometry ahead by 3 points or more; such an advantage is excluded in 7 of 12, and 5 are not discriminating. The
statement is "undetermined" (0 / 7 / 5). Every interval contains zero; the median half-width is 2.5 points,
with about 8 test blocks per configuration.

**Spacing does not explain V(G1).** With a city term, the slope on realised spacing is −0.009 points/m
[−0.023; +0.017], and a two-line form does not beat the linear one. With the median distance from a hidden node
to the nearest observed one instead, the slope is −0.003 points/m [−0.008; +0.007].

At 5% false alarms, red recall on hidden nodes is 0.04–0.08 in Madrid against a realised false-alarm rate of
0.03–0.06: on segments never seen, no arm separates congestion from free flow.
