#!/usr/bin/env python3
"""
Prima di E5, a costo zero: F'(1 settimana) − A sulle origini comuni.
=====================================================================
Richiesto dal revisore il 4/10: se l'intervallo include lo zero, «una settimana
chiude il divario» col veterano. Il numero va in `protocol/E5.md` come gia'
calcolato.

Nessun modello si riesegue. F'(1 settimana), F'(24 h), F0' e C vengono dagli
aggregati per (fascia d'eta', nodo, orizzonte) salvati da `esegui_e4.py`
(terza fascia: origini > t0 + 672). A viene dalle predizioni per cella
ricostruite in E3 (`predizioni_fase3/A_*.npz`), aggregate QUI sulle stesse
origini con la stessa formula (`esegui_e4._aggregati`).

**Verifica interna, non assunta**: C aggregato qui dalle predizioni di
`predizioni_fase3` deve coincidere con l'aggregato di C salvato da E4
(stesse origini, stessa formula) entro 1e-9 relativo; altrimenti ci si ferma.

Ricampionamento congiunto (partizioni × semi × nodi), 4000 repliche, seme
proprio. Scrive `results/evoluzione/e5_settimana_vs_A.json`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/settimana_vs_A_e5.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    CITTA, FASCE_ETA, _aggregati, _boot, _carica_celle, _wce)

B_BOOT, SEME = 4000, 20261005
TOLLERANZA = 1e-9


def aggregato_fase3(f: Path, pesi, t0: int):
    """A, B (K,H) di un braccio di E3 sulle origini > t0 + 672."""
    with np.load(f, allow_pickle=True) as z:
        per = z["origini"].astype("int64")
        m = per - t0 > FASCE_ETA[1]
        A, Bm = _aggregati(z["prob"], z["y"], z["m"], pesi, [m])
        return A[0], Bm[0], int(m.sum()), z["nodi"].astype("int64")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    from evoluzione.analisi.pesi import carica as carica_pesi
    print("=" * 84)
    print("F'(1 settimana) − A sulle origini comuni (eta' > 1 settimana) — prima di E5")
    print("=" * 84)
    celle = _carica_celle(a.out, "prova")
    rng = np.random.default_rng(SEME)
    R = {"confronti": {}, "verifica_C": {}, "origini_comuni": {}, "celle": {}}
    for c in CITTA:
        kk = sorted(k for k in celle if k[0] == c)
        if len(kk) != 36:
            raise RuntimeError(f"{c}: {len(kk)} celle, attese 36")
        cc = {}
        sc_max = 0.0
        for k in kk:
            _, p, s = k
            z = celle[k]
            pesi = np.asarray(carica_pesi(a.out / "pesi_griglia", c, p).vettore(), dtype="float64")
            t0 = int(z["t0"])
            fA = a.out / "predizioni_fase3" / f"A_{c}_p{p}_s{s}.npz"
            fC = a.out / "predizioni_fase3" / f"C_{c}_p{p}_s{s}.npz"
            for f in (fA, fC):
                if not f.exists():
                    raise RuntimeError(f"manca {f}")
            A_A, B_A, nA, nodiA = aggregato_fase3(fA, pesi, t0)
            A_C, B_C, nC, nodiC = aggregato_fase3(fC, pesi, t0)
            if not (np.array_equal(nodiA, z["nodi"].astype("int64"))
                    and np.array_equal(nodiC, z["nodi"].astype("int64"))):
                raise RuntimeError(f"{c} p{p} s{s}: nodi diversi fra E3 ed E4")
            if nA != int(z["fasce"][2]) or nC != int(z["fasce"][2]):
                raise RuntimeError(f"{c} p{p} s{s}: origini comuni {nA}/{nC} contro {int(z['fasce'][2])}")
            # verifica: C aggregato qui = C aggregato da E4 (terza fascia)
            w_qui = _wce(A_C, B_C); w_e4 = _wce(z["A_C"][2], z["B_C"][2])
            rel = abs(w_qui - w_e4) / abs(w_e4)
            sc_max = max(sc_max, rel)
            if rel > TOLLERANZA:
                raise RuntimeError(f"{c} p{p} s{s}: C ricalcolato {w_qui:.9f} contro E4 {w_e4:.9f}")
            # la cella per il ricampionamento: tutto sulla terza fascia, forma (1,K,H)
            cc[k] = {"celle_valide": z["celle_valide"],
                     "A_A": A_A[None], "B_A": B_A[None],
                     "A_C": z["A_C"][2][None], "B_C": z["B_C"][2][None],
                     "A_Fp_672": z["A_Fp_672"][2][None], "B_Fp_672": z["B_Fp_672"][2][None],
                     "A_Fp_96": z["A_Fp_96"][2][None], "B_Fp_96": z["B_Fp_96"][2][None],
                     "A_F0p": z["A_F0p"][2][None], "B_F0p": z["B_F0p"][2][None]}
        R["verifica_C"][c] = sc_max
        R["origini_comuni"][c] = int(celle[kk[0]]["fasce"][2])
        R["celle"][c] = len(kk)

        def diff(n1, n2):
            def f(z, idx):
                def AB(n):
                    A, Bm = z[f"A_{n}"].sum(0), z[f"B_{n}"].sum(0)
                    return (A, Bm) if idx is None else (A[idx], Bm[idx])
                return _wce(*AB(n1)) - _wce(*AB(n2))
            return f

        print(f"\n{c}: {len(kk)} celle, {R['origini_comuni'][c]} origini comuni, "
              f"verifica C scarto max {sc_max:.1e}")
        for n1, n2 in (("Fp_672", "A"), ("A", "C"), ("Fp_672", "C"), ("Fp_96", "A"), ("F0p", "A")):
            r = _boot(cc, diff(n1, n2), rng)
            R["confronti"][f"{c}/{n1}-{n2}"] = r
            print(f"  {n1:7s} - {n2:3s} {r['media']:+.5f} [{r['ic_con_nodi'][0]:+.5f}, "
                  f"{r['ic_con_nodi'][1]:+.5f}]" + ("   include lo zero" if r["include_zero"] else ""))
    chiude = [c for c in CITTA if R["confronti"][f"{c}/Fp_672-A"]["include_zero"]]
    R["una_settimana_chiude_il_divario"] = {"citta": chiude, "n": len(chiude)}
    R["repliche"] = B_BOOT; R["seme_bootstrap"] = SEME; R["tolleranza_verifica_C"] = TOLLERANZA
    R["istante"] = datetime.now(timezone.utc).isoformat()
    f = a.out / "e5_settimana_vs_A.json"
    f.write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print("\n" + "=" * 84)
    print(f"F'(1 settimana) − A include lo zero in {len(chiude)} citta' su 3"
          + (f" ({', '.join(chiude)})" if chiude else ""))
    print(f"  salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
