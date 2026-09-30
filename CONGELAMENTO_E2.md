# Congelamento — E2, costo di trasferimento con token ignoto

**Congelato il 2026-09-30**, commit `c7b42da179e9`. Pre-registrazione `protocol/E2.md` (impronta `14a94b8a2bebc7e5`). **Ogni numero di questo documento e' calcolato da `genera_congelamento_e2.py`** a partire dai file di risultato; il verdetto sul criterio e' derivato, non scritto.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| braccio addestrato | **E1** = E con token ignoto appreso e identity dropout **ρ = 0.15**, dichiarato prima del lancio (108 manifesti concordi) |
| punti E1 | **108** su 108 attesi, marcatori `.fatto`; cartella `E1_inserimento_griglia` |
| protocollo | `griglia_E1`: 2.290 aggiornamenti, undici punti, selezione su V-full della rete iniziale, griglia temporale reale |
| parallelismo | 8 processi × 1 filo, backend CPU |
| ore di calendario | 16.4 |
| somma dei tempi di parete | 127.2 ore — **non e' il costo seriale**: le esecuzioni erano concorrenti |
| bracci di valutazione | F₀′ (token, nessun aggiornamento), F′ (dal token, adattato sulle 24 h con la configurazione F congelata), F₀-mean′ (media degli iniziali, controllo); 324 valutazioni |

## 2. Controlli obbligatori

| controllo | esito |
|---|---|
| token effettivamente usato | norma del token a **1.20×** la norma mediana di un embedding (min 0.50, max 1.89 su 108 punti); distanza dall'embedding medio mediana 0.563, minima 0.241: **non e' una copia della media** |
| veterani (E1 contro E sui nodi iniziali) | **0** celle su 108 oltre l'1% relativo; scarto mediano +0.03%, massimo +0.89% — **il token non danneggia la rete esistente** |
| appaiamento dei confronti | 108 celle, 6 ricalcoli cella per cella, **0 anomalie** |
| controllo F₀-mean′ | eseguito, 3 citta' |

## 3. I confronti pre-registrati

Differenze di wCE, appaiate per cella (seme, partizione, nodo); intervallo al 95% con ricampionamento congiunto di partizioni, semi e nodi, 4000 repliche, seme 20260930. Negativo = meglio del secondo termine.

| | F₀′ − C | F₀′ − F₀ | F′ − C | F₀′ − F₀-mean′ | F′ − F |
|---|---|---|---|---|---|
| Madrid (12×3×135) | **+0.008** [+0.006, +0.011] | **-0.065** [-0.080, -0.051] | **-0.011** [-0.020, -0.002] | **-0.035** [-0.044, -0.026] | **-0.001** [-0.003, +0.002] (zero) |
| Londra (12×3×135) | **+0.013** [+0.010, +0.017] | **-0.037** [-0.049, -0.026] | **+0.034** [+0.024, +0.045] | **-0.021** [-0.030, -0.012] | **-0.006** [-0.011, -0.001] |
| Melbourne (12×3×90) | **+0.001** [-0.005, +0.007] (zero) | **-0.077** [-0.099, -0.054] | **-0.019** [-0.029, -0.009] | **-0.037** [-0.051, -0.024] | **-0.008** [-0.016, +0.000] (zero) |

### Riduzione del costo di trasferimento

| | F₀ − C | F₀′ − C | riduzione |
|---|---|---|---|
| Madrid | +0.073 | +0.008 | 89% |
| Londra | +0.050 | +0.013 | 74% |
| Melbourne | +0.078 | +0.001 | 98% |

(F₀ − C e' ricavato per differenza dai due confronti sopra: stesse celle.)

## 4. Verdetto sul criterio pre-registrato

> **Successo = (1) F₀′ − C con intervallo che include lo zero o negativo in 3 citta' su 3, e (3) F′ − C negativo con intervallo che esclude lo zero in almeno 2.**

- condizione (1): soddisfatta in **1 citta' su 3** (serviva 3/3)
- condizione (3): soddisfatta in **2 citta' su 3** (servivano 2/3)

**Criterio NON soddisfatto.** Si riportano gli effetti circoscritti, senza riclassificare i confronti secondari come principali.

## 5. Che cosa si riporta

- **Madrid**: il token porta il nodo nuovo a +0.008 da C [+0.006, +0.011]; dentro lo stesso modello il token batte la media di -0.035 [-0.044, -0.026]; l'adattamento dal token arriva dove arrivava dalla media: F′ − F = -0.001 [-0.003, +0.002] (zero).
- **Londra**: il token porta il nodo nuovo a +0.013 da C [+0.010, +0.017]; dentro lo stesso modello il token batte la media di -0.021 [-0.030, -0.012]; l'adattamento dal token arriva dove arrivava dalla media: F′ − F = -0.006 [-0.011, -0.001].
- **Melbourne**: il token porta il nodo nuovo a +0.001 da C [-0.005, +0.007]; dentro lo stesso modello il token batte la media di -0.037 [-0.051, -0.024]; l'adattamento dal token arriva dove arrivava dalla media: F′ − F = -0.008 [-0.016, +0.000] (zero).

Il costo di trasferimento si riduce ma non si azzera; l'adattamento e' indifferente al punto di partenza; i veterani non peggiorano. **Il confronto secondario F₀′ − F₀-mean′ resta secondario.**

## 6. Gli altri due controlli della pre-registrazione

### Sensibilita' a ρ (figura, non criterio)

Madrid p0, semi [201, 202, 203, 204]; ρ = 0.15 dalla campagna, gli altri addestrati apposta. Intervalli a ricampionamento di semi e nodi su una sola partizione: **non confrontabili** con quelli a tre livelli della sezione 3. Figura: `figure/sensibilita_rho_e2.png`.

| ρ | F₀′ − C | F′ − C | token / mediana embedding (min–max sui semi) | veterani, scarto massimo |
|---|---|---|---|---|
| 0.05 | +0.0329 [+0.0247, +0.0420] | -0.0219 [-0.0281, -0.0158] | 0.38–1.13 | -0.01% |
| 0.15 | +0.0097 [+0.0062, +0.0136] | -0.0210 [-0.0276, -0.0145] | 1.18–1.55 | +0.00% |
| 0.3 | +0.0026 [+0.0003, +0.0048] | -0.0206 [-0.0266, -0.0145] | 1.07–1.73 | +0.04% |

**ρ resta 0,15**: e' stato fissato prima del lancio e il criterio e' stato valutato li'. La figura dice come il costo di trasferimento al punto di partenza dipende da ρ; un altro ρ come braccio sarebbe un esperimento nuovo, da pre-registrare.

### Prova di adeguatezza ridotta a 4.580 per E1

Madrid p0 seme 201, E ed E1 attraverso `addestra_una`, 21 punti fino a 4580. I primi undici punti riproducono la campagna: scarto massimo E 0e+00, E1 0e+00.

| tetto | E: u, V-full | E1: u, V-full | ordine |
|---|---|---|---|
| 2290 | u2061, 0.91827 | u1832, 0.91883 | E < E1 |
| 4580 | u4580, 0.90455 | u4580, 0.90620 | E < E1 |

**Ordine invariato** fra 2.290 e 4580; oltre il budget V-full migliora ancora di E +1.49%, E1 +1.38%: plateau non raggiunto, ordine stabile — come nella prova di adeguatezza della campagna principale.

## 7. Decisioni conseguenti

- **E′ (= E1) e' il braccio E principale per E5 ed E6**: dichiarato nel protocollo §6 (esito riportato il 30/9), prima di E4.
- **E7 non e' piu' opzionale** e la politica gated di E4 ammette **τ = «mai»**: l'adattamento dal token peggiora C con intervallo che esclude lo zero a Londra (+0.034 [+0.024, +0.045]).

## 8. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_E.py` | `ccd37ca7a9f4012e` |
| `evoluzione/esperimenti/addestramento.py` | `d2d68544fc153371` |
| `evoluzione/componente/identita.py` | `e13498ad4f3aea18` |
| `evoluzione/componente/adattamento.py` | `80e810978be4fff6` |
| `evoluzione/componente/canonico.py` | `13159f040bde67f1` |
| `evoluzione/esperimenti/esegui_e2.py` | `d84a78e61e239dc4` |
| `evoluzione/esperimenti/ricostruisci_predizioni.py` | `5b37aeb8d51ea15f` |
| `evoluzione/analisi/analizza_e2.py` | `d50afaf7aad4534c` |
| `evoluzione/analisi/verifica_appaiamento.py` | `ab1857cde149e44c` |
| `evoluzione/esperimenti/adeguatezza_E1.py` | `d006022ce5529bd7` |
| `evoluzione/esperimenti/sensibilita_rho_e2.py` | `cf347e585b8f6c6f` |
| `protocol/E2.md` | `14a94b8a2bebc7e5` |

**Nessun parametro e' stato scelto dopo aver visto i risultati**: ρ e' nei manifesti di ogni esecuzione, la configurazione di F e' quella congelata in `selezione_F_griglia`.
