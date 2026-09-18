#!/usr/bin/env python3
"""
Diagnostica post-hoc del raccordo. ESPLORATIVA.
================================================
Nessun addestramento, nessuna modifica della rappresentazione. Opera sulle
predizioni gia' salvate della campagna conforme.

**LE ASSOCIAZIONI OSSERVATE NON SONO SPIEGAZIONI CAUSALI.** La diagnostica e'
suggerita dai risultati che descrive, sicche' cio' che vi emerge va confermato
altrove, non da questo esperimento.

LA FINESTRA E' QUELLA DELL'INSERIMENTO, verificata nel codice: `addestramento.py`
calcola il descrittore UNA VOLTA su `ist["prova"][0]` e lo riusa per ogni istante
di previsione. Copertura e bande mancanti sono quindi proprieta' del nodo
NELL'EPISODIO DI INSERIMENTO, non di ciascun istante.

    storia all'inserimento        96 passi, FISSA: e' quella caratterizzata qui
    storia del descrittore
      aggiornata                  non usata in questa campagna
    ingresso dinamico recente     12 passi, mobile: e' un terzo oggetto

I CINQUE TAGLI:

    per inizializzazione e partizione   descrive la struttura gia' osservata,
                                        e non ne e' conferma indipendente
    per orizzonte                       senza media sugli orizzonti
    per classe vera                     con il CONTRIBUTO alla differenza totale
    per copertura della finestra        [0;.25) [.25;.5) [.5;.75) [.75;1]
    per bande non osservate             0, 1, 2, almeno 3

I CONFINI DEI GRUPPI SONO FISSATI QUI, prima di guardare i delta.

SI RIPORTANO LE PERDITE ASSOLUTE oltre al delta relativo: quest'ultimo puo'
crescere per il solo cambiare del denominatore. I pesi restano quelli originari,
**non ristimati nei sottogruppi**.

NESSUN INTERVALLO: stime descrittive. I valori per inizializzazione si conservano
separati, perche' un andamento nei sottogruppi puo' dipendere da una sola colonna
della matrice.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/diagnostica_posthoc.py
    poetry run python evoluzione/analisi/diagnostica_posthoc.py --contesto Londra
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.analizza_raccordo import (  # noqa: E402
    CONTESTI, ORIZZONTI, VARIANTI, carica, controlla, coppie_presenti,
    partizioni_presenti, pesi_classe)
from evoluzione.analisi.pesi import media_orizzonti  # noqa: E402

N_BANDE = 8
L_STORIA = 96
CONFINI_COP = (0.0, 0.25, 0.50, 0.75, 1.0001)
GRUPPI_BANDE = ((0, 0), (1, 1), (2, 2), (3, N_BANDE))
T4 = "data_collection/traffic4cast"
MASC = {"Madrid": "Madrid", "Londra": "Londra", "Melbourne": "Melbourne"}


def perdite_per_cella(d, w):
    """Termine pesato e peso, per ciascuna riga."""
    p = d[["p1", "p2", "p3"]].to_numpy()
    y = d.vero.to_numpy()
    pt = np.clip(p[np.arange(len(y)), y], 1e-7, 1.0)
    wy = w[y]
    return wy * -np.log(pt), wy


def wce(num, den, orizz, sel=None):
    """La perdita: per orizzonte, poi media. Stessa formula del raccordo."""
    v = []
    for h in np.unique(orizz):
        m = (orizz == h) if sel is None else ((orizz == h) & sel)
        dd = den[m].sum()
        v.append(num[m].sum() / dd if dd > 0 else np.nan)
    return media_orizzonti(v)


def caratterizza(contesto, nodi, t_ins, dir_masc: Path):
    """Copertura e bande non osservate, sulla finestra dell'INSERIMENTO."""
    M = np.load(dir_masc / f"maschere_{MASC[contesto]}.npz", allow_pickle=True)
    m_r = M["maschera_r"]
    ts = pd.to_datetime(M["timestamps"])
    ore = ts.hour.to_numpy()
    a = max(t_ins - L_STORIA, 0)
    sel = slice(a + 1, t_ins + 1)
    b = ore[sel] // 3
    fuori = {}
    for k in nodi:
        m = m_r[sel, k]
        n = np.array([int(m[b == j].sum()) for j in range(N_BANDE)])
        att = np.array([int((b == j).sum()) for j in range(N_BANDE)])
        fuori[int(k)] = {"copertura": float(m.mean()),
                         "bande_vuote": int(((n == 0) & (att > 0)).sum())}
    return fuori


def riga(eti, num_a, den_a, num_b, den_b, orizz, sel, extra=""):
    """Perdite assolute, differenza e delta relativo, su un gruppo."""
    n = int(sel.sum())
    if n == 0:
        return {"gruppo": eti, "n": 0, "nota": "GRUPPO VUOTO"}
    la, ka = wce(num_a, den_a, orizz, sel)
    lb, kb = wce(num_b, den_b, orizz, sel)
    if not np.isfinite(la) or not np.isfinite(lb) or la <= 0:
        return {"gruppo": eti, "n": n, "nota": "DENOMINATORE NON DEFINITO"}
    return {"gruppo": eti, "n": n, "L_legacy": la, "L_corrected": lb,
            "differenza": lb - la, "delta_rel": 100 * (lb - la) / la,
            "orizzonti_contribuenti": min(ka, kb), "extra": extra}


def stampa(titolo, righe, colonne_extra=""):
    print(f"\n  {titolo}")
    print(f"     {'gruppo':22s} {'n':>10} {'L LEGACY':>10} {'L CORR.':>10} "
          f"{'differenza':>11} {'delta':>9}  {colonne_extra}")
    for r in righe:
        if r.get("nota"):
            print(f"     {r['gruppo']:22s} {r['n']:>10,}  {r['nota']}")
            continue
        print(f"     {r['gruppo']:22s} {r['n']:>10,} {r['L_legacy']:10.5f} "
              f"{r['L_corrected']:10.5f} {r['differenza']:+11.5f} "
              f"{r['delta_rel']:+8.3f}%  {r.get('extra','')}")


def main() -> int:
    ap = argparse.ArgumentParser(description="diagnostica post-hoc")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/raccordo"))
    ap.add_argument("--pesi", type=Path,
                    default=Path("results/evoluzione/pesi"))
    ap.add_argument("--maschere", type=Path,
                    default=Path("results/evoluzione/maschere"))
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    print("=" * 92)
    print("DIAGNOSTICA POST-HOC — ESPLORATIVA")
    print("=" * 92)
    print("  Le associazioni osservate NON sono spiegazioni causali: la")
    print("  diagnostica e' suggerita dai risultati che descrive.")
    print("\n  Finestra caratterizzata: quella dell'INSERIMENTO (96 passi, FISSA).")
    print("  Verificato nel codice: il descrittore e' calcolato una volta su")
    print("  ist['prova'][0] e riusato per ogni istante di previsione.")
    print(f"\n  Confini dei gruppi, fissati prima di guardare i delta:")
    print(f"     copertura      {list(CONFINI_COP[:-1])} … 1")
    print(f"     bande vuote    0, 1, 2, ≥3")

    fuori = {}
    for c in a.contesto:
        print(f"\n{'=' * 92}\n{c}\n{'=' * 92}")
        CP = coppie_presenti(a.dir, c)
        PZ = {p: pesi_classe(c, p, a.pesi)
              for p in partizioni_presenti(a.dir, c)}
        celle = []
        car = {}
        for p, s in CP:
            if True:
                D = carica(a.dir, c, p, s)
                if D is None:
                    continue
                controlla(D, c, p, s)
                w = PZ[p].vettore()
                A, B = D["LEGACY"], D["BASE-CORRECTED"]
                na, da = perdite_per_cella(A, w)
                nb, db = perdite_per_cella(B, w)
                t_ins = int(A.istante.min())
                if (p, t_ins) not in car:
                    car[(p, t_ins)] = caratterizza(
                        c, np.unique(A.nodo.to_numpy()), t_ins, a.maschere)
                cc = car[(p, t_ins)]
                celle.append(pd.DataFrame({
                    "p": p, "s": s, "nodo": A.nodo.to_numpy(),
                    "orizzonte": A.orizzonte.to_numpy(), "vero": A.vero.to_numpy(),
                    "num_a": na, "den_a": da, "num_b": nb, "den_b": db,
                    "copertura": [cc[int(k)]["copertura"] for k in A.nodo],
                    "bande_vuote": [cc[int(k)]["bande_vuote"] for k in A.nodo]}))
        if not celle:
            print("  nessuna coppia")
            continue
        T = pd.concat(celle, ignore_index=True)
        NA, DA = T.num_a.to_numpy(), T.den_a.to_numpy()
        NB, DB = T.num_b.to_numpy(), T.den_b.to_numpy()
        OR = T.orizzonte.to_numpy()
        tutto = np.ones(len(T), bool)
        base = riga("COMPLESSIVO", NA, DA, NB, DB, OR, tutto)
        print(f"\n  complessivo: L LEGACY {base['L_legacy']:.5f}, "
              f"BASE-CORRECTED {base['L_corrected']:.5f}, "
              f"differenza {base['differenza']:+.5f}, "
              f"delta {base['delta_rel']:+.3f}%")
        print(f"  {len(T):,} celle | {T.nodo.nunique()} nodi distinti | "
              f"{T.groupby(['p','s']).ngroups} coppie")
        R = {"complessivo": base}

        # --- 1. per inizializzazione e partizione -------------------------
        rr = [riga(f"p{p} s{s}", NA, DA, NB, DB, OR,
                   ((T.p == p) & (T.s == s)).to_numpy()) for p, s in CP]
        stampa("[1] per partizione e inizializzazione  (descrive la struttura "
               "gia' osservata, non la conferma)", rr)
        R["partizione_inizializzazione"] = rr

        # --- 2. per orizzonte, SENZA media sugli orizzonti ----------------
        rr = []
        for h in ORIZZONTI:
            m = (OR == h)
            dda, ddb = DA[m].sum(), DB[m].sum()
            if dda <= 0 or ddb <= 0:
                rr.append({"gruppo": f"{h} passi", "n": int(m.sum()),
                           "nota": "DENOMINATORE NON DEFINITO"}); continue
            la, lb = NA[m].sum() / dda, NB[m].sum() / ddb
            rr.append({"gruppo": f"{h} passi ({h*15} min)", "n": int(m.sum()),
                       "L_legacy": la, "L_corrected": lb,
                       "differenza": lb - la, "delta_rel": 100 * (lb - la) / la})
        stampa("[2] per orizzonte  (senza media sugli orizzonti)", rr)
        R["orizzonte"] = rr

        # --- 3. per classe vera, con il CONTRIBUTO alla differenza totale --
        tot_diff = float(NB.sum() - NA.sum())
        rr = []
        for k, nome in ((0, "verde"), (1, "intermedia"), (2, "CRITICA")):
            m = (T.vero.to_numpy() == k)
            r = riga(nome, NA, DA, NB, DB, OR, m)
            if not r.get("nota"):
                contrib = float(NB[m].sum() - NA[m].sum())
                r["extra"] = (f"contributo {contrib:+.1f} su {tot_diff:+.1f} "
                              f"({100*contrib/tot_diff:+.1f}%)"
                              if tot_diff != 0 else "contributo n.d.")
            rr.append(r)
        stampa("[3] per classe vera  (il peso si cancella nel rapporto interno: "
               "guardare il CONTRIBUTO)", rr, "contributo alla differenza totale")
        R["classe"] = rr

        # --- 4. per copertura della finestra d'inserimento ----------------
        rr = []
        for i in range(len(CONFINI_COP) - 1):
            lo, hi = CONFINI_COP[i], CONFINI_COP[i + 1]
            m = ((T.copertura >= lo) & (T.copertura < hi)).to_numpy()
            r = riga(f"[{lo:.2f}; {hi if hi<=1 else 1:.2f})", NA, DA, NB, DB,
                     OR, m)
            if not r.get("nota"):
                sub = T[m]
                r["extra"] = (f"{sub.nodo.nunique():3d} nodi | critica "
                              f"{int((sub.vero == 2).sum()):>7,} | "
                              f"{sub.groupby(['p','s']).ngroups} coppie")
            rr.append(r)
        stampa("[4] per COPERTURA della finestra d'inserimento", rr,
               "nodi | celle critiche | coppie")
        R["copertura"] = rr

        # --- 5. per bande non osservate -----------------------------------
        rr = []
        for lo, hi in GRUPPI_BANDE:
            eti = f"{lo}" if lo == hi else f"≥{lo}"
            m = ((T.bande_vuote >= lo) & (T.bande_vuote <= hi)).to_numpy()
            r = riga(f"{eti} bande vuote", NA, DA, NB, DB, OR, m)
            if not r.get("nota"):
                sub = T[m]
                r["extra"] = (f"{sub.nodo.nunique():3d} nodi | critica "
                              f"{int((sub.vero == 2).sum()):>7,} | "
                              f"{sub.groupby(['p','s']).ngroups} coppie")
            rr.append(r)
        stampa("[5] per BANDE NON OSSERVATE nella finestra d'inserimento", rr,
               "nodi | celle critiche | coppie")
        R["bande"] = rr

        # -- i valori per INIZIALIZZAZIONE, separati -----------------------
        print(f"\n  [4bis] copertura, separata per inizializzazione")
        SS = sorted({s for _, s in CP})
        print(f"     {'gruppo':22s} " + "".join(f"{'s'+str(s):>12}" for s in SS))
        for i in range(len(CONFINI_COP) - 1):
            lo, hi = CONFINI_COP[i], CONFINI_COP[i + 1]
            v = []
            for s in SS:
                m = ((T.copertura >= lo) & (T.copertura < hi)
                     & (T.s == s)).to_numpy()
                r = riga("", NA, DA, NB, DB, OR, m)
                v.append("—" if r.get("nota") else f"{r['delta_rel']:+.3f}%")
            print(f"     {f'[{lo:.2f}; {min(hi,1):.2f})':22s} "
                  + "".join(f"{x:>12}" for x in v))
        print(f"     un andamento sistematico deve reggere su TUTTE le colonne")
        fuori[c] = R

    print(f"\n{'=' * 92}")
    print("  Stime descrittive, senza intervalli: con tre inizializzazioni")
    print("  l'incertezza nei sottogruppi sarebbe ancora meno informata.")
    print("  Il delta relativo puo' crescere per il solo cambiare del")
    print("  denominatore: le perdite assolute sono riportate accanto.")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"natura": "esplorativa, non causale",
             "finestra": "inserimento, 96 passi, fissa",
             "confini_copertura": list(CONFINI_COP),
             "gruppi_bande": [list(x) for x in GRUPPI_BANDE],
             "risultati": fuori}, indent=2, ensure_ascii=False, default=float))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
