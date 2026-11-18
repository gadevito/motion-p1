# E13-pre — Microbenchmark of training cost (P4R §2, §8, gate G-compute, part 1)

Draft 1, 2026-11-18, coordination role. Protocol to be signed and deposited before execution (P4R §10). **Measures cost only.** No test metric is computed; the validation values produced by the pipeline's checkpoints are not read, not recorded in any table and not used for any choice. This protocol does not authorise any other run.

## 1. Purpose

Confirm or reduce, before E13 is signed, the budget of the classification campaign (A1: 300 fits of G0/G1 on the Mac) and give a preliminary estimate for the dedicated model in its original form (P4R §8). The second microbenchmark, E14-pre, measures the **adapted** dedicated model after the adapter is reviewed and is a separate protocol.

## 2. What is measured

| Measure | Arms | Data | Updates | Machines |
| --- | --- | --- | --- | --- |
| seconds per update, full update (forward, loss, backward, step), batch 32 as in the campaign | G0, G1 | Madrid, coverage f = 0.20 (targets 0.2/0.2/0.6), split seed 0, grid of E9 | difference between a run of 60 and a run of 10 updates, divided by 50; three repetitions, median and range | Mac (MPS, CPU), Spark (CUDA, CPU) |
| peak process memory (RSS) and device memory allocated, reported separately, never summed | G0, G1 | same | same | same |
| seconds per update and memory of the dedicated model, **original code at commit `86b153fb4bf9…`**, synthetic tensors with the real node count of Madrid (K kept nodes as reported by `Setup`), batch 32 | MoGERNN original | synthetic (the audited benchmark `evoluzione/audit/benchmark_mogernn.py`, unchanged) | its default warm-up and measured updates | same |
| fixed costs: `Setup` construction time, one checkpoint (validation prediction) time | — | Madrid f = 0.20 | — | same |

Runs are launched **with no other campaign or heavy process on the machine** (the audit of 2026-10 showed a 5× distortion otherwise); the launcher records the load average before and after.

## 3. How the budget is derived (rule fixed now)

A1 cost on the Mac = 300 × U × t_update(arm, MPS) + 300 × (Setup + 11 checkpoints) with U = the cap of E13 (10 000 unless E13 states otherwise; the E9 pilot gave U = 1 000 by its rule — E13 restates the rule); reported as hours per arm and in total. A2/A3 cost on Spark is **not** derived here beyond the order of magnitude from the original model: it is the object of E14-pre. The outcome of E13-pre is one of: (a) A1 within the agreed calendar at the full grid; (b) A1 requires the uniform reduction of P4R §8 (grid 4 → 2 for all families); (c) A1 unsustainable even at 500 → scope renegotiated before any test. The outcome is written as a dated note to P4R with the numbers.

## 4. Execution

Code: `paper4/code/e13pre.py` (new; imports `p4b.py` and `e9.py` unchanged) and `evoluzione/audit/benchmark_mogernn.py` (unchanged). Frozen by tag `paper4-E13pre-<date>` after signature; launched by the responsible author from a clean checkout of the tag on each machine:

```
$PY paper4/code/e13pre.py --device mps   --out paper4/runs/e13pre_<host>
$PY paper4/code/e13pre.py --device cpu   --out paper4/runs/e13pre_<host>
$PY evoluzione/audit/benchmark_mogernn.py --repo <local MoGERNN checkout at 86b153f> --dispositivo mps  (Mac)
$PY evoluzione/audit/benchmark_mogernn.py --repo <...> --dispositivo cuda (Spark)   [or cpu where cuda is not accepted by the script: see §6]
```

Outputs: `e13pre_<host>/report.json` (every measure, environment, git commit, load averages, fingerprints of the data files read) and `report.md`; committed with the dated note. Raw checkpoint values are written by the pipeline into the run directory as it always does; they are **not** copied into the report.

## 5. Checks folded into this run (no cost, recorded in the report)

- Fingerprints of the Madrid data files read by `Setup`, and of the London files named in `e9.py` (`LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz`, …): the London fingerprints must differ from the Madrid ones (file names reuse the Madrid stem; a wrong path would load Madrid twice). A1 uses London: this check is prerequisite to E13.
- `torch.backends.mps.is_available()` / `torch.cuda.is_available()`, library versions against `paper4/ENV.txt`; differences listed.

## 6. Open points to settle at signature

- Whether `benchmark_mogernn.py` accepts `--dispositivo cuda` (it was written for cpu/mps); if not, E13-pre reports the Mac numbers only for the original model and E14-pre covers Spark.
- Location of the local MoGERNN checkout (not in the repository: `evoluzione/MoGERNN-main/ORIGINE.md`).

## Signature

Responsible author: ______ date ______ (Europe/Rome). Tag: ______. Deposited with DEP-01: see `P4R_RECEIPT.md`, later receipts.

## Dated notes after signature

(none)
