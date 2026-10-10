# Costi appaiati per contesto — F′(1 sett.) contro R-orig(1 sett.), stessa macchina

Generato da `evoluzione/esperimenti/costi_appaiati.py` il 2026-10-10; numeri in `results/evoluzione/costi_appaiati.json` (impronta `7eec120643b41283`). Campione isolato, un processo: partizione 0, semi 201-203 (citta'); PEMS08 da E6 §5. F′ rimisurato qui in tutte le citta' (ogni wCE riproduce la fase valuta di E4 entro 1e-6); R-orig(1 sett.) dai manifesti isolati di E3-bis. Mediane sui semi.

| contesto | n | F′(24 h) | F′(1 sett.) | aggiornamenti di F | R-orig(1 sett.) | R-orig / F′(1 sett.) |
|---|---|---|---|---|---|---|
| Madrid | 3 | 14.0 s | **151 s** | 50 | **2272 s** | 15.0× |
| Londra | 3 | 14.0 s | **144 s** | 50 | **2270 s** | 15.8× |
| Melbourne | 3 | 38.0 s | **404 s** | 200 | **1489 s** | 3.7× |
| PEMS08 | 3 | 13.8 s | **124 s** | cfg E6 | **413 s** | 3.3× |

- Il **2268 s** di R-orig(1 sett.) in `costi_e3bis.json` e' la mediana sulle 9 celle delle tre citta' (Madrid 2272 s, Londra 2270 s, Melbourne 1489 s): non appartiene a una citta'.
- F′(1 sett.) a Melbourne in `costi_e4.json`: 406 s (rimisura di oggi: 404 s).
- Il «almeno 6×» di E3-bis §3 divideva la mediana sulle tre citta' per il solo F′(1 sett.) di Melbourne: i rapporti per citta' sono nella colonna a destra.
- **Che cosa misura il tempo di F′, e perche' Melbourne costa di piu'.** E' il tempo per cella, un processo, un filo di torch: copia del punto di controllo di E′, costruzione dei lotti su tutte le origini in (t₀, t₀+L] (77 a 24 h, 634 a 1 sett.) e `aggiornamenti` passi di Adam sulla tabella dei nodi di prova della partizione (Madrid 135, Londra 135, Melbourne 90 nodi), con (passo, aggiornamenti) scelti su validazione per citta' in E4 (`selezione_F_griglia/configurazione_F.json`): aggiornamenti Madrid 50, Londra 50, Melbourne 200. Il rapporto con Madrid e' Londra 1.0× a 24 h e 0.9× a 1 sett.; Melbourne 2.7× a 24 h e 2.7× a 1 sett. Ogni aggiornamento e' un passaggio completo (gradiente a lotto pieno, `adatta`) su tutte le origini della finestra e tutti i nodi di prova, quindi il tempo e' ∝ aggiornamenti × origini × nodi: il rapporto fra citta' e' lo stesso alle due finestre (le origini si semplificano) e vale il rapporto dei prodotti aggiornamenti × nodi, Londra 1.00× atteso; Melbourne 2.67× atteso.

| ingresso | impronta |
|---|---|
| `costi_e3bis.json` | `32df030ae8fc6bd2` |
| `costi_e4.json` | `057d5c122b2cb0b1` |
| `e6_costi.json` | `e824b7be795577ca` |
| `inserimento_griglia_672/R-orig_Madrid_p0_s201.json` | `ec2508b0f34ec327` |
| `inserimento_griglia_672/R-orig_Madrid_p0_s202.json` | `211f986ceafb4997` |
| `inserimento_griglia_672/R-orig_Madrid_p0_s203.json` | `ceab6c72299326c0` |
| `inserimento_griglia_672/R-orig_Londra_p0_s201.json` | `d73996e4e49fa056` |
| `inserimento_griglia_672/R-orig_Londra_p0_s202.json` | `14d0862f732b5597` |
| `inserimento_griglia_672/R-orig_Londra_p0_s203.json` | `202bbf3e7171b8ce` |
| `inserimento_griglia_672/R-orig_Melbourne_p0_s201.json` | `d459a6dd106a1f57` |
| `inserimento_griglia_672/R-orig_Melbourne_p0_s202.json` | `bdf34f8760ddd10d` |
| `inserimento_griglia_672/R-orig_Melbourne_p0_s203.json` | `26d40ad92ed7fe33` |
