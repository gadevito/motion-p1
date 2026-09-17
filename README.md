# MOTION — OR3: pipeline, campagne e rielaborazioni

Guida all'esecuzione della campagna sperimentale del deliverable
**`MOTION_deliverable_v227`**.

Per ogni blocco: **il comando**, **perché si esegue**, **quale sezione o tabella del
deliverable alimenta**. I risultati numerici stanno nel deliverable, non qui: questo
documento serve a produrli, non a riportarli.

I percorsi sono relativi alla radice `OR3/`. Dove serve una sottocartella, il `cd` è
nel blocco.

---

## 0. Convenzioni

| Livello | Che cos'è | Costo |
|---|---|---|
| **Costruzione** | dai dati grezzi ai contesti (§3) | ore, una volta sola |
| **Campagne** | addestramenti su semi e contesti (§8) | ~507 ore macchina misurate |
| **Rielaborazioni** | analisi sui `.npz` già salvati | minuti, nessun addestramento |

**Prima di lanciare una campagna, verificare che la rielaborazione corrispondente non
sia già possibile dai dump esistenti.**

**Semi.** Cinque (0–4) sulla campagna principale, tre dove la didascalia lo dichiara. Il
seme è sempre nel nome del file di risultato.

**Bracci di un confronto nella stessa invocazione.** `--modes none,fixed,adaptive`, mai
esecuzioni separate: altrimenti la differenza misurata include la versione dello script
oltre all'effetto studiato (§7.3).

**Determinismo.** Il backend MPS non è riproducibile bit-a-bit a parità di seme. La
replica riproduce gli esiti entro la dispersione fra semi, non cifra per cifra.

**Ripresa.** I cicli saltano i file già prodotti: una campagna interrotta si riprende
rilanciando lo stesso comando.

---

## 1. Prerequisiti

Ogni sottocartella con `pyproject.toml` è un progetto Poetry indipendente:
`data_collection/`, `data_collection/go-mo/`, `data_collection/traffic4cast/`,
`models/`, `baselines/`, `analisi/`, radice.

```bash
poetry install
```

| Servizio | Serve per | Chiave |
|---|---|---|
| Hugging Face | dataset GO-MO | no |
| Overpass | grafo e attributi OSM d'epoca | no |
| Open-Meteo | storico meteorologico | no |
| Socrata | radar di Austin | no |
| HERE | raccolta Baronissi | `HERE_API_KEY` |

Hardware di riferimento: MacBook M3 Max, 96 GB, MPS. In caso di memoria esaurita,
ridurre `--batch`.

---

## 2. Preambolo

**Da eseguire una volta per sessione di shell**, prima di qualunque blocco.

```bash
cd /percorso/di/OR3
setopt +o nomatch 2>/dev/null   # zsh
R=$(pwd)
declare -A T G S W CITY

D1=$R/data_collection/go-mo/gomo
for c in d8_2024 d15_2024 d8_2023; do
  G[$c]=$D1/routes-graph.pkl; S[$c]=$D1/traffic_sensors.csv; CITY[$c]=madrid
  W[$c]=$D1/weather_2024_d8.npz
done
T[d8_2024]=$D1/targets_2024_urb_d8.npz
T[d15_2024]=$D1/targets_2024_urb_d15.npz
T[d8_2023]=$D1/targets_2023_urb_d8.npz

D2=$R/data_collection/traffic4cast/MADRID_2022/gomo_fmt
T[t4cmad]=$D2/targets_t4cmad_d8.npz; G[t4cmad]=$D2/t4cmad_routes-graph.pkl
S[t4cmad]=$D2/t4cmad_sensors.csv;    W[t4cmad]=$D2/weather_t4cmad.npz; CITY[t4cmad]=madrid

D3=$R/data_collection/traffic4cast/LONDON_2022/gomo_fmt
T[t4clon]=$D3/targets_t4cmad_d8.npz; G[t4clon]=$D3/t4cmad_routes-graph.pkl
S[t4clon]=$D3/t4cmad_sensors.csv;    W[t4clon]=$D3/weather_t4clon.npz; CITY[t4clon]=londra

D4=$R/data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt
T[t4cmel]=$D4/targets_t4cmel_d8.npz; G[t4cmel]=$D4/t4cmel_routes-graph.pkl
S[t4cmel]=$D4/t4cmel_sensors.csv;    W[t4cmel]=$D4/weather_t4cmel.npz; CITY[t4cmel]=melbourne

for d in suite sparse calibrazione identita onboard geo meteo validita \
         validazione diagnostiche aggregati storici superati \
         probs probsval probs_wx; do
  mkdir -p "$R/replication/$d"
done
mkdir -p "$R/descrittori" "$R/log"

for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for p in "${T[$c]}" "${G[$c]}" "${S[$c]}"; do
    [ -f "$p" ] || echo "  MANCA $p"
  done
done
```

Il ciclo finale non deve stampare nulla.

> **Nome storico di Londra**: `T[t4clon]` punta a `targets_t4cmad_d8.npz` e non è un
> refuso. Il meteo fa eccezione e si chiama `weather_t4clon.npz`.
>
> **`W` per i contesti a spire punta al solo d8/2024**: il meteo è di area e una serie
> per città copre i distretti dello stesso anno. Per d8/2023 va rigenerato con
> `6_gomo_weather.py` sull'annata corretta.

---

## 3. Ordine di esecuzione

```
  A. costruzione dei contesti (§4)
        |
        +--> B. verifiche sui dati costruiti (§5)        [minuti]
        |
        +--> C. patch dell'attributo di distanza (§6)     [obbligatoria prima di D]
                    |
                    +--> D. campagne (§7)                 [~507 ore misurate]
                              |
                              +--> E. rielaborazioni (§8) [minuti]
```

**C precede D senza eccezioni.** Le campagne lanciate prima della patch producono
risultati validi solo dove nessun braccio consuma l'adiacenza fornita.

Dentro D l'ordine è libero salvo due vincoli: la campagna a popolazione ristretta del
riferimento tabellare precede le rielaborazioni di R1, e i descrittori precedono la
griglia dell'identità.

---

## 4. Costruzione dei contesti (→ §3)

### 4.1 Contesti primari (→ §3.1)

```bash
cd data_collection/traffic4cast
poetry run python t4c_recover_osm_nodes.py \
  --speed-dir MELBOURNE_2022/speed_classes/melbourne \
  --bbox -37.95 144.75 -37.65 145.15 --date 2020-06-01 \
  --out MELBOURNE_2022/road_graph_nodes_osm.parquet

poetry run python t4c_recover_osm_edge_attrs.py \
  --edges MELBOURNE_2022/road_graph_edges_district.parquet \
  --bbox -37.95 144.75 -37.65 145.15 --date 2020-06-01 \
  --out MELBOURNE_2022/road_graph_edge_attrs_osm_2020.parquet

poetry run python t4c22_adapter.py \
  --nodes MELBOURNE_2022/road_graph_nodes_osm.parquet \
  --edges MELBOURNE_2022/road_graph_edges_district.parquet \
  --speed-dir MELBOURNE_2022/speed_classes/melbourne \
  --edge-attrs MELBOURNE_2022/road_graph_edge_attrs_osm_2020.parquet \
  --out-dir MELBOURNE_2022/gomo_fmt --prefix t4cmel
```

**Perché**: costruisce i tre contesti a velocità misurata. **Alimenta**: §3.1, Tabella 2.

| Città | data attic | bbox | prefisso |
|---|---|---|---|
| Madrid | 2021-06-01 | dal distretto GO-MO | `t4cmad` |
| Londra | 2019-07-01 | override | `t4cmad` |
| Melbourne | 2020-06-01 | `-37.95 144.75 -37.65 145.15` | `t4cmel` |

> **Le date attic sono l'inizio del periodo dei dati.** I tag odierni introducono un
> errore sistematico: su una quota rilevante dei tratti londinesi il limite di velocità
> è cambiato dopo la raccolta.

```bash
poetry run python t4c_compare_osm_epochs.py
```

**Perché**: quantifica l'anacronismo dei tag e giustifica la scelta delle date.
**Alimenta**: §3.1.2.

### 4.2 Varianti di soglia (→ §4.2, §8.7.2)

```bash
cd data_collection/traffic4cast
poetry run python genera_varianti_soglia.py \
  --base MADRID_2022/gomo_fmt --prefix t4cmad \
  --soglie 0.70 0.725 0.75 0.775 0.825 0.85 0.90 --collaudo
```

**Perché**: separa la rarità della classe critica dalle altre differenze fra contesti,
manipolandola dentro un solo contesto. **Alimenta**: §8.7.2, sensibilità di R1 e R3 alle
soglie.

`--collaudo` rigenera la soglia 0,80 e verifica che riproduca il file base: se lo scarto
supera un centesimo di punto si ferma.

### 4.3 Contesti GO-MO (→ §3.2)

```bash
cd data_collection/go-mo
poetry run python 1_gomo_stage1_loader.py
poetry run python 2_gomo_targets.py
poetry run python 3_gomo_target_check.py
poetry run python 4_gomo_urb.py --year 2024 --district 8
poetry run python 4_gomo_urb.py --year 2024 --district 15
poetry run python 4_gomo_urb.py --year 2023 --district 8
poetry run python 4_gomo_urb.py --year 2021 --district 8    # solo §8.6.3
poetry run python 5_urb_check.py
```

**Perché**: costruisce i tre contesti a velocità ricostruita più il perimetro della
validazione incrociata. **Alimenta**: §3.2, Tabelle 3–6.

Ogni invocazione stampa in testa la validazione del proxy sull'M30, che è il controllo di
metodo del passo.

> ⚠ **`speed` sui contesti URB non è una misura**: è `r × ff_emp` (riga 124), con
> correlazione unitaria per costruzione. Non entra in alcun modello della suite
> principale, ma va saputo prima di usare i file.
>
> ⚠ **`ff_emp` sui contesti URB è il limite di velocità dell'anagrafica**, non il
> percentile empirico, che è usato internamente e non salvato. Sul ramo M30 vale la
> convenzione opposta.
>
> ⚠ **Anagrafica GO-MO.** Dal 6/7/2026 `traffic_sensors.csv` ha perso `max_capacity` e
> `has_data`. Gli esperimenti che le richiedono (`sparse`, `onboard`, `ign`) devono usare
> la revisione dei run originali:
> ```python
> hf_hub_download('dmariaa70/GO-MO', 'traffic_sensors.csv',
>                 repo_type='dataset', revision='7b8dbd3476')
> ```

### 4.4 Meteo (→ §3.3)

```bash
cd data_collection/go-mo
poetry run python 6_gomo_weather.py \
  --targets ../traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz \
  --sensors ../traffic4cast/MELBOURNE_2022/gomo_fmt/t4cmel_sensors.csv \
  --tz Australia/Melbourne \
  --out ../traffic4cast/MELBOURNE_2022/gomo_fmt/weather_t4cmel.npz
```

**Perché**: cinque serie meteorologiche **di area**, una per città. **Alimenta**: §3.3 e
tutta §8.6.2.

### 4.5 Austin (→ §3.4)

```bash
cd austin/radar
poetry run python scarica.py
poetry run python caratterizza_radar.py --input radar_completo.json
```

**Perché**: l'unico riferimento in cui lo stesso dispositivo misura volume, occupazione
**e** velocità su arterie semaforizzate. **Alimenta**: §3.4 e §8.6.4.

> ⚠ **`curdatetime` è inservibile** su una quota rilevante dei record: usare i campi
> separati `year/month/day/hour/minute`. Raggruppare per `curdatetime` crea istanti spuri.
>
> ⚠ **Tre intersezioni non riportano la direzione** e vanno escluse dalle analisi per
> sezione.

### 4.6 Attributi direzionali (→ §10)

```bash
cd data_collection/traffic4cast
poetry run python t4c_recover_osm_directions.py \
  --edges MADRID_2022/road_graph_edges_district.parquet \
  --nodes MADRID_2022/road_graph_nodes_osm.parquet \
  --bbox 40.31 -3.89 40.55 -3.56 --date 2021-06-01 --tiles 12 --pausa 12 \
  --out MADRID_2022/road_graph_edge_direction_osm_2021.parquet
```

**Perché**: chiude il limite dichiarato sulla mediazione fra carreggiate opposte. Il
verso di marcia viene dall'ordine dei nodi nel tratto, e l'azimut dalla tangente locale
anziché dalla corda. **Alimenta**: §10, limite sulla normalizzazione simmetrica.

Bbox: Londra `51.456 -0.225 51.573 0.011` con `--date 2019-07-01`; Melbourne
`-37.968 144.741 -37.628 145.177` con `--date 2020-06-01`.

> Le interrogazioni con data attic sono molto più pesanti di quelle correnti: `--tiles 12
> --pausa 12` evita i blocchi per quota. La ripresa è automatica.

---

## 5. Verifiche sui dati costruiti

Nessuna richiede addestramenti.

```bash
poetry run python analisi/caratterizza_grafi.py
```

**Perché**: verifica tipo, orientamento e — soprattutto — **quale attributo di distanza i
modelli consumano**. Sui contesti a spire deve dire `distance`, sui primari `weight`.
**Alimenta**: §3.1.2, §3.2.2, e l'affermazione di §8.3 sulle protezioni contro la
mediazione fra carreggiate opposte.

> ⚠ **L'asimmetria va misurata come rapporto, non come differenza, e sull'attributo che
> i modelli consumano.** Sul grafo GO-MO l'asimmetria relativa mediana fra i due versi
> vale **0,334 su `distance` e 0,115 su `weight`**: riportare il valore senza dichiarare
> l'attributo è ambiguo, e una differenza assoluta su pesi compresi fra 0,01 e 1 dà un
> numero di un ordine di grandezza inferiore che si presta a essere letto come assenza
> di asimmetria.
>
> **È la differenza fra dire che la direzionalità è una protezione nominale o effettiva.**
> Con il 96,4% degli archi reciproci ma un terzo delle coppie che differisce di oltre il
> cinquanta per cento sulla distanza di percorso, la protezione è effettiva.

> ⚠ **È il controllo che intercetta il difetto più consequenziale della campagna.** Una
> quota di archi sopravvissuti al nucleo gaussiano prossima a zero significa che la patch
> di §6 non è applicata.

```bash
poetry run python analisi/imputazione_gomo.py
```

**Perché**: quantifica l'effetto della regola di strada vuota e verifica che **nessuna
cella imputata abbia etichetta diversa da verde** — su cui poggia la lettura in richiamo
di §8.3. **Alimenta**: §3.2.4, Tabelle 5 e 6.

```bash
cd data_collection/go-mo
poetry run python 4b_gomo_urb_p85tr.py --year 2024 --district 8 \
  --out gomo/targets_2024_urb_d8_p85tr.npz \
  --confronta gomo/targets_2024_urb_d8.npz
```

**Perché**: il riferimento di flusso libero è l'unica statistica calcolata sull'intero
periodo anziché sul solo addestramento. Questo rigenera il contesto senza quell'eccezione.
**Alimenta**: §3.2.4, §7.2.7, §8.7.2.

Il collaudo `--confronta` è obbligatorio e blocca lo script se fallisce.

---

## 6. Patch dell'attributo di distanza

**Obbligatoria prima di qualunque campagna.**

```bash
poetry run python patch_attributo_distanza.py --verifica
poetry run python patch_attributo_distanza.py
```

**Perché**: sui contesti a spire il campo `weight` è una **similarità** e non una
distanza in metri, che sta in `distance`. Il nucleo gaussiano applicato alla similarità
azzera i nodi vicini e conserva i lontani.

**Chi ne risente:**

| script | modelli che consumano il grafo | contesti | interessato |
|---|---|---|---|
| `gomo_sparse.py`, `gomo_classify.py` | — | — | **già corretti** |
| `gomo_rnn_baselines.py` | DCRNN (AGCRN no) | tutti e sei | **sì, sui tre a spire** |
| `gomo_sota_baselines.py` | `t4c_gnn` (STAEformer no) | tutti e sei | **sì, sui tre a spire** |
| `gomo_ign.py`, `gomo_onboard.py` | `norm_adj` | soli primari | no, in pratica |
| `gomo_gwn.py`, `gomo_stgnn.py` | modalità `fixed` | regressione (§7.2.7) | fuori dalle tabelle principali |

**Alimenta**: le righe del DCRNN nelle Tabelle 17–19, la riga del GCN nella 21, tutto il
braccio `fixed` di §8.3 e §8.5.

Gli script sono cercati per nome sotto la radice: `--radice ~/OR3` se lanciato altrove.
Al primo run controllare la riga `[grafo] attributo di distanza: …`.

---

## 7. Campagne

### 7.1 Suite principale (→ §8.1)

**Servono due orchestratori**, le cui competenze non si sovrappongono:

```bash
poetry run python run_replication.py --seeds 0 1 2 3 4 \
  --context d8_2024=data_collection/go-mo/gomo/targets_2024_urb_d8.npz \
  --context d15_2024=data_collection/go-mo/gomo/targets_2024_urb_d15.npz \
  --context d8_2023=data_collection/go-mo/gomo/targets_2023_urb_d8.npz

poetry run python run_replication.py --seeds 0 1 2 3 4 \
  --context t4cmad=$D2/targets_t4cmad_d8.npz \
  --graph $D2/t4cmad_routes-graph.pkl --sensors $D2/t4cmad_sensors.csv
# idem t4clon, t4cmel

poetry run python run_model_suite.py --seeds 0 1 2 3 4 \
  --ctx d8_2024 "${T[d8_2024]}" "${G[d8_2024]}" "${S[d8_2024]}" \
  --ctx t4cmad  "${T[t4cmad]}"  "${G[t4cmad]}"  "${S[t4cmad]}"
# ... le altre quadruple
```

**Perché**: gli otto modelli delle quattro fasce informative. **Alimenta**: §8.1, Tabelle
17, 18, 19.

| Orchestratore | Esperimenti |
|---|---|
| `run_replication.py` | `classify`, `lgb`, `sparse` |
| `run_model_suite.py` | `rnn`, `sota` |

> ⚠ **Tre cose che gli orchestratori non fanno**, e che vanno lanciate a mano:
> non passano `--dump-probs`, quindi nessuna rielaborazione di §8 è possibile su quanto
> producono; non restringono la popolazione del riferimento tabellare; non addestrano il
> braccio a grafo fisso, invocando `sparse` con `--modes none,adaptive`.
>
> ⚠ **`ALL_results.csv` contiene più esperimenti**: ogni aggregazione deve filtrare la
> colonna `experiment`. E **non contiene la precisione**, che nasce dalla campagna
> dedicata.

### 7.2 Precisione sulla classe critica (→ §8.1)

```bash
cd baselines
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    poetry run python gomo_rnn_baselines.py --model both \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" \
      --seed $s --city "${CITY[$c]}" \
      --out $R/replication/suite/prec_rnn_${c}_s$s.csv \
      --dump-probs $R/replication/probs/rnn_${c}_s$s.npz
    poetry run python gomo_sota_baselines.py --model both \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" \
      --seed $s --city "${CITY[$c]}" \
      --out $R/replication/suite/prec_sota_${c}_s$s.csv \
      --dump-probs $R/replication/probs/sota_${c}_s$s.npz
  done
done
cd ..
```

**Perché**: `red_prec` non è negli aggregati. **Alimenta**: §8.1, Tabella 19 e le
correlazioni di rango del capoverso che la commenta.

### 7.3 R1 appaiato e calibrazione (→ §8.2)

```bash
cd baselines
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    O=$R/replication/suite/lgbristr_${c}_s$s.csv
    [ -s "$O" ] || poetry run python gomo_lgb_fair.py \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" \
      --seed $s --city "${CITY[$c]}" --num-threads 5 \
      --out "$O" --dump-probs $R/replication/probs/lgbristr_${c}_s$s.npz
  done
done
cd ..
```

**Perché**: il riferimento tabellare deve stare sulla **popolazione ristretta**,
altrimenti gli intervalli appaiati non sono calcolabili e le tabelle di §8.1 sono
incoerenti con quelle di §8.2. **Alimenta**: §8.2 Tabelle 23–25, e le righe del LightGBM
nelle Tabelle 17–19.

**Collaudo**: scarto esattamente nullo sui tre contesti a spire, dove le popolazioni già
coincidevano.

```bash
cd models
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    poetry run python gomo_classify.py --targets "${T[$c]}" --graph "${G[$c]}" \
      --sensors "${S[$c]}" --backend torch --modes none --seed $s \
      --city "${CITY[$c]}" --prior-alpha 1 \
      --out $R/replication/calibrazione/val_nn_${c}_s$s.csv \
      --dump-probs     $R/replication/probsval/nn_test_${c}_s$s.npz \
      --dump-probs-val $R/replication/probsval/nn_${c}_s$s.npz
  done
done
cd ../baselines
# idem gomo_lgb_fair.py -> val_gb_* e probsval/gb_*
cd ..
```

**Perché**: la convenzione canonica di R1 stima il calibratore sulla **validazione**.
Senza `--dump-probs-val` l'unico confronto disponibile è l'oracolo, che non è
dispiegabile. **Alimenta**: §8.2 Tabella 23, §8.7.3 Tabelle 86–87.

### 7.4 Regime severo (→ §8.3)

```bash
cd models
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    O=$R/replication/sparse/fix_sparse_${c}_s$s.csv
    [ -s "$O" ] || poetry run python gomo_sparse.py \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" \
      --modes none,fixed,adaptive --inductive --no-coords \
      --mask structured --obs-frac 0.4 --seed $s --city "${CITY[$c]}" \
      --out "$O" --dump-probs $R/replication/probs/fix_sparse_${c}_s$s.npz
  done
done
cd ..
```

**Perché**: R3 è misurato sul braccio a **grafo dato**, l'unico dispiegabile su un tratto
mai sensorizzato. Il braccio adattivo è un limite superiore trasduttivo.
**Alimenta**: §8.3 Tabelle 27–29 e la scomposizione, §8.5 Tabella 51.

> ⚠ **I tre bracci nella stessa invocazione.** `run_replication.py` invoca `sparse` con
> `--modes none,adaptive` e **non produce quindi la misura dichiarata di R3**.

### 7.5 Riferimenti di interpolazione (→ §8.3.4)

```bash
cd models
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    poetry run python gomo_sparse.py --targets "${T[$c]}" --graph "${G[$c]}" \
      --sensors "${S[$c]}" \
      --modes none,idw,idw_dist,knn,nbr_idw,nbr_prior \
      --inductive --no-coords --mask structured --obs-frac 0.4 \
      --calib-mode weighted --seed $s \
      --out $R/replication/sparse/spatial_ref3_${c}_s$s.csv
  done
done
cd ..
```

**Perché**: verifica che il denominatore di R3 non sia un riferimento debole.
**Alimenta**: §8.3.4, Tabelle 34–36.

`--calib-mode weighted` è predefinito e stima la mappa `p ∝ w·f`, che minimizza la
metrica pesata. La variante `frequency` è non calibrata.

### 7.6 Grafo dato nel compito denso (→ §8.5)

```bash
cd models
for c in d8_2024 d15_2024 d8_2023; do
  for s in 0 1 2 3 4; do
    O=$R/replication/suite/fixdensefix_${c}_s$s.csv
    [ -s "$O" ] || poetry run python gomo_classify.py \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" \
      --backend torch --modes none,fixed --seed $s --city "${CITY[$c]}" \
      --prior-alpha 1 --out "$O" \
      --dump-probs $R/replication/probs/fixdensefix_${c}_s$s.npz
  done
done
cd ..
```

**Perché**: il braccio `fixed` consuma l'adiacenza fornita, quindi era degenere sui
contesti a spire. **Alimenta**: §8.5 Tabelle 48 e 50, e il confronto fra regimi.

**Solo i tre contesti a spire**: sulle città `weight` è già la distanza.

**Alimenta anche la scomposizione di R2** in propagazione e vettori indicizzati sul
singolo nodo: la prima è il confronto `none → fixed` di questa campagna, la seconda il
residuo `fixed → adaptive`, con il ramo adattivo dalla campagna di §7.1.

> ⚠ **La scomposizione va calcolata appaiata per seme**, come quella del regime severo
> (§8.3), non come residuo algebrico fra rapporti di medie. Le due convenzioni qui
> coincidono entro un centesimo, perché i contributi sono piccoli, ma il residuo
> `1 − (1−R2)/(1−propagazione)` **divide per un denominatore prossimo a zero** — e su due
> contesti negativo — quindi è instabile per costruzione. L'appaiamento fornisce inoltre
> gli intervalli, che il residuo non ha.

**Collaudo**: il braccio `none` non consuma l'adiacenza e deve riprodurre i valori
precedenti.

### 7.7 Geometria (→ §8.3.2)

```bash
poetry run python make_geo_sweep.py --sweep --compact-n 99 \
  --sensors $D2/t4cmad_sensors.csv --targets $D2/targets_t4cmad_d8.npz --citta madrid
# idem melbourne

cd models
for g in $R/geo_sweep/*.pkl; do
  tag=$(basename $g .pkl)
  for s in 0 1 2 3 4; do
    poetry run python gomo_sparse.py --targets <contesto del tag> --graph "$g" \
      --sensors <anagrafica> --modes none,fixed --inductive --no-coords \
      --mask structured --obs-frac 0.4 --seed $s \
      --out $R/replication/geo/geo_${tag}_s$s.csv
  done
done
cd ..
```

**Perché**: verifica se il valore della propagazione dipenda dalla spaziatura fra
sensori, controllando per selezione geografica a numerosità costante.
**Alimenta**: §8.3.2, Tabelle 29–32.

**Solo il braccio a grafo fisso**: la variante adattiva genera il grafo da vettori
appresi per nodo e confonderebbe propagazione e identità.

**Le covariate vanno prodotte prima** e definiscono quali configurazioni entrano nel
blocco principale: solo quelle a connettività ≥ 0,99.

### 7.8 Inserimento di un sensore nuovo (→ §8.4)

```bash
cd models
for c in mad lon mel; do
  for s in 0 1 2; do
    poetry run python gomo_onboard.py --targets <contesto> --graph <grafo> \
      --sensors <anagrafica> --seed $s --out $R/replication/onboard/onboard_${c}_s$s.csv
    poetry run python gomo_onboard.py <...> --hist-mode both --seed $s \
      --out $R/replication/onboard/onboardC_${c}_s$s.csv
  done
done
cd ..
```

**Perché**: misura quanto tempo di osservazione serve perché un sensore nuovo diventi
utile quanto uno con lunga storia. **Alimenta**: §8.4, Tabelle 41–42.

| config | comando | blocco | profilo |
|---|---|---|---|
| base | `--hist-mode summary` | 8 dim. | assente |
| B | `--hist-mode profile` | 10 dim. | presente |
| C | `--hist-mode both` | 16 dim. | presente |
| D | `--hist-mode summary --hist-dim 10` | 10 dim. | **azzerato** |
| E | `--hist-mode summary --hist-dim 16` | 16 dim. | **azzerato** |

**D ed E sono i controlli a capacità appaiata**, solo su Melbourne. Il confronto
principale è **C − E**: stessa capacità, differisce per il solo contenuto.

> ⚠ **B ha tre semi, le altre cinque.** Il confronto appaiato usa i soli semi comuni, e
> la differenza delle medie di tabella non lo riproduce.

### 7.9 Identità di nodo (→ §8.6.1)

```bash
poetry run python analisi/genera_descrittori.py --out-dir descrittori

cd models
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    poetry run python gomo_classify.py --targets "${T[$c]}" --graph "${G[$c]}" \
      --sensors "${S[$c]}" --backend torch --modes none --seed $s \
      --city "${CITY[$c]}" --prior-alpha 1 \
      --emb 0 --node-desc $R/descrittori/${c}_d16.npy --desc-proj 8 --desc-hidden 32 \
      --out $R/replication/identita/a6N8_${c}_s$s.csv \
      --dump-probs $R/replication/probs/a6N8_${c}_s$s.npz
  done
done
cd ..
```

**Perché**: verifica se il residuo di identità che i vettori liberi aggiungono sopra la
media storica sia raggiungibile da statistiche **osservabili**, e quindi dispiegabile su
un tratto mai sensorizzato. **Alimenta**: §8.6.1, Tabella 52.

| cella | comando |
|---|---|
| A | `--emb 8` |
| C | `--emb 0` |
| P2 / P8 | `--emb 0 --node-desc <npy> --desc-proj 2` o `8` |
| N8 | `--emb 0 --node-desc <npy> --desc-proj 8 --desc-hidden 32` |

**Le statistiche sono calcolate sul solo addestramento** (§3.5). **Il collaudo** è la
riproduzione della cella completa.

```bash
cd models
poetry run python gomo_ign.py --model transductive --statics x-y-degree --seed 0 \
  --out $R/replication/identita/ign_mad_s0_x-y-degree.csv
cd ..
```

**Perché**: verifica se gli attributi cartografici ricostruiscano l'identità.
**Alimenta**: §8.6.1, Tabella 53.

> ⚠ Il peggioramento misura **la copertura degli attributi**, non il loro potere
> informativo: il numero di corsie è disponibile per una quota molto diversa fra le città.

### 7.10 Meteo (→ §8.6.2)

```bash
cd models
for c in t4cmad t4clon t4cmel; do
  for s in 0 1 2 3 4; do
    for V in reale permutato; do
      O=$R/replication/meteo/wx_${V}_${c}_s$s.csv
      [ -s "$O" ] && continue
      EXTRA=""; [ "$V" = "permutato" ] && EXTRA="--wx-permuta"
      poetry run python gomo_weather_ablation.py --targets "${T[$c]}" --weather "${W[$c]}" \
        --seed $s --epochs 30 --patience 999 --eval-epochs 20,25,30 $EXTRA \
        --out "$O" --dump-probs $R/replication/probs_wx/wx_${V}_${c}_s$s
    done
  done
done
cd ..
```

**Perché**: la permutazione fra giornate dello stesso mese e categoria feriale conserva
distribuzione, persistenza e scala dei canali e distrugge il **solo** allineamento
temporale col bersaglio. È l'unico controllo che separa il contenuto informativo dal
costo strutturale di ampliare l'ingresso. **Alimenta**: §8.6.2, Tabella 61.

**Epoche fisse e arresto anticipato disattivato**: con l'arresto anticipato il punto di
arresto diventerebbe una variabile del confronto.

**Collaudo**: lo script addestra entrambi i rami in un'unica esecuzione, quindi il ramo
privo di meteo è prodotto due volte per seme e **a parità di seme deve coincidere**.

| configurazione | file | contesti | semi |
|---|---|---|---|
| ablazione delle cinque variabili | `weather_abl_*` | d8/2024 + tre città | 3 |
| attribuzione (sola precipitazione) | `weather_abl_*_precip` | Londra, Melbourne | 3 |
| rumore, un canale e cinque | `weather_placebo{1,5}_*` | Londra, Melbourne | 3 |
| ablazione: concatenazione e FiLM | `wgate_{concat,film}_*` | Londra, Melbourne | 3 |
| rumore sotto condizionamento | `wgate_placebo_*` | Londra, Melbourne | 3 |
| rimozione dei canali temporali | `wnotime_*` | Londra, Melbourne | 3 |
| **permutazione** | `wx_{reale,permutato}_*` | tre città | **5** |

> ⚠ **La catena si restringe da quattro contesti a due dopo il primo anello.** Le
> spiegazioni alternative del degrado non sono state messe alla prova su d8/2024 e Madrid.

### 7.11 Validazione co-localizzata (→ §8.6.3, §8.6.4)

```bash
cd data_collection
T4=traffic4cast/MADRID_2022
ARG=(--gomo-targets go-mo/gomo/targets_2021_urb_d8.npz
     --gomo-sensors go-mo/gomo/traffic_sensors.csv
     --t4c-nodes  $T4/road_graph_nodes_osm.parquet
     --t4c-edges  $T4/road_graph_edges_district.parquet
     --speed-dir  $T4/speed_classes/madrid)
poetry run python t4c_crossval.py "${ARG[@]}" --out crossval_results.csv
poetry run python t4c_crossval.py --exclude-empty "${ARG[@]}" --out crossval_results_noempty.csv
poetry run python t4c_crossval.py --max-dist 30 "${ARG[@]}" --out crossval_results_d30.csv
cd ..
```

**Perché**: verifica l'assunzione su cui poggiano tre dei sei contesti, cioè che il
fattore ricostruito rappresenti la congestione sperimentata. **Alimenta**: §8.6.3,
Tabelle 62–64.

> ⚠ **Il perimetro è d8/2021**, non d8/2024: le sonde coprono giugno–dicembre 2021 e non
> c'è sovrapposizione. Confrontare anni diversi dà zero istanti in comune.

I criteri di allineamento sono **prudenzialmente poco restrittivi**: con criteri severi
una bassa concordanza potrebbe dipendere dall'allineamento.

### 7.12 Verifiche di validità (→ §8.7.2)

```bash
# --- soglie di classe: dopo genera_varianti_soglia.py (§4.2) -----------------
# Tre script perche' la tabella riporta R1, R2 e R3 insieme: l'omogeneita' va
# garantita su ciascuna riga, non solo su R3. Cinque semi e riferimento
# tabellare sulla popolazione ristretta, come le tabelle di §8.1 e §8.2.
for v in g075 g085; do
  Dg=$R/data_collection/traffic4cast/MADRID_2022/gomo_fmt_$v
  c=t4cmad_$v
  for s in 0 1 2 3 4; do
    O=$R/replication/sparse/fix_sparse_${c}_s$s.csv
    [ -s "$O" ] || poetry run python models/gomo_sparse.py \
      --targets $Dg/targets_t4cmad_d8.npz --graph $Dg/t4cmad_routes-graph.pkl \
      --sensors $Dg/t4cmad_sensors.csv \
      --modes none,fixed,adaptive --inductive --no-coords --mask structured \
      --obs-frac 0.4 --seed $s --city madrid --out "$O" \
      --dump-probs $R/replication/probs/fix_sparse_${c}_s$s.npz

    O=$R/replication/suite/fix_classify_${c}_s$s.csv
    [ -s "$O" ] || poetry run python models/gomo_classify.py \
      --targets $Dg/targets_t4cmad_d8.npz --graph $Dg/t4cmad_routes-graph.pkl \
      --sensors $Dg/t4cmad_sensors.csv --backend torch --modes none,adaptive \
      --seed $s --city madrid --prior-alpha 1 --out "$O" \
      --dump-probs $R/replication/probs/fix_classify_${c}_s$s.npz

    O=$R/replication/suite/lgbristr_${c}_s$s.csv
    [ -s "$O" ] || poetry run python baselines/gomo_lgb_fair.py \
      --targets $Dg/targets_t4cmad_d8.npz --graph $Dg/t4cmad_routes-graph.pkl \
      --sensors $Dg/t4cmad_sensors.csv --seed $s --city madrid --num-threads 5 \
      --out "$O" --dump-probs $R/replication/probs/lgbristr_${c}_s$s.npz
  done
done 2>&1 | tee -a $R/log/soglie_omogenee.log

# finestra d'ingresso
cd models
for WIN in 4 12 24; do
  for s in 0 1 2; do
    poetry run python gomo_weather_ablation.py --win $WIN --seed $s \
      --targets "${T[t4cmad]}" --weather "${W[t4cmad]}" \
      --out $R/replication/validita/winabl_w${WIN}_s${s}.csv
  done
done
cd ..

# STAEformer a scala piena: --dim e' PER EMBEDDING, quella di modello vale 4x
cd baselines
for c in t4cmad t4clon; do
  for s in 0 1 2; do
    poetry run python gomo_sota_baselines.py --model staeformer --dim 38 --layers 3 \
      --targets "${T[$c]}" --graph "${G[$c]}" --sensors "${S[$c]}" --seed $s \
      --out $R/replication/validita/stae_full_${c}_s$s.csv
  done
done
cd ..

# MLP per-nodo
cd models
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  for s in 0 1 2; do
    poetry run python gomo_classify.py --targets "${T[$c]}" --graph "${G[$c]}" \
      --sensors "${S[$c]}" --backend torch --modes stid --seed $s \
      --city "${CITY[$c]}" --out $R/replication/validita/stid_${c}_s$s.csv
  done
done
cd ..
```

**Perché**: verifica che le conclusioni reggano al variare di una scelta di costruzione.
**Alimenta**: §8.7.2 Tabelle 76–80, §8.7.3 Tabelle 72–74.

> ⚠ **Le tre righe della tabella vanno prodotte con le stesse definizioni.** La
> campagna precedente, generata da `run_replication.py`, aveva tre semi, il riferimento
> tabellare sulla popolazione piena e **nessun braccio a grafo fisso**, quindi R3 non era
> ricalcolabile sulla definizione corrente e le righe non erano confrontabili fra loro.
>
> **Collaudo del confronto**: il numero di nodi valutati e la copertura realizzata dalla
> maschera devono essere **identici** nelle tre varianti, poiché l'anagrafica e il grafo
> sono i medesimi e il generatore della maschera non dipende dalle etichette. Se
> differiscono, il confronto non isola la sola definizione delle classi.

**Non-debolezza del riferimento**, verifica post-hoc dichiarata come tale:

```bash
--lambda-l1 8.544 --lambda-l2 0.0958 --min-data-in-leaf 10
```

Configurazione della soluzione seconda classificata a Traffic4cast 2022. **Il numero di
foglie resta 5.000**: nella fonte cresce con la dimensione dei dati, e replicare il
valore più alto sarebbe stato meno fedele.

---

## 8. Rielaborazioni

Nessuna richiede addestramenti. Tutte in `analisi/`.

| Comando | Perché | Alimenta |
|---|---|---|
| `tabelle_prestazione.py` | tre tabelle di prestazione assoluta, correlazioni di rango fra metriche, rapporto di sovra-predizione (richiede `--dump-dir`) | §8.1, §8.1.2, Tabelle 17–19 |
| `priore_calibrato.py` | il priore è l'unico riferimento non calibrato rispetto alla metrica su cui è giudicato | §8.1, Tabella 20 |
| `r1_calibrazione.py` | R1 nelle tre convenzioni, dipendenza dalla metrica, intervalli appaiati | §8.2, Tabelle 23–25 |
| `r3_propagazione.py` | R3 in entrambe le varianti, lettura in richiamo, scomposizione, intervalli | §8.3, Tabelle 27–29 |
| `geometria_criteri.py` | i cinque criteri pre-registrati e i controlli negativi | §8.3.2, Tabelle 29–32 |
| `r4_configurazioni.py` | confronto **appaiato per seme** fra configurazioni, che `onboard_aggregate.py` non fa | §8.4, Tabella 42 |
| `figura_recupero.py` | recupero per storia osservata, figura in scala logaritmica | §8.4, Tabella 44, Figura 8 |
| `semi_equivalenza.py` | numerosità necessaria a decidere l'equivalenza nella fascia | §8.8.3, Tabella 82 |
| `struttura_spaziale.py` | correlogramma, indice di Moran e varianza comune sui soli dati | §3, §8.3, §10 |
| `costo_campagna.py` | invocazioni e ore effettive dalle date dei file | §11 |
| `identita_descrittore.py` | recupero del divario di identità da statistiche osservabili | §8.6.1, Tabella 52 |
| `meteo_permutazione.py` | collaudo, ablazione, curvatura, potere del test per variabile | §8.6.2, Tabella 61 |
| `validazione_colocalizzata.py` | anello, scomposizione dell'accoppiamento su scala di Gini, aggregazione fra corsie | §8.6.4, Tabelle 65–67 |
| `lettura_operativa.py` | decadimento per orizzonte, punto di lavoro, dominanza a richiamo appaiato | §8.6.5–8.6.7 |
| `sensibilita_perimetro.py` | sensibilità del vantaggio medio a dove è posta la soglia di richiamo | §8.6.7 |
| `calibrazione.py` | affidabilità e risoluzione, costruzione dei gruppi, i quattro vincoli | §8.7.3, Tabelle 86–87 |
| `effetti_misti.py` | modello a effetti misti e covariata di copertura | §8.8, Tabella 89 |
| `r1_ricampionamento.py` | R1 con incertezza a livello di dato | §8.2, §8.8 Tabella 89 |
| `r23_ricampionamento.py` | R2 e R3 con la medesima procedura | §8.3, §8.5, Tabella 89 |
| `r3_richiamo.py` | R3 letto in richiamo, stessa procedura | §8.3, Tabella 39 |
| `curva_precrec.py` | soglie equivalenti per contesto e figura della curva | §8.1.2, §8.2, Tabella 23 |
| `distribuzione_classi.py` | quote di classe per contesto e per perimetro | §3, §8.1, §8.2 |
| `recupero_f1.py` | F1-macro a soglie tarate su validazione | §8.1.2 |
| `meteo_ricampionamento.py` | permutazione del meteo, intervalli | §8.6.2, Tabella 61 |
| `decadimento_orizzonte.py` | entropia e richiamo per orizzonte, incroci, figura | §8.1.1, Tabella 22, Figura 5 |
| `costante_margine.py` | costante entropia-richiamo dai dump | §7.3, verifica in §8 |
| `costante_da_curve.py` | la stessa dalle curve salvate, priore incluso | §7.3, verifica in §8 |

**Le rielaborazioni hanno percorsi predefiniti piatti** — `replication/<nome>.csv` —
che è dove le campagne storiche hanno scritto. Dopo il riordino di §9 vanno invocate con
lo schema esplicito:

```bash
poetry run python analisi/tabelle_prestazione.py \
  --risultati "replication/aggregati/ALL_results.csv"
poetry run python analisi/r1_calibrazione.py \
  --probs replication/probs --probsval replication/probsval
poetry run python analisi/r3_propagazione.py \
  --sparse "replication/sparse/fix_sparse_{c}_s{s}.csv"
poetry run python analisi/lettura_operativa.py --sezioni dominanza --repliche 2000
poetry run python curva_precrec.py --figura figure/curva_precrec_81.png --riferimento ""
poetry run python curva_precrec.py --figura figure/curva_precrec_82.png
poetry run python recupero_f1.py
poetry run python distribuzione_classi.py
poetry run python analisi/lettura_operativa.py \
  --classify "replication/suite/fix_classify_{c}_s{s}.csv"
poetry run python analisi/identita_descrittore.py --dir replication/identita
poetry run python analisi/r4_configurazioni.py    --dir replication/onboard
poetry run python figura_recupero.py
poetry run python semi_equivalenza.py
poetry run python struttura_spaziale.py
poetry run python costo_campagna.py
poetry run python analisi/geometria_criteri.py    --geo-dir replication/geo
poetry run python analisi/meteo_permutazione.py   --dir replication/meteo
poetry run python analisi/effetti_misti.py \
  --classify "replication/suite/classify_{c}_s{s}.csv" \
  --lgb "replication/suite/lgbristr_{c}_s{s}.csv"
```

`censimento_csv.py` stampa in coda l'elenco aggiornato. **Le cartelle dei dump non
cambiano**: `probs/`, `probsval/` e `probs_wx/` restano dove sono.

> ⚠ **Le grandezze per orizzonte vanno lette dalla stessa campagna dell'aggregato.**
> I file di risultato hanno una riga per seme e orizzonte, e la media dei quattro
> riproduce le tabelle di prestazione assoluta: il collaudo è che lo scarto sia nullo.
> Una campagna che abbia il richiamo per orizzonte e un'altra che abbia solo
> l'entropia producono un confronto non omogeneo fra i due decadimenti.
>
> ⚠ **Gli incroci fra contesti si verificano sui livelli, non sui degradi.** Nel
> grafico del degrado relativo tutte le curve partono per costruzione dall'origine,
> e due contesti che si scambiano l'ordine non appaiono mai sovrapposti. Il
> controllo va fatto su tutte le coppie e tutti gli orizzonti, non sui soli estremi.

> ⚠ **`lettura_operativa.py` precalcola l'ordinamento delle probabilità.** Prima lo
> rifaceva a ogni replica, e con duemila repliche l'esecuzione superava l'ora senza
> completare i sei contesti; ora ne impiega ventidue minuti. Se una sezione di
> ricampionamento risulta lenta, il primo sospetto è un `argsort` dentro il ciclo.

> ⚠ **La frequenza della classe critica va riportata con perimetro E popolazione.**
> Variano indipendentemente, e non basta dichiararne uno. I quattro periodi danno
> valori che differiscono fino a **due punti e mezzo su Londra** — 15,37 per cento
> in addestramento contro 12,81 in prova — e la restrizione ai sensori agganciati
> al grafo ne sposta altri: su Melbourne i sette sensori esclusi hanno il 13,5 per
> cento di classe critica contro il 4,8 degli agganciati.
>
> **La convenzione delle tabelle di §8 è popolazione RISTRETTA su INTERO periodo**,
> che è quella su cui i modelli sono valutati. I pesi della metrica sono invece
> calcolati sul solo addestramento (§7.1): le due convenzioni non coincidono.
>
> ⚠ **L'aggancio dei sensori al grafo va fatto per identificativo, non per
> posizione.** L'indice nell'anagrafica non coincide con la colonna nella matrice
> dei bersagli: confonderli seleziona colonne sbagliate e produce frequenze
> plausibili ma false — su Madrid 8,86 per cento anziché 9,21.
>
> ⚠ **Un valore che non corrisponde ad alcun perimetro non è una frequenza.**
> `distribuzione_classi.py --cerca` lo verifica. Alla verifica, due valori presenti
> nel documento si sono rivelati un vantaggio percentuale lungo la curva e una
> quota oraria di un contesto diverso — non quote di popolazione.

> ⚠ **Un valore citato in più sezioni può non essere riportato in nessuna.** Il
> rapporto di sovra-predizione compariva in tre sedi che vi rimandavano e in una
> quarta che lo citava, senza essere mai tabulato: era ricalcolabile, ma il lettore
> non aveva modo di verificarlo. Vale la pena cercare i valori che il documento
> richiama senza mostrarli, non solo quelli che mostra in modo incoerente.
>
> ⚠ **Il rapporto di sovra-predizione è calcolato sulla configurazione priva di
> scambio spaziale**, non su quella con grafo, e viene dai dump di probabilità.
> Entrambe le cose vanno dichiarate: un lettore che trova il valore accanto a
> precisione e richiamo del classificatore principale assume l'altra configurazione.

> ⚠ **Contare i file non è contare le invocazioni.** Una corsa di calibrazione
> scrive `nn`, `nn_test` e `val_classify` insieme: contarli come tre campagne
> triplica il tempo attribuito. La firma sono mediane per invocazione identiche
> alla decima di minuto fra campagne diverse. Vanno raggruppate le scritture
> separate da pochi secondi — il conteggio è stabile fra 30 e 120 secondi.
>
> ⚠ **Le misure di struttura spaziale vanno calcolate sulle sole celle trafficate.**
> Sui contesti a velocità ricostruita il 77% delle celle ha fattore di congestione
> pari a uno per imputazione: una correlazione calcolata su quelle misura la regola
> deterministica, non il traffico.
>
> ⚠ **L'indice di Moran su k vicini confronta scale diverse.** L'ottavo vicino cade
> a 96 metri su Madrid e a 256 sui contesti a spire: l'indice misura quindi la
> correlazione a distanze diverse nelle due famiglie. Va riportato con la distanza
> mediana del k-esimo vicino accanto, e affiancato da un correlogramma a fasce
> fisse, che è l'unico confronto omogeneo.

> ⚠ **Il Friedman sulla fascia di testa legge `MODEL_leaderboard.csv`, non gli
> aggregati per esperimento.** Ricalcolarlo dai file di campagna dà valori diversi —
> 5,333 anziché 7,000 — perché le due fonti contengono campagne differenti per
> STAEformer e AGCRN. La fonte va replicata, non ricostruita.
>
> ⚠ **Un test di Friedman va riportato con il numero di trattamenti e di blocchi.**
> La statistica dipende da entrambi, e senza quei due numeri il valore non è
> verificabile. Va dichiarato anche il **valore p minimo ottenibile**: con tre
> trattamenti e tre blocchi le assegnazioni di rango sono 216 e la concordanza
> perfetta ne occupa 6, sicché il test non può scendere sotto 0,0278 e un esito
> non significativo dice poco.

> ⚠ **Il numero di repliche del ricampionamento va dichiarato accanto ai valori.**
> Le ampiezze ne dipendono, e su un contesto l'esito può cambiare: su d15/2024 la
> dominanza esclude lo zero per quattro decimi di punto a duemila repliche e per
> più di un punto a venti. Una tabella senza quel dato non è riproducibile.
>
> ⚠ **Un asse dei tempi a passo costante nasconde la saturazione.** Gli orizzonti
> di storia distano una, quattro, ventiquattro e centosessantotto ore: disposti a
> distanza uguale, il tratto fra un giorno e una settimana occupa lo spazio di
> quello fra un'ora e quattro, pur corrispondendo a sei volte più dati. La scala
> logaritmica è quella su cui la forma della curva si legge.
>
> ⚠ **Un punto definito per costruzione non va tracciato come se fosse misurato.**
> Il recupero a storia nulla vale zero per definizione ed è l'unico privo di barra:
> collocarlo su un asse logaritmico richiede una posizione arbitraria, e la
> pendenza del primo tratto che ne risulta viene letta come dato.

> ⚠ **La soglia del regime operativo non è il punto di lavoro.** Il richiamo alla
> regola della classe più probabile vale fra 0,594 e 0,770 secondo il contesto: una
> linea tracciata a 0,60 indica la soglia sotto la quale il confronto non è
> formulato, non il punto in cui i modelli operano. Nelle figure vanno distinti.
>
> ⚠ **Il riferimento tabellare nella campagna della curva esiste in due forme.**
> I file `precrec_*` contengono `lightgbm` sulla popolazione piena e solo su tre
> contesti; `metrics_lgbfair_*` contiene `lgb_fair` sulla ristretta su tutti e sei.
> La correzione di §6.2.1 vale anche qui: va usata la seconda.

**Gli intervalli a livello di dato hanno tre convenzioni**, che valgono per tutti e
tre gli obiettivi e vanno dichiarate in didascalia:

> **La stima puntuale viene dai file di risultato, la larghezza dal ricampionamento sui
> dump, e l'intervallo è centrato sulla stima.** Le due fonti valutano popolazioni che
> differiscono dell'ordine del per mille — il dump conserva alcune celle che il file di
> risultato esclude — e su un rapporto fra grandezze vicine lo scarto si amplifica fino a
> due decimi di punto. Del ricampionamento si usa quindi la grandezza che misura davvero,
> cioè l'ampiezza.
>
> **Si ricampionano i soli nodi effettivamente valutati.** Nel regime severo sono poco più
> della metà del totale: includere quelli non valutati diluirebbe il ricampionamento e
> comprimerebbe la variabilità.
>
> **Il numero di sensori si legge dal contesto, non si deduce dai dump del regime severo**,
> dove metà delle posizioni è vuota e la deduzione automatica restituisce un valore che non
> corrisponde ad alcun sensore.

> ⚠ **Il numero di nodi non è salvato nei dump** e va ricostruito da `idx`, che è l'indice
> piatto della matrice tempo × nodi. Il criterio è la varianza fra gruppi della quota di
> classe critica, prendendo il divisore **minimo** che raggiunge il novanta per cento del
> massimo: l'argmax restituisce un multiplo, perché con un divisore doppio ogni sensore si
> divide in due gruppi e la varianza resta alta.

```bash
poetry run python stats_tests.py \
  --leaderboard replication/aggregati/MODEL_leaderboard.csv \
  --replication replication/aggregati/ALL_results.csv \
  --out stats_report.txt
poetry run python stats_tests.py --unita citta <...> --out stats_report_citta.txt
```

**Perché**: test dei segni, Friedman ai tre livelli, validazione incrociata, blocco delle
statiche. **Alimenta**: §8.8.

`--escludi-ctx` esclude di default le rietichettature, che non sono contesti indipendenti.

```bash
poetry run python patch_stats_friedman.py --verifica
poetry run python patch_stats_friedman.py
```

**Perché**: aggiunge il test di Friedman **del protocollo** — i quattro modelli presenti
in tutte le configurazioni — che lo script non calcolava, e il valore p esatto per
enumerazione dove il campionamento non risolve valori piccoli. **Alimenta**: §8.8.2.

```bash
cd models
poetry run python onboard_aggregate.py --glob "onboard_mel_s?.csv" --label Melbourne
cd ..
poetry run python placement_analysis.py
poetry run python profile_identity_check.py
```

**Perché**: curva di recupero di una configurazione, e le tre diagnostiche di §8.4.
**Alimenta**: §8.4.

---

## 9. Manutenzione del repository

Nessuno dei due script cancella nulla.

```bash
poetry run python inventario.py --verifica
poetry run python inventario.py --genera-script pulizia.sh

poetry run python censimento_csv.py
poetry run python censimento_csv.py --firma 7
poetry run python censimento_csv.py --genera-script riordino.sh

poetry run python confronta_generazioni.py
```

**Perché**: `inventario.py` raccoglie i log in `log/` e sposta archivi e duplicati;
`censimento_csv.py` raggruppa i CSV per **firma di contenuto** e propone una destinazione;
`confronta_generazioni.py` distingue copie, arricchimenti e riesecuzioni fra campagne.

**Ordine del riordino:**

```bash
# 1. fotografia, prima di toccare nulla
poetry run python censimento_csv.py > censimento_prima.txt 2>&1
tar czf ../OR3_csv_backup_$(date +%Y%m%d).tgz \
  $(find . -name "*.csv" -not -path "./_archivio/*")

# 2. genera e RILEGGI, verificando che non tocchi i dati sorgente
poetry run python censimento_csv.py --genera-script riordino.sh
grep "data_collection\|austin/" riordino.sh    # deve essere vuoto

# 3. esegui e verifica
bash riordino.sh
find replication -name "*.csv" | sed 's|/[^/]*$||' | sort | uniq -c
ls replication/*.csv 2>/dev/null | wc -l        # deve dare zero

# 4. controlla che le rielaborazioni trovino ancora i file
poetry run python analisi/tabelle_prestazione.py \
  --risultati "replication/aggregati/ALL_results.csv" 2>&1 | head -20
```

Se il passo 2 stampa anche una sola riga, **non eseguire**: significa che un dato
sorgente è finito fra i candidati allo spostamento.

> ⚠ **Sette cartelle sono intoccabili**: `data_collection`, `austin`, `descrittori`,
> `geo_sweep`, `prereg`, `papers`, `kit_archivio`. Contengono dati sorgente, non risultati.
>
> ⚠ **Le anagrafiche replicate non sono duplicati.** Le revisioni di
> `traffic_sensors.csv` vanno tenute tutte, e `t4cmad_sensors.csv` è ripetuto in ogni
> cartella `gomo_fmt_g*` perché ciascuna variante è un contesto autonomo.
>
> ⚠ **La segregazione non può essere decisa dal solo prefisso.** La stessa campagna
> può essere superata su alcuni contesti e valida su altri, perché il difetto che l'ha
> resa obsoleta non tocca tutte le famiglie. `camp_sparse` è superata sui tre contesti a
> velocità ricostruita, dove l'adiacenza era degenere, ma **è l'unica fonte di R3 sulle
> tre città**, dove `weight` conteneva già la distanza: segregarla lì significa perdere
> metà della tabella.
>
> Dopo il riordino, verificare sempre che le rielaborazioni trovino ancora tutti i
> contesti, non solo che i file siano stati spostati.

> ⚠ **Due categorie da segregare e non cancellare**: `superati`, anteriori alla patch con
> modelli che consumano il grafo; e `storici`, rifatti da una campagna successiva.

**Spostare i CSV rompe gli schemi predefiniti degli script di analisi**, che accettano il
percorso come argomento. Le cartelle dei dump non vanno spostate.

---

## 10. Costo di calcolo

Stima dal conteggio delle invocazioni e dai tempi medi, **non misurata**.

| Blocco | Invocazioni | Ore |
|---|---|---|
| suite a otto modelli | ~180 | 90–110 |
| R1 appaiata e calibrazione | ~120 | 55–70 |
| regime severo, tre bracci | ~30 | 45–60 |
| geometria | 115 | 60–75 |
| inserimento | ~70 | 35–45 |
| meteo | ~90 | 40–50 |
| identità e descrittori | ~120 | 25–35 |
| **totale dichiarato** (campagne principali) | **~1.065** | **350–400** |
| **totale MISURATO** (tutte, incluse minori e collaudi) | **~1.650** | **507** |

I valori dichiarati riguardano le sole campagne principali; quelli misurati
comprendono tutto ed escono da `costo_campagna.py`, che conta le invocazioni
raggruppando i file scritti dalla medesima corsa e somma i soli intervalli
inferiori all'ora, trattando i più lunghi come pause fra sessioni.

**Arco di calendario: 62 giorni, con utilizzo del 34%.** Durata mediana di
un'invocazione: 18 minuti; le campagne più onerose — modelli allo stato
dell'arte — ne richiedono circa cinquanta. Le campagne rifatte o superate
valgono l'8% del totale, ed è il costo delle correzioni della revisione.

---

## 11. Avvertenze

### 11.1 Le cinque che fanno sbagliare i risultati

**`ALL_results.csv` contiene più esperimenti**: filtrare `experiment`.

**Il grafo GO-MO ha `weight` = similarità**, non distanza. Applicare la patch di §6 prima
delle campagne.

**I bracci di un confronto nella stessa invocazione** (§7.3).

**Il riferimento tabellare va ristretto** con `--graph` e `--sensors`. Gli orchestratori
non lo fanno.

**`--dump-probs` ovunque disponibile**: senza, le rielaborazioni non sono eseguibili.

### 11.2 Le cinque che fanno leggere male i risultati

**Le due incertezze non sono intercambiabili**, ma il rapporto **non è una costante**:
vale fino a 5,3 volte su R1, fra 1,1 e 2,0 su R3 e fra 0,6 e 1,2 su R2. Dipende da due
cose — il numero di sensori del contesto, perché con più blocchi ogni replica media su
una popolazione più stabile, e la natura del confronto, perché R2 e R3 oppongono due
configurazioni del medesimo modello e la variabilità a livello di dato si cancella in
parte nel confronto appaiato. **Un fattore uniforme non va dichiarato.**

**Aumentare i semi non rende decidibile un test di equivalenza il cui centro è fuori
dal margine.** La semiampiezza vale `t(n−1)·s/√n` e si riduce con la numerosità, ma la
stima puntuale non si sposta: dove la differenza media eccede già il margine, nessun
numero di semi porta l'intervallo dentro. Prima di calcolare quanti ne servano va
verificato dove cade il centro — altrimenti si risponde con un numero a una domanda
che non ne ammette.

**Aggregare sugli orizzonti non riduce la dispersione fra semi.** Su cinque contesti
su sei la aumenta, con rapporti da 1,05 a 3,49 fra i quattro orizzonti e i soli quindici
minuti. Mediare orizzonti eterogenei non equivale a mediare repliche della stessa
grandezza: a centoventi minuti i modelli divergono di più e le inizializzazioni pesano
maggiormente.

**Le ampiezze non sono confrontabili fra metriche**: l'enunciato sostenibile è
l'invarianza di segno.

**Le quote sono rapporti** e vanno lette accanto al divario assoluto.

**Le scomposizioni vanno appaiate per seme**, non calcolate come residuo fra rapporti
di medie: il residuo divide per un denominatore che può essere prossimo a zero, e non
fornisce intervalli. La convenzione va inoltre **la stessa in tutte le sezioni**,
altrimenti due scomposizioni dello stesso tipo non sono confrontabili.

**Le differenze di AUC non sono additive**: per ripartire un divario serve la scala di
Gini.

**Una metrica su sottopopolazione rara ha potenza minore**: un esito non decidibile lì
non è confrontabile con uno deciso altrove.

### 11.3 Lacune dichiarate

| Lacuna | Sezione | Stato |
|---|---|---|
| soglia sulla distanza dal profilo cittadino | §8.6.1 | **colmata** |
| mediane di somiglianza e stabilità split-half | §8.4 | **colmata** |
| valori puntuali della diagnostica di posizionamento | §8.4 | **colmata** |
| mediazione fra carreggiate opposte | §10 | **colmata** (§3.1.2) |
| punto di lavoro sulle sole celle trafficate | §8.6.6 | non eseguito |
| controllo randomizzato su bersaglio continuo | §8.3.2 | infrastruttura assente |
| separazione fra regime e tecnologia | §8.6.4 | **non risolvibile** |
| rango dell'adiacenza adattiva | §8.6.6 | fuori dal disegno |

---

## 12. Nota finale

**Dove il README dichiara un collaudo, quel collaudo va eseguito prima di leggere i
risultati.** Sono controlli che intercettano difetti silenziosi — l'adiacenza degenere, la
popolazione disallineata, il ramo base che non coincide fra due varianti — e ciascuno di
essi, in questa campagna, ha già intercettato qualcosa almeno una volta.
