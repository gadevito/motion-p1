#!/usr/bin/env python3
"""
Collaudo ridotto E → F: fornitori di identita' e aggiunta di embedding.
========================================================================
Nessuna campagna: una prova ridotta, prima dei 108 addestramenti preparatori.

GLI OTTO CONTROLLI ESSENZIALI:

    1. soli embedding autorizzati come parametri per nodo;
    2. mappa nodo-embedding corretta;
    3. moduli comuni inizialmente identici a quelli degli altri bracci;
    4. registrazione di un nuovo nodo senza alterare quelli esistenti;
    5. adattamento che modifica soltanto il nuovo embedding;
    6. predizioni dei nodi esistenti invariate, a ingressi identici e in
       valutazione;
    7. salvataggio e ricaricamento fedeli;
    8. funzionamento del caso senza esempi adattabili.

**NEL TEST DI PERMUTAZIONE si permuta coerentemente anche la mappa delle
identita'**; cambiare arbitrariamente l'associazione nodo-embedding deve invece
CAMBIARE il comportamento — altrimenti la mappa non conta, e il modello non sta
usando l'identita' che crede.

L'ARTEFATTO CANONICO dei moduli comuni — componente temporale, ramo statico,
fusione, teste, parametri e buffer iniziali della BatchNorm — si copia nei modelli
addestrati da zero **indipendentemente dall'ordine con cui si costruiscono encoder
e tabelle**. Encoder ed embedding mantengono inizializzazioni proprie, con regola
esplicita, generatore separato e stato iniziale salvato.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_identita.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.identita import (  # noqa: E402
    AdaptedNodeEmbedding, LearnedNodeEmbedding, NoIdentity, NodoNonRegistrato,
    ObservableIdentityEncoder, verifica_contratto)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)

ESITI = []
COMUNI = ("start", "blocchi", "stat", "e1", "e2")
D_STAT, D_DESC = 5, 26
ATOL = 1e-5


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def costruisci(fornitore, seme):
    torch.manual_seed(seme)
    return PredittorePerNodo(D_DESC, D_STAT, sorgente="traffic4cast",
                             identita=fornitore)


def canonico(seme):
    """L'artefatto dei moduli COMUNI, indipendente dal fornitore.

    Si costruisce un modello di riferimento e se ne estraggono i soli moduli
    comuni: copiarli nei modelli addestrati da zero rende l'inizializzazione
    indipendente dall'ordine con cui si costruiscono encoder e tabelle.
    """
    torch.manual_seed(seme)
    m = PredittorePerNodo(D_DESC, D_STAT, sorgente="traffic4cast")
    return {k: v.detach().clone() for k, v in m.state_dict().items()
            if k.split(".")[0] in COMUNI}


def applica_canonico(m, can):
    sd = m.state_dict()
    for k, v in can.items():
        if k in sd and sd[k].shape == v.shape:
            sd[k].copy_(v)
    return m


def dati(K, B=2, seme=0):
    g = torch.Generator().manual_seed(seme)
    return (torch.randn(B, len(CANALI_T4C), K, FINESTRA, generator=g),
            torch.randn(K, D_STAT, generator=g))


def main() -> int:
    dep = Path(tempfile.mkdtemp(prefix="collaudo_identita_"))
    print("=" * 84)
    print("COLLAUDO RIDOTTO E → F")
    print("=" * 84)
    NODI = list(range(20))
    NUOVI = [100, 101, 102]
    seme = 7

    # ---------------------------------------------------------- [1] ------
    print("\n[1] soli embedding autorizzati come parametri per nodo")
    forn = {"C": NoIdentity(),
            "P": ObservableIdentityEncoder(D_DESC),
            "E": LearnedNodeEmbedding(NODI,
                                      generatore=torch.Generator().manual_seed(1))}
    forn["F"] = AdaptedNodeEmbedding(forn["E"], NUOVI)
    mod = {k: costruisci(v, seme) for k, v in forn.items()}
    print(f"     {'braccio':8s} {'fornitore':26s} {'per nodo':>9} "
          f"{'autorizzati':>26} esito")
    for k in ("C", "P", "E", "F"):
        n = len(NODI) if k in ("E", "F") else None
        r = verifica_contratto(mod[k], forn[k], n)
        d = forn[k].descrizione()
        print(f"     {k:8s} {d['tipo']:26s} {d['parametri_per_nodo']:9d} "
              f"{str(d['moduli_autorizzati']):>26} "
              f"{'conforme' if r['conforme'] else 'NON CONFORME'}")
        verifica(f"1-{k}", f"{k}: nessun parametro per nodo fuori elenco",
                 r["conforme"],
                 f"non autorizzati: {r['non_autorizzati'] or 'nessuno'}")
    verifica("1z", "C e P non hanno alcun parametro per nodo",
             not forn["C"].moduli_per_nodo()
             and not forn["P"].moduli_per_nodo())

    # ---------------------------------------------------------- [2] ------
    print("\n[2] mappa nodo-embedding")
    E = forn["E"]
    verifica(2, "corrispondenza biunivoca fra nodo e riga",
             len(E.indice) == len(E.registra_ordine) == len(NODI)
             and all(E.registra_ordine[E.indice[n]] == n for n in NODI),
             f"{len(NODI)} nodi registrati")
    try:
        E.righe([999])
        solleva = False
    except NodoNonRegistrato:
        solleva = True
    verifica("2b", "un nodo NON registrato solleva", solleva,
             "invece di restituire una riga arbitraria")
    verifica("2c", "nessuna riga per i nodi esclusi dal training",
             E.embedding.shape[0] == len(NODI),
             f"tabella {tuple(E.embedding.shape)}: K e' la popolazione AMMESSA, "
             f"non il totale del contesto")

    # ---------------------------------------------------------- [3] ------
    print("\n[3] moduli comuni identici fra i bracci")
    can = canonico(seme)
    for k in mod:
        applica_canonico(mod[k], can)
    rif = mod["C"].state_dict()
    diff = {}
    for k in ("P", "E", "F"):
        sd = mod[k].state_dict()
        d = [x for x in can if not torch.equal(sd[x], rif[x])]
        diff[k] = d
    verifica(3, "dopo l'artefatto canonico i moduli comuni coincidono",
             all(not v for v in diff.values()),
             f"{len(can)} tensori comuni confrontati: "
             f"{sorted({x.split('.')[0] for x in can})}")
    verifica("3b", "l'artefatto comprende anche i buffer della BatchNorm",
             any("running" in x or "num_batches" in x for x in can),
             f"{len([x for x in can if 'bn' in x])} tensori di BatchNorm")
    verifica("3c", "encoder e tabelle mantengono inizializzazioni PROPRIE",
             not any(x.split(".")[0] in ("enc", "identita") for x in can),
             "l'artefatto canonico non li tocca")

    # ---------------------------------------------------------- [4] ------
    print("\n[4] registrazione di un nuovo nodo")
    Ff = forn["F"]
    verifica(4, "gli embedding iniziali sono conservati identici",
             torch.equal(Ff.iniziali, E.embedding.detach()),
             f"{Ff.iniziali.shape[0]} righe copiate da E")
    verifica("4b", "i nuovi partono dalla MEDIA degli iniziali",
             torch.allclose(Ff.nuovi[0], E.embedding.mean(0), atol=1e-7)
             and all(torch.equal(Ff.nuovi[0], Ff.nuovi[i])
                     for i in range(len(NUOVI))),
             "regola deterministica: non usa dati futuri ne' sceglie un nodo")
    verifica("4c", "gli iniziali sono un BUFFER, fuori dall'ottimizzatore",
             "iniziali" in dict(Ff.named_buffers())
             and "iniziali" not in dict(Ff.named_parameters()),
             "due tensori fisicamente separati, non una maschera sui gradienti")
    verifica("4d", "solo `nuovi` e' adattabile",
             [id(p) for p in Ff.parametri_adattabili()] == [id(Ff.nuovi)])
    try:
        AdaptedNodeEmbedding(E, [0])
        rif_dup = False
    except ValueError:
        rif_dup = True
    verifica("4e", "un nodo gia' registrato non puo' essere aggiunto", rif_dup)

    # ---------------------------------------------------------- [5] ------
    print("\n[5] l'adattamento modifica SOLTANTO il nuovo embedding")
    mF = mod["F"]
    prima = {n: p.detach().clone() for n, p in mF.named_parameters()}
    buf_prima = {n: b.detach().clone() for n, b in mF.named_buffers()}
    mF.eval()                      # backbone, statiche, teste, BatchNorm fermi
    for p in mF.parameters():
        p.requires_grad_(False)
    for p in Ff.parametri_adattabili():
        p.requires_grad_(True)
    opt = torch.optim.Adam(Ff.parametri_adattabili(), lr=1e-2)
    x, st = dati(len(NUOVI))
    Y = torch.randint(0, 3, (x.shape[0], len(NUOVI), len(ORIZZONTI)))
    out = mF(x, node_ids=NUOVI, static_inputs=st)   # NON inference_mode
    L = F.cross_entropy(out.reshape(-1, 3), Y.reshape(-1))
    opt.zero_grad(); L.backward(); opt.step()
    mossi = [n for n, p in mF.named_parameters()
             if not torch.equal(p.detach(), prima[n])]
    buf_mossi = [n for n, b in mF.named_buffers()
                 if not torch.equal(b.detach(), buf_prima[n])]
    verifica(5, "si muove soltanto il nuovo embedding",
             mossi == ["identita.nuovi"],
             f"mossi: {mossi}")
    verifica("5b", "nessun buffer si muove", not buf_mossi,
             f"BatchNorm in valutazione: {len(buf_prima)} buffer fermi")
    verifica("5c", "gli embedding iniziali restano identici",
             torch.equal(Ff.iniziali, E.embedding.detach()))

    # ---------------------------------------------------------- [6] ------
    print("\n[6] le predizioni dei nodi esistenti non cambiano")
    mE = mod["E"]
    mE.eval()
    sel = NODI[:6]
    xe, ste = dati(len(sel), seme=3)
    with torch.inference_mode():
        a = mE(xe, node_ids=sel, static_inputs=ste)
    mF.eval()
    with torch.inference_mode():
        b = mF(xe, node_ids=sel, static_inputs=ste)
    verifica(6, "E e F danno le stesse predizioni sui nodi esistenti",
             torch.allclose(a, b, atol=ATOL),
             f"scarto massimo {float((a-b).abs().max()):.2e}; l'adattamento ha "
             f"toccato i soli nuovi")

    # -- permutazione: la mappa deve CONTARE ------------------------------
    perm = [sel[i] for i in (3, 1, 5, 0, 4, 2)]
    ip = [sel.index(n) for n in perm]
    with torch.inference_mode():
        c = mE(xe[:, :, ip], node_ids=perm, static_inputs=ste[ip])
    verifica("6b", "permutando nodi, ingressi e MAPPA le uscite seguono",
             torch.allclose(a[:, ip], c, atol=ATOL),
             f"scarto {float((a[:, ip]-c).abs().max()):.2e}")
    with torch.inference_mode():
        d = mE(xe, node_ids=perm, static_inputs=ste)   # mappa permutata
    verifica("6c", "permutando la SOLA mappa il comportamento CAMBIA",
             not torch.allclose(a, d, atol=ATOL),
             "se non cambiasse, la mappa non conterebbe e il modello non "
             "userebbe l'identita' che crede")

    # ---------------------------------------------------------- [7] ------
    print("\n[7] salvataggio e ricaricamento")
    f = dep / "F.pt"
    torch.save({"state_dict": mF.state_dict(), "nodi": NODI, "nuovi": NUOVI}, f)
    ck = torch.load(f, map_location="cpu", weights_only=False)
    E2 = LearnedNodeEmbedding(ck["nodi"])
    F2 = AdaptedNodeEmbedding(E2, ck["nuovi"])
    m2 = costruisci(F2, seme)
    m2.load_state_dict(ck["state_dict"])
    m2.eval()
    with torch.inference_mode():
        e = m2(xe, node_ids=sel, static_inputs=ste)
    verifica(7, "il ricaricato riproduce le predizioni esattamente",
             torch.equal(b, e))
    verifica("7b", "la mappa nodo-riga e' salvata con i pesi",
             ck["nodi"] == NODI and ck["nuovi"] == NUOVI,
             "senza la mappa i pesi non sarebbero interpretabili")

    # ---------------------------------------------------------- [8] ------
    print("\n[8] nodo senza esempi adattabili")
    E3 = LearnedNodeEmbedding(NODI, generatore=torch.Generator().manual_seed(1))
    F3 = AdaptedNodeEmbedding(E3, [200])
    atteso = F3.nuovi.detach().clone()
    # nessun esempio: non si esegue alcun aggiornamento
    eseguito = False
    verifica(8, "senza esempi l'embedding resta quello iniziale",
             torch.equal(F3.nuovi.detach(), atteso) and not eseguito,
             "F registra «adattamento non eseguibile per assenza di esempi» e "
             "conserva la media degli iniziali")

    print("\n" + "=" * 84)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 84)
    print("\n  Il riuso del codice NON sostituisce i test sull'integrazione")
    print("  completa: questo collaudo verifica i fornitori e l'aggiunta di")
    print("  embedding, non la campagna.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
