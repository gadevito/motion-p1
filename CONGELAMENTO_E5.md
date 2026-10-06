# Congelamento — E5, piu' episodi d'inserimento

**Congelato il 2026-10-06**, commit `668ca1cff33d`. Pre-registrazione `protocol/E5.md` (impronta `3dd706bcf3ddd899`), firmata al commit `cff0310c7c49fe36` prima del lancio (E3-bis compreso). **Ogni numero e' calcolato da `genera_congelamento_e5.py`** dai file di risultato; il verdetto e' derivato, non scritto.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| addestramenti | **324** marcatori (ep2/C 54, ep2/A 54, ep2/E1 54, ep3/C 54, ep3/A 54, ep3/E1 54); esito del lancio: 324 completati, 0 falliti, 50.0 ore di calendario con 8 processi — **non e' il costo seriale** |
| aggiornamento selezionato (episodi 2 e 3, dal registro) | u1374 × 1, u1603 × 9, u1832 × 29, u2061 × 91, u2290 × 194 |
| celle valutate | episodio 1 54, episodio 2 54, episodio 3 54; semi (201, 202, 203, 204, 205, 206) |
| controllo 3 (nodi nuovi fuori da E′, C, pesi, normalizzazione; dentro A) | verificato in 162 celle su 162 |
| controllo 6 (episodio 1 = celle di E4) | scarto relativo massimo 0.0e+00 su C, F₀′, F′(24 h/48 h/1 sett.) |
| (τ, N) | letti da `e4_scelta_gated.json`, impronta `81e47f64f3d63b3b` (= `81e47f64f3d63b3b`), mai riselezionati |
| k della secondaria | `e5_k_secondaria.json`, impronta `395d17a4f05462ea` (= `395d17a4f05462ea`, una sola nelle celle: ['395d17a4f05462ea']); k = Madrid 50, Londra 10, Melbourne 100 |
| ricampionamento | 4000 repliche, seme 20261007, partizioni × semi × nodi |

## 2. Calendario degli episodi (regola meccanica, verificata dall'esecutore)

| citta' | ep. | t₀ | data e ora | valutazione (origini amm.) | addestramento (origini amm.) | perdita |
|---|---|---|---|---|---|---|
| Madrid | 1 | 8887 | 2021-12-01 13:45 | 1426 | 7118 | 0.0% |
| Madrid | 2 | 7295 | 2021-10-24 23:45 | 1438 | 5844 | 17.9% |
| Madrid | 3 | 5726 | 2021-09-24 15:30 | 1426 | 4571 | 35.8% |
| Londra | 1 | 8966 | 2020-01-01 10:15 | 1440 | 7161 | 0.0% |
| Londra | 2 | 7292 | 2019-11-23 23:45 | 1520 | 5823 | 18.7% |
| Londra | 3 | 5709 | 2019-10-24 12:00 | 1440 | 4549 | 36.5% |
| Melbourne | 1 | 8806 | 2020-11-30 17:30 | 1411 | 7050 | 0.0% |
| Melbourne | 2 | 7233 | 2020-10-24 08:15 | 1411 | 5793 | 17.8% |
| Melbourne | 3 | 5679 | 2020-09-24 03:45 | 1411 | 4551 | 35.4% |

**Righe contro origini, contate dall'esecutore** (`e5_prepara.json`): 
- Madrid: 1569 righe del periodo di prova → 1464 origini nominali, 38 escluse per salto, 1426 ammissibili. Salti: righe 9407 (2021-12-06 → 2021-12-14, 19 origini); righe 10079 (2021-12-20 → 2021-12-28, 19 origini).
- Londra: 1583 righe del periodo di prova → 1478 origini nominali, 38 escluse per salto, 1440 ammissibili. Salti: righe 9404 (2020-01-05 → 2020-01-13, 19 origini); righe 10076 (2020-01-19 → 2020-01-27, 19 origini).
- Melbourne: 1554 righe del periodo di prova → 1449 origini nominali, 38 escluse per salto, 1411 ammissibili. Salti: righe 9407 (2020-12-06 → 2020-12-14, 19 origini); righe 10079 (2020-12-20 → 2020-12-28, 19 origini).

Le 38 origini escluse in ogni citta' sono **due salti di sette giorni** del calendario Traffic4cast, 19 origini ciascuno (12 di finestra + 8 di orizzonte − 1): un valore della sorgente, non una costante.

## 3. Scelte pre-registrate e loro base

### Sei semi (201–206): la semiampiezza non dipende dai semi

| citta' | confronto | 6 semi | 12 semi |
|---|---|---|---|
| Madrid | Fp_96-C | ±0.0090 | ±0.0093 |
| Madrid | Fp_672-C | ±0.0052 | ±0.0048 |
| Madrid | gated-F0p | ±0.0080 | ±0.0079 |
| Londra | Fp_96-C | ±0.0107 | ±0.0105 |
| Londra | Fp_672-C | ±0.0042 | ±0.0038 |
| Londra | gated-F0p | ±0.0065 | ±0.0063 |
| Melbourne | Fp_96-C | ±0.0092 | ±0.0094 |
| Melbourne | Fp_672-C | ±0.0069 | ±0.0069 |
| Melbourne | gated-F0p | ±0.0039 | ±0.0038 |

### k della secondaria (traiettoria sull'episodio di validazione esteso, mai dal test)

- Madrid: k = **50**; k0 0.9523, k5 0.9336, k10 0.9277, k25 0.9260, k50 0.9258
- Londra: k = **10**; k0 0.8804, k5 0.8639, k10 0.8589, k25 0.8615, k50 0.8631
- Melbourne: k = **100**; k0 0.8455, k5 0.8431, k10 0.8410, k25 0.8359, k50 0.8310, k100 0.8287, k200 0.8345

## 4. Le affermazioni principali per citta' × episodio

| citta' | aff. | episodio 1 | episodio 2 | episodio 3 | segni | stesso segno 3/3 | solo ep. 3 |
|---|---|---|---|---|---|---|---|
| Madrid | (a) F₀′ − C | +0.008 [+0.005, +0.011] | +0.004 [+0.002, +0.007] | +0.002 [-0.000, +0.005] | ++0 | no | 0 |
| Madrid | (b) gated − F₀′ | -0.029 [-0.037, -0.021] | -0.027 [-0.035, -0.019] | -0.008 [-0.018, +0.003] | --0 | no | 0 |
| Madrid | (c) F′(1 sett.) − C, eta' > 1 sett. | -0.031 [-0.036, -0.026] | -0.035 [-0.042, -0.030] | -0.036 [-0.043, -0.029] | --- | **si** | - |
| Madrid | (d) F′(24 h) − C | -0.011 [-0.021, -0.002] | -0.012 [-0.020, -0.004] | +0.011 [-0.004, +0.026] | --0 | no | 0 |
| Madrid | (e) F′(1 sett.) − A, eta' > 1 sett. | +0.008 [+0.004, +0.012] | +0.005 [+0.001, +0.008] | +0.003 [+0.000, +0.006] | +++ | **si** | + |
| Londra | (a) F₀′ − C | +0.015 [+0.010, +0.019] | +0.010 [+0.006, +0.015] | +0.011 [+0.007, +0.014] | +++ | **si** | + |
| Londra | (b) gated − F₀′ | -0.011 [-0.017, -0.004] | -0.018 [-0.024, -0.013] | -0.024 [-0.032, -0.016] | --- | **si** | - |
| Londra | (c) F′(1 sett.) − C, eta' > 1 sett. | -0.031 [-0.035, -0.026] | -0.024 [-0.029, -0.020] | -0.030 [-0.035, -0.026] | --- | **si** | - |
| Londra | (d) F′(24 h) − C | +0.032 [+0.021, +0.043] | +0.005 [-0.004, +0.015] | -0.007 [-0.014, +0.001] | +00 | no | 0 |
| Londra | (e) F′(1 sett.) − A, eta' > 1 sett. | +0.008 [+0.006, +0.012] | +0.009 [+0.005, +0.013] | +0.008 [+0.004, +0.012] | +++ | **si** | + |
| Melbourne | (a) F₀′ − C | +0.002 [-0.004, +0.008] | +0.006 [+0.001, +0.011] | +0.016 [+0.013, +0.020] | 0++ | no | + |
| Melbourne | (b) gated − F₀′ | -0.024 [-0.028, -0.020] | +0.001 [-0.003, +0.004] | -0.033 [-0.039, -0.029] | -0- | no | - |
| Melbourne | (c) F′(1 sett.) − C, eta' > 1 sett. | -0.036 [-0.044, -0.029] | -0.025 [-0.032, -0.018] | -0.038 [-0.045, -0.033] | --- | **si** | - |
| Melbourne | (d) F′(24 h) − C | -0.020 [-0.029, -0.010] | +0.023 [+0.008, +0.039] | -0.022 [-0.029, -0.013] | -+- | no | - |
| Melbourne | (e) F′(1 sett.) − A, eta' > 1 sett. | -0.002 [-0.012, +0.007] | +0.010 [+0.001, +0.020] | +0.015 [+0.010, +0.021] | 0++ | no | + |

Segno dell'intervallo: − (sotto lo zero), + (sopra), 0 (lo zero dentro). **7 affermazioni su 15 hanno lo stesso segno in tutti e tre gli episodi**; le altre vanno riportate nel paper come dipendenti dall'episodio, con la figura `figure/episodi_e5.png`.
- **Il criterio primario di E4, esteso ai nove episodi**: gated − F₀′ ha estremo superiore massimo +0.004 (≤ +0,005: la politica non peggiora mai il modello che la ospita, su nessuna data); lo migliora con intervallo sotto lo zero in 7/9.
- (a) F₀′ − C: concorda in 1/3 citta' (Londra); solo episodio 3: Madrid 0, Londra +, Melbourne +.
- (b) gated − F₀′: concorda in 1/3 citta' (Londra); solo episodio 3: Madrid 0, Londra -, Melbourne -.
- (c) F′(1 sett.) − C, eta' > 1 sett.: concorda in 3/3 citta' (Madrid, Londra, Melbourne); solo episodio 3: Madrid -, Londra -, Melbourne -.
- (d) F′(24 h) − C: concorda in 0/3 citta'; solo episodio 3: Madrid 0, Londra 0, Melbourne -.
- (e) F′(1 sett.) − A, eta' > 1 sett.: concorda in 2/3 citta' (Madrid, Londra); solo episodio 3: Madrid +, Londra +, Melbourne +.

## 5. Altri confronti (secondari)

| citta' | confronto | episodio 1 | episodio 2 | episodio 3 |
|---|---|---|---|---|
| Madrid | gated − C | -0.021 [-0.027, -0.014] | -0.023 [-0.030, -0.016] | -0.005 [-0.014, +0.003] |
| Madrid | A − C | -0.039 [-0.044, -0.034] | -0.041 [-0.047, -0.035] | -0.036 [-0.044, -0.028] |
| Madrid | F′(1 sett.) − C, intero periodo | -0.037 [-0.043, -0.032] | -0.039 [-0.046, -0.034] | -0.041 [-0.050, -0.034] |
| Madrid | F′(24 h, k) − C [secondaria] | -0.011 [-0.020, -0.002] | -0.012 [-0.020, -0.004] | +0.011 [-0.004, +0.026] |
| Madrid | F′(24 h, k) − F′(24 h) [secondaria] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] | +0.000 [+0.000, +0.000] |
| Londra | gated − C | +0.004 [-0.001, +0.009] | -0.008 [-0.012, -0.004] | -0.013 [-0.018, -0.007] |
| Londra | A − C | -0.034 [-0.039, -0.030] | -0.032 [-0.037, -0.028] | -0.040 [-0.045, -0.036] |
| Londra | F′(1 sett.) − C, intero periodo | -0.037 [-0.041, -0.033] | -0.034 [-0.038, -0.031] | -0.037 [-0.041, -0.033] |
| Londra | F′(24 h, k) − C [secondaria] | -0.002 [-0.007, +0.002] | -0.009 [-0.014, -0.005] | -0.010 [-0.014, -0.005] |
| Londra | F′(24 h, k) − F′(24 h) [secondaria] | -0.034 [-0.044, -0.025] | -0.015 [-0.022, -0.008] | -0.003 [-0.009, +0.002] |
| Melbourne | gated − C | -0.021 [-0.027, -0.016] | +0.007 [+0.003, +0.011] | -0.017 [-0.021, -0.013] |
| Melbourne | A − C | -0.039 [-0.050, -0.028] | -0.041 [-0.051, -0.029] | -0.054 [-0.064, -0.046] |
| Melbourne | F′(1 sett.) − C, intero periodo | -0.045 [-0.053, -0.039] | -0.034 [-0.041, -0.029] | -0.043 [-0.049, -0.038] |
| Melbourne | F′(24 h, k) − C [secondaria] | -0.020 [-0.027, -0.013] | +0.002 [-0.006, +0.011] | -0.016 [-0.021, -0.011] |
| Melbourne | F′(24 h, k) − F′(24 h) [secondaria] | -0.001 [-0.005, +0.003] | -0.021 [-0.028, -0.013] | +0.006 [+0.002, +0.010] |

La secondaria non entra in nessuna affermazione principale (pre-registrata come tale). Madrid: k = 50 coincide con la configurazione congelata, quindi F′(24 h, k) ≡ F′(24 h) per costruzione; Londra: k = 10; F′(24 h, k) − F′(24 h) = -0.034, -0.015, -0.003 negli episodi 1-3; F′(24 h, k) − C = -0.002, -0.009, -0.010; Melbourne: k = 100; F′(24 h, k) − F′(24 h) = -0.001, -0.021, +0.006 negli episodi 1-3; F′(24 h, k) − C = -0.020, +0.002, -0.016.

## 6. N al lavoro: nodi sotto soglia per episodio

| citta' | N | episodio 1 | episodio 2 | episodio 3 |
|---|---|---|---|---|
| Madrid | 77 | 0.0 (max 0) su 135 | 0.0 (max 0) su 135 | 0.0 (max 0) su 135 |
| Londra | 154 | 99.0 (max 101) su 135 | 69.7 (max 77) su 135 | 36.3 (max 38) su 135 |
| Melbourne | 154 | 0.0 (max 0) su 90 | 68.0 (max 72) su 90 | 0.7 (max 1) su 90 |

N e' **entrato in gioco** in: Londra ep. 1 (99 nodi su 135 tenuti su F₀′), Londra ep. 2 (70 nodi su 135 tenuti su F₀′), Londra ep. 3 (36 nodi su 135 tenuti su F₀′), Melbourne ep. 2 (68 nodi su 90 tenuti su F₀′), Melbourne ep. 3 (1 nodi su 90 tenuti su F₀′). In validazione (E4) era inerte; sul test no. Dove molti nodi restano su F₀′, gated − F₀′ si avvicina a zero per costruzione: Londra ep. 1 gated − F₀′ -0.011 contro F′(1 sett.) − C -0.031; Londra ep. 2 gated − F₀′ -0.018 contro F′(1 sett.) − C -0.024; Melbourne ep. 2 gated − F₀′ +0.001 contro F′(1 sett.) − C -0.025. La soglia, scelta dallo spareggio, ha trattenuto adattamenti che avrebbero pagato: va detto nel paper.

## 7. F′(1 settimana) − A sull'episodio principale (numero richiesto, calcolato prima di E5)

- Madrid: +0.007 [+0.004, +0.010]; A − C -0.039; quota del divario recuperata 82%.
- Londra: +0.009 [+0.006, +0.012]; A − C -0.039; quota del divario recuperata 76%.
- Melbourne: -0.003 [-0.012, +0.006] (zero dentro); A − C -0.034; quota del divario recuperata 108%.

## 8. Dichiarazioni

- **Sei semi invece di otto**: deviazione dalla lettera del §9 confermata dal revisore; la semiampiezza cambia di ±0,0003 fra 12 e 6 semi (sezione 3).
- **Costo del protocollo corretto prima del lancio**: 324 addestramenti, non 108 (le tre citta' non erano moltiplicate); il lancio e' durato 50.0 ore con 8 processi.
- **Limitazione 7**: l'episodio di validazione di E4 cade dentro il periodo di valutazione dell'episodio 2 (nodi diversi); per questo (b) ed (e) sono riportate anche per il solo episodio 3.
- Nei periodi di valutazione degli episodi 2 la lunghezza differisce dove un salto della griglia impedisce l'uguaglianza esatta (Madrid 1438, Londra 1520 contro 1426 e 1440): dichiarato, non corretto.
- `_partizioni` accetta `fine_periodo` e la finestra del descrittore si verifica solo per chi lo usa: collaudi 8/8 (scarto 0), 25/25, 24/24, 19/19 dopo la modifica.
- Il numero di repliche del ricampionamento e' `esegui_e4.B_BOOT`, usato da `_boot`; una costante locale omonima nei moduli di E5 e' stata rimossa perche' non comandava nulla (stesso valore).
- **E3-bis**: **non eseguito** prima di questo congelamento: nel paper il confronto dei costi fra R-orig (24 h di dati) e F′ (1 settimana) e' dichiarato **a dati asimmetrici**.

## 9. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/addestramento.py` | `b549d8a90bdeffe8` |
| `evoluzione/esperimenti/esegui_e5.py` | `f08dd758210319e2` |
| `evoluzione/esperimenti/preparazione_e5.py` | `324044aefb327bab` |
| `evoluzione/analisi/settimana_vs_A_e5.py` | `ef2ceb4812f93353` |
| `evoluzione/analisi/analizza_e5.py` | `2206c2dff622bef0` |
| `protocol/E5.md` | `3dd706bcf3ddd899` |

**Nessun parametro scelto dopo aver visto i risultati**: t₀, semi, (τ, N), k della secondaria e configurazione di F sono nella pre-registrazione firmata o in file con impronta scritti prima del test.
