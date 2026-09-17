#!/usr/bin/env bash
# build_results.sh — MOTION OR3
# Costruisce la cartella results/ con tutte le fonti dei risultati (§8),
# organizzate per esperimento, con aggregati rigenerati e MANIFEST.
# Uso: ./build_results.sh   (dalla radice OR3/; idempotente, sovrascrive results/)
set -u

cd "$(dirname "$0")"
if [ ! -f run_replication.py ]; then
  echo "ERRORE: lanciare dalla radice OR3/ (run_replication.py non trovato)"; exit 1
fi

R=results
rm -rf "$R"
mkdir -p "$R"/{suite,onboarding,componenti,validita,fondativi}
cpq() { cp -f "$@" 2>/dev/null || true; }   # copia senza bloccarsi sui glob vuoti

echo "== [1/6] suite e statistica =="
cpq replication/ALL_results.csv replication/MODEL_leaderboard.csv replication/FINDINGS_check.csv "$R"/suite/
cpq stats_report.txt "$R"/suite/
cpq replication/classify_d8_p85tr_*.csv replication/lgb_d8_p85tr_*.csv replication/sparse_d8_p85tr_*.csv "$R"/suite/

echo "== [2/6] onboarding (R4): grezzi =="
find models -name "onboard*_s?.csv" -exec cp -f {} "$R"/onboarding/ \; 2>/dev/null
find models -name "onboard*_s?_pernode.csv" -exec cp -f {} "$R"/onboarding/ \; 2>/dev/null
cpq placement_Madrid.csv placement_Londra.csv placement_Melbourne.csv "$R"/onboarding/
cpq profcheck.txt simnode.txt subsetcheck.txt "$R"/onboarding/
cpq models/onboardB.log models/onboardC.log models/onboard_rerun.log "$R"/onboarding/
cpq models/onboard_base_permcheck_*.log models/onboard_base_recheck_*.csv "$R"/onboarding/

echo "== [3/6] onboarding: rigenero gli aggregati (6 curve) =="
AGG="$R/onboarding/onboard_aggregates.txt"; : > "$AGG"
if [ -f models/onboard_aggregate.py ]; then
  ( cd models
    for spec in \
      "onboard_mad_s?.csv|Madrid (base)" \
      "onboard_lon_s?.csv|Londra (base)" \
      "onboard_mel_s?.csv|Melbourne (base)" \
      "onboardC_mad_s?.csv|Madrid (statistiche + bande orarie)" \
      "onboardC_lon_s?.csv|Londra (statistiche + bande orarie)" \
      "onboardC_mel_s?.csv|Melbourne (statistiche + bande orarie)"; do
      glob="${spec%%|*}"; label="${spec##*|}"
      poetry run python onboard_aggregate.py --glob "$glob" --label "$label" 2>&1
      echo
    done ) >> "$AGG"
  echo "   -> $AGG"
else
  echo "   [warn] models/onboard_aggregate.py non trovato: salto la rigenerazione"
fi

echo "== [3b] quarantena artefatti invalidi (sparse_geo_* duplicati) =="
for f in models/sparse_geo_long_s?.csv models/sparse_geo_short_s?.csv; do
  [ -f "$f" ] && mv -f "$f" "$f.INVALID" && echo "   -> $f.INVALID"
done

echo "== [4/6] componenti (RQ2) =="
find models -name "ign_*_s*.csv"    -exec cp -f {} "$R"/componenti/ \; 2>/dev/null
find models -name "weather_*.csv"   -exec cp -f {} "$R"/componenti/ \; 2>/dev/null
find models -name "winabl_*.csv"    -exec cp -f {} "$R"/componenti/ \; 2>/dev/null
find models -name "sparse_geoF_*.csv" -exec cp -f {} "$R"/componenti/ \; 2>/dev/null
cpq models/sparse_geoF.log geo_graph_short.pkl geo_graph_long.pkl make_geo_graphs.py geo_criteri_printout.txt "$R"/componenti/
cpq data_collection/crossval_results.csv "$R"/componenti/

echo "== [5/6] validita' e fondativi =="
cpq stae_full_*.csv "$R"/validita/
cpq models/gwn_results.csv models/stgnn_results.csv models/classify_results.csv \
    models/sparse_results.csv models/onboard_results.csv models/ign_results.csv "$R"/fondativi/
cpq baselines/lgb_fair_results.csv baselines/rnn_baseline_results.csv \
    baselines/sota_baseline_results.csv "$R"/fondativi/

echo "== [6/6] MANIFEST =="
cat > "$R"/MANIFEST.md << 'EOF'
# results/ — mappa fonte -> sezione (deliverable v4)

## suite/  (-> §8.1, §8.2–8.4, §8.8)
- MODEL_leaderboard.csv, ALL_results.csv: Tabella 11 e tabella del richiamo.
  AVVERTENZA: ogni aggregazione da ALL_results DEVE filtrare la colonna `experiment`
  (classify | lgb | rnn | sota | sparse), altrimenti GWN e priore si contaminano
  con le righe sparse.
- FINDINGS_check.csv: verdetti R1–R3 per contesto.
- stats_report.txt: IC e TOST per contesto (§8.2–8.4); trasversali (§8.8):
  segni 6/6 p=0,0156 (extra: vs GBDT 8/8 p=0,0039, perimetro da dichiarare),
  Friedman chi2=21,25 p=0,0034 (4 modelli comuni x 8 contesti — AGGIORNARE nel doc),
  crossval mediana 0,041 [0,034; 0,046].

## onboarding/  (-> §8.5)
- onboard[_C]_{mad,lon,mel}_s?.csv (+_pernode): grezzi per seme; C = profilo orario.
- onboard_aggregates.txt: le 6 curve rigenerate (base: 93/101/21 a 24h; profilo:
  82/85/53 — criterio invariato sulle citta', costo iniziale a 1h da dichiarare).
- placement_*.csv + simnode.txt: posizionamento, |rho| < 0,1 su tre citta'.
- profcheck.txt: natura dei profili (mediane 0,67/0,49/0,34; split-half 0,21/0,37/0,20).
  ESITO: Melbourne = identita' di forma INDIVIDUALE, NON "non stazionaria"
  (criterio pre-registrato su (b) smentito: 0,201 vs Madrid 0,208).
- subsetcheck.txt: pari difficolta' visti/tenuti-fuori su TRE citta' (a Melbourne
  i tenuti-fuori sono semmai piu' difficili: il mancato criterio non e' artefatto).

## componenti/  (-> §8.6, §8.7)
- ign_*_s*.csv: identita' dalle statiche (generatore vs trasduttivo).
- weather_*.csv: ablazione meteo + attribuzione precipitazione-sola.
- winabl_*.csv: finestra d'ingresso 1/3/6h (-> §8.7).
- sparse_geoF_*.csv + sparse_geoF.log + geo_graph_*.pkl + make_geo_graphs.py +
  geo_criteri_printout.txt: esperimento GEO valido (inductive-nocoords, criteri
  pre-registrati) -> GEOMETRIA CONFERMATA 3/3: short +10,3/+9,7/+9,2% vs long
  +0,2/+1,4/+0,5%; sanity adaptive +11,9/+10,8/+11,3. I vecchi sparse_geo_*
  sono DUPLICATI INVALIDI, quarantenati come .INVALID dal passo 3b.
- crossval_results.csv: 399 coppie spira–segmento (-> §8.6).

## validita/  (-> §8.7)
- stae_full_*.csv: STAEformer a scala piena, Madrid e Londra, 3 semi.

## fondativi/  (era a seme 0 su d8, -> §8.3–8.4 scomposizione)
- gwn_results.csv: none/fixed/adaptive con identita'. VERIFICATO: 0,8% = none->adaptive
  su MAE del fattore r (0,05973 -> 0,05926). Il «5,5%» NON e' ricostruibile da questi
  file: per decisione (ii) va riformulato senza cifra puntuale, con metrica dichiarata.
- stgnn_results.csv, classify_results.csv, sparse_results.csv, *_baseline_results.csv:
  altri bracci fondativi (attenzione alle metriche: MAE/F1 vs entropia pesata).

## suite/ — variante p85-train (-> §3.2.4, §7.2.7)
- *_d8_p85tr_*.csv: replica sulla variante a riferimento train-only. FINDINGS OK/OK/OK,
  ampiezze invarianti: eccezione p85 dichiarata e verificata (0,47% celle rietichettate).
- AVVERTENZA anagrafica: run sparse/onboard/ign GO-MO richiedono traffic_sensors.csv
  alla revisione HF 7b8dbd3476 (11/12/2025); il file pubblicato dal 6/7/2026 e' impoverito.

## Residui aperti (dettaglio in NOTA_RIPRESA_sessione.md)
- Coppia 0,943/0,942: non identificata (escluse le tre citta' del subset check);
  risolvere dalla frase di §8.5 che la cita.
- +10,8/+47,0 e 69%: candidato = confronto appaiato per seme base vs profilo
  su Madrid/Londra (i grezzi ci sono in onboarding/).
- Fonte del 127–158% della permutazione: script/run dell'epoca, non un flag attuale.
EOF

echo
echo "=== riepilogo ==="
find "$R" -type f | wc -l | xargs echo "file totali:"
du -sh "$R" 2>/dev/null
for d in suite onboarding componenti validita fondativi; do
  printf "  %-12s %s file\n" "$d" "$(find "$R/$d" -type f | wc -l | tr -d ' ')"
done
echo "results/ pronta. Per il kit sessione: allegare results/ (i *_pernode.csv sono"
echo "opzionali se pesano) + deliverable + NOTA_RIPRESA_sessione.md + README.md"
