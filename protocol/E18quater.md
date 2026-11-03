# E18-quater — C_A ri-valutato con la coverage di valutazione dei sensori nuovi uguale a quella di C

Nota del 2026-11-03 (richiesta del revisore, 3/11, 09:30, punto 1; forma standard e parte B richieste alle 12:40). Esperimento di sensibilità a modelli congelati: nessun addestramento, nessun numero del Paper 1 cambia. Fase `E18QUATER` del giro di rigenerazione (`analysis/main.py`: parte A `--fase analizza`, parte B, congelamento); risultati in `results/evoluzione/e18quater_risultati.json` (parte A) e `results/evoluzione/e18quater_classi_risultati.json` (parte B); record `CONGELAMENTO_E18QUATER.md` + `results/evoluzione/congelamento_e18quater.json` dal generatore `genera_congelamento_e18quater.py`; tabelle del supplemento da `analysis/tabelle_suppl.py` (`scrivi_E18quater`, sezione E dopo E10; `scrivi_classi_sensori`, accanto a C5).

## La domanda

In E15 la differenza C_A − C mescola due cose. **Dati**: C_A è addestrato con la storia anteriore a t₀ dei sensori che simulano le nuove installazioni (corpus privilegiato, `evoluzione/componente/bracci.py` r. 142, `_CORPUS_A` r. 127-128), C no. **Coverage di valutazione**: in `evoluzione/esperimenti/esegui_e15.py`, `_episodio` (r. 365-368, 383, 419), A e C_A ricevono per i sensori nuovi la coverage calcolata su [0, t₀) come per gli iniziali (`nodi_davvero_nuovi`, `evoluzione/esperimenti/inserimento.py` r. 87-94: corpus privilegiato → nessun nodo nuovo per la statica), mentre C, F₀, F₀′, F′ ricevono la finestra espansiva da t₀ (`statica_cella`, r. 106-146, variante `espansiva`). Quanto di C_A − C è coverage e quanto è dati?

## Il metodo

`evoluzione/esperimenti/esegui_e18quater.py`.

- `--fase valuta`: per ciascuna delle 54 celle di E15 (3 città × 3 partizioni × 6 semi) carica il punto di controllo di C_A già addestrato (`ck_di("C_A", …)`), ricostruisce nodi di prova, origini dopo t₁, pesi e fasce d'età esattamente come `_cella_prova`/`_episodio` di E15 (stesse funzioni: `_contesto_cella`, `_valuta_origini`, `_aggregati`), e lo valuta con la statica che vede C: `statica_cella(statiche(D), D, nodi, nn, t0, s)` con `nn` = nodi di prova (finestra espansiva, minimo 24 h). Controlli bloccanti per cella: stessi nodi e stesse origini della cella E15 (`predizioni_e15/prova_*.npz`); la ri-valutazione con la statica di E15 (`nodi_davvero_nuovi("C_A", nn)`) riproduce **bit per bit** gli aggregati `A_C_A`, `B_C_A` salvati da E15; la statica dei nuovi differisce da quella degli iniziali. Uscita: `results/evoluzione/predizioni_e18quater/prova_<città>_p<p>_s<s>.npz` con gli aggregati `A_C_A_esp`, `B_C_A_esp` e le impronte del punto di controllo e della cella E15.
- `--fase analizza`: sulle 18 celle per città, le medie e gli intervalli al 95 % con il ricampionamento congiunto di E15 (`_boot_vec`: partizioni × semi × posizioni dei nodi, 4 000 repliche, seme 20261023) del vettore (C, A, C_A, C_A_esp; e le stesse sulla fascia > 1 settimana). Differenze: **C_A_esp − C_A** (effetto della coverage, stesso modello), **C_A_esp − C** (effetto dei dati a pari coverage), **A − C_A_esp**; riferimenti A − C, A − C_A, C_A − C, le cui medie devono coincidere con `e15_risultati.json` entro 1e-12 (controllo bloccante; stesse estrazioni del ricampionamento, quindi stessi intervalli). Quota del divario dovuta alla coverage: (C_A − C_A_esp)/(C_A − C), con intervallo.

## Parte B — distribuzione delle classi per sensore (richiesta del 3/11, 12:40)

`evoluzione/analisi/classi_per_sensore.py`, sola lettura dei bersagli: per ciascun contesto del Paper 1 e ciascuna partizione dei nodi usata dagli esperimenti (le unità di E8: città p0–p2, PEMS08 p0–p5, PEMS04 p0–p2), con lo stesso perimetro delle valutazioni (`origini_dopo(ok, t1, fine)`, quattro orizzonti, cella (origine, orizzonte) valida se classe > 0), per ogni sensore la quota di bersagli nella classe congestionata (3) fra i validi. Per contesto e gruppo — iniziali (nodi di addestramento), nuovi (nodi di prova), validazione — statistiche sulle coppie (partizione, sensore): numero, minimo, quartili, mediana, massimo, media, sensori con zero congestionati, sensori senza bersagli validi, frequenze aggregate delle tre classi. Uscita `results/evoluzione/e18quater_classi_risultati.json`, con le impronte dei file di bersagli e maschere. Nessun numero del Paper 1 dipende da questa parte.

Soglia di congestione, dal codice: Traffic4cast per segmento (`free_flow_kph` dell'anagrafica, `costruisci_maschere.py` r. 26 e 146; classi 0,8/0,4, `data_collection/traffic4cast/t4c22_adapter.py` r. 11); PEMS per partizione (95° percentile delle velocità aggregate dei soli nodi iniziali nel periodo di addestramento, `estrai_pems04.py` r. 63–64, 119, 122; classi 0,8/0,5). Registro delle correzioni, voce 31: la descrizione nel manoscritto va allineata.

## Ingressi e congelamento

Ingressi: punti di controllo di C_A e celle di prova di E15 (impronte registrate per cella nel json), `e15_risultati.json` (impronta nel json), `e15_k_secondaria.json` tramite `_contesto_cella`; per la parte B, bersagli e maschere dei contesti. Statica: `OR3_STATICA` assente (= `espansiva`); `_contesto_cella` rifiuta ogni altra variante. Le celle `predizioni_e18quater/` sono un ingresso del giro, come `predizioni_e15/`; il giro rigenera i due json di analisi e il congelamento.

## Costo

Due valutazioni di un modello per cella (controllo e nuova), senza adattamenti: frazione della fase `valuta` di E15 (54 celle, 42 min di parete con 7 modelli e 4 adattamenti per cella, `results/evoluzione/e15_prova.log`).
