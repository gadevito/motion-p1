# Paper 4, fase 1 — grafi senza generatore: caratterizzazione dal file

Generato da `analisi/p4_fase1_grafi.py` il 2026-11-06 14:38 UTC (non modificare a mano) da `../OR3/data_collection/traffic4cast/MADRID_2022/gomo_fmt`. I tre grafi `t4cmad_rand_k1.pkl`, `t4cmad_rand_k2.pkl` (scritti nello stesso secondo, 22/8/2026) e `t4cmad_identity_graph.pkl` (21/8/2026) non hanno generatore nel repository ne' nelle storie (D9); le sole tracce d'uso sono `OLD/log/randk.log` (dieci esecuzioni di `models/gomo_sparse.py`, CSV di uscita non conservati) e `OLD/log/identita.log` (`replication/identita/ident_t4cmad_s0-4.csv`, conservati). Il grafo stradale `t4cmad_routes-graph.pkl` (`data_collection/traffic4cast/t4c22_adapter.py` r. 144) e' il riferimento per la sovrapposizione.

| file | sha256 | byte | modificato | tipo | nodi | archi | cappi | comp. (gigante) | gradi min/q1/med/q3/max (media) | pesi n, min/med/media/max |
|---|---|---:|---|---|---:|---:|---:|---|---|---|
| `t4cmad_rand_k1.pkl` | `74ae8301f4367e4c` | 78,494 | 2026-08-22 06:48:06 UTC | Graph | 900 | 900 | 0 | 4 (662) | 1/1/2/3/7 (2.00) | 900, 15.1/2217.1/2225.2/5818.6 |
| `t4cmad_rand_k2.pkl` | `66209dafd0b380a9` | 106,903 | 2026-08-22 06:48:06 UTC | Graph | 900 | 1800 | 0 | 1 (900) | 2/3/4/5/11 (4.00) | 1800, 11.3/2135.6/2185.7/5584.7 |
| `t4cmad_identity_graph.pkl` | `d67725c00ecdbdc5` | 48,858 | 2026-08-21 13:50:51 UTC | Graph | 900 | 0 | 0 | 900 (1) | 0/0/0/0/0 (0.00) | nessun peso |
| `t4cmad_routes-graph.pkl` | `3c1280a75411f3ec` | 115,992 | 2026-07-07 12:51:02 UTC | Graph | 900 | 1705 | 0 | 1 (900) | 1/3/4/5/9 (3.79) | 1705, 1.0/59.8/82.9/700.6 |

## Dettaglio per grafo

### `t4cmad_rand_k1.pkl`

- attributi dei nodi: {'utm_x': 900, 'utm_y': 900}; attributi degli archi: {'weight': 900}
- tipo dei nodi: [('str', 900)]; esempi: '21473125_153059151', '21473133_21473145', '21682622_240001263'; esempio di arco: `('21473125_153059151', '1738553332_81468686', {'weight': 4472.365549287591})`
- istogramma dei gradi (grado: nodi): 1: 335, 2: 328, 3: 162, 4: 55, 5: 18, 6: 1, 7: 1
- componenti connesse: 4, le piu' grandi [662, 212, 21, 5]
- nodi in comune con il grafo stradale: 900 su 900; archi (non orientati) in comune: 3 su 900

### `t4cmad_rand_k2.pkl`

- attributi dei nodi: {'utm_x': 900, 'utm_y': 900}; attributi degli archi: {'weight': 1800}
- tipo dei nodi: [('str', 900)]; esempi: '21473125_153059151', '21473133_21473145', '21682622_240001263'; esempio di arco: `('21473125_153059151', '102320031_102320034', {'weight': 5367.46995534838})`
- istogramma dei gradi (grado: nodi): 2: 127, 3: 247, 4: 222, 5: 178, 6: 80, 7: 28, 8: 13, 9: 4, 11: 1
- componenti connesse: 1, le piu' grandi [900]
- nodi in comune con il grafo stradale: 900 su 900; archi (non orientati) in comune: 6 su 1800

### `t4cmad_identity_graph.pkl`

- attributi dei nodi: {'utm_x': 900, 'utm_y': 900}; attributi degli archi: nessuno
- tipo dei nodi: [('str', 900)]; esempi: '21473125_153059151', '21473133_21473145', '21682622_240001263'; esempio di arco: `None`
- istogramma dei gradi (grado: nodi): 0: 900 — **grado costante**
- componenti connesse: 900, le piu' grandi [1, 1, 1, 1, 1]
- nodi in comune con il grafo stradale: 900 su 900; archi (non orientati) in comune: 0 su 0

### `t4cmad_routes-graph.pkl`

- attributi dei nodi: {'utm_x': 900, 'utm_y': 900}; attributi degli archi: {'weight': 1705}
- tipo dei nodi: [('str', 900)]; esempi: '21473125_153059151', '21473133_21473145', '21682622_240001263'; esempio di arco: `('21473125_153059151', '153059151_21473133', {'weight': 502.37586351758955})`
- istogramma dei gradi (grado: nodi): 1: 39, 2: 129, 3: 228, 4: 276, 5: 109, 6: 70, 7: 34, 8: 13, 9: 2
- componenti connesse: 1, le piu' grandi [900]
- nodi in comune con il grafo stradale: 900 su 900; archi (non orientati) in comune: 1705 su 1705

## Relazioni fra i grafi

- `rand_k1` e `rand_k2`: stessi nodi: True; archi in comune 2 (k1 ha 900, k2 1800); rapporto archi k2/k1 = 2.00
- lettura: se `k` fosse il numero di vicini per nodo, un grafo a k vicini non orientato avrebbe grado medio fra k e 2k (k1: 2.00; k2: 4.00); con coppie casuali a pari numero di archi il grado medio sarebbe 2·archi/nodi: k1 2.00, k2 4.00.
- `identity_graph`: 0 archi su 900 nodi, cappi 0 — **nessun arco: grafo identita' (nessuna propagazione fra nodi)**.

Script: `analisi/p4_fase1_grafi.py` `8e50745bd31d21ae`.
