# Congelamento dei risultati del raccordo LEGACY ↔ BASE-CORRECTED

**Congelato il 2026-09-17.** Nessun addestramento successivo.

## 1. Conclusione fissata

> **Nessuna città dimostra la non inferiorità con entrambe le procedure
> considerate.** L'evidenza di deterioramento superiore all'1% osservata a
> Londra con il ricampionamento originario **non è robusta alla
> specificazione incrociata**. Le stime puntuali sono sfavorevoli a
> BASE-CORRECTED, ma l'incertezza non consente conclusioni robuste rispetto
> al margine prefissato.

**Due precisazioni sulla lettura.**

L'esito negativo **non si rafforza come evidenza di peggioramento**: resta
robusta la sola *mancata dimostrazione* della non inferiorità.

L'allargamento degli intervalli è **coerente** con una dipendenza associata
all'inizializzazione, ma **non ne è una conferma indipendente**: deriva
proprio dalla diversa struttura imposta al ricampionamento.

## 2. Stime e intervalli, procedure affiancate

**Le stime puntuali sono INVARIATE fra le due procedure**: il
ricampionamento modifica gli intervalli, non lo stimatore.

| città | stima | procedura | limite NI (95% unil.) | equivalenza (90% bil.) | ampiezza |
|---|---|---|---|---|---|
| Madrid | +0.333% | originaria | +1.019% | [-0.375; +1.019] | 1.393 |
|  | +0.333% | incrociata | +1.363% | [-0.762; +1.363] | 2.126 |
| Londra | +2.316% | originaria | +3.805% | [+1.116; +3.805] | 2.689 |
|  | +2.316% | incrociata | +4.612% | [+0.321; +4.612] | 4.291 |
| Melbourne | +1.909% | originaria | +3.146% | [+0.536; +3.146] | 2.609 |
|  | +1.909% | incrociata | +3.809% | [-0.163; +3.809] | 3.972 |

Ampiezza dell'incrociata rispetto all'originaria: **1.53×**, **1.60×**, **1.52×**.

## 3. Verdetti, separati per domanda

| città | non inferiorità | equivalenza | deterioramento oltre il margine |
|---|---|---|---|
| **Madrid** | **non dimostrata** con entrambe | **non sostenuta** con entrambe | orig. non stabilito / incr. non stabilito |
| **Londra** | **non dimostrata** con entrambe | **non sostenuta** con entrambe | orig. sì / incr. non stabilito |
| **Melbourne** | **non dimostrata** con entrambe | **non sostenuta** con entrambe | orig. non stabilito / incr. non stabilito |

**Su Londra il verdetto cambia**: `eq_inf` passa da +1.116 a +0.321, sicché l'intervallo non sta
più interamente sopra il margine.

**Su Madrid lo scarto dal margine è di 0,019 punti percentuali** — +1.019% contro +1,000%. La vicinanza
si dichiara, **senza trasformarla in accettazione**.

**Su Melbourne l'intervallo originario è interamente positivo**: il
risultato è non conclusivo **rispetto al margine dell'1%**, non rispetto
all'assenza di differenza.

## 4. Criterio di deterioramento: specificazione NON preregistrata

Il protocollo congelato fissa la non inferiorità al 95% unilaterale e
l'equivalenza al 90% bilaterale, ma **non definisce con quale limite si
dichiari il deterioramento oltre il margine**.

L'implementazione usa il **limite inferiore dell'intervallo bilaterale al
90%**, coerente con il test unilaterale al 5% di

$$H_0:\ \delta \leq 1\% \qquad \text{contro} \qquad H_1:\ \delta > 1\%$$

> **Si registra come specificazione non esplicitata nel protocollo
> originario, non come criterio preregistrato.** Non modifica la domanda
> principale già fissata: nessuna città dimostra la non inferiorità.

## 5. Artefatti della campagna conforme

| | |
|---|---|
| schema del descrittore | 1.2 |
| implementazione dell'estrattore | 1.3 |
| coppie utilizzabili | 27/27 |
| ricampionamento | 1000 repliche |
| margine | ±1.0% |

**Impronte del codice di analisi:**

| file | impronta |
|---|---|
| `evoluzione/analisi/analizza_raccordo.py` | `1b9b75337605e5b5` |
| `evoluzione/analisi/sensibilita_incrociata.py` | `1038a15f5751107c` |
| `evoluzione/analisi/pesi.py` | `523769860117b3d0` |
| `evoluzione/analisi/ricampionamento.py` | `665a120d30e2cf9b` |
| `evoluzione/esperimenti/addestramento.py` | `ae33b3477b0738f2` |
| `evoluzione/esperimenti/esegui_raccordo.py` | `435f8b3e57dd39e6` |
| `evoluzione/componente/estrattore.py` | `5a402382c36fbedd` |
| `evoluzione/componente/predittore.py` | `1db32e1b23e2701e` |

**Pesi di classe**, uno per città e partizione, consumati da
addestramento e analisi senza ricalcolo:

| città | p0 | p1 | p2 |
|---|---|---|---|
| Madrid | `09852f026634da96` | `48385a529124b836` | `dcac9d571f4fe9b0` |
| Londra | `e870287ec9199f2e` | `f42ea393cc8255d5` | `24b2ec9929e5078d` |
| Melbourne | `9bfb59eabf2a115e` | `0792a6b23d69f7c2` | `ea7ee6280771a26a` |

## 6. Storia delle esecuzioni

**Tre campagne. Le prime due sono invalidate e NON entrano nell'analisi.**

### Prima campagna — non conforme

**Difetto**: l'addestramento usava l'entropia **non pesata**, mentre il
protocollo fissa $w_k = N/(3n_k)$. I pesi della valutazione non erano
tracciati: `reg.metrica(...)` non veniva mai chiamato.

**I risultati NON erano stati esaminati**: il difetto è emerso durante la
verifica dell'analisi, prima di interpretarli.

### Seconda campagna — non conforme

**Difetto**: `clamp(0, 2)` portava i bersagli **non assegnati alla classe
verde**. Nel periodo di prova erano il **14,1%** su Madrid, il **40,0%** su
Londra, il **19,6%** su Melbourne. Il modello imparava a prevedere verde
dove non c'è misura, e la metrica lo premiava — mentre i pesi erano stimati
sulle sole celle valide.

> **I risultati ERANO STATI ESAMINATI prima della scoperta del difetto.**
> Davano Madrid non inferiore, Londra in deterioramento e Melbourne non
> conclusiva. Il difetto è emerso da una verifica successiva del codice,
> non dall'esame di quei numeri.

### Che cosa resta e che cosa no

| | conservato |
|---|---|
| manifesti delle esecuzioni | **sì**, in `results/evoluzione/registro/` |
| versioni del codice | **sì**, nella storia del repository |
| difetti e motivazione dell'invalidazione | **sì**, in questo documento e nel diario |
| **predizioni e punti di controllo** | **NO, eliminati** e quindi non più disponibili |

**Le predizioni delle due campagne invalidate non sono ricostruibili** senza
riaddestrare. La scelta è stata di liberare 4,4 GB di risultati non
interpretabili, conservando la traccia di che cosa fossero e perché lo
fossero.

### Terza campagna — conforme

Collaudo dell'integrazione **22 verifiche su 22**, con la distribuzione
valutata che coincide con quella delle celle valide a **scarto nullo**, e
**54 esecuzioni su 54** completate al primo tentativo.

## 7. Limiti dichiarati

**Il raccordo misura il pacchetto**, non la sola imputazione né le sole
maschere: BASE-CORRECTED cambia insieme imputazione, dimensionalità e
capacità del primo strato. Il peggioramento non è attribuibile a una
componente senza un'ablazione separata.

**Gli intervalli sono condizionati al periodo di prova** e descrivono la
variabilità rispetto a partizioni, inizializzazioni e nodi valutati. Non
quantificano la trasferibilità ad altri periodi.

**La dipendenza spaziale fra nodi non è modellata**: si ricampionano nodi
singoli, non blocchi spaziali.

**Con tre inizializzazioni** entrambe le procedure restano poco informate
sulla variabilità dell'addestramento. La sensibilità dice **se** il verdetto
dipenda dalla struttura assunta, **non quale** procedura sia corretta.

**L'encoder è stato scelto per la rappresentazione nuova.** Nessuna variante
è ottimizzata, ma la configurazione non è neutrale rispetto a LEGACY.

