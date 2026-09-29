#!/usr/bin/env python3
"""
E5: tre episodi consecutivi, t0 spostato INDIETRO. **Sola ricognizione.**
==========================================================================
Regola approvata: ogni periodo di valutazione ha **la stessa lunghezza in
ORIGINI AMMISSIBILI** di quello attuale; i tre sono consecutivi, non
sovrapposti; il piu' recente e' quello di oggi. L'episodio piu' antico si
addestra su meno dati.

**Soglia dichiarata prima del lancio: se l'addestramento perde piu' del 40%
delle origini ammissibili, si scende a due episodi.**

Ogni t0 rispetta la regola gia' approvata: ventiquattro ore complete di
acquisizione, cioe' righe t0..t0+96 contigue sulla griglia reale.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/episodi_e5.py
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.esperimenti.addestramento import _carica  # noqa: E402

CAL = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
       "Melbourne": (8806, 8902)}
SOGLIA = 0.40
L = GR.L_DESCRITTORE


def main() -> int:
    fuori = {}
    print("=" * 92)
    print("E5 — tre episodi consecutivi, valutazioni di pari lunghezza")
    print("=" * 92)
    for c, (t0_a, t1_a) in CAL.items():
        D = _carica(c, Path("results/evoluzione/maschere"))
        ts, ok = D["ts"], GR.passi_regolari(D["ts"])
        amm = GR.maschera_origini(ok)
        T = len(ts); fine = T - GR.MAX_ORIZZ

        def n_amm(a, b):
            """origini ammissibili in [a, b)"""
            if b <= a:
                return 0
            z = np.arange(max(a, GR.FINESTRA - 1), min(b, fine))
            return int(amm[z].sum()) if len(z) else 0

        # l'episodio ATTUALE: la valutazione dopo t1, fino alla fine
        n_ev = n_amm(t1_a + 1, fine)
        tr_att = n_amm(GR.FINESTRA - 1, int(fine * .70))
        print(f"\n{c}")
        print(f"  episodio attuale: t0={t0_a}, t1={t1_a}, "
              f"{n_ev} origini di valutazione")
        print(f"  addestramento attuale: {tr_att} origini ammissibili")

        ep = [{"episodio": 1, "t0": t0_a, "t1": t1_a, "fine_val": fine,
               "origini_valutazione": n_ev}]
        confine = t0_a          # la valutazione precedente finisce qui
        ok_tutti = True
        for k in (2, 3):
            # si cerca t1 tale che le origini ammissibili in (t1, confine)
            # siano n_ev, poi t0 = t1 - 96 con acquisizione contigua
            t1_k = None
            for t1_c in range(confine - 1, GR.FINESTRA, -1):
                if n_amm(t1_c + 1, confine) >= n_ev:
                    t1_k = t1_c
                    break
            if t1_k is None:
                print(f"  episodio {k}: **non collocabile**")
                ok_tutti = False
                break
            t0_k = t1_k - L
            if not GR.contigue(ok, t0_k, t1_k):
                # si arretra fino alla prima acquisizione completa
                trovato = None
                for z in range(t0_k, GR.FINESTRA, -1):
                    if z + L <= t1_k and GR.contigue(ok, z, z + L):
                        trovato = z
                        break
                if trovato is None:
                    print(f"  episodio {k}: **nessuna acquisizione completa**")
                    ok_tutti = False
                    break
                t0_k, t1_k = trovato, trovato + L
            ep.append({"episodio": k, "t0": int(t0_k), "t1": int(t1_k),
                       "fine_val": int(confine),
                       "origini_valutazione": n_amm(t1_k + 1, confine)})
            print(f"  episodio {k}: t0={t0_k} ({str(ts[t0_k])[:16]}), "
                  f"t1={t1_k}, valutazione fino a {confine}: "
                  f"{n_amm(t1_k + 1, confine)} origini")
            confine = t0_k
        if ok_tutti and len(ep) == 3:
            # l'addestramento dell'episodio piu' antico: tutto cio' che
            # precede il suo t0, con la stessa proporzione 70/15
            t0_min = ep[-1]["t0"]
            tr_min = n_amm(GR.FINESTRA - 1, int(t0_min * .70 / .85))
            perdita = 1 - tr_min / tr_att
            print(f"\n  episodio piu' antico: addestramento {tr_min} origini "
                  f"contro {tr_att}")
            print(f"  **perdita {perdita:.1%}**  "
                  f"{'entro' if perdita <= SOGLIA else 'OLTRE'} la soglia del "
                  f"{SOGLIA:.0%}"
                  f"  ->  {'TRE episodi' if perdita <= SOGLIA else 'DUE episodi'}")
            fuori[c] = {"episodi": ep, "addestramento_attuale": tr_att,
                        "addestramento_piu_antico": tr_min,
                        "perdita": perdita,
                        "decisione": "tre" if perdita <= SOGLIA else "due"}
        else:
            fuori[c] = {"episodi": ep, "decisione": "due o meno"}
    Path("results/evoluzione/episodi_e5.json").write_text(
        json.dumps(fuori, indent=2, default=str))
    print(f"\n{'=' * 92}")
    print("  salvato in results/evoluzione/episodi_e5.json")
    print("  **la decisione va presa ora, prima di scrivere protocol/E5.md**")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
