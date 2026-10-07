#!/usr/bin/env python3
"""
Calendario della parte B di E6 (PEMS08). **Sola ricognizione**: nessuna
prestazione, nessun modello. Deriva i numeri che il protocollo chiede di
scrivere «dalla fattibilita', non stimati»:

    t0 di prova         = la prima riga del giorno --giorno-t0 (a 15 minuti)
                          che soddisfa la regola approvata `primo_t0`
                          (24 h complete dopo t0 e giornata successiva completa)
    periodi             = quote del principale su [0, t0): addestramento
                          70/85, selezione 15/85 (come E5 `_partizioni(fine=t0)`)
    t0 di validazione   = `primo_t0` sul periodo di selezione, stessa regola
    origini             = con `maschera_origini` della griglia (finestra 12,
                          orizzonte massimo 8): dopo t1 = t0 + 24 h, e comuni
                          (eta' > 1 settimana, cioe' dopo t0 + 672)
    nodi                = 70/15/15 del numero di sensori, come `_partizioni`

Stampa anche quante origini dell'episodio di validazione hanno eta' > 1
settimana: se sono poche, tau = 1 settimana non e' distinguibile da «mai» in
selezione, e il protocollo lo deve dichiarare.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/calendario_pems08.py \\
        --file data_collection/pems08/pems08.npz --giorno-t0 40
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402

AGG = 3            # 5 -> 15 minuti, come fattibilita_pems04
PASSI_GIORNO = 96
SETTIMANA = 7 * PASSI_GIORNO
QUOTE_NODI = (.70, .85)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--inizio", default="2016-07-01")
    ap.add_argument("--giorno-t0", type=int, default=40)
    ap.add_argument("--prova-minima-giorni", type=float, default=21.0)
    a = ap.parse_args()
    z = np.load(a.file)
    X = z["data" if "data" in z else list(z.keys())[0]]
    T5, N, C = X.shape
    Tg = (T5 // AGG)
    ts = pd.date_range(a.inizio, periods=Tg, freq="15min")
    ok = GR.passi_regolari(ts)
    e = Tg - GR.MAX_ORIZZ
    print("=" * 78)
    print(f"CALENDARIO PEMS08 — {a.file}")
    print("=" * 78)
    print(f"  {T5} righe a 5 min -> {Tg} righe a 15 min ({Tg / PASSI_GIORNO:.1f} giorni), "
          f"{N} sensori; griglia regolare: {'si' if ok.all() else 'NO'}")
    print(f"  ultima origine utile e = {e} (Tg - orizzonte massimo {GR.MAX_ORIZZ})")

    # nodi, come _partizioni
    na, nb = int(N * QUOTE_NODI[0]), int(N * QUOTE_NODI[1])
    print(f"\n  nodi 70/15/15: addestramento {na}, validazione {nb - na}, "
          f"prova (NUOVI) {N - nb}")

    # t0 di prova con la regola approvata
    inizio = a.giorno_t0 * PASSI_GIORNO
    t0 = GR.primo_t0(ts, ok, inizio, e, giornata_dopo=True)
    if t0 is None:
        print("  nessun t0 valido: fermo"); return 1
    t1 = t0 + PASSI_GIORNO
    t7 = t0 + SETTIMANA
    giorni_prova = (e - t0) / PASSI_GIORNO
    print(f"\n  t0 di prova = {t0} ({ts[t0]}, giorno {t0 // PASSI_GIORNO} di {Tg // PASSI_GIORNO}); "
          f"t1 (24 h) = {t1}; t0 + 1 sett. = {t7}")
    print(f"  periodo di prova [t0, e): {e - t0} righe = {giorni_prova:.1f} giorni "
          f"({'>=' if giorni_prova >= a.prova_minima_giorni else '< !!'} {a.prova_minima_giorni:g} richiesti)")
    o_dopo = GR.origini_dopo(ok, t1, e)
    o_com = [t for t in o_dopo if t > t7]
    print(f"  origini dopo t1 = {len(o_dopo)}; origini comuni (eta' > 1 sett.) = {len(o_com)}"
          f"{'' if len(o_com) >= 600 else '   <- meno di 600: limite da dichiarare'}")

    # periodi prima di t0, quote del principale (E5 _partizioni(fine=t0))
    a_tr = int(t0 * .70 / .85)
    amm = GR.maschera_origini(ok)
    o_tr = [t for t in range(GR.FINESTRA - 1, a_tr) if amm[t]]
    o_va = [t for t in range(a_tr, t0) if amm[t]]
    print(f"\n  addestramento [{GR.FINESTRA - 1}, {a_tr}): {len(o_tr)} origini "
          f"({a_tr / PASSI_GIORNO:.1f} giorni)")
    print(f"  selezione     [{a_tr}, {t0}): {len(o_va)} origini "
          f"({(t0 - a_tr) / PASSI_GIORNO:.1f} giorni)")

    # episodio di validazione (per F e per gated), stessa regola
    t0v = GR.primo_t0(ts, ok, a_tr, t0, giornata_dopo=True)
    if t0v is None:
        print("  nessun t0 di validazione valido: fermo"); return 1
    t1v = t0v + PASSI_GIORNO
    ov = GR.origini_dopo(ok, t1v, t0)
    ov7 = [t for t in ov if t > t0v + SETTIMANA]
    print(f"\n  t0 di validazione = {t0v} ({ts[t0v]}); t1 = {t1v}; "
          f"origini dopo t1 entro il periodo di selezione = {len(ov)}")
    print(f"  di cui con eta' > 1 settimana = {len(ov7)}"
          + ("   <- tau = 1 sett. NON distinguibile da «mai» in selezione: da dichiarare"
             if len(ov7) < PASSI_GIORNO else ""))
    print("\n  da scrivere in protocol/E6.md, parte B:")
    print(f"    prova t0 = {t0} (giorno {t0 // PASSI_GIORNO}), validazione t0 = {t0v}, "
          f"origini dopo t1 = {len(o_dopo)}, origini comuni = {len(o_com)}, nodi nuovi = {N - nb}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
