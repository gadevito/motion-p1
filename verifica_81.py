"""Verifica dei tre rilievi su §8.1, dai CSV della campagna."""
import pandas as pd, glob, numpy as np

CTX = {"t4cmad":"Madrid","t4clon":"Londra","t4cmel":"Melbourne",
       "d8_2024":"d8/2024","d15_2024":"d15/2024","d8_2023":"d8/2023"}
IDENTITA = ["gwn_adaptive","gwn_none","staeformer","agcrn","gwn_stid"]
FONTE = {"gwn_adaptive":["fix_classify","prec_classify","camp_classify"],
         "gwn_none":["fix_classify","prec_classify","camp_classify"],
         "gwn_stid":["prec_classify"],
         "staeformer":["fixgraph_sota","prec_sota"],
         "agcrn":["fixgraph_rnn","prec_rnn"],
         "dcrnn":["fixgraph_rnn","prec_rnn"],
         "lgb_fair":["lgbristr"]}

def med(m, c, col):
    for p in FONTE[m]:
        v=[]
        for s in range(5):
            f=sorted(glob.glob(f"replication/*/{p}_{c}_s{s}.csv"))
            if not f: break
            d=pd.read_csv(f[0]); q=d[d.model==m]
            if not len(q) or col not in q.columns: break
            v.append(q[col].mean())
        if len(v)>=3: return np.mean(v)
    return None

print("=== 1. PRECISIONE: tabellare contro il MIGLIORE fra i modelli con identita' ===")
print(f"{'contesto':10s} {'tabellare':>10} {'migliore identita':>26} esito")
sup=0
for c,n in CTX.items():
    gb = med("lgb_fair", c, "red_prec")
    best = max(((m, med(m,c,"red_prec")) for m in IDENTITA),
               key=lambda x: x[1] if x[1] else -1)
    if gb is None or best[1] is None: print(f"{n:10s} incompleto"); continue
    e = "tabellare SUPERA" if gb > best[1] else "identita' superiore"
    sup += gb > best[1]
    print(f"{n:10s} {gb:10.4f} {best[0]+' '+f'{best[1]:.4f}':>26} {e}")
print(f"\n   il tabellare supera in {sup} contesti su 6")

print("\n=== 2. MIGLIOR MODELLO CON IDENTITA' per entropia (minore e' meglio) ===")
print(f"{'contesto':10s} " + "".join(f"{m:>14}" for m in IDENTITA) + "   migliore")
for c,n in CTX.items():
    v = {m: med(m,c,"wCE") for m in IDENTITA}
    v = {k:x for k,x in v.items() if x}
    if not v: continue
    b = min(v, key=v.get)
    print(f"{n:10s} " + "".join(f"{v.get(m,float('nan')):14.4f}" for m in IDENTITA)
          + f"   {b}")

print("\n=== 3. RICHIAMO: estremi fra i modelli con identita' ===")
tutti=[]
for c,n in CTX.items():
    v=[med(m,c,"red_recall") for m in IDENTITA]
    v=[x for x in v if x]
    if v: tutti += v; print(f"{n:10s} min {min(v):.3f}  max {max(v):.3f}")
if tutti:
    print(f"\n   fra i sei contesti: {min(tutti):.3f} ÷ {max(tutti):.3f}")
    print(f"   {min(tutti)*10:.1f} e {max(tutti)*10:.1f} episodi su dieci")
