#!/usr/bin/env python3
"""
Figura per l'appendice C: curve richiamo–falsi allarmi per contesto (E8-bis).
==============================================================================
Cinque pannelli (Madrid, Londra, Melbourne, PEMS08, PEMS04), dai file
`predizioni_e8/curva_*.npz`: per ogni modello la matrice di confusione per
nodo a ciascuna delle 19 soglie, **sommata su celle e nodi**, perimetro delle
origini comuni (eta' > 1 settimana: `griglia7_*`), cosi' che F′(1 sett.) sia
confrontabile con gli altri. Modelli: C, F₀, F₀′, F′(1 sett.), A (dove esiste).
Nessun ricampionamento qui: gli intervalli sono nel congelamento (§7).

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/figura_e8bis.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8, DIR_PRED, curva  # noqa: E402

GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
MODELLI = (("C", "C", "#444444", "-"), ("F0", "F₀ (embedding medio)", "#b86b00", ":"),
           ("F0p", "F₀′ (token)", "#1f77b4", "--"), ("Fp_672", "F′ (1 sett.)", "#1f77b4", "-"),
           ("A", "A (veterano)", "#2ca02c", "-."))
MODELLI_EN = (("C", "$C$", "#444444", "-"), ("F0", "$F_0$ (mean)", "#b86b00", ":"),
              ("F0p", "$F_0'$ (token)", "#1f77b4", "--"), ("Fp_672", "$F'$(1 wk)", "#1f77b4", "-"),
              ("A", "$A$ (oracle)", "#2ca02c", "-."))
FA_MAX = 0.12


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    ap.add_argument("--lingua", choices=("it", "en"), default="it",
                    help="en: figura C1 del supplementare (PDF, inglese); non scrive nulla in --out")
    a = ap.parse_args()
    from evoluzione.analisi.stile_paper import PAGINA, applica, citta, nome as nome_file
    en = a.lingua == "en"
    if en:
        applica(plt)
    somme = {}
    for nome, cost in CONTESTI_E8.items():
        ctx = cost(a.out)
        for (c, p, s) in ctx["unita"]:
            g = a.out / DIR_PRED / f"curva_{c}_p{p}_s{s}.npz"
            with np.load(g, allow_pickle=True) as z:
                gr = str(z["gruppo"]); modelli = json.loads(str(z["modelli"]))
                for m in modelli:
                    G = z[f"griglia7_{m}"].sum(1)                 # (19, 3, 3) sui nodi della cella
                    somme.setdefault(gr, {}); somme[gr][m] = somme[gr].get(m, 0) + G
    fig, axs = plt.subplots(1, 5, figsize=(PAGINA, 1.9) if en else (17, 3.9), sharey=True)
    for ax, gr in zip(axs, GRUPPI):
        for m, et, col, ls in (MODELLI_EN if en else MODELLI):
            if m not in somme.get(gr, {}):
                continue
            far, rich = curva(somme[gr][m])
            o = np.argsort(far)
            ax.plot(100 * far[o], 100 * rich[o], ls, color=col, lw=1.2 if en else 1.6, label=et)
        ax.set_xlim(0, 100 * FA_MAX); ax.set_ylim(0, 100)
        ax.set_title(citta(a.lingua, gr)); ax.set_xlabel("false alarms (%)" if en else "falsi allarmi (%)")
        ax.grid(alpha=.3)
        if not en:
            for fa in (0.5, 1, 2, 5, 10):
                ax.axvline(fa, color="#bbbbbb", lw=.6, ls=":")
    axs[0].set_ylabel("recall, congested (%)" if en else "richiamo sulla classe congestionata (%)")
    axs[0].legend(loc="upper left", fontsize=5.5 if en else 8)   # Madrid ha tutti e cinque i modelli; in alto a sinistra e' vuoto
    if en:
        fig.tight_layout(pad=.3, w_pad=.3)
    else:
        fig.suptitle("Curve richiamo–falsi allarmi sulle origini comuni (eta' > 1 settimana), soglie 0,05…0,95 (E8-bis)", fontsize=10)
        fig.tight_layout()
    a.figure.mkdir(parents=True, exist_ok=True)
    f = a.figure / nome_file(a.lingua, "curve_e8bis")
    fig.savefig(f, dpi=150)
    if en:
        print(f"  figura in {f}")
        return 0
    (a.out / "curve_e8bis_punti.json").write_text(json.dumps(
        {gr: {m: {"falsi_allarmi": curva(G)[0].tolist(), "richiamo": curva(G)[1].tolist()} for m, G in d.items()}
         for gr, d in somme.items()}, indent=1))
    print(f"  figura in {f}; punti delle curve in {a.out / 'curve_e8bis_punti.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
