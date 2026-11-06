# Paper 4 — open questions

For the internal review (R) or the experimental colleague (C). Each item refers to `RICOGNIZIONE.md`.
Status updated 2026-11-06: all items closed.

**D1 (R) — Hidden nodes in training.** *Decided (internal review, 2026-10-10):* evaluation nodes are excluded
from both input and loss. In `gomo_sparse.py` training masks are drawn over all nodes, so training-period
labels of nodes later hidden at test enter the loss (RICOGNIZIONE §0.4, §2); the change touches
`make_batch`/`train_gwn` and goes in the pre-registration.

**D2 (R) — G1 and G1-rand.** *Decided:* the given graph is the road graph; the randomisation preserves the
degree sequence; the deliverable's edge-count-only randomisation is kept as a secondary arm in E11.

**D3 (R) — Node blocks in the E9 resample.** *Decided:* blocks = corridors (exact definition to be written in
the pre-registration).

**D4 (R) — Comparison with arm C of Paper 1.** *Decided:* no Paper 1 arm C; the reference is internal to the
cell (hidden against observed nodes).

**D5 (R) — Class thresholds.** *Decided:* 0.8 / 0.4.

**D6 (C) — Geometry, 5 August.** Which copy of `models/gomo_sparse.py` was used? The last archived copy is of
1 August (`campagna_5semi_20260804.tgz`). *Partly answered (2026-10-10): no commit, no epoch timestamps;
on-disk modification 21/8. See the addendum, RICOGNIZIONE §13. Phase 1 verdict final, 2026-11-06: no
geometry or R3 number of the deliverable in the paper; E11 replaces them.*

**D7 (C) — Tables 34–35.** Which script or command computed the negative controls?
`analisi/geometria_criteri.py` finds no pairs with the current covariate names. *Closed by the executor (branch `p4-fase1`), 2026-11-06.*

**D8 (C) — Tables 64–66.** Where are the outputs of the `--exclude-empty` and `--max-dist 30` variants of
`t4c_crossval.py`, and which script produces the ratio in Table 66? *Closed by the executor (branch `p4-fase1`), 2026-11-06: Tables 64–65 regenerated; Table 66 out of the
perimeter.*

**D9 (C) — Generator of `t4cmad_rand_k1.pkl` / `t4cmad_rand_k2.pkl`** (`log/randk.log`, 24/8). *Closed by the executor (branch `p4-fase1`), 2026-11-06.*
