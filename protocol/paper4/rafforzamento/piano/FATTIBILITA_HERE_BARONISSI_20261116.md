# Fattibilità dei dati HERE Baronissi come replica indipendente (A4) — 2026-11-16

Verifica di sola lettura su `baronissi_here.csv` (897 363 righe, 191 MB) e `baronissi_here_tratti.csv` (406 tratti). Nessun dato di Paper 4 usato. Coordinamento, sotto la responsabilità dell'autore responsabile.

## Che cosa contiene

- Area: cerchio 40.7487, 14.7717, r = 4 850 m. Periodo 2026-07-04 08:45 → 2026-11-16 09:15 UTC, passo 15 min, 10 975 bin su 130 giorni.
- Campi: velocità, velocità free-flow, `speed_ratio`, `jam_factor` (0–10), `congestion_level` (5 classi), `confidence` (0,70–0,99), `traversability`; due versioni di raccolta: `v1` fino a ottobre (nessun `segment_id`), `v2` da ottobre (id stabili).
- Qualità delle risposte: HTTP 200 nel 99,98 %; velocità mancante 0,1 %; 688 righe `closed`.

## Perché oggi non è una replica del disegno di Paper 4

Paper 4 richiede una rete **fissa** di nodi osservati per mesi (Madrid/London/Melbourne: ~10 400 timestamp continui per nodo), su cui nascondere il 60–80 % dei segmenti e misurare il guadagno dello scambio spaziale oltre il calendario. Qui:

1. **L'insieme dei segmenti cambia a ogni bin.** HERE restituisce i segmenti per cui ha dati in quel momento e li ri-suddivide (175 tratti su 406 hanno sotto-tratti). Mediana 52 tratti per bin, ma la copertura temporale per tratto è: mediana 1,7 % dei bin, 75° percentile 14 %, solo **9 tratti ≥ 90 %** (A3, raccordo, poche arterie). Raggruppando per coordinate a 3 decimali: 212 nodi, 7 con copertura ≥ 90 %, 33 con ≥ 50 %. Una rete di 7–33 nodi non sostiene un disegno a coverage 20 % con split spaziali a blocchi.
2. **Serie temporale discontinua.** 103 interruzioni > 15 min, una di 5 giorni (27 ago → 1 set), 62 giorni su 130 con meno di 96 bin. Da novembre la raccolta copre solo le 04–22 UTC (56–76 bin/giorno). `admissible_origins` di `p4b.py` richiede continuità dall'inizio della finestra alla fine del target: con 3 h di input e 2 h di orizzonte, le origini ammissibili si riducono molto.
3. **Il dato è già l'uscita di un modello.** Le velocità HERE sono stime da probe + profili storici; `confidence` < ~0,75 indica prevalenza del profilo storico. Il "calendario" è quindi in parte già dentro il target, e il guadagno spaziale oltre il calendario sarebbe sistematicamente sottostimato per costruzione: è una minaccia alla validità della domanda stessa, non solo al campione.
4. **Due regimi di raccolta** (`v1`/`v2`), con cambio di id e di orario: un confondente temporale che coincide con la divisione training/test più naturale.

Esito: **non utilizzabile come A4** per il disegno di Paper 4. Non utilizzabile nemmeno come "trasferimento senza adattamento" su rete fissa: i nodi stabili sono troppo pochi.

## Che cosa lo renderebbe utilizzabile (se si decide di continuare la raccolta)

- Lista **fissa** di segmenti interrogata a ogni bin con id stabile (`v2`, `segment_id`), ≥ 100 segmenti, scelta ora e congelata, senza guardare i dati.
- Raccolta 24 h, 15 min, ≥ 12 settimane consecutive dopo il congelamento della lista, con registro delle interruzioni; nessun cambio di versione nel periodo.
- Filtro dichiarato sulla `confidence` (es. ≥ 0,90) per tenere solo stime a prevalenza real-time, e analisi di sensibilità senza filtro.
- Target: `jam_factor` → tre classi con soglie fissate prima (es. < 4 / 4–8 / ≥ 8, che è la convenzione HERE), oppure fattore continuo per la track regressiva; dichiarare che non è una misura di sensore e che il confronto con Paper 4 è "stessa procedura, altra natura del dato".
- Grafo: distanze su rete stradale fra segmenti (non euclidee), da OSM.

Con raccolta da ora, i dati sarebbero pronti a metà febbraio 2027: compatibile con una revisione, non con la campagna A1–A3. In alternativa, dati di sensori fissi (spire/radar) dei partner o di un gestore stradale campano, se esistono, sarebbero una replica più forte e più vicina alla natura dei dati di Paper 4.

## Cifre di controllo

| Grandezza | Valore |
| --- | --- |
| righe / bin / tratti | 897 363 / 10 975 / 406 |
| tratti per bin (mediana, 90°) | 52, 85 |
| copertura per tratto (mediana, 90°, max) | 0,017, 0,40, 0,98 |
| tratti con copertura ≥ 0,9 | 9 |
| nodi (lat,lon 3 dec.) con copertura ≥ 0,5 / ≥ 0,9 | 33 / 7 |
| interruzioni > 15 min / > 1 h / max | 103 / 20 / 5 g 3 h 30 |
| giorni con < 96 bin | 62 su 130 |
| `jam_factor` 50° / 90° / 99° | 0,6 / 2,7 / 8,0 |
| tratti con `jam_factor` ≥ 4 in > 5 % dei bin | 65 |
| righe `v1` / `v2` | 744 749 / 152 614 |
