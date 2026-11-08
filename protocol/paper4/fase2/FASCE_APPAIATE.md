# Parte A, punto 5 — sensori M30 presenti in piu' fasce di distanza e confronto appaiato

Generato da `analisi/p4a_fasce_appaiate.py` il 2026-11-08 20:28 UTC con il modulo congelato `analisi/validazione_colocalizzata.py` (`f1f6340779b612d5`), dati `../OR3/data_collection/go-mo/gomo`; filtro di `sez_accoppiamento` (r. 170-183) replicato. Sola lettura; nessun numero del paper cambia.

Sensori allineati: 279. Un sensore «e' in una fascia» se ha un vicino in quella fascia e la coppia supera le 50 celle.

## Sensori per fascia e intersezioni

| fascia | sensori | dist. mediana | celle | ρ | AUC | Gini |
|---|---:|---:|---:|---:|---:|---:|
| 0-20 m | 191 | 14 m | 2,808,770 | +0.0904 | 0.7893 | 0.5787 |
| 19-72 m | 181 | 31 m | 2,613,959 | +0.0817 | 0.7241 | 0.4483 |
| 20-60 m | 156 | 31 m | 2,254,158 | +0.0873 | 0.7638 | 0.5276 |
| 60-200 m | 165 | 96 m | 2,431,886 | +0.0329 | 0.5934 | 0.1867 |

| fasce | sensori comuni | solo nella prima | solo nella seconda |
|---|---:|---:|---:|
| 0-20 m ∩ 19-72 m | 130 | 61 | 51 |
| 0-20 m ∩ 20-60 m | 107 | 84 | 49 |
| 0-20 m ∩ 60-200 m | 105 | 86 | 60 |
| 19-72 m ∩ 20-60 m | 156 | 25 | 0 |
| 19-72 m ∩ 60-200 m | 112 | 69 | 53 |
| 20-60 m ∩ 60-200 m | 91 | 65 | 74 |

Sensori in **tutte e quattro** le fasce: 54; in **0-20 e 60-200 m** (la domanda del revisore): 105; in almeno una fascia: 263 su 279.

## Confronto appaiato: stesse metriche sui soli sensori comuni a ogni coppia di fasce

Per ogni coppia di fasce, le metriche di ciascuna fascia ricalcolate sulle celle dei soli sensori comuni, cosi' che la differenza fra le due fasce non dipenda dalla composizione dei sensori.

| fasce | sensori comuni | fascia | dist. mediana | celle | ρ | AUC | Gini | ΔGini (seconda − prima) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| 0-20 m ∩ 19-72 m | 130 | 0-20 m | 15 m | 1,916,265 | +0.0941 | 0.8026 | 0.6052 | 
| 0-20 m ∩ 19-72 m | 130 | 19-72 m | 30 m | 1,913,704 | +0.0546 | 0.6556 | 0.3112 | -0.2940
| 0-20 m ∩ 20-60 m | 107 | 0-20 m | 15 m | 1,577,626 | +0.1064 | 0.8346 | 0.6692 | 
| 0-20 m ∩ 20-60 m | 107 | 20-60 m | 30 m | 1,573,780 | +0.0581 | 0.6700 | 0.3400 | -0.3291
| 0-20 m ∩ 60-200 m | 105 | 0-20 m | 14 m | 1,554,618 | +0.1005 | 0.7974 | 0.5948 | 
| 0-20 m ∩ 60-200 m | 105 | 60-200 m | 92 m | 1,561,371 | +0.0221 | 0.5650 | 0.1299 | -0.4649
| 19-72 m ∩ 20-60 m | 156 | 19-72 m | 31 m | 2,254,158 | +0.0873 | 0.7638 | 0.5276 | 
| 19-72 m ∩ 20-60 m | 156 | 20-60 m | 31 m | 2,254,158 | +0.0873 | 0.7638 | 0.5276 | +0.0000
| 19-72 m ∩ 60-200 m | 112 | 19-72 m | 33 m | 1,624,343 | +0.0609 | 0.7313 | 0.4627 | 
| 19-72 m ∩ 60-200 m | 112 | 60-200 m | 92 m | 1,645,607 | +0.0323 | 0.5874 | 0.1749 | -0.2878
| 20-60 m ∩ 60-200 m | 91 | 20-60 m | 31 m | 1,335,856 | +0.0793 | 0.8020 | 0.6039 | 
| 20-60 m ∩ 60-200 m | 91 | 60-200 m | 94 m | 1,355,861 | +0.0408 | 0.6108 | 0.2217 | -0.3823

### Sui 54 sensori presenti in tutte e quattro le fasce

| fascia | dist. mediana | celle | ρ | AUC | Gini |
|---|---:|---:|---:|---:|---:|
| 0-20 m | 14 m | 770,362 | +0.1519 | 0.8540 | 0.7081 |
| 19-72 m | 31 m | 772,184 | +0.0255 | 0.6492 | 0.2984 |
| 20-60 m | 31 m | 772,184 | +0.0255 | 0.6492 | 0.2984 |
| 60-200 m | 88 m | 764,745 | +0.0102 | 0.5703 | 0.1407 |
