# Register of corrections (Paper 4)

Consolidated list of the defects found during Paper 4, with the correction adopted and its source. Items 1–3
are defects of the deliverable UC-04 pipeline found during Phase 0 and the drafting of the protocol; they are
corrected in the Paper 4 pipeline, not in the deliverable. The paper refers to the items by number.

Other defects of the deliverable found in Phase 0 are listed in `paper4/RICOGNIZIONE.md` §0, but are not
registered here because no Paper 4 number depends on them:

- the randomisation preserved only the edge count;
- hidden nodes entered the loss;
- Tables 34–35 cannot be regenerated;
- the resampling used `np.isin`.

| # | Defect | Correction and measured effect | Found by | Source |
|---|---|---|---|---|
| 1 | Windows built by index across calendar jumps: the Traffic4cast series are one-week blocks separated by 7-day jumps (Madrid 15, London 16, Melbourne 15), and `models/gomo_sparse.py:119` builds origins as `arange` over raw indices | admissible-origin rule (15-min cadence from the first input step to the last target), with a causality test, as in Paper 1 (register of corrections item 5). Effect: to be measured as the share of excluded origins per city | reading the timestamps of the target files while drafting the perimeter, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.3 |
| 2 | Free-flow reference on the loop contexts computed as the 85th percentile of speed over the whole year, test period included (`OR3/data_collection/go-mo/2_gomo_targets.py:42`) | 85th percentile on the training period only, if GO-MO contexts are used in forecasting; the city contexts use the provider's `free_flow_kph`, which is causal | reading the target builders, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.1 |
| 3 | Population: `gomo_sparse.py` aligns 828 / 774 / 587 nodes (Madrid, London, Melbourne), not the 900 / 900 / 594 of the target files | declared; the same difference as Paper 1, register of corrections item 8 | `aligned graph` lines in `OLD/log/sparse_5semi.log`, `sparse_fixed.log`, `gomo_corretto.log`, 2026-11-06 | `protocol/paper4/PROTOCOLLO.md` §2.3 |
