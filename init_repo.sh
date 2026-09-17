#!/usr/bin/env bash
# Inizializza un repository git LOCALE per tracciare il codice, non i dati.
# Da lanciare una sola volta, dalla radice OR3/.
#
# PERCHE' SERVE. Il registro delle esecuzioni deve riportare quale versione del
# codice ha prodotto ciascun risultato. Senza un repository quel campo non e'
# compilabile, e le esecuzioni restano distinguibili solo per data.
#
# PERCHE' VA FATTO CON CAUTELA. L'albero contiene milioni di righe di dati:
# `replication/` ha migliaia di file di risultato e di dump, `austin/` un JSON da
# quasi sette milioni di record, `descrittori/` gli artefatti. Un `git add .`
# incauto li includerebbe tutti, rendendo il repository inutilizzabile.
#
# Lo script percio' SCRIVE PRIMA il .gitignore, poi mostra cosa entrerebbe e
# quanto pesa, e si ferma prima di committare: il commit e' un passo separato e
# manuale.
set -euo pipefail

[ -d models ] || { echo "non sembra la radice OR3/: manca models/"; exit 1; }

if [ -d .git ]; then
  echo "repository gia' presente: non reinizializzo."
else
  git init -q
  echo "repository inizializzato (locale, nessun remoto)"
fi

# --- .gitignore: si tracciano i SORGENTI, non i dati ne' i risultati ---------
if [ -f .gitignore ]; then
  echo ".gitignore gia' presente: lo lascio com'e'. Verificare a mano che escluda"
  echo "  replication/, results/, descrittori/, austin/, data_collection/, log/"
else
cat > .gitignore << 'EOF'
# --- dati di ingresso: grandi, immutabili, versionati altrove ---------------
data_collection/
austin/
*.npz
*.npy
*.parquet

# --- risultati ed esecuzioni: tracciati dal registro, non da git ------------
replication/
results/
log/
*.log
descrittori/
figure/
_archivio/

# --- artefatti di lavoro ----------------------------------------------------
__pycache__/
*.pyc
.ipynb_checkpoints/
.DS_Store
/tmp/
*.docx
*.pdf

# --- eccezioni: questi SI' ---------------------------------------------------
!evoluzione/**/*.md
!README*.md
EOF
  echo ".gitignore scritto"
fi

echo
echo "=== cosa entrerebbe nel primo commit ==="
git add -An . >/dev/null 2>&1 || true
N=$(git status --porcelain --untracked-files=all 2>/dev/null | wc -l | tr -d ' ')
echo "file candidati: $N"
git status --porcelain --untracked-files=all 2>/dev/null \
  | sed 's/^...//' | sed 's|/.*||' | sort | uniq -c | sort -rn | head -12

echo
echo "=== i dieci piu' pesanti fra i candidati ==="
git status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//' \
  | while read -r f; do [ -f "$f" ] && echo "$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f") $f"; done \
  | sort -rn | head -10 | awk '{printf "  %8.1f KB  %s\n", $1/1024, $2}'

echo
echo "Se l'elenco contiene solo sorgenti e documenti, il commit e':"
echo
echo "    git add -A && git commit -q -m 'stato alla data di avvio della campagna JSS'"
echo
echo "Se contiene dati, correggere .gitignore PRIMA di committare."
