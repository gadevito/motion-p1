# Glossary — Italian terms in code, files and folders

The project was run in Italian. This glossary maps the terms that appear in file names, folder names,
JSON keys and code to the English used in the paper. Arm names follow the paper.

## Process and records

| Italian | English | Meaning |
|---|---|---|
| protocollo | protocol | pre-registered plan of an experiment (`protocol/E<n>.md`), signed and dated before launch |
| pre-registrazione, firma | pre-registration, signature | the protocol with date, commit and fingerprint, fixed before any test number |
| congelamento, `CONGELAMENTO_*.md`, `congelamento_*.json` | frozen record | the generated, immutable record of an experiment's results; never edited by hand |
| impronta | fingerprint | first 16 hexadecimal digits of the SHA-256 of a file (as cited in the paper) |
| giro (di `main.py`) | run, regeneration run | one complete execution of `analysis/main.py` |
| rigenerazione | regeneration | recomputation of every number from the per-cell predictions |
| `CONFRONTO.md` | comparison report | outcome of the last complete regeneration ("TUTTO COINCIDE" = everything coincides; "DIFFERENZE O ERRORI" = differences or errors) |
| rapporto | report | per-run detail (`rapporto.md`, `rapporto.json`) |
| fase | phase | one step of `main.py` (one script with its outputs) |
| tag `paper1-freeze-<data><lettera>` | freeze tag | verified state of code and records |
| esecutore | executor | the team member who ran the experiments and delivered `esecutore/*` branches |
| revisore | reviewer | internal reviewer who signed protocols and decisions |
| registro delle correzioni, difetto | register of corrections, defect | list of corrections made to the pipeline during the study (`register_of_corrections.en.md`) |
| deviazione dichiarata | declared deviation | a departure from the protocol, stated with date and reason in the frozen record |
| correzione datata, nota datata | dated correction | a correction added to a record with its date, the earlier version kept in the history |
| addendum | addendum | additional measures added to a record later, from the same resamples |
| pilota | pilot | small preliminary run used to estimate cost (`E_pilota_e15/`) |
| collaudo | test, acceptance test | automated test of a component before use |
| preflight | preflight | assertions run before a launch (`checks/preflight.py`) |
| scheda dei fatti | fact sheet | `paper/SCHEDA_FATTI.md` |
| criterio, verdetto | criterion, verdict | pre-registered success rule and its outcome |
| confermata | confirmed | a statement whose interval sign is unchanged in a re-evaluation |
| sensibile / insensibile | sensitive / insensitive | E14: a statement that moves / does not move beyond the declared threshold |

## Design of the study

| Italian | English | Meaning |
|---|---|---|
| sensore, nodo | sensor, node | one measurement location |
| sensori iniziali | initial sensors | sensors present during training |
| sensori nuovi | new sensors | sensors installed at t₀ (15 % held out) |
| sensori di validazione | validation sensors | 15 % held out, used only for selections |
| veterani | veterans | initial sensors evaluated after the insertion |
| partizione | partition | one seeded split of the sensors into initial / validation / new |
| seme, semi | seed, seeds | initialisation seeds of training |
| cella | cell | one seed × partition × new sensor (the unit of the paired differences) |
| run, esecuzione | run | one trained model for a city, partition and seed |
| episodio | installation episode | one installation date t₀ with its test period |
| episodio di validazione | validation episode | the installation episode on validation sensors, used for every selection |
| origine | origin | the time at which a forecast is issued |
| origini comuni | common origins | origins older than one week, shared by every arm |
| fascia (d'età), fasce | age band | band of origins by age since installation: (t₁, 48 h], (48 h, 1 wk], > 1 wk (`FASCE_ETA = (192, 672)` steps of 15 min); `fascia2` = older than one week |
| età | age | time since installation |
| bersagli validi, copertura | valid targets, coverage | valid target slots of a sensor in its first 24 h (out of 308) |
| contesto | context | a city or a Caltrans network |
| città | city | Madrid, Londra (London), Melbourne |
| braccio, bracci | arm, arms | one policy or model under comparison |
| statica, ramo statico | static input, static branch | the per-sensor coverage scalar and its branch (`5 → 8`) |
| statica congelata / causale / espansiva / variante (a), (b), (c) | frozen / causal / expanding / variant | coverage scalar: whole-series (frozen campaign); causal variants of E14; expanding window of E15 (default since E15); `OR3_STATICA` selects it |
| campagna congelata / causale | pre-registered (frozen) / causal campaign | the original experiments / E15 |
| ricampionamento congiunto | joint resampling | bootstrap over partitions × seeds × sensor positions (4,000 replicates) |
| soglia | threshold | decision threshold on p(congested) |
| richiamo, falsi allarmi | recall, false alarms | of the congested class |
| quota di calibrazione | calibration share | s = 1 − (F₀ᶜᵃˡ − Cᶜᵃˡ)/(F₀ − C) (E16) |
| recupero | recovery | (L_C − L_F′)/(L_C − L_A) (E17, E15) |
| riduzione del token | token reduction | 1 − (F₀′ − C)/(F₀ − C) |
| costo, tempi | cost, timings | compute measured in a single timing session |
| aggiornamenti, budget | updates, update budget | gradient steps of the embedding adaptation (k) |

## Arms and models (paper notation)

| In files | Paper | Meaning |
|---|---|---|
| `C` | C | identity-free model |
| `A` | A | oracle: identity model trained with the new sensors present |
| `C_A` | C_A | identity-free model trained on the oracle's data (E15) |
| `E` | E | identity model trained on the initial sensors |
| `E1`, `Ep` | E′ | identity model trained with the unknown-node token |
| `F0` | F₀ | E with the mean embedding for the new sensor |
| `F0p` | F₀′ | E′ with the token for the new sensor |
| `F_96`, `Fp_96`, `Fp_672` | F(24 h), F′(24 h), F′(1 wk) | embedding adapted on the first L hours (number = steps of 15 min) |
| `Fpk_672` | F′(1 wk; k) | secondary adaptation with the reselected budget k |
| `R`, `R-orig`, `Rorig_672`, `R-mon` | R, R-orig(L), — | naive retraining (uniform per node); retraining uniform per origin; R-orig with checkpoint selection that also watches the new sensors' last 6 of their 24 hours, weighted by their share |
| `gated`, `gated_sel`, `gated672_0` | gated(τ, N), gated(1 wk, 0) | gating policy (selected; waiting a week without coverage gate) |

## Folders

| Folder | Content |
|---|---|
| `evoluzione/` | the code of the study ("evolution" of the deliverable pipeline) |
| `evoluzione/componente/` | components: model, identity providers, adaptation |
| `evoluzione/esperimenti/` | experiment runners and training |
| `evoluzione/analisi/` | analyses and figures |
| `analysis/` | regeneration (`main.py`) and the paper's tables |
| `analysis/rigenerazione/` | working directories and `CONFRONTO.md` of the regeneration runs |
| `protocol/` | protocols and frozen inputs of later experiments |
| `results/evoluzione/predizioni_*` | per-cell predictions of an experiment |
| `results/evoluzione/*_inserimento_griglia*` | checkpoints of the insertion campaign (grid of origins); `_ep2`, `_ep3` = episodes 2 and 3 |
| `results/evoluzione/pesi_*` | class-weight files actually loaded |
| `_quarantena_*` | quarantined runs, kept for the record and excluded from every analysis |
| `paper/` | fact sheet and cost tables for the manuscript |
