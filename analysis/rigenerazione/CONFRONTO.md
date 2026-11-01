# Paper 1 — verifica di testo (`--solo-testo`)

Generato da `analysis/main.py --solo-testo` (non modificare a mano). Nessuna fase eseguita e nessun numero rigenerato: i valori rigenerati sono quelli del giro completo di riferimento, valido per questi ingressi se le loro impronte coincidono con quelle registrate da quel giro.

- esito: **TUTTO COINCIDE**
- verifica di testo su giro completo protocol/spark/CONFRONTO_paper1-freeze-20261030l-pub3.md, OR3 ae50a25; esito di quel giro: TUTTO COINCIDE; manoscritto di quel giro: commit `41c960b43984af0b4773e860f2029bae7b408ed1`
- OR3 di questa verifica: commit `6403e7a08afbff6413272578e60d6ab31d8aa172` (pulito)
- ingressi (`results/evoluzione`): 289 impronte, diverse dal giro di riferimento: 0
- impronte citate nei congelamenti: 68, diverse: 0
- manoscritto (fuori dal repository): commit `c14cfd8e1c3617214f9aa1c0ea3aea860b9572c2` (pulito); SHA-256 `main.tex` 9b7ccd500b83dc07cfc6b32acb24ca9208fa3057794f6302a61e82e4510fd789, `supplementary.tex` 7f0c48a1e8a025c5a534f51caa9971107f063faf77637289a627b78d19b42224

## 1. Trascrizioni dei numeri nel testo

| tabella | voce | stampato | congelato | rigenerato (giro di riferimento) | scarto | esito |
|---|---|---|---:|---:|---:|---|
| I | origini > 1 sett., Mad. | 869 | 869 | 869 | 0 | ok |
| I | origini > 1 sett., Lon. | 883 | 883 | 883 | 0 | ok |
| I | origini > 1 sett., Mel. | 854 | 854 | 854 | 0 | ok |
| I | origini > 1 sett., PEMS04 | 168 | 168 | 168 | 0 | ok |
| I | origini > 1 sett., PEMS08 | 1423 | 1423 | 1423 | 0 | ok |
| I, II | A - C, Madrid (causale) | -0.040 | -0.0401172783648 | -0.0401172783648 | 0 | ok |
| I, II | A - C, Londra (causale) | -0.034 | -0.0343703457796 | -0.0343703457796 | 0 | ok |
| I, II | A - C, Melbourne (causale) | -0.045 | -0.0450263933112 | -0.0450263933112 | 0 | ok |
| I, II | A - C, PEMS08 | -0.133 | -0.132525592 | -0.132525592 | 0 | ok |
| II, §V | F0-C, Madrid (causale) | +0.075 | 0.0746019649735 | 0.0746019649735 | 0 | ok |
| II, §V | F0-C, Londra (causale) | +0.049 | 0.0486153661514 | 0.0486153661514 | 0 | ok |
| II, §V | F0-C, Melbourne (causale) | +0.078 | 0.0781145735936 | 0.0781145735936 | 0 | ok |
| II, §V | F0p-C, Madrid (causale) | +0.008 | 0.00783961089552 | 0.00783961089552 | 0 | ok |
| II, §V | F0p-C, Londra (causale) | +0.014 | 0.0137686787154 | 0.0137686787154 | 0 | ok |
| II, §V | F0p-C, Melbourne (causale) | 0.000 | 0.000220417611945 | 0.000220417611945 | 0 | ok |
| II, §V | Fp_672-C, Madrid (causale) | -0.031 | -0.0311312379253 | -0.0311312379253 | 0 | ok |
| II, §V | Fp_672-C, Londra (causale) | -0.031 | -0.0308726927005 | -0.0308726927005 | 0 | ok |
| II, §V | Fp_672-C, Melbourne (causale) | -0.040 | -0.040027724888 | -0.040027724888 | 0 | ok |
| II, §V | Fp_672-A, Madrid (causale) | +0.008 | 0.00797550422574 | 0.00797550422574 | 0 | ok |
| II, §V | Fp_672-A, Londra (causale) | +0.008 | 0.00838346292543 | 0.00838346292543 | 0 | ok |
| II, §V | Fp_672-A, Melbourne (causale) | -0.002 | -0.00167715897065 | -0.00167715897065 | 0 | ok |
| II, §V | A-C_A, Madrid (causale) | -0.038 | -0.0381983736651 | -0.0381983736651 | 0 | ok |
| II, §V | A-C_A, Londra (causale) | -0.033 | -0.0331789772472 | -0.0331789772472 | 0 | ok |
| II, §V | A-C_A, Melbourne (causale) | -0.037 | -0.0366500996166 | -0.0366500996166 | 0 | ok |
| §V-A | (F0 - C)/(A - C_A), minimo sulle citta' (causale) | 1.5 | -1.46524607402 | -1.46524607402 | 0 | ok |
| §V-A | (F0 - C)/(A - C_A), massimo sulle citta' (causale) | 2.1 | -2.13136047134 | -2.13136047134 | 0 | ok |
| II | F0-C, PEMS08 | +0.156 | 0.156490961717 | 0.156490961717 | 0 | ok |
| II | F0p-C, PEMS08 | -0.039 | -0.0394311960087 | -0.0394311960087 | 0 | ok |
| III-B | F'(24 h) - C, Madrid (sei semi, episodio 1) | -0.011 | -0.0111972446731 | -0.0111972446731 | 0 | ok |
| III-B | F'(24 h) - C, Londra (sei semi, episodio 1) | +0.032 | 0.031670135316 | 0.031670135316 | 0 | ok |
| III-B | F'(24 h) - C, Melbourne (sei semi, episodio 1) | -0.020 | -0.0195346274074 | -0.0195346274074 | 0 | ok |
| III-B | (d) PEMS08 | -0.074 | -0.0738236406527 | -0.0738236406527 | 0 | ok |
| III-B | (e) PEMS08 | +0.040 | 0.0395886280471 | 0.0395886280471 | 0 | ok |
| II, III | F'(1 wk) - C, PEMS08 | -0.091 | -0.0908492906919 | -0.0908492906919 | 0 | ok |
| II | gated - F0', massimo sui nove episodi | <= +0.004 | 0.000531946038111 | 0.000531946038111 | 0 | ok |
| II tempi | Fp_96, Madrid | 14 | 14.4177479744 | 14.4177479744 | 0 | ok (ingresso) |
| II tempi | Fp_672, Madrid | 138 | 138.350170851 | 138.350170851 | 0 | ok (ingresso) |
| II tempi | R-orig_96, Madrid | 2225 | 2225.2480011 | 2225.2480011 | 0 | ok (ingresso) |
| II tempi | R-orig_672, Madrid | 2229 | 2228.89215088 | 2228.89215088 | 0 | ok (ingresso) |
| II tempi | R-orig(1 wk) / F'(1 wk), Madrid | 16.1 | 16.1105124567 | 16.1105124567 | 0 | ok (ingresso) |
| II tempi | addestramento C (min), Madrid | 41.1 | 41.1158252637 | 41.1158252637 | 0 | ok (ingresso) |
| II tempi | addestramento E1 (min), Madrid | 41.2 | 41.1905310869 | 41.1905310869 | 0 | ok (ingresso) |
| II tempi | Fp_96, Londra | 15 | 14.5284748077 | 14.5284748077 | 0 | ok (ingresso) |
| II tempi | Fp_672, Londra | 139 | 138.817257881 | 138.817257881 | 0 | ok (ingresso) |
| II tempi | R-orig_96, Londra | 2228 | 2228.43431497 | 2228.43431497 | 0 | ok (ingresso) |
| II tempi | R-orig_672, Londra | 2228 | 2228.44759321 | 2228.44759321 | 0 | ok (ingresso) |
| II tempi | R-orig(1 wk) / F'(1 wk), Londra | 16.1 | 16.0531019502 | 16.0531019502 | 0 | ok (ingresso) |
| II tempi | addestramento C (min), Londra | 41.0 | 41.0430243651 | 41.0430243651 | 0 | ok (ingresso) |
| II tempi | addestramento E1 (min), Londra | 41.1 | 41.0922940652 | 41.0922940652 | 0 | ok (ingresso) |
| II tempi | Fp_96, Melbourne | 39 | 38.7914543152 | 38.7914543152 | 0 | ok (ingresso) |
| II tempi | Fp_672, Melbourne | 401 | 401.33042407 | 401.33042407 | 0 | ok (ingresso) |
| II tempi | R-orig_96, Melbourne | 1556 | 1555.96331716 | 1555.96331716 | 0 | ok (ingresso) |
| II tempi | R-orig_672, Melbourne | 1557 | 1557.45345378 | 1557.45345378 | 0 | ok (ingresso) |
| II tempi | R-orig(1 wk) / F'(1 wk), Melbourne | 3.9 | 3.88072610589 | 3.88072610589 | 0 | ok (ingresso) |
| II tempi | addestramento C (min), Melbourne | 29.1 | 29.1001541654 | 29.1001541654 | 0 | ok (ingresso) |
| II tempi | addestramento E1 (min), Melbourne | 29.2 | 29.2365280469 | 29.2365280469 | 0 | ok (ingresso) |
| II tempi | Fp_96, PEMS08 | 13 | 13.1187236309 | 13.1187236309 | 0 | ok (ingresso) |
| II tempi | Fp_672, PEMS08 | 127 | 127.005913973 | 127.005913973 | 0 | ok (ingresso) |
| II tempi | R-orig_96, PEMS08 | 377 | 376.789088011 | 376.789088011 | 0 | ok (ingresso) |
| II tempi | R-orig_672, PEMS08 | 379 | 378.730353117 | 378.730353117 | 0 | ok (ingresso) |
| II tempi | R-orig(1 wk) / F'(1 wk), PEMS08 | 3.0 | 2.98198990323 | 2.98198990323 | 0 | ok (ingresso) |
| II tempi | addestramento C (min), PEMS08 | 7.1 | 7.09993986686 | 7.09993986686 | 0 | ok (ingresso) |
| II tempi | addestramento E1 (min), PEMS08 | 7.1 | 7.07598810196 | 7.07598810196 | 0 | ok (ingresso) |
| §III | dimensione dell'embedding | 8 | 8 | 8 | 0 | ok |
| §III | canali Traffic4cast | 9 | 9 | 9 | 0 | ok |
| §III | canali PEMS | 11 | 11 | 11 | 0 | ok |
| §III | canali nascosti | 32 | 32 | 32 | 0 | ok |
| §III | blocchi | 4 | 4 | 4 | 0 | ok |
| §III | uscite (4 orizzonti x 3 classi) | 12 | 12 | 12 | 0 | ok |
| §III | K Melbourne | 415 | 415 | 415 | 0 | ok |
| §III | K Madrid e Londra | 630 | 630 | 630 | 0 | ok |
| §III | parametri del token | 8 | 8 | 8 | 0 | ok |
| §III | finestra (passi) | 12 | 12 | 12 | 0 | ok |
| §III | nucleo | 2 | 2 | 2 | 0 | ok |
| §III | campo ricettivo (passi) | 16 | 16 | 16 | 0 | ok |
| §III | K PEMS04 | 214 | 214 | 214 | 0 | ok |
| §III | K PEMS08 | 118 | 118 | 118 | 0 | ok |
| §III | parametri Madrid e Londra | 28752 | 28752 | 28752 | 0 | ok |
| §III | parametri Melbourne | 27032 | 27032 | 27032 | 0 | ok |
| §III | parametri PEMS08 | 24720 | 24720 | 24720 | 0 | ok |
| §III | parametri PEMS04 (E') | 25496 | 25496 | 25496 | 0 | ok |
| §III | corpo condiviso, 9 canali | 23712 | 23712 | 23712 | 0 | ok |
| §III | corpo condiviso, 11 canali | 23776 | 23776 | 23776 | 0 | ok |
| §III | dilatazioni | 1, 2, 4, 8 | [1, 2, 4, 8] | [1, 2, 4, 8] | = | ok |
| §V-A | dAUC F0-C, PEMS08 (E18) | +0.008 | 0.00827906955777 | 0.00827906955777 | 0 | ok |
| §V-A | dAUC F0p-F0, PEMS08 (E18) | -0.004 | -0.00402102136357 | -0.00402102136357 | 0 | ok |
| §V-A | dAUC F0-C, minimo sulle citta' (E18) | -0.051 | -0.0513271746402 | -0.0513271746402 | 0 | ok |
| §V-A | dAUC F0-C, massimo sulle citta' (E18) | -0.018 | -0.018221120357 | -0.018221120357 | 0 | ok |
| §V-A | dAUC F0p-F0, minimo sulle citta' (E18) | +0.013 | 0.0134979332685 | 0.0134979332685 | 0 | ok |
| §V-A | dAUC F0p-F0, massimo sulle citta' (E18) | +0.045 | 0.0454542734838 | 0.0454542734838 | 0 | ok |
| §V-A | dAUC A-C, minimo sulle citta' (E18) | +0.017 | 0.0172459325915 | 0.0172459325915 | 0 | ok |
| §V-A | dAUC A-C, massimo sulle citta' (E18) | +0.036 | 0.0364881988723 | 0.0364881988723 | 0 | ok |
| §V-A | richiamo a FA 5 % F0-C, perdita minima sulle citta' (E18) | 1.3 | -0.0132494524885 | -0.0132494524885 | 0 | ok |
| §V-A | richiamo a FA 5 % F0-C, perdita massima sulle citta' (E18) | 4.5 | -0.0453481815884 | -0.0453481815884 | 0 | ok |
| §V-A | richiamo a FA 5 % F0-C, PEMS08 (E18) | +5.3 | 0.05288878301 | 0.05288878301 | 0 | ok |
| §V-A | quota recuperata a FA 5 %, Madrid (E18) | 92 | 0.917592159819 | 0.917592159819 | 0 | ok |
| §V-A | quota recuperata a FA 5 %, Londra (E18) | 84 | 0.838731407105 | 0.838731407105 | 0 | ok |
| §V-A | quota recuperata a FA 5 %, Melbourne (E18) | 80 | 0.801656433341 | 0.801656433341 | 0 | ok |
| §V-B | dAUC F'(1 wk) - C, minimo sui cinque contesti (E18) | +0.007 | 0.00735190868396 | 0.00735190868396 | 0 | ok |
| §V-B | dAUC F'(1 wk) - C, massimo sui cinque contesti (E18) | +0.032 | 0.0324661375716 | 0.0324661375716 | 0 | ok |
| §V-B | margine minimo per sensore, E3-bis Madrid (E18) | 0.006 | 0.00610180216275 | 0.00610180216275 | 0 | ok |
| §V-B | margine minimo per sensore, E3-bis Londra (E18) | 0.005 | 0.004903930846 | 0.004903930846 | 0 | ok |
| §V-B | margine minimo per sensore, E3-bis Melbourne (E18) | 0.020 | 0.0203652082047 | 0.0203652082047 | 0 | ok |
| §V-B | margine minimo per sensore, PEMS08 (E18) | 0.100 | 0.0998448915119 | 0.0998448915119 | 0 | ok |

## 2. Tabelle e figure del manoscritto (riusate dal giro di riferimento)

Confronto con la versione del manoscritto del giro di riferimento: identica, o con il solo testo cambiato e gli stessi numeri (stesso multinsieme di valori numerici); figure PDF identiche al byte.

| file | stato |
|---|---|
| `cronologia.pdf` | identica |
| `curva_e4.pdf` | identica |
| `curve_e8bis.pdf` | identica |
| `episodi_e5.pdf` | identica |
| `figura2_51.pdf` | identica |
| `rete.pdf` | identica |
| `tableC1_episodes.tex` | identica |
| `tableC3_operative.tex` | identica |
| `tableC8_classi.tex` | identica |
| `tableC9_orizzonti.tex` | identica |
| `tableD_e14.tex` | identica |
| `tableE_e15.tex` | identica |
| `tableE_e16.tex` | identica |
| `tableG_e18.tex` | solo testo (numeri identici) |
| `tableG_e18ter.tex` | identica |
| `table_policies.tex` | identica |
| `table_replication.tex` | identica |
| `traiettoria_e4.pdf` | identica |

## 3. Rimandi

Ogni \ref e \Sref ha la sua etichetta (\Sref nel supplemento), nessuna etichetta e' duplicata, ogni \cite ha la sua voce in bibliografia.

Nessun problema.

## 4. Problemi

Nessuno.
