#!/usr/bin/env python3
"""
Preparazione di E5 — calendario degli episodi e potenza, derivati dai dati.
===========================================================================
Produce i numeri che `protocol/E5.md` deve contenere PRIMA di qualunque run:

  --calendario  i tre t0 per citta' con data e ora, dalla REGOLA MECCANICA del
                protocollo (§9): la lunghezza del periodo di valutazione e'
                quella dell'episodio attuale, in origini ammissibili; i periodi
                sono consecutivi e non sovrapposti, il piu' recente e' quello
                attuale; ogni t0 e' l'istante che precede il proprio periodo,
                con la stessa regola d'ammissibilita' dell'acquisizione
                (96 intervalli contigui su griglia reale). Per ogni episodio:
                origini di addestramento (tutto cio' che precede t0, con le
                quote 70/15 del principale) e perdita rispetto all'attuale
                (soglia 40 %: oltre, si scende a due episodi).
  --potenza     semiampiezza attesa dell'intervallo con 6 semi, dalle celle di
                E4 (ricampionamento congiunto su partizioni x 6 semi x nodi),
                per F'(24 h) - C, F'(1 settimana) - C e gated - F0';
                soglia 0,010: oltre, 8 semi.

Nessun modello si esegue. Scrive results/evoluzione/preparazione_e5.json.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/preparazione_e5.py --calendario --potenza
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

CITTA = ("Madrid", "Londra", "Melbourne")
L24 = 96
QUOTE = (0.70, 0.85)                     # addestramento / selezione del principale
SOGLIA_PERDITA = 0.40
SEMI_6 = (201, 202, 203, 204, 205, 206)  # i primi sei semi dichiarati
SOGLIA_SEMIAMPIEZZA = 0.010
N_EPISODI = 3


def _t0_valido(ts, ok, t0):
    """Acquisizione (t0, t0+96] su griglia reale: la regola di `primo_t0`."""
    from evoluzione.componente import griglia as GR
    import pandas as pd
    t1 = t0 + L24
    return (t0 >= GR.FINESTRA and GR.contigue(ok, t0, t1)
            and pd.DatetimeIndex(ts)[t1] - pd.DatetimeIndex(ts)[t0] == L24 * GR.PASSO)


def calendario(out: Path) -> dict:
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _carica
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    fuori = {}
    for c in CITTA:
        D = _carica(c, out / "maschere")
        ts = D["ts"]
        ok = GR.passi_regolari(ts)
        T = D["r"].shape[0]
        fine = T - GR.MAX_ORIZZ
        amm = GR.maschera_origini(ok)
        # episodio 1 = la campagna principale, esattamente
        t0_1 = GR.primo_t0(ts, ok, int(fine * QUOTE[1]), fine, False)
        if (t0_1, t0_1 + L24) != tuple(CALENDARIO[c]):
            raise RuntimeError(f"{c}: calendario ricalcolato {t0_1} diverso da {CALENDARIO[c]}")
        N = len(GR.origini_dopo(ok, t0_1 + L24, fine))
        # origini di addestramento del principale: periodo [FINESTRA-1, 0.70 e)
        e = fine
        tr_1 = int(amm[GR.FINESTRA - 1:int(e * QUOTE[0])].sum())
        ep = [{"episodio": 1, "t0": int(t0_1), "t1": int(t0_1 + L24),
               "fine_valutazione": int(fine), "origini_valutazione": N,
               "addestramento": [GR.FINESTRA - 1, int(e * QUOTE[0])],
               "selezione": [int(e * QUOTE[0]), int(e * QUOTE[1])],
               "origini_addestramento": tr_1, "perdita_addestramento": 0.0,
               "data_t0": str(ts[t0_1]), "nota": "campagna principale, punti esistenti"}]
        fine_k = int(t0_1)                  # i bersagli dell'episodio 2 maturano prima di t0_1
        for k in (2, 3):
            # il piu' recente t1 tale che le origini ammissibili in (t1, fine_k)
            # siano ESATTAMENTE N e (t1-96, t1] sia un'acquisizione valida
            t1 = fine_k - GR.MAX_ORIZZ - 1
            scelto = None
            while t1 - L24 >= GR.FINESTRA:
                n = len(GR.origini_dopo(ok, t1, fine_k))
                if n > N:
                    break
                if n == N and _t0_valido(ts, ok, t1 - L24):
                    scelto = t1
                    break
                t1 -= 1
            if scelto is None:
                # nessun t1 con esattamente N: si prende il piu' recente con n >= N
                t1 = fine_k - GR.MAX_ORIZZ - 1
                while t1 - L24 >= GR.FINESTRA:
                    if len(GR.origini_dopo(ok, t1, fine_k)) >= N and _t0_valido(ts, ok, t1 - L24):
                        scelto = t1
                        break
                    t1 -= 1
            if scelto is None:
                ep.append({"episodio": k, "fattibile": False})
                break
            t0_k = scelto - L24
            e_k = t0_k                       # tutto cio' che precede t0, quote 70/15 su [0, t0)
            a_tr = int(e_k * QUOTE[0] / QUOTE[1])
            tr_k = int(amm[GR.FINESTRA - 1:a_tr].sum())
            ep.append({"episodio": k, "t0": int(t0_k), "t1": int(scelto),
                       "fine_valutazione": int(fine_k),
                       "origini_valutazione": len(GR.origini_dopo(ok, scelto, fine_k)),
                       "addestramento": [GR.FINESTRA - 1, a_tr], "selezione": [a_tr, int(t0_k)],
                       "origini_addestramento": tr_k,
                       "perdita_addestramento": 1 - tr_k / tr_1 if tr_1 else float("nan"),
                       "data_t0": str(ts[t0_k]), "fattibile": True})
            fine_k = int(t0_k)
        n_ep = sum(1 for z in ep if z.get("fattibile", True)
                   and z.get("perdita_addestramento", 0) <= SOGLIA_PERDITA)
        fuori[c] = {"righe": int(T), "fine": int(fine), "episodi": ep,
                    "episodi_ammessi": n_ep}
        print(f"\n{c}: {T} righe; valutazione del principale {N} origini ammissibili; "
              f"addestramento del principale {tr_1} origini")
        for z in ep:
            if not z.get("fattibile", True):
                print(f"  episodio {z['episodio']}: NON fattibile (serie troppo corta)"); continue
            print(f"  episodio {z['episodio']}: t0 = {z['t0']} ({z['data_t0']}), valutazione "
                  f"{z['origini_valutazione']} origini fino a {z['fine_valutazione']}; "
                  f"addestramento {z['origini_addestramento']} origini "
                  f"(perdita {z['perdita_addestramento']:.1%})"
                  + ("  **OLTRE IL 40 %**" if z["perdita_addestramento"] > SOGLIA_PERDITA else ""))
        print(f"  episodi ammessi dalla regola: {n_ep}")
    return fuori


def potenza(out: Path) -> dict:
    import evoluzione.esperimenti.esegui_e4 as E4
    celle = E4._carica_celle(out, "prova")
    SC = json.loads((out / "e4_scelta_gated.json").read_text())["scelta"]
    rng = np.random.default_rng(20261006)
    fuori = {}

    def diff(n1, n2, tau=None, N=None):
        def f(z, idx):
            def AB(n):
                if n == "gated":
                    A, Bm = E4._politica(z, tau, N)
                else:
                    A, Bm = z[f"A_{n}"].sum(0), z[f"B_{n}"].sum(0)
                return (A, Bm) if idx is None else (A[idx], Bm[idx])
            return E4._wce(*AB(n1)) - E4._wce(*AB(n2))
        return f

    print("\nPotenza: semiampiezza dell'intervallo con 6 semi (201-206) contro 12")
    for c in CITTA:
        tau, N = SC[c]["tau"], SC[c]["N"]
        tutte = {k: z for k, z in celle.items() if k[0] == c}
        sei = {k: z for k, z in tutte.items() if k[2] in SEMI_6}
        if len(sei) != 18:
            raise RuntimeError(f"{c}: {len(sei)} celle con i semi 201-206, attese 18")
        fuori[c] = {}
        for n1, n2 in (("Fp_96", "C"), ("Fp_672", "C"), ("gated", "F0p")):
            r6 = E4._boot(sei, diff(n1, n2, tau, N), rng)
            r12 = E4._boot(tutte, diff(n1, n2, tau, N), rng)
            s6 = (r6["ic_con_nodi"][1] - r6["ic_con_nodi"][0]) / 2
            s12 = (r12["ic_con_nodi"][1] - r12["ic_con_nodi"][0]) / 2
            fuori[c][f"{n1}-{n2}"] = {"semiampiezza_6": s6, "semiampiezza_12": s12,
                                     "media_6": r6["media"], "media_12": r12["media"],
                                     "oltre_soglia": s6 > SOGLIA_SEMIAMPIEZZA}
            print(f"  {c:11s} {n1:7s}-{n2:4s} 6 semi ±{s6:.4f} (media {r6['media']:+.4f}); "
                  f"12 semi ±{s12:.4f} (media {r12['media']:+.4f})"
                  + ("  **> 0,010**" if s6 > SOGLIA_SEMIAMPIEZZA else ""))
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--calendario", action="store_true")
    ap.add_argument("--potenza", action="store_true")
    a = ap.parse_args()
    print("=" * 84); print("PREPARAZIONE DI E5 — numeri per la pre-registrazione"); print("=" * 84)
    f = a.out / "preparazione_e5.json"
    R = json.loads(f.read_text()) if f.exists() else {}
    if a.calendario:
        R["calendario"] = calendario(a.out)
        R["regola_calendario"] = ("periodi di valutazione consecutivi, non sovrapposti, di "
                                  "lunghezza uguale in origini ammissibili; t0 = t1 - 96 con "
                                  "acquisizione su griglia reale; addestramento su tutto cio' "
                                  "che precede t0 con quote 70/15; soglia di perdita 40 %")
    if a.potenza:
        R["potenza"] = potenza(a.out)
        R["regola_potenza"] = ("semiampiezza con i semi 201-206 dalle celle di E4, "
                               "ricampionamento congiunto; oltre 0,010 si passa a 8 semi")
    R["istante"] = datetime.now(timezone.utc).isoformat()
    f.write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"\n  salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
