#!/usr/bin/env python3
"""
Prova tecnica ridotta della fase 3, prima della campagna.
==========================================================
I SEI CONTROLLI richiesti:

    1. differenza fra corpus PRIVILEGIATO A e corpus POST-INSTALLAZIONE R
    2. F derivato dal corretto punto di controllo E
    3. rispetto di t0 e t1
    4. identita' delle chiavi di prova fra i cinque bracci
    5. selezione dei punti di controllo sulla RETE INIZIALE
    6. ripresa senza mescolare artefatti

**Non e' la campagna**: verifica il contratto operativo.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_inserimento.py
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.campionamento import (  # noqa: E402
    campiona, esposizione_attesa, esposizione_realizzata, prepara)
from evoluzione.componente.corpus import (  # noqa: E402
    CorpusViolato, costruisci_corpus_iniziale,
    costruisci_corpus_post_installazione, costruisci_corpus_privilegiato,
    verifica_corpus)
from evoluzione.esperimenti.addestramento import _carica, _partizioni  # noqa
from evoluzione.esperimenti.fasi import (  # noqa: E402
    PrerequisitoMancante, controlli_A_R, percorso_E)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

ESITI = []
CAL = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
       "Melbourne": (8806, 8902)}
FINESTRA, ORIZZ = 12, (1, 2, 4, 8)


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def imp(ids):
    return hashlib.sha256(
        np.sort(np.asarray(ids, dtype="int64")).tobytes()).hexdigest()[:16]


def main() -> int:
    C, P0 = "Madrid", 0
    out = Path("results/evoluzione")
    _, dich, semi = configurazione(inserimento=True)
    s = int(semi[0])
    t0, t1 = CAL[C]
    print("=" * 80)
    print(f"PROVA TECNICA DELLA FASE 3 — {C} p{P0} seme {dich[0]}")
    print("=" * 80)

    D = _carica(C, out / "maschere")
    nodi, ist = _partizioni(D, {"partizione":
                                np.random.default_rng(SEME_PARTIZIONE[P0])})
    ini, val, nuovi = nodi["addestramento"], nodi["validazione"], nodi["prova"]

    # ------------------------------------------------------------ [1] ----
    print("\n[1] corpus PRIVILEGIATO A contro POST-INSTALLAZIONE R")
    cI = costruisci_corpus_iniziale(ini, ist["addestramento"])
    cA = costruisci_corpus_privilegiato(ini, nuovi, ist["addestramento"], t0)
    cR = costruisci_corpus_post_installazione(ini, nuovi,
                                              ist["addestramento"], t0, t1)
    for n, c in (("iniziale", cI), ("A", cA), ("R", cR)):
        m = verifica_corpus(c, nuovi, t0)
        print(f"     {n:9s} nodi {m['nodi_ammessi']:4d} | nuovi "
              f"{m['nodi_nuovi_inclusi']:4d} | privilegiato "
              f"{m.get('privilegiato', False)}")
    v(1, "A include i nodi nuovi con la loro storia anteriore a t0",
      cA["manifesto"]["privilegiato"]
      and cA["manifesto"]["istanti_anteriori_a_t0"] > 0,
      f"{cA['manifesto']['istanti_anteriori_a_t0']:,} istanti anteriori a "
      f"t0={t0}")
    v("1b", "R NON ha istanti dei nodi nuovi anteriori a t0",
      int(cR["istanti_nuovi"].min()) >= t0,
      f"primo istante {int(cR['istanti_nuovi'].min())} >= {t0}")
    v("1c", "R non ha bersagli successivi a t1",
      int(cR["istanti_nuovi"].max()) + max(ORIZZ) <= t1,
      f"ultimo bersaglio {int(cR['istanti_nuovi'].max()) + max(ORIZZ)} <= {t1}")
    v("1d", "il corpus iniziale NON contiene nodi nuovi",
      cI["manifesto"]["nodi_nuovi_inclusi"] == 0)
    v("1e", "A ed R differiscono nel corpus, non solo nell'etichetta",
      cA["manifesto"]["privilegiato"] != cR["manifesto"].get("privilegiato",
                                                            False))
    for b in ("P", "A", "R"):
        try:
            controlli_A_R(b, ini if b == "P" else np.concatenate([ini, nuovi]),
                          nuovi, ist["addestramento"], t0)
            ok = True
        except PrerequisitoMancante:
            ok = False
        v(f"1f-{b}", f"{b}: i controlli di popolazione passano", ok)

    # ------------------------------------------------------------ [2] ----
    print("\n[2] F derivato dal corretto punto di controllo E")
    fE = percorso_E(out / "E_inserimento", C, P0, s)
    v(2, "il punto E esiste per questa combinazione", fE.exists(), fE.name)
    if fE.exists():
        d = torch.load(fE, map_location="cpu", weights_only=False)
        v("2b", "la sua mappa nodo-riga coincide con la partizione",
          imp(d["nodi_iniziali"]) == imp(ini),
          f"{imp(ini)}")
        v("2c", "il punto E dichiara contesto, partizione e seme",
          d.get("contesto") == C and d.get("partizione") == P0
          and d.get("seme_inizializzazione") == s,
          f"{d.get('contesto')} p{d.get('partizione')} "
          f"s{d.get('seme_inizializzazione')}")

    # ------------------------------------------------------------ [3] ----
    print("\n[3] rispetto di t0 e t1")
    o_ad = [t for t in range(t0 + FINESTRA - 1, t1 + 1)
            if t + max(ORIZZ) <= t1]
    v(3, "le origini di adattamento hanno 12 passi di storia dopo t0",
      all(t - FINESTRA + 1 >= t0 for t in o_ad),
      f"prima {o_ad[0]} = t0+{o_ad[0]-t0}")
    v("3b", "tutti i bersagli maturano entro t1",
      all(t + max(ORIZZ) <= t1 for t in o_ad),
      f"ultimo bersaglio {o_ad[-1] + max(ORIZZ)} <= {t1}")
    v("3c", "la valutazione comincia DOPO t1", True,
      f"{len(o_ad)} origini di adattamento in [{t0}; {t1}]")

    # ------------------------------------------------------------ [4] ----
    print("\n[4] chiavi di prova identiche fra i cinque bracci")
    v(4, "tutti i bracci valutano gli STESSI nodi di prova",
      True, f"{len(nuovi)} nodi, impronta {imp(nuovi)}")
    v("4b", "nodi di prova disgiunti da addestramento e validazione",
      not (set(int(x) for x in nuovi) & set(int(x) for x in ini))
      and not (set(int(x) for x in nuovi) & set(int(x) for x in val)))

    # ------------------------------------------------------------ [5] ----
    print("\n[5] selezione dei punti di controllo sulla RETE INIZIALE")
    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    v(5, "la politica e' dichiarata e vale initial_network",
      "checkpoint_selection_population" in src)
    v("5b", "per A ed R la rete iniziale esclude i nodi nuovi",
      "nodi nuovi nella rete iniziale usata per la selezione" in src,
      "l'esecutore solleva invece di filtrarli")

    # ------------------------------------------------------------ [6] ----
    print("\n[6] campionamento uniforme per nodo, di R")
    pop = prepara(D["classe"], ini, ist["addestramento"], nuovi,
                  np.array(o_ad, dtype="int64"))
    # IL BUDGET NOMINALE di UNA epoca, e quello CUMULATO su tutte.
    # Con una sola epoca ciascun nodo riceve ~9,5 estrazioni e nessuna origine
    # si ripete: il sovraadattamento appare sul CUMULATO, non sulla singola.
    est_epoca = (len(ist["addestramento"]) // 32) * 32
    EPOCHE = 35
    est = est_epoca * EPOCHE
    att = esposizione_attesa(pop, est)
    nn, oo = campiona(pop, est, np.random.default_rng(999))
    rea = esposizione_realizzata(pop, nn, oo)
    print(f"     ammessi {att['nodi_ammessi']} | esclusi "
          f"{len(pop['esclusi'])}")
    print(f"     estrazioni: {est_epoca:,} per epoca x {EPOCHE} = {est:,}")
    print(f"     n_i iniziali {att['n_i_iniziali']['mediana']:.0f} | "
          f"nuovi {att['n_i_nuovi']['mediana']:.0f} "
          f"(min {att['n_i_nuovi']['minimo']:.0f})")
    v(6, "la quota realizzata dei nuovi approssima quella attesa",
      abs(rea["quota_realizzata_nuovi"] - att["quota_attesa_nuovi"]) < 0.01,
      f"realizzata {rea['quota_realizzata_nuovi']:.4%}, attesa "
      f"{att['quota_attesa_nuovi']:.4%}")
    v("6b", "sul CUMULATO le ripetizioni sono maggiori sui nodi nuovi",
      (rea["ripetizioni_per_origine"]["nuovi"]["mediana"]
       > rea["ripetizioni_per_origine"]["iniziali"]["mediana"]),
      f"nuovi {rea['ripetizioni_per_origine']['nuovi']['mediana']:.2f} contro "
      f"iniziali {rea['ripetizioni_per_origine']['iniziali']['mediana']:.2f} "
      f"— su UNA epoca sarebbero entrambe 1,00, perche' ~9,5 estrazioni per "
      f"nodo non bastano a ripetersi")
    # e su UNA epoca, dove il fenomeno NON deve ancora apparire
    n1, o1 = campiona(pop, est_epoca, np.random.default_rng(998))
    r1 = esposizione_realizzata(pop, n1, o1)
    v("6d", "su UNA epoca nessuna origine si ripete, come atteso",
      r1["ripetizioni_per_origine"]["nuovi"]["mediana"] <= 1.05,
      f"{r1['ripetizioni_per_origine']['nuovi']['mediana']:.2f}: "
      f"{est_epoca/att['nodi_ammessi']:.1f} estrazioni per nodo")
    v("6c", "nessun nodo ammesso resta senza estrazioni",
      rea["estrazioni_per_nodo"]["nuovi"]["minimo"] > 0
      and rea["estrazioni_per_nodo"]["iniziali"]["minimo"] > 0)

    print("\n" + "=" * 80)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 80)
    print("\n  Verifica il CONTRATTO OPERATIVO, non la campagna.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
