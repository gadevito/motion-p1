# Addendum — verifica esterna su PEMS04

**Da congelare prima del collaudo.** Nessuna modifica successiva guidata dai
risultati del nuovo test.

---

## 1. Schema dei canali e aggregazione

Artefatto: una sola chiave `data`, forma **(16.992, 307, 3)**, ordine
documentato **flusso, occupazione, velocità**. Correlazioni come controllo di
plausibilità, non come verifica delle unità: occupazione–velocità −0,826,
flusso–occupazione +0,615.

| grandezza | aggregazione a 15 minuti |
|---|---|
| flusso | **somma**, valida in quanto conteggio per intervallo secondo la fonte documentale; il nome del canale non basta |
| occupazione | **media**, aggregazione temporale dichiarata |
| velocità | **media dei valori pubblicati**, senza attribuirle il significato di velocità media spaziale o ponderata per veicolo |

**Lo schema non coincide con Traffic4cast.** Là due grandezze dinamiche e due
maschere; qui tre grandezze e tre maschere, e cambiano le componenti del
descrittore. **Cambiano le dimensioni dei primi strati**: si mantiene la
struttura del modello e la politica di aggiornamento, si adatta lo schema degli
ingressi alle grandezze disponibili. L'appaiamento resta **fra C e P dentro
questo esperimento**.

---

## 2. Calendario e assunzioni temporali

| | |
|---|---|
| periodo | **1 gennaio – 28 febbraio 2018**, documentato |
| griglia | 5 minuti, regolare: 59 × 288 = 16.992 **senza residui** |
| ora locale | **assunzione dichiarata**, California; non è una proprietà verificata dell'artefatto |
| primo giorno | **Capodanno**, festivo; periodo invernale |

L'allineamento settimanale ricavato dai profili di traffico **coincide** con
quello documentato, ma è solo un controllo di plausibilità: la fonte è la
documentazione.

---

## 3. Riferimento e pesi

> **Riferimento empirico di velocità della rete**, non «velocità di flusso
> libero del sensore».

$$v_{\text{rif},p} = Q_{0,95}\left(v_{i,t} : i \in V_{\text{iniziali},p},\ t \in T_{\text{addestramento}}\right)$$

Stimato **per partizione**, sui **soli nodi iniziali**, sulle velocità **già
aggregate**, **congelato prima di validazione e prova**, **comune a C, P-frozen
e P-refresh**, usato coerentemente in ingressi, descrittori e bersagli. **Il
valore prodotto dalla regola si registra**, non si fissa a priori.

**Il bersaglio è una classificazione della velocità relativa a un riferimento
comune**, non la congestione normalizzata sul riferimento proprio di ciascun
tratto. Soglie dichiarate: ≥ 0,8, 0,5–0,8, < 0,5.

**I pesi si ricalcolano sul solo addestramento ammesso**, col nuovo bersaglio.
La distribuzione 92,4 / 5,2 / 2,4 veniva dal riferimento precedente ed è
**superata**: non si riusa.

I nodi il cui riferimento proprio è distante restano una **diagnostica
privilegiata**, mai un ingresso né un criterio per escluderli dal risultato
principale.

---

## 4. Periodo di valutazione

| | |
|---|---|
| suddivisione | 70 / 15 / 15 sulle origini |
| prova | ≈ **8,8 giorni** |
| acquisizione | 24 ore da $t_0$ |
| **valutazione** | ≈ **7,8 giorni** dopo l'acquisizione |

Fasce: **prima giornata**, **giorni 2–7**, **residuo oltre i sette giorni**,
quest'ultimo dichiarato **di supporto molto breve**. **Non si estrapola alla
persistenza di ventuno giorni.**

---

## 5. Criterio dei due confronti

$$\Delta_C = \mathcal L_{\text{refresh}} - \mathcal L_C \qquad
\Delta_F = \mathcal L_{\text{refresh}} - \mathcal L_{\text{frozen}}$$

Stesso periodo, stesse celle, stessi ricampionamenti per tutti i bracci, con
nodi e molteplicità preservate.

> **Affermazione congiunta solo se il limite superiore unilaterale al 95% è
> inferiore a zero per ENTRAMBI i confronti.** Altrimenti si riportano effetti
> circoscritti ed esiti non conclusivi.

**È una replica esterna su un dataset**, non una generalizzazione geografica.

Metriche obbligatorie: wCE, average precision, precisione e richiamo con la
regola decisionale già congelata, costo incrementale e cumulativo
dell'aggiornamento del descrittore. **Nessuna ricalibrazione delle soglie sui
nuovi bersagli.**

---

## 6. Limite del preprocessing

> **Il rilascio è preprocessato e indicato come già imputato. L'interpolazione
> lineare è riportata nelle fonti consultate, ma, in assenza delle maschere
> originarie e della completa tracciabilità del preprocessing, non è
> verificabile la causalità delle singole osservazioni imputate. Le procedure
> del nostro modello sono causali rispetto alla serie distribuita; non è
> garantita la causalità rispetto alle misure grezze.**

Un'interpolazione lineare usa un valore precedente **e uno successivo**: se
applicata prima della suddivisione, un ingresso può contenere informazione
posteriore all'istante di previsione, e le prime ventiquattro ore possono
dipendere da osservazioni successive. **Non sappiamo se accada qui né in quale
misura.**

Che tutti i bracci usino la stessa serie rende il confronto **controllato**, ma
**non garantisce che gli effetti del preprocessing si cancellino**.

### Certezza delle fonti, distinta

| affermazione | grado |
|---|---|
| il dataset è già imputato, mancanti 0% | **dichiarato** per PEMS04 dalla documentazione di una libreria |
| l'imputazione è per interpolazione lineare | **descritto in letteratura per la famiglia** di dataset |
| quella procedura si applica a **questo** file | **presunto**, non verificato |
| il flusso è un conteggio per intervallo | **documentale**, non dedotto dal nome del canale |

---

## 7. Artefatto

| | |
|---|---|
| repository | `github.com/Davidham3/ASTGCN`, rinominato `ASTGCN-2019-mxnet`, percorso `data/PEMS04/pems04.npz` |
| **SHA-256** | `95a3c9b720fffdb85f0330d09bfab41b0b3cad0ca86c0d7d5f3accacb4ac999a` |
| identificativo git del contenuto | `a1a39eac4b86963b1ac22874fd1cc693eb642cd2` |
| **revisione** | **`a3a70af8a8ba`**, 18 giugno 2019, «update all code, fix bugs» — **l'unica** che abbia toccato il file |

**Verifica eseguita**: l'identificativo git del file locale coincide con quello
pubblicato sul ramo principale, quindi **il contenuto e' lo stesso bit per
bit**.

> **L'artefatto utilizzato coincide con quello disponibile alla revisione
> `a3a70af8a8ba`.** Non si afferma che il download sia stato effettuato da
> quella revisione: manca una registrazione del download. **Lo SHA-256 resta
> l'identificatore principale del contenuto**, ricalcolabile senza git.

Nel paper il contesto si chiama **PEMS04**, senza attribuirgli una città non
accertata e senza presentarlo come «quarta città».

---

## 8. Perimetro

3 partizioni × 12 inizializzazioni × 2 modelli = **72 addestramenti**. Modelli:
**C** e **P**, quest'ultimo valutato come **P-frozen** e **P-refresh** dallo
stesso punto di controllo.

**La politica è già congelata**: descrittore delle ultime ventiquattro ore,
aggiornamento a ogni previsione, pesi congelati, nessuna selezione di durata o
frequenza sul nuovo test.

**La distribuzione delle classi è già stata ispezionata** nella ricognizione del
dato: è una ricognizione, non una valutazione predittiva, e **le soglie non sono
state cambiate** sulla base dello sbilanciamento osservato.
