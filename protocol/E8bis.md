# E8-bis — Discriminazione e calibrazione (post hoc, dichiarato)

**Pre-registrazione.** Data _______ · commit ________________ · chi lancia Gabriele De Vito.

Scritta il 10/10 su richiesta del revisore, dopo `CONGELAMENTO_E8.md`
(commit `d8106f0`). **Descrittivo e post hoc**, nessun criterio; nessun
addestramento; stessa ricostruzione, stessi controlli e stesso
ricampionamento di E8.

## Domanda

E8 ha mostrato che la wCE e il richiamo a soglia fissa non si muovono sempre
insieme (Londra) e che il costo di trasferimento di F₀ crolla con una soglia
ricalibrata (argmax −47,6 punti di richiamo a Madrid, soglia su validazione
−7,9). Due cose vanno separate: la **discriminazione** (quanto le probabilità
ordinano bene le celle congestionate) e la **calibrazione** (dove cade la
soglia). La curva richiamo–falsi allarmi su tutta la griglia di soglie
risponde senza scegliere una soglia.

## Che cosa si calcola (sul test, per contesto, braccio, cella)

Per ogni modello di E8 (C, A, F₀, F₀′, F′(24 h), F′(48 h), F′(1 sett.),
R-orig(1 sett.); **gated escluso**: è una politica composta per fascia, non un
modello con una probabilità) le matrici di confusione **per nodo** a ciascuna
soglia della griglia di E8 (t ∈ {0,05, …, 0,95}, 19 punti, stessa regola di
decisione: congestionata se p ≥ t), sommate su orizzonti e origini: (a) tutte
le origini dopo t₁; (b) le origini comuni (età > 1 settimana), per il
confronto a una settimana. Nessuna probabilità salvata; i controlli 1 e 2 di
E8 (wCE ricalcolata = aggregato congelato a 1e-6; stessi nodi e origini)
restano bloccanti.

## Riassunti, con ricampionamento congiunto (partizioni × semi × nodi)

1. **Area sotto la curva richiamo–falsi allarmi** della classe congestionata
   (AUC, trapezi sui 19 punti più gli estremi (0, 0) e (1, 1)); per ogni
   confronto di E8 la **ΔAUC** con intervallo.
2. **Δrichiamo a falsi allarmi fissati**: ai livelli di falsi allarmi 0,5 %,
   1 %, 2 %, 5 %, 10 %, il richiamo di ciascun braccio interpolato
   linearmente sulla propria curva; la differenza fra bracci con intervallo.
   Se un livello è fuori dalla curva di un braccio (nessuna soglia lo
   raggiunge), si scrive «n.d.».
3. **Dominanza**: F′(1 sett.) domina C se Δrichiamo ≥ 0 a tutti i livelli
   raggiunti, con intervallo che non scende sotto lo zero a nessuno; se a un
   livello l'intervallo sta sotto lo zero, le curve si incrociano e si dice.
   Lo stesso per A − C e per F₀ − C.

## Lettura, scritta prima

- F′(1 sett.) − C: curva che domina ovunque → il guadagno in wCE è reale a
  ogni punto operativo e Londra è una soglia spostata; curve che si incrociano
  → compromesso vero, da riportare come tale.
- F₀ − C: ΔAUC indistinguibile da zero con ΔwCE grande → il costo di
  trasferimento è **calibrazione**; ΔAUC sotto lo zero → è anche
  discriminazione, nella misura dell'intervallo.
- A − C: la traduzione del 3–5 % in richiamo a falsi allarmi fissati.

Il generatore scrive la frase per la 5.1 solo dai segni degli intervalli; se
PEMS08 non distingue, lo scrive, come in E8.

## Costo

Stessa fase di prova di E8 con la griglia completa per nodo: ≈ 3 h di
calendario con 8 lavoratori (misurato in E8: 186 min). Nessun modello nuovo.

## File

`esegui_e8.py --fase curve` e `--fase test-curve`; `predizioni_e8/curva_*`;
`e8bis_risultati.json`; sezione 7 di `CONGELAMENTO_E8.md` rigenerato.
