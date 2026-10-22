# Scheda dei fatti — revisione interna (richiesta del revisore, 20/10/2026)

Generata da `evoluzione/analisi/scheda_fatti.py` al commit `e10c579`, 2026-10-22 07:00 UTC. Sola lettura: nessun numero del paper cambia. I fatti di codice citano il frammento che li stabilisce (ritrovato nel file dallo script); i fatti di dati sono calcolati dai file di `results/evoluzione/`.

## 1. Il ricampionamento congiunto partizioni × semi × sensori

Procedura (`_boot`, evoluzione/esperimenti/esegui_e4.py:350; identica in E2 `analizza_e2.py`, E5, E6, E6-bis, E6a, E8, E8-bis, E14, stesse 4.000 repliche, seme fisso per esperimento):

- **Incrociato, non gerarchico.** A ogni replica si estraggono con reinserimento: le 3 partizioni (`ps`), i semi (`ss`, 12 nella campagna principale, 6 in E5/E6) e un vettore `nd` di K **posizioni** di sensore (K = numero di sensori nuovi per partizione, uguale in tutte le partizioni di una citta'); la statistica della replica e' la media, sulle |ps| × |ss| celle estratte, della differenza per cella calcolata sui sensori `nd`. Le tre estrazioni sono indipendenti e si combinano in prodotto (ogni partizione estratta con ogni seme estratto), non annidate.
- **Stessi indici per tutti i bracci**: `f_pair(z, nd)` calcola la differenza fra i due bracci della stessa cella sugli stessi sensori `nd`; il confronto e' appaiato per cella e per sensore.
- **Statistica per sensore**: wCE = media sugli orizzonti di (Σ_k A_k,h / Σ_k B_k,h) sui sensori selezionati (evoluzione/esperimenti/esegui_e4.py:259), con A e B gli aggregati per (sensore, orizzonte) salvati per cella; un sensore estratto due volte conta due volte (pesi interi del ricampionamento).
- **Sensori presenti in piu' partizioni**: le partizioni sono permutazioni indipendenti dei sensori (`_partizioni`, seme di partizione), quindi lo stesso sensore puo' essere «nuovo» in piu' partizioni. Il vettore `nd` e' di posizioni nella lista ordinata dei nuovi di ciascuna partizione: la posizione i indica sensori diversi in partizioni diverse. Nessun accoppiamento fra partizioni per identita' di sensore: l'unita' ricampionata e' (partizione, posizione), non il sensore fisico.
- **Intervallo**: percentili 2,5 e 97,5 delle repliche (evoluzione/esperimenti/esegui_e4.py:353); la stima puntuale e' la media delle differenze per cella su tutte le celle (non la mediana delle repliche). Rappresenta la variabilita' congiunta rispetto a (i) scelta della partizione dei sensori, (ii) inizializzazione, (iii) campione di sensori nuovi, a dato osservato fisso.
- **Dipendenza temporale**: le origini NON si ricampionano; gli aggregati A, B sommano su tutte le origini del perimetro (o della fascia d'eta'), quindi l'intervallo non copre la variabilita' temporale (nessun bootstrap a blocchi sul tempo). E' una scelta dichiarata nei protocolli.
- **Eccezioni**: in E3 (`analizza_e3.py`, evoluzione/analisi/analizza_e3.py:86) le posizioni `nd` sono estratte una volta per replica e applicate a tutte le partizioni come sopra; nei veterani (`analizza_veterani_e3.py`, evoluzione/analisi/analizza_veterani_e3.py:77) i nodi sono gli iniziali e `nd` e' estratto per partizione (K[p] diversi); E7 (ρ di Spearman) ricampiona le unita' (partizione, nodo) con 2.000 repliche; E8-bis ricampiona AUC e richiami con lo stesso schema congiunto (`_boot_curve`).

## 2. PEMS08: i sei insiemi di 26 nuovi sensori

Partizioni p0–p5 = permutazioni indipendenti dei 170 sensori (`_partizioni`, semi `SEME_PARTIZIONE_E6`), 15 % nuovi ciascuna: 156 occorrenze, **117 sensori distinti**. Molteplicita' (quante partizioni includono lo stesso sensore fra i nuovi): 83 sensori in 1 partizione, 30 sensori in 2 partizioni, 3 sensori in 3 partizioni, 1 sensori in 4 partizioni. Intersezioni a coppie (sensori in comune): p0∩p1=3, p0∩p2=2, p0∩p3=3, p0∩p4=3, p0∩p5=4, p1∩p2=3, p1∩p3=4, p1∩p4=3, p1∩p5=3, p2∩p3=3, p2∩p4=5, p2∩p5=1, p3∩p4=4, p3∩p5=2, p4∩p5=2. Quindi NON sono disgiunti: le 156 sono occorrenze, e il ricampionamento (§1) le tratta come unita' (partizione, posizione).

## 3. `adatta`: la rete e' in `eval()` durante l'adattamento

Si' (evoluzione/componente/adattamento.py:160): `m.eval()` prima del ciclo di aggiornamenti — BatchNorm usa le statistiche correnti e i buffer non si muovono; tutti i parametri sono congelati (`requires_grad_(False)`) tranne gli embedding adattabili del fornitore d'identita'; ottimizzatore Adam nuovo, solo su quei parametri, nessun decadimento, nessun arresto anticipato. `verifica_vincoli` (inserimento.py) controlla a valle che il punto E sia immutato. Vale per F, F′ (24 h, 48 h, 1 sett., k) in tutte le fasi.

## 4. Budget secondario k di E5

`../OR3/results/evoluzione/e5_k_secondaria.json` (impronta `0781e1d65ff764f2`, registrata `395d17a4f05462ea`): Madrid k = **50**, Londra k = **10**, Melbourne k = **100**. Il valore usato da E5 (`esegui_e5.py`, fase valuta, controllo dell'impronta per cella) e' quello del file: **la tabella D9 (100) e' giusta**. Il «200» e' un altro numero: il budget di adattamento di F′ scelto in validazione (`../OR3/results/evoluzione/selezione_F_griglia/configurazione_F.json`, impronta `18062d5ba9596a6f`): Madrid 50 aggiornamenti, passo 0.01, Londra 50 aggiornamenti, passo 0.01, Melbourne 200 aggiornamenti, passo 0.001. Dove il testo dice 200 per k va corretto in 100; dove parla del budget di F′ (p.es. il costo di 401 s di Melbourne) 200 e' giusto. Nel manoscritto (`../paper1/main.tex`) le occorrenze di «200» vicine a «k», «secondar» o «Melbourne»: 2
  - `…validation episode and frozen: Madrid (50, 0.01), London (50, 0.01), Melbourne (200, 0.001). Every origin needs the 12 preceding steps as in…`
  - `…--401\,s; the Melbourne figure of 401\,s reflects a validation-chosen budget of 200 updates against 50, on 90 new sensors against 135): we t…`

## 5. Londra, episodio 1: F₀′ − C vale +0,013 (E2) e +0,015 (E5/C3)

Stesse celle (partizioni 0–2), stesse origini del test ([1440] origini dopo t₁, [135] sensori nuovi), stessi punti di controllo (C della fase 3, F₀′ dal token di E′): le **medie per cella coincidono** dove le celle coincidono. Differenza: **i semi**. E2 usa i 12 semi dichiarati ([201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212]): media delle 36 celle = +0.01288 (congelamento_e2: +0.01288 [+0.0096, +0.0168]). E5 usa i 6 semi con identificativo piu' basso ([201, 202, 203, 204, 205, 206], `SEMI_E5`): media delle 18 celle ricalcolata qui dalle stesse predizioni di E2 = +0.01452; e5_risultati Londra/ep1/(a) = +0.01452 [+0.0103, +0.0191] (predizioni di E5, episodio 1, origini 1440). E4 (12 semi, stesso perimetro): +0.01288. I semi del ricampionamento differiscono (E2 20260930, E5 20261007) ma gli intervalli si sovrappongono ampiamente; la differenza fra +0,013 e +0,015 e' il sottoinsieme di semi, non una campagna diversa.

## 6. AUC delle curve richiamo–falsi allarmi (E8-bis)

- **Soglie**: 19 valori 0,05 … 0,95 a passo 0,05 (evoluzione/esperimenti/esegui_e8.py:45); per ogni soglia t la classe congestionata e' predetta se p(congestionata) ≥ t, altrimenti l'argmax fra verde e giallo (`predizione`).
- **Curva**: per ogni soglia, falsi allarmi FAR = FP/(FP+TN) e richiamo = TP/(TP+FN) della classe congestionata, dalle matrici di confusione SOMMATE su sensori e orizzonti del perimetro (`curva`).
- **AUC completa, non parziale**: trapezi sui 19 punti ordinati per FAR, con gli estremi (0, 0) e (1, 1) aggiunti (evoluzione/esperimenti/esegui_e8.py:550); nessuna interpolazione oltre i trapezi lineari fra punti consecutivi.
- **Richiamo a falsi allarmi fissati** (evoluzione/esperimenti/esegui_e8.py:532): interpolazione lineare (`np.interp`) della curva ai livelli FA = 0,5 %, 1 %, 2 %, 5 %, 10 %; `nan` se il livello e' fuori dall'intervallo dei FAR osservati.
- **Aggregazione e intervallo**: la curva e' dei conteggi sommati sulla cella; ΔAUC fra bracci per cella, ricampionamento congiunto come in §1 (`_boot_curve`, stessi `nd`), percentili 2,5–97,5; segno dell'intervallo come verdetto. Perimetri: intero e eta' > 1 settimana.

## 7. Macro-F1 dopo la soglia sulla classe rossa

Regola di assegnazione (evoluzione/esperimenti/esegui_e8.py:183): se p(rossa) ≥ t → rossa; altrimenti **argmax fra verde e gialla** sulle probabilita' non rinormalizzate (il confronto fra le due e' invariante alla rinormalizzazione). Macro-F1 = media delle F1 delle tre classi calcolate dalla matrice di confusione 3×3 (evoluzione/esperimenti/esegui_e8.py:197); le regole sono `prim` (soglia che massimizza F1 della rossa in validazione), `par` (stesso tasso di falsi allarmi di C alla sua soglia primaria) e `argmax`.
## 8. Date per episodio e contesto (indici della griglia a 15 min → istante)

Convenzioni: addestramento su [FINESTRA − 1, a_tr), selezione del checkpoint (V-full) su [a_tr, a_va); episodio: installazione t₀, acquisizione (t₀, t₁ = t₀ + 24 h], test (t₁, fine]; politica (τ, N) e k scelti sull'episodio di validazione (t₀ᵛ, t₁ᵛ, fino a FINE_VAL). Episodi 2 e 3 (E5): periodi ricavati da [0, t₀) con le quote 70/85 e 15/85 (`_partizioni(fine=t₀)`).

| contesto | ep. | addestramento | selezione ckpt | validazione politica (t₀ᵛ → t₁ᵛ … fine) | installazione t₀ | t₁ | fine test |
|---|---|---|---|---|---|---|---|
| Madrid | 1 | 2021-06-01 02:45 → 2021-10-25 05:30 | 2021-10-25 05:45 → 2021-12-01 13:30 | 2021-11-02 00:00 → 2021-11-03 00:00 … 2021-12-01 13:30 | 2021-12-01 13:45 (8887) | 2021-12-02 13:45 (8983) | 2021-12-31 22:00 (10456) |
| Madrid | 2 | 2021-06-01 02:45 → 2021-09-27 13:30 | 2021-09-27 13:45 → 2021-10-24 23:30 | — (τ, N, k dell'ep. 1) | 2021-10-24 23:45 (7295) | 2021-10-25 23:45 (7391) | 2021-12-01 13:45 (8887) |
| Madrid | 3 | 2021-06-01 02:45 → 2021-09-07 02:30 | 2021-09-07 02:45 → 2021-09-24 15:15 | — (τ, N, k dell'ep. 1) | 2021-09-24 15:30 (5726) | 2021-09-25 15:30 (5822) | 2021-10-24 23:45 (7295) |
| Londra | 1 | 2019-07-01 02:45 → 2019-11-24 22:30 | 2019-11-24 22:45 → 2020-01-01 10:00 | 2019-12-02 00:00 → 2019-12-03 00:00 … 2020-01-01 10:00 | 2020-01-01 10:15 (8966) | 2020-01-02 10:15 (9062) | 2020-01-31 22:00 (10549) |
| Londra | 2 | 2019-07-01 02:45 → 2019-10-27 13:45 | 2019-10-27 14:00 → 2019-11-23 23:30 | — (τ, N, k dell'ep. 1) | 2019-11-23 23:45 (7292) | 2019-11-24 23:45 (7388) | 2020-01-01 10:15 (8966) |
| Londra | 3 | 2019-07-01 02:45 → 2019-09-29 23:45 | 2019-10-07 00:00 → 2019-10-24 11:45 | — (τ, N, k dell'ep. 1) | 2019-10-24 12:00 (5709) | 2019-10-25 12:00 (5805) | 2019-11-23 23:45 (7292) |
| Melbourne | 1 | 2020-06-01 02:45 → 2020-10-24 12:30 | 2020-10-24 12:45 → 2020-11-30 17:15 | 2020-11-02 00:00 → 2020-11-03 00:00 … 2020-11-30 17:15 | 2020-11-30 17:30 (8806) | 2020-12-01 17:30 (8902) | 2020-12-30 22:00 (10360) |
| Melbourne | 2 | 2020-06-01 02:45 → 2020-09-27 00:45 | 2020-09-27 01:00 → 2020-10-24 08:00 | — (τ, N, k dell'ep. 1) | 2020-10-24 08:15 (7233) | 2020-10-25 08:15 (7329) | 2020-11-30 17:30 (8806) |
| Melbourne | 3 | 2020-06-01 02:45 → 2020-08-30 16:45 | 2020-08-30 17:00 → 2020-09-24 03:30 | — (τ, N, k dell'ep. 1) | 2020-09-24 03:45 (5679) | 2020-09-25 03:45 (5775) | 2020-10-24 08:15 (7233) |
| PEMS08 | 1 | 2016-07-01 02:45 → 2016-08-02 22:15 | 2016-08-02 22:30 → 2016-08-09 23:45 | 2016-08-02 22:30 → 2016-08-03 22:30 … 2016-08-09 23:45 | 2016-08-10 00:00 (3840) | 2016-08-11 00:00 (3936) | 2016-08-31 22:00 (5944) |
| PEMS04 | 1 | 2018-01-01 02:45 → 2018-02-11 05:30 | 2018-02-11 05:45 → 2018-02-20 01:30 | 2018-02-11 05:45 → 2018-02-12 05:45 … 2018-02-20 01:30 | 2018-02-20 01:45 (4807) | 2018-02-21 01:45 (4903) | 2018-02-28 22:00 (5656) |

Nota: la selezione del checkpoint usa i nodi iniziali sul periodo di selezione (`initial_network`); la validazione della politica (τ, N) e di k usa l'episodio di validazione con i nodi di validazione (E4 §scegli, E5 k-secondaria, E6/E6a scegli); PEMS04 ha calendario 70/15/15 della serie intera, PEMS08 il periodo [0, t₀) con le quote del principale.
