# Rettifica documentale — popolazione della campagna di evoluzione

**Emendamento al protocollo.** Non sostituisce né riscrive i documenti
congelati: vi si collega.

---

## 1. Lo scostamento

| | popolazione **dichiarata** nel deliverable | popolazione **effettivamente usata** |
|---|---|---|
| Madrid | 828 | **900** |
| Londra | 774 | **900** |
| Melbourne | 587 | **594** |

**Non è una scelta precedentemente formalizzata**: è uno scostamento documentale
emerso dalla riconciliazione, e si registra come tale.

### Il nome corretto

> **Popolazione selezionata prima del filtro di aggancio al grafo.**

**Non «popolazione intera della sorgente»**: il rilascio sorgente contiene molti
più segmenti, e quelli qui usati sono già il risultato di una selezione a monte.

---

## 2. Perché il filtro non si applica

Il deliverable escludeva i nodi non agganciati al grafo, perché il suo backbone
usava lo **scambio spaziale** e un nodo isolato non vi partecipava.

**Il predittore per-nodo non usa il grafo.** Ogni sensore è elaborato
indipendentemente — è la proprietà verificata dall'audit B — sicché il filtro
non ha ragione d'essere.

---

## 3. La scelta precede i risultati

**L'assenza del filtro risale alla costruzione dell'estrattore**, prima di
qualunque campagna: `_carica` legge tutti i nodi della sorgente e `_partizioni`
li divide 70/15/15.

**Nessun risultato è stato consultato** per adottarla: non è mai stata una
decisione presa, ma un'assenza mai dichiarata.

---

## 4. Esito dei controlli di conformità

**324 verifiche per impronta** — tre insiemi per ciascuno dei 108 punti di
controllo E — più le partizioni e i manifesti della selezione di F.

| | esito |
|---|---|
| punti E contro partizioni | **coincidono tutti** |
| selezione di F contro partizione di validazione | coincide |
| sovrapposizioni fra addestramento, validazione e prova | **nessuna** |
| copertura: le tre partizioni sommano alla popolazione | **verificata** |

**Le fasi sono coerenti fra loro.** L'unica discrepanza era col deliverable.

### Le impronte congelate

| città | partizione | addestramento | validazione | prova |
|---|---|---|---|---|
| Madrid, Londra | p0 | `f7a44c934cd72ec5` | `08eb1e92b10527c2` | `7e5eaa6e92ce59ea` |
| | p1 | `c62efa50896bf162` | `73232d2b33f2c31d` | `545396b17c4ad7dc` |
| | p2 | `b8c045457dfaaf33` | `92e8c588a17adef6` | `9d22170240ee63de` |
| Melbourne | p0 | `1178f19d5908e6ed` | `c3e826c4d1b40c9a` | `f3e9ea021d56c456` |
| | p1 | `271243208f5a52f4` | `e0256aa1cdd89512` | `505140d04ffac9ff` |
| | p2 | `795b82d4a829eb8f` | `b58f187c274e9637` | `6a52f57febbef48a` |

> **Madrid e Londra condividono le impronte** perché hanno lo stesso numero di
> nodi e lo stesso seme di partizione: gli **indici** coincidono, i sensori no.

**Le fasi C, P, A, R e F useranno queste partizioni, già verificate.**

---

## 5. Origini ammissibili per nodo

**Verificate per ciascun nodo**, non sull'unione:

| città | minimo | mediana | massimo | media | senza esempi |
|---|---|---|---|---|---|
| Madrid | 56 | 78 | 78 | 76,0 | **0** |
| **Londra** | **26** | **63** | 78 | **60,7** | **0** |
| Melbourne | 57 | 77 | 78 | 75,9 | **0** |

**Su Londra un nodo ha 26 origini su 78.** Nessun nodo è privo di esempi in
alcun contesto, sicché il caso di fallback non si presenta in questa campagna.

---

## 6. Confrontabilità

**I risultati delle campagne di evoluzione restano confrontabili fra loro.**

> **Non sono direttamente confrontabili, cella per cella, con quelli del
> deliverable** — anche per questa differenza di popolazione, oltre che per
> backbone, protocollo e metrica.

---

## 7. Vincolo per la futura variante con grafo

Quando si aggiungerà lo scambio spaziale, **il filtro del deliverable non va
reintrodotto in silenzio**. Due vie:

| | |
|---|---|
| 1 | costruire un grafo **sulla popolazione corrente**, gestendo esplicitamente i nodi isolati |
| 2 | definire un **sottoinsieme comune** e valutare entrambi i backbone su quello |

**Decisione futura**: non blocca questa campagna.

---

## Registro

| | |
|---|---|
| documenti congelati | **non sovrascritti**, collegati a questa rettifica |
| protocollo corrente | aggiornato con la popolazione approvata |
| artefatti | **mantenuti**: nessuna rigenerazione |
| training preparatori | **non ripetuti** |
| selezione di F | **non ripetuta** |
