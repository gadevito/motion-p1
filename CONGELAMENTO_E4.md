# Congelamento — E4, F contro C e la politica gated

**Congelato il 2026-10-04**, commit `5d134f08fc24`. Pre-registrazione `protocol/E4.md` (impronta `e275daec5945c26b`), firmata al commit `dadd2dc2dcb59798` prima del lancio. **Ogni numero e' calcolato da `genera_congelamento_e4.py`** dai file di risultato; il verdetto e' derivato, non scritto.

## 1. Che cosa e' stato eseguito

| | |
|---|---|
| addestramenti | **nessuno**: C, E ed E′ sono i punti delle campagne precedenti, impronte verificate per cella (controllo 4: uguali fra episodio di prova e di validazione nelle 108 celle) |
| celle | prova 108 (Madrid 36, Londra 36, Melbourne 36), validazione 108; lancio: 216 celle, 0 fallite, 11.3 ore in concorrenza (8 processi) — **non e' il costo seriale** |
| durate d'adattamento | prova 6 h, 12 h, 24 h, 48 h, 1 settimana; validazione 24 h, 48 h, 1 settimana (i soli τ della politica) |
| origini d'adattamento per durata | Madrid: 6 h 5, 12 h 29, 24 h 77, 48 h 173, 1 settimana 634; Londra: 6 h 5, 12 h 29, 24 h 77, 48 h 173, 1 settimana 634; Melbourne: 6 h 5, 12 h 29, 24 h 77, 48 h 173, 1 settimana 634 |
| aggiornamenti eseguiti (= configurati) | Madrid [50]; Londra [50]; Melbourne [200] |
| controllo 3 (wCE dai punti contro le ricostruite, tolleranza 1e-6) | scarto massimo: C 1.4e-14, F0 1.4e-14, F0p 1.4e-14, F_96 1.4e-14, Fp_96 1.3e-14 |
| controllo 6 (stessi nodi e origini) | verificato in ogni cella di prova, insieme al 3 |
| controllo 7 (nodi di validazione esclusi da E, E′, C, pesi, normalizzazione) | verificato in 216 celle su 216 |
| ricampionamento | 4000 repliche, seme 20261004, partizioni × semi × nodi |

## 2. La scelta di (τ, N) sulla validazione — controllo 1

Registrata in `e4_scelta_gated.json` (impronta `81e47f64f3d63b3b`, 2026-10-03T22:54:37.053635+00:00), prima del test; i risultati del test riportano la stessa impronta (`81e47f64f3d63b3b`). Regola: minimo della wCE integrata su tutte le origini dopo t1 dell'episodio di validazione, nodi della partizione di validazione; spareggio: N maggiore, poi tau = mai, poi tau minore.

| citta' | τ | N | wCE validazione | celle | pari merito |
|---|---|---|---|---|---|
| Madrid | 48 h | 77 | 0.91723 | 36 | tau=192/N=0, tau=192/N=77 |
| Londra | 48 h | 154 | 0.85686 | 36 | tau=192/N=154 |
| Melbourne | 1 settimana | 154 | 0.83291 | 36 | tau=672/N=0, tau=672/N=77, tau=672/N=154 |

Dove piu' coppie coincidono alla nona cifra, nessun nodo di validazione aveva meno celle valide di quelle soglie: lo spareggio (N maggiore) ha deciso, come pre-registrato.

## 3. Criterio primario: gated − F₀′ ≤ 0 ovunque

| citta' | gated(τ, N) | gated − F₀′ | IC 95 % | IC ≤ +0,005 |
|---|---|---|---|---|
| Madrid | (48 h, 77) | **-0.030** | [-0.038, -0.022] | si |
| Londra | (48 h, 154) | **-0.009** | [-0.016, -0.003] | si |
| Melbourne | (1 settimana, 154) | **-0.024** | [-0.027, -0.020] | si |

**Criterio SODDISFATTO** (3/3): la politica non peggiora mai il modello unico che la ospita, e lo migliora in tutte e tre le citta' con intervallo interamente sotto lo zero.

### Secondari

| citta' | gated − C | F₀′ − C (costo del modello unico) | gated − F′(24 h) | gated − oracolo |
|---|---|---|---|---|
| Madrid | -0.021 [-0.028, -0.015] | +0.008 [+0.006, +0.011] | -0.010 [-0.015, -0.005] | -0.010 [-0.015, -0.005] (oracolo Fp_96) |
| Londra | +0.003 [-0.001, +0.008] (zero dentro) | +0.013 [+0.010, +0.017] | -0.030 [-0.041, -0.020] | +0.003 [-0.001, +0.008] (oracolo C) |
| Melbourne | -0.022 [-0.028, -0.016] | +0.001 [-0.005, +0.007] | -0.003 [-0.013, +0.006] (zero dentro) | -0.003 [-0.013, +0.006] (oracolo Fp_96) |

Rispetto a C la politica paga in 2 citta' (Madrid, Melbourne) ed e' alla pari in 1 (Londra). La frase del paper, derivata: «il modello unico con token costa rispetto a un secondo modello senza identita' da +0.001 a +0.013; con la politica gated non peggiora mai e in 2 citta' su 3 batte C».

## 4. F − C e F′ − C a 24 ore, intero periodo e terzi

| citta' | F − C | F′ − C | F′ − F | F₀ − C |
|---|---|---|---|---|
| Madrid | -0.011 [-0.020, -0.001] | -0.011 [-0.020, -0.002] | -0.001 [-0.003, +0.002] (zero dentro) | +0.073 [+0.059, +0.088] |
| Londra | +0.040 [+0.028, +0.052] | +0.034 [+0.023, +0.045] | -0.006 [-0.012, -0.001] | +0.050 [+0.038, +0.063] |
| Melbourne | -0.011 [-0.024, +0.002] (zero dentro) | -0.019 [-0.028, -0.010] | -0.008 [-0.016, +0.001] (zero dentro) | +0.078 [+0.053, +0.102] |

| citta' | braccio | terzo 1 | terzo 2 | terzo 3 |
|---|---|---|---|---|
| Madrid | F − C | -0.015 | -0.018 | +0.002 (0) |
| Madrid | F′ − C | -0.015 | -0.016 | -0.003 (0) |
| Madrid | F₀′ − C | +0.007 | +0.005 | +0.012 |
| Londra | F − C | +0.018 | +0.038 | +0.059 |
| Londra | F′ − C | +0.017 | +0.033 | +0.048 |
| Londra | F₀′ − C | +0.013 | +0.013 | +0.013 |
| Melbourne | F − C | -0.017 | -0.016 (0) | +0.004 (0) |
| Melbourne | F′ − C | -0.024 | -0.025 | -0.003 (0) |
| Melbourne | F₀′ − C | -0.001 (0) | -0.005 (0) | +0.016 |

(0) = intervallo che include lo zero. L'adattamento a 24 ore **invecchia** dove il suo vantaggio si riduce dal primo al terzo terzo; F₀′ − C e' costante per costruzione (nessun adattamento).

## 5. Curva per eta' (origini comuni, eta' > 1 settimana) — figura `figure/curva_e4.png`

| citta' | origini | F 6 h | F 12 h | F 24 h | F 48 h | F 1 settimana | F′ 6 h | F′ 12 h | F′ 24 h | F′ 48 h | F′ 1 settimana | F₀′ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Madrid | 869 | +0.215 | +0.039 | -0.006 | -0.021 | -0.033 | +0.182 | +0.035 | -0.008 | -0.021 | -0.032 | +0.009 |
| Londra | 883 | +0.232 | +0.148 | +0.050 | +0.009 | -0.032 | +0.217 | +0.138 | +0.041 | +0.001 | -0.030 | +0.013 |
| Melbourne | 854 | +0.219 | +0.090 | -0.006 | -0.019 | -0.031 | +0.096 | +0.043 | -0.015 | -0.026 | -0.036 | +0.004 |

Adattando su una settimana, F′ batte C sulle origini comuni in **3 citta' su 3** (Madrid -0.032 [-0.037, -0.027], Londra -0.030 [-0.034, -0.026], Melbourne -0.036 [-0.043, -0.030]).
Sotto le 24 ore (6 h e 12 h: 5/29 origini per 50/200 aggiornamenti) l'adattamento peggiora il modello in tutte le citta', per F e per F′, con intervallo sopra lo zero. Figura, non criterio.

## 6. Traiettoria dell'adattamento a 24 ore — figura `figure/traiettoria_e4.png`

| citta' | braccio | wCE a 0 | minimo (a k) | plateau (entro 0,5 %) | finale (a k) |
|---|---|---|---|---|---|
| Madrid | F | 1.0330 | 0.9487 (25) | 25 | 0.9491 (50) |
| Madrid | F′ | 0.9680 | 0.9485 (50) | 5 | 0.9485 (50) |
| Londra | F | 0.9397 | 0.8943 (10) | 10 | 0.9297 (50) |
| Londra | F′ | 0.9029 | 0.8870 (10) | 5 | 0.9236 (50) |
| Melbourne | F | 0.8926 | 0.8030 (200) | 200 | 0.8030 (200) |
| Melbourne | F′ | 0.8158 | 0.7940 (100) | 100 | 0.7951 (200) |

F′ raggiunge il plateau non dopo F in 3 citta' su 3. Dove la wCE finale e' sopra il minimo, i 50/200 aggiornamenti congelati (scelti per il giorno di validazione) sovradattano le 77 origini del test: e' un fatto sulla configurazione di F, dichiarato, non ritoccato.

## 7. Griglia (τ, N) sul test — figura `figure/griglia_e4.png`, NON usata per la scelta

| citta' | scelta (validazione) | wCE test della scelta | minimo sul test | wCE | coincidono |
|---|---|---|---|---|---|
| Madrid | tau=192/N=77 | 0.93843 | tau=192/N=0 | 0.93843 | si |
| Londra | tau=192/N=154 | 0.89347 | tau=672/N=0 | 0.87531 | no |
| Melbourne | tau=672/N=154 | 0.79226 | tau=192/N=0 | 0.78708 | no |

Il trasferimento dalla validazione (periodo di selezione dei punti, limitazione 8) al test e' imperfetto dove la riga dice «no»; la scelta resta quella registrata.

## 8. Costi — campione isolato, un processo (`costi_e4.json`)

| configurazione | calcolo all'inserimento | attesa dati | pronto dopo |
|---|---|---|---|
| F₀′ (modello unico, token) | 0 s | 0 | **all'installazione** |
| F′ (24 h) | 16.1 s | 24 h | 24.0 h |
| gated Madrid (τ = 48 h, N = 77) | F₀′ subito, poi 36.8 s | 48 h | F₀′ all'installazione, F′ dopo 48.0 h |
| gated Londra (τ = 48 h, N = 154) | F₀′ subito, poi 35.7 s | 48 h | F₀′ all'installazione, F′ dopo 48.0 h |
| gated Melbourne (τ = 1 settimana, N = 154) | F₀′ subito, poi 406.0 s | 168 h | F₀′ all'installazione, F′ dopo 168.1 h |

Le 18 rimisure isolate riproducono la wCE concorrente entro 1e-06. Per confronto, in E3 il riaddestramento leale (R-orig) costava 2206 s dopo 24 h di dati.

## 9. Dichiarazioni

- **Deviazione dal §8 del protocollo, dichiarata prima del lancio in E4.md**: curva a {6 h, 12 h, 24 h, 48 h, 1 settimana} invece di {1 h, 4 h, …}: sotto le 5 ore la regola delle origini non ne contiene alcuna.
- **Stima di costo del protocollo sbagliata, non deviazione**: «< 10 ore-processo» contava gli adattamenti; le 13 valutazioni per cella sull'intero periodo piu' le 12 intermedie della traiettoria hanno portato il lancio a 11.3 ore con 8 processi. Nessun parametro e' cambiato.
- **Limitazione 8**: (τ, N) scelti sul periodo di validazione cronologica, su cui i punti di C, E, E′ sono stati selezionati (non addestrati); la sezione 7 mostra quanto il trasferimento ha reso.
- La griglia di N {0, 77, 154, 231} e' stata fissata dopo l'analisi di copertura del 2/10 (quartili del massimo), come dichiarato nel protocollo; sulla validazione le soglie basse coincidono (sezione 2).
- In validazione si sono adattate le sole durate della politica (24 h, 48 h, 1 settimana): le altre non sarebbero servite a nulla.
- Analisi di copertura (punto 5, descrittiva, `copertura_e4.json`): Madrid ρ(celle valide, F − C) = +0.02 [-0.08, +0.12], F′ − C -0.06 [-0.16, +0.05]; Londra ρ(celle valide, F − C) = -0.16 [-0.26, -0.07], F′ − C -0.27 [-0.36, -0.18]; Melbourne ρ(celle valide, F − C) = +0.12 [-0.00, +0.24], F′ − C +0.10 [-0.02, +0.22]. Senza soglia di successo: ipotesi per E7.

## 10. Impronte

| file | impronta |
|---|---|
| `evoluzione/componente/adattamento.py` | `ce88e086bcbdddba` |
| `evoluzione/esperimenti/esegui_e4.py` | `b8fbdf050a27f487` |
| `evoluzione/esperimenti/costi_e4.py` | `c56d0883d7ca775c` |
| `evoluzione/analisi/analizza_e4.py` | `1fb316ed0a0ae223` |
| `evoluzione/analisi/analizza_copertura_e4.py` | `0269f7763aa09d4d` |
| `protocol/E4.md` | `e275daec5945c26b` |

**Nessun parametro scelto dopo aver visto il test**: griglie di τ e N, regola di selezione e spareggio, criterio e soglia sono nella pre-registrazione firmata; la griglia sul test e' figura.
