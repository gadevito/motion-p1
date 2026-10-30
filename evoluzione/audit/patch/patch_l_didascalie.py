#!/usr/bin/env python3
"""
Didascalie allineate (richiesta del revisore, 30/10, 18:30): «over cells» → «over runs» in C1, C3, C9, D, F15–F17, G7;
F15 «fitted per arm and cell» → «per arm and run» con l'obiettivo di adattamento; «cell» resta solo nell'unita' del
ricampionamento (G18–G21, gia' allineate). Solo testo. Ogni frase deve comparire almeno una volta; sostituzione di
tutte le occorrenze; alla fine nessun «cells» residuo fuori dall'unita' del ricampionamento.
Dalla radice OR3/:  python3 patch_l_didascalie.py
"""
import re
import sys
from pathlib import Path

R = Path(__file__).resolve().parent
SUPP = R / "analysis" / "tabelle_suppl.py"
P1 = R / "analysis" / "tabelle_paper1.py"

FRASI = {SUPP: [
    ("mean over cells", "mean over runs"),                                                              # C3, C9, F15, G7, E12
    ("Mean over cells", "Mean over runs"),                                                              # D, G7
    ("means over cells", "means over runs"),                                                            # F17 (×2)
    ("fitted per arm and cell on the validation episode ",
     "fitted per arm and run on the validation episode, objective pooled over origins, sensors and horizons, "),  # F15
    ("same cells and resamples (frozen)", "same runs and resamples (frozen)"),                          # E9
    ("Frozen, same cells", "Frozen, same runs"),                                                        # E9
    ("on the same cells, is in the E15 record", "on the same runs, is in the E15 record"),              # E10
    ("causal and frozen on the same cells", "causal and frozen on the same runs"),                      # E12
    ("summed over cells, identical to the frozen levels", "summed over runs, identical to the frozen levels"),  # G7
], P1: [
    ("mean $\\Delta$wCE over cells and 95\\% interval", "mean $\\Delta$wCE over runs and 95\\% interval"),  # C1
    ("on the same cells (Section~E)", "on the same runs (Section~E)"),                                   # C1
]}
RESIDUO_OK = ("the cell (seed",)   # l'unita' del ricampionamento (G18–G21)


def main() -> int:
    testi = {f: f.read_text() for f in FRASI}
    for f, coppie in FRASI.items():
        for v, _ in coppie:
            if testi[f].count(v) == 0:
                print(f"FERMO: in {f.relative_to(R)} la frase non compare:\n{v}"); return 1
    for f, coppie in FRASI.items():
        t = testi[f]
        for v, n in coppie:
            k = t.count(v); t = t.replace(v, n); print(f"  {f.name}: «{v[:50]}» ×{k}")
        testi[f] = t
    # nessun «cells» residuo nelle stringhe inglesi, salvo l'unita' del ricampionamento
    for f, t in testi.items():
        for m in re.finditer(r"[^\n]{0,60}\bcells?\b[^\n]{0,40}", t):
            riga = m.group(0)
            if any(ok in riga for ok in RESIDUO_OK) or "cella" in riga or "celle" in riga:
                continue
            print(f"FERMO: «cell» residuo in {f.relative_to(R)}: …{riga}…"); return 1
    for f, t in testi.items():
        f.write_text(t)
    import py_compile
    for f in FRASI:
        py_compile.compile(str(f), doraise=True)
    print("  compilazione: ok; nessun «cell» residuo fuori dall'unita' del ricampionamento")
    return 0


if __name__ == "__main__":
    sys.exit(main())
