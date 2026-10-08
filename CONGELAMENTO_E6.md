# Congelamento — E6, replica esterna, parte B (PEMS08)

**Congelato il 2026-10-08**, commit `4aa4e211ca17`. Pre-registrazione `protocol/E6.md` (impronta `c7a6583897215545`), firmata al commit `546bd72f7aea520f` prima del lancio. **Ogni numero e' calcolato da `genera_congelamento_e6.py`** dai file di risultato. E6-bis (`protocol/E6bis.md`, firmata al commit `168d6f5f57d721d5`) e' nella sezione 3b. La parte A (PEMS04) e' nella sezione 3c.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| dati | PEMS08, 170 sensori, 62 giorni a 15 min; estrazione con le scelte di PEMS04 (`estrazione_pems08.json`: riferimento = percentile 95 sui 118 nodi iniziali in [11, 3162), soglie [0.8, 0.5]) |
| calendario | t₀ di prova 3840 (giorno 40), t₁ = 3936; t₀ di validazione 3162; origini dopo t₁ nel test 1999, comuni (eta' > 1 sett.) 1423 |
| disegno | **6 contesti-partizione × 6 semi (201–206)** = 36 celle per braccio; 26 nodi nuovi per partizione, 156 distinti (motivo nel protocollo) |
| addestramenti | 180 completati, 0 falliti, 5.9 h di calendario con 8 lavoratori (C, A, E′, R-orig 24 h, R-orig 1 sett.); canonico a 11 canali riusato; pesi su [11, 3162) |
| F′ | configurazione selezionata su PEMS08 da E′: **200 aggiornamenti, passo 0.001** (wCE di validazione 0.4671, 36 gruppi × 6 candidati), impronta `7c289e6e5d3c73d4`, congelata prima della prova |
| gated | (τ, N) con la regola di E4 sull'episodio di validazione: **τ = 96 passi (24 h), N = 231** (wCE 0.4633); impronta `1ce676da7a5168f8` prima del test. Celle valide per nodo in validazione min/mediana/max 308/308/308: **N e' inerte per costruzione** (copertura 100 %), come dichiarato nel protocollo |
| ricampionamento | 4000 repliche congiunte (partizioni × semi × nodi), seme 20261010; 36 celle di prova |

## 2. Le affermazioni (a)–(e) su PEMS08 e il segno nelle tre citta'

| | confronto | PEMS08 | segno | Madrid | Londra | Melbourne | concorda |
|---|---|---|---|---|---|---|---|
| (a) | F₀′ − C | -0.039 [-0.076, -0.004] | − | + | + | 0 | citta' discordi |
| (b) | gated − F₀′ | -0.034 [-0.071, +0.009] | 0 | − | − | − | **no** |
| (c) | F′(1 sett.) − C, eta' > 1 sett. | -0.091 [-0.131, -0.042] | − | − | − | − | si |
| (d) | F′(24 h) − C | -0.074 [-0.118, -0.023] | − | − | + | − | citta' discordi (PEMS08 come Madrid/Melbourne) |
| (e) | F′(1 sett.) − A, eta' > 1 sett. | +0.040 [-0.019, +0.089] | 0 | + | + | 0 | citta' discordi (PEMS08 come Melbourne) |

Segni delle citta': `e5_risultati.json`, episodio 1 (la campagna principale). «−» = intervallo sotto lo zero, «+» sopra, «0» include lo zero.

## 3. Altri confronti pre-registrati

| confronto | Δ | segno |
|---|---|---|
| gated − C | -0.074 [-0.119, -0.023] | − |
| gated(τ, N = 0) − F₀′ | -0.034 [-0.071, +0.011] | 0 |
| gated(τ, N = 0) − C | -0.074 [-0.117, -0.022] | − |
| A − C | -0.133 [-0.189, -0.066] | − |
| R-orig(1 sett.) − F′(1 sett.), eta' > 1 sett. | +0.010 [-0.040, +0.079] | 0 |
| R-orig(24 h) − C | -0.011 [-0.095, +0.102] | 0 |
| R-orig(1 sett.) − R-orig(24 h), eta' > 1 sett. | -0.082 [-0.162, -0.016] | − |
| F′(1 sett.) − C, tutte le origini dopo t₁ | -0.106 [-0.145, -0.063] | − |
| F′(48 h) − C | -0.081 [-0.127, -0.029] | − |

**Equivalenza ±3 % (R-orig(1 sett.) contro F′(1 sett.), eta' > 1 sett.)**: livello di F′(1 sett.) 0.5186, banda ±0.0156; intervallo [-0.0396, +0.0792] → **non si conclude l'equivalenza**: l'intervallo esce dalla banda (26 nodi nuovi per partizione, intervalli larghi come dichiarato).

Livelli medi di wCE sulle 36 celle di prova (tutte le origini dopo t₁ / eta' > 1 sett.): A 0.477 / 0.479; C 0.610 / 0.609; F0p 0.570 / 0.569; Fp_192 0.528 / 0.537; Fp_672 0.503 / 0.519; Fp_96 0.536 / 0.541; Rorig_672 0.482 / 0.528; Rorig_96 0.599 / 0.610.

## 3b. E6-bis — il costo di trasferimento su PEMS08 (`protocol/E6bis.md`)

E senza token: 36 addestramenti, 0 falliti; F₀ all'embedding medio; F(24 h) e F(1 sett.) con la configurazione di F′ congelata (impronta `7c289e6e5d3c73d4`); 36 celle sugli stessi nodi e origini di E6 (controllo 2); 4000 repliche, seme 20261011.

| confronto | Δ | segno |
|---|---|---|
| F₀ − C (embedding medio) | +0.156 [+0.066, +0.242] | + |
| F₀′ − F₀ (il token) | -0.196 [-0.272, -0.113] | − |
| F(1 sett.) − F′(1 sett.), eta' > 1 sett. | +0.076 [+0.031, +0.120] | + |
| F(24 h) − F′(24 h) | +0.101 [+0.058, +0.150] | + |
| F(1 sett.) − C, eta' > 1 sett. | -0.015 [-0.073, +0.059] | 0 |
| F(24 h) − C | +0.028 [-0.038, +0.106] | 0 |

Il costo di trasferimento dell'embedding medio **esiste anche su PEMS08** (F₀ − C sopra lo zero; nelle citta' +0,050…+0,078 in E2); il token conta ancora dopo l'adattamento (F − F′ sopra lo zero a 24 h e a 1 settimana).

## 3c. Parte A — PEMS04, bracci definitivi (completamento, 168 origini comuni)

E′ su PEMS04: 36 addestramenti; F′ selezionata da E′ (50 aggiornamenti, passo 0.001, impronta `16a47787e7f89d5a`); gated τ = 192 passi, N = 231 (impronta `16ed7800df4b401b`); 36 celle (3 contesti × 12 semi, 47 nodi nuovi); nodi sotto N 0.0 per cella su 47 (celle valide min/mediana/max 308/308/308: N inerte anche qui, copertura 100 %). (e) non riportabile: A non esiste su PEMS04.

| | confronto | PEMS04 | segno | PEMS08 | Madrid | Londra | Melbourne |
|---|---|---|---|---|---|---|---|
| (a) | F₀′ − C | +0.003 [-0.007, +0.013] | 0 | − | + | + | 0 |
| (b) | gated − F₀′ | -0.022 [-0.031, -0.013] | − | 0 | − | − | − |
| (c) | F′(1 sett.) − C, eta' > 1 sett. | -0.033 [-0.047, -0.019] | − | − | − | − | − |
| (d) | F′(24 h) − C | -0.023 [-0.034, -0.010] | − | − | − | + | − |

- gated − C: -0.019 [-0.030, -0.007] (−)
- F′(1 sett.) − C, tutte le origini: -0.032 [-0.042, -0.022] (−)
- F′(48 h) − C: -0.026 [-0.037, -0.013] (−)

(c) su PEMS04: -0.033 [-0.047, -0.019], **segno concorde** con PEMS08 e con le tre citta'.

## 4. Nodi sotto soglia e copertura

N = 231: nodi sotto soglia 0.0 per cella (massimo 0) su 26; celle valide per nodo min/mediana/max 308/308/308. **Non e' un risultato**: il rilascio e' completo per costruzione (protocollo, nota derivata); gated(τ, N) e gated(τ, 0) coincidono (Δ identiche nella tabella 3).

## 5. Costi (campione isolato: partizione 0, semi 201–203, un processo)

| braccio | addestramento (s, mediana) | adattamento (s, mediana) | totale per un nodo nuovo (s) |
|---|---|---|---|
| C | 441 | 0.0 | 441 |
| A | 503 | 0.0 | 503 |
| E′ | 419 | 0.0 | 419 |
| F₀′ (da E′) | 419 | 0.0 | 419 |
| F′(24 h) | 419 | 13.8 | 433 |
| F′(1 sett.) | 419 | 124.5 | 544 |
| R-orig(24 h) | 392 | 0.0 | 392 |
| R-orig(1 sett.) | 413 | 0.0 | 413 |

Pilota pre-firma: C 454 s; campione isolato: C 441 s. R-orig(1 sett.) costa **3.3×** il solo adattamento di F′(1 sett.) e **0.76×** E′ + adattamento: su PEMS08 (118 nodi iniziali, 3 151 origini) il riaddestramento e' economico e il vantaggio di costo dell'adattamento, netto nelle citta' (E3-bis: almeno 6×), qui si riduce al solo adattamento. Lo si dice.

## 6. Difetti emersi e dichiarati

- `da_E1` (`esegui_e2.py`) costruiva il predittore a nove canali qualunque fosse la sorgente: su PEMS (undici canali) la copia da E′ falliva. Corretto leggendo la sorgente dal punto di controllo (commit `6629f40`); collaudi 8/8 a scarto 0, 37/37, 25/25. Nelle citta' il comportamento e' identico: nessun risultato precedente cambia.

## 7. Che cosa dice al paper

Su PEMS08, con intervallo che esclude lo zero: (a), (c), (d). La tesi a una settimana — (c) F′(1 sett.) − C sulle origini comuni — **regge** fuori da Traffic4cast; i segni concordano con le tre citta' per 1 affermazione su 5 (tabella 2). Dove PEMS08 differisce dalle citta' il paper lo riporta nella stessa tabella, senza spiegazioni post hoc. La soglia N non si misura su PEMS08 (copertura 100 %); τ scelto in validazione = 96 passi.

## 8. Impronte

| file | impronta |
|---|---|
| `evoluzione/esperimenti/esegui_e6.py` | `00f7b0442c08f98c` |
| `evoluzione/esperimenti/esegui_e6a.py` | `56f8ea3ad50ac238` |
| `evoluzione/esperimenti/estrai_pems04.py` | `93d98cf3d58bbb95` |
| `evoluzione/esperimenti/calendario_pems08.py` | `35bc7585e8732454` |
| `evoluzione/esperimenti/esegui_e2.py` | `cc43cf3ac7128515` |
| `protocol/E6.md` | `c7a6583897215545` |
| `protocol/E6bis.md` | `1d74950bf0f0ba9a` |
| configurazione F′ | `7c289e6e5d3c73d4` |
| scelta gated | `1ce676da7a5168f8` |
