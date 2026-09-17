# Protocollo di conferma — dodici inizializzazioni nuove

**Fissato prima delle esecuzioni.** Addendum 2 al disegno congelato alla versione
5. Metodo, dati, partizioni, iperparametri e regola di appaiamento **invariati**.

---

## 0. Che cosa questa campagna verifica

> **La robustezza rispetto a nuove inizializzazioni**, non la generalizzazione a
> nuovi dati né a nuovi sistemi.

La domanda: *la non inferiorità osservata con l'appaiamento controllato si
mantiene su inizializzazioni non utilizzate per scoprire e diagnosticare il
problema?*

---

## 1. Perimetro

| | |
|---|---|
| contesti | Madrid, Londra, Melbourne |
| partizioni dei nodi | le stesse tre, semi **1000, 1037, 1074** |
| **inizializzazioni** | **dodici nuove**, semi **101 … 112** |
| varianti | LEGACY 16, BASE-CORRECTED 26 |
| **addestramenti** | 3 × 3 × 12 × 2 = **216** |

**Costo stimato circa 72 ore**, dall'ordine di grandezza osservato — una stima,
non un impegno.

> **Dodici inizializzazioni sono una scelta di budget e precisione, non una
> garanzia di potenza.** Rispetto a tre possono dimezzare l'errore standard della
> componente indipendente fra inizializzazioni, a parità delle altre condizioni;
> **non dimezzano necessariamente l'incertezza totale.**

**Il numero resta dodici anche se il risultato è non conclusivo.** Nessuna
estensione decisa sulla base dell'esito.

### I semi, e una collisione da dichiarare

La sequenza consecutiva è ammissibile: non serve cercare numeri apparentemente più
casuali.

**Verificato sui manifesti di tutte le campagne**: i soli semi registrati sono
7, 18 e 29 per l'inizializzazione e 1000, 1037, 1074 per la partizione, con
settantadue esecuzioni ciascuno. **Nessuno dei dodici compare, in alcun ruolo.**

Il valore 101 compare come seme di partizione nel codice delle prove tecniche
`prova_reale.py` e `prova_mancanti.py`, che **non scrivono manifesti nel registro
della campagna e non producono valutazioni predittive**. Si registra per
completezza: qui è un seme di inizializzazione, e i due ruoli non si toccano.

---

## 2. Appaiamento, invariato

Esattamente la politica della campagna appaiata:

1. costruzione dei due stati iniziali per ciascun seme;
2. **encoder proprio** di ciascuna variante;
3. **ramo statico e teste di BASE-CORRECTED copiati** dallo stato iniziale LEGACY;
4. salvataggio degli stati completi e delle impronte;
5. generatori dell'addestramento e ordine dei lotti secondo il contratto
   collaudato.

> **Non si introduce contemporaneamente una politica di inizializzazione per
> modulo**: sarebbe un altro cambiamento, e il risultato non sarebbe attribuibile.

---

## 3. Analisi primaria: i soli dodici semi nuovi

$$\widehat{\delta}_{\text{new}} = \frac{1}{3}\sum_{p=1}^{3}\frac{1}{12}
\sum_{s=1}^{12} 100 \cdot
\frac{\mathcal{L}_{\text{CORRECTED},p,s} - \mathcal{L}_{\text{LEGACY},p,s}}
{\mathcal{L}_{\text{LEGACY},p,s}}$$

**Invariati**: definizione delle perdite, media sui quattro orizzonti prima del
rapporto, condizione primaria a ventiquattro ore, popolazione e periodo, pesi di
classe, selezione del punto di controllo, margine dell'1%.

### Ricampionamento

**Incrociato**, fissato qui:

- tre partizioni con reinserimento;
- **dodici inizializzazioni con reinserimento**;
- **la stessa lista di inizializzazioni per tutte le partizioni** della replica;
- nodi secondo la procedura dichiarata, molteplicità preservate;
- campioni identici fra le varianti.

**20.000 repliche**, generatore **1000**, identificato qui. **Nessuna scelta del
generatore in funzione dei limiti ottenuti.**

Gli intervalli restano **condizionati al periodo di prova** e ai limiti già
dichiarati del ricampionamento dei nodi.

---

## 4. Che cosa conta come conferma

**La conferma è ottenuta soltanto se, in ciascuna delle tre città:**

$$U_{95}(\delta_{\text{new}}) < +1\%$$

| esito | conclusione |
|---|---|
| non inferiorità in **tutte e tre** | **conferma nel perimetro esaminato** |
| non inferiorità in una o due | evidenza circoscritta; **conferma non raggiunta** |
| in nessuna città | conferma non raggiunta |
| deterioramento oltre il margine in almeno una | evidenza **contraria** alla non inferiorità in quel contesto |

> **Il mancato raggiungimento della conferma non equivale a dimostrare
> inferiorità.**

**Sulla molteplicità.** Per l'affermazione congiunta «non inferiore in tutte e
tre», richiedere il superamento di **tutti** i test è un criterio di
intersezione: **non si applica Bonferroni** a questo verdetto congiunto. La
proprietà **non si estende** a eventuali famiglie di confronti secondari.

**Equivalenza**: verifica aggiuntiva entro ±1%, **non condizione necessaria**
della conferma.

**Metriche secondarie**: complementari. Non modificano il verdetto sulla wCE, ma
**possono impedire di descriverlo come accettabilità operativa generale**.

---

## 5. Tre blocchi distinti, nessuno cancellato

| blocco | natura |
|---|---|
| campagna di sensibilità, già congelata | tre semi, **sviluppo e diagnosi** |
| **conferma sui dodici semi nuovi** | **analisi primaria** |
| analisi combinata sui quindici semi | secondaria, **se eseguita** |

> **L'analisi combinata non può salvare una conferma fallita sui nuovi semi.**

Va dichiarato che **i primi tre semi sono stati utilizzati per diagnosticare e
sviluppare la procedura di appaiamento**, e non sono quindi neutrali.

---

## 6. Fallimenti e arresto

Regola già approvata, invariata:

- **massimo tre tentativi** per problemi tecnici recuperabili;
- **nessuna ripetizione selettiva** dei fallimenti del metodo;
- **nessun seme sostitutivo**;
- **nessuna imputazione** delle coppie mancanti.

Se mancano coppie, l'analisi dei completati resta **condizionata a quel
sottoinsieme**: il verdetto non si attribuisce al disegno completo.

> **La campagna termina dopo il piano fissato, non quando un risultato diventa
> significativo.**

---

## 7. Controlli prima del lancio

| | |
|---|---|
| 1 | i dodici semi **non sono stati usati** per valutazioni predittive |
| 2 | gli stati iniziali dei dodici semi sono **preparati e salvati** |
| 3 | i cinque controlli dell'appaiamento passano **su tutti e dodici** |
| 4 | la campagna scrive in una **cartella propria**, senza toccare le precedenti |
| 5 | l'ordine delle esecuzioni è **salvato prima** del lancio |

---

## Registro delle versioni

| | |
|---|---|
| disegno del raccordo | **5**, invariato |
| addendum 1 | appaiamento dell'inizializzazione |
| **addendum 2** | **questo protocollo** |
| schema del descrittore | 1.2, invariato |
| implementazione dell'estrattore | 1.3, invariata |
