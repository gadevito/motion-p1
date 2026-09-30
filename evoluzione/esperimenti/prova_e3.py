#!/usr/bin/env python3
"""
Prova tecnica ridotta di E3: R-orig e R-mon attraverso gli ESECUTORI DEFINITIVI.
================================================================================
Madrid, partizione 0, seme 201, **budget ridotto a 20 aggiornamenti**. Stessi
costruttori della fase 3 (`cfg_braccio`, `addestra_una`, `valuta_prova`),
nessun percorso semplificato.

> Le prestazioni di questa prova NON orientano alcuna scelta.

I CONTROLLI

    1. configurazioni: campionamento per origine; R-mon seleziona sulle
       ultime 6 ore dei nodi nuovi, e SOLO su quelle
    2. campionamento uniforme per origine: quota realizzata dei nodi nuovi
       uguale a quella attesa; conteggio delle riviste salvato
    3. selezione di R-mon: criterio dichiarato nel punto, curva con la
       componente dei nodi nuovi, minimo scelto sulla media pesata
    4. valutazione: stesse chiavi di prova di R, nomi distinti

Scrive in `results/evoluzione/prova_e3/`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_e3.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.registro import Registro  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _carica, _partizioni, addestra_una)
from evoluzione.esperimenti.esegui_inserimento import (  # noqa: E402
    CALENDARIO, FASCE, Esec, costo_addestramento, tempo_disponibilita)
from evoluzione.esperimenti.inserimento import (  # noqa: E402
    PASSI_6H, cfg_braccio, valuta_prova)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

OUT = Path("results/evoluzione")
ETICHETTA = "prova_e3"
C, P, DICH = "Madrid", 0, 201
BRACCI = ("R-orig", "R-mon")
ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def main() -> int:
    t0, t1 = CALENDARIO[C]
    D = _carica(C, OUT / "maschere")
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
        SEME_PARTIZIONE[P])})
    ok = GR.passi_regolari(D["ts"])
    o_acq = GR.origini_acquisizione(ok, t0, t1)
    print("=" * 80)
    print(f"PROVA TECNICA DI E3 — {C} p{P} seme {DICH}, budget ridotto")
    print("=" * 80)

    # ------------------------------------------------------------ [1] ----
    print("\n[1] configurazioni dalla tabella unica")
    cfg = {b: cfg_braccio(b, C, P, DICH, OUT, nodi, o_acq, t1=t1)
           for b in BRACCI}
    v(1, "R-orig e R-mon campionano uniformemente per ORIGINE",
      all(cfg[b]["campionamento"] == "uniforme_origine" for b in BRACCI))
    v("1b", "R-orig seleziona sulla sola rete iniziale",
      cfg["R-orig"]["checkpoint_selection_population"] == "initial_network"
      and "origini_selezione_nuovi" not in cfg["R-orig"])
    o_sel = cfg["R-mon"].get("origini_selezione_nuovi", [])
    v("1c", "R-mon seleziona con i nodi nuovi sulle ultime 6 ore",
      cfg["R-mon"]["checkpoint_selection_population"]
      == "initial_network_piu_nuovi_6h" and len(o_sel) > 0
      and all(t1 - PASSI_6H < t <= t1 - 8 for t in o_sel)
      and set(o_sel) <= set(int(z) for z in o_acq),
      f"{len(o_sel)} origini in ({t1 - PASSI_6H}, {t1 - 8}], su {len(o_acq)} "
      f"d'acquisizione")
    v("1d", "popolazione ampliata, corpus post-installazione, come R",
      all(cfg[b]["popolazione"] == "ampliata"
          and cfg[b]["nodi_nuovi"] == [int(z) for z in nodi["prova"]]
          and cfg[b]["origini_nuovi"] == [int(z) for z in o_acq]
          for b in BRACCI))
    v("1e", "il costo va all'inserimento e attende le 24 ore, come R",
      all(costo_addestramento(b, 10.0)["inserimento_s"] == 10.0
          and tempo_disponibilita(b, {})["attesa_dati_s"] == 24 * 3600
          for b in BRACCI))

    # ---- le esecuzioni ---------------------------------------------------
    print("\n[esecuzioni] budget 20 aggiornamenti, punti 5, 10, 20")
    ck, man = {}, {}
    for b in BRACCI:
        c_ = dict(cfg[b])
        c_.update({"etichetta": ETICHETTA, "max_optimizer_updates": 20,
                   "punti": [5, 10, 20],
                   "dir_stati_completi": str(OUT / f"stati_{ETICHETTA}")})
        reg = Registro.avvia(f"{ETICHETTA}/{b}", note=f"prova {b}",
                             radice=OUT / "registro_prova")
        reg.configurazione(c_)
        t_ = time.time()
        addestra_una(Esec(C, P, c_["variante"]), reg, c_, {
            "partizione": np.random.default_rng(SEME_PARTIZIONE[P]),
            "inizializzazione": np.random.default_rng(DICH)}, OUT)
        ck[b] = OUT / c_["etichetta"] / c_["nome_ck"]
        reg.completa()
        man[b] = json.loads(Path(reg._p).read_text())
        print(f"    {b:7s} {time.time() - t_:5.1f}s  {ck[b].name}")

    # ------------------------------------------------------------ [2] ----
    print("\n[2] campionamento uniforme per origine")
    for i, b in enumerate(BRACCI):
        cs = man[b].get("campionamento_uniforme_origine", {})
        att, rea = cs.get("attesa", {}), cs.get("realizzata", {})
        v(f"2{'' if i == 0 else 'b'}", f"{b}: budget 32 x K iniziali per "
          f"aggiornamento, conteggio delle riviste salvato",
          att.get("estrazioni", 0) == 32 * len(nodi["addestramento"]) * 20
          and bool(rea.get("ripetizioni_per_origine"))
          and bool(rea.get("estrazioni_per_nodo")),
          f"{att.get('estrazioni')} estrazioni, {att.get('coppie_ammesse')} "
          f"coppie ammesse")
        v(f"2{'c' if i == 0 else 'd'}", f"{b}: la quota realizzata dei nodi "
          f"nuovi e' quella attesa (proporzionale alla loro storia)",
          abs(rea.get("quota_realizzata_nuovi", 0)
              - att.get("quota_attesa_nuovi", 1)) < 0.005,
          f"realizzata {rea.get('quota_realizzata_nuovi', 0):.4%}, attesa "
          f"{att.get('quota_attesa_nuovi', 0):.4%}; rapporto atteso "
          f"nuovi/iniziali {att.get('rapporto_mediane')}")
    v("2e", "il manifesto NON contiene il campionamento per nodo",
      all("campionamento_uniforme_nodo" not in man[b] for b in BRACCI))

    # ------------------------------------------------------------ [3] ----
    print("\n[3] selezione del punto di controllo")
    d_o = torch.load(ck["R-orig"], map_location="cpu", weights_only=False)
    d_m = torch.load(ck["R-mon"], map_location="cpu", weights_only=False)
    v(3, "R-orig: criterio della campagna (V-full della rete iniziale)",
      d_o["criterio"] == "minimum_full_validation_wCE")
    v("3b", "R-mon: criterio dichiarato nel punto salvato",
      d_m["criterio"] == "minimum_initial_plus_new6h_wCE", d_m["criterio"])
    curve = man["R-mon"]["protocollo_principale"]["curve"]
    ha = all(all(k in r for k in ("V-full", "V-nuovi-6h", "V-selezione",
                                  "celle", "celle_nuovi")) for r in curve)
    v("3c", "R-mon: la curva registra V-full, V-nuovi-6h e la media pesata",
      ha and len(curve) == 3)
    if ha:
        coer = all(abs(r["V-selezione"] - (r["V-full"] * r["celle"]
                                           + r["V-nuovi-6h"] * r["celle_nuovi"])
                       / (r["celle"] + r["celle_nuovi"])) < 1e-9 for r in curve)
        v("3d", "la media e' pesata per numero di celle", coer)
        u_att = curve[int(np.argmin([r["V-selezione"] for r in curve]))]["aggiornamento"]
        v("3e", "R-mon: selezionato il minimo della media pesata",
          d_m["aggiornamento"] == u_att,
          f"V-selezione {[round(r['V-selezione'], 5) for r in curve]} -> "
          f"u{d_m['aggiornamento']}")
        n_sel = curve[0]["celle_nuovi"]
        v("3f", "le celle dei nodi nuovi usate vengono dalle sole origini "
          "dichiarate", n_sel <= len(o_sel) * len(nodi["prova"]) * 4,
          f"{n_sel} celle <= {len(o_sel)} origini x {len(nodi['prova'])} "
          f"nodi x 4 orizzonti")
    cur_o = man["R-orig"]["protocollo_principale"]["curve"]
    v("3g", "R-orig: la curva NON ha la componente dei nodi nuovi",
      all("V-nuovi-6h" not in r for r in cur_o))

    # ------------------------------------------------------------ [4] ----
    print("\n[4] valutazione")
    ris = {}
    for b in BRACCI:
        reg = Registro.avvia(f"{ETICHETTA}/val_{b}", note=f"val {b}",
                             radice=OUT / "registro_prova")
        ris[b] = valuta_prova(b, C, P, DICH, OUT, D, nodi, ist, t1, ok, reg,
                              ck[b], None, FASCE)
        reg.completa()
    imp = {ris[b]["metriche"]["impronta_chiavi"] for b in BRACCI}
    f_R = OUT / "inserimento_griglia" / f"R_{C}_p{P}_s{DICH}.json"
    imp_R = (json.loads(f_R.read_text())["valutazione"]["impronta_chiavi"]
             if f_R.exists() else None)
    v(4, "stesse chiavi di prova fra R-orig, R-mon e la R della campagna",
      len(imp) == 1 and (imp_R is None or imp_R in imp),
      f"impronta {imp.pop() if len(imp) == 1 else imp}"
      + ("" if imp_R else " (R della campagna non trovata: confronto omesso)"))
    v("4b", "nomi dei punti distinti per braccio",
      len({ck[b].name for b in BRACCI}) == 2,
      ", ".join(ck[b].name for b in BRACCI))
    v("4c", "il modello si ricostruisce dal punto con il fornitore della "
      "tabella e valuta sul perimetro primario",
      all(np.isfinite(ris[b]["metriche"]["perimetro_primario"]["perdita"])
          for b in BRACCI),
      ", ".join(f"{b} wCE {ris[b]['metriche']['perimetro_primario']['perdita']:.5f}"
                for b in BRACCI))

    print("\n" + "=" * 80)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 80)
    print("\n  Le prestazioni di questa prova NON orientano alcuna scelta.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
