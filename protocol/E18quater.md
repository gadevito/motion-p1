# E18-quater — C_A ri-valutato con la coverage di valutazione dei sensori nuovi uguale a quella di C

Nota del 2026-11-03 (richiesta del revisore, 3/11, 09:30, punto 1). Esperimento di sensibilità a modelli congelati: nessun addestramento, nessun numero del Paper 1 cambia. Non entra nel giro di rigenerazione (`analysis/main.py`); i suoi risultati stanno in `results/evoluzione/e18quater_risultati.json` e nel resoconto derivato `protocol/e18quater/RISULTATI.md`.

## La domanda

In E15 la differenza C_A − C mescola due cose. **Dati**: C_A è addestrato con la storia anteriore a t₀ dei sensori che simulano le nuove installazioni (corpus privilegiato, `evoluzione/componente/bracci.py` r. 142, `_CORPUS_A` r. 127-128), C no. **Coverage di valutazione**: in `evoluzione/esperimenti/esegui_e15.py`, `_episodio` (r. 365-368, 383, 419), A e C_A ricevono per i sensori nuovi la coverage calcolata su [0, t₀) come per gli iniziali (`nodi_davvero_nuovi`, `evoluzione/esperimenti/inserimento.py` r. 87-94: corpus privilegiato → nessun nodo nuovo per la statica), mentre C, F₀, F₀′, F′ ricevono la finestra espansiva da t₀ (`statica_cella`, r. 106-146, variante `espansiva`). Quanto di C_A − C è coverage e quanto è dati?

## Il metodo

`evoluzione/esperimenti/esegui_e18quater.py`.

- `--fase valuta`: per ciascuna delle 54 celle di E15 (3 città × 3 partizioni × 6 semi) carica il punto di controllo di C_A già addestrato (`ck_di("C_A", …)`), ricostruisce nodi di prova, origini dopo t₁, pesi e fasce d'età esattamente come `_cella_prova`/`_episodio` di E15 (stesse funzioni: `_contesto_cella`, `_valuta_origini`, `_aggregati`), e lo valuta con la statica che vede C: `statica_cella(statiche(D), D, nodi, nn, t0, s)` con `nn` = nodi di prova (finestra espansiva, minimo 24 h). Controlli bloccanti per cella: stessi nodi e stesse origini della cella E15 (`predizioni_e15/prova_*.npz`); la ri-valutazione con la statica di E15 (`nodi_davvero_nuovi("C_A", nn)`) riproduce **bit per bit** gli aggregati `A_C_A`, `B_C_A` salvati da E15; la statica dei nuovi differisce da quella degli iniziali. Uscita: `results/evoluzione/predizioni_e18quater/prova_<città>_p<p>_s<s>.npz` con gli aggregati `A_C_A_esp`, `B_C_A_esp` e le impronte del punto di controllo e della cella E15.
- `--fase analizza`: sulle 18 celle per città, le medie e gli intervalli al 95 % con il ricampionamento congiunto di E15 (`_boot_vec`: partizioni × semi × posizioni dei nodi, 4 000 repliche, seme 20261023) del vettore (C, A, C_A, C_A_esp; e le stesse sulla fascia > 1 settimana). Differenze: **C_A_esp − C_A** (effetto della coverage, stesso modello), **C_A_esp − C** (effetto dei dati a pari coverage), **A − C_A_esp**; riferimenti A − C, A − C_A, C_A − C, le cui medie devono coincidere con `e15_risultati.json` entro 1e-12 (controllo bloccante; stesse estrazioni del ricampionamento, quindi stessi intervalli). Quota del divario dovuta alla coverage: (C_A − C_A_esp)/(C_A − C), con intervallo.

## Ingressi e congelamento

Ingressi: punti di controllo di C_A e celle di prova di E15 (impronte registrate per cella nel json), `e15_risultati.json` (impronta nel json), `e15_k_secondaria.json` tramite `_contesto_cella`. Statica: `OR3_STATICA` assente (= `espansiva`); `_contesto_cella` rifiuta ogni altra variante. Il json porta l'istante; il resoconto `protocol/e18quater/RISULTATI.md` è derivato dal json e ne cita l'impronta.

## Costo

Due valutazioni di un modello per cella (controllo e nuova), senza adattamenti: frazione della fase `valuta` di E15 (54 celle, 42 min di parete con 7 modelli e 4 adattamenti per cella, `results/evoluzione/e15_prova.log`).
