#!/usr/bin/env python3
"""
Collaudo di non regressione della costruzione del rapporto.
============================================================
Nessun addestramento. Confronto deterministico fra l'implementazione originaria e
quella corretta.

IL CRITERIO. Su tutte le celle con operandi validi e rapporto finito, le due
implementazioni devono produrre gli STESSI valori e le STESSE classi. Dove
differiscono, la differenza deve riguardare esclusivamente celle che la vecchia
trattava come valide pur non essendolo.

I CASI LIMITE devono essere coperti anche se non presenti nei dati: un riferimento
negativo, una velocita' infinita, un riferimento nullo. Che oggi non ricorrano nei
tre contesti non garantisce che non ricorrano in una campagna futura o in un altro
contesto.

L'esito va salvato nel registro.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_rapporto.py
    poetry run python evoluzione/componente/collauda_rapporto.py --contesto t4cmad
"""
import argparse
import glob as globmod
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.rapporto import (  # noqa: E402
    CLASSE_NON_VALIDA, costruisci, costruisci_vecchio)

ESITI = []
T4 = "data_collection/traffic4cast"
BERSAGLI = {
    "t4cmad": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
}


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def confronta(speed, ff, eti):
    """Il confronto richiesto: identita' dove gli operandi sono validi."""
    rv, vv, cv = costruisci_vecchio(speed, ff)
    rn, vn, cn = costruisci(speed, ff)
    # le celle che la NUOVA giudica valide sono quelle con operandi validi e
    # rapporto finito: e' su queste che le due devono coincidere
    m = vn
    ug_r = np.allclose(rv[m], rn[m], rtol=0, atol=0, equal_nan=True) if m.any() else True
    ug_c = bool((cv[m] == cn[m]).all()) if m.any() else True
    # dove la vecchia era valida e la nuova no: sono le celle recuperate
    spurie = vv & ~vn
    return ug_r, ug_c, int(m.sum()), int(spurie.sum()), cv, cn, spurie


def main() -> int:
    ap = argparse.ArgumentParser(description="non regressione del rapporto")
    ap.add_argument("--contesto", nargs="*", default=list(BERSAGLI))
    a = ap.parse_args()

    # ------------------------------------------------------- casi limite ----
    print("[1] casi limite, costruiti perche' coprano anche cio' che oggi non ricorre")
    ff = np.array([50.0, 0.0, -30.0, np.nan, np.inf, 50.0])
    speed = np.array([[40.0, 40.0, 40.0, 40.0, 40.0, np.inf],
                      [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                      [np.nan, 25.0, 25.0, 25.0, 25.0, 25.0]])
    rv, vv, cv = costruisci_vecchio(speed, ff)
    rn, vn, cn = costruisci(speed, ff)
    print(f"\n{'caso':34s} {'vecchia':>22s} {'nuova':>22s}")
    CASI = [
        ((0, 0), "riferimento valido"),
        ((0, 1), "riferimento NULLO"),
        ((0, 2), "riferimento NEGATIVO"),
        ((0, 3), "riferimento mancante"),
        ((0, 4), "riferimento infinito"),
        ((0, 5), "velocita' INFINITA"),
        ((1, 0), "velocita' zero, rif. valido"),
        ((2, 0), "velocita' mancante"),
    ]
    for (i, j), eti in CASI:
        print(f"{eti:34s} r={rv[i,j]:8.3f} cls={cv[i,j]}      "
              f"r={rn[i,j]:8.3f} cls={cn[i,j]}")

    verifica(1, "riferimento nullo: la vecchia assegna una classe, la nuova no",
             cv[0, 1] != CLASSE_NON_VALIDA and cn[0, 1] == CLASSE_NON_VALIDA,
             f"vecchia r={rv[0,1]:.2f} classe {cv[0,1]}; nuova non valida")
    verifica("1b", "riferimento negativo: la vecchia lo rende critico",
             cv[0, 2] == 3 and cn[0, 2] == CLASSE_NON_VALIDA,
             "il troncamento a zero produceva la classe critica")
    verifica("1c", "velocita' infinita: la vecchia la rende libera",
             cv[0, 5] != CLASSE_NON_VALIDA and cn[0, 5] == CLASSE_NON_VALIDA)
    verifica("1d", "velocita' ZERO resta valida e critica in entrambe",
             cv[1, 0] == 3 and cn[1, 0] == 3,
             "traffico fermo: e' un valore legittimo, non va escluso")
    verifica("1e", "velocita' mancante: non valida in entrambe",
             cv[2, 0] == CLASSE_NON_VALIDA and cn[2, 0] == CLASSE_NON_VALIDA)
    verifica("1f", "riferimento valido: le due coincidono",
             rv[0, 0] == rn[0, 0] and cv[0, 0] == cn[0, 0])

    # ---------------------------------------------- non regressione a caso --
    print("\n[2] non regressione su dati casuali con operandi tutti validi")
    rng = np.random.default_rng(0)
    ffr = rng.uniform(10, 100, 200)
    spr = rng.uniform(0, 120, (500, 200))
    ug_r, ug_c, n, spurie, *_ = confronta(spr, ffr, "casuale")
    verifica(2, "valori identici dove la nuova e' valida", ug_r, f"{n:,} celle")
    verifica("2b", "classi identiche", ug_c)
    verifica("2c", "nessuna cella spuria quando tutto e' valido", spurie == 0)

    # ------------------------------------------------ non regressione reale --
    print("\n[3] non regressione sui dati dei contesti")
    for c in a.contesto:
        p = BERSAGLI.get(c)
        if not p or not globmod.glob(p):
            print(f"  {c}: bersagli non trovati")
            continue
        z = np.load(p, allow_pickle=True)
        if "speed" not in z.files or "ff_emp" not in z.files:
            print(f"  {c}: campi `speed` o `ff_emp` assenti "
                  f"({[k for k in z.files][:8]})")
            continue
        sp = np.asarray(z["speed"], dtype="float64")
        ffc = np.asarray(z["ff_emp"], dtype="float64")
        ug_r, ug_c, n, spurie, cv, cn, msp = confronta(sp, ffc, c)
        tot = sp.size
        print(f"  {c}: {tot:,} celle | valide con la nuova {n:,} "
              f"({100*n/tot:.2f}%) | spurie nella vecchia {spurie:,}")
        verifica(f"3-{c}", "valori identici dove la nuova e' valida", ug_r)
        verifica(f"3-{c}b", "classi identiche", ug_c)
        if spurie:
            da = np.bincount(cv[msp], minlength=4)
            print(f"        classi che la vecchia assegnava a celle non valide: "
                  f"verde {da[1]:,}, intermedia {da[2]:,}, critica {da[3]:,}")
        # confronto con la classe conservata nell'artefatto
        if "congestion_emp" in z.files:
            ce = np.asarray(z["congestion_emp"], dtype="int64")
            if ce.shape == cv.shape:
                d = int((ce != cv).sum())
                print(f"        la riproduzione della vecchia differisce "
                      f"dall'artefatto in {d:,} celle "
                      f"({100*d/tot:.4f}%)")
                verifica(f"3-{c}c",
                         "la riproduzione della vecchia coincide con l'artefatto",
                         d == 0,
                         "se non coincide, l'ordine ricostruito non e' quello "
                         "effettivo e il confronto va rifatto sul codice vero")

    print("\n" + "=" * 64)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 64)
    print("\n  Il criterio e' che le due implementazioni coincidano dove gli")
    print("  operandi sono validi, e differiscano SOLO su celle che la vecchia")
    print("  trattava come valide pur non essendolo.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
