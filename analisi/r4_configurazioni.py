#!/usr/bin/env python3
"""
R4 — confronti appaiati fra le cinque configurazioni (§8.4, Tabella 43).
========================================================================
`onboard_aggregate.py` calcola gia' la curva di recupero di UNA configurazione.
Questo script fa la cosa che manca: il confronto APPAIATO PER SEME fra le
configurazioni, che e' l'unica lettura ammessa dal disegno (§7.2.4).

Perche' appaiato. La variabilita' assoluta del recupero fra semi e' ampia — su
Melbourne la configurazione base recupera 35,9 / 19,5 / 14,4 / 25,1 / 11,1 per
cento — quindi un confronto fra medie isolate sarebbe poco informativo. Con lo
stesso seme le due configurazioni condividono partizione, maschera e
inizializzazione, e la differenza dipende dal solo elemento variato.

LE CINQUE CONFIGURAZIONI e come si ottengono da `gomo_onboard.py`:

    base   --hist-mode summary                 blocco 8 dim., nessun profilo
    B      --hist-mode profile                  blocco 10 dim., profilo presente
    C      --hist-mode both                     blocco 16 dim., profilo presente
    D      --hist-mode summary --hist-dim 10    blocco 10 dim., profilo AZZERATO
    E      --hist-mode summary --hist-dim 16    blocco 16 dim., profilo AZZERATO

D ed E sono i CONTROLLI A CAPACITA' APPAIATA, e servono a separare due
spiegazioni del guadagno di C: le otto dimensioni aggiuntive del blocco, oppure
il contenuto informativo del profilo a bande. Il confronto principale e' C - E,
che ha la stessa capacita' e differisce per il solo contenuto.

IL DISEGNO E' SBILANCIATO PER COSTRUZIONE: i controlli di capacita' esistono
solo sul contesto in cui il criterio non e' raggiunto, e la numerosita' dei semi
varia per configurazione. Non e' un difetto dei dati, e lo script riporta la
numerosita' di ogni confronto.

DUE AVVERTENZE SULLA SCALA.

La quota colmata e' un RAPPORTO e diventa instabile quando il denominatore e'
piccolo. Va sempre letta accanto al divario assoluto: una quota su un divario di
0,068 non e' commensurabile a una su 0,192, e un valore oltre il 100% e' effetto
della partizione casuale, non recupero piu' che completo.

Il controllo a capacita' appaiata NON elimina l'effetto della difficolta'
relativa delle partizioni. Su Melbourne il differenziale fra le due partizioni
vale -0,0242 su un divario di 0,079, cioe' circa il 31%, benche' l'intervallo
includa lo zero.

Uso (da models/, o dalla radice indicando --dir):

    poetry run python analisi/r4_configurazioni.py --dir models
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd

ORDINE = ["0h", "1h", "4h", "24h", "1wk"]
CONFIG = {
    "base": ("onboard_{c}_s{s}.csv",  "summary",  8, "assente"),
    "B":    ("onboardB_{c}_s{s}.csv", "profile", 10, "presente"),
    "C":    ("onboardC_{c}_s{s}.csv", "both",    16, "presente"),
    "D":    ("onboardD_{c}_s{s}.csv", "summary", 10, "azzerato"),
    "E":    ("onboardE_{c}_s{s}.csv", "summary", 16, "azzerato"),
}
CITTA = {"mad": "Madrid", "lon": "Londra", "mel": "Melbourne"}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def recupero(schema, cartella: Path, c: str, storia: str = "24h"):
    """Quota di divario colmata, per seme. None se nessun file corrisponde."""
    fuori, divari, assoluti = [], [], []
    for s in range(5):
        f = globmod.glob(str(cartella / schema.format(c=c, s=s)))
        if not f:
            continue
        d = pd.read_csv(f[0])
        try:
            v = d[d.split == "seen"].wCE.mean()
            g0 = d[(d.split == "heldout") & (d.history == "0h")].wCE.mean()
            gl = d[(d.split == "heldout") & (d.history == storia)].wCE.mean()
        except Exception:
            continue
        if not np.isfinite([v, g0, gl]).all() or abs(g0 - v) < 1e-9:
            continue
        fuori.append(100 * (g0 - gl) / (g0 - v))
        divari.append(g0 - v)
        assoluti.append(gl)
    return (fuori, divari, assoluti) if fuori else None


def main() -> int:
    ap = argparse.ArgumentParser(description="R4: confronti appaiati fra configurazioni")
    ap.add_argument("--dir", type=Path, default=Path("models"),
                    help="cartella dei CSV di gomo_onboard.py")
    ap.add_argument("--storia", default="24h", choices=ORDINE)
    ap.add_argument("--confronti", nargs="*", default=["C-E", "C-base", "E-base", "B-D"],
                    help="coppie appaiate da riportare")
    a = ap.parse_args()

    print("=" * 96)
    print(f"RECUPERO A {a.storia} PER CONFIGURAZIONE E CITTA'")
    print("=" * 96)
    print(f"{'config':7s} {'blocco':>7} {'profilo':>10} | " +
          " ".join(f"{n:>22}" for n in CITTA.values()))
    dati = {}
    for nome, (schema, modo, dim, prof) in CONFIG.items():
        celle = []
        for c in CITTA:
            r = recupero(schema, a.dir, c, a.storia)
            if r is None:
                celle.append(f"{'—':>22}")
                continue
            dati[(nome, c)] = r
            m, sd = st(r[0])
            celle.append(f"{m:8.1f}% ± {sd:5.1f}  n={len(r[0])}")
        print(f"{nome:7s} {dim:7d} {prof:>10} | " + " ".join(celle))

    print("\ndivario di identita' assoluto (denominatore della quota):")
    for c, nome in CITTA.items():
        if ("base", c) in dati:
            print(f"  {nome:10s} {np.mean(dati[('base', c)][1]):.4f}")
    print("  La quota e' un rapporto: su un divario piccolo diventa instabile agli estremi,")
    print("  e un valore oltre il 100% e' effetto della partizione casuale.")

    print("\n" + "=" * 96)
    print("CONFRONTI APPAIATI PER SEME")
    print("=" * 96)
    print(f"{'confronto':12s} {'citta':11s} {'semi':>5} | {'differenza (punti)':>24} | "
          f"{'segni':>7} | interpretazione")
    for coppia in a.confronti:
        x, y = coppia.split("-")
        for c, nome in CITTA.items():
            if (x, c) not in dati or (y, c) not in dati:
                continue
            vx, vy = dati[(x, c)][0], dati[(y, c)][0]
            n = min(len(vx), len(vy))
            if n < 2:
                continue
            diff = [vx[i] - vy[i] for i in range(n)]
            m, sd = st(diff)
            lo, hi = min(diff), max(diff)
            concordi = sum(1 for d in diff if d > 0)
            if coppia == "C-E":
                senso = "contenuto del profilo (capacita' appaiata)"
            elif coppia == "E-base":
                senso = "sola capacita' aggiuntiva"
            elif coppia == "C-base":
                senso = "capacita' + contenuto"
            elif coppia == "B-D":
                senso = "contenuto, capacita' intermedia"
            else:
                senso = ""
            print(f"{coppia:12s} {nome:11s} {n:5d} | {m:+9.1f}  [{lo:+7.1f}; {hi:+7.1f}] | "
                  f"{concordi:2d}/{n:<4d} | {senso}")

    print("\nIl confronto PRINCIPALE e' C - E: stessa capacita', differisce per il solo")
    print("contenuto del profilo a bande. Se C - E e' positivo e E - base non lo e', il")
    print("guadagno viene dal contenuto e non dalla dimensione del blocco di storia.")
    print()
    print("Il controllo a capacita' appaiata non elimina pero' l'effetto della difficolta'")
    print("relativa delle partizioni, che va misurato a parte con `--attach-check` o con il")
    print("priore storico sui due gruppi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
