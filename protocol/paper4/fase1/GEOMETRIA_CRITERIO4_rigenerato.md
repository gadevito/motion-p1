# Paper 4, fase 1 — criterio 4 (controllo negativo della geometria) rieseguito sui CSV conservati

Generato da `analisi/p4_fase1_criterio4.py` il 2026-11-06 14:43 UTC (non modificare a mano). Nessun addestramento: i vantaggi per seme vengono dai CSV conservati in `../OR3_vecchia_storia/replication/geo` (bracci `gwn_none` e `gwn_fixed` nello stesso file, come in `geometria_criteri.vantaggio`), le covariate da `geo_sweep/covariate_*.csv`. Accoppiamento `comp_q<xy>` ↔ `neg_rand_q<xy>` della stessa citta' (`make_geo_sweep.py`); fino al 6/11/2026 lo script cercava «knn» nel nome del grafo e non trovava coppie. Intervallo = t a 5 semi (2,776·sd/√5), come nello script. Confronto con le Tabelle 34-35 del deliverable UC-04 v1 (pag. 95) e con la terza esecuzione descritta nel testo (pag. 96). **Solo registro: nessun numero del Paper 4.**

| citta' | coppia | tabella del deliverable | grandezza | rigenerato | deliverable | esito |
|---|---|---|---|---:|---:|---|
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | vantaggio grafo vero (%) | +1.96 | +1.96 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | sd grafo vero | +0.61 | +0.61 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | arco medio vero (m) | +42.3 | +42.3 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | vantaggio randomizzato (%) | +2.09 | +2.09 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | sd randomizzato | +0.48 | +0.48 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | arco medio randomizzato (m) | +390.7 | +390.7 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | grado medio | +5.23 | +5.23 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | differenza appaiata (punti) | -0.12 | -0.12 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | IC inferiore | -0.44 | -0.44 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | IC superiore | +0.20 | +0.20 | uguale |
| madrid | comp_q2080 ↔ neg_rand_q2080 | 34 (prima esecuzione, Madrid, 42,3 m) | segni positivi su 5 | +2 | +2 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | vantaggio grafo vero (%) | +8.75 | +8.75 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | sd grafo vero | +0.68 | +0.68 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | arco medio vero (m) | +56.3 | +56.3 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | vantaggio randomizzato (%) | +8.93 | +8.93 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | sd randomizzato | +0.86 | +0.86 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | arco medio randomizzato (m) | +494.3 | +494.3 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | grado medio | +5.29 | — | assente nel deliverable |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | differenza appaiata (punti) | -0.18 | -0.18 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | IC inferiore | -0.47 | -0.47 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | IC superiore | +0.10 | +0.10 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | segni positivi su 5 | +1 | +1 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, vero, s0 | +9.72 | +9.72 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, vero, s1 | +9.13 | +9.13 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, vero, s2 | +8.32 | +8.32 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, vero, s3 | +8.52 | +8.52 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, vero, s4 | +8.05 | +8.05 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, randomizzato, s0 | +9.98 | +9.98 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, randomizzato, s1 | +9.62 | +9.62 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, randomizzato, s2 | +8.35 | +8.35 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, randomizzato, s3 | +8.78 | +8.78 | uguale |
| madrid | comp_q5020 ↔ neg_rand_q5020 | 35 (seconda esecuzione, Madrid, 56,3 m) | per seme, randomizzato, s4 | +7.94 | +7.94 | uguale |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | vantaggio grafo vero (%) | +3.09 | +3.09 | uguale |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | sd grafo vero | +9.34 | — | assente nel deliverable |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | arco medio vero (m) | +396.5 | +396.0 | diversa (deliverable +396.0) |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | vantaggio randomizzato (%) | +2.73 | — | assente nel deliverable |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | sd randomizzato | +8.20 | — | assente nel deliverable |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | arco medio randomizzato (m) | +3377.5 | — | assente nel deliverable |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | grado medio | +5.13 | — | assente nel deliverable |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | differenza appaiata (punti) | +0.36 | +0.36 | uguale |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | IC inferiore | -9.11 | -9.11 | uguale |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | IC superiore | +9.83 | +9.83 | uguale |
| melbourne | comp_q5080 ↔ neg_rand_q5080 | testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella) | segni positivi su 5 | +2 | — | assente nel deliverable |

## Esiti del criterio 4 (regola dello script)

- madrid comp_q2080: valori per seme vero = 1.30 / 2.27 / 1.37 / 2.15 / 2.72 (assenti nel deliverable)
- madrid comp_q2080: valori per seme randomizzato = 1.46 / 2.06 / 1.86 / 2.35 / 2.71 (assenti nel deliverable)
- madrid comp_q2080 ↔ neg_rand_q2080: differenza appaiata -0.12 [-0.44; +0.20], margine 1.96 punti → REFUTAZIONE (margine sotto i due punti: non conclusiva)
- madrid neg_rand_q5020: riga assente in covariate_madrid.csv (lo script attuale genera un solo controllo per citta'); arco medio calcolato dal pkl `geo_sweep/madrid_neg_rand_q5020.pkl`
- madrid comp_q5020 ↔ neg_rand_q5020: differenza appaiata -0.18 [-0.47; +0.10], margine 8.75 punti → REFUTAZIONE
- melbourne comp_q5080: valori per seme vero = 1.48 / -5.01 / -3.07 / 18.67 / 3.40 (assenti nel deliverable)
- melbourne comp_q5080: valori per seme randomizzato = -7.28 / 1.91 / -2.91 / 11.23 / 10.71 (assenti nel deliverable)
- melbourne comp_q5080 ↔ neg_rand_q5080: differenza appaiata +0.36 [-9.11; +9.83], margine 3.09 punti → non distinguibili

Configurazioni del braccio principale senza controllo randomizzato (nessun CSV `neg_rand_q<xy>`): madrid comp_q2020, madrid comp_q2050, madrid comp_q5050, madrid comp_q5080, madrid comp_q8020, madrid comp_q8050, madrid comp_q8080, melbourne comp_q2020, melbourne comp_q2050, melbourne comp_q2080, melbourne comp_q5020, melbourne comp_q5050, melbourne comp_q8020, melbourne comp_q8050, melbourne comp_q8080. Il deliverable ne riporta tre (pag. 95-96), tutte ritrovate.

## Uscita integrale di `analisi/geometria_criteri.py` (dopo la correzione)

```
$ /Users/gabrieledevito/Personal/MOTION/deliverables/repo-paper4/analisi/geometria_criteri.py --geo-dir ../OR3_vecchia_storia/replication/geo --covariate geo_sweep --semi 5
============================================================================================
TABELLA 30 - braccio principale: vantaggio per spaziatura (braccio a grafo fisso)
============================================================================================
grafo                  citta         N  arco medio          vantaggio segni
comp_q2080             madrid       99       42.3 m     +1.96% ± 0.61  5/5
comp_q2050             madrid       99       49.7 m     +3.31% ± 0.56  5/5
comp_q8020             madrid       99       55.3 m     +7.34% ± 0.95  5/5
comp_q5020             madrid       99       56.3 m     +8.75% ± 0.68  5/5
comp_q8050             madrid       99       60.2 m     +5.81% ± 1.03  5/5
comp_q5050             madrid       99       68.4 m     +6.95% ± 2.15  5/5
comp_q8080             madrid       99       73.3 m     +6.48% ± 0.26  5/5
comp_q5080             madrid       99       88.2 m     +3.37% ± 0.27  5/5
comp_q8050             melbourne    99       94.7 m     +2.14% ± 3.41  4/5
comp_q8020             melbourne    99      127.1 m     +3.14% ± 2.42  5/5
comp_q2080             melbourne    99      383.1 m     +3.05% ± 2.29  5/5
comp_q5080             melbourne    99      396.5 m     +3.09% ± 9.34  3/5

============================================================================================
TABELLA 31 - i cinque criteri
============================================================================================
1 tendenza          NON sostenuto    pendenza +0.00209 %/m, IC [-0.01240; +0.01657], p = 0.784
                                      differenza fra estremi -1.13 punti (rilevabilita 4.00, progettuale 3.00)
                                      senza termine di citta': -0.00664 %/m, p = 0.245  <-- il SEGNO non e' robusto alla specificazione
3 trasferibilita'   compatibile, FRAGILE termine additivo di citta' p = 0.143
                                      con dodici punti il modello e' scarsamente identificato: e' l'esito piu' fragile dei cinque

4 controllo negativo  madrid comp_q2080 contro neg_rand_q2080
                       vero  +1.96% ± 0.61 (arco 42.3 m) | casuale  +2.09% ± 0.48 (arco 390.7 m)
                       differenza appaiata -0.12 punti, IC [-0.44; +0.20], segni 2/5
                       margine disponibile 1.96 punti -> REFUTAZIONE
                       ATTENZIONE: con margine sotto i due punti l'esecuzione non e'
                       conclusiva, qualunque sia la differenza (§7.3, sesto caso)

4 controllo negativo  madrid comp_q5020 contro neg_rand_q5020
                       vero  +8.75% ± 0.68 (arco 56.3 m) | casuale  +8.93% ± 0.86 (arco nan m)
                       differenza appaiata -0.18 punti, IC [-0.47; +0.10], segni 1/5
                       margine disponibile 8.75 punti -> REFUTAZIONE

4 controllo negativo  melbourne comp_q5080 contro neg_rand_q5080
                       vero  +3.09% ± 9.34 (arco 396.5 m) | casuale  +2.73% ± 8.20 (arco 3377.5 m)
                       differenza appaiata +0.36 punti, IC [-9.11; +9.83], segni 2/5
                       margine disponibile 3.09 punti -> non distinguibili

Nota sul criterio 4. Il grafo randomizzato NON e' «lo stesso grafo senza
geometria»: ha arco medio molto maggiore e proprieta' di mescolamento diverse.
Cio' che l'esito sostiene e' che a parita' di grado la connettivita' a lungo
raggio funzioni almeno quanto quella locale — conclusione piu' stretta e piu'
difendibile di «la prossimita' e' irrilevante».

La conclusione poggia sul SOLO criterio 4, che ha potere discriminante misurato.
Gli altri quattro sono non sostenuti o fragili e non si aggregano in una
conclusione positiva: assenza di evidenza su piu' criteri non e' dimostrazione.

[codice di uscita 0]
```

## Ingressi (impronte sha256, 16 esadecimali)

- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q2080_s0.csv` `3a796d99174dffa5`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q2080_s1.csv` `f4a941b24be4072a`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q2080_s2.csv` `c47bacf6c0d07f6b`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q2080_s3.csv` `df1b3ec2df45e445`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q2080_s4.csv` `220c926f44c1cc0c`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q5020_s0.csv` `721215942308e1e6`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q5020_s1.csv` `5c2da404f4bb4969`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q5020_s2.csv` `bdb5700c486786b5`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q5020_s3.csv` `4265f9e89535139d`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_comp_q5020_s4.csv` `713b8c4ded6ebd69`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q2080_s0.csv` `65762c768a20ccbf`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q2080_s1.csv` `3fad18266b713d9d`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q2080_s2.csv` `440e5a4b9f6ead10`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q2080_s3.csv` `f65dbf13da412aef`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q2080_s4.csv` `fda232cf733359f0`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q5020_s0.csv` `d38461b0dfdf466f`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q5020_s1.csv` `a95e0b8e36ba6722`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q5020_s2.csv` `55838c057cbde509`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q5020_s3.csv` `d442623baecf2343`
- `../OR3_vecchia_storia/replication/geo/geo_madrid_neg_rand_q5020_s4.csv` `09f79c3d25752d4c`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_comp_q5080_s0.csv` `a59223420fea3395`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_comp_q5080_s1.csv` `acdcd4f5ee4159ca`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_comp_q5080_s2.csv` `6375442dd3495c9c`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_comp_q5080_s3.csv` `f1161f04e80f3031`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_comp_q5080_s4.csv` `060b3af6a648808d`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_neg_rand_q5080_s0.csv` `fbec820b202202c6`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_neg_rand_q5080_s1.csv` `2110e533adeceb23`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_neg_rand_q5080_s2.csv` `87adef077968cd2a`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_neg_rand_q5080_s3.csv` `2ae90122dc10aeca`
- `../OR3_vecchia_storia/replication/geo/geo_melbourne_neg_rand_q5080_s4.csv` `bad76786d96b504b`
- `geo_sweep/covariate_madrid.csv` `e3eb1b162ee326bb`
- `geo_sweep/covariate_melbourne.csv` `19175872e98db701`
- `geo_sweep/madrid_neg_rand_q5020.pkl` `29384d7e8d7f1e23`

Script: `analisi/geometria_criteri.py` `594a8180d6443b37`; `analisi/p4_fase1_criterio4.py` `531f121878d53613`.
