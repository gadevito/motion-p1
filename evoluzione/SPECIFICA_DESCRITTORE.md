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

**Tolleranza sulle variazioni**: $\tau = 0{,}005$ in unità di $r$, fissata prima
degli esperimenti. Le variazioni in modulo inferiori a $\tau$ non contano né come
incremento né come decremento.

---

## 3. Statistiche comportamentali $s$

### Gruppo 1 — livello e dispersione (6 componenti, BASE ed EXTENDED)

Per ciascun canale $c \in \{r, f, o\}$, sulle osservazioni valide della finestra:

$$\mu_c = \frac{S^{(1)}_c}{n_c}, \qquad
\sigma_c = \sqrt{\max\!\left(\frac{S^{(2)}_c}{n_c} - \mu_c^2,\; 0\right)}$$

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

## 5. Le due varianti

| | $s$ | $q$ | totale |
|---|---|---|---|
| **BASE** | gruppi 1–2 → **14** | durata nominale, copertura di $r$ → **2** | **16** |
| **EXTENDED** | gruppi 1–5 → **20** | tutte → **15** | **35** |

**BASE riproduce la rappresentazione attuale dell'inserimento** in modalità `both`:
sei fra medie e deviazioni, otto bande, quota di validi, codice di durata. Si
conserva come ablazione.

**EXTENDED è la configurazione principale.** Il confronto fra le due stabilirà se
le aggiunte siano utili: **è una domanda sperimentale, non una premessa.**

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

## Registro delle versioni

| versione | data | modifica |
|---|---|---|
| 1.0 | — | prima stesura, decisioni del revisore senior recepite |
