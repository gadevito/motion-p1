#!/usr/bin/env bash
# E14 stadio B — prepara la copia dell'albero in cui si rivaluta con una variante della statica.
# ======================================================================================
# Uso (sulla Spark):   bash ~/OR3/evoluzione/esperimenti/e14b_prepara_copia.sh <variante> [ramo]
#   variante  a | b | c          ramo (predefinito esecutore/e14)
#
# Crea ~/OR3_<variante>:
#   1. clone del repo nudo ~/OR3.git al ramo indicato (codice al commit del ramo);
#   2. results/ copiato da ~/OR3/results con COLLEGAMENTI FISICI (cp -al): nessun byte
#      duplicato; poi ogni file sotto 32 MB viene reso una copia vera (i json e i file
#      piccoli che le fasi riscrivono in loco non devono toccare l'originale); i file
#      grandi (punti di controllo) restano collegati e si leggono soltanto;
#   3. data_collection/ come collegamento simbolico (sola lettura);
#   4. cancella nella copia le predizioni e le scelte che lo stadio B rigenera
#      (le originali in ~/OR3 restano intatte e sono i «congelati» del confronto);
#   5. scrive _e14b/variante e verifica che nessun file piccolo sia ancora collegato.
set -euo pipefail
V="${1:?variante a|b|c}"; RAMO="${2:-esecutore/e14}"
case "$V" in a|b|c) ;; *) echo "variante $V non ammessa"; exit 2;; esac
SRC="$HOME/OR3"; DST="$HOME/OR3_$V"
[ -d "$SRC/results/evoluzione" ] || { echo "manca $SRC/results/evoluzione"; exit 2; }
[ -e "$DST" ] && { echo "$DST esiste gia': rimuoverlo prima (rm -rf $DST) se si vuole ripartire"; exit 2; }

echo "== clone di ~/OR3.git ($RAMO) in $DST"
git clone -q -b "$RAMO" "$HOME/OR3.git" "$DST"
( cd "$DST" && echo "   commit $(git rev-parse --short HEAD)  $(git log -1 --format=%s | cut -c1-70)" )

echo "== results/ con collegamenti fisici"
cp -al "$SRC/results" "$DST/results"
echo "== cancellazione nella copia di cio' che lo stadio B rigenera"
E="$DST/results/evoluzione"
for d in predizioni_f0 predizioni_e2 predizioni_fase3 predizioni_fase3_672 predizioni_veterani_e3 \
         predizioni_e4 predizioni_e5 predizioni_e6 predizioni_e6bis predizioni_e6a predizioni_e8; do
  [ -d "$E/$d" ] && { rm -rf "$E/$d"; echo "   rimossa $d/"; }
done
for j in e4_scelta_gated e5_k_secondaria e6_scelta_gated e6a_scelta_gated e8_soglie \
         e4_risultati e4_griglia_test copertura_e4 e5_risultati e5_settimana_vs_A \
         e6_risultati e6bis_risultati e6a_risultati e6_origini_comuni e7_stadio1 e7_posthoc \
         e8_risultati e8bis_risultati curve_e8bis_punti analisi_e3 veterani_e3 e3bis_risultati \
         riselezione_rmon_test congelamento_e2 congelamento_e3 congelamento_e3bis congelamento_e4 \
         congelamento_e5 congelamento_e6 congelamento_e7 congelamento_e8; do
  [ -f "$E/$j.json" ] && { rm -f "$E/$j.json"; echo "   rimosso $j.json"; }
done
# gli originali devono essere ancora al loro posto
for j in e4_scelta_gated e5_k_secondaria e6_scelta_gated e8_soglie e5_risultati; do
  [ -f "$SRC/results/evoluzione/$j.json" ] || { echo "ERRORE: $SRC/results/evoluzione/$j.json sparito"; exit 1; }
done
for d in predizioni_fase3 predizioni_e4 predizioni_e5 predizioni_e8; do
  [ -d "$SRC/results/evoluzione/$d" ] || { echo "ERRORE: $SRC/results/evoluzione/$d sparito"; exit 1; }
done
echo "== file < 32 MB resi copie vere"
n=0
while IFS= read -r -d '' f; do
  cp -p "$f" "$f.__tmp" && mv -f "$f.__tmp" "$f"; n=$((n+1))
done < <(find "$DST/results" -type f -links +1 -size -32M -print0)
echo "   $n file copiati"
resto=$(find "$DST/results" -type f -links +1 -size -32M | wc -l)
[ "$resto" -eq 0 ] || { echo "ERRORE: $resto file piccoli ancora collegati"; exit 1; }

echo "== data_collection/ (simbolico), figure/, log/"
ln -s "$SRC/data_collection" "$DST/data_collection"
mkdir -p "$DST/figure" "$DST/log" "$DST/_e14b"

echo "$V" > "$DST/_e14b/variante"
date -u +%Y-%m-%dT%H:%M:%SZ > "$DST/_e14b/preparata"
echo "== pronta: $DST (variante $V). Lancio:"
echo "   cd $DST && nohup bash evoluzione/esperimenti/esegui_e14b.sh $V 16 > log/e14b_$V.log 2>&1 &"
