#!/usr/bin/env python3
"""
Controllo completo del riferimento: artefatti usati e intero periodo sorgente.
==============================================================================
Nessun addestramento. Chiude le due limitazioni del controllo precedente, che
riguardava dieci giornate e la sorgente anziche' gli artefatti.

PARTE A — GLI ARTEFATTI EFFETTIVAMENTE USATI. `t4c22_adapter.py` alla riga 137
salva il vettore `ff` dentro il file dei bersagli come `ff_emp` e `ff_leg`: il
riferimento realmente impiegato per costruire ogni contesto e' quindi ispezionabile
direttamente, senza passare dalla sorgente. E' il controllo che il revisore chiede
per poter affermare «nessun effetto sui risultati» anziche' «nessun riferimento
invalido nelle giornate controllate».

PARTE B — L'INTERO PERIODO SORGENTE. Legge il solo identificativo di segmento e il
riferimento da TUTTI i file usati nella costruzione, e accumula i valori validi
distinti per segmento. La classificazione e' a tre esiti, che non vanno confusi:

    nessun riferimento valido   |  un solo valore distinto  |  piu' valori distinti

Il primo e il terzo sono proprieta' diverse: un segmento senza riferimenti validi
non e' un segmento variabile, ed e' l'errore che il controllo precedente commetteva
usando `nunique()`, che scarta i mancanti.

DUE POPOLAZIONI DA TENERE DISTINTE, come il deliverable le nomina: i nodi
selezionati dal preprocessing — 900, 900 e 594 — e quelli ulteriormente ristretti
dall'aggancio al grafo, che sono 828, 774 e 587. Il controllo sul soprainsieme
protegge il sottoinsieme, ma i nomi devono restare coerenti.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/controllo_riferimento_completo.py
    poetry run python evoluzione/audit/controllo_riferimento_completo.py --solo-artefatti
"""
import argparse
import glob as globmod
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

T4 = "data_collection/traffic4cast"
CTX = {"MADRID_2022": ("Madrid", "madrid"),
       "LONDON_2022": ("Londra", "london"),
       "MELBOURNE_2022": ("Melbourne", "melbourne")}


# ------------------------------------------------------------- parte A ------
def artefatti(a):
    print("=" * 78)
    print("PARTE A — i vettori `ff` dentro gli artefatti effettivamente usati")
    print("=" * 78)
    trovati = 0
    for citta, (nome, _) in CTX.items():
        f = sorted(globmod.glob(f"{T4}/{citta}/gomo_fmt*/targets_*.npz"))
        if not f:
            print(f"\n{nome}: nessun file di bersagli sotto {T4}/{citta}/gomo_fmt*/")
            continue
        print(f"\n{nome}  ({len(f)} artefatti)")
        for x in f:
            z = np.load(x, allow_pickle=True)
            campi = [k for k in z.files if k.startswith("ff")]
            if not campi:
                print(f"  {Path(x).parent.name}/{Path(x).name:30s} nessun campo `ff`: "
                      "non e' conservato in questo artefatto")
                continue
            trovati += 1
            for k in campi:
                v = np.asarray(z[k], dtype="float64")
                fin = np.isfinite(v)
                pos = fin & (v > 0)
                sid = z["sensor_ids"].astype(str) if "sensor_ids" in z.files else None
                eti = f"{Path(x).parent.name}/{Path(x).name}"
                print(f"  {eti:52s} {k}: {len(v):5d} valori | "
                      f"finiti {fin.sum():5d} | positivi {pos.sum():5d} | "
                      f"INVALIDI {int((~pos).sum()):4d}")
                if (~pos).any() and sid is not None and len(sid) == len(v):
                    cattivi = [str(x) for x in sid[~pos][:8]]
                    print(f"       sensori con riferimento invalido: "
                          f"{', '.join(cattivi)}"
                          f"{' …' if (~pos).sum() > 8 else ''}")
                if pos.any():
                    print(f"       intervallo dei validi: "
                          f"[{v[pos].min():.1f}; {v[pos].max():.1f}] km/h, "
                          f"mediana {np.median(v[pos]):.1f}")
    if trovati:
        print("\n  Questo controllo riguarda i vettori REALMENTE impiegati per")
        print("  costruire i bersagli, non un campione della sorgente: se nessun")
        print("  valore e' invalido, l'affermazione «nessun effetto sui risultati»")
        print("  e' sostenuta per i contesti ispezionati.")
    return trovati


# ------------------------------------------------------------- parte B ------
def sorgente(a):
    print("\n" + "=" * 78)
    print("PARTE B — intero periodo sorgente, classificazione a tre esiti")
    print("=" * 78)
    for citta, (nome, sotto) in CTX.items():
        f = sorted(globmod.glob(f"{T4}/{citta}/speed_classes/*/speed_classes_*.parquet")) \
            or sorted(globmod.glob(f"{T4}/{citta}/speed_classes/*/speed_classes_*.csv"))
        if not f:
            print(f"\n{nome}: file sorgente non trovati")
            continue
        if a.giorni:
            f = f[:a.giorni]
        val = defaultdict(set)      # valori VALIDI distinti per segmento
        visti = set()               # ogni segmento incontrato, anche solo invalido
        for i, x in enumerate(f, 1):
            d = (pd.read_parquet(x, columns=["u", "v", "free_flow_kph"])
                 if str(x).endswith(".parquet")
                 else pd.read_csv(x, usecols=["u", "v", "free_flow_kph"]))
            u = d.u.to_numpy(); v_ = d.v.to_numpy()
            ff = pd.to_numeric(d.free_flow_kph, errors="coerce").to_numpy()
            ok = np.isfinite(ff) & (ff > 0)
            for k in zip(u, v_):
                visti.add(k)
            for k, x_ in zip(zip(u[ok], v_[ok]), np.round(ff[ok], 6)):
                val[k].add(float(x_))
            if i % 20 == 0:
                print(f"  {nome}: {i}/{len(f)} file, {len(visti):,} segmenti",
                      end="\r", flush=True)
        senza = sum(1 for k in visti if not val.get(k))
        uno = sum(1 for k in visti if len(val.get(k, ())) == 1)
        molti = sum(1 for k in visti if len(val.get(k, ())) > 1)
        print(f"\n{nome}  ({len(f)} file, {len(visti):,} segmenti)")
        print(f"  nessun riferimento valido : {senza:8,d} ({100*senza/len(visti):6.3f}%)")
        print(f"  un solo valore distinto   : {uno:8,d} ({100*uno/len(visti):6.3f}%)")
        print(f"  piu' valori distinti      : {molti:8,d} ({100*molti/len(visti):6.3f}%)")
        if molti:
            ese = [(k, sorted(val[k])) for k in visti if len(val.get(k, ())) > 1][:6]
            for k, vv in ese:
                sc = (max(vv) - min(vv)) / max(vv)
                print(f"     {k[0]}_{k[1]}: {vv}  scarto relativo {100*sc:.2f}%")
            out = Path("results/evoluzione/audit") / f"variabili_{sotto}.csv"
            out.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame([{"segment_key": f"{k[0]}_{k[1]}",
                           "numero_valori_distinti": len(val[k]),
                           "valori_distinti": sorted(val[k])}
                          for k in visti if len(val.get(k, ())) > 1]).to_csv(out, index=False)
            print(f"     elenco completo in {out}")


def main() -> int:
    ap = argparse.ArgumentParser(description="controllo completo del riferimento")
    ap.add_argument("--giorni", type=int, default=None,
                    help="limita i file della parte B; senza, tutti")
    ap.add_argument("--solo-artefatti", action="store_true")
    a = ap.parse_args()
    artefatti(a)
    if not a.solo_artefatti:
        sorgente(a)
    print("\n" + "=" * 78)
    print("  La disponibilita' operativa del riferimento all'inserimento resta")
    print("  questione distinta e non chiudibile da questi dati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
