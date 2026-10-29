# Registro delle correzioni (Paper 1)

Registro consolidato delle correzioni fatte durante lo studio: alla pipeline (voci 1–16, 17a, 19–27) e
al manoscritto (17b, 18). **Dal 28/10/2026 questo file è l'originale**; `register_of_corrections.en.md`
ne è la traduzione inglese. Il paper richiama le voci per numero.

Colonna «Fonte»: il protocollo o il congelamento che riporta la correzione datata; per le voci senza
un file in questo repository, «tabella del supplemento fino a `manoscritto-20261015f`;
`NOTE_PER_GLI_AUTORI.md`» (la tabella del supplemento del manoscritto, presente fino al tag
`manoscritto-20261015f` e tolta in `manoscritto-20261015g`; le note per gli autori stanno nel
repository del manoscritto, non in questo).

Come sono state trovate: 1–16 da asserzioni, controlli preliminari o confronti di impronte; 17 leggendo
un congelamento contro il manoscritto; 19 e 20 dallo script di rigenerazione (`analysis/main.py`); 21
descrivendo la rete dai pesi dei checkpoint; 22 rigenerando su una seconda macchina; 23 generando una
tabella del supplementare dai file dei pesi di classe effettivamente caricati; 24 da un controllo di E4
durante l'esperimento di sensibilità; 25 rigenerando da zero; 26 leggendo il congelamento di E14 contro
le sue stesse tabelle; 27 nella seconda revisione esterna; nessuna ispezionando il codice fine a se
stesso. Le voci 17b e 18 sono errori del manoscritto, non della pipeline.

| # | Difetto | Correzione ed effetto misurato | Fonte |
|---|---|---|---|
| 1 | un lotto per epoca presentato come un'epoca | 35 aggiornamenti = 15 % di un passaggio; con un budget adeguato l'ordine dei modelli è cambiato | `evoluzione/RETTIFICA_BUDGET.md` |
| 2 | selezione del checkpoint su 32 istanti fissi di validazione (2 %) | selezione sull'intero insieme di validazione | `evoluzione/RETTIFICA_BUDGET.md` |
| 3 | un clamp che assegnava una classe ai bersagli mancanti | riguardava il 40 % dei bersagli di Londra; mascherati | `CONGELAMENTO_RACCORDO.md` |
| 4 | ramo statico e teste disallineati fra varianti (640 estrazioni in più) | artefatto canonico per impronta | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 5 | finestre costruite per indice attraverso i salti di calendario | orizzonte senza il significato dichiarato; 2,6 % delle origini escluse come non ammissibili | `CONGELAMENTO_E_F_PIPELINE_PRECEDENTE.md` |
| 6 | riga t₀ inclusa nell'adattamento | 77 origini invece di 78 | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 7 | descrittore addestrato su un'istantanea non causale di fine periodo | variante causale pre-registrata, non eseguita (paper, Limitations) | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 8 | popolazione di nodi 900/900/594 contro i 828/774/587 documentati | dichiarata | `evoluzione/RETTIFICA_POPOLAZIONE.md` |
| 9 | bracci dichiarati in sei punti; quattro dimenticati aggiungendo un braccio | tabella unica delle proprietà dei bracci, collaudo con 36 controlli | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 10 | R-orig e R-mon instradati nel ramo di adattamento | 216 esecuzioni, trovate dal tempo di calcolo, in quarantena con indice | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 11 | un riepilogo di fase sovrascritto da un lancio successivo | uscite scritte per lancio | `CONGELAMENTO_E3.md` |
| 12 | script di fattibilità che arrotondava le partizioni a 27 sensori invece di 26 | corretto prima del lancio | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 13 | un predittore a nove canali costruito qualunque fosse la sorgente | falliva su PEMS; città invariate | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 14 | un criterio post hoc non discriminante proposto in revisione dell'esperimento di copertura | corretto prima dell'uso | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 15 | un ramo di lettura del generatore delle metriche operative che scriveva «non distinguibile» per «sopra a qualche livello, mai sotto» | corretto prima del commit | `CONGELAMENTO_E8.md` |
| 16 | `np.trapz` assente nell'ambiente | trapezi espliciti | `CONGELAMENTO_E8.md` |
| 17a | generatore di E3-bis: «almeno 6×» divideva la mediana di R-orig(1 sett.) sulle nove celle delle tre città per il solo F′(1 sett.) misurato in isolamento (Melbourne) | tempi per contesto dalla sessione unica (`costi_tabella_sessione.json`); rapporto solo nella stessa città; congelamento di E3-bis rigenerato (impronta `174d8e2d1808516c`) | `CONGELAMENTO_E3bis.md` |
| 17b | in una bozza del manoscritto i tempi 36,8 s e 35,7 s erano attribuiti a F′(1 sett.) a Madrid e Londra; sono i tempi di gated(48 h) di E4 | manoscritto corretto con i tempi appaiati per città | `NOTE_PER_GLI_AUTORI.md` |
| 18 | una citazione in una bozza del manoscritto non corrispondeva al riferimento a cui rimandava | citazione tolta; il riferimento citato con il suo titolo | `NOTE_PER_GLI_AUTORI.md` |
| 19 | il conteggio delle riviste di E3 prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 rimisure isolate fatte per la tabella dei costi (117 invece di 108) | lancio definito dai 108 manifesti per braccio, elencati per impronta in `analisi_e3.json`; ogni cella conta solo l'esecuzione che ha prodotto la wCE registrata; rimisure etichettate a parte; congelamento rigenerato, non modificato a mano; numeri del paper invariati | `CONGELAMENTO_E3.md` |
| 20 | una frase del congelamento di E5 su E3-bis dipendeva da quali esperimenti esistevano al momento della generazione; trovata diversa rigenerando (numeri identici) | frase resa stabile nel tempo; congelamento rigenerato, non modificato a mano | `CONGELAMENTO_E5.md` |
| 21 | ramo statico alimentato con la copertura del sensore sull'intera serie, test compreso | effetto misurato da E14: confinato ai bracci senza un'identità appresa per il sensore, wCE dei bracci spostata di ≤ 0,007; l'unica lettura a tre episodi che cambia lo fa a favore del paper; le cinque dichiarazioni ristabilite da capo a fondo con ingressi causali da E15; codice causale per default dopo lo studio (`--statica=congelata` riproduce la campagna congelata) | `protocol/E14.md`, `CONGELAMENTO_E14.md`, `CONGELAMENTO_E14B.md`, `CONGELAMENTO_E15.md` |
| 22 | il controllo di identità dei dati nella verifica dell'appaiamento di E2 confrontava aggregati float32 ricalcolati con rtol 10⁻¹²; fallito fra architetture diverse (scarto massimo sull'elemento 4,9 × 10⁻⁹) | tolleranza portata a 10⁻⁷; trovato rigenerando su una seconda macchina | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 23 | la tabella descrittiva congelata delle frequenze di classe (E6, `frequenze_classi.json`) era calcolata da un insieme precedente di file dei pesi di classe (campagna per indice) e da 3 delle 6 partizioni di PEMS08, non dai file caricati dagli esperimenti | tabella ricostruita dai file effettivamente caricati, con impronte; nessun effetto sui risultati; cambiano tre limiti descrittivi (città: classe congestionata fino a 15,9 % invece di 15,7 %; Madrid 9,0–9,5 %; Londra 15,4–15,9 %) | `protocol/E6.md` (correzione datata) |
| 24 | `adatta_F` costruiva un proprio vettore statico invece di prendere quello della cella; con le varianti di E14 F era adattato con lo scalare congelato e valutato con quello della variante; nessun effetto sui numeri congelati (lì i due coincidevano) | rilevato dal controllo 3 di E4 durante lo stadio B (scarti 10⁻⁴–10⁻³); corretto (commit `8f9afbf`), F riadattato, E4 rieseguito | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 25 | l'orchestratore dello stadio B (`esegui_e14b.sh`) eseguiva la fase «origini» di E6 prima di E6a, di cui legge le predizioni; nessun effetto sui numeri; `main.py` non coinvolto | trovato rigenerando da zero; fase spostata dopo E6a | tabella del supplemento fino a `manoscritto-20261015f`; `NOTE_PER_GLI_AUTORI.md` |
| 26 | il generatore di E14-B confrontava l'intero record della scelta (τ, N) di PEMS, compresa la wCE di validazione che differisce di ~10⁻⁹ fra macchine, e marcava come «diverse» scelte (τ, N) identiche | solo documentazione, nessun effetto sui numeri; il generatore confronta (τ, N) e riporta a parte la differenza di wCE; congelamento rigenerato con correzione datata (commit `109aca5`, impronta `864b21c7796aefb2`) | `CONGELAMENTO_E14B.md` |
| 27 | in `esegui_e16.py` ogni braccio era valutato su tutte le origini dopo t₁; per F′(1 sett.) questo include la prima settimana, in cui l'embedding adattato usa dati fino a t₀ + 1 settimana, quindi le righe F′(1 sett.) delle tabelle di E16 sono su una finestra non causale per quel braccio; il controllo bloccante confrontava con l'aggregato congelato somma delle tre fasce e non poteva rilevarlo; la quota di calibrazione s di F₀ − C non è toccata | corretto da E18, parte C: righe F′(1 sett.) delle tabelle di E16 ricalcolate sulle origini più vecchie di una settimana per entrambi i bracci, parametri di calibrazione invariati; controllo bloccante sugli aggregati congelati superato (scarto relativo massimo 8,66 × 10⁻⁷, soglia 10⁻⁶) | `protocol/E18.md` §3, `CONGELAMENTO_E18.md` §1 |
