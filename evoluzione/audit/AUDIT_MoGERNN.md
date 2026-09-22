# Audit di compatibilità sperimentale — MoGERNN

**Commit esaminato**: `86b153fb4bf9358e32079930ccaea1cbcffa66f8` (dal commento
dell'archivio del repository). Nessun tag né release. Articolo: Transportation
Research Part C 174 (2025) 105080.

**Metodo**: lettura del codice; controlli su dati **sintetici** eseguiti col
caricatore originale (`prova_nas.py`, `traccia_nas.py`); riproduzione in numpy
della semantica degli aggregatori. **torch non era disponibile**: i controlli
d'esecuzione dei punti 5 e 9 sono in `audit_mogernn_runtime.py`, da eseguire.

Etichette: **[codice]** verificato nel codice · **[prova]** verificato con
esecuzione su dati sintetici · **[articolo]** dichiarato nell'articolo ·
**[n.d.]** non determinabile dal repository.

---

## 0. Versione ed esperimenti

Dipendenze (`environment.yml`): python 3.10, pytorch 2.1.1 con CUDA 11.8, numpy
1.26, pandas 2.2. Il dataset (con i file dei nodi) **non è nel repository**: va
scaricato da Google Drive, citato nel README.

| esperimento | comando / configurazione | punto di partenza | uscita | ricostruibile? |
|---|---|---|---|---|
| nodi virtuali, §5.2, Tab. 2 | `scripts/MoGERNN-train.sh` → `StaticPEMS` | da zero, seme 32 | `reports.csv`, `results.txt` | **sì**: `reports.csv` coincide con la Tab. 2 METR-LA (VS 14,08 / 5,83 / 8,64) |
| inserimento e guasti, §5.3, Tab. 4 | `scripts/MoGERNN-test_for_new_env.sh` → `DynamicPEMS`, `--test_for_changed` | `pretrained/…seed-32.pth` | `results.txt` | **sì**: righe di `results.txt` coincidono con la Tab. 4 (NAS 11,38 / 4,04 / 6,94) |
| **riaddestrato, Tab. 5** | **nessuno** | — | — | **NO** |

> **Il codice della Tabella 5 non è identificabile.** `main.py` righe 68–88: con
> `--test_for_changed` il programma carica un modello, esegue l'inferenza e
> **termina** (`exit()`, riga 88). Nessun percorso del repository addestra sulla
> classe `DynamicPEMS`. **[codice]**

Incoerenza interna all'articolo: MAPE dei NAS 11,38 nella Tab. 4 e 11,01 nella
Tab. 5 per lo stesso modello congelato (MAE e RMSE coincidono). **[articolo]**

---

## 1. Separazione fra AAS, NAS, VS e FS — priorità

Due configurazioni. Il **modello congelato** si addestra con `StaticPEMS`, in cui
i nodi sconosciuti sono i VS del primo esperimento; il test sulla rete cambiata
usa `DynamicPEMS`.

### Modello congelato (Tab. 4)

| | grafo train | input train | target train | normalizzazione | selezione ck | input test | target test |
|---|---|---|---|---|---|---|---|
| **AAS** | sì | sì | sì | sì | sì | sì | sì |
| **NAS** | no | no | no | **sì, al test** ⚠ | no | **sì, dalla prima origine** | sì |
| **VS** | no | no | no | no | no | no (zero) | sì |
| **FS** | sì | sì | sì | sì | sì | no (zero) | sì |

Fonti: `graph_data_loader.py` righe 94–111 e 122–123 (StaticPEMS), 276–291,
321–326 (DynamicPEMS). **[codice]**, confermato **[prova]**.

**⚠ La normalizzazione al test** è calcolata da `DynamicPEMS` (righe 290–291,
321–322) su `train_known_nodes` che le righe 286–287 hanno **ampliato con i NAS**:
la loro storia del periodo di training entra nella media e deviazione applicate
a **tutti** i nodi in test. Alterando solo quella storia (+200), la media cambia
di 22,6 e i dati normalizzati di test di 1,77. **[prova]** È una statistica
globale per canale: sui dati reali l'effetto è probabilmente piccolo, ma
**[n.d.]** senza il dataset. Inoltre il modello congelato è stato addestrato con
la normalizzazione di `StaticPEMS`, diversa da quella applicata al test.

### Risposte

| domanda | risposta |
|---|---|
| NAS esclusi dal training o solo mascherati? | **Esclusi del tutto** dal training del modello congelato: grafo, ingressi, bersagli, normalizzazione, selezione. **[codice][prova]** |
| i loro target entrano nella perdita? | **No**, nel modello congelato. |
| i NAS derivano dai VS? | **Sì**: righe 257–259 li estraggono da `train_unknown_nodes`, poi le 265–274 li sovrascrivono coi file `new_add_nodes.npy`. **[codice]** |
| selezione casuale? quale seme? | Dai **file** del dataset, non nel repository. L'estrazione casuale delle righe 257–262 è codice morto per la riproduzione. **[codice]** |
| gli identificativi cambiano nei sottografi? | **Sì**: in train la posizione nel tensore non è l'identificativo (`data[:, known_nodes]`). La coerenza è garantita dallo stesso elenco usato per dati e adiacenza. **Nessuna mappa salvata.** In test l'ordine è quello originale. **[codice]** |

---

## 2. Che cosa riceve un sensore nuovo in inferenza — priorità

**Traccia** (dati sintetici con la struttura di METR-LA, `traccia_nas.py`) **[prova]**:

| | origine 0 | origine 1 |
|---|---|---|
| ingressi | 12 passi da 5 min, **1 ora**, sola velocità | idem, +1 ora |
| NAS | **12/12 osservati** | 12/12 |
| VS | 0/12 | 0/12 |
| FS | 0/12 | 0/12 |
| vicini | grafo **completo** (`adj` intera, `DynamicPEMS` in test) | idem |
| istante d'installazione | **nessuno dichiarato** | — |

Il test comincia a `0,7·T + 12` (righe 312, 317): dodici passi dopo la fine del
training vengono saltati «per ragioni storiche» (commento alla riga 316). **Il NAS
è osservato dalla prima origine di test e per tutto il test**: nessun t₀, nessun
periodo d'acquisizione, la maschera non cambia mai.

> **Nel codice, «zero-shot sui NAS» significa esattamente:** il modello congelato
> non ha mai visto i NAS in training — né nel grafo, né negli ingressi, né nei
> bersagli, né nella selezione del punto di controllo — ma al test ciascun NAS è
> un sensore **osservato**: riceve la **propria velocità misurata nell'ora che
> precede ogni origine**, è collegato ai vicini nel grafo completo, e la sua
> storia anteriore all'installazione entra soltanto attraverso la
> **normalizzazione globale**. **Assenza di training sul NAS, non assenza di
> osservazioni locali.**

---

## 3. Che cosa significa «retrained» — priorità

| interpretazione | esito |
|---|---|
| riaddestramento con storia pregressa dei NAS | **l'unica implementata nel repository**, ma non raggiungibile |
| adattamento causale dopo l'installazione | **assente**: nessun codice usa soltanto osservazioni posteriori all'installazione |
| fine-tuning del modello precedente | **assente**: nessun caricamento di pesi seguito da addestramento |
| **procedura non ricostruibile dal repository** | **sì** |

**Motivazione.** `main.py` non addestra mai su `DynamicPEMS` (§0). Ma il ramo
`train` di `DynamicPEMS` (righe 286–300) esiste: include i NAS nel grafo, negli
ingressi, nei bersagli e nella normalizzazione, **con tutta la loro storia del
primo 70% del periodo** — cioè anteriore all'installazione simulata. Include
anche i FS con la storia precedente al guasto. **[codice][prova]**

> **Registrato: la procedura della Tabella 5 non è stata ricostruita dal
> repository esaminato. L'implementazione identificata utilizza informazione
> assimilabile al nostro riferimento privilegiato A.** Il comportamento di quel
> percorso di codice **non si attribuisce** alla tabella.
>
> **Se la Tabella 5 è stata prodotta con quel ramo, il «retrained» corrisponde al
> nostro riferimento privilegiato A, non a R.** Che lo sia è **[n.d.]**: va
> chiesto agli autori, con il periodo usato per i NAS e il criterio di
> selezione.

---

## 4. Normalizzazione e valori mancanti

| | |
|---|---|
| normalizzazione | **globale per canale**: media e deviazione su tempo × nodi del training, nodi noti (righe 122–123). Nessuna statistica per nodo: un nodo nuovo non ne richiede. **[codice]** |
| valori ≤ 0 | **diventano mancanti** (righe 77, 238): una velocità fisica nulla è trattata come assenza, per convenzione esplicita. **[codice]** |
| mancanti negli ingressi | `NaN → 0` **dopo** la normalizzazione (`inductive_epoch.py` 57): lo zero vale **la media globale**, non una velocità nulla. **[codice]** |
| indicatore di nodo nascosto | un nodo è «ignoto» se **la somma dei suoi ingressi sull'intero lotto è zero** (`MoGERNN.py` 83–84): dipende dalla **composizione del lotto**. **[codice]** |
| riempimento | **ogni** valore pari a zero è sostituito dall'uscita degli esperti (97–98): osservazione mancante, nodo mascherato e valore uguale alla media **non sono distinguibili**. Nessun canale di maschera. **[codice]** |
| perdita e metriche | escludono i bersagli `NaN` (`inductive_epoch.py` 83–86). I nodi mascherati artificialmente **restano** nei bersagli. **[codice]** |

**Per i nostri dati** — Londra al 37,5% di copertura — questo trattamento non è
compatibile senza modifiche: mancanza originaria e occultamento vengono fusi, e
l'identificazione dei nodi ignoti cambierebbe col lotto.

---

## 5. Induttività ed espansione del grafo

| | |
|---|---|
| parametri indicizzati per nodo | **nessuno**: `Linear` sulla finestra e sui canali, `Theta1` di forma `(canali × matrici, uscita)`. **[codice]** |
| adiacenza | passata a **ogni** forward; random walk ricalcolata ogni volta, su CPU con scipy (`gnn.py` 32–45). **[codice]** |
| nodi isolati | grado 0 → posto a 1: non ricevono nulla dal grafo. **[codice]** |
| stato in valutazione | nessun aggiornamento di pesi in `inference_model` (`torch.no_grad`, `eval`). **[codice]**; verifica esecutiva in `audit_mogernn_runtime.py` [5] |

### La maschera dell'adiacenza, verificata su tre nodi

In tutti gli esperti la maschera è `adj[:, ignoti] = 0` (colonne). Ma le
**convenzioni di aggregazione differiscono**: **[codice]**, riprodotto **[prova]**

| esperto | un nodo riceve da | effetto della maschera sul nodo ignoto |
|---|---|---|
| media, media pesata, diffusione | la sua **riga** (`adj @ x`) | **non invia**: coerente con l'articolo |
| **massimo, minimo** | la sua **colonna** (`einsum 'ijk,kl'`) | **non riceve**: riceve 0 |

Grafo 0→1→2, nodo 2 ignoto: nel massimo il nodo 2 passa da 7 a **0**. Inoltre
nel massimo e nel minimo **i non-vicini contribuiscono con zero**: con vicini a
−3 e −4 il massimo vale 0. Sono proprietà dell'implementazione; l'effetto sulle
prestazioni è **[n.d.]**.

> **Il test conferma un comportamento del codice, non dimostra da solo che esso
> realizzi o tradisca l'intenzione dell'articolo** — ricavare la rappresentazione
> del nodo ignoto dai vicini. Il test si conserva (grafo 0→1→2, adiacenza
> `adj[i,j] > 0` per l'arco i→j, nodo 2 ignoto, aggregazione prima e dopo la
> maschera). **Non si corregge nell'ottimizzazione**: una correzione semantica
> sarebbe una variante del metodo, da discutere a parte, eventualmente con gli
> autori. Nell'encoder e decoder, invece, la random walk usa
l'adiacenza **completa**, non mascherata (`MoGERNN.py` 218–219): lì i valori
ricostruiti dei nodi ignoti raggiungono i nodi osservati.

---

## 6. Training e selezione effettivi

| | |
|---|---|
| epoca | fino a **600 lotti** da 64, **un aggiornamento per lotto** (`inductive_epoch.py` 40–41, 87–90). Passo 1 in training, 12 in validazione e test. **[codice]** |
| mascheramento | **25% dei nodi** a zero negli ingressi, grafo invariato (72–78). Il sottocampionamento del 90% (61–63) è **annullato** dalla riga 64. **[codice]** |
| perdita | MSE sui valori normalizzati, su **tutti** i bersagli non mancanti dei nodi noti. **[codice]** |
| teacher forcing | probabilità `1 − epoca/40`, per passo: si annulla dopo l'epoca 40. **[codice]** |
| **validazione** | **identica al training**: stessi nodi, stesso periodo (StaticPEMS 103–111). Conferma dell'articolo §5.1. Criterio `val_mask`: perdita sui nodi **mascherati a caso** in quella valutazione. **[codice]** |
| arresto | pazienza 10, mai prima dell'epoca 20, massimo 200. **[codice]** |
| test durante il training | **valutato a ogni epoca**; viene salvato anche un punto `best_test` scelto sulla perdita di test dei VS (`train.py` 64–66). **[codice]** |
| numeri pubblicati | Tab. 2 e 4 corrispondono al punto scelto su **validazione**, non su test. L'etichetta «Best Based on test» in `results.txt` indica la chiave delle predizioni, non il criterio (`test.py` 82). **[codice]** |
| semi | un solo seme (32), `pl.seed_everything`. Nessuna ripetizione. **[codice]** |
| suddivisione | 70/30 **fissa nel codice**; `--train_ratio` e `--valid_ratio` sono ignorati. **[codice]** |

---

## 7. Fattibilità di un compito comune

**Il decoder è autoregressivo sulla velocità.** `Decoder.fc` riporta lo stato
nascosto alla dimensione dell'ingresso (1), e **l'uscita di ogni passo è
l'ingresso del successivo** (`MoGERNN.py` 177–186). Anche il primo ingresso è
l'ultima velocità osservata (201).

> **Sostituire la testa con tre logit non è neutra: cambia la dinamica
> ricorrente.** Va progettata e dichiarata.

| opzione | modifiche necessarie | rischio di alterare il metodo | costo |
|---|---|---|---|
| **classificazione comune** | testa di classi **aggiunta** accanto alla regressione (il decoder continua a ricircolare la velocità); orizzonti 1, 2, 4, 8 a 15 min; ingressi a 9 canali oppure sola velocità; **maschera esplicita** invece dello zero; grafo per Traffic4cast, con **nodi isolati** | **medio**: la testa aggiuntiva è una variante multi-compito, non l'originale | alto |
| **regressione comune** | un bersaglio continuo per tutti; **riaddestrare i nostri cinque bracci in regressione** | basso per MoGERNN, **alto per noi**: un'altra campagna | molto alto |

Non si confrontano probabilità di classe con classi ottenute a soglia da una
previsione continua.

---

## 8. Differenze informative

| informazione | nostro P | MoGERNN originale | confronto comune possibile |
|---|---|---|---|
| storia locale recente | 3 ore | **1 ora**, sola velocità | allineabile |
| storia per il descrittore | prime 24 ore | **nessuna** | — |
| misure dei vicini | no | **sì**, grafo completo | intrinseca a MoGERNN |
| grafo | no | **sì**, distanze stradali | da costruire per Traffic4cast |
| statiche stradali | sì | no (posizione disattivata negli script) | — |
| calendario | sì | no (`t_mark` disattivato negli script) | — |
| aggiornamento dei pesi sui NAS | no | no | — |
| periodo d'acquisizione | 24 ore | **nessuno**: osservato da subito | va imposto |
| storia pregressa del nodo | no | **solo nella normalizzazione** | va rimossa |

Sono strategie di sistema con dipendenze diverse: il confronto **non è
un'ablazione a parità di informazione**, e non va presentato come tale.

---

## 9. Costi — misurati

`audit_mogernn_runtime.py`, MacBook Pro M3, CPU, un processo, lotto 64, mediana
di 5 ripetizioni dopo 2 di riscaldamento. **[prova]**

| | esito |
|---|---|
| parametri | **226.270**, nessuna forma dipende dal numero di nodi |
| nodo isolato aggiunto | uscite degli altri **identiche**, scarto 0 |
| permutazione coerente | uscite permutate, scarto 4,5·10⁻⁸ |
| stato in valutazione | **invariato**, 47 tensori |
| direzione della maschera, classi vere | **confermata**: media riceve dalla riga, massimo dalla colonna; il nodo ignoto nel massimo passa da 7 a 0 |
| gating: 1 esperto contro 5 | 2.004 contro 2.042 ms, **rapporto 1,02**: gli esperti non scelti **vengono calcolati** |

| nodi | aggiornamento | inferenza |
|---|---|---|
| 207 | 4,6 s | 2,6 s |
| **765** | **18,6 s** | **9,9 s** |

Il costo cresce di circa **4 volte** passando da 207 a 765 nodi: **più che
lineare**, coerente con le componenti quadratiche nel numero di nodi — la random
walk ricalcolata su CPU e i tensori `[lotto, finestra, N, N]` degli esperti di
massimo e minimo. **Quale delle due domini è [n.d.]** senza profilazione.

### Profilo di un aggiornamento — 765 nodi, lotto 64 **[prova]**

`profila_mogernn.py`: forward 9,03 s, backward e passo 9,57 s, **totale 18,59 s**.

| componente del forward | chiamate | secondi | quota |
|---|---|---|---|
| **DiffConv, celle ricorrenti** | 144 | **7,39** | **81,9%** |
| esperti di massimo e minimo | 1 + 1 | 0,38 | 4,2% |
| altri tre esperti | 3 | 0,05 | 0,5% |
| random walk, tutte | 4 | 0,02 | 0,2% |

| operazione, forward e backward | tempo proprio | quota |
|---|---|---|
| `aten::mm`, prodotti per matrici dense | 5,27 s | 34,5% |
| **`aten::copy_`** | **4,23 s** | **27,7%** |
| `aten::cat` | 1,38 s | 9,1% |

**Memoria di picco: 13,0 GB per processo.**

- **Gating**: con un solo esperto attivo **tutti e cinque vengono chiamati**. Il
  percorso d'esecuzione conferma quanto indicato dal rapporto dei tempi. **[prova]**
- **Le due ottimizzazioni autorizzate** — cache della random walk, massimo e
  minimo sui vicini — agiscono su **meno del 5% del forward**.
- **Il costo sta nelle celle ricorrenti**: prodotti densi, e quasi altrettanto in
  copie e concatenazioni dovute a `permute` + `reshape` e `torch.cat` in
  `DiffConv.forward` (`DCRNNCell.py` 53–72). 144 chiamate = 24 passi × 2 strati
  × 3 porte.

> **RETTIFICA.** Il controllo d'esecuzione (18,6 s per aggiornamento) e il
> profilo sono stati eseguiti **mentre la fase E occupava la macchina con otto
> processi**. **I tempi assoluti sono inflazionati dalla contesa e si
> ritrattano**, con le stime di campagna che ne derivavano. Restano validi la
> memoria, i conteggi delle chiamate e l'esito dei controlli funzionali; la
> ripartizione percentuale del profilo resta **indicativa**.

### Benchmark in isolamento — lotto 32, macchina libera **[prova]**

`benchmark_mogernn.py`: grafo sintetico, 765 nodi, 29.207 archi, densità 0,050,
normalizzazione random walk; torch 2.12.1, macOS 26.6.2, M3; 3 aggiornamenti di
riscaldamento esclusi, 10 misurati; MPS sincronizzato prima e dopo ogni tratto.

| misura | CPU | GPU, backend MPS |
|---|---|---|
| aggiornamento completo, mediana | **3,27 s** (3,21–3,47) | **0,91 s** (0,91–0,92) |
| inferenza, mediana | 1,95 s | 0,51 s |
| memoria di picco | RSS 6,9 GB | RSS 0,5 GB; pool del driver MPS 9,3 GB — **non sommati** |
| fallback su CPU | — | **nessuno** |
| scarti CPU contro MPS | — | uscite 3,7·10⁻⁸, perdita 6,0·10⁻⁸, gradienti 3,8·10⁻⁹ |

**Equivalenza numerica entro la precisione di float32, non identità.**

**Throughput CPU in concorrenza**, misurato:

| processi × fili | per aggiornamento | aggiornamenti al secondo, totale |
|---|---|---|
| 1 × 14 | 3,68 s | 0,272 |
| **3 × 4** | 7,17 s | **0,419** |
| 5 × 2 | 16,45 s | 0,304 |

**La GPU con un solo processo, 1,10 aggiornamenti al secondo, rende circa 2,6
volte la migliore configurazione CPU.** Prima stima di un minuto: non stabilisce
il throughput sostenuto per ore.

### Che cosa implica per il nostro protocollo

Con il nostro budget di 2.290 aggiornamenti e 765 nodi:

| | per addestramento | 108 addestramenti | in calendario, 8 × 1 a 3,5× |
|---|---|---|---|
| lotto 64, come misurato | ~11,8 ore | **~1.280 ore-macchina** | ~15 giorni |
| lotto 32, il nostro | ~6 ore, **da misurare** | ~650 ore-macchina | ~8 giorni |

**Un solo braccio MoGERNN costerebbe da due a quattro volte l'intera campagna
principale** (276 ore-macchina). L'articolo usava una GPU RTX 4090: la nostra
scelta di un unico backend CPU, fatta per la coerenza numerica dei bracci
appaiati, qui pesa molto.

# A. Risposte accertate

- **NAS esclusi da tutto il training del modello congelato**, ma presenti nella
  **normalizzazione** applicata al test. Formulazione registrata: **l'architettura
  è induttiva, ma la pipeline verificata richiede informazione storica dei nuovi
  sensori non disponibile nel nostro scenario di installazione.** Ne segue che
  serve una normalizzazione ammissibile, dichiarata come adattamento, non che
  MoGERNN sia inutilizzabile.
- **L'induttività è confermata**: l'inserimento senza riaddestramento **non è la
  nostra novità distintiva**.
- **In inferenza ricevono la propria velocità dell'ultima ora**, da subito, più i
  vicini. Nessun t₀.
- **«Retrained» non è ricostruibile**; l'unica implementazione presente userebbe
  la **storia pregressa** dei NAS → assimilabile al nostro **A**.
- **Nessun parametro specifico per nodo**; nessuna statistica per nodo.
- **Il trattamento dei mancanti non è compatibile** col nostro scenario senza
  modifiche: zero ambiguo, identificazione dei nodi ignoti dipendente dal lotto.

# B. Differenze dal nostro problema

**Sostanziali**: sorgente dell'identità (vicini contro storia propria); nessun
periodo d'acquisizione; storia pregressa nella normalizzazione; compito di
regressione con decoder autoregressivo; grafo obbligatorio.

**Implementative**: risoluzione (5 contro 15 minuti), orizzonti, numero di
canali, validazione coincidente col training, un solo seme, convenzioni degli
aggregatori.

# C. Piano minimo di confronto

**Proposta: MoGERNN adattato alla classificazione, come braccio di sistema
dichiarato**, sotto il nostro protocollo:

1. testa di classi **aggiunta**, decoder che continua a ricircolare la velocità;
2. **nessun uso della storia pregressa** dei nodi nuovi, nemmeno nella
   normalizzazione;
3. il nodo nuovo entra nel grafo a t₀ e riceve **gli stessi ingressi causali**
   del nostro calendario;
4. maschera esplicita al posto dello zero;
5. stesso budget, semi, partizioni, perimetro di selezione e chiavi di
   valutazione dei nostri bracci.

Se il punto 1 risultasse troppo invasivo, **dichiarare l'impossibilità di un
confronto affidabile senza modifiche rilevanti** è un esito legittimo.

# D. Stima del lavoro

| | |
|---|---|
| adattamento dei dati | grafo per Traffic4cast con nodi isolati, 15 min, calendario |
| adattamento del modello | testa di classi, maschera esplicita, orizzonti |
| integrazione nel protocollo | t₀, acquisizione, chiavi di valutazione, parallelismo |
| collaudi | equivalenza sull'originale, assenza della storia pregressa, permutazione, nodo isolato |
| costo computazionale | **da misurare** con lo script; la random walk su CPU è il rischio principale |

**Domande agli autori**: codice e dati della Tabella 5 (periodo usato per i NAS,
punto di partenza, selezione); file dei nodi usati; incoerenza fra Tab. 4 e 5;
intenzione della maschera negli esperti di massimo e minimo; procedura di misura
della Fig. 8.
