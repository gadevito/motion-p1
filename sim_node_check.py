import numpy as np, pandas as pd
from scipy.stats import spearmanr
CFG=[('Madrid','data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz'),
     ('Londra','data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz'),
     ('Melbourne','data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz')]
for nome,path in CFG:
    z=np.load(path,allow_pickle=True); r=z['r_emp'].astype('float64'); sids=z['sensor_ids'].astype(str)
    T=r.shape[0]; slot=np.arange(T)%672; t_tr=int(T*0.7)
    P=np.full((672,r.shape[1]),np.nan)
    for s in range(672):
        rows=np.where((np.arange(T)<t_tr)&(slot==s))[0]
        if len(rows): P[s]=np.nanmean(r[rows],0)
    city=np.nanmean(P,1)
    a={}
    for k in range(r.shape[1]):
        v=np.isfinite(P[:,k])&np.isfinite(city)
        if v.sum()>100: a[sids[k]]=np.corrcoef(P[v,k],city[v])[0,1]
    d=pd.read_csv(f'placement_{nome}.csv').groupby('sensor_id').agg(rec=('recover','mean'),w0=('w0','mean'))
    d['rel']=d.rec/d.w0; d['a']=d.index.map(a); d=d.dropna(subset=['a'])
    s=spearmanr(d.a,d.rel)
    print(f'{nome}: corr(somiglianza nodo~citta, recupero relativo) rho={s.statistic:+.3f}  p={s.pvalue:.2g}  (n={len(d)})')