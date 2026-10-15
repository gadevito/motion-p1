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
    D    E14 (difetto 21), sensibilita' alla statica non causale: dichiarazioni, livelli,
         selezioni e altri confronti, congelato contro ogni variante <- congelamento_e14b.json

Ogni funzione scrive un file LaTeX (longtable) che supplementary.tex include.
"""
import hashlib
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


_NOMI_E14 = (("Rorig_672", r"R-orig$(1\,\mathrm{wk})$"), ("R-orig", "R-orig"), ("R-mon", "R-mon"),
             ("Fp_672", r"$F'(1\,\mathrm{wk})$"), ("Fp_96", r"$F'(24\,\mathrm{h})$"), ("F_96", r"$F(24\,\mathrm{h})$"),
             ("F0p", r"$F_0'$"), ("F0", r"$F_0$"), ("Fpw", r"$F'(1\,\mathrm{wk})$"), ("Rw", r"R-orig$(1\,\mathrm{wk})$"),
             ("gated", "gated"), ("A", "$A$"), ("C", "$C$"), ("E", "$E$"), ("R", "$R$"))
DICH_EN = {"a": r"(a) $F_0'-C$", "b": r"(b) gated$-F_0'$", "c": r"(c) $F'(1\,\mathrm{wk})-C$",
           "d": r"(d) $F'(24\,\mathrm{h})-C$", "e": r"(e) $F'(1\,\mathrm{wk})-A$"}
FASE_EN = {"E3": "E3", "E3 veterani": "E3, veterans", "E3-bis": "E3-bis", "E4": "E4"}
TAU_EN = {96: "24 h", 192: "48 h", 672: "1 wk"}


def _nome_e14(k: str) -> str:
    """'Rorig_672-Fp_672_eta>1sett' -> R-orig(1 wk) - F'(1 wk) con il segno delle origini anziane."""
    vecchie = k.endswith("_eta>1sett")
    k, parti = k.removesuffix("_eta>1sett"), []
    while k:
        for chiave, et in _NOMI_E14:
            if k.startswith(chiave):
                parti.append(et)
                k = k[len(chiave):].removeprefix("-")
                break
        else:
            raise ValueError(k)
    return "$-$".join(parti) + ("$^\\dagger$" if vecchie else "")


def _segni(a: str, b: str) -> str:
    s = {"+": "+", "-": "-", "0": "0", "n.d.": "n.d."}
    return f"${s[a]}$" if a == b else f"${s[a]}\\to{s[b]}$"


def _lettura(r: dict) -> str:
    if r.get("cambia_verdetto"):
        return r"\textbf{verdict changes}"
    return "insensitive" if r.get("insensibile") else "sensitive"


def scrivi_D(ris: Path, f: Path) -> None:
    """Supplementare D (E14, difetto 21), da congelamento_e14b.json: D1 le dichiarazioni (a)-(e) per
    contesto, episodio e variante con gli intervalli dei due insiemi; D2 i livelli di C, A, F0, F0' e il
    rapporto costo/beneficio; D3 le selezioni su validazione, E7 e le letture 3/3; D4 le altre
    dichiarazioni (E3, E3-bis, E4, E8, E8-bis) con Δ e segni. Una variante = una colonna di lettura."""
    R = json.loads((ris / "congelamento_e14b.json").read_text())
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    md = Path(__file__).resolve().parents[1] / "CONGELAMENTO_E14B.md"   # radice del repository, non la sandbox
    fonte = (" Source: record \\texttt{CONGELAMENTO\\_E14B.md}, fingerprint \\texttt{" + imp(md) + "}; "
             if md.exists() else " Source: ") + \
        "\\texttt{congelamento\\_e14b.json}, fingerprint \\texttt{" + imp(ris / "congelamento_e14b.json") + "}."
    V, soglia = R["varianti"], R["soglia_delta"]
    crit = (f"$\\Delta$ = re-evaluated $-$ frozen (means); insensitive if $|\\Delta|<{soglia:g}$ wCE with the same "
            "interval sign; the verdict changes if the interval sign changes ($-$: below zero; $+$: above; 0: "
            "includes zero). Re-evaluation without retraining; validation selections redone under the variant.")
    out = []
    # D1 -------------------------------------------------------------------------------------------
    righe, prec = [], None
    for k, d in R["dichiarazioni"].items():
        if k == "stesso_segno":
            continue
        p = k.split("/")
        ctx, ep, s = (p[0], p[1].removeprefix("ep"), p[2]) if len(p) == 3 else (p[0], "--", p[1])
        if prec is not None and ctx != prec:
            righe.append("\\addlinespace")
        for i, v in enumerate(V):
            r = d["varianti"][v]
            righe.append(" & ".join([
                CTX_EN[ctx] if ctx != prec and i == 0 else "", ep if i == 0 else "", DICH_EN[s] if i == 0 else "",
                _ic(d["congelato"], scala=1.0, cifre=4) if i == 0 else "", f"({v})",
                _ic(r["valore"], scala=1.0, cifre=4), f"${r['delta']:+.4f}$",
                _segni(r["segno_congelato"], r["segno_variante"]), _lettura(r)]) + " \\\\")
            prec = ctx
    out.append(_longtable(
        "@{}l c l c c c r c l@{}",
        "E14: the five pre-registered statements of the replication table of the paper, per context and installation episode, "
        "frozen (non-causal coverage scalar) against each re-evaluation variant. Mean over cells and 95\\% interval "
        "from 4{,}000 joint resamples. " + crit,
        "Context & Ep. & Statement & Frozen & Var. & Re-evaluated & $\\Delta$ & Sign & Reading", righe, "tab:suppD1"))
    # D2 -------------------------------------------------------------------------------------------
    righe = []
    for c in ("Madrid", "Londra", "Melbourne"):
        for i, ins in enumerate(["congelato"] + [f"({v})" for v in V]):
            x = R["livelli"].get(f"{c}/{ins}")
            if x is None:
                continue
            lv, df, rp = x["livelli"], x["differenze"], x["rapporto_F0C_su_AC"]
            q = {"media": -rp["media"], "ic": [-rp["ic"][1], -rp["ic"][0]]}
            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", "frozen" if i == 0 else ins]
                                    + [f"{lv[a]['media']:.4f}" for a in ("C", "A", "F0", "F0p")]
                                    + [_ic({"media": df[a]["media"], "ic_con_nodi": df[a]["ic"]}, scala=1.0, cifre=4) for a in ("A-C", "F0-C")]
                                    + [f"${q['media']:.2f}$ \\scriptsize$[{q['ic'][0]:.2f}, {q['ic'][1]:.2f}]$"])
                         + " \\\\")
        righe.append("\\addlinespace")
    out.append(_longtable(
        "@{}l l r r r r c c c@{}",
        "E14: absolute wCE of $C$, $A$, $F_0$, $F_0'$ (episode 1, 36 cells per city), and the ratio of the transfer "
        "cost to the identity benefit, $(F_0-C)/(C-A)$, frozen and re-evaluated; intervals from 4{,}000 joint "
        "resamples with the same seed in both sets.",
        "City & Set & $C$ & $A$ & $F_0$ & $F_0'$ & $A-C$ & $F_0-C$ & $(F_0-C)/(C-A)$", righe[:-1], "tab:suppD2"))
    # D3 -------------------------------------------------------------------------------------------
    righe = []
    tn = lambda z: f"({TAU_EN.get(z['tau'], z['tau'])}, {z['N']})"
    for k, z in R["scelte"].items():
        p = k.split("/")
        if p[0] in ("E4", "E5k") or p[0].startswith("E6"):
            fase = {"E4": "E4 $(\\tau,N)$", "E5k": "E5 $k$ (secondary)"}.get(p[0], p[0].replace("(τ, N)", "$(\\tau,N)$"))
            ctx = CTX_EN.get(p[1], "") if len(p) == 3 else {"E6": "PEMS08", "E6a": "PEMS04"}[p[0].split()[0]]
            a, b = (tn(z["congelato"]), tn(z["variante"])) if isinstance(z["congelato"], dict) else (z["congelato"], z["variante"])
            righe.append(f"{fase} & {ctx} & {a} & {b} & " + ("\\textbf{changes}" if z["cambia"] else "unchanged") + " \\\\")
    for v in V:
        n, t = R["sintesi"][v]["soglie_e8_cambiate"]
        righe.append(f"E8 thresholds (F1-opt., FA parity) & all & -- & ({v}) & {n} of {t} change \\\\")
        e7c, e7v = R["e7"]["congelato"]["decisione"], R["e7"][f"({v})"]["decisione"]
        righe.append("E7 stage 1: hypothesis holds; stage 2a run & all & "
                     f"{'yes' if e7c['ipotesi_vale'] else 'no'}; {'yes' if e7c['stadio_2a'] else 'no'} & ({v}) "
                     f"{'yes' if e7v['ipotesi_vale'] else 'no'}; {'yes' if e7v['stadio_2a'] else 'no'} & "
                     + ("unchanged" if e7c == e7v else "\\textbf{changes}") + " \\\\")
        for k, z in R["dichiarazioni"]["stesso_segno"].items():
            c, s, vv = k.split("/")
            if vv == v:
                righe.append(f"3/3 reading, {DICH_EN[s]} & {CTX_EN[c]} & {''.join(z['congelato']['segni'])} & "
                             f"({v}) {''.join(z['variante']['segni'])} & "
                             + ("\\textbf{changes}" if z["cambia"] else "unchanged") + " \\\\")
    out.append(_longtable(
        "@{}l l l l l@{}",
        "E14: validation selections redone under each variant ($(\\tau,N)$ of the gating policy, update budget $k$ "
        "of the secondary variant of E5, decision thresholds of E8), the decision rule of E7, and the reading "
        "``same sign in 3/3 episodes'' of each statement per city (signs of episodes 1/2/3).",
        "Selection or reading & Context & Frozen & Re-evaluated & Outcome", righe, "tab:suppD3"))
    # D4 -------------------------------------------------------------------------------------------
    righe, prec = [], None
    voci = [(FASE_EN[k.split("/")[0]], k.split("/")[1], k.split("/")[2], k.split("/")[3], r)
            for k, r in R["altre"].items() if k.count("/") == 3]
    for misura, et in (("wce", "E8 (wCE)"), ("auc", "E8-bis ($\\Delta$AUC)")):
        voci += [(et, k.split("/")[0], k.split("/")[1], k.split("/")[2], r[misura])
                 for k, r in R["e8"].items() if r[misura]["delta"] is not None]
    for fase, ctx, conf, v, r in voci:
        if prec is not None and fase != prec:
            righe.append("\\addlinespace")
        righe.append(" & ".join([fase if fase != prec else "", CTX_EN[ctx], _nome_e14(conf), f"({v})",
                                 f"${r['delta']:+.4f}$", _segni(r["segno_congelato"], r["segno_variante"]),
                                 _lettura(r)]) + " \\\\")
        prec = fase
    for v in V:
        eq = R["altre"]["e3bis_equivalenza"]
        sn = lambda l: "/".join("yes" if x else "no" for x in l)
        righe += ["\\addlinespace", f"E3-bis & cities & R-orig$(1\\,\\mathrm{{wk}})\\equiv F'(1\\,\\mathrm{{wk}})$ "
                  f"$\\pm3\\%$ & ({v}) & -- & {sn(eq['congelato'])} $\\to$ {sn(eq[f'({v})'])} & "
                  + ("unchanged" if eq["congelato"] == eq[f"({v})"] else "\\textbf{changes}") + " \\\\"]
    out.append(_longtable(
        "@{}l l l c r c l@{}",
        "E14: the other comparisons reported in the paper (E3 retraining, E3 on veterans, E3-bis on common origins, "
        "E4 policy and adaptation arms, E8 wCE and E8-bis $\\Delta$AUC of the principal comparisons). " + crit
        + " $^\\dagger$ origins older than one week. Intervals of both sets are in the E14 record.",
        "Phase & Context & Comparison & Var. & $\\Delta$ & Sign & Reading", righe, "tab:suppD4"))
    f.write_text("\n".join(out).replace("}\\label{tab:suppD", fonte + "}\\label{tab:suppD"))
