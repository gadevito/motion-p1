# CONGELAMENTO E15 — campagna causale end-to-end (statica a finestra espansiva)

Generato da `genera_congelamento_e15.py` al commit `1ac33ce`, 2026-10-28 13:50 UTC. Protocollo `protocol/E15.md` (impronta `31d731567da30bb4`), firmato prima di ogni numero; `e15_risultati.json` impronta `0cf754b66d6a219f`. Statica «espansiva»: iniziali con copertura media su [0, t₀); nuovo sensore con finestra espansiva da t₀ all'origine corrente, minimo 24 h. Tre citta', episodio 1, partizioni [0, 1, 2], semi [201, 202, 203, 204, 205, 206]: 54 celle; 4000 ricampionamenti congiunti (partizioni × semi × sensori, schema di E4), seme 20261023, le STESSE estrazioni per le differenze causali e per quelle congelate. Letture del protocollo del 27/10 (in `protocol/E15.md`): per A e C_A i sensori di prova sono iniziali a tutti gli effetti, copertura su [0, t₀) in addestramento, selezione e valutazione; la finestra minima di 24 h e l'espansione valgono per C, F₀, F₀′, F′ e per la selezione di k sui nodi di validazione. **Rigenerato il 28/10/2026** con l'addendum di sola analisi del revisore (sezione 7-bis) e, nello stesso giorno, con i registri dei tempi come ingresso congelato in `protocol/e15/tempi/` (sezione 7-ter): nuove impronte, numeri precedenti invariati.

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

## 7-bis. Addendum del 28/10/2026 (revisore, sola analisi; correzione datata)

Stesso congelamento rigenerato con due misure in piu', dalle stesse repliche; i numeri delle altre sezioni non cambiano. **Recupero causale** (E17): (L_C − L_F′(1 sett.))/(L_C − L_A) sulle origini con eta' > 1 settimana, rapporto delle medie nella stessa replica; anche con A − C_A al denominatore, (L_C − L_F′(1 sett.))/(L_C_A − L_A). **Riduzione del costo da parte del token**: 1 − (F₀′ − C)/(F₀ − C), tutte le origini dopo t₁.

| citta' | recupero causale, (L_C − L_A) | recupero causale, (L_C_A − L_A) | recupero congelato, 54 celle | riduzione del token, causale | riduzione del token, congelata 54 celle | repliche con denominatore ≤ 0 (rec. c. / rec. c._A / rec. cong. / rid. c. / rid. cong.) |
|---|---|---|---|---|---|---|
| Madrid | 0.796 [0.692, 0.890] | 0.822 [0.708, 0.929] | 0.800 [0.705, 0.888] | 0.895 [0.860, 0.925] | 0.894 [0.859, 0.925] | 0 / 0 / 0 / 0 / 0 |
| Londra | 0.786 [0.708, 0.858] | 0.813 [0.734, 0.883] | 0.783 [0.706, 0.856] | 0.717 [0.620, 0.795] | 0.700 [0.577, 0.781] | 0 / 0 / 0 / 0 / 0 |
| Melbourne | 1.044 [0.840, 1.451] | 1.259 [0.966, 1.889] | 1.057 [0.831, 1.527] | 0.997 [0.928, 1.110] | 0.970 [0.908, 1.062] | 0 / 0 / 0 / 0 / 0 |

## 7-ter. Registri dei tempi (ingresso congelato, `protocol/e15/tempi/`)

I marcatori `.fatto` dei 270 addestramenti (secondi, ambiente, istante), l'esito del lancio e il pilota dichiarato, copiati dai risultati nel repo: la fase E15 di `main.py` li tratta come ingresso, non li rigenera. Per ogni file l'impronta (sha256, 16 esadecimali); dove il file originale e' ancora nei risultati, l'impronta e' verificata uguale.

- **E**: 54 marcatori, 67.0 ore-macchina, mediana 82.9 min.
- **E1**: 54 marcatori, 66.9 ore-macchina, mediana 83.2 min.
- **C**: 54 marcatori, 67.3 ore-macchina, mediana 83.3 min.
- **A**: 54 marcatori, 78.8 ore-macchina, mediana 97.8 min.
- **C_A**: 54 marcatori, 78.8 ore-macchina, mediana 97.5 min.
- `esito_e15.json` `e282c18d3f514641` (verifica con i risultati: uguale).
- `pilota_tempi_16.json` `ceaf1a5c1cd27ac8` (verifica con i risultati: uguale).

Verifiche contro i risultati: 272 file confrontati, 0 diversi.

| file | secondi | impronta | verifica |
|---|---|---|---|
| `E/ck_E_Londra_p0_s1150248972.pt.fatto` | 5070 | `c61cac31a874534d` | uguale |
| `E/ck_E_Londra_p0_s1157715887.pt.fatto` | 5013 | `2d4eef0c32b2ccc9` | uguale |
| `E/ck_E_Londra_p0_s1592395901.pt.fatto` | 5042 | `58cac6876b8b19a0` | uguale |
| `E/ck_E_Londra_p0_s399595374.pt.fatto` | 4998 | `5b4e2869a48d3d9f` | uguale |
| `E/ck_E_Londra_p0_s643310434.pt.fatto` | 4968 | `fc04263c23e460da` | uguale |
| `E/ck_E_Londra_p0_s682647013.pt.fatto` | 4991 | `48d46c88f52b1ab3` | uguale |
| `E/ck_E_Londra_p1_s1150248972.pt.fatto` | 4972 | `d72a3ac066151c6b` | uguale |
| `E/ck_E_Londra_p1_s1157715887.pt.fatto` | 4974 | `6bc0c0017bc4071d` | uguale |
| `E/ck_E_Londra_p1_s1592395901.pt.fatto` | 4966 | `30ceffe5abd6d748` | uguale |
| `E/ck_E_Londra_p1_s399595374.pt.fatto` | 4973 | `b34152237fe0d8b4` | uguale |
| `E/ck_E_Londra_p1_s643310434.pt.fatto` | 4984 | `6c7ad0fc3a3fbd5e` | uguale |
| `E/ck_E_Londra_p1_s682647013.pt.fatto` | 4967 | `a3e7979c63c2feac` | uguale |
| `E/ck_E_Londra_p2_s1150248972.pt.fatto` | 3973 | `d7dfbf607ecb6c37` | uguale |
| `E/ck_E_Londra_p2_s1157715887.pt.fatto` | 5069 | `a0ad55f89612c44c` | uguale |
| `E/ck_E_Londra_p2_s1592395901.pt.fatto` | 5139 | `8fbb683273c68051` | uguale |
| `E/ck_E_Londra_p2_s399595374.pt.fatto` | 5108 | `c6459f36b902ed53` | uguale |
| `E/ck_E_Londra_p2_s643310434.pt.fatto` | 5083 | `b513a77e83f3ccf7` | uguale |
| `E/ck_E_Londra_p2_s682647013.pt.fatto` | 5093 | `2b0918c49ef23f1f` | uguale |
| `E/ck_E_Madrid_p0_s1150248972.pt.fatto` | 5082 | `fb9adf3310580e58` | uguale |
| `E/ck_E_Madrid_p0_s1157715887.pt.fatto` | 5060 | `f7cc051b76a95700` | uguale |
| `E/ck_E_Madrid_p0_s1592395901.pt.fatto` | 5073 | `abd2a32fb937709b` | uguale |
| `E/ck_E_Madrid_p0_s399595374.pt.fatto` | 5083 | `a444c3a6de6930a2` | uguale |
| `E/ck_E_Madrid_p0_s643310434.pt.fatto` | 5008 | `0fe7d027ce5e09df` | uguale |
| `E/ck_E_Madrid_p0_s682647013.pt.fatto` | 5056 | `23f3384172c23b37` | uguale |
| `E/ck_E_Madrid_p1_s1150248972.pt.fatto` | 5005 | `53ba92129aa21007` | uguale |
| `E/ck_E_Madrid_p1_s1157715887.pt.fatto` | 4995 | `1169a0a37ffc09f0` | uguale |
| `E/ck_E_Madrid_p1_s1592395901.pt.fatto` | 4943 | `ba947cf23f86a065` | uguale |
| `E/ck_E_Madrid_p1_s399595374.pt.fatto` | 4972 | `ef617774e5b3dd3d` | uguale |
| `E/ck_E_Madrid_p1_s643310434.pt.fatto` | 4967 | `59a85826d6ee7e31` | uguale |
| `E/ck_E_Madrid_p1_s682647013.pt.fatto` | 4968 | `1bc85940e9cfa471` | uguale |
| `E/ck_E_Madrid_p2_s1150248972.pt.fatto` | 4428 | `8f3e89156387ba74` | uguale |
| `E/ck_E_Madrid_p2_s1157715887.pt.fatto` | 5028 | `25188e11d1d48c0f` | uguale |
| `E/ck_E_Madrid_p2_s1592395901.pt.fatto` | 5054 | `b2e5bafb8fd25baa` | uguale |
| `E/ck_E_Madrid_p2_s399595374.pt.fatto` | 5064 | `24612a97ed075eb8` | uguale |
| `E/ck_E_Madrid_p2_s643310434.pt.fatto` | 5062 | `dfbf6111308426d2` | uguale |
| `E/ck_E_Madrid_p2_s682647013.pt.fatto` | 5057 | `a26d735977c21bd1` | uguale |
| `E/ck_E_Melbourne_p0_s1150248972.pt.fatto` | 3442 | `1e3783dfc08d8045` | uguale |
| `E/ck_E_Melbourne_p0_s1157715887.pt.fatto` | 3451 | `059da7da09992f56` | uguale |
| `E/ck_E_Melbourne_p0_s1592395901.pt.fatto` | 3433 | `cbd58240ed73932c` | uguale |
| `E/ck_E_Melbourne_p0_s399595374.pt.fatto` | 3415 | `9788409b100aa57d` | uguale |
| `E/ck_E_Melbourne_p0_s643310434.pt.fatto` | 3461 | `d87fa93702a4c9f9` | uguale |
| `E/ck_E_Melbourne_p0_s682647013.pt.fatto` | 3444 | `1cbda74da925d466` | uguale |
| `E/ck_E_Melbourne_p1_s1150248972.pt.fatto` | 3438 | `ce836b45d0ad8e41` | uguale |
| `E/ck_E_Melbourne_p1_s1157715887.pt.fatto` | 3427 | `417f0c287fc3730d` | uguale |
| `E/ck_E_Melbourne_p1_s1592395901.pt.fatto` | 3426 | `fa68324a74d2a112` | uguale |
| `E/ck_E_Melbourne_p1_s399595374.pt.fatto` | 3416 | `1e1fe9eabaacc176` | uguale |
| `E/ck_E_Melbourne_p1_s643310434.pt.fatto` | 3412 | `d9ca1bbd76e1306e` | uguale |
| `E/ck_E_Melbourne_p1_s682647013.pt.fatto` | 3456 | `0a1b8a9486e2860f` | uguale |
| `E/ck_E_Melbourne_p2_s1150248972.pt.fatto` | 3451 | `53b1d3b111ff4050` | uguale |
| `E/ck_E_Melbourne_p2_s1157715887.pt.fatto` | 3465 | `f179e1c8f78c9e3b` | uguale |
| `E/ck_E_Melbourne_p2_s1592395901.pt.fatto` | 3450 | `89021b5de1e7bf9e` | uguale |
| `E/ck_E_Melbourne_p2_s399595374.pt.fatto` | 3457 | `3fa746db0691d34b` | uguale |
| `E/ck_E_Melbourne_p2_s643310434.pt.fatto` | 3466 | `1c2798ac2cae1474` | uguale |
| `E/ck_E_Melbourne_p2_s682647013.pt.fatto` | 3432 | `9766c3a37a796662` | uguale |
| `E1/ck_E1_Londra_p0_s1150248972.pt.fatto` | 5005 | `80c79a229fc72e35` | uguale |
| `E1/ck_E1_Londra_p0_s1157715887.pt.fatto` | 5017 | `2de2802d9dd860bf` | uguale |
| `E1/ck_E1_Londra_p0_s1592395901.pt.fatto` | 5010 | `87c84d46e9b62ef9` | uguale |
| `E1/ck_E1_Londra_p0_s399595374.pt.fatto` | 5009 | `c5d63b4ada5024d2` | uguale |
| `E1/ck_E1_Londra_p0_s643310434.pt.fatto` | 5010 | `229dba66594829d1` | uguale |
| `E1/ck_E1_Londra_p0_s682647013.pt.fatto` | 5044 | `5aa5fe567f7c53f1` | uguale |
| `E1/ck_E1_Londra_p1_s1150248972.pt.fatto` | 5003 | `e0c511df51e5dc30` | uguale |
| `E1/ck_E1_Londra_p1_s1157715887.pt.fatto` | 4954 | `603710e74a1d44b0` | uguale |
| `E1/ck_E1_Londra_p1_s1592395901.pt.fatto` | 4966 | `ae0670335d242276` | uguale |
| `E1/ck_E1_Londra_p1_s399595374.pt.fatto` | 4992 | `36f9ccd3fe5d7071` | uguale |
| `E1/ck_E1_Londra_p1_s643310434.pt.fatto` | 5012 | `2b77356c54646ed6` | uguale |
| `E1/ck_E1_Londra_p1_s682647013.pt.fatto` | 4982 | `22546345f44a1c8a` | uguale |
| `E1/ck_E1_Londra_p2_s1150248972.pt.fatto` | 3473 | `83a16898df0bed9b` | uguale |
| `E1/ck_E1_Londra_p2_s1157715887.pt.fatto` | 5091 | `49ba0512b34d6cc4` | uguale |
| `E1/ck_E1_Londra_p2_s1592395901.pt.fatto` | 5035 | `5d2fb09dffb02be9` | uguale |
| `E1/ck_E1_Londra_p2_s399595374.pt.fatto` | 5106 | `3fd35a6b6509d598` | uguale |
| `E1/ck_E1_Londra_p2_s643310434.pt.fatto` | 5099 | `c22e9920a3814e85` | uguale |
| `E1/ck_E1_Londra_p2_s682647013.pt.fatto` | 5081 | `9f04ac1559a139c3` | uguale |
| `E1/ck_E1_Madrid_p0_s1150248972.pt.fatto` | 5076 | `5ac1fd876369c5c9` | uguale |
| `E1/ck_E1_Madrid_p0_s1157715887.pt.fatto` | 5054 | `f1808029caef9c71` | uguale |
| `E1/ck_E1_Madrid_p0_s1592395901.pt.fatto` | 5052 | `9c5ddefd54f20949` | uguale |
| `E1/ck_E1_Madrid_p0_s399595374.pt.fatto` | 5084 | `695d43a89c11a055` | uguale |
| `E1/ck_E1_Madrid_p0_s643310434.pt.fatto` | 5014 | `0daadeab03081fa5` | uguale |
| `E1/ck_E1_Madrid_p0_s682647013.pt.fatto` | 5075 | `6452de03e0fe7462` | uguale |
| `E1/ck_E1_Madrid_p1_s1150248972.pt.fatto` | 4984 | `22a169016d697a41` | uguale |
| `E1/ck_E1_Madrid_p1_s1157715887.pt.fatto` | 5016 | `1101dde556c2cc00` | uguale |
| `E1/ck_E1_Madrid_p1_s1592395901.pt.fatto` | 4993 | `006e0198e00649a6` | uguale |
| `E1/ck_E1_Madrid_p1_s399595374.pt.fatto` | 4971 | `86ad42f28897da35` | uguale |
| `E1/ck_E1_Madrid_p1_s643310434.pt.fatto` | 4976 | `5d263d495c7bf40b` | uguale |
| `E1/ck_E1_Madrid_p1_s682647013.pt.fatto` | 4986 | `1b30444f894d94ff` | uguale |
| `E1/ck_E1_Madrid_p2_s1150248972.pt.fatto` | 4420 | `7b10ae1c4f9b2268` | uguale |
| `E1/ck_E1_Madrid_p2_s1157715887.pt.fatto` | 5043 | `f10a1d45a5add97f` | uguale |
| `E1/ck_E1_Madrid_p2_s1592395901.pt.fatto` | 5005 | `38338ebc7c3b80c3` | uguale |
| `E1/ck_E1_Madrid_p2_s399595374.pt.fatto` | 5010 | `986eff80dcb43f05` | uguale |
| `E1/ck_E1_Madrid_p2_s643310434.pt.fatto` | 5090 | `5c1045516877ec85` | uguale |
| `E1/ck_E1_Madrid_p2_s682647013.pt.fatto` | 5072 | `b21945479822170f` | uguale |
| `E1/ck_E1_Melbourne_p0_s1150248972.pt.fatto` | 3459 | `e963a70ca3bb7378` | uguale |
| `E1/ck_E1_Melbourne_p0_s1157715887.pt.fatto` | 3418 | `0eccf9cf6e836bbc` | uguale |
| `E1/ck_E1_Melbourne_p0_s1592395901.pt.fatto` | 3448 | `5c77cd7fe6b41f2d` | uguale |
| `E1/ck_E1_Melbourne_p0_s399595374.pt.fatto` | 3448 | `25dab181f8fbad84` | uguale |
| `E1/ck_E1_Melbourne_p0_s643310434.pt.fatto` | 3466 | `270aedfef192949d` | uguale |
| `E1/ck_E1_Melbourne_p0_s682647013.pt.fatto` | 3474 | `974f834a57624df9` | uguale |
| `E1/ck_E1_Melbourne_p1_s1150248972.pt.fatto` | 3440 | `6ec5c43a56cbf6b4` | uguale |
| `E1/ck_E1_Melbourne_p1_s1157715887.pt.fatto` | 3432 | `b62206b50d1a1113` | uguale |
| `E1/ck_E1_Melbourne_p1_s1592395901.pt.fatto` | 3434 | `9a4373e2a6813444` | uguale |
| `E1/ck_E1_Melbourne_p1_s399595374.pt.fatto` | 3425 | `73a5d84d810266bc` | uguale |
| `E1/ck_E1_Melbourne_p1_s643310434.pt.fatto` | 3454 | `9fbb45983c142a4d` | uguale |
| `E1/ck_E1_Melbourne_p1_s682647013.pt.fatto` | 3424 | `4356bbf165fd1980` | uguale |
| `E1/ck_E1_Melbourne_p2_s1150248972.pt.fatto` | 3462 | `7019f7a4cfb87250` | uguale |
| `E1/ck_E1_Melbourne_p2_s1157715887.pt.fatto` | 3450 | `eab2cd0ec43e79b9` | uguale |
| `E1/ck_E1_Melbourne_p2_s1592395901.pt.fatto` | 3441 | `4990b576698a92ab` | uguale |
| `E1/ck_E1_Melbourne_p2_s399595374.pt.fatto` | 3443 | `7ccb3bd83574c8ef` | uguale |
| `E1/ck_E1_Melbourne_p2_s643310434.pt.fatto` | 3465 | `3adc914e179a0756` | uguale |
| `E1/ck_E1_Melbourne_p2_s682647013.pt.fatto` | 3464 | `8f18d07327199e80` | uguale |
| `C/C_Londra_p0_s201.json.fatto` | 5016 | `221f498404b16b39` | uguale |
| `C/C_Londra_p0_s202.json.fatto` | 5033 | `e004c3210b6658d6` | uguale |
| `C/C_Londra_p0_s203.json.fatto` | 5055 | `b1ca66f8d2cb89a0` | uguale |
| `C/C_Londra_p0_s204.json.fatto` | 5024 | `8882a475bb46dd91` | uguale |
| `C/C_Londra_p0_s205.json.fatto` | 5060 | `0862741cb26055ea` | uguale |
| `C/C_Londra_p0_s206.json.fatto` | 5021 | `899c0725eeef9153` | uguale |
| `C/C_Londra_p1_s201.json.fatto` | 5015 | `9a4f51793877f81b` | uguale |
| `C/C_Londra_p1_s202.json.fatto` | 4979 | `2f51d53de9011222` | uguale |
| `C/C_Londra_p1_s203.json.fatto` | 4994 | `bd1ebacd8bfce59e` | uguale |
| `C/C_Londra_p1_s204.json.fatto` | 4983 | `f3354e5fde2fafd4` | uguale |
| `C/C_Londra_p1_s205.json.fatto` | 4981 | `db8df9c7d6fe5a5f` | uguale |
| `C/C_Londra_p1_s206.json.fatto` | 4970 | `9cee593159e1252f` | uguale |
| `C/C_Londra_p2_s201.json.fatto` | 5122 | `58b532ccfbcefac9` | uguale |
| `C/C_Londra_p2_s202.json.fatto` | 5060 | `45ddd17fd0fe3238` | uguale |
| `C/C_Londra_p2_s203.json.fatto` | 5078 | `376614e0e3caa691` | uguale |
| `C/C_Londra_p2_s204.json.fatto` | 5050 | `6f34321e23fbc8dd` | uguale |
| `C/C_Londra_p2_s205.json.fatto` | 5062 | `08aa2f3323ffe0a8` | uguale |
| `C/C_Londra_p2_s206.json.fatto` | 4384 | `f5f1f166d2665c5a` | uguale |
| `C/C_Madrid_p0_s201.json.fatto` | 5044 | `68a2e59d3a3f388e` | uguale |
| `C/C_Madrid_p0_s202.json.fatto` | 5087 | `64bd1a23d75bd5d9` | uguale |
| `C/C_Madrid_p0_s203.json.fatto` | 5081 | `30fa7544f5bf542f` | uguale |
| `C/C_Madrid_p0_s204.json.fatto` | 5104 | `de1f19902aebd516` | uguale |
| `C/C_Madrid_p0_s205.json.fatto` | 5087 | `5f33a7acd7d5ffc7` | uguale |
| `C/C_Madrid_p0_s206.json.fatto` | 5110 | `91d7c6bd71e34877` | uguale |
| `C/C_Madrid_p1_s201.json.fatto` | 4995 | `2959bf4af43b4102` | uguale |
| `C/C_Madrid_p1_s202.json.fatto` | 4998 | `974281b7b0eba3a4` | uguale |
| `C/C_Madrid_p1_s203.json.fatto` | 5041 | `ee235994f7a52d9f` | uguale |
| `C/C_Madrid_p1_s204.json.fatto` | 5004 | `8e9ba2b80a98856c` | uguale |
| `C/C_Madrid_p1_s205.json.fatto` | 4998 | `fb03e1ba49a36efe` | uguale |
| `C/C_Madrid_p1_s206.json.fatto` | 4985 | `98ffc1c2aff6ea5f` | uguale |
| `C/C_Madrid_p2_s201.json.fatto` | 5070 | `fd9cfed25a9652a2` | uguale |
| `C/C_Madrid_p2_s202.json.fatto` | 5051 | `8d709b463210d8f0` | uguale |
| `C/C_Madrid_p2_s203.json.fatto` | 5099 | `b6cd7c22e2251503` | uguale |
| `C/C_Madrid_p2_s204.json.fatto` | 5006 | `1ab4d3ab6b335aba` | uguale |
| `C/C_Madrid_p2_s205.json.fatto` | 5053 | `c7c48531d925d8f1` | uguale |
| `C/C_Madrid_p2_s206.json.fatto` | 4602 | `4d0a5372e0599c81` | uguale |
| `C/C_Melbourne_p0_s201.json.fatto` | 3451 | `7ed33348dd88efcf` | uguale |
| `C/C_Melbourne_p0_s202.json.fatto` | 3442 | `cd58e47897de7740` | uguale |
| `C/C_Melbourne_p0_s203.json.fatto` | 3480 | `536512b2963433f2` | uguale |
| `C/C_Melbourne_p0_s204.json.fatto` | 3440 | `8e0bdc4a71f1570a` | uguale |
| `C/C_Melbourne_p0_s205.json.fatto` | 3463 | `e3c5746b35fba0ca` | uguale |
| `C/C_Melbourne_p0_s206.json.fatto` | 3461 | `af42ce45bf23f7ac` | uguale |
| `C/C_Melbourne_p1_s201.json.fatto` | 3435 | `de30ae8fccdb4e6e` | uguale |
| `C/C_Melbourne_p1_s202.json.fatto` | 3442 | `8cdd60964e0931f0` | uguale |
| `C/C_Melbourne_p1_s203.json.fatto` | 3448 | `4cf473dcd54688d5` | uguale |
| `C/C_Melbourne_p1_s204.json.fatto` | 3414 | `fe171758eb87fcf6` | uguale |
| `C/C_Melbourne_p1_s205.json.fatto` | 3458 | `241a7d6fbfe09eaa` | uguale |
| `C/C_Melbourne_p1_s206.json.fatto` | 3440 | `9563d73b6afa672c` | uguale |
| `C/C_Melbourne_p2_s201.json.fatto` | 3447 | `179fe8cfeaed9b94` | uguale |
| `C/C_Melbourne_p2_s202.json.fatto` | 3447 | `73b2a1b571570ad3` | uguale |
| `C/C_Melbourne_p2_s203.json.fatto` | 3465 | `7d5066c048dbdc16` | uguale |
| `C/C_Melbourne_p2_s204.json.fatto` | 3441 | `4c3d3d11bce0e03c` | uguale |
| `C/C_Melbourne_p2_s205.json.fatto` | 3475 | `5deaaea7e9a924c0` | uguale |
| `C/C_Melbourne_p2_s206.json.fatto` | 3442 | `86e1183a4977e0a4` | uguale |
| `A/A_Londra_p0_s201.json.fatto` | 5912 | `58de8b76995d3582` | uguale |
| `A/A_Londra_p0_s202.json.fatto` | 5933 | `9b85d627d7cbaebd` | uguale |
| `A/A_Londra_p0_s203.json.fatto` | 5925 | `0687c237d3e9f826` | uguale |
| `A/A_Londra_p0_s204.json.fatto` | 5823 | `033199f20eaba676` | uguale |
| `A/A_Londra_p0_s205.json.fatto` | 5900 | `a5f807df5e524e97` | uguale |
| `A/A_Londra_p0_s206.json.fatto` | 5871 | `7ef512174db1ebc2` | uguale |
| `A/A_Londra_p1_s201.json.fatto` | 5866 | `4ef92d8c09d6499b` | uguale |
| `A/A_Londra_p1_s202.json.fatto` | 5870 | `01951bb128f26e93` | uguale |
| `A/A_Londra_p1_s203.json.fatto` | 5862 | `4e7ae2b5a430d8d8` | uguale |
| `A/A_Londra_p1_s204.json.fatto` | 5856 | `2fe96cc30277875b` | uguale |
| `A/A_Londra_p1_s205.json.fatto` | 5860 | `d1eb48ba4b354dc0` | uguale |
| `A/A_Londra_p1_s206.json.fatto` | 5914 | `d94528e255a3d688` | uguale |
| `A/A_Londra_p2_s201.json.fatto` | 6025 | `f8c89357d9aa67d7` | uguale |
| `A/A_Londra_p2_s202.json.fatto` | 5935 | `397f0227219be416` | uguale |
| `A/A_Londra_p2_s203.json.fatto` | 5970 | `a02fe084d162b95f` | uguale |
| `A/A_Londra_p2_s204.json.fatto` | 5950 | `23c3c90a9e161e20` | uguale |
| `A/A_Londra_p2_s205.json.fatto` | 5987 | `0afe7191d536c112` | uguale |
| `A/A_Londra_p2_s206.json.fatto` | 4576 | `368a84f83f5121ed` | uguale |
| `A/A_Madrid_p0_s201.json.fatto` | 5920 | `fa13896b2944185d` | uguale |
| `A/A_Madrid_p0_s202.json.fatto` | 5934 | `9689aca1aeb11052` | uguale |
| `A/A_Madrid_p0_s203.json.fatto` | 5906 | `a0cafafc831b2e1b` | uguale |
| `A/A_Madrid_p0_s204.json.fatto` | 5945 | `370edd1a9589cf86` | uguale |
| `A/A_Madrid_p0_s205.json.fatto` | 5950 | `e4d4106e207b0a4b` | uguale |
| `A/A_Madrid_p0_s206.json.fatto` | 5915 | `ee94c8258d1d0609` | uguale |
| `A/A_Madrid_p1_s201.json.fatto` | 5850 | `045a4f4382ca8a9c` | uguale |
| `A/A_Madrid_p1_s202.json.fatto` | 5894 | `1e012b18d03feffd` | uguale |
| `A/A_Madrid_p1_s203.json.fatto` | 5915 | `49484eb0b92e0b3f` | uguale |
| `A/A_Madrid_p1_s204.json.fatto` | 5871 | `7f944bea7fdd06ff` | uguale |
| `A/A_Madrid_p1_s205.json.fatto` | 5924 | `7f35ccf32ceabfbb` | uguale |
| `A/A_Madrid_p1_s206.json.fatto` | 5790 | `a7b988df8c03c1fa` | uguale |
| `A/A_Madrid_p2_s201.json.fatto` | 5996 | `4e669026c82f4acb` | uguale |
| `A/A_Madrid_p2_s202.json.fatto` | 5910 | `4c4a2b792a4ced0a` | uguale |
| `A/A_Madrid_p2_s203.json.fatto` | 5895 | `2e79103bde3eeedc` | uguale |
| `A/A_Madrid_p2_s204.json.fatto` | 5958 | `98228c54f1a76cdb` | uguale |
| `A/A_Madrid_p2_s205.json.fatto` | 5919 | `40733c5085413d3e` | uguale |
| `A/A_Madrid_p2_s206.json.fatto` | 5145 | `f600e796225d96c5` | uguale |
| `A/A_Melbourne_p0_s201.json.fatto` | 4089 | `5bd3dce43a7d9d92` | uguale |
| `A/A_Melbourne_p0_s202.json.fatto` | 4054 | `e7eccab4a3b7e3a3` | uguale |
| `A/A_Melbourne_p0_s203.json.fatto` | 4090 | `8d4828a12fd3e282` | uguale |
| `A/A_Melbourne_p0_s204.json.fatto` | 4051 | `64776eed9c7e0778` | uguale |
| `A/A_Melbourne_p0_s205.json.fatto` | 4083 | `e361da049b9e624b` | uguale |
| `A/A_Melbourne_p0_s206.json.fatto` | 4073 | `d18c045547af6802` | uguale |
| `A/A_Melbourne_p1_s201.json.fatto` | 4056 | `0ad3bd53818e4d3b` | uguale |
| `A/A_Melbourne_p1_s202.json.fatto` | 4078 | `151b98b42b37fd8f` | uguale |
| `A/A_Melbourne_p1_s203.json.fatto` | 4038 | `e3fb24f616312e1a` | uguale |
| `A/A_Melbourne_p1_s204.json.fatto` | 4063 | `12716995cfbb11bd` | uguale |
| `A/A_Melbourne_p1_s205.json.fatto` | 4038 | `0013beb9d421dfab` | uguale |
| `A/A_Melbourne_p1_s206.json.fatto` | 4036 | `cea2e43e8b091c47` | uguale |
| `A/A_Melbourne_p2_s201.json.fatto` | 4067 | `a9c9167d895ceb1d` | uguale |
| `A/A_Melbourne_p2_s202.json.fatto` | 4095 | `1138415d791ea929` | uguale |
| `A/A_Melbourne_p2_s203.json.fatto` | 4034 | `bbc6a69c26b3abb4` | uguale |
| `A/A_Melbourne_p2_s204.json.fatto` | 4074 | `6b9b74927668257d` | uguale |
| `A/A_Melbourne_p2_s205.json.fatto` | 4074 | `2184328b671bc2a8` | uguale |
| `A/A_Melbourne_p2_s206.json.fatto` | 4071 | `043f89aeb73731a4` | uguale |
| `C_A/C_A_Londra_p0_s201.json.fatto` | 5917 | `c6fafa14a68c5fe3` | uguale |
| `C_A/C_A_Londra_p0_s202.json.fatto` | 5913 | `b7de2051299dc21c` | uguale |
| `C_A/C_A_Londra_p0_s203.json.fatto` | 5891 | `6482f4e2d3afd3f3` | uguale |
| `C_A/C_A_Londra_p0_s204.json.fatto` | 5934 | `69a2ba447e389cc6` | uguale |
| `C_A/C_A_Londra_p0_s205.json.fatto` | 5879 | `96f16c9bf220259a` | uguale |
| `C_A/C_A_Londra_p0_s206.json.fatto` | 5839 | `e3691ca437fbdc6b` | uguale |
| `C_A/C_A_Londra_p1_s201.json.fatto` | 5884 | `7320aae6be008c23` | uguale |
| `C_A/C_A_Londra_p1_s202.json.fatto` | 5850 | `b4dd09847a82ad0d` | uguale |
| `C_A/C_A_Londra_p1_s203.json.fatto` | 5829 | `e89eb0b08f37ad72` | uguale |
| `C_A/C_A_Londra_p1_s204.json.fatto` | 5820 | `68dbeebd334b1f57` | uguale |
| `C_A/C_A_Londra_p1_s205.json.fatto` | 5849 | `cbed6401223cf9c2` | uguale |
| `C_A/C_A_Londra_p1_s206.json.fatto` | 5848 | `78eb145b43baa0f7` | uguale |
| `C_A/C_A_Londra_p2_s201.json.fatto` | 5973 | `6afc97ca2edbe5ea` | uguale |
| `C_A/C_A_Londra_p2_s202.json.fatto` | 5931 | `d3234ebc6eb07fb4` | uguale |
| `C_A/C_A_Londra_p2_s203.json.fatto` | 5960 | `f20a022428a4b436` | uguale |
| `C_A/C_A_Londra_p2_s204.json.fatto` | 5930 | `7293768436dc6ade` | uguale |
| `C_A/C_A_Londra_p2_s205.json.fatto` | 5967 | `a27a4544896baa13` | uguale |
| `C_A/C_A_Londra_p2_s206.json.fatto` | 4563 | `0a57badc128cb964` | uguale |
| `C_A/C_A_Madrid_p0_s201.json.fatto` | 5877 | `d745323c7aa25487` | uguale |
| `C_A/C_A_Madrid_p0_s202.json.fatto` | 5971 | `c153e56e85da9d06` | uguale |
| `C_A/C_A_Madrid_p0_s203.json.fatto` | 5934 | `ff777560c342e312` | uguale |
| `C_A/C_A_Madrid_p0_s204.json.fatto` | 5935 | `f4a80017e5015006` | uguale |
| `C_A/C_A_Madrid_p0_s205.json.fatto` | 5954 | `c7ac9a46b58bb9ce` | uguale |
| `C_A/C_A_Madrid_p0_s206.json.fatto` | 5942 | `6e3d2749d3f94167` | uguale |
| `C_A/C_A_Madrid_p1_s201.json.fatto` | 5873 | `b727f9369dd76364` | uguale |
| `C_A/C_A_Madrid_p1_s202.json.fatto` | 5867 | `88bb582bbc0fd97c` | uguale |
| `C_A/C_A_Madrid_p1_s203.json.fatto` | 5888 | `2ca7632a21be2f8a` | uguale |
| `C_A/C_A_Madrid_p1_s204.json.fatto` | 5841 | `d1e5b0cbfa6037ff` | uguale |
| `C_A/C_A_Madrid_p1_s205.json.fatto` | 5864 | `252f3775c5e4f7df` | uguale |
| `C_A/C_A_Madrid_p1_s206.json.fatto` | 5744 | `a113a25b549a0f17` | uguale |
| `C_A/C_A_Madrid_p2_s201.json.fatto` | 6009 | `3afed0ea51b5eb6c` | uguale |
| `C_A/C_A_Madrid_p2_s202.json.fatto` | 5943 | `b833cc015d1648df` | uguale |
| `C_A/C_A_Madrid_p2_s203.json.fatto` | 5986 | `9b14e120db7242b7` | uguale |
| `C_A/C_A_Madrid_p2_s204.json.fatto` | 6007 | `aad4754dcf422c7d` | uguale |
| `C_A/C_A_Madrid_p2_s205.json.fatto` | 5907 | `ff161a4561e9639c` | uguale |
| `C_A/C_A_Madrid_p2_s206.json.fatto` | 5087 | `a1bb3ef79ca37fef` | uguale |
| `C_A/C_A_Melbourne_p0_s201.json.fatto` | 4092 | `3011c0fdff4888d2` | uguale |
| `C_A/C_A_Melbourne_p0_s202.json.fatto` | 4060 | `658c5b468212584e` | uguale |
| `C_A/C_A_Melbourne_p0_s203.json.fatto` | 4044 | `0aeb50bb6845ab70` | uguale |
| `C_A/C_A_Melbourne_p0_s204.json.fatto` | 4077 | `836035c8fb4b6863` | uguale |
| `C_A/C_A_Melbourne_p0_s205.json.fatto` | 4061 | `7ee76a5c338ca711` | uguale |
| `C_A/C_A_Melbourne_p0_s206.json.fatto` | 4048 | `16f6a42235f741a2` | uguale |
| `C_A/C_A_Melbourne_p1_s201.json.fatto` | 4048 | `70a84b24aeaccc01` | uguale |
| `C_A/C_A_Melbourne_p1_s202.json.fatto` | 4059 | `e4f2189b5e77c473` | uguale |
| `C_A/C_A_Melbourne_p1_s203.json.fatto` | 4072 | `dcb10029d55ea9b4` | uguale |
| `C_A/C_A_Melbourne_p1_s204.json.fatto` | 4050 | `b5e462cfff2dd6be` | uguale |
| `C_A/C_A_Melbourne_p1_s205.json.fatto` | 4047 | `d56ff45d527b9a73` | uguale |
| `C_A/C_A_Melbourne_p1_s206.json.fatto` | 4076 | `85fd250970ac2b4e` | uguale |
| `C_A/C_A_Melbourne_p2_s201.json.fatto` | 4053 | `90f1ab46c5926a72` | uguale |
| `C_A/C_A_Melbourne_p2_s202.json.fatto` | 4084 | `c48a6a730e8aa455` | uguale |
| `C_A/C_A_Melbourne_p2_s203.json.fatto` | 4079 | `16b7a63dba930bb4` | uguale |
| `C_A/C_A_Melbourne_p2_s204.json.fatto` | 4067 | `647bb0e2f9a20aa0` | uguale |
| `C_A/C_A_Melbourne_p2_s205.json.fatto` | 4037 | `ea542683844a1ea3` | uguale |
| `C_A/C_A_Melbourne_p2_s206.json.fatto` | 4060 | `28060dcf5db73ff1` | uguale |

## 8. Impronte

- Fonti delle pubblicate: `e14b_livelli_congelata.json` `916c2e5883c81b9c`, `e3bis_risultati.json` `2db2dd9ffece2072`.
- `results/evoluzione/e15_risultati.json` `0cf754b66d6a219f` (copia committata in `protocol/e15/`); `protocol/E15.md` `31d731567da30bb4`; `results/evoluzione/congelamento_e15.json` `fbe1d1901a8aadb2`.
- Punti di controllo per cella (sha256, 16 esadecimali) in `e15_risultati.json` → `impronte_celle` (54 celle × 5 bracci, piu' l'impronta del punto E).
