#!/usr/bin/env python3
"""
Figura della rete per nodo (sezione III del paper), a colori, colonna singola.
================================================================================
Dimensioni da `results/evoluzione/architettura_ck.json` (lette dai pesi dei checkpoint:
canali, larghezza, blocchi, embedding, token, uscita, K) e dal codice dove non stanno nei
pesi (dilatazioni, orizzonti, classi, campo ricettivo: `codice` dello stesso json; ingresso
e uscita del ramo statico: `architettura_ck.D_STAT` e il valore predefinito di
`PredittorePerNodo`). La fusione e' la somma delle tre parti e si verifica, non si scrive.
Nessun numero nuovo.

Una tinta per famiglia di blocco, dalla palette delle altre figure del paper: ingresso
(grigio), backbone temporale (blu C0), identita' (arancio di F₀, evidenziata), ramo
statico (verde chiaro, bordo tratteggiato), fusione e uscita (grigio chiaro). Le famiglie restano
distinguibili in scala di grigi per luminanza e stile del bordo. Sotto, cosa riceve la riga
dell'identita' per un sensore nuovo in ciascun braccio.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/figura_rete.py [--lingua en] [--figure DIR]
"""
import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

GRIGIO, BLU, ARANCIO, VERDE = "#444444", "#1f77b4", "#b86b00", "#2ca02c"
# (riempimento, bordo, stile del bordo, testo): luminanze 1.0 / 0.64 / 0.48 / 0.95 tratteggiato / 0.85
TINTE = {"ingresso": ("white", GRIGIO, "-", "k"),
         "backbone": ("#6baed6", BLU, "-", "k"),
         "identita": (ARANCIO, "#6b3e00", "-", "white"),
         "statica": ("#e5f5e0", VERDE, "--", "k"),
         "fusione": ("#d9d9d9", GRIGIO, "-", "k")}
TESTI = {
    "it": {"ingresso": "finestra\n12 passi", "conv": "conv\n1×1", "blocco": "blocco\na cancello", "dil": "d = {}",
           "somma": "Σ skip\n(ultimo\npasso)", "tabella": "embedding $K\\times{}$", "token": "+ token (solo $E'$)",
           "statica": "ramo statico", "statica_in": "copertura\n+ 4 costanti", "concat": "concat", "fusione": "fusione\n1×1",
           "uscita_box": "uscita\n1×1", "uscita": "{} orizzonti × {} classi", "titolo_b": "riga dell'identità per un sensore nuovo",
           "bracci": (("$C$", "zeri: nessuna identità"), ("$F_0$", "media delle $K$ righe di $E$"),
                      ("$F_0'$", "token appreso di $E'$"), ("$F'$", "token adattato sui primi dati"))},
    "en": {"ingresso": "input\nwindow", "conv": "conv\n1×1", "blocco": "gated\nblock", "dil": "d = {}",
           "somma": "Σ skips\n(last\nstep)", "tabella": "embedding $K\\times{}$", "token": "+ token row ($E'$ only)",
           "statica": "static branch", "statica_in": "coverage\n+ 4 consts", "concat": "concat", "fusione": "fusion\n1×1",
           "uscita_box": "output\n1×1", "uscita": "{} horizons × {} classes", "titolo_b": "identity row given to a new sensor",
           "bracci": (("$C$", "zeros: no identity"), ("$F_0$", "mean of the $K$ rows of $E$"),
                      ("$F_0'$", "learned token of $E'$"), ("$F'$", "token adapted on first data"))},
}


def dimensioni(ris: Path) -> dict:
    from evoluzione.analisi.architettura_ck import D_STAT
    from evoluzione.componente.predittore import PredittorePerNodo
    A = json.loads((ris / "architettura_ck.json").read_text())
    S, cod = A["sintesi"], A["codice"]
    uno = lambda k: {v[k] for v in S.values()}
    d_emb, nasc, nb, usc = (uno(k) for k in ("d_emb", "nascosti", "n_blocchi", "uscita"))
    assert len(d_emb) == len(nasc) == len(nb) == len(usc) == 1, "famiglie in disaccordo"
    d = {"d_emb": d_emb.pop(), "nascosti": nasc.pop(), "n_blocchi": nb.pop(), "uscita": usc.pop(),
         "canali": sorted(uno("c_in")), "finestra": cod["finestra_passi"], "dil": cod["dilatazioni"],
         "orizzonti": len(cod["orizzonti_passi"]), "classi": cod["classi"],
         "stat_in": D_STAT,
         "stat_out": inspect.signature(PredittorePerNodo.__init__).parameters["d_statiche_uscita"].default,
         "K": sorted({k for v in S.values() for k in v["K"]}),
         "token": sorted({v["token"] for v in S.values()})}
    assert d["n_blocchi"] == len(d["dil"]) and d["uscita"] == d["orizzonti"] * d["classi"]
    d["fuso"] = d["nascosti"] + d["d_emb"] + d["stat_out"]
    return d


def disegna(D: dict, lingua: str, f: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle
    from evoluzione.analisi.stile_paper import COLONNA, applica
    applica(plt)
    T = TESTI[lingua]
    fig = plt.figure(figsize=(COLONNA, 3.55))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100), ax.set_ylim(0, 106), ax.axis("off")
    FS, FSD, FSP = 6.3, 6.6, 5.8
    MARRONE = "#6b3e00"

    def box(x, y, w, h, fam, testo, lw=0.8, fs=FS):
        fc, ec, ls, tc = TINTE[fam]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec,
                                    lw=lw * (1.25 if ls == "--" else 1), ls=ls, zorder=2))
        if testo:
            ax.text(x + w / 2, y + h / 2, testo, ha="center", va="center", fontsize=fs, color=tc, zorder=3,
                    linespacing=1.05)

    def freccia(p, q, dim="", lato="sopra", col=GRIGIO):
        ax.annotate("", q, p, arrowprops=dict(arrowstyle="-|>", lw=0.8, color=col, mutation_scale=6,
                                              shrinkA=0, shrinkB=0), zorder=1)
        if dim:
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            dx, dy, ha, va = {"sopra": (0, 1.0, "center", "bottom"), "destra": (1.2, 0, "left", "center"),
                              "sinistra": (-1.2, 0, "right", "center")}[lato]
            ax.text(mx + dx, my + dy, dim, ha=ha, va=va, fontsize=FSD, color="k", zorder=4)

    canali = "/".join(str(c) for c in D["canali"])
    # --- backbone temporale (in alto) ---
    yb, hb = 92, 12
    box(0.5, yb, 9, hb, "ingresso", T["ingresso"], fs=FSP)
    freccia((9.5, yb + hb / 2), (18, yb + hb / 2), f"{D['finestra']}$\\times C$")
    ax.text(5, yb - 1.2, f"$C$ = {canali}", ha="center", va="top", fontsize=5.4, color=GRIGIO)
    box(18, yb, 7, hb, "backbone", T["conv"], fs=FSP)
    x = 25
    for i, dl in enumerate(D["dil"]):
        freccia((x, yb + hb / 2), (x + 3.5, yb + hb / 2), str(D["nascosti"]) if i == 0 else "")
        box(x + 3.5, yb, 9, hb, "backbone", T["blocco"], fs=FSP)
        ax.text(x + 8, yb - 1.2, T["dil"].format(dl), ha="center", va="top", fontsize=FSP, color=BLU)
        x += 12.5
    freccia((x, yb + hb / 2), (x + 3, yb + hb / 2))
    box(x + 3, yb - 1, 11, hb + 2, "backbone", T["somma"], fs=FSP)
    xs = x + 8.5
    # --- concatenazione (colonna di destra) ---
    xc, wc, yc = 80, 18, 64.75
    box(xc, yc, wc, 8, "fusione", T["concat"])
    freccia((xs, yb - 1), (xs, yc + 8), str(D["nascosti"]), "sinistra")
    # --- identita' (riga evidenziata) ---
    ax.add_patch(Rectangle((0.5, 53), 73, 28, fc="#fbe9d4", ec=ARANCIO, lw=1.2, zorder=0))
    xt, ct, rt, y0 = 6, 3.0, 2.5, 64
    for r in range(4):
        for j in range(D["d_emb"]):
            ax.add_patch(Rectangle((xt + j * ct, y0 + 6 - r * rt), ct, rt, fc=ARANCIO, ec="white", lw=0.4,
                                   zorder=2))
    ax.text(xt + 4 * ct, y0 + 6 + rt + 1.2, T["tabella"].format(D["d_emb"]), ha="center", va="bottom",
            fontsize=FS, color=MARRONE)
    ax.text(xt - 1, y0 + 3.5, "$K$", ha="right", va="center", fontsize=FS, color=MARRONE)
    ax.add_patch(Rectangle((xt, y0 + 6 - rt), D["d_emb"] * ct, rt, fc="none", ec=MARRONE, lw=1.4, zorder=3))
    for j in range(D["d_emb"]):
        ax.add_patch(Rectangle((xt + j * ct, y0 - 6), ct, rt, fc="white", ec=ARANCIO, lw=0.7, hatch="////",
                               zorder=2))
    ax.text(xt + D["d_emb"] * ct + 1.2, y0 - 4.75, T["token"], ha="left", va="center", fontsize=FSP,
            color=MARRONE)
    xr = xt + D["d_emb"] * ct
    freccia((xr + 0.3, yc + 4), (xc, yc + 4), str(D["d_emb"]), col=ARANCIO)
    ax.text((xr + xc) / 2 + 2, yc + 2.6, "row of the sensor" if lingua == "en" else "riga del sensore",
            ha="center", va="top", fontsize=5.4, color=MARRONE, style="italic")
    # --- ramo statico ---
    ys = 40
    box(0.5, ys, 15, 9, "statica", T["statica_in"], fs=FSP)
    freccia((15.5, ys + 4.5), (24, ys + 4.5), str(D["stat_in"]), col=VERDE)
    box(24, ys, 20, 9, "statica", f"{T['statica']}\n{D['stat_in']}$\\to${D['stat_out']}", fs=FSP)
    freccia((44, ys + 4.5), (xc + 3, ys + 4.5), col=VERDE)
    ax.plot([xc + 3, xc + 3], [ys + 4.5, ys + 4.6], color=VERDE, lw=0.8)
    freccia((xc + 3, ys + 4.5), (xc + 3, yc), str(D["stat_out"]), "sinistra", col=VERDE)
    # --- fusione e uscita ---
    xf = xc + 12
    freccia((xf, yc), (xf, 44), str(D["fuso"]), "destra")
    box(xc + 6, 35, 12, 9, "fusione", T["fusione"], fs=FSP)
    freccia((xf, 35), (xf, 28), str(D["nascosti"]), "destra")
    box(xc + 6, 19, 12, 9, "fusione", T["uscita_box"], fs=FSP)
    freccia((xc + 6, 23.5), (62, 23.5), str(D["uscita"]))
    ax.text(61, 23.5, T["uscita"].format(D["orizzonti"], D["classi"]), ha="right", va="center", fontsize=FSP)
    # --- bracci: cosa riceve la riga dell'identita' ---
    ax.plot([0.5, 99.5], [15.5, 15.5], color="#bbbbbb", lw=0.5)
    ax.text(0.5, 12.6, T["titolo_b"] + ":", ha="left", va="center", fontsize=FS, color=MARRONE, weight="bold")
    stili = (dict(fc="white", ec=GRIGIO, hatch=""), dict(fc="#e8b77a", ec=ARANCIO, hatch=""),
             dict(fc="white", ec=ARANCIO, hatch="////"), dict(fc=ARANCIO, ec=MARRONE, hatch="////"))
    for i, ((sig, des), st) in enumerate(zip(T["bracci"], stili)):
        x0, y0 = 0.5 + (i % 2) * 50, 6.4 - (i // 2) * 5.4
        ax.text(x0, y0 + 1.2, sig, ha="left", va="center", fontsize=FS)
        for j in range(D["d_emb"]):
            ax.add_patch(Rectangle((x0 + 5 + j * 1.6, y0 + 0.2), 1.6, 2.0, lw=0.4, zorder=2, **st))
        ax.text(x0 + 5 + D["d_emb"] * 1.6 + 1, y0 + 1.2, des, ha="left", va="center", fontsize=5.4)
    fig.savefig(f, dpi=300)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    ap.add_argument("--lingua", choices=("it", "en"), default="it")
    a = ap.parse_args()
    from evoluzione.analisi.stile_paper import nome
    D = dimensioni(a.out)
    a.figure.mkdir(parents=True, exist_ok=True)
    disegna(D, a.lingua, a.figure / nome(a.lingua, "rete"))
    print(f"figura: {a.figure / nome(a.lingua, 'rete')}  (fusione {D['nascosti']}+{D['d_emb']}+{D['stat_out']}={D['fuso']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
