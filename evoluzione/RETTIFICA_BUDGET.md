# Rettifica — il budget di addestramento delle campagne

**Emendamento al protocollo.** Non cancella né sostituisce i documenti
congelati: vi si collega.

---

## 1. Che cosa il protocollo diceva, e che cosa il codice faceva

Il protocollo dichiarava **«35 epoche massime, lotto 32, pazienza 8»**.

Il ciclo eseguito è:

```python
for ep in range(35):
    idx = g.choice(istanti, size=32, replace=False)
    L.backward(); opt.step()        # UN aggiornamento
    # validazione, dopo OGNI aggiornamento
```

> **Le esecuzioni utilizzavano al massimo 35 aggiornamenti dell'ottimizzatore,
> ciascuno su 32 istanti campionati, con arresto anticipato valutato a ogni
> aggiornamento. La denominazione «epoche» riportata nel protocollo non
> corrispondeva all'implementazione.**

**«Pazienza 8» sono otto verifiche dopo aggiornamenti**, non otto passate: circa
il **23% del budget totale**.

---

## 2. Lo scarto fra intenzione e implementazione, quantificato

| | |
|---|---|
| origini di addestramento | **7.308** |
| aggiornamenti per **passata nominale**, ⌈7308/32⌉ | **229** |
| aggiornamenti eseguiti | **35** |
| **quota di UNA passata** | **15,3%** |
| origini distinte viste in 35 aggiornamenti | 1.050 su 7.308 |
| **copertura delle origini** | **14,4%** |
| istanze nodo–origine per aggiornamento | 20.160 |
| bersagli validi per aggiornamento, mediana | 66.480 |

**Le 35 esecuzioni vedevano il 14,4% delle origini disponibili**, ciascuna
quasi sempre una volta sola: 1.050 distinte su 1.120 estratte.

> **I conteggi 32 × K sono esposizioni nominali nodo–origine per aggiornamento**,
> non istanze distinte né celle che contribuiscono alla perdita. Il numero di
> aggiornamenti e il numero di esempi elaborati vanno **entrambi** riportati.

---

## 3. Un secondo fatto, emerso dallo stesso ciclo

**La validazione usa sempre i primi 32 istanti del periodo**, mai altri:

```python
Xv, Yv, Mv = _lotto(x, D["classe"], ist_ck[:cfg["lotto"]], nodi_ck)
```

**Non è un campione della validazione: è una finestra fissa.** Il punto di
controllo è selezionato su **32 istanti su circa 1.560** disponibili, cioè il
2% del periodo.

**Vale per tutte le campagne**, incluse le tre congelate del raccordo.

> Non era stato richiesto di verificarlo, ed emerge dall'audit del budget.
> **Riguarda la selezione del punto di controllo**, quindi va deciso insieme al
> budget e non dopo.

---

## 4. Che cosa resta valido delle campagne precedenti

**Le differenze numeriche restano risultati delle esecuzioni effettuate**, e le
campagne non si cancellano né si sostituiscono.

**Vanno però interpretate come confronti sotto quel budget di aggiornamento:**

| campagna | che cosa ha verificato | condizionata a |
|---|---|---|
| raccordo, appaiamento | differenze fra LEGACY e BASE-CORRECTED | 35 aggiornamenti |
| **conferma, dodici semi** | **robustezza rispetto all'inizializzazione ENTRO quel budget** | 35 aggiornamenti |
| E, 108 punti di controllo | i punti di partenza di F | 35 aggiornamenti |
| **selezione di F** | la configurazione di adattamento | **quei punti E** |

> **La conferma con dodici semi ha verificato la robustezza rispetto
> all'inizializzazione entro quel budget, non rispetto al regime di
> addestramento originariamente inteso.**

**Se cambia il training di E, la configurazione di F non si trasferisce
automaticamente al nuovo punto di controllo.**

### Un'ipotesi, non una spiegazione

**È possibile che parte della sensibilità all'inizializzazione osservata dipenda
da un addestramento molto breve.** È un'ipotesi da verificare, **non una
spiegazione dimostrata**: 35 aggiornamenti usano ciascuno molti nodi e quattro
orizzonti, e non equivalgono a 35 esempi indipendenti.

---

## 5. Il budget dei bracci addestrati da zero

**Principio fissato:**

> **A parità di configurazione, i bracci addestrati da zero devono avere lo
> stesso budget massimo di aggiornamenti e lo stesso numero nominale di finestre
> nodo–origine per aggiornamento.**

Quindi il riferimento è **32 × K_iniziali = 20.160** quando i nodi iniziali sono
630 — **non 24.480** solo perché la rete di R è più grande.

**R campiona uniformemente i nodi della rete ampliata, ma entro quel budget.**

**Vale anche per A**: il riferimento privilegiato differisce per **informazione
disponibile**, e non deve ricevere automaticamente più esempi a ogni
aggiornamento.

> **Non è ancora un'autorizzazione a usare 35 aggiornamenti.** Il massimo va
> definito dopo la verifica di adeguatezza.

---

## 6. Nomenclatura del nuovo protocollo

La parola «epoca» si abbandona, o riceve una definizione computabile e distinta:

| | |
|---|---|
| `max_optimizer_updates` | il massimo di aggiornamenti |
| `validation_every_updates` | ogni quanti si valuta |
| `early_stopping_patience_checks` | verifiche senza miglioramento |
| `node_origin_windows_per_update` | finestre nodo–origine per aggiornamento |
| `sampling_policy` | uniforme sugli istanti, o uniforme per nodo |

**Il numero di aggiornamenti e il numero di esempi elaborati vanno entrambi
riportati**: nessuno dei due, da solo, descrive il budget.

---

## 7. Stato

| | |
|---|---|
| **fase 3** | **SOSPESA** |
| audit del ciclo | **eseguito**, rapporto in `audit_ciclo.json` |
| rettifica delle campagne | **questo documento** |
| prova di adeguatezza | **da definire**, su sola validazione |
| nuovo budget comune | **da fissare** dopo la prova |
| punti di controllo e selezioni da rigenerare | **da valutare** dopo il budget |

**Non si rigenerano** dati, maschere o descrittori già collaudati. **Non si rifà
automaticamente il raccordo.**
