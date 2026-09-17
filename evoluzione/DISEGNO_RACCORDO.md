# Disegno del raccordo LEGACY ↔ BASE-CORRECTED

**Versione 4 — CONGELATA.** Approvata dal revisore senior. Ogni modifica successiva
incrementa la versione e va registrata in coda; il protocollo **non si modifica in
base ai risultati**.

---

## 0. Che cosa stabilisce, e che cosa no

**Stabilisce** se BASE-CORRECTED introduca un deterioramento predittivo superiore
alla tolleranza dichiarata, **nel nuovo impianto**.

**Non stabilisce** la riproduzione delle prestazioni storiche. L'encoder è diverso —
due strati a 64 unità contro una proiezione lineare — sicché **anche LEGACY qui non
è la configurazione che ha prodotto la Tabella 54**.

### Che cosa il raccordo misura, esattamente

> **BASE-CORRECTED non aggiunge nuove statistiche comportamentali** rispetto alle
> dodici statistiche non strutturalmente costanti di LEGACY. Elimina due componenti
> relative all'occupazione assente e aggiunge dodici componenti di disponibilità,
> con un incremento netto di **dieci ingressi e 640 parametri**.

**Il raccordo misura quindi l'effetto del trattamento esplicito della
disponibilità**, comprendente gli indicatori e le convenzioni di rappresentazione dei
valori non stimabili.

**Non isola il solo contributo delle maschere**, né quello della capacità aggiuntiva:
servirebbe un'ablazione ulteriore, non necessaria per questo raccordo.

**E le dodici statistiche non coincidono senza qualificazione.** Le formule
coincidono **dove le statistiche sono stimabili**; nei casi mancanti le due varianti
differiscono nel riempimento — in particolare **nelle bande non osservate**, che
LEGACY riempie con la media globale di addestramento mentre BASE-CORRECTED dichiara
non stimabili.

### Dimensione nominale e componenti variabili

| | nominali | **variabili** | encoder |
|---|---|---|---|
| **LEGACY** | 16 | **14** | 1.608 |
| **BASE-CORRECTED** | 26 | 26 | 2.248 |

**LEGACY conserva i tre canali storici** anche su Traffic4cast, dove l'occupazione è
assente: `media_occupazione` e `dev_occupazione` risultano **costanti a zero** per
ogni sensore e ogni finestra.

**Si conservano.** Eliminarle cambierebbe parametrizzazione e inizializzazione del
primo strato, e introdurrebbe un'altra variante senza necessità.

**La normalizzazione usa la convenzione storica** `std + 1e-6`, **dichiarata** come
gestione di un canale costante. Il contratto distingue:

| | esito |
|---|---|
| scala accidentalmente nulla o invalida | **errore** |
| canale costante **esplicitamente dichiarato** | ammesso e registrato |

Una scala pari a uno darebbe lo stesso risultato quando il valore centrato è zero,
ma non è universalmente equivalente: **la convenzione non si cambia.**

**Un limite da dichiarare**: l'encoder è stato scelto per la rappresentazione nuova.
Nessuna delle due varianti è ottimizzata, ma la configurazione non è neutrale
rispetto a LEGACY.

---

## 1. Protocollo: induttivo di inserimento

È il protocollo in cui la disponibilità incompleta della storia ha rilevanza per il
paper.

| | definizione |
|---|---|
| **nodi di addestramento** | 70% dei nodi, estratti per partizione |
| **nodi di validazione induttiva** | 15%, mai visti in addestramento, per la selezione |
| **nodi di prova** | 15%, **completamente esclusi** fino alla valutazione |
| **storia locale dei nodi nuovi** | **24 ore**, condizione primaria |
| **reinserimento nel grafo** | i nodi nuovi entrano nell'adiacenza all'inserimento; i collegamenti fra nodi preesistenti restano invariati |

**La disponibilità degli ingressi dinamici sui nodi nuovi durante la prova non rende
l'esperimento trasduttivo**, poiché quei nodi sono stati esclusi dall'apprendimento.

**Altre durate — 4 ore, 7 giorni, 28 giorni — sono valutazioni secondarie dello
stesso modello, senza nuovi addestramenti**, con protocollo compatibile fissato in
anticipo.

---

## 2. Perimetro

| | scelta |
|---|---|
| contesti | Madrid, Londra, Melbourne |
| partizioni dei nodi | **3**, comuni alle due varianti |
| inizializzazioni per partizione | **3**, semi separati da quelli delle partizioni |
| esecuzioni | 3 × 3 × 3 × 2 = **54** |

**Tre contesti verificano l'eterogeneità geografica**, non costituiscono un minimo
matematico: anche un solo contesto fornirebbe evidenza valida, limitata a quello.

**Le partizioni condividono il dataset**: non sono tre repliche geografiche
indipendenti, e con tre sole partizioni l'incertezza sulla loro variabilità resta
stimata con precisione limitata.

**Costo stimato circa diciotto ore, da verificare.** Non è un vincolo che giustifichi
arresti differenti fra varianti.

---

## 3. La grandezza e il criterio

Per partizione $p$ e inizializzazione $s$, con le perdite mediate **prima** sui
quattro orizzonti:

$$\delta_{p,s} = 100 \cdot
\frac{\mathcal{L}_{\text{CORRECTED},p,s} - \mathcal{L}_{\text{LEGACY},p,s}}
{\mathcal{L}_{\text{LEGACY},p,s}}$$

**Valori positivi indicano peggioramento.**

$$\widehat{\delta} = \frac{1}{3}\sum_{p=1}^{3}\frac{1}{3}\sum_{s=1}^{3}\delta_{p,s}$$

### Criterio principale: non inferiorità

**Per ciascuna città**, sostenuta se il **limite superiore unilaterale al 95%** di
$\widehat{\delta}$ è inferiore a **+1%**.

> **Margine convenzionale dell'1% relativo di entropia pesata**, adottato per
> verificare che il nuovo trattamento dei mancanti non introduca un deterioramento
> predittivo superiore alla tolleranza stabilita. **Le conseguenze operative si
> valutano separatamente** mediante precisione e richiamo.

Il criterio è fissato **prima delle nuove esecuzioni**.

### Verifica aggiuntiva: equivalenza

**Entro ±1%** con i due test unilaterali al livello 0,05, mediante l'intervallo
bilaterale al 90%. È più restrittiva della non inferiorità.

**Equivalenza non significa «nessun costo»**: significa differenza contenuta nel
margine.

### Che cosa si riporta, per città

| | |
|---|---|
| **non inferiorità** | sostenuta / non sostenuta / **non conclusiva** |
| **equivalenza** | sostenuta / non sostenuta / non conclusiva |
| **miglioramento rilevante** | limite superiore sotto zero |
| **deterioramento rilevante** | limite inferiore sopra il margine |

**L'esito «non conclusivo» esiste** e si usa quando l'incertezza attraversa il
margine.

### Nessun verdetto aggregato

**Le tre città non si aggregano in un unico verdetto numerico.** Per ciascuna si
riportano differenza stimata, limite di non inferiorità, intervallo di equivalenza,
metriche secondarie ed eventuale esito non conclusivo.

> **Due città favorevoli su tre non equivalgono a non inferiorità generale.**

**Un miglioramento non dimostra che la maschera aggiunga informazione**: il confronto
cambia anche imputazione, dimensionalità e capacità del primo strato.

---

## 4. Convenzioni fissate (audit E)

| elemento | valore |
|---|---|
| **popolazione** | dichiarata per contesto e **verificata dal manifesto** (§6) |
| **pesi di classe** | $w_k = N/(3n_k)$, stimati sui soli **nodi e periodi ammessi all'addestramento**; fissi fra varianti e fra repliche dello stesso confronto |
| **partizione dei NODI** | 70/15/15, con identificativi registrati per partizione |
| **partizione TEMPORALE** | 70/15/15 **cronologica**, con timestamp esatti dei confini |
| **confini temporali** | definiti cronologicamente. Un esempio appartiene all'addestramento **solo se tutti i suoi bersagli** vi ricadono; stessa regola per validazione e prova. Gli ingressi anteriori al confine sono utilizzabili se causalmente disponibili |
| **orizzonti** | 15, 30, 60, 120 minuti |
| **riferimento** | `esterno_fisso`, versione registrata per contesto |
| **normalizzazione dei descrittori** | media e scala sui **soli nodi di addestramento nel periodo di addestramento**, identiche fra varianti |
| **dimensione d'ingresso** | LEGACY **16** nominali, 14 variabili; BASE-CORRECTED **26** |
| **parametri dell'encoder** | **1.608** e **2.248**; modello completo **25.060** e **25.700** |
| **budget di addestramento** | identico fra varianti: epoche, dimensione del lotto, ottimizzatore, passo |
| **arresto anticipato** | sulla validazione induttiva, medesima pazienza e medesimo criterio |
| **selezione** | epoca con la minore perdita di validazione; a parità, la prima |

---

## 5. Ricampionamento

**Ogni replica ricostruisce la struttura dello stimatore:**

1. estrarre **tre partizioni con reinserimento**;
2. per ciascuna occorrenza, estrarre **tre inizializzazioni con reinserimento**;
3. applicare il ricampionamento dei dati **preservando le molteplicità**;
4. usare **gli stessi campioni** per entrambe le varianti;
5. ricalcolare le differenze relative, poi le medie previste.

**Il ricampionamento dei dati riguarda i nodi di prova**, estratti come serie
intere: la sequenza temporale interna a ciascun nodo è quindi preservata.

> **Gli intervalli descrivono la variabilità rispetto alle partizioni, alle
> inizializzazioni e ai nodi valutati, condizionatamente al periodo temporale di
> prova. Non quantificano la trasferibilità a periodi differenti.**

**La dipendenza spaziale fra nodi non è modellata esplicitamente**: si ricampionano
nodi singoli, non blocchi spaziali.

**Gli aggregati restano separati per orizzonte**, poiché la metrica è la media delle
quattro perdite e non la perdita delle somme: sul collaudo differiscono di
3,7 × 10⁻⁴.

**Collaudo eseguito**: il calcolo per aggregati coincide con la **duplicazione
esplicita delle celle** a scarto esattamente nullo, su quattro configurazioni di
molteplicità. **Dieci verifiche su dieci.**

---

## 6. Manifesto delle istanze attese

**Costruito prima dell'addestramento.** Ogni predizione ha chiave:

    contesto, partizione, inizializzazione, nodo, istante_di_previsione, orizzonte

**Controlli, ciascuno bloccante:**

| | verifica |
|---|---|
| 1 | assenza di duplicati inattesi |
| 2 | appartenenza ai nodi di prova dichiarati |
| 3 | appartenenza dei bersagli al periodo di prova |
| 4 | **identità delle chiavi fra LEGACY e BASE-CORRECTED** |
| 5 | corrispondenza fra istanze attese e salvate |

> **Un controllo fallito blocca l'analisi**, non produce un avviso. È il requisito
> che impedisce alla campagna nuova di ereditare l'incertezza sul perimetro che
> affligge i dump storici.

---

## 7. Metriche secondarie

**Fuori dal criterio principale.** Si riportano **anche quando contraddicono** la
metrica principale.

| | specifica |
|---|---|
| average precision sulla classe critica | quel nome, non «precisione media» |
| precisione e richiamo | a soglia scelta sulla **validazione induttiva** |
| regola di scelta della soglia | massimizza F1 sulla classe critica; **comune alle varianti**, mentre le soglie numeriche possono differire |

**Una non inferiorità in entropia non autorizza una conclusione di accettabilità
operativa** se le metriche secondarie mostrano deterioramenti rilevanti.

---

## 8. Decisioni approvate

| | decisione |
|---|---|
| 1 | **protocollo induttivo**: partizione dei nodi 70/15/15, con ruoli di addestramento, validazione induttiva e prova |
| 2 | **condizione primaria**: ventiquattro ore di storia |
| 3 | **criterio principale**: non inferiorità rispetto a LEGACY, margine +1% relativo di entropia pesata, limite superiore unilaterale al 95% |
| 4 | **verifica aggiuntiva**: equivalenza entro ±1%, intervallo bilaterale al 90% |
| 5 | **ricampionamento**: coerente con la media su partizioni e inizializzazioni, molteplicità preservate, confronti appaiati |
| 6 | **interpretazione**: confronto del pacchetto di modifiche, non effetto isolato dell'imputazione o delle maschere; metriche secondarie complementari, fuori dal criterio |

## 9. Condizioni per avviare le esecuzioni

Le cinquantaquattro esecuzioni possono partire **dopo** che:

1. questo documento è congelato;
2. gli **audit B e D sono superati sul modello completo** — non su quello minimo del
   collaudo dell'encoder;
3. una **prova tecnica end-to-end ridotta** ha verificato manifesti, salvataggi e
   analisi.

> **Le prestazioni della prova tecnica non si usano per modificare il protocollo.**

**L'approvazione del disegno non sostituisce gli audit.**

---

## Appendice — stato della verifica retrospettiva

**La correzione algoritmica è approvata**; la validazione retrospettiva **no**.

> Sui dump disponibili, le procedure confrontate conservano gli esiti di
> distinguibilità da zero. Per i dump il cui perimetro di valutazione non è stato
> ricostruito, il risultato costituisce **un'analisi di sensibilità e non una
> validazione** degli intervalli pubblicati.

**Tre domande distinte, di cui una sola verificata:**

| | verificata? |
|---|---|
| distinguibilità da zero | **sì**, invariata con le tre procedure |
| equivalenza di R2 entro il margine | **no** |
| superamento della soglia del 10% per R3 | **no** |

**I risultati storici restano marcati come parzialmente verificati.** La piccola
differenza numerica sulle città non certifica l'identità delle popolazioni.

**Sulla riduzione della varianza**: la componente indipendente fra inizializzazioni
si riduce di un fattore pari al loro numero, **condizionatamente a dati e
partizione**. Le componenti condivise non si riducono nello stesso modo. L'esito
mostra quindi che le due modifiche hanno effetti opposti **nei confronti analizzati**,
non una regola universale di compensazione.

**La ricostruzione storica si interrompe** perché non produttiva, non perché chiusa.


---

## Registro delle versioni

| versione | modifica |
|---|---|
| 1 | prima stesura |
| 2 | protocollo induttivo, non inferiorità, ricampionamento a tre livelli, manifesto bloccante |
| **3** | congelata: partizioni separate, incertezza condizionata al periodo di prova, nessun verdetto aggregato, condizioni per l'avvio |
| **4** | **congelata**: schemi per sorgente, nove canali con maschere, LEGACY a 16 nominali e 14 variabili, formulazione qualificata di cosa il raccordo misura |
