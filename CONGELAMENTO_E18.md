# CONGELAMENTO E18 — analisi di verifica dalla seconda revisione esterna

Generato da `genera_congelamento_e18.py` al commit `0fe01d6`, 2026-10-29 08:58 UTC. Protocollo `protocol/E18.md` (impronta `42da14831a4e982c`; firma 28/10/2026, commit 964e4f5), letto per intero prima del codice; `e18_risultati.json` impronta `7a77b98705da6861`. Nessun addestramento: sola analisi da artefatti congelati. Parti presenti: C, A, B, D. Ordine di esecuzione: C → A → B → D.

## 1. Parte C — E16: finestra di F′(1 sett.) (correzione 27)

finestra: origini con eta' > 1 settimana per F'(1 sett.) E per C; parametri di calibrazione di e16_risultati.json (stimati sulla validazione della stessa cella), invariati. Finestra: origini con eta' > 672 passi. 4000 ricampionamenti congiunti (schema di E16), seme 20261028.

**Controllo bloccante**: per ciascuna delle 144 celle di prova, la wCE grezza per orizzonte di F′(1 sett.) e di C sulla finestra, ricalcolata dalle probabilita' di E16, contro l'aggregato congelato della campagna (fascia eta' > 1 settimana di `predizioni_e4` per le citta', di `predizioni_e6` per PEMS08), nodi e origini identici: scarto relativo massimo **8.66e-07** (soglia 1e-06): superato.

| contesto | calibrazione | wCE F′(1 sett.), > 1 sett. | wCE C, > 1 sett. | F′(1 sett.) − C, > 1 sett. [IC 95 %] | categoria | F′(1 sett.) − C, intero periodo (E16, non causale per la prima settimana) |
|---|---|---|---|---|---|---|
| Madrid | grezzo | 0.9310 | 0.9626 | -0.0316 [-0.0371, -0.0270] | superiorita' | -0.0383 [-0.0433, -0.0337] |
|  | T (log-loss) | 0.9316 | 0.9644 | -0.0328 [-0.0385, -0.0279] | superiorita' | -0.0384 [-0.0437, -0.0335] |
|  | T (wCE) | 0.9303 | 0.9625 | -0.0323 [-0.0376, -0.0277] | superiorita' | -0.0387 [-0.0435, -0.0343] |
|  | V (log-loss) | 1.0898 | 1.1561 | -0.0663 [-0.0836, -0.0501] | superiorita' | -0.0704 [-0.0877, -0.0546] |
|  | V (wCE) | 0.9306 | 0.9624 | -0.0318 [-0.0369, -0.0273] | superiorita' | -0.0381 [-0.0427, -0.0339] |
| Londra | grezzo | 0.8581 | 0.8883 | -0.0302 [-0.0344, -0.0260] | superiorita' | -0.0368 [-0.0406, -0.0328] |
|  | T (log-loss) | 0.8576 | 0.8882 | -0.0306 [-0.0345, -0.0269] | superiorita' | -0.0365 [-0.0403, -0.0328] |
|  | T (wCE) | 0.8572 | 0.8882 | -0.0310 [-0.0348, -0.0271] | superiorita' | -0.0372 [-0.0408, -0.0336] |
|  | V (log-loss) | 0.9531 | 0.9347 | +0.0183 [+0.0088, +0.0272] | inferiorita' | +0.0072 [-0.0015, +0.0152] |
|  | V (wCE) | 0.8624 | 0.8892 | -0.0267 [-0.0314, -0.0223] | superiorita' | -0.0340 [-0.0381, -0.0302] |
| Melbourne | grezzo | 0.7772 | 0.8136 | -0.0364 [-0.0433, -0.0298] | superiorita' | -0.0457 [-0.0529, -0.0392] |
|  | T (log-loss) | 0.7766 | 0.8142 | -0.0376 [-0.0443, -0.0312] | superiorita' | -0.0469 [-0.0538, -0.0406] |
|  | T (wCE) | 0.7779 | 0.8130 | -0.0351 [-0.0416, -0.0289] | superiorita' | -0.0436 [-0.0499, -0.0378] |
|  | V (log-loss) | 1.0455 | 1.1549 | -0.1094 [-0.1325, -0.0861] | superiorita' | -0.1174 [-0.1403, -0.0949] |
|  | V (wCE) | 0.7822 | 0.8118 | -0.0296 [-0.0359, -0.0233] | superiorita' | -0.0385 [-0.0443, -0.0332] |
| PEMS08 | grezzo | 0.5186 | 0.6094 | -0.0908 [-0.1320, -0.0403] | superiorita' | -0.1061 [-0.1431, -0.0616] |
|  | T (log-loss) | 0.5202 | 0.6073 | -0.0871 [-0.1265, -0.0376] | superiorita' | -0.1017 [-0.1363, -0.0586] |
|  | T (wCE) | 0.5205 | 0.5774 | -0.0570 [-0.0958, -0.0008] | superiorita' | -0.0719 [-0.1048, -0.0290] |
|  | V (log-loss) | 1.0116 | 1.1006 | -0.0889 [-0.1779, +0.0213] | inconclusivo | -0.1114 [-0.1902, -0.0181] |
|  | V (wCE) | 0.5212 | 0.5674 | -0.0462 [-0.0916, +0.0100] | inconclusivo | -0.0613 [-0.1000, -0.0205] |

Le righe F′(1 sett.) di F15 (differenze) e di F16 (metriche per braccio) vanno sostituite con questi valori; in F16 si aggiunge la riga «C, origini > 1 settimana» per ogni calibrazione (colonna «wCE C, > 1 sett.»). I parametri di temperature e vector scaling sono quelli di E16 (stimati sulla validazione): cambia solo la finestra di valutazione.

## 2. Parte A — ROC empirica, AUC, pAUC(0–10 %), richiamo a falsi allarmi fissi

punteggio = p(congestionata) per (origine, sensore, orizzonte) sui bersagli validi; ROC empirica su tutti i punteggi distinti per cella, orizzonti e sensori riuniti; AUC trapezoidale; pAUC su FPR in [0, 0.10] (area / 0.10); richiamo a FA 0.5/1/2/5/10 % per interpolazione lineare; unita' = cella, media sulle celle. Finestre: tutte le origini dopo t1 (C, A, F0, F0'); origini con eta' > 1 settimana (F'(1 sett.) e C). Intervalli: 4000 ricampionamenti congiunti (partizioni × semi × posizioni dei sensori) con pesi di molteplicita' sui sensori, ordinamento una volta per cella e braccio; stessi indici per i due bracci di una differenza; seme 20261028 + indice del gruppo.

PEMS04 (A.6): ricostruzione tipo E16 in `predizioni_e18_pems04/` (36 celle di prova, 3 controlli per cella); bracci C, F₀′, F′(1 sett.): A1, A2, A4 not defined (no E, no A); A3 and F₀′ − C only.

| gruppo | celle | sensori | parete (min) | ore-macchina | s per cella (mediana) | verifica sklearn: scarto AUC / richiami | punteggi | soglie distinte |
|---|---|---|---|---|---|---|---|---|
| Madrid | 36 | 135 | 20.2 | 4.88 | 466 | 0.0e+00 / 0.0e+00 | 666282 | 653519 |
| Londra | 36 | 135 | 15.6 | 3.63 | 343 | 0.0e+00 / 0.0e+00 | 489710 | 483612 |
| Melbourne | 36 | 90 | 13.0 | 2.97 | 279 | 0.0e+00 / 0.0e+00 | 409801 | 408027 |
| PEMS08 | 36 | 26 | 5.5 | 1.25 | 117 | 0.0e+00 / 0.0e+00 | 207896 | 167690 |
| PEMS04 | 36 | 47 | 1.6 | 0.39 | 41 | 0.0e+00 / 0.0e+00 | 139872 | 129413 |

Totale: 13.1 ore-macchina; sotto le 6 h per citta' del protocollo, quindi 4.000 repliche ovunque.

### 2a. AUC e pAUC per braccio (media sulle celle [IC 95 %])

| gruppo | braccio / finestra | AUC | pAUC (0–10 %) | AUC a 19 soglie (E8-bis, sostituita) |
|---|---|---|---|---|
| Madrid | A / intero | +0.7834 [+0.7595, +0.8065] | +0.2221 [+0.1912, +0.2549] | 0.7826 |
| Madrid | C / intero | +0.7469 [+0.7215, +0.7719] | +0.1969 [+0.1704, +0.2248] | 0.7460 |
| Madrid | C / > 1 sett. | +0.7459 [+0.7204, +0.7706] | +0.1914 [+0.1654, +0.2198] | 0.7449 |
| Madrid | F0 / intero | +0.6956 [+0.6713, +0.7201] | +0.1603 [+0.1382, +0.1830] | 0.6886 |
| Madrid | F0p / intero | +0.7411 [+0.7162, +0.7659] | +0.1913 [+0.1668, +0.2177] | 0.7397 |
| Madrid | Fp_672 / > 1 sett. | +0.7784 [+0.7538, +0.8019] | +0.2173 [+0.1853, +0.2513] | 0.7778 |
| Londra | A / intero | +0.8116 [+0.7875, +0.8331] | +0.3354 [+0.2868, +0.3814] | 0.8107 |
| Londra | C / intero | +0.7874 [+0.7610, +0.8110] | +0.3172 [+0.2698, +0.3624] | 0.7863 |
| Londra | C / > 1 sett. | +0.7915 [+0.7651, +0.8143] | +0.3219 [+0.2735, +0.3667] | 0.7906 |
| Londra | F0 / intero | +0.7692 [+0.7447, +0.7907] | +0.3050 [+0.2602, +0.3467] | 0.7669 |
| Londra | F0p / intero | +0.7827 [+0.7561, +0.8062] | +0.3129 [+0.2665, +0.3570] | 0.7815 |
| Londra | Fp_672 / > 1 sett. | +0.8114 [+0.7865, +0.8329] | +0.3334 [+0.2820, +0.3814] | 0.8101 |
| Melbourne | A / intero | +0.8891 [+0.8719, +0.9048] | +0.4744 [+0.4308, +0.5186] | 0.8866 |
| Melbourne | C / intero | +0.8719 [+0.8528, +0.8887] | +0.4526 [+0.4117, +0.4937] | 0.8701 |
| Melbourne | C / > 1 sett. | +0.8732 [+0.8526, +0.8910] | +0.4619 [+0.4143, +0.5084] | 0.8718 |
| Melbourne | F0 / intero | +0.8419 [+0.8223, +0.8603] | +0.4162 [+0.3768, +0.4583] | 0.8378 |
| Melbourne | F0p / intero | +0.8727 [+0.8547, +0.8890] | +0.4521 [+0.4118, +0.4933] | 0.8710 |
| Melbourne | Fp_672 / > 1 sett. | +0.8917 [+0.8731, +0.9073] | +0.4879 [+0.4400, +0.5350] | 0.8904 |
| PEMS08 | A / intero | +0.9710 [+0.9510, +0.9824] | +0.8106 [+0.7080, +0.8725] | 0.9567 |
| PEMS08 | C / intero | +0.9523 [+0.9310, +0.9666] | +0.7249 [+0.6357, +0.7878] | 0.9354 |
| PEMS08 | C / > 1 sett. | +0.9531 [+0.9335, +0.9674] | +0.7264 [+0.6435, +0.7886] | 0.9359 |
| PEMS08 | F0 / intero | +0.9606 [+0.9423, +0.9734] | +0.7786 [+0.7115, +0.8307] | 0.9202 |
| PEMS08 | F0p / intero | +0.9566 [+0.9360, +0.9708] | +0.7545 [+0.6751, +0.8126] | 0.9475 |
| PEMS08 | Fp_672 / > 1 sett. | +0.9646 [+0.9439, +0.9788] | +0.7749 [+0.6794, +0.8476] | 0.9544 |
| PEMS04 | C / intero | +0.9727 [+0.9649, +0.9795] | +0.8045 [+0.7571, +0.8456] | 0.9670 |
| PEMS04 | C / > 1 sett. | +0.9676 [+0.9544, +0.9773] | +0.7620 [+0.6737, +0.8227] | 0.9653 |
| PEMS04 | F0p / intero | +0.9738 [+0.9661, +0.9801] | +0.8107 [+0.7666, +0.8501] | 0.9693 |
| PEMS04 | Fp_672 / > 1 sett. | +0.9750 [+0.9634, +0.9833] | +0.8079 [+0.7265, +0.8641] | 0.9743 |

### 2b. Confronti (differenze, stessi indici): ΔAUC, ΔpAUC e Δrichiamo ai livelli di falsi allarmi

| gruppo | confronto | finestra | ΔAUC [IC] | ΔpAUC [IC] | Δrichiamo FA 0.5 % | Δrichiamo FA 1 % | Δrichiamo FA 2 % | Δrichiamo FA 5 % | Δrichiamo FA 10 % |
|---|---|---|---|---|---|---|---|---|---|
| Madrid | F0-C | intero | -0.0513 [-0.0600, -0.0426] - | -0.0366 [-0.0499, -0.0244] - | -0.5 [-0.8, -0.1] - | -1.1 [-1.6, -0.5] - | -1.9 [-2.7, -1.0] - | -3.9 [-5.5, -2.5] - | -6.2 [-8.1, -4.4] - |
| Madrid | F0p-F0 | intero | +0.0455 [+0.0377, +0.0535] + | +0.0310 [+0.0212, +0.0416] + | +0.4 [+0.2, +0.7] + | +0.9 [+0.5, +1.3] + | +1.5 [+0.9, +2.2] + | +3.3 [+2.1, +4.5] + | +5.4 [+3.9, +7.1] + |
| Madrid | F0p-C | intero | -0.0059 [-0.0081, -0.0037] - | -0.0056 [-0.0093, -0.0023] - | -0.1 [-0.2, +0.1] 0 | -0.2 [-0.4, +0.0] 0 | -0.3 [-0.6, -0.0] - | -0.6 [-1.1, -0.2] - | -0.8 [-1.2, -0.4] - |
| Madrid | A-C | intero | +0.0365 [+0.0308, +0.0430] + | +0.0252 [+0.0165, +0.0340] + | +0.3 [-0.1, +0.7] 0 | +0.6 [+0.0, +1.2] + | +1.3 [+0.5, +2.1] + | +2.6 [+1.6, +3.7] + | +4.4 [+3.2, +5.7] + |
| Madrid | Fp_672-C | > 1 sett. | +0.0325 [+0.0277, +0.0375] + | +0.0259 [+0.0175, +0.0338] + | +0.3 [-0.0, +0.6] 0 | +0.7 [+0.2, +1.1] + | +1.5 [+0.9, +2.0] + | +2.8 [+1.8, +3.9] + | +4.2 [+2.9, +5.5] + |
| Londra | F0-C | intero | -0.0182 [-0.0227, -0.0132] - | -0.0122 [-0.0174, -0.0069] - | -0.5 [-1.2, +0.0] 0 | -0.6 [-1.1, -0.1] - | -0.6 [-1.2, -0.2] - | -1.3 [-2.0, -0.7] - | -1.9 [-2.6, -1.2] - |
| Londra | F0p-F0 | intero | +0.0135 [+0.0094, +0.0173] + | +0.0079 [+0.0049, +0.0110] + | +0.3 [+0.0, +0.7] + | +0.3 [+0.1, +0.7] + | +0.4 [+0.1, +0.7] + | +0.8 [+0.5, +1.2] + | +1.2 [+0.8, +1.7] + |
| Londra | F0p-C | intero | -0.0047 [-0.0066, -0.0029] - | -0.0044 [-0.0067, -0.0018] - | -0.2 [-0.5, +0.1] 0 | -0.2 [-0.5, -0.0] - | -0.2 [-0.5, -0.0] - | -0.5 [-0.8, -0.1] - | -0.6 [-1.0, -0.3] - |
| Londra | A-C | intero | +0.0242 [+0.0201, +0.0289] + | +0.0182 [+0.0115, +0.0246] + | +0.7 [-0.0, +1.4] 0 | +0.9 [+0.3, +1.6] + | +1.3 [+0.5, +2.2] + | +1.9 [+1.1, +2.7] + | +2.7 [+1.9, +3.7] + |
| Londra | Fp_672-C | > 1 sett. | +0.0199 [+0.0159, +0.0239] + | +0.0115 [+0.0053, +0.0177] + | +0.7 [-0.1, +1.5] 0 | +0.9 [+0.0, +1.8] + | +1.0 [+0.1, +2.0] + | +1.1 [+0.3, +1.9] + | +1.8 [+1.0, +2.7] + |
| Melbourne | F0-C | intero | -0.0300 [-0.0383, -0.0197] - | -0.0363 [-0.0520, -0.0183] - | +0.9 [+0.2, +1.6] + | +0.1 [-0.8, +1.2] 0 | -1.5 [-2.9, -0.1] - | -4.5 [-6.5, -2.4] - | -5.7 [-7.8, -3.1] - |
| Melbourne | F0p-F0 | intero | +0.0308 [+0.0236, +0.0372] + | +0.0359 [+0.0237, +0.0469] + | -0.3 [-0.6, +0.1] 0 | +0.1 [-0.4, +0.6] 0 | +1.4 [+0.6, +2.3] + | +4.4 [+2.8, +5.9] + | +5.6 [+3.8, +7.2] + |
| Melbourne | F0p-C | intero | +0.0008 [-0.0024, +0.0049] 0 | -0.0005 [-0.0070, +0.0065] 0 | +0.6 [+0.2, +1.2] + | +0.3 [-0.3, +1.0] 0 | -0.1 [-0.8, +0.7] 0 | -0.1 [-0.9, +0.6] 0 | -0.1 [-0.8, +0.8] 0 |
| Melbourne | A-C | intero | +0.0172 [+0.0115, +0.0228] + | +0.0219 [+0.0082, +0.0348] + | -0.4 [-2.5, +1.5] 0 | +0.4 [-2.5, +2.3] 0 | +1.9 [-0.6, +3.5] 0 | +2.5 [+0.7, +4.4] + | +3.1 [+1.6, +4.5] + |
| Melbourne | Fp_672-C | > 1 sett. | +0.0184 [+0.0139, +0.0236] + | +0.0261 [+0.0178, +0.0346] + | +0.7 [-0.0, +1.5] 0 | +1.0 [+0.1, +1.9] + | +1.9 [+0.8, +2.8] + | +2.7 [+1.7, +4.0] + | +3.8 [+2.7, +4.8] + |
| PEMS08 | F0-C | intero | +0.0083 [-0.0004, +0.0194] 0 | +0.0537 [+0.0202, +0.1007] + | +7.1 [+1.4, +14.7] + | +8.0 [+2.9, +14.5] + | +7.1 [+2.9, +12.7] + | +5.3 [+1.3, +10.5] + | +3.4 [+0.2, +7.9] + |
| PEMS08 | F0p-F0 | intero | -0.0040 [-0.0092, +0.0000] 0 | -0.0241 [-0.0526, -0.0058] - | -1.5 [-5.8, +1.3] 0 | -2.5 [-6.5, +0.2] 0 | -2.9 [-6.3, -0.4] - | -2.7 [-5.8, -0.6] - | -1.9 [-4.3, -0.3] - |
| PEMS08 | F0p-C | intero | +0.0043 [-0.0023, +0.0119] 0 | +0.0296 [+0.0057, +0.0580] + | +5.6 [+1.6, +10.0] + | +5.5 [+2.0, +9.1] + | +4.2 [+1.3, +7.6] + | +2.6 [-0.2, +5.9] 0 | +1.5 [-0.9, +4.5] 0 |
| PEMS08 | A-C | intero | +0.0187 [+0.0072, +0.0332] + | +0.0857 [+0.0320, +0.1330] + | +14.0 [+7.3, +20.5] + | +14.3 [+7.6, +19.6] + | +12.1 [+5.6, +17.5] + | +7.9 [+1.8, +13.3] + | +4.6 [-0.0, +9.5] 0 |
| PEMS08 | Fp_672-C | > 1 sett. | +0.0115 [+0.0007, +0.0220] + | +0.0485 [+0.0027, +0.0858] + | +5.5 [-0.3, +11.2] 0 | +5.4 [-0.5, +10.8] 0 | +4.8 [-0.7, +10.0] 0 | +5.1 [+0.1, +9.1] + | +4.1 [+0.5, +7.5] + |
| PEMS04 | F0p-C | intero | +0.0010 [-0.0010, +0.0030] 0 | +0.0063 [-0.0067, +0.0203] 0 | +1.2 [-0.2, +3.0] 0 | +1.6 [-0.1, +3.5] 0 | +1.2 [-0.8, +3.5] 0 | +0.5 [-1.3, +2.3] 0 | +0.1 [-0.8, +1.0] 0 |
| PEMS04 | Fp_672-C | > 1 sett. | +0.0074 [+0.0041, +0.0115] + | +0.0459 [+0.0282, +0.0667] + | +2.8 [+0.9, +5.6] + | +4.5 [+2.1, +7.9] + | +6.3 [+3.5, +9.6] + | +5.1 [+2.8, +7.7] + | +3.0 [+1.3, +5.2] + |

### 2c. Affermazioni ri-valutate (sostituiscono quelle a 19 soglie; voce 28 del registro)

- **A1** ΔAUC(F₀ − C) < 0 nelle tre citta': Madrid sotto zero, Londra sotto zero, Melbourne sotto zero → **confermata**; PEMS08: include lo zero.
- **A2** ΔAUC(F₀′ − F₀) > 0 nelle tre citta' e su PEMS08: Madrid sopra zero, Londra sopra zero, Melbourne sopra zero, PEMS08 include lo zero → citta' **confermata**, PEMS08 **NON confermata**.
- **A3** F′(1 sett.) sopra C in richiamo ai cinque livelli di FA (origini > 1 settimana), segni per livello 0,5/1/2/5/10 %: Madrid 0++++; Londra 0++++; Melbourne 0++++; PEMS08 000++; PEMS04 +++++ → sopra zero a tutti e cinque i livelli in 1/5 contesti; per livello: 0.5 %: 1/5, 1 %: 4/5, 2 %: 4/5, 5 %: 5/5, 10 %: 5/5.
- **A4** richiamo perso da F₀ sotto argmax e quota recuperata a FA 5 %:

| gruppo | richiamo argmax C | richiamo argmax F₀ | perdita sotto argmax (punti) [IC] | perdita a FA 5 % (punti) [IC] | quota recuperata [IC] | testo attuale |
|---|---|---|---|---|---|---|
| Madrid | 65.9 | 18.3 | +47.6 [+43.4, +51.4] | +3.9 [+2.5, +5.5] | 0.918 [0.885, 0.947] | 92 % |
| Londra | 51.7 | 43.5 | +8.2 [+6.1, +10.3] | +1.3 [+0.7, +2.0] | 0.839 [0.733, 0.921] | 81 % |
| Melbourne | 66.3 | 43.5 | +22.9 [+17.7, +27.2] | +4.5 [+2.4, +6.5] | 0.802 [0.725, 0.882] | 80 % |
| PEMS08 | 67.0 | 48.3 | +18.8 [+11.1, +26.6] | -5.3 [-10.5, -1.3] | 1.282 [1.062, 1.781] | — |

Le soglie scelte su validazione (−7,9 / −0,8 / −0,7 punti) restano dalla campagna originaria (E8) e il testo le separa da queste.
- **A5** ΔpAUC(0–10 %): colonna «ΔpAUC» della tabella 2b, descrittiva.

## 3. Parte B — bootstrap che conserva il sensore fisico

passo sui sensori: K_d identificatori fisici estratti con reimmissione fra i distinti delle partizioni del contesto; ogni partizione pesa i propri sensori di prova con la molteplicita' del loro ID; pesi condivisi fra bracci, partizioni e semi della replica; partizioni e semi ricampionati come oggi. 4000 repliche, seme 20261128. Categorie: superiorita' (limite superiore < 0), non inferiorita' (limite superiore < δ = 0.005), inferiorita' (limite inferiore > 0), inconclusivo. Gli intervalli attuali restano quelli pre-registrati e primari; quelli per sensore sono una sensibilita'.

Mappa posizione → ID fisico (`D["sid"][nodi]`): verificata su Madrid p0 contro `_partizioni(SEME_PARTIZIONE[p])`: nodi uguali = True; 900 ID distinti su 900 sensori del contesto.

| contesto | sensori distinti / occorrenze | differenza | media | IC attuale (congelato) | categoria | IC attuale ricalcolato (stesse estrazioni) | IC per sensore | categoria per sensore | esito |
|---|---|---|---|---|---|---|---|---|---|
| Madrid/ep1 | 348 / 405 | (a) F0p-C | +0.0079 | +0.0079 [+0.0053, +0.0107] | inferiorita' | [+0.0054, +0.0108] | [+0.0052, +0.0110] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0287 | -0.0287 [-0.0372, -0.0210] | superiorita' | [-0.0372, -0.0208] | [-0.0373, -0.0204] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0308 | -0.0308 [-0.0363, -0.0256] | superiorita' | [-0.0365, -0.0257] | [-0.0364, -0.0257] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0112 | -0.0112 [-0.0206, -0.0018] | superiorita' | [-0.0205, -0.0020] | [-0.0206, -0.0019] | superiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0077 | +0.0077 [+0.0042, +0.0116] | inferiorita' | [+0.0040, +0.0115] | [+0.0040, +0.0116] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0238 | -0.0238 [-0.0280, -0.0199] | superiorita' | [-0.0281, -0.0198] | [-0.0282, -0.0197] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | +0.0049 | +0.0049 [+0.0003, +0.0098] | inferiorita' | [+0.0003, +0.0098] | [+0.0000, +0.0098] | inferiorita' | invariata |
| Madrid/ep2 | 348 / 405 | (a) F0p-C | +0.0041 | +0.0041 [+0.0016, +0.0067] | inferiorita' | [+0.0015, +0.0067] | [+0.0014, +0.0068] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0267 | -0.0267 [-0.0353, -0.0189] | superiorita' | [-0.0355, -0.0186] | [-0.0354, -0.0185] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0353 | -0.0353 [-0.0424, -0.0295] | superiorita' | [-0.0424, -0.0295] | [-0.0424, -0.0295] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0119 | -0.0119 [-0.0204, -0.0038] | superiorita' | [-0.0204, -0.0038] | [-0.0207, -0.0035] | superiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0045 | +0.0045 [+0.0014, +0.0076] | inferiorita' | [+0.0014, +0.0075] | [+0.0012, +0.0074] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0242 | -0.0242 [-0.0291, -0.0200] | superiorita' | [-0.0291, -0.0199] | [-0.0293, -0.0198] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | +0.0025 | +0.0025 [-0.0019, +0.0069] | inconclusivo | [-0.0020, +0.0068] | [-0.0021, +0.0068] | inconclusivo | invariata |
| Madrid/ep3 | 348 / 405 | (a) F0p-C | +0.0022 | +0.0022 [-0.0005, +0.0049] | non inferiorita' | [-0.0004, +0.0048] | [-0.0005, +0.0048] | non inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0076 | -0.0076 [-0.0177, +0.0027] | non inferiorita' | [-0.0172, +0.0024] | [-0.0175, +0.0030] | non inferiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0356 | -0.0356 [-0.0433, -0.0291] | superiorita' | [-0.0434, -0.0289] | [-0.0437, -0.0291] | superiorita' | invariata |
|  |  | (d) Fp_96-C | +0.0105 | +0.0105 [-0.0040, +0.0264] | inconclusivo | [-0.0037, +0.0258] | [-0.0045, +0.0274] | inconclusivo | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0030 | +0.0030 [+0.0001, +0.0061] | inferiorita' | [+0.0000, +0.0060] | [-0.0002, +0.0062] | inconclusivo | **cambia** |
|  |  | E17 gated(1sett,0)-F0p | -0.0237 | -0.0237 [-0.0289, -0.0189] | superiorita' | [-0.0289, -0.0192] | [-0.0290, -0.0191] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0162 | -0.0162 [-0.0255, -0.0084] | superiorita' | [-0.0253, -0.0083] | [-0.0258, -0.0081] | superiorita' | invariata |
| Londra/ep1 | 348 / 405 | (a) F0p-C | +0.0145 | +0.0145 [+0.0103, +0.0191] | inferiorita' | [+0.0104, +0.0190] | [+0.0105, +0.0191] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0106 | -0.0106 [-0.0175, -0.0043] | superiorita' | [-0.0174, -0.0043] | [-0.0174, -0.0040] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0306 | -0.0306 [-0.0351, -0.0264] | superiorita' | [-0.0349, -0.0263] | [-0.0354, -0.0262] | superiorita' | invariata |
|  |  | (d) Fp_96-C | +0.0317 | +0.0317 [+0.0211, +0.0428] | inferiorita' | [+0.0212, +0.0427] | [+0.0213, +0.0434] | inferiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0085 | +0.0085 [+0.0056, +0.0119] | inferiorita' | [+0.0055, +0.0117] | [+0.0053, +0.0117] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0289 | -0.0289 [-0.0339, -0.0241] | superiorita' | [-0.0337, -0.0242] | [-0.0339, -0.0240] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0183 | -0.0183 [-0.0236, -0.0132] | superiorita' | [-0.0237, -0.0131] | [-0.0238, -0.0131] | superiorita' | invariata |
| Londra/ep2 | 348 / 405 | (a) F0p-C | +0.0098 | +0.0098 [+0.0056, +0.0149] | inferiorita' | [+0.0056, +0.0149] | [+0.0056, +0.0149] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0178 | -0.0178 [-0.0240, -0.0127] | superiorita' | [-0.0241, -0.0123] | [-0.0244, -0.0122] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0243 | -0.0243 [-0.0290, -0.0196] | superiorita' | [-0.0291, -0.0197] | [-0.0294, -0.0192] | superiorita' | invariata |
|  |  | (d) Fp_96-C | +0.0055 | +0.0055 [-0.0035, +0.0147] | inconclusivo | [-0.0036, +0.0147] | [-0.0037, +0.0152] | inconclusivo | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0090 | +0.0090 [+0.0054, +0.0128] | inferiorita' | [+0.0055, +0.0127] | [+0.0054, +0.0128] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0204 | -0.0204 [-0.0253, -0.0160] | superiorita' | [-0.0250, -0.0161] | [-0.0254, -0.0159] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0026 | -0.0026 [-0.0064, +0.0011] | non inferiorita' | [-0.0062, +0.0010] | [-0.0065, +0.0011] | non inferiorita' | invariata |
| Londra/ep3 | 348 / 405 | (a) F0p-C | +0.0105 | +0.0105 [+0.0075, +0.0140] | inferiorita' | [+0.0075, +0.0140] | [+0.0074, +0.0140] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0236 | -0.0236 [-0.0316, -0.0158] | superiorita' | [-0.0312, -0.0156] | [-0.0316, -0.0158] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0304 | -0.0304 [-0.0349, -0.0259] | superiorita' | [-0.0348, -0.0257] | [-0.0352, -0.0257] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0069 | -0.0069 [-0.0138, +0.0006] | non inferiorita' | [-0.0140, +0.0010] | [-0.0144, +0.0007] | non inferiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0084 | +0.0084 [+0.0044, +0.0121] | inferiorita' | [+0.0044, +0.0123] | [+0.0044, +0.0122] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0251 | -0.0251 [-0.0291, -0.0214] | superiorita' | [-0.0291, -0.0212] | [-0.0294, -0.0210] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0016 | -0.0016 [-0.0070, +0.0033] | non inferiorita' | [-0.0071, +0.0032] | [-0.0071, +0.0034] | non inferiorita' | invariata |
| Melbourne/ep1 | 232 / 270 | (a) F0p-C | +0.0024 | +0.0024 [-0.0040, +0.0084] | inconclusivo | [-0.0038, +0.0082] | [-0.0039, +0.0085] | inconclusivo | invariata |
|  |  | (b) gated-F0p | -0.0239 | -0.0239 [-0.0280, -0.0201] | superiorita' | [-0.0280, -0.0203] | [-0.0282, -0.0201] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0360 | -0.0360 [-0.0436, -0.0295] | superiorita' | [-0.0433, -0.0292] | [-0.0437, -0.0291] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0195 | -0.0195 [-0.0287, -0.0101] | superiorita' | [-0.0291, -0.0100] | [-0.0287, -0.0098] | superiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | -0.0019 | -0.0019 [-0.0120, +0.0069] | inconclusivo | [-0.0121, +0.0072] | [-0.0126, +0.0072] | inconclusivo | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0239 | -0.0239 [-0.0279, -0.0201] | superiorita' | [-0.0280, -0.0203] | [-0.0282, -0.0201] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | +0.0000 | +0.0000 [+0.0000, +0.0000] | non inferiorita' | [+0.0000, +0.0000] | [+0.0000, +0.0000] | non inferiorita' | invariata |
| Melbourne/ep2 | 232 / 270 | (a) F0p-C | +0.0062 | +0.0062 [+0.0012, +0.0107] | inferiorita' | [+0.0012, +0.0109] | [+0.0011, +0.0110] | inferiorita' | invariata |
|  |  | (b) gated-F0p | +0.0005 | +0.0005 [-0.0030, +0.0039] | non inferiorita' | [-0.0030, +0.0039] | [-0.0033, +0.0042] | non inferiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0254 | -0.0254 [-0.0325, -0.0179] | superiorita' | [-0.0330, -0.0180] | [-0.0333, -0.0174] | superiorita' | invariata |
|  |  | (d) Fp_96-C | +0.0227 | +0.0227 [+0.0079, +0.0386] | inferiorita' | [+0.0080, +0.0386] | [+0.0076, +0.0397] | inferiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0101 | +0.0101 [+0.0006, +0.0196] | inferiorita' | [+0.0004, +0.0198] | [+0.0004, +0.0201] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0177 | -0.0177 [-0.0250, -0.0104] | superiorita' | [-0.0250, -0.0107] | [-0.0251, -0.0101] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0183 | -0.0183 [-0.0241, -0.0129] | superiorita' | [-0.0244, -0.0128] | [-0.0243, -0.0125] | superiorita' | invariata |
| Melbourne/ep3 | 232 / 270 | (a) F0p-C | +0.0163 | +0.0163 [+0.0126, +0.0200] | inferiorita' | [+0.0128, +0.0200] | [+0.0127, +0.0200] | inferiorita' | invariata |
|  |  | (b) gated-F0p | -0.0334 | -0.0334 [-0.0388, -0.0285] | superiorita' | [-0.0385, -0.0286] | [-0.0388, -0.0283] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0383 | -0.0383 [-0.0447, -0.0326] | superiorita' | [-0.0448, -0.0326] | [-0.0451, -0.0325] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0216 | -0.0216 [-0.0294, -0.0131] | superiorita' | [-0.0296, -0.0137] | [-0.0296, -0.0132] | superiorita' | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0154 | +0.0154 [+0.0100, +0.0213] | inferiorita' | [+0.0101, +0.0216] | [+0.0101, +0.0214] | inferiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0334 | -0.0334 [-0.0385, -0.0289] | superiorita' | [-0.0385, -0.0287] | [-0.0388, -0.0284] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | -0.0001 | -0.0001 [-0.0002, +0.0000] | non inferiorita' | [-0.0002, +0.0000] | [-0.0002, +0.0000] | non inferiorita' | invariata |
| PEMS08 | 117 / 156 | (a) F0p-C | -0.0394 | -0.0394 [-0.0760, -0.0037] | superiorita' | [-0.0749, -0.0038] | [-0.0793, -0.0023] | superiorita' | invariata |
|  |  | (b) gated-F0p | -0.0344 | -0.0344 [-0.0712, +0.0091] | inconclusivo | [-0.0714, +0.0085] | [-0.0764, +0.0174] | inconclusivo | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0908 | -0.0908 [-0.1315, -0.0420] | superiorita' | [-0.1316, -0.0421] | [-0.1390, -0.0328] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0738 | -0.0738 [-0.1181, -0.0225] | superiorita' | [-0.1193, -0.0243] | [-0.1258, -0.0189] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0361 | -0.0361 [-0.0615, -0.0029] | superiorita' | [-0.0608, -0.0001] | [-0.0670, +0.0108] | inconclusivo | **cambia** |
|  |  | E17 gated(1sett,0)-gated | -0.0017 | -0.0017 [-0.0333, +0.0220] | inconclusivo | [-0.0324, +0.0225] | [-0.0327, +0.0215] | inconclusivo | invariata |
|  |  | (e) Fp_672-A >1sett | +0.0396 | +0.0396 [-0.0193, +0.0890] | inconclusivo | [-0.0172, +0.0899] | [-0.0181, +0.0932] | inconclusivo | invariata |
|  |  | E17 Rorig_672-Fp_672 >1sett | +0.0098 | +0.0098 [-0.0396, +0.0792] | inconclusivo | [-0.0403, +0.0762] | [-0.0478, +0.0998] | inconclusivo | invariata |
| PEMS04 | 123 / 141 | (a) F0p-C | +0.0026 | +0.0026 [-0.0071, +0.0129] | inconclusivo | [-0.0070, +0.0126] | [-0.0069, +0.0123] | inconclusivo | invariata |
|  |  | (b) gated-F0p | -0.0219 | -0.0219 [-0.0305, -0.0133] | superiorita' | [-0.0309, -0.0138] | [-0.0309, -0.0130] | superiorita' | invariata |
|  |  | (c) Fp_672-C >1sett | -0.0330 | -0.0330 [-0.0467, -0.0187] | superiorita' | [-0.0469, -0.0187] | [-0.0468, -0.0192] | superiorita' | invariata |
|  |  | (d) Fp_96-C | -0.0225 | -0.0225 [-0.0341, -0.0096] | superiorita' | [-0.0337, -0.0099] | [-0.0335, -0.0099] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-F0p | -0.0101 | -0.0101 [-0.0131, -0.0075] | superiorita' | [-0.0131, -0.0075] | [-0.0132, -0.0071] | superiorita' | invariata |
|  |  | E17 gated(1sett,0)-gated | +0.0118 | +0.0118 [+0.0049, +0.0187] | inferiorita' | [+0.0052, +0.0184] | [+0.0047, +0.0188] | inferiorita' | invariata |
| E15 Madrid | 348 / 405 | F0-C | +0.0746 | +0.0746 [+0.0594, +0.0903] | inferiorita' | [+0.0600, +0.0912] | [+0.0594, +0.0911] | inferiorita' | invariata |
|  |  | F0p-C | +0.0078 | +0.0078 [+0.0053, +0.0106] | inferiorita' | [+0.0054, +0.0105] | [+0.0052, +0.0106] | inferiorita' | invariata |
|  |  | Fp_672-C >1sett | -0.0311 | -0.0311 [-0.0368, -0.0256] | superiorita' | [-0.0371, -0.0258] | [-0.0368, -0.0257] | superiorita' | invariata |
|  |  | Fp_672-A >1sett | +0.0080 | +0.0080 [+0.0042, +0.0120] | inferiorita' | [+0.0041, +0.0120] | [+0.0042, +0.0121] | inferiorita' | invariata |
|  |  | A-C | -0.0401 | -0.0401 [-0.0453, -0.0353] | superiorita' | [-0.0451, -0.0352] | [-0.0452, -0.0352] | superiorita' | invariata |
|  |  | A-C_A | -0.0382 | -0.0382 [-0.0431, -0.0335] | superiorita' | [-0.0430, -0.0335] | [-0.0431, -0.0334] | superiorita' | invariata |
|  |  | C_A-C | -0.0019 | -0.0019 [-0.0029, -0.0010] | superiorita' | [-0.0029, -0.0011] | [-0.0030, -0.0010] | superiorita' | invariata |
|  |  | Fpk_672-C >1sett | -0.0336 | -0.0336 [-0.0391, -0.0284] | superiorita' | [-0.0392, -0.0287] | [-0.0389, -0.0285] | superiorita' | invariata |
|  |  | Fpk_672-A >1sett | +0.0055 | +0.0055 [+0.0024, +0.0086] | inferiorita' | [+0.0023, +0.0087] | [+0.0023, +0.0087] | inferiorita' | invariata |
| E15 Londra | 348 / 405 | F0-C | +0.0486 | +0.0486 [+0.0363, +0.0622] | inferiorita' | [+0.0369, +0.0619] | [+0.0363, +0.0628] | inferiorita' | invariata |
|  |  | F0p-C | +0.0138 | +0.0138 [+0.0096, +0.0181] | inferiorita' | [+0.0099, +0.0182] | [+0.0097, +0.0184] | inferiorita' | invariata |
|  |  | Fp_672-C >1sett | -0.0309 | -0.0309 [-0.0353, -0.0265] | superiorita' | [-0.0353, -0.0265] | [-0.0356, -0.0263] | superiorita' | invariata |
|  |  | Fp_672-A >1sett | +0.0084 | +0.0084 [+0.0054, +0.0117] | inferiorita' | [+0.0055, +0.0116] | [+0.0053, +0.0117] | inferiorita' | invariata |
|  |  | A-C | -0.0344 | -0.0344 [-0.0390, -0.0299] | superiorita' | [-0.0390, -0.0300] | [-0.0392, -0.0296] | superiorita' | invariata |
|  |  | A-C_A | -0.0332 | -0.0332 [-0.0374, -0.0290] | superiorita' | [-0.0374, -0.0290] | [-0.0378, -0.0288] | superiorita' | invariata |
|  |  | C_A-C | -0.0012 | -0.0012 [-0.0026, -0.0001] | superiorita' | [-0.0025, -0.0001] | [-0.0025, -0.0001] | superiorita' | invariata |
|  |  | Fpk_672-C >1sett | -0.0309 | -0.0309 [-0.0353, -0.0265] | superiorita' | [-0.0353, -0.0265] | [-0.0356, -0.0263] | superiorita' | invariata |
|  |  | Fpk_672-A >1sett | +0.0084 | +0.0084 [+0.0054, +0.0117] | inferiorita' | [+0.0055, +0.0116] | [+0.0053, +0.0117] | inferiorita' | invariata |
| E15 Melbourne | 232 / 270 | F0-C | +0.0781 | +0.0781 [+0.0515, +0.1035] | inferiorita' | [+0.0518, +0.1029] | [+0.0516, +0.1051] | inferiorita' | invariata |
|  |  | F0p-C | +0.0002 | +0.0002 [-0.0064, +0.0066] | inconclusivo | [-0.0063, +0.0062] | [-0.0068, +0.0067] | inconclusivo | invariata |
|  |  | Fp_672-C >1sett | -0.0400 | -0.0400 [-0.0481, -0.0325] | superiorita' | [-0.0483, -0.0322] | [-0.0489, -0.0320] | superiorita' | invariata |
|  |  | Fp_672-A >1sett | -0.0017 | -0.0017 [-0.0116, +0.0076] | inconclusivo | [-0.0114, +0.0075] | [-0.0121, +0.0077] | inconclusivo | invariata |
|  |  | A-C | -0.0450 | -0.0450 [-0.0566, -0.0330] | superiorita' | [-0.0562, -0.0330] | [-0.0571, -0.0321] | superiorita' | invariata |
|  |  | A-C_A | -0.0367 | -0.0367 [-0.0467, -0.0256] | superiorita' | [-0.0464, -0.0257] | [-0.0470, -0.0248] | superiorita' | invariata |
|  |  | C_A-C | -0.0084 | -0.0084 [-0.0124, -0.0052] | superiorita' | [-0.0126, -0.0052] | [-0.0125, -0.0052] | superiorita' | invariata |
|  |  | Fpk_672-C >1sett | -0.0400 | -0.0400 [-0.0481, -0.0325] | superiorita' | [-0.0483, -0.0322] | [-0.0489, -0.0320] | superiorita' | invariata |
|  |  | Fpk_672-A >1sett | -0.0017 | -0.0017 [-0.0116, +0.0076] | inconclusivo | [-0.0114, +0.0075] | [-0.0121, +0.0077] | inconclusivo | invariata |
| E3-bis Madrid | 348 / 405 | Rorig_672-Fp_672 >1sett | -0.0033 | -0.0033 [-0.0059, -0.0010] | superiorita' | [-0.0060, -0.0010] | [-0.0061, -0.0011] | superiorita' | invariata |
| E3-bis Londra | 348 / 405 | Rorig_672-Fp_672 >1sett | -0.0025 | -0.0025 [-0.0049, +0.0003] | non inferiorita' | [-0.0048, +0.0003] | [-0.0049, +0.0006] | non inferiorita' | invariata |
| E3-bis Melbourne | 232 / 270 | Rorig_672-Fp_672 >1sett | -0.0134 | -0.0134 [-0.0199, -0.0069] | superiorita' | [-0.0197, -0.0067] | [-0.0204, -0.0067] | superiorita' | invariata |

**Cambi di categoria** (attuale → per sensore): 2.
- Madrid/ep3, (e) Fp_672-A >1sett: inferiorita' → inconclusivo (attuale [+0.0001, +0.0061], per sensore [-0.0002, +0.0062]).
- PEMS08, E17 gated(1sett,0)-F0p: superiorita' → inconclusivo (attuale [-0.0615, -0.0029], per sensore [-0.0670, +0.0108]).

Casi nominati dal protocollo (se cambiano, la frase passa a «inconclusive under sensor-level resampling»):
- non inferiorita' di gated(τ,N) − F₀′, Madrid ep. 3: attuale non inferiorita' → per sensore non inferiorita' ([-0.0175, +0.0030]).
- non inferiorita' di gated(τ,N) − F₀′, Melbourne ep. 2: attuale non inferiorita' → per sensore non inferiorita' ([-0.0033, +0.0042]).
- superiorita' di gated(1 sett., 0) − F₀′, PEMS08: attuale superiorita' → per sensore inconclusivo ([-0.0670, +0.0108]).

Margini minimi di equivalenza (R-orig(1 sett.) ≡ F′(1 sett.)), max(|lo|, |hi|) dell'intervallo al 95 %:

| contesto | attuale (E17) | per sensore |
|---|---|---|
| E3-bis Madrid | 0.0059 | 0.0061 |
| E3-bis Londra | 0.0049 | 0.0049 |
| E3-bis Melbourne | 0.0199 | 0.0204 |
| PEMS08 | 0.0792 | 0.0998 |

## 4. Parte D — provenienza della politica gated(1 sett., 0) (documentaria)

tabella per gli undici contesti: campagna, gated(1 sett., 0) - F0', gated(1 sett., 0) - gated(tau, N), intervalli attuali (E17) e per sensore (B), data della prima osservazione dei risultati del contesto (git log dei CONGELAMENTO_*), data della prima formulazione scritta della politica (protocollo e manoscritto, git log -S).

Prima formulazione scritta della politica: **2026-10-22** — protocol/E17.md «gated(1 sett., 0)»: 2026-10-22 (e5ae222); «waiting a week»: 2026-10-22 (5fb9b2d).

| contesto | campagna | gated(1 sett., 0) − F₀′ [IC attuale] | categoria | IC per sensore | categoria | gated(1 sett., 0) − gated(τ,N) [IC attuale] | categoria | prima osservazione dei risultati (file, commit) | osservato prima della formulazione |
|---|---|---|---|---|---|---|---|---|---|
| Madrid/ep1 | E4/E2 (campagna principale) | -0.0238 [-0.0280, -0.0199] | superiorita' | [-0.0282, -0.0197] | superiorita' | +0.0049 [+0.0003, +0.0098] | inferiorita' | 2026-09-23 (CONGELAMENTO_E_F_GRIGLIA.md, 1f5da08) | sì |
| Madrid/ep2 | E5 | -0.0242 [-0.0291, -0.0200] | superiorita' | [-0.0293, -0.0198] | superiorita' | +0.0025 [-0.0019, +0.0069] | inconclusivo | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| Madrid/ep3 | E5 | -0.0237 [-0.0289, -0.0189] | superiorita' | [-0.0290, -0.0191] | superiorita' | -0.0162 [-0.0255, -0.0084] | superiorita' | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| Londra/ep1 | E4/E2 (campagna principale) | -0.0289 [-0.0339, -0.0241] | superiorita' | [-0.0339, -0.0240] | superiorita' | -0.0183 [-0.0236, -0.0132] | superiorita' | 2026-09-23 (CONGELAMENTO_E_F_GRIGLIA.md, 1f5da08) | sì |
| Londra/ep2 | E5 | -0.0204 [-0.0253, -0.0160] | superiorita' | [-0.0254, -0.0159] | superiorita' | -0.0026 [-0.0064, +0.0011] | non inferiorita' | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| Londra/ep3 | E5 | -0.0251 [-0.0291, -0.0214] | superiorita' | [-0.0294, -0.0210] | superiorita' | -0.0016 [-0.0070, +0.0033] | non inferiorita' | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| Melbourne/ep1 | E4/E2 (campagna principale) | -0.0239 [-0.0279, -0.0201] | superiorita' | [-0.0282, -0.0201] | superiorita' | +0.0000 [+0.0000, +0.0000] | non inferiorita' | 2026-09-23 (CONGELAMENTO_E_F_GRIGLIA.md, 1f5da08) | sì |
| Melbourne/ep2 | E5 | -0.0177 [-0.0250, -0.0104] | superiorita' | [-0.0251, -0.0101] | superiorita' | -0.0183 [-0.0241, -0.0129] | superiorita' | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| Melbourne/ep3 | E5 | -0.0334 [-0.0385, -0.0289] | superiorita' | [-0.0388, -0.0284] | superiorita' | -0.0001 [-0.0002, +0.0000] | non inferiorita' | 2026-10-06 (CONGELAMENTO_E5.md, 6b72236) | sì |
| PEMS08 | E6 | -0.0361 [-0.0615, -0.0029] | superiorita' | [-0.0670, +0.0108] | inconclusivo | -0.0017 [-0.0333, +0.0220] | inconclusivo | 2026-10-08 (CONGELAMENTO_E6.md, 83e9a85) | sì |
| PEMS04 | E6-bis (parte A) | -0.0101 [-0.0131, -0.0075] | superiorita' | [-0.0132, -0.0071] | superiorita' | +0.0118 [+0.0049, +0.0187] | inferiorita' | 2026-10-08 (CONGELAMENTO_E6.md, 83e9a85) | sì |

Esito: 11 contesti su 11 osservati prima della prima formulazione scritta (2026-10-22); atteso: nessun contesto osservato dopo la formulazione -> valutazione post hoc descrittiva. **tutti gli undici contesti erano gia' stati osservati quando la politica e' stata scritta: valutazione post hoc descrittiva, senza conferma prospettica**. Il paper riporta la politica come valutazione post hoc descrittiva sugli undici contesti, senza «not used to formulate it» e senza conferma prospettica.

## 5. TOST (punto 6) — nessun calcolo

I margini minimi usano gli estremi dell'intervallo al 95 % (`analizza_e17.py` r. 72 e 167): equivalgono a un TOST a α = 0,025 per lato, piu' conservativo del convenzionale (α = 0,05, 90 %). Si dichiara cosi' nel testo; non si cambia percentile. δ = 0,005 e' stato fissato in E17 quando i limiti superiori ≈ 0,003 e 0,004 erano noti: le due non inferiorita' sono analisi secondaria post hoc e non entrano nella sintesi confirmatory (superiorita' in 8 contesti su 11).

## 6. Deviazioni (con data e motivo)

- 28/10/2026, parte C: due celle di `predizioni_e16` (prova Madrid p1 s203, Melbourne p2 s212) avevano, sulla finestra > 1 settimana, scarto relativo 1,36e-6 e 1,56e-6 rispetto all'aggregato congelato (soglia 1e-6): rumore fra macchine (voce 22; le probabilita' erano state ricostruite sulla Spark, gli aggregati sul Mac). Rimedio gia' usato in E16: le due celle sono state ricostruite sul Mac con `esegui_e16.py --solo` (controllo interno di E16 a 1,1e-14 e 9,6e-16) e copiate sulla Spark; gli originali sono in `predizioni_e16_spark_sostituite/`. Tolleranza invariata.
- 28/10/2026, A.6: PEMS04 ha solo C, F₀′ e F′(1 sett.) (nessun E ne' A): A1, A2, A4 not defined (no E, no A); A3 and F₀′ − C only — come da A.6, non e' una deviazione. La validazione di PEMS04 non viene ricostruita (non serve ad A).
- 29/10/2026, parte B: per i contesti di PEMS04 i confronti con A ed R-orig non esistono (nessun A, nessun R-orig in E6-bis parte A); per le citta' R-orig(1 sett.) − F′(1 sett.) usa `predizioni_fase3_672` (R-orig per nodo sulle origini comuni) e la fascia > 1 settimana di `predizioni_e4`, come E3-bis.

## 7. Impronte

- `results/evoluzione/e18_risultati.json` `7a77b98705da6861`; `protocol/E18.md` `42da14831a4e982c`; `results/evoluzione/congelamento_e18.json` `3e1409e19e7317e7`.
- Ingressi per parte (impronte dei file elencate in `e18_risultati.json` → `impronte_ingressi`): C: 2 file, insieme `9bfd450be26b80fc`; A: 180 file, insieme `1ebcd16ef54185b6`; B: 9 file, insieme `30cd1c11c5c7e48d`; D: 0 file, insieme `e3b0c44298fc1c14`.
- `evoluzione/analisi/analizza_e18.py` `eec942ac326118ae`.
