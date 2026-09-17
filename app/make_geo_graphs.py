"""Esperimento GEO — il valore del grafo dipende dalla distanza dei vicini?
Costruisce DUE grafi sintetici sui sensori di Madrid con la stessa regola (k vicini
piu' prossimi oltre un raggio minimo Rmin); l'unico parametro che cambia e' Rmin:
  corto: Rmin=0     -> mediana archi ~scala Madrid (decine di metri)
  lungo: Rmin=250 m -> mediana archi ~scala Melbourne (>=273 m)
Stesso N, stesso grado (k) per costruzione. Da OR3/:
  poetry run python make_geo_graphs.py \
      --sensors data_collection/traffic4cast/MADRID_2022/gomo_fmt/t4cmad_sensors.csv
Output: geo_graph_short.pkl, geo_graph_long.pkl (+ statistiche a video).
"""
import argparse, pickle
import numpy as np, pandas as pd, networkx as nx

ap = argparse.ArgumentParser()
ap.add_argument("--sensors", required=True)
ap.add_argument("--k", type=int, default=4, help="vicini per nodo (grado ~2k non orientato)")
ap.add_argument("--rmin-long", type=float, default=250.0)
ap.add_argument("--out-prefix", default="geo_graph")
args = ap.parse_args()

s = pd.read_csv(args.sensors, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
ids = s["id"].to_numpy(); X = s[["utm_x", "utm_y"]].to_numpy("float64")
N = len(ids)
D = np.sqrt(((X[:, None, :] - X[None, :, :])**2).sum(-1))
np.fill_diagonal(D, np.inf)

def build(rmin, tag):
    G = nx.Graph()
    for i in range(N):
        G.add_node(ids[i], utm_x=float(X[i, 0]), utm_y=float(X[i, 1]))
    for i in range(N):
        cand = np.where(D[i] >= rmin)[0]
        near = cand[np.argsort(D[i][cand])][:args.k]
        for j in near:
            G.add_edge(ids[i], ids[j], weight=float(D[i, j] + 1.0))
    w = [d["weight"] for *_, d in G.edges(data=True)]
    deg = [d for _, d in G.degree()]
    comp = max(nx.connected_components(G), key=len)
    print(f"[{tag}] nodi {G.number_of_nodes()}, archi {G.number_of_edges()}, "
          f"grado medio {np.mean(deg):.2f}, mediana archi {np.median(w):.0f} m, "
          f"componente massima {len(comp)}")
    pickle.dump(G, open(f"{args.out_prefix}_{tag}.pkl", "wb"))

build(0.0, "short")
build(args.rmin_long, "long")
print("\nCriteri pre-registrati (fissati prima dei run):")
print(" sanity:  R3(short) entro ±5 punti da R3(grafo originale, +11,4%)")
print(" test:    geometria CONFERMATA se R3(long) < 10% e R3(short) - R3(long) >= 5 punti;")
print("          SMENTITA se R3(long) resta >= 10% o ~= R3(short).")
