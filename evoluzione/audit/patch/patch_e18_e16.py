#!/usr/bin/env python3
"""
E18 (A.6) — `esegui_e16.py --fase predizioni` per PEMS04, in una cartella propria.
====================================================================================
Due aggiunte, senza cambiare il comportamento predefinito di E16 (i cui ingressi restano
`predizioni_e16/` per `citta` e `pems08`): il contesto `pems04` diventa ammesso (NON predefinito) e
`--dir-pred` sceglie la cartella d'uscita della fase `predizioni` (predefinita `predizioni_e16`).
Patch letterale: si ferma se il testo atteso non compare esattamente una volta.

Dalla radice OR3/:  python3 patch_e18_e16.py
"""
import sys
from pathlib import Path

F = Path(__file__).resolve().parent / "evoluzione" / "esperimenti" / "esegui_e16.py"
SOST = [
    ('''    nome_ctx, c, p, s, ep_nome, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
''', '''    nome_ctx, c, p, s, ep_nome, out, fili, dir_pred = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
'''),
    ('''    g = out / DIR_PRED / f"{ep_nome}_{c}_p{p}_s{s}.npz"
    if g.exists():
''', '''    g = out / dir_pred / f"{ep_nome}_{c}_p{p}_s{s}.npz"
    if g.exists():
'''),
    ('''def fase_predizioni(out: Path, contesti, lavoratori, fili, piano, pilota, solo=None) -> int:
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8
    celle = []
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        unita = ctx["unita"][:1] if pilota else ctx["unita"]
        for ep in ("validazione", "prova"):
            celle += [(nome, c, p, s, ep, str(out), fili) for (c, p, s) in unita]
''', '''def fase_predizioni(out: Path, contesti, lavoratori, fili, piano, pilota, solo=None, dir_pred=DIR_PRED) -> int:
    from evoluzione.esperimenti.esegui_e8 import CONTESTI_E8
    celle = []
    for nome in contesti:
        ctx = CONTESTI_E8[nome](out)
        unita = ctx["unita"][:1] if pilota else ctx["unita"]
        for ep in ("validazione", "prova"):
            celle += [(nome, c, p, s, ep, str(out), fili, dir_pred) for (c, p, s) in unita]
'''),
    ('''        celle = [x for x in celle if (x[4], x[1], str(x[2]), str(x[3])) in chiavi]
        print(f"  --solo: {len(celle)} celle su richiesta {sorted(chiavi)}")
    fatte = sum((out / DIR_PRED / f"{ep}_{c}_p{p}_s{s}.npz").exists() for _, c, p, s, ep, _, _ in celle)
''', '''        celle = [x for x in celle if (x[4], x[1], str(x[2]), str(x[3])) in chiavi]
        print(f"  --solo: {len(celle)} celle su richiesta {sorted(chiavi)}")
    fatte = sum((out / dir_pred / f"{ep}_{c}_p{p}_s{s}.npz").exists() for _, c, p, s, ep, _, _, _ in celle)
'''),
    ('''    ap.add_argument("--contesto", nargs="*", choices=CONTESTI, default=list(CONTESTI))
''', '''    # E18 (A.6): `pems04` ammesso ma NON predefinito, con `--dir-pred` propria: E16 resta com'e'
    ap.add_argument("--contesto", nargs="*", choices=CONTESTI + ("pems04",), default=list(CONTESTI))
    ap.add_argument("--dir-pred", default=DIR_PRED, help="cartella d'uscita della fase predizioni (E18: predizioni_e18_pems04)")
'''),
    ('''        return fase_predizioni(a.out, a.contesto, a.lavoratori, a.fili, a.piano, a.pilota, a.solo)
''', '''        return fase_predizioni(a.out, a.contesto, a.lavoratori, a.fili, a.piano, a.pilota, a.solo, a.dir_pred)
'''),
]


def main() -> int:
    src = F.read_text()
    for a, _ in SOST:
        if src.count(a) != 1:
            print(f"FERMO: testo atteso presente {src.count(a)} volte in {F}:\n{a[:200]}")
            return 1
    for a, b in SOST:
        src = src.replace(a, b)
    F.write_text(src)
    print(f"  {F.name}: {len(SOST)} sostituzioni (contesto pems04 ammesso, --dir-pred)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
