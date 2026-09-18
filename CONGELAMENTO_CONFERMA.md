# Congelamento — conferma su dodici inizializzazioni nuove

**Congelato il 2026-09-18.** Addendum 2. Margine, protocollo e criterio di successo **invariati**.

## 1. Conclusione

> **Sulle dodici inizializzazioni nuove, la non inferiorità di
> BASE-CORRECTED rispetto a LEGACY è sostenuta a Londra e Melbourne, ma
> rimane non conclusiva a Madrid. Il criterio congiunto sulle tre città non
> è quindi soddisfatto.** A Madrid la stima puntuale è interna al margine,
> mentre il limite superiore lo supera; tale esito è **stabile rispetto alla
> precisione Monte Carlo**.

**Non è dimostrata un'inferiorità rilevante a Madrid.** La vicinanza al
margine si riporta, ma non modifica il verdetto.

## 2. Risultati primari — analisi incrociata, dodici semi nuovi

| città | stima | $U_{95}$ | intervallo di equivalenza (90%) | non inferiorità | equivalenza |
|---|---|---|---|---|---|
| **Madrid** | +0.254% | **+1.078%** | [-0.299; +1.078] | **non conclusiva** | non conclusiva |
| **Londra** | -0.042% | **+0.295%** | [-0.361; +0.295] | **SOSTENUTA** | SOSTENUTA |
| **Melbourne** | -0.653% | **-0.305%** | [-1.011; -0.305] | **SOSTENUTA** | non conclusiva |

**Gli intervalli sono riportati con entrambi gli estremi**, e i confronti di
ampiezza usano la medesima procedura, livello e statistica.

**Su Melbourne il limite superiore è negativo** (-0.305%), il che
sostiene anche una differenza **favorevole rispetto a zero** secondo quella
procedura. **Non basta da solo a dimostrare equivalenza**: occorre il limite
inferiore rispetto a −1%, che vale -1.011% — **oltre** il margine, sicché l'equivalenza non è sostenuta.

### Stabilità Monte Carlo

**20,000 repliche**, **10 generatori**, definitivo 1000.

| città | limite | mediana | dispersione | escursione | sotto il margine |
|---|---|---|---|---|---|
| Madrid | +1.1396% | +1.1205% | 0.00911 | 0.02584 | **0/10** |
| Londra | +0.2880% | +0.2865% | 0.00333 | 0.00945 | **10/10** |
| Melbourne | -0.3177% | -0.3199% | 0.00267 | 0.00998 | **10/10** |

**Su Madrid nessuna delle dieci ripetizioni** scende sotto il margine:
l'esito non conclusivo non è un artefatto della precisione numerica.

| città | 1.000 repliche | 5.000 | 20,000 | scostamento |
|---|---|---|---|---|
| Madrid | +1.1415% | +1.1396% | +1.1396% | -0.0020 punti |
| Londra | +0.2686% | +0.2785% | +0.2880% | +0.0194 punti |
| Melbourne | -0.3226% | -0.3215% | -0.3177% | +0.0050 punti |

## 3. Confronto con la campagna di sensibilità

**Solo la NON INFERIORITÀ**, misurata con la medesima procedura incrociata:

| città | tre semi | dodici semi nuovi |
|---|---|---|
| **Madrid** | sostenuta (+0.072%) | **non conclusiva** (+1.078%) |
| **Londra** | sostenuta (+0.575%) | **sostenuta** (+0.295%) |
| **Melbourne** | sostenuta (+0.977%) | **sostenuta** (-0.305%) |

> **Alcune conclusioni ottenute con tre inizializzazioni non si mantengono
> sulle dodici nuove, mostrando la sensibilità dell'evidenza alla
> realizzazione della casualità di addestramento.**

**Non si dichiara** che i primi tre semi fossero «non rappresentativi»: è
una proprietà non dimostrata.

### Ampiezze

| città | tre semi | dodici semi | rapporto |
|---|---|---|---|
| Madrid | 0.673 | 1.377 | 2.05× |
| Londra | 1.010 | 0.657 | 0.65× |
| Melbourne | 2.449 | 0.706 | 0.29× |

**Medesima procedura, livello e statistica** in entrambe le colonne.

> **Il fattore due riguarda un'aspettativa sulla componente indipendente fra
> inizializzazioni, non una previsione sulle ampiezze ottenute da due insiemi
> diversi di semi.** Le riduzioni osservate **non sono, da sole, una verifica
> della decomposizione della varianza.**

## 4. Metriche secondarie

**Fuori dal criterio.** Ricalcolate su questa campagna.

| città | AP LEGACY | AP BASE-CORR | differenza | differenza APPAIATA, media | dispersione |
|---|---|---|---|---|---|
| **Madrid** | 0.2008 | 0.1961 | -0.0047 | **-0.0047** | 0.0241 [-0.1210; +0.0129] |
| **Londra** | 0.3289 | 0.3303 | +0.0014 | **+0.0014** | 0.0135 [-0.0223; +0.0462] |
| **Melbourne** | 0.2747 | 0.2766 | +0.0019 | **+0.0019** | 0.0085 [-0.0152; +0.0218] |

> **Non emerge un miglioramento uniforme della discriminazione della classe
> critica**: l'AP peggiora descrittivamente a Madrid e migliora lievemente
> nelle altre due città.

**Le differenze APPAIATE fra varianti**, non la sola escursione dei livelli
assoluti, misurano la stabilità del confronto: i livelli assoluti variano
molto fra coppie perché variano i modelli, non il loro divario.

### Perdita sui soli positivi

| città | LEGACY | BASE-CORRECTED | differenza |
|---|---|---|---|
| Madrid | 0.9436 | 0.9372 | -0.0064 |
| Londra | 0.9368 | 0.9197 | -0.0171 |
| Melbourne | 0.7704 | 0.7652 | -0.0052 |

**È una proprietà distinta**, e **non compensa automaticamente** il
peggioramento dell'AP.

## 5. Perimetro e completamenti

| | |
|---|---|
| coppie utilizzabili | **108/108** |
| schema del descrittore | 1.2 |
| implementazione dell'estrattore | 1.3 |
| esecuzioni | 216 |
| BASE-CORRECTED — completata | 108 |
| LEGACY — completata | 108 |

**Nessun fallimento**: tutte le coppie sono utilizzabili, e l'analisi non è
condizionata a un sottoinsieme.

**Impronte del codice:**

| file | impronta |
|---|---|
| `evoluzione/esperimenti/semi.py` | `162afaca0aa2c6de` |
| `evoluzione/esperimenti/prepara_stati_iniziali.py` | `8e3306f5d199514c` |
| `evoluzione/esperimenti/addestramento.py` | `513af836dd8c15f7` |
| `evoluzione/analisi/analizza_raccordo.py` | `6066183070b05775` |
| `evoluzione/analisi/sensibilita_incrociata.py` | `883cfc4be9e24e91` |
| `evoluzione/analisi/stabilita_bootstrap.py` | `b66d1406d8e101af` |

**Stati iniziali**: 36 salvati, semi dichiarati
[101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112] → semi di torch [666291128, 951503465, 1186735207, 1510822925, 597953926, 1177941530, 226343263, 9693054, 1192611950, 1288128005, 1018519217, 413001143].

## 6. Analisi combinata sui quindici semi

**Resta secondaria e non modifica il mancato raggiungimento della
conferma.** Se eseguita, va dichiarato che **i primi tre semi sono stati
utilizzati per diagnosticare e sviluppare la procedura di appaiamento**.

## 7. Che cosa questo chiude, e che cosa no

**Chiude il raccordo**, non l'intero progetto.

> **BASE-CORRECTED può essere studiata come soluzione ingegneristica
> esplicita e verificabile, ma non va presentata come universalmente priva di
> costo predittivo entro l'1%.**

### Limiti, invariati

**Non è una validazione su dati indipendenti**: la campagna verifica la
robustezza rispetto a nuove inizializzazioni, non la generalizzazione a
nuovi dati né a nuovi sistemi.

**Il raccordo misura il pacchetto**, non la sola imputazione né le sole
maschere.

**Gli intervalli sono condizionati al periodo di prova**, e la dipendenza
spaziale fra nodi non è modellata esplicitamente.

