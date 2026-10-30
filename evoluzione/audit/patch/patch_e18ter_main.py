#!/usr/bin/env python3
"""
E18-ter in `analysis/main.py` e in `analysis/tabelle_suppl.py` (sostituzioni letterali: si ferma se un testo
atteso non compare esattamente una volta).

main.py: fase E18TER (analisi dei livelli e congelamento) dopo E18; "E18TER" in ESPERIMENTI; tabella G7 del
supplemento (`figures/tableG_e18ter.tex`) nel blocco del manoscritto.
tabelle_suppl.py: `scrivi_E18ter` — tabella `tab:suppG7`, livelli assoluti alle soglie operative, da
`congelamento_e18ter.json` (nome per il rimando di P1: Table G7, file `figures/tableG_e18ter.tex`).

Dalla radice OR3/:  python3 patch_e18ter_main.py
"""
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
MAIN = R / "analysis" / "main.py"
SUPP = R / "analysis" / "tabelle_suppl.py"

SOST = {MAIN: [
    ('''    F("E18", ["genera_congelamento_e18.py"], [R_ + "congelamento_e18.json", "CONGELAMENTO_E18.md"]),
]''',
     '''    F("E18", ["genera_congelamento_e18.py"], [R_ + "congelamento_e18.json", "CONGELAMENTO_E18.md"]),
    # E18-ter (terza revisione esterna, sola analisi): livelli assoluti alle soglie operative di E8 (controllo contro
    # e8_risultati.json), poi il congelamento
    F("E18TER", [A + "analizza_e18ter.py", "--parte", "livelli"], [R_ + "e18ter_risultati.json"]),
    F("E18TER", ["genera_congelamento_e18ter.py"], [R_ + "congelamento_e18ter.json", "CONGELAMENTO_E18TER.md"]),
]'''),
    ('''ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15", "E18"]''',
     '''ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8", "E14", "E16", "E15", "E18", "E18TER"]'''),
    ('''                from analysis.tabelle_paper1 import scrivi_tabella_politiche
                scrivi_tabella_politiche(radice / RIS, dfig / "table_policies.tex")   # tabella del testo, da E18''',
     '''                from analysis.tabelle_paper1 import scrivi_tabella_politiche
                scrivi_tabella_politiche(radice / RIS, dfig / "table_policies.tex")   # tabella del testo, da E18
            if "E18TER" in a.solo:                  # supplementare G7 (E18-ter, livelli assoluti alle soglie operative)
                from analysis.tabelle_suppl import scrivi_E18ter
                print("[paper] tabella G7 del supplementare (E18-ter)", flush=True)
                scrivi_E18ter(radice / RIS, dfig / "tableG_e18ter.tex")'''),
], SUPP: [
    ('''GRUPPI_E18 = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")''',
     '''GRUPPI_E18 = ("Madrid", "Londra", "Melbourne", "PEMS08", "PEMS04")
BR_TER_EN = {"C": "$C$", "A": "$A$", "F0": "$F_0$", "F0p": "$F_0'$", "Fp_672": r"$F'(1\\,\\mathrm{wk})$",
             "Rorig_672": r"$R$-orig$(1\\,\\mathrm{wk})$", "gated": r"gated$(\\tau,N)$"}
REG_TER_EN = {"prim": "F1-optimal", "par": "validation-FPR-matched"}


def scrivi_E18ter(ris: Path, f: Path) -> None:
    """Supplementare G7 (E18-ter): livelli assoluti — richiamo, tasso di falsi allarmi, precisione della classe
    congestionata — alle soglie F1-ottima e appaiata sui falsi allarmi di C in validazione, per braccio e contesto,
    media sulle celle con intervallo al 95 %, da congelamento_e18ter.json (file figures/tableG_e18ter.tex)."""
    R = json.loads((ris / "congelamento_e18ter.json").read_text())["risultati"]["livelli"]
    imp = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:16]
    rep = Path(__file__).resolve().parents[1]
    md, js = rep / "CONGELAMENTO_E18TER.md", rep / "results" / "evoluzione" / "congelamento_e18ter.json"
    fonte = " Source: record \\\\texttt{CONGELAMENTO\\\\_E18TER.md}, fingerprint \\\\texttt{" + imp(md) + "}; " \\
        "\\\\texttt{congelamento\\\\_e18ter.json}, fingerprint \\\\texttt{" + imp(js) + "}."
    righe, prima = [], True
    for g in GRUPPI_E18:
        G = R["gruppi"].get(g)
        if G is None:
            continue
        if not prima:
            righe.append("\\\\addlinespace")
        primo = True
        for fin in ("intero", "sett"):
            for r in ("prim", "par"):
                for b in R["bracci"][fin]:
                    v = G["livelli"].get(f"{fin}/{r}/{b}")
                    if v is None:
                        continue
                    mc = v["media_celle"]
                    righe.append((CTX_EN[g] if primo else "") + f" & {BR_TER_EN[b]} & {FIN_EN[fin]} & {REG_TER_EN[r]} & "
                                 + _ic_lista(mc["richiamo"]["media"], mc["richiamo"]["ic_con_nodi"], 3).replace("$+", "$") + " & "
                                 + _ic_lista(mc["falsi_allarmi"]["media"], mc["falsi_allarmi"]["ic_con_nodi"], 4).replace("$+", "$").replace("[+", "[").replace(",+", ",") + " & "
                                 + _ic_lista(mc["precisione"]["media"], mc["precisione"]["ic_con_nodi"], 3).replace("$+", "$").replace("[+", "[").replace(",+", ",") + " \\\\\\\\")
                    primo = False
        prima = False
    righe = [x.replace("[+", "[").replace(",+", ",") for x in righe]
    out = [_longtable(
        "@{}l l l l c c c@{}",
        "E18-ter: absolute operating-point values of the congested class per arm and context: recall, false-alarm rate "
        "and precision at the F1-optimal threshold and at the validation-FPR-matched threshold (both chosen on validation "
        "as in the operational-metrics experiment; gated$(\\\\tau,N)$ composes $F_0'$ and $F'$ with their own thresholds). "
        "Window: all origins after $t_1$ for $C$, $A$, $F_0$, $F_0'$, gated$(\\\\tau,N)$; origins older than one week for "
        "$F'(1\\\\,\\\\mathrm{wk})$, $R$-orig$(1\\\\,\\\\mathrm{wk})$ and the $C$ they are compared with. Mean over cells and 95\\\\% "
        "interval from 4{,}000 joint resamples (partitions, seeds, sensor positions); the pooled values (confusion matrices "
        "summed over cells, identical to the frozen levels of the operational-metrics experiment on the full window) are in "
        "the record. The differences between arms are those frozen earlier; this table gives their levels." + fonte,
        "Context & Arm & Window & Threshold & Recall & FAR & Precision", righe, "tab:suppG7")
        .replace("{\\\\footnotesize\\\\setlength{\\\\tabcolsep}{3pt}", "{\\\\scriptsize\\\\setlength{\\\\tabcolsep}{2pt}", 1)]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\\n".join(out) + "\\n")'''),
]}


def main() -> int:
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\n{v[:150]}"); return 1
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
