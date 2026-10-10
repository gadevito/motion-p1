# Congelamento — E3, riaddestramento leale

**Congelato il 2026-10-10**, commit `33cafd6e2914`. Pre-registrazione `protocol/E3.md` (impronta `245085de8a909ca8`), firmata al commit `4bafa5ef0491a4b7` prima del primo run. **Ogni numero e' calcolato da `genera_congelamento_e3.py`** dai file di risultato; il verdetto e' derivato, non scritto.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| bracci nuovi | **R-orig** (uniforme per origine, selezione sulla rete iniziale) e **R-mon** (come R-orig, selezione rete iniziale + nodi nuovi sulle ultime 6 h, media pesata per celle); budget 2.290, architettura di A |
| esecuzioni | **216** completate, 0 fallite; marcatori R-orig 108, R-mon 108 |
| calendario | 33.0 ore, 8 processi; somma dei tempi di parete 261 ore — **non e' il costo seriale** |
| campione isolato | 9 + 9 celle rimisurate a un processo, ciascuna con wCE identica alla concorrente |
| predizioni per cella | ricostruite dai punti di controllo, tolleranza 1e-6: R 108 esecuzioni, 0 anomalie, scarto max 9.8e-09, R-orig 108 esecuzioni, 0 anomalie, scarto max 4.5e-09, R-mon 108 esecuzioni, 0 anomalie, scarto max 4.5e-09 |

## 2. Controlli obbligatori

### Conteggio delle riviste per origine (mediana sulle esecuzioni)

| braccio | esecuzioni | riviste/origine iniziali | nuovi | rapporto | quota estrazioni ai nuovi |
|---|---|---|---|---|---|
| R | 108 | 9.38 | 807.93 | **92.767** | 17.648% |
| R-orig | 108 | 11.32 | 11.29 | **1.000** | 0.231% |
| R-mon | 108 | 11.32 | 11.29 | **1.000** | 0.231% |

Per R-orig il rapporto atteso e' 1: **verificato** (1.000). I nodi nuovi ricevono lo 0.23% delle estrazioni: pesano quanto la loro storia.

### La rete esistente prima e dopo (nodi iniziali, periodo di prova)

| | R-orig − C | R-orig − E | R − C | R-mon − R-orig |
|---|---|---|---|---|
| Madrid | -0.040 [-0.042, -0.038] | -0.003 [-0.004, -0.002] | -0.029 [-0.031, -0.026] | +0.000 [+0.000, +0.000] (zero) |
| Londra | -0.037 [-0.039, -0.035] | -0.004 [-0.005, -0.003] | -0.030 [-0.032, -0.028] | +0.000 [+0.000, +0.000] (zero) |
| Melbourne | -0.033 [-0.037, -0.028] | -0.001 [-0.003, +0.000] (zero) | -0.016 [-0.021, -0.011] | +0.000 [+0.000, +0.000] (zero) |

**Costo della politica**: nessuno — R-orig non peggiora la rete esistente in alcuna citta'.

### Tabella dei costi (campione isolato, un processo)

| braccio | n | addestramento | inserimento | attesa dati | disponibile |
|---|---|---|---|---|---|
| C | 9 | 41.9 min | 0.0 s | 0 h | 0.0 h |
| P | 9 | 42.0 min | 0.0 s | 24 h | 24.0 h |
| A | 9 | 49.9 min | 0.0 s | 0 h | 0.0 h |
| R | 9 | 0.0 min | 2320.5 s | 24 h | 24.6 h |
| R-orig | 9 | 0.0 min | 2206.1 s | 24 h | 24.6 h |
| R-mon | 9 | 0.0 min | 2232.8 s | 24 h | 24.6 h |
| F | 9 | 0.0 min | 15.6 s | 24 h | 24.0 h |

R-orig costa **36.8 min** all'inserimento contro 15.6 s di F: **142×**.

## 3. I confronti pre-registrati (nodi nuovi, periodo di prova)

Celle (seme, partizione, nodo) appaiate; IC 95 % con ricampionamento congiunto di partizioni, semi e nodi, 4000 repliche, seme 20261002. Negativo = meglio del secondo termine.

| | R-orig − C (principale) | R-orig − R | R-mon − R-orig | R-mon − C |
|---|---|---|---|---|
| Madrid (12×3×135) | **-0.014** [-0.023, -0.004] | **-0.111** [-0.177, -0.051] | **+0.000** [-0.000, +0.000] (zero) | **-0.014** [-0.023, -0.004] |
| Londra (12×3×135) | **+0.049** [+0.034, +0.067] | **-0.085** [-0.124, -0.052] | **+0.000** [+0.000, +0.000] (zero) | **+0.049** [+0.034, +0.067] |
| Melbourne (12×3×90) | **+0.011** [-0.011, +0.035] (zero) | **-0.138** [-0.205, -0.083] | **+0.000** [+0.000, +0.000] (zero) | **+0.011** [-0.011, +0.037] (zero) |

## 4. Verdetto sul criterio pre-registrato

> **R-orig − C con intervallo che esclude lo zero: negativo = il riaddestramento leale paga; positivo = anche leale non paga a questo budget.**

- Madrid: **paga**
- Londra: **non paga**
- Melbourne: **non conclusivo**

**Esito eterogeneo per citta'**: paga in 1, non paga in 1, non conclusivo in 1. Il criterio non prevede un'aggregazione fra citta' e non la si introduce dopo. **R-orig − R** e' negativo con intervallo che esclude lo zero in tutte e tre: quasi tutto il peggioramento di R era il campionamento per nodo.

## 5. R-mon: nullo per costruzione, e la riselezione a peso uguale

R-mon coincide con R-orig in 3 citta' su 3 (media |Δ| < 1e-4): con la media pesata per numero di celle, dichiarata nel protocollo, i nodi nuovi pesano circa lo 0,3 % della selezione. **La sorveglianza con quel peso e' nulla per costruzione**; si riporta in una frase.

**Analisi aggiunta il 2/10, non pre-registrata, secondaria.** Dalle curve, la regola a peso uguale (0,5 rete iniziale + 0,5 nodi nuovi) avrebbe scelto un punto diverso in **34 celle su 108**. Quelle celle sono state riaddestrate salvando tutti i punti (il punto migliore riproduce la campagna a bit) e il punto a peso uguale valutato sul test:

| | R-mon-eq − R-mon | R-mon-eq − R-orig | R-mon-eq − C |
|---|---|---|---|
| Madrid | -0.0002 [-0.0009, +0.0002] (zero) | -0.0002 [-0.0009, +0.0002] (zero) | -0.0142 [-0.0233, -0.0044] |
| Londra | +0.0012 [+0.0000, +0.0029] (zero) | +0.0012 [+0.0000, +0.0028] (zero) | +0.0506 [+0.0354, +0.0679] |
| Melbourne | +0.0046 [+0.0009, +0.0095] | +0.0046 [+0.0010, +0.0095] | +0.0153 [-0.0068, +0.0407] (zero) |

Dare peso ai nodi nuovi nella selezione **non li migliora in prova** e li peggiora a Melbourne. Le 6 ore usate per la selezione appartengono al corpus di addestramento di R: premiarle sceglie punti piu' tardi, piu' adattati al proprio training.

## 6. R-orig e F: stesso punto d'arrivo?

Due letture, entrambe del protocollo (§12): una **differenza** si afferma con l'intervallo che esclude lo zero; un'**equivalenza** con il margine convenzionale ±3 % relativo a C (TOST; qui, in modo conservativo, l'intervallo al 95 % interamente dentro il margine).

| | F − C | R-orig − F | esclude lo zero | margine ±3 % | equivalenti |
|---|---|---|---|---|---|
| Madrid | -0.011 [-0.020, -0.001] | -0.003 [-0.005, -0.002] | si | ±0.029 | si |
| Londra | +0.040 [+0.028, +0.052] | +0.010 [+0.003, +0.018] | si | ±0.027 | si |
| Melbourne | -0.011 [-0.024, +0.003] | +0.022 [+0.006, +0.039] | si | ±0.024 | no |

R-orig differisce da F con intervallo che esclude lo zero in 3 citta' su 3 — di pochi millesimi, in favore di R-orig a Madrid e di F altrove — ed e' **equivalente a F entro il margine dichiarato in 2 citta' su 3** (Madrid, Londra). Il riaddestramento leale compra una differenza di quell'ordine a 142 volte il tempo dell'adattamento.

## 7. Dichiarazioni

- **Primo lancio non valido**, in quarantena con indice (`_quarantena_e3_falso_20260930`, 649 file): primo lancio di E3: R-orig e R-mon instradati nel ramo di F da `esegui_inserimento._lavora` (ADDESTRANO derivato dai soli cinque bracci della fase 3). Adattamenti di F con nome sbagliato, un minuto l'uno. Corretto: esegui_inserimento.esecutore(), dalla tabella unica.
- **Perso**: esito_concorrente.json della fase 3, sovrascritto; numeri in CONGELAMENTO_E_F_GRIGLIA.md e nei manifesti.
- Il tempo di parete atteso per braccio e' ora un assert dell'orchestratore (protocollo §13).
- **Correzione del 2026-10-10 (difetto 19 del registro)**: il conteggio delle riviste prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 rimisure isolate di R-orig e R-mon fatte per la tabella dei costi (117 invece di 108). Ora il lancio di E3 e' definito dai 108 manifesti per braccio di `inserimento_griglia/`, elencati per impronta in `analisi_e3.json` (`riviste/<braccio>/lancio`), e di ogni cella conta la sola esecuzione che ha prodotto la wCE registrata; le rimisure future hanno etichetta propria nel registro (`…/rimisura`). Documento rigenerato, non modificato a mano.

## 8. Impronte

| file | impronta |
|---|---|
| `evoluzione/componente/bracci.py` | `d803e43387c5c6a4` |
| `evoluzione/componente/campionamento.py` | `d45b2980a89a570f` |
| `evoluzione/esperimenti/addestramento.py` | `f5d69a789aadd479` |
| `evoluzione/esperimenti/inserimento.py` | `bc1d6ecd562b0888` |
| `evoluzione/esperimenti/esegui_inserimento.py` | `95349fe3b6f6356f` |
| `evoluzione/esperimenti/ricostruisci_predizioni.py` | `12f5a31f2521a5fa` |
| `evoluzione/esperimenti/veterani_e3.py` | `5fee87edbc851cde` |
| `evoluzione/esperimenti/riselezione_rmon_test.py` | `a8b19db9c3d2fc07` |
| `evoluzione/analisi/analizza_e3.py` | `a591fde2f22d251f` |
| `evoluzione/analisi/analizza_veterani_e3.py` | `d51ff7c1953d9fc2` |
| `evoluzione/analisi/costi_e3.py` | `c71f3f1ca388a3cb` |
| `evoluzione/analisi/riselezione_rmon.py` | `d0552d186bccad66` |
| `protocol/E3.md` | `245085de8a909ca8` |

**Nessun parametro scelto dopo aver visto i risultati**: budget, campionamento e finestra di selezione sono nella pre-registrazione firmata; la riselezione a peso uguale e' dichiarata come analisi aggiunta e secondaria.
