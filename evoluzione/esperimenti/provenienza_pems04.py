#!/usr/bin/env python3
"""
Provenienza di PEMS04: canali, calendario, imputazione. **Sola ispezione.**
============================================================================
Risponde a quattro domande, con numeri:

    [1] l'ordine e le unita' dei canali sono flusso, occupazione, velocita'?
    [2] la frequenza e l'origine del calendario reggono al ciclo settimanale?
    [3] il rilascio contiene gia' un'imputazione?
    [4] quale riferimento di flusso libero e' costruibile SENZA la storia
        nascosta dei nodi nuovi?

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/provenienza_pems04.py \\
        --file data_collection/pems04/pems04.npz
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--inizio", default="2016-07-01")
    a = ap.parse_args()
    z = np.load(a.file)
    X = z["data" if "data" in z else list(z.keys())[0]]
    T, N, C = X.shape
    fl, oc, ve = X[..., 0], X[..., 1], X[..., 2]
    print("=" * 78)
    print("[1] canali: coerenza con flusso, occupazione, velocita'")
    print("=" * 78)
    print(f"  {'canale':14s} {'min':>8} {'max':>8} {'mediana':>9}"
          f"   unita' plausibile")
    for n, v, u in (("0 flusso", fl, "veicoli per 5 min"),
                    ("1 occupazione", oc, "frazione 0-1"),
                    ("2 velocita'", ve, "miglia orarie")):
        print(f"  {n:14s} {v.min():8.2f} {v.max():8.2f} {np.median(v):9.2f} "
              f"{u:>22}")
    # la relazione attesa: occupazione alta -> velocita' bassa
    c1 = np.corrcoef(oc.ravel(), ve.ravel())[0, 1]
    c2 = np.corrcoef(fl.ravel(), oc.ravel())[0, 1]
    print(f"\n  correlazione occupazione-velocita': {c1:+.3f}  "
          f"(attesa NEGATIVA)")
    print(f"  correlazione flusso-occupazione:    {c2:+.3f}  "
          f"(attesa positiva)")
    print(f"  > l'ordine dichiarato in letteratura e' {'COERENTE' if c1 < 0 else 'DA VERIFICARE'}")

    print("\n" + "=" * 78)
    print("[2] frequenza e origine del calendario")
    print("=" * 78)
    ts = pd.date_range(a.inizio, periods=T, freq="5min")
    print(f"  {T} istanti = {T/288:.2f} giorni; con inizio {a.inizio} la serie")
    print(f"  va da {ts[0]} a {ts[-1]}")
    # il ciclo settimanale: il flusso nei fine settimana deve calare
    gio = pd.Series(ts.dayofweek).values
    med = [float(np.median(fl[gio == g])) for g in range(7)]
    nomi = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
    print(f"\n  flusso mediano per giorno: "
          + "  ".join(f"{n} {m:.0f}" for n, m in zip(nomi, med)))
    fer, wk = np.mean(med[:5]), np.mean(med[5:])
    print(f"  feriali {fer:.0f} contro fine settimana {wk:.0f}: "
          f"{'COERENTE' if wk < fer else 'INCOERENTE'} con l'origine assunta")
    ora = pd.Series(ts.hour).values
    per_ora = [float(np.median(fl[ora == h])) for h in range(24)]
    print(f"  ora di minimo {int(np.argmin(per_ora))}, di massimo "
          f"{int(np.argmax(per_ora))}  (atteso: minimo notturno)")

    print("\n" + "=" * 78)
    print("[3] imputazione gia' presente nel rilascio")
    print("=" * 78)
    print(f"  zeri: flusso {np.mean(fl == 0):.2%}, occupazione "
          f"{np.mean(oc == 0):.2%}, velocita' {np.mean(ve == 0):.2%}")
    # una velocita' mai nulla con flusso nullo e' il segno di un riempimento
    sosp = (fl == 0) & (ve > 0)
    print(f"  celle con flusso nullo e velocita' positiva: {np.mean(sosp):.2%}")
    # ripetizioni identiche consecutive: firma dell'imputazione a gradini
    rip = np.mean(np.isclose(ve[1:], ve[:-1]))
    print(f"  velocita' identica al passo precedente: {rip:.2%}")
    lunghe = 0
    for k in range(N):
        d = np.diff(ve[:, k]) == 0
        if d.any():
            run = np.diff(np.flatnonzero(np.r_[True, ~d, True]))
            lunghe += int((run > 12).sum())
    print(f"  tratti di velocita' costante oltre un'ora: {lunghe}")
    print(f"  > {'segni compatibili con un riempimento' if rip > .1 or lunghe > N else 'nessun segno evidente di riempimento'}")

    print("\n" + "=" * 78)
    print("[4] riferimenti di flusso libero costruibili")
    print("=" * 78)
    e = T - 8 * 3
    a_va = int(e * .70)
    v_tr = ve[11:a_va]
    p95_nodo = np.percentile(v_tr, 95, axis=0)
    p95_rete = float(np.percentile(v_tr, 95))
    print(f"  per NODO, sull'addestramento: mediana {np.median(p95_nodo):.1f}, "
          f"dispersione fra nodi {p95_nodo.std():.1f}")
    print(f"     **non utilizzabile per i nodi nuovi**: userebbe la loro "
          f"storia nascosta")
    print(f"  di RETE, un solo valore: {p95_rete:.1f}")
    print(f"     utilizzabile: non dipende dal singolo nodo nuovo")
    scarto = np.abs(p95_nodo - p95_rete)
    print(f"     scarto dal riferimento per nodo: mediana {np.median(scarto):.1f}, "
          f"massimo {scarto.max():.1f} ({scarto.max()/p95_rete:.0%})")
    print(f"\n  con un riferimento di rete, le classi diventerebbero:")
    rap = ve / p95_rete
    for s_alto, s_basso, n in ((0.8, 0.5, "soglie dichiarate"),):
        cl = np.where(rap >= s_alto, 1, np.where(rap >= s_basso, 2, 3))
        print(f"     {n}: scorrevole {np.mean(cl==1):.1%}, moderato "
              f"{np.mean(cl==2):.1%}, congestionato {np.mean(cl==3):.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
