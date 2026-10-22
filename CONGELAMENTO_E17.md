# CONGELAMENTO E17 — politica integrata, categorie di verdetto, recupero, margine minimo

Generato da `genera_congelamento_e17.py` al commit `e10c579`, 2026-10-22 13:31 UTC. Protocollo `protocol/E17.md` (impronta `dcacf323f9f5defb`), firmato prima di ogni numero. Sola analisi dalle predizioni per cella della campagna congelata (statica non causale, difetto 21 dichiarato) e dai json congelati; `e17_risultati.json` impronta `d9c5f646191945df`; 4000 ricampionamenti congiunti (partizioni × semi × sensori, schema di E4), seme 20261022.

**Categorie** (E17): *superiorita'* = limite superiore dell'intervallo < 0; *non inferiorita'* = limite superiore < δ = 0.005 wCE (meta' del piu' piccolo effetto trattato come rilevante); *inconclusivo* altrimenti.

## 1. Politica integrata gated(1 sett., 0) come politica completa

gated(672, 0): F0' per eta' <= 1 settimana, F'(1 sett.) oltre, per tutti i sensori (N = 0). wCE integrata su tutte le origini dopo t₁; episodi 2 e 3 non l'hanno formulata, l'episodio 1 e' il riferimento; PEMS08 e PEMS04 righe aggiuntive.

| contesto | celle | (τ, N) selezionata | gated(1 sett., 0) − F₀′ | categoria | gated(1 sett., 0) − gated(τ, N) | gated(1 sett., 0) − C | wCE gated(1 sett., 0) | wCE F₀′ | wCE gated(τ, N) |
|---|---|---|---|---|---|---|---|---|---|
| Madrid/ep1 | 18 | τ=192, N=77 | -0.0238 [-0.0280, -0.0199] | superiorita' | +0.0049 [+0.0003, +0.0098] | -0.0159 [-0.0188, -0.0133] | 0.9442 | 0.9680 | 0.9393 |
| Madrid/ep2 | 18 | τ=192, N=77 | -0.0242 [-0.0291, -0.0200] | superiorita' | +0.0025 [-0.0019, +0.0069] | -0.0201 [-0.0242, -0.0166] | 0.9447 | 0.9689 | 0.9422 |
| Madrid/ep3 | 18 | τ=192, N=77 | -0.0237 [-0.0289, -0.0189] | superiorita' | -0.0162 [-0.0255, -0.0084] | -0.0216 [-0.0264, -0.0176] | 0.9488 | 0.9725 | 0.9650 |
| Londra/ep1 | 18 | τ=192, N=154 | -0.0289 [-0.0339, -0.0241] | superiorita' | -0.0183 [-0.0236, -0.0132] | -0.0143 [-0.0169, -0.0118] | 0.8759 | 0.9048 | 0.8942 |
| Londra/ep2 | 18 | τ=192, N=154 | -0.0204 [-0.0253, -0.0160] | superiorita' | -0.0026 [-0.0064, +0.0011] | -0.0106 [-0.0134, -0.0080] | 0.8744 | 0.8948 | 0.8770 |
| Londra/ep3 | 18 | τ=192, N=154 | -0.0251 [-0.0291, -0.0214] | superiorita' | -0.0016 [-0.0070, +0.0033] | -0.0146 [-0.0172, -0.0119] | 0.8780 | 0.9031 | 0.8795 |
| Melbourne/ep1 | 18 | τ=672, N=154 | -0.0239 [-0.0279, -0.0201] | superiorita' | +0.0000 [+0.0000, +0.0000] | -0.0215 [-0.0275, -0.0158] | 0.7934 | 0.8173 | 0.7934 |
| Melbourne/ep2 | 18 | τ=672, N=154 | -0.0177 [-0.0250, -0.0104] | superiorita' | -0.0183 [-0.0241, -0.0129] | -0.0115 [-0.0163, -0.0069] | 0.8144 | 0.8321 | 0.8327 |
| Melbourne/ep3 | 18 | τ=672, N=154 | -0.0334 [-0.0385, -0.0289] | superiorita' | -0.0001 [-0.0002, +0.0000] | -0.0171 [-0.0213, -0.0136] | 0.7792 | 0.8126 | 0.7792 |
| PEMS08 | 36 | τ=96, N=231 | -0.0361 [-0.0615, -0.0029] | superiorita' | -0.0017 [-0.0333, +0.0220] | -0.0755 [-0.1111, -0.0365] | 0.5341 | 0.5702 | 0.5358 |
| PEMS04 | 36 | τ=192, N=231 | -0.0101 [-0.0131, -0.0075] | superiorita' | +0.0118 [+0.0049, +0.0187] | -0.0075 [-0.0169, +0.0018] | 0.4927 | 0.5028 | 0.4809 |

gated(1 sett., 0) − F₀′: superiorita' in 11, non inferiorita' in 0, inconclusivo in 0 contesti su 11.

## 2. Categorie dei verdetti congelati

### 2a. gated(τ, N) − F₀′ negli 11 contesti

| contesto | valore [IC 95 %] | categoria | fonte |
|---|---|---|---|
| Madrid/ep1 | -0.0287 [-0.0372, -0.0210] | superiorita' | `e5_risultati.json` |
| Madrid/ep2 | -0.0267 [-0.0353, -0.0189] | superiorita' | `e5_risultati.json` |
| Madrid/ep3 | -0.0076 [-0.0177, +0.0027] | non inferiorita' | `e5_risultati.json` |
| Londra/ep1 | -0.0106 [-0.0175, -0.0043] | superiorita' | `e5_risultati.json` |
| Londra/ep2 | -0.0178 [-0.0240, -0.0127] | superiorita' | `e5_risultati.json` |
| Londra/ep3 | -0.0236 [-0.0316, -0.0158] | superiorita' | `e5_risultati.json` |
| Melbourne/ep1 | -0.0239 [-0.0280, -0.0201] | superiorita' | `e5_risultati.json` |
| Melbourne/ep2 | +0.0005 [-0.0030, +0.0039] | non inferiorita' | `e5_risultati.json` |
| Melbourne/ep3 | -0.0334 [-0.0388, -0.0285] | superiorita' | `e5_risultati.json` |
| PEMS08 | -0.0344 [-0.0712, +0.0091] | inconclusivo | `e6_risultati.json` |
| PEMS04 | -0.0219 [-0.0305, -0.0133] | superiorita' | `e6a_risultati.json` |

Totale: 8 superiorita', 2 non inferiorita', 1 inconclusivo.

### 2b. R-orig(1 sett.) − F′(1 sett.), origini con eta' > 1 settimana

| contesto | valore [IC 95 %] | categoria | fonte |
|---|---|---|---|
| Madrid | -0.0033 [-0.0059, -0.0010] | superiorita' | `e3bis_risultati.json` |
| Londra | -0.0025 [-0.0049, +0.0003] | non inferiorita' | `e3bis_risultati.json` |
| Melbourne | -0.0134 [-0.0199, -0.0069] | superiorita' | `e3bis_risultati.json` |
| PEMS08 | +0.0098 [-0.0396, +0.0792] | inconclusivo | `e6_risultati.json (altri)` |

## 3. Recupero del divario C → A da F′(1 sett.)

(L_C − L_F′(1 sett.)) / (L_C − L_A) sulle stesse origini (eta' > 1 settimana); intervallo = rapporto delle medie nella stessa replica.

| contesto | L_C | L_F′(1 sett.) | L_A | recupero [IC 95 %] | repliche con denominatore ≤ 0 |
|---|---|---|---|---|---|
| Madrid/ep1 | 0.9628 | 0.9320 | 0.9243 | 0.800 [0.706, 0.891] | 0 |
| Madrid/ep2 | 0.9637 | 0.9284 | 0.9239 | 0.887 [0.806, 0.963] | 0 |
| Madrid/ep3 | 0.9720 | 0.9363 | 0.9334 | 0.923 [0.844, 1.003] | 0 |
| Londra/ep1 | 0.8886 | 0.8580 | 0.8495 | 0.783 [0.704, 0.853] | 0 |
| Londra/ep2 | 0.8932 | 0.8689 | 0.8599 | 0.730 [0.616, 0.832] | 0 |
| Londra/ep3 | 0.8947 | 0.8643 | 0.8559 | 0.783 [0.691, 0.877] | 0 |
| Melbourne/ep1 | 0.8143 | 0.7784 | 0.7803 | 1.057 [0.834, 1.565] | 0 |
| Melbourne/ep2 | 0.8229 | 0.7975 | 0.7875 | 0.716 [0.534, 1.006] | 0 |
| Melbourne/ep3 | 0.8014 | 0.7631 | 0.7477 | 0.714 [0.649, 0.786] | 0 |
| PEMS08 | 0.6094 | 0.5186 | 0.4790 | 0.696 [0.380, 1.221] | 0 |

## 4. Margine minimo di equivalenza (TOST) per R-orig(1 sett.) ≡ F′(1 sett.)

Il piu' piccolo δ a cui l'intervallo al 95 % della differenza sta in (−δ, δ): max(|lo|, |hi|). E3-bis usava ±3 % del livello di F′(1 sett.) (colonna «margine ±3 %», dove registrato).

| contesto | δ minimo (wCE) | margine ±3 % di E3-bis | fonte |
|---|---|---|---|
| Madrid | 0.0059 | 0.0289 | `e3bis_risultati.json` |
| Londra | 0.0049 | 0.0266 | `e3bis_risultati.json` |
| Melbourne | 0.0199 | 0.0244 | `e3bis_risultati.json` |
| PEMS08 | 0.0792 | — | `e6_risultati.json (altri)` |

## 5. Impronte

- `results/evoluzione/e17_risultati.json` `d9c5f646191945df`; `protocol/E17.md` `dcacf323f9f5defb`.
- Ingressi: `e5_risultati.json` `04609880cbede25f`, `e6_risultati.json` `7d8bdb9c51e24993`, `e6a_risultati.json` `74c6c95bacfeffd1`, `e3bis_risultati.json` `2db2dd9ffece2072`, `e4_scelta_gated.json` `5ec1d3a3df09a712`, `e6_scelta_gated.json` `e76346636f769c2d`, `e6a_scelta_gated.json` `b699066ca0cac94d`.
- `results/evoluzione/congelamento_e17.json` `e6748bef25ed2e1e`.
