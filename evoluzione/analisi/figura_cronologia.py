#!/usr/bin/env python3
"""
Cronologia degli episodi d'installazione (sezione III del paper), colonna singola.
====================================================================================
Le date vengono dalla tabella del punto 8 di `paper/SCHEDA_FATTI.md` (generata da
`evoluzione/analisi/scheda_fatti.py` dagli indici della griglia a 15 minuti): addestramento,
selezione del checkpoint, validazione della politica (solo episodio 1: le scelte di (tau, N) e
k valgono anche per gli episodi 2 e 3), installazione t0, acquisizione (t0, t1], test (t1, fine].
Nessun numero nuovo: la figura legge la tabella e la disegna; l'asse e' in giorni dall'inizio
della serie di ciascun contesto, perche' i contesti coprono anni diversi.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/figura_cronologia.py [--lingua en] [--figure DIR]
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SCHEDA = Path("paper/SCHEDA_FATTI.md")
ORDINE = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
COLORI = {"addestramento": "#bdbdbd", "selezione": "#6baed6", "validazione": "#e08214",
          "acquisizione": "#2ca02c", "test": "#333333"}
TESTI = {"it": {"addestramento": "addestramento", "selezione": "selezione del checkpoint",
                "validazione": "validazione della politica", "acquisizione": "primo giorno $(t_0,t_1]$",
                "test": "test", "asse": "giorni dall'inizio della serie", "ep": "ep."},
         "en": {"addestramento": "training", "selezione": "checkpoint selection",
                "validazione": "policy validation", "acquisizione": "first day $(t_0,t_1]$",
                "test": "test", "asse": "days from the start of the series", "ep": "ep."}}
DATA = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})")


def leggi_tabella(f: Path) -> list:
    """Righe della tabella del punto 8: contesto, episodio e gli intervalli come datetime."""
    testo = f.read_text()
    blocco = testo[testo.index("## 8."):]
    righe = []
    for r in blocco.splitlines():
        c = [x.strip() for x in r.strip().strip("|").split("|")]
        if len(c) != 8 or c[0] not in ORDINE:
            continue
        d = lambda x: [datetime.strptime(t, "%Y-%m-%d %H:%M") for t in DATA.findall(x)]
        tr, sel, val = d(c[2]), d(c[3]), d(c[4])
        righe.append({"contesto": c[0], "ep": int(c[1]), "addestramento": tr, "selezione": sel,
                      "validazione": [val[0], val[2]] if len(val) == 3 else None,
                      "t0": d(c[5])[0], "t1": d(c[6])[0], "fine": d(c[7])[0]})
    assert righe, f"tabella del punto 8 non trovata in {f}"
    return sorted(righe, key=lambda r: (ORDINE.index(r["contesto"]), r["ep"]))


def disegna(R: list, lingua: str, f: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from evoluzione.analisi.stile_paper import COLONNA, applica, citta
    applica(plt)
    T = TESTI[lingua]
    fig, ax = plt.subplots(figsize=(COLONNA, 2.55))
    giorni = lambda a, b: (b - a).total_seconds() / 86400
    y = 0
    etichette, posizioni = [], []
    prec = None
    for r in reversed(R):
        if prec is not None and r["contesto"] != prec:
            y += 0.45
        prec = r["contesto"]
        o = r["addestramento"][0]
        segm = [("addestramento", r["addestramento"]), ("selezione", r["selezione"]),
                ("acquisizione", [r["t0"], r["t1"]]), ("test", [r["t1"], r["fine"]])]
        for nome, (a, b) in segm:
            ax.barh(y, giorni(a, b), left=giorni(o, a), height=0.62, color=COLORI[nome], lw=0, zorder=2)
        if r["validazione"]:
            a, b = r["validazione"]
            ax.barh(y + 0.43, giorni(a, b), left=giorni(o, a), height=0.2, color=COLORI["validazione"], lw=0,
                    zorder=3)
        ax.text(giorni(o, r["fine"]) + 1.5, y, r["t0"].strftime("%Y-%m-%d"), va="center", fontsize=5.4,
                color="#555555")
        etichette.append(f"{citta(lingua, r['contesto'])} {T['ep']} {r['ep']}" if r["contesto"] not in
                         ("PEMS08", "PEMS04") else r["contesto"])
        posizioni.append(y)
        y += 1
    ax.set_yticks(posizioni, etichette, fontsize=6)
    ax.set_xlabel(T["asse"], fontsize=6.5)
    ax.tick_params(axis="x", labelsize=6)
    ax.set_ylim(-0.6, y - 0.1)
    xmax = max(giorni(r["addestramento"][0], r["fine"]) for r in R)
    ax.set_xlim(0, xmax + 36)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
    ax.legend(handles=[Patch(color=COLORI[k], label=T[k]) for k in
                       ("addestramento", "selezione", "validazione", "acquisizione", "test")],
              ncol=3, fontsize=5.6, frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0),
              handlelength=1.2, columnspacing=0.9)
    fig.tight_layout(pad=0.3)
    fig.savefig(f, dpi=300)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scheda", type=Path, default=SCHEDA)
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    ap.add_argument("--lingua", choices=("it", "en"), default="it")
    a = ap.parse_args()
    from evoluzione.analisi.stile_paper import nome
    R = leggi_tabella(a.scheda)
    a.figure.mkdir(parents=True, exist_ok=True)
    disegna(R, a.lingua, a.figure / nome(a.lingua, "cronologia"))
    print(f"figura: {a.figure / nome(a.lingua, 'cronologia')}  ({len(R)} episodi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
