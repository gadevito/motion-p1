#!/bin/bash
# 1) attende che i due run LightGBM in corso completino
# 2) ferma il vecchio xargs (nato con taskpolicy -c utility)
# 3) rilancia il loop pulito, senza prefissi di classe QoS
R=~/Personal/MOTION/deliverables/OR3
OLD_XARGS=16688

echo "[$(date +%H:%M)] attesa completamento run in corso"
while true; do
  [ -s "$R/replication/probs/lgb_d8_2024_s4.npz" ] && \
  [ -s "$R/replication/probs/lgb_d15_2024_s0.npz" ] && break
  sleep 300
done
echo "[$(date +%H:%M)] entrambi completati, fermo il vecchio ramo"
kill $OLD_XARGS 2>/dev/null; sleep 5; pkill -f "gomo_lgb_fair.py" 2>/dev/null; sleep 5

echo "[$(date +%H:%M)] rilancio pulito"
cd "$R/baselines" || exit 1
for c in d8_2024 d15_2024 d8_2023 t4cmad t4clon t4cmel; do
  case $c in
    d8_2024)  T=$R/data_collection/go-mo/gomo/targets_2024_urb_d8.npz;  CITY=madrid ;;
    d15_2024) T=$R/data_collection/go-mo/gomo/targets_2024_urb_d15.npz; CITY=madrid ;;
    d8_2023)  T=$R/data_collection/go-mo/gomo/targets_2023_urb_d8.npz;  CITY=madrid ;;
    t4cmad)   T=$R/data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz;    CITY=madrid ;;
    t4clon)   T=$R/data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz;    CITY=londra ;;
    t4cmel)   T=$R/data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz; CITY=melbourne ;;
  esac
  for s in 0 1 2 3 4; do echo "$T $s $CITY $c"; done
done | xargs -P 2 -L 1 bash -c '
  NPZ='"$R"'/replication/probs/lgb_${3}_s${1}.npz
  [ -s "$NPZ" ] && { echo "salto $3 s$1"; exit 0; }
  poetry run python -u gomo_lgb_fair.py --targets $0 --seed $1 --city $2 \
    --num-threads 5 --out '"$R"'/replication/camp_lgb_${3}_s${1}.csv --dump-probs "$NPZ" \
    > /tmp/camp_lgb_${3}_s${1}.log 2>&1
  echo "[$(date +%H:%M)] fatto $3 seme $1"'
