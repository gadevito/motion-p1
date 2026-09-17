# Specifica del descrittore — BASE ed EXTENDED

Versione di schema **1.0**. Deriva dalle decisioni approvate dal revisore senior.
Ogni modifica incrementa la versione e va registrata in coda.

---

## 0. I tre oggetti

$$s_i(t,L) \quad\text{statistiche comportamentali}$$
$$q_i(t,L) \quad\text{informazioni sulla disponibilità}$$
$$z_i(t,L) = g_\theta\bigl(s_i(t,L),\, q_i(t,L)\bigr) \quad\text{vettore di identità}$$

**L'anagrafica non entra in nessuno dei tre.** È un ingresso separato $a_i$ della
previsione, disponibile a tutte le strategie.

$g_\theta$ è un encoder a due strati con uscita a **otto dimensioni**, con la
medesima specifica nel compito denso e nell'inserimento. I pesi possono essere
addestrati separatamente nei due protocolli; **durante ogni valutazione induttiva
restano congelati.**

---

## 1. La finestra

$$W(t, L, t_0) = (t-L,\, t] \;\cap\; [t_0,\, t]$$

con $t_0$ **istante di installazione del sensore**. Il limite inferiore è applicato
dal componente, non dal chiamante.

| $L$ | significato |
|---|---|
| $0$ | finestra vuota: nessuna statistica stimabile |
| $-1$ | intera storia dall'installazione |
| $>0$ | ultimi $L$ passi, troncati a $t_0$ |

$L_{\max} = 2688$ passi, ossia ventotto giorni a quindici minuti: è la durata
massima ammessa da E1 e fissa la dimensione del buffer.

> **«Incrementale» non significa memoria costante in $L$.** Le statistiche additive
> su finestra mobile richiedono di sottrarre i campioni che escono. La prima
> implementazione conserva un buffer limitato a $L_{\max}$, senza approssimazioni.

---

## 2. Canali e convenzioni comuni

**Canali**: $r$ fattore di congestione, $f$ flusso, $o$ occupazione.

**Standardizzazione**: ogni statistica di livello è centrata e ridotta con media e
deviazione del **canale sul periodo di addestramento della rete iniziale**, non
sulla finestra. I parametri sono costanti del componente e versionati con lo schema.

**Valore convenzionale**: una statistica non stimabile assume **zero dopo
standardizzazione** — ossia la media di addestramento — e la componente di $q$
corrispondente vale **zero**. Non si usa uno zero ambiguo: $q$ dice quali parti di
$s$ siano affidabili.

**Convenzione numerica del bersaglio.** Il tipo e le regole di confronto fanno
parte della definizione implementativa, non sono un dettaglio.

| | |
|---|---|
| tipo di `speed` e `ff` nell'artefatto | `float32` |
| tipo della divisione | `float64` |
| tipo in cui si valutano le soglie | **`float32`** |
| regole | critica `r < 0,4`; intermedia `0,4 ≤ r < 0,8`; libera `r ≥ 0,8` |
| ordine | validazione → divisione → controllo di finitezza → troncamento → classificazione |
| troncamento | `[0; 1,5]`, applicato solo alle celle valide |

**Le differenze fra le due convenzioni numeriche, pur molto piccole, modificano
l'assegnazione di alcune celle prossime alle soglie**: 0,248 per mille su Madrid,
0,415 su Londra e 0,0175 su Melbourne. Su Madrid e Londra sono **alcuni decimi di
per mille**.

Vanno conservati come prove di regressione alcuni di quei casi, insieme a valori
immediatamente sotto, uguali e sopra ciascuna soglia. **La versione delle librerie
numeriche va registrata**, poiché il comportamento ai bordi può dipenderne.

**Ordine delle operazioni sul rapporto**: si validano gli operandi, si divide solo
dove sono validi, si verifica che il rapporto sia finito, e **solo allora** si
tronca. Il riferimento è valido se finito e positivo; la velocità se finita e non
negativa — **lo zero è ammesso**, poiché rappresenta traffico fermo. Una cella non
valida vale `nan` e non zero, che sarebbe indistinguibile da un rapporto
legittimamente nullo.

**Tolleranza sulle variazioni**: $\tau = 0{,}005$ in unità di $r$, fissata prima
degli esperimenti. Le variazioni in modulo inferiori a $\tau$ non contano né come
incremento né come decremento.

---

## 3. Statistiche comportamentali $s$

### Gruppo 1 — livello e dispersione (6 componenti, BASE ed EXTENDED)

Per ciascun canale $c \in \{r, f, o\}$, sulle osservazioni valide della finestra:

$$\mu_c = \frac{S^{(1)}_c}{n_c}, \qquad
\sigma_c = \sqrt{\max\!\left(\frac{S^{(2)}_c}{n_c} - \mu_c^2,\; 0\right)}$$

**Normalizzazione**: con media $\mu_x$ e scala $\sigma_x$ del canale stimate sul
periodo di addestramento,

$$\text{media normalizzata} = \frac{m - \mu_x}{\sigma_x}, \qquad
\text{deviazione normalizzata} = \frac{v}{\sigma_x}$$

**La media del canale non si sottrae dalla deviazione.** Una standardizzazione
propria della caratteristica «deviazione» richiederebbe media e scala sue, stimate
sul periodo ammesso.

**Denominatore**: $n_c$, il numero di osservazioni valide **di quel canale**, non
la lunghezza della finestra.

**Non stimabile**: $\mu_c$ se $n_c = 0$; $\sigma_c$ se $n_c < 2$.

### Gruppo 2 — profilo orario (8 componenti, BASE ed EXTENDED)

Otto bande di tre ore **dell'ora locale**, non ottavi della finestra osservata:

$$b(u) = \left\lfloor \frac{\text{ora locale di } u}{3} \right\rfloor \in \{0,\dots,7\}$$

$$\text{prof}_b = \frac{S^{(1)}_{r,b}}{n_{r,b}}$$

**Non stimabile**: se $n_{r,b} = 0$. Una finestra di quattro ore ne osserva al più
due: le altre sei sono non stimabili, e $q$ deve dirlo.

> Una copertura complessiva elevata **non garantisce** che tutte le bande siano
> rappresentate: la disponibilità è per banda.

### Gruppo 3 — frequenze di classe (3 componenti, solo EXTENDED)

$$\text{freq}_k = \frac{n_k}{n_{\text{cls}}}, \qquad k \in \{1,2,3\}$$

**Denominatore**: $n_{\text{cls}}$, le celle con classe assegnata nella finestra.

Le tre sommano a uno: la terza è ridondante e si conserva per leggibilità.

**Non stimabile**: se $n_{\text{cls}} = 0$. Non standardizzate, essendo già in
$[0,1]$.

### Gruppo 4 — autocorrelazione a un passo (1 componente, solo EXTENDED)

Sulle **coppie consecutive valide**: entrambi gli estremi validi **e distanti
esattamente un passo temporale**. Una coppia a cavallo di un'interruzione non è
consecutiva e non entra.

Grandezze da mantenere: $m$, $A=\sum x_s$, $B=\sum x_{s+1}$, $AA=\sum x_s^2$,
$BB=\sum x_{s+1}^2$, $AB=\sum x_s x_{s+1}$.

$$\rho = \frac{AB/m - (A/m)(B/m)}
{\sqrt{AA/m - (A/m)^2}\;\sqrt{BB/m - (B/m)^2}}$$

**Non stimabile**: se $m < 2$, o se una delle due varianze è nulla — serie costante.

### Gruppo 5 — incrementi e decrementi (2 componenti, solo EXTENDED)

Sulle medesime coppie consecutive valide, con $d = x_{s+1} - x_s$:

$$\text{inc} = \frac{|\{d > \tau\}|}{m}, \qquad
\text{dec} = \frac{|\{d < -\tau\}|}{m}$$

**Denominatore**: $m$, il numero di **coppie consecutive valide**, non le
osservazioni.

Le variazioni in modulo inferiori a $\tau$ non entrano in nessuna delle due:
$\text{inc} + \text{dec} \le 1$, e il complemento è la quota di quiete.

**Non stimabile**: se $m = 0$.

---

## 4. Informazioni sulla disponibilità $q$

| gruppo | componenti | definizione |
|---|---|---|
| durata | 3 | nominale richiesta, effettiva dall'installazione, numero di osservazioni valide — tutte come $\log(1+x)/\log(1+L_{\max})$ |
| copertura per canale | 3 | $n_c / |W|$ per $c \in \{r,f,o\}$ |
| disponibilità per banda | 8 | $n_{r,b} / |W_b|$, dove $|W_b|$ sono i passi della finestra che cadono nella banda |
| copertura delle coppie | 1 | $m / \max(|W|-1,\,1)$ |

**Totale 15 componenti.** Tutte in $[0,1]$ salvo le tre di durata, anch'esse
normalizzate a $[0,1]$.

**La durata nominale e quella effettiva differiscono** per un sensore installato da
meno di $L$: la prima dice quanta storia è stata richiesta, la seconda quanta ne
esiste.

---

## 4bis. Schemi per sorgente

**I canali dipendono dalla sorgente, e lo schema è dichiarato.** Il componente non
decide quali caratteristiche rimuovere osservando se un canale sia costante: **un
canale realmente misurato può legittimamente esserlo.**

| sorgente | canali | nota |
|---|---|---|
| **traffic4cast** | `r`, `volume_class` | l'occupazione è **assente dalla sorgente**, non mancante |
| **gomo** | `r`, `conteggio`, `occupazione` | `r` vi è **ricostruito**, non misurato |

`volume_class` è una classe discretizzata a tre livelli — 1, 3, 5 — con zero dove il
dato manca. **Non condivide il nome con il conteggio veicolare**, perché non è la
stessa grandezza: `media_volume_class` e `dev_volume_class` sono sommari della
**codifica**, non stime del flusso, e la loro interpretazione dipende dai livelli.
La standardizzazione non le rende fisicamente equivalenti.

L'invocazione dichiara entrambe:

    source_schema      = traffic4cast | gomo
    descriptor_variant = LEGACY | BASE-CORRECTED | EXTENDED

## 5. Le tre varianti

| | GO-MO | **Traffic4cast** | funzione |
|---|---|---|---|
| **LEGACY** | 14 + 2 = **16** | 14 + 2 = **16** | riproduzione, **non esercizio** |
| **BASE-CORRECTED** | 14 + 15 = **29** | 12 + 14 = **26** | base della campagna |
| **EXTENDED** | 20 + 15 = **35** | 18 + 14 = **32** | configurazione principale |

**Su Traffic4cast si rimuovono tre componenti**: `media_occupazione`,
`dev_occupazione` e `copertura_occupazione`.

**LEGACY resta a 16 su entrambe le sorgenti**, poiché la sua funzione è la fedeltà
alle funzioni storiche, non la coerenza con il dato.

**La differenza fra LEGACY e BASE-CORRECTED su Traffic4cast è di 10 componenti e
640 pesi** nel primo strato a 64 unità.

**LEGACY su Traffic4cast ha 16 componenti nominali e 14 variabili**: `media_occupazione`
e `dev_occupazione` sono costanti a zero, poiché il canale è assente dalla sorgente.
Si conservano — eliminarle cambierebbe parametrizzazione e inizializzazione — e la
normalizzazione usa la convenzione storica `std + 1e-6`, **dichiarata** come gestione
di un canale costante.

**Il contratto distingue** una scala accidentalmente nulla, che è un errore, da un
canale costante esplicitamente dichiarato, che è ammesso e registrato.

**BASE-CORRECTED ed EXTENDED condividono il blocco di disponibilità per intero.**
Se cambiassero anche quelle, il confronto fra le due misurerebbe il beneficio
complessivo della rappresentazione anziché quello delle **sei sole statistiche
aggiuntive**: frequenze delle tre classi, autocorrelazione, quote di incremento e
decremento.

**LEGACY riproduce le convenzioni storiche**, comprese quelle che la specifica
altrove corregge:

| | LEGACY | BASE-CORRECTED |
|---|---|---|
| denominatore | protetto a uno — **mai zero** | numerosità vera |
| canale senza osservazioni | media zero, indistinguibile | **non stimabile** |
| fascia mai osservata | riempita con la media globale | **non stimabile** |
| non stimabili dichiarati | **nessuno** | elenco esplicito |

> Il denominatore protetto e l'imputazione con la media globale **non sono difetti
> in sé**: sono una protezione aritmetica e una scelta metodologica. Lo diventano
> senza maschera, perché il risultato è presentato come statistica osservata senza
> indicarne l'indisponibilità.

**LEGACY serve al raccordo con i risultati pubblicati e non entra nella campagna.**

---

## 6. Interfaccia

```
ingest_observations(sensor_id, observations)

update_representation(sensor_id, as_of_time, history_duration)
    -> { behavioral_statistics,      # s
         availability_information,   # q
         schema_version,
         window_start, window_end }

encode_representation(statistics, availability)
    -> identity_vector               # z, otto dimensioni
```

**L'anagrafica resta fuori da `update_representation`.** Il componente conosce
l'istante di installazione e applica da sé il limite inferiore della finestra.

---

## 7. Criterio di completamento di questo passo

| | requisito | stato |
|---|---|---|
| 1 | elenco esatto delle caratteristiche di BASE ed EXTENDED | **questo documento** |
| 2 | formule, denominatori, trattamento dei mancanti | **questo documento** |
| 3 | un'unica implementazione richiamata da entrambi gli esperimenti | da fare |
| 4 | confronto fra calcolo incrementale e ricalcolo diretto | da fare |
| 5 | prove su finestra vuota, serie costante, interruzioni, cambio di fascia, uscita dalla finestra | da fare |
| 6 | tracciabilità della configurazione originaria a 45 statistiche | **da fare, prioritario** |

> **Il requisito 6 precede gli altri.** L'audit ha trovato 45 statistiche e una rete
> a due strati, mentre il deliverable descrive in alcuni passaggi sedici statistiche
> e una proiezione lineare. Va registrato quale configurazione ha prodotto ciascun
> risultato: **le percentuali della Tabella 54 non sono attribuibili al nuovo
> descrittore né trasferibili al paper.**

---

## 8. Questioni aperte, da verificare prima dell'implementazione

**L'anagrafica campo per campo.** «Nota prima dell'installazione» vale per il limite
legale e per il numero di corsie, che sono informazione esterna. **Non
necessariamente per `max_speed` e `max_capacity`**, se ricavate dall'intera serie
del sensore: in tal caso sono storia mascherata da attributo statico, e non possono
stare in $a_i$.

**Il preprocessing a monte.** La causalità delle somme cumulate non basta se la
normalizzazione o l'imputazione a monte usano l'intera serie. Va verificato
separatamente, ed è parte dell'audit C.

---

## Versione di implementazione, distinta da quella di schema

**Lo schema elenca nomi e ordine delle caratteristiche; l'implementazione dice come
sono calcolate.** Una correzione che non tocchi l'elenco lascia lo schema invariato
e incrementa la versione di implementazione.

| implementazione | correzione |
|---|---|
| 1.0 | prima stesura |
| 1.1 | soglie in precisione singola; ordine delle operazioni sul rapporto; accumulatori traslati |
| 1.2 | schemi per sorgente; deviazione scalata e non centrata |
| **1.3** | **`copertura_coppie` spostata nel blocco condiviso** |

### La correzione 1.3

`copertura_coppie` era calcolata **solo dentro il ramo `EXTENDED`**, mentre
appartiene al blocco di disponibilità condiviso: su BASE-CORRECTED restava
**costantemente zero**.

> Le due varianti **non condividevano davvero le informazioni di disponibilità**,
> che è il requisito posto perché il confronto isolasse le statistiche
> comportamentali. Una delle quattordici componenti era nulla in una variante e
> corretta nell'altra.

**Due verifiche aggiunte**: che la componente sia calcolata e non lasciata a zero, e
che **tutte e quattordici** le componenti coincidano fra BASE-CORRECTED ed EXTENDED,
confrontate una per una sulle medesime istanze.

**Lo schema resta alla 1.2**: nomi, ordine e dimensioni non cambiano — 26 e 32
componenti su Traffic4cast. **Il disegno del raccordo resta alla versione 4**: è una
correzione implementativa, non una modifica del protocollo.

**I manifesti delle nuove esecuzioni riportano entrambe le versioni**, `schema_version`
e `implementation_version`, sicché l'esecuzione è identificabile senza ambiguità.

## Due precisazioni da conservare

**L'uguaglianza delle quattordici componenti riguarda BASE-CORRECTED ed EXTENDED.**
Il raccordo con LEGACY continua a valutare **il pacchetto di trattamento esplicito
della disponibilità**: LEGACY ne ha due, non quattordici.

**Le componenti sono quantità numeriche normalizzate, non indicatori binari.**
Sui casi reali nessuna assume soltanto zero e uno: `copertura_r` varia fra 0,22 e
0,66, le disponibilità di banda fra 0 e 1, `copertura_coppie` fra 0,05 e 0,54.

## Registro delle versioni

| versione | data | modifica |
|---|---|---|
| 1.0 | — | prima stesura, decisioni del revisore senior recepite |
| 1.1 | — | precisione di valutazione delle soglie e ordine delle operazioni sul rapporto |
| 1.4 | — | contratto di normalizzazione bloccante; canale costante dichiarato; dimensione nominale distinta da quella variabile |
| 1.3 | — | schemi per sorgente: Traffic4cast senza occupazione, `volume_class` distinto dal conteggio |
| 1.2 | — | tre varianti LEGACY, BASE-CORRECTED ed EXTENDED; disponibilità condivisa fra le ultime due; deviazione scalata e non centrata; fasce confermate sull'ora locale |
