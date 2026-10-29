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
# varianti di E14 per nome: (a)-(e) restano alle dichiarazioni
VAR_EN = {"c": "permuted", "a": "causal", "b": "causal-b"}
VAR_DEF = ("permuted variant: the scalar permuted across sensors; causal variant: the scalar computed from data "
           "available at installation.")


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
    # numeri dal file rigenerato (ris); impronte citate: quelle dei file congelati nel repository
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E14B.md", rep / "results" / "evoluzione" / "congelamento_e14b.json"
    fonte = " Source: record \\texttt{CONGELAMENTO\\_E14B.md}, fingerprint \\texttt{" + imp(md) + "}; " \
        "\\texttt{congelamento\\_e14b.json}, fingerprint \\texttt{" + imp(js) + "}."
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
                _ic(d["congelato"], scala=1.0, cifre=4) if i == 0 else "", VAR_EN[v],
                _ic(r["valore"], scala=1.0, cifre=4), f"${r['delta']:+.4f}$",
                _segni(r["segno_congelato"], r["segno_variante"]), _lettura(r)]) + " \\\\")
            prec = ctx
    out.append(_longtable(
        "@{}l c l c c c r c l@{}",
        "E14: the five pre-registered statements of the replication table of the paper, per context and installation episode, "
        "frozen (non-causal coverage scalar) against each re-evaluation variant (" + VAR_DEF[:-1] + "). Mean over cells and 95\\% interval "
        "from 4{,}000 joint resamples. " + crit,
        "Context & Ep. & Statement & Frozen & Var. & Re-evaluated & $\\Delta$ & Sign & Reading", righe, "tab:suppD1"))
    # D2 -------------------------------------------------------------------------------------------
    righe = []
    for c in ("Madrid", "Londra", "Melbourne"):
        for i, (ins, nome) in enumerate([("congelato", "frozen")] + [(f"({v})", VAR_EN[v]) for v in V]):
            x = R["livelli"].get(f"{c}/{ins}")
            if x is None:
                continue
            lv, df, rp = x["livelli"], x["differenze"], x["rapporto_F0C_su_AC"]
            q = {"media": -rp["media"], "ic": [-rp["ic"][1], -rp["ic"][0]]}
            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", nome]
                                    + [f"{lv[a]['media']:.4f}" for a in ("C", "A", "F0", "F0p")]
                                    + [_ic({"media": df[a]["media"], "ic_con_nodi": df[a]["ic"]}, scala=1.0, cifre=4) for a in ("A-C", "F0-C")]
                                    + [f"${q['media']:.2f}$ \\scriptsize$[{q['ic'][0]:.2f}, {q['ic'][1]:.2f}]$"])
                         + " \\\\")
        righe.append("\\addlinespace")
    out.append(_longtable(
        "@{}l l r r r r c c c@{}",
        "E14: absolute wCE of $C$, $A$, $F_0$, $F_0'$ (episode 1, 36 runs per city), and the ratio of the transfer "
        "cost to the advantage of the oracle with full history, $(F_0-C)/(C-A)$, frozen and re-evaluated; intervals from 4{,}000 joint "
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
            righe.append(f"{fase} & {ctx} & {VAR_EN[p[-1]]} & {a} & {b} & "
                         + ("\\textbf{changes}" if z["cambia"] else "unchanged") + " \\\\")
    for v in V:
        n, t = R["sintesi"][v]["soglie_e8_cambiate"]
        righe.append(f"E8 thresholds (F1-opt., FA parity) & all & {VAR_EN[v]} & -- & -- & {n} of {t} change \\\\")
        e7c, e7v = R["e7"]["congelato"]["decisione"], R["e7"][f"({v})"]["decisione"]
        righe.append(f"E7 stage 1: hypothesis holds; stage 2a run & all & {VAR_EN[v]} & "
                     f"{'yes' if e7c['ipotesi_vale'] else 'no'}; {'yes' if e7c['stadio_2a'] else 'no'} & "
                     f"{'yes' if e7v['ipotesi_vale'] else 'no'}; {'yes' if e7v['stadio_2a'] else 'no'} & "
                     + ("\\textbf{changes}" if R["sintesi"][v]["e7_cambia"] else "unchanged") + " \\\\")
        si = lambda x: "holds" if x["concorda"] else "does not hold"
        for k, z in R["dichiarazioni"]["stesso_segno"].items():
            c, s, vv = k.split("/")
            if vv == v:
                righe.append(f"3/3 reading, {DICH_EN[s]} & {CTX_EN[c]} & {VAR_EN[v]} & "
                             f"{''.join(z['congelato']['segni'])} ({si(z['congelato'])}) & "
                             f"{''.join(z['variante']['segni'])} ({si(z['variante'])}) & "
                             + ("\\textbf{reading changes}" if z["congelato"]["concorda"] != z["variante"]["concorda"]
                                else "signs change, reading unchanged" if z["cambia"] else "unchanged") + " \\\\")
    out.append(_longtable(
        "@{}l l l l l l@{}",
        "E14: validation selections redone under each variant ($(\\tau,N)$ of the gating policy, update budget $k$ "
        "of the secondary variant of E5, decision thresholds of E8), the decision rule of E7, and the reading "
        "``same sign in 3/3 episodes'' of each statement per city (signs of episodes 1/2/3).",
        "Selection or reading & Context & Variant & Frozen & Re-evaluated & Outcome", righe, "tab:suppD3"))
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
        righe.append(" & ".join([fase if fase != prec else "", CTX_EN[ctx], _nome_e14(conf), VAR_EN[v],
                                 f"${r['delta']:+.4f}$", _segni(r["segno_congelato"], r["segno_variante"]),
                                 _lettura(r)]) + " \\\\")
        prec = fase
    for v in V:
        eq = R["altre"]["e3bis_equivalenza"]
        sn = lambda l: "/".join("yes" if x else "no" for x in l)
        righe += ["\\addlinespace", f"E3-bis & cities & R-orig$(1\\,\\mathrm{{wk}})\\equiv F'(1\\,\\mathrm{{wk}})$ "
                  f"$\\pm3\\%$ & {VAR_EN[v]} & -- & {sn(eq['congelato'])} $\\to$ {sn(eq[f'({v})'])} & "
                  + ("unchanged" if eq["congelato"] == eq[f"({v})"] else "\\textbf{changes}") + " \\\\"]
    out.append(_longtable(
        "@{}l l l c r c l@{}",
        "E14: the other comparisons reported in the paper (E3 retraining, E3 on veterans, E3-bis on common origins, "
        "E4 policy and adaptation arms, E8 wCE and E8-bis $\\Delta$AUC of the principal comparisons). " + crit
        + " $^\\dagger$ origins older than one week. Intervals of both sets are in the E14 record.",
        "Phase & Context & Comparison & Var. & $\\Delta$ & Sign & Reading", righe, "tab:suppD4"))
    out = out[:2]          # nel supplemento del Paper 1 restano D1 e D2 (revisore, 28/10); D3 e D4 nel congelamento
    f.write_text("\n".join(out).replace("}\\label{tab:suppD", fonte + "}\\label{tab:suppD"))


# --- E: calibrazione (E16), da congelamento_e16.json -------------------------------------------------
CAL_EN = {"grezzo": "raw", "T_nll": "T: log-loss", "T_wce": "T: wCE", "V_nll": "V: log-loss", "V_wce": "V: wCE"}
BRACCI_E16 = (("C", "$C$"), ("A", "$A$"), ("F0", "$F_0$"), ("F0p", "$F_0'$"), ("Fp_672", r"$F'(1\,\mathrm{wk})$"))
DIFF_E16 = (("F0-C", r"$F_0-C$"), ("F0p-C", r"$F_0'-C$"), ("Fp_672-C", r"$F'(1\,\mathrm{wk})-C$"), ("A-C", r"$A-C$"))
GRUPPI_E16 = ("Madrid", "Londra", "Melbourne", "PEMS08")


def scrivi_E(ris: Path, f: Path) -> None:
    """Supplementare E (E16, calibrazione), da congelamento_e16.json: E1 la quota di calibrazione s per
    contesto e calibrazione; E2 le differenze fra bracci prima e dopo; E3 ECE per classe, log-loss non
    pesata, Brier e wCE per braccio e calibrazione. A senza calibrazione post-hoc (deviazione dichiarata)."""
    R = json.loads((ris / "congelamento_e16.json").read_text())
    G = R["gruppi"]
    # correzione 27 (E18, parte C): le righe di F'(1 sett.) sono sulle origini piu' vecchie di una settimana,
    # per F'(1 sett.) e per C, con i parametri di calibrazione di E16
    S = json.loads((ris / "congelamento_e18.json").read_text())["risultati"]["C"]["gruppi"]
    md18 = Path(__file__).resolve().parents[1] / "CONGELAMENTO_E18.md"
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E16.md", rep / "results" / "evoluzione" / "congelamento_e16.json"
    fonte = " Source: record \\texttt{CONGELAMENTO\\_E16.md}, fingerprint \\texttt{" + imp(md) + "}; " \
        "\\texttt{congelamento\\_e16.json}, fingerprint \\texttt{" + imp(js) + "}."
    fonte18 = " Rows marked $^\\dagger$: origins older than one week for both arms (correction~27), from record " \
        "\\texttt{CONGELAMENTO\\_E18.md}, fingerprint \\texttt{" + imp(md18) + "}, part C; calibration parameters as fitted " \
        "in E16 on the validation episode. All other rows: all origins after $t_1$."
    cal = [c for c in CAL_EN if c != "grezzo"]
    out = []
    righe = [CTX_EN[g] + " & " + " & ".join(_ic(G[g]["quota_calibrazione"][c], scala=1.0, cifre=2) for c in cal)
             + " \\\\" for g in GRUPPI_E16]
    righe.append("\\addlinespace")
    righe.append("lower limit $>0.5$ in all three cities & " + " & ".join(
        "yes" if R["criterio_s"][c] else "no" for c in cal) + " \\\\")
    out.append(_longtable(
        "@{}l c c c c@{}",
        "E16: calibration share $s=1-(F_0^{\\mathrm{cal}}-C^{\\mathrm{cal}})/(F_0-C)$ of the transfer cost, per context "
        "and post-hoc calibration (temperature or vector scaling, fitted per arm and cell on the validation episode "
        "alone, against the unweighted log-loss or against the campaign loss, wCE; T = temperature, V = vector), mean over cells and 95\\% interval "
        "from 4{,}000 joint resamples; cities: episode 1. The pre-registered criterion for ``calibration first'' "
        "is a lower limit above 0.5 in all three cities." + fonte,
        "Context & " + " & ".join(CAL_EN[c] for c in cal), righe, "tab:suppE1"))
    righe, prima = [], True
    for g in GRUPPI_E16:
        if not prima:
            righe.append("\\addlinespace")
        for i, (k, et) in enumerate(DIFF_E16):
            src = (lambda c: S[g]["differenze_settimana"][f"{k}/{c}"]) if k == "Fp_672-C" else \
                (lambda c: G[g]["differenze"][f"{k}/{c}"])
            et = et + "$^\\dagger$" if k == "Fp_672-C" else et
            righe.append((CTX_EN[g] if i == 0 else "") + f" & {et} & "
                         + " & ".join(_ic(src(c), scala=1.0, cifre=3) for c in CAL_EN) + " \\\\")
        prima = False
    out.append(_longtable(
        "@{}l l c c c c c@{}",
        "E16: differences in test wCE between arms before (raw) and after post-hoc calibration; $A$ has no "
        "embeddings for the validation sensors and is not calibrated, so $A-C$ after calibration uses the raw $A$ "
        "and the calibrated $C$ (declared deviation)." + fonte + fonte18,
        "Context & Difference & " + " & ".join(CAL_EN[c] for c in CAL_EN), righe, "tab:suppE2")
               .replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\scriptsize\\setlength{\\tabcolsep}{2pt}", 1))
    righe, prima = [], True
    for g in GRUPPI_E16:
        if not prima:
            righe.append("\\addlinespace")
        primo = True
        for b, et in BRACCI_E16 + (("C_sett", "$C$$^\\dagger$"),):
            for c in CAL_EN:
                if b in ("Fp_672", "C_sett"):       # correzione 27: solo la wCE e' ricalcolata sulla finestra
                    w = S[g]["wce_settimana"][f"{b.replace('_sett', '')}/{c}"]["media"]
                    righe.append((CTX_EN[g] if primo else "") + f" & {et}{'$^\\dagger$' if b == 'Fp_672' else ''} & "
                                 f"{CAL_EN[c]} & -- & -- & -- & -- & -- & {w:.4f} \\\\")
                    primo = False
                    continue
                m = G[g]["medie_test"].get(f"{b}/{c}")
                if m is None:
                    continue
                e = m["ece"]
                righe.append((CTX_EN[g] if primo else "") + f" & {et} & {CAL_EN[c]} & "
                             + " & ".join(f"{e[k]:.4f}" for k in ("0", "1", "2"))
                             + f" & {m['logloss']:.4f} & {m['brier']:.4f} & {m['wce']:.4f} \\\\")
                primo = False
        prima = False
    out.append(_longtable(
        "@{}l l l c c c c c c@{}",
        "E16: expected calibration error per class (10 reliability bins), unweighted log-loss, multiclass Brier score "
        "and wCE on the test, per arm and calibration, means over cells. Calibrating against the unweighted log-loss "
        "targets the natural class distribution, while the campaign loss is minimised by the class-reweighted "
        "posterior: vector scaling against log-loss brings every class's ECE below 0.04 but raises the wCE. "
        "For $F'(1\\,\\mathrm{wk})$ only the wCE is recomputed on its causal window (--: not recomputed); the row "
        "$C^\\dagger$ is $C$ on the same window." + fonte + fonte18,
        "Context & Arm & Calibration & \\multicolumn{3}{c}{ECE (free / mod. / cong.)} & log-loss & Brier & wCE", righe, "tab:suppE3"))
    f.write_text("\n".join(out))


# --- E: campagna causale (E15), da congelamento_e15.json ---------------------------------------------
DICH_E15 = (("F0-C", r"$F_0-C$"), ("F0p-C", r"$F_0'-C$"), ("Fp_672-C", r"$F'(1\,\mathrm{wk})-C$$^\dagger$"),
            ("Fp_672-A", r"$F'(1\,\mathrm{wk})-A$$^\dagger$"), ("A-C", r"$A-C$"), ("A-C_A", r"$A-C_A$"),
            ("C_A-C", r"$C_A-C$"), ("Fpk_672-C", r"$F'(1\,\mathrm{wk};k)-C$$^\dagger$"),
            ("Fpk_672-A", r"$F'(1\,\mathrm{wk};k)-A$$^\dagger$"))
CAT_EN = {"superiorita'": "superiority", "non inferiorita'": "non-inferiority", "inconclusivo": "inconclusive",
          "inferiorita'": "inferiority"}
CITTA_E15 = ("Madrid", "Londra", "Melbourne")


def scrivi_E15(ris: Path, f: Path) -> None:
    """Supplementare E (E15, campagna causale end-to-end), da congelamento_e15.json: E1 le dichiarazioni
    causali con categoria, accanto alla congelata sulle stesse celle e alla pubblicata a dodici semi; E2 i
    rapporti, il recupero e la riduzione del token; E3 la secondaria k; E4 i livelli; E5 costi e controlli."""
    R = json.loads((ris / "congelamento_e15.json").read_text())["risultati"]
    D = R["citta"]
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E15.md", rep / "results" / "evoluzione" / "congelamento_e15.json"
    fonte = " Source: record \\texttt{CONGELAMENTO\\_E15.md}, fingerprint \\texttt{" + imp(md) + "}; " \
        "\\texttt{congelamento\\_e15.json}, fingerprint \\texttt{" + imp(js) + "}."
    neg = lambda r: {"media": -r["media"], "ic_con_nodi": [-r["ic_con_nodi"][1], -r["ic_con_nodi"][0]]}
    out = []
    # E1
    righe, prima = [], True
    for c in CITTA_E15:
        if not prima:
            righe.append("\\addlinespace")
        for i, (k, et) in enumerate(DICH_E15):
            r = D[c]["dichiarazioni"][k]
            cg, pb = D[c]["congelate"].get(k), D[c]["pubblicate"].get(k)
            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", et, _ic(r, scala=1.0, cifre=3),
                                     CAT_EN.get(r["categoria"], r["categoria"]),
                                     _ic(cg, scala=1.0, cifre=3) if cg else "--",
                                     ("confirmed" if r.get("confermata") else "\\textbf{changed}") if cg else "new",
                                     _ic(pb, scala=1.0, cifre=3) if pb else "--"]) + " \\\\")
        prima = False
    out.append(_longtable(
        "@{}l l c l c l c@{}",
        "E15: the differences of the causal campaign (six seeds, 18 cells per city, episode 1), with the category of "
        "Section~III of the paper (inferiority: interval above zero), against the pre-registered campaign on the "
        "same cells and resamples (frozen) and the published value on twelve seeds; $k$: update budget reselected on "
        "the causal validation episode. $^\\dagger$ origins older than one week; otherwise all origins after $t_1$."
        + fonte, "City & Difference & Causal & Category & Frozen, same cells & Verdict & Published (12 seeds)",
        righe, "tab:suppE15a").replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\scriptsize\\setlength{\\tabcolsep}{2pt}", 1))
    # E2
    righe = []
    for c in CITTA_E15:
        rp, ad = D[c]["rapporti"], D[c]["addendum"]
        rc, rt = ad["recupero"], ad["riduzione_token"]
        righe.append(" & ".join([CTX_EN[c], _ic(neg(rp["(F0-C)/(A-C)"]), scala=1.0, cifre=2),
                                 _ic(neg(rp["(F0-C)/(A-C_A)"]), scala=1.0, cifre=2),
                                 _ic(rp["(C_A-C)/(A-C)"], scala=1.0, cifre=2),
                                 _ic(rc["causale (L_C-L_A)"], scala=1.0, cifre=2),
                                 _ic(rc["causale (L_C_A-L_A)"], scala=1.0, cifre=2),
                                 _ic(rt["causale"], scala=1.0, cifre=2)]) + " \\\\")
    out.append(_longtable(
        "@{}l c c c c c c@{}",
        "E15: ratio of the transfer cost to the oracle's advantage, $(F_0-C)/(C-A)$, and to the value of identity, "
        "$(F_0-C)/(C_A-A)$ (the frozen ratio, on the same cells, is in the E15 record); share of the oracle's advantage due to the additional data, "
        "$(C_A-C)/(A-C)$; recovery of one week of adaptation, $(L_C-L_{F'})/(L_C-L_A)$ and $(L_C-L_{F'})/(L_{C_A}-L_A)$ "
        "(origins older than one week); reduction of the transfer cost by the token, $1-(F_0'-C)/(F_0-C)$. Ratios of "
        "means within each resample." + fonte,
        "City & $\\frac{F_0-C}{C-A}$ & $\\frac{F_0-C}{C_A-A}$ & $\\frac{C_A-C}{A-C}$ & "
        "recovery & recovery ($C_A$) & token", righe, "tab:suppE15b")
               .replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\scriptsize\\setlength{\\tabcolsep}{2pt}", 1))
    # E3
    righe = []
    for c in CITTA_E15:
        z = R["k_secondaria"][c]
        righe.append(f"{CTX_EN[c]} & " + " & ".join(f"{z['wce_validazione'][k]:.4f}" for k in ("10", "50", "200"))
                     + f" & {z['k']} & {z['k_congelato']} \\\\")
    out.append(_longtable(
        "@{}l c c c c c@{}",
        "E15: update budget $k$ of the secondary adaptation, reselected per city on the causal validation episode "
        "(validation wCE on origins older than one week; ties to the smaller $k$; step frozen), against the frozen "
        "budget." + fonte, "City & $k=10$ & $k=50$ & $k=200$ & chosen & frozen", righe, "tab:suppE15c"))
    # E4
    BR = (("C", "$C$"), ("A", "$A$"), ("C_A", "$C_A$"), ("F0", "$F_0$"), ("F0p", "$F_0'$"))
    righe = []
    for c in CITTA_E15:
        L = D[c]["livelli"]
        for i, ins in enumerate(("causale", "congelata")):
            righe.append(" & ".join([CTX_EN[c] if i == 0 else "", "causal" if i == 0 else "frozen"]
                                    + [f"{L[f'{ins}/{b}']['media']:.4f}" if f"{ins}/{b}" in L else "--" for b, _ in BR]
                                    + [f"{L[f'{ins}/Fp_672/settimana']['media']:.4f}"]) + " \\\\")
    out.append(_longtable(
        "@{}l l c c c c c c@{}",
        "E15: test wCE per arm, mean over cells, causal and frozen on the same cells (all origins after $t_1$; "
        "$F'(1\\,\\mathrm{wk})$ on origins older than one week)." + fonte,
        "City & Set & " + " & ".join(e for _, e in BR) + " & $F'(1\\,\\mathrm{wk})$", righe, "tab:suppE15d"))
    # E5
    K, ES, Z = R["costi"]["addestramenti"], R["costi"]["esito_e15"], R["controllo_scarto_zero"]
    NOMI = {"E": "$E$", "E1": "$E'$", "C": "$C$", "A": "$A$", "C_A": "$C_A$"}
    num = lambda x: "--" if x is None else f"{x:.1f}"      # tempi assenti dove i registri non ci sono
    righe = [f"{NOMI.get(b, b)} & {K[b]['n']} & {num(K[b]['minuti_mediana'])} & {num(K[b]['ore_macchina'])} \\\\"
             for b in K]
    out.append(_longtable(
        "@{}l r r r@{}",
        f"E15: training cost per arm ({ES['completate']} trainings in {ES['ore_calendario']:.1f}\\,h of calendar "
        f"time, {ES['ore_macchina']:.1f} machine-hours, on {ES['ambiente']['piattaforma'].replace('_', chr(92) + '_')}, "
        f"{ES['ambiente']['nuclei_logici']} cores, one thread per worker). Zero-difference control: cell "
        f"{CTX_EN[Z['cella']['contesto']]} p{Z['cella']['partizione']} seed {Z['cella']['seme']}, arm "
        f"{Z['cella']['braccio']}, retrained with the frozen scalar: wCE {Z['wce_congelata']:.12f} frozen, "
        f"{Z['wce_riprodotta']:.12f} reproduced, checkpoint identical to the bit." + fonte,
        "Arm & trainings & minutes per training (median) & machine-hours", righe, "tab:suppE15e"))
    f.write_text("\n".join(out))


# --- G: analisi di verifica della seconda revisione esterna (E18), da congelamento_e18.json ------------
CONF_A_EN = {"F0-C": r"$F_0-C$", "F0p-F0": r"$F_0'-F_0$", "F0p-C": r"$F_0'-C$", "A-C": r"$A-C$",
             "Fp_672-C": r"$F'(1\,\mathrm{wk})-C$"}
BR_A_EN = {"A": "$A$", "C": "$C$", "F0": "$F_0$", "F0p": "$F_0'$", "Fp_672": r"$F'(1\,\mathrm{wk})$"}
FIN_EN = {"intero": "all after $t_1$", "sett": r"$>1$\,wk"}
LIV_E18 = ("0.005", "0.01", "0.02", "0.05", "0.1")
GRUPPI_E18 = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
DIFF_B_EN = {"(a) F0p-C": r"(a) $F_0'-C$", "(b) gated-F0p": r"(b) gated$-F_0'$",
             "(c) Fp_672-C >1sett": r"(c) $F'(1\,\mathrm{wk})-C$$^\dagger$", "(d) Fp_96-C": r"(d) $F'(24\,\mathrm{h})-C$",
             "(e) Fp_672-A >1sett": r"(e) $F'(1\,\mathrm{wk})-A$$^\dagger$",
             "E17 gated(1sett,0)-F0p": r"gated$(1\,\mathrm{wk},0)-F_0'$",
             "E17 gated(1sett,0)-gated": r"gated$(1\,\mathrm{wk},0)-$gated$(\tau,N)$",
             "E17 Rorig_672-Fp_672 >1sett": r"R-orig$(1\,\mathrm{wk})-F'(1\,\mathrm{wk})$$^\dagger$",
             "Rorig_672-Fp_672 >1sett": r"R-orig$(1\,\mathrm{wk})-F'(1\,\mathrm{wk})$$^\dagger$",
             "F0-C": r"$F_0-C$", "F0p-C": r"$F_0'-C$", "Fp_672-C >1sett": r"$F'(1\,\mathrm{wk})-C$$^\dagger$",
             "Fp_672-A >1sett": r"$F'(1\,\mathrm{wk})-A$$^\dagger$", "A-C": r"$A-C$", "A-C_A": r"$A-C_A$",
             "C_A-C": r"$C_A-C$", "Fpk_672-C >1sett": r"$F'(1\,\mathrm{wk};k)-C$$^\dagger$",
             "Fpk_672-A >1sett": r"$F'(1\,\mathrm{wk};k)-A$$^\dagger$"}


def _ctx_e18(c: str) -> str:
    """'Madrid/ep3' -> 'Madrid ep.\\ 3'; 'E15 Londra' -> 'London (E15)'; 'E3-bis Melbourne' -> 'Melbourne (E3-bis)'."""
    if "/ep" in c:
        g, e = c.split("/ep")
        return f"{CTX_EN[g]} ep.\\ {e}"
    if " " in c:
        camp, g = c.split(" ", 1)
        return f"{CTX_EN[g]} ({camp})"
    return CTX_EN[c]


def _ic_lista(m, lo_hi, cifre=4):
    return f"${m:+.{cifre}f}$ {{\\tiny$[{lo_hi[0]:+.{cifre}f},{lo_hi[1]:+.{cifre}f}]$}}"


def _ic_t(r, scala=100.0, cifre=1):           # come _ic, intervallo in \\tiny (tabelle larghe)
    return _ic_lista(r["media"] * scala, [v * scala for v in r["ic_con_nodi"]], cifre)


def scrivi_E18(ris: Path, f: Path) -> None:
    """Supplementare G (E18): G1 AUC e pAUC per braccio (ROC empirica); G2 confronti, Delta AUC, Delta pAUC e
    Delta richiamo a falsi allarmi fissi; G3 richiamo perso da F0 sotto argmax e quota recuperata a FA 5 %;
    G4 bootstrap per sensore fisico contro quello attuale; G5 margini minimi di equivalenza; G6 provenienza
    della politica gated(1 sett., 0)."""
    R = json.loads((ris / "congelamento_e18.json").read_text())["risultati"]
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E18.md", rep / "results" / "evoluzione" / "congelamento_e18.json"
    fonte = " Source: record \\texttt{CONGELAMENTO\\_E18.md}, fingerprint \\texttt{" + imp(md) + "}; " \
        "\\texttt{congelamento\\_e18.json}, fingerprint \\texttt{" + imp(js) + "}."
    A, B, D = R["A"], R["B"], R["D"]
    out = []
    # G1
    righe, prima = [], True
    for g in GRUPPI_E18:
        G = A["gruppi"].get(g)
        if G is None:
            continue
        if not prima:
            righe.append("\\addlinespace")
        for i, k in enumerate(sorted(G["metriche"])):
            b, fin = k.split("/")
            m = G["metriche"][k]
            righe.append((CTX_EN[g] if i == 0 else "") + f" & {BR_A_EN[b]} & {FIN_EN[fin]} & "
                         + _ic(m["auc"], scala=1.0, cifre=3) + " & " + _ic(m["pauc"], scala=1.0, cifre=3) + " \\\\")
        prima = False
    out.append(_longtable(
        "@{}l l l c c@{}",
        "E18, part A: AUC and partial AUC on false-alarm rates 0--10\\% (area divided by 0.10) of the empirical ROC on "
        "the congested class, per arm; score $p(\\text{congested})$ per origin, sensor and horizon on valid targets, all "
        "distinct scores of a cell as thresholds, cell = unit, mean over cells and 95\\% interval from 4{,}000 joint "
        "resamples. Windows: all origins after $t_1$, or origins older than one week (for $F'(1\\,\\mathrm{wk})$ and the "
        "$C$ it is compared with). These replace the 19-threshold AUC of the operational-metrics experiment; the partial "
        "AUC is descriptive. Cities: episode 1, pre-registered campaign (36 cells); PEMS04 has neither $E$ nor $A$." + fonte,
        "Context & Arm & Window & AUC & pAUC (0--10\\%)", righe, "tab:suppG1"))
    # G2
    righe, prima = [], True
    for g in GRUPPI_E18:
        G = A["gruppi"].get(g)
        if G is None:
            continue
        if not prima:
            righe.append("\\addlinespace")
        for i, (k, d) in enumerate(G["confronti"].items()):
            righe.append((CTX_EN[g] if i == 0 else "") + f" & {CONF_A_EN[k]} & " + _ic_t(d["auc"], scala=1.0, cifre=3)
                         + " & " + _ic_t(d["pauc"], scala=1.0, cifre=3) + " & "
                         + " & ".join(_ic_t(d[f"richiamo_fa_{l}"]) for l in LIV_E18) + " \\\\")
        prima = False
    out.append(_longtable(
        "@{}l l c c c c c c c@{}",
        "E18, part A: differences between arms on the empirical ROC (same resampling indices for both arms): "
        "$\\Delta$AUC, $\\Delta$pAUC (0--10\\%) and $\\Delta$recall on the congested class, in points, at fixed "
        "false-alarm rates 0.5, 1, 2, 5 and 10\\% (linear interpolation). Window: all origins after $t_1$, except "
        "$F'(1\\,\\mathrm{wk})-C$, on origins older than one week." + fonte,
        "Context & Difference & $\\Delta$AUC & $\\Delta$pAUC & 0.5\\% & 1\\% & 2\\% & 5\\% & 10\\%", righe, "tab:suppG2")
               .replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\tiny\\setlength{\\tabcolsep}{1pt}", 1))
    # G3
    righe = []
    for g in GRUPPI_E18:
        G = A["gruppi"].get(g)
        r = G.get("recupero_argmax") if G else None
        if not r:
            continue
        am = G["argmax"]
        righe.append(f"{CTX_EN[g]} & {100 * am['C']['richiamo']:.1f} & {100 * am['F0']['richiamo']:.1f} & "
                     + _ic(r["perdita_argmax_punti"], scala=1.0) + " & " + _ic(r["perdita_fa5_punti"], scala=1.0)
                     + " & " + _ic(r["quota_recuperata"], scala=1.0, cifre=3) + " \\\\")
    out.append(_longtable(
        "@{}l c c c c c@{}",
        "E18, part A: recall on the congested class lost by $F_0$ against $C$ under the argmax rule, and the share "
        "recovered at a fixed false-alarm rate of 5\\%: $1-(\\text{loss at 5\\%})/(\\text{loss under argmax})$, in points of "
        "recall; all origins after $t_1$. A share above 1 (PEMS08) means that at 5\\% false alarms $F_0$ recalls more "
        "than $C$." + fonte,
        "Context & recall, $C$ (argmax) & recall, $F_0$ (argmax) & loss under argmax & loss at 5\\% & share recovered",
        righe, "tab:suppG3"))
    # G4
    righe, prima = [], True
    for c, X in B["contesti"].items():
        if not prima:
            righe.append("\\addlinespace")
        for i, (k, d) in enumerate(X["differenze"].items()):
            cambia = d["categoria_attuale"] != d["categoria_per_sensore"]
            cat = CAT_EN[d["categoria_per_sensore"]]
            righe.append((f"{_ctx_e18(c)} & {X['sensori_distinti']}/{X['occorrenze']}" if i == 0 else " & ")
                         + f" & {DIFF_B_EN[k]} & ${d['media_attuale']:+.4f}$ & "
                         f"\\scriptsize$[{d['ic_attuale'][0]:+.4f}, {d['ic_attuale'][1]:+.4f}]$ & {CAT_EN[d['categoria_attuale']]} & "
                         f"\\scriptsize$[{d['ic_per_sensore'][0]:+.4f}, {d['ic_per_sensore'][1]:+.4f}]$ & "
                         + (f"\\textbf{{{cat}}}" if cambia else cat) + " \\\\")
        prima = False
    out.append(_longtable(
        "@{}l c l c c l c l@{}",
        "E18, part B: intervals from the current joint resampling (partitions $\\times$ seeds $\\times$ sensor "
        "positions; pre-registered, primary) and from a resampling that preserves the physical sensor (sensitivity): "
        "physical sensor identifiers drawn with replacement among the distinct sensors of the context's partitions, "
        "each partition weighting its test sensors by the multiplicity of their identifier, weights shared across "
        "arms, partitions and seeds; 4{,}000 replicates. Categories as in the main paper ($\\delta=0.005$ wCE). "
        "Second column: distinct sensors / sensor--partition occurrences. Changes of category in bold. "
        "$^\\dagger$: origins older than one week." + fonte,
        "Context & sensors & Difference & mean & current interval & category & sensor-level interval & category",
        righe, "tab:suppG4")
               .replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\scriptsize\\setlength{\\tabcolsep}{2pt}", 1))
    # G5
    righe = []
    for c, X in B["contesti"].items():
        for k, d in X["differenze"].items():
            if "margine_minimo_attuale" in d:
                righe.append(f"{_ctx_e18(c)} & {d['margine_minimo_attuale']:.4f} & {d['margine_minimo_per_sensore']:.4f} \\\\")
    out.append(_longtable(
        "@{}l c c@{}",
        "E18, part B: smallest equivalence margin of R-orig$(1\\,\\mathrm{wk})$ and $F'(1\\,\\mathrm{wk})$ on the "
        "origins older than one week, $\\max(|\\text{lower}|,|\\text{upper}|)$ of the 95\\% interval (TOST at "
        "$\\alpha=0.025$ per side), under the current and the sensor-level resampling, in wCE." + fonte,
        "Context & current & sensor-level", righe, "tab:suppG5"))
    # G6
    righe = []
    for c, X in D["contesti"].items():
        a, b, o = X["gated0-F0p"], X["gated0-gated"], X["osservato"]
        camp = X["campagna"].replace("campagna principale", "main campaign").replace("parte A", "part A")
        righe.append(f"{_ctx_e18(c)} & {camp} & " + _ic_lista(a["media"], a["ic_attuale"]) + f" & {CAT_EN[a['categoria_attuale']]} & "
                     f"{{\\tiny$[{a['ic_per_sensore'][0]:+.4f},{a['ic_per_sensore'][1]:+.4f}]$}} & {CAT_EN[a['categoria_per_sensore']]} & "
                     + _ic_lista(b["media"], b["ic_attuale"]) + f" & {CAT_EN[b['categoria_attuale']]} & {o['data']} \\\\")
    pf = D["prima_formulazione"]
    FONTE_EN = {"protocollo": "protocol", "manoscritto": "manuscript"}
    det = "; ".join(f"{FONTE_EN.get(t, t)}, {k} {v['data']} (commit {v['commit']})"
                    for t, s in pf["dettaglio"].items() for k, v in s.items())
    det = det.replace("«", "``").replace("»", "''").replace("gated(1 sett., 0)", "gated(1 wk, 0)")
    E = D["esito"]
    out.append(_longtable(
        "@{}l l c l c l c l c@{}",
        "E18, part D: provenance of the policy gated$(1\\,\\mathrm{wk},0)$ (token until one week, then $F'(1\\,\\mathrm{wk})$ "
        "for every sensor). For each context: integrated wCE of the policy against $F_0'$ (current and sensor-level "
        "interval) and against the selected gated$(\\tau,N)$, and the date on which the results of that context were "
        "first observed (first commit of its frozen record). First written formulation of the policy: "
        f"{pf['data']} ({det}). {E['osservati_prima_della_formulazione']} of {E['contesti']} contexts had been observed "
        "before it: the policy is a post hoc descriptive evaluation on the eleven contexts, without prospective "
        "confirmation." + fonte,
        "Context & campaign & gated$(1\\,\\mathrm{wk},0)-F_0'$ & category & sensor-level & category & "
        "gated$(1\\,\\mathrm{wk},0)-$gated$(\\tau,N)$ & category & first observed", righe, "tab:suppG6")
               .replace("{\\footnotesize\\setlength{\\tabcolsep}{3pt}", "{\\scriptsize\\setlength{\\tabcolsep}{2pt}", 1))
    f.write_text("\n".join(out))
