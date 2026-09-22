import sys, types, pickle
import numpy as np, pandas as pd
stub = types.ModuleType("torch"); u = types.ModuleType("torch.utils")
d = types.ModuleType("torch.utils.data"); d.Dataset = object
stub.utils = u; u.data = d
sys.modules.update({"torch": stub, "torch.utils": u, "torch.utils.data": d})
REPO = sys.argv[1] if len(sys.argv) > 1 else "MoGERNN-main"
sys.path.insert(0, REPO)
from data_provider.graph_data_loader import DynamicPEMS

T = 2000
ts = pd.date_range("2012-03-01", periods=T, freq="5min")
nas = np.load("data/METR-LA/new_add_nodes.npy")
unk = np.load("data/METR-LA/unknown_nodes.npy")
vs = [int(x) for x in unk if x not in set(nas)]
fs = np.load("data/METR-LA/failed_nodes.npy")
ds = DynamicPEMS(data_path="orig.pkl", size=[12, 0, 12], flag="test", scale=True,
                 freq="min", target_features="v", input_features="v",
                 dloader_name="METRLA", splits=[0.7, 0.1], step=12,
                 unknown_nodes_path="data/METR-LA/unknown_nodes.npy")
inizio = int(0.7 * T) + 12        # righe 312 e 317: taglio al 70%, poi input_len
n, v, f = int(nas[0]), vs[0], int(fs[0])
for k in (0, 1):
    x, y, _, _ = ds.__getitem__(k)
    a = inizio + k * 12
    print(f"ORIGINE {k}  (step 12)")
    print(f"  ingressi  {ts[a]} -> {ts[a+11]}   12 passi, 1 ora, solo velocita'")
    print(f"  bersagli  {ts[a+12]} -> {ts[a+23]}")
    print(f"  NAS {n:3d}: ingressi osservati {int((~np.isnan(x[:, n, 0])).sum())}/12")
    print(f"  VS  {v:3d}: ingressi osservati {int((~np.isnan(x[:, v, 0])).sum())}/12")
    print(f"  FS  {f:3d}: ingressi osservati {int((~np.isnan(x[:, f, 0])).sum())}/12")
    print()
print(f"inizio del periodo di training: {ts[0]}, fine {ts[int(0.7*T)-1]}")
print(f"primo ingresso del NAS in test: {ts[inizio]}  -> nessun t0 dichiarato,")
print(f"nessun periodo di acquisizione: il NAS e' osservato dalla prima origine.")
