# Congelamento — E8, metriche operative (post hoc, dichiarato)

**Congelato il 2026-10-10**, commit `78c4e30556e5`. Protocollo `protocol/E8.md` (impronta `611d3541a6086e19`), firmato al commit `1185d9ecceb39bdf` prima di ricostruire; deviazione del 9/10 dichiarata nel file (A eredita le soglie di C). **Nessun criterio**: è descrittivo. **Ogni numero e' calcolato da `genera_congelamento_e8.py`** da `e8_risultati.json` e `e8_soglie.json`. Va in appendice C; la frase derivata (§4) nel testo della sezione 5.1.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| ricostruzione | 360 celle (validazione + prova) dai punti di controllo dei congelamenti, nessun addestramento; **2268 controlli** contro gli aggregati congelati, scarto relativo massimo **1.3e-14** (soglia 1e-6): la ricostruzione riproduce i congelamenti |
| soglie | `e8_soglie.json`, impronta `dcb93389339a6657`, scelte su validazione prima di qualunque metrica di prova; griglia 0.05…0.95; A eredita C, R-orig(1 sett.) eredita F′(1 sett.) |
| ricampionamento | 4000 repliche congiunte (partizioni × semi × nodi), semi dei congelamenti |
| contesti | Madrid, Londra, Melbourne (episodio 1; gli episodi 2–3 non inclusi, deciso dopo il pilota), PEMS08 (6 × 6), PEMS04 (3 × 12) |

## 2. Soglie scelte su validazione

| gruppo | C | A | F0 | F0p | Fp_96 | Fp_192 | Fp_672 | Rorig_672 |
|---|---|---|---|---|---|---|---|---|
| Madrid | 0.45 / 0.45 | 0.45 / 0.45 (er.) | 0.30 / 0.30 | 0.45 / 0.45 | 0.55 / 0.45 | 0.55 / 0.45 | 0.50 / 0.45 | 0.50 / 0.45 (er.) |
| Londra | 0.45 / 0.45 | 0.45 / 0.45 (er.) | 0.40 / 0.40 | 0.45 / 0.45 | 0.55 / 0.55 | 0.55 / 0.55 | 0.55 / 0.50 | 0.55 / 0.50 (er.) |
| Melbourne | 0.60 / 0.60 | 0.60 / 0.60 (er.) | 0.40 / 0.40 | 0.60 / 0.60 | 0.60 / 0.65 | 0.60 / 0.65 | 0.60 / 0.65 | 0.60 / 0.65 (er.) |
| PEMS08 | 0.80 / 0.80 | 0.80 / 0.80 (er.) | 0.45 / 0.45 | 0.75 / 0.75 | 0.75 / 0.75 | — | 0.80 / 0.80 | 0.80 / 0.80 (er.) |
| PEMS04 | 0.75 / 0.75 | 0.75 / 0.75 (er.) | — | 0.75 / 0.75 | 0.70 / 0.70 | 0.70 / 0.70 | 0.75 / 0.70 | 0.75 / 0.70 (er.) |

Per cella: soglia primaria / soglia a parita' di falsi allarmi con C; «er.» = ereditata.

## 3. Differenze fra bracci, per regola e metrica

### Madrid (36 celle; gated τ = 192, N = 77)

| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |
|---|---|---|---|---|---|---|
| A − C | -0.039 [-0.044, -0.034] − | primaria (F1 per braccio) | +6.9 [+2.4, +11.1] + | +0.2 [-2.1, +2.5] 0 | +2.1 [+1.3, +3.0] + | +2.0 [+1.2, +2.6] + |
|  |  | parita' di falsi allarmi con C | +6.9 [+2.2, +11.2] + | +0.2 [-2.0, +2.7] 0 | +2.1 [+1.3, +3.0] + | +2.0 [+1.2, +2.6] + |
|  |  | argmax | +3.7 [+0.2, +7.3] + | -2.6 [-5.1, -0.1] − | +2.3 [+1.6, +3.2] + | +2.5 [+1.7, +3.4] + |
| F₀ − C | +0.073 [+0.059, +0.089] + | primaria (F1 per braccio) | -7.9 [-12.3, -3.3] − | +0.4 [-2.5, +3.2] 0 | -3.0 [-4.1, -1.9] − | -4.2 [-5.1, -3.3] − |
|  |  | parita' di falsi allarmi con C | -7.9 [-12.3, -3.2] − | +0.4 [-2.4, +3.2] 0 | -3.0 [-4.0, -1.9] − | -4.2 [-5.1, -3.2] − |
|  |  | argmax | -47.6 [-51.3, -43.5] − | -25.9 [-29.6, -22.5] − | +8.8 [+6.8, +10.7] + | +0.8 [-0.3, +2.0] 0 |
| F₀′ − C | +0.008 [+0.006, +0.011] + | primaria (F1 per braccio) | -1.8 [-3.7, +0.1] 0 | -0.6 [-1.7, +0.6] 0 | -0.1 [-0.5, +0.3] 0 | -0.6 [-0.9, -0.2] − |
|  |  | parita' di falsi allarmi con C | -1.8 [-3.6, +0.1] 0 | -0.6 [-1.7, +0.5] 0 | -0.1 [-0.5, +0.3] 0 | -0.6 [-0.8, -0.3] − |
|  |  | argmax | -1.4 [-2.9, +0.1] 0 | -0.8 [-1.9, +0.4] 0 | +0.1 [-0.2, +0.3] 0 | -0.4 [-0.8, -0.0] − |
| F′(24 h) − C | -0.011 [-0.021, -0.002] − | primaria (F1 per braccio) | -6.9 [-11.0, -3.0] − | -5.6 [-7.9, -3.4] − | +3.4 [+2.1, +5.0] + | +2.0 [+1.3, +2.7] + |
|  |  | parita' di falsi allarmi con C | +10.8 [+7.3, +14.2] + | +5.0 [+2.7, +7.3] + | -0.6 [-1.3, +0.3] 0 | -0.3 [-1.1, +0.3] 0 |
|  |  | argmax | +5.0 [+1.5, +8.2] + | +1.1 [-1.7, +3.7] 0 | +0.6 [-0.1, +1.3] 0 | +0.4 [-0.5, +1.2] 0 |
| F′(1 sett.) − C, eta' > 1 sett. | -0.032 [-0.037, -0.027] − | primaria (F1 per braccio) | +6.7 [+3.2, +10.2] + | +0.6 [-1.3, +2.5] 0 | +1.6 [+0.9, +2.5] + | +1.7 [+1.1, +2.2] + |
|  |  | parita' di falsi allarmi con C | +16.1 [+12.8, +19.3] + | +6.5 [+4.3, +8.9] + | -0.2 [-0.9, +0.6] 0 | +0.2 [-0.6, +0.8] 0 |
|  |  | argmax | +10.4 [+7.5, +13.2] + | +3.3 [+0.9, +5.9] + | +0.7 [+0.1, +1.4] + | +0.5 [-0.4, +1.4] 0 |
| gated − F₀′ | -0.030 [-0.038, -0.022] − | primaria (F1 per braccio) | -1.3 [-5.6, +3.0] 0 | -3.6 [-5.6, -1.4] − | +3.2 [+2.3, +4.1] + | +2.6 [+2.0, +3.2] + |
|  |  | parita' di falsi allarmi con C | +15.7 [+11.9, +19.3] + | +7.0 [+4.5, +9.7] + | -0.6 [-1.5, +0.2] 0 | +0.2 [-0.7, +0.9] 0 |
|  |  | argmax | +9.6 [+6.5, +12.8] + | +3.7 [+1.1, +6.4] + | +0.4 [-0.3, +1.1] 0 | +0.6 [-0.4, +1.5] 0 |
| R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett. | -0.003 [-0.006, -0.001] − | primaria (F1 per braccio) | +0.7 [-0.4, +1.9] 0 | +0.1 [-0.6, +0.9] 0 | +0.1 [-0.2, +0.5] 0 | +0.2 [-0.0, +0.4] 0 |
|  |  | parita' di falsi allarmi con C | +0.4 [-0.6, +1.3] 0 | -0.0 [-0.7, +0.7] 0 | +0.1 [-0.1, +0.4] 0 | +0.2 [-0.1, +0.4] 0 |
|  |  | argmax | -0.1 [-0.9, +0.8] 0 | -0.2 [-0.9, +0.4] 0 | +0.1 [-0.1, +0.3] 0 | +0.2 [-0.1, +0.4] 0 |

Livelli (regola primaria): C richiamo 0.505, falsi allarmi 0.1965; A richiamo 0.574, falsi allarmi 0.1989; Rorig_672 richiamo 0.574, falsi allarmi 0.1939; F0 richiamo 0.426, falsi allarmi 0.2005; F0p richiamo 0.487, falsi allarmi 0.1909; Fp_96 richiamo 0.436, falsi allarmi 0.1405; Fp_192 richiamo 0.473, falsi allarmi 0.1504; Fp_672 richiamo 0.566, falsi allarmi 0.1950; gated richiamo 0.474, falsi allarmi 0.1553.

### Londra (36 celle; gated τ = 192, N = 154)

| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |
|---|---|---|---|---|---|---|
| A − C | -0.035 [-0.039, -0.031] − | primaria (F1 per braccio) | +7.1 [+4.6, +9.4] + | +2.2 [+1.0, +3.4] + | -1.2 [-2.6, +0.2] 0 | +1.3 [+0.9, +1.8] + |
|  |  | parita' di falsi allarmi con C | +7.1 [+4.7, +9.4] + | +2.2 [+1.0, +3.4] + | -1.2 [-2.5, +0.3] 0 | +1.3 [+0.9, +1.8] + |
|  |  | argmax | +6.8 [+4.1, +9.4] + | +2.2 [+0.6, +3.7] + | -0.6 [-1.8, +0.8] 0 | +1.4 [+0.8, +1.9] + |
| F₀ − C | +0.050 [+0.038, +0.063] + | primaria (F1 per braccio) | -0.8 [-2.9, +1.5] 0 | +0.7 [-0.5, +1.9] 0 | -1.6 [-3.2, -0.1] − | -3.5 [-4.3, -2.7] − |
|  |  | parita' di falsi allarmi con C | -0.8 [-3.0, +1.4] 0 | +0.7 [-0.5, +1.9] 0 | -1.6 [-3.2, -0.0] − | -3.5 [-4.3, -2.7] − |
|  |  | argmax | -8.2 [-10.4, -6.2] − | -3.8 [-4.9, -2.7] − | +4.0 [+2.5, +5.5] + | -2.2 [-2.9, -1.4] − |
| F₀′ − C | +0.013 [+0.010, +0.017] + | primaria (F1 per braccio) | +1.5 [-0.0, +3.1] 0 | +1.2 [+0.4, +2.1] + | -1.8 [-2.9, -0.6] − | -1.1 [-1.6, -0.6] − |
|  |  | parita' di falsi allarmi con C | +1.5 [-0.1, +3.0] 0 | +1.2 [+0.3, +2.1] + | -1.8 [-2.9, -0.7] − | -1.1 [-1.6, -0.6] − |
|  |  | argmax | +1.0 [-0.7, +2.8] 0 | +0.9 [-0.1, +2.0] 0 | -0.9 [-1.9, -0.0] − | -1.0 [-1.6, -0.5] − |
| F′(24 h) − C | +0.034 [+0.023, +0.044] + | primaria (F1 per braccio) | -11.0 [-15.0, -7.5] − | -4.0 [-5.3, -2.7] − | +5.5 [+2.9, +8.3] + | -1.0 [-2.2, -0.1] − |
|  |  | parita' di falsi allarmi con C | -11.0 [-14.8, -7.5] − | -4.0 [-5.3, -2.8] − | +5.5 [+3.0, +8.2] + | -1.0 [-2.2, -0.2] − |
|  |  | argmax | -1.7 [-5.9, +2.4] 0 | +0.2 [-1.7, +2.2] 0 | -1.1 [-2.8, +0.9] 0 | -2.0 [-3.2, -1.0] − |
| F′(1 sett.) − C, eta' > 1 sett. | -0.030 [-0.035, -0.026] − | primaria (F1 per braccio) | -11.5 [-14.0, -9.4] − | -5.6 [-6.6, -4.7] − | +10.3 [+8.2, +12.4] + | +2.0 [+1.2, +2.6] + |
|  |  | parita' di falsi allarmi con C | -6.2 [-8.4, -4.2] − | -3.7 [-4.6, -2.9] − | +6.4 [+4.8, +8.1] + | +2.0 [+1.4, +2.4] + |
|  |  | argmax | -0.7 [-3.1, +1.4] 0 | -1.6 [-2.8, -0.5] − | +2.5 [+1.3, +4.0] + | +1.7 [+1.1, +2.2] + |
| gated − F₀′ | -0.009 [-0.016, -0.003] − | primaria (F1 per braccio) | -5.6 [-7.8, -3.7] − | -2.6 [-3.5, -1.7] − | +3.0 [+1.8, +4.3] + | +1.0 [+0.4, +1.6] + |
|  |  | parita' di falsi allarmi con C | -5.6 [-7.9, -3.6] − | -2.6 [-3.5, -1.7] − | +3.0 [+1.8, +4.2] + | +1.0 [+0.4, +1.6] + |
|  |  | argmax | -3.0 [-4.9, -1.3] − | -1.7 [-2.7, -0.7] − | +1.4 [+0.4, +2.6] + | +1.0 [+0.3, +1.7] + |
| R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett. | -0.002 [-0.005, +0.000] 0 | primaria (F1 per braccio) | -2.8 [-4.1, -1.7] − | -0.9 [-1.3, -0.6] − | +2.5 [+1.5, +3.6] + | -0.1 [-0.4, +0.2] 0 |
|  |  | parita' di falsi allarmi con C | -2.3 [-3.6, -1.1] − | -0.9 [-1.3, -0.4] − | +1.7 [+0.7, +2.7] + | +0.1 [-0.1, +0.3] 0 |
|  |  | argmax | -0.7 [-1.9, +0.5] 0 | -0.3 [-0.9, +0.2] 0 | +0.4 [-0.2, +1.1] 0 | +0.2 [-0.0, +0.4] 0 |

Livelli (regola primaria): C richiamo 0.470, falsi allarmi 0.1028; A richiamo 0.541, falsi allarmi 0.1247; Rorig_672 richiamo 0.340, falsi allarmi 0.0438; F0 richiamo 0.461, falsi allarmi 0.1095; F0p richiamo 0.484, falsi allarmi 0.1147; Fp_96 richiamo 0.359, falsi allarmi 0.0629; Fp_192 richiamo 0.339, falsi allarmi 0.0494; Fp_672 richiamo 0.365, falsi allarmi 0.0518; gated richiamo 0.428, falsi allarmi 0.0890.

### Melbourne (36 celle; gated τ = 672, N = 154)

| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |
|---|---|---|---|---|---|---|
| A − C | -0.038 [-0.048, -0.027] − | primaria (F1 per braccio) | +8.0 [+2.9, +12.9] + | +1.4 [+0.2, +2.8] + | -2.5 [-4.9, +0.7] 0 | +0.5 [-0.3, +1.3] 0 |
|  |  | parita' di falsi allarmi con C | +8.0 [+2.7, +13.0] + | +1.4 [+0.2, +2.7] + | -2.5 [-4.7, +0.6] 0 | +0.5 [-0.3, +1.3] 0 |
|  |  | argmax | +6.3 [+2.3, +9.6] + | +1.7 [-0.4, +3.9] 0 | -0.7 [-2.3, +1.5] 0 | +0.3 [-1.0, +1.6] 0 |
| F₀ − C | +0.078 [+0.053, +0.103] + | primaria (F1 per braccio) | -0.7 [-3.9, +3.0] 0 | +1.0 [+0.4, +1.7] + | -5.0 [-7.1, -3.0] − | -1.9 [-2.6, -1.1] − |
|  |  | parita' di falsi allarmi con C | -0.7 [-4.0, +3.0] 0 | +1.0 [+0.4, +1.7] + | -5.0 [-7.2, -3.1] − | -1.9 [-2.7, -1.1] − |
|  |  | argmax | -22.9 [-27.1, -17.5] − | -7.0 [-9.0, -5.2] − | +8.7 [+6.9, +10.3] + | +2.3 [+1.2, +3.4] + |
| F₀′ − C | +0.001 [-0.005, +0.007] 0 | primaria (F1 per braccio) | +1.2 [-0.6, +3.1] 0 | +0.3 [-0.1, +0.7] 0 | -1.0 [-2.3, +0.1] 0 | -0.1 [-0.4, +0.2] 0 |
|  |  | parita' di falsi allarmi con C | +1.2 [-0.6, +3.1] 0 | +0.3 [-0.1, +0.7] 0 | -1.0 [-2.3, +0.1] 0 | -0.1 [-0.4, +0.2] 0 |
|  |  | argmax | +1.2 [-0.3, +2.8] 0 | +0.7 [+0.0, +1.4] + | -0.6 [-1.3, -0.0] − | -0.4 [-0.9, +0.0] 0 |
| F′(24 h) − C | -0.019 [-0.028, -0.009] − | primaria (F1 per braccio) | +7.6 [+3.6, +11.6] + | +1.4 [+0.4, +2.6] + | -2.9 [-4.9, -0.6] − | -0.2 [-0.9, +0.5] 0 |
|  |  | parita' di falsi allarmi con C | +1.3 [-3.0, +5.0] 0 | -0.1 [-0.8, +0.7] 0 | +1.1 [-1.1, +3.8] 0 | +0.4 [-0.2, +0.9] 0 |
|  |  | argmax | +3.8 [+0.0, +7.5] + | +0.6 [-1.3, +2.5] 0 | +0.1 [-1.7, +2.1] 0 | +0.2 [-1.0, +1.4] 0 |
| F′(1 sett.) − C, eta' > 1 sett. | -0.036 [-0.043, -0.030] − | primaria (F1 per braccio) | +9.3 [+5.5, +12.9] + | +1.6 [+0.7, +2.6] + | -3.5 [-5.1, -1.5] − | -0.2 [-0.8, +0.4] 0 |
|  |  | parita' di falsi allarmi con C | +2.8 [-0.6, +5.9] 0 | +0.0 [-0.6, +0.6] 0 | +1.1 [-0.7, +3.5] 0 | +0.6 [+0.1, +1.0] + |
|  |  | argmax | +6.9 [+3.7, +9.6] + | +1.6 [-0.0, +3.2] 0 | -0.6 [-2.2, +1.2] 0 | -0.1 [-1.2, +0.9] 0 |
| gated − F₀′ | -0.024 [-0.027, -0.020] − | primaria (F1 per braccio) | +4.6 [+2.4, +6.6] + | +0.8 [+0.3, +1.4] + | -1.5 [-2.5, -0.2] − | -0.0 [-0.4, +0.4] 0 |
|  |  | parita' di falsi allarmi con C | +1.0 [-0.9, +2.8] 0 | -0.1 [-0.5, +0.2] 0 | +1.2 [+0.1, +2.4] + | +0.4 [+0.1, +0.7] + |
|  |  | argmax | +3.3 [+1.5, +4.8] + | +0.6 [-0.5, +1.7] 0 | +0.0 [-1.1, +1.1] 0 | +0.2 [-0.4, +0.8] 0 |
| R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett. | -0.013 [-0.020, -0.007] − | primaria (F1 per braccio) | +1.2 [-0.7, +2.9] 0 | -0.0 [-0.4, +0.4] 0 | +0.6 [-0.6, +2.0] 0 | +0.6 [+0.2, +1.1] + |
|  |  | parita' di falsi allarmi con C | +1.8 [-0.4, +3.9] 0 | +0.1 [-0.3, +0.5] 0 | +0.3 [-1.0, +2.1] 0 | +0.6 [+0.2, +1.1] + |
|  |  | argmax | +0.2 [-1.8, +1.7] 0 | +0.1 [-0.7, +0.8] 0 | -0.0 [-0.7, +0.9] 0 | +0.4 [-0.1, +0.9] 0 |

Livelli (regola primaria): C richiamo 0.471, falsi allarmi 0.0450; A richiamo 0.551, falsi allarmi 0.0586; Rorig_672 richiamo 0.578, falsi allarmi 0.0580; F0 richiamo 0.464, falsi allarmi 0.0552; F0p richiamo 0.483, falsi allarmi 0.0482; Fp_96 richiamo 0.547, falsi allarmi 0.0593; Fp_192 richiamo 0.549, falsi allarmi 0.0577; Fp_672 richiamo 0.563, falsi allarmi 0.0599; gated richiamo 0.529, falsi allarmi 0.0561.

### PEMS08 (36 celle; gated τ = 96, N = 231)

**Intervalli larghi per costruzione**: classe congestionata allo 0,9–1,4 % (p0 allo 0,9 %), 26 nodi nuovi per partizione (protocollo E6, ripetuto qui).

| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |
|---|---|---|---|---|---|---|
| A − C | -0.133 [-0.188, -0.067] − | primaria (F1 per braccio) | +7.9 [-5.0, +16.5] 0 | -0.2 [-0.7, +0.2] 0 | +12.5 [+2.1, +27.2] + | +3.7 [+1.0, +5.7] + |
|  |  | parita' di falsi allarmi con C | +7.9 [-5.5, +16.6] 0 | -0.2 [-0.7, +0.2] 0 | +12.5 [+2.2, +27.5] + | +3.7 [+0.9, +5.7] + |
|  |  | argmax | +8.3 [-2.8, +15.4] 0 | -0.5 [-1.7, +0.7] 0 | +6.5 [+0.2, +13.7] + | +3.5 [+0.6, +6.6] + |
| F₀ − C | +0.156 [+0.065, +0.244] + | primaria (F1 per braccio) | +6.2 [-0.2, +14.9] 0 | -0.0 [-0.4, +0.6] 0 | +4.3 [-5.7, +15.7] 0 | +3.4 [+1.7, +5.6] + |
|  |  | parita' di falsi allarmi con C | +6.2 [-0.0, +14.7] 0 | -0.0 [-0.4, +0.5] 0 | +4.3 [-5.7, +15.6] 0 | +3.4 [+1.8, +5.6] + |
|  |  | argmax | -18.8 [-26.5, -10.7] − | -2.4 [-3.3, -1.7] − | +32.7 [+22.0, +43.9] + | +7.4 [+4.9, +10.1] + |
| F₀′ − C | -0.039 [-0.076, -0.004] − | primaria (F1 per braccio) | +5.2 [+0.3, +11.3] + | -0.0 [-0.3, +0.3] 0 | +3.0 [-4.6, +11.5] 0 | +0.9 [-0.4, +2.3] 0 |
|  |  | parita' di falsi allarmi con C | +5.2 [+0.1, +11.2] + | -0.0 [-0.3, +0.3] 0 | +3.0 [-4.8, +11.0] 0 | +0.9 [-0.4, +2.3] 0 |
|  |  | argmax | +2.6 [-0.6, +6.8] 0 | -0.0 [-0.6, +0.6] 0 | +1.8 [-1.6, +5.7] 0 | +0.1 [-1.7, +1.8] 0 |
| F′(24 h) − C | -0.074 [-0.118, -0.023] − | primaria (F1 per braccio) | +9.5 [+2.5, +15.3] + | +0.1 [-0.2, +0.5] 0 | -1.2 [-8.0, +8.0] 0 | +2.1 [+0.1, +4.3] + |
|  |  | parita' di falsi allarmi con C | +9.5 [+2.2, +15.2] + | +0.1 [-0.2, +0.5] 0 | -1.2 [-7.9, +8.8] 0 | +2.1 [+0.1, +4.3] + |
|  |  | argmax | +6.4 [-0.2, +12.0] 0 | -0.1 [-0.9, +0.8] 0 | +2.6 [-2.1, +10.0] 0 | +1.8 [-0.3, +4.7] 0 |
| F′(1 sett.) − C, eta' > 1 sett. | -0.091 [-0.130, -0.043] − | primaria (F1 per braccio) | +4.5 [-1.6, +9.3] 0 | -0.1 [-0.4, +0.2] 0 | +3.8 [-3.7, +12.5] 0 | +1.7 [-0.2, +3.3] 0 |
|  |  | parita' di falsi allarmi con C | +4.5 [-2.2, +9.5] 0 | -0.1 [-0.4, +0.2] 0 | +3.8 [-3.6, +12.9] 0 | +1.7 [-0.2, +3.4] 0 |
|  |  | argmax | +7.3 [+1.4, +12.6] + | +0.5 [-0.5, +1.5] 0 | -1.0 [-5.8, +4.8] 0 | +0.3 [-1.6, +2.7] 0 |
| gated − F₀′ | -0.034 [-0.072, +0.012] 0 | primaria (F1 per braccio) | +4.3 [-3.9, +11.1] 0 | +0.2 [-0.1, +0.5] 0 | -4.3 [-10.4, +1.9] 0 | +1.2 [-0.7, +3.0] 0 |
|  |  | parita' di falsi allarmi con C | +4.3 [-4.1, +11.0] 0 | +0.2 [-0.1, +0.5] 0 | -4.3 [-10.4, +2.0] 0 | +1.2 [-0.7, +3.1] 0 |
|  |  | argmax | +3.7 [-3.7, +9.1] 0 | -0.1 [-0.9, +0.8] 0 | +0.8 [-3.8, +8.0] 0 | +1.6 [-0.2, +4.2] 0 |
| R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett. | +0.010 [-0.041, +0.078] 0 | primaria (F1 per braccio) | +2.7 [-4.1, +8.2] 0 | -0.0 [-0.3, +0.3] 0 | +3.6 [-4.0, +14.6] 0 | +0.8 [-1.2, +2.6] 0 |
|  |  | parita' di falsi allarmi con C | +2.7 [-4.1, +8.2] 0 | -0.0 [-0.3, +0.3] 0 | +3.6 [-3.8, +14.9] 0 | +0.8 [-1.2, +2.6] 0 |
|  |  | argmax | -0.2 [-7.0, +5.1] 0 | -0.3 [-0.9, +0.3] 0 | +2.0 [-2.0, +6.1] 0 | +0.9 [-0.9, +2.6] 0 |

Livelli (regola primaria): C richiamo 0.450, falsi allarmi 0.0064; A richiamo 0.532, falsi allarmi 0.0043; Rorig_672 richiamo 0.557, falsi allarmi 0.0055; F0 richiamo 0.505, falsi allarmi 0.0062; F0p richiamo 0.497, falsi allarmi 0.0062; Fp_96 richiamo 0.549, falsi allarmi 0.0078; Fp_672 richiamo 0.506, falsi allarmi 0.0058; gated richiamo 0.549, falsi allarmi 0.0078.

### PEMS04 (36 celle; gated τ = 192, N = 231)

| confronto | ΔwCE | regola | Δrichiamo (punti) | Δfalsi allarmi (punti) | Δprecisione (punti) | ΔF1-macro (punti) |
|---|---|---|---|---|---|---|
| F₀′ − C | +0.003 [-0.007, +0.013] 0 | primaria (F1 per braccio) | -1.2 [-3.1, +1.0] 0 | -0.2 [-0.3, -0.1] − | +3.8 [+1.7, +6.4] + | -0.4 [-0.9, +0.2] 0 |
|  |  | parita' di falsi allarmi con C | -1.2 [-3.0, +0.9] 0 | -0.2 [-0.3, -0.1] − | +3.8 [+1.7, +6.3] + | -0.4 [-0.9, +0.2] 0 |
|  |  | argmax | -0.1 [-2.3, +2.4] 0 | -0.3 [-0.7, +0.1] 0 | +1.8 [-0.2, +3.9] 0 | -0.5 [-1.4, +0.3] 0 |
| F′(24 h) − C | -0.023 [-0.034, -0.010] − | primaria (F1 per braccio) | +4.4 [+1.4, +7.0] + | -0.0 [-0.2, +0.2] 0 | +1.9 [-1.4, +5.3] 0 | +1.0 [+0.3, +1.8] + |
|  |  | parita' di falsi allarmi con C | +4.4 [+1.4, +6.9] + | -0.0 [-0.2, +0.2] 0 | +1.9 [-1.4, +5.5] 0 | +1.0 [+0.2, +1.8] + |
|  |  | argmax | +0.8 [-1.7, +2.8] 0 | -1.0 [-1.6, -0.5] − | +6.3 [+3.4, +8.8] + | +2.0 [+0.8, +3.1] + |
| F′(1 sett.) − C, eta' > 1 sett. | -0.033 [-0.047, -0.019] − | primaria (F1 per braccio) | +2.0 [-1.2, +4.6] 0 | -0.3 [-0.5, -0.1] − | +5.6 [+2.1, +10.0] + | +1.1 [+0.3, +2.1] + |
|  |  | parita' di falsi allarmi con C | +7.1 [+3.6, +9.8] + | +0.1 [-0.1, +0.4] 0 | +0.7 [-2.8, +4.9] 0 | +0.9 [+0.1, +1.9] + |
|  |  | argmax | +3.2 [-0.0, +5.9] 0 | -0.9 [-1.6, -0.2] − | +4.2 [+1.8, +6.5] + | +1.2 [+0.2, +2.3] + |
| gated − F₀′ | -0.022 [-0.031, -0.013] − | primaria (F1 per braccio) | +5.1 [+3.2, +6.5] + | +0.1 [+0.0, +0.2] + | -1.6 [-3.8, +1.0] 0 | +1.2 [+0.8, +1.6] + |
|  |  | parita' di falsi allarmi con C | +5.1 [+3.2, +6.5] + | +0.1 [+0.0, +0.3] + | -1.6 [-3.7, +0.9] 0 | +1.2 [+0.8, +1.6] + |
|  |  | argmax | +0.9 [-1.4, +2.6] 0 | -0.6 [-1.0, -0.2] − | +3.7 [+1.4, +5.6] + | +2.1 [+1.1, +3.0] + |

Livelli (regola primaria): C richiamo 0.618, falsi allarmi 0.0094; F0p richiamo 0.606, falsi allarmi 0.0079; Fp_96 richiamo 0.664, falsi allarmi 0.0094; Fp_192 richiamo 0.667, falsi allarmi 0.0094; Fp_672 richiamo 0.633, falsi allarmi 0.0074; gated richiamo 0.658, falsi allarmi 0.0091.

Δ in punti percentuali; segno «−» = intervallo sotto lo zero, «+» sopra, «0» include lo zero. ΔwCE ricalcolata dalle stesse celle (verificata a 1e-6 contro i congelamenti).

## 4. La frase derivata per il paper (confronto principale, F′(1 sett.) − C sulle origini comuni)

- **Madrid**: «ΔwCE = -0.032 corrisponde a **+16.1 punti di richiamo** sulla classe congestionata [+12.8, +19.3] con soglie a parita' di falsi allarmi **su validazione**; sul test la parita' **non ha retto**: scarto residuo di falsi allarmi +6.5 punti [+4.3, +8.9], quindi il richiamo va letto insieme ai falsi allarmi, non da solo»; con la regola primaria +6.7 punti di richiamo con +0.6 punti di falsi allarmi.
- **Londra**: «ΔwCE = -0.030 corrisponde a **-6.2 punti di richiamo** sulla classe congestionata [-8.4, -4.2] con soglie a parita' di falsi allarmi **su validazione**; sul test la parita' **non ha retto**: scarto residuo di falsi allarmi -3.7 punti [-4.6, -2.9], quindi il richiamo va letto insieme ai falsi allarmi, non da solo»; con la regola primaria -11.5 punti di richiamo con -5.6 punti di falsi allarmi.
- **Melbourne**: ΔwCE -0.036 [-0.043, -0.030]; a parita' di falsi allarmi il richiamo sulla classe congestionata **non si distingue** (+2.8 punti [-0.6, +5.9]): nessuna frase.
- **PEMS08**: ΔwCE -0.091 [-0.130, -0.043]; a parita' di falsi allarmi il richiamo sulla classe congestionata **non si distingue** (+4.5 punti [-2.2, +9.5]): nessuna frase.
- **PEMS04**: «ΔwCE = -0.033 corrisponde a **+7.1 punti di richiamo** sulla classe congestionata [+3.6, +9.8] a parita' di falsi allarmi (scarto residuo +0.1 punti, intervallo che include lo zero)»; con la regola primaria +2.0 punti di richiamo con -0.3 punti di falsi allarmi.

La parita' di falsi allarmi imposta su validazione ha retto sul test (scarto residuo con intervallo che include lo zero) in **3 contesti su 5**: la soglia che eguaglia i falsi allarmi su validazione non li eguaglia sul test, e la frase «a parita'» vale solo dove lo scarto residuo e' indistinguibile da zero.

## 5. Richiamo e wCE si muovono insieme?

**Divergenze** (ΔwCE e Δrichiamo con intervalli che escludono lo zero nello stesso verso, cioe' wCE migliore e richiamo peggiore o viceversa): si riportano entrambe, non si sceglie la metrica.

- Madrid, F′(24 h) − C, regola primaria (F1 per braccio): ΔwCE -0.011 ma Δrichiamo -6.9 punti
- Londra, F′(1 sett.) − C, eta' > 1 sett., regola primaria (F1 per braccio): ΔwCE -0.030 ma Δrichiamo -11.5 punti
- Londra, F′(1 sett.) − C, eta' > 1 sett., regola parita' di falsi allarmi con C: ΔwCE -0.030 ma Δrichiamo -6.2 punti
- Londra, gated − F₀′, regola primaria (F1 per braccio): ΔwCE -0.009 ma Δrichiamo -5.6 punti
- Londra, gated − F₀′, regola parita' di falsi allarmi con C: ΔwCE -0.009 ma Δrichiamo -5.6 punti
- Londra, gated − F₀′, regola argmax: ΔwCE -0.009 ma Δrichiamo -3.0 punti

## 6. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_e8.py` | `d74c8594d9a3ab23` |
| `protocol/E8.md` | `611d3541a6086e19` |
| soglie | `dcb93389339a6657` |
