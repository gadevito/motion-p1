# CONGELAMENTO E15 — campagna causale end-to-end (statica a finestra espansiva)

Generato da `genera_congelamento_e15.py` al commit `811bce9`, 2026-10-28 11:47 UTC. Protocollo `protocol/E15.md` (impronta `31d731567da30bb4`), firmato prima di ogni numero; `e15_risultati.json` impronta `269fe44c9d4a0b1c`. Statica «espansiva»: iniziali con copertura media su [0, t₀); nuovo sensore con finestra espansiva da t₀ all'origine corrente, minimo 24 h. Tre citta', episodio 1, partizioni [0, 1, 2], semi [201, 202, 203, 204, 205, 206]: 54 celle; 4000 ricampionamenti congiunti (partizioni × semi × sensori, schema di E4), seme 20261023, le STESSE estrazioni per le differenze causali e per quelle congelate. Letture del protocollo del 27/10 (in `protocol/E15.md`): per A e C_A i sensori di prova sono iniziali a tutti gli effetti, copertura su [0, t₀) in addestramento, selezione e valutazione; la finestra minima di 24 h e l'espansione valgono per C, F₀, F₀′, F′ e per la selezione di k sui nodi di validazione.

Perimetro: origini comuni dopo t1 (fasce d'eta' 1-3); per i confronti a una settimana, origini con eta' > 1 settimana (fascia 3). Congelate: predizioni_e5/ep1_* (C, A, F0', F'(1 sett.)) e predizioni_e4/prova_* (F0): stesse celle, stessi nodi, stesse origini, stesse estrazioni.

**Verdetto** = segno dell'intervallo al 95 % (sotto zero / include lo zero / sopra zero); una dichiarazione e' *confermata* se il segno causale coincide con quello congelato. Accanto, la categoria di E17 (superiorita' = limite superiore < 0; non inferiorita' = limite superiore < δ = 0.005; inconclusivo) piu' la simmetrica inferiorita' (limite inferiore > 0).

## 1. Controlli

- **Scarto zero** (`--statica congelata`, stessi semi, braccio C Madrid p0 seme 201): wCE congelata 0.941409303857, riprodotta 0.941409303857, scarto 0.000e+00; punto di controllo identico al bit: sì (scarto massimo sui parametri 0.000e+00); macchina `macOS-26.6.2-arm64-arm-64bit`. Verdetto: **scarto zero**.
- **Preflight** (15 controlli, il 15 sulla finestra espansiva), statica «espansiva»: 54/54 celle verdi.
- **Perimetro**: per ogni cella, nodi e origini coincidono con la cella congelata di E5 (ep. 1) e di E4 (verificato per cella, `controllo_perimetro`); nodi nuovi assenti da E, E′, C, pesi e normalizzazione, presenti in A e C_A.
- **Configurazione di F′**: quella congelata per citta' — Madrid 50/0.01; Londra 50/0.01; Melbourne 200/0.001 (aggiornamenti/passo), verificata contro `configurazione_F.json`; F′(1 sett.) e F′(1 sett.; k = k congelato) danno aggregati identici (adattamento deterministico).

## 2. Le sette differenze, con il verdetto causale accanto a quello congelato

### Madrid — 18 celle, 135 sensori nuovi

| dichiarazione | perimetro | causale [IC 95 %] | verdetto | categoria | congelata, 54 celle [IC 95 %] | verdetto | esito | pubblicata, 12 semi [IC 95 %] |
|---|---|---|---|---|---|---|---|---|
| F₀ − C | tutte le origini dopo t1 | +0.0746 [+0.0594, +0.0903] | sopra zero | inferiorita' | +0.0749 [+0.0593, +0.0909] | sopra zero | confermata | +0.0732 [+0.0585, +0.0873] (36 celle) |
| F₀′ − C | tutte le origini dopo t1 | +0.0078 [+0.0053, +0.0106] | sopra zero | inferiorita' | +0.0079 [+0.0054, +0.0107] | sopra zero | confermata | +0.0081 [+0.0056, +0.0109] (36 celle) |
| F′(1 sett.) − C | origini con eta' > 1 settimana | -0.0311 [-0.0368, -0.0256] | sotto zero | superiorita' | -0.0308 [-0.0363, -0.0258] | sotto zero | confermata | -0.0316 [-0.0369, -0.0266] |
| F′(1 sett.) − A | origini con eta' > 1 settimana | +0.0080 [+0.0042, +0.0120] | sopra zero | inferiorita' | +0.0077 [+0.0042, +0.0115] | sopra zero | confermata | non pubblicata a 12 semi |
| A − C | tutte le origini dopo t1 | -0.0401 [-0.0453, -0.0353] | sotto zero | superiorita' | -0.0390 [-0.0441, -0.0341] | sotto zero | confermata | -0.0391 [-0.0443, -0.0344] (36 celle) |
| A − C_A | tutte le origini dopo t1 | -0.0382 [-0.0431, -0.0335] | sotto zero | superiorita' | — | — | nuova | — |
| C_A − C | tutte le origini dopo t1 | -0.0019 [-0.0029, -0.0010] | sotto zero | superiorita' | — | — | nuova | — |

Pubblicata (12 semi) meno congelata (54 celle, stessi 6 semi): F₀ − C -0.0017; F₀′ − C +0.0002; F′(1 sett.) − C -0.0008; A − C -0.0001. Fonti: e3bis_risultati.json confronti[Madrid/Fpw-C], protocol/e14b/congelata/e14b_livelli_congelata.json.

### Londra — 18 celle, 135 sensori nuovi

| dichiarazione | perimetro | causale [IC 95 %] | verdetto | categoria | congelata, 54 celle [IC 95 %] | verdetto | esito | pubblicata, 12 semi [IC 95 %] |
|---|---|---|---|---|---|---|---|---|
| F₀ − C | tutte le origini dopo t1 | +0.0486 [+0.0363, +0.0622] | sopra zero | inferiorita' | +0.0484 [+0.0363, +0.0618] | sopra zero | confermata | +0.0497 [+0.0383, +0.0629] (36 celle) |
| F₀′ − C | tutte le origini dopo t1 | +0.0138 [+0.0096, +0.0181] | sopra zero | inferiorita' | +0.0145 [+0.0105, +0.0191] | sopra zero | confermata | +0.0129 [+0.0096, +0.0167] (36 celle) |
| F′(1 sett.) − C | origini con eta' > 1 settimana | -0.0309 [-0.0353, -0.0265] | sotto zero | superiorita' | -0.0306 [-0.0350, -0.0263] | sotto zero | confermata | -0.0302 [-0.0343, -0.0261] |
| F′(1 sett.) − A | origini con eta' > 1 settimana | +0.0084 [+0.0054, +0.0117] | sopra zero | inferiorita' | +0.0085 [+0.0054, +0.0118] | sopra zero | confermata | non pubblicata a 12 semi |
| A − C | tutte le origini dopo t1 | -0.0344 [-0.0390, -0.0299] | sotto zero | superiorita' | -0.0343 [-0.0389, -0.0298] | sotto zero | confermata | -0.0347 [-0.0392, -0.0304] (36 celle) |
| A − C_A | tutte le origini dopo t1 | -0.0332 [-0.0374, -0.0290] | sotto zero | superiorita' | — | — | nuova | — |
| C_A − C | tutte le origini dopo t1 | -0.0012 [-0.0026, -0.0001] | sotto zero | superiorita' | — | — | nuova | — |

Pubblicata (12 semi) meno congelata (54 celle, stessi 6 semi): F₀ − C +0.0014; F₀′ − C -0.0016; F′(1 sett.) − C +0.0004; A − C -0.0005. Fonti: e3bis_risultati.json confronti[Londra/Fpw-C], protocol/e14b/congelata/e14b_livelli_congelata.json.

### Melbourne — 18 celle, 90 sensori nuovi

| dichiarazione | perimetro | causale [IC 95 %] | verdetto | categoria | congelata, 54 celle [IC 95 %] | verdetto | esito | pubblicata, 12 semi [IC 95 %] |
|---|---|---|---|---|---|---|---|---|
| F₀ − C | tutte le origini dopo t1 | +0.0781 [+0.0515, +0.1035] | sopra zero | inferiorita' | +0.0807 [+0.0543, +0.1058] | sopra zero | confermata | +0.0783 [+0.0538, +0.1024] (36 celle) |
| F₀′ − C | tutte le origini dopo t1 | +0.0002 [-0.0064, +0.0066] | include lo zero | inconclusivo | +0.0024 [-0.0039, +0.0084] | include lo zero | confermata | +0.0015 [-0.0048, +0.0072] (36 celle) |
| F′(1 sett.) − C | origini con eta' > 1 settimana | -0.0400 [-0.0481, -0.0325] | sotto zero | superiorita' | -0.0360 [-0.0430, -0.0293] | sotto zero | confermata | -0.0364 [-0.0437, -0.0297] |
| F′(1 sett.) − A | origini con eta' > 1 settimana | -0.0017 [-0.0116, +0.0076] | include lo zero | inconclusivo | -0.0019 [-0.0118, +0.0074] | include lo zero | confermata | non pubblicata a 12 semi |
| A − C | tutte le origini dopo t1 | -0.0450 [-0.0566, -0.0330] | sotto zero | superiorita' | -0.0391 [-0.0498, -0.0280] | sotto zero | confermata | -0.0384 [-0.0487, -0.0276] (36 celle) |
| A − C_A | tutte le origini dopo t1 | -0.0367 [-0.0467, -0.0256] | sotto zero | superiorita' | — | — | nuova | — |
| C_A − C | tutte le origini dopo t1 | -0.0084 [-0.0124, -0.0052] | sotto zero | superiorita' | — | — | nuova | — |

Pubblicata (12 semi) meno congelata (54 celle, stessi 6 semi): F₀ − C -0.0024; F₀′ − C -0.0010; F′(1 sett.) − C -0.0004; A − C +0.0008. Fonti: e3bis_risultati.json confronti[Melbourne/Fpw-C], protocol/e14b/congelata/e14b_livelli_congelata.json.

### Esito

Le cinque dichiarazioni sono **confermate in tutte e tre le citta'**: la campagna causale diventa il risultato principale e la congelata va nel supplemento come campagna pre-registrata, con le differenze per nome.
- Madrid: A − C_A -0.0382 [-0.0431, -0.0335] (sotto zero: l’identita’ vale da sola); C_A − C -0.0019 [-0.0029, -0.0010] (sotto zero); quota di A − C spiegata dal dato in piu', (C_A − C)/(A − C) = 0.048 [0.026, 0.070].
- Londra: A − C_A -0.0332 [-0.0374, -0.0290] (sotto zero: l’identita’ vale da sola); C_A − C -0.0012 [-0.0026, -0.0001] (sotto zero); quota di A − C spiegata dal dato in piu', (C_A − C)/(A − C) = 0.035 [0.003, 0.071].
- Melbourne: A − C_A -0.0367 [-0.0467, -0.0256] (sotto zero: l’identita’ vale da sola); C_A − C -0.0084 [-0.0124, -0.0052] (sotto zero); quota di A − C spiegata dal dato in piu', (C_A − C)/(A − C) = 0.186 [0.121, 0.272].

## 3. Rapporti (F₀ − C)/(A − C) e (F₀ − C)/(A − C_A)

Rapporto delle medie nella stessa replica; tutte le origini dopo t₁. La colonna congelata usa le celle congelate (stesse estrazioni).

| citta' | (F₀ − C)/(A − C) causale | (F₀ − C)/(A − C_A) causale | (F₀ − C)/(A − C) congelata, 54 celle | (F₀ − C)/(A − C) pubblicata, 12 semi | repliche senza divario al denominatore (A − C ≥ 0; A − C_A ≥ 0; cong.) |
|---|---|---|---|---|---|
| Madrid | -1.860 [-2.268, -1.474] | -1.953 [-2.423, -1.528] | -1.920 [-2.373, -1.490] | -1.872 [-2.302, -1.476] | 0 / 0 / 0 |
| Londra | -1.414 [-1.768, -1.087] | -1.465 [-1.843, -1.124] | -1.412 [-1.755, -1.086] | -1.432 [-1.756, -1.131] | 0 / 0 / 0 |
| Melbourne | -1.735 [-2.513, -1.130] | -2.131 [-3.193, -1.365] | -2.062 [-2.970, -1.361] | -2.042 [-3.057, -1.348] | 0 / 0 / 0 |

## 4. Secondaria: F′(1 sett.; k) con k riselezionato sull'episodio di validazione causale

k scelto per citta' fra 10, 50, 200 aggiornamenti (passo congelato) con la wCE media sulle origini con eta' > 1 settimana dell'episodio di validazione (nodi di validazione, finestra espansiva); a pari merito il k minore. Scelta scritta in `e15_k_secondaria.json` (impronta `67aeef155f50d92d`, 2026-10-28T10:45 UTC) prima di ogni valutazione sul test; ogni cella di prova registra la stessa impronta (verificato).

| citta' | wCE validazione per k | k scelto | k congelato | F′(1 sett.; k) − C | verdetto | F′(1 sett.; k) − A | verdetto |
|---|---|---|---|---|---|---|---|
| Madrid | k=10: 0.9202, k=50: 0.9040, k=200: 0.8997 | 200 | 50 | -0.0336 [-0.0391, -0.0284] | sotto zero | +0.0055 [+0.0024, +0.0086] | sopra zero |
| Londra | k=10: 0.8664, k=50: 0.8602, k=200: 0.8613 | 50 | 50 | -0.0309 [-0.0353, -0.0265] | sotto zero | +0.0084 [+0.0054, +0.0117] | sopra zero |
| Melbourne | k=10: 0.8336, k=50: 0.8235, k=200: 0.8188 | 200 | 200 | -0.0400 [-0.0481, -0.0325] | sotto zero | -0.0017 [-0.0116, +0.0076] | include lo zero |

## 5. Le stesse differenze sulle origini con eta' > 1 settimana (secondarie)

| citta' | F₀ − C | F₀′ − C | A − C | A − C_A | C_A − C |
|---|---|---|---|---|---|
| Madrid | +0.0721 [+0.0574, +0.0871] (+) | +0.0088 [+0.0063, +0.0117] (+) | -0.0391 [-0.0440, -0.0345] (-) | -0.0379 [-0.0426, -0.0332] (-) | -0.0012 [-0.0021, -0.0004] (-) |
| Londra | +0.0464 [+0.0341, +0.0604] (+) | +0.0136 [+0.0095, +0.0180] (+) | -0.0393 [-0.0439, -0.0346] (-) | -0.0380 [-0.0420, -0.0337] (-) | -0.0013 [-0.0026, -0.0003] (-) |
| Melbourne | +0.0878 [+0.0615, +0.1133] (+) | +0.0035 [-0.0022, +0.0085] (0) | -0.0384 [-0.0511, -0.0250] (-) | -0.0318 [-0.0432, -0.0195] (-) | -0.0066 [-0.0103, -0.0038] (-) |

## 6. Livelli di wCE per braccio (media [IC 95 %])

| citta' | origine | C | A | C_A | F₀ | F₀′ | C (sett.) | A (sett.) | F′(1 sett.) (sett.) |
|---|---|---|---|---|---|---|---|---|---|
| Madrid | causale | 0.9610 [0.9366, 0.9841] | 0.9209 [0.8942, 0.9458] | 0.9591 [0.9343, 0.9826] | 1.0356 [1.0188, 1.0532] | 0.9689 [0.9460, 0.9909] | 0.9632 [0.9393, 0.9860] | 0.9241 [0.8989, 0.9482] | 0.9320 [0.9059, 0.9567] |
| Madrid | congelata | 0.9601 [0.9356, 0.9834] | 0.9211 [0.8944, 0.9460] | — | 1.0350 [1.0178, 1.0523] | 0.9680 [0.9449, 0.9903] | 0.9628 [0.9388, 0.9858] | 0.9243 [0.8990, 0.9485] | 0.9320 [0.9059, 0.9567] |
| Londra | causale | 0.8902 [0.8633, 0.9163] | 0.8559 [0.8271, 0.8831] | 0.8891 [0.8619, 0.9152] | 0.9389 [0.9218, 0.9559] | 0.9040 [0.8783, 0.9292] | 0.8886 [0.8615, 0.9150] | 0.8493 [0.8200, 0.8785] | 0.8577 [0.8285, 0.8869] |
| Londra | congelata | 0.8903 [0.8634, 0.9164] | 0.8560 [0.8272, 0.8833] | — | 0.9386 [0.9217, 0.9556] | 0.9048 [0.8783, 0.9308] | 0.8886 [0.8615, 0.9150] | 0.8495 [0.8201, 0.8786] | 0.8580 [0.8288, 0.8867] |
| Melbourne | causale | 0.8206 [0.7847, 0.8531] | 0.7756 [0.7404, 0.8074] | 0.8122 [0.7778, 0.8442] | 0.8987 [0.8658, 0.9283] | 0.8208 [0.7862, 0.8520] | 0.8187 [0.7784, 0.8559] | 0.7804 [0.7414, 0.8148] | 0.7787 [0.7413, 0.8133] |
| Melbourne | congelata | 0.8148 [0.7803, 0.8469] | 0.7757 [0.7403, 0.8074] | — | 0.8955 [0.8629, 0.9242] | 0.8173 [0.7838, 0.8479] | 0.8143 [0.7752, 0.8505] | 0.7803 [0.7411, 0.8149] | 0.7784 [0.7415, 0.8133] |

## 7. Costi e macchina

| braccio | addestramenti | minuti per addestramento (mediana, in concorrenza) | ore-macchina |
|---|---|---|---|
| E | 54 | 82.9 | 67.0 |
| E1 | 54 | 83.1 | 66.9 |
| C | 54 | 83.3 | 67.3 |
| A | 54 | 97.8 | 78.8 |
| C_A | 54 | 97.5 | 78.8 |

Lancio: 270 addestramenti (270 nell'ultima sessione, 0 gia' fatte, 0 fallite), 16 lavoratori × 1 filo/i, 22.9 h di calendario e 358.8 ore-macchina nell'ultima sessione; piattaforma `Linux-7.0.0-1019-nvidia-aarch64-with-glibc2.39`, 20 nuclei, torch 2.12.1+cu130, numpy 2.5.1. Adattamenti: 54 celle × 2 sulla prova (F′(1 sett.), F′(1 sett.; k)) + 3 k sulla validazione.
Pilota dichiarato (`E_pilota_e15/pilota_tempi_16.json`): 16 addestramenti E su Londra a 16 lavoratori, mediana 87.2 min, stima 24.5 h per 270 addestramenti, piattaforma `Linux-7.0.0-1019-nvidia-aarch64-with-glibc2.39`.

## 8. Impronte

- Fonti delle pubblicate: `e14b_livelli_congelata.json` `916c2e5883c81b9c`, `e3bis_risultati.json` `2db2dd9ffece2072`.
- `results/evoluzione/e15_risultati.json` `269fe44c9d4a0b1c` (copia in `protocol/e15/`); `protocol/E15.md` `31d731567da30bb4`; `results/evoluzione/congelamento_e15.json` `e5e42e6fb0e30fe7`.
- Punti di controllo per cella (sha256, 16 esadecimali) in `e15_risultati.json` → `impronte_celle` (54 celle × 5 bracci, piu' l'impronta del punto E).
