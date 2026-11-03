# E18-quater — C_A con la coverage di valutazione dei sensori nuovi uguale a quella di C

Derivato da `evoluzione/esperimenti/esegui_e18quater.py --fase analizza` da `results/evoluzione/e18quater_risultati.json` (impronta `cb3294fe6b8bafba`) il 2026-11-03 11:23 UTC; ingresso `e15_risultati.json` (impronta `82df1d02792e330e`). Modelli congelati di E15; statica dei nuovi in valutazione: «espansiva» (E15 dava a C_A la coverage su [0, t0)). Medie sulle 18 celle per citta'; intervalli al 95 % da 4000 ricampionamenti congiunti (partizioni, semi, posizioni dei nodi), seme 20261023. wCE, tutte le origini dopo t1.

| citta' | differenza | media | IC 95 % | segno | categoria | E15 (media; IC) |
|---|---|---:|---|:-:|---|---|
| Madrid | C_A_esp-C_A | +0.0010 | [+0.0003, +0.0017] | + | non inferiorita' | — |
| Madrid | C_A_esp-C | -0.0010 | [-0.0016, -0.0004] | - | superiorita' | — |
| Madrid | A-C_A_esp | -0.0392 | [-0.0441, -0.0345] | - | superiorita' | — |
| Madrid | A-C | -0.0401 | [-0.0453, -0.0353] | - | superiorita' | -0.0401; [-0.0453, -0.0353] |
| Madrid | A-C_A | -0.0382 | [-0.0431, -0.0335] | - | superiorita' | -0.0382; [-0.0431, -0.0335] |
| Madrid | C_A-C | -0.0019 | [-0.0029, -0.0010] | - | superiorita' | -0.0019; [-0.0029, -0.0010] |
| Londra | C_A_esp-C_A | -0.0000 | [-0.0001, +0.0000] | 0 | non inferiorita' | — |
| Londra | C_A_esp-C | -0.0012 | [-0.0026, -0.0002] | - | superiorita' | — |
| Londra | A-C_A_esp | -0.0331 | [-0.0373, -0.0289] | - | superiorita' | — |
| Londra | A-C | -0.0344 | [-0.0390, -0.0299] | - | superiorita' | -0.0344; [-0.0390, -0.0299] |
| Londra | A-C_A | -0.0332 | [-0.0374, -0.0290] | - | superiorita' | -0.0332; [-0.0374, -0.0290] |
| Londra | C_A-C | -0.0012 | [-0.0026, -0.0001] | - | superiorita' | -0.0012; [-0.0026, -0.0001] |
| Melbourne | C_A_esp-C_A | +0.0064 | [+0.0038, +0.0095] | + | inferiorita' | — |
| Melbourne | C_A_esp-C | -0.0020 | [-0.0041, -0.0005] | - | superiorita' | — |
| Melbourne | A-C_A_esp | -0.0430 | [-0.0537, -0.0317] | - | superiorita' | — |
| Melbourne | A-C | -0.0450 | [-0.0566, -0.0330] | - | superiorita' | -0.0450; [-0.0566, -0.0330] |
| Melbourne | A-C_A | -0.0367 | [-0.0467, -0.0256] | - | superiorita' | -0.0367; [-0.0467, -0.0256] |
| Melbourne | C_A-C | -0.0084 | [-0.0124, -0.0052] | - | superiorita' | -0.0084; [-0.0124, -0.0052] |

Quota del divario C_A − C dovuta alla coverage di valutazione, (C_A − C_A_esp)/(C_A − C); il complemento a 1 e' la quota dei dati anteriori a t0 nell'addestramento:

| citta' | quota coverage | IC 95 % |
|---|---:|---|
| Madrid | 0.505 | [0.242, 0.725] |
| Londra | -0.038 | [-0.305, 0.048] |
| Melbourne | 0.761 | [0.590, 0.935] |

Livelli (wCE, tutte le origini dopo t1):

| citta' | C | A | C_A | C_A_esp |
|---|---:|---:|---:|---:|
| Madrid | 0.9610 | 0.9209 | 0.9591 | 0.9601 |
| Londra | 0.8902 | 0.8559 | 0.8891 | 0.8890 |
| Melbourne | 0.8206 | 0.7756 | 0.8122 | 0.8186 |

Controlli: in ogni cella la ri-valutazione di C_A con la statica di E15 riproduce bit per bit gli aggregati salvati da E15; le medie di A − C, A − C_A, C_A − C coincidono con `e15_risultati.json` (scarto ≤ 1e-12); gli intervalli dei riferimenti coincidono con quelli di E15: stesso seme e stesse estrazioni (il ricampionamento di partizioni, semi e posizioni dei nodi non dipende dal vettore delle statistiche).
