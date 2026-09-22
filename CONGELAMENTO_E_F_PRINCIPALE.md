# Congelamento — fase E principale e selezione di F

**Congelato il 2026-09-22.** Protocollo di addestramento `principale`: 2.290 aggiornamenti, undici punti, selezione su V-full, nessun arresto anticipato.

## 1. Fase E

| | |
|---|---|
| esecuzioni completate | **108**, fallite 0, marcatori `.fatto` 108 |
| parallelismo | 8 processi × 1 filo, backend CPU, un'unica macchina |
| ore di calendario | 16.4 |
| somma dei tempi di parete per esecuzione | 127.9 ore |

> **La somma dei tempi di parete NON è il costo seriale**: con 8 processi concorrenti ogni esecuzione rallenta per contesa. Non va confrontata con misure fatte in isolamento.

### Aggiornamento selezionato su V-full

| aggiornamento | punti E |
|---|---|
| 1374 | 6 |
| 1832 | 14 |
| 2061 | 20 |
| 2290 | 68 |

**68 su 108 selezionati al tetto.** Coerente con la prova di adeguatezza, che non aveva osservato il plateau: il budget resta finito e non dimostrato convergente.

## 2. Selezione di F

| città | scelta | wCE | seconda migliore | margine |
|---|---|---|---|---|
| **Madrid** | (50, 0.01) | 0.904833 | (200, 0.001) 0.905255 | 0.0004 wCE |
| **Londra** | (50, 0.01) | 0.804272 | (200, 0.001) 0.807185 | 0.0029 wCE |
| **Melbourne** | (200, 0.001) | 0.953782 | (10, 0.01) 0.955899 | 0.0021 wCE |

**La migliore configurazione fra le sei considerate**, per città. La regola di spareggio non è stata applicata: nessun pareggio.

### I sei candidati

| città | (10, 0.001) | (10, 0.01) | (50, 0.001) | (50, 0.01) | (200, 0.001) | (200, 0.01) |
|---|---|---|---|---|---|---|
| Madrid | 0.97425 | 0.92013 | 0.94347 | **0.90483** | 0.90526 | 0.91232 |
| Londra | 0.87159 | 0.82154 | 0.84389 | **0.80427** | 0.80718 | 0.80986 |
| Melbourne | 1.00387 | 0.95590 | 0.97481 | 1.01057 | **0.95378** | 1.13374 |

### Confronto con la selezione storica

| città | sui punti E a 35 aggiornamenti | sui punti E principali |
|---|---|---|
| Madrid | (200, 0.01) | **(50, 0.01)** |
| Londra | (200, 0.01) | **(50, 0.01)** |
| Melbourne | (200, 0.01) | **(200, 0.001)** |

**La scelta cambia in 3 città su 3.** Il trasferimento automatico della selezione storica, escluso dal protocollo, sarebbe stato scorretto: ora è verificato, non assunto.

### Episodio di validazione e costo

| | |
|---|---|
| manifesti | 108, tutti su E `principale` |
| conformi al perimetro | 108/108 |
| acquisizione, esempio | 2019-12-02 00:00 → 2019-12-03 00:00, 78 timestamp |
| valutazione, esempio | 2019-12-03 00:00 → 2019-12-04 00:00, 88 timestamp |
| adattamenti | 648, mediana 10.7 s, totale 3.13 ore, un processo |

## 3. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_E.py` | `d386eb4fe9819556` |
| `evoluzione/esperimenti/addestramento.py` | `346713146e1f9ab6` |
| `evoluzione/esperimenti/seleziona_F.py` | `110d26d3c07cf9c4` |
| `evoluzione/componente/adattamento.py` | `80e810978be4fff6` |
| `evoluzione/componente/valutazione.py` | `712d053aec8102c8` |
| `results/evoluzione/selezione_F_principale/configurazione_F.json` | `06d23ed1b0c48106` |

**Nessun dato di test è stato consultato.** La selezione non si modifica più.
