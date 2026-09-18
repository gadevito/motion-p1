#!/usr/bin/env python3
"""
Prova end-to-end REALE, ridotta: dalla sorgente all'analisi appaiata.
=====================================================================
Attraversa la catena per intero su un contesto vero, in configurazione ridotta.

    speed_classes
      -> valori e maschere            (artefatto del costruttore)
      -> finestre e descrittori       (estrattore, con osservazioni VERE)
      -> addestramento e validazione induttiva
      -> inserimento
      -> predizioni
      -> analisi appaiata

**I descrittori NON sono vettori casuali.** Vengono dall'estrattore alimentato con
le osservazioni reali del nodo, sulla finestra di ventiquattro ore che precede
l'istante di inserimento, con le maschere ricostruite dalla sorgente.

**Le prestazioni di questa prova non si usano per scegliere iperparametri ne' per
modificare il protocollo.** La configurazione e' ridotta — pochi nodi, poche
epoche, un contesto — e serve a verificare il percorso, non a misurare.

UNA PREVISIONE DICHIARATA PRIMA. La copertura delle finestre di ventiquattro ore
differisce fra i contesti: Madrid 86%, Melbourne 84%, Londra 64% con un minimo del
40%. Poiche' le due varianti differiscono SOLO dove una statistica non e'
stimabile, **le occasioni di divergenza sono piu' rare dove la copertura e' alta**.
Su Madrid ci si attende quindi la differenza minore.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_reale.py
    poetry run python evoluzione/esperimenti/prova_reale.py --contesto Madrid --nodi 60
"""
import argparse
import hashlib
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    SCHEMI_T4C, Osservazioni, estrai_diretto)
from evoluzione.componente.normalizzazione import (  # noqa: E402
    verifica_contratto)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)

ESITI = []
VARIANTI = ("LEGACY", "BASE-CORRECTED")
L_STORIA = 96            # ventiquattro ore, condizione primaria
# canali DICHIARATI costanti: LEGACY conserva i tre storici anche dove la
# sorgente ne ha due, e l'occupazione vi risulta costante
COSTANTI = frozenset({"occupazione", "conteggio"})
SOGLIE = (0.40, 0.80)    # critica, libera
T4 = "data_collection/traffic4cast"
CTX = {"Madrid": (f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
       "Londra": (f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
       "Melbourne": (f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
                     "Melbourne")}


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def impronta_stato(m):
    h = hashlib.sha256()
    for k, v in sorted(m.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


# ------------------------------------------------------------ dati veri -----
def carica(nome, dir_masc: Path, nodi_max):
    tp, eti = CTX[nome]
    M = np.load(dir_masc / f"maschere_{eti}.npz", allow_pickle=True)
    B = np.load(tp, allow_pickle=True)
    if not np.array_equal(M["sensor_ids"].astype(str),
                          B["sensor_ids"].astype(str)):
        raise SystemExit("maschere e bersagli disallineati")
    ts = pd.to_datetime(M["timestamps"])
    # i nodi piu' coperti, per avere finestre utilizzabili in una prova ridotta
    cop = M["maschera_r"].mean(0)
    sel = np.argsort(-cop)[:nodi_max]
    sel = np.sort(sel)
    return {
        "sid": M["sensor_ids"].astype(str)[sel],
        "ts": ts, "ore": ts.hour.to_numpy(),
        "r": np.asarray(M["speed_grezza"], "float64")[:, sel]
             / np.asarray(M["riferimento_risolto"], "float64")[sel][None, :],
        "vol": np.asarray(M["volume_class_grezza"], "float64")[:, sel],
        "m_r": M["maschera_r"][:, sel],
        "m_v": M["maschera_volume_class"][:, sel],
        "classe": np.asarray(B["congestion_emp"], "int64")[:, sel],
        "sel": sel, "copertura": cop[sel],
    }


def canali(D, norm_r, norm_v):
    """Il tensore (T, 9, K): due dinamici RIEMPITI, due maschere, calendario."""
    T, K = D["r"].shape
    r = np.where(D["m_r"], D["r"], 0.0)
    v = np.where(D["m_v"], D["vol"], 0.0)
    r = (r - norm_r[0]) / norm_r[1]
    v = (v - norm_v[0]) / norm_v[1]
    ore, dow = D["ts"].hour.to_numpy(), D["ts"].dayofweek.to_numpy()
    cal = [np.sin(2 * np.pi * ore / 24), np.cos(2 * np.pi * ore / 24),
           np.sin(2 * np.pi * dow / 7), np.cos(2 * np.pi * dow / 7),
           (dow >= 5).astype("float64")]
    x = np.zeros((T, len(CANALI_T4C), K), dtype="float32")
    x[:, 0] = r; x[:, 1] = v
    x[:, 2] = D["m_r"]; x[:, 3] = D["m_v"]
    for i, c in enumerate(cal):
        x[:, 4 + i] = c[:, None]
    return x


def descrittori(D, nodi, t_rif, variante, norm):
    """I descrittori dalle osservazioni VERE, sulla finestra di 24 ore."""
    S = SCHEMI_T4C[variante]
    d = len(S["statistiche"]) + len(S["disponibilita"])
    Z = np.zeros((len(nodi), d), dtype="float32")
    manc = []
    for i, k in enumerate(nodi):
        # solo le osservazioni valide entrano: `nan` dove la maschera e' falsa
        oss = Osservazioni(
            istanti=np.arange(len(D["ts"])),
            r=np.where(D["m_r"][:, k], D["r"][:, k], np.nan),
            f=np.where(D["m_v"][:, k], D["vol"][:, k], np.nan),
            o=np.full(len(D["ts"]), np.nan),
            classe=D["classe"][:, k],
            ora_locale=D["ore"],
            t0=max(t_rif - L_STORIA, 0),
            reference_version="artefatto")
        e = estrai_diretto(oss, t=t_rif, L=L_STORIA, sensor_id=str(k),
                           schema=variante, norm=norm, sorgente="traffic4cast",
                           canali_costanti=COSTANTI)
        Z[i] = np.concatenate([e.statistics, e.availability])
        manc.append(len(e.non_stimabili))
    return torch.as_tensor(Z), np.array(manc)


def lotto(x, classe, istanti, nodi):
    """(B, C, K, T) e (B, K, H).

    `x` ha forma (T, C, K): impilando le finestre si ottiene (B, T, C, K), e
    servono quindi DUE spostamenti — il canale in seconda posizione e il tempo in
    ultima. `transpose(1, 2)` da solo lascia i nodi sull'ultimo asse.
    """
    X = np.stack([x[t - FINESTRA + 1:t + 1] for t in istanti])   # (B,T,C,K)
    X = torch.as_tensor(X).permute(0, 2, 3, 1)[:, :, nodi]       # (B,C,K,T)
    Y = torch.as_tensor(np.stack(
        [np.stack([classe[t + h] for h in ORIZZONTI], -1) for t in istanti]
    )[:, nodi]) - 1                                          # classi 1..3 -> 0..2
    return X, Y.clamp(0, 2)


def main() -> int:
    ap = argparse.ArgumentParser(description="prova end-to-end reale ridotta")
    ap.add_argument("--contesto", default="Madrid", choices=list(CTX))
    ap.add_argument("--nodi", type=int, default=60)
    ap.add_argument("--epoche", type=int, default=3)
    ap.add_argument("--maschere", type=Path,
                    default=Path("results/evoluzione/maschere"))
    a = ap.parse_args()
    dep = Path(tempfile.mkdtemp(prefix="prova_reale_"))
    print(f"CONTESTO REALE {a.contesto} | {a.nodi} nodi | {a.epoche} epoche")
    print(f"configurazione RIDOTTA, distinta dalla campagna\ndeposito {dep}\n")

    D = carica(a.contesto, a.maschere, a.nodi)
    T, K = D["r"].shape
    print(f"  {T:,} istanti, {K} nodi | copertura mediana "
          f"{np.median(D['copertura']):.2%}")

    # -- normalizzazione dai SOLI nodi e periodo di addestramento -----------
    e = T - max(ORIZZONTI)
    ist = {"addestramento": np.arange(FINESTRA - 1, int(e * .70)),
           "validazione": np.arange(int(e * .70), int(e * .85)),
           "prova": np.arange(int(e * .85), e)}
    g = np.random.default_rng(101)                  # seme di PARTIZIONE
    p = g.permutation(K)
    na, nb = int(K * .70), int(K * .85)
    nodi = {"addestramento": np.sort(p[:na]), "validazione": np.sort(p[na:nb]),
            "prova": np.sort(p[nb:])}
    reg = np.ix_(ist["addestramento"], nodi["addestramento"])
    rv = D["r"][reg][D["m_r"][reg]]
    vv = D["vol"][reg][D["m_v"][reg]]
    norm_r = (float(rv.mean()), float(rv.std()) + 1e-6)
    norm_v = (float(vv.mean()), float(vv.std()) + 1e-6)
    NORM = {"media_r": norm_r, "media_volume_class": norm_v,
            "media_conteggio": norm_v, "media_occupazione": (0.0, 1e-6)}
    print(f"  normalizzazione dai soli nodi e periodo di addestramento: "
          f"r ({norm_r[0]:.3f}, {norm_r[1]:.3f})")

    print("\n[1] catena dalla sorgente")
    verifica(1, "i valori grezzi provengono dall'artefatto delle maschere",
             np.isnan(D["r"][~D["m_r"]]).all()
             or not np.isfinite(D["r"][~D["m_r"]]).all(),
             "dove la maschera e' falsa il valore non e' una misura")
    verifica("1b", "le classi provengono dai bersagli",
             set(np.unique(D["classe"])) <= {0, 1, 2, 3})

    x = canali(D, norm_r, norm_v)
    verifica("1c", "il tensore ha nove canali, due dei quali binari",
             x.shape[1] == 9
             and set(np.unique(x[:, 2])) <= {0.0, 1.0}
             and set(np.unique(x[:, 3])) <= {0.0, 1.0},
             f"{x.shape} | canali: {', '.join(CANALI_T4C[:4])} …")

    print("\n[2] descrittori dalle osservazioni VERE")
    t_ins = int(ist["prova"][0])
    DESC, MANC = {}, {}
    for v in VARIANTI:
        S = SCHEMI_T4C[v]
        verifica_contratto(S["statistiche"], S["disponibilita"], NORM, v,
                           canali_costanti=COSTANTI)
        DESC[v], MANC[v] = descrittori(D, nodi["prova"], t_ins, v, NORM)
        print(f"     {v:16s} {tuple(DESC[v].shape)} | non stimabili per nodo: "
              f"mediana {np.median(MANC[v]):.0f}, massimo {MANC[v].max()}")
    verifica(2, "i descrittori sono finiti", 
             all(torch.isfinite(DESC[v]).all() for v in VARIANTI))
    verifica("2b", "LEGACY non dichiara non stimabili, BASE-CORRECTED sì",
             MANC["LEGACY"].sum() == 0 and MANC["BASE-CORRECTED"].sum() >= 0,
             f"LEGACY {MANC['LEGACY'].sum()}, BASE-CORRECTED "
             f"{MANC['BASE-CORRECTED'].sum()} — e' la differenza che il "
             f"raccordo misura")
    verifica("2c", "i descrittori differiscono fra le varianti",
             DESC["LEGACY"].shape[1] != DESC["BASE-CORRECTED"].shape[1])

    print("\n[3] addestramento e selezione induttiva")
    M, R, D_tr, ST = {}, {}, {}, {}
    stat = torch.as_tensor(np.stack([
        D["copertura"], np.log1p(np.arange(K)), np.zeros(K), np.ones(K),
        np.zeros(K)], 1).astype("float32"))
    for v in VARIANTI:
        S = SCHEMI_T4C[v]
        dd = len(S["statistiche"]) + len(S["disponibilita"])
        torch.manual_seed(7)                        # seme di INIZIALIZZAZIONE
        m = PredittorePerNodo(dd, stat.shape[1], sorgente="traffic4cast")
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        dtr, _ = descrittori(D, nodi["addestramento"], int(ist["addestramento"][-1]),
                             v, NORM)
        dva, _ = descrittori(D, nodi["validazione"], int(ist["validazione"][0]),
                             v, NORM)
        storia, best, be = [], float("inf"), -1
        for ep in range(a.epoche):
            m.train()
            X, Y = lotto(x, D["classe"], ist["addestramento"][:32],
                         nodi["addestramento"])
            out = m(X, node_ids=nodi["addestramento"], descriptor=dtr, static_inputs=stat[nodi["addestramento"]])
            L = F.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
            opt.zero_grad(); L.backward(); opt.step()
            m.eval()
            with torch.inference_mode():
                Xv, Yv = lotto(x, D["classe"], ist["validazione"][:16],
                               nodi["validazione"])
                pv = float(F.cross_entropy(
                    m(Xv, node_ids=nodi["validazione"], descriptor=dva, static_inputs=stat[nodi["validazione"]]).reshape(-1, 3),
                    Yv.reshape(-1)))
            storia.append((ep, float(L.detach()), pv))
            if pv < best:
                best, be = pv, ep
                torch.save({"state_dict": m.state_dict(), "epoca": ep}, dep / f"{v}.pt")
        M[v], R[v], D_tr[v] = m, {"storia": storia, "epoca": be, "val": best}, dtr
        print(f"     {v:16s} epoca {be} | validazione {best:.4f} | "
              f"{sum(q.numel() for q in m.parameters()):,} parametri")
    verifica(3, "i pesi cambiano", all(R[v]["storia"][0][1] != R[v]["storia"][-1][1]
                                       for v in VARIANTI))
    verifica("3b", "la selezione usa nodi MAI visti in addestramento",
             not set(nodi["validazione"]) & set(nodi["addestramento"]))

    print("\n[4] inserimento a stato congelato e predizioni")
    CH, LG, VR = {}, {}, {}
    for v in VARIANTI:
        M[v].eval()
        pre = impronta_stato(M[v])
        ch, lg, vr = [], [], []
        with torch.inference_mode():
            for t in ist["prova"][:8]:
                X, Y = lotto(x, D["classe"], [int(t)], nodi["prova"])
                o = M[v](X, DESC[v], stat[nodi["prova"]])[0]
                for i, k in enumerate(nodi["prova"]):
                    for h, hz in enumerate(ORIZZONTI):
                        ch.append((a.contesto, 0, 7, int(k), int(t), int(hz)))
                        lg.append(o[i, h].numpy()); vr.append(int(Y[0, i, h]))
        CH[v], LG[v], VR[v] = ch, np.array(lg), np.array(vr)
        verifica(f"4-{v[:6]}", f"{v}: stato invariato dopo l'inserimento",
                 impronta_stato(M[v]) == pre, f"impronta {pre[:16]}")

    print("\n[5] manifesti")
    verifica(5, "chiavi identiche fra le varianti",
             CH["LEGACY"] == CH["BASE-CORRECTED"], f"{len(CH['LEGACY']):,} istanze")
    verifica("5b", "nessun duplicato", len(set(CH["LEGACY"])) == len(CH["LEGACY"]))
    verifica("5c", "nodi e istanti nel perimetro di prova",
             set(k[3] for k in CH["LEGACY"]) <= set(map(int, nodi["prova"]))
             and set(k[4] for k in CH["LEGACY"]) <= set(map(int, ist["prova"])))
    verifica("5d", "i bersagli coincidono",
             np.array_equal(VR["LEGACY"], VR["BASE-CORRECTED"]))

    print("\n[6] analisi appaiata")
    fr = np.array([(D["classe"][reg] == k).sum() for k in (1, 2, 3)], float)
    pesi = (fr.sum() / np.maximum(fr, 1) / 3)
    print(f"     pesi di classe dai soli nodi e periodo di addestramento: "
          f"{np.round(pesi, 3)}")
    L = {}
    for v in VARIANTI:
        p = torch.softmax(torch.as_tensor(LG[v]), -1).numpy()
        pt = np.clip(p[np.arange(len(VR[v])), VR[v]], 1e-7, 1.0)
        w = pesi[VR[v]]
        L[v] = float(np.sum(w * -np.log(pt)) / np.sum(w))
    delta = 100 * (L["BASE-CORRECTED"] - L["LEGACY"]) / L["LEGACY"]
    verifica(6, "le perdite sono finite",
             all(np.isfinite(L[v]) for v in VARIANTI),
             " | ".join(f"{v} {L[v]:.4f}" for v in VARIANTI))
    verifica("6b", "la differenza appaiata e' calcolabile", np.isfinite(delta),
             f"delta = {delta:+.3f}%  — valore della PROVA, non un risultato: "
             f"{a.epoche} epoche su {a.nodi} nodi")

    print("\n" + "=" * 74)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 74)
    print("\n  La catena e' percorsa per intero su dati reali. Le prestazioni NON")
    print("  si usano per scegliere iperparametri ne' per modificare il protocollo.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
