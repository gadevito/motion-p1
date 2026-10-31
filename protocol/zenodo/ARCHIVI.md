# Archivi del record Zenodo

Generati da `evoluzione/audit/archivi_zenodo.py` il 2026-10-31 09:58 UTC su `spark-9809`, dal manifesto `protocol/zenodo/MANIFEST.txt` (tag `paper1-freeze-20261030l`, commit `8986779e0ed233b885a9db8c222a0a11fa09c296`, sha256 del manifesto `4d0c27bb2ba8ef72`). Tre archivi tar **non compressi**, membri in ordine di percorso, percorsi relativi alla radice di OR3 (`results/evoluzione/...`): si estraggono nella radice con `tar -xf <archivio> -C <radice OR3>` e `analysis/main.py` li legge dove li attende. Archivi gia' presenti in --dest, non ricostruiti: verificati contro questo manifesto.

| archivio | gruppo | byte | SHA-256 | file | mancanti rispetto al manifesto | in piu' | dimensioni diverse |
|---|---|---:|---|---:|---:|---:|---:|
| `zenodo_rigenerazione.tar` | rigenerazione | 10,910,607,360 | `93e91ad89705ea111865435996c8e23a066e4ffcba2827f10b6089f33cadd6e4` | 4,165 | 0 | 0 | 0 |
| `zenodo_probabilita.tar` | probabilita | 7,680,102,400 | `c5c0d123855cab32eb838650ee67bb138d76fe543554c56d0081d1c88df4cccf` | 326 | 0 | 0 | 0 |
| `zenodo_punti_di_controllo.tar` | punti | 662,865,920 | `470115fef5d6047dbc667d89a257e15f9f976b67c6928efdd235579205c514f9` | 8,185 | 0 | 0 | 0 |
| **totale** | | **19,253,575,680** (17.93 GiB) | | **12,676** | | | |

Verifica: l'elenco dei membri di ciascun archivio (nome e dimensione) coincide con le righe del gruppo nel manifesto — **superata** per i tre archivi.

probabilita e punti di controllo: archivi identici a quelli del tag k (same SHA-256); zenodo_rigenerazione.tar rebuilt at tag l (two E18-ter json added).

Controllo dopo la copia: `shasum -a 256 zenodo_*.tar` deve dare gli SHA-256 della tabella.
