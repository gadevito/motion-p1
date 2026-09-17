"""Sweep geometrico: decimazione a grado costante, sotto-aree compatte, controlli negativi.
Genera i grafi e il CSV delle covariate (spaziatura realizzata e connettivita per grafo).
Da OR3/:
  poetry run python make_geo_sweep.py --sensors <csv> --targets <npz> --citta madrid
"""
import argparse, pickle, numpy as np, pandas as pd, networkx as nx
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("--sensors", required=True)
ap.add_argument("--targets", required=True)
ap.add_argument("--citta", required=True)
ap.add_argument("--k", type=int, default=4)
ap.add_argument("--out-dir", default="geo_sweep")
ap.add_argument("--sweep", action="store_true", help="genera anche lo sweep di decimazione")
ap.add_argument("--compact-n", type=int, default=99, help="N del blocco a pari numero di nodi")
args = ap.parse_args()

import os; os.makedirs(args.out_dir, exist_ok=True)
ids_t = [str(x) for x in np.load(args.targets, allow_pickle=True)["sensor_ids"]]
s = pd.read_csv(args.sensors, dtype={"id":"string"}).dropna(subset=["utm_x","utm_y"])
s["id"] = s["id"].astype(str); s = s[s.id.isin(ids_t)]
ids = s["id"].to_numpy(); X = s[["utm_x","utm_y"]].to_numpy("float64")
print(f"{args.citta}: {len(ids)} sensori agganciabili")

def costruisci(sel, tag, modo="knn"):
    sub_ids, sub_X = ids[sel], X[sel]
    n = len(sel); k = min(args.k, n-1)
    G = nx.Graph()
    for i in range(n): G.add_node(sub_ids[i], utm_x=float(sub_X[i,0]), utm_y=float(sub_X[i,1]))
    D = np.sqrt(((sub_X[:,None,:]-sub_X[None,:,:])**2).sum(-1)); np.fill_diagonal(D, np.inf)
    if modo == "knn":
        for i in range(n):
            for j in np.argsort(D[i])[:k]:
                G.add_edge(sub_ids[i], sub_ids[j], weight=float(D[i,j]+1.0))
    elif modo == "casuale":                      # stesso NUMERO DI ARCHI, coppie casuali
        rng = np.random.default_rng(0); H = nx.Graph()
        for i in range(n):
            for j in np.argsort(D[i])[:k]: H.add_edge(i, j)
        while G.number_of_edges() < H.number_of_edges():
            i, j = int(rng.integers(n)), int(rng.integers(n))
            if i != j: G.add_edge(sub_ids[i], sub_ids[j], weight=float(D[i,j]+1.0))
    elif modo == "randomizzato":                 # stesso numero di archi, coppie casuali
        rng = np.random.default_rng(0); H = nx.Graph()
        for i in range(n):
            for j in np.argsort(D[i])[:k]: H.add_edge(i, j)
        while G.number_of_edges() < H.number_of_edges():
            a, b = int(rng.integers(n)), int(rng.integers(n))
            if a != b: G.add_edge(sub_ids[a], sub_ids[b], weight=float(D[a, b] + 1.0))
    w = np.array([d["weight"]-1.0 for *_, d in G.edges(data=True)])
    gig = max(len(c) for c in nx.connected_components(G))
    pickle.dump(G, open(f"{args.out_dir}/{args.citta}_{tag}.pkl","wb"))
    return {"citta":args.citta, "grafo":tag, "modo":modo, "N":n, "k":k,
            "archi":G.number_of_edges(), "grado_medio":2*G.number_of_edges()/n,
            "arco_medio":w.mean(), "arco_mediano":float(np.median(w)),
            "arco_p90":float(np.percentile(w,90)), "arco_sd":w.std(),
            "comp_gigante":gig, "frac_gigante":gig/n}

righe = []
rng = np.random.default_rng(0)
if args.sweep:                                           # sweep di decimazione (solo Melbourne)
    for liv in (1,2,6):
        sel = rng.permutation(len(ids))[:len(ids)//liv] if liv > 1 else np.arange(len(ids))
        righe.append(costruisci(np.sort(sel), f"dec{liv}"))
for qx in (20, 50, 80):                                  # blocco compatto: 9 posizioni, N comune
    for qy in (20, 50, 80):
        c = np.array([np.percentile(X[:,0],qx), np.percentile(X[:,1],qy)])
        sel = np.sort(np.argsort(((X-c)**2).sum(1))[:args.compact_n])
        righe.append(costruisci(sel, f"comp_q{qx}{qy}"))
# controllo negativo: permutato agli estremi del braccio principale, a connettivita piena
#   Madrid  q20/80 ~36 m  (piu denso, controllo di potenza)
#   Melbourne q50/80 ~350 m (piu rado a connettivita piena; q80/80 e a 370 m ma gigante 0,56)
_qneg = (20, 80) if args.citta == "madrid" else (50, 80)
c = np.array([np.percentile(X[:,0],_qneg[0]), np.percentile(X[:,1],_qneg[1])])
sel = np.sort(np.argsort(((X-c)**2).sum(1))[:args.compact_n])
righe.append(costruisci(sel, f"neg_rand_q{_qneg[0]}{_qneg[1]}", modo="randomizzato"))

d = pd.DataFrame(righe)
d.to_csv(f"{args.out_dir}/covariate_{args.citta}.csv", index=False)
print(d[["grafo","N","grado_medio","arco_medio","arco_mediano","frac_gigante"]].round(2).to_string(index=False))
