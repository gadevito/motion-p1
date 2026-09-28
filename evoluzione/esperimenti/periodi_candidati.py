#!/usr/bin/env python3
"""
Periodi candidati per la conferma temporale. **Sola ricognizione.**
===================================================================
Un periodo e' utilizzabile per la conferma solo se **non** e' stato usato per
addestrare i punti di controllo, selezionare punti o iperparametri, valutare, o
formulare l'ipotesi di P-refresh.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/periodi_candidati.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.esperimenti.addestramento import _carica  # noqa: E402

CAL = {"Madrid": (8887, 8983), "Londra": (8966, 9062), "Melbourne": (8806, 8902)}
GIORNI_RICHIESTI = 21


def main() -> int:
    fuori = {}
    print("=" * 96)
    print("PERIODI CANDIDATI PER LA CONFERMA TEMPORALE")
    print("=" * 96)
    for c in CAL:
        D = _carica(c, Path("results/evoluzione/maschere"))
        ts = D["ts"]; T = len(ts); e = T - 8
        ok = GR.passi_regolari(ts)
        t0, t1 = CAL[c]
        b = {"addestramento": (11, int(e * .70)),
             "validazione": (int(e * .70), int(e * .85)),
             "prova": (int(e * .85), e)}
        print(f"\n{c}  —  {T} righe, da {ts[0]} a {ts[-1]}")
        print(f"  {'periodo':16s} {'righe':>14} {'dal':>20} {'al':>20}  utilizzi")
        usi = {"addestramento": "addestramento dei punti di controllo, pesi, "
                                "normalizzazione",
               "validazione": "selezione dei punti di controllo e della "
                              "configurazione di F",
               "prova": "valutazione della fase 3, diagnostica della "
                        "persistenza, formulazione di P-refresh"}
        for n, (a_, b_) in b.items():
            print(f"  {n:16s} {a_:6d}-{b_:6d} {str(ts[a_])[:19]:>20} "
                  f"{str(ts[b_ - 1])[:19]:>20}  {usi[n]}")
        # che cosa resta DOPO il periodo di prova
        dopo = T - e
        giorni_dopo = ((ts[-1] - ts[e]).total_seconds() / 86400
                       if e < T else 0.0)
        print(f"\n  dopo la prova: {dopo} righe ({giorni_dopo:.1f} giorni di "
              f"calendario)")
        amm = False
        if dopo > 0:
            t0n = GR.primo_t0(ts, ok, e, T, giornata_dopo=True)
            if t0n is not None:
                t1n = t0n + GR.L_DESCRITTORE
                resta = (ts[T - 1] - ts[t1n]).total_seconds() / 86400
                amm = resta >= GIORNI_RICHIESTI
                print(f"  primo t0 ammissibile: {t0n} ({ts[t0n]}), "
                      f"osservazione successiva {resta:.1f} giorni "
                      f"(richiesti {GIORNI_RICHIESTI})")
            else:
                print(f"  nessun t0 con 24 ore complete e giornata successiva")
        print(f"  **episodio di conferma ammissibile: "
              f"{'SI' if amm else 'NO'}**")
        fuori[c] = {"righe": T, "inizio": str(ts[0]), "fine": str(ts[-1]),
                    "confini": {k: [int(x), int(y)] for k, (x, y) in b.items()},
                    "righe_dopo_la_prova": int(dopo),
                    "giorni_dopo_la_prova": float(giorni_dopo),
                    "episodio_ammissibile": bool(amm),
                    "t0_vecchio": t0, "t1_vecchio": t1}
    Path("results/evoluzione/periodi_candidati.json").write_text(
        json.dumps(fuori, indent=2))
    print(f"\n{'=' * 96}")
    n = sum(v["episodio_ammissibile"] for v in fuori.values())
    print(f"  citta' con un episodio di conferma ammissibile: {n}/3")
    print(f"\n  salvato in results/evoluzione/periodi_candidati.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
