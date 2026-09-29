# Sintesi — tabella decisionale, matrice delle conclusioni, sinossi

---

# A. Tabella decisionale

| | dati richiesti dal nuovo nodo | stato aggiornato | acquisizione | costo d'inserimento | qualità contro C | persistenza | limiti principali | ruolo |
|---|---|---|---|---|---|---|---|---|
| **C** | finestra recente, 3 h | **nulla** | **0** | **0 s** | riferimento | stabile: 0,884 → 0,888 | nessuna personalizzazione | **operativo** |
| **P-frozen** | + prime 24 h | descrittore fisso | 24 h | ~1 s (descrittore) | peggio a Madrid e Melbourne, pari a Londra | **degrada**: 0,875 → 0,904 | descrittore invecchia | operativo |
| **P-refresh** | + ultime 24 h a ogni origine | descrittore, ogni previsione | 24 h | ~1 s per origine | meglio a Madrid e Londra, non a Melbourne; **peggio su PEMS04** | degrada meno | sviluppato **post-hoc** | operativo, non confermato |
| **F₀** | nessuno oltre la finestra | nulla, embedding medio | 0 | 0 s | **peggio ovunque**: +0,050 ÷ +0,078 | non valutata | — | **diagnostico** |
| **F** | + prime 24 h | embedding del nodo nuovo | 24 h | **15,6 s per l'intero gruppo** di 135 o 90 nodi | meglio a Madrid, pari a Melbourne, peggio a Londra | degrada: 0,862 → 0,903 | beneficio non uniforme | **operativo** |
| **R** | + prime 24 h | **intero modello** | 24 h | **38,7 min** | **peggio ovunque**: +0,13 | degrada: 0,969 → 1,023 | esposizione ~790× per origine nuova; selezione cieca ai nodi nuovi | operativo, sconsigliato |
| **A** | intera storia pregressa | intero modello | — | — | meglio ovunque: −0,037 | stabile: 0,850 → 0,852 | **informazione non disponibile all'installazione** | **diagnostico** |

Costi dal solo **campione isolato** — tre città, partizione 1000, semi 201–203, un processo, macchina libera. I tempi delle esecuzioni concorrenti non dimostrano che un braccio sia più veloce.

---

# B. Matrice delle conclusioni

### B1. Trasferire un'identità appresa a un'entità nuova ha un costo

| | |
|---|---|
| **affermazione** | applicare ai nodi nuovi il modello E con embedding inizializzato alla **media** degli embedding appresi dà prestazioni **peggiori** del modello condiviso C |
| confronto | **F₀ − C** |
| perimetro | 3 città, 135/90 nodi nuovi, 12 semi × 3 partizioni, ~1.460 origini dopo $t_1$ |
| stima | +0,073 [+0,058, +0,089] · +0,050 [+0,038, +0,063] · +0,078 [+0,053, +0,102] |
| statuto | **controllo post-hoc**, non confermativo |
| non separato | l'embedding medio può essere poco rappresentativo in una rete non lineare: **non distingue** «training con identità» da «assegnazione media» |
| conseguenza | **è un problema di trasferimento**: un modello efficace con identità apprese non ha automaticamente un comportamento adeguato per una nuova entità |

### B2. L'adattamento locale recupera quel costo, non lo supera di molto

| | |
|---|---|
| **affermazione** | l'ottimizzazione dell'embedding sulle prime 24 ore migliora nettamente rispetto all'identità predefinita in due città su tre |
| confronto | **F − F₀**, con $L_F - L_C = (L_F - L_{F_0}) + (L_{F_0} - L_C)$ |
| stima | −0,084 [−0,106, −0,063] · −0,010 [−0,029, **+0,007**] · −0,090 [−0,113, −0,065] |
| statuto | controllo post-hoc |
| conseguenza | **gran parte del beneficio compensa lo svantaggio iniziale**: il vantaggio finale su C è piccolo (−0,011 a Madrid), non distinguibile da zero a Melbourne, e **negativo a Londra** (+0,040). Le 24 ore sono utili per adattare E in due città, **ma F non è uniformemente preferibile a C** |

### B3. Il descrittore statistico non è robusto né trasferibile

| | |
|---|---|
| **affermazione** | il descrittore esaminato **non offre un vantaggio robusto e trasferibile** rispetto al predittore senza descrittore; aggiornarlo migliora la strategia congelata ma **non ne garantisce la competitività** |
| confronti | P−C (fase 3, pianificato) · P-refresh−P-frozen e P-refresh−C (post-hoc) · gli stessi su PEMS04 (replica esterna) |
| stima, urbano | P−C: +0,010 · −0,002 · +0,016. P-refresh−C: −0,010 · −0,008 · +0,009 |
| stima, PEMS04 aggregato | $\Delta_F = -0{,}020$ [−0,040, −0,002] · $\Delta_C = +0{,}029$ **[+0,007, +0,054]** |
| statuto | **criterio congiunto NON soddisfatto** sul dataset esterno |
| conseguenza | **l'informazione viene sfruttata in alcune condizioni** — P-refresh batte P-frozen ovunque — ma su PEMS04 C è migliore, con intervallo che esclude lo zero da entrambi i lati |

### B4. Il riaddestramento completo, così definito, non conviene

| | |
|---|---|
| **affermazione** | R peggiora rispetto al non intervenire, al costo più alto |
| stima | +0,13 contro C, uniforme sulle tre città; 38,7 min contro 15,6 s di F |
| meccanismo **misurato** | campionamento uniforme per nodo con budget fisso → **790 ripetizioni per origine nuova** contro 9,2 delle iniziali; la selezione su V-full della **rete iniziale** non può rilevarne il sovraadattamento |
| conseguenza | **non rappresenta ogni riaddestramento**: è il riaddestramento con campionamento bilanciato per nodo e selezione sulla rete iniziale |

### B5. La persistenza urbana non si replica sul periodo esterno breve

| | |
|---|---|
| **affermazione** | l'andamento temporale osservato sui dati urbani **non trova conferma netta** negli ~8 giorni di PEMS04 |
| conseguenza | beneficio iniziale e beneficio persistente sono **proprietà diverse**; non si forzano i due dataset dentro un unico meccanismo |

### Statuto dell'evidenza

| livello | che cosa comprende |
|---|---|
| **pianificato** | fase 3: C, P, A, R, F; costi; fasce temporali |
| **rianalisi** | ricampionamento dei nodi, previsto dal protocollo e **assente** nell'analisi originale |
| **post-hoc** | P-refresh, F₀ |
| **replica esterna** | PEMS04, condizionata al **preprocessing già imputato** e a un **riferimento di velocità diverso** |

---

# C. Sinossi

## Problema

Integrare **nuove entità** in sistemi predittivi già operativi. Un sensore installato oggi non ha storia: il modello in esercizio deve trattarlo senza che il servizio si degradi, e chi lo gestisce deve decidere **se e che cosa aggiornare**.

## Lacuna

La letteratura mostra che l'inserimento senza riaddestramento è possibile. Restano distinte e non separate tre questioni: **quanto sia utile personalizzare** una nuova entità, **quanto costi trasferirle** un'identità appresa, e **quali aggiornamenti recuperino davvero** quel costo.

## Disegno

Cinque strategie — nessuna identità, descrittore osservabile, adattamento dell'embedding, riaddestramento completo, riferimento privilegiato — su tre città, 12 inizializzazioni, 3 partizioni, con calendario d'inserimento congelato, budget e selezione dichiarati, costi misurati in isolamento. Più due controlli: **F₀**, che separa l'adattamento dal modello di partenza, e una **replica esterna** su PEMS04 della sola politica di aggiornamento.

## Risultati

**Il modello condiviso è un riferimento difficile da superare.** Nessuna strategia lo batte uniformemente.

**Trasferire un'identità appresa costa**: con l'embedding medio, il modello addestrato con identità è peggiore del modello senza, in tutte e tre le città.

**L'adattamento locale recupera quel costo**, a 15,6 secondi per l'intero gruppo di nuovi sensori, ma il vantaggio residuo su C è piccolo e non uniforme.

**Il descrittore statistico non è competitivo in modo robusto**, e la replica esterna lo conferma: aggiornarlo aiuta, ma non basta.

**Il riaddestramento completo, con campionamento bilanciato per nodo, peggiora** — e il meccanismo è misurato, non ipotizzato.

**Beneficio iniziale e persistenza sono proprietà diverse**: chi parte meglio non resta meglio.

## Implicazioni

La decisione operativa non è «quale modello è migliore», ma **quando conviene non intervenire**. I dati dicono: spesso. E quando si interviene, **aggiornare pochi parametri locali costa 150 volte meno che riaddestrare**, con esito migliore.

## Limiti

Un solo episodio d'inserimento per città; budget finito e non dimostrato convergente; R rappresenta una politica di campionamento specifica; la replica esterna è su un rilascio già imputato con un riferimento di velocità diverso; P-refresh e F₀ sono post-hoc.

## Rispetto a MoGERNN

MoGERNN mostra l'inserimento senza riaddestramento con estrapolazione spaziale dai vicini. **Qui non c'è grafo**, l'identità viene dalla storia breve del sensore, e la domanda è un'altra: **non se si possa inserire senza riaddestrare, ma quale aggiornamento convenga**. Il contributo è la **separazione dei meccanismi** — trasferimento, adattamento, freschezza dello stato — con costi e persistenza misurati.

> **Resta da valutare se questa conoscenza sia abbastanza generale e distinta** da giustificare la pubblicazione. Gli audit la rendono credibile; non ne sostituiscono la novità.
