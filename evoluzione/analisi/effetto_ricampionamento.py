#!/usr/bin/env python3
"""
Effetto della correzione del ricampionamento sui valori del deliverable.
========================================================================
Nessun addestramento. Ricalcola gli intervalli di R1, R2 e R3 con le tre
procedure e li riporta AFFIANCATI: i valori pubblicati non si sostituiscono, si
dichiarano accanto a quelli ricalcolati con la procedura corretta.

LE TRE PROCEDURE.

    storica        maschera booleana, un solo seme per replica — la pubblicata
    molteplicita'  molteplicita' conservate, un solo seme per replica
    gerarchica     semi con reinserimento E nodi con molteplicita'

CHE COSA GUARDARE. La seconda colonna isola l'effetto delle sole molteplicita'; la
terza aggiunge la variabilita' fra semi, che lo stimatore richiede essendo la
stima una media su di essi. Se un esito passa da «distinguibile da zero» a «tocca
lo zero», va dichiarato: non e' una correzione silenziosa.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/effetto_ricampionamento.py
    poetry run python evoluzione/analisi/effetto_ricampionamento.py --repliche 2000
"""
import argparse
import glob as globmod
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.ricampionamento import (  # noqa: E402
    blocchi, intervalli, prepara)

GO = "data_collection/go-mo/gomo"
T4 = "data_collection/traffic4cast"
CTX = {
    "Madrid": ("t4cmad", f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", 828),
    "Londra": ("t4clon", f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", 774),
    "Melbourne": ("t4cmel", f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", 587),
    "d8/2024": ("d8_2024", f"{GO}/targets_2024_urb_d8.npz", 445),
    "d15/2024": ("d15_2024", f"{GO}/targets_2024_urb_d15.npz", 384),
    "d8/2023": ("d8_2023", f"{GO}/targets_2023_urb_d8.npz", 444),
}
# obiettivo: (prefissi, tag peggiore, tag migliore)
OBIETTIVI = {
    # R2 confronta il modello privo di scambio spaziale con quello ad ADIACENZA
    # APPRESA, non con il grafo dato: la campagna e' `camp_classify`, e
    # `fixdensefix` e' un braccio diverso
    "R2 adiacenza appresa nel denso": (["camp_classify", "fix_classify", "classify"],
                                       "gwn_none", "gwn_adaptive"),
    # i dump del regime severo sulle citta' stanno sotto `sparse_`, senza il
    # prefisso `camp_` dei file di risultato: i due nomi non coincidono
    "R3 grafo dato nel severo": (["fix_sparse", "sparse", "camp_sparse"],
                                 "gwn_none", "gwn_fixed"),
}


def pesi(tp):
    z = np.load(tp, allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float32")


def main() -> int:
    ap = argparse.ArgumentParser(description="effetto della correzione")
    ap.add_argument("--probs", default="replication/probs")
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--semi", type=int, default=5)
    a = ap.parse_args()

    for nome_ob, (pref, tag_a, tag_b) in OBIETTIVI.items():
        print("=" * 92)
        print(nome_ob)
        print("=" * 92)
        print(f"{'contesto':10s} {'stima':>8} " +
              "".join(f"{p:>26}" for p in ("storica (pubblicata)",
                                           "molteplicita' conservate",
                                           "gerarchica")))
        for nome, (sig, tp, K) in CTX.items():
            if not globmod.glob(tp):
                continue
            w = pesi(tp)
            A = B = None
            for p in pref:
                # ricerca in TUTTE le sottocartelle: i dump sono stati spostati
                # dal riordino dell'archivio, e cercare nella sola probs/ ne
                # manca una parte
                sch = f"replication/**/{p}_{sig}_s{{}}.npz"
                da = {s: blocchi(sch.format(s), tag_a, K) for s in range(a.semi)}
                db = {s: blocchi(sch.format(s), tag_b, K) for s in range(a.semi)}
                da = {s: v for s, v in da.items() if v}
                db = {s: v for s, v in db.items() if v}
                if len(da) >= 3 and len(db) >= 3:
                    A, B = prepara(da, w, K), prepara(db, w, K)
                    break
            if A is None:
                print(f"{nome:10s} dump non trovati")
                continue
            nodi = np.unique(list(da.values())[0]["15m"][2])
            riga, st = [], None
            for proc in ("storica", "molteplicita", "gerarchica"):
                r = intervalli(A, B, nodi, K, repliche=a.repliche,
                               procedura=proc)
                if r is None:
                    riga.append(f"{'—':>26}")
                    continue
                st = r["stima"]
                z = "" if r["lo"] * r["hi"] > 0 else " 0"
                riga.append(f"  [{r['lo']:+7.2f};{r['hi']:+7.2f}] ±{r['semiampiezza']:5.2f}{z:>2}")
            print(f"{nome:10s} {st:+7.2f}% " + "".join(riga))
        print()

    print("=" * 92)
    print("  Le colonne con «0» in coda hanno l'intervallo che TOCCA lo zero.")
    print("  Un esito che cambi fra le procedure va dichiarato: la correzione")
    print("  allarga gli intervalli, e alcuni «distinguibile da zero» possono")
    print("  non esserlo piu'.")
    print("\n  I valori pubblicati restano quelli della colonna «storica», con la")
    print("  procedura dichiarata. Le altre due si riportano accanto, non al loro")
    print("  posto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
