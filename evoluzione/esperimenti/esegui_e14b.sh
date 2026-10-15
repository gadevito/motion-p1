#!/usr/bin/env bash
# E14 stadio B — orchestratore: tutte le fasi di valutazione E2–E8-bis con una variante della statica.
# ===================================================================================================
# Uso (dalla radice della COPIA preparata da e14b_prepara_copia.sh, p.es. ~/OR3_c):
#
#     cd ~/OR3_c && nohup bash evoluzione/esperimenti/esegui_e14b.sh c 16 > log/e14b_c.log 2>&1 &
#
# Nessun addestramento: i punti di controllo sono quelli della campagna. Si rifanno SOLO le fasi
# di valutazione, selezione su validazione e analisi, nell'ordine delle dipendenze, con
# OR3_STATICA=<variante> esportata per ogni processo (inserimento.statica_cella). Le scelte su
# validazione ((tau, N) di E4/E6/E6a, k di E5, soglie di E8) si rifanno con la variante; la
# configurazione di F' (selezione_F_*, fase 2 della campagna, fuori da E2–E8-bis) resta quella
# congelata, dichiarato. Su PEMS04/08 la variante e' l'identita' (copertura 1 ovunque): quelle
# fasi sono il controllo a scarto zero.
#
# Ogni passo scrive log/e14b_<variante>_<nn>_<nome>.log e, se riesce, _e14b/<nn>_<nome>.ok; un
# rilancio riprende dal primo passo senza marcatore. Al primo fallimento ci si ferma.
set -uo pipefail
V="${1:?variante a|b|c}"; LAV="${2:-16}"
[ -f _e14b/variante ] || { echo "non e' una copia preparata (manca _e14b/variante)"; exit 2; }
[ "$(cat _e14b/variante)" = "$V" ] || { echo "la copia e' per la variante $(cat _e14b/variante), non $V"; exit 2; }
PY="${OR3_PY:-}"
if [ -z "$PY" ]; then
  PY="$(cd "$HOME/OR3" && "$HOME/.local/bin/poetry" env info -p 2>/dev/null)/bin/python"
fi
[ -x "$PY" ] || { echo "interprete non trovato: $PY (impostare OR3_PY)"; exit 2; }
export OR3_STATICA="$V"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p log _e14b
T_INIZIO=$(date +%s)
echo "E14 stadio B — variante $V, $LAV lavoratori, $(date -u +%FT%TZ), commit $(git rev-parse --short HEAD), python $PY"
"$PY" - <<'EOF'
import sys; sys.path.insert(0, ".")
from evoluzione.esperimenti.inserimento import variante_statica
print(f"  OR3_STATICA letta da inserimento: {variante_statica()}")
EOF

N=0
passo() {                       # passo <nome> <comando...>
  N=$((N+1)); local nome; nome=$(printf "%02d_%s" "$N" "$1"); shift
  local ok="_e14b/$nome.ok" log="log/e14b_${V}_$nome.log"
  if [ -f "$ok" ]; then echo "  [$nome] gia' fatto ($(cat "$ok"))"; return 0; fi
  local t0; t0=$(date +%s)
  echo "  [$nome] $(date -u +%H:%M:%S)  $*"
  if "$@" > "$log" 2>&1; then
    echo "$(date -u +%FT%TZ) $(( $(date +%s) - t0 )) s" > "$ok"
    echo "  [$nome] fatto in $(( ($(date +%s) - t0) / 60 )) min"
  else
    echo "  [$nome] FALLITO (codice $?): vedi $log"; tail -n 25 "$log"; exit 1
  fi
}
parallelo() {                   # parallelo <nome> <comando con BRACCIO> -- braccio1 braccio2 ...
  N=$((N+1)); local nome; nome=$(printf "%02d_%s" "$N" "$1"); shift
  local ok="_e14b/$nome.ok"
  if [ -f "$ok" ]; then echo "  [$nome] gia' fatto ($(cat "$ok"))"; return 0; fi
  local cmd=(); while [ "$1" != "--" ]; do cmd+=("$1"); shift; done; shift
  local t0; t0=$(date +%s); local pids=() bracci=("$@")
  echo "  [$nome] $(date -u +%H:%M:%S)  ${cmd[*]} per bracci: ${bracci[*]} (in parallelo)"
  for b in "${bracci[@]}"; do
    OMP_NUM_THREADS=2 "${cmd[@]}" --braccio "$b" > "log/e14b_${V}_${nome}_$b.log" 2>&1 & pids+=($!)
  done
  local fall=0 i=0
  for p in "${pids[@]}"; do wait "$p" || { echo "  [$nome] braccio ${bracci[$i]} FALLITO: vedi log/e14b_${V}_${nome}_${bracci[$i]}.log"; fall=1; }; i=$((i+1)); done
  [ "$fall" -eq 0 ] || exit 1
  echo "$(date -u +%FT%TZ) $(( $(date +%s) - t0 )) s" > "$ok"
  echo "  [$nome] fatto in $(( ($(date +%s) - t0) / 60 )) min"
}
E=evoluzione/esperimenti; A=evoluzione/analisi; R=results/evoluzione

# ---- E2: F0 e i bracci dal punto E1 (citta') ------------------------------------------------
passo f0            "$PY" $E/esegui_f0.py
passo e2            "$PY" $E/esegui_e2.py
# ---- fase 3 ricostruita: i sette bracci, poi R-orig con acquisizione di una settimana (E3-bis)
parallelo fase3     "$PY" $E/ricostruisci_predizioni.py -- C P A R F R-orig R-mon
passo fase3_672     "$PY" $E/ricostruisci_predizioni.py --braccio R-orig --acquisizione-passi 672
# ---- E3: veterani, R-mon a peso uguale, analisi --------------------------------------------
passo veterani_e3   "$PY" $E/veterani_e3.py --lavoratori "$LAV"
passo rmon_eq       "$PY" $E/riselezione_rmon_test.py --valuta --analizza
passo analizza_e3   "$PY" $A/analizza_e3.py --out $R/analisi_e3.json
passo analizza_vet  "$PY" $A/analizza_veterani_e3.py --out $R/veterani_e3.json
# ---- E4: valutazione (prova + validazione), scelta di (tau, N) su validazione, test ---------
passo e4_valuta     "$PY" $E/esegui_e4.py --fase valuta --lavoratori "$LAV"
passo e4_scegli     "$PY" $E/esegui_e4.py --fase scegli
passo e4_test       "$PY" $E/esegui_e4.py --fase test
passo analizza_e4   "$PY" $A/analizza_e4.py
passo copertura_e4  "$PY" $A/analizza_copertura_e4.py --out $R/copertura_e4.json
passo analizza_e3bis "$PY" $A/analizza_e3bis.py
# ---- E5: k su validazione, valutazione dei tre episodi, test --------------------------------
passo e5_k          "$PY" $E/esegui_e5.py --fase k-secondaria --lavoratori "$LAV"
passo e5_valuta     "$PY" $E/esegui_e5.py --fase valuta --lavoratori "$LAV"
passo e5_test       "$PY" $E/esegui_e5.py --fase test
passo e5_settimana  "$PY" $A/settimana_vs_A_e5.py
passo analizza_e5   "$PY" $A/analizza_e5.py
# ---- E6 / E6-bis / E6a (PEMS: controllo a scarto zero) --------------------------------------
passo e6_val        "$PY" $E/esegui_e6.py --fase valuta --episodio validazione --lavoratori "$LAV"
passo e6_scegli     "$PY" $E/esegui_e6.py --fase scegli
passo e6_prova      "$PY" $E/esegui_e6.py --fase valuta --episodio prova --lavoratori "$LAV"
passo e6_test       "$PY" $E/esegui_e6.py --fase test
passo e6_valuta_E   "$PY" $E/esegui_e6.py --fase valuta-E --lavoratori "$LAV"
passo e6_test_bis   "$PY" $E/esegui_e6.py --fase test-bis
passo e6a_val       "$PY" $E/esegui_e6a.py --fase valuta --episodio validazione --lavoratori "$LAV"
passo e6a_scegli    "$PY" $E/esegui_e6a.py --fase scegli
passo e6a_prova     "$PY" $E/esegui_e6a.py --fase valuta --episodio prova --lavoratori "$LAV"
passo e6a_test      "$PY" $E/esegui_e6a.py --fase test
passo e6_origini    "$PY" $E/esegui_e6.py --fase origini      # legge anche predizioni_e6a: dopo E6a
# ---- E7 (a costo zero, dai file di E5 rigenerati) -------------------------------------------
passo e7_stadio1    "$PY" $A/e7_stadio1.py
passo e7_posthoc    "$PY" $A/e7_posthoc.py
# ---- E8 / E8-bis: validazione, soglie, prova, test, curve ------------------------------------
passo e8_val        "$PY" $E/esegui_e8.py --fase validazione --lavoratori "$LAV"
passo e8_soglie     "$PY" $E/esegui_e8.py --fase soglie
passo e8_prova      "$PY" $E/esegui_e8.py --fase prova --lavoratori "$LAV"
passo e8_test       "$PY" $E/esegui_e8.py --fase test
passo e8_curve      "$PY" $E/esegui_e8.py --fase curve --lavoratori "$LAV"
passo e8_test_curve "$PY" $E/esegui_e8.py --fase test-curve
passo figura_e8bis  "$PY" $A/figura_e8bis.py
passo figura2_51    "$PY" $A/figura2_51.py
# ---- generatori (i json congelamento_*.json rigenerati; i .md nella copia non si usano) -----
for g in e2 e3 e3bis e4 e5 e6 e7 e8; do passo "gen_$g" "$PY" genera_congelamento_$g.py; done
# ---- livelli assoluti di C, A, F0 per citta' e fascio dei json rigenerati -------------------
passo livelli       "$PY" $A/e14b_livelli.py --out $R --etichetta "$V"
passo fascio        "$PY" $A/e14b_fascio.py --out $R --variante "$V" --dopo "$(cat _e14b/preparata)"

echo "E14 stadio B — variante $V completata in $(( ($(date +%s) - T_INIZIO) / 3600 )) h $(( (($(date +%s) - T_INIZIO) % 3600) / 60 )) min, $(date -u +%FT%TZ)"
echo "fascio: $R/e14b_fascio_$V.tar.gz (da copiare sul Mac in results/evoluzione/e14b/)"
