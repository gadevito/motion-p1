#!/usr/bin/env python3
"""
Prova tecnica end-to-end, ridotta.
==================================
Verifica il PERCORSO SOFTWARE, non le prestazioni.

> **Le prestazioni di questa prova non si usano per scegliere iperparametri ne'
> per modificare il protocollo.** La configurazione e' deliberatamente ridotta e
> distinta dalla campagna: pochi nodi, poche epoche, un contesto.

I SEI CONTROLLI:

    1. esclusione effettiva dei nodi di prova dall'addestramento;
    2. aggiornamento dei pesi e selezione del punto di controllo;
    3. inserimento e inferenza a stato CONGELATO;
    4. salvataggio e ricaricamento del punto di controllo;
    5. manifesti e identita' delle chiavi delle predizioni;
    6. ricalcolo delle metriche e analisi appaiata.

CIASCUN CONTROLLO E' BLOCCANTE. Un manifesto che non corrisponda ferma l'analisi
anziche' produrre un avviso: e' il requisito che impedisce alla campagna nuova di
ereditare l'incertezza sul perimetro dei dump storici.

LE DUE VARIANTI del raccordo — LEGACY a 16 e BASE-CORRECTED a 26 — girano
entrambe, con le medesime partizioni e i medesimi semi, perche' il confronto e'
APPAIATO.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_end_to_end.py
    poetry run python evoluzione/esperimenti/prova_end_to_end.py --nodi 60 --epoche 3
"""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.encoder import inventario_per_nodo  # noqa: E402
from evoluzione.componente.estrattore import SCHEMI_T4C  # noqa: E402
from evoluzione.componente.normalizzazione import (  # noqa: E402
    verifica_contratto)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)

ESITI = []
VARIANTI = ("LEGACY", "BASE-CORRECTED")


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


# --------------------------------------------------------------- dati -------
def genera(K, T, seme):
    """Dati sintetici: la prova verifica il percorso, non la previsione."""
    g = np.random.default_rng(seme)
    x = g.normal(0, 1, (T, len(CANALI_T4C), K)).astype("float32")
    # le due maschere sono binarie, come nel dato vero
    x[:, 2] = (g.random((T, K)) > 0.2).astype("float32")
    x[:, 3] = (g.random((T, K)) > 0.3).astype("float32")
    y = g.integers(0, 3, (T, K, len(ORIZZONTI)))
    return x, y


def partizione(K, seme_partizione):
    """70/15/15 sui NODI, con seme SEPARATO da quello di inizializzazione."""
    g = np.random.default_rng(seme_partizione)
    p = g.permutation(K)
    a, b = int(K * 0.70), int(K * 0.85)
    return {"addestramento": np.sort(p[:a]), "validazione": np.sort(p[a:b]),
            "prova": np.sort(p[b:])}


def finestre(T, quota=(0.70, 0.85)):
    """70/15/15 CRONOLOGICO. Un esempio appartiene a una partizione solo se
    TUTTI i suoi bersagli vi ricadono: si sottrae l'orizzonte massimo."""
    omax = max(ORIZZONTI)
    utili = np.arange(FINESTRA - 1, T - omax)
    a, b = int(len(utili) * quota[0]), int(len(utili) * quota[1])
    return {"addestramento": utili[:a], "validazione": utili[a:b],
            "prova": utili[b:]}


def lotto(x, y, istanti, nodi):
    X = np.stack([x[t - FINESTRA + 1:t + 1] for t in istanti])   # (B,T,C,K)
    X = torch.as_tensor(X).permute(0, 2, 3, 1)[:, :, nodi]       # (B,C,K,T)
    Y = torch.as_tensor(np.stack([y[t] for t in istanti])[:, nodi])
    return X, Y


# ----------------------------------------------------- addestramento --------
def addestra(variante, x, y, nodi, ist, d_stat, semi, epoche, dep: Path):
    """Restituisce (modello, registro dell'addestramento, percorso salvato)."""
    S = SCHEMI_T4C[variante]
    d_desc = len(S["statistiche"]) + len(S["disponibilita"])
    torch.manual_seed(semi["inizializzazione"])
    m = PredittorePerNodo(d_desc, d_stat, sorgente="traffic4cast")
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    g = np.random.default_rng(semi["inizializzazione"])
    desc = torch.as_tensor(g.normal(0, 1, (x.shape[2], d_desc)).astype("float32"))
    stat = torch.as_tensor(g.normal(0, 1, (x.shape[2], d_stat)).astype("float32"))

    storia, migliore, epoca_migliore = [], float("inf"), -1
    salvato = dep / f"{variante}.pt"
    for e in range(epoche):
        m.train()
        X, Y = lotto(x, y, ist["addestramento"][:24], nodi["addestramento"])
        out = m(X, node_ids=nodi["addestramento"],
                descriptor=desc[nodi["addestramento"]],
                static_inputs=stat[nodi["addestramento"]])
        perdita = F.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
        opt.zero_grad(); perdita.backward(); opt.step()
        # selezione sulla VALIDAZIONE INDUTTIVA: nodi mai visti
        m.eval()
        with torch.inference_mode():
            Xv, Yv = lotto(x, y, ist["validazione"][:12], nodi["validazione"])
            pv = float(F.cross_entropy(
                m(Xv, node_ids=nodi["validazione"],
                  descriptor=desc[nodi["validazione"]],
                  static_inputs=stat[nodi["validazione"]]).reshape(-1, 3),
                Yv.reshape(-1)))
        storia.append({"epoca": e, "addestramento": float(perdita.detach()),
                       "validazione": pv})
        # a parita', la PRIMA
        if pv < migliore:
            migliore, epoca_migliore = pv, e
            torch.save({"state_dict": m.state_dict(), "epoca": e,
                        "validazione": pv, "variante": variante,
                        "d_descrittore": d_desc}, salvato)
    return m, {"storia": storia, "epoca_scelta": epoca_migliore,
               "validazione_scelta": migliore, "d_descrittore": d_desc,
               "parametri": sum(p.numel() for p in m.parameters())}, salvato, desc, stat


def predici(m, x, y, ist, nodi, desc, stat, contesto, partizione_id, seme):
    """Predizioni con CHIAVE completa, a stato congelato."""
    m.eval()
    chiavi, logit, veri = [], [], []
    with torch.inference_mode():
        for t in ist:
            X, Y = lotto(x, y, [t], nodi)
            out = m(X, node_ids=nodi, descriptor=desc[nodi],
                    static_inputs=stat[nodi])[0]     # (K, H, C)
            for i, nodo in enumerate(nodi):
                for h, orizz in enumerate(ORIZZONTI):
                    chiavi.append((contesto, partizione_id, seme,
                                   int(nodo), int(t), int(orizz)))
                    logit.append(out[i, h].numpy())
                    veri.append(int(Y[0, i, h]))
    return chiavi, np.array(logit), np.array(veri)


def wce(logit, veri, pesi):
    p = torch.softmax(torch.as_tensor(logit), -1).numpy()
    pt = np.clip(p[np.arange(len(veri)), veri], 1e-7, 1.0)
    w = pesi[veri]
    return float(np.sum(w * -np.log(pt)) / np.sum(w))


def main() -> int:
    ap = argparse.ArgumentParser(description="prova end-to-end ridotta")
    ap.add_argument("--nodi", type=int, default=40)
    ap.add_argument("--istanti", type=int, default=400)
    ap.add_argument("--epoche", type=int, default=3)
    a = ap.parse_args()
    dep = Path(tempfile.mkdtemp(prefix="prova_e2e_"))
    print(f"configurazione RIDOTTA, distinta dalla campagna: {a.nodi} nodi, "
          f"{a.istanti} istanti, {a.epoche} epoche\ndeposito {dep}\n")

    K, T, d_stat = a.nodi, a.istanti, 5
    SEMI = {"partizione": 101, "inizializzazione": 7}   # SEPARATI
    x, y = genera(K, T, seme=0)
    nodi = partizione(K, SEMI["partizione"])
    ist = finestre(T)
    pesi = np.array([1.0, 3.5, 11.0])

    # --------------------------------------------------------------- [1] ---
    print("[1] esclusione dei nodi di prova")
    tutti = np.concatenate(list(nodi.values()))
    verifica(1, "le tre partizioni sono disgiunte e coprono i nodi",
             len(np.unique(tutti)) == K == len(tutti),
             f"{len(nodi['addestramento'])}/{len(nodi['validazione'])}/"
             f"{len(nodi['prova'])}")
    verifica("1b", "nessun nodo di prova fra quelli di addestramento",
             not set(nodi["prova"]) & set(nodi["addestramento"]))
    verifica("1c", "le finestre temporali sono disgiunte",
             not (set(ist["addestramento"]) & set(ist["prova"])),
             f"addestramento {len(ist['addestramento'])}, prova "
             f"{len(ist['prova'])} istanti; orizzonte massimo sottratto")
    verifica("1d", "i semi di partizione e inizializzazione sono separati",
             SEMI["partizione"] != SEMI["inizializzazione"])

    # --------------------------------------------------------------- [2] ---
    print("\n[2] aggiornamento dei pesi e selezione")
    M, R, P, D, ST = {}, {}, {}, {}, {}
    for v in VARIANTI:
        S = SCHEMI_T4C[v]
        norm = {k: (0.0, 1.0) for k in
                {c for n in S["statistiche"] + S["disponibilita"]
                 for c in ([f"media_{n.split('_', 1)[1]}"]
                           if n.startswith(("media_", "dev_"))
                           else ["media_r"] if n.startswith("banda_") else [])}}
        verifica_contratto(S["statistiche"], S["disponibilita"], norm,
                           f"{v}/traffic4cast",
                           canali_costanti={"occupazione", "conteggio"})
        M[v], R[v], P[v], D[v], ST[v] = addestra(
            v, x, y, nodi, ist, d_stat, SEMI, a.epoche, dep)
        print(f"     {v:16s} {R[v]['parametri']:,} parametri | "
              f"epoca scelta {R[v]['epoca_scelta']} | "
              f"validazione {R[v]['validazione_scelta']:.4f}")
    verifica(2, "i pesi cambiano durante l'addestramento",
             all(R[v]["storia"][0]["addestramento"]
                 != R[v]["storia"][-1]["addestramento"] for v in VARIANTI))
    verifica("2b", "la selezione usa la validazione INDUTTIVA",
             all(R[v]["epoca_scelta"] == min(
                 R[v]["storia"], key=lambda s: (s["validazione"], s["epoca"])
             )["epoca"] for v in VARIANTI),
             "a parita' di perdita, la PRIMA epoca")
    verifica("2c", "i parametri coincidono con gli attesi",
             R["LEGACY"]["parametri"] == 25060
             and R["BASE-CORRECTED"]["parametri"] == 25700,
             f"{R['LEGACY']['parametri']:,} e "
             f"{R['BASE-CORRECTED']['parametri']:,}")

    # --------------------------------------------------------------- [3] ---
    print("\n[3] inserimento e inferenza a stato CONGELATO")
    for v in VARIANTI:
        M[v].eval()
        pre = impronta_stato(M[v])
        _ = predici(M[v], x, y, ist["prova"][:6], nodi["prova"],
                    D[v], ST[v], "prova", 0, SEMI["inizializzazione"])
        verifica(f"3-{v[:6]}", f"{v}: lo stato non cambia dopo l'inferenza",
                 impronta_stato(M[v]) == pre, f"impronta {pre[:16]}")
        verifica(f"3-{v[:6]}b", f"{v}: nessun parametro per sensore",
                 not inventario_per_nodo(M[v], K)
                 and not inventario_per_nodo(M[v], len(nodi["prova"])))

    # --------------------------------------------------------------- [4] ---
    print("\n[4] salvataggio e ricaricamento")
    for v in VARIANTI:
        ck = torch.load(P[v], map_location="cpu", weights_only=False)
        S = SCHEMI_T4C[v]
        m2 = PredittorePerNodo(ck["d_descrittore"], d_stat,
                               sorgente="traffic4cast")
        m2.load_state_dict(ck["state_dict"])
        m2.eval()
        Xp, _ = lotto(x, y, ist["prova"][:4], nodi["prova"])
        with torch.inference_mode():
            a1 = M[v](Xp, node_ids=nodi["prova"],
                      descriptor=D[v][nodi["prova"]],
                      static_inputs=ST[v][nodi["prova"]])
            a2 = m2(Xp, node_ids=nodi["prova"],
                    descriptor=D[v][nodi["prova"]],
                    static_inputs=ST[v][nodi["prova"]])
        verifica(f"4-{v[:6]}", f"{v}: il ricaricato riproduce le predizioni",
                 torch.equal(a1, a2),
                 f"epoca {ck['epoca']}, validazione {ck['validazione']:.4f}")

    # --------------------------------------------------------------- [5] ---
    print("\n[5] manifesti e identita' delle chiavi")
    CH, LG, VR = {}, {}, {}
    for v in VARIANTI:
        CH[v], LG[v], VR[v] = predici(
            M[v], x, y, ist["prova"][:8], nodi["prova"], D[v], ST[v],
            "t4cmad", 0, SEMI["inizializzazione"])
    verifica(5, "nessun duplicato fra le chiavi",
             len(set(CH["LEGACY"])) == len(CH["LEGACY"]),
             f"{len(CH['LEGACY']):,} istanze")
    verifica("5b", "le chiavi sono IDENTICHE fra le due varianti",
             CH["LEGACY"] == CH["BASE-CORRECTED"],
             "e' il controllo che impedisce di confrontare popolazioni diverse")
    verifica("5c", "ogni nodo appartiene alla partizione di prova",
             set(k[3] for k in CH["LEGACY"]) <= set(int(n) for n in nodi["prova"]))
    verifica("5d", "ogni istante appartiene al periodo di prova",
             set(k[4] for k in CH["LEGACY"]) <= set(int(t) for t in ist["prova"]))
    atteso = len(ist["prova"][:8]) * len(nodi["prova"]) * len(ORIZZONTI)
    verifica("5e", "le istanze salvate corrispondono a quelle attese",
             len(CH["LEGACY"]) == atteso, f"{len(CH['LEGACY'])} su {atteso}")
    verifica("5f", "i bersagli coincidono fra le varianti",
             np.array_equal(VR["LEGACY"], VR["BASE-CORRECTED"]),
             "chiavi identiche implicano bersagli identici")

    # --------------------------------------------------------------- [6] ---
    print("\n[6] metriche e analisi appaiata")
    L = {v: wce(LG[v], VR[v], pesi) for v in VARIANTI}
    delta = 100 * (L["BASE-CORRECTED"] - L["LEGACY"]) / L["LEGACY"]
    verifica(6, "le perdite sono finite e positive",
             all(np.isfinite(L[v]) and L[v] > 0 for v in VARIANTI),
             " | ".join(f"{v} {L[v]:.4f}" for v in VARIANTI))
    verifica("6b", "la differenza relativa e' calcolabile e appaiata",
             np.isfinite(delta),
             f"delta = {delta:+.3f}%  — valore della PROVA, non un risultato")
    # ricalcolo indipendente, per nodo
    per_nodo = {}
    for v in VARIANTI:
        nn = np.array([k[3] for k in CH[v]])
        s = np.bincount(nn, weights=pesi[VR[v]] * -np.log(np.clip(
            torch.softmax(torch.as_tensor(LG[v]), -1).numpy()[
                np.arange(len(VR[v])), VR[v]], 1e-7, 1.0)), minlength=K)
        w = np.bincount(nn, weights=pesi[VR[v]], minlength=K)
        per_nodo[v] = (s, w)
    ric = {v: float(per_nodo[v][0].sum() / per_nodo[v][1].sum()) for v in VARIANTI}
    verifica("6c", "gli aggregati per nodo riproducono la metrica",
             all(abs(ric[v] - L[v]) < 1e-9 for v in VARIANTI),
             "e' il calcolo che il ricampionamento con molteplicita' usa")

    print("\n" + "=" * 72)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 72)
    print("\n  Questa prova verifica il PERCORSO SOFTWARE. Le prestazioni che vi")
    print("  compaiono NON si usano per scegliere iperparametri ne' per modificare")
    print("  il protocollo: la configurazione e' ridotta e distinta dalla campagna.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
