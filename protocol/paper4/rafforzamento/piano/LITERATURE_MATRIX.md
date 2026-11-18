# Literature matrix for gate G-lit (P4R §3)

Version 0, 2026-11-18, coordination role. Rows: the closest works from the Scopus record of 2026-11-16 (`SCOPUS_SEARCH_20261116.json`) and the plan v3. Cells marked **[abstract]** or **[title]** were filled from Scopus metadata only and must be re-read at full text; cells marked **[full text]** were filled from the full text or the official repository during the planning of 2026-11-16 (`EXPERIMENT_PLAN_20261116.txt`) and must be **re-verified by a co-author** before the gate closes. "?" = not yet known. Nothing in this matrix is a result; the gate closes only when every row has "verified at full text: yes" by a named reader and the co-authors have ratified in writing the three statements at the end.

## Our study, for reference

| Item | Paper 4 (frozen) + strengthening campaign |
| --- | --- |
| task | future forecasting, horizons 15/30/60/120 min, 3 congestion classes (frozen) + continuous factor regression (new, A2/A3) |
| target history | **none** for hidden sites, at training and inference; hidden sites never in loss or inputs |
| inputs | observed sites' dynamic history, calendar, topology; coordinates only as a new factor (I1, S1) |
| calendar baseline | yes (per-slot table; median for regression) |
| training controls | adequacy rule on validation, nested tuning per split (new) |
| component comparisons | G0/G1 (spatial exchange on/off); static × dynamic 2×2 in the dedicated model (new) |
| replication | NDW-Rotterdam, different source, frozen recipes (new) |
| code | public repository, frozen tags |

## Matrix

| # | Work (Scopus id) | Future forecasting or contemporaneous reconstruction? | Target history allowed for the predicted sites? | Inputs: static / dynamic | Calendar baseline? | Training controls reported? | Component comparisons (spatial on/off, static ablation)? | Replication / several networks? | Code available? | Verified at full text | Reader |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | MoGERNN 2025 (86000622989) | forecasting; VS = never-observed sites; NAS = new sites receiving their own recent history at test **[full text]** | VS: no; NAS: yes at test **[full text, repo]** | dynamic history of observed nodes + graph; no coordinates as features **[repo]** | ? | validation identical to training period, 70/30 hardcoded, best_test checkpoint available **[repo audit]** | mixture of experts by aggregation type; no calendar/static ablation reported? **?** | METR-LA, PEMS **[full text]** | yes, ZJU-TSELab/MoGERNN e80f6ca | partly (audit of the code: `evoluzione/audit/AUDIT_MoGERNN.md`); paper to re-read | ______ |
| 2 | UIGNN 2023, Mei et al. (85182752693) | forecasting + sensor placement **[full text arXiv 2309.06800v5]** | excludes missing targets from training (§V-A) **[full text]** | ? | ? | ? | ? | ? | ? | partly (§V-A) | ______ |
| 3 | V-DCRNN, T-ITS 2025 (105003381364) | virtual network, estimation of masked nodes/intersections — forecasting vs imputation **unclear [abstract]** | ? | ? | ? | ? | ? | ? | ? | no | ______ |
| 4 | Varga et al., data-driven distance metrics for kriging, T-ITS 2023 (85151331546) | temporal extension of kriging **[abstract]** | ? (distances may need target history) | distances on network | ? | — | ? | ? | ? | no | ______ |
| 5 | SIML/MSIGN 2026 (105034589342) | variable masks, generalisation to layouts **[abstract]** — unseen mask ≠ unseen target history | ? | ? | ? | ? | ? | ? | ? | no (publisher page 403 on open access) | ______ |
| 6 | Ding et al. 2025, spatio-temporal prompt for inductive extrapolation (105028253337) | Definition 3: output Nu×P×C on the **same** time axis as the input window — not future forecasting as stated **[full text]** | ? | prompts; ? | ? | ? | ? | ? | ? | partly (Def. 3) | ______ |
| 7 | SLPF (105014648543) | forecasting | **uses target data in training** (§4, arXiv 2408.02689v3) **[full text]** → conceptual comparison only | ? | ? | ? | ? | ? | ? | partly (§4) | ______ |
| 8 | Ermagun 2017, temporal detrending to observe spatial correlation (85019149811) | analysis of spatial correlation after detrending, not forecasting **[full text, doi 10.1371/journal.pone.0176853]** | n/a | — | detrending = calendar removal | — | — | — | — | yes (planning) | ______ |
| 9 | Climatology 2026 (105048319921, doi 10.3390/computers15080548) | forecasting; strong temporal baselines and negative graph ablation **[full text]** | observed regime (sites with history) | ? | yes | ? | graph on/off | ? | ? | yes (planning) | ______ |
| 10 | Math et al. 2025, iterative GNN forecasting + placement (105011483390) | co-design on SUMO/Győr **[abstract]** | ? | ? | ? | ? | ? | simulation | ? | no | ______ |
| 11 | TA-ANP 2026 (105053448561; preprint arXiv 2605.25004) | multi-source with floating-car data **[preprint]** — not an absence of local dynamic information | ? | FCD | ? | ? | ? | ? | ? | partly | ______ |
| 12 | Ahsani et al. 2019 (85055094949); Shin et al. 2012 (84896989365) | local measurement (probe coverage/speed bias; loop vs DSRC) **[title/metadata]** — RQ4 only | n/a | — | — | — | — | — | — | no | ______ |

## How to fill a row

Read the full text (and the repository if there is one). For each cell write the fact and where it is (section, table, file:line). Replace every "?" and every [abstract]/[title] mark. If a cell cannot be determined from the paper, write "not stated" — that is a finding. Do not write what the work "probably" does.

## Statements to ratify (co-authors, in writing, before any training)

1. **The gap.** No work in the matrix trains and evaluates a forecast at sites with **no target history at any time**, with a calendar baseline, a spatial-exchange on/off contrast and a static × dynamic factorial on the same network, masks and horizons, **and** a replication on a second data source. (To be confirmed or refuted row by row: a single row that satisfies all of it refutes the statement.)
2. **The comparison that addresses it.** A1–A4 of P4R, as signed.
3. **The expected added value** over the closest row(s): ______ (written by the co-authors after reading, not by the coordination).

If a row already contains the comparison under equivalent conditions, P4R §3 applies: the value of the replication or the core design is reconsidered before any cost is incurred; the decision is recorded as a dated note to P4R.

Ratification: ______ (names, date). Commit of the completed matrix: ______.
