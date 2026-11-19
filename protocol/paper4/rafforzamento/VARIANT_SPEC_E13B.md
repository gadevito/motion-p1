# Specification of the variant for protocol E13B — draft 3, approved for the drafting of E13B (three alignments of 2026-11-19 12:38 incorporated: I0 only with `static=False`, A0.1 wording, I3 qualification)

Coordination role, 2026-11-19; draft 1 reviewed by F. Ferrucci and the co-authors (decisions on the open points and two substantive corrections incorporated below). Mandate: collegial decision of 2026-11-19 (P4R, dated note; E13.md, closure note). This document specifies the variant and its primary contrast; it authorises nothing. Protocol E13B (controls, criteria, budgets, stopping rule, analysis) is written after this specification is reviewed. Everything here is informed by the development evidence A0.2, I1, I2 and I3 of E13 and is not presented as a demonstrated repair of G1.

## 1. What stays identical to E9/E11/E13

Cities, sensors, aligned road graphs, f = 0.20, grids, node sets per seed (`p4b.node_sets`), cell masking in training (`batch_mask`, same stream), origins and the 70/10/20 split with purge, the 11 input channels of `p4b.Setup.batch` and their construction, class thresholds and weights, the weighted cross-entropy, the four horizons, the per-cell outputs, the hidden-node rules (never in the training loss and never in the inputs; validation-hidden nodes serve the authorised selection; test-hidden nodes are read once; A0.1 unchanged), the development/extension/final/test machinery of `e13.py` (configurations C1–C4 nested per split, checkpoints every 500, adequacy rule, lock, two-way block bootstrap, per-horizon metric), the gate and the frozen-version model. Information availability is unchanged: a masked or hidden node contributes nothing of its own, in training, selection or inference.

## 2. The variant: GF (graph feature, no graph convolution)

Architecture: `p4b.GWN` with `graph=False` (the G0 architecture: start convolution, four blocks with temporal convolutions, skip branches, two output convolutions; no graph convolution anywhere), `hidden=32`, `blocks=4`, dropout per configuration, as in E13. No added depth, no change to blocks, kernels or dilations.

Inputs: the 11 channels of `p4b.Setup.batch` plus **two channels**, computed for every node and every step of the input window from the **input nodes of the batch only** (`inp`; at validation and test, the observed nodes), hence history-free:

- **F (normalised neighbourhood factor).** With A the kernel adjacency G1 receives (`p4b.kernel_adjacency` on the aligned graph), M = Σ_{k=1..6} A^k (6 = the receptive field of the predictions of `p4b.GWN`, I3), r the factor channel as in channel 0 (`Rf`, i.e. r with non-finite values set to 1.0, multiplied by the input indicator), for node n and step t: F_n(t) = Σ_m M[n,m]·om_m·r_m(t) / Σ_m M[n,m]·om_m when the denominator is > 0, and 0 otherwise. Numerator and denominator are computed exactly as in the frozen R2 code of I2: both in double precision on the CPU from M (float64), the input indicator and the window of r, the final feature then converted to single precision. This is the R2 feature verified there against `tabular_diagnostic` within 6·10⁻⁸; its cost is measured as part of the pipeline (§4). Any numerical optimisation (for example the numerator in single precision on the device) is a separate change to be verified on its own and does not inherit the tolerance observed in R2.
- **R (reach indicator).** R_n = 1 if the denominator above is > 0 (a path of ≤ 6 steps from an input node exists), else 0. Constant over the window. It is a property of the graph and of the input set, not of any reading.

Unreachable nodes (R = 0): F is 0 and R is 0; the model sees that no neighbourhood information is available and predicts from the remaining channels. Normalisation creates no missing path: the share of unreachable targets is the one measured by I3 — for the training targets, over the 20 masks sampled per split, not over the whole future training trajectory — and is reported with the results for every (city, seed), training targets included. No propagation beyond 6 steps, no kNN graph, no distance-based neighbourhood: the neighbourhood is the one the historical G1 had.

Channel count: 13 in both arms. Static information identical in both arms: `static=False`, so the max_speed channel is always zero; no coordinate channels (regime I0).

## 3. Primary contrast: with versus without dynamic readings

- **D1 — with dynamic readings.** The 13 channels as above.
- **D0 — without dynamic readings.** Same architecture, same 13 channels, same static information, same calendar channels, same input indicator (om) and same reach indicator R; the dynamic readings and **every derivative of them** are set to zero for every node and step: channels 0 (r), 1 (flow), 2 (occupancy), 3 (historical average, an aggregate of the readings over the training period) and F. What remains informative in D0: calendar (5 channels), om, R; the max_speed channel is zero (`static=False`). D0 is therefore a learned calendar-and-structure predictor with the same parameters and training as D1; it is not the calendar baseline of E14 (a table), and the two are reported separately.

The primary contrast measures the benefit of making observed-site readings and their derivatives available to the trained pipeline, beyond the shared calendar and structural information. It does not isolate the feature F alone: `BatchNorm2d` shares statistics across nodes during training, so the channels 0–3 present in D1 can shape shared statistics and parameters even where they are masked on the targets; and D0 removes the historical average together with the recent readings, so the contrast does not separate the contribution of the recent readings from that of the climatology. The statement scales are those of E13 (sign; margin of 3 points). Both arms receive the same batches, masks, origins, seeds and initialisation streams (arm-specific only where E13 already differentiated).

No comparison with the historical G0 of E13: A1 of E13 did not start, so those real fits do not exist.

Regimes: **I0 only.** I1 (coordinates) is outside the current perimeter, without automatic recovery later.

## 4. Controls of E13B (to be fixed in the protocol before execution)

Development and verification are separated: A0.2, I1, I2, I3 are development evidence and are not reused as verification. E13B fixes before execution:

- **Synthetic dependent and independent controls on realisations not yet observed**: generator of version 2 (`synth_processes`, unchanged in form), **new seed(s) fixed in the protocol** and never used before; validity check on the graph feature before any training (thresholds fixed in the protocol, chronology recorded); then D1 versus D0 with the A0.2 budget (2 000 updates, checkpoints every 250 as in A0.2 of E13, or as the protocol fixes) and explicit rules: *best checkpoint* = the checkpoint ≥ 500 at which D1's validation wCE is minimal, V(D1) = 100 (wCE_D0 − wCE_D1)/wCE_D0 read there; the **dependent control passes if V(D1) ≥ +3 at the best checkpoint**; the **independent control signals an anomaly if V(D1) > +3 at any checkpoint ≥ 500** (not only at the best one) — an anomaly to be explained in a dated note before anything else, not a demonstration that an advantage is impossible, since the independent process is constructed so that nothing of the hidden nodes is predictable from the observed nodes beyond the shared calendar. **One new realisation per condition**, as a minimal functional verification, declared in advance; no substitution after the outcome; no selection of seeds, generators or variants after seeing results.
- **Deterministic checks**: A0.1 (noise on the hidden nodes' readings leaves inputs, training losses, parameters and predictions identical — the feature is computed from input nodes only, so this must hold bit for bit; the validation loss is not invariant if the hidden nodes' labels themselves are perturbed, and A0.1 perturbs readings, not labels), the feature equal to `tabular_diagnostic`'s computation on validation origins with all observed nodes as inputs, A0.4, A0.5, the preflight assertions of E11/E9, and the structural measurement of I3 reproduced for the record.
- **Costs**: an authorised preflight benchmark (E13-pre style, a bounded number of updates of D1 and D0 on the Mac, the exact feature computation included) before the full fits, since the feature adds a per-batch computation; the E13 budget is not transferred automatically.
- **Binding stopping rule**: if the dependent control is not passed, or the independent control shows an unexplained anomaly, real fits stay blocked; no automatic change of generator, neighbourhood or architecture; a further investigation requires a new collegial decision.

## 5. Decisions on the open points of draft 1 (2026-11-19)

| Point | Decision |
| --- | --- |
| Historical average HA | Zeroed in D0, with the other derivatives of the readings. |
| Reach indicator R | Kept in both arms. |
| Coordinates | I0 only; I1 outside the current perimeter, without automatic recovery later. |
| Comparison with the historical G0 of E13 | Removed: A1 did not start, those real fits do not exist. |
| Synthetic realisations | One new realisation per condition, as a minimal functional verification, without substitution after the outcome. |
