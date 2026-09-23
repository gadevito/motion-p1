# Congelamento — fase E e selezione di F, GRIGLIA TEMPORALE REALE

**Regola temporale, in tutte le fasi e per tutti i bracci:** un'origine e' ammissibile soltanto se la sequenza dal primo passo della finestra dinamica all'ultimo bersaglio rispetta la cadenza reale di quindici minuti, senza salti nella griglia. Le misure mancanti del singolo sensore restano alle maschere.

**Convenzione degli estremi:** l'acquisizione e' $(t_0, t_1]$. La riga $t_0$ non e' usata da descrittore, adattamento di F o corpus di R.

**Pesi delle classi** ricalcolati sulle origini ammissibili in `pesi_griglia`; la normalizzazione, che usa le righe del periodo come osservazioni, e' invariata.

**Congelato il 2026-09-23.** Protocollo di addestramento `principale`: 2.290 aggiornamenti, undici punti, selezione su V-full, nessun arresto anticipato.

## 1. Fase E

| | |
|---|---|
| esecuzioni completate | **108**, fallite 0, marcatori `.fatto` 108 |
| parallelismo | 8 processi × 1 filo, backend CPU, un'unica macchina |
| ore di calendario | 16.2 |
| somma dei tempi di parete per esecuzione | 125.6 ore |

> **La somma dei tempi di parete NON è il costo seriale**: con 8 processi concorrenti ogni esecuzione rallenta per contesa. Non va confrontata con misure fatte in isolamento.

### Aggiornamento selezionato su V-full

| aggiornamento | punti E |
|---|---|
| 1374 | 3 |
| 1603 | 2 |
| 1832 | 8 |
| 2061 | 27 |
| 2290 | 68 |

**68 su 108 selezionati al tetto.** Coerente con la prova di adeguatezza, che non aveva osservato il plateau: il budget resta finito e non dimostrato convergente.

## 2. Selezione di F

| città | scelta | wCE | seconda migliore | margine |
|---|---|---|---|---|
| **Madrid** | (50, 0.01) | 0.904932 | (200, 0.001) 0.905676 | 0.0007 wCE |
| **Londra** | (50, 0.01) | 0.804652 | (200, 0.001) 0.807122 | 0.0025 wCE |
| **Melbourne** | (200, 0.001) | 0.827683 | (10, 0.01) 0.848599 | 0.0209 wCE |

**La migliore configurazione fra le sei considerate**, per città. La regola di spareggio non è stata applicata: nessun pareggio.

### I sei candidati

| città | (10, 0.001) | (10, 0.01) | (50, 0.001) | (50, 0.01) | (200, 0.001) | (200, 0.01) |
|---|---|---|---|---|---|---|
| Madrid | 0.97606 | 0.92057 | 0.94466 | **0.90493** | 0.90568 | 0.91261 |
| Londra | 0.87023 | 0.82093 | 0.84291 | **0.80465** | 0.80712 | 0.80996 |
| Melbourne | 0.95577 | 0.84860 | 0.89359 | 0.85318 | **0.82768** | 0.87923 |

### Confronto con le selezioni precedenti

| città | E a 35 aggiornamenti | E a 2.290, origini per indice | questa pipeline |
|---|---|---|---|
| Madrid | (200, 0.01) | (50, 0.01) | **(50, 0.01)** |
| Londra | (200, 0.01) | (50, 0.01) | **(50, 0.01)** |
| Melbourne | (200, 0.01) | (200, 0.001) | **(200, 0.001)** |

- rispetto a «E a 35 aggiornamenti»: la scelta cambia in **3 città su 3**
- rispetto a «E a 2.290, origini per indice»: la scelta cambia in **0 città su 3**

**Nessuna selezione si trasferisce da una pipeline all'altra**: ciascuna vale per i punti E e le origini con cui e' stata prodotta.

### Episodio di validazione e costo

| | |
|---|---|
| manifesti | 108, tutti su E `griglia` |
| conformi al perimetro | 108/108 |
| acquisizione, esempio | 2019-12-02 00:00 → 2019-12-03 00:00, 77 timestamp |
| valutazione, esempio | 2019-12-03 00:00 → 2019-12-04 00:00, 88 timestamp |
| adattamenti | 648, mediana 10.7 s, totale 3.13 ore, un processo |

## 3. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_E.py` | `97b51e17f13c06c2` |
| `evoluzione/esperimenti/addestramento.py` | `ebe4147a047ab60b` |
| `evoluzione/esperimenti/seleziona_F.py` | `4c5fbb3441756f68` |
| `evoluzione/componente/adattamento.py` | `80e810978be4fff6` |
| `evoluzione/componente/valutazione.py` | `712d053aec8102c8` |
| `results/evoluzione/selezione_F_griglia/configurazione_F.json` | `18062d5ba9596a6f` |

**Nessun dato di test è stato consultato.** La selezione non si modifica più.
