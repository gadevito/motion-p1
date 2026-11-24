# Decision note — E14: a common road radius for the method's graph (revision of the draft before the pre-registration)

Date 2026-11-24 · written by the coordination role · decided by the responsible author (De Vito) with the internal reviewer (Ferrucci), written exchange of 16:35–16:46 · status: **revision of the E14 drafts before signature, deposit or any fit** (no `paper4-E14*` tag exists; the deterministic preflight of 2026-11-24 11:15 performed no model update) — not a deviation.

## What was observed (topological diagnostic, before any fit)

The deterministic preflight of E14 (commit `447ee2b`, Spark, log `e14_preflight.log`, 0 failures) built the method's graph as ADAPTER_SPEC draft 4 §6 prescribed — Gaussian kernel on road-network distance, σ = standard deviation of the finite distances, weight threshold 0.1 — on the E11 aligned road graphs, where **every pair of kept sensors has a finite distance**. σ was therefore dominated by the far pairs and the graph came out dense:

| city | K | nearest sensor (road, median / p90) | σ | density | degree median / min | isolated |
|---|---|---|---|---|---|---|
| Madrid | 828 | 31 m / 121 m | 1 874 m | 0.406 | 302 / 134 | 0 |
| London | 774 | 44 m / 93 m | 1 544 m | 0.393 | 292 / 25 | 0 |
| Melbourne | 587 | 154 m / 495 m | 10 400 m | 0.441 | 268 / 106 | 0 |

The structural dependency bound of C0.5(a) was 1.0 everywhere, as expected on such a graph. The reference method's data are built differently: DCRNN's `gen_adj_mx.py` initialises the distance matrix to ∞, fills in only the pairs present in its distance file and takes σ on the finite ones (https://github.com/liyaguang/DCRNN/blob/master/scripts/gen_adj_mx.py); we have no source on how that file was generated and attribute no radius to it.

Diagnostic of a road radius R applied before σ (pairs farther than R along the road network treated as not connected), same statistics, no model involved (`graph_radius.py`, one-off, outside the repository):

| city | R | σ | density | degree median / min | isolated |
|---|---|---|---|---|---|
| Madrid | 3 000 m | 815 m | 0.153 | 123 / 9 | 0 |
| Madrid | 2 000 m | 548 m | 0.093 | 76 / 2 | 0 |
| Madrid | 1 000 m | 279 m | 0.038 | 29 / 0 | 1 |
| Madrid | 500 m | 145 m | 0.017 | 13 / 0 | 19 |
| London | 3 000 m | 819 m | 0.174 | 129 / 2 | 0 |
| London | 2 000 m | 544 m | 0.101 | 80 / 0 | 2 |
| London | 1 000 m | 276 m | 0.039 | 31 / 0 | 3 |
| London | 500 m | 145 m | 0.018 | 12 / 0 | 7 |
| Melbourne | 3 000 m | 922 m | 0.027 | 13 / 0 | 5 |
| Melbourne | 2 000 m | 649 m | 0.020 | 9 / 0 | 15 |
| Melbourne | 1 000 m | 302 m | 0.012 | 3 / 0 | 71 |
| Melbourne | 500 m | 150 m | 0.007 | 1 / 0 | 233 |

## Alternatives examined

- **No radius (draft 4 as written).** Faithful to the letter of the kernel; the dedicated model would operate on a dense graph (density ≈ 0.4). Rejected.
- **A common road radius R for the three cities, applied before σ.** 2 km keeps the densities of Madrid and London at 0.09–0.10 (median degree 76–80) and leaves Melbourne sparse (0.02, median degree 9, 15 isolated nodes of 587) — a property of its sensor layout, reported; 3 km keeps Madrid and London at 0.15–0.17 with median degrees above 120. **Chosen: R = 2 000 m.**
- **A per-city radius** (e.g. a multiple of the median nearest-sensor distance). More homogeneous graphs, but a rule of our own calibrated on the cities; rejected for the same reason the diagnostic of C0.2 is not adapted to the data.

## Decision and its motivation

A common road radius of **2 000 m**, applied before the estimate of σ, as an **explicit adaptation of ours** whose purpose is to preserve the locality of the connections (exchanges limited to road-local pairs, the same rule in the three cities). It is not chosen to make C0.5(a) informative, and the resulting *dependency excluded* nodes are a consequence to be reported per city. A dense graph makes C0.5(a) non-discriminating, which by itself does not show that diffusion and pooling are meaningless. The experts of an isolated node aggregate nothing from neighbours; their output is not necessarily zero (the transformations after the aggregation carry biases and learned parameters): such a hidden node receives no dynamic reading from the observed nodes and can still use the calendar, the coordinates in S1 and the learned parameters.

## Consequences

ADAPTER_SPEC_E14.md draft 5 (§6), E14.md draft 10 (one line of the summary paragraph), `mogernn_adapter.py` (`ROAD_RADIUS_M = 2000`, the cutoff before σ, descriptive statistics returned), `e14.py` (statistics recorded in `adjacency_e14` and `e14_struct.json`; the preflight logs, per city, σ, the effective radius σ·√ln 10, the longest surviving edge, density, degree median / min and the isolated nodes, and asserts that no surviving edge exceeds the radius), the self-test (radius checks). The self-test and the deterministic preflight are run again; no fit has been performed under any version. Traced in the commit message and in this note.
