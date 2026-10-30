# E18-ter — Terza revisione esterna: livelli assoluti, presentazione delle categorie, formula della wCE

Richiesta del revisore (Andrea De Lucia) del 30/10/2026, ore 09:00 e 09:30, trascritta qui come protocollo
della fase; autore Gabriele De Vito. Nessun addestramento. Ramo `esecutore/e18-ter`.

## 1. Tabella dei valori assoluti (punto 2.3)

Per i confronti centrali (C, A, F₀, F₀′, F′(1 sett.), gated(τ, N), R-orig(1 sett.)): richiamo, tasso di falsi
allarmi, precisione della classe congestionata alla soglia F1-ottima e alla soglia appaiata sul tasso di falsi
allarmi di C in validazione (`validation-FPR-matched`), per contesto, dagli artefatti di E8/E18 già congelati. Se
un valore non è in un congelamento, analisi dalle predizioni salvate, con nota datata. Nome della tabella per il
rimando di P1 nel manoscritto.

Attuazione (`evoluzione/analisi/analizza_e18ter.py --parte livelli`): soglie di `e8_soglie.json` (`prim`, `par`),
matrici di confusione per fascia d'età, sensore e orizzonte di `predizioni_e8/prova_*.npz`, politica gated(τ, N)
composta come in E8. Finestra intera per C, A, F₀, F₀′, gated(τ, N); origini con età > 1 settimana per F′(1 sett.),
R-orig(1 sett.) e la C di riferimento (correzione 27). Per ogni livello: aggregato (confusioni sommate sulle celle,
come `livelli` di E8) e media sulle celle con intervallo al 95 % dal ricampionamento congiunto di E8 (4 000
repliche, seme di E8 del contesto). **Controllo bloccante**: gli aggregati sulla finestra intera coincidono con
`e8_risultati.json` → `livelli` entro 1e-12. I livelli sulla finestra > 1 settimana non sono in alcun congelamento:
calcolati qui, dichiarato.

## 2. Presentazione delle categorie (punto 2 e punto a)

Generatori delle Tabelle IV e V del manoscritto e delle tabelle E9, G21, G23 del supplemento: due colonne di
categoria dagli stessi intervalli — segno rispetto a zero (favourable / unfavourable / inconclusive) e margine
(entro δ = 0,005: sì/no). Nota datata: cambio di presentazione, non di analisi. Didascalia di F17: «below 0.04»
sostituito dal valore vero (massimo ECE osservato), calcolato dal generatore.

## 3. Formula della wCE (punto 3 e punto b)

A P1, dal codice: formula esatta della wCE (normalizzazione, ordine di aggregazione su orizzonti, sensori,
origini) e conferma che l'unità della ROC in E18 è il run con sensori e orizzonti riuniti. Risposta data il
30/10/2026 (`esegui_e4.py` `_aggregati`, `_wce`; `componente/valutazione.py`; `esegui_e16.py` `_nll`, `_AB`,
`_wce_ab`; `analizza_e18.py` `_cella_A`, `_metriche_roc`), riportata nel congelamento §3.

## 4. Uscite

`results/evoluzione/e18ter_risultati.json`; `CONGELAMENTO_E18TER.md` e `results/evoluzione/congelamento_e18ter.json`
dal generatore `genera_congelamento_e18ter.py`; fase `E18TER` in `analysis/main.py`; tabella del supplemento dal
generatore di `analysis/tabelle_suppl.py`. «Pronto per il merge» su `esecutore/e18-ter`.
