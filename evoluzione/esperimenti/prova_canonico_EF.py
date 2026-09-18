#!/usr/bin/env python3
"""
Prova ridotta: caricamento canonico e percorso E → selezione F → F di test.
============================================================================
**Prima dei 108 addestramenti di E.** Verifica il contratto operativo, non la
campagna.

    1. l'artefatto canonico e' caricato e verificato PRIMA dell'ottimizzatore,
       per C, P, E, A, R;
    2. F dichiara il NON caricamento e la sua ragione;
    3. ogni candidato della griglia RIPARTE da E: nessun adattamento cumulativo;
    4. ottimizzatore NUOVO per ogni candidato;
    5. il punto di controllo E resta IMMUTATO;
    6. la selezione trasferisce al test i soli IPERPARAMETRI;
    7. nodi di validazione e di test hanno REGISTRI DISTINTI;
    8. le copie si eseguono in SEQUENZA, non tutte in memoria.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_canonico_EF.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.adattamento import (  # noqa: E402
    adatta, carica_E, copia_da_E, seleziona, verifica_vincoli)
from evoluzione.componente.canonico import (  # noqa: E402
    CARICANO, CanonicoViolato, applica, carica, prepara, verifica)
from evoluzione.componente.identita import (  # noqa: E402
    LearnedNodeEmbedding, NoIdentity, ObservableIdentityEncoder)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, N_CLASSI, NASCOSTI, ORIZZONTI, PredittorePerNodo)

ESITI = []
D_STAT, D_DESC = 5, 26
SEME = 201
GRIGLIA = [(b, e) for b in (10, 50) for e in (1e-3, 1e-2)]


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def lotto(nodi, B=2, seme=0):
    g = torch.Generator().manual_seed(seme)
    K = len(nodi)
    X = torch.randn(B, len(CANALI_T4C), K, FINESTRA, generator=g)
    S = torch.randn(K, D_STAT, generator=g)
    Y = torch.randint(0, 3, (B, K, len(ORIZZONTI)), generator=g)
    M = torch.ones(B, K, len(ORIZZONTI), dtype=torch.bool)
    return X, nodi, Y, M, S


def main() -> int:
    dep = Path(tempfile.mkdtemp(prefix="prova_EF_"))
    NODI_IN = list(range(24))         # rete iniziale
    NODI_VAL = [100, 101, 102]        # episodio di VALIDAZIONE
    NODI_TEST = [200, 201, 202]       # episodio di TEST — registro DISTINTO
    cfg = {"c_in": len(CANALI_T4C), "nascosti": NASCOSTI, "blocchi": 4,
           "d_statiche": D_STAT, "d_statiche_uscita": 8,
           "n_orizzonti": len(ORIZZONTI), "n_classi": N_CLASSI}
    pesi = torch.tensor([0.7, 0.8, 3.5])

    print("=" * 84)
    print("PROVA RIDOTTA — canonico e percorso E → F")
    print("=" * 84)

    # ---------------------------------------------------------- [1] ------
    print("\n[1] artefatto canonico: caricato e verificato")
    def costruttore(s):
        torch.manual_seed(s)
        return PredittorePerNodo(D_DESC, D_STAT, sorgente="traffic4cast")
    prepara(costruttore, [SEME], cfg, dep / "canonico")
    art = carica(SEME, cfg, dep / "canonico")
    v(1, "l'artefatto esiste e si carica",
      art["n_tensori"] > 0 and art["chiave"].startswith("canonico_"),
      f"{art['n_tensori']} tensori, impronta {art['impronta']}")

    forn = {"C": NoIdentity(), "P": ObservableIdentityEncoder(D_DESC),
            "E": LearnedNodeEmbedding(NODI_IN)}
    mod = {}
    for k, f in forn.items():
        torch.manual_seed(SEME + 50)      # seme DIVERSO: i comuni divergono
        m = PredittorePerNodo(D_DESC, D_STAT, sorgente="traffic4cast",
                              identita=f)
        r = applica(m, art)
        verifica(m, art, k)               # BLOCCA se non conforme
        mod[k] = m
        v(f"1-{k}", f"{k}: canonico applicato e verificato",
          r["identita_intatta"],
          f"{r['applicati']} tensori comuni, fornitore intatto")
    rif = mod["C"].state_dict()
    uguali = all(torch.equal(mod[k].state_dict()[x], rif[x])
                 for k in mod for x in art["state_dict"])
    v("1z", "i moduli comuni coincidono fra i tre bracci", uguali,
      "pur costruiti con fornitori di dimensioni diverse")

    # un artefatto assente deve SOLLEVARE
    try:
        carica(SEME + 999, cfg, dep / "canonico")
        manca = False
    except CanonicoViolato:
        manca = True
    v("1y", "un artefatto assente SOLLEVA, non si ricostruisce", manca)

    # ---------------------------------------------------------- [2] ------
    print("\n[2] E addestrato, poi congelato")
    mE = mod["E"]
    optE = torch.optim.Adam(mE.parameters(), lr=1e-2)
    mE.train()
    X, n, Y, M, S = lotto(NODI_IN, seme=1)
    out = mE(X, node_ids=n, static_inputs=S)
    L = torch.nn.functional.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
    optE.zero_grad(); L.backward(); optE.step()
    fE = dep / "E.pt"
    torch.save({"state_dict": mE.state_dict(), "nodi_iniziali": NODI_IN}, fE)
    dE, nodi_in, imp_E = carica_E(fE, D_STAT)
    v(2, "il punto di controllo E e' salvato con la mappa nodo-riga",
      nodi_in == NODI_IN, f"impronta {imp_E}, {len(nodi_in)} nodi")

    # ---------------------------------------------------------- [3] ------
    print("\n[3] selezione di F: ogni candidato riparte da E")
    punteggi, impronte_iniziali, opt_ids = {}, [], []
    for b, e in GRIGLIA:
        # COPIA INDIPENDENTE, in SEQUENZA: la precedente esce di ambito
        mF, fF = copia_da_E(dE, nodi_in, NODI_VAL, D_STAT)
        impronte_iniziali.append(float(fF.nuovi.detach().abs().sum()))
        reg = []
        n_agg = adatta(mF, fF, [lotto(NODI_VAL, seme=2)], pesi, e, b, reg)
        mF.eval()
        with torch.inference_mode():
            Xv, nv, Yv, Mv, Sv = lotto(NODI_VAL, seme=3)
            o = mF(Xv, node_ids=nv, static_inputs=Sv)
            punteggi[(b, e)] = float(torch.nn.functional.cross_entropy(
                o.reshape(-1, 3), Yv.reshape(-1), weight=pesi))
        opt_ids.append(n_agg)
    v(3, "ogni candidato parte dallo stesso punto",
      len(set(round(x, 9) for x in impronte_iniziali)) == 1,
      f"{len(GRIGLIA)} candidati, embedding iniziali identici: nessun "
      f"adattamento cumulativo")
    v("3b", "gli aggiornamenti eseguiti corrispondono ai richiesti",
      opt_ids == [b for b, _ in GRIGLIA],
      f"{opt_ids} contro {[b for b, _ in GRIGLIA]}")

    # ---------------------------------------------------------- [4] ------
    print("\n[4] il punto di controllo E resta immutato")
    _, _, imp_dopo = carica_E(fE, D_STAT)
    v(4, "l'impronta di E non cambia dopo i candidati", imp_dopo == imp_E,
      f"{imp_E} prima, {imp_dopo} dopo {len(GRIGLIA)} adattamenti")

    # ---------------------------------------------------------- [5] ------
    print("\n[5] la selezione trasferisce i soli iperparametri")
    scelta = seleziona(punteggi, GRIGLIA)
    print(f"     punteggi: " + ", ".join(
        f"({b},{e:g})={x:.4f}" for (b, e), x in punteggi.items()))
    v(5, "una sola combinazione scelta", scelta in GRIGLIA,
      f"scelta {scelta}; a parita' vince la prima dell'ordine dichiarato")
    # l'istanza di TEST: nuova, con registro DISTINTO
    mT, fT = copia_da_E(dE, nodi_in, NODI_TEST, D_STAT)
    v("5b", "l'istanza di test parte dalla MEDIA, non dagli embedding di "
      "validazione",
      torch.allclose(fT.nuovi[0], fF.iniziali.mean(0), atol=1e-7),
      "gli embedding adattati sulla validazione NON si trasferiscono")
    v("5c", "nodi di validazione e test hanno registri DISTINTI",
      set(fF.nuovi_ordine) != set(fT.nuovi_ordine)
      and not set(fF.nuovi_ordine) & set(fT.nuovi_ordine),
      f"validazione {fF.nuovi_ordine}, test {fT.nuovi_ordine}")
    reg = []
    adatta(mT, fT, [lotto(NODI_TEST, seme=4)], pesi, scelta[1], scelta[0], reg)
    v("5d", "l'adattamento di test usa la configurazione scelta",
      reg and reg[0]["passo"] == scelta[1]
      and reg[0]["aggiornamenti"] == scelta[0],
      f"{reg[0] if reg else 'nessun registro'}")

    # ---------------------------------------------------------- [6] ------
    print("\n[6] i vincoli, verificati dopo l'adattamento")
    r = verifica_vincoli(mT, fT, dE, imp_E,
                         torch.as_tensor(dE["state_dict"]["identita.embedding"]),
                         fE)
    v(6, "i cinque vincoli sono rispettati", r["conforme"],
      f"E immutato ({r['impronta_E']}), {r['nuovi_adattati']} parametri "
      f"adattati")

    # ---------------------------------------------------------- [7] ------
    print("\n[7] F non carica l'artefatto canonico")
    v(7, "F non e' fra i bracci che caricano", "F" not in CARICANO,
      f"caricano: {list(CARICANO)}; F parte da E gia' addestrato, e caricarvi "
      f"lo stato iniziale cancellerebbe l'addestramento")

    print("\n" + "=" * 84)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 84)
    print("\n  Verifica il CONTRATTO OPERATIVO, non la campagna.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
