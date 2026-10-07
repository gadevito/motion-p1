# Congelamento — E3-bis, riaddestramento leale con una settimana di dati

**Congelato il 2026-10-07**, commit `45caa7ac822d`. Pre-registrato in `protocol/E5.md` (sezione E3-bis; impronta `3dd706bcf3ddd899`), firmato al commit `cff0310c7c49fe36` prima del lancio. **Ogni numero e' calcolato da `genera_congelamento_e3bis.py`** dai file di risultato.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| braccio | **R-orig** con acquisizione (t₀, t₀ + 672] (una settimana): campionamento uniforme per origine, budget 2.290, selezione sulla rete iniziale, architettura di A; `esegui_inserimento.py --acquisizione-passi 672` |
| esecuzioni | 108 completate, 0 fallite, 108 marcatori; 15.5 ore di calendario con 8 processi — **non e' il costo seriale** |
| ricostruzione delle predizioni | 108 esecuzioni, 0 anomalie, scarto massimo 3.4e-09 |
| perimetro | le origini dopo t₁ = t₀ + 672, cioe' **le origini comuni di E4** (eta' > 1 settimana): Madrid 869, Londra 883, Melbourne 854; verificato uguale, cella per cella, alla terza fascia di E4 |
| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo Madrid 0.0e+00, Londra 0.0e+00, Melbourne 0.0e+00 |
| ricampionamento | 4000 repliche, seme 20261009, partizioni × semi × nodi |

## 2. Confronti sulle origini comuni

| citta' | R-orig(1 sett.) − F′(1 sett.) | zero dentro | equivalenti ±3 % | R-orig(1 sett.) − C | R-orig(1 sett.) − A | R-orig(1 sett.) − R-orig(24 h) |
|---|---|---|---|---|---|---|
| Madrid | -0.003 [-0.006, -0.001] | no | si (±0.029) | -0.035 [-0.040, -0.030] | +0.004 [+0.001, +0.006] | -0.025 [-0.033, -0.019] |
| Londra | -0.002 [-0.005, +0.000] | si | si (±0.027) | -0.033 [-0.038, -0.028] | +0.007 [+0.004, +0.010] | -0.092 [-0.111, -0.077] |
| Melbourne | -0.013 [-0.020, -0.007] | no | si (±0.024) | -0.050 [-0.062, -0.038] | -0.016 [-0.026, -0.006] | -0.068 [-0.094, -0.047] |

Con gli stessi dati (una settimana), il riaddestramento leale e' **equivalente all'adattamento entro ±3 % in 3 citta' su 3**; include lo zero in 1/3; e' peggiore con intervallo sopra lo zero in 0/3 e migliore in 2/3. Dove e' migliore, lo e' di: Madrid -0.003, Melbourne -0.013.

**R-orig(1 sett.) − R-orig(24 h) e' sotto lo zero in 3 citta' su 3** (Madrid -0.025, Londra -0.092, Melbourne -0.068): anche per il riaddestramento la finestra di 24 ore era il problema, non il metodo — la stessa lezione di E4 letta sull'altro braccio.

Per riferimento, sulle stesse origini: Madrid F′(1 sett.) − C -0.032, A − C -0.039; Londra F′(1 sett.) − C -0.030, A − C -0.039; Melbourne F′(1 sett.) − C -0.036, A − C -0.034.

## 3. Costi — campione isolato, un processo, **a dati simmetrici**

| configurazione | calcolo all'inserimento | attesa dati | rimisure che riproducono la concorrente |
|---|---|---|---|
| R-orig(1 sett.) | **2268 s** | 168 h | 9/9 |
| F′(1 sett.) Melbourne (da costi_e4) | 406 s | 168 h | — |
| F′(24 h) (da costi_e4) | 16 s | 24 h | — |

Rapporto di calcolo a parita' di dati: R-orig(1 sett.) / F′(1 sett.) = **almeno 6×**: il denominatore e' l'unico F′(1 sett.) misurato in isolamento (Melbourne, 406 s, con la configurazione F piu' costosa, 200 aggiornamenti); a Madrid e Londra F ha 50 aggiornamenti e il rapporto sarebbe maggiore. Il confronto dei costi del paper e' ora a dati simmetrici: il riaddestramento compra pochi millesimi a diverse volte il costo, non nulla a cento.

## 4. Dichiarazioni

- Un solo parametro aggiunto agli esecutori di E3 (`--acquisizione-passi`), con il valore predefinito identico al comportamento precedente; `prova_inserimento` 19/19 e `collauda_bracci` 37/37 dopo la modifica.
- Le fasce d'eta' della valutazione restano quelle di E3; con t₁ = t₀ + 672 tutte le origini valutate cadono nella terza.

## 5. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_inserimento.py` | `3df759803c95fe49` |
| `evoluzione/esperimenti/ricostruisci_predizioni.py` | `12f5a31f2521a5fa` |
| `evoluzione/analisi/analizza_e3bis.py` | `c4d791c24eedded9` |
| `protocol/E5.md` | `3dd706bcf3ddd899` |
