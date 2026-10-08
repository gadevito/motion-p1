# E6-bis — Il costo di trasferimento fuori da Traffic4cast (F₀ su PEMS08)

**Pre-registrazione.** Data _______ · commit ________________ · chi lancia Gabriele De Vito.

Scritta l'8/10, dopo il congelamento di E6 parte B (`CONGELAMENTO_E6.md`,
commit `83e9a85`), su richiesta del revisore, **prima di addestrare qualunque
E su PEMS08**.

## Motivo

Il paper apre con il costo di trasferimento dell'embedding medio: F₀ − C =
+0,073 / +0,050 / +0,078 nelle città (E2), e il token ignoto (E′, F₀′) è la
risposta a quel costo. Su PEMS08 il perimetro di E6 escludeva E senza token
(E2 lo aveva escluso dai bracci definitivi), quindi F₀ non esiste e la
domanda «il costo di trasferimento esiste fuori da Traffic4cast?» resta
aperta — tanto più che su PEMS08 il solo token batte C ((a) −0,039
[−0,076, −0,004]). E6-bis la chiude con 36 addestramenti di E.

## Bracci

- **E**: embedding appreso senza token, `budget 2.290`, selezione sulla rete
  iniziale, stessa configurazione di E′ di E6 (pesi `pesi_pems08`,
  `fine_periodo` 3840, canonico a 11 canali), 6 contesti-partizione × 6 semi
  (201–206) = **36 addestramenti**. Cartella `E_e6_pems08/`.
- **F₀**: copia di E con i nodi nuovi all'**embedding medio** (`copia_da_E`,
  regola di E2), nessun adattamento.
- **F(24 h), F(1 sett.)**: adattamento da E con la **configurazione di F′
  congelata in E6** (200 aggiornamenti, passo 1e-3, impronta
  `7c289e6e5d3c73d4`), come E4 usa la stessa configurazione per F e F′. Non
  si riseleziona nulla.
- C, F₀′, F′(24 h), F′(1 sett.) sono quelli di E6 (celle `predizioni_e6/`,
  stessi nodi e stesse origini: controllo bloccante).

## Confronti pre-registrati (ricampionamento congiunto, 4000 repliche)

1. **F₀ − C** su tutte le origini dopo t₁: il costo di trasferimento. Atteso
   nelle città **positivo**; su PEMS08 non si prevede, si misura.
2. **F₀′ − F₀**: il beneficio del token, a parità di tutto.
3. **F(1 sett.) − F′(1 sett.)** sulle origini comuni (età > 1 sett.) e
   **F(24 h) − F′(24 h)**: se il token conta ancora dopo l'adattamento.
4. F(1 sett.) − C sulle origini comuni, per la tabella.

## Criterio

Nessuna soglia: ogni Δ si riporta con l'intervallo e il segno, e per (1) si
dice se concorda con le tre città (E2: + in 3/3). Il risultato va nella
tabella di E6 come riga aggiuntiva, non cambia la conclusione di E6.

## Controlli

1. Nodi nuovi fuori da E, C, pesi, normalizzazione (controllo 7 di E4).
2. Stesse origini e stessi nodi delle celle di E6 (confronto letterale degli
   array `nodi` e `origini`), impronta della configurazione di F′ uguale a
   quella congelata.
3. Impronta di E registrata per cella.

## Costo

36 addestramenti di E ≈ 36 × 7,6 min ≈ **4,6 ore-processo** (pilota di E6;
E senza token costa come C), ≈ 40 min di calendario con 8 lavoratori; 36 celle
di valutazione ≈ 20 min. Nessuna rimisura isolata: E costa come E′ (419 s
isolati in E6) e non entra in una tabella dei costi nuova.

## Che cosa invalida

E addestrato con un budget o una selezione diversi da E′ di E6; F adattato
con una configurazione diversa da quella congelata; nodi od origini diversi
dalle celle di E6.
