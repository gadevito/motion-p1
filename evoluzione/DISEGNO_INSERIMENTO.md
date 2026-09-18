# Disegno dell'esperimento principale sull'inserimento

**Versione 2.2.** Recepisce le specificazioni operative. Nessuna esecuzione
avviata.

---

## 0. Le domande

**Predittiva.** Quanto migliora la previsione sui nuovi sensori quando il modello
dispone di un descrittore ricavato dalle prime ventiquattro ore di osservazioni,
rispetto a un modello privo di tale descrittore?

**Ingegneristica.** Quale compromesso fra qualità predittiva e costo di
aggiornamento offre questa soluzione rispetto all'adattamento del solo embedding e
al riaddestramento dell'intero modello?

**Diagnostica.** Quanto rimane distante la soluzione dal risultato ottenuto quando
il nodo era già presente durante l'addestramento iniziale?

> **Le prime due sono le domande principali.** La terza utilizza informazione **non
> disponibile** nello scenario di nuova installazione e **rimane separata**.

**Non si introduce un criterio generale di successo.** Si stimano differenze e
costi con la relativa incertezza.

---

## 1. I cinque bracci

Tutti valutati **sugli stessi nodi nuovi e sulle stesse celle future**.

| | strategia | informazione locale del nuovo nodo | aggiornamento dopo l'installazione |
|---|---|---|---|
| **C** | modello condiviso senza descrittore storico | finestra dinamica, calendario, statiche comuni | **nessuno** |
| **P** | identità osservabile **BASE-CORRECTED** | come C, più il descrittore dalle prime 24 ore | **nessuno** |
| **F** | adattamento dell'embedding | prime 24 ore, per apprendere il nuovo embedding | solo l'embedding del nuovo nodo |
| **R** | **riaddestramento completo** | dati della rete iniziale e prime 24 ore dei nuovi nodi | tutti i parametri del predittore |
| **A** | riferimento storico **privilegiato** | il nodo era presente nell'addestramento iniziale | nessuno, all'inserimento simulato |

### Precisazioni

**C riceve le statiche**, come gli altri: «senza identità» significa **senza
descrittore storico né embedding specifico**, non assenza di ogni informazione
caratterizzante.

**A non è garantito migliore degli altri**: maggiore informazione in addestramento
non implica necessariamente minore perdita in prova.

**R è una strategia disponibile in esercizio**, anche se costosa. **A non la
sostituisce.**

**Non si aggiunge LEGACY**: il raccordo ha già risposto alla domanda pertinente.
BASE-CORRECTED resta la proposta, con i limiti documentati.

**Non si aggiunge EXTENDED**: cambiare contemporaneamente strategia di inserimento
e descrittore renderebbe il primo esperimento meno leggibile.

---

## 2. Modelli iniziali e provenienza dei punti di controllo

### C e P

Addestrati **esclusivamente sui nodi iniziali**, secondo il protocollo induttivo già
definito.

**P deve incontrare in addestramento descrittori costruiti con una disponibilità
storica compatibile con quella valutata.** Per questa campagna la configurazione
primaria usa finestre di **ventiquattro ore**, senza introdurre ora una nuova
distribuzione di durate.

### Il modello E, preparatorio

**Embedding liberi a otto dimensioni, sui soli nodi iniziali.**

> **E è un punto di controllo preparatorio, non un braccio di valutazione.**

| | |
|---|---|
| **F** | parte da **E** |
| **R** | stessa famiglia architetturale di E, **riaddestrato da zero** sulla rete ampliata |
| **A** | addestrato separatamente, **includendo** i nodi che simulano le nuove installazioni |

> **F non può partire da A**, neppure eliminando poi l'embedding del nodo: **il
> backbone di A avrebbe già appreso dalle sue osservazioni.**

---

## 3. Cronologia

| | |
|---|---|
| $t_0$ | installazione simulata |
| $t_1 = t_0 + 24\,\text{h}$ | termine della storia iniziale disponibile |
| valutazione | **successiva a $t_1$** |

### Lo STESSO $t_0$ nelle tre partizioni della stessa città

Per ciascuna città, $t_0$ è **l'inizio del periodo di prova già definito**, e la
valutazione riguarda le origini previsionali successive alla disponibilità delle
ventiquattro ore, **con tutti gli orizzonti contenuti nel periodo di prova**.

> **Non si sceglie un giorno diverso per partizione**: introdurrebbe una variazione
> temporale insieme a quella della popolazione, rendendo meno interpretabile il
> fattore «partizione».

Gli inserimenti ripetuti in date diverse saranno una verifica temporale successiva.

### Il calendario, con i timestamp effettivi

**Congelato. Lo stesso $t_0$ nelle tre partizioni di ciascuna città.**

| città | $t_0$ | istante | $t_1$ | istante |
|---|---|---|---|---|
| **Madrid** | 8887 | 2021-12-01 13:45 | 8983 | 2021-12-02 13:45 |
| **Londra** | 8966 | 2020-01-01 10:15 | 9062 | 2020-01-02 10:15 |
| **Melbourne** | 8806 | 2020-11-30 17:30 | 8902 | 2020-12-01 17:30 |

**Origini previsionali temporalmente ammissibili per F e R: 78** in tutte e tre le
città — con finestra dinamica di dodici passi e orizzonte massimo di otto,
ventotto delle novantasei non sono utilizzabili.

### Copertura e bande nelle prime ventiquattro ore

**Registrate prima delle esecuzioni**, come prescritto.

| città | copertura mediana | minimo | nodi a copertura zero | bande vuote, massimo | nodi con ≥1 banda vuota |
|---|---|---|---|---|---|
| Madrid | 87,5% | 44,8% | **0** | 1 | 15 |
| **Londra** | **37,5%** | **8,3%** | **0** | **5** | **205** |
| Melbourne | 84,4% | 63,5% | **0** | 1 | 9 |

> **Londra è il caso in cui il descrittore lavora nelle condizioni più difficili**:
> copertura mediana del 37,5%, un nodo all'8,3%, e **205 nodi su 900 con almeno una
> banda non osservata**. È anche il contesto in cui P e C possono differire di più,
> e quello in cui le convenzioni di riempimento pesano.

**Nessun nodo è a copertura zero** in alcuna città: F avrà esempi adattabili
ovunque, salvo verifica sui singoli nodi di prova.

**Il 1° gennaio di Londra** cade nel periodo, con il traffico anomalo del
capodanno. **Resta parte dell'esperimento**: non si sposta l'installazione per
ottenere condizioni migliori.

### Regole del calendario

| | |
|---|---|
| **ventiquattro ore** | **durata di calendario**, non 96 osservazioni valide |
| l'installazione | **non si sposta** per ottenere maggiore copertura |
| i nodi con storia scarsa | **non si escludono** automaticamente |
| F senza esempi adattabili | conserva l'embedding iniziale, come già previsto |
| copertura e bande | **si registrano** per le prime ventiquattro ore |

> **Se l'inizio della prova coincide con un'interruzione della sorgente, quella
> condizione resta parte dell'esperimento** — salvo un requisito di ammissibilità
> definito **prima** della selezione. **Non si corregge dopo aver osservato le
> prestazioni.**

### Informazioni ammesse

Per **P, F e R**, le osservazioni locali del nuovo sensore sono **esclusivamente
quelle raccolte a partire da $t_0$**.

### Ammissibilità di un esempio: due condizioni distinte

**Maturazione temporale e validità della misura non sono la stessa cosa.**

> **Un esempio è temporalmente ammissibile quando il suo orizzonte massimo non
> supera $t_1$. Le celle bersaglio mancanti sono escluse dalla perdita; l'esempio
> contribuisce se contiene almeno un target valido.**

**Non si richiedono quattro target validi su quattro**: selezionerebbe le finestre
più coperte e penalizzerebbe proprio i sensori più incompleti.

La convenzione è **la stessa per F e per i nuovi esempi di R**, ed è quella della
perdita mascherata già collaudata.

> Con orizzonte massimo di due ore, **non tutte le origini previsionali contenute
> nelle ventiquattro ore sono temporalmente ammissibili**.

### Valutazione primaria, da $t_1$

- tutte le strategie ricevono **gli stessi ingressi dinamici** causalmente
  disponibili;
- **P mantiene fisso** il descrittore costruito sulle prime ventiquattro ore;
- **F e R non eseguono ulteriori aggiornamenti**;
- A utilizza il proprio stato appreso in precedenza;
- il riferimento esterno di congestione resta **fisso e comune**.

> **Nessuna strategia aggiorna il modello usando i target del periodo di
> valutazione.**

---

## 4. Specifica di F — adattamento dell'embedding

### Parametri aggiornati

**Soltanto il nuovo embedding a otto dimensioni.**

Restano **congelati**: backbone temporale, ramo statico, teste, embedding dei nodi
esistenti, **statistiche e buffer della BatchNorm**.

> **Non si aggiorna un encoder**: F appartiene alla famiglia con **embedding
> liberi**, non a quella con descrittore osservabile.

### Inizializzazione del nuovo embedding

**La media degli embedding dei nodi iniziali**, calcolata sul punto di controllo E.

È una regola **deterministica**, che non usa dati futuri né sceglie un nodo
favorevole.

### Dati di adattamento

Gli esempi supervisionati **validi** ricavabili dalle prime ventiquattro ore del
nuovo sensore.

Nel backbone per-nodo, aggiornare i soli nuovi embedding **non richiede dati dei
nodi esistenti**.

> Se il nodo non dispone di alcun esempio utilizzabile, **F conserva l'embedding
> iniziale** e registra «adattamento non eseguibile per assenza di esempi».

### Che cosa significa «aggiornamento»

| | |
|---|---|
| ottimizzatore | **Adam** |
| decadimento dei pesi | **nessuno** |
| arresto anticipato durante l'adattamento | **nessuno** |
| ciascun aggiornamento | usa **tutti gli esempi ammissibili del singolo nodo** |

> Le finestre di ventiquattro ore producono pochi esempi: **un aggiornamento a
> lotto completo per nodo** rende il budget interpretabile e **indipendente
> dall'ordine dei minilotti**.

L'operazione si può vettorizzare, **purché il risultato sia equivalente
all'adattamento separato dei nodi**.

### La selezione: UNA configurazione per città

$$\eta \in \{10^{-3},\ 10^{-2}\}, \qquad B \in \{10,\ 50,\ 200\}$$

**Sei combinazioni**, valutate su un **episodio di validazione**:

| | |
|---|---|
| installazione | all'inizio del periodo temporale di **validazione** |
| acquisizione | le prime ventiquattro ore |
| adattamento | sui soli **nodi di validazione induttiva** |
| valutazione | sul periodo successivo, **sempre entro la validazione temporale** |

**I nodi di validazione induttiva restano esclusi dall'addestramento iniziale di E.**

### Regola di scelta

Per ogni combinazione, la wCE **mediata sui quattro orizzonti**, poi **sulle
inizializzazioni**, poi **sulle tre partizioni con uguale peso**.

**Una sola combinazione per città**, applicata a **tutti** i nodi nuovi, le
partizioni e le inizializzazioni della prova.

**A parità numerica**, si preferisce nell'ordine: **meno aggiornamenti**, poi
**passo minore**.

> **Non si seleziona una configurazione per ciascun nodo**: cambierebbe il metodo e
> richiederebbe un'ulteriore validazione locale.

> **Evita di indebolire artificialmente F**, e non costituisce ottimizzazione sui
> nodi di prova.

---

## 5. Specifica di R — riaddestramento completo

**R rappresenta il riaddestramento disponibile dopo l'installazione**, non il
riferimento privilegiato A.

Utilizza il corpus di addestramento della rete iniziale **e** gli esempi ammissibili
delle prime ventiquattro ore dei nuovi nodi. **Non riceve la loro storia anteriore
a $t_0$.**

Backbone e configurazione di ottimizzazione **coerenti con E**.

### Il corpus, fissato

| | |
|---|---|
| dati di addestramento **originari** dei nodi iniziali | sì |
| esempi **ammissibili** delle prime ventiquattro ore dei nodi nuovi | sì |
| dati di validazione nella perdita di addestramento | **no** |
| dati locali dei nuovi nodi **anteriori a $t_0$** | **no** |

**Politica di campionamento: NESSUN sovracampionamento dei nuovi nodi**, mantenendo
la convenzione di addestramento della famiglia E.

**Si riporta comunque la quota effettiva di contributi alla perdita proveniente dai
nodi nuovi.**

> **Se è molto piccola, sarà un limite della strategia R così definita**, non la
> prova che ogni riaddestramento completo sia inefficace.

**Si registra**: composizione del corpus, numero di esempi vecchi e nuovi, politica
di campionamento, epoche e aggiornamenti effettivi.

---

## 5bis. La regola di arresto, comune a tutte le famiglie

**Per C, P, E, A e R**, il riferimento per il punto di controllo è:

> **la wCE sui nodi della RETE INIZIALE, nel periodo temporale di validazione, con
> gli stessi orizzonti e le stesse maschere.**

Questo insieme:

- **non richiede embedding** dei nodi di validazione induttiva per E;
- **non contiene target futuri** dei nuovi nodi di prova;
- **è disponibile anche per R**;
- consente **una regola comune fra famiglie**.

**La validazione induttiva sui nodi separati serve invece a scegliere la
configurazione di adattamento di F.**

Iperparametri già fissati, ove applicabili all'addestramento completo: **35 epoche
massime, lotto 32, passo $10^{-3}$, pazienza 8**.

> **Limite dichiarato**: la selezione del punto di controllo **privilegia la
> prestazione sulla rete iniziale**. Non è una procedura ottimizzata specificamente
> sui nuovi nodi. È però **comune, riproducibile e disponibile operativamente**.

---

## 6. Grandezze principali

**Per ogni città, anzitutto le differenze di perdita:**

$$\mathcal{L}_P - \mathcal{L}_C, \qquad
\mathcal{L}_P - \mathcal{L}_F, \qquad
\mathcal{L}_P - \mathcal{L}_R$$

Affiancate da **differenze relative appaiate** e metriche secondarie.

| confronto | che cosa misura |
|---|---|
| **P – C** | il **beneficio del descrittore** |
| **P – F**, **P – R** | il **compromesso** rispetto alle alternative che aggiornano parametri |

### Recupero rispetto ad A: misura SECONDARIA

$$R_P = \operatorname{media}_{p,s}\left[
\frac{\mathcal{L}_{C,p,s} - \mathcal{L}_{P,p,s}}
{\mathcal{L}_{C,p,s} - \mathcal{L}_{A,p,s}}\right]$$

**Si chiama**: *quota del divario rispetto al riferimento storico privilegiato
recuperata dal descrittore*.

> **Non «percentuale di identità ricostruita»**: il denominatore riflette anche la
> **diversa informazione ricevuta in addestramento**.

### Denominatore instabile — regole fissate qui

| situazione | regola |
|---|---|
| sempre | si riportano **differenze assolute** e **distribuzione dei denominatori** |
| un denominatore **nullo o negativo** per esecuzione | **non si sintetizza** il recupero come percentuale media per quella città |
| denominatori positivi ma **prossimi a zero** | si riporta l'**instabilità** del rapporto e il suo intervallo, **senza filtrare** le esecuzioni sfavorevoli |
| il ricampionamento produce denominatori non positivi | **non si eliminano** quelle repliche per ottenere un intervallo finito |

> **In questi casi le differenze di perdita restano il risultato principale
> interpretabile.**

---

## 6bis. Informazione e pesi: fissi per tutti i bracci

**Per tutti e cinque i bracci restano fissi:**

| | stimato su |
|---|---|
| riferimento esterno | artefatto già registrato |
| normalizzazione dei canali dinamici | **rete iniziale** |
| pesi di classe della **metrica** | **rete iniziale** |
| pesi di classe della **perdita** di addestramento e adattamento | **rete iniziale** |

> **Stimandoli sulla rete iniziale si evita che A e R cambino anche obiettivo di
> ottimizzazione per effetto della popolazione ampliata.**

**I parametri di normalizzazione del descrittore appartengono a P** e si stimano
**soltanto sui dati iniziali ammessi**.

---

## 7. Inizializzazioni e partizioni

| | |
|---|---|
| inizializzazioni | **dodici**, semi **201 … 212** |
| partizioni | le stesse tre, semi 1000, 1037, 1074 |

> **Non si usano i tre semi di sviluppo**, né i dodici della conferma.

**L'appaiamento riguarda gli stati iniziali dei moduli comuni.** Non richiede di
rendere artificialmente identici componenti che hanno struttura diversa.

**Per F il punto iniziale del backbone è il punto di controllo E già addestrato**:
questa dipendenza va preservata nei manifesti e nell'analisi.

**Il ricampionamento resta incrociato**, con dodici inizializzazioni e tre
partizioni, mantenendo l'appaiamento fra strategie.

---

## 8. Costo: misurare il sistema, non i soli pesi aggiornati

**Per P, F e R** si misurano:

| | |
|---|---|
| tempo di calcolo del descrittore | |
| tempo di adattamento o riaddestramento | |
| memoria di picco | |
| numero di parametri aggiornati | |
| numero di aggiornamenti dell'ottimizzatore | |
| **dimensione dello stato memorizzato per nuovo sensore** | |
| latenza di inferenza | |

**Si separano:**

- le **ventiquattro ore di acquisizione**, comuni alle strategie operative;
- il **tempo computazionale successivo** necessario a rendere disponibile la
  configurazione.

### L'istante di disponibilità

La valutazione sulle stesse celle future si esegue **offline a partire da $t_1$**,
con modelli costruiti esclusivamente con informazioni disponibili entro $t_1$.

**Ma il confronto informativo non è il servizio reale:**

> **F e R diventano utilizzabili soltanto dopo il completamento del rispettivo
> aggiornamento.**

Si registra quindi

$$t_{\text{ready}} = t_1 + T_{\text{preparazione/aggiornamento}}$$

> **Non si afferma che tutte le strategie siano operative esattamente a $t_1$.** La
> valutazione offline a parità di celle misura **la qualità**; il tempo di
> disponibilità misura **il costo operativo**. **In questa campagna restano due
> risultati separati.**

**Per A** si riporta il costo di addestramento come **informazione diagnostica**,
non come costo operativo dell'inserimento.

> **Non è corretto affermare che F, se economico, elimini automaticamente la
> ragione di P**: P potrebbe conservare vantaggi nella gestione dello stato e nella
> validazione. **Ma questi vantaggi vanno dimostrati, non presunti.**

### La stima computazionale

**Il costo non si ottiene moltiplicando cinque bracci per quaranta secondi:**

| | |
|---|---|
| **E** | è un addestramento preparatorio |
| **F** | è un adattamento, non un addestramento completo |
| **R** | usa un corpus differente |
| **A** | include più nodi |

**Si riportano separatamente**: tempo complessivo a calendario, tempi per
esecuzione, parallelismo.

> La durata effettiva della conferma — **2,2 ore per 216 esecuzioni, mediana 40
> secondi** — sostituisce correttamente la vecchia stima di settantadue ore, **ma
> non determina automaticamente quella di questa campagna.**

---

## 8bis. Ordine di costruzione e artefatto canonico

**Si conserva l'ordine storico** — `start`, `blocchi`, identità, `stat`, `e1`,
`e2` — **e l'allineamento resta affidato all'artefatto canonico.**

| | |
|---|---|
| **un solo meccanismo** | esplicito, verificabile e gia' approvato |
| gli stati iniziali storici | restano **riproducibili** |
| la correzione | **non dipende dalla struttura interna** dei fornitori |

**Il costo è che l'allineamento avviene dopo la costruzione.** È accettabile
purché sia obbligatorio e verificato.

### Il controllo bloccante, registrato

Per ogni esecuzione di **C, P, E, A e R**:

| | |
|---|---|
| 1 | l'artefatto canonico **è stato caricato** |
| 2 | i moduli comuni **coincidono esattamente** con esso |
| 3 | entrambe le condizioni sono verificate **prima della creazione
      dell'ottimizzatore** |

**F dichiara esplicitamente il non caricamento**, e ne registra la ragione: parte
dal punto di controllo E già addestrato.

> **Se il controllo non è registrato nel manifesto, l'esecuzione non è
> conforme.**

### Riproducibilità degli stati iniziali dei bracci nuovi

**E, A ed R non condividono i quarantacinque artefatti storici**, sicché i loro
stati iniziali possono essere generati con una convenzione nuova.

> **Un eventuale cambio di ordine di costruzione deve però essere una decisione
> esplicita e versionata**, applicata a tutti i bracci nuovi e **mai mescolata
> all'interno della stessa campagna**.

**Per questa campagna la convenzione è unica: ordine storico per tutti e cinque i
bracci.**

## 9. Controlli bloccanti, prima del lancio

| | |
|---|---|
| 1 | **chiavi di prova identiche** fra tutti i bracci |
| 2 | statiche, calendario e maschere **comuni** |
| 3 | **nessun descrittore storico né embedding specifico in C** |
| 4 | **P congelato** dopo l'addestramento iniziale |
| 5 | **F derivato da E, mai da A** |
| 6 | in F cambiano **soltanto i nuovi embedding** |
| 7 | **R non usa storia dei nuovi nodi anteriore a $t_0$** |
| 8 | **A marcato esplicitamente come privilegiato** |
| 9 | pesi della metrica **comuni**, stimati sull'addestramento iniziale |
| 10 | **nessuna contaminazione** nella normalizzazione |
| 11 | stato iniziale e **provenienza dei punti di controllo** registrati |
| 12 | **costo misurato anche per P**, non soltanto per F e R |
| 13 | **artefatto canonico caricato e verificato** prima dell'ottimizzatore, per C, P, E, A, R |
| 14 | **F dichiara il non caricamento** e la sua ragione |

> **Gli artefatti di normalizzazione esistenti si riusano soltanto se corrispondono
> esattamente a nodi, periodo e schema della nuova configurazione.**

---

## 10. Le decisioni, come approvate

| domanda | decisione |
|---|---|
| quanti bracci | **cinque**: aggiunto **R**, il riaddestramento realmente disponibile |
| inizializzazioni | **dodici** |
| che cosa aggiorna F | **solo il nuovo embedding** |
| denominatore instabile | recupero **secondario**; nessun filtraggio opportunistico; **differenze assolute sempre principali** |
| costo | tempo, memoria, stato e parametri aggiornati, **per tutte le strategie operative** |
| LEGACY | **non necessaria** in questa campagna |

---

## 11. Ordine delle attività

| attività | stato |
|---|---|
| cinque bracci e loro funzione | **approvati** |
| dodici inizializzazioni nuove, semi 201…212 | **approvate** |
| differenze di perdita principali, recupero secondario | **approvati** |
| calendario | **da inserire con i timestamp effettivi** |
| griglia e procedura di selezione di F | **approvate** |
| regola di arresto e corpus di R | **resi espliciti**, §5 e §5bis |
| **campagna di prova** | **NON ancora da avviare** |

### Il prossimo passo, e solo quello

**Congelare il calendario e il protocollo di selezione**, poi eseguire **la sola
selezione di F sulla validazione**.

**L'esito da riportare** è una tabella delle sei configurazioni **per città**, con:

- il criterio di scelta applicato;
- la **numerosità degli esempi adattabili**;
- i **costi**.

**Dopo la scelta, le tre configurazioni cittadine si registrano e si congelano.**

> Non occorre cambiare le domande scientifiche: **occorre completare queste
> specifiche operative prima della prova.**

---

## 12. Che cosa questa campagna risponde

> **Non soltanto se il descrittore predice bene, ma se rappresenta un'alternativa
> conveniente alle strategie di aggiornamento del sistema.**

È la domanda centrale del paper.

---

## Registro delle versioni

| | |
|---|---|
| disegno del raccordo | 5, concluso |
| addendum 1, 2 | conclusi |
| bozza 1 dell'inserimento | quattro bracci, superata |
| versione 2 | cinque bracci, R aggiunto, F da E, recupero secondario |
| versione 2.1 | calendario, selezione di F, ammissibilità, arresto, corpus, disponibilità |
| **versione 2.2** | **questo documento**: ordine storico conservato, artefatto canonico come meccanismo unico, controllo bloccante registrato |
| _2.1_ | _sostituita_: calendario, selezione di F eseguibile, ammissibilità degli esempi, regola di arresto comune, corpus di R, istante di disponibilità |
