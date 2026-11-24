# Decision note — E14: collegial renegotiation of the computing budget after the E14-pre benchmark

Date 2026-11-24 · collegial decision at 19:57 (De Vito, Palomba, Ferrucci; written exchange, no minutes) · written by the coordination role · status: decision before the signature of E14. No C0.2 or C1 training has started; only the updates authorised by E14pre have been performed.

## Trigger

`E14pre.md` (signed, tag `paper4-E14pre-20261124`, deposited 18:58) was run on the Spark: C0.1 passed for the four cell types (`e14_pre.json` `643d4fd050111bc6`, bit-identical trajectories on the perturbed setups, identical benchmark repetitions). Benchmark medians, net of the validation passes: 0.810–0.821 s per update, 14.4–14.6 s per validation pass, peak 6.3 GiB; one fit of U_max = 12 000 updates with 24 validations ≈ 2.8 h. With H_cal = 600 h stated at 18:45 (20 % reserve included, 480 h usable), the budget rule of ADAPTER_SPEC §9 / E14.md Order 3 gave: full grid 844 h > 480 h; reduced grid C1 + C2 (180 fits) 507 h > 480 h → **scope to be renegotiated collegially** (P4R §8), U_max not lowered. `e14.py budget --h-cal 600` recorded that outcome in `paper4/runs/e14_grid.json` at 19:45; the gate refuses every launch while the active decision says so.

## Decision

1. **Reduced grid C1 + C2**, 180 fits (45 per cell type: 120 development, 60 final), U_max = 12 000, the contrasts of E14.md unchanged.
2. **H_cal raised from 600 h to 650 h** (520 h ordinary budget, sufficient for the 507 h estimated; 130 h reserve; 27 days and 2 hours of Spark in all, about two days more than the 600 h first stated). The increase is decided **after** the benchmark and motivated by its outcome; the 507 h remain an estimate, not a guarantee.
3. **Sequential execution**, one fit at a time. The multiplication of calendar hours by a degree of parallelism k is **not approved**: the memory available shows that several fits could reside on the machine at once, not that they would advance at the speed measured in isolation (shared GPU, memory bandwidth, CPU); two concurrent fits can each take more than twice as long. If parallelism is ever pursued, a short concurrent-benchmark protocol is written and signed first (configurations, updates, criteria, accounting), then run — updates authorised beforehand, not an improvised trial; it is an additional step that is not needed to close the present gap.

## Ancillary costs and the start of the count

The 507 h cover the 180 fits with their validations. The other computations of E14 are accounted as follows, from the measured unit times where they exist (no estimate is invented where none is measurable):
- **C0.2** (`c0-synth`): four trainings of 2 000 updates with a validation every 250 — ≈ 4 × (2 000 × 0.81 s + 9 × 14.4 s) ≈ **1.9 h**, from the ordinary budget (520 − 507 ≈ 13 h residual).
- **Test** (`test`): one inference pass over the test origins per cell, of the order of a validation pass (14.4 s) — ≈ **0.3 h** for 60 cells, from the ordinary budget.
- **Analysis** (`analysis`): CPU bootstrap, minutes; from the ordinary budget.
- **Sensitivity diagnostic** (`sensitivity`): float64 on the CPU, two states, of the order of 600 backward passes each on 4 origins; no measured unit time — **charged to the reserve** (130 h), its actual duration recorded in the report; it occupies the Spark's CPU, not the GPU.
- **E14-pre** (1 120 updates, already executed under its own protocol, ≈ 0.4 h of fits plus validations) is **not** counted: the 650 h run **from this decision** (2026-11-24 19:57).
The usable 520 h therefore cover 507 + 1.9 + 0.3 + minutes ≈ 509–510 h; everything beyond an estimate (the 507 h included) draws on the reserve, whose use is recorded.

## Procedure for the records (explicit, no silent overwrite)

- The record of the renegotiation outcome is **kept**: `paper4/runs/e14_grid.json` written at 19:45 (H_cal 600 h, grid `renegotiate`, bound to `e14_pre.json` `643d4fd050111bc6`) is renamed to `paper4/runs/e14_grid_renegotiate_20261124.json` and committed (`git add -f`).
- The new decision is then produced by the same rule on the same benchmark: `e14.py budget --h-cal 650 --by "Gabriele De Vito"` writes `paper4/runs/e14_grid.json` (grid `reduced`, cost full 844 h, cost reduced 507 h, usable 520 h, bound to the same report fingerprint), committed (`git add -f`) and frozen with the E14 tag as E14.md Order 3 prescribes; the gate re-verifies the binding and reproduces the rule with H_cal = 650 h.
- E14.md draft 10 is signed with this note cited in its signature line; no other text of E14.md changes (Order 3 already provides the reduced grid and the budget file).

## Consequences

Development phase: 60 cells × 2 configurations = 120 fits; final phase: 60 fits; expected ≈ 507 h of Spark, sequential. Everything else as E14.md draft 10 and ADAPTER_SPEC draft 5.
