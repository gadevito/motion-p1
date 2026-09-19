# Congelamento — selezione della configurazione di adattamento di F

**Congelato il 2026-09-19.** Protocollo 2.4.

## 1. Conclusione, come formulata

> **Tutte e tre le città selezionano la configurazione con 200
> aggiornamenti e learning rate 0,01. Nei punti esplorati, la perdita
> diminuisce all'aumentare del budget e il learning rate maggiore prevale a
> parità di budget. Il miglioramento prosegue fino al massimo budget
> considerato; non è stato verificato se ulteriori aggiornamenti o learning
> rate diversi producano benefici.**

**F è valutato entro il budget esplorato, non come migliore adattamento
possibile.** Un eventuale vantaggio di P non dimostrerà superiorità rispetto
a ogni possibile adattamento.

## 2. Configurazione scelta

| città | aggiornamenti | passo | wCE | gruppi |
|---|---|---|---|---|
| **Madrid** | 200 | 0.01 | 0.978252 | 36 |
| **Londra** | 200 | 0.01 | 0.867776 | 36 |
| **Melbourne** | 200 | 0.01 | 0.952270 | 36 |

**Regola di spareggio**: meno aggiornamenti, poi passo minore. Non applicata: nessun pareggio.

## 3. I sei candidati, per città

| città | (10, 10⁻³) | (10, 10⁻²) | (50, 10⁻³) | (50, 10⁻²) | (200, 10⁻³) | (200, 10⁻²) |
|---|---|---|---|---|---|---|
| **Madrid** | 1.017934 | 1.013572 | 1.015956 | 0.998784 | 1.009328 | **0.978252** |
| **Londra** | 0.902712 | 0.898714 | 0.900892 | 0.885715 | 0.894948 | **0.867776** |
| **Melbourne** | 0.994645 | 0.990260 | 0.992658 | 0.974547 | 0.985850 | **0.952270** |

### Rendimento del budget

**Gli incrementi di budget sono diversi** — 40 aggiornamenti da 10 a 50,
150 da 50 a 200 — sicché le variazioni percentuali non sono confrontabili.
Si riportano le **riduzioni assolute per aggiornamento aggiuntivo** e per
**secondo aggiuntivo misurato**, a passo 10⁻²:

| città | Δ/agg. (10→50) | Δ/agg. (50→200) | Δ/s (10→50) | Δ/s (50→200) |
|---|---|---|---|---|
| Madrid | 3.697e-04 | 1.369e-04 | 1.740e-03 | 6.337e-04 |
| Londra | 3.250e-04 | 1.196e-04 | 1.529e-03 | 5.537e-04 |
| Melbourne | 3.928e-04 | 1.485e-04 | 1.849e-03 | 6.876e-04 |

> **Il rendimento per aggiornamento DIMINUISCE** fra i due intervalli, di
> circa 2,7 volte, in tutte e tre le città. **Non è dimostrata alcuna
> accelerazione della curva, né che l'ottimo si trovi fuori dalla griglia.**

## 4. Calendario e istanze

| città | acquisizione | valutazione | timestamp acq./val. | istanze | celle valide |
|---|---|---|---|---|---|
| **Madrid** | 2021-11-02 00:00 → 2021-11-03 00:00 | 2021-11-03 00:00 → 2021-11-04 00:00 | 78 / 88 | 11,880 | 39,073 |
| **Londra** | 2019-12-02 00:00 → 2019-12-03 00:00 | 2019-12-03 00:00 → 2019-12-04 00:00 | 78 / 88 | 11,880 | 32,000 |
| **Melbourne** | 2020-10-24 12:45 → 2020-10-25 12:45 | 2020-10-25 12:45 → 2020-10-25 23:45 | 78 / 36 | 3,204 | 6,801 |

**Origine = timestamp previsionale distinto.** Le tre unità sono riportate
separatamente, per acquisizione e valutazione.

## 5. Costo misurato

| | |
|---|---|
| gruppi di sei candidati | **108** |
| adattamenti | **648** |
| mediana per adattamento | 10.5 s |
| totale | 3.01 ore |

| budget | mediana |
|---|---|
| 10 aggiornamenti | 2.1 s |
| 50 aggiornamenti | 10.5 s |
| 200 aggiornamenti | 42.2 s |

## 6. Provenienza e tracciabilità

**108 manifesti aggregati**, uno per gruppo, ciascuno con i sei
candidati: aggiornamenti richiesti ed eseguiti, impronte iniziale e finale
degli embedding, wCE, secondi, nodi adattati e registro dell'adattamento.

**Conformi al perimetro**: 108/108.

**Punti di controllo E**, con impronta, in ciascun manifesto:

| città | esempio | impronta |
|---|---|---|
| Madrid | `ck_E_Madrid_p0_s1150248972.pt` | `ccd981cef444d40a` |
| Londra | `ck_E_Londra_p0_s1150248972.pt` | `2bbba337cd09afe3` |
| Melbourne | `ck_E_Melbourne_p0_s1150248972.pt` | `5cc7dcb5b0b5d79d` |

**Impronte del codice:**

| file | impronta |
|---|---|
| `evoluzione/esperimenti/seleziona_F.py` | `4f55696c41fc369c` |
| `evoluzione/componente/adattamento.py` | `80e810978be4fff6` |
| `evoluzione/componente/episodio.py` | `63da2ca2d98fcd3e` |
| `evoluzione/componente/identita.py` | `5aed747e4367449c` |
| `evoluzione/esperimenti/calendario.py` | `2a4a573181df7a10` |

## 7. Che cosa questo NON decide

**La selezione non si tocca più.** Il test non modifica la configurazione
di F, e nessun risultato di prova è stato consultato durante questa fase.

**La griglia resta invariata**: estenderla richiederebbe un emendamento
trasparente al budget fissato, e non è autorizzata per questa campagna.

