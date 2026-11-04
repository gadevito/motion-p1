# Archivi del record Zenodo

Generati da `evoluzione/audit/archivi_zenodo.py` il 2026-11-04 13:35 UTC su `MacBook-Pro-di-gabriele-2.local`, dal manifesto `protocol/zenodo/MANIFEST.txt` (tag `paper1-freeze-20261103q`, commit `d327eb19046754f7ac2f122652b973ed68ba0eb6`, sha256 del manifesto `59ba34f62100df3c`). Tre archivi tar **non compressi**, membri in ordine di percorso, percorsi relativi alla radice di OR3 (`results/evoluzione/...`): si estraggono nella radice con `tar -xf <archivio> -C <radice OR3>` e `analysis/main.py` li legge dove li attende. Archivi gia' presenti in --dest, non ricostruiti: verificati contro questo manifesto.

| archivio | gruppo | byte | SHA-256 | file | mancanti rispetto al manifesto | in piu' | dimensioni diverse |
|---|---|---:|---|---:|---:|---:|---:|
| `zenodo_rigenerazione.tar` | rigenerazione | 10,912,307,200 | `293f71b57c82ab8763f9867819814377eae9a55e82a506085d49928a4f77b3e8` | 4,222 | 0 | 0 | 0 |
| `zenodo_probabilita.tar` | probabilita | 7,680,102,400 | `c5c0d123855cab32eb838650ee67bb138d76fe543554c56d0081d1c88df4cccf` | 326 | 0 | 0 | 0 |
| `zenodo_punti_di_controllo.tar` | punti | 662,865,920 | `470115fef5d6047dbc667d89a257e15f9f976b67c6928efdd235579205c514f9` | 8,185 | 0 | 0 | 0 |
| **totale** | | **19,255,275,520** (17.93 GiB) | | **12,733** | | | |

Verifica: l'elenco dei membri di ciascun archivio (nome e dimensione) coincide con le righe del gruppo nel manifesto — **superata** per i tre archivi.

Tag q: zenodo_rigenerazione.tar ricostruito (+54 celle predizioni_e18quater/ e 3 record di E18-quater rispetto al tag l); zenodo_probabilita.tar e zenodo_punti_di_controllo.tar identici a quelli del tag l (stessi SHA-256), verificati contro il manifesto q.

Controllo dopo la copia: `shasum -a 256 zenodo_*.tar` deve dare gli SHA-256 della tabella.
