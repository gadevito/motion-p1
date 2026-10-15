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

Una tinta per famiglia di blocco, dalla palette delle altre figure del paper: backbone temporale
(blu C0; nodi pieni = campo ricettivo dell'ultimo passo), identita' (arancio, riquadro evidenziato:
la tabella E, la riga del sensore, la riga del token e le quattro righe che riceve un sensore nuovo,
una per braccio; per C la riga di zeri di `NoIdentity`), ramo statico (verde chiaro), fusione e
uscita (grigio). La concatenazione e' una barra 32 | 8 | 8 con un segmento per ramo. Le tinte piene
hanno luminanze distinte, sicche' la figura resta leggibile stampata in grigio.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/figura_rete.py [--lingua en] [--figure DIR]
"""
import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

GRIGIO, BLU, ARANCIO, VERDE = "#444444", "#1f77b4", "#e08214", "#2ca02c"
VERDE_PIENO = "#a6dba0"
# blu C0 di Fig. 4-5, arancio e verde delle stesse famiglie di Fig. 3; luminanze in scala di grigi
# 0.42 / 0.58 / 0.80, piu' il grigio scuro di fusione e uscita: le quattro famiglie restano distinte
# tinte chiare e scure per famiglia (palette di Fig. 3-5); luminanze distinte in scala di grigi
CHIARO = {"blu": "#c6dbef", "arancio": "#fbe3c4", "verde": "#dff2dc", "grigio": "#e6e6e6"}
SCURO = {"blu": "#0b4f86", "arancio": "#7a3f00", "verde": "#1b5e1b", "grigio": "#333333"}
TESTI = {
    "it": {"titolo_b": "backbone temporale: {} blocchi a cancello, nucleo {},\ndilatazioni {}, campo ricettivo {} passi",
           "ingresso": "{} passi × $C$", "canali": "$C$ = {}", "conv": "conv\n1×1", "somma": "Σ skip,\nultimo passo",
           "tabella": "$E$: $K\\times{}$", "token": "+ token ($E'$)", "veterano": "sensore iniziale: la sua riga",
           "nuovo": "sensore nuovo: una delle quattro righe sotto", "statica_in": "copertura\n+ 4 costanti", "statica": "ramo statico",
           "concat": "concat", "fusione": "fusione\n1×1", "uscita": "{} orizzonti × {} classi",
           "bracci": (("$C$", "riga di zeri"), ("$F_0$", "media di $E$"), ("$F_0'$", "token"), ("$F'$", "token adattato"))},
    "en": {"titolo_b": "temporal backbone: {} gated blocks, kernel {},\ndilations {}, receptive field {} steps",
           "ingresso": "{} steps × $C$", "canali": "$C$ = {}", "conv": "conv\n1×1", "somma": "Σ skips,\nlast step",
           "tabella": "$E$: $K\\times{}$", "token": "+ token ($E'$)", "veterano": "initial sensor: its own row",
           "nuovo": "new sensor: one of the four rows below", "statica_in": "coverage\n+ 4 consts", "statica": "static branch",
           "concat": "concat", "fusione": "fusion\n1×1", "uscita": "{} horizons × {} classes",
           "bracci": (("$C$", "zero row"), ("$F_0$", "mean of $E$"), ("$F_0'$", "token"), ("$F'$", "adapted token"))},
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
    d["nucleo"], d["campo"] = cod.get("nucleo", 2), cod["campo_ricettivo"]
    assert d["n_blocchi"] == len(d["dil"]) and d["uscita"] == d["orizzonti"] * d["classi"]
    d["fuso"] = d["nascosti"] + d["d_emb"] + d["stat_out"]
    return d


def disegna(D: dict, lingua: str, f: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
    from evoluzione.analisi.stile_paper import COLONNA, applica
    applica(plt)
    T = TESTI[lingua]
    fig = plt.figure(figsize=(COLONNA, 2.75))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100), ax.set_ylim(0, 78.6), ax.set_aspect("equal"), ax.axis("off")
    FS, FSS = 6.2, 5.4

    def box(x, y, w, h, fam, testo="", forte=True, fs=FS):
        fc = {"blu": BLU, "arancio": ARANCIO, "verde": VERDE_PIENO, "grigio": "#5a5a5a"}[fam] if forte else CHIARO[fam]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.0", fc=fc,
                                    ec=SCURO[fam], lw=0.6, zorder=3))
        if testo:
            ax.text(x + w / 2, y + h / 2, testo, ha="center", va="center", fontsize=fs, zorder=4, linespacing=1.0,
                    color="white" if forte and fam != "verde" else SCURO[fam])

    def freccia(p, q, col=GRIGIO, dim="", dxy=(0, 0.8), ha="center", va="bottom", lw=0.8):
        ax.annotate("", q, p, arrowprops=dict(arrowstyle="-|>", lw=lw, color=col, mutation_scale=5.5,
                                              shrinkA=0, shrinkB=0), zorder=2)
        if dim:
            ax.text((p[0] + q[0]) / 2 + dxy[0], (p[1] + q[1]) / 2 + dxy[1], dim, ha=ha, va=va, fontsize=FS,
                    color=col, weight="bold", zorder=5)

    # ---------------- backbone temporale: ingresso, conv, blocchi dilatati, somma degli skip ----------------
    n, dil = D["finestra"], D["dil"]
    x0, dx, y0, dy = 25, 3.15, 49, 4.6
    ax.text(x0 - 1, 74.5, T["titolo_b"].format(D["n_blocchi"], D["nucleo"], ", ".join(map(str, dil)),
                                               D["campo"]), ha="left", va="center", fontsize=FSS, color=SCURO["blu"],
            linespacing=1.1)
    for r in range(4):                                          # tensore d'ingresso n x C
        for t in range(n):
            ax.add_patch(Rectangle((1 + t * 0.95, 44 + r * 2.1), 0.95, 2.1, fc=CHIARO["grigio"] if (r + t) % 2 else "white",
                                   ec="#9a9a9a", lw=0.25, zorder=2))
    ax.text(1, 53.6, T["ingresso"].format(n), ha="left", va="bottom", fontsize=FSS)
    ax.text(6.7, 43.2, T["canali"].format("/".join(map(str, D["canali"]))), ha="center", va="top", fontsize=FSS,
            color=GRIGIO)
    freccia((12.6, 48.2), (15.2, 48.2))
    box(15.2, 44.2, 5.8, 8, "blu", T["conv"], fs=5.2)
    freccia((21, 48.2), (x0 - 1.2, y0), BLU)
    ax.text(23.4, 46.4, str(D["nascosti"]), ha="center", va="top", fontsize=FS, color=BLU, weight="bold")
    # nodi e collegamenti; evidenziato il campo ricettivo dell'ultimo passo
    attivi = {(len(dil), n - 1)}
    for l in range(len(dil), 0, -1):
        attivi |= {(l - 1, t - s) for (ll, t) in attivi if ll == l for s in (0, dil[l - 1]) if t - s >= 0}
    for l in range(1, len(dil) + 1):
        for t in range(n):
            for s_ in (0, dil[l - 1]):
                if t - s_ < 0:
                    continue
                on = (l, t) in attivi and (l - 1, t - s_) in attivi
                ax.plot([x0 + (t - s_) * dx, x0 + t * dx], [y0 + (l - 1) * dy, y0 + l * dy],
                        color=BLU if on else CHIARO["blu"], lw=0.75 if on else 0.35, zorder=2 if on else 1)
        ax.text(x0 - 1.4, y0 + l * dy, f"d={dil[l - 1]}", ha="right", va="center", fontsize=FSS,
                color=SCURO["blu"])
    for l in range(len(dil) + 1):
        for t in range(n):
            on = (l, t) in attivi
            ax.add_patch(Circle((x0 + t * dx, y0 + l * dy), 0.62, fc=BLU if on else "white",
                                ec=BLU if on else "#8fb3d6", lw=0.4, zorder=3))
    # skip dell'ultimo passo di ogni blocco verso la somma
    xS, yS = 83, y0 + 2.5 * dy
    for l in range(1, len(dil) + 1):
        ax.plot([x0 + (n - 1) * dx + 0.6, xS - 2.6], [y0 + l * dy, yS], color=BLU, lw=0.45, ls=(0, (2, 1.2)),
                zorder=1)
    ax.add_patch(Circle((xS, yS), 2.6, fc=BLU, ec=SCURO["blu"], lw=0.6, zorder=3))
    ax.text(xS, yS, "Σ", ha="center", va="center", fontsize=7.5, color="white", zorder=4)
    ax.text(xS + 3.4, yS, T["somma"], ha="left", va="center", fontsize=FSS, color=SCURO["blu"])
    # ---------------- concatenazione come barra 32 | 8 | 8 ----------------
    xb, wb, u = 81.2, 3.6, 0.62
    yv = 23.2 + 3.5 * 1.55                                       # riga del sensore nella tabella (sotto)
    yb0 = yv - D["d_emb"] * u / 2 - D["stat_out"] * u
    seg = [("verde", D["stat_out"]), ("arancio", D["d_emb"]), ("blu", D["nascosti"])]
    y = yb0
    centro = {}
    for fam, k in seg:
        ax.add_patch(Rectangle((xb, y), wb, k * u, fc={"blu": BLU, "arancio": ARANCIO, "verde": VERDE_PIENO}[fam],
                               ec="white", lw=0.6, zorder=3))
        centro[fam] = y + k * u / 2
        y += k * u
    ytop = y
    freccia((xS, yS - 2.6), (xS, ytop), BLU, str(D["nascosti"]), (1.0, 0), "left", "center")
    ax.text(xb + wb / 2, yb0 - 0.8, f"{T['concat']}\n{D['fuso']}", ha="center", va="top", fontsize=FSS)
    # ---------------- identita': tabella, riga del sensore, token, bracci ----------------
    ax.add_patch(FancyBboxPatch((0.6, 14.4), 73.5, 25.8, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="#fef5ea", ec=ARANCIO, lw=0.9, zorder=0))
    cx, cw, ch, ty = 3.2, 1.75, 1.55, 23.2
    righe = 6
    for r in range(righe):
        for j in range(D["d_emb"]):
            ax.add_patch(Rectangle((cx + j * cw, ty + r * ch), cw, ch, fc=ARANCIO if r != 3 else "#a85a00",
                                   ec="#fef5ea", lw=0.35, zorder=2))
    ax.add_patch(Rectangle((cx, ty + 3 * ch), D["d_emb"] * cw, ch, fc="none", ec=SCURO["arancio"], lw=1.1,
                           zorder=3))
    ax.text(cx + 4 * cw, ty + righe * ch + 0.7, T["tabella"].format(D["d_emb"]), ha="center", va="bottom",
            fontsize=FS, color=SCURO["arancio"])
    for j in range(D["d_emb"]):
        ax.add_patch(Rectangle((cx + j * cw, ty - 2.5), cw, ch, fc="white", ec=ARANCIO, lw=0.5, hatch="//////",
                               zorder=2))
    ax.text(cx + 4 * cw, ty - 3.2, T["token"], ha="center", va="top", fontsize=FSS, color=SCURO["arancio"])
    xr = cx + D["d_emb"] * cw
    xm = 64                                                     # punto in cui la riga entra nel ramo
    ax.plot([xr + 0.3, xm], [yv, yv], color=ARANCIO, lw=0.8, zorder=2)
    ax.text(xr + 1.2, yv + 0.7, T["veterano"], ha="left", va="bottom", fontsize=FSS, color=SCURO["arancio"])
    # sensore nuovo: quattro righe possibili, una per braccio
    ax.text(xr + 1.2, 23.3, T["nuovo"], ha="left", va="center", fontsize=FSS, color=SCURO["arancio"],
            style="italic")
    stili = (dict(fc="white", ec=GRIGIO, hatch=""), dict(fc="#f3b768", ec=ARANCIO, hatch=""),
             dict(fc="white", ec=ARANCIO, hatch="//////"), dict(fc=ARANCIO, ec=SCURO["arancio"], hatch="//////"))
    for i, ((sig, des), st) in enumerate(zip(T["bracci"], stili)):
        bx = xr + 2 + (i % 2) * 23.5
        by = 19.6 if i < 2 else 16.2
        ax.text(bx, by + 0.8, sig, ha="left", va="center", fontsize=FS)
        for j in range(D["d_emb"]):
            ax.add_patch(Rectangle((bx + 3.6 + j * 0.95, by), 0.95, 1.6, lw=0.35, zorder=2, **st))
        ax.text(bx + 3.6 + D["d_emb"] * 0.95 + 0.8, by + 0.8, des, ha="left", va="center", fontsize=FSS)
    freccia((xm, yv), (xb, yv), ARANCIO, str(D["d_emb"]), (2.5, 0.6))
    # ---------------- ramo statico ----------------
    box(1.2, 3, 13, 7.6, "verde", T["statica_in"], forte=False, fs=FSS)
    freccia((14.2, 6.8), (20, 6.8), VERDE, str(D["stat_in"]), (0, 0.6))
    box(20, 3, 16, 7.6, "verde", f"{T['statica']}\n{D['stat_in']}→{D['stat_out']}", fs=FSS)
    xg = 77.6
    ax.plot([36, xg, xg], [6.8, 6.8, centro["verde"]], color=VERDE, lw=0.8, zorder=2)
    freccia((xg, centro["verde"]), (xb, centro["verde"]), VERDE)
    ax.text(57, 7.4, str(D["stat_out"]), ha="center", va="bottom", fontsize=FS, color=VERDE, weight="bold")
    # ---------------- fusione e uscita ----------------
    xf, yf = 88.6, 36
    freccia((xb + wb, yf + 4), (xf, yf + 4), GRIGIO, str(D["fuso"]), (0, 0.9))
    box(xf, yf, 10.4, 8, "grigio", T["fusione"], fs=5.2)
    gx, gw = xf + 1.7, 2.35
    gy = yf - 5 - D["orizzonti"] * gw
    freccia((xf + 5.2, yf), (xf + 5.2, gy + D["orizzonti"] * gw), GRIGIO, str(D["nascosti"]), (0.9, 0), "left",
            "center")
    for h in range(D["orizzonti"]):
        for c in range(D["classi"]):
            ax.add_patch(Rectangle((gx + c * gw, gy + (D["orizzonti"] - 1 - h) * gw), gw, gw,
                                   fc=("#bdbdbd", "#8c8c8c", "#4d4d4d")[c], ec="white", lw=0.5, zorder=3))
    ax.text(gx + 1.5 * gw, gy - 0.6, f"{D['uscita']}", ha="center", va="top", fontsize=FS, weight="bold",
            color=GRIGIO)
    ax.text(gx + 1.5 * gw, gy - 3.6, T["uscita"].format(D["orizzonti"], D["classi"]).replace(" × ", "\n× "),
            ha="center", va="top", fontsize=FSS, color=GRIGIO)
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
