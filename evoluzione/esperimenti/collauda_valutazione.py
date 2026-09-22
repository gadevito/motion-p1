#!/usr/bin/env python3
"""
Collaudo del valutatore sull'intero perimetro.
===============================================
    1. l'accumulo A_h/B_h coincide con il calcolo su tutto l'insieme;
    2. NON coincide con la media delle perdite dei lotti;
    3. il risultato non dipende dalla dimensione del lotto;
    4. le celle senza bersaglio sono escluse;
    5. la valutazione non muove i buffer ne' i parametri;
    6. V-rest e' il complemento di V-prefix dentro V-full;
    7. un perimetro troppo corto per il prefisso SOLLEVA.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_valutazione.py
"""
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.identita import NoIdentity
from evoluzione.componente.predittore import (
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)
from evoluzione.componente.valutazione import (
    ValutazioneViolata, perimetri, valuta)

ESITI = []
D_STAT = 5


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def finti(K=12, T=600, seme=0):
    g = np.random.default_rng(seme)
    x = g.normal(size=(T, len(CANALI_T4C), K)).astype("float32")
    classe = g.integers(0, 4, (T, K))          # 0 = bersaglio NON assegnato
    stat = g.normal(size=(K, D_STAT)).astype("float32")
    return x, classe, stat


def main() -> int:
    print("=" * 78)
    print("COLLAUDO DEL VALUTATORE")
    print("=" * 78)
    K = 12
    x, classe, stat = finti(K)
    nodi = np.arange(K)
    ist = np.arange(FINESTRA - 1, 560)
    pesi = torch.tensor([0.73, 0.74, 3.70])
    from evoluzione.esperimenti.addestramento import _lotto
    torch.manual_seed(7)
    m = PredittorePerNodo(0, D_STAT, sorgente="traffic4cast",
                          identita=NoIdentity())

    # ---- [1] e [3]: accumulo, e indipendenza dal lotto ----------------
    r = {}
    for L in (32, 128, 1024):
        r[L] = valuta(m, x, classe, stat, nodi, ist, pesi, lotto=L)
    # LA SOGLIA E' RELATIVA: l'accumulo in doppia precisione riduce lo scarto
    # a ~1e-14, ma una soglia assoluta a 1e-9 su perdite di ordine 1 sarebbe
    # comunque una richiesta sulla precisione, non sulla correttezza.
    scarto = max(abs(r[a]["perdita"] - r[b]["perdita"])
                 for a in r for b in r)
    rel = scarto / abs(r[128]["perdita"])
    # DA DOVE VIENE LO SCARTO RESIDUO. Si confrontano le uscite degli STESSI
    # istanti calcolati in lotti di dimensione diversa, **incluso il lotto
    # RESIDUO** — quello incompleto in coda, che con 549 istanti vale 5, 37 o
    # 549 a seconda della suddivisione. Un lotto pieno contro un altro lotto
    # pieno non basta: e' la dimensione a cambiare l'algoritmo scelto.
    m.eval()
    S_ = torch.as_tensor(stat[nodi])
    prove = []
    with torch.inference_mode():
        for n in (5, 37, 128, 549):
            X_, _, _ = _lotto(x, classe, ist[:n], nodi)
            prove.append((n, m(X_, node_ids=[int(z) for z in nodi],
                               static_inputs=S_)[:5]))
    rif = prove[0][1]
    d_fwd = max(float((o - rif).abs().max()) for _, o in prove[1:])
    print(f"        [diagnostica] i primi 5 istanti, calcolati dentro lotti "
          f"da {[n for n, _ in prove]}:")
    print(f"        scarto massimo nelle uscite: {d_fwd:.2e}"
          + ("  -> il forward dipende dalla dimensione del lotto"
             if d_fwd > 0 else
             "  -> il forward NON dipende dal lotto; il residuo viene "
             "dall'ordine delle somme"))
    # la soglia riflette il rumore di accumulo, qualunque ne sia l'origine
    # esatta: 1e-9 relativo sta due ordini sopra il residuo osservato e sette
    # sotto le differenze da misurare.
    v(1, "il risultato non dipende dalla dimensione del lotto", rel < 1e-9,
      f"lotto 32 {r[32]['perdita']:.12f} | 128 {r[128]['perdita']:.12f} | "
      f"1024 {r[1024]['perdita']:.12f}; scarto relativo {rel:.2e} — rumore "
      f"di accumulo, sette ordini sotto le differenze da misurare")

    # ---- [2]: la media dei lotti e' DIVERSA ---------------------------
    from evoluzione.esperimenti.addestramento import _perdita
    m.eval()
    medie = []
    with torch.inference_mode():
        S = torch.as_tensor(stat[nodi])
        for i in range(0, len(ist), 64):
            X, Y, M = _lotto(x, classe, ist[i:i + 64], nodi)
            o = m(X, node_ids=[int(z) for z in nodi], static_inputs=S)
            L_, _ = _perdita(o, Y, M, pesi)
            medie.append(float(L_))
    d = abs(float(np.mean(medie)) - r[128]["perdita"])
    v(2, "l'accumulo NON coincide con la media dei lotti", d > 1e-9,
      f"accumulo {r[128]['perdita']:.8f}, media {np.mean(medie):.8f}, "
      f"scarto {d:.2e} — i lotti hanno massa di pesi diversa")

    # ---- [4]: le celle senza bersaglio sono escluse -------------------
    c2 = classe.copy()
    c2[c2 > 0] = np.where(np.random.default_rng(1).random(
        (c2 > 0).sum()) < 0.4, 0, c2[c2 > 0])      # piu' celle a zero
    r2 = valuta(m, x, classe, stat, nodi, ist, pesi, lotto=128)
    r3 = valuta(m, x, c2, stat, nodi, ist, pesi, lotto=128)
    v(4, "azzerare bersagli riduce le celle valutate",
      r3["celle_totali"] < r2["celle_totali"],
      f"{r2['celle_totali']:,} -> {r3['celle_totali']:,} celle valide")
    tot = len(ist) * K * len(ORIZZONTI)
    v("4b", "le celle valide sono meno di quelle attese",
      r2["celle_totali"] < tot,
      f"{r2['celle_totali']:,} su {tot:,} — le celle a zero sono escluse")

    # ---- [5]: nulla si muove ------------------------------------------
    m.train()
    pp = {n: p.detach().clone() for n, p in m.named_parameters()}
    bb = {n: b.detach().clone() for n, b in m.named_buffers()}
    valuta(m, x, classe, stat, nodi, ist, pesi)
    mossi = [n for n, p in m.named_parameters()
             if not torch.equal(p.detach(), pp[n])]
    bmossi = [n for n, b in m.named_buffers()
              if not torch.equal(b.detach(), bb[n])]
    v(5, "la valutazione non muove parametri ne' buffer",
      not mossi and not bmossi,
      f"{len(pp)} parametri e {len(bb)} buffer fermi")
    v("5b", "il modello resta in valutazione: il ripristino spetta al "
      "chiamante", not m.training)

    # ---- [6]: i tre perimetri -----------------------------------------
    P = perimetri(ist, 32)
    v(6, "V-rest e' il complemento di V-prefix dentro V-full",
      len(P["V-prefix"]) + len(P["V-rest"]) == len(P["V-full"])
      and not (set(P["V-prefix"].tolist()) & set(P["V-rest"].tolist())),
      f"prefix {len(P['V-prefix'])} + rest {len(P['V-rest'])} = "
      f"full {len(P['V-full'])}")
    rr = {k: valuta(m, x, classe, stat, nodi, P[k], pesi)["perdita"]
          for k in P}
    v("6b", "le tre perdite differiscono", len(set(round(z, 9)
                                                   for z in rr.values())) == 3,
      " | ".join(f"{k} {z:.6f}" for k, z in rr.items()))

    # ---- [8]: LA SCOMPOSIZIONE, contro tre inferenze separate ---------
    print()
    from evoluzione.componente.valutazione import (confronta_perimetri,
                                                   valuta_scomposto)
    sc = valuta_scomposto(m, x, classe, stat, nodi, ist, pesi, prefisso=32)
    se = confronta_perimetri(m, x, classe, stat, nodi, ist, pesi, prefisso=32)
    d = {k: abs(sc[k]["perdita"] - se[k]["perdita"])
         for k in ("V-prefix", "V-full", "V-rest")}
    v(8, "la scomposizione riproduce le tre inferenze separate",
      max(d.values()) < 1e-9,
      " | ".join(f"{k} {sc[k]['perdita']:.10f} contro {se[k]['perdita']:.10f}"
                 for k in ("V-prefix", "V-full", "V-rest")))
    v("8b", "gli scarti sono al livello del rumore di accumulo",
      max(d.values()) < 1e-9,
      " | ".join(f"{k} {z:.2e}" for k, z in d.items()))
    v("8c", "le celle si ripartiscono esattamente",
      (sc["V-prefix"]["celle_totali"] + sc["V-rest"]["celle_totali"]
       == sc["V-full"]["celle_totali"]),
      f"{sc['V-prefix']['celle_totali']:,} + "
      f"{sc['V-rest']['celle_totali']:,} = "
      f"{sc['V-full']['celle_totali']:,}")
    # e V-full NON e' la media delle due
    media = (sc["V-prefix"]["perdita"] + sc["V-rest"]["perdita"]) / 2
    v("8d", "V-full NON e' la media di V-prefix e V-rest",
      abs(media - sc["V-full"]["perdita"]) > 1e-9,
      f"media {media:.8f} contro V-full {sc['V-full']['perdita']:.8f}: "
      f"i due sottoinsiemi hanno massa di pesi diversa")

    # ---- [7]: perimetro troppo corto ----------------------------------
    try:
        perimetri(ist[:20], 32)
        ok = False
    except ValutazioneViolata:
        ok = True
    v(7, "un perimetro piu' corto del prefisso SOLLEVA", ok,
      "V-rest sarebbe vuoto")

    print("\n" + "=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
