#!/usr/bin/env python3
"""
Calendario della parte A di E6 (PEMS04, campagna vecchia). **Sola ricognizione.**

I t0 della parte A si derivano con le regole gia' in uso sui file di PEMS04:

    t0 di prova         `primo_t0` sul periodo di prova del 70/15/15 della
                        serie intera, giornata dopo NON richiesta — la stessa
                        chiamata di `analizza_copertura_e4.pems04` e di
                        `ricostruisci_predizioni --pems04`
    t0 di validazione   `primo_t0` sul periodo di validazione con la giornata
                        dopo completa — la regola di E4 (`seleziona_F`)
    origini             `maschera_origini` (finestra 12, orizzonte massimo 8):
                        dopo t1 = t0 + 24 h e comuni (eta' > 1 settimana)

Ogni contesto PEMS04_p<k> e' una partizione: i nodi nuovi sono `nodi["prova"]`
di `_partizioni` con `SEME_PARTIZIONE[k]`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/calendario_pems04.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.esperimenti.addestramento import _carica, _partizioni  # noqa: E402
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

CONTESTI = ("PEMS04_p0", "PEMS04_p1", "PEMS04_p2")
PASSI_GIORNO = 96
SETTIMANA = 7 * PASSI_GIORNO


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    print("=" * 78); print("CALENDARIO PEMS04 — parte A di E6 (campagna vecchia, 70/15/15 della serie)"); print("=" * 78)
    righe = []
    for p, c in enumerate(CONTESTI):
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        T = D["r"].shape[0]
        fine = T - GR.MAX_ORIZZ
        a_tr, a_va = int(fine * .70), int(fine * .85)
        nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])})
        t0 = GR.primo_t0(D["ts"], ok, a_va, fine, False)
        t0v = GR.primo_t0(D["ts"], ok, a_tr, a_va, True)
        if t0 is None or t0v is None:
            print(f"  {c}: t0 non trovato (prova {t0}, validazione {t0v})"); return 1
        t1, t1v = t0 + PASSI_GIORNO, t0v + PASSI_GIORNO
        o_dopo = GR.origini_dopo(ok, t1, fine)
        o_com = [t for t in o_dopo if t > t0 + SETTIMANA]
        ov = GR.origini_dopo(ok, t1v, a_va)
        ov7 = [t for t in ov if t > t0v + SETTIMANA]
        print(f"\n  {c}: {T} righe ({T / PASSI_GIORNO:.1f} giorni), griglia regolare {'si' if ok.all() else 'NO'}; "
              f"nodi {len(nodi['addestramento'])}/{len(nodi['validazione'])}/{len(nodi['prova'])} (nuovi {len(nodi['prova'])})")
        print(f"    prova       [{a_va}, {fine}): t0 = {t0} ({D['ts'][t0]}), t1 = {t1}; "
              f"origini dopo t1 = {len(o_dopo)}, comuni (eta' > 1 sett.) = {len(o_com)}"
              f"{'' if len(o_com) >= 600 else '   <- meno di 600: limite dichiarato'}")
        print(f"    validazione [{a_tr}, {a_va}): t0 = {t0v} ({D['ts'][t0v]}), t1 = {t1v}; "
              f"origini dopo t1 = {len(ov)}, con eta' > 1 sett. = {len(ov7)}"
              f"{'' if len(ov7) >= PASSI_GIORNO else '   <- tau = 1 sett. non distinguibile da «mai»'}")
        righe.append((c, t0, t0v, len(o_dopo), len(o_com), len(nodi["prova"])))
    print("\n  da scrivere in protocol/E6.md, parte A:")
    print("    prova t0 = " + " / ".join(str(r[1]) for r in righe)
          + ", validazione t0 = " + " / ".join(str(r[2]) for r in righe))
    print("    origini dopo t1 = " + " / ".join(str(r[3]) for r in righe)
          + ", comuni = " + " / ".join(str(r[4]) for r in righe)
          + ", nodi nuovi = " + " / ".join(str(r[5]) for r in righe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
