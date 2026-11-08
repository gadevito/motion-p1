# Paper 4 — draft of the data and code availability statement

Draft of 2026-11-08, after the internal review of the full draft (item 13). Zenodo record reserved by Gabriele
(10.5281/zenodo.24059573); three archives from the partition of `paper4/runs/` by the executor
(`protocol/paper4/zenodo/RIPARTIZIONE_RUNS.md`, c9222f224441b6b2): regeneration 25.7 MB and pilot 35.0 MB in one
archive, predictions of E9 19.53 GiB, predictions of E11 3.72 GiB.

---

## Data and Code Availability

Pre-registrations, protocols, frozen records, the register of corrections and the regeneration script are at
https://github.com/gadevito/motion-p1, under `protocol/paper4/` and `paper4/`, with a README that maps every
experiment to its pre-registration, frozen code and frozen record. The per-cell predictions and the run folders are
archived at Zenodo, https://doi.org/10.5281/zenodo.24059573, in three archives: the regeneration inputs of every
frozen record with the pilot runs (about 61 MB), the per-cell predictions of E9 (19.5 GiB) and those of E11
(3.7 GiB). Model states are not saved: the frozen code keeps checkpoints in memory for validation-based selection and writes only per-cell predictions; every number regenerates from those, while re-evaluating the models on other data requires retraining (180 + 240 trainings, about 7.5 h on the Mac M3). External data: the
Traffic4cast benchmark [neun2023t4c]; the Madrid loop and Austin radar data as used by the project report [motion2026uc04], with
the fingerprints of every file in the repository.
