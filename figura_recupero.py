#!/usr/bin/env python3
"""
Recupero del divario di identita' per storia osservata, in scala logaritmica.
=============================================================================
Nessun addestramento: legge i file della campagna di inserimento.

PERCHE' LA SCALA LOGARITMICA. Gli intervalli fra i punti misurati valgono tre,
venti e centoquarantaquattro ore: disposti a distanza costante, il tratto fra un
giorno e una settimana occupa lo stesso spazio di quello fra un'ora e quattro ore
pur corrispondendo a sei volte piu' dati. La figura a passo costante mostra
percio' una crescita quasi lineare fino a ventiquattro ore, mentre sulla scala
del tempo la curva e' ripida all'inizio e piatta dopo — che e' la forma che il
testo afferma.

IL PUNTO A STORIA NULLA NON E' RAPPRESENTABILE, e non e' una misura: con storia
nulla il recupero vale zero per costruzione, ed e' infatti l'unico punto privo di
barra di incertezza. Viene quindi omesso dal grafico e dichiarato in didascalia.
Con `--con-zero` lo si colloca a sinistra con una interruzione dichiarata.

Uso (dalla radice OR3/):

    poetry run python figura_recupero.py
    poetry run python figura_recupero.py --con-zero --config onboardC
"""
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd

ORE = {"1h": 1.0, "4h": 4.0, "24h": 24.0, "1wk": 168.0}
ETICHETTA = {"1h": "1 h", "4h": "4 h", "24h": "1 g", "1wk": "1 sett."}
CITTA = {"mad": "Madrid", "lon": "Londra", "mel": "Melbourne"}
STILE = {"mad": dict(color="#1f4e79", marker="o", ls="-"),
         "lon": dict(color="#c00000", marker="s", ls="--"),
         "mel": dict(color="#2e8b57", marker="^", ls=":")}


def recupero(pref, c, semi):
    """{storia: [valore per seme]} — quota del divario di identita' colmata.

    Il divario e' la differenza fra i sensori con storia lunga e quelli senza;
    il recupero e' la frazione di esso che la storia osservata colma.
    """
    fuori = {h: [] for h in ORE}
    for s in range(semi):
        f = sorted(x for x in globmod.glob(f"**/{pref}_{c}_s{s}.csv", recursive=True)
                   if "pernode" not in x)
        if not f:
            continue
        d = pd.read_csv(f[0])
        try:
            v = d[d.split == "seen"].wCE.mean()
            g0 = d[(d.split == "held-out") & (d.history == "0h")].wCE.mean()
        except Exception:
            continue
        if not np.isfinite([v, g0]).all() or abs(g0 - v) < 1e-9:
            continue
        for h in ORE:
            gl = d[(d.split == "held-out") & (d.history == h)].wCE.mean()
            if np.isfinite(gl):
                fuori[h].append(100 * (g0 - gl) / (g0 - v))
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="figura del recupero per storia osservata")
    ap.add_argument("--config", default="onboard",
                    help="prefisso della configurazione: onboard, onboardB, onboardC…")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--criterio", type=float, default=70.0)
    ap.add_argument("--con-zero", action="store_true",
                    help="include il punto a storia nulla, fuori scala e con "
                         "interruzione dichiarata")
    ap.add_argument("--figura", default="figure/recupero_identita.png")
    a = ap.parse_args()

    D = {}
    for c, n in CITTA.items():
        r = recupero(a.config, c, a.semi)
        if all(len(r[h]) >= 2 for h in ORE):
            D[c] = r
    if not D:
        print(f"nessun dato per la configurazione '{a.config}'")
        return 1

    print(f"configurazione {a.config}\n")
    print(f"{'citta':10s} {'semi':>4} " +
          "".join(f"{ETICHETTA[h]:>16}" for h in ORE))
    for c in CITTA:
        if c not in D:
            print(f"{CITTA[c]:10s} dati insufficienti")
            continue
        riga = []
        for h in ORE:
            v = D[c][h]
            m = np.mean(v)
            hw = ((2.776 if len(v) == 5 else 4.303) * np.std(v, ddof=1)
                  / math.sqrt(len(v))) if len(v) > 1 else 0
            riga.append(f"{m:8.1f} ±{hw:5.1f}")
        print(f"{CITTA[c]:10s} {len(D[c]['1h']):4d} " + "".join(riga))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from pathlib import Path
    except ImportError:
        print("\nmatplotlib assente: figura non prodotta")
        return 0

    Path(a.figura).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    # con `--con-zero` il punto a storia nulla e' collocato a un quarto d'ora
    # fittizio, separato dal resto da una interruzione visibile: NON e' una
    # misura a quel tempo, ed e' per questo che va dichiarato in didascalia
    X0 = 0.25
    for c in CITTA:
        if c not in D:
            continue
        x = [ORE[h] for h in ORE]
        y = [np.mean(D[c][h]) for h in ORE]
        e = [((2.776 if len(D[c][h]) == 5 else 4.303) * np.std(D[c][h], ddof=1)
              / math.sqrt(len(D[c][h]))) if len(D[c][h]) > 1 else 0 for h in ORE]
        if a.con_zero:
            x = [X0] + x
            y = [0.0] + y
            e = [0.0] + e
        ax.errorbar(x, y, yerr=e, label=CITTA[c], capsize=3.5, linewidth=1.8,
                    markersize=7, markerfacecolor="white", markeredgewidth=1.6,
                    elinewidth=1.1, **STILE[c])

    ax.set_xscale("log")
    tick = [ORE[h] for h in ORE]
    lab = [ETICHETTA[h] for h in ORE]
    if a.con_zero:
        tick = [X0] + tick
        lab = ["0"] + lab
        ax.axvline(0.6, color="#bbbbbb", linewidth=1.2, ls=(0, (2, 3)), zorder=0)
    ax.set_xticks(tick)
    ax.set_xticklabels(lab)
    ax.minorticks_off()
    ax.axhline(a.criterio, color="#888888", linewidth=1.0, ls="--", zorder=0)
    ax.annotate(f"criterio R4 ({a.criterio:.0f}%)", (tick[-1], a.criterio),
                textcoords="offset points", xytext=(-4, 7), ha="right",
                fontsize=9, color="#666666")
    ax.set_xlabel("storia osservata del nodo nuovo (scala logaritmica)")
    ax.set_ylabel("divario di identità colmato (%)")
    ax.grid(alpha=0.22, linewidth=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    fig.tight_layout()
    fig.savefig(a.figura, dpi=200)
    print(f"\nfigura -> {a.figura}")
    if not a.con_zero:
        print("  il punto a storia nulla e' omesso: vale zero per costruzione e")
        print("  non e' rappresentabile in scala logaritmica. Va dichiarato in")
        print("  didascalia come definizione e non come misura.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
