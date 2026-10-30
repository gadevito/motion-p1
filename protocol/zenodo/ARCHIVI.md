# Archivi del record Zenodo

Generati da `evoluzione/audit/archivi_zenodo.py` il 2026-10-30 09:34 UTC su `spark-9809`, dal manifesto `protocol/zenodo/MANIFEST.txt` (tag `paper1-freeze-20261030k`, commit `6ebac229592928d8c9212321a88fb4dbb3456b16`, sha256 del manifesto `183b58d5fe3a7434`). Tre archivi tar **non compressi**, membri in ordine di percorso, percorsi relativi alla radice di OR3 (`results/evoluzione/...`): si estraggono nella radice con `tar -xf <archivio> -C <radice OR3>` e `analysis/main.py` li legge dove li attende.

| archivio | gruppo | byte | SHA-256 | file | mancanti rispetto al manifesto | in piu' | dimensioni diverse |
|---|---|---:|---|---:|---:|---:|---:|
| `zenodo_rigenerazione.tar` | rigenerazione | 10,909,829,120 | `85ef2051567de4083fd4f5187084f1f2c833e4fef4b66fae63487f9f8f443169` | 4,163 | 0 | 0 | 0 |
| `zenodo_probabilita.tar` | probabilita | 7,680,102,400 | `c5c0d123855cab32eb838650ee67bb138d76fe543554c56d0081d1c88df4cccf` | 326 | 0 | 0 | 0 |
| `zenodo_punti_di_controllo.tar` | punti | 662,865,920 | `470115fef5d6047dbc667d89a257e15f9f976b67c6928efdd235579205c514f9` | 8,185 | 0 | 0 | 0 |
| **totale** | | **19,252,797,440** (17.93 GiB) | | **12,674** | | | |

Verifica: l'elenco dei membri di ciascun archivio (nome e dimensione) coincide con le righe del gruppo nel manifesto — **superata** per i tre archivi.

Controllo dopo la copia: `shasum -a 256 zenodo_*.tar` deve dare gli SHA-256 della tabella.
