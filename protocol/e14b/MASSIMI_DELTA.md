# E14-B — massimo |Δ| per variante e per famiglia

Derivato da `evoluzione/audit/massimi_e14b.py` da `results/evoluzione/congelamento_e14b.json` (impronta `83fb792e766f815c`) il 2026-11-01 11:58 UTC. Δ = variante − congelato, in wCE (il rapporto (F₀ − C)/(A − C) e le AUC di E8-bis sono esclusi: non sono wCE). Etichette delle varianti da `analysis/tabelle_suppl.py` (`VAR_EN`, la stessa fonte delle tabelle D7/D8): (c) = permutata; (a) = causale. **Nota del 2026-11-01**: nella versione del 30/10 le etichette «permutata» e «causale» erano invertite rispetto al protocollo E14 (emendamento 12/10: (c) permutata, (a) causale); le cifre e i «dove» erano gia' corretti.

Famiglie: `dichiarazioni` = le cinque dichiarazioni (a)–(e) per contesto ed episodio; `livelli_assoluti` = wCE assoluta dei bracci `C`, `A`, `F0`, `F0p`, `Fp_96` (episodio 1, i bracci della tabella D8); `livelli_diff` = differenze `F0-C`, `F0p-C`, `A-C`, `Fp_96-C`, `F0p-F0`; `altre` = altre dichiarazioni (E3, E3-bis, E4, E8, E8-bis) con Δ in wCE; `e8_wce` = wCE delle soglie E8. Δ dei livelli e delle differenze = media della variante − media congelata (`<città>/(v)` contro `<città>/congelato`), controllata contro `delta_<v>` dove questo esiste. **Nota del 2026-11-01 (seconda)**: fino a questa data `livelli_assoluti` e `livelli_diff` leggevano solo `delta_<v>` (C, A, F0; A-C, F0-C): mancavano F0' e F'(24 h).

| variante | famiglia | n | max \|Δ\| | Δ | dove |
|---|---|---:|---:|---:|---|
| permutata (c) | dichiarazioni | 54 | 0.0092 | -0.0092 | `Melbourne/ep3/b` |
| permutata (c) | livelli_assoluti | 15 | 0.0054 | +0.0054 | `Madrid/F0p` |
| permutata (c) | livelli_diff | 15 | 0.0047 | -0.0047 | `Melbourne/A-C` |
| permutata (c) | altre | 42 | 0.0050 | -0.0050 | `E4/Madrid/gated-F0p` |
| permutata (c) | e8_wce | 32 | 0.0050 | -0.0050 | `Madrid/gated-F0p` |
| permutata (c) | **tutte** | 158 | **0.0092** | | |
| causale (a) | dichiarazioni | 54 | 0.0054 | -0.0054 | `Melbourne/ep2/d` |
| causale (a) | livelli_assoluti | 15 | 0.0069 | +0.0069 | `Melbourne/C` |
| causale (a) | livelli_diff | 15 | 0.0066 | -0.0066 | `Melbourne/A-C` |
| causale (a) | altre | 42 | 0.0062 | -0.0062 | `E4/Melbourne/F_96-C` |
| causale (a) | e8_wce | 32 | 0.0066 | -0.0066 | `Melbourne/A-C` |
| causale (a) | **tutte** | 158 | **0.0069** | | |
