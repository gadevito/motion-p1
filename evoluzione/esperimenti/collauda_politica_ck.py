#!/usr/bin/env python3
"""
Collaudo della politica di selezione del punto di controllo.
=============================================================
Dopo la patch, verifica automaticamente che:

    1. gli identificativi usati per il punto di controllo coincidano ESATTAMENTE
       con quelli della rete iniziale;
    2. i timestamp appartengano alla validazione temporale;
    3. tutti e cinque i modelli usino le STESSE chiavi di valutazione;
    4. NESSUN nodo nuovo entri in quella metrica;
    5. la selezione di F usi invece i nodi di validazione induttiva.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_politica_ck.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def main() -> int:
    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    print("=" * 78)
    print("POLITICA DI SELEZIONE DEL PUNTO DI CONTROLLO")
    print("=" * 78)

    # ---- [1] i nodi della metrica ------------------------------------
    # il nome compare nel COMMENTO che spiega di non usarlo: si cerca un uso
    # come variabile, non la sua menzione
    import re
    uso = re.search(r"^\s*validation_nodes\s*=|\bvalidation_nodes\[", src,
                    re.M)
    v(1, "la politica e' esplicita e non generica",
      "checkpoint_selection_population" in src and uso is None,
      "nessuna variabile `validation_nodes` riusata per due scopi; il nome "
      "compare solo nel commento che ne spiega l'assenza")
    v("1b", "`nodi_ck` deriva dalla politica, non da un valore fisso",
      'nodi_ck = (nodi_rete_iniziale if politica_ck == "initial_network"' in src)
    v("1c", "la rete iniziale e' distinta dalla popolazione di addestramento",
      'cfg.get("nodi_rete_iniziale", nodi["addestramento"])' in src,
      "per A ed R la seconda e' ampliata, la prima no")

    # ---- [2] il periodo ----------------------------------------------
    v(2, "il periodo e' quello di validazione",
      'ist_ck = ist["validazione"]' in src)
    v("2b", "il lotto della metrica usa `ist_ck`, non un altro periodo",
      '_lotto(x, D["classe"], ist_ck[:cfg["lotto"]], nodi_ck)' in src)

    # ---- [3] le stesse chiavi per tutti -------------------------------
    v(3, "la metrica non dipende dal braccio",
      src.count("nodi_ck") >= 3
      and "if braccio_" not in src[src.index("nodi_ck = ("):
                                   src.index("dtr = dva = None")],
      "nessun ramo per braccio nella definizione di `nodi_ck`")

    # ---- [4] nessun nodo nuovo ----------------------------------------
    v(4, "i nodi nuovi sono rifiutati nella rete iniziale",
      "nodi nuovi nella rete iniziale usata per la selezione" in src,
      "solleva invece di filtrarli in silenzio")

    # ---- [5] la selezione di F usa i nodi induttivi --------------------
    ad = Path("evoluzione/componente/adattamento.py").read_text()
    v(5, "l'adattamento di F non usa la politica del punto di controllo",
      "checkpoint_selection_population" not in ad,
      "F seleziona gli iperparametri sull'episodio di validazione induttiva, "
      "che e' un'altra cosa")
    dis = Path("evoluzione/DISEGNO_INSERIMENTO.md").read_text()
    v("5b", "il disegno riserva la validazione induttiva alla selezione di F",
      "validazione induttiva sui nodi separati serve invece a scegliere" in dis
      or "riservati alla" in Path(
          "evoluzione/esperimenti/esegui_E.py").read_text())

    # ---- l'orchestratore dichiara la politica -------------------------
    eE = Path("evoluzione/esperimenti/esegui_E.py").read_text()
    v(6, "l'orchestratore di E dichiara `initial_network`",
      '"checkpoint_selection_population": "initial_network"' in eE)

    print("\n" + "=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    print("\n  Le campagne del raccordo restano su `inductive_validation`:")
    print("  non si uniformano retroattivamente a un protocollo introdotto")
    print("  per un esperimento diverso.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
