# Congelamento — E7, copertura e adattamento (stadio 1)

**Congelato il 2026-10-07**, commit `5ddf4770e863`. Pre-registrazione `protocol/E7.md` (impronta `07db021e85236235`), firmata al commit `faf27f2e0c15a83f` prima di eseguire lo stadio 1. **Ogni numero e' calcolato da `genera_congelamento_e7.py`** da `e7_stadio1.json`; la decisione sullo stadio 2a e' quella della regola pre-registrata.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| stadio 1 | a costo zero, dai 162 npz di E5 (nessun modello eseguito); N da `e4_scelta_gated.json` (impronta `81e47f64f3d63b3b`), k da `e5_k_secondaria.json` (impronta `395d17a4f05462ea`); v₇ dalle maschere con `celle_valide` |
| ricampionamento | gruppi 4000 repliche (partizioni × semi × nodi del gruppo), ρ 2000 repliche sulle unita' (partizione, nodo); seme 20261008; soglia di gruppo 10 nodi |
| stadio 2a | **NON eseguito**: la regola pre-registrata non lo richiede (sotto) |

## 2. Gruppi sotto e sopra la soglia N (nodi per cella)

| citta' | ep. | N | sotto N | Δ₁ sotto | Δ₁ sopra | Δ₂ sotto | Δ₂ sopra | Δ₃ sotto | Δ₃ sopra |
|---|---|---|---|---|---|---|---|---|---|
| Madrid | 1 | 77 | 0 | n.d. (0 nodi) | -0.031 [-0.036, -0.026] * | n.d. (0 nodi) | -0.011 [-0.020, -0.002] * | n.d. (0 nodi) | -0.011 [-0.021, -0.002] * |
| Madrid | 2 | 77 | 0 | n.d. (0 nodi) | -0.035 [-0.042, -0.029] * | n.d. (0 nodi) | -0.012 [-0.020, -0.004] * | n.d. (0 nodi) | -0.012 [-0.020, -0.004] * |
| Madrid | 3 | 77 | 0 | n.d. (0 nodi) | -0.036 [-0.043, -0.029] * | n.d. (0 nodi) | +0.011 [-0.004, +0.026] | n.d. (0 nodi) | +0.011 [-0.004, +0.026] |
| Londra | 1 | 154 | 99 | -0.030 [-0.037, -0.024] * | -0.032 [-0.041, -0.024] * | +0.045 [+0.031, +0.060] * | +0.007 [-0.006, +0.019] | -0.004 [-0.009, +0.001] | +0.001 [-0.007, +0.011] |
| Londra | 2 | 154 | 70 | -0.030 [-0.037, -0.022] * | -0.021 [-0.027, -0.014] * | +0.017 [+0.000, +0.034] * | -0.001 [-0.012, +0.009] | -0.012 [-0.018, -0.005] * | -0.008 [-0.013, -0.003] * |
| Londra | 3 | 154 | 36 | -0.032 [-0.043, -0.021] * | -0.030 [-0.035, -0.025] * | +0.004 [-0.011, +0.020] | -0.009 [-0.018, -0.001] * | -0.011 [-0.018, -0.003] * | -0.010 [-0.015, -0.004] * |
| Melbourne | 1 | 154 | 0 | n.d. (0 nodi) | -0.036 [-0.043, -0.029] * | n.d. (0 nodi) | -0.020 [-0.029, -0.010] * | n.d. (0 nodi) | -0.020 [-0.027, -0.013] * |
| Melbourne | 2 | 154 | 68 | -0.029 [-0.037, -0.021] * | -0.012 [-0.029, +0.004] | +0.025 [+0.009, +0.043] * | +0.013 [-0.006, +0.034] | +0.004 [-0.006, +0.015] | -0.006 [-0.018, +0.006] |
| Melbourne | 3 | 154 | 1 | n.d. (1 nodi) | -0.039 [-0.046, -0.033] * | n.d. (1 nodi) | -0.022 [-0.030, -0.014] * | n.d. (1 nodi) | -0.016 [-0.021, -0.011] * |

\* intervallo che esclude lo zero. n.d. = gruppo con meno di 10 nodi per cella (soglia pre-registrata).

**Ipotesi pre-registrata** («l'adattamento su una settimana paga anche per i nodi sotto soglia»): **VALE** nei 4 gruppi sotto soglia esistenti (Londra ep. 1 -0.030, Londra ep. 2 -0.030, Londra ep. 3 -0.032, Melbourne ep. 2 -0.029).

## 3. Correlazioni di rango (segno atteso negativo)

| citta' | ep. | ρ(v, Δ₁) | ρ(v₇, Δ₁) | ρ(v, Δ₂) | ρ(v₇, Δ₂) | ρ(v, Δ₃) | ρ(v₇, Δ₃) |
|---|---|---|---|---|---|---|---|
| Madrid | 1 | -0.07 [-0.18, +0.04] | -0.08 [-0.19, +0.03] | -0.05 [-0.16, +0.05] | -0.05 [-0.16, +0.05] | -0.05 [-0.15, +0.05] | -0.05 [-0.15, +0.05] |
| Madrid | 2 | -0.30 [-0.39, -0.20] * | -0.35 [-0.44, -0.26] * | -0.13 [-0.24, -0.03] * | -0.15 [-0.25, -0.05] * | -0.13 [-0.24, -0.03] * | -0.15 [-0.26, -0.05] * |
| Madrid | 3 | -0.17 [-0.28, -0.07] * | -0.21 [-0.31, -0.11] * | +0.00 [-0.09, +0.10] | +0.03 [-0.08, +0.13] | +0.00 [-0.09, +0.10] | +0.03 [-0.07, +0.13] |
| Londra | 1 | +0.03 [-0.07, +0.12] | +0.03 [-0.07, +0.13] | -0.27 [-0.36, -0.18] * | -0.23 [-0.32, -0.14] * | +0.04 [-0.06, +0.14] | +0.04 [-0.05, +0.14] |
| Londra | 2 | +0.20 [+0.10, +0.30] * **A** | +0.22 [+0.12, +0.31] * **A** | -0.16 [-0.26, -0.05] * | -0.13 [-0.23, -0.03] * | +0.11 [+0.02, +0.21] * **A** | +0.09 [-0.01, +0.19] |
| Londra | 3 | +0.07 [-0.04, +0.16] | +0.08 [-0.02, +0.18] | -0.16 [-0.25, -0.07] * | -0.14 [-0.23, -0.04] * | -0.00 [-0.10, +0.09] | +0.03 [-0.06, +0.12] |
| Melbourne | 1 | -0.02 [-0.14, +0.12] | -0.05 [-0.18, +0.07] | +0.09 [-0.03, +0.21] | +0.07 [-0.06, +0.19] | +0.01 [-0.10, +0.14] | -0.02 [-0.14, +0.11] |
| Melbourne | 2 | +0.18 [+0.06, +0.29] * **A** | +0.19 [+0.07, +0.30] * **A** | -0.05 [-0.17, +0.06] | -0.01 [-0.13, +0.11] | -0.07 [-0.19, +0.05] | -0.03 [-0.15, +0.09] |
| Melbourne | 3 | +0.08 [-0.03, +0.20] | +0.08 [-0.04, +0.20] | +0.02 [-0.10, +0.13] | +0.04 [-0.09, +0.15] | +0.05 [-0.07, +0.17] | +0.07 [-0.05, +0.18] |

\* esclude lo zero; **A** = anomalia dichiarata (ρ positiva che esclude lo zero: i nodi meno coperti traggono piu' beneficio).

ρ(v, Δ₂) negativa con intervallo sotto lo zero in 4/9 (Madrid ep. 2, Londra ep. 1, Londra ep. 2, Londra ep. 3); ρ(v, Δ₁) negativa con intervallo sotto lo zero in 2/9 (Madrid ep. 2, Madrid ep. 3). Anomalie: Londra/ep2/D1/v, Londra/ep2/D1/v7, Londra/ep2/D3/v, Melbourne/ep2/D1/v, Melbourne/ep2/D1/v7.

## 4. Decisione sullo stadio 2a (regola pre-registrata)

- (i) ipotesi fallita in almeno un gruppo: **no**
- (ii) ρ(v, Δ₁) o ρ(v₇, Δ₁) negativa che esclude lo zero in ≥ 2 citta' nell'episodio 1 o in 2 episodi: **no** (v: False, v₇: False)
- stadio 2a: **NON si esegue**; stadio 2b, condizionato a 2a, non si esegue.

## 5. Che cosa cambia nel paper

La copertura delle prime 24 ore e' una condizione dell'adattamento a 24 ore **in alcuni contesti** — per gradiente in 4/9 (ρ(v, Δ₂) sotto lo zero) e per gruppi in 3 (F′(24 h) − C sopra lo zero sotto soglia: Londra ep. 1 +0.045, Londra ep. 2 +0.017, Melbourne ep. 2 +0.025) — e **in nessun contesto** dell'adattamento a una settimana, che paga sotto soglia quanto sopra. La raccomandazione: «dopo una settimana, adattare tutti i nodi; la soglia serve solo a chi adatta prima». Londra: a 24 ore copertura e budget (E5, secondaria); a una settimana nulla da spiegare. Cambia quanto si promette, non la raccomandazione.

## 5b. Post hoc dichiarato (richiesto dal revisore dopo il congelamento, costo zero)

Le anomalie dello stadio 1 (ρ(v, Δ₁) > 0) sono F′ che guadagna o C che perde sui nodi radi? ρ(v, wCE per nodo) di C e di F′(1 sett.), stessi file, stesso ricampionamento:

| citta' | ep. | v mediana | v₇ mediana | ρ(v, wCE C) | ρ(v, wCE F′(1 sett.)) | anomalia st. 1 |
|---|---|---|---|---|---|---|
| Madrid | 1 | 260 | 2297 | -0.53 [-0.60, -0.45] * | -0.50 [-0.57, -0.42] * | — |
| Madrid | 2 | 284 | 2276 | -0.52 [-0.59, -0.44] * | -0.50 [-0.58, -0.42] * | — |
| Madrid | 3 | 288 | 2253 | -0.50 [-0.58, -0.41] * | -0.48 [-0.56, -0.40] * | — |
| Londra | 1 | 114 | 1355 | -0.33 [-0.42, -0.24] * | -0.28 [-0.37, -0.19] * | — |
| Londra | 2 | 149 | 1582 | -0.25 [-0.34, -0.15] * | -0.17 [-0.26, -0.07] * | si |
| Londra | 3 | 188 | 1529 | -0.34 [-0.42, -0.24] * | -0.29 [-0.37, -0.19] * | — |
| Melbourne | 1 | 260 | 2098 | -0.44 [-0.52, -0.34] * | -0.43 [-0.52, -0.33] * | — |
| Melbourne | 2 | 109 | 1598 | -0.44 [-0.54, -0.35] * | -0.40 [-0.49, -0.30] * | si |
| Melbourne | 3 | 226 | 1666 | -0.62 [-0.68, -0.54] * | -0.58 [-0.64, -0.50] * | — |

\* esclude lo zero.

ρ(v, wCE C) negativa con intervallo sotto lo zero in **9/9** celle; celle con anomalia 2, di cui con ρ negativa 2; celle **senza** anomalia con ρ negativa 7.

Il segno di ρ(v, wCE C) **non discrimina** le celle anomale: i nodi con ingressi radi hanno errore maggiore per C e per F′(1 sett.) in ogni citta' e in ogni episodio, dove l'anomalia compare e dove non compare. Il post hoc quindi **non spiega** l'anomalia: la registra come un guadagno relativo di F′ sui nodi radi in quegli episodi, senza una causa identificabile nei file di E5. Resta dichiarata come tale.

**Copertura per episodio**: e' una proprieta' dell'episodio oltre che della citta' (colonne v e v₇), e va nella riga del paper sulla struttura del calendario, accanto ai salti settimanali.

## 6. Impronte

| file | impronta |
|---|---|
| `evoluzione/analisi/e7_stadio1.py` | `fab3034c6cf470c9` |
| `evoluzione/analisi/e7_posthoc.py` | `ab62ffb9a8b69a49` |
| `protocol/E7.md` | `07db021e85236235` |
