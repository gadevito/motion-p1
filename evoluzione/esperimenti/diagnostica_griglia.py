#!/usr/bin/env python3
"""
Diagnostica della griglia temporale. Legge SOLTANTO le marche temporali.
=========================================================================
Nessuna prestazione, nessun bersaglio, nessun dato di test oltre ai tempi.

REGOLA APPROVATA per le origini:

    un'origine t e' ammissibile soltanto se la sequenza temporale, dal primo
    passo della finestra dinamica (t - 11) all'ultimo bersaglio (t + 8),
    rispetta la cadenza reale di 15 minuti SENZA SALTI nella griglia

Le misure mancanti del singolo sensore NON c'entrano: restano alle maschere.

MISURA

    [1] origini ammissibili per periodo, prima e dopo la regola
    [2] le finestre del DESCRITTORE: sono 24 ore reali o 96 righe compresse?
    [3] il CALENDARIO con la regola approvata — tutti i 96 intervalli attesi,
        e per la validazione una giornata completa di valutazione — contro
        quello congelato, costruito con la regola «almeno 90 marche»
    [4] gli ESTREMI di acquisizione, descrittore e adattamento di F

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/diagnostica_griglia.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.addestramento import _carica  # noqa: E402

PASSO = pd.Timedelta(minutes=15)
FIN, H, L = 12, 8, 96
TEST = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
        "Melbourne": (8806, 8902)}
VAL = {"Madrid": (7392, 7488), "Londra": (7389, 7485),
       "Melbourne": (7251, 7347)}


def passi_regolari(ts):
    """ok[i] vero se fra la riga i e la i+1 passano esattamente 15 minuti."""
    return np.asarray(pd.Series(ts).diff().iloc[1:] == PASSO)


def contigua(ok, a, b):
    """Righe a..b (incluse) su griglia regolare: nessun salto fra a e b."""
    if a < 0 or b >= len(ok) + 1 or b <= a:
        return False
    return bool(ok[a:b].all())


def ammissibili(ok, T, inizio, fine):
    """Origini t in [inizio, fine) con righe t-11..t+8 contigue."""
    return [t for t in range(max(inizio, FIN - 1), fine)
            if t + H < T and contigua(ok, t - FIN + 1, t + H)]


def primo_t0(ok, ts, a, b, giornata_dopo: bool):
    """Regola APPROVATA: il primo t0 con i 96 intervalli di (t0, t0+24h]
    tutti presenti — righe t0..t0+96 contigue — e, se richiesto, anche la
    giornata successiva completa, entro il periodo [a, b)."""
    for t0 in range(a, b):
        t1 = t0 + L
        if t1 >= b or not contigua(ok, t0, t1):
            continue
        if ts[t1] - ts[t0] != L * PASSO:
            continue
        if giornata_dopo:
            if t1 + L >= b or not contigua(ok, t1, t1 + L):
                continue
        return t0
    return None


def main() -> int:
    out = {}
    for c in ("Madrid", "Londra", "Melbourne"):
        D = _carica(c, Path("results/evoluzione/maschere"))
        ts = D["ts"]; T = len(ts); e = T - H
        ok = passi_regolari(ts)
        a_tr, a_va, a_te = FIN - 1, int(e * .70), int(e * .85)
        print(f"\n{'=' * 78}\n{c}  —  {T} righe, {int((~ok).sum())} salti\n{'=' * 78}")

        # ---- [1] origini ----------------------------------------------
        print("\n[1] origini ammissibili")
        per = {"addestramento": (a_tr, a_va), "validazione": (a_va, a_te),
               "prova, dopo t1": (TEST[c][1] + 1, e)}
        r1 = {}
        for n, (a, b) in per.items():
            nom = len([t for t in range(max(a, FIN - 1), b) if t + H < T])
            amm = len(ammissibili(ok, T, a, b))
            r1[n] = {"nominali": nom, "ammissibili": amm}
            print(f"    {n:16s} {amm:5d} su {nom:5d}  (escluse {nom - amm})")

        # ---- [2] finestre del descrittore -----------------------------
        print("\n[2] finestre del descrittore: (t - 96, t] in RIGHE")
        rif = {"training, fine periodo": a_va - 1,
               "validazione, inizio": a_va,
               "prova, t1": TEST[c][1],
               "episodio di validazione, t1": VAL[c][1]}
        r2 = {}
        for n, t in rif.items():
            reale = ts[t] - ts[t - L + 1]
            giusta = contigua(ok, t - L + 1, t)
            r2[n] = {"t": int(t), "durata_reale": str(reale),
                     "24_ore_reali": giusta}
            print(f"    {n:30s} t={t:5d}  96 righe coprono {reale}  "
                  f"{'OK: 24 ore reali' if giusta else 'COMPRESSA: attraversa un salto'}")

        # ---- [3] calendario con la regola approvata --------------------
        print("\n[3] calendario: regola APPROVATA contro regola implementata (>= 90)")
        tv = primo_t0(ok, ts, a_va, a_te, giornata_dopo=True)
        tp = primo_t0(ok, ts, a_te, e, giornata_dopo=False)
        r3 = {"validazione": {"approvata": tv, "congelata": VAL[c][0]},
              "prova": {"approvata": tp, "congelata": TEST[c][0]}}
        for n, v in r3.items():
            print(f"    {n:12s} approvata t0={v['approvata']}  congelata "
                  f"t0={v['congelata']}  "
                  f"{'COINCIDE' if v['approvata'] == v['congelata'] else 'DIVERSO'}")

        # ---- [4] estremi -------------------------------------------------
        t0, t1 = TEST[c]
        prima_ad = t0 + FIN - 1
        print("\n[4] estremi, episodio di prova")
        print(f"    acquisizione dichiarata   (t0, t1] = righe {t0 + 1}..{t1}, "
              f"96 intervalli")
        print(f"    descrittore di P          righe {t1 - L + 1}..{t1}")
        print(f"    adattamento di F          righe {prima_ad - FIN + 1}..{t1} "
              f"-> {'INCLUDE t0' if prima_ad - FIN + 1 == t0 else 'esclude t0'}")
        out[c] = {"origini": r1, "descrittore": r2, "calendario": r3,
                  "salti_totali": int((~ok).sum())}

    Path("results/evoluzione/diagnostica_griglia.json").write_text(
        json.dumps(out, indent=2, default=str))
    print("\n  salvato in results/evoluzione/diagnostica_griglia.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
