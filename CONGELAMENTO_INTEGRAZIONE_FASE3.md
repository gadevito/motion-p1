# Congelamento — versione dell'integrazione della fase 3

**Congelato il 2026-09-23**, commit `1f5da08476cd`. Prova tecnica ridotta: **19 controlli su 19**, log in `results/evoluzione/prova_fase3.log`.

## I cinque bracci, attraverso gli stessi esecutori

| braccio | popolazione | corpus | campionamento | esecutore |
|---|---|---|---|---|
| **C** | iniziale | originario | uniforme sugli istanti | `addestra_una` |
| **P** | iniziale | originario | uniforme sugli istanti | `addestra_una` |
| **A** | ampliata | privilegiato | uniforme sugli istanti | `addestra_una` |
| **R** | ampliata | post-installazione | **uniforme per nodo** | `addestra_una` |
| **F** | — | acquisizione | — | `adattamento.adatta` |

**Valutazione unica per tutti e cinque**, con `valutazione.valuta`: stesse chiavi di prova, stesso perimetro, accumulo per orizzonte.

## Regole in vigore

| | |
|---|---|
| budget | `max_optimizer_updates` = 2.290, undici punti, nessun arresto anticipato |
| selezione | minimo di V-full sulla **rete iniziale**; a parità, il precedente |
| griglia temporale | **reale**: nessuna finestra attraversa un salto |
| estremi | acquisizione $(t_0, t_1]$: la riga $t_0$ non si usa |
| pesi | ricalcolati sulle origini ammissibili, `pesi_griglia` |
| budget di R | 32 × K iniziali finestre per aggiornamento, invariato |
| perimetro di prova | tutte le origini ammissibili dopo $t_1$ |
| fasce temporali | prima giornata, fino a una settimana, oltre — **fissate prima dell'analisi** |

## Misure distinte

| misura | modalità | serve a |
|---|---|---|
| prestazioni | campagna in parallelo, registrato | qualità dei modelli |
| **costi** | **campione isolato**: 3 città, partizione 1000, semi 201–203, un processo | costo delle strategie |
| durata | come eseguita | costo operativo |

> **I tempi delle esecuzioni concorrenti non dimostrano che un braccio sia più veloce di un altro.**

## Impronte del codice congelato

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_inserimento.py` | `eac0d78acbf33cf2` |
| `evoluzione/esperimenti/inserimento.py` | `50094d7812cd0db0` |
| `evoluzione/esperimenti/prova_inserimento.py` | `28c79732f94a7cff` |
| `evoluzione/esperimenti/addestramento.py` | `4fe7c857c486a823` |
| `evoluzione/esperimenti/seleziona_F.py` | `4c5fbb3441756f68` |
| `evoluzione/componente/griglia.py` | `dc4c8857bba94dc1` |
| `evoluzione/componente/corpus.py` | `350fb2fbce1fb80a` |
| `evoluzione/componente/campionamento.py` | `253921afd21f8dd6` |
| `evoluzione/componente/adattamento.py` | `80e810978be4fff6` |
| `evoluzione/componente/episodio.py` | `63da2ca2d98fcd3e` |
| `evoluzione/componente/valutazione.py` | `712d053aec8102c8` |

**Nessun dato di prova è stato consultato** prima del lancio. Le prestazioni della prova tecnica non hanno orientato alcun iperparametro.
