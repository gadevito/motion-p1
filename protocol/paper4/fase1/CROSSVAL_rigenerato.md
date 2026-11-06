# Paper 4, fase 1 — validazione co-localizzata (`t4c_crossval.py`) rigenerata: base, `--exclude-empty`, `--max-dist 30`

Generato da `analisi/p4_fase1_crossval.py` il 2026-11-06 14:13 UTC (non modificare a mano). Comandi di `README.it.md` §7.11 eseguiti in `/Users/gabrieledevito/Personal/MOTION/deliverables/OR3/data_collection`; CSV e uscite a video in `protocol/paper4/fase1/crossval/`. Confronto con le Tabelle 64-65 del deliverable UC-04 v1 (pag. 127-128) e con la sensibilita' al raggio (testo, pag. 127). Tabella 66 (rapporti fra correlazioni) non rigenerata: nessuno script la calcola. **Solo registro.**

## CSV rigenerati

| file | righe (coppie) | sha256 |
|---|---:|---|
| `crossval_results.csv` | 404 | `57e7b139cca39693` |
| `crossval_results_noempty.csv` | 404 | `d958ff99f618437f` |
| `crossval_results_d30.csv` | 184 | `6c2f37dbb4c20d89` |

`crossval_results.csv` gia' presente in `OR3/data_collection/` (sha256 `57e7b139cca39693`, 404 coppie): **identico** al rigenerato.

## Confronto con il deliverable

| tabella | grandezza | variante | rigenerato (dall'uscita a video) | deliverable |
|---|---|---|---|---|
| 64 | coppie con correlazione definibile | base | 399 | 399 |
| 64 | correlazione istantanea, mediana | base | 0.041 | 0.04 (testo: 0.0405) |
| 64 | correlazione del profilo settimanale medio, mediana | base | 0.130 | 0.13 |
| 64 | concordanza di classe (3 classi) | base | 44.0% | 44% |
| 64 | richiamo giallo+rosso | base | 16.7% | 16,7% |
| 64 | distribuzione classi, ricostruito (spire) | base | 85.4% / 11.4% / 3.2% | 85% / 11% / 3% |
| 64 | distribuzione classi, misurato (sonde) | base | 42.7% / 44.2% / 13.1% | 43% / 44% / 13% |
| testo p. 127 | raggio 30 m: mediana e coppie | d30 | 181 | 0.045 | 0,0452 su 181 coppie |
| 65 | r ricostruito, insieme completo | base | Pearson +0.0405 | Spearman +0.0397 | coppie 399 | +0,0397 |
| 65 | occupazione grezza, insieme completo | base | Pearson -0.1081 | Spearman -0.1252 | coppie 399 | -0,1252 |
| 65 | flusso grezzo, insieme completo | base | Pearson -0.1386 | Spearman -0.1410 | coppie 399 | -0,1410 |
| 65 | r ricostruito, sole celle trafficate | noempty | Pearson +0.0117 | Spearman +0.0157 | coppie 276 | +0,0157 (276 coppie) |
| 65 | occupazione grezza, sole celle trafficate | noempty | Pearson -0.0708 | Spearman -0.0689 | coppie 276 | -0,0689 |
| 65 | flusso grezzo, sole celle trafficate | noempty | Pearson -0.0672 | Spearman -0.0712 | coppie 276 | -0,0712 |

Nota: l'uscita a video e' l'unico posto in cui lo script stampa gli indicatori (il CSV contiene solo le coppie `gomo_sensor, t4c_segment, dist_m, corr`); i valori «non estratti» vanno letti nelle uscite integrali qui sotto.

## Uscita integrale — base

```
GO-MO: 432 sensori 2021 (432 con coordinate)
t4c: 8,357 segmenti geolocalizzati
coppie sensore-segmento entro 120 m: 404 (distanza mediana 33 m)
t4c: 1,701,502 righe misurate | 10,464 quarti d'ora distinti (giu-dic 2021)
  scostamento  -8 ( -120 min): mediana +0.0216
  scostamento  -7 ( -105 min): mediana +0.0233
  scostamento  -6 (  -90 min): mediana +0.0242
  scostamento  -5 (  -75 min): mediana +0.0262
  scostamento  -4 (  -60 min): mediana +0.0282
  scostamento  -3 (  -45 min): mediana +0.0287
  scostamento  -2 (  -30 min): mediana +0.0288
  scostamento  -1 (  -15 min): mediana +0.0302
  scostamento  +0 (   +0 min): mediana +0.0360
  scostamento  +1 (  +15 min): mediana +0.0405
  scostamento  +2 (  +30 min): mediana +0.0348
  scostamento  +3 (  +45 min): mediana +0.0299
  scostamento  +4 (  +60 min): mediana +0.0290
  scostamento  +5 (  +75 min): mediana +0.0256
  scostamento  +6 (  +90 min): mediana +0.0224
  scostamento  +7 ( +105 min): mediana +0.0218
  scostamento  +8 ( +120 min): mediana +0.0199

scostamento temporale ottimo: 1 quarti d'ora (+15 min) -> probabile differenza di fuso/convenzione

=== correlazione di rango: sonde contro ciascun ingresso grezzo ===
  [maschera] celle vuote: 10,105,137 (66.8%) | applicata: False
  r ricostruito    scost. ottimo +1 ( +15 min) | Pearson +0.0405 | Spearman +0.0397 | coppie 399
  occupazione      scost. ottimo +1 ( +15 min) | Pearson -0.1081 | Spearman -0.1252 | coppie 399
  flusso           scost. ottimo +1 ( +15 min) | Pearson -0.1386 | Spearman -0.1410 | coppie 399

=== VALIDAZIONE INCROCIATA (ricostruito vs misurato) ===
coppie valide: 399 | correlazione r: mediana 0.041, media 0.063
concordanza di classe (3 classi): 44.0%
recall della congestione ricostruita (giallo+rosso): 16.7% (quanta congestione misurata le spire 'vedono')

distribuzione classi sui punti allineati:
  ricostruito (spire) verde/giallo/rosso = 85.4% / 11.4% / 3.2%
  misurato   (sonde)  verde/giallo/rosso = 42.7% / 44.2% / 13.1%

correlazione del profilo settimanale medio (672 momenti-tipo): mediana 0.130, media 0.170  (su 400 coppie)
  -> alta = il proxy coglie il pattern tipico anche se non l'istante; bassa = non coglie nemmeno la stagionalita'

salvato -> /Users/gabrieledevito/Personal/MOTION/deliverables/repo-paper4/protocol/paper4/fase1/crossval/crossval_results.csv
```

## Uscita integrale — noempty

```
[exclude-empty] celle con r=1.0 rimosse: 10,111,597 su 13,112,545 (77.1%)
GO-MO: 432 sensori 2021 (432 con coordinate)
t4c: 8,357 segmenti geolocalizzati
coppie sensore-segmento entro 120 m: 404 (distanza mediana 33 m)
t4c: 1,701,502 righe misurate | 10,464 quarti d'ora distinti (giu-dic 2021)
  scostamento  -8 ( -120 min): mediana -0.0136
  scostamento  -7 ( -105 min): mediana -0.0089
  scostamento  -6 (  -90 min): mediana -0.0065
  scostamento  -5 (  -75 min): mediana -0.0057
  scostamento  -4 (  -60 min): mediana -0.0086
  scostamento  -3 (  -45 min): mediana -0.0060
  scostamento  -2 (  -30 min): mediana -0.0090
  scostamento  -1 (  -15 min): mediana -0.0024
  scostamento  +0 (   +0 min): mediana +0.0038
  scostamento  +1 (  +15 min): mediana +0.0114
  scostamento  +2 (  +30 min): mediana +0.0030
  scostamento  +3 (  +45 min): mediana -0.0048
  scostamento  +4 (  +60 min): mediana -0.0015
  scostamento  +5 (  +75 min): mediana -0.0070
  scostamento  +6 (  +90 min): mediana -0.0073
  scostamento  +7 ( +105 min): mediana -0.0120
  scostamento  +8 ( +120 min): mediana -0.0137

scostamento temporale ottimo: 1 quarti d'ora (+15 min) -> probabile differenza di fuso/convenzione

=== correlazione di rango: sonde contro ciascun ingresso grezzo ===
  [maschera] celle vuote: 10,105,137 (66.8%) | applicata: True
  r ricostruito    scost. ottimo +1 ( +15 min) | Pearson +0.0117 | Spearman +0.0157 | coppie 276
  occupazione      scost. ottimo +1 ( +15 min) | Pearson -0.0708 | Spearman -0.0689 | coppie 276
  flusso           scost. ottimo +1 ( +15 min) | Pearson -0.0672 | Spearman -0.0712 | coppie 276

=== VALIDAZIONE INCROCIATA (ricostruito vs misurato) ===
coppie valide: 275 | correlazione r: mediana 0.011, media 0.025
concordanza di classe (3 classi): 39.0%
recall della congestione ricostruita (giallo+rosso): 54.3% (quanta congestione misurata le spire 'vedono')

distribuzione classi sui punti allineati:
  ricostruito (spire) verde/giallo/rosso = 45.7% / 42.4% / 11.9%
  misurato   (sonde)  verde/giallo/rosso = 34.3% / 50.2% / 15.5%

correlazione del profilo settimanale medio (672 momenti-tipo): mediana -0.103, media -0.098  (su 315 coppie)
  -> alta = il proxy coglie il pattern tipico anche se non l'istante; bassa = non coglie nemmeno la stagionalita'

salvato -> /Users/gabrieledevito/Personal/MOTION/deliverables/repo-paper4/protocol/paper4/fase1/crossval/crossval_results_noempty.csv
```

## Uscita integrale — d30

```
GO-MO: 432 sensori 2021 (432 con coordinate)
t4c: 8,357 segmenti geolocalizzati
coppie sensore-segmento entro 30 m: 184 (distanza mediana 18 m)
t4c: 917,457 righe misurate | 10,464 quarti d'ora distinti (giu-dic 2021)
  scostamento  -8 ( -120 min): mediana +0.0229
  scostamento  -7 ( -105 min): mediana +0.0212
  scostamento  -6 (  -90 min): mediana +0.0227
  scostamento  -5 (  -75 min): mediana +0.0258
  scostamento  -4 (  -60 min): mediana +0.0307
  scostamento  -3 (  -45 min): mediana +0.0272
  scostamento  -2 (  -30 min): mediana +0.0316
  scostamento  -1 (  -15 min): mediana +0.0306
  scostamento  +0 (   +0 min): mediana +0.0369
  scostamento  +1 (  +15 min): mediana +0.0452
  scostamento  +2 (  +30 min): mediana +0.0350
  scostamento  +3 (  +45 min): mediana +0.0299
  scostamento  +4 (  +60 min): mediana +0.0282
  scostamento  +5 (  +75 min): mediana +0.0244
  scostamento  +6 (  +90 min): mediana +0.0226
  scostamento  +7 ( +105 min): mediana +0.0214
  scostamento  +8 ( +120 min): mediana +0.0185

scostamento temporale ottimo: 1 quarti d'ora (+15 min) -> probabile differenza di fuso/convenzione

=== correlazione di rango: sonde contro ciascun ingresso grezzo ===
  [maschera] celle vuote: 10,105,137 (66.8%) | applicata: False
  r ricostruito    scost. ottimo +1 ( +15 min) | Pearson +0.0452 | Spearman +0.0463 | coppie 181
  occupazione      scost. ottimo +1 ( +15 min) | Pearson -0.1238 | Spearman -0.1447 | coppie 181
  flusso           scost. ottimo +1 ( +15 min) | Pearson -0.1482 | Spearman -0.1462 | coppie 181

=== VALIDAZIONE INCROCIATA (ricostruito vs misurato) ===
coppie valide: 181 | correlazione r: mediana 0.045, media 0.066
concordanza di classe (3 classi): 42.9%
recall della congestione ricostruita (giallo+rosso): 18.7% (quanta congestione misurata le spire 'vedono')

distribuzione classi sui punti allineati:
  ricostruito (spire) verde/giallo/rosso = 83.6% / 13.5% / 2.9%
  misurato   (sonde)  verde/giallo/rosso = 40.8% / 46.1% / 13.0%

correlazione del profilo settimanale medio (672 momenti-tipo): mediana 0.130, media 0.174  (su 181 coppie)
  -> alta = il proxy coglie il pattern tipico anche se non l'istante; bassa = non coglie nemmeno la stagionalita'

salvato -> /Users/gabrieledevito/Personal/MOTION/deliverables/repo-paper4/protocol/paper4/fase1/crossval/crossval_results_d30.csv
```

## Ingressi (impronte sha256, 16 esadecimali)

- `go-mo/gomo/targets_2021_urb_d8.npz` `b5db8261fd295077`
- `go-mo/gomo/traffic_sensors.csv` `63cf54c05e4b380e`
- `traffic4cast/MADRID_2022/road_graph_nodes_osm.parquet` `26045de9b9b22b68`
- `traffic4cast/MADRID_2022/road_graph_edges_district.parquet` `f2027534873a5715`
- `traffic4cast/MADRID_2022/speed_classes/madrid/ (109 file)` `c783c72aea71c16c`
- `t4c_crossval.py` `0320018785d5658d`

Script: `analisi/p4_fase1_crossval.py` `14386205ee2698d1`.
