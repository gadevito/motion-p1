# P4A — tre cause misurate sui dati (T67 verde, T68 bande, Austin sezioni)

Generato da `analisi/p4a_cause.py` il 2026-11-08 18:46 UTC con il modulo congelato del deliverable `analisi/validazione_colocalizzata.py` (`f1f6340779b612d5`), dati `../OR3/data_collection/go-mo/gomo` e `../OR3_vecchia_storia/austin/radar/radar_completo.json`. Sola lettura; nessun numero del Paper 4 cambia. Valori del deliverable da UC-04 v1, pag. 130-133.

## 1. T67 — classe verde e correlazione complessiva

Celle non imputate `v`: 4,199,040. Il codice conservato definisce verde = 0,8 ≤ r_tr < 1,6 con r_tr tagliato a 1,5 (`carica_m30`, `np.clip(..., 0, 1.5)`; `sez_anello`, r. 117).

| definizione del verde | celle | scarto dal deliverable (2.989.877) | Spearman | deliverable +0,033 |
|---|---:|---:|---:|---|
| 0,8 ≤ r < 1,6 (codice conservato) | 3,432,842 | +442,965 | +0.0125 | diverso |
| 0,8 ≤ r < 1,5 (esclusi i tagliati a 1,5) | 2,989,877 | +0 | +0.0326 | **coincide** |
| 0,8 ≤ r < 1,2 | 2,378,123 | -611,754 | +0.0653 | diverso |
| 0,8 ≤ r < 1,0 (sotto il riferimento) | 1,184,961 | -1,804,916 | +0.1055 | diverso |

Celle di `v` con r_tr ≥ 1,0: 2,247,881; con r_tr tagliato a 1,5: 442,965; mancanti nel deliverable: 442.965.

| insieme per l'«overall» | celle | Spearman | deliverable +0,255 |
|---|---:|---:|---|
| tutte le `v` (codice conservato) | 4,199,040 | +0.2491 | diverso |
| `v` con r_tr < 1,0 | 1,951,159 | +0.4799 | diverso |
| `v` con r_tr < 1,5 | 3,756,075 | +0.2864 | diverso |
| `v` con r_pr < 1,5 | 4,198,251 | +0.2491 | diverso |
| `v` con r_pr < 1,5 e r_tr < 1,5 | 3,755,592 | +0.2865 | diverso |
| `v` con r_pr > 0 e r_tr > 0 (esclusi i tagliati a 0) | 4,199,040 | +0.2491 | diverso |
| `v` con 0 < r < 1,5 su entrambi (esclusi tutti i tagliati) | 3,755,592 | +0.2865 | diverso |

## 2. T68 — sensori per banda e varianti del filtro

Il filtro del deliverable (`sez_accoppiamento`, r. 176-178: r_pr_i finito, r_tr_j finito, sp_j > 0, oc_i ≥ 5; > 50 celle per coppia; ≥ 20 sensori; vicino piu' prossimo a 33 m) e' lo stesso di `p4a.py` (`table67_68`): i sensori per banda coincidono per costruzione. Varianti provate per spiegare gli scarti del deliverable.

| banda | variante | sensori | dist. mediana | celle | Spearman | AUC | Gini | deliverable (dist., ρ, AUC, Gini) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 0-20 m | deliverable | 191 | 14 | 2,808,770 | +0.0904 | 0.7893 | 0.5787 | 14 m, +0.086, 0.789, 0.578  |
| 0-20 m | senza_filtro_imputazione_i | 191 | 14 | 2,808,770 | +0.0904 | 0.7893 | 0.5787 | 14 m, +0.086, 0.789, 0.578  |
| 0-20 m | con_sp_i | 191 | 14 | 2,808,770 | +0.0904 | 0.7893 | 0.5787 | 14 m, +0.086, 0.789, 0.578  |
| 0-20 m | vicino_piu_prossimo | 191 | 10 | 2,819,116 | +0.1028 | 0.8217 | 0.6433 | 14 m, +0.086, 0.789, 0.578  |
| 0-20 m | escl_r_tr_j_1.5 | 170 | 14 | 2,051,732 | +0.1905 | 0.7957 | 0.5913 | 14 m, +0.086, 0.789, 0.578  |
| 0-20 m | escl_entrambi_1.5 | 170 | 14 | 2,051,541 | +0.1907 | 0.7956 | 0.5913 | 14 m, +0.086, 0.789, 0.578  |
| 19-72 m | deliverable | 181 | 31 | 2,613,959 | +0.0817 | 0.7241 | 0.4483 | 31 m, +0.076, 0.726, 0.452  |
| 19-72 m | senza_filtro_imputazione_i | 181 | 31 | 2,613,959 | +0.0817 | 0.7241 | 0.4483 | 31 m, +0.076, 0.726, 0.452  |
| 19-72 m | con_sp_i | 181 | 31 | 2,613,959 | +0.0817 | 0.7241 | 0.4483 | 31 m, +0.076, 0.726, 0.452  |
| 19-72 m | vicino_piu_prossimo | 181 | 27 | 2,635,383 | +0.0900 | 0.7451 | 0.4902 | 31 m, +0.076, 0.726, 0.452  |
| 19-72 m | escl_r_tr_j_1.5 | 173 | 31 | 2,178,837 | +0.1370 | 0.7304 | 0.4608 | 31 m, +0.076, 0.726, 0.452  |
| 19-72 m | escl_entrambi_1.5 | 173 | 31 | 2,178,728 | +0.1370 | 0.7304 | 0.4609 | 31 m, +0.076, 0.726, 0.452  |
| 20-60 m | deliverable | 156 | 31 | 2,254,158 | +0.0873 | 0.7638 | 0.5276 | 31 m, +0.080, 0.761, 0.522  |
| 20-60 m | senza_filtro_imputazione_i | 156 | 31 | 2,254,158 | +0.0873 | 0.7638 | 0.5276 | 31 m, +0.080, 0.761, 0.522  |
| 20-60 m | con_sp_i | 156 | 31 | 2,254,158 | +0.0873 | 0.7638 | 0.5276 | 31 m, +0.080, 0.761, 0.522  |
| 20-60 m | vicino_piu_prossimo | 156 | 28 | 2,278,207 | +0.0924 | 0.7869 | 0.5737 | 31 m, +0.080, 0.761, 0.522  |
| 20-60 m | escl_r_tr_j_1.5 | 149 | 31 | 1,935,624 | +0.1312 | 0.7691 | 0.5381 | 31 m, +0.080, 0.761, 0.522  |
| 20-60 m | escl_entrambi_1.5 | 149 | 31 | 1,935,567 | +0.1312 | 0.7691 | 0.5381 | 31 m, +0.080, 0.761, 0.522  |
| 60-200 m | deliverable | 165 | 96 | 2,431,886 | +0.0329 | 0.5934 | 0.1867 | 96 m, +0.037, 0.598, 0.196  |
| 60-200 m | senza_filtro_imputazione_i | 165 | 96 | 2,431,886 | +0.0329 | 0.5934 | 0.1867 | 96 m, +0.037, 0.598, 0.196  |
| 60-200 m | con_sp_i | 165 | 96 | 2,431,886 | +0.0329 | 0.5934 | 0.1867 | 96 m, +0.037, 0.598, 0.196  |
| 60-200 m | vicino_piu_prossimo | 165 | 96 | 2,431,886 | +0.0329 | 0.5934 | 0.1867 | 96 m, +0.037, 0.598, 0.196  |
| 60-200 m | escl_r_tr_j_1.5 | 156 | 94 | 2,052,978 | +0.0494 | 0.5950 | 0.1900 | 96 m, +0.037, 0.598, 0.196  |
| 60-200 m | escl_entrambi_1.5 | 156 | 94 | 2,052,673 | +0.0495 | 0.5954 | 0.1908 | 96 m, +0.037, 0.598, 0.196  |

## 3. Austin — sezioni: 40 contro 31, e la sezione che esce dalla correzione 3

`carica_austin` esclude `direction == 'None'` (le tre intersezioni senza direzione) e definisce la sezione come `intname|direction`. Celle 4,554,698, corsie 76, sezioni 40; per numero di corsie: 1: 10, 2: 22, 3: 6, 4: 2.

| definizione | sezioni | = 31? |
|---|---:|---|
| sezioni (intname|direction) con direzione | 40 |  |
| intersezioni (intname) con direzione | 17 |  |
| sezioni con >= 2 corsie | 30 |  |
| sezioni con >= 2 corsie e >= 1.000 celle aggregate | 30 |  |
| sezioni con >= 2 corsie e AUC definita (> 20 rosse e > 20 non rosse) | 29 |  |
| sezioni con AUC definita (qualunque numero di corsie) | 31 | **si** |
| sezioni con >= 2 corsie da almeno 200 celle | 30 |  |
| sezioni con >= 1 corsia da almeno 200 celle | 40 |  |
| sezioni + intersezioni senza direzione (3) | 43 |  |

Sezioni con ≥ 2 corsie e AUC **non** definita (escluse dalla correzione 3, che richiede > 20 celle rosse e > 20 non rosse per sezione, `p4a.py` `austin`, come `sez_austin` del deliverable per la Tabella 69):

| sezione | corsie | celle aggregate | celle con ≥ 1 corsia rossa | celle senza |
|---|---:|---:|---:|---:|
| `LAMARZENNIA|SB` | 2 | 43,081 | 11 | 43,070 |

Livelli per numero di corsie come li stampa `sez_austin` (Tabella 69), con la differenza di prevalenza (celle con ≥ 1 corsia rossa meno celle con la sezione rossa, punti percentuali; ≥ 0 per costruzione):

| corsie | sezioni | celle aggregate | AUC mediana [q25; q75] (n con AUC definita) | diff. prevalenza (pp) |
|---:|---:|---:|---|---:|
| 1 | 10 | 244,367 | 0.948 [0.943; 0.953] (n=2) | -0.00 |
| 2 | 22 | 1,432,457 | 0.990 [0.982; 0.997] (n=21) | +0.19 |
| 3 | 6 | 433,660 | 0.755 [0.489; 0.995] (n=6) | +18.62 |
| 4 | 2 | 154,380 | 0.664 [0.533; 0.796] (n=2) | +9.88 |

Per sezione (≥ 2 corsie): celle, AUC, differenza di prevalenza — per cercare la sezione «−45,1 punti» del deliverable:

| sezione | corsie | celle | AUC | diff. prevalenza (pp) |
|---|---:|---:|---:|---:|
| `BURNETPALM WAY|NB` | 2 | 77,044 | 0.996 | +0.04 |
| `BURNETPALM WAY|SB` | 3 | 76,139 | 0.443 | +16.68 |
| `BurnetRutland|NB` | 2 | 77,233 | 0.989 | +0.10 |
| `BurnetRutland|SB` | 3 | 76,820 | 0.518 | +51.99 |
| `CESAR CHAVEZIH 35 WSR|EB` | 3 | 106,039 | 0.480 | +25.27 |
| `CESAR CHAVEZIH 35 WSR|WB` | 2 | 101,622 | 0.997 | +0.19 |
| `CONGRESSBARTON SPRINGS|NB` | 3 | 53,383 | 0.996 | +0.46 |
| `CONGRESSBARTON SPRINGS|SB` | 3 | 53,118 | 0.992 | +1.75 |
| `Cesar ChavezBR Reynolds|EB` | 2 | 77,163 | 0.970 | +0.23 |
| `Cesar ChavezBR Reynolds|WB` | 2 | 79,064 | 0.990 | +0.03 |
| `CongressJohanna|NB` | 2 | 49,667 | 0.997 | +0.03 |
| `CongressJohanna|SB` | 2 | 49,275 | 0.996 | +0.17 |
| `LAMARCOLLIER|NB` | 2 | 77,098 | 0.994 | +0.06 |
| `LAMARCOLLIER|SB` | 2 | 78,569 | 0.987 | +0.31 |
| `LAMARMANCHACA|NB` | 2 | 81,976 | 0.998 | +0.02 |
| `LAMARMANCHACA|SB` | 2 | 81,242 | 0.971 | +0.01 |
| `LAMARSANDRA MURAIDA|NB` | 2 | 66,385 | 0.963 | +1.04 |
| `LAMARSANDRA MURAIDA|SB` | 2 | 62,792 | 0.990 | +1.21 |
| `LAMARSHOALCREEK|NB` | 2 | 81,143 | 0.998 | +0.06 |
| `LAMARSHOALCREEK|SB` | 2 | 78,617 | 0.985 | +0.06 |
| `LAMARZENNIA|NB` | 2 | 42,074 | 0.998 | +0.03 |
| `LAMARZENNIA|SB` | 2 | 43,081 | n.d. | +0.01 |
| `LOOP 360CEDAR|NB` | 2 | 29,986 | 0.982 | +0.50 |
| `LOOP 360CEDAR|SB` | 2 | 30,410 | 0.864 | +0.12 |
| `LOOP 360LAKEWOOD|NB` | 2 | 81,872 | 0.955 | +0.03 |
| `LOOP 360LAKEWOOD|SB` | 4 | 84,505 | 0.402 | +17.53 |
| `LOOP 360WALSH TARLTON|NB` | 3 | 68,161 | 0.997 | +0.21 |
| `LOOP 360WALSH TARLTON|SB` | 4 | 69,875 | 0.927 | +0.63 |
| `N Lamar15th|NB` | 2 | 42,658 | 0.999 | +0.05 |
| `N Lamar15th|SB` | 2 | 43,486 | 0.998 | +0.11 |

Correlazione di rango fra numero di corsie e AUC per sezione (deliverable: −0,541, p = 0,002, su 31 sezioni):

- 31 sezioni con AUC definita, qualunque numero di corsie: n = 31, ρ = -0.269, p = 0.144
- 29 sezioni con ≥ 2 corsie e AUC definita (correzione 3): n = 29, ρ = -0.441, p = 0.017

Sezioni a 1 corsia (escluse dalla Tabella 69 come caso degenere): `LOOP 360CEDAR|NB3`, `LOOP 360CEDAR|NB4`, `LOOP 360CEDAR|SB1`, `LOOP 360CEDAR|SB2`, `LamarBroken Spoke|Lane1`, `LamarBroken Spoke|Lane2`, `LamarBroken Spoke|Lane3`, `LamarBroken Spoke|Lane4`, `Robert E LeeBarton Springs|NB`, `Robert E LeeBarton Springs|SB`.

Nota: la correlazione corsie/AUC «−0,541 su 31 sezioni» e la sezione esclusa per la differenza di prevalenza −45,1 punti (deliverable, pag. 133) non sono calcolate da nessuno script conservato (`validazione_colocalizzata.py`, `caratterizza_radar.py`): generatore **non trovato**.
