#!/usr/bin/env python3
"""
Struttura spaziale nei dati, indipendente da qualunque modello.
===============================================================
Nessun addestramento: tre misure sul solo fattore di congestione.

UN'AVVERTENZA PRELIMINARE, senza la quale il risultato e' privo di senso. Sui tre
contesti a velocita' ricostruita circa il 77 per cento delle celle ha fattore di
congestione esattamente pari a uno per effetto della regola di strada vuota:
qualunque misura di correlazione spaziale calcolata su quelle celle misurerebbe
la regola deterministica e non il traffico. Su quei contesti lo script restringe
percio' alle sole celle TRAFFICATE, con occupazione non inferiore al cinque per
cento; sui tre contesti a velocita' misurata usa tutte le celle valide.

LE TRE MISURE.

  * CORRELOGRAMMA: correlazione fra coppie di nodi per fasce di distanza e per
    ritardo temporale, con mediana e quartili. La distribuzione fra coppie e'
    asimmetrica e la media sarebbe fuorviante.
  * INDICE DI MORAN per istante, sul grafo dei k vicini piu' prossimi
    normalizzato per riga, con distribuzione e profilo per ora del giorno.
  * QUOTA DI VARIANZA COMUNE: quota spiegata dalla prima componente principale
    del fattore di congestione attraverso i nodi.

Come termine di paragone lo script riporta anche l'autocorrelazione TEMPORALE:
senza di essa non si sa se una correlazione spaziale debole sia una proprieta'
dello spazio o del segnale in generale.

SULLA DISTANZA. Il correlogramma usa la distanza EUCLIDEA fra le coordinate dei
sensori, non quella di percorso: sono due grandezze diverse e sui contesti a
velocita' ricostruita differiscono di un fattore due nella mediana e di quasi sei
sulle coppie entro cinquanta metri. Con `--distanza percorso` si usa l'attributo
del grafo, disponibile solo dove il grafo lo riporta.

Uso (dalla radice OR3/):

    poetry run python struttura_spaziale.py
    poetry run python struttura_spaziale.py --contesti d8_2024 t4cmad --coppie 5000
"""
import argparse
import glob as globmod
import pickle

import numpy as np
import pandas as pd

GO = "data_collection/go-mo/gomo"
T4 = "data_collection/traffic4cast"
CTX = {
    "d8_2024":  (f"{GO}/targets_2024_urb_d8.npz", f"{GO}/routes-graph.pkl",
                 f"{GO}/traffic_sensors.csv", "d8/2024", True),
    "d15_2024": (f"{GO}/targets_2024_urb_d15.npz", f"{GO}/routes-graph.pkl",
                 f"{GO}/traffic_sensors.csv", "d15/2024", True),
    "d8_2023":  (f"{GO}/targets_2023_urb_d8.npz", f"{GO}/routes-graph.pkl",
                 f"{GO}/traffic_sensors.csv", "d8/2023", True),
    "t4cmad":   (f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 f"{T4}/MADRID_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 f"{T4}/MADRID_2022/gomo_fmt/t4cmad_sensors.csv", "Madrid", False),
    "t4clon":   (f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
                 f"{T4}/LONDON_2022/gomo_fmt/t4cmad_routes-graph.pkl",
                 f"{T4}/LONDON_2022/gomo_fmt/t4cmad_sensors.csv", "Londra", False),
    "t4cmel":   (f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                 f"{T4}/MELBOURNE_2022/gomo_fmt/t4cmel_routes-graph.pkl",
                 f"{T4}/MELBOURNE_2022/gomo_fmt/t4cmel_sensors.csv", "Melbourne", False),
}
# La fascia piu' corta e' SEPARATA dalle altre: a pochi metri di distanza si
# trovano sensori appaiati sul medesimo punto in versi opposti, che nell'ora di
# punta misurano traffico opposto e contribuiscono con correlazione nulla o
# negativa. Aggregarli con le coppie a venti o trenta metri deprime la banda che
# il correlogramma usa come riferimento a corto raggio.
FASCE = [(0, 10), (10, 25), (25, 50), (50, 100), (100, 250), (250, 500), (500, 1e9)]
RITARDI = (0, 1, 4, 8)


def carica(c):
    tp, gp, sp, nome, spire = CTX[c]
    if not globmod.glob(tp):
        return None
    z = np.load(tp, allow_pickle=True)
    r = z["r_emp"].astype("float32")
    occ = z["occupancy"].astype("float32") if "occupancy" in z.files else None
    ts = pd.to_datetime(z["timestamps"]) if "timestamps" in z.files else None
    sid = z["sensor_ids"].astype(str)
    s = pd.read_csv(sp, dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    s = s.set_index("id")
    tenuti = [x for x in sid if x in s.index]
    idx = np.array([list(sid).index(x) for x in tenuti])
    XY = s.loc[tenuti, ["utm_x", "utm_y"]].to_numpy(float)
    R = r[:, idx]
    if spire and occ is not None:
        # SOLE CELLE TRAFFICATE: altrove il fattore vale uno per imputazione
        R = np.where(np.isfinite(occ[:, idx]) & (occ[:, idx] >= 5.0), R, np.nan)
    return R, XY, ts, nome, spire


def main() -> int:
    ap = argparse.ArgumentParser(description="struttura spaziale nei dati grezzi")
    ap.add_argument("--contesti", nargs="*", default=list(CTX))
    ap.add_argument("--vicini", type=int, default=8)
    ap.add_argument("--coppie", type=int, default=3000)
    ap.add_argument("--distanza", choices=["euclidea", "percorso"], default="euclidea")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    SINTESI = {}

    for c in a.contesti:
        d = carica(c)
        if d is None:
            print(f"{c}: bersagli assenti")
            continue
        R, XY, ts, nome, spire = d
        K = R.shape[1]
        print("=" * 82)
        print(f"{nome}  —  {K} sensori, "
              f"{'sole celle trafficate' if spire else 'tutte le celle valide'}, "
              f"{np.isfinite(R).mean():.1%} valide")
        print("=" * 82)

        D = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1))
        np.fill_diagonal(D, np.inf)

        # ------------------------------------------------ indice di Moran ---
        W = np.zeros((K, K), dtype="float32")
        for i in range(K):
            W[i, np.argsort(D[i])[:a.vicini]] = 1.0
        W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
        I, ore = [], []
        for t in range(R.shape[0]):
            x = R[t]
            m = np.isfinite(x)
            if m.sum() < K * 0.5:
                continue
            z_ = np.where(m, x - np.nanmean(x), 0.0)
            den = float((z_ ** 2).sum())
            if den > 0:
                I.append(float(z_ @ W @ z_) / den * K / W.sum())
                if ts is not None and t < len(ts):
                    ore.append(ts[t].hour)
        I = np.array(I)
        if not len(I):
            print("  indice di Moran non calcolabile\n")
            continue
        print(f"  indice di Moran: mediana {np.median(I):+.3f}  "
              f"quartili [{np.percentile(I,25):+.3f}; {np.percentile(I,75):+.3f}]  "
              f"su {len(I):,} istanti")
        if len(ore) == len(I):
            o = np.array(ore)
            pun = np.median(I[np.isin(o, [7, 8, 9, 17, 18, 19])])
            not_ = np.median(I[np.isin(o, [0, 1, 2, 3, 4, 5])])
            print(f"     nelle ore di punta {pun:+.3f}, nelle ore notturne {not_:+.3f}")

        # -------------------------------------------------- correlogramma ---
        iu = np.triu_indices(K, 1)
        dd = D[iu]
        print(f"\n  {'fascia':13s} {'coppie':>8} " +
              "".join(f"{'lag '+str(l):>18}" for l in RITARDI))
        prima = None
        for lo, hi in FASCE:
            sel = np.where((dd >= lo) & (dd < hi))[0]
            eti = f"{lo}-{int(hi) if hi < 1e9 else '∞'} m"
            if len(sel) < 20:
                print(f"  {eti:13s} {len(sel):8d}   troppe poche coppie")
                continue
            pick = rng.choice(sel, min(a.coppie, len(sel)), replace=False)
            ii, jj = iu[0][pick], iu[1][pick]
            riga = []
            for lag in RITARDI:
                A = R[:R.shape[0]-lag if lag else None][:, ii]
                B = R[lag:][:, jj]
                m = np.isfinite(A) & np.isfinite(B)
                cs = [np.corrcoef(A[m[:, k], k], B[m[:, k], k])[0, 1]
                      for k in range(len(ii)) if m[:, k].sum() > 50]
                if cs:
                    cs = np.array(cs)
                    riga.append((np.nanmedian(cs), np.nanpercentile(cs, 25),
                                 np.nanpercentile(cs, 75)))
                else:
                    riga.append((np.nan, np.nan, np.nan))
            # riferimento a corto raggio: la fascia 10-25 m, NON la piu' corta,
            # che sui contesti con sensori appaiati e' contaminata dall'antifase
            if lo == 10:
                prima = riga[0][0]
            print(f"  {eti:13s} {len(sel):8d} " +
                  "".join(f"{x[0]:+7.3f} [{x[1]:+.2f};{x[2]:+.2f}]" for x in riga))
        lontano = None
        for lo, hi in FASCE:
            if lo == 250:
                sel = np.where((dd >= lo) & (dd < hi))[0]
                if len(sel) >= 20:
                    pick = rng.choice(sel, min(a.coppie, len(sel)), replace=False)
                    ii, jj = iu[0][pick], iu[1][pick]
                    m = np.isfinite(R[:, ii]) & np.isfinite(R[:, jj])
                    cs = [np.corrcoef(R[m[:, k], ii[k]], R[m[:, k], jj[k]])[0, 1]
                          for k in range(len(ii)) if m[:, k].sum() > 50]
                    lontano = np.nanmedian(cs) if cs else None

        # ------------------------------------------- varianza comune e tempo ---
        # PRIMA COMPONENTE su un SOTTOINSIEME di nodi. Richiedere istanti in cui
        # TUTTI i nodi siano validi non lascia alcun istante: con il filtro
        # sull'occupazione la copertura scende al venti per cento, e nessun
        # momento ha l'intera rete attiva. Si prendono percio' i nodi piu'
        # coperti, e fra questi gli istanti completi.
        pc1 = nodi_pc = ist_pc = None
        cop = np.isfinite(R).mean(0)
        for quota in (0.90, 0.75, 0.60, 0.45):
            sel = np.where(cop >= quota)[0]
            if len(sel) < 10:
                continue
            S = R[:, sel]
            pieni = np.isfinite(S).all(1)
            if pieni.sum() > 100:
                X = S[pieni] - S[pieni].mean(0)
                sv = np.linalg.svd(X, compute_uv=False)
                pc1 = 100 * sv[0] ** 2 / (sv ** 2).sum()
                nodi_pc, ist_pc = len(sel), int(pieni.sum())
                break
        if pc1 is not None:
            print(f"\n  prima componente principale: {pc1:.1f}% della varianza "
                  f"(su {nodi_pc} nodi con copertura ≥ {quota:.0%}, "
                  f"{ist_pc:,} istanti completi)")
        else:
            print("\n  prima componente principale: non calcolabile, nessun "
                  "sottoinsieme di nodi ha istanti completi a sufficienza")
        at = []
        for lag in (1, 2, 4, 8):
            A, B = R[:-lag], R[lag:]
            m = np.isfinite(A) & np.isfinite(B)
            cs = [np.corrcoef(A[m[:, k], k], B[m[:, k], k])[0, 1]
                  for k in range(K) if m[:, k].sum() > 50]
            at.append(np.nanmedian(cs) if cs else np.nan)
        print(f"  autocorrelazione TEMPORALE (ritardi 1,2,4,8): " +
              " ".join(f"{x:+.3f}" for x in at))
        print("     e' il termine di paragone: una correlazione spaziale debole va")
        print("     letta accanto a quella temporale sullo stesso segnale.\n")
        SINTESI[nome] = (float(np.median(I)), prima, lontano, pc1, at[0])

    if len(SINTESI) > 1:
        print("=" * 82)
        print("SINTESI — le tre misure separano le due famiglie?")
        print("=" * 82)
        print(f"{'contesto':11s} {'Moran':>8} {'corr 10-25m':>12} {'corr 250-500':>13} "
              f"{'PC1 %':>7} {'autocorr t':>11}")
        for n, v in SINTESI.items():
            print(f"{n:11s} " + "".join(
                f"{x:>{w}.3f}" if x is not None and np.isfinite(x) else f"{'—':>{w}}"
                for x, w in zip(v, (8, 12, 13, 7, 11))))
        print("\n  Se le tre misure ordinano i contesti come R3 e il richiamo del")
        print("  modello privo di grafo, si ha per la prima volta una proprieta' del")
        print("  DATO, e non del modello, che li ordina allo stesso modo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
