#!/usr/bin/env python3
"""
E18-quater in `analysis/main.py` e in `analysis/tabelle_suppl.py` (sostituzioni letterali: si ferma se un testo
atteso non compare esattamente una volta). Richiesta del revisore del 3/11/2026, 12:40.

main.py: fase E18QUATER dopo E18TER (parte A `esegui_e18quater.py --fase analizza`, parte B
`classi_per_sensore.py`, congelamento); "E18QUATER" in ESPERIMENTI; due tabelle del supplemento nel blocco del
manoscritto (`figures/tableE_e18quater.tex`, sezione E dopo E10; `figures/tableC_classi_sensori.tex`, accanto a C5).
tabelle_suppl.py: `scrivi_E18quater` (tab:suppE18quater) e `scrivi_classi_sensori` (tab:suppC5bis), da
`congelamento_e18quater.json`.

Dalla radice OR3/:  python3 evoluzione/audit/patch/patch_e18quater_main.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[3]
MAIN = R / "analysis" / "main.py"
SUPP = R / "analysis" / "tabelle_suppl.py"

SOST = {MAIN: [
    ('''    F("E18TER", ["genera_congelamento_e18ter.py"], [R_ + "congelamento_e18ter.json", "CONGELAMENTO_E18TER.md"]),
]''',
     '''    F("E18TER", ["genera_congelamento_e18ter.py"], [R_ + "congelamento_e18ter.json", "CONGELAMENTO_E18TER.md"]),
    # E18-quater (3/11/2026): parte A, C_A ri-valutato con la coverage dei nuovi uguale a quella di C (le celle
    # predizioni_e18quater/ sono un ingresso, come predizioni_e15/); parte B, classi per sensore nei bersagli; congelamento
    F("E18QUATER", [E + "esegui_e18quater.py", "--fase", "analizza"], [R_ + "e18quater_risultati.json"]),
    F("E18QUATER", [A + "classi_per_sensore.py"], [R_ + "e18quater_classi_risultati.json"]),
    F("E18QUATER", ["genera_congelamento_e18quater.py"], [R_ + "congelamento_e18quater.json", "CONGELAMENTO_E18QUATER.md"]),
]'''),
    ('''ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15", "E18", "E18TER"]''',
     '''ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15", "E18", "E18TER", "E18QUATER"]'''),
    ('''            if "E18TER" in a.solo:                  # supplementare G7 (E18-ter, livelli assoluti alle soglie operative)
                from analysis.tabelle_suppl import scrivi_E18ter
                print("[paper] tabella G7 del supplementare (E18-ter)", flush=True)
                scrivi_E18ter(radice / RIS, dfig / "tableG_e18ter.tex")''',
     '''            if "E18TER" in a.solo:                  # supplementare G7 (E18-ter, livelli assoluti alle soglie operative)
                from analysis.tabelle_suppl import scrivi_E18ter
                print("[paper] tabella G7 del supplementare (E18-ter)", flush=True)
                scrivi_E18ter(radice / RIS, dfig / "tableG_e18ter.tex")
            if "E18QUATER" in a.solo:               # supplementare: sezione E dopo E10 (parte A) e accanto a C5 (parte B)
                from analysis.tabelle_suppl import scrivi_E18quater, scrivi_classi_sensori
                print("[paper] tabelle E18-quater del supplementare (coverage di C_A; classi per sensore)", flush=True)
                scrivi_E18quater(radice / RIS, dfig / "tableE_e18quater.tex")
                scrivi_classi_sensori(radice / RIS, dfig / "tableC_classi_sensori.tex")'''),
], SUPP: [
    ('''REG_TER_EN = {"prim": "F1-optimal", "par": "validation-FPR-matched"}''',
     '''REG_TER_EN = {"prim": "F1-optimal", "par": "validation-FPR-matched"}
DIFF_Q_EN = {"C_A_esp-C_A": r"$C_A^{\\mathrm{exp}}-C_A$", "C_A_esp-C": r"$C_A^{\\mathrm{exp}}-C$",
             "A-C_A_esp": r"$A-C_A^{\\mathrm{exp}}$", "A-C_A": r"$A-C_A$", "C_A-C": r"$C_A-C$"}
GRP_Q_EN = {"iniziali": "initial", "nuovi": "new", "validazione": "validation"}


def _fonte_e18quater():
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E18QUATER.md", rep / "results" / "evoluzione" / "congelamento_e18quater.json"
    return (" Source: record \\\\texttt{CONGELAMENTO\\\\_E18QUATER.md}, fingerprint \\\\texttt{" + imp(md) + "}; "
            "\\\\texttt{congelamento\\\\_e18quater.json}, fingerprint \\\\texttt{" + imp(js) + "}.")


def scrivi_E18quater(ris: Path, f: Path) -> None:
    """Supplementare, sezione E dopo E10 (E18-quater, parte A): C_A ri-valutato con la coverage di valutazione dei
    sensori nuovi uguale a quella di C — C_A^exp − C_A, C_A^exp − C, quota del divario dovuta alla coverage, A − C_A^exp,
    con intervalli; da congelamento_e18quater.json (file figures/tableE_e18quater.tex)."""
    A = json.loads((ris / "congelamento_e18quater.json").read_text())["risultati"]["parte_A"]
    righe = []
    for i, c in enumerate(CITTA_E15):
        Rc = A["citta"][c]
        if i:
            righe.append("\\\\addlinespace")
        for j, k in enumerate(("C_A_esp-C_A", "C_A_esp-C", "A-C_A_esp", "A-C_A", "C_A-C")):
            d = Rc["differenze"][k]
            q = Rc["quota_coverage"]
            righe.append(" & ".join([CTX_EN[c] if j == 0 else "", DIFF_Q_EN[k], _ic(d, scala=1.0, cifre=4),
                                     CAT_EN.get(d["categoria"], d["categoria"]),
                                     (f"${q['media']:.2f}$ \\\\scriptsize$[{q['ic_con_nodi'][0]:.2f}, {q['ic_con_nodi'][1]:.2f}]$" if j == 0 else "")])
                         + " \\\\\\\\")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(_longtable(
        "@{}l l c l c@{}",
        "E18-quater: the frozen $C_A$ of the causal campaign re-evaluated with the same coverage of the new sensors as $C$ "
        "(expanding window from $t_0$; in the causal campaign $A$ and $C_A$ receive the coverage computed on $[0,t_0)$, as "
        "for initial sensors). $C_A^{\\\\mathrm{exp}}-C_A$ is the effect of the evaluation coverage (same model); "
        "$C_A^{\\\\mathrm{exp}}-C$ the effect of the pre-$t_0$ history of the new sensors in training, at equal coverage; "
        "$A-C_A^{\\\\mathrm{exp}}$ the value of identity at equal coverage. Share: fraction of the gap $C_A-C$ due to the "
        "coverage, $(C_A-C_A^{\\\\mathrm{exp}})/(C_A-C)$. wCE, all origins after $t_1$, 18 runs per city; mean and 95\\\\% "
        "interval from 4{,}000 joint resamples (partitions, seeds, sensor positions), the same draws as the causal campaign; "
        "category as in Section~III of the paper." + _fonte_e18quater(),
        "City & Difference & wCE & Category & Share of $C_A-C$ due to coverage", righe, "tab:suppE18quater"))


def scrivi_classi_sensori(ris: Path, f: Path) -> None:
    """Supplementare, accanto a C5 (E18-quater, parte B): per contesto e gruppo di sensori, la quota di bersagli
    congestionati per sensore nel periodo di prova (min, quartili, mediana, max, sensori con zero congestionati); da
    congelamento_e18quater.json (file figures/tableC_classi_sensori.tex)."""
    B = json.loads((ris / "congelamento_e18quater.json").read_text())["risultati"]["parte_B"]
    righe = []
    for i, g in enumerate(("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")):
        G = B["contesti"][g]
        if i:
            righe.append("\\\\addlinespace")
        for j, grp in enumerate(("iniziali", "nuovi")):
            s = G["gruppi"][grp]
            righe.append(" & ".join([CTX_EN[g] if j == 0 else "", str(len(G["partizioni"])) if j == 0 else "", GRP_Q_EN[grp], str(s["n"]),
                                     f"{100 * s['min']:.1f}", f"{100 * s['q1']:.1f}", f"{100 * s['mediana']:.1f}", f"{100 * s['q3']:.1f}",
                                     f"{100 * s['max']:.1f}", f"{100 * s['quota_congestionati_aggregata']:.1f}", str(s["zero_congestionati"])])
                         + " \\\\\\\\")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(_longtable(
        "@{}l c l r r r r r r r r@{}",
        "Share of congested targets per sensor (\\\\%) in the test window of each context (origins after $t_1$, four "
        "horizons, valid cells only), for the initial sensors (training partition) and the new sensors (test partition) "
        "of every node partition used by the experiments; statistics over the (partition, sensor) pairs: minimum, "
        "quartiles, median, maximum, pooled share, and number of sensors with no congested target. The congestion "
        "class is defined on the ratio of speed to the free-flow reference: per segment (reference \\\\texttt{free\\\\_flow\\\\_kph}, "
        "thresholds 0.8/0.4) on Traffic4cast, per partition (95th percentile of the initial sensors' aggregated speeds "
        "in the training period, thresholds 0.8/0.5) on PEMS." + _fonte_e18quater(),
        "Context & Part. & Sensors & Pairs & Min & Q1 & Median & Q3 & Max & Pooled & Zero", righe, "tab:suppC5bis"))'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\\n{v[:150]}"); return 1
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, n in coppie:
            t = t.replace(v, n)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
