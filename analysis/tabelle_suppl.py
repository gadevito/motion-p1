"""
Tabelle del materiale supplementare del Paper 1 (sezione C), dai risultati
rigenerati e con il codice statistico del repository (nessuna copia):

    C.3  metriche operative sulla classe congestionata per ogni confronto
         principale e tre regole di decisione       <- e8_risultati.json
    C.8  frequenze di classe e pesi per contesto     <- artefatti dei pesi usati (pesi_griglia,
                                                         pesi_pems04, pesi_pems08)
    C.9  wCE per orizzonte, X - C, con ricampionamento congiunto
         <- predizioni_e8/prova_*.npz, con esegui_e4._boot ed esegui_e4._wce,
            contesti e semi del bootstrap di esegui_e8 (CONTESTI_E8)

Ogni funzione scrive un file LaTeX (longtable) che supplementary.tex include.
"""
import json
from pathlib import Path

CTX_EN = {"Madrid": "Madrid", "Londra": "London", "Melbourne": "Melbourne", "PEMS08": "PEMS08", "PEMS04": "PEMS04"}
CONF_EN = {"A-C": r"$A-C$", "F0-C": r"$F_0-C$", "F0p-C": r"$F_0'-C$", "Fp_96-C": r"$F'(24\,\mathrm{h})-C$",
           "Fp_672-C_eta>1sett": r"$F'(1\,\mathrm{wk})-C$$^\dagger$", "gated-F0p": r"gated$-F_0'$",
           "Rorig_672-Fp_672_eta>1sett": r"R-orig$(1\,\mathrm{wk})-F'(1\,\mathrm{wk})$$^\dagger$"}
REGOLE_EN = {"prim": "F1-opt.", "par": "FA parity", "argmax": "argmax"}
MET = ("richiamo", "falsi_allarmi", "precisione", "f1_macro")
TESTA = "% generato da OR3/analysis/main.py (tabelle_suppl): non modificare a mano\n"


def _ic(r, scala=100.0, cifre=1):
    m, (lo, hi) = r["media"] * scala, r["ic_con_nodi"]
    return f"${m:+.{cifre}f}$ \\scriptsize$[{lo * scala:+.{cifre}f}, {hi * scala:+.{cifre}f}]$"


def _longtable(colonne: str, didascalia: str, intestazione: str, righe: list, etichetta: str = "") -> str:
    lab = f"\\label{{{etichetta}}}" if etichetta else ""
    return (TESTA + "{\\footnotesize\\setlength{\\tabcolsep}{3pt}\n"
            f"\\begin{{longtable}}{{{colonne}}}\n\\caption{{{didascalia}}}{lab}\\\\\n\\toprule\n{intestazione}\\\\\n"
            "\\midrule\n\\endfirsthead\n\\toprule\n" f"{intestazione}\\\\\n\\midrule\n\\endhead\n"
            + "\n".join(righe) + "\n\\bottomrule\n\\end{longtable}}\n")


def scrivi_C3(ris: Path, f: Path) -> None:
    R = json.loads((ris / "e8_risultati.json").read_text())
    righe = []
    for g in ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04"):
        if g not in R["gruppi"]:
            continue
        cf = R["gruppi"][g]["confronti"]
        prima = True
        for k, et in CONF_EN.items():
            if k not in cf:
                continue
            for regola, er in REGOLE_EN.items():
                if regola not in cf[k]:
                    continue
                righe.append((CTX_EN[g] if prima else "") + f" & {et} & {er} & "
                             + " & ".join(_ic(cf[k][regola][m]) for m in MET) + " \\\\")
                prima = False
        righe.append("\\addlinespace")
    f.write_text(_longtable(
        "@{}l l l c c c c@{}",
        "Operational metrics on the congested class for every principal comparison (differences in percentage "
        "points, mean over cells and 95\\% interval from 4{,}000 joint resamples), under three decision rules: "
        "F1-optimal threshold per arm chosen on validation; threshold giving each arm the false-alarm rate of $C$ "
        "on validation; argmax. $^\\dagger$ origins older than one week.",
        "Context & Comparison & Rule & $\\Delta$ recall & $\\Delta$ false alarms & $\\Delta$ precision & "
        "$\\Delta$ macro-F1", righe[:-1], "tab:suppC3"))


def scrivi_C8(ris: Path, f: Path) -> None:
    """Dagli artefatti dei pesi USATI dagli esperimenti del paper: pesi_griglia (citta',
    episodio 1), pesi_pems04, pesi_pems08 (sei partizioni). Non da frequenze_classi.json,
    che legge la cartella `pesi/` precedente e solo tre partizioni di PEMS08."""
    righe = []
    for cart, ctxs in (("pesi_griglia", ("Madrid", "Londra", "Melbourne")), ("pesi_pems04", ("PEMS04",)),
                       ("pesi_pems08", ("PEMS08",))):
        for ctx in ctxs:
            ff = sorted((ris / cart).glob(f"pesi_{ctx}_p*.json"), key=lambda x: int(x.stem.split("_p")[-1].split("_")[0]))
            for g in ff:
                v = json.loads(g.read_text())
                n = sum(v["conteggi"])
                fr = " & ".join(f"{100 * x / n:.1f}" for x in v["conteggi"])
                pw = " & ".join(f"{x:.2f}" for x in v["pesi"])
                righe.append(f"{CTX_EN[ctx]} & p{v['partizione']} & {v['n_train']:,} & {fr} & {pw} & "
                             f"\\texttt{{{v['impronta']}}} \\\\".replace(",", "{,}"))
    f.write_text(_longtable(
        "@{}l l r r r r r r r l@{}",
        "Class frequencies (\\%) in the training targets and class weights of the weighted cross-entropy, per "
        "context and node partition, from the weight artefacts used by the experiments (cities: installation "
        "episode 1). Classes: free-flowing, moderate, congested.",
        "Context & Part. & Training targets & \\multicolumn{3}{c}{Frequency (\\%)} & "
        "\\multicolumn{3}{c}{Weight} & Artefact", righe, "tab:suppC8"))


def scrivi_C9(ris: Path, f: Path) -> None:
    import numpy as np
    from evoluzione.esperimenti.esegui_e4 import _boot, _wce
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8, DIR_PRED
    CONF = {"A-C": ("A", "C", None), "F0-C": ("F0", "C", None), "F0p-C": ("F0p", "C", None),
            "Fp_96-C": ("Fp_96", "C", None), "Fp_672-C_eta>1sett": ("Fp_672", "C", 2)}
    ORIZ = ("15 min", "30 min", "60 min", "120 min")
    righe = []
    for nome, costruttore in CONTESTI_E8.items():
        ctx = costruttore(ris)
        celle = {}
        for (c, p, s) in ctx["unita"]:
            with np.load(ris / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True) as z:
                celle[(ctx["gruppo"](c), p, s)] = {k: z[k] for k in z.files}
        for gr in sorted({k[0] for k in celle}, key=lambda x: list(CTX_EN).index(x)):
            cc = {k: z for k, z in celle.items() if k[0] == gr}
            modelli = json.loads(str(next(iter(cc.values()))["modelli"]))
            rng = np.random.default_rng(ctx["seme_boot"])
            prima = True
            for k, (n1, n2, fascia) in CONF.items():
                if n1 not in modelli or n2 not in modelli:
                    continue

                def ab(z, n, h, idx, _f=fascia):
                    A, B = z[f"AF_{n}"], z[f"BF_{n}"]
                    A = A.sum(0) if _f is None else A[_f]
                    B = B.sum(0) if _f is None else B[_f]
                    A, B = A[:, h:h + 1], B[:, h:h + 1]
                    return (A, B) if idx is None else (A[idx], B[idx])
                vals = [_boot(cc, lambda z, idx, _h=h: _wce(*ab(z, n1, _h, idx)) - _wce(*ab(z, n2, _h, idx)), rng)
                        for h in range(len(ORIZ))]
                righe.append((CTX_EN[gr] if prima else "") + f" & {CONF_EN[k]} & "
                             + " & ".join(_ic(v, scala=1.0, cifre=3) for v in vals) + " \\\\")
                prima = False
            righe.append("\\addlinespace")
    f.write_text(_longtable(
        "@{}l l c c c c@{}",
        "Difference in weighted cross-entropy against $C$ per forecasting horizon (mean over cells and 95\\% "
        "interval from 4{,}000 joint resamples of partitions, seeds and sensors). $^\\dagger$ origins older than "
        "one week; otherwise all origins after $t_1$.",
        "Context & Comparison & " + " & ".join(ORIZ), righe[:-1], "tab:suppC9"))
