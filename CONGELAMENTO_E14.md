# Congelamento — E14, sensibilità alla statica non causale (difetto 21)

**Congelato il 2026-10-13**, commit `77f1d902f6c9`. Pre-registrazione `protocol/E14.md` (impronta `b669b5d8a269f1bd`), firmata al commit `102642b48adbe377` prima dello stadio A, con emendamento del 12/10 20:20 (variante (c), PEMS come controllo). **Ogni numero è calcolato da `genera_congelamento_e14.py`** dai file di risultato; il verdetto è derivato, non scritto. Nessun riaddestramento.

## 1. Che cosa è stato eseguito

| | |
|---|---|
| stadio 0 | sola lettura, 36 celle (contesto × episodio × partizione); `e14_stadio0.json` impronta `8072111407112630` |
| stadio A, celle | 432 cella-varianti completate, 0 fallite, 16 processi, 1.91 h di calendario; varianti ['a', 'b', 'c'] |
| macchina | NVIDIA DGX Spark (GB10, aarch64, Ubuntu 24.04), stesso ambiente del Mac (lockfile); il riferimento non causale sono gli aggregati per cella di `predizioni_e8/prova_*` (Mac) |
| bracci | C, A, F₀, F₀′, F′(1 sett.) (adattamento rifatto con la statica della variante), R-orig(1 sett.), dai checkpoint congelati |
| controllo 1 | 10 celle rivalutate con la statica non causale contro E8: scarto relativo massimo sulla wCE **5.1e-08** (sul Mac, pilota: 0); soglia d'arresto 1e-6 |
| statistica | ricampionamento congiunto partizioni × semi × nodi, 4000 repliche, semi di E8; soglia |Δ| 0.002 |

## 2. Stadio 0 — quanto differisce l'ingresso

| contesto/episodio | p90 \|Δ\| iniziali | nuovi (a) | nuovi (b) | p90 tutti (a) | criterio |
|---|---|---|---|---|---|
| Madrid/ep1 | 0.0119 | 0.0842 | 0.2255 | 0.0201 | ≥ 0,01 |
| Madrid/ep2 | 0.0224 | 0.0659 | 0.2215 | 0.0290 | ≥ 0,01 |
| Madrid/ep3 | 0.0403 | 0.1261 | 0.2128 | 0.0569 | ≥ 0,01 |
| Londra/ep1 | 0.0045 | 0.2588 | 0.2197 | 0.1906 | ≥ 0,01 |
| Londra/ep2 | 0.0100 | 0.2062 | 0.2197 | 0.0939 | ≥ 0,01 |
| Londra/ep3 | 0.0143 | 0.1219 | 0.2200 | 0.0573 | ≥ 0,01 |
| Melbourne/ep1 | 0.0269 | 0.2069 | 0.1931 | 0.1296 | ≥ 0,01 |
| Melbourne/ep2 | 0.0299 | 0.3160 | 0.1933 | 0.2479 | ≥ 0,01 |
| Melbourne/ep3 | 0.0268 | 0.0973 | 0.1904 | 0.0428 | ≥ 0,01 |
| PEMS08/ep1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | < 0,01 |
| PEMS04/ep1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | < 0,01 |

Criterio pre-registrato (p90 |Δ| < 0.01 ovunque, variante (a)): **NON verificato** → stadio A con entrambe le varianti (a) e (b). Su PEMS08 e PEMS04 Δ = 0 per ogni sensore (maschera piena): la replica densa è immune per costruzione.

## 3. Stadio A — le sei dichiarazioni, per contesto e variante

### Madrid (36 celle)

| confronto | non causale (congelata) | (a) nuovi: prime 24 h: valore, Δ, verdetto | (b) nuovi: media degli iniziali: valore, Δ, verdetto | (c) nuovi: permutata: valore, Δ, verdetto |
|---|---|---|---|---|
| F₀ − C | +0.0732 [+0.0586, +0.0882] + | +0.0737 [+0.0593, +0.0886] +, Δ +0.0005, **insensibile** | +0.0736 [+0.0593, +0.0884] +, Δ +0.0004, **insensibile** | +0.0713 [+0.0571, +0.0858] +, Δ -0.0019, **insensibile** |
| F₀′ − C | +0.0081 [+0.0057, +0.0108] + | +0.0082 [+0.0057, +0.0110] +, Δ +0.0001, **insensibile** | +0.0091 [+0.0066, +0.0119] +, Δ +0.0009, **insensibile** | +0.0090 [+0.0063, +0.0120] +, Δ +0.0008, **insensibile** |
| F′(1 sett.) − C (età > 1 sett.) | -0.0316 [-0.0370, -0.0268] - | -0.0317 [-0.0371, -0.0269] -, Δ -0.0000, **insensibile** | -0.0337 [-0.0390, -0.0291] -, Δ -0.0021, **SENSIBILE** | -0.0361 [-0.0420, -0.0309] -, Δ -0.0044, **SENSIBILE** |
| F′(1 sett.) − A (età > 1 sett.) | +0.0070 [+0.0040, +0.0102] + | +0.0070 [+0.0039, +0.0102] +, Δ -0.0001, **insensibile** | +0.0068 [+0.0037, +0.0100] +, Δ -0.0002, **insensibile** | +0.0068 [+0.0036, +0.0101] +, Δ -0.0003, **insensibile** |
| R-orig(1 sett.) − F′(1 sett.) (età > 1 sett.) | -0.0033 [-0.0059, -0.0010] - | -0.0035 [-0.0060, -0.0011] -, Δ -0.0001, **insensibile** | -0.0030 [-0.0054, -0.0008] -, Δ +0.0003, **insensibile** | -0.0026 [-0.0052, -0.0002] -, Δ +0.0007, **insensibile** |
| A − C | -0.0391 [-0.0441, -0.0342] - | -0.0392 [-0.0442, -0.0344] -, Δ -0.0001, **insensibile** | -0.0407 [-0.0454, -0.0364] -, Δ -0.0016, **insensibile** | -0.0430 [-0.0482, -0.0383] -, Δ -0.0040, **SENSIBILE** |

| wCE assoluta | non causale | a: valore, Δ | b: valore, Δ | c: valore, Δ |
|---|---|---|---|---|
| C | 0.9598 [+0.9348, +0.9830] | 0.9600, Δ +0.0002 | 0.9619, Δ +0.0020 | 0.9644, Δ +0.0046 |
| A | 0.9207 [+0.8937, +0.9455] | 0.9208, Δ +0.0001 | 0.9212, Δ +0.0004 | 0.9213, Δ +0.0006 |

### Londra (36 celle)

| confronto | non causale (congelata) | (a) nuovi: prime 24 h: valore, Δ, verdetto | (b) nuovi: media degli iniziali: valore, Δ, verdetto | (c) nuovi: permutata: valore, Δ, verdetto |
|---|---|---|---|---|
| F₀ − C | +0.0497 [+0.0382, +0.0624] + | +0.0498 [+0.0383, +0.0626] +, Δ +0.0001, **insensibile** | +0.0498 [+0.0382, +0.0626] +, Δ +0.0000, **insensibile** | +0.0497 [+0.0381, +0.0625] +, Δ -0.0001, **insensibile** |
| F₀′ − C | +0.0129 [+0.0096, +0.0166] + | +0.0127 [+0.0096, +0.0163] +, Δ -0.0002, **insensibile** | +0.0130 [+0.0097, +0.0166] +, Δ +0.0001, **insensibile** | +0.0130 [+0.0098, +0.0166] +, Δ +0.0001, **insensibile** |
| F′(1 sett.) − C (età > 1 sett.) | -0.0302 [-0.0343, -0.0261] - | -0.0305 [-0.0348, -0.0264] -, Δ -0.0004, **insensibile** | -0.0303 [-0.0345, -0.0262] -, Δ -0.0001, **insensibile** | -0.0304 [-0.0346, -0.0263] -, Δ -0.0002, **insensibile** |
| F′(1 sett.) − A (età > 1 sett.) | +0.0093 [+0.0063, +0.0124] + | +0.0092 [+0.0061, +0.0123] +, Δ -0.0001, **insensibile** | +0.0094 [+0.0063, +0.0124] +, Δ +0.0000, **insensibile** | +0.0094 [+0.0063, +0.0124] +, Δ +0.0001, **insensibile** |
| R-orig(1 sett.) − F′(1 sett.) (età > 1 sett.) | -0.0025 [-0.0049, +0.0004] 0 | -0.0015 [-0.0041, +0.0015] 0, Δ +0.0009, **insensibile** | -0.0023 [-0.0048, +0.0005] 0, Δ +0.0002, **insensibile** | -0.0023 [-0.0048, +0.0005] 0, Δ +0.0002, **insensibile** |
| A − C | -0.0347 [-0.0392, -0.0307] - | -0.0349 [-0.0395, -0.0308] -, Δ -0.0002, **insensibile** | -0.0349 [-0.0395, -0.0309] -, Δ -0.0002, **insensibile** | -0.0351 [-0.0396, -0.0310] -, Δ -0.0003, **insensibile** |

| wCE assoluta | non causale | a: valore, Δ | b: valore, Δ | c: valore, Δ |
|---|---|---|---|---|
| C | 0.8900 [+0.8634, +0.9151] | 0.8901, Δ +0.0001 | 0.8902, Δ +0.0002 | 0.8904, Δ +0.0004 |
| A | 0.8553 [+0.8273, +0.8816] | 0.8553, Δ -0.0000 | 0.8553, Δ +0.0000 | 0.8553, Δ +0.0000 |

### Melbourne (36 celle)

| confronto | non causale (congelata) | (a) nuovi: prime 24 h: valore, Δ, verdetto | (b) nuovi: media degli iniziali: valore, Δ, verdetto | (c) nuovi: permutata: valore, Δ, verdetto |
|---|---|---|---|---|
| F₀ − C | +0.0783 [+0.0519, +0.1024] + | +0.0742 [+0.0476, +0.0982] +, Δ -0.0041, **SENSIBILE** | +0.0797 [+0.0546, +0.1025] +, Δ +0.0014, **insensibile** | +0.0771 [+0.0519, +0.1001] +, Δ -0.0013, **insensibile** |
| F₀′ − C | +0.0015 [-0.0052, +0.0075] 0 | +0.0010 [-0.0059, +0.0071] 0, Δ -0.0005, **insensibile** | +0.0029 [-0.0034, +0.0084] 0, Δ +0.0014, **insensibile** | +0.0024 [-0.0038, +0.0079] 0, Δ +0.0009, **insensibile** |
| F′(1 sett.) − C (età > 1 sett.) | -0.0364 [-0.0432, -0.0297] - | -0.0415 [-0.0489, -0.0338] -, Δ -0.0051, **SENSIBILE** | -0.0379 [-0.0439, -0.0319] -, Δ -0.0015, **insensibile** | -0.0405 [-0.0468, -0.0340] -, Δ -0.0041, **SENSIBILE** |
| F′(1 sett.) − A (età > 1 sett.) | -0.0027 [-0.0129, +0.0062] 0 | -0.0023 [-0.0128, +0.0068] 0, Δ +0.0004, **insensibile** | -0.0018 [-0.0118, +0.0070] 0, Δ +0.0009, **insensibile** | -0.0017 [-0.0118, +0.0071] 0, Δ +0.0010, **insensibile** |
| R-orig(1 sett.) − F′(1 sett.) (età > 1 sett.) | -0.0134 [-0.0200, -0.0070] - | -0.0144 [-0.0213, -0.0077] -, Δ -0.0011, **insensibile** | -0.0136 [-0.0200, -0.0073] -, Δ -0.0002, **insensibile** | -0.0137 [-0.0200, -0.0073] -, Δ -0.0003, **insensibile** |
| A − C | -0.0384 [-0.0482, -0.0271] - | -0.0449 [-0.0558, -0.0327] -, Δ -0.0066, **SENSIBILE** | -0.0402 [-0.0499, -0.0290] -, Δ -0.0019, **insensibile** | -0.0430 [-0.0531, -0.0316] -, Δ -0.0047, **SENSIBILE** |

| wCE assoluta | non causale | a: valore, Δ | b: valore, Δ | c: valore, Δ |
|---|---|---|---|---|
| C | 0.8143 [+0.7795, +0.8475] | 0.8212, Δ +0.0069 | 0.8157, Δ +0.0014 | 0.8187, Δ +0.0043 |
| A | 0.7759 [+0.7407, +0.8094] | 0.7763, Δ +0.0004 | 0.7755, Δ -0.0005 | 0.7756, Δ -0.0003 |

### PEMS08 (36 celle)

| confronto | non causale (congelata) | (a) nuovi: prime 24 h: valore, Δ, verdetto | (b) nuovi: media degli iniziali: valore, Δ, verdetto | (c) nuovi: permutata: valore, Δ, verdetto |
|---|---|---|---|---|
| F₀ − C | +0.1565 [+0.0591, +0.2405] + | +0.1565 [+0.0591, +0.2405] +, Δ -0.0000, **insensibile** | +0.1565 [+0.0591, +0.2405] +, Δ -0.0000, **insensibile** | +0.1565 [+0.0591, +0.2405] +, Δ -0.0000, **insensibile** |
| F₀′ − C | -0.0394 [-0.0760, -0.0037] - | -0.0394 [-0.0760, -0.0037] -, Δ +0.0000, **insensibile** | -0.0394 [-0.0760, -0.0037] -, Δ +0.0000, **insensibile** | -0.0394 [-0.0760, -0.0037] -, Δ +0.0000, **insensibile** |
| F′(1 sett.) − C (età > 1 sett.) | -0.0908 [-0.1313, -0.0454] - | -0.0908 [-0.1313, -0.0454] -, Δ -0.0000, **insensibile** | -0.0908 [-0.1313, -0.0454] -, Δ -0.0000, **insensibile** | -0.0908 [-0.1313, -0.0454] -, Δ -0.0000, **insensibile** |
| F′(1 sett.) − A (età > 1 sett.) | +0.0396 [-0.0165, +0.0906] 0 | +0.0396 [-0.0165, +0.0906] 0, Δ -0.0000, **insensibile** | +0.0396 [-0.0165, +0.0906] 0, Δ -0.0000, **insensibile** | +0.0396 [-0.0165, +0.0906] 0, Δ -0.0000, **insensibile** |
| R-orig(1 sett.) − F′(1 sett.) (età > 1 sett.) | +0.0098 [-0.0396, +0.0775] 0 | +0.0098 [-0.0396, +0.0775] 0, Δ +0.0000, **insensibile** | +0.0098 [-0.0396, +0.0775] 0, Δ +0.0000, **insensibile** | +0.0098 [-0.0396, +0.0775] 0, Δ +0.0000, **insensibile** |
| A − C | -0.1325 [-0.1880, -0.0670] - | -0.1325 [-0.1880, -0.0670] -, Δ -0.0000, **insensibile** | -0.1325 [-0.1880, -0.0670] -, Δ -0.0000, **insensibile** | -0.1325 [-0.1880, -0.0670] -, Δ -0.0000, **insensibile** |

| wCE assoluta | non causale | a: valore, Δ | b: valore, Δ | c: valore, Δ |
|---|---|---|---|---|
| C | 0.6096 [+0.4988, +0.7077] | 0.6096, Δ -0.0000 | 0.6096, Δ -0.0000 | 0.6096, Δ -0.0000 |
| A | 0.4771 [+0.3848, +0.5670] | 0.4771, Δ -0.0000 | 0.4771, Δ -0.0000 | 0.4771, Δ -0.0000 |

## 4. Verdetto derivato

| variante | tutte e sei insensibili in tutti i contesti | dichiarazioni sensibili |
|---|---|---|
| (a) nuovi: prime 24 h | **NO** | Melbourne: F₀ − C (Δ -0.0041); Melbourne: F′(1 sett.) − C (età > 1 sett.) (Δ -0.0051); Melbourne: A − C (Δ -0.0066) |
| (b) nuovi: media degli iniziali | **NO** | Madrid: F′(1 sett.) − C (età > 1 sett.) (Δ -0.0021) |
| (c) nuovi: permutata | **NO** | Madrid: F′(1 sett.) − C (età > 1 sett.) (Δ -0.0044); Madrid: A − C (Δ -0.0040); Melbourne: F′(1 sett.) − C (età > 1 sett.) (Δ -0.0041); Melbourne: A − C (Δ -0.0047) |

- Dichiarazioni sensibili: **8** su 72 (confronto × contesto × variante); cambi di segno dell'intervallo: **0**.
- Livello assoluto: Δ wCE di C con la variante (c) Madrid +0.0046, Londra +0.0004, Melbourne +0.0043, PEMS08 -0.0000; di A Madrid +0.0006, Londra +0.0000, Melbourne -0.0003, PEMS08 -0.0000.
- Lettura della variante (c) (emendamento, punto 1): il modello usa la scalare per nodo in Madrid, Melbourne; dove la usa, il modello che si muove è C (senza identità), non A: le differenze sensibili sono quelle contro C.
- Regola pre-registrata: **almeno una sensibile → stadio B**, decisione del revisore (variante da usare: quelle che hanno mostrato sensibilità: a, b, c).

## 5. Dichiarazioni

- Il controllo 1 vale «scarto zero» sulla stessa macchina di E8 (Mac, pilota 188 s); sulla Spark lo scarto è il rumore di macchina della voce 22 (massimo 5.1e-08), tre ordini di grandezza sotto la soglia di sensibilità.
- Lo stadio 0 è stato ricalcolato il 13/10 con la classe critica (3 di `pesi.CLASSI`): la prima versione contava l'intermedia; distribuzioni di Δ e verdetto invariati, ρ ricalcolata.
- Solo i nodi di prova consumano la statica nello stadio A (valutazione e adattamento di F′); i modelli restano addestrati con la statica non causale: lo stadio A misura la sensibilità, non ripara.
- Preflight n. 8 (perturbazione di `m_r` dopo t₀ → `static_inputs` invariato): da aggiungere con la correzione del codice, qualunque sia l'esito (pre-registro, controlli, punto 2).

## 6. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_e14.py` | `fe1945976e0bb91a` |
| `evoluzione/analisi/e14_stadio0.py` | `132160382d964d00` |
| `evoluzione/esperimenti/esegui_e8.py` | `f9db7b5830a5b325` |
| `evoluzione/esperimenti/inserimento.py` | `bc1d6ecd562b0888` |
| `protocol/E14.md` | `b669b5d8a269f1bd` |
| `results/evoluzione/e14_stadio0.json` | `8072111407112630` |
| `results/evoluzione/e14_risultati.json` | `5019fd42135cde10` |
| `results/evoluzione/esito_e14_celle.json` | `0b4b003372f708b2` |
