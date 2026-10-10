#!/bin/sh
# Seconda ricognizione (sola lettura): la firma del ciclo nei log della geometria.
#     sh evoluzione/esperimenti/ricognizione_paper4_log.sh > /tmp/ricognizione_paper4_log.txt 2>&1
T() { printf '\n==== %s ====\n' "$1"; }
LOGS="log/geo_campagna.log log/geo_rimedio.log log/grafo_corretto.log densefix_corretto.log log/sparse_geo.log log/sparse_geoF.log results/componenti/sparse_geoF.log log/randk.log models/onboardB.log"

T "A. log: data di modifica, righe, righe con 'epoch'"
for f in $LOGS; do [ -e "$f" ] && { stat -f '%Sm %z %N' -t '%Y-%m-%d %H:%M' "$f"; printf '   righe %s, epoch %s, early-stop %s\n' "$(wc -l < "$f")" "$(grep -c 'epoch' "$f")" "$(grep -ci 'early' "$f")"; }; done

T "B. prime 12 righe di ogni log"
for f in $LOGS; do [ -e "$f" ] && { printf -- '-- %s\n' "$f"; head -12 "$f"; }; done

T "C. epoche massime per run (ultima riga 'epoch NN' prima di ogni cambio di modalita')"
for f in log/geo_campagna.log log/geo_rimedio.log log/grafo_corretto.log densefix_corretto.log; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; grep -o '^\[[^]]*\] epoch [0-9]*' "$f" | awk '{k=$1; e=$3+0; if(e>m[k])m[k]=e} END{for(k in m)print k, "max epoch", m[k]}' | sort | head -30; }
done

T "D. tempi nei log (sec, time, elapsed, s/ep, durata)"
for f in $LOGS; do [ -e "$f" ] && { printf -- '-- %s\n' "$f"; grep -in 'sec\|elapsed\|s/ep\|durata\|tempo\|time' "$f" | head -6; }; done

T "E. curve di validazione: prime 6 epoche del primo run di ogni log (convergono o no?)"
for f in log/geo_campagna.log log/geo_rimedio.log log/grafo_corretto.log densefix_corretto.log; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; grep -m6 'epoch 0[1-6]' "$f"; }; done

T "F. replication/geo: quanti file, date, intestazione e prima riga"
ls replication/geo | wc -l; ls -lt replication/geo | head -5; ls -lt replication/geo | tail -3
for f in replication/geo/geo_madrid_comp_q2050_s0.csv replication/geo/geo_melbourne_dec2_s4.csv; do [ -e "$f" ] && { printf -- '-- %s\n' "$f"; head -3 "$f"; }; done
ls geo_sweep | head -8; ls geo_sweep | wc -l

T "G. README: cosa dice su geometria, ciclo, validazione a 32 istanti"
grep -n 'geo_campagna\|geo_rimedio\|grafo_corretto\|densefix\|lotto per epoca\|un lotto\|32 istanti\|val_n\|n_val\|Tabell[ae] 3[2-6]\|Tabella 6[4-9]\|Tab\. 6[4-9]' README.md | head -30
sed -n 515,532p README.md

T "H. sonde 2021 / M30 2024 / Austin: dimensioni e chiavi"
ls -la data_collection/go-mo/gomo/targets_2021_urb_d8.npz data_collection/go-mo/gomo/traffic_data_2021.csv data_collection/go-mo/gomo/targets_2024_m30.npz data_collection/go-mo/gomo/tensors_2024_m30.npz data_collection/go-mo/gomo/adj_2024_m30.npy austin/radar/radar_completo.json austin/radar/Radar_Traffic_Counts_20260824.csv 2>&1
poetry run python - <<'EOF'
import numpy as np
for f in ("data_collection/go-mo/gomo/targets_2021_urb_d8.npz","data_collection/go-mo/gomo/targets_2024_m30.npz","data_collection/go-mo/gomo/tensors_2024_m30.npz"):
    try:
        z=np.load(f,allow_pickle=True); print(f, {k:(z[k].shape if hasattr(z[k],'shape') else type(z[k]).__name__) for k in z.files})
    except Exception as e: print(f, "errore", e)
EOF
ls data_collection/go-mo/gomo/gomo | head -12
T "fine"
