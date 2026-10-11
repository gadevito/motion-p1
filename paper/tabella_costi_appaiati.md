# Costi per contesto — una macchina, una sessione, macchina ferma

Generato da `evoluzione/esperimenti/costi_appaiati.py --sessione` il 2026-10-11; numeri in `results/evoluzione/costi_sessione.json` (impronta `3fabd92bb2bf9f0c`), scritto da `costi_sessione.py`. Macchina: Apple M3 Max, torch 2.12.1, un processo, un filo; sessione dal 2026-10-10 16:31 UTC al 2026-10-11 16:23 UTC (23.9 h), load average prima 2.58 / dopo 2.25. Campione isolato: partizione 0, semi 201-203 (citta'), semi 201-203 (PEMS08); mediane sui semi. Controlli: wCE di C, R-orig e F′ riprodotte entro 1e-6 (scarto massimo 0.0e+00 su 45); pesi di E′ riprodotti 9/9; PEMS08 15/15 checkpoint sui pesi di E6.

| contesto | n | C | E′ | F′(24 h) | F′(1 sett.) | R-orig(24 h) | R-orig(1 sett.) | R-orig/F′ (24 h) | R-orig/F′ (1 sett.) |
|---|---|---|---|---|---|---|---|---|---|
| Madrid | 3 | 41.1 min | 41.2 min | 14 s | 138 s | 2225 s | 2229 s | 154.3× | 16.1× |
| Londra | 3 | 41.0 min | 41.1 min | 15 s | 139 s | 2228 s | 2228 s | 153.4× | 16.1× |
| Melbourne | 3 | 29.1 min | 29.2 min | 39 s | 401 s | 1556 s | 1557 s | 40.1× | 3.9× |
| PEMS08 | 3 | 7.1 min | 7.1 min | 13 s | 127 s | 377 s | 379 s | 28.7× | 3.0× |

- A (veterano, non operativo) su PEMS08: 8.4 min di addestramento.
- F′ e' per cella: copia di E′, lotti su tutte le origini della finestra e `aggiornamenti` passi di Adam a gradiente pieno sui nodi di prova (Madrid 135 nodi, 50 aggiornamenti, Londra 135 nodi, 50 aggiornamenti, Melbourne 90 nodi, 200 aggiornamenti): il tempo e' ∝ aggiornamenti × origini × nodi, da cui le differenze fra citta'.
- R-orig riaddestra l'intera rete ampliata dopo i dati: il suo tempo cresce col numero di nodi della rete (900 Madrid/Londra, 594 Melbourne, 170 PEMS08).

| ingresso | impronta |
|---|---|
| `results/evoluzione/costi_sessione.json` | `3fabd92bb2bf9f0c` |
| `results/evoluzione/costi_sessione_pems08.json` | `de392bca1b944791` |
| `results/evoluzione/costi_tabella_sessione.json` | `93d346501f9bc777` |
