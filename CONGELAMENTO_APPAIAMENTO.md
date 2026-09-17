# Congelamento — sensibilità all'appaiamento dell'inizializzazione

**Congelato il 2026-09-17.** Addendum 1 al disegno congelato alla versione 5.

## 1. Le due campagne

| campagna | funzione |
|---|---|
| **raccordo** | confronto con inizializzazione **parzialmente disallineata** |
| **raccordo_appaiato** | sensibilità **prospetticamente specificata** all'allineamento dei moduli comuni |

**Entrambe si conservano.** La prima non è invalidata: è il confronto svolto
secondo il protocollo allora vigente, con il disallineamento scoperto dopo.

## 2. Conclusione fissata

> **L'allineamento dell'inizializzazione dei moduli comuni modifica
> sostanzialmente le differenze predittive osservate e riduce la loro
> variabilità fra inizializzazioni.** Nella campagna di sensibilità la non
> inferiorità è sostenuta nelle tre città; l'equivalenza è sostenuta in due.

> **Il deterioramento osservato nella prima campagna non è robusto
> all'allineamento dell'inizializzazione dei moduli comuni e non può essere
> attribuito alla sola rappresentazione.**

**Non si scrive** che il risultato «dipendeva dall'inizializzazione e non
dalla rappresentazione»: l'intervento mostra una sensibilità effettiva, ma
**non esclude interazioni fra rappresentazione e inizializzazione**.

## 3. Stima e intervalli, prima e dopo

| città | stima prima | stima dopo | differenza | NI prima | NI dopo |
|---|---|---|---|---|---|
| **Madrid** | +0.333% | **-0.235%** | -0.568 | +1.019% | **-0.012%** |
| **Londra** | +2.316% | **+0.065%** | -2.251 | +3.805% | **+0.394%** |
| **Melbourne** | +1.909% | **-0.293%** | -2.202 | +3.146% | **+0.441%** |

**Differenza appaiata fra i delta**, con il controllo LEGACY fermo: Madrid -0.568, Londra -2.251, Melbourne -2.202 punti. **Lo spostamento è nella stessa direzione in tutte le città.**

### Verdetti

| città | non inferiorità | equivalenza |
|---|---|---|
| **Madrid** | prima non conclusiva → **dopo SOSTENUTA** | prima non conclusiva → **dopo SOSTENUTA** |
| **Londra** | prima deterioramento rilevante → **dopo SOSTENUTA** | prima non sostenuta → **dopo SOSTENUTA** |
| **Melbourne** | prima non conclusiva → **dopo SOSTENUTA** | prima non conclusiva → **dopo non conclusiva** |

**Con entrambe le procedure di ricampionamento** nessun verdetto della nuova
campagna cambia: originaria e incrociata concordano su tutte e tre le città.

## 4. Stabilità Monte Carlo del limite

**Il generatore del risultato definitivo è il seme 1000**, identificato senza selezionarlo in funzione
dell'esito. Gli altri nove **documentano la sensibilità numerica**.

| città | limite (generatore definitivo) | mediana | dispersione | escursione | sotto il margine |
|---|---|---|---|---|---|
| Madrid | **+0.0677%** | +0.0678% | 0.00228 | 0.00599 | 10/10 |
| Londra | **+0.5822%** | +0.5763% | 0.00400 | 0.01242 | 10/10 |
| Melbourne | **+0.9190%** | +0.9119% | 0.01359 | 0.04890 | 10/10 |

Con **20,000 repliche** e **10 generatori**.

**Nessuna città appare marginale rispetto alla precisione numerica del
ricampionamento**: il limite resta sotto il margine in tutte le ripetizioni.

**Lo scostamento con la numerosità**, misurato sul MEDESIMO generatore
definitivo — misurarlo su un altro mescolerebbe due effetti:

| città | 1.000 repliche | 5.000 | 20,000 | scostamento |
|---|---|---|---|---|
| Madrid | +0.0622% | +0.0649% | +0.0677% | **+0.0056** punti |
| Londra | +0.5766% | +0.5818% | +0.5822% | **+0.0056** punti |
| Melbourne | +0.8523% | +0.9145% | +0.9190% | **+0.0666** punti |

**Le analisi a mille repliche erano meno precise di quanto sembrasse.**

> **La dispersione Monte Carlo del limite non è la significatività
> dell'effetto predittivo**, e non si usa come argomento inferenziale.

## 5. Matrice partizione × inizializzazione

| città | escursione fra i semi, prima | dopo | dispersione fra inizializzazioni |
|---|---|---|---|
| Madrid | 2.500 | **0.789** | 1,290 → 0,407 |
| Londra | 5.310 | **1.223** | 2,784 → 0,612 |
| Melbourne | 5.214 | **2.849** | 2,637 → 1,482 |

**La struttura per colonna si attenua ma non sparisce**: su Melbourne resta
un'escursione di 2,85 punti fra le tre inizializzazioni.

> **L'escursione fra inizializzazioni non si confronta con il margine**, che
> si riferisce all'effetto **medio**: descrive un'altra quantità.

## 6. Stabilità del controllo LEGACY

> **La ripetizione di LEGACY riproduce esattamente le perdite nelle
> esecuzioni considerate.** Scarto relativo massimo `0,00e+00%` su tutte e
> ventisette le celle, nei tre contesti.

**Non dimostra** che il backend sia universalmente deterministico, né che
tutte le predizioni coincidano: **sono state confrontate le perdite**.

È però la condizione che rende interpretabile il confronto: l'intervento
tocca la sola BASE-CORRECTED, e il controllo non si è mosso.

## 7. Metriche secondarie, ricalcolate su questa campagna

**Non si trasferiscono dalla campagna precedente**: un modello diverso ha
ordinamenti diversi.

| città | AP LEGACY | AP BASE-CORR | differenza assoluta | variazione relativa |
|---|---|---|---|---|
| **Madrid** | 0.2002 | 0.2057 | **+0.0054**, cioè +0.54 punti percentuali | **+2.72%** dalle medie; +2.77% appaiata |
| **Londra** | 0.3297 | 0.3359 | **+0.0062**, cioè +0.62 punti percentuali | **+1.89%** dalle medie; +2.13% appaiata |
| **Melbourne** | 0.2914 | 0.2963 | **+0.0049**, cioè +0.49 punti percentuali | **+1.68%** dalle medie; +1.75% appaiata |

**Le due colonne sono grandezze diverse**: la differenza assoluta è in punti
percentuali di average precision, la variazione relativa è il rapporto. La
**variazione appaiata** media le variazioni delle nove coppie, e può
differire da quella calcolata sulle medie.

> **Il miglioramento dell'AP è descrittivamente concorde nelle tre città,
> non una superiorità inferenziale dimostrata.**

### Perdita sui soli positivi

| città | LEGACY | BASE-CORRECTED | differenza |
|---|---|---|---|
| Madrid | 0.9308 | 0.9102 | -0.0206 |
| Londra | 0.9274 | 0.9240 | -0.0035 |
| Melbourne | 0.7487 | 0.7506 | +0.0019 |

## 8. Una correzione da registrare

Nella diagnostica precedente l'average precision era stata tratta dalla
**sola coppia `p0 s0`**. Su Madrid quel valore era **0,2355**, mentre la
media sulle nove coppie è **0,2002**, con estremi 0,1793 e 0,2355.

> **Una singola cella descrive quella combinazione di partizione e
> inizializzazione, non l'intera colonna né la campagna.**

Le metriche secondarie sono ora calcolate su tutte e nove le coppie, con
estremi riportati.

## 9. Artefatti

| | |
|---|---|
| schema del descrittore | 1.2 |
| implementazione dell'estrattore | 1.3 |
| coppie utilizzabili | 27/27 |
| repliche del ricampionamento | 20,000 |
| generatore definitivo | 1000 |

**Stati iniziali**, uno per seme e configurazione, salvati in
`results/evoluzione/stati_iniziali/`:

| chiave | impronta |
|---|---|
| `LEGACY_seme2029167940_c9_h32_b4_s5_d16` | `0c7e65475b66992a444752c839feec799b772a9ad2e4e9fdbc237c8a7f3b403a` |
| `BASE-CORRECTED_seme2029167940_c9_h32_b4_s5_d26` | `53f694125b859a667bc8c7b05b14a36b39b7997dadece0025eacd1b969c4feab` |
| `BASE-CORRECTED_seme2029167940_c9_h32_b4_s5_d26_allineato` | `46abcf2919808209bec44037bc588b0aef72ddbc71d08fcd08d837afb916d301` |
| `LEGACY_seme1918988776_c9_h32_b4_s5_d16` | `7fdc15521658bffe7bb2f90097764396489e3e827571034aa8e15bf860f806d0` |
| `BASE-CORRECTED_seme1918988776_c9_h32_b4_s5_d26` | `4ac80675e6eeb97761d758b010239983087a3a5dc5ff37f2a2c53137c0b7dff4` |
| `BASE-CORRECTED_seme1918988776_c9_h32_b4_s5_d26_allineato` | `517100256a86c3d02cca1c553f3e6cd30e3955dfc6df6f921ecfb984b181213f` |
| `LEGACY_seme2007055255_c9_h32_b4_s5_d16` | `0fd3d4a851c7a5d4814645f3145acdab9134d95003dc56fa062b88f6b729ae06` |
| `BASE-CORRECTED_seme2007055255_c9_h32_b4_s5_d26` | `8eb24b2ffa14fd1dc2c6e3f2215a757cccd3fb60b8936ddca39fce249b006b4f` |
| `BASE-CORRECTED_seme2007055255_c9_h32_b4_s5_d26_allineato` | `d81808054d6c174e0dbfe7b5c4d3bcde5c842886278aa6278ca09a663ae6f9ab` |

Semi dichiarati [7, 18, 29] → semi di torch [2029167940, 1918988776, 2007055255].

**Impronte del codice:**

| file | impronta |
|---|---|
| `evoluzione/esperimenti/prepara_stati_iniziali.py` | `77a7eba98130f07a` |
| `evoluzione/esperimenti/addestramento.py` | `513af836dd8c15f7` |
| `evoluzione/esperimenti/semi.py` | `1df55afa74745ab0` |
| `evoluzione/analisi/analizza_raccordo.py` | `6ba656d8184e050f` |
| `evoluzione/analisi/sensibilita_incrociata.py` | `1038a15f5751107c` |
| `evoluzione/analisi/stabilita_bootstrap.py` | `5c4c1be268e5b281` |
| `evoluzione/analisi/confronta_campagne.py` | `582e82f2bf02aa4e` |

## 10. Limiti

**Non è una replica su dati indipendenti**: stessi contesti, partizioni,
semi e dati. È un'analisi di sensibilità.

**Gli stessi tre semi hanno scoperto e diagnosticato il problema**, e ora ne
misurano la correzione. Serve una conferma su inizializzazioni nuove.

**Con tre inizializzazioni** entrambe le procedure restano poco informate
sulla variabilità dell'addestramento.

**Il raccordo misura il pacchetto**, non la sola imputazione né le sole
maschere.

**Gli intervalli sono condizionati al periodo di prova** e la dipendenza
spaziale fra nodi non è modellata.

