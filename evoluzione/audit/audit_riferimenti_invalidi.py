#!/usr/bin/env python3
"""
Riferimenti non validi e segmenti variabili — fino alla popolazione modellata.
==============================================================================
Nessun addestramento. Due tabelle, entrambe riferite anche alle celle che entrano
davvero negli esperimenti, piu' il percorso corrispondente nel codice.

PERCHE' NON BASTA CONTARE NEL DATO GREZZO. Una quota trascurabile sulle righe
sorgente puo' concentrarsi in pochi nodi della popolazione modellata, e li' non
essere piu' trascurabile. I conteggi vanno quindi a tre livelli — righe, segmenti
distinti, celle incluse — e separati per periodo.

L'ORDINE DELLE OPERAZIONI E' IL CONTROLLO PIU' IMPORTANTE. Una divisione per zero
produce infinito; se il troncamento all'intervallo ammesso avviene PRIMA del
controllo di validita', quell'infinito diventa un valore finito apparentemente
valido, e quindi una classe. Lo script cerca nel codice l'ordine effettivo e lo
riporta, perche' e' cio' che decide se esistano celle etichettate impropriamente.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/audit_riferimenti_invalidi.py
    poetry run python evoluzione/audit/audit_riferimenti_invalidi.py --giorni 10
    poetry run python evoluzione/audit/audit_riferimenti_invalidi.py --solo-melbourne
"""
import argparse
import glob as globmod
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

T4 = "data_collection/traffic4cast"
CTX = {
    "MADRID_2022": ("Madrid", "t4cmad", f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz"),
    "LONDON_2022": ("Londra", "t4clon", f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz"),
    "MELBOURNE_2022": ("Melbourne", "t4cmel", f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz"),
}
QUOTA_TR, QUOTA_VA = 0.70, 0.85
ORIZZONTE_MAX = 8


def file_velocita(citta, n=None):
    for est in ("parquet", "csv"):
        f = sorted(globmod.glob(
            f"{T4}/{citta}/speed_classes/*/speed_classes_*.{est}"))
        if f:
            return f if n is None else f[:n]
    return []


def leggi(x, colonne=None):
    if str(x).endswith(".parquet"):
        return pd.read_parquet(x, columns=colonne)
    return pd.read_csv(x, usecols=colonne, low_memory=False)


def chiave(d):
    """La chiave del segmento. Con `u` e `v` e' orientata, quindi distingue i due
    versi; se esistessero archi paralleli servirebbe un identificativo ulteriore,
    e lo script lo segnala."""
    return list(zip(d.u.to_numpy(), d.v.to_numpy()))


# --------------------------------------------------------- percorso nel codice
def percorso_codice():
    print("=" * 78)
    print("PERCORSO NEL CODICE — ordine fra divisione, troncamento e validita'")
    print("=" * 78)
    cand = sorted(set(globmod.glob(f"{T4}/*.py") + globmod.glob(f"{T4}/**/*.py",
                                                                recursive=True)))
    trovati = 0
    for p in cand:
        t = Path(p).read_text(errors="ignore")
        if "free_flow" not in t:
            continue
        trovati += 1
        print(f"\n  {p}")
        righe = t.split("\n")
        for i, r in enumerate(righe, 1):
            if re.search(r"free_flow|median_speed|clip|np\.where|/\s*ff|/\s*free|"
                         r"isfinite|nan_to_num|congestion", r):
                print(f"    {i:5d}  {r.strip()[:96]}")
    if not trovati:
        print("  nessun sorgente con `free_flow` sotto data_collection/traffic4cast/")
        print("  cercare a mano: grep -rl free_flow data_collection/ models/")
    print("\n  Da verificare in queste righe: se il troncamento all'intervallo")
    print("  ammesso preceda il controllo di validita', un infinito da divisione")
    print("  per zero diventa un valore finito e riceve una classe.")


# ------------------------------------------------------- riferimenti invalidi
def invalidi(citta, nome, sigla, tp, giorni):
    f = file_velocita(citta, giorni)
    if not f:
        print(f"{nome}: file sorgente non trovati")
        return None
    agg = defaultdict(lambda: {"righe": 0, "valori": set(), "inval": 0,
                               "manc": 0, "nulli": 0, "neg": 0, "nonfin": 0})
    tot = dict(righe=0, manc=0, nulli=0, neg=0, nonfin=0)
    for x in f:
        d = leggi(x, ["u", "v", "free_flow_kph"])
        v = pd.to_numeric(d.free_flow_kph, errors="coerce").to_numpy()
        manc = np.isnan(v)
        nonfin = ~np.isfinite(v) & ~manc
        nulli = np.isfinite(v) & (v == 0)
        neg = np.isfinite(v) & (v < 0)
        tot["righe"] += len(d)
        tot["manc"] += int(manc.sum()); tot["nonfin"] += int(nonfin.sum())
        tot["nulli"] += int(nulli.sum()); tot["neg"] += int(neg.sum())
        for k, val, m1, m2, m3, m4 in zip(chiave(d), v, manc, nulli, neg, nonfin):
            a = agg[k]
            a["righe"] += 1
            if np.isfinite(val):
                a["valori"].add(round(float(val), 6))
            a["manc"] += int(m1); a["nulli"] += int(m2)
            a["neg"] += int(m3); a["nonfin"] += int(m4)
            a["inval"] += int(m1 or m2 or m3 or m4)

    seg_tot = len(agg)
    seg_con_inval = sum(1 for a in agg.values() if a["inval"])
    seg_tutti_inval = sum(1 for a in agg.values() if a["inval"] == a["righe"])

    # -- la popolazione modellata -------------------------------------------
    mod = mod_inval = mod_tutti = None
    celle = {}
    if globmod.glob(tp):
        z = np.load(tp, allow_pickle=True)
        sid = z["sensor_ids"].astype(str)
        mod = len(sid)
        # la chiave dei bersagli puo' essere "u_v" oppure un identificativo proprio
        chiavi_mod = set()
        for s in sid:
            p = s.split("_")
            if len(p) == 2 and p[0].isdigit() and p[1].isdigit():
                chiavi_mod.add((int(p[0]), int(p[1])))
        if chiavi_mod:
            mod_inval = sum(1 for k in chiavi_mod if agg.get(k, {}).get("inval", 0))
            mod_tutti = sum(1 for k in chiavi_mod
                            if k in agg and agg[k]["inval"] == agg[k]["righe"])
        # celle per periodo, dalla classe gia' costruita
        C = z["congestion_emp"]
        T = C.shape[0]; e = T - ORIZZONTE_MAX
        for eti, sl in (("addestramento", slice(0, int(e * QUOTA_TR))),
                        ("validazione", slice(int(e * QUOTA_TR), int(e * QUOTA_VA))),
                        ("prova", slice(int(e * QUOTA_VA), None))):
            s = C[sl]
            celle[eti] = {"totali": int(s.size), "non valide": int((s <= 0).sum())}

    print(f"\n{'='*78}\n{nome}  ({len(f)} file esaminati)\n{'='*78}")
    print(f"  [righe sorgente]     {tot['righe']:>12,}")
    for k, eti in (("manc", "mancanti"), ("nulli", "nulli"),
                   ("neg", "negativi"), ("nonfin", "non finiti")):
        print(f"     {eti:14s} {tot[k]:>12,}  ({100*tot[k]/max(tot['righe'],1):.4f}%)")
    print(f"\n  [segmenti distinti]  {seg_tot:>12,}")
    print(f"     con almeno un riferimento invalido: {seg_con_inval:,} "
          f"({100*seg_con_inval/max(seg_tot,1):.3f}%)")
    print(f"     invalidi in TUTTE le righe:         {seg_tutti_inval:,} "
          f"({100*seg_tutti_inval/max(seg_tot,1):.3f}%)")
    if mod is not None:
        print(f"\n  [popolazione modellata] {mod:,} sensori")
        if mod_inval is not None:
            print(f"     con almeno un riferimento invalido: {mod_inval:,}")
            print(f"     invalidi ovunque -> NON VALUTABILI: {mod_tutti:,}")
        else:
            print("     chiavi dei bersagli non riconducibili a (u, v): "
                  "il collegamento va fatto a mano")
    if celle:
        print("\n  [celle incluse negli esperimenti]")
        for eti, c in celle.items():
            print(f"     {eti:14s} {c['totali']:>12,} celle, "
                  f"{c['non valide']:>10,} non valide "
                  f"({100*c['non valide']/max(c['totali'],1):.2f}%)")
    return agg


# --------------------------------------------------- segmenti variabili ------
def variabili(nome, agg, out: Path, limite=40):
    if agg is None:
        return
    anom = {k: a for k, a in agg.items() if len(a["valori"]) > 1}
    print(f"\n{'='*78}\n{nome}: segmenti con piu' di un valore\n{'='*78}")
    print(f"  {len(anom):,} su {len(agg):,} ({100*len(anom)/max(len(agg),1):.3f}%)")
    if not anom:
        return
    # la variabilita' sparisce togliendo i valori invalidi?
    resta = sum(1 for a in anom.values()
                if len({v for v in a["valori"] if v > 0}) > 1)
    print(f"  ancora variabili escludendo nulli e negativi: {resta:,} "
          f"({100*resta/max(len(anom),1):.1f}%)")
    # differenze minime o sostanziali?
    sost = 0
    for a in anom.values():
        v = sorted(x for x in a["valori"] if x > 0)
        if len(v) > 1 and (v[-1] - v[0]) / v[-1] > 0.01:
            sost += 1
    print(f"  con scarto relativo oltre l'1%: {sost:,} "
          f"(gli altri sono differenze di rappresentazione)")
    righe = []
    for k, a in sorted(anom.items(), key=lambda x: -len(x[1]["valori"]))[:limite]:
        righe.append(dict(segment_key=f"{k[0]}_{k[1]}", numero_righe=a["righe"],
                          numero_valori_distinti=len(a["valori"]),
                          valori_distinti=sorted(a["valori"]),
                          presenza_di_valori_non_positivi=bool(a["nulli"] or a["neg"]),
                          righe_invalide=a["inval"]))
    T = pd.DataFrame(righe)
    out.parent.mkdir(parents=True, exist_ok=True)
    T.to_csv(out, index=False)
    print(f"\n  primi {min(limite,len(anom))} in {out}")
    print(T.head(8).to_string(index=False, max_colwidth=34))
    print("\n  Restano da accertare, sui segmenti elencati: se la chiave sia")
    print("  sufficientemente specifica (direzione, archi paralleli), se esistano")
    print("  righe con la medesima chiave e istante e riferimenti diversi, e se le")
    print("  variazioni siano aggiornamenti persistenti della sorgente.")


def main() -> int:
    ap = argparse.ArgumentParser(description="riferimenti invalidi e segmenti variabili")
    ap.add_argument("--giorni", type=int, default=None,
                    help="file per contesto; senza, tutti")
    ap.add_argument("--solo-melbourne", action="store_true")
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/audit"))
    a = ap.parse_args()

    percorso_codice()
    voci = ([("MELBOURNE_2022", CTX["MELBOURNE_2022"])] if a.solo_melbourne
            else list(CTX.items()))
    for citta, (nome, sigla, tp) in voci:
        agg = invalidi(citta, nome, sigla, tp, a.giorni)
        variabili(nome, agg, a.out / f"segmenti_variabili_{sigla}.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
