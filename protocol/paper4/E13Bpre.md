# E13B-pre — authorised preflight updates of E13B: hidden-node invariance (B0.1) and cost benchmark

**Pre-registration.** Date ______ · commit ______ (code `p4b.py` ______, `e9.py` ______, `e13.py` ______, `e13b.py` ______; E13B preflight log `e13b_preflight.log` ______, 0 failures) · signed: ______ · internal review: ______ · launched by ______ (Mac M3 Max, MPS).

Draft 2 of 2026-11-19 (gate completed on the code review), written under P4R as revised by the collegial decision of 2026-11-19 and under `E13B.md` (draft 3, Order step 3). It covers **every model update that precedes the signature of E13B**, so that the signature of E13B does not document them retroactively. The sequence is binding: implementation → review of `e13b.py` and of its self-test → deterministic preflight of E13B (no update) → this protocol signed, deposited and tagged → the updates below → signature of E13B. No other training is authorised by this protocol; B0.2 and B1 belong to E13B.

## What runs (`e13b.py pre`, once; the command refuses to run if its report exists)

**B0.1 — hidden-node invariance, four trajectories of 50 updates (200 updates).** Madrid, seed 0, regime I0, configuration C1, initialisation stream `p4b.K_INIT`. For **each arm** D1 and D0: one trajectory on the ordinary setup and one on the perturbed setup (`_perturbed_copy`: the dynamic readings of every validation-hidden and test-hidden node replaced by noise; the classes of test-hidden nodes replaced; validation labels kept). The comparison is **per arm, original against perturbed**: the 50 per-step training losses, the parameters after 50 updates and the validation predictions on 64 origins must be identical to the bit. D1 against D0 is not an invariance check and is not compared here. Criterion: pass if all three identities hold for both arms; otherwise E13B is not signed until the cause is found and corrected (dated note, new tag of this protocol).

**Benchmark — seconds per update, D1 and D0.** Same setup; 60 updates per repetition, three repetitions per arm, checkpoint every 10 updates; seconds per update = (t₆₀ − t₁₀)/50 per repetition, median of three, as in E13-pre; the exact feature computation (double precision on the CPU, as the frozen R2 code) is included in the measured time. The result is written into the signature line of E13B and used for its cost section (B1 nominal: 150 trajectories × 10 000 updates plus checkpoints; B0.2: 4 trainings of 2 000 updates). The device, library versions and load average are recorded.

Total: 200 + 360 = **560 updates**, two arms, one city, one seed; no checkpoint selection, no test node, no real-data result.

## Gate of this protocol

`e13b.py pre` refuses to run unless: the nearest `paper4-E13Bpre-*` tag is reachable from HEAD; `p4b.py`, `e9.py`, `e11.py`, `e13.py`, `e13b.py`, `E13.md`, `E13B.md` and this protocol are identical to that tag; the working tree is clean; the signature line of this protocol is filled; `paper4/runs/e13b_pre.json` does not exist (an interrupted attempt leaves it with status *incomplete* and is not repeated without a dated note); the approved deterministic preflight log `e13b_preflight.log` exists, reports 0 failures and carries the current code fingerprints (its fingerprint is recorded in the report); the device is **MPS** (no silent fallback to CPU). The report records the fingerprints of this protocol and of `E13B.md`, the device, the environment and the load average, and is written before the first update and after every step.

## Output

`paper4/runs/e13b_pre.json`: B0.1 identities per arm, seconds per update per repetition and median per arm, device, environment, load average, tag, time; committed with `git add -f`; its fingerprint goes into the signature line of E13B.

## Deviations and dated notes

None.
