# Paper 1 — confronto fra numeri rigenerati e congelati

Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni per cella con il codice del repository e confrontato con il file congelato omonimo. Valori a 12 cifre significative; scarto = rigenerato − congelato.

- esito: **DIFFERENZE O ERRORI**
- esperimenti: ARCH, E2, E3, E4, E3bis, E5, E6, E7, E8
- tolleranza: relativa 1e-09, assoluta 1e-12
- risultati reali dopo l'esecuzione: invariati
- non coperto (ingressi, non rigenerati): addestramenti e valutazioni dei modelli sulle celle, adattamenti di E2, k della secondaria di E5, sensibilita' a rho, costi misurati (manifesti isolati), numeri del resoconto della campagna principale, dati di disegno (sensori, partizioni, semi)

## 1. Tabelle del Paper 1

| tabella | voce | stampato | congelato | rigenerato | scarto | esito |
|---|---|---|---:|---:|---:|---|
| I | origini > 1 sett., Mad. | 869 | 869 | 869 | 0 | ok |
| I | origini > 1 sett., Lon. | 883 | 883 | 883 | 0 | ok |
| I | origini > 1 sett., Mel. | 854 | 854 | 854 | 0 | ok |
| I | origini > 1 sett., PEMS04 | 168 | 168 | 168 | 0 | ok |
| I | origini > 1 sett., PEMS08 | 1423 | 1423 | 1423 | 0 | ok |
| I, II | A - C, Madrid | -0.039 | -0.0390870914489 | -0.0390870914489 | 0 | ok |
| I, II | A - C, Londra | -0.035 | -0.0347222837387 | -0.0347222837387 | 0 | ok |
| I, II | A - C, Melbourne | -0.038 | -0.03835925723 | -0.03835925723 | 0 | ok |
| I, II | A - C, PEMS08 | -0.133 | -0.132525592 | -0.132525592 | 0 | ok |
| II | F0-C, Madrid | +0.073 | 0.0731832385361 | 0.0731832385361 | 0 | ok |
| II | F0-C, Londra | +0.050 | 0.0497320474341 | 0.0497320474341 | 0 | ok |
| II | F0-C, Melbourne | +0.078 | 0.0783218637074 | 0.0783218637074 | 0 | ok |
| II | F0-C, PEMS08 | +0.156 | 0.156490961717 | 0.156490961717 | 0 | ok |
| II | F0p-C, Madrid | +0.008 | 0.00814709569878 | 0.00814709569878 | 0 | ok |
| II | F0p-C, Londra | +0.013 | 0.0128755236073 | 0.0128755236073 | 0 | ok |
| II | F0p-C, Melbourne | +0.001 | 0.00148874796433 | 0.00148874796433 | 0 | ok |
| II | F0p-C, PEMS08 | -0.039 | -0.0394311960087 | -0.0394311960087 | 0 | ok |
| II | F'(24 h) - C, Madrid | -0.011 | -0.0113417063787 | -0.0113417063787 | 0 | ok |
| II | F'(24 h) - C, Londra | +0.034 | 0.0336059154614 | 0.0336059154614 | 0 | ok |
| II | F'(24 h) - C, Melbourne | -0.019 | -0.0192303273445 | -0.0192303273445 | 0 | ok |
| II | F'(1 wk) - C, Madrid | -0.032 | -0.0316287150003 | -0.0316287150003 | 0 | ok |
| II | F'(1 wk) - C, Londra | -0.030 | -0.0301793508553 | -0.0301793508553 | 0 | ok |
| II | F'(1 wk) - C, Melbourne | -0.036 | -0.0364075559391 | -0.0364075559391 | 0 | ok |
| II, III | F'(1 wk) - C, PEMS08 | -0.091 | -0.0908492906919 | -0.0908492906919 | 0 | ok |
| II | gated - F0', massimo sui nove episodi | <= +0.004 | 0.000531946038111 | 0.000531946038111 | 0 | ok |
| II tempi | Fp_96_s, Mad. | 14.0 | 14.0453300476 | 14.0453300476 | 0 | ok (ingresso) |
| II tempi | Fp_672_s, Mad. | 151 | 151.386086941 | 151.386086941 | 0 | ok (ingresso) |
| II tempi | R-orig_672_s, Mad. | 2272 | 2272.27956581 | 2272.27956581 | 0 | ok (ingresso) |
| II tempi | rapporto_Rorig_su_Fp_672, Mad. | 15.0 | 15.0098309014 | 15.0098309014 | 0 | ok (ingresso) |
| II tempi | Fp_96_s, Lon. | 14.0 | 13.9728770256 | 13.9728770256 | 0 | ok (ingresso) |
| II tempi | Fp_672_s, Lon. | 144 | 143.675832033 | 143.675832033 | 0 | ok (ingresso) |
| II tempi | R-orig_672_s, Lon. | 2270 | 2270.17524815 | 2270.17524815 | 0 | ok (ingresso) |
| II tempi | rapporto_Rorig_su_Fp_672, Lon. | 15.8 | 15.800675841 | 15.800675841 | 0 | ok (ingresso) |
| II tempi | Fp_96_s, Mel. | 38.0 | 37.9512679577 | 37.9512679577 | 0 | ok (ingresso) |
| II tempi | Fp_672_s, Mel. | 404 | 404.375754833 | 404.375754833 | 0 | ok (ingresso) |
| II tempi | R-orig_672_s, Mel. | 1489 | 1488.96792912 | 1488.96792912 | 0 | ok (ingresso) |
| II tempi | rapporto_Rorig_su_Fp_672, Mel. | 3.7 | 3.68213947381 | 3.68213947381 | 0 | ok (ingresso) |
| II tempi | Fp_96_s, PEMS08 | 13.8 | 13.8225059509 | 13.8225059509 | 0 | ok (ingresso) |
| II tempi | Fp_672_s, PEMS08 | 124 | 124.487620115 | 124.487620115 | 0 | ok (ingresso) |
| II tempi | R-orig_672_s, PEMS08 | 413 | 413.33783412 | 413.33783412 | 0 | ok (ingresso) |
| II tempi | rapporto_Rorig_su_Fp_672, PEMS08 | 3.3 | 3.32031276473 | 3.32031276473 | 0 | ok (ingresso) |
| II tempi | F'(48 h) = gated(48 h), Madrid | 36.8 | 36.7518091202 | 36.7518091202 | 0 | ok (ingresso) |
| II tempi | F'(48 h) = gated(48 h), Londra | 35.7 | 35.7145662308 | 35.7145662308 | 0 | ok (ingresso) |
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
| §III | dilatazioni | 1, 2, 4, 8 | [1, 2, 4, 8] | [1, 2, 4, 8] | = | ok |
| III | (a) Mad. | ++0 | ['+', '+', '0'] | ['+', '+', '0'] | = | ok |
| III | (a) Lon. | +++ | ['+', '+', '+'] | ['+', '+', '+'] | = | ok |
| III | (a) Mel. | 0++ | ['0', '+', '+'] | ['0', '+', '+'] | = | ok |
| III | (b) Mad. | --0 | ['-', '-', '0'] | ['-', '-', '0'] | = | ok |
| III | (b) Lon. | --- | ['-', '-', '-'] | ['-', '-', '-'] | = | ok |
| III | (b) Mel. | -0- | ['-', '0', '-'] | ['-', '0', '-'] | = | ok |
| III | (c) Mad. | --- | ['-', '-', '-'] | ['-', '-', '-'] | = | ok |
| III | (c) Lon. | --- | ['-', '-', '-'] | ['-', '-', '-'] | = | ok |
| III | (c) Mel. | --- | ['-', '-', '-'] | ['-', '-', '-'] | = | ok |
| III | (d) Mad. | --0 | ['-', '-', '0'] | ['-', '-', '0'] | = | ok |
| III | (d) Lon. | +00 | ['+', '0', '0'] | ['+', '0', '0'] | = | ok |
| III | (d) Mel. | -+- | ['-', '+', '-'] | ['-', '+', '-'] | = | ok |
| III | (e) Mad. | +++ | ['+', '+', '+'] | ['+', '+', '+'] | = | ok |
| III | (e) Lon. | +++ | ['+', '+', '+'] | ['+', '+', '+'] | = | ok |
| III | (e) Mel. | 0++ | ['0', '+', '+'] | ['0', '+', '+'] | = | ok |
| III | (a) PEMS04 | 0 | 0 | 0 | = | ok |
| III | (a) PEMS08 | - | - | - | = | ok |
| III | (b) PEMS04 | - | - | - | = | ok |
| III | (b) PEMS08 | 0 | 0 | 0 | = | ok |
| III | (c) PEMS04 | - | - | - | = | ok |
| III | (c) PEMS08 | - | - | - | = | ok |
| III | (d) PEMS04 | - | - | - | = | ok |
| III | (d) PEMS08 | - | - | - | = | ok |
| III | (e) PEMS08 | 0 | 0 | 0 | = | ok |
| III nota | (a) PEMS04 media | +0.003 | 0.00258101560498 | 0.00258101560498 | 0 | ok |
| III nota | (a) PEMS04 IC basso | -0.007 | -0.007100800293 | -0.007100800293 | 0 | ok |
| III nota | (a) PEMS04 IC alto | +0.013 | 0.0128630072062 | 0.0128630072062 | 0 | ok |
| III nota | (b) PEMS04 media | -0.022 | -0.0219013491219 | -0.0219013491219 | 0 | ok |
| III nota | (b) PEMS04 IC basso | -0.031 | -0.0305107109079 | -0.0305107109079 | 0 | ok |
| III nota | (b) PEMS04 IC alto | -0.013 | -0.0132830613844 | -0.0132830613844 | 0 | ok |
| III nota | (c) PEMS04 media | -0.033 | -0.0330253450752 | -0.0330253450752 | 0 | ok |
| III nota | (c) PEMS04 IC basso | -0.047 | -0.0466584475138 | -0.0466584475138 | 0 | ok |
| III nota | (c) PEMS04 IC alto | -0.019 | -0.0186843696192 | -0.0186843696192 | 0 | ok |
| III nota | (d) PEMS04 media | -0.023 | -0.022513523397 | -0.022513523397 | 0 | ok |
| III nota | (d) PEMS04 IC basso | -0.034 | -0.0341435507561 | -0.0341435507561 | 0 | ok |
| III nota | (d) PEMS04 IC alto | -0.010 | -0.0096419201121 | -0.0096419201121 | 0 | ok |
| III nota | (a) PEMS08 media | -0.039 | -0.0394311960087 | -0.0394311960087 | 0 | ok |
| III nota | (a) PEMS08 IC basso | -0.076 | -0.0759818154857 | -0.0759818154857 | 0 | ok |
| III nota | (a) PEMS08 IC alto | -0.004 | -0.00367426162329 | -0.00367426162329 | 0 | ok |
| III nota | (b) PEMS08 media | -0.034 | -0.034392444644 | -0.034392444644 | 0 | ok |
| III nota | (b) PEMS08 IC basso | -0.071 | -0.0712011375247 | -0.0712011375247 | 0 | ok |
| III nota | (b) PEMS08 IC alto | +0.009 | 0.00906330758332 | 0.00906330758332 | 0 | ok |
| III nota | (c) PEMS08 media | -0.091 | -0.0908492906919 | -0.0908492906919 | 0 | ok |
| III nota | (c) PEMS08 IC basso | -0.131 | -0.13147935877 | -0.13147935877 | 0 | ok |
| III nota | (c) PEMS08 IC alto | -0.042 | -0.0419810744684 | -0.0419810744684 | 0 | ok |
| III nota | (d) PEMS08 media | -0.074 | -0.0738236406527 | -0.0738236406527 | 0 | ok |
| III nota | (d) PEMS08 IC basso | -0.118 | -0.118070507686 | -0.118070507686 | 0 | ok |
| III nota | (d) PEMS08 IC alto | -0.023 | -0.0225435790391 | -0.0225435790391 | 0 | ok |
| III nota | (e) PEMS08 media | +0.040 | 0.0395886280471 | 0.0395886280471 | 0 | ok |
| III nota | (e) PEMS08 IC basso | -0.019 | -0.0193122781405 | -0.0193122781405 | 0 | ok |
| III nota | (e) PEMS08 IC alto | +0.089 | 0.0890112716417 | 0.0890112716417 | 0 | ok |

## 2. File rigenerati

Impronta = SHA-256 (16 cifre) dell'elenco ordinato (punto, valore a 12 cifre) di tutti i numeri del file: coincide fra congelato e rigenerato se e solo se coincidono tutti i numeri.

| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |
|---|---|---|---:|---:|---:|---|---|
| `evoluzione/analisi/architettura_ck.py` | `architettura_ck.json` | ok | 2828 | 0 | 0 | 9a6024410ca9af1c | 9a6024410ca9af1c |
| `genera_congelamento_e2.py` | `congelamento_e2.json` | ok | 408 | 0 | 0 | b98132278a8d338f | b98132278a8d338f |
| `genera_congelamento_e2.py` | `CONGELAMENTO_E2.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/analisi/analizza_e3.py --out results/evoluzione/analisi_e3.json` | `analisi_e3.json` | ok | 104 | 0 | 0 | e91b1ef89b13fef8 | e91b1ef89b13fef8 |
| `evoluzione/analisi/analizza_veterani_e3.py --out results/evoluzione/veterani_e3.json` | `veterani_e3.json` | ok | 53 | 0 | 0 | 98bce138c2c27a5e | 98bce138c2c27a5e |
| `evoluzione/analisi/riselezione_rmon.py --out results/evoluzione/riselezione_rmon.json` | `riselezione_rmon.json` | ok | 974 | 0 | 0 | 94497835ba2fa3e2 | 94497835ba2fa3e2 |
| `evoluzione/analisi/costi_e3.py --out results/evoluzione/costi_e3.json` | `costi_e3.json` | ok | 168 | 0 | 0 | 6a6ce87e36947420 | 6a6ce87e36947420 |
| `genera_congelamento_e3.py` | `congelamento_e3.json` | ok | 398 | 0 | 0 | 102a7062c1d161e5 | 102a7062c1d161e5 |
| `genera_congelamento_e3.py` | `CONGELAMENTO_E3.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/esperimenti/esegui_e4.py --fase scegli` | `e4_scelta_gated.json` | ok | 64 | 0 | 0 | fb94098876d3d807 | fb94098876d3d807 |
| `evoluzione/esperimenti/esegui_e4.py --fase test` | `e4_risultati.json` | ok | 969 | 0 | 0 | e069d72f828c8dd9 | e069d72f828c8dd9 |
| `evoluzione/analisi/analizza_e4.py` | `e4_griglia_test.json` | ok | 60 | 0 | 0 | 50107659f8ac6540 | 50107659f8ac6540 |
| `evoluzione/analisi/analizza_copertura_e4.py --out results/evoluzione/copertura_e4.json` | `copertura_e4.json` | ok | 5594 | 0 | 0 | 1f54c582fcc7aae1 | 1f54c582fcc7aae1 |
| `genera_congelamento_e4.py` | `congelamento_e4.json` | ok | 7028 | 0 | 0 | 9eedc2f2eb9d0bd9 | 9eedc2f2eb9d0bd9 |
| `genera_congelamento_e4.py` | `CONGELAMENTO_E4.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/analisi/analizza_e3bis.py` | `e3bis_risultati.json` | ok | 68 | 0 | 0 | de04d622c519661c | de04d622c519661c |
| `genera_congelamento_e3bis.py` | `congelamento_e3bis.json` | ok | 346 | 0 | 0 | bdeb10747e7130e0 | bdeb10747e7130e0 |
| `genera_congelamento_e3bis.py` | `CONGELAMENTO_E3bis.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/esperimenti/esegui_e5.py --fase prepara` | `e5_prepara.json` | ok | 180 | 0 | 0 | c0190bc37213ecf0 | c0190bc37213ecf0 |
| `evoluzione/analisi/settimana_vs_A_e5.py` | `e5_settimana_vs_A.json` | ok | 58 | 0 | 0 | 2ba3e8250e3e646a | 2ba3e8250e3e646a |
| `evoluzione/esperimenti/esegui_e5.py --fase test` | `e5_risultati.json` | ok | 338 | 0 | 0 | bc9bcd92ea290f6c | bc9bcd92ea290f6c |
| `evoluzione/analisi/analizza_e5.py` | (solo figure) | ok | — | — | — | — | — |
| `genera_congelamento_e5.py` | `congelamento_e5.json` | DIVERSO | 828 | 0 | 0 | 52cdd962ff9888f6 | 52cdd962ff9888f6 |
| `genera_congelamento_e5.py` | `CONGELAMENTO_E5.md` | DIVERSO | — | 2 righe | — | — | — |
| `evoluzione/esperimenti/esegui_e6.py --fase scegli` | `e6_scelta_gated.json` | ok | 27 | 0 | 0 | a2b292f6a2e4cfcf | a2b292f6a2e4cfcf |
| `evoluzione/esperimenti/esegui_e6.py --fase test` | `e6_risultati.json` | ok | 61 | 0 | 0 | 301ef97098ef8def | 301ef97098ef8def |
| `evoluzione/esperimenti/esegui_e6.py --fase test-bis` | `e6bis_risultati.json` | ok | 21 | 0 | 0 | 65bd37791575acfa | 65bd37791575acfa |
| `evoluzione/esperimenti/esegui_e6a.py --fase scegli` | `e6a_scelta_gated.json` | ok | 27 | 0 | 0 | cded6a4416643846 | cded6a4416643846 |
| `evoluzione/esperimenti/esegui_e6a.py --fase test` | `e6a_risultati.json` | ok | 45 | 0 | 0 | 3cf90d306917ec12 | 3cf90d306917ec12 |
| `evoluzione/esperimenti/esegui_e6.py --fase origini` | `e6_origini_comuni.json` | ok | 10 | 0 | 0 | e51b9c6f886e2b51 | e51b9c6f886e2b51 |
| `genera_congelamento_e6.py` | `CONGELAMENTO_E6.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/analisi/e7_stadio1.py` | `e7_stadio1.json` | ok | 826 | 0 | 0 | a79b94c5c23f74fb | a79b94c5c23f74fb |
| `evoluzione/analisi/e7_posthoc.py` | `e7_posthoc.json` | ok | 149 | 0 | 0 | 2f748762a3606a3d | 2f748762a3606a3d |
| `genera_congelamento_e7.py` | `congelamento_e7.json` | ok | 975 | 0 | 0 | d97c79a97d4566f1 | d97c79a97d4566f1 |
| `genera_congelamento_e7.py` | `CONGELAMENTO_E7.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/esperimenti/esegui_e8.py --fase soglie` | `e8_soglie.json` | ok | 247 | 0 | 0 | b797b271a467cf7b | b797b271a467cf7b |
| `evoluzione/esperimenti/esegui_e8.py --fase test` | `e8_risultati.json` | ok | 1879 | 0 | 0 | b04fcfbd9e3c88db | b04fcfbd9e3c88db |
| `evoluzione/esperimenti/esegui_e8.py --fase test-curve` | `e8bis_risultati.json` | ok | 1177 | 0 | 0 | 42d24d69adae6d31 | 42d24d69adae6d31 |
| `evoluzione/analisi/figura_e8bis.py` | `curve_e8bis_punti.json` | ok | 1368 | 0 | 0 | c9be56b1126d0bc0 | c9be56b1126d0bc0 |
| `evoluzione/analisi/figura2_51.py` | (solo figure) | ok | — | — | — | — | — |
| `genera_congelamento_e8.py` | `CONGELAMENTO_E8.md` | ok | — | 0 righe | — | — | — |
| `evoluzione/analisi/analizza_e4.py --lingua en` | (solo figure) | ok | — | — | — | — | — |
| `evoluzione/analisi/analizza_e5.py --lingua en` | (solo figure) | ok | — | — | — | — | — |
| `evoluzione/analisi/figura2_51.py --lingua en` | (solo figure) | ok | — | — | — | — | — |
| `evoluzione/analisi/figura_e8bis.py --lingua en` | (solo figure) | ok | — | — | — | — | — |

## 3. Ogni numero diverso oltre la tolleranza

- `CONGELAMENTO_E5.md` (date e impronte mascherate): `-- **E3-bis**: **non eseguito** prima di questo congelamento: nel paper il confronto dei costi fra R-orig (24 h di dati) e F′ (1 settimana) e' dichiarato **a dati asimmetrici**.`
- `CONGELAMENTO_E5.md` (date e impronte mascherate): `+- **E3-bis**: eseguito, vedi il suo congelamento.`

## 4. Impronte degli ingressi citate nei congelamenti

Ogni impronta di file citata in un congelamento (e nella tabella dei costi), ricalcolata sul file del repository: SHA-256 dei byte (16 cifre) o campo interno `impronta`. Un dato diverso fa fallire; un file di codice cambiato dopo il congelamento e' informativo.

| congelamento | file | tipo | impronta citata | esito |
|---|---|---|---|---|
| `CONGELAMENTO_E2.md` | `protocol/E2.md` | codice | `14a94b8a2bebc7e5` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/esegui_E.py` | codice | `ccd37ca7a9f4012e` | cambiato dopo il congelamento |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/addestramento.py` | codice | `d2d68544fc153371` | cambiato dopo il congelamento |
| `CONGELAMENTO_E2.md` | `evoluzione/componente/identita.py` | codice | `e13498ad4f3aea18` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/componente/adattamento.py` | codice | `80e810978be4fff6` | cambiato dopo il congelamento |
| `CONGELAMENTO_E2.md` | `evoluzione/componente/canonico.py` | codice | `13159f040bde67f1` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/esegui_e2.py` | codice | `d84a78e61e239dc4` | cambiato dopo il congelamento |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/ricostruisci_predizioni.py` | codice | `5b37aeb8d51ea15f` | cambiato dopo il congelamento |
| `CONGELAMENTO_E2.md` | `evoluzione/analisi/analizza_e2.py` | codice | `d50afaf7aad4534c` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/analisi/verifica_appaiamento.py` | codice | `ab1857cde149e44c` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/adeguatezza_E1.py` | codice | `d006022ce5529bd7` | ok |
| `CONGELAMENTO_E2.md` | `evoluzione/esperimenti/sensibilita_rho_e2.py` | codice | `cf347e585b8f6c6f` | ok |
| `CONGELAMENTO_E3.md` | `protocol/E3.md` | codice | `245085de8a909ca8` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/componente/bracci.py` | codice | `d803e43387c5c6a4` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/componente/campionamento.py` | codice | `d45b2980a89a570f` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/addestramento.py` | codice | `f5d69a789aadd479` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/inserimento.py` | codice | `bc1d6ecd562b0888` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/esegui_inserimento.py` | codice | `95349fe3b6f6356f` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/ricostruisci_predizioni.py` | codice | `12f5a31f2521a5fa` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/veterani_e3.py` | codice | `5fee87edbc851cde` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/esperimenti/riselezione_rmon_test.py` | codice | `a8b19db9c3d2fc07` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/analisi/analizza_e3.py` | codice | `a591fde2f22d251f` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/analisi/analizza_veterani_e3.py` | codice | `d51ff7c1953d9fc2` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/analisi/costi_e3.py` | codice | `c71f3f1ca388a3cb` | ok |
| `CONGELAMENTO_E3.md` | `evoluzione/analisi/riselezione_rmon.py` | codice | `d0552d186bccad66` | ok |
| `CONGELAMENTO_E3bis.md` | `protocol/E5.md` | codice | `3dd706bcf3ddd899` | ok |
| `CONGELAMENTO_E3bis.md` | `evoluzione/esperimenti/esegui_inserimento.py` | codice | `3df759803c95fe49` | cambiato dopo il congelamento |
| `CONGELAMENTO_E3bis.md` | `evoluzione/esperimenti/ricostruisci_predizioni.py` | codice | `12f5a31f2521a5fa` | ok |
| `CONGELAMENTO_E3bis.md` | `evoluzione/analisi/analizza_e3bis.py` | codice | `c4d791c24eedded9` | ok |
| `CONGELAMENTO_E4.md` | `protocol/E4.md` | codice | `e275daec5945c26b` | ok |
| `CONGELAMENTO_E4.md` | `e4_scelta_gated.json` | dato | `81e47f64f3d63b3b` | ok |
| `CONGELAMENTO_E4.md` | `evoluzione/componente/adattamento.py` | codice | `ce88e086bcbdddba` | ok |
| `CONGELAMENTO_E4.md` | `evoluzione/esperimenti/esegui_e4.py` | codice | `b8fbdf050a27f487` | ok |
| `CONGELAMENTO_E4.md` | `evoluzione/esperimenti/costi_e4.py` | codice | `c56d0883d7ca775c` | ok |
| `CONGELAMENTO_E4.md` | `evoluzione/analisi/analizza_e4.py` | codice | `1fb316ed0a0ae223` | cambiato dopo il congelamento |
| `CONGELAMENTO_E4.md` | `evoluzione/analisi/analizza_copertura_e4.py` | codice | `0269f7763aa09d4d` | ok |
| `CONGELAMENTO_E5.md` | `protocol/E5.md` | codice | `3dd706bcf3ddd899` | ok |
| `CONGELAMENTO_E5.md` | `e4_scelta_gated.json` | dato | `81e47f64f3d63b3b` | ok |
| `CONGELAMENTO_E5.md` | `e5_k_secondaria.json` | dato | `395d17a4f05462ea` | ok |
| `CONGELAMENTO_E5.md` | `evoluzione/esperimenti/addestramento.py` | codice | `b549d8a90bdeffe8` | cambiato dopo il congelamento |
| `CONGELAMENTO_E5.md` | `evoluzione/esperimenti/esegui_e5.py` | codice | `f08dd758210319e2` | ok |
| `CONGELAMENTO_E5.md` | `evoluzione/esperimenti/preparazione_e5.py` | codice | `324044aefb327bab` | ok |
| `CONGELAMENTO_E5.md` | `evoluzione/analisi/settimana_vs_A_e5.py` | codice | `ef2ceb4812f93353` | ok |
| `CONGELAMENTO_E5.md` | `evoluzione/analisi/analizza_e5.py` | codice | `2206c2dff622bef0` | cambiato dopo il congelamento |
| `CONGELAMENTO_E6.md` | `protocol/E6.md` | codice | `c7a6583897215545` | ok |
| `CONGELAMENTO_E6.md` | `e6_origini_comuni.json` | dato | `604cac98cf78ce31` | ok |
| `CONGELAMENTO_E6.md` | `results/evoluzione/e6bis_risultati.json` | dato | `7c289e6e5d3c73d4` | ok |
| `CONGELAMENTO_E6.md` | `results/evoluzione/e6_risultati.json` | dato | `1ce676da7a5168f8` | ok |
| `CONGELAMENTO_E6.md` | `results/evoluzione/e6a_risultati.json` | dato | `16a47787e7f89d5a` | ok |
| `CONGELAMENTO_E6.md` | `results/evoluzione/e6a_risultati.json` | dato | `16ed7800df4b401b` | ok |
| `CONGELAMENTO_E6.md` | `evoluzione/esperimenti/esegui_e6.py` | codice | `8776e85d4006317a` | ok |
| `CONGELAMENTO_E6.md` | `evoluzione/esperimenti/esegui_e6a.py` | codice | `56f8ea3ad50ac238` | ok |
| `CONGELAMENTO_E6.md` | `evoluzione/esperimenti/estrai_pems04.py` | codice | `93d98cf3d58bbb95` | ok |
| `CONGELAMENTO_E6.md` | `evoluzione/esperimenti/calendario_pems08.py` | codice | `35bc7585e8732454` | ok |
| `CONGELAMENTO_E6.md` | `evoluzione/esperimenti/esegui_e2.py` | codice | `cc43cf3ac7128515` | ok |
| `CONGELAMENTO_E6.md` | `protocol/E6bis.md` | codice | `1d74950bf0f0ba9a` | ok |
| `CONGELAMENTO_E7.md` | `protocol/E7.md` | codice | `07db021e85236235` | ok |
| `CONGELAMENTO_E7.md` | `e4_scelta_gated.json` | dato | `81e47f64f3d63b3b` | ok |
| `CONGELAMENTO_E7.md` | `e5_k_secondaria.json` | dato | `395d17a4f05462ea` | ok |
| `CONGELAMENTO_E7.md` | `evoluzione/analisi/e7_stadio1.py` | codice | `fab3034c6cf470c9` | ok |
| `CONGELAMENTO_E7.md` | `evoluzione/analisi/e7_posthoc.py` | codice | `ab62ffb9a8b69a49` | ok |
| `CONGELAMENTO_E8.md` | `protocol/E8.md` | codice | `611d3541a6086e19` | ok |
| `CONGELAMENTO_E8.md` | `e8_soglie.json` | dato | `dcb93389339a6657` | ok |
| `CONGELAMENTO_E8.md` | `evoluzione/esperimenti/esegui_e8.py` | codice | `f9db7b5830a5b325` | ok |
| `CONGELAMENTO_E8.md` | `evoluzione/analisi/figura_e8bis.py` | codice | `756828a7025fa32c` | cambiato dopo il congelamento |
| `CONGELAMENTO_E8.md` | `protocol/E8bis.md` | codice | `0323686ceb957117` | ok |
| `CONGELAMENTO_E8.md` | `results/evoluzione/e8_risultati.json` | dato | `dcb93389339a6657` | ok |
| `paper/tabella_costi_appaiati.md` | `results/evoluzione/costi_sessione.json` | dato | `3fabd92bb2bf9f0c` | ok |
| `paper/tabella_costi_appaiati.md` | `results/evoluzione/costi_sessione_pems08.json` | dato | `de392bca1b944791` | ok |
| `paper/tabella_costi_appaiati.md` | `results/evoluzione/costi_tabella_sessione.json` | dato | `93d346501f9bc777` | ok |

## 5. Documenti: differenze di sola prosa (stessi numeri)

Informativo, non fa fallire: righe del documento rigenerato diverse da quelle congelate ma con gli stessi numeri (per esempio una frase che dipende da quali esperimenti esistevano al momento del congelamento).

Nessuna.

## 6. Coerenza per contenuto fra risultati e congelamenti

Dove il generatore incorpora il json di analisi nel proprio, i due devono coincidere per contenuto (non per impronta del file). Una divergenza fa fallire.

| copia | controllo | esito |
|---|---|---|
| congelata | congelamento_e3.json["analisi"] == analisi_e3.json | ok |
| congelata | riviste/R/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |
| congelata | riviste/R-mon/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |
| congelata | riviste/R-orig/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |
| rigenerata | congelamento_e3.json["analisi"] == analisi_e3.json | ok |
| rigenerata | riviste/R/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |
| rigenerata | riviste/R-mon/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |
| rigenerata | riviste/R-orig/lancio: 108 impronte in analisi_e3.json, 108 nel congelamento | ok |

## 7. File di codice cambiati dopo il congelamento che li cita (registro, Paper 2)

Informativo. Per ogni file di codice con impronta citata diversa da quella attuale: il commit della versione citata (se la storia git la contiene) e i commit successivi che lo cambiano; **etichette** = cambio di sole etichette e impaginazione delle figure (`--lingua en`), nessun calcolo.

| file | congelamento | impronta citata | versione citata (commit, data) | cambiato in (commit, data, oggetto) |
|---|---|---|---|---|
| `evoluzione/esperimenti/esegui_E.py` | `CONGELAMENTO_E2.md` | `ccd37ca7a9f4012e` | `c7b42da179e9` 2026-09-30 | `7204736f14e8` 2026-10-02 Preflight sul tempo di parete; analisi copertura E4; riselezione R-mon a peso uguale |
| `evoluzione/esperimenti/addestramento.py` | `CONGELAMENTO_E2.md` | `d2d68544fc153371` | `4bafa5ef0491` 2026-09-30 | `7204736f14e8` 2026-10-02 Preflight sul tempo di parete; analisi copertura E4; riselezione R-mon a peso uguale<br>`c6526af55607` 2026-10-04 E5: esecutore (prepara, k-secondaria, addestra, valuta, test); _partizioni con fine_period<br>`eb7f852afec6` 2026-10-07 E6: contesti PEMS08_p<k> (stesso schema di PEMS04); estrattore parametrizzato su nome, ini<br>`fda754ec150f` 2026-10-07 E6 parte B: 6 partizioni x 6 semi (SEME_PARTIZIONE_E6, contesti PEMS08_p0..p5, --partizion |
| `evoluzione/componente/adattamento.py` | `CONGELAMENTO_E2.md` | `80e810978be4fff6` | `b064cfc5c93b` 2026-09-19 | `dadd2dc2dcb5` 2026-10-03 E4: esecutore (valuta/scegli/test), gancio di traiettoria in adatta; controlli 3,4,6,7 per |
| `evoluzione/esperimenti/esegui_e2.py` | `CONGELAMENTO_E2.md` | `d84a78e61e239dc4` | `f9290bbaa468` 2026-09-30 | `6629f40fd549` 2026-10-08 da_E1: sorgente del predittore dal punto di controllo (undici canali su PEMS); difetto eme |
| `evoluzione/esperimenti/ricostruisci_predizioni.py` | `CONGELAMENTO_E2.md` | `5b37aeb8d51ea15f` | `ffac660209ee` 2026-09-29 | `821295f19a06` 2026-10-02 E3: analisi, veterani, rimisura isolata dei costi<br>`dc35e91fb1fc` 2026-10-07 E3-bis: ricostruzione delle predizioni con acquisizione dichiarata |
| `evoluzione/esperimenti/esegui_inserimento.py` | `CONGELAMENTO_E3bis.md` | `3df759803c95fe49` | `d8e828664d96` 2026-10-06 | `db9f8f3b1c24` 2026-10-10 Esecutore: difetto 19 — riviste di E3 dal solo lancio (108 manifesti per braccio, per impr |
| `evoluzione/analisi/analizza_e4.py` | `CONGELAMENTO_E4.md` | `1fb316ed0a0ae223` | `5af016944005` 2026-10-04 | `680b35ef7a1c` 2026-10-04 E5: F'(1 sett.) - A, calendario e potenza derivati; protocol/E5.md con le quattro righe de<br>`d8ef81299651` 2026-10-10 paper1: analysis/main.py, prima versione — **etichette** |
| `evoluzione/esperimenti/addestramento.py` | `CONGELAMENTO_E5.md` | `b549d8a90bdeffe8` | `c6526af55607` 2026-10-04 | `eb7f852afec6` 2026-10-07 E6: contesti PEMS08_p<k> (stesso schema di PEMS04); estrattore parametrizzato su nome, ini<br>`fda754ec150f` 2026-10-07 E6 parte B: 6 partizioni x 6 semi (SEME_PARTIZIONE_E6, contesti PEMS08_p0..p5, --partizion |
| `evoluzione/analisi/analizza_e5.py` | `CONGELAMENTO_E5.md` | `2206c2dff622bef0` | `820d419c9649` 2026-10-06 | `d8ef81299651` 2026-10-10 paper1: analysis/main.py, prima versione — **etichette** |
| `evoluzione/analisi/figura_e8bis.py` | `CONGELAMENTO_E8.md` | `756828a7025fa32c` | `853c8474b7ce` 2026-10-10 | `d80043c971e8` 2026-10-10 paper1: figura 2 (§5.1) e legenda figura E8-bis<br>`d8ef81299651` 2026-10-10 paper1: analysis/main.py, prima versione — **etichette** |

## 8. Impronte del codice diverse da quelle registrate nel congelamento (json)

Informativo, non fa fallire: il file di codice e' cambiato dopo il congelamento, i numeri no (sezione 3). Date, commit e istanti non sono elencati.

- `congelamento_e2.json` `/impronte/evoluzione/componente/adattamento.py`: congelato 80e810978be4fff6, attuale ce88e086bcbdddba
- `congelamento_e2.json` `/impronte/evoluzione/esperimenti/addestramento.py`: congelato d2d68544fc153371, attuale f5d69a789aadd479
- `congelamento_e2.json` `/impronte/evoluzione/esperimenti/esegui_E.py`: congelato ccd37ca7a9f4012e, attuale 87abfd761022c868
- `congelamento_e2.json` `/impronte/evoluzione/esperimenti/esegui_e2.py`: congelato d84a78e61e239dc4, attuale cc43cf3ac7128515
- `congelamento_e2.json` `/impronte/evoluzione/esperimenti/ricostruisci_predizioni.py`: congelato 5b37aeb8d51ea15f, attuale 12f5a31f2521a5fa
- `congelamento_e3bis.json` `/impronte/evoluzione/esperimenti/esegui_inserimento.py`: congelato 3df759803c95fe49, attuale 95349fe3b6f6356f
- `congelamento_e4.json` `/impronte/evoluzione/analisi/analizza_e4.py`: congelato 1fb316ed0a0ae223, attuale a0357827b0afe9d4
- `congelamento_e5.json` `/impronte/evoluzione/analisi/analizza_e5.py`: congelato 2206c2dff622bef0, attuale b85d5af32a602af6
- `congelamento_e5.json` `/impronte/evoluzione/esperimenti/addestramento.py`: congelato b549d8a90bdeffe8, attuale f5d69a789aadd479
- `e4_scelta_gated.json` `/impronta`: congelato 81e47f64f3d63b3b, attuale 76adea6278cf72be
- `e6_scelta_gated.json` `/impronta`: congelato 1ce676da7a5168f8, attuale 27e9e15e24026a88
- `e6a_scelta_gated.json` `/impronta`: congelato 16ed7800df4b401b, attuale 4a66e2d93eecc12d
- `e8_soglie.json` `/_impronta`: congelato dcb93389339a6657, attuale f415a8f0bc2bdb02

## 9. Figure (script esistenti)

- `figure/curva_e4.png` da `evoluzione/analisi/analizza_e4.py`: prodotta
- `figure/traiettoria_e4.png` da `evoluzione/analisi/analizza_e4.py`: prodotta
- `figure/griglia_e4.png` da `evoluzione/analisi/analizza_e4.py`: prodotta
- `figure/episodi_e5.png` da `evoluzione/analisi/analizza_e5.py`: prodotta
- `figure/secondaria_e5.png` da `evoluzione/analisi/analizza_e5.py`: prodotta
- `figure/e7_stadio1.png` da `evoluzione/analisi/e7_stadio1.py`: prodotta
- `figure/curve_e8bis.png` da `evoluzione/analisi/figura_e8bis.py`: prodotta
- `figure/figura2_51.png` da `evoluzione/analisi/figura2_51.py`: prodotta
- `<paper>/figures/curva_e4.pdf` da `evoluzione/analisi/analizza_e4.py --lingua en`: prodotta
- `<paper>/figures/traiettoria_e4.pdf` da `evoluzione/analisi/analizza_e4.py --lingua en`: prodotta
- `<paper>/figures/episodi_e5.pdf` da `evoluzione/analisi/analizza_e5.py --lingua en`: prodotta
- `<paper>/figures/figura2_51.pdf` da `evoluzione/analisi/figura2_51.py --lingua en`: prodotta
- `<paper>/figures/curve_e8bis.pdf` da `evoluzione/analisi/figura_e8bis.py --lingua en`: prodotta

## 10. Impronte degli ingressi (`results/evoluzione`)

SHA-256 dei file di primo livello; per le cartelle, dell'elenco (nome, dimensione) dei file.

```
E1_costi_sessione/  elenco:13819b134101f6681ac41f88785a0222d070a476296a92442d9a08b3e16c72f6 (18 file)
E1_e6_pems04/  elenco:aab2c96dd59ab92acd25fbac6da10c9b34713864a7ea4d0530043cdc6820698e (72 file)
E1_e6_pems08/  elenco:a569553cc35001d9d38d3ce7e4ee2da3e84caf53ec902c3c52b5f2606e27dbf2 (72 file)
E1_inserimento/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
E1_inserimento_griglia/  elenco:99488d175a742aea903d19fd3a28ec6f8b47c2d297f3828e440ff294d54b72b1 (218 file)
E1_inserimento_griglia_ep2/  elenco:b830c0bf04e3fceeb5c6cf005af23b9a98c9cd98b88b5c8fc0922a22c860df54 (108 file)
E1_inserimento_griglia_ep3/  elenco:2f8639b08c54717bc57d56ad80d132e55ae7e358c3481eb4968bc548f665c1cf (108 file)
E1_rho005_inserimento_griglia/  elenco:7271aeadcf685c7b012f98ee3e5c5168ee5b4e2431fee9da1ddf04b32ea2fbf2 (8 file)
E1_rho030_inserimento_griglia/  elenco:7271aeadcf685c7b012f98ee3e5c5168ee5b4e2431fee9da1ddf04b32ea2fbf2 (8 file)
E2_espansioni/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
E3_regressioni/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
E4_costo/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
E5_robustezza/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
E_e6_pems08/  elenco:a87c1240fcf7b18c4dd758fdd82f32f19a7e821faadf4b3402aae8f011950e9f (72 file)
E_inserimento/  elenco:12719c2b0ffdccd82c99b80eea31b873b3d09b905334e8f6adbf8c12829aec0d (110 file)
E_inserimento_griglia/  elenco:12bdaaf4ec5193c0b0303317c082eea54664a8b491ad00d1390d55606107ec23 (218 file)
E_inserimento_principale/  elenco:29c4ada11d82c22d2cb2791ca569c1b538e5e74877e164c16d2737a58500a5ab (218 file)
LEGGIMI.md  a99d17f4d66ebb91c756b24d4d21cd9bdeedc9ccb42ba3b28e3a13652424d11d
_quarantena_e3_falso_20260930/  elenco:ebb71f2a61554d20a56d8398e3ccc479ad6047e0cc0e012e72f7332f87f061a7 (650 file)
adeguatezza/  elenco:11ce3583cba476620b1f78a070a965fe769b264235032849d2d39d76949bfac4 (110 file)
adeguatezza_E1.json  600ec636dc81dc8e83590d9f92b54c94921e6005ca974be62aa12ad0a8e98ede
adeguatezza_E1/  elenco:54aed0a62ea0efdfd8a09bd33b3aa765f033b5123c9dabfd48eeb3f2eb96f508 (2 file)
analisi_e2.log  b7ae2f3450211bc928ff1805cdebe5ed2bf84b3ddfeecda29b6dbbf8b3440f47
analisi_e3.json  3ca56089294b858f92f2d490fe01aa0082328ec815cd78fecab7d4f3818119b7
analisi_f0.log  89cc7353484b2a27acba33cb0fb00a10a49bcf3c2c98c61bb2bf460225e575c9
analisi_pems04.log  15681ab40d37ad87bfc7f59b374baa26fbba06b1f7e870037523b6777f3fddfe
analisi_refresh.log  7a1e01f0c145b24a8a8857132a7fc0947746fec1f437866a41b83ebec9c72894
architettura_ck.json  cf03298aad91efa588605f962ec1cd1f2a7324e00af085691f7a7838dac15bfc
audit/  elenco:1b9767d96db97f9ca2e719963d8d80345da73f08b35beac5d94266a2120f04dc (1 file)
audit_ciclo.json  731a885f2f4fe38c9dc1cf68ce91812b9dee90182cdb1a9e82d01e81c6628b6f
audit_mogernn/  elenco:363f3e843226e3155d7783867351c0f7a2baacf1183e0a8adb994141d133c1e3 (3 file)
canonico/  elenco:f5376a19cd04f7b2eae23fcd1e83e7456a99fa4996fd0e4fab5e0308d1d3ab2d (30 file)
collaudo_pems04.log  038e2f6f94d30af1b7efe508a576315df6125d09357e6f65e38167b4fddadb9e
congelamento_e2.json  356cec99f3af05e74c112f5067ccd6e2c76d73620c011a6a34efa17544e14e0a
congelamento_e3.json  b594eb185369bbd87f45a02660deee3372101b98858495e1f4c1c3c117db434b
congelamento_e3bis.json  0797a1b655cf7be72632df8dbe14a5c5ffd7aecd57a1e39a0864b81f54739260
congelamento_e4.json  a59ce714521181faa1d28e3ef53d70b438ad40bc3b206768e31dc7bf7d6527f7
congelamento_e5.json  8fabf2e04b96e40d2ed85b66d3298bd97e54b83402c370fbdf89e3054a40c3ac
congelamento_e7.json  ba9c946b4e024894f47a6e81280881e61c4f6feab8f691e6da666ed24f019ac5
copertura_e4.json  f0332c8b7e4031bdf56022d685613d21411fe2b93eff16f519b470ed15da22ee
costi_appaiati.json  7eec120643b41283e7235283907e650a8c5380c349b4bd93ebe4f27d026484b5
costi_e3.json  90b0ddebe6637b325ea54bba0891831923d05da09eae9a2e5905a2528e3cc6bc
costi_e3bis.json  32df030ae8fc6bd2a193af7796717a585e8747b9d3639385eb0115dc4a526917
costi_e4.json  057d5c122b2cb0b1d1704d2e0bbc81ca6e8fbd471a973aca17a70946069c9f6b
costi_e4.log  5234d8856b1abe524c330b72c078ca833379bfb72c5384adca040f8f85941a3e
costi_sessione.json  3fabd92bb2bf9f0cbfe5bbf6cbb6abf4adf8b7570c788dac4bd61c53b329af45
costi_sessione_pems08.json  de392bca1b944791f001f71ff72fb5d2abc1ec28ad833b1ae1c557b1b142c448
costi_tabella_sessione.json  93d346501f9bc77789df30c51d90182f05e8cf1c11b50d97c67460a588e8afad
curve_e8bis_punti.json  2d82913a44059d7b435f63a96d2679f68a81b4b6e13148be9495443076c7e94b
diagnostica_griglia.json  3e8e23ae9b6cc58539880c068094c31a090163a674917a68dfa4d9cbe5133502
e3bis_addestra.log  b3aa5305a662cb55642e535cb7965166afc0002313b540335221e5dd704689c4
e3bis_analisi.log  21698cd47e20842715cfe093936cae1afce11b3ff8ba56aab0818498ea6f165a
e3bis_isolato.log  6642bc75a38504a4049fc2200a3fd87a022320005ca7bdae9ed7bdc099207c49
e3bis_risultati.json  2db2dd9ffece20726e5fb95fc3b2a7a9ae43b878e91c035140e5acdd889d715e
e4_griglia_test.json  ec5216a1206d1454283baf48fbe8c008d8ef69c892a811c9585d25460fa652f8
e4_risultati.json  bfd2b52b3d7440fe536061d49ca15328d6eaae1e65c2040189fb6b0152b93b2a
e4_scelta_gated.json  5ec1d3a3df09a7129c16105d51271b3472f8b1cbd69a6edd6715314ae99f9268
e4_test.log  31c099fb5f6270dd356181ca336eabebf9ff813a7b2357cc2362f2a29550f831
e4_valuta.log  878959f8d57bd1f20d5c9de925459d6210658ff68d57efe449cbe5e459f13e81
e5_addestra.log  c72299f1382238d222d61ac6705667ba677baf9414f2106569489ec8c49ccf14
e5_k_secondaria.json  0781e1d65ff764f2aa8a30921971a425d02c4ca93cee1f8c275da05ffb6d2092
e5_k_secondaria.log  8a9a337087aec90b64f8b2c2d53b437d27157c9acefbeaeeea0c0e079a04a187
e5_prepara.json  1d6cd0ce2638e75053d89b48bc9d1e2d4b02453d503c04297f28fa19936f64da
e5_prepara.log  96c9545ad46288c9e0eb792c7db12a3ba2a38181166465090b1967daf8fa1a32
e5_risultati.json  04609880cbede25f4803eeb1f3fec41e65c93392d145a8391e7b0e790838fc62
e5_settimana_vs_A.json  855b216f6e85a1d6dd3c488b63d60c672cc6d1cc725a16f01d3a6ac931545be8
e5_settimana_vs_A.log  008a6906543415754b58b7ce963f8e79edbb86120d45c76d95a53c4c1a136a61
e5_test.log  323ced3f64fe094f0f5f5957e4569a54c52dd235fad5ccd56280b7dbdd49667e
e5_valuta.log  11b1ff84107203291a868f2e01151e1c04c9ad3c02608aba05d22c85b3fafa79
e6_addestra.log  bee97921f9a7532d0bed5aae08028aa8d55a4afa05d6cead0625b3525f182911
e6_costi.json  e824b7be795577cacc6578997aaabbc6fa6c44f5c3dec8378a551c5d064221a8
e6_costi.log  234f74e6675b633281f65d84084160f4f9ebb6cc2a9fb808a6d35f2b67958a53
e6_costi.prima_della_sessione.json  e824b7be795577cacc6578997aaabbc6fa6c44f5c3dec8378a551c5d064221a8
e6_costi_E1_e6_pems08/  elenco:bbb9a5ceac0b20f2106b5bc567a538d5eae601a5126cec3c98ffcab375d8e040 (6 file)
e6_costi_e6_pems08/  elenco:948d2e6972f8895b3f16f6e85e67a58ca65587d46ed8009256cbf48faf9e4201 (18 file)
e6_costi_e6_pems08_672/  elenco:6ae0a47205caa680f1daf99bab4351888aac43d6efed74f46ce0eb02c95190fc (6 file)
e6_origini_comuni.json  7ba4598fbd016be717cb3135587441d791282087ba3323b7d8e31025196f1d75
e6_pems08/  elenco:e937683e7f98d65f9a9b06f7a2ad19a0687139be43b5d301571294f8464de71f (216 file)
e6_pems08_672/  elenco:f118fd35d86c18c19bddce737aa84d527da366687928bffa26cf68be8c92570d (72 file)
e6_pilota.json  86469c687df3e6f79931f371c0ec9525344731694011979127f416009d8fca8a
e6_pilota/  elenco:390aacbede26d1ba886e44c7a1889153b17c39de841269e24f0abba52fa0682f (2 file)
e6_risultati.json  7d8bdb9c51e24993a3242dad12cea5b08adb90259a6c4267b0718b0266fa66ee
e6_scegli.log  ba1730ad456a95f9233861b7047e9a45afc443fb9057bfbf7aa9d5ed8a6a8f29
e6_scelta_gated.json  e76346636f769c2d0451363ed320be6712d37877a249db71e6a89d53388cf592
e6_selezioneF.log  6f569d841fb3398bb884079b0a4cd92d5aa6514231639e95debde614cd7000a6
e6_sessione_E1_e6_pems08/  elenco:c0430b2eccf967ca55eff4ee131f65e28ef8d73054d617bc6ac9ac7c5576628d (6 file)
e6_sessione_e6_pems08/  elenco:c316bd2e6e8602507cb168b5cfeb7ccf53f49dc67387e2a8a82dd5e67cc881dd (18 file)
e6_sessione_e6_pems08_672/  elenco:10c44a593f2f05a6c0eacaa9099e15c445af090caeb91692480283eef8058411 (6 file)
e6_test.log  dc02644d54d7794bfb17bbd3b7511ce2565c11f11b18ea85416d5c1a197ce419
e6_valuta_prova.log  9f90fe55d88d3a0593e2491b71e894685f698a0574b14b72925edfb025fc7103
e6_valuta_validazione.log  62d4cc7af193eed3f0635d33ddf4f66465516f571887d7018d130628d9678c94
e6a_addestra.log  678aac2e2d2960a9b63a55145098d2b328a7e8134efdb4c92a6336abe35ff35c
e6a_risultati.json  74c6c95bacfeffd1cfa6cb558c2937cbb390b9b547733409bdf623cfb4a731cb
e6a_scegli.log  251127daf0b62078aa3dd1e54917e1eeb79feeef2e1304f4b13c0bb458a8bb36
e6a_scelta_gated.json  b699066ca0cac94d01ab02cd2a32c66905d7c40c9cdd1af5e2270facece4b45c
e6a_selezioneF.log  233ad4b3bcedb97758b362b7c883048a0ad09bfd6a7e3cbd2c7ac0c84cd64576
e6a_test.log  177e903f17a0f990ee38140b1063ecffec802f9f5b0e44fdb308c6fc8c7d13f6
e6a_valuta_prova.log  e6cd4b69f903d6f18165577dd67a91b36656b93560375f1505ba1a1d30730527
e6a_valuta_validazione.log  07b2e53f79c37269dbdf962916ae8ee0316d54800cdd0cd2f5a37b3bc5b57629
e6bis_addestra.log  cd72c7c7e4d727418218bee123258ef1ef74c92f4d9ba6306bce29e4972ed111
e6bis_risultati.json  6848731e9bc76f61ad0bca8449cfafc1d853582f4b23f15098c22fcde128b721
e6bis_test.log  12a84433f6a1bca00dfacaf87185ced80d944d0cc773a8c220198ebe65eec989
e6bis_valuta.log  9dfabdb3d77e9cb936c158b7ca505cfe708bad9eb78f6e6f0f0f636dbd605f2b
e7_posthoc.json  7b60446c1de9583011c78e3ae4ab39de8bcf00562859c202bb02f7cd9c11afe2
e7_posthoc.log  cd8be402d34bbeb05196b81779c91db6816c49460e9a4928c06117ae9ce533ef
e7_stadio1.json  a5d0bbc9efe3478b0411e2e63b16204bf803f1631f7d019b57d340fa9ff0035d
e7_stadio1.log  34c40d9dbeab070bcfca4447bc9c4b3293d06e0374dbd036bbcdb42be289785f
e8_curve.log  d18583ae33adbebc72201bdcf57b8537bb9b3a0bb0ce80c22e0ef45d6f9f62e2
e8_pilota.log  2881be18f81c5bc425915d125b8cbb899eb414fdade9501149433913ce414c55
e8_prova.log  47c068bd2dfbaa7f35198d16d2d91e1fbfe5e10f91fcddaf6c42189f70893771
e8_risultati.json  bf1d1f68d6bb9292e90d77e7be420042e3250823266afa83bc12995aacda5959
e8_soglie.json  c863a6e2f0aa489b7fdb3aceef32c930eed9f4dc0e20dfa3cdc198a4f33f5f73
e8_soglie.log  d70f7503fdb903e0ed816b9ce4516f9692aa29db5671f999b087d14415287a70
e8_test.log  2eaef6d7023569bf5fa7bfbf26e8133a133aaf7335ff31b3e3e84fdef92cf0ca
e8_test_curve.log  d5128cf7c0f8b94473f1a43862e21b4326c787983e19b876e5af71e6ab861942
e8_validazione.log  670468a911de92cd586627023e2b36d1c595e6b1f04cc16a0064c9d7230d6c87
e8bis_risultati.json  a91dfbfbcb6a7fb16a2be3ccd2056d83065c953b5844544315dd265968014dae
episodi_e5.json  e25a62cf4d8481a05ca9add71ed17d91abbf17d9491873e62630c247399ab2bc
episodi_e5.log  a36cdec5cce865e2f437ad5767167a36551b8e9b3b87e2b81ddbd92d15406d78
esito_e5_addestra.json  84a2b3a465702a8bf9875c1710f06d126b86e9551b0464b85b703958bad97078
esito_e6_addestra.json  8b17ec6e3179105a9a61e3457ccb52f7cb434dc483ab330e40649526a65905fc
esito_e6a_addestra.json  d94007b9e279f824c2d4276214558cb97bf7746356f430038abe5b36a57fed60
esito_e6bis_addestra.json  306ccc1ed2e7084c83cb92fa0653fe90a58c373b8739278cfb0ec20c09e15054
estrazione_pems04.json  5276d91480245624b59aa1d6459e967eddb484487c8006b984b88f327739b097
estrazione_pems04.log  6affc8ff2ee50572b80151787a6915ff80ac8ba924cad2e10997167a0980a1f4
estrazione_pems08.json  bc0d929a1fac60f7d05f9827a09eda7293401989ff70f5a1ca0501eccf900b9c
fattibilita_pems04.log  696688a8509799ad496dab018fcf8623b156b6727758b452de4c57ffc74d1f58
frequenze_classi.json  a14ea433dc695cf323b7ecf04aa13cba659f932e0268af1aff4807b8fab66c67
inserimento_griglia/  elenco:411d7b8b662b91940c295a547314d86073475c724c6f8aa7291e50ae9eb6afb8 (2164 file)
inserimento_griglia_672/  elenco:95ee474b6b0fb60e60151860eaba39fd7ba38e7dd9486f15498ee89625e476a7 (326 file)
inserimento_griglia_672_sessione/  elenco:0bd43ddb171acc6feb2c479b8089eff92065d2e873409b861d9a276de385d58c (27 file)
inserimento_griglia_ep2/  elenco:e1d9d299dbf4cf868704448a425941011ca19180dbd2b8dd41653034ba5e04fa (216 file)
inserimento_griglia_ep3/  elenco:c609a7a7322cfd9e490bdd46ab67ca1e09e4c13a07bbfd7a8c071bf4a6f994d9 (216 file)
inserimento_griglia_sessione/  elenco:8ec734945bbdfa53608329ae2539612107266bd94ded9b33ce16cfa83c9c5cdf (54 file)
lancio_3.log  8657d3dd5b9287d488bf3549c550f8947cfad679bc6c2167724dff2f18c6906a
lancio_E.log  ad683d2e754ee2859851ab56aa533aee83ce5ba11d38c5040382b6be6aecbc04
lancio_E1.log  d30af83605267b1088fea1550fc50eef20fca4e08b74bd0479dc9b9e48a6b877
lancio_E_griglia.log  c6b134486f06d8e0e75cd7e65dcd7b0dd706056f38aeff347b758553d13385cc
lancio_E_principale.log  55a29aed9e2d4c997a995ac34fc8b465940674d4b746c2bdeaa99cc125b565d3
lancio_F.log  91a5a4b9fc93c7694e4e7ea916edba6b5037a7dee3239831e0385055faeae985
lancio_F_griglia.log  f2aee2a5fa803dc0d2a41adff2b47dd8c1597a3604bc28f36c288ad044c620a7
lancio_F_principale.log  61ed0f8fe975c5d0282ecbd08d5f50c606953c5524e71e516a80934d77c79995
lancio_adeguatezza.log  c0137c24fdfb082df5d778ee8c7775d12bfb2ea5543e3f384b8221e24b1c6745
lancio_appaiato.log  acc73b95b1f57ba61c8eec1823acd3e5393ddcb6235cc6f0a334edecfb1a0c33
lancio_conferma.log  911704f1a09eda691af8ead3520e440cebfa0371861e1c05ebc4193d217d0d6d
lancio_conforme.log  8657d3dd5b9287d488bf3549c550f8947cfad679bc6c2167724dff2f18c6906a
lancio_e2.log  324446b3a03f8d725935d8866d6ad3d982b495bb654898ed222444be339e774f
lancio_f0.log  c633aabde16252040f7aec1768d6f8c574900b36fe60ad139ded6dcbb51db661
lancio_fase3.log  89b5968569c283cd83cfedb5002f62e9f0cf67adaed617d99c738498643d0186
lancio_fase3_isolata.log  377f3e0324fa4c17eb523be9bb9a1aa75436944d1e5560d0f2d6d47119c6463a
lancio_pems04.log  e260fd427e71e472a8de1be975b278bfb5e0da64aff170ac0c1e2a6332912a3b
lancio_refresh.log  c672d5433ec3ae642068aa6add046c21f80044a8f1f20ac0a95223c23f57db45
lancio_refresh_pems04.log  cbd038916ec23a7fac860b78c4d895395bcdada77925b80deb8966a80f60a6e2
lancio_sensibilita.log  04fb74ab5c4ed359e94cbf50d954386c389b04f2ce7e033d4f0d335cd962e28f
maschere/  elenco:8cf5828adc26ee1ea31cbae9b58e4182a158d78c1f1ae2ddf57e0088fcaf4fe7 (15 file)
pems04/  elenco:8c98395c631297b0478d6b7fcb9dce53374398b6755fa4cab086618f2e68cfc6 (145 file)
periodi_candidati.json  327b5dae1b1b5dac28539dd084bd08647ff735e33243a672bfbbcde523289bc9
periodi_candidati.log  4dcacfe7a64a8414675e9734495c8131e3af2cb58ec32e4c954086ce608bc54e
pesi/  elenco:60a70c0b926ec3c9f861916afc578177c3355fc5d77dc625d2e5cbaf8d0e9170 (9 file)
pesi_griglia/  elenco:4e096cc4da8fee5c81b82dd84ab12b703cb7f781d17d9d08b56915695cd9fad3 (10 file)
pesi_griglia_ep2/  elenco:9c39da8430225ac2971651b6d492a8a679f60830a97cae187fa8a98d435069cd (9 file)
pesi_griglia_ep3/  elenco:ff2f5589a09c790c5965cef51ef781a3214d928223970586bdfbf4550f423f24 (9 file)
pesi_pems04.log  e4ea15ea84c1163a7ac6a6317d305d550cbe54d6ed9017c3561f73306cbcc977
pesi_pems04/  elenco:67b14f582ee268d8633d726dc095d8fda9858499372acf33acd0c91e7ec683ee (4 file)
pesi_pems08/  elenco:8924a2903594bf18f83d6d1724e0d513a4ef0176ada10144e73f54935bc23645 (7 file)
predizioni/  elenco:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 (0 file)
predizioni_e2/  elenco:717ca0df4c4268e54f1e101c9896bf905fd14aff7432bd266d06cde4d88399a8 (326 file)
predizioni_e4/  elenco:075f73a9ed16d6dfccaf2d4815644998a3006489a8725609b5e960eac9bac59b (216 file)
predizioni_e5/  elenco:3e8a0cd319103d09f1fde92c7cc03a66e6ee455b499f862d7a9a8cdb85afe628 (162 file)
predizioni_e6/  elenco:f9c158bc77e4886aae0048ed5f93e6085051083b66ef03f540c2a0422396c595 (72 file)
predizioni_e6a/  elenco:d646eff70e5a11a4d642e5bb7d076593e7aff9ce12878e2247a91834fbd7e576 (72 file)
predizioni_e6bis/  elenco:7f8f67bd3ff9bca67aed0a7ad35e19117d0b385559a03c295897053c0adeeeca (36 file)
predizioni_e8/  elenco:4bb1e4757c6304c036409fe6a4ec871009ec422082d668f22e00b672fe8bc6fa (540 file)
predizioni_f0/  elenco:b75aa21e93416fdfd265bdd5d4772f0f0fd0505b0884bffa7ae8101627d90725 (110 file)
predizioni_fase3/  elenco:7b30345ba89682a3065873a93cc1dedc379304773d526d034a747f969be94e02 (871 file)
predizioni_fase3_672/  elenco:89ce4efbc1fb7c49e7c8f8cfdf43f45d7293cdc8a2af23f958dc66248ee742e0 (109 file)
predizioni_pems04/  elenco:723c48be015d8f0a98bd684a20396e6eb83d45790fcecd06be403be957b02d23 (75 file)
predizioni_refresh/  elenco:bd0c2d6f9750f1e590a58a7365d412a8a945be952a6851a17eb06459b9a4f3a7 (146 file)
predizioni_sensibilita_rho/  elenco:054302d087fde21361c2a44057a270ba5d5ef2c5389073ba60a701f324887211 (16 file)
predizioni_veterani_e3/  elenco:76abb16eafa4216bb4ea246b85e6dde992bd7fb839b51c0d9f6d3778d95be779 (540 file)
preflight.json  5cccf52ca549cc0c028b42ece0b4ae6590911087f590984518c60130f4c77460
preparazione_e5.json  9db38e20064dbf09c0e94b5ea56479a64397e6955fc26b9810ce91fcdb220772
preparazione_e5.log  35d512be4898089874b8bab63b541252aaa6c4c20f2f3a4329c597d0a261bb3d
prova_e3/  elenco:ebc6f110ba24e8ed69ca374bbbfb0d0753d08c0a18348d600038e17a6af3315c (2 file)
prova_fase3.log  202d1e8fa0011b78ac83b7b6b1116a320783aa0c9d1dadfabe5509b92bcc2aa7
provenienza_pems04.log  5d92682439b453f419b63d17ef394ec5fa0847b37c9e83545fdb20617ecff6dd
raccordo/  elenco:68b1369ae3360408297ee47dbf706ffee85f6c733215da19bf1baaf185a40007 (113 file)
raccordo_appaiato/  elenco:c927e6d21abd0f8b1e54c99020339ecb16848712ca1aae407e817f9615a8c852 (113 file)
raccordo_conferma/  elenco:24fa74d0949bc5f0a4a66a8eda5b8e37a64eaf0f38acd37480a03c96d741a715 (438 file)
registro/  elenco:ed199d6bb575e3a177e9b152f15fa2b6fbce0279d868b03ccc6ea9b0f2870993 (2762 file)
registro_collaudo/  elenco:ec5d6bccdb36a3bf063ea91d64f2f02ff7aeab2427a74a614b13fb14f168eb1b (57 file)
registro_prova/  elenco:dad5f46128885e250718a65502a317461abec9074e0b0f6f519ed01ca295d61d (108 file)
registro_ricostruzione/  elenco:43cd1168921f6b7f238f3cf931920a069604bcac54a6241276968de8f9f865a1 (108 file)
riconciliazione.json  a712b250f1b0995d7bba5085c608edd06dc1f5a4e02cb0a3be49acb60216c199
ricostruzione_A.log  4d00b022ee47babea7b0fe9afc2b7c2ccd7939c02b05466fb5083ce4d4d9c9ac
ricostruzione_C.log  4e467918c724458b75c05149d01c85ca3e3b4b84f5bd386c671817aacb13a34a
ricostruzione_F.log  708f431113b0b82e32c81b8d4ca429f6289f805450f8cbd3a621d1b663c20828
ricostruzione_P.log  254ed463e62951121a599496eddbfee7fcf886408b5b3840f727509189cba1ce
ricostruzione_e3bis.log  698e2c0fd76318f2778e2f1bd5ac5b1c83f56765e2b578f1ca155f5e01c1f426
ricostruzione_pems04_C.log  31b18e334d55d4aa9ce293345f7b9fbd544cb1186732741d7056a37861097e7b
ricostruzione_pems04_P.log  974047bd95156026159f9a2367b1105e7fd2dd4007a2b851cc9019d8c6e942fc
riselezione_rmon.json  3ecde8a95dabc8afe60393b38d198b40b3ad16c779baf6825eabfea69dea16b4
riselezione_rmon_test.json  b0a3838da268c076976c81f94375c177d2fa92ae94319b6c9f897ebbc973f64d
rmon_punti/  elenco:77376b1d65e3d50a3e8341180ef29bbef00815516fbe9f49ca33cc0d4b2f24e3 (442 file)
selezione_F/  elenco:953adeba4005018aa338b260a36aa0d5cde70625fdc414ee03d9c6f919d57807 (109 file)
selezione_F_e6/  elenco:6d85f97b1eb8311256fdb5787fc8630d2eedf58b5a8259f1103a34a837818757 (37 file)
selezione_F_e6a/  elenco:eac6f0bf25ba9af33ba6bca05911d0828363f3c30e2aa93833c03a74d0f40242 (37 file)
selezione_F_griglia/  elenco:49ba9a6167c7e3aa33a9ef334bdc5546b3b02ebb976081a4b07feb2d5d22227b (109 file)
selezione_F_non_conforme/  elenco:7022a4d8b11877b306feca48aab290cff3fab9833ecbef9abf8ffe46411c1c53 (16 file)
selezione_F_principale/  elenco:0c9795d7693eea4173063a29a58d1f98921c112a7a7e74be8482e5034578d425 (109 file)
sensibilita_rho_e2.json  e3dcf0d641e6be5e5652211c61291bd50acfe4e5f76ff67201024c19973e8078
stati_E1_e6_pems04/  elenco:3750a613e229b41bfe309c7b81b6e2a28c6584874cedaa02320136bdfe0d93f3 (36 file)
stati_E1_e6_pems08/  elenco:8c99e6892ef8f6f236585cc84cf39ffee611cb90882ebde3c30011b191116adc (36 file)
stati_E_e6_pems08/  elenco:0960c2983ff6bbc81d6169c794a7406e22f16f8523375657b0fe4ca2f91ff54b (36 file)
stati_completi/  elenco:9bde8ebfdcdd90b683fbb2f6f9cfe687108ea43f1887723a8298668c563f0d3f (12 file)
stati_completi_E1_costi_sessione/  elenco:81a2c9db982a10e91a9a768587eeb6178a57227d1b57e396886eed4d6687601e (9 file)
stati_completi_E1_inserimento_griglia/  elenco:6e4f549331b7b50f3920ffc8679259cfe271d9a219bb13e3f42320530502b1f7 (108 file)
stati_completi_E1_inserimento_griglia_ep2/  elenco:b122dc53829cbc3333fd76aec5a1abe7b6b9143d0690c98f621e825f23f303e3 (54 file)
stati_completi_E1_inserimento_griglia_ep3/  elenco:b122dc53829cbc3333fd76aec5a1abe7b6b9143d0690c98f621e825f23f303e3 (54 file)
stati_completi_E1_rho005_inserimento_griglia/  elenco:9ff1d1b31d1f1afe1c79a926789772ec08f7c08ff85244b3cffc2711a5ea185e (4 file)
stati_completi_E1_rho030_inserimento_griglia/  elenco:9ff1d1b31d1f1afe1c79a926789772ec08f7c08ff85244b3cffc2711a5ea185e (4 file)
stati_completi_E_inserimento_griglia/  elenco:6c083287e04578d3d8413d5bc1476aca7a1a1b8a2bdcc084f4aa61421b291d1f (108 file)
stati_completi_E_inserimento_principale/  elenco:6c083287e04578d3d8413d5bc1476aca7a1a1b8a2bdcc084f4aa61421b291d1f (108 file)
stati_completi_adeguatezza_E1/  elenco:7f14a31b4263cefb4305469c0604c6892054c71286b1e8582c2b4034a2fbae52 (2 file)
stati_completi_collaudo/  elenco:eb4ecada1873b98a38ab6ef32a5afe90e769d9d1b7fcdc48886554498914b723 (2 file)
stati_completi_collaudo_griglia/  elenco:87d2f112bafeb09b1b3cd998330ab4ef1bd402c1206a183096ab5892893670cb (1 file)
stati_completi_inserimento_griglia/  elenco:014c9a09a560176ed9eccb7da99959950c1c148556c9d42dd2c0719883446cb8 (648 file)
stati_completi_inserimento_griglia_672/  elenco:46c9a667619194df2f0806e0019c1af72669d40d01989c93abd9f7d2b53f275b (108 file)
stati_completi_inserimento_griglia_672_sessione/  elenco:14ecc4b5382329a059ab73344040100e40b7fdf79a3f52b99b35328ed1396c1b (9 file)
stati_completi_inserimento_griglia_ep2/  elenco:4f674dc51cd1423f8a4d24dfc616cae540abb19c3136507869a961e6594522d0 (108 file)
stati_completi_inserimento_griglia_ep3/  elenco:4f674dc51cd1423f8a4d24dfc616cae540abb19c3136507869a961e6594522d0 (108 file)
stati_completi_inserimento_griglia_sessione/  elenco:86833f76deb201b63ecf394555cf35572b418ad71b1f06b8b3aa164420763089 (18 file)
stati_completi_rmon_punti/  elenco:a07aad663e2518c90d28408a7c85667189b0a0902b9a2ea221e42c9365f5f96c (34 file)
stati_e6_costi_E1_e6_pems08/  elenco:af0e4a95b2cb3f005a8400191590c4e23b7b0d5a4f548037a7a998aa2e73aee3 (3 file)
stati_e6_costi_e6_pems08/  elenco:36325e158ad2f2ba7f186bb627e2994775b12c8974fd3c511121074d37f3e905 (9 file)
stati_e6_costi_e6_pems08_672/  elenco:825ba8c2eb6e2754b8714d1c25a229205c1507095ebff6487a879a730cd7a14e (3 file)
stati_e6_pems08/  elenco:184ed8d22bd5af5b67d693e328ac3aa28e14577d323ca59808c8e5fcc689efcb (108 file)
stati_e6_pems08_672/  elenco:14e6824ff2927c63fa3d21a6d35ecc6b2a406204be3dfb6c543e332746daa34b (36 file)
stati_e6_pilota/  elenco:efc889482343f365e5d9e053c4afcc10eddc198c911d1700dce5c81985312aef (1 file)
stati_e6_sessione_E1_e6_pems08/  elenco:af0e4a95b2cb3f005a8400191590c4e23b7b0d5a4f548037a7a998aa2e73aee3 (3 file)
stati_e6_sessione_e6_pems08/  elenco:36325e158ad2f2ba7f186bb627e2994775b12c8974fd3c511121074d37f3e905 (9 file)
stati_e6_sessione_e6_pems08_672/  elenco:825ba8c2eb6e2754b8714d1c25a229205c1507095ebff6487a879a730cd7a14e (3 file)
stati_iniziali/  elenco:df59000414648d38bf0a9c8964aa15b2a888067d837d4c84e6f6a02577d67714 (93 file)
stati_pems04/  elenco:f3fb00ef2d11d4e257bdc26c2425308f1cf84fa3392d2a85efa6398bd4e98226 (72 file)
stati_prova_e3/  elenco:19db72e905fa9997b97f990fa8c41cb23e22f8c4a2f926e95022cc0c09c9caa9 (2 file)
stati_prova_inserimento/  elenco:871a1134bcbfd34573303fc817f14a70d96df7c5d43f94b3cb952ca1ce7ea5ca (4 file)
verifica_appaiamento.log  77f69befb2b12fc8867e330958d5295275f7d7cac1afeeb37ca80666599a75b8
veterani_e3.json  1e13e794cbf2a3bab5332c2c761a161319599934c252c6df0ac48d4bded81643
```
