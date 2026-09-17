#!/usr/bin/env python3
"""
Caratterizzazione dei grafi delle rotte dei sei contesti (§3.1.2, §3.2.2).
==========================================================================
Produce i numeri riportati nel documento a proposito di:

  * tipo del grafo e orientamento (MultiDiGraph nei contesti a spire,
    Graph non orientato nei tre contesti primari);
  * quota di archi reciproci e ASIMMETRIA RELATIVA fra i due versi, misurata
    come rapporto sulle sole coppie reciproche e sull'attributo che i modelli
    consumano: e' la grandezza che stabilisce se la direzionalita' costituisca
    una protezione effettiva contro la mediazione fra carreggiate opposte, o
    soltanto nominale;
  * ATTRIBUTO DI DISTANZA effettivamente consumato dai modelli.

Quest'ultimo punto e' il piu' importante e va verificato a ogni ripresa
del lavoro. Nei grafi Traffic4cast l'attributo `weight` E' la distanza in
metri (mediana ~60 m). Nel grafo GO-MO `weight` e' invece una SIMILARITA'
gia' normalizzata in [0,01; 1] e decrescente nella distanza, mentre la
distanza in metri sta nell'attributo separato `distance` (mediana ~644 m).
Applicare a `weight` il nucleo gaussiano che i modelli applicano alla
distanza azzera i nodi vicini e conserva i lontani: e' il difetto corretto
dalla patch `_wattr` in `gomo_sparse.py` / `gomo_classify.py`, che sceglie
`distance` dove esiste. Lo script stampa, per ciascun contesto, quale
attributo verrebbe scelto e quanti archi sopravvivono alla trasformazione.

Uso (dalla radice OR3/):

    poetry run python analisi/caratterizza_grafi.py
    poetry run python analisi/caratterizza_grafi.py --contesti t4cmad d8_2024
"""
from pathlib import Path
import argparse
import pickle

import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"

CONTESTI = {
    "d8_2024":  (GOMO / "targets_2024_urb_d8.npz",  GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv", "d8/2024"),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv", "d15/2024"),
    "d8_2023":  (GOMO / "targets_2023_urb_d8.npz",  GOMO / "routes-graph.pkl",
                 GOMO / "traffic_sensors.csv", "d8/2023"),
    "t4cmad":   (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 T4C / "MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 T4C / "MADRID_2022/gomo_fmt/t4cmad_sensors.csv", "Madrid"),
    "t4clon":   (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 T4C / "LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 T4C / "LONDON_2022/gomo_fmt/t4cmad_sensors.csv", "Londra"),
    "t4cmel":   (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                 T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl",
                 T4C / "MELBOURNE_2022/gomo_fmt/t4cmel_sensors.csv", "Melbourne"),
}

RAGGIO_AGGANCIO = 20.0  # metri, come in gomo_sparse.py / gomo_classify.py


def scegli_attributo(g) -> str:
    """Replica la regola della patch `_wattr` dei modelli."""
    campione = list(g.edges(data=True))[:50]
    return "distance" if any("distance" in a for *_, a in campione) else "weight"


def aggancia(g, sensori_csv, sensor_ids):
    """Aggancio nodi->sensori entro 20 m, come nei modelli. Restituisce il
    sottografo sui sensori presenti nei target."""
    s = pd.read_csv(sensori_csv, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    s["id"] = s["id"].astype(str)
    nodi = list(g.nodes)
    if not nodi:
        return g, []
    primo = g.nodes[nodi[0]]
    if "utm_x" not in primo:            # nodi gia' identificativi di sensore
        tenuti = [x for x in sensor_ids if x in g.nodes]
        return g, tenuti
    nxy = np.array([[g.nodes[n]["utm_x"], g.nodes[n]["utm_y"]] for n in nodi])
    d, i = cKDTree(s[["utm_x", "utm_y"]].to_numpy()).query(nxy, k=1)
    mappa = {nodi[k]: s["id"].to_numpy()[i[k]] for k in range(len(nodi))
             if d[k] <= RAGGIO_AGGANCIO}
    rg = nx.relabel_nodes(g, mappa, copy=True)
    tenuti = [x for x in sensor_ids if x in rg.nodes]
    return rg, tenuti


def main() -> int:
    ap = argparse.ArgumentParser(description="caratterizzazione dei grafi delle rotte")
    ap.add_argument("--contesti", nargs="*", default=list(CONTESTI),
                    help="sottoinsieme di contesti da analizzare")
    args = ap.parse_args()

    print("=" * 96)
    print("TIPO, ORIENTAMENTO E ATTRIBUTO DI DISTANZA")
    print("=" * 96)
    print(f"{'contesto':11s} {'tipo':14s} {'nodi':>6} {'archi':>8} {'diretto':>8} "
          f"{'reciproci':>10} {'attributo':>10} {'mediana':>9} {'asimmetria':>20}")

    for nome in args.contesti:
        tp, gp, sp, etichetta = CONTESTI[nome]
        if not gp.exists():
            print(f"{etichetta:11s} grafo non trovato: {gp}")
            continue
        g = pickle.load(open(gp, "rb"))
        attr = scegli_attributo(g)
        w = np.array([a.get(attr, np.nan) for *_, a in g.edges(data=True)], dtype=float)
        asim = "n/a"
        if g.is_directed():
            archi = set((u, v) for u, v in g.edges())
            rec = sum(1 for u, v in archi if (v, u) in archi)
            qrec = f"{100 * rec / max(len(archi), 1):.1f}%"
            # ASIMMETRIA RELATIVA sulle sole coppie reciproche, ciascuna contata
            # una volta. Va misurata come RAPPORTO e non come differenza: su pesi
            # compresi fra 0,01 e 1 una differenza assoluta media restituisce un
            # valore di un ordine di grandezza inferiore, che si presta a essere
            # letto come assenza di asimmetria. E va misurata sull'attributo che i
            # modelli CONSUMANO: sul grafo GO-MO la mediana vale 0,334 su
            # `distance` e 0,115 su `weight`.
            W = {(u, v): float(d[attr]) for u, v, d in g.edges(data=True) if attr in d}
            visti, val = set(), []
            for (u, v) in W:
                if (v, u) not in W or (v, u) in visti:
                    continue
                visti.add((u, v))
                x, y = W[(u, v)], W[(v, u)]
                val.append(abs(x - y) / max(abs(x), abs(y), 1e-12))
            if val:
                val = np.array(val)
                asim = f"{np.median(val):.3f} ({100 * (val > 0.5).mean():.0f}% >50%)"
        else:
            qrec = "n/a"
        print(f"{etichetta:11s} {type(g).__name__:14s} {g.number_of_nodes():6d} "
              f"{g.number_of_edges():8d} {str(g.is_directed()):>8} {qrec:>10} "
              f"{attr:>10} {np.nanmedian(w):8.1f} {asim:>20}")

    print()
    print("=" * 96)
    print("ASIMMETRIA DELLA MATRICE E ARCHI SOPRAVVISSUTI AL NUCLEO GAUSSIANO")
    print("=" * 96)
    print("(la trasformazione replicata qui e' quella dei modelli:")
    print("  Aff = exp(-(D/sd)^2) sugli archi presenti, sd = deviazione standard di D,")
    print("  poi diagonale a 1 e normalizzazione per grado)")
    print()
    print(f"{'contesto':11s} {'sensori':>8} {'archi':>8} {'asimm. media':>13} "
          f"{'asimm. max':>11} {'archi > 0,01':>14} {'fuori/diag':>11}")

    for nome in args.contesti:
        tp, gp, sp, etichetta = CONTESTI[nome]
        if not (gp.exists() and tp.exists() and sp.exists()):
            print(f"{etichetta:11s} file mancanti")
            continue
        z = np.load(tp, allow_pickle=True)
        sids = z["sensor_ids"].astype(str)
        g = pickle.load(open(gp, "rb"))
        attr = scegli_attributo(g)
        rg, tenuti = aggancia(g, sp, sids)
        if not tenuti:
            print(f"{etichetta:11s} nessun sensore agganciato")
            continue
        K = len(tenuti)
        A = nx.to_numpy_array(rg.subgraph(tenuti).copy(), nodelist=tenuti,
                              weight=attr).astype("float32")
        A[A > 0] = np.maximum(A[A > 0], 1.0)   # archi a distanza nulla: sensori coincidenti
        m = A > 0
        if not m.sum():
            print(f"{etichetta:11s} {K:8d} {0:8d}  sottografo senza archi")
            continue
        asim = np.abs(A - A.T)
        sd = A[m].std()
        aff = np.where(m, np.exp(-((A / max(sd, 1e-9)) ** 2)), 0.0)
        np.fill_diagonal(aff, 0.0)
        aff2 = aff + np.eye(K, dtype="float32")
        fuori = aff2 - np.diag(np.diag(aff2))
        print(f"{etichetta:11s} {K:8d} {int(m.sum()):8d} {asim.mean():13.5f} "
              f"{asim.max():11.3f} {int((aff > 0.01).sum()):8d} "
              f"({100 * (aff > 0.01).sum() / m.sum():3.0f}%) "
              f"{fuori.sum() / np.trace(aff2):11.4f}")

    print()
    print("Lettura. Una quota di archi sopravvissuti prossima a zero segnala che")
    print("l'attributo scelto NON e' una distanza in metri: e' il sintomo del difetto")
    print("corretto dalla patch `_wattr`. Sui contesti a spire attesi ~78-85%, sui")
    print("contesti primari ~88-91%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
