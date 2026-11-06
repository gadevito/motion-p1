# Paper 4 — Phase 0: reconnaissance

Written 2026-10-10 on the earlier history (base `d80043c`, tag `paper1-freeze-20261010`); re-applied
2026-11-06 on the rewritten history (branch `paper4` from `main` = `abbe5a6`; tag
`paper1-freeze-20261103q` = `d327eb1`). No training was run and no metric was computed.
`models/gomo_sparse.py` is byte-identical on both histories (SHA-256 `c82ca3fa74f805ab…`).

**Conventions.** Paths without a prefix are relative to the worktree root and are **tracked files**.
Untracked material (git-ignored) is cited with its location on the author's machine:

- `OR3/data_collection/…` — pre-processed data, in the current `deliverables/OR3/`;
- `OLD/…` — `deliverables/OR3_vecchia_storia/`, the copy of the working tree kept at the history rewrite,
  which is now the only place holding `log/`, `replication/`, `austin/` and `_archivio/spedizioni/`.

All untracked files were read only (`ls`, `grep`, `head`, `tar t`, `stat`). Table numbers are those of the
**deliverable** (`MOTION_deliverable_UC-04_v1.docx`); the Italian guide of the deliverable campaign
(`README.it.md`) and the script docstrings use an older numbering, offset by 2–3 (§11).

---

## 0. Six facts that change the plan

1. **The "one batch per epoch / 32 validation instants" defect is documented in the Paper 1 pipeline, not
   in the Graph WaveNets.** It lives in `evoluzione/esperimenti/addestramento.py` (register of corrections,
   items 1–2; `checks/preflight.py` checks 1–2; `evoluzione/esperimenti/audit_ciclo.py`). The GWNs of R3
   and of the geometry run with `models/gomo_sparse.py`, whose `train_gwn` loops over all batches
   (`for i in range(0, len(perm), args.batch)`) and validates on the whole `va`. Four dated copies of the
   file exist in the archives; `train_gwn` is **byte-identical** in all of them and in `main`, including
   the copy of 1 August, the last one before the geometry campaign of 5 August (§1, addendum §13). The
   git history starts on 2026-09-17, so there is **no "fix commit"** for this script.
2. **The randomised graph does not preserve degrees.** `make_geo_sweep.py`, mode `randomizzato`, keeps the
   number of edges (hence the *mean* degree) and draws uniform pairs (`rng` seed 0); the degree sequence
   is not preserved. The brief asks for "degree-preserving".
3. **The given graph is not always kNN.** In R3 (six contexts, whole cities) the `fixed` arm uses the road
   graph (`*_routes-graph.pkl`, Gaussian kernel on distances); the kNN graph (k = 4) appears **only** in the
   geometry (`geo_sweep/*.pkl`).
4. **Nodes hidden at evaluation enter the training loss.** Training masks are drawn over *all* nodes for
   every batch, so training-period labels of nodes later hidden at test contribute to the loss. The split is
   temporal and `--inductive --no-coords` has no per-node vectors, but this is not "the model sees only the
   observable sensors".
5. **The negative control of the deliverable (Tables 34–35) cannot be regenerated from the repository
   script.** `analisi/geometria_criteri.py:202` pairs configurations by name (`"knn"` → `"rand"`); the
   tracked covariates are named `comp_q*` / `neg_rand_q*`, so the script prints "nessuna coppia knn/rand
   trovata". The interval is a 5-seed t interval (`2.776·sd/√5`), not a resample. How Tables 34–35 were
   computed: **NOT FOUND**.
6. **Class thresholds are 0.8 and 0.4, not 0.8 and 0.5** as the brief §0 states (code and deliverable
   agree, §8).

---

## 1. Graph models

| Item | Finding |
|---|---|
| GWN training script (R3 and geometry) | `models/gomo_sparse.py` (393 lines). Classes `GTCN`, `GCN`, `Block`, `GWN`; modes `none` (G0), `fixed` (given graph), `adaptive` (excluded). Environment: the poetry venv of `models/` (`models/pyproject.toml`, `models/poetry.lock`), as `OLD/log/geo_campagna.log` shows (`…/virtualenvs/models-QWTpj_PQ-py3.12/`) |
| Epoch loop | `train_gwn(mode)`, `models/gomo_sparse.py:242–268`. Inner loop over **all** batches (batch 32), coverage drawn per batch; validation on **all** of `va` in blocks of 256; early stopping, patience 8, 35 epochs, lr 1e-3 |
| Validation set | `starts = arange(T_IN-1, Tn-8)` (line 119); temporal split 70/10/20 on `starts` (`tr`, `va`, `te`). Validation = **all** instants of the middle 10%, scored with the fixed evaluation mask `eval_obs`. Size: T4c ≈ 1,040 instants, GO-MO ≈ 3,500 (from series length, §6; not printed in the logs) |
| Fix commit | **Does not exist in git** for `gomo_sparse.py`: `git log -S'for i in range(0, len(perm), args.batch)' -- models/` returns only the first commit (2026-09-17). Dated copies of `train_gwn`, all identical to `main`: `OLD/_archivio/spedizioni/kit_MOTION_completo_20260729.tgz` (file dated 5/7, SHA-256 `e6fe8f81…`), `R3_scomposizione_20260731.tgz` (30/7, `dd5bf812…`), `campagna_5semi_20260804.tgz` (1/8, `fe44a6c1…`), `OLD/models/gomo_sparse.py.pre_priorecal` (4/9). The only difference between the 1/8 copy and `main` is the distance-attribute patch (lines 90–93), which changes nothing on the cities (`weight` already holds a distance, `README.it.md` §6) |
| Where the documented defect is | `evoluzione/esperimenti/addestramento.py` (Paper 1 pipeline): `checks/preflight.py:75–92`; `evoluzione/esperimenti/audit_ciclo.py`; `protocol/REGISTRO_CORREZIONI.md` items 1–2 |
| Signature in the logs | `OLD/log/geo_campagna.log` (5/8) and `OLD/log/geo_rimedio.log`: lines `[none\|fixed] epoch NN val wCE=… best=…`, gradual curves (e.g. 1.0677 → 1.0433 in 29 epochs), `early stop`. No epoch duration, step count, commit or validation size |
| Probability dumps | The geometry saved `OLD/replication/probs/geo_*_s*.npz` (8 blocks: 2 arms × 4 horizons), as R3 did (`fix_sparse_*`, 29 files): joint resampling can be redone **without retraining** |

## 2. Observability masks

| Item | Finding |
|---|---|
| Function | `sample_obs(mode, frac, rng)`, `models/gomo_sparse.py:108`. `structured`: 6×6 grid (`--grid 6`) on UTM coordinates; cells in random order, added whole until observed nodes ≥ `round(frac·K)`. **Grid cells, not corridors**, and coverage overshoots: 0.46 against 0.40 in R3 Madrid (`OLD/replication/sparse/camp_sparse_t4cmad_s0.csv`, column `cov_frac`) |
| Evaluation | `eval_obs_np = sample_obs(mask, obs_frac, default_rng(seed))`: depends only on the seed; **deterministic** given the seed and the node set; the same for every arm of one invocation |
| Training | `frac ~ U(train_lo=0.15, train_hi=0.6)` **per batch**, new mask per batch, `rng = default_rng(seed+1)`; deterministic given the seed, but batch permutation uses the global `np.random.permutation` (`np.random.seed(seed)`) |
| Loss | `make_batch` (line 158): loss mask `Cm · (1 − obs)`, only nodes *unobserved in the batch*, which can include nodes hidden at evaluation (§0.4) |
| Paper 1 masks | `evoluzione/esperimenti/costruisci_maschere.py`, `collauda_maschere.py`: **data validity** masks, not observability; not reusable for R3 |

## 3. kNN and randomised graphs

| Item | Finding |
|---|---|
| kNN (geometry) | `make_geo_sweep.py:costruisci(modo="knn")`, `--k 4` (default), edge weight = distance + 1 m; undirected (mean degree > k, e.g. 5.23 in Table 34) |
| Randomised | `make_geo_sweep.py:costruisci(modo="randomizzato")`: same number of edges as kNN, uniform `rng.integers` pairs, fixed seed **0**; mean degree preserved, degree sequence **not**. A `modo="casuale"` exists, identical in code, unused |
| Given graph in R3 | `--graph ${G[c]}` = `OR3/data_collection/traffic4cast/<CITY>_2022/gomo_fmt/t4c*_routes-graph.pkl` (cities), `OR3/data_collection/go-mo/gomo/routes-graph.pkl` (loops). `A_fixed` = Gaussian kernel on distance, symmetric normalisation with self-loops (`gomo_sparse.py:152`) |
| Other randomised graphs | `OR3/data_collection/traffic4cast/MADRID_2022/gomo_fmt/t4cmad_rand_k1.pkl`, `t4cmad_rand_k2.pkl`; `OLD/log/randk.log` (24/8). Generator: **NOT FOUND** among tracked files |

## 4. Geometry (Tables 32–35)

| Item | Finding |
|---|---|
| Configurations | `geo_sweep/{madrid,melbourne}_comp_q{20,50,80}{20,50,80}.pkl` (18), `melbourne_dec{1,2,6}.pkl` (594/297/99 series), `madrid_neg_rand_q2080.pkl`, `madrid_neg_rand_q5020.pkl`, `melbourne_neg_rand_q5080.pkl`. Covariates `geo_sweep/covariate_{madrid,melbourne}.csv`. Generator `make_geo_sweep.py` (k = 4, seed 0) |
| Inputs | `--sensors $D2/t4cmad_sensors.csv --targets $D2/targets_t4cmad_d8.npz` (`README.it.md` §7.7); the Melbourne path is not written ("idem melbourne") |
| Command | `README.it.md` §7.7: `gomo_sparse.py --modes none,fixed --inductive --no-coords --mask structured --obs-frac 0.4 --seed s`, seeds 0–4; no `--dump-probs` there, but the dumps exist (§1) |
| Logs | `OLD/log/geo_campagna.log` (115 invocations, 5/8 10:03–18:30); `OLD/log/geo_rimedio.log` (5 invocations, `madrid_neg_rand_q5020`, until 20:50) |
| Outputs | `OLD/replication/geo/geo_<tag>_s{0..4}.csv` (120 files, 24 tags × 5 seeds) + `densrand_t4clon_s*.csv` (9/8) + `sparse_geoF_*` (July) |
| Checkpoints | **NOT FOUND**: `gomo_sparse.py` saves no weights |
| Commit / fingerprint at launch | **NOT FOUND** in the logs (git did not exist); see the snapshot fingerprints (§1) and the addendum (§13) |
| Tables | 32–33: `analisi/geometria_criteri.py --geo-dir replication/geo` (docstring: "Tabelle 30–33"). 34–35: **NOT FOUND** (§0.5) |
| Realised N | Brief and deliverable say N = 99 constant. Logs (`aligned graph: K of …`): Madrid **81–98** (q2050 = 81, q2020 = 84, q5080 = 85, …), Melbourne 96–99; alignment within 20 m merges coincident sensors |
| Sessions | 115 invocations × 2 arms = 230 (deliverable) + 5 of `geo_rimedio` = **240** sessions actually run |

## 5. Technology — Paper 4A (Tables 64–69)

| Table | Script | Inputs | Saved output |
|---|---|---|---|
| 64 (loop–probe agreement, Madrid arterials) | `OR3/data_collection/t4c_crossval.py`, **untracked**, in `data_collection/` (`README.it.md` §7.11, "Tabelle 62–64") | `go-mo/gomo/targets_2021_urb_d8.npz` (65.97 MB), `go-mo/gomo/traffic_sensors.csv` (0.94 MB), `traffic4cast/MADRID_2022/road_graph_nodes_osm.parquet`, `road_graph_edges_district.parquet`, `speed_classes/madrid/` | `OR3/data_collection/crossval_results.csv` (7/7); copy in `OLD/replication/validazione/crossval_results.csv` |
| 65 (Spearman, 399/276 pairs) | same | same | variants `--exclude-empty` (`crossval_results_noempty.csv`) and `--max-dist 30` (`crossval_results_d30.csv`): **NOT FOUND** |
| 66 (raw-input correlation ratio) | same (likely; table → output row **not verified**) | same | — |
| 67 (M30, rank by occupancy band) | `analisi/validazione_colocalizzata.py`, `sez_anello` (docstring "Tabelle 65–67") | `go-mo/gomo/targets_2024_m30.npz` (46.7 MB), `tensors_2024_m30.npz` (37.5 MB) | **stdout only**: no file or log found (`OLD/log/validazione.log` is another campaign) |
| 68 (matching error, Gini 58/42) | same, `sez_accoppiamento`; the value 0.542 is **hard-coded** (line 195), not computed | + `traffic_sensors.csv` | stdout only |
| 69 (Austin, lane aggregation) | same, `carica_austin` / `sez_austin` | `OLD/austin/radar/radar_completo.json` (**2.45 GB**), produced by `austin/radar/scarica.py` | stdout only |
| M30 threshold | `sez_anello:131–147` prints precision/recall at thresholds 0.20/0.30/0.40/0.50 **on the same cells**, and warns that the threshold must be chosen on held-out data: correction 1 of the brief |

SHA-256 of the inputs: **not computed** in Phase 0 (a Paper 1 timing measurement required an idle machine);
to be recorded in `runs/MANIFEST.tsv` at the start of Phase 2.

## 6. Contexts

| Context | Type | Nodes | Period | Pre-processed targets |
|---|---|---|---|---|
| t4cmad | Traffic4cast, measured speed | 900 | 2021-06-01 → 2021-12-31 (10,464 instants) | `OR3/data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz` |
| t4clon | Traffic4cast | 900 | 2019-07-01 → 2020-01-31 (10,557) | `OR3/data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz` (sic: the London file is named `t4cmad`) |
| t4cmel | Traffic4cast | 594 | 2020-06-01 → 2020-12-30 (10,368) | `OR3/data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz` |
| d8_2024 | GO-MO, reconstructed speed | 445 | 2024 (35,068) | `OR3/data_collection/go-mo/gomo/targets_2024_urb_d8.npz` |
| d15_2024 | GO-MO | 384 | 2024 (35,068) | `…/targets_2024_urb_d15.npz` |
| d8_2023 | GO-MO | 444 | 2023 (35,028) | `…/targets_2023_urb_d8.npz` |
| *(4A)* d8_2021 | Madrid probes | 432 | 2021 | `…/targets_2021_urb_d8.npz` |
| *(4A)* m30_2024 | M30 ring | 284 | 2024 | `…/targets_2024_m30.npz` |

Sensor tables: `t4cmad_sensors.csv` (Madrid and London) has `lanes` and `max_capacity` **all NaN**, so under
`--inductive --no-coords` lanes and capacity are 0 and only `max_speed` remains; present in Melbourne (83% and
100%). This is the `Mean of empty slice` warning in the logs.

## 7. Costs

Hardware at the time: Apple M3 Max, 14 CPU, 30-core GPU (MPS), 96 GB RAM; no CUDA. Historical campaigns ran on
`mps`. Epoch times are **not in the logs**; the figures below come from the dates of output files written in
sequence (gaps < 1 h) and are upper bounds, since concurrent campaigns are not excluded.

| Campaign | Arms per invocation | Duration per invocation | Per training |
|---|---|---|---|
| Geometry, N ≈ 99 (5/8) | 2 | median **3.2 min** (118 gaps) | ≈ 1.6 min |
| R3 cities, `camp_sparse` (1–3/8) | 3 (none, fixed, adaptive) | 1 h 39 – 2 h 13, typical **1 h 55** | ≈ **38 min** |
| R3 loops, `fix_sparse` (22–24/8) | 3 | d8_2023 1 h 47 – 2 h 22; d15 2 h 30 – 3 h 18; d8_2024 3 h 37 – 5 h 00 | ≈ **40–100 min** |
| No-graph model | — | not separable: `none` runs in the same invocation | — |

`README.it.md` §10 declares 60–75 h for the geometry: an **estimate, not a measurement**; file dates give about
6 h. Estimates for Paper 4 (sequential, one MPS GPU, times above): E9 ≈ 170 h (three cities) or ≈ 440 h (six
contexts); E10 ≈ 190 h (three cities); E11 ≈ 5 h. Parallelism on MPS was not measured for `gomo_sparse.py`.

## 8. Metrics

| Item | Finding |
|---|---|
| wCE and weights | `gomo_sparse.py:scores()` (line 227): `wCE = Σ W[y]·(−log p_y) / Σ W[y]` on valid cells. Weights `Wnp = Σfreq / (3·freq_k)` from training-period cells **only** (`reg = slice(0, tr[-1]+1)`), over all nodes. Training loss `loss_fn`, same form. Paper 1: `evoluzione/analisi/pesi.py` (shared artefact) |
| Classes | `congestion_emp` in `targets_*.npz` (1/2/3 = green/yellow/red, 0 = missing), built upstream, not in `gomo_sparse.py`. Thresholds **0.8 / 0.4**: `OR3/data_collection/go-mo/2_gomo_targets.py:24`, `4_gomo_urb.py:34`, `t4c_crossval.py:41`; the deliverable agrees ("Le soglie 0,80 e 0,40, definite nell'ambito della competizione Traffic4cast"). Free-flow reference ("95th percentile" in the brief): **not verified** |
| Propagation advantage | `analisi/geometria_criteri.py:vantaggio()` (line 71): per seed `100·(wCE_none − wCE_fixed)/wCE_none`, wCE **already averaged over the 4 horizons**, then mean over seeds. Same convention in `evoluzione/analisi/ricampionamento.py:intervalli()` and `analisi/r3_propagazione.py` |
| Recall at fixed false alarms | Not in `gomo_sparse.py` (only argmax `red_recall`). Paper 1: `evoluzione/analisi/figura_e8bis.py`, `genera_congelamento_e8.py`, on the dumps |

## 9. Statistics

| Item | Finding |
|---|---|
| Deliverable (R3) | `r23_ricampionamento.py`, procedure of `r1_ricampionamento.py`, on dumps, node decoded as `idx % n_nodi`. **Known defect** documented in `evoluzione/analisi/ricampionamento.py`: the published procedure selects nodes with `np.isin`, so a node drawn twice counts once (~63% of cells) and dispersion is underestimated |
| Deliverable (geometry) | Criteria 1, 3, 5: OLS in `geometria_criteri.py:regressione()`; criterion 4: 5-seed t interval; no resampling |
| Paper 1 (reusable) | `evoluzione/analisi/ricampionamento.py:intervalli(pre_a, pre_b, nodi, K, repliche, procedura="molteplicita"\|"gerarchica")` (line 101): wCE by multiplicity (`Σc·S/Σc·W`), seeds and nodes with replacement. Joint partitions × seeds × nodes with B = 4000 in `evoluzione/analisi/analizza_e2.py` (and `analizza_e3.py`, `analizza_f0.py`, …) |
| Reusable for E9? | **Yes in form**: it works on per-seed `p, y, idx` dumps, which `gomo_sparse.py --dump-probs` already writes. **To adapt**: no node partitions in E9 (unit = seeds × node blocks, block definition to be fixed); the `gomo_sparse` dump format (`tag{i}`, `p{i}`, `y{i}`, `idx{i}`) differs from Paper 1's |

## 10. Repository state

| Item | Value |
|---|---|
| Base | `main` = `abbe5a6` (one commit after tag `paper1-freeze-20261103q` = `d327eb1`) |
| Worktree / branch | `deliverables/repo-paper4`, branch `paper4` from `main`; `paper4/{protocol,runs,congelamenti,analysis}` created. The branch is not pushed |
| Environment | **Not created.** Two lockfiles are needed: `models/poetry.lock` (for `gomo_sparse.py`) and the root `poetry.lock` (for `evoluzione/` and the resampling) |
| Changes to existing files | `.gitignore` (`paper4/runs/*`, `!paper4/runs/MANIFEST.tsv`, `paper4/data_cache/`), required by the brief §2; recorded in `MODIFICHE_AL_CODICE.md` |

## 11. Table numbering offset (README.it.md / docstrings → deliverable)

| Content | README.it.md / docstring | Deliverable |
|---|---|---|
| geometry: main, criteria, negative controls | 29–32 / 30–33 | **32–35** |
| loop–probe cross-check | 62–64 | **64–66** |
| co-located (M30, Gini, lanes) | 65–67 | **67–69** |

## 12. Open items

See `DOMANDE.md`.

## 13. Addendum of 2026-11-06 — line numbers in the geometry logs

Added after the experimental colleague's answers of 2026-10-10, which observe that the on-disk modification
time of `models/gomo_sparse.py` (21/8) is later than the geometry campaign (5/8) and conclude "not decidable"
from steps 1–3 of Phase 1. A read-only check on the archived copies narrows this.

The logs print a `RuntimeWarning` with the line of `def _z(a)` in the file that was running. That line
differs across the dated copies:

| Copy | Line of `def _z(a)` | `train_gwn` vs `main` |
|---|---|---|
| `kit_MOTION_completo_20260729.tgz` (file dated 5/7) | 124 | identical |
| `R3_scomposizione_20260731.tgz` (30/7) | 132 | identical |
| `campagna_5semi_20260804.tgz` (1/8, SHA-256 `fe44a6c1…`) | **134** | identical |
| `main` (and `.pre_priorecal`, 4/9) | 137 | — |

Warning lines found in `OLD/log/`: `sparse_geo.log` and `sparse_geoF.log` (18–21/7) → 124;
`geo_campagna.log` and `geo_rimedio.log` (5/8) → **134** only. In both geometry logs the warning echoes the
source text of that line, `def _z(a): return np.nan_to_num(…)`, so the match is on content, not only on the
number.

The geometry campaign therefore ran a file whose layout matches the 1/8 copy, and the 1/8 copy has the
full-epoch loop of `main`. The three-line shift from 134 to 137 is the distance-attribute patch (lines 90–93),
which is the only difference between the 1/8 copy and `main` and is consistent with the 21/8 modification
time. A matching line number is necessary, not sufficient: the 1/8 copy may have been edited elsewhere before
5/8 without moving line 134. This is evidence for Phase 1 (method 2); the verdict belongs to the internal
review.
