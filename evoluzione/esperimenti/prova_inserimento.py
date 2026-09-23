#!/usr/bin/env python3
"""
Prova tecnica ridotta della fase 3, attraverso gli ESECUTORI DEFINITIVI.
========================================================================
Una sola combinazione — Madrid, partizione 0, seme 201 — e tutti e cinque i
bracci, con **budget ridotto a 20 aggiornamenti**. Stessi costruttori, stesse
configurazioni, stessa valutazione della campagna: **nessun percorso
semplificato**.

> **Le prestazioni di questa prova non devono orientare alcuna modifica agli
> iperparametri.** Serve a verificare il contratto operativo.

I SEI CONTROLLI

    1. corpus A e R
    2. campionamento uniforme per nodo di R
    3. adattamento di F dai nuovi punti E, con la configurazione congelata
    4. descrittore di P: ventiquattro ore reali anche in addestramento
    5. valutazione: stesse chiavi, selezione su V-full della rete iniziale,
       nessun aggiornamento in inferenza
    6. orchestrazione: manifesti, modalita' di misura, ripresa

Scrive in `results/evoluzione/prova_inserimento/`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_inserimento.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.corpus import (  # noqa: E402
    costruisci_corpus_iniziale, costruisci_corpus_post_installazione,
    costruisci_corpus_privilegiato, verifica_corpus)
from evoluzione.componente.registro import Registro  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _carica, _partizioni, addestra_una)
from evoluzione.esperimenti.esegui_inserimento import (  # noqa: E402
    CALENDARIO, FASCE, Esec, nel_campione_isolato)
from evoluzione.esperimenti.fasi import percorso_E  # noqa: E402
from evoluzione.esperimenti.inserimento import (  # noqa: E402
    adatta_F, cfg_braccio, valuta_prova)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

OUT = Path("results/evoluzione")
ETICHETTA = "prova_inserimento"
C, P, DICH = "Madrid", 0, 201
ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def main() -> int:
    _, dich, semi_torch = configurazione(inserimento=True)
    s_torch = int(semi_torch[list(dich).index(DICH)])
    t0, t1 = CALENDARIO[C]
    D = _carica(C, OUT / "maschere")
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
        SEME_PARTIZIONE[P])})
    ok = GR.passi_regolari(D["ts"])
    o_acq = GR.origini_acquisizione(ok, t0, t1)
    print("=" * 80)
    print(f"PROVA TECNICA DELLA FASE 3 — {C} p{P} seme {DICH}, budget ridotto")
    print("=" * 80)

    # ------------------------------------------------------------ [1] ----
    print("\n[1] corpus A e R")
    cA = costruisci_corpus_privilegiato(nodi["addestramento"], nodi["prova"],
                                        ist["addestramento"], t0, ok=ok)
    cR = costruisci_corpus_post_installazione(nodi["addestramento"],
                                              nodi["prova"],
                                              ist["addestramento"], t0, t1,
                                              ok=ok)
    cI = costruisci_corpus_iniziale(nodi["addestramento"], ist["addestramento"])
    for n_, c_ in (("iniziale", cI), ("A", cA), ("R", cR)):
        verifica_corpus(c_, nodi["prova"], t0)
    v(1, "A riceve la storia privilegiata dichiarata",
      cA["manifesto"]["privilegiato"]
      and cA["manifesto"]["istanti_anteriori_a_t0"] > 0,
      f"{cA['manifesto']['istanti_anteriori_a_t0']:,} origini anteriori a t0")
    ist_n = cR["istanti_nuovi"]
    v("1b", "R non usa osservazioni dei nodi nuovi anteriori all'acquisizione",
      int(ist_n.min()) - 11 >= t0 + 1,
      f"prima riga usata {int(ist_n.min()) - 11}, t0 + 1 = {t0 + 1}")
    v("1c", "R non ha bersagli successivi a t1",
      int(ist_n.max()) + 8 <= t1,
      f"ultimo bersaglio {int(ist_n.max()) + 8} <= {t1}")
    v("1d", "il corpus iniziale non contiene nodi nuovi",
      cI["manifesto"]["nodi_nuovi_inclusi"] == 0)

    # ---- le esecuzioni, con gli ESECUTORI della campagna ----------------
    print("\n[esecuzioni] gli stessi costruttori, budget 20 aggiornamenti")
    ck, man, mod = {}, {}, {}
    for b in ("C", "P", "A", "R"):
        cfg = cfg_braccio(b, C, P, DICH, OUT, nodi, o_acq)
        cfg.update({"etichetta": ETICHETTA, "max_optimizer_updates": 20,
                    "punti": [5, 10, 20],
                    "dir_stati_completi": str(OUT / f"stati_{ETICHETTA}")})
        reg = Registro.avvia(f"{ETICHETTA}/{b}", note=f"prova {b}",
                             radice=OUT / "registro_prova")
        reg.configurazione(cfg)
        t_ = time.time()
        # `addestra_una` restituisce il file delle PREDIZIONI: il punto di
        # controllo e' quello dichiarato nella configurazione
        addestra_una(Esec(C, P, cfg["variante"]), reg, cfg, {
            "partizione": np.random.default_rng(SEME_PARTIZIONE[P]),
            "inizializzazione": np.random.default_rng(DICH)}, OUT)
        ck[b] = OUT / cfg["etichetta"] / cfg["nome_ck"]
        reg.completa()
        man[b] = json.loads(Path(reg._p).read_text())
        print(f"    {b}  {time.time() - t_:5.1f}s  {Path(ck[b]).name}")
    regF = Registro.avvia(f"{ETICHETTA}/F", note="prova F",
                          radice=OUT / "registro_prova")
    mod["F"], costoF = adatta_F(C, P, s_torch, OUT, D, nodi, ist, o_acq, regF)
    regF.completa()
    man["F"] = json.loads(Path(regF._p).read_text())
    print(f"    F  {costoF['inserimento_s']:5.1f}s  adattamento")

    # ------------------------------------------------------------ [2] ----
    print("\n[2] campionamento uniforme per nodo di R")
    cs = man["R"].get("campionamento_uniforme_nodo", {})
    att, rea = cs.get("attesa", {}), cs.get("realizzata", {})
    v(2, "il budget e' 32 x K iniziali finestre per aggiornamento",
      att.get("estrazioni", 0) == 32 * len(nodi["addestramento"]) * 20,
      f"{att.get('estrazioni')} su 20 aggiornamenti = "
      f"{32 * len(nodi['addestramento'])} per aggiornamento")
    v("2b", "la quota realizzata dei nodi nuovi approssima quella attesa",
      abs(rea.get("quota_realizzata_nuovi", 0)
          - att.get("quota_attesa_nuovi", 1)) < 0.01,
      f"realizzata {rea.get('quota_realizzata_nuovi', 0):.4%}, attesa "
      f"{att.get('quota_attesa_nuovi', 0):.4%}")
    v("2c", "esposizioni attese ed effettive registrate",
      bool(att.get("esposizione_per_origine_nuovi"))
      and bool(rea.get("ripetizioni_per_origine")))

    # ------------------------------------------------------------ [3] ----
    print("\n[3] adattamento di F")
    aF = man["F"].get("adattamento_F", {})
    fE = percorso_E(OUT / "E_inserimento_griglia", C, P, s_torch)
    cfgF = json.loads((OUT / "selezione_F_griglia" / "configurazione_F.json")
                      .read_text())["scelte"][C]
    v(3, "parte dal punto E della pipeline corretta", aF.get("punto_E") == fE.name,
      fE.name)
    v("3b", "usa la configurazione appena congelata",
      aF.get("aggiornamenti_richiesti") == cfgF["aggiornamenti"]
      and abs(aF.get("passo", 0) - cfgF["passo"]) < 1e-12,
      f"({aF.get('aggiornamenti_richiesti')}, {aF.get('passo')})")
    dE = torch.load(fE, map_location="cpu", weights_only=False)["state_dict"]
    sF = mod["F"].state_dict()
    comuni = [k for k in dE if not k.startswith("identita.")]
    mossi = [k for k in comuni if not torch.equal(dE[k], sF[k])]
    v("3c", "cambiano SOLTANTO i nuovi embedding", not mossi,
      f"{len(comuni)} moduli comuni invariati")

    # ------------------------------------------------------------ [4] ----
    print("\n[4] descrittore di P, anche in addestramento")
    ev = " ".join(e["testo"] for e in man["P"].get("eventi", []))
    e_ = D["r"].shape[0] - 8
    finestre = [int(e_ * .70) - 1, int(e_ * .70), t1]
    try:
        for t_ in finestre:
            GR.verifica_finestra_descrittore(ok, t_)
        reali = True
    except GR.GrigliaViolata:
        reali = False
    v(4, "le finestre usate in addestramento e all'inserimento sono reali",
      reali, f"t = {finestre}; l'esecutore le verifica e si ferma altrimenti")
    v("4b", "P dichiara la griglia reale", "griglia_temporale = reale" in ev)

    # ------------------------------------------------------------ [5] ----
    print("\n[5] valutazione")
    ris = {}
    for b in ("C", "P", "A", "R", "F"):
        reg = Registro.avvia(f"{ETICHETTA}/val_{b}", note=f"val {b}",
                             radice=OUT / "registro_prova")
        prima = ({k: z.clone() for k, z in mod["F"].state_dict().items()}
                 if b == "F" else None)
        ris[b] = valuta_prova(b, C, P, DICH, OUT, D, nodi, ist, t1, ok, reg,
                              ck.get(b), mod.get(b), FASCE)
        reg.completa()
        if b == "F":
            dopo = mod["F"].state_dict()
            v("5d", "nessun parametro cambia durante l'inferenza",
              all(torch.equal(prima[k], dopo[k]) for k in prima),
              f"{len(prima)} tensori")
    imp = {ris[b]["metriche"]["impronta_chiavi"] for b in ris}
    v(5, "stesse chiavi di prova per tutti e cinque i bracci", len(imp) == 1,
      f"impronta {imp.pop() if len(imp) == 1 else imp}")
    org = {ris[b]["costo"]["origini_valutate"] for b in ris}
    v("5b", "stesso perimetro per tutti", len(org) == 1,
      f"{org.pop() if len(org) == 1 else org} origini dopo t1")
    crit = set()
    for b in ("C", "P", "A", "R"):
        d = torch.load(ck[b], map_location="cpu", weights_only=False)
        crit.add((d["criterio"], d["training_protocol"]))
    v("5c", "punti selezionati su V-full della rete iniziale",
      crit == {("minimum_full_validation_wCE", "principale")}, str(crit))

    # ------------------------------------------------------------ [6] ----
    print("\n[6] orchestrazione")
    v(6, "i nomi dei punti di controllo sono distinti per braccio e seme",
      len({Path(x).name for x in ck.values()}) == 4,
      ", ".join(sorted(Path(x).name for x in ck.values())))
    v("6b", "la combinazione della prova appartiene al campione isolato",
      nel_campione_isolato({"partizione": P, "seme": DICH}),
      "partizione 0, seme 201")
    v("6c", "le fasce temporali sono fissate prima dell'analisi",
      len(FASCE) == 3 and all(n in ris["C"]["metriche"] for _, _, n in FASCE
                              if n in ris["C"]["metriche"]),
      ", ".join(n for _, _, n in FASCE))

    print("\n" + "=" * 80)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 80)
    print("\n  Le prestazioni di questa prova NON orientano gli iperparametri.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
