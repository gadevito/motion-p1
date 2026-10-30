# CONGELAMENTO E18-TER — terza revisione esterna: livelli assoluti alle soglie operative

Generato da `genera_congelamento_e18ter.py` al commit `2407be0`, 2026-10-30 08:09 UTC. Protocollo `protocol/E18ter.md` (trascrizione datata della richiesta del revisore del 30/10/2026; impronta `25ee156fa3178dbf`); `e18ter_risultati.json` impronta `2a3bb86c1ba9c292`. Nessun addestramento: sola analisi da artefatti congelati di E8.

## 1. Livelli assoluti alle soglie operative (punto 2.3)

richiamo, tasso di falsi allarmi, precisione e F1 della classe congestionata alle soglie di E8 (prim = F1-ottima in validazione; par = tasso di falsi allarmi appaiato a quello di C in validazione), per braccio e contesto; finestra intera per C, A, F0, F0', gated(tau, N); origini con eta' > 1 settimana per F'(1 sett.), R-orig(1 sett.) e la C di riferimento; aggregato (confusioni sommate sulle celle, come i livelli di E8) e media sulle celle con intervallo al 95 % (ricampionamento congiunto di E8).

Regole di decisione (E8, `e8_soglie.json`, impronta `dcb93389339a6657`): prim = massimo F1 della classe congestionata su validazione, matrici sommate sulle celle; a parita' la soglia piu' alta; par = tasso di falsi allarmi uguale a quello di C alla sua soglia primaria; a parita' la piu' alta. Classe predetta: congestionata se p(congestionata) ≥ soglia, altrimenti argmax fra le altre due. Finestre: intera = tutte le origini dopo t1 (fasce sommate); > 1 sett. = origini con eta' > 1 settimana (fascia 2). Bracci sulla finestra intera: C, A, F₀, F₀′, gated(τ,N); sulla finestra > 1 settimana: C, F′(1 sett.), R-orig(1 sett.). Intervalli: 4000 ricampionamenti congiunti (partizioni × semi × posizioni dei sensori, pesi di molteplicita'), percentili 2,5/97,5, stessi indici per tutti i bracci di un contesto; seme di E8 del contesto.

**Controllo bloccante** (aggregati sulla finestra intera contro `e8_risultati.json` → `livelli`): Londra: 40 valori, scarto massimo 0.0e+00; Madrid: 40 valori, scarto massimo 0.0e+00; Melbourne: 40 valori, scarto massimo 0.0e+00; PEMS08: 40 valori, scarto massimo 0.0e+00; PEMS04: 24 valori, scarto massimo 0.0e+00 (soglia 1e-12): superato.

### 1.1. Madrid — 36 celle, 135 sensori per cella; gated(τ = 192, N = 77)

| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |
|---|---|---|---|---|---|---|---|---|
| C | intera | F1-ottima | 0.45 | 0.505 [0.450, 0.562] | 0.1965 [0.1699, 0.2256] | 0.223 [0.204, 0.243] | 0.310 [0.282, 0.337] | 0.505 / 0.1965 / 0.224 |
| A | intera | F1-ottima | 0.45 | 0.573 [0.494, 0.647] | 0.1989 [0.1606, 0.2401] | 0.244 [0.226, 0.264] | 0.342 [0.313, 0.371] | 0.574 / 0.1989 / 0.244 |
| F₀ | intera | F1-ottima | 0.30 | 0.426 [0.372, 0.479] | 0.2005 [0.1746, 0.2306] | 0.194 [0.173, 0.216] | 0.264 [0.238, 0.292] | 0.426 / 0.2005 / 0.192 |
| F₀′ | intera | F1-ottima | 0.45 | 0.487 [0.436, 0.537] | 0.1909 [0.1652, 0.2173] | 0.223 [0.203, 0.244] | 0.305 [0.278, 0.333] | 0.487 / 0.1909 / 0.222 |
| gated(τ,N) | intera | F1-ottima | composta (F₀′, F′) | 0.474 [0.391, 0.555] | 0.1553 [0.1259, 0.1879] | 0.254 [0.234, 0.274] | 0.330 [0.295, 0.364] | 0.474 / 0.1553 / 0.255 |
| C | intera | FA appaiati a C | 0.45 | 0.505 [0.450, 0.562] | 0.1965 [0.1699, 0.2256] | 0.223 [0.204, 0.243] | 0.310 [0.282, 0.337] | 0.505 / 0.1965 / 0.224 |
| A | intera | FA appaiati a C | 0.45 | 0.573 [0.494, 0.647] | 0.1989 [0.1606, 0.2401] | 0.244 [0.226, 0.264] | 0.342 [0.313, 0.371] | 0.574 / 0.1989 / 0.244 |
| F₀ | intera | FA appaiati a C | 0.30 | 0.426 [0.372, 0.479] | 0.2005 [0.1746, 0.2306] | 0.194 [0.173, 0.216] | 0.264 [0.238, 0.292] | 0.426 / 0.2005 / 0.192 |
| F₀′ | intera | FA appaiati a C | 0.45 | 0.487 [0.436, 0.537] | 0.1909 [0.1652, 0.2173] | 0.223 [0.203, 0.244] | 0.305 [0.278, 0.333] | 0.487 / 0.1909 / 0.222 |
| gated(τ,N) | intera | FA appaiati a C | composta (F₀′, F′) | 0.644 [0.574, 0.709] | 0.2612 [0.2210, 0.3031] | 0.216 [0.200, 0.233] | 0.324 [0.298, 0.349] | 0.645 / 0.2612 / 0.217 |
| C | > 1 sett. | F1-ottima | 0.45 | 0.488 [0.434, 0.543] | 0.1885 [0.1624, 0.2172] | 0.213 [0.196, 0.231] | 0.297 [0.271, 0.323] | 0.488 / 0.1885 / 0.213 |
| F′(1 sett.) | > 1 sett. | F1-ottima | 0.50 | 0.556 [0.480, 0.629] | 0.1948 [0.1598, 0.2339] | 0.230 [0.213, 0.247] | 0.325 [0.297, 0.351] | 0.556 / 0.1948 / 0.230 |
| R-orig(1 sett.) | > 1 sett. | F1-ottima | 0.50 | 0.563 [0.485, 0.635] | 0.1962 [0.1596, 0.2351] | 0.231 [0.214, 0.250] | 0.327 [0.299, 0.354] | 0.563 / 0.1962 / 0.231 |
| C | > 1 sett. | FA appaiati a C | 0.45 | 0.488 [0.434, 0.543] | 0.1885 [0.1624, 0.2172] | 0.213 [0.196, 0.231] | 0.297 [0.271, 0.323] | 0.488 / 0.1885 / 0.213 |
| F′(1 sett.) | > 1 sett. | FA appaiati a C | 0.45 | 0.649 [0.584, 0.712] | 0.2537 [0.2125, 0.2975] | 0.211 [0.195, 0.228] | 0.318 [0.294, 0.343] | 0.649 / 0.2537 / 0.211 |
| R-orig(1 sett.) | > 1 sett. | FA appaiati a C | 0.45 | 0.653 [0.587, 0.716] | 0.2537 [0.2113, 0.2997] | 0.212 [0.196, 0.229] | 0.320 [0.296, 0.345] | 0.653 / 0.2537 / 0.212 |

### 1.2. Londra — 36 celle, 135 sensori per cella; gated(τ = 192, N = 154)

| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |
|---|---|---|---|---|---|---|---|---|
| C | intera | F1-ottima | 0.45 | 0.468 [0.399, 0.532] | 0.1028 [0.0864, 0.1195] | 0.384 [0.341, 0.429] | 0.422 [0.369, 0.473] | 0.470 / 0.1028 / 0.385 |
| A | intera | F1-ottima | 0.45 | 0.539 [0.460, 0.609] | 0.1247 [0.1007, 0.1505] | 0.372 [0.336, 0.412] | 0.440 [0.392, 0.487] | 0.541 / 0.1247 / 0.372 |
| F₀ | intera | F1-ottima | 0.40 | 0.460 [0.399, 0.517] | 0.1095 [0.0918, 0.1272] | 0.368 [0.320, 0.416] | 0.407 [0.356, 0.457] | 0.461 / 0.1095 / 0.366 |
| F₀′ | intera | F1-ottima | 0.45 | 0.483 [0.421, 0.540] | 0.1147 [0.0977, 0.1322] | 0.367 [0.320, 0.414] | 0.417 [0.365, 0.467] | 0.484 / 0.1147 / 0.366 |
| gated(τ,N) | intera | F1-ottima | composta (F₀′, F′) | 0.427 [0.362, 0.491] | 0.0890 [0.0742, 0.1051] | 0.397 [0.349, 0.446] | 0.411 [0.357, 0.464] | 0.428 / 0.0890 / 0.397 |
| C | intera | FA appaiati a C | 0.45 | 0.468 [0.399, 0.532] | 0.1028 [0.0864, 0.1195] | 0.384 [0.341, 0.429] | 0.422 [0.369, 0.473] | 0.470 / 0.1028 / 0.385 |
| A | intera | FA appaiati a C | 0.45 | 0.539 [0.460, 0.609] | 0.1247 [0.1007, 0.1505] | 0.372 [0.336, 0.412] | 0.440 [0.392, 0.487] | 0.541 / 0.1247 / 0.372 |
| F₀ | intera | FA appaiati a C | 0.40 | 0.460 [0.399, 0.517] | 0.1095 [0.0918, 0.1272] | 0.368 [0.320, 0.416] | 0.407 [0.356, 0.457] | 0.461 / 0.1095 / 0.366 |
| F₀′ | intera | FA appaiati a C | 0.45 | 0.483 [0.421, 0.540] | 0.1147 [0.0977, 0.1322] | 0.367 [0.320, 0.414] | 0.417 [0.365, 0.467] | 0.484 / 0.1147 / 0.366 |
| gated(τ,N) | intera | FA appaiati a C | composta (F₀′, F′) | 0.427 [0.362, 0.491] | 0.0890 [0.0742, 0.1051] | 0.397 [0.349, 0.446] | 0.411 [0.357, 0.464] | 0.428 / 0.0890 / 0.397 |
| C | > 1 sett. | F1-ottima | 0.45 | 0.498 [0.426, 0.563] | 0.1140 [0.0960, 0.1321] | 0.392 [0.346, 0.437] | 0.439 [0.384, 0.489] | 0.499 / 0.1140 / 0.393 |
| F′(1 sett.) | > 1 sett. | F1-ottima | 0.55 | 0.382 [0.301, 0.458] | 0.0576 [0.0446, 0.0715] | 0.495 [0.440, 0.543] | 0.431 [0.360, 0.493] | 0.383 / 0.0576 / 0.496 |
| R-orig(1 sett.) | > 1 sett. | F1-ottima | 0.55 | 0.354 [0.272, 0.429] | 0.0483 [0.0361, 0.0614] | 0.520 [0.464, 0.569] | 0.421 [0.346, 0.486] | 0.355 / 0.0483 / 0.521 |
| C | > 1 sett. | FA appaiati a C | 0.45 | 0.498 [0.426, 0.563] | 0.1140 [0.0960, 0.1321] | 0.392 [0.346, 0.437] | 0.439 [0.384, 0.489] | 0.499 / 0.1140 / 0.393 |
| F′(1 sett.) | > 1 sett. | FA appaiati a C | 0.50 | 0.436 [0.355, 0.509] | 0.0768 [0.0606, 0.0938] | 0.456 [0.406, 0.504] | 0.445 [0.382, 0.502] | 0.437 / 0.0768 / 0.457 |
| R-orig(1 sett.) | > 1 sett. | FA appaiati a C | 0.50 | 0.413 [0.332, 0.485] | 0.0681 [0.0527, 0.0842] | 0.473 [0.421, 0.522] | 0.441 [0.375, 0.498] | 0.414 / 0.0681 / 0.473 |

### 1.3. Melbourne — 36 celle, 90 sensori per cella; gated(τ = 672, N = 154)

| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |
|---|---|---|---|---|---|---|---|---|
| C | intera | F1-ottima | 0.60 | 0.471 [0.411, 0.522] | 0.0450 [0.0341, 0.0573] | 0.384 [0.350, 0.414] | 0.422 [0.381, 0.459] | 0.471 / 0.0450 / 0.384 |
| A | intera | F1-ottima | 0.60 | 0.551 [0.457, 0.629] | 0.0586 [0.0382, 0.0827] | 0.359 [0.326, 0.400] | 0.435 [0.391, 0.472] | 0.551 / 0.0586 / 0.359 |
| F₀ | intera | F1-ottima | 0.40 | 0.464 [0.420, 0.503] | 0.0553 [0.0444, 0.0675] | 0.335 [0.299, 0.365] | 0.388 [0.351, 0.420] | 0.464 / 0.0552 / 0.333 |
| F₀′ | intera | F1-ottima | 0.60 | 0.483 [0.431, 0.528] | 0.0482 [0.0375, 0.0602] | 0.374 [0.340, 0.405] | 0.421 [0.381, 0.456] | 0.483 / 0.0482 / 0.373 |
| gated(τ,N) | intera | F1-ottima | composta (F₀′, F′) | 0.529 [0.462, 0.584] | 0.0561 [0.0414, 0.0728] | 0.359 [0.330, 0.388] | 0.428 [0.388, 0.463] | 0.529 / 0.0561 / 0.359 |
| C | intera | FA appaiati a C | 0.60 | 0.471 [0.411, 0.522] | 0.0450 [0.0341, 0.0573] | 0.384 [0.350, 0.414] | 0.422 [0.381, 0.459] | 0.471 / 0.0450 / 0.384 |
| A | intera | FA appaiati a C | 0.60 | 0.551 [0.457, 0.629] | 0.0586 [0.0382, 0.0827] | 0.359 [0.326, 0.400] | 0.435 [0.391, 0.472] | 0.551 / 0.0586 / 0.359 |
| F₀ | intera | FA appaiati a C | 0.40 | 0.464 [0.420, 0.503] | 0.0553 [0.0444, 0.0675] | 0.335 [0.299, 0.365] | 0.388 [0.351, 0.420] | 0.464 / 0.0552 / 0.333 |
| F₀′ | intera | FA appaiati a C | 0.60 | 0.483 [0.431, 0.528] | 0.0482 [0.0375, 0.0602] | 0.374 [0.340, 0.405] | 0.421 [0.381, 0.456] | 0.483 / 0.0482 / 0.373 |
| gated(τ,N) | intera | FA appaiati a C | composta (F₀′, F′) | 0.493 [0.427, 0.548] | 0.0468 [0.0345, 0.0607] | 0.386 [0.356, 0.414] | 0.433 [0.391, 0.468] | 0.493 / 0.0468 / 0.385 |
| C | > 1 sett. | F1-ottima | 0.60 | 0.458 [0.396, 0.513] | 0.0403 [0.0297, 0.0523] | 0.384 [0.346, 0.418] | 0.417 [0.371, 0.458] | 0.459 / 0.0403 / 0.383 |
| F′(1 sett.) | > 1 sett. | F1-ottima | 0.60 | 0.552 [0.469, 0.618] | 0.0562 [0.0388, 0.0759] | 0.349 [0.318, 0.385] | 0.427 [0.386, 0.465] | 0.552 / 0.0562 / 0.349 |
| R-orig(1 sett.) | > 1 sett. | F1-ottima | 0.60 | 0.563 [0.469, 0.640] | 0.0560 [0.0365, 0.0781] | 0.355 [0.323, 0.396] | 0.435 [0.394, 0.472] | 0.564 / 0.0559 / 0.355 |
| C | > 1 sett. | FA appaiati a C | 0.60 | 0.458 [0.396, 0.513] | 0.0403 [0.0297, 0.0523] | 0.384 [0.346, 0.418] | 0.417 [0.371, 0.458] | 0.459 / 0.0403 / 0.383 |
| F′(1 sett.) | > 1 sett. | FA appaiati a C | 0.65 | 0.486 [0.405, 0.553] | 0.0407 [0.0275, 0.0560] | 0.395 [0.361, 0.434] | 0.436 [0.389, 0.476] | 0.487 / 0.0406 / 0.395 |
| R-orig(1 sett.) | > 1 sett. | FA appaiati a C | 0.65 | 0.504 [0.409, 0.582] | 0.0417 [0.0262, 0.0593] | 0.398 [0.364, 0.443] | 0.445 [0.397, 0.484] | 0.505 / 0.0417 / 0.398 |

### 1.4. PEMS08 — 36 celle, 26 sensori per cella; gated(τ = 96, N = 231)

| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |
|---|---|---|---|---|---|---|---|---|
| C | intera | F1-ottima | 0.80 | 0.443 [0.330, 0.545] | 0.0064 [0.0033, 0.0114] | 0.541 [0.373, 0.653] | 0.477 [0.350, 0.568] | 0.450 / 0.0064 / 0.525 |
| A | intera | F1-ottima | 0.80 | 0.522 [0.321, 0.665] | 0.0043 [0.0016, 0.0087] | 0.666 [0.565, 0.744] | 0.573 [0.408, 0.658] | 0.532 / 0.0043 / 0.660 |
| F₀ | intera | F1-ottima | 0.45 | 0.504 [0.388, 0.593] | 0.0062 [0.0026, 0.0123] | 0.584 [0.435, 0.719] | 0.525 [0.426, 0.610] | 0.505 / 0.0062 / 0.562 |
| F₀′ | intera | F1-ottima | 0.75 | 0.494 [0.378, 0.591] | 0.0062 [0.0029, 0.0111] | 0.571 [0.417, 0.701] | 0.518 [0.402, 0.607] | 0.497 / 0.0062 / 0.559 |
| gated(τ,N) | intera | F1-ottima | composta (F₀′, F′) | 0.538 [0.386, 0.655] | 0.0078 [0.0039, 0.0128] | 0.528 [0.385, 0.642] | 0.526 [0.391, 0.625] | 0.549 / 0.0078 / 0.526 |
| C | intera | FA appaiati a C | 0.80 | 0.443 [0.330, 0.545] | 0.0064 [0.0033, 0.0114] | 0.541 [0.373, 0.653] | 0.477 [0.350, 0.568] | 0.450 / 0.0064 / 0.525 |
| A | intera | FA appaiati a C | 0.80 | 0.522 [0.321, 0.665] | 0.0043 [0.0016, 0.0087] | 0.666 [0.565, 0.744] | 0.573 [0.408, 0.658] | 0.532 / 0.0043 / 0.660 |
| F₀ | intera | FA appaiati a C | 0.45 | 0.504 [0.388, 0.593] | 0.0062 [0.0026, 0.0123] | 0.584 [0.435, 0.719] | 0.525 [0.426, 0.610] | 0.505 / 0.0062 / 0.562 |
| F₀′ | intera | FA appaiati a C | 0.75 | 0.494 [0.378, 0.591] | 0.0062 [0.0029, 0.0111] | 0.571 [0.417, 0.701] | 0.518 [0.402, 0.607] | 0.497 / 0.0062 / 0.559 |
| gated(τ,N) | intera | FA appaiati a C | composta (F₀′, F′) | 0.538 [0.386, 0.655] | 0.0078 [0.0039, 0.0128] | 0.528 [0.385, 0.642] | 0.526 [0.391, 0.625] | 0.549 / 0.0078 / 0.526 |
| C | > 1 sett. | F1-ottima | 0.80 | 0.444 [0.331, 0.546] | 0.0065 [0.0034, 0.0112] | 0.548 [0.374, 0.659] | 0.480 [0.352, 0.572] | 0.449 / 0.0065 / 0.533 |
| F′(1 sett.) | > 1 sett. | F1-ottima | 0.80 | 0.489 [0.340, 0.613] | 0.0058 [0.0030, 0.0092] | 0.586 [0.434, 0.684] | 0.524 [0.384, 0.623] | 0.495 / 0.0058 / 0.585 |
| R-orig(1 sett.) | > 1 sett. | F1-ottima | 0.80 | 0.516 [0.322, 0.676] | 0.0055 [0.0023, 0.0109] | 0.622 [0.486, 0.713] | 0.548 [0.388, 0.640] | 0.527 / 0.0055 / 0.610 |
| C | > 1 sett. | FA appaiati a C | 0.80 | 0.444 [0.331, 0.546] | 0.0065 [0.0034, 0.0112] | 0.548 [0.374, 0.659] | 0.480 [0.352, 0.572] | 0.449 / 0.0065 / 0.533 |
| F′(1 sett.) | > 1 sett. | FA appaiati a C | 0.80 | 0.489 [0.340, 0.613] | 0.0058 [0.0030, 0.0092] | 0.586 [0.434, 0.684] | 0.524 [0.384, 0.623] | 0.495 / 0.0058 / 0.585 |
| R-orig(1 sett.) | > 1 sett. | FA appaiati a C | 0.80 | 0.516 [0.322, 0.676] | 0.0055 [0.0023, 0.0109] | 0.622 [0.486, 0.713] | 0.548 [0.388, 0.640] | 0.527 / 0.0055 / 0.610 |

### 1.5. PEMS04 — 36 celle, 47 sensori per cella; gated(τ = 192, N = 231)

| braccio | finestra | regola | soglia | richiamo, media sulle celle [IC 95 %] | falsi allarmi [IC] | precisione [IC] | F1 cong. [IC] | aggregato: richiamo / FA / precisione |
|---|---|---|---|---|---|---|---|---|
| C | intera | F1-ottima | 0.75 | 0.611 [0.525, 0.673] | 0.0095 [0.0069, 0.0120] | 0.629 [0.488, 0.724] | 0.619 [0.507, 0.693] | 0.618 / 0.0094 / 0.642 |
| F₀′ | intera | F1-ottima | 0.75 | 0.599 [0.517, 0.658] | 0.0079 [0.0056, 0.0103] | 0.668 [0.529, 0.758] | 0.630 [0.526, 0.700] | 0.606 / 0.0079 / 0.678 |
| gated(τ,N) | intera | F1-ottima | composta (F₀′, F′) | 0.649 [0.559, 0.716] | 0.0091 [0.0064, 0.0118] | 0.652 [0.534, 0.735] | 0.650 [0.549, 0.720] | 0.658 / 0.0091 / 0.663 |
| C | intera | FA appaiati a C | 0.75 | 0.611 [0.525, 0.673] | 0.0095 [0.0069, 0.0120] | 0.629 [0.488, 0.724] | 0.619 [0.507, 0.693] | 0.618 / 0.0094 / 0.642 |
| F₀′ | intera | FA appaiati a C | 0.75 | 0.599 [0.517, 0.658] | 0.0079 [0.0056, 0.0103] | 0.668 [0.529, 0.758] | 0.630 [0.526, 0.700] | 0.606 / 0.0079 / 0.678 |
| gated(τ,N) | intera | FA appaiati a C | composta (F₀′, F′) | 0.649 [0.559, 0.716] | 0.0091 [0.0064, 0.0118] | 0.652 [0.534, 0.735] | 0.650 [0.549, 0.720] | 0.658 / 0.0091 / 0.663 |
| C | > 1 sett. | F1-ottima | 0.75 | 0.589 [0.438, 0.681] | 0.0137 [0.0102, 0.0175] | 0.584 [0.376, 0.730] | 0.584 [0.405, 0.697] | 0.613 / 0.0137 / 0.612 |
| F′(1 sett.) | > 1 sett. | F1-ottima | 0.75 | 0.610 [0.443, 0.715] | 0.0112 [0.0074, 0.0149] | 0.639 [0.449, 0.766] | 0.623 [0.446, 0.731] | 0.638 / 0.0112 / 0.668 |
| C | > 1 sett. | FA appaiati a C | 0.75 | 0.589 [0.438, 0.681] | 0.0137 [0.0102, 0.0175] | 0.584 [0.376, 0.730] | 0.584 [0.405, 0.697] | 0.613 / 0.0137 / 0.612 |
| F′(1 sett.) | > 1 sett. | FA appaiati a C | 0.70 | 0.660 [0.502, 0.760] | 0.0151 [0.0102, 0.0199] | 0.590 [0.410, 0.722] | 0.622 [0.452, 0.732] | 0.687 / 0.0151 / 0.616 |

Lettura: i livelli sulla finestra intera di C, A, F₀, F₀′ e gated(τ,N) riproducono esattamente i `livelli` di E8 (controllo); quelli di F′(1 sett.), R-orig(1 sett.) e della C di riferimento sono sulla finestra > 1 settimana, come i confronti «> 1 sett.» di E8 e di E18 parte C, e non erano in alcun congelamento (vedi §4). Le differenze fra bracci restano quelle congelate in E8/E17/E18: questa tabella ne da' i livelli, non ne cambia i confronti.

## 1-bis. Colonna wCE di F17 con la definizione del manoscritto (richiesta del 30/10, 09:45)

wCE con la definizione del manoscritto: per orizzonte Σ w_y·(−log p_y) / Σ w_y sulle coppie (origine, sensore) valide, poi media sui quattro orizzonti; per cella, poi media sulle celle; dalle probabilita' di E16 (grezze e calibrate con i parametri di e16_risultati.json); finestra intera per tutti i bracci, finestra > 1 settimana per F'(1 sett.) e C. Finestra > 1 settimana: origini con eta' > 672 passi.

**Controlli bloccanti**: (i) media sulle celle contro `e16_risultati.json` → `wce` (stessa definizione per cella: le differenze di F16 restano invariate); (ii) livelli grezzi di C, F₀, F₀′, A per cella contro gli aggregati congelati della campagna (`predizioni_e4`, `predizioni_fase3`, `predizioni_e6`, `predizioni_e6bis`: quelli che il controllo di E8 riproduce), scarto relativo; (iii) finestra > 1 settimana contro E18 parte C `wce_settimana`. Londra: e16 21 valori, scarto max 3.3e-16; campagna 144 celle×bracci, scarto relativo max 7.5e-09; E18-C 10 valori, scarto max 2.2e-16; Madrid: e16 21 valori, scarto max 4.4e-16 (con gli originali della Spark per 1 cella/e sostituita/e il 28/10; scarto della sostituzione sulla media del gruppo 9.3e-08); campagna 144 celle×bracci, scarto relativo max 6.4e-09; E18-C 10 valori, scarto max 2.2e-16; Melbourne: e16 21 valori, scarto max 3.3e-16 (con gli originali della Spark per 1 cella/e sostituita/e il 28/10; scarto della sostituzione sulla media del gruppo 7.0e-08); campagna 144 celle×bracci, scarto relativo max 1.2e-08; E18-C 10 valori, scarto max 4.4e-16; PEMS08: e16 21 valori, scarto max 2.2e-16; campagna 144 celle×bracci, scarto relativo max 7.5e-08; E18-C 10 valori, scarto max 4.4e-16 (soglie 1e-09 assolute, 1e-06 relativa): superati.

| contesto | braccio | finestra | grezzo | T (log-loss) | T (wCE) | V (log-loss) | V (wCE) |
|---|---|---|---|---|---|---|---|
| Londra | C | intera | 0.8900 | 0.8898 | 0.8898 | 0.9341 | 0.8907 |
|  | A | intera | 0.8553 | — | — | — | — |
|  | F₀ | intera | 0.9397 | 0.9389 | 0.9389 | 0.9675 | 0.9393 |
|  | F₀′ | intera | 0.9029 | 0.9025 | 0.9026 | 0.9407 | 0.9028 |
|  | F′(1 sett.) | intera | 0.8533 | 0.8533 | 0.8526 | 0.9413 | 0.8567 |
|  | F′(1 sett.) | > 1 sett. | 0.8581 | 0.8576 | 0.8572 | 0.9531 | 0.8624 |
|  | C | > 1 sett. | 0.8883 | 0.8882 | 0.8882 | 0.9347 | 0.8892 |
| Madrid | C | intera | 0.9598 | 0.9617 | 0.9597 | 1.1681 | 0.9593 |
|  | A | intera | 0.9207 | — | — | — | — |
|  | F₀ | intera | 1.0330 | 1.0605 | 1.0337 | 1.2424 | 1.0086 |
|  | F₀′ | intera | 0.9680 | 0.9697 | 0.9678 | 1.1797 | 0.9665 |
|  | F′(1 sett.) | intera | 0.9215 | 0.9233 | 0.9210 | 1.0977 | 0.9212 |
|  | F′(1 sett.) | > 1 sett. | 0.9310 | 0.9316 | 0.9303 | 1.0898 | 0.9306 |
|  | C | > 1 sett. | 0.9626 | 0.9644 | 0.9625 | 1.1561 | 0.9624 |
| Melbourne | C | intera | 0.8143 | 0.8150 | 0.8132 | 1.1747 | 0.8109 |
|  | A | intera | 0.7759 | — | — | — | — |
|  | F₀ | intera | 0.8926 | 0.9429 | 0.8947 | 1.2138 | 0.8624 |
|  | F₀′ | intera | 0.8158 | 0.8168 | 0.8151 | 1.1733 | 0.8139 |
|  | F′(1 sett.) | intera | 0.7686 | 0.7682 | 0.7697 | 1.0573 | 0.7724 |
|  | F′(1 sett.) | > 1 sett. | 0.7772 | 0.7766 | 0.7779 | 1.0455 | 0.7822 |
|  | C | > 1 sett. | 0.8136 | 0.8142 | 0.8130 | 1.1549 | 0.8118 |
| PEMS08 | C | intera | 0.6096 | 0.6071 | 0.5769 | 1.0972 | 0.5679 |
|  | A | intera | 0.4771 | — | — | — | — |
|  | F₀ | intera | 0.7661 | 0.7810 | 0.6830 | 1.1215 | 0.5835 |
|  | F₀′ | intera | 0.5702 | 0.5812 | 0.5616 | 1.1000 | 0.5709 |
|  | F′(1 sett.) | intera | 0.5035 | 0.5053 | 0.5051 | 0.9858 | 0.5066 |
|  | F′(1 sett.) | > 1 sett. | 0.5186 | 0.5202 | 0.5205 | 1.0116 | 0.5212 |
|  | C | > 1 sett. | 0.6094 | 0.6073 | 0.5774 | 1.1006 | 0.5674 |

Nota del 30/10/2026: la colonna «wCE» di F17 (`medie_test` di E16, `_nll` pesata congiuntamente anche sugli orizzonti) e' sostituita da questi valori nel generatore di F17; i valori precedenti restano in `e16_risultati.json`. Nessuna differenza fra bracci cambia.

## 2. Presentazione delle categorie (punto 2 e punto a)

Cambio di presentazione, non di analisi (30/10/2026): nei generatori delle tabelle con categorie, le due scale sono riportate in colonne separate dagli stessi intervalli — segno rispetto a zero (favourable / unfavourable / inconclusive) e margine (entro δ = 0,005: si'/no). La didascalia della tabella delle metriche di calibrazione riporta l'ECE massimo osservato, calcolato dal generatore, al posto di «below 0.04». Nessun numero cambia.

## 3. Formula della wCE e unita' della ROC (punto 3 e punto b)

Dal codice (`esegui_e4.py` `_aggregati` r. 73–85 e `_wce` r. 256–260; `componente/valutazione.py` r. 90–112, 155–172; `esegui_e16.py` `_nll` r. 173–181, `_AB`/`_wce_ab` r. 242–254; `analizza_e18.py` `_cella_A` r. 239–246, `_metriche_roc` r. 198–218): per ogni orizzonte h, wCE_h = Σ w_y·(−log p_y) / Σ w_y sulle coppie (origine, sensore) valide — una sola somma pesata congiunta, non una media di medie per sensore; p tagliata a 1e-12; pesi w_y = N_train/(3·n_y,train) per contesto × partizione, stimati sui soli nodi e periodo di addestramento; wCE = media semplice sui quattro orizzonti (un orizzonte senza bersagli validi non contribuisce); differenza fra bracci per run (contesto, partizione, seme) e media sui run; intervallo dal ricampionamento congiunto di partizioni, semi e posizioni dei sensori (i sensori rientrano nelle somme, 4 000 repliche, percentili 2,5/97,5). Precisazione per F16: la colonna «wCE» dei livelli per braccio (`_metriche` → `_nll`) e' pesata congiuntamente anche sugli orizzonti e coincide con la wCE della campagna solo se i Σw per orizzonte sono uguali. ROC di E18: unita' = run; in ogni run i punteggi p(congestionata) di tutte le terne valide (origine, sensore, orizzonte) nella finestra sono riuniti in una sola ROC empirica; il ricampionamento pesa i sensori per molteplicita'; AUC, pAUC e richiami mediati sui run. Confermato.

## 4. Deviazioni e note datate

- 30/10/2026, finestra: i livelli di F′(1 sett.), R-orig(1 sett.) e della C di riferimento sulla finestra > 1 settimana non sono in alcun congelamento (E8 somma le tre fasce d'eta'); calcolati qui dalle matrici di confusione per fascia salvate in `predizioni_e8/` (stesse soglie, stessa politica, stesso ricampionamento). Dichiarato nel protocollo §1.
- 30/10/2026, intervalli: i `livelli` di E8 sono aggregati senza intervallo; qui si aggiunge la media sulle celle con intervallo nello schema di E8 (sequenza del generatore casuale propria di questa analisi, seme di E8).

## 5. Impronte

- `results/evoluzione/e18ter_risultati.json` `2a3bb86c1ba9c292`; `protocol/E18ter.md` `25ee156fa3178dbf`; `results/evoluzione/congelamento_e18ter.json` `1983aca248349c9b`.
- Ingressi: 330 file (`e8_soglie.json`, `e8_risultati.json`, `predizioni_e8/prova_*.npz`; `e16_risultati.json`, `e18_risultati.json`, `predizioni_e16/prova_*.npz`), insieme `7d5b6bf36c55fc6c`.
- `evoluzione/analisi/analizza_e18ter.py` `0038812ad4e09695`.
