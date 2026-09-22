#!/usr/bin/env python3
"""
Collaudo dei due protocolli di addestramento.
==============================================
    STORICO     deve RIPRODURRE ESATTAMENTE un punto E gia' esistente
    PRINCIPALE  deve fare tutti gli aggiornamenti, valutare ai punti fissati,
                selezionare il minimo di V-full e non arrestarsi prima

Il principale si prova con un tetto RIDOTTO — 20 aggiornamenti, punti 5, 10,
20 — perche' qui si verifica il contratto, non il budget.

**Scrive in `E_collaudo/`**, mai nella cartella dei punti E veri.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_protocolli.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.registro import Registro  # noqa: E402
from evoluzione.esperimenti.addestramento import addestra_una  # noqa: E402
from evoluzione.esperimenti.fasi import percorso_E  # noqa: E402
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

ESITI = []
OUT = Path("results/evoluzione")
C, P, DICH, TORCH = "Madrid", 0, 201, 643310434


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


class Esec:
    contesto, partizione, inizializzazione, variante = C, P, 0, None


def gira(etichetta, extra):
    cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": etichetta, "braccio": "E",
           "checkpoint_selection_population": "initial_network",
           "dir_canonico": str(OUT / "canonico"),
           "dir_stati_completi": str(OUT / "stati_completi_collaudo"), **extra}
    gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[P]),
           "inizializzazione": np.random.default_rng(DICH)}
    reg = Registro.avvia(f"{etichetta}/E", note="collaudo dei protocolli",
                         radice=OUT / "registro_collaudo")
    reg.configurazione(cfg)
    ck = addestra_una(Esec(), reg, cfg, gen, OUT)
    reg.completa()
    return ck, reg


def main() -> int:
    print("=" * 80)
    print("COLLAUDO DEI PROTOCOLLI DI ADDESTRAMENTO")
    print("=" * 80)

    # ---- STORICO: riproduce il punto E esistente ------------------------
    print("\n[storico] deve riprodurre ESATTAMENTE il punto E gia' esistente")
    orig = percorso_E(OUT / "E_inserimento", C, P, TORCH)
    if not orig.exists():
        v(1, "il punto E di riferimento esiste", False, str(orig))
        return 1
    ck, _ = gira("E_collaudo_storico", {"training_protocol": "storico"})
    a = torch.load(orig, map_location="cpu", weights_only=False)
    b = torch.load(ck, map_location="cpu", weights_only=False)
    sa, sb = a["state_dict"], b["state_dict"]
    d = max(float((sa[k].float() - sb[k].float()).abs().max()) for k in sa)
    v(1, "i pesi coincidono con il punto E storico", d == 0.0,
      f"scarto massimo {d:.2e} su {len(sa)} tensori; {orig.name}")
    v("1b", "stessa epoca selezionata", a["epoca"] == b["epoca"],
      f"storico {a['epoca']}, riprodotto {b['epoca']}")
    v("1c", "la mappa nodo-riga coincide",
      a["nodi_iniziali"] == b["nodi_iniziali"])

    # ---- PRINCIPALE, con tetto ridotto ---------------------------------
    print("\n[principale] tetto 20, punti 5, 10, 20")
    ck2, reg2 = gira("E_collaudo_principale",
                     {"training_protocol": "principale",
                      "max_optimizer_updates": 20, "punti": [5, 10, 20]})
    c = torch.load(ck2, map_location="cpu", weights_only=False)
    # il registro scrive in `_p`, e ogni artefatto e' una chiave di PRIMO
    # livello del manifesto, col nome del suo tipo
    man = json.loads(Path(reg2._p).read_text())
    art = man.get("protocollo_principale", {})
    curve = art.get("curve") or []
    v(2, "il punto salvato dichiara il protocollo principale",
      c.get("training_protocol") == "principale"
      and c.get("criterio") == "minimum_full_validation_wCE")
    if curve:
        us = [r["aggiornamento"] for r in curve]
        v("2b", "valutato ESATTAMENTE ai punti fissati", us == [5, 10, 20],
          f"punti valutati {us}")
        vs = [r["V-full"] for r in curve]
        atteso = us[int(np.argmin(vs))]
        v("2c", "selezionato il MINIMO di V-full", c["aggiornamento"] == atteso,
          f"V-full {[round(z, 5) for z in vs]} -> u{c['aggiornamento']}")
        v("2d", "nessun arresto anticipato: raggiunto il tetto",
          us[-1] == 20, f"ultimo punto valutato u{us[-1]}")
    else:
        v("2b", "le curve sono registrate nel manifesto", False,
          "artefatto `protocollo_principale` non trovato: controllare il "
          "registro in results/evoluzione/registro_collaudo/")
    v("2e", "la mappa nodo-riga e' salvata anche nel principale",
      c.get("nodi_iniziali") == a["nodi_iniziali"])

    print("\n" + "=" * 80)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 80)
    print("\n  I file del collaudo sono in results/evoluzione/E_collaudo_*/:")
    print("  si possono cancellare, non toccano i punti E veri.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
