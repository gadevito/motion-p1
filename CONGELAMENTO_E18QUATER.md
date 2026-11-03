# CONGELAMENTO E18-QUATER — coverage di valutazione di C_A e classi per sensore

Generato da `genera_congelamento_e18quater.py` al commit `b4ab62a`, 2026-11-03 11:39 UTC. Protocollo `protocol/E18quater.md` (nota datata del 3/11/2026; impronta `56046a7784a5169e`); `e18quater_risultati.json` impronta `316f1f9a3b0fa29e`; `e18quater_classi_risultati.json` impronta `020fea6939297a96`. Nessun addestramento: parte A a modelli congelati di E15, parte B sola lettura dei bersagli.

## 1. Parte A — C_A ri-valutato con la coverage dei sensori nuovi uguale a quella di C

Braccio `C_A`; statica dei nuovi in valutazione «espansiva» (E15: coverage su [0, t0) per A e C_A); 4000 ricampionamenti congiunti (partizioni × semi × posizioni dei nodi), seme 20261023, δ = 0.005. Perimetro: origini comuni dopo t1 (fasce d'eta' 1-3); settimana = origini con eta' > 1 settimana (fascia 3).

**Controlli bloccanti**: ogni cella: ri-valutazione con la statica di E15 identica bit per bit agli aggregati di E15; medie dei riferimenti contro `e15_risultati.json` (impronta `82df1d02792e330e`): Madrid/A-C scarto 0.0e+00; Madrid/A-C_A scarto 0.0e+00; Madrid/C_A-C scarto 0.0e+00; Londra/A-C scarto 0.0e+00; Londra/A-C_A scarto 0.0e+00; Londra/C_A-C scarto 0.0e+00; Melbourne/A-C scarto 0.0e+00; Melbourne/A-C_A scarto 0.0e+00; Melbourne/C_A-C scarto 0.0e+00: superati.

| citta' | differenza | media [IC 95 %] | segno | categoria | > 1 sett.: media [IC] | E15: media [IC] |
|---|---|---|---|---|---|---|
| Madrid | C_A^esp − C_A (effetto della coverage) | +0.0010 [+0.0003, +0.0017] | + | non inferiorita' | +0.0005 [-0.0001, +0.0010] | — |
| Madrid | C_A^esp − C (effetto dei dati, pari coverage) | -0.0010 [-0.0016, -0.0004] | - | superiorita' | -0.0008 [-0.0013, -0.0002] | — |
| Madrid | A − C_A^esp | -0.0392 [-0.0441, -0.0345] | - | superiorita' | -0.0383 [-0.0430, -0.0337] | — |
| Madrid | A − C (riferimento E15) | -0.0401 [-0.0453, -0.0353] | - | superiorita' | -0.0391 [-0.0440, -0.0345] | -0.0401 [-0.0453, -0.0353] |
| Madrid | A − C_A (riferimento E15) | -0.0382 [-0.0431, -0.0335] | - | superiorita' | -0.0379 [-0.0426, -0.0332] | -0.0382 [-0.0431, -0.0335] |
| Madrid | C_A − C (riferimento E15) | -0.0019 [-0.0029, -0.0010] | - | superiorita' | -0.0012 [-0.0021, -0.0004] | -0.0019 [-0.0029, -0.0010] |
| Londra | C_A^esp − C_A (effetto della coverage) | -0.0000 [-0.0001, +0.0000] | 0 | non inferiorita' | -0.0000 [-0.0001, +0.0000] | — |
| Londra | C_A^esp − C (effetto dei dati, pari coverage) | -0.0012 [-0.0026, -0.0002] | - | superiorita' | -0.0013 [-0.0026, -0.0003] | — |
| Londra | A − C_A^esp | -0.0331 [-0.0373, -0.0289] | - | superiorita' | -0.0380 [-0.0420, -0.0336] | — |
| Londra | A − C (riferimento E15) | -0.0344 [-0.0390, -0.0299] | - | superiorita' | -0.0393 [-0.0439, -0.0346] | -0.0344 [-0.0390, -0.0299] |
| Londra | A − C_A (riferimento E15) | -0.0332 [-0.0374, -0.0290] | - | superiorita' | -0.0380 [-0.0420, -0.0337] | -0.0332 [-0.0374, -0.0290] |
| Londra | C_A − C (riferimento E15) | -0.0012 [-0.0026, -0.0001] | - | superiorita' | -0.0013 [-0.0026, -0.0003] | -0.0012 [-0.0026, -0.0001] |
| Melbourne | C_A^esp − C_A (effetto della coverage) | +0.0064 [+0.0038, +0.0095] | + | inferiorita' | +0.0049 [+0.0026, +0.0076] | — |
| Melbourne | C_A^esp − C (effetto dei dati, pari coverage) | -0.0020 [-0.0041, -0.0005] | - | superiorita' | -0.0017 [-0.0037, -0.0002] | — |
| Melbourne | A − C_A^esp | -0.0430 [-0.0537, -0.0317] | - | superiorita' | -0.0367 [-0.0486, -0.0239] | — |
| Melbourne | A − C (riferimento E15) | -0.0450 [-0.0566, -0.0330] | - | superiorita' | -0.0384 [-0.0511, -0.0250] | -0.0450 [-0.0566, -0.0330] |
| Melbourne | A − C_A (riferimento E15) | -0.0367 [-0.0467, -0.0256] | - | superiorita' | -0.0318 [-0.0432, -0.0195] | -0.0367 [-0.0467, -0.0256] |
| Melbourne | C_A − C (riferimento E15) | -0.0084 [-0.0124, -0.0052] | - | superiorita' | -0.0066 [-0.0103, -0.0038] | -0.0084 [-0.0124, -0.0052] |

| citta' | celle | nodi | C | A | C_A | C_A^esp | quota del divario C_A − C dovuta alla coverage [IC] | repliche con C_A − C ≥ 0 |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| Madrid | 18 | 135 | 0.9610 | 0.9209 | 0.9591 | 0.9601 | 0.505 [0.242, 0.725] | 0 |
| Londra | 18 | 135 | 0.8902 | 0.8559 | 0.8891 | 0.8890 | -0.038 [-0.305, 0.048] | 68 |
| Melbourne | 18 | 90 | 0.8206 | 0.7756 | 0.8122 | 0.8186 | 0.761 [0.590, 0.935] | 0 |

Quota: (C_A - C_A_esp) / (C_A - C): quota del divario C_A - C dovuta alla coverage di valutazione; il resto, (C_A_esp - C) / (C_A - C), ai dati anteriori a t0 nell'addestramento.

## 2. Parte B — classi per sensore nei bersagli del periodo di prova

per sensore, quota di bersagli nella classe congestionata (3) fra le celle (origine, orizzonte) valide (classe > 0) del periodo di prova: origini dopo t1 fino alla fine del periodo (origini_dopo, come le valutazioni), quattro orizzonti; statistiche sulle coppie (partizione, sensore) per gruppo. Gruppi: iniziali = nodi di addestramento, nuovi = nodi di prova, validazione = nodi di validazione della partizione.

| contesto | partizioni | sensori/part. | origini/part. | gruppo | coppie (part., sensore) | min | q1 | mediana | q3 | max | media | zero congestionati | senza bersagli | quota aggregata | frequenze (1, 2, 3) |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Madrid | 3 | 900 | 1426 | iniziali | 1890 | 0.000 | 0.032 | 0.086 | 0.158 | 0.698 | 0.110 | 11 | 0 | 0.104 | 4,032,788, 4,315,175, 969,091 |
|  |  |  |  | nuovi | 405 | 0.000 | 0.033 | 0.083 | 0.156 | 0.450 | 0.106 | 4 | 0 | 0.101 | 867,963, 923,255, 200,619 |
|  |  |  |  | validazione | 405 | 0.001 | 0.029 | 0.074 | 0.145 | 0.413 | 0.105 | 0 | 0 | 0.099 | 888,286, 918,233, 198,947 |
| Londra | 3 | 900 | 1440 | iniziali | 1890 | 0.001 | 0.045 | 0.099 | 0.178 | 0.836 | 0.132 | 0 | 0 | 0.132 | 3,150,821, 2,696,499, 890,859 |
|  |  |  |  | nuovi | 405 | 0.001 | 0.044 | 0.088 | 0.165 | 0.680 | 0.120 | 0 | 0 | 0.120 | 687,230, 594,183, 175,464 |
|  |  |  |  | validazione | 405 | 0.001 | 0.041 | 0.092 | 0.177 | 0.836 | 0.133 | 0 | 0 | 0.137 | 665,753, 578,727, 197,520 |
| Melbourne | 3 | 594 | 1411 | iniziali | 1245 | 0.000 | 0.008 | 0.033 | 0.077 | 0.668 | 0.058 | 87 | 0 | 0.055 | 4,100,877, 1,285,928, 310,617 |
|  |  |  |  | nuovi | 270 | 0.000 | 0.007 | 0.030 | 0.077 | 0.533 | 0.059 | 11 | 0 | 0.056 | 894,751, 269,766, 69,245 |
|  |  |  |  | validazione | 267 | 0.000 | 0.006 | 0.034 | 0.078 | 0.533 | 0.059 | 16 | 0 | 0.056 | 866,324, 290,875, 68,014 |
| PEMS08 | 6 | 170 | 1999 | iniziali | 708 | 0.000 | 0.000 | 0.001 | 0.009 | 0.287 | 0.014 | 327 | 0 | 0.014 | 5,298,858, 281,935, 80,375 |
|  |  |  |  | nuovi | 156 | 0.000 | 0.000 | 0.001 | 0.013 | 0.287 | 0.016 | 74 | 0 | 0.016 | 1,159,427, 68,551, 19,398 |
|  |  |  |  | validazione | 156 | 0.000 | 0.000 | 0.001 | 0.013 | 0.287 | 0.018 | 72 | 0 | 0.018 | 1,156,419, 68,306, 22,651 |
| PEMS04 | 3 | 307 | 744 | iniziali | 642 | 0.000 | 0.000 | 0.007 | 0.044 | 0.423 | 0.030 | 246 | 0 | 0.030 | 1,731,826, 121,052, 57,714 |
|  |  |  |  | nuovi | 141 | 0.000 | 0.000 | 0.007 | 0.034 | 0.198 | 0.027 | 46 | 0 | 0.027 | 383,393, 25,049, 11,174 |
|  |  |  |  | validazione | 138 | 0.000 | 0.000 | 0.003 | 0.035 | 0.208 | 0.023 | 53 | 0 | 0.023 | 379,276, 21,910, 9,502 |

Finestre (passi di 15 min): Madrid: t0 8887, t1 8983, fine 10456; Londra: t0 8966, t1 9062, fine 10549; Melbourne: t0 8806, t1 8902, fine 10360; PEMS08: t0 3840, t1 3936, fine 5944; PEMS04: t0 4807, t1 4903, fine 5656.

## 3. Note datate

- 3/11/2026, parte A: ri-valutazione a modelli congelati; le medie e gli intervalli dei riferimenti A − C, A − C_A, C_A − C coincidono con E15 (stesse celle, stessi aggregati, stesse estrazioni del ricampionamento).
- 3/11/2026, parte B: perimetro identico alle valutazioni (unita' di E8, `origini_dopo`); nessun numero del Paper 1 dipende da questa tabella, che descrive i bersagli.

## 4. Impronte

- `results/evoluzione/e18quater_risultati.json` `316f1f9a3b0fa29e`; `results/evoluzione/e18quater_classi_risultati.json` `020fea6939297a96`; `protocol/E18quater.md` `56046a7784a5169e`; `results/evoluzione/congelamento_e18quater.json` `b2fb7829d3995659`.
- Ingressi: 133 file (celle `predizioni_e15/prova_*.npz`, punti di controllo di C_A, `e15_risultati.json`, bersagli e maschere dei contesti), insieme `281801b89676836a`.
- `evoluzione/esperimenti/esegui_e18quater.py` `efd45c86dc337a1d`; `evoluzione/analisi/classi_per_sensore.py` `8b8cb7c5ee1fe265`.
