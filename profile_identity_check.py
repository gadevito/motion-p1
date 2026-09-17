"""Identita' di livello o di forma? E quanto e' stazionaria?
Per ogni citta', per ogni nodo, dal solo 70% di addestramento:
 (a) corr(profilo settimanale del nodo, profilo medio cittadino)  -> alta = identita' di LIVELLO
 (b) corr split-half (profilo 1a meta' vs 2a meta' del train)      -> bassa = identita' NON STAZIONARIA
Criteri (fissati prima di guardare): l'ipotesi 'Melbourne di forma/non stazionaria' e' supportata
se la mediana di (b) a Melbourne e' inferiore di >=0,10 a quella di Madrid E Londra; idem come
indizio secondario per (a). Altrimenti e' smentita."""
import numpy as np, pandas as pd

CFG = [("Madrid","data_collection/traffic4cast/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz"),
       ("Londra","data_collection/traffic4cast/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz"),
       ("Melbourne","data_collection/traffic4cast/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz")]

def profili(r, slot, mask):
    """profilo 672 momenti-tipo per nodo, sui soli istanti in mask"""
    P = np.full((672, r.shape[1]), np.nan)
    for s in range(672):
        rows = np.where(mask & (slot == s))[0]
        if len(rows): 
            with np.errstate(invalid="ignore"): P[s] = np.nanmean(r[rows], 0)
    return P

def corr_cols(A, B):
    out = np.full(A.shape[1], np.nan)
    for k in range(A.shape[1]):
        v = np.isfinite(A[:,k]) & np.isfinite(B[:,k])
        if v.sum() > 100: out[k] = np.corrcoef(A[v,k], B[v,k])[0,1]
    return out

print(f"{'citta':<10} {'(a) nodo~citta mediana':>24} {'(b) split-half mediana':>24}")
for nome, path in CFG:
    z = np.load(path, allow_pickle=True)
    r = z["r_emp"].astype("float64"); T = r.shape[0]
    slot = np.arange(T) % 672
    t_tr = int(T*0.7); train = np.arange(T) < t_tr
    Pfull = profili(r, slot, train)
    city = np.nanmean(Pfull, 1, keepdims=True) * np.ones((1, r.shape[1]))
    a = corr_cols(Pfull, city)
    h1 = profili(r, slot, train & (np.arange(T) < t_tr//2))
    h2 = profili(r, slot, train & (np.arange(T) >= t_tr//2))
    b = corr_cols(h1, h2)
    print(f"{nome:<10} {np.nanmedian(a):>20.3f} ({np.nanquantile(a,.25):.2f}–{np.nanquantile(a,.75):.2f})"
          f" {np.nanmedian(b):>16.3f} ({np.nanquantile(b,.25):.2f}–{np.nanquantile(b,.75):.2f})")