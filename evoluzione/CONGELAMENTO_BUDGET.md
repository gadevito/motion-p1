# Congelamento — adeguatezza e sensibilità del budget di addestramento

**Verifica chiusa, senza ulteriori estensioni.**

---

## 1. Perimetro

**La conclusione è circoscritta** a tre città, **una partizione pilota** (seme
1000) e **tre inizializzazioni** (semi 301, 302, 303), su C, P ed E.

**Riguarda la rete iniziale.** Non anticipa l'ordinamento delle strategie sui
sensori nuovi, che resta l'oggetto dell'esperimento principale.

---

## 2. Il budget storico era insufficiente

| | da 35 a 2.290 aggiornamenti |
|---|---|
| guadagno su V-full | **+7 ÷ +16%** nelle nove combinazioni |
| plateau raggiunto | **0 su 9** |
| minimo entro 35 aggiornamenti | **0 su 27** traiettorie |

> **Le campagne precedenti confrontavano i modelli sotto un budget di 35
> aggiornamenti, significativamente inferiore a quello necessario per ottenere
> le prestazioni osservate nella prova. L'estensione del training modifica
> anche le distanze fra famiglie.**

A 35 aggiornamenti C ed E erano **numericamente prossimi** — non
«indistinguibili»: due medie vicine non lo dimostrano.

---

## 3. Formulazione approvata della sensibilità

> **Nel perimetro pilota, l'estensione da 2.290 a 4.580 aggiornamenti produce
> miglioramenti contenuti rispetto a quelli osservati passando da 35 a 2.290.
> L'ordinamento medio E < P < C rimane invariato nelle tre città. Le differenze
> assolute fra famiglie cambiano in misura limitata, mentre il confronto P–E,
> caratterizzato dai divari più piccoli, mostra una maggiore sensibilità
> relativa. Il budget di 2.290 aggiornamenti viene pertanto mantenuto per la
> campagna principale, senza assumerne la convergenza.**

### L'ordinamento vale anche per ciascuna inizializzazione

**E < P < C in 9 combinazioni seme–città su 9**, al budget principale — non
soltanto sulle medie.

---

## 4. Tre precisazioni

### Riproduzione

**Riproduzione esatta delle metriche registrate ai punti di controllo**: 27
traiettorie su 27 a scarto zero, fino a 2.290.

**Non identità bit a bit dell'intero stato**: i piloti originari conservavano
soltanto le curve, non la traiettoria parametrica.

### Punto finale contro punto selezionato

| | che cosa misura |
|---|---|
| valore **finale** | la perdita all'aggiornamento 2.290 o 4.580 |
| **minimo** selezionato su V-full | il migliore fra i punti disponibili |

**Sul valore finale** Melbourne P peggiora lievemente, da 0,79451 a 0,79466.

**Sul minimo selezionato nessuna combinazione peggiora** — 0 su 9, come deve:
estendendo l'insieme, i punti precedenti restano disponibili.

| città | C | P | E |
|---|---|---|---|
| Madrid | +0,40% | +0,61% | +0,57% |
| Londra | +0,13% | +0,51% | +0,57% |
| Melbourne | +0,47% | +0,27% | +0,62% |

*Guadagno del minimo su V-full, da ≤ 2.290 a ≤ 4.580.*

### Unità delle differenze

**Le variazioni si riportano in unità di wCE**, con eventuale variazione
relativa a denominatore esplicito.

| coppia | divario a 2.290 | a 4.580 | variazione assoluta | relativa |
|---|---|---|---|---|
| Melbourne P–E | 0,0041 | 0,0061 | **+0,0019 wCE** | +46,6% del divario |
| Londra C–P | 0,0257 | 0,0296 | +0,0039 wCE | +15,2% del divario |
| Madrid C–E | 0,0439 | 0,0446 | +0,0008 wCE | +1,7% del divario |

> **Il 46,6% descrive la variazione di un divario piccolo, non un
> deterioramento del 46,6% del modello.**

---

## 5. Decisione operativa

| | |
|---|---|
| **`max_optimizer_updates`** | **2.290** |
| punti di controllo | **35, 229, 458, 687, 916, 1145, 1374, 1603, 1832, 2061, 2290** |
| selezione | **validazione completa**, a parità il punto precedente |
| arresto anticipato | **nessuno** nella campagna principale |
| budget ed esposizioni | **registrati per ogni braccio** |
| costo riportato | quello dell'**intera procedura**, non fino al punto selezionato |

---

## 6. Che cosa ne consegue

**I 108 punti di controllo E vanno rigenerati** con il nuovo budget e la
selezione su V-full.

**La selezione di F va ripetuta** sui nuovi punti E, con la stessa griglia:
la vecchia scelta `(200, 0.01)` **non si trasferisce automaticamente**. Resta un
risultato della procedura precedente.

**Il raccordo storico non si rifà.** Raccordo, appaiamento e conferma restano
risultati di un regime a budget breve e selezione temporalmente ristretta.

---

## Artefatti

| | |
|---|---|
| piloti originari, 35 → 2.290 | `adeguatezza/originali/traj_*.json` |
| estensione a 4.580 | `adeguatezza/traj_*.json` |
| punti correnti e migliori | `adeguatezza/ck_*_{corrente,migliore}.pt` |
| analisi | `adeguatezza/analisi.json`, `sensibilita.json` |
| audit del ciclo | `audit_ciclo.json` |
| rettifiche | `RETTIFICA_BUDGET.md`, `RETTIFICA_POPOLAZIONE.md` |
