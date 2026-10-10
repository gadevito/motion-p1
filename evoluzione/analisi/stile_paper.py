"""
Stile delle figure per il Paper 1 (`--lingua en` negli script delle figure).
=============================================================================
Con `--lingua it` (predefinito) gli script producono le figure di lavoro, in
italiano, come prima. Con `--lingua en` producono la versione del manoscritto:
etichette in inglese, carattere serif, larghezze IEEE (colonna 3,5 in, pagina
7,16 in), PDF vettoriale con lo stesso nome base. Nessun numero cambia: la
lingua tocca solo testo e impaginazione.
"""
COLONNA, PAGINA = 3.5, 7.16
CITTA_EN = {"Madrid": "Madrid", "Londra": "London", "Melbourne": "Melbourne",
            "PEMS08": "PEMS08", "PEMS04": "PEMS04"}


def applica(plt):
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.titlesize": 8.5,
                         "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "mathtext.fontset": "dejavuserif"})


def nome(lingua: str, base: str) -> str:
    """`curva_e4` -> curva_e4.png (it) o curva_e4.pdf (en)."""
    return f"{base}.pdf" if lingua == "en" else f"{base}.png"


def citta(lingua: str, c: str) -> str:
    return CITTA_EN.get(c, c) if lingua == "en" else c
