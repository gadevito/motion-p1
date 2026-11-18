# Paper 4 — Piano di rafforzamento da discutere

Bozza per discussione. Non autorizza nuovi esperimenti e non modifica risultati o protocolli già congelati.

## Obiettivo scientifico

Studiare quando e quanto le letture dinamiche dei sensori osservati migliorino la previsione nei siti senza storico, oltre alle regolarità di calendario e alle informazioni statiche disponibili.

Il contributo candidato è la separazione controllata di queste fonti informative, verificata con un modello dedicato, un addestramento adeguato e una replica esterna. Il disegno deve produrre conclusioni informative anche se il beneficio spaziale emerge, varia tra condizioni o rimane incerto.

## 1. Verificare il contributo prima della campagna

Completare il confronto con i lavori più vicini attraverso i testi integrali. La matrice bibliografica deve distinguere previsione futura, disponibilità dello storico target, informazioni utilizzate, baseline di calendario, controlli sull’addestramento e confronti tra componenti.

Prima degli addestramenti estesi, i coautori devono approvare:

- la lacuna documentata nella letteratura;
- il confronto sperimentale che la affronta;
- il valore aggiunto atteso rispetto ai precedenti.

Se un lavoro contiene già il confronto in condizioni equivalenti, rivalutare il contributo della replica o il disegno prima di sostenere il costo della campagna.

## 2. Decidere l’outcome prima di scegliere il dataset esterno

Nelle città originali il riferimento di velocità libera proviene dal provider. Nei dataset di spire, un riferimento calcolato dallo storico del sito nascosto non è disponibile operativamente.

**Proposta preferita:** utilizzare nella replica esterna la velocità normalizzata per il limite, scegliendo un dataset con limiti verificabili per sito.

Questa scelta costituisce una replica del confronto tra fonti informative su un outcome diverso, non una replica esatta del fattore originale: il rapporto velocità/limite non ha lo stesso significato del rapporto velocità/free-flow (in autostrada il free-flow supera spesso il limite, in ambito urbano gli è inferiore). Le soglie di classe per il nuovo outcome vanno quindi ridefinite e giustificate prima degli esperimenti, e non ereditate dalle soglie 0,8/0,4 del fattore originale.

**Alternativa:** utilizzare un riferimento operativo stimato soltanto dagli observed-training, con una regola comune a tutti i modelli. Questa strada richiede una verifica aggiuntiva della stima del riferimento.

Un riferimento ricavato dallo storico del sito nascosto può essere eventualmente usato per definire un outcome offline, ma tale uso deve essere dichiarato e separato dagli input disponibili al modello. Non risolve automaticamente il problema operativo.

La scelta tra queste strade precede la graduatoria dei dataset.

## 3. Selezionare e congelare il dataset esterno

Valutare i candidati sulla base di:

- disponibilità del riferimento richiesto dall’outcome scelto;
- velocità, timestamp, identificatori e topologia verificabili;
- durata e copertura sufficienti;
- indipendenza dai dati già analizzati e dallo sviluppo del modello;
- accesso e riproducibilità.

NDW e WebTRIS sono candidati da verificare, non ancora selezionati. Per WebTRIS non assumere un limite uniforme senza riscontro per sito. M30 resta una riserva e richiede lo stesso controllo sul riferimento, oltre alla dichiarazione del precedente utilizzo.

La selezione non utilizza prestazioni dei modelli. Congelare dati, partizioni, impronte e motivazione della scelta prima della valutazione.

## 4. A0 — Verificare implementazione e addestramento

Prima della campagna:

- verificare maschere, normalizzazioni, decoder e assenza di accesso allo storico dei target nascosti;
- distinguere validation-hidden, utilizzabile per la selezione autorizzata, e test-hidden;
- verificare con controlli sintetici che il modello sappia utilizzare un segnale spaziale informativo;
- fissare criteri di adeguatezza dell’addestramento e gestione dei fallimenti.

Il modello dedicato proposto resta MoGERNN, subordinatamente all’audit dell’adattamento. La ricorrenza autoregressiva viene mantenuta; il teacher forcing viene disabilitato coerentemente nei bracci regressivi proposti.

Un controllo fallito o un addestramento insufficiente impediscono di interpretare un risultato negativo come evidenza di scarso beneficio.

## 5. A1 — Rafforzare la classificazione originale

Confrontare G0 e G1, rispettivamente senza e con scambio spaziale, con e senza coordinate aggiuntive.

Mantenere tre città, cinque split e copertura primaria del 20%. Prevedere quattro configurazioni di sviluppo per ciascun braccio e split, con tuning annidato e inizializzazione finale distinta.

La classificazione conserva la famiglia di modelli originale. Viene rafforzata attraverso tuning, coordinate e replica, ma non acquisisce una validazione su una seconda architettura dedicata.

## 6. A2/A3 — Confronto regressivo e ruolo degli input

A2 confronta il modello dedicato, G0-reg, G1-reg e calendario su uno schema informativo comune. La metrica primaria proposta è MAE; RMSE è secondaria.

A3 incrocia nel modello dedicato:

| | Senza coordinate aggiuntive | Con coordinate aggiuntive |
|---|---|---|
| Senza letture dinamiche in input | Controllo di base | Apporto delle coordinate |
| Con letture dinamiche in input | Apporto dinamico | Apporto combinato |

La topologia rimane disponibile in tutte le celle. Il confronto riguarda quindi **coordinate aggiuntive × letture dinamiche**, non presenza o assenza di ogni informazione spaziale.

Ogni cella viene riaddestrata con la stessa politica di selezione. Il modello completo senza coordinate viene condiviso tra A2 e A3 quando tutte le specifiche coincidono.

Stimare direttamente il beneficio dinamico nelle due condizioni e la loro interazione. Non dedurre un’interazione dal fatto che un confronto sia significativo e l’altro no.

La conclusione multi-architettura riguarda la regressione con input comuni. Non spiega causalmente il precedente risultato classificatorio.

## 7. A4 — Replica esterna di entrambi i task

Replicare classificazione e regressione, incluso il confronto tra le quattro celle del dedicato.

Trasferire gli iperparametri mediante una regola definita usando soltanto lo sviluppo storico. Non effettuare una nuova ricerca sul dataset esterno.

Selezionare il checkpoint sulla validation esterna mediante una regola prespecificata. Questo è riaddestramento con adattamento controllato, non trasferimento integrale senza adattamento.

Congelare prima del test criteri di arresto, gestione dell’inadeguatezza e analisi. L’eventuale trasferimento senza riaddestramento resta secondario e non necessario al nucleo.

## 8. Budget e assegnazione delle macchine

| Componente | Fit neurali previsti |
|---|---:|
| A1 classificazione | 300 |
| Quattro celle del modello dedicato | 300 |
| G0-reg e G1-reg | 150 |
| Replica esterna, entrambi i task | 50 |
| **Totale** | **800** |

Il conteggio comprende sviluppo e fit finali, ma esclude controlli tecnici, benchmark, eventuali ripetizioni registrate e analisi. Le baseline tabellari sono contabilizzate separatamente.

Proposta di assegnazione:

- **Mac:** classificazione A1 e classificazione esterna.
- **Spark GPU:** intero confronto regressivo, comprese le baseline G0-reg/G1-reg e la replica esterna.

Mettere soltanto il dedicato su Spark e le baseline regressive sul Mac confonderebbe architettura e backend nei confronti diretti di A2.

Con questa assegnazione Spark porta 480 fit su 800, compresi tutti quelli del modello dedicato, che sono i più lenti. E13-pre deve misurare proprio quel carico (memoria e tempo per aggiornamento su CUDA, con il carico del Mac misurato in parallelo); le stime preliminari non costituiscono un calendario garantito.

Se necessario, ridurre prima degli esiti la griglia da quattro a due configurazioni porta il totale a **500 fit**, conservando bracci, città e split. La riduzione si applica a entrambe le macchine e a tutte le famiglie allo stesso modo, non alla sola Spark o al solo dedicato: non ridurre preventivamente l'addestramento del dedicato compromettendo il controllo di adeguatezza.

## 9. Analisi e interpretazione

Prespecificare contrasti, dipendenze spaziali e temporali, sovrapposizione degli split e correzione della molteplicità. La proposta comprende 24 contrasti principali sui dati storici e otto nella replica esterna.

I dati storici restano già conosciuti; una nuova preregistrazione non li rende incontaminati.

Una conclusione di beneficio trascurabile richiede precisione e una soglia giustificata. In assenza di tale soglia, riportare grandezza e incertezza senza dichiarare equivalenza. Intervalli ampi o addestramento inadeguato producono un esito inconclusivo.

## 10. Perimetro e tracciabilità

Il forecasting costituisce il nucleo. Placement e misurazione locale restano evidenze complementari, senza graduatorie sul valore locale o remoto dei sensori. Nuovi esperimenti di placement richiedono una decisione separata.

Prima dei lanci, seguire il ciclo concordato di revisione, firma, commit, tag e push. Congelare anche l’analisi prima dei fit finali. Conservare risultati storici e run superati; registrare deviazioni e correzioni senza riscrivere i record congelati.

Deposito proposto nuovamente a DEP-01, previa conferma della disponibilità, con nuove ricevute per i documenti firmati.

## Decisioni richieste ai coautori

1. Accettare la regressione come sede principale del nuovo confronto multi-architettura.
2. Scegliere l’outcome esterno prima del dataset.
3. Confermare il confronto coordinate aggiuntive × letture dinamiche.
4. Approvare l’assegnazione proposta e il budget, subordinatamente al microbenchmark.
5. Ratificare il contributo dopo la verifica bibliografica.

La doppia revisione avversariale ha sostenuto la struttura del piano dopo le correzioni metodologiche e narrative. Le ultime proposte su outcome e assegnazione delle macchine richiedono ancora ratifica e verifica operativa. Nessun esperimento è stato avviato.