#!/usr/bin/env python3
"""
Costo effettivo della campagna, misurato invece che stimato.
=============================================================
Nessuna esecuzione: legge le date di modifica dei file di risultato.

PERCHE' LA STIMA A OCCHIO SBAGLIA. Il conteggio delle invocazioni si ottiene
contando i file, ed e' esatto. Il tempo no: sommare le differenze fra date di
modifica consecutive include le pause fra sessioni, che su otto settimane di
calendario possono valere piu' del calcolo stesso. Lo script separa quindi il
TEMPO DI CALCOLO dal TEMPO DI CALENDARIO, troncando gli intervalli che superano
una soglia: un'invocazione che risulti durata sei ore non e' durata sei ore, e'
l'ultima prima di una pausa.

CHE COSA MISURA.

  * invocazioni per campagna, contando i file di risultato;
  * durata mediana per invocazione, dalle differenze fra file consecutivi della
    medesima campagna, escluse quelle oltre la soglia;
  * tempo di calcolo, come prodotto fra le due, che e' piu' robusto della somma
    diretta perche' non eredita le code;
  * arco di calendario, dalla prima all'ultima modifica.

Le campagne rifatte contano DUE volte nel tempo speso e una sola nel risultato:
lo script riporta entrambi i conteggi, poiche' il costo sostenuto e quello
necessario a riprodurre l'esito non coincidono.

Uso (dalla radice OR3/):

    poetry run python costo_campagna.py
    poetry run python costo_campagna.py --soglia 45 --dettaglio
"""
import argparse
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

# le campagne superate o rifatte: contano nel costo sostenuto, non nell'esito
RIFATTE = ("camp_sparse", "densefix", "sparse_", "classify_t4c", "prec_",
           "sota_", "rnn_", "lgb_")


def campagna(nome):
    """Prefisso di campagna, con seme e contesto rimossi."""
    b = re.sub(r"_s\d+(\.\w+)?$", "", nome)
    b = re.sub(r"\.(csv|npz|txt|log)$", "", b)
    b = re.sub(r"_(t4c\w+|d\d+_\d{4}|d8_p85tr)(_\w+)?$", "", b)
    return b or nome


def main() -> int:
    ap = argparse.ArgumentParser(description="costo effettivo della campagna")
    ap.add_argument("--radice", default="replication")
    ap.add_argument("--soglia", type=float, default=60.0,
                    help="minuti oltre i quali l'intervallo e' una pausa, non "
                         "una durata")
    ap.add_argument("--dettaglio", action="store_true")
    a = ap.parse_args()

    F = defaultdict(list)
    for p in Path(a.radice).rglob("*"):
        if p.is_file() and p.suffix in (".csv", ".npz"):
            F[campagna(p.name)].append((p.stat().st_mtime, p))
    if not F:
        print(f"nessun file sotto {a.radice}")
        return 1

    righe, tot_inv, tot_ore, tot_rif = [], 0, 0.0, 0
    for c, v in F.items():
        v.sort()
        t = np.array([x[0] for x in v])
        if len(t) < 2:
            continue
        d = np.diff(t) / 60.0
        interne = d[d <= a.soglia]
        med = float(np.median(interne)) if len(interne) else float("nan")
        ore = med * len(v) / 60.0 if np.isfinite(med) else float("nan")
        arco = (t[-1] - t[0]) / 86400.0
        rif = any(c.startswith(x) for x in RIFATTE)
        righe.append((c, len(v), med, ore, arco, len(interne), rif))
        tot_inv += len(v)
        if np.isfinite(ore):
            tot_ore += ore
        if rif:
            tot_rif += len(v)

    righe.sort(key=lambda r: -(r[3] if np.isfinite(r[3]) else 0))
    print(f"{'campagna':26s} {'file':>6} {'mediana':>9} {'ore':>8} "
          f"{'giorni':>7} {'usati':>6}  rifatta")
    for c, n, med, ore, arco, k, rif in righe:
        if not a.dettaglio and (not np.isfinite(ore) or ore < 0.5):
            continue
        print(f"{c[:26]:26s} {n:6d} "
              + (f"{med:8.1f}m" if np.isfinite(med) else f"{'—':>9}")
              + (f"{ore:8.1f}" if np.isfinite(ore) else f"{'—':>8}")
              + f" {arco:6.1f} {k:6d}  {'sì' if rif else ''}")

    T = np.array(sorted(x[0] for v in F.values() for x in v))
    D = np.diff(T) / 60.0
    calcolo = float(D[D <= a.soglia].sum()) / 60.0
    calendario = (T[-1] - T[0]) / 86400.0
    print("\n" + "=" * 74)
    print(f"  invocazioni totali (file di risultato):        {tot_inv:6,d}")
    print(f"     di cui in campagne rifatte o superate:      {tot_rif:6,d}"
          f"  ({100*tot_rif/tot_inv:.0f}%)")
    print(f"  tempo di CALCOLO, somma degli intervalli:      {calcolo:6.0f} ore")
    print(f"  tempo di CALCOLO, mediana per campagna:        {tot_ore:6.0f} ore")
    print(f"  arco di CALENDARIO:                            {calendario:6.0f} giorni"
          f"  ({calendario/7:.1f} settimane)")
    print(f"  utilizzo: {100*calcolo/max(calendario*24,1e-9):.1f}% del tempo di calendario")
    print("=" * 74)
    print("\n  Le due stime del tempo di calcolo differiscono perche' la prima somma")
    print("  ogni intervallo sotto soglia e la seconda moltiplica la mediana per il")
    print("  numero di file: la seconda e' piu' robusta alle code, la prima include")
    print("  le invocazioni piu' lente. Riportarle entrambe come intervallo.")
    print("\n  ATTENZIONE: le date di modifica cambiano se i file sono stati copiati")
    print("  o spostati senza preservarle. Il riordino dell'archivio le ha conservate")
    print("  solo dove e' stato usato `cp -p` o `mv`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
