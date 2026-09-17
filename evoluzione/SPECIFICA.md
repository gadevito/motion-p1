# Campagna JSS — evoluzione di un sistema predittivo a sensori

Specifica operativa derivata dalle istruzioni del revisore senior.
Documento di lavoro: si aggiorna a ogni fase con gli esiti e con le decisioni prese.

---

## 0. Ipotesi e domande

**Ipotesi.** Una rappresentazione delle entità generata dalle osservazioni mediante
una funzione condivisa riduce la dipendenza del componente ML dalla popolazione di
addestramento, consentendo espansioni successive senza aggiornamento dei pesi e con
un compromesso misurabile fra qualità predittiva e costo di aggiornamento.

| | domanda | esperimento |
|---|---|---|
| **RQ1** | Quanto costa, in termini predittivi, integrare nuovi sensori senza riaddestrare? | E1 |
| **RQ2** | La soluzione continua a funzionare dopo più espansioni successive? | E2 |
| **RQ3** | L'inserimento modifica le prestazioni dei sensori già operativi? | E3 |
| **RQ4** | Quali costi di aggiornamento elimina e quali di gestione introduce? | E4 |
| **RQ5** | In quali condizioni la storia non basta e l'aggiornamento torna necessario? | E5 |

> **«Semplifica la manutenzione» è una conclusione da sostenere, non una premessa.**

---

## 1. Le quattro strategie

| | gestione del nuovo sensore | aggiornamento dei pesi |
|---|---|---|
| **S0** | ingressi recenti, calendario, statiche — nessuna identità storica | nessuno |
| **S1** | calcola e aggiorna il descrittore osservabile — **la proposta** | nessuno |
| **S2** | aggiunge un embedding al nuovo nodo e lo ottimizza, backbone congelato | solo nuovi nodi |
| **S3** | riaddestra sulla rete ampliata | tutti |

**Regola di equità.** Alla data di aggiornamento S1, S2 e S3 devono avere accesso
alla **stessa storia effettivamente disponibile**. S2 e S3 possono usare le
osservazioni passate come esempi supervisionati purché i bersagli siano maturati;
non possono usare i dati futuri che S1 sta prevedendo.

**Primo confronto a parità di backbone**, con grafo fisso o senza grafo:
l'adiacenza adattiva introduce differenze ulteriori e va isolata.

---

## 2. Audit preliminare — precede ogni esecuzione

| | controllo | criterio di superamento |
|---|---|---|
| **A** | un solo descrittore nei due esperimenti | il descrittore del compito denso e quello dell'inserimento sono il medesimo oggetto |
| **B** | nessun parametro nascosto per sensore | dopo un'espansione i parametri appresi sono invariati; i descrittori memorizzati possono crescere e vanno contati |
| **C** | causalità della storia | nessun descrittore usa osservazioni successive a `t`; per un sensore installato a `t₀`, nessuna osservazione locale anteriore a `t₀` |
| **D** | congelamento completo | hash dello stato del modello identico prima e dopo l'inserimento: pesi, buffer, statistiche di normalizzazione |
| **E** | confrontabilità | popolazioni, pesi di classe, margini, periodi e orizzonti uniformi; ricampionamento che **conserva le molteplicità** dei blocchi |

**Da cercare in B**: embedding liberi per nodo, vettori `E1`/`E2` dell'adiacenza
adattiva, bias o teste predittive per sensore, stato di normalizzazione indicizzato
sul nodo.

**Prodotto**: suite di test automatici più specifica della disponibilità delle
informazioni. Non è il contributo, ne rende verificabile l'implementazione.

---

## 3. Gli esperimenti

### E1 — qualità dell'inserimento senza riaddestramento

Per città: addestrare sui nodi iniziali, tenere **completamente escluso** un insieme
di nodi nuovi, simularne l'installazione, rendere disponibili progressivamente
**4 ore, 24 ore, 7 giorni, 28 giorni**. Valutare su previsioni **successive** al
periodo usato per i descrittori o per i pesi. Ripetere su più giorni e fasce orarie.

**Due letture, entrambe necessarie:**
- *controllata*: a parità di nodo e istante, finestra dinamica recente identica,
  varia solo la storia del descrittore — isola il valore dell'identità osservabile;
- *operativa*: descrittore e ingressi recenti usano solo osservazioni del nuovo
  sensore — misura la fase iniziale reale.

**Misure**: wCE, precisione media sulla classe critica, precisione e richiamo a
soglia scelta sulla validazione, differenza rispetto a S3, differenza fra storia
breve e lunga sugli stessi nodi.

**I sensori veterani non sono il riferimento**: possono essere più facili o più
difficili di quelli nuovi.

**Non è necessario che S1 vinca**: deve emergere un compromesso credibile.

### E2 — espansioni successive *(il più importante da aggiungere)*

Rete iniziale al 50%, poi **50 → 60 → 70 → 80 → 100%**. Le percentuali sono una
configurazione, non un requisito.

A ogni espansione: registrare i nuovi sensori, accumulare storia prefissata,
applicare S0–S3, valutare **prima** dell'espansione successiva, conservare stato e
costi. **Per S1 i pesi restano quelli della rete iniziale per l'intera sequenza.**

**Due modalità di crescita**: casuale, e **per area o corridoio** — la seconda è più
impegnativa e più vicina a una campagna reale.

**Misure per fase**: qualità sui nuovi nodi, sulle coorti precedenti, sull'intera
rete; numero di aggiornamenti; tempo e risorse cumulative; memoria e latenza.

**Figura**: asse orizzontale la fase; tre pannelli — qualità dei nuovi, qualità
degli esistenti, costo cumulativo.

### E3 — regressioni sui sensori già operativi

**Pesi congelati non garantiscono predizioni invariate**: un nuovo nodo cambia
grafo, vicinati e normalizzazione della propagazione.

Per ogni espansione confrontare, sullo stesso intervallo futuro e valutando **solo
sui nodi già operativi**: sistema senza inserimento contro sistema dopo
l'inserimento.

**Ablazione per i modelli a grafo**: aggiornamento che mantiene invariati i
collegamenti fra nodi esistenti, contro ricostruzione dell'intero grafo. La prima
non elimina necessariamente gli effetti — anche nuovi collegamenti modificano le
aggregazioni — e proprio per questo va misurata.

**Misure**: variazione media di perdita sui nodi esistenti, sua distribuzione per
nodo, quota di nodi peggiorati oltre un margine, variazione delle predizioni,
prestazioni delle coorti più vecchie dopo più espansioni.

**Per un modello interamente per-nodo l'invarianza è un controllo positivo, non una
scoperta.** L'interesse è nelle configurazioni con dipendenze fra nodi.

### E4 — costo end-to-end

| componente | misura |
|---|---|
| raccolta iniziale | tempo di **osservazione** richiesto |
| costruzione descrittore | tempo CPU e memoria |
| aggiornamento descrittore | costo per osservazione o lotto |
| aggiornamento grafo | tempo e memoria |
| adattamento o riaddestramento | calcolo e memoria di picco |
| validazione del candidato | tempo e dati richiesti |
| inferenza | latenza mediana e al 95°, portata |
| stato persistente | dimensione del modello e dei dati per sensore |

**Distinguere attesa da calcolo.** Due tempi operativi: alla prima previsione, e
alla previsione che **soddisfa un criterio di qualità** fissato sulla validazione.

**Scalabilità**: ripetere per diverse dimensioni di rete e di lotto. Un modello di
dimensione costante può avere costo grafico quadratico o stato storico crescente.

**Per quantili e statistiche non aggiornabili esattamente**, dichiarare se si
conserva la finestra grezza, si ricalcola periodicamente, o si approssima — e in
quest'ultimo caso misurarne l'effetto predittivo.

**Il vecchio modello continua a servire durante l'aggiornamento**: non attribuire
downtime al riaddestramento. Riportare costo del candidato, tempo alla sua
disponibilità, qualità nel frattempo, costo dell'esecuzione parallela.

### E5 — robustezza e condizioni di aggiornamento

**A. osservazioni mancanti** — perdite casuali e interruzioni consecutive sui nuovi
sensori, percentuali e durate **fissate prima della campagna**. Confronto S0–S3 a
parità di osservabilità. Misure: degradazione, tempo per un descrittore utile,
utilità degli indicatori di copertura, recupero dopo l'interruzione.

**B. cambiamenti di comportamento** — periodi cronologicamente distinti. Per S1:
descrittore fissato dopo il periodo iniziale, aggiornato su tutta la storia,
aggiornato a finestra mobile. Pesi congelati. Confronto con aggiornamento periodico
del modello.

**Criterio di aggiornamento**: regola definita **sulla validazione** che segnali la
necessità di aggiornare — errore osservato a bersagli maturi, copertura
insufficiente, cambiamento delle statistiche. **Non deve usare il futuro né essere
scelta sul test.**

> Il risultato interessante non è «non serve mai riaddestrare», ma **in quali
> condizioni si può evitare o posticipare**.

---

## 4. Il componente software

**Non quattro script che producono tabelle.** Un componente con interfaccia comune:

```
register_sensor(metadata)
ingest_observations(sensor_id, observations)
update_representation(sensor_id)
predict(sensor_id, horizon)
update_model(policy)
```

Dietro la stessa interfaccia, S0–S3.

**Registro automatico**: versione del modello e del grafo, sensori disponibili,
periodo osservativo, operazioni eseguite, tempi, risorse, esiti dei controlli.

Serve un **artefatto eseguibile che riproduca il processo di evoluzione**, non solo
l'addestramento. Niente interfaccia grafica né deployment.

**Non affermare riduzioni dello sforzo degli sviluppatori** senza uno studio
dedicato: si misurano le operazioni richieste dalla pipeline.

---

## 5. Generalizzabilità

Almeno **due configurazioni software significativamente diverse**: un predittore
per-nodo e uno con scambio su grafo. Verifica se la soluzione sia riutilizzabile e
se le regressioni dipendano dalle relazioni fra entità.

Un secondo dominio rafforzerebbe, ma non è obbligatorio. Restando sul traffico, le
conclusioni si formulano **per sistemi predittivi a sensori di quel tipo**, non per
tutto il software ML.

**Le tre città sono repliche di contesto, non diversità di implementazione.**

---

## 6. Fasi e priorità

| fase | contenuto |
|---|---|
| **1 — validità tecnica** | descrittore unico, audit, prova ridotta su una città, confronto S0–S3 |
| **2 — evidenza principale** | sulle tre città: inserimento a diverse durate, espansioni successive, regressioni, costo end-to-end |
| **3 — limiti** | dati mancanti, descrittori in condizioni non stazionarie, portabilità su un secondo backbone |

**Punto di partenza**: tre partizioni dei nodi e tre inizializzazioni per
partizione, **con semi separati**.

**Salvare le predizioni per nodo e istante**, confrontare le strategie in modo
appaiato, riportare per città. **Milioni di celle non sono milioni di repliche
indipendenti.**

---

## 7. Fuori perimetro per questo articolo

Meteo, validazione flusso/occupazione, analisi delle corsie, spaziatura ottimale,
nuova classifica di architetture. Sono risultati utili ma **non rispondono alla
domanda sull'evoluzione**.

---

## 8. Stato

| | descrizione | stato |
|---|---|---|
| audit A | descrittore unico | **da fare** |
| audit B | parametri per sensore | **da fare** |
| audit C | causalità | **da fare** |
| audit D | congelamento | **da fare** |
| audit E | confrontabilità | **da fare** |
| componente | interfaccia comune S0–S3 | da progettare |
| E1–E5 | | non avviati |
