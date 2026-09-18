#!/usr/bin/env python3
"""
Prova mirata al ramo dei MANCANTI.
==================================
La prova end-to-end verifica l'integrazione della catena, ma sui nodi piu' coperti
nessuna statistica risulta non stimabile: **il ramo che tratta i mancanti non viene
percorso**, ed e' il comportamento centrale del raccordo.

LA SELEZIONE NON GUARDA LE PRESTAZIONI. Si scelgono coppie (nodo, istante) la cui
finestra di ventiquattro ore soddisfi tre condizioni verificate DIRETTAMENTE sulle
maschere:

    almeno una banda OSSERVATA
    almeno una banda NON osservata
    osservazioni sufficienti perche' alcune statistiche siano calcolabili

**Una copertura bassa non basta**: le osservazioni potrebbero distribuirsi
sull'intera giornata lasciando tutte le bande popolate. Si verificano quindi le
finestre, non la copertura del nodo.

IL CONTEGGIO DEI NON STIMABILI VIENE ANCHE DALL'ORACOLO. Le bande vuote si contano
direttamente dalla maschera nella finestra, indipendentemente da cio' che
l'estrattore dichiara: se i due non coincidono, e' un difetto dell'estrattore.

NON SI RICHIEDE CHE I VALORI RIEMPITI DIFFERISCANO SEMPRE. Possono coincidere per
caso — LEGACY riempie con la media di addestramento, e una banda osservata puo'
valervi vicina. **Si verifica la rappresentazione della disponibilita'**, che e'
cio' che distingue le due varianti.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_mancanti.py --contesto Madrid
    poetry run python evoluzione/esperimenti/prova_mancanti.py --contesto Londra
    poetry run python evoluzione/esperimenti/prova_mancanti.py --mascheramento
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
    N_BANDE, SCHEMI_T4C, Osservazioni, estrai_diretto)
from evoluzione.componente.predittore import (  # noqa: E402
    FINESTRA, ORIZZONTI, PredittorePerNodo)
from evoluzione.esperimenti.prova_reale import (  # noqa: E402
    COSTANTI, CTX, L_STORIA, canali, impronta_stato, lotto)

ESITI = []
VARIANTI = ("LEGACY", "BASE-CORRECTED")


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def bande_oracolo(m_r, ore, k, t, L=L_STORIA):
    """Conteggio per banda calcolato DIRETTAMENTE dalla maschera.

    Indipendente dall'estrattore: se i due non coincidono, l'estrattore sbaglia.
    """
    a = max(t - L, 0)
    sel = slice(a + 1, t + 1)
    m = m_r[sel, k]
    b = ore[sel] // 3
    n = np.array([int(m[b == j].sum()) for j in range(N_BANDE)])
    att = np.array([int((b == j).sum()) for j in range(N_BANDE)])
    return n, att


def scegli(D, nodi, istanti, quanti, min_oss=20):
    """Coppie (nodo, istante) con almeno una banda vuota e una popolata.

    Il criterio e' sulle MASCHERE, non sulle prestazioni: nessun modello e'
    stato addestrato quando questa scelta avviene.
    """
    scelte = []
    for t in istanti:
        for k in nodi:
            n, att = bande_oracolo(D["m_r"], D["ore"], k, int(t))
            vuote = int(((n == 0) & (att > 0)).sum())
            piene = int((n > 0).sum())
            if vuote >= 1 and piene >= 1 and n.sum() >= min_oss:
                scelte.append({"nodo": int(k), "istante": int(t),
                               "bande_vuote": vuote, "bande_piene": piene,
                               "osservazioni": int(n.sum())})
                if len(scelte) >= quanti:
                    return scelte
    return scelte


def main() -> int:
    ap = argparse.ArgumentParser(description="prova mirata ai mancanti")
    ap.add_argument("--contesto", default="Madrid", choices=list(CTX))
    ap.add_argument("--nodi", type=int, default=120)
    ap.add_argument("--casi", type=int, default=12)
    ap.add_argument("--epoche", type=int, default=2)
    ap.add_argument("--mascheramento", action="store_true",
                    help="se i casi naturali non bastano, ne costruisce di "
                         "artificiali: la prova viene marcata separatamente")
    ap.add_argument("--maschere", type=Path,
                    default=Path("results/evoluzione/maschere"))
    a = ap.parse_args()
    dep = Path(tempfile.mkdtemp(prefix="prova_mancanti_"))

    tp, eti = CTX[a.contesto]
    M = np.load(a.maschere / f"maschere_{eti}.npz", allow_pickle=True)
    B = np.load(tp, allow_pickle=True)
    ts = pd.to_datetime(M["timestamps"])
    cop = M["maschera_r"].mean(0)
    # i MENO coperti, ma la scelta finale e' sulle finestre
    sel = np.sort(np.argsort(cop)[:a.nodi])
    D = {"ts": ts, "ore": ts.hour.to_numpy(),
         "r": np.asarray(M["speed_grezza"], "float64")[:, sel]
              / np.asarray(M["riferimento_risolto"], "float64")[sel][None, :],
         "vol": np.asarray(M["volume_class_grezza"], "float64")[:, sel],
         "m_r": M["maschera_r"][:, sel], "m_v": M["maschera_volume_class"][:, sel],
         "classe": np.asarray(B["congestion_emp"], "int64")[:, sel],
         "copertura": cop[sel]}
    T, K = D["r"].shape
    print(f"MIRATA AI MANCANTI — {a.contesto} | {K} nodi meno coperti | "
          f"{a.epoche} epoche")
    print(f"  copertura dei nodi scelti: mediana {np.median(D['copertura']):.2%}, "
          f"minimo {D['copertura'].min():.2%}\n")

    e = T - max(ORIZZONTI)
    ist_prova = np.arange(int(e * .85), e)
    cand = ist_prova[::max(len(ist_prova) // 60, 1)]

    print("[1] selezione delle finestre, sulle MASCHERE")
    scelte = scegli(D, np.arange(K), cand, a.casi)
    artificiale = False
    if len(scelte) < a.casi and a.mascheramento:
        artificiale = True
        print(f"     casi naturali insufficienti ({len(scelte)}): si aggiunge "
              f"MASCHERAMENTO CONTROLLATO")
        mm = D["m_r"].copy()
        for t in cand[:a.casi]:
            for k in range(min(4, K)):
                s = slice(max(int(t) - L_STORIA, 0), int(t) + 1)
                b = D["ore"][s] // 3
                mm[s, k] &= ~np.isin(b, [2, 5])       # due bande svuotate
        D["m_r"] = mm
        scelte = scegli(D, np.arange(K), cand, a.casi)
    if not scelte:
        print("     nessun caso adeguato e mascheramento non richiesto")
        return 1
    S = pd.DataFrame(scelte)
    print(f"     {len(scelte)} casi | bande vuote: mediana "
          f"{S.bande_vuote.median():.0f}, massimo {S.bande_vuote.max()} | "
          f"osservazioni: mediana {S.osservazioni.median():.0f}")
    print(f"     criterio: ≥1 banda vuota, ≥1 piena, ≥20 osservazioni — "
          f"sulle maschere, senza consultare prestazioni")
    print(f"     nodi {sorted(S.nodo.unique())[:8]}… istanti "
          f"{sorted(S.istante.unique())[:4]}…")
    verifica(1, "esiste almeno una banda non osservata nei casi scelti",
             S.bande_vuote.min() >= 1 and S.bande_piene.min() >= 1,
             "verificato sull'ORACOLO, direttamente dalle maschere"
             + ("  [MASCHERAMENTO CONTROLLATO]" if artificiale else ""))

    # -- normalizzazione dai soli nodi/periodo di addestramento -------------
    ist_tr = np.arange(FINESTRA - 1, int(e * .70))
    g = np.random.default_rng(101)
    p = g.permutation(K); na, nb = int(K * .70), int(K * .85)
    nodi = {"addestramento": np.sort(p[:na]), "validazione": np.sort(p[na:nb]),
            "prova": np.sort(p[nb:])}
    reg = np.ix_(ist_tr, nodi["addestramento"])
    rv = D["r"][reg][D["m_r"][reg]]; vv = D["vol"][reg][D["m_v"][reg]]
    nr = (float(rv.mean()), float(rv.std()) + 1e-6)
    nv = (float(vv.mean()), float(vv.std()) + 1e-6)
    NORM = {"media_r": nr, "media_volume_class": nv,
            "media_conteggio": nv, "media_occupazione": (0.0, 1e-6)}

    print("\n[2] estrattore contro oracolo, sui casi scelti")
    EST = {v: [] for v in VARIANTI}
    concordi = disponibili = riempiti = 0
    for c in scelte:
        k, t = c["nodo"], c["istante"]
        n_or, att = bande_oracolo(D["m_r"], D["ore"], k, t)
        vuote_or = {j for j in range(N_BANDE) if n_or[j] == 0 and att[j] > 0}
        for v in VARIANTI:
            oss = Osservazioni(
                istanti=np.arange(T),
                r=np.where(D["m_r"][:, k], D["r"][:, k], np.nan),
                f=np.where(D["m_v"][:, k], D["vol"][:, k], np.nan),
                o=np.full(T, np.nan), classe=D["classe"][:, k],
                ora_locale=D["ore"], t0=max(t - L_STORIA, 0))
            x = estrai_diretto(oss, t=t, L=L_STORIA, schema=v, norm=NORM,
                               sorgente="traffic4cast", canali_costanti=COSTANTI)
            EST[v].append(x)
        bc = EST["BASE-CORRECTED"][-1]
        vuote_est = {int(n.split("_")[1]) for n in bc.non_stimabili
                     if n.startswith("banda_")}
        concordi += int(vuote_est == vuote_or)
        # BASE-CORRECTED dichiara indisponibile
        q = dict(zip(bc.availability_names_and_order, bc.availability))
        disponibili += int(all(q[f"disponibilita_banda_{j}"] == 0.0
                               for j in vuote_or))
        # LEGACY riempie, e NON dichiara
        lg = EST["LEGACY"][-1]
        riempiti += int(not any(n.startswith("banda_") for n in lg.non_stimabili))
    n = len(scelte)
    verifica(2, "l'estrattore concorda con l'oracolo sulle bande vuote",
             concordi == n, f"{concordi}/{n} casi")
    verifica("2b", "BASE-CORRECTED dichiara indisponibili le bande vuote",
             disponibili == n, f"{disponibili}/{n}: disponibilita' esattamente 0")
    verifica("2c", "LEGACY applica il riempimento e NON dichiara",
             riempiti == n, f"{riempiti}/{n}: nessuna banda fra i non stimabili")

    print("\n[3] le dodici componenti aggiuntive, una per una")
    qn = EST["BASE-CORRECTED"][0].availability_names_and_order
    Q = np.array([x.availability for x in EST["BASE-CORRECTED"]])
    solo_bc = [x for x in qn if x not in ("quota_validi", "codice_durata")]
    print(f"     {'componente':26s} {'minimo':>9} {'massimo':>9} {'distinti':>9}  natura")
    variabili = 0
    for i, nome in enumerate(qn):
        col = Q[:, i]
        u = np.unique(np.round(col, 9))
        bin_ = set(u) <= {0.0, 1.0}
        if len(u) > 1:
            variabili += 1
        print(f"     {nome:26s} {col.min():9.4f} {col.max():9.4f} {len(u):9d}  "
              f"{'binaria' if bin_ else 'numerica'}")
    verifica(3, "non tutte le componenti di disponibilita' valgono uno",
             not np.allclose(Q, 1.0),
             f"{variabili} componenti su {len(qn)} assumono piu' di un valore "
             f"sui casi scelti")
    verifica("3b", "le disponibilita' di banda comprendono lo zero",
             any(Q[:, qn.index(f"disponibilita_banda_{j}")].min() == 0.0
                 for j in range(N_BANDE)))
    # la copertura delle coppie appartiene al blocco CONDIVISO: se restasse a
    # zero su BASE-CORRECTED, le due varianti non lo condividerebbero davvero
    ic = qn.index("copertura_coppie")
    verifica("3c", "la copertura delle coppie e' calcolata, non lasciata a zero",
             Q[:, ic].max() > 0,
             f"intervallo [{Q[:, ic].min():.4f}; {Q[:, ic].max():.4f}] — "
             f"appartiene al blocco condiviso con EXTENDED")
    Qe = np.array([
        estrai_diretto(
            Osservazioni(np.arange(T),
                         np.where(D["m_r"][:, c["nodo"]], D["r"][:, c["nodo"]], np.nan),
                         np.where(D["m_v"][:, c["nodo"]], D["vol"][:, c["nodo"]], np.nan),
                         np.full(T, np.nan), D["classe"][:, c["nodo"]],
                         D["ore"], t0=max(c["istante"] - L_STORIA, 0)),
            t=c["istante"], L=L_STORIA, schema="EXTENDED", norm=NORM,
            sorgente="traffic4cast", canali_costanti=COSTANTI).availability
        for c in scelte])
    ne = SCHEMI_T4C["EXTENDED"]["disponibilita"]
    comuni = [x for x in qn if x in ne]
    verifica("3d", "il blocco di disponibilita' coincide con quello di EXTENDED",
             all(np.allclose(Q[:, qn.index(x)], Qe[:, ne.index(x)], atol=1e-12)
                 for x in comuni),
             f"{len(comuni)} componenti confrontate una per una")

    print("\n[4] nessun valore non finito raggiunge l'encoder")
    DESC = {}
    for v in VARIANTI:
        Z = np.stack([np.concatenate([x.statistics, x.availability])
                      for x in EST[v]]).astype("float32")
        DESC[v] = torch.as_tensor(Z)
        verifica(f"4-{v[:6]}", f"{v}: descrittore finito",
                 bool(torch.isfinite(DESC[v]).all()),
                 f"forma {tuple(DESC[v].shape)}")

    print("\n[5] addestramento, salvataggio, ricarico, inferenza congelata")
    xt = canali(D, nr, nv)
    stat = torch.as_tensor(np.stack([
        D["copertura"], np.zeros(K), np.ones(K), np.zeros(K), np.ones(K)],
        1).astype("float32"))
    nodi_casi = np.array(sorted({c["nodo"] for c in scelte}))
    ist_casi = np.array(sorted({c["istante"] for c in scelte}))
    for v in VARIANTI:
        sch = SCHEMI_T4C[v]
        dd = len(sch["statistiche"]) + len(sch["disponibilita"])
        torch.manual_seed(7)
        m = PredittorePerNodo(dd, stat.shape[1], sorgente="traffic4cast")
        opt = torch.optim.Adam(m.parameters(), lr=1e-3)
        dtr = torch.randn(len(nodi["addestramento"]), dd) * 0.1
        for _ in range(a.epoche):
            m.train()
            X, Y = lotto(xt, D["classe"], ist_tr[:24], nodi["addestramento"])
            L = F.cross_entropy(
                m(X, node_ids=nodi["addestramento"], descriptor=dtr, static_inputs=stat[nodi["addestramento"]]).reshape(-1, 3),
                Y.reshape(-1))
            opt.zero_grad(); L.backward(); opt.step()
        torch.save({"state_dict": m.state_dict()}, dep / f"{v}.pt")
        m.eval(); pre = impronta_stato(m)
        # SUI CASI SCELTI, quelli con bande vuote
        # i descrittori dei casi scelti, tanti quanti i nodi del lotto
        dcasi = DESC[v][:len(nodi_casi)]
        with torch.inference_mode():
            X, _ = lotto(xt, D["classe"], ist_casi[:4], nodi_casi)
            o1 = m(X, node_ids=nodi_casi, descriptor=dcasi, static_inputs=stat[nodi_casi])
        m2 = PredittorePerNodo(dd, stat.shape[1], sorgente="traffic4cast")
        m2.load_state_dict(torch.load(dep / f"{v}.pt",
                                      weights_only=False)["state_dict"])
        m2.eval()
        with torch.inference_mode():
            o2 = m2(X, node_ids=nodi_casi, descriptor=dcasi, static_inputs=stat[nodi_casi])
        verifica(f"5-{v[:6]}", f"{v}: stato invariato sui casi con bande vuote",
                 impronta_stato(m) == pre)
        verifica(f"5-{v[:6]}b", f"{v}: il ricaricato riproduce le predizioni",
                 torch.equal(o1, o2))
        verifica(f"5-{v[:6]}c", f"{v}: uscite finite sui casi con mancanti",
                 bool(torch.isfinite(o1).all()))

    print("\n" + "=" * 74)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate"
          + ("   [con MASCHERAMENTO CONTROLLATO]" if artificiale else ""))
    print("=" * 74)
    print("\n  Il ramo dei mancanti e' percorso su istanze reali del modello.")
    print("  Non si verifica che i valori riempiti differiscano — possono")
    print("  coincidere per caso — ma che la DISPONIBILITA' sia rappresentata.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
