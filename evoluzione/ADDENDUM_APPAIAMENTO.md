# Addendum prospettico — sensibilità all'appaiamento dell'inizializzazione

**Fissato prima delle esecuzioni.** Estende il disegno congelato alla versione 5
senza modificarne margine, condizioni di storia, metriche o perimetro.

---

## 0. Che cosa questo esperimento è, e che cosa non è

**È un'analisi di sensibilità all'appaiamento dell'inizializzazione.**

**Non è una replica su dati indipendenti**: stessi contesti, stesse partizioni,
stessi semi, stessi dati. La riesecuzione di LEGACY vi funge da **controllo di
stabilità**, non da conferma esterna.

**Non isola una spiegazione.** Se la struttura per colonna sopravvive, avremo
escluso l'allineamento di questi moduli come spiegazione **sufficiente**; se si
attenua, avremo evidenza della sua sensibilità all'inizializzazione comune, **non
ancora una spiegazione esaustiva**.

---

## 1. Che cosa l'audit ha stabilito

`PredittorePerNodo` costruisce nell'ordine `start → blocchi → enc → stat → e1 →
e2`, e l'encoder ha dimensioni diverse fra le varianti — 1.608 parametri contro
2.248 — sicché consuma **640 estrazioni in più** e tutto ciò che segue riceve
numeri diversi.

| elemento comune | esito, su tutti e tre i semi |
|---|---|
| `start`, backbone temporale, BatchNorm | **identici** (66 tensori) |
| **ramo statico, teste previsionali** | **DIVERSI** (6 tensori) |
| ordine dei lotti | identico, generatore numpy separato |

**Due precisazioni.** Il consumo del generatore è deterministico a seme fissato,
ma riguarda comunque **una sorgente di variabilità dell'addestramento**. E l'8%
dei parametri **indica l'estensione del disallineamento, non la sua rilevanza
predittiva**.

---

## 2. L'intervento, circoscritto

Per ciascuno dei tre semi:

1. ricostruire lo stato iniziale **originario** di LEGACY;
2. ricostruire lo stato iniziale **originario** di BASE-CORRECTED;
3. **conservare entrambi come artefatti**, non identificarli solo dal seme;
4. nella nuova BASE-CORRECTED, sostituire **soltanto** ramo statico e teste con
   quelli iniziali di LEGACY.

```text
LEGACY
    stato iniziale originario, INVARIATO

BASE-CORRECTED allineata
    backbone            originario
    encoder             originario BASE-CORRECTED
    ramo statico        iniziale LEGACY      <- sostituito
    teste previsionali  iniziali LEGACY      <- sostituito
```

> **L'unica modifica intenzionale rispetto alla campagna precedente è quella
> identificata dall'audit.**

### Perché non semi separati per tutti i moduli

Sarebbe la soluzione giusta per l'implementazione futura, ma **cambierebbe anche
l'inizializzazione dell'encoder** e di altri componenti: il nuovo risultato non
sarebbe allora attribuibile al solo allineamento dei moduli individuati.

**Prima l'intervento circoscritto**; la gestione modulare dei generatori si adotta
poi come convenzione generale.

---

## 3. Perimetro, invariato

| | |
|---|---|
| contesti | Madrid, Londra, Melbourne |
| partizioni | le stesse tre, semi 1000, 1037, 1074 |
| inizializzazioni | le stesse tre, semi 7, 18, 29 |
| rappresentazioni | LEGACY 16, BASE-CORRECTED 26 |
| iperparametri | 35 epoche, lotto 32, passo 10⁻³, pazienza 8 |
| esecuzioni | **54** |
| margine | **±1%**, invariato |
| storia primaria | 96 passi, invariata |
| metriche | invariate, pesi dagli artefatti esistenti |

---

## 4. Controlli prima del lancio, tutti bloccanti

| | verifica |
|---|---|
| 1 | **tutti i moduli comuni** hanno tensori iniziali identici fra le varianti |
| 2 | l'encoder di BASE-CORRECTED **coincide esattamente** con quello iniziale della campagna precedente |
| 3 | LEGACY ha lo **stesso stato iniziale** della campagna precedente |
| 4 | ordine dei lotti e altre sorgenti casuali **non cambiano** |
| 5 | gli **stati iniziali completi sono salvati**, non identificati dal solo seme |

**Se il backend non è deterministico, si dichiara**: anche un intervento così
controllato può conservare variabilità numerica di esecuzione.

---

## 5. Analisi, fissata adesso

**Il ricampionamento è quello INCROCIATO**, scelto ora e non dopo: una sola lista
di inizializzazioni per replica, condivisa fra le partizioni estratte.

Si riportano:

1. **nuovo delta** LEGACY ↔ BASE-CORRECTED, per città;
2. **non inferiorità ed equivalenza** con il bootstrap incrociato;
3. **matrice** partizione × inizializzazione;
4. **confronto descrittivo della struttura per colonna**, prima e dopo;
5. **differenze fra la vecchia e la nuova LEGACY** — quanto si muove il controllo.

Le procedure precedenti restano documentate. **Nessun verdetto aggregato**, come
sempre.

### Come NON si leggerà l'esito

> **Non si dichiarerà che il disallineamento «spiegava il deterioramento»** se il
> risultato migliora.

Si valuterà **anche quanto si muove il controllo LEGACY** e **quanto l'effetto sia
coerente fra partizioni e città**: un miglioramento che si accompagni a uno
spostamento analogo della sola LEGACY non direbbe nulla sull'allineamento.

| esito | lettura |
|---|---|
| la struttura per colonna **sopravvive** | l'allineamento di questi moduli **non è spiegazione sufficiente** |
| la struttura **si attenua** | evidenza di **sensibilità** all'inizializzazione comune, **non una spiegazione esaustiva** |

---

## 6. Che cosa non si aggiunge

**Nessuna nuova caratteristica, nessun nuovo seme, nessuna ablazione.** Le
decisioni fra isolare una componente del pacchetto e aumentare le
inizializzazioni si prendono **dopo** questo esperimento.

---

## Registro delle versioni

| | |
|---|---|
| disegno del raccordo | **5**, invariato |
| schema del descrittore | 1.2, invariato |
| implementazione dell'estrattore | 1.3, invariata |
| **addendum** | **1**, questo documento |
