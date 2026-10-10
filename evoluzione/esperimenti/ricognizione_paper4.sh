#!/bin/sh
# Ricognizione in SOLA LETTURA per le quattro domande della §1 del brief del Paper 4.
# Stampa percorsi reali, commit e date; non addestra, non scrive. Dalla radice OR3/:
#     sh evoluzione/esperimenti/ricognizione_paper4.sh > /tmp/ricognizione_paper4.txt 2>&1
T() { printf '\n==== %s ====\n' "$1"; }
G='git log --format=%h_%ad_%s --date=short'

T "0. repo"; git rev-parse --short=12 HEAD; git describe --tags --always 2>/dev/null; git status --short | head -8

T "1a. geometria: script e storia"
for f in make_geo_sweep.py make_geo_graphs.py app/make_geo_graphs.py analisi/geometria_criteri.py analisi/r3_propagazione.py analisi/caratterizza_grafi.py placement_analysis.py run_model_suite.py run_replication.py; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; $G -- "$f" | head -4; }
done
T "1b. geometria: risultati, log, checkpoint (nomi che contengono geo/sweep/sottoret)"
find . -maxdepth 4 \( -iname '*geo*' -o -iname '*sweep*' -o -iname '*sottoret*' -o -iname '*subnet*' \) -not -path './.git/*' -not -path '*/__pycache__/*' 2>/dev/null | head -40
T "1c. tabelle 32-35 nel codice e nei documenti"
grep -rn "Tabell[ae] 3[2-5]" --include=*.py --include=*.md --include=*.sh . 2>/dev/null | grep -v '^./evoluzione/MoGERNN' | head -20
T "1d. file di configurazione / esiti con 'commit' dentro (le run si attribuiscono da qui)"
grep -rl '"commit"' --include=*.json . 2>/dev/null | grep -v '^./results/evoluzione' | head -20

T "2a. ciclo di addestramento dei Graph WaveNet: storia dei file"
for f in models/gomo_gwn.py models/gomo_stgnn.py models/gomo_sparse.py models/gomo_classify.py; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; $G -- "$f" | head -6; }
done
T "2b. quando e' entrato il ciclo a lotti completi (git log -S sulla riga del ciclo)"
git log --format='%h %ad %s' --date=short -S'for i in range(0, len(perm), args.batch)' -- models/ | head
T "2c. ciclo attuale (righe con epoch/perm/batch) e dimensione della validazione"
for f in models/gomo_gwn.py models/gomo_stgnn.py models/gomo_sparse.py models/gomo_classify.py; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; grep -n "range(args.epochs)\|perm\[\|starts\[\|int(n\*\|\[:32\]\|va = \|va, te\|n_val" "$f" | head -8; }
done
T "2d. versioni precedenti del ciclo (prima occorrenza di 'perm[' in ogni commit del file)"
for c in $(git log --format=%h -- models/gomo_gwn.py | head -8); do printf '%s: ' "$c"; git show "$c:models/gomo_gwn.py" 2>/dev/null | grep -m1 -n "perm\[" || echo "(nessun perm[)"; done

T "3a. costo di un addestramento a grafo: log con 'epoch' e la loro durata"
find . -maxdepth 4 \( -iname '*.log' -o -iname '*.txt' -o -iname '*.out' \) -not -path './.git/*' -not -path './evoluzione/*' 2>/dev/null | xargs grep -l "epoch 01\|epoch 1 " 2>/dev/null | head -12
T "3b. hardware di questa macchina"
uname -m; sysctl -n machdep.cpu.brand_string 2>/dev/null; sysctl -n hw.memsize 2>/dev/null
poetry run python -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available(),'mps',torch.backends.mps.is_available())" 2>/dev/null

T "4a. dati: Austin, M30 2024, sonde Madrid 2021 (percorsi reali)"
find . -maxdepth 4 \( -iname '*austin*' -o -iname '*m30*' -o -iname '*sonde*' -o -iname '*probe*' -o -iname '*2021*' -o -iname '*radar*' \) -not -path './.git/*' -not -path '*/__pycache__/*' 2>/dev/null | head -40
for d in data_collection data_collection/go-mo/gomo data_collection/traffic4cast austin; do [ -d "$d" ] && { printf -- '-- %s\n' "$d"; ls "$d" | head -12; }; done
T "4b. script delle tabelle 64-69"
grep -rn "Tabell[ae] 6[4-9]" --include=*.py --include=*.md . 2>/dev/null | grep -v '^./evoluzione/MoGERNN' | head -20
for f in analisi/validazione_colocalizzata.py analisi/caratterizza_radar.py censimento_csv.py inventario.py; do
  [ -e "$f" ] && { printf -- '-- %s\n' "$f"; $G -- "$f" | head -3; grep -n "^[A-Z_]* = Path(\|read_csv(\|np.load(\|json.load" "$f" | head -8; }
done
T "fine"
