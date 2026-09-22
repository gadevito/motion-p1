"""Controllo di dipendenza: alterare le serie dei NAS e vedere che cosa cambia.

Dati SINTETICI con la forma di METR-LA (207 nodi). torch non e' disponibile:
si sostituisce `torch.utils.data.Dataset` con `object`, che e' l'unico uso di
torch nel caricatore.
"""
import sys, types, pickle
import numpy as np, pandas as pd
stub = types.ModuleType("torch"); u = types.ModuleType("torch.utils")
d = types.ModuleType("torch.utils.data"); d.Dataset = object
stub.utils = u; u.data = d
sys.modules.update({"torch": stub, "torch.utils": u, "torch.utils.data": d})
REPO = sys.argv[1] if len(sys.argv) > 1 else "MoGERNN-main"
sys.path.insert(0, REPO)
from data_provider.graph_data_loader import StaticPEMS, DynamicPEMS

rng = np.random.default_rng(0)
T, N = 2000, 207
ts = pd.date_range("2012-03-01", periods=T, freq="5min").values
base = rng.uniform(30, 70, (T, N, 3))
unknown = rng.choice(N, 50, replace=False)                 # VS del primo esperimento
nas = rng.choice(unknown, 20, replace=False)                # NAS scelti fra i VS
known = np.setdiff1d(range(N), unknown)
fs = rng.choice(known, 20, replace=False)
import os; os.makedirs("data/METR-LA", exist_ok=True)
np.save("data/METR-LA/unknown_nodes.npy", unknown)
np.save("data/METR-LA/new_add_nodes.npy", nas)
np.save("data/METR-LA/failed_nodes.npy", fs)

def scrivi(dati, f):
    with open(f, "wb") as h:
        pickle.dump({"time_stamp": ts, "pos_stamp": rng.uniform(0, 1, (N, 2)),
                     "adj": rng.uniform(0, 1, (N, N)), "data": dati}, h)

alterati = base.copy()
T70 = int(0.7 * T)
alterati[:T70, nas, :] += 200.0          # SOLO la storia di training dei NAS
scrivi(base, "orig.pkl"); scrivi(alterati, "alt.pkl")

def carica(cls, f, flag):
    return cls(data_path=f, size=[12, 0, 12], flag=flag, scale=True, freq="min",
               target_features="v", input_features="v", dloader_name="METRLA",
               splits=[0.7, 0.1], step=12,
               unknown_nodes_path="data/METR-LA/unknown_nodes.npy")

print("alterata SOLO la storia dei NAS nel periodo di training (+200)\n")
print(f"{'classe':12s} {'flag':6s} {'media':>10} {'dati':>9} {'nodi':>6}  cambia?")
for cls in (StaticPEMS, DynamicPEMS):
    for flag in ("train", "val", "test"):
        a, b = carica(cls, "orig.pkl", flag), carica(cls, "alt.pkl", flag)
        dm = float(abs(a.mean_ - b.mean_).max())
        dd = float(np.nanmax(abs(a.data - b.data)))
        print(f"{cls.__name__:12s} {flag:6s} {dm:10.4f} {dd:9.4f} "
              f"{a.data.shape[1]:6d}  {'SI' if dm > 0 or dd > 0 else 'no'}")
dyn = carica(DynamicPEMS, "orig.pkl", "train")
print(f"\nDynamicPEMS 'train': NAS fra i nodi di training? "
      f"{set(int(x) for x in nas) <= set(dyn.train_known_nodes)}")
print(f"NAS sottoinsieme dei VS del primo esperimento? "
      f"{set(int(x) for x in nas) <= set(int(x) for x in unknown)}")
