#!/bin/bash
# Sposta sui P-core i run della campagna che nascono in classe background.
# Uso:  sudo ./pcore_watch.sh [intervallo_secondi]   (default 300)
INT=${1:-300}
LOG=/tmp/pcore_watch.log
VISTI=""
echo "[$(date +%H:%M:%S)] avvio, intervallo ${INT}s" | tee -a "$LOG"
while true; do
  ATTIVI=$(pgrep -f "gomo_(classify|sparse|lgb_fair)\.py" 2>/dev/null)
  for p in $ATTIVI; do
    case " $VISTI " in
      *" $p "*) ;;                       # gia trattato
      *)
        if taskpolicy -B -p "$p" 2>/dev/null; then
          VISTI="$VISTI $p"
          CMD=$(ps -o command= -p "$p" | grep -o "probs/[a-z0-9_]*\.npz" | head -1)
          PRI=$(ps -o pri= -p "$p" | tr -d " ")
          [ -n "$CMD" ] && echo "[$(date +%H:%M:%S)] spostato PID $p  pri=$PRI  $CMD" | tee -a "$LOG"
        fi ;;
    esac
  done
  sleep "$INT"
done
