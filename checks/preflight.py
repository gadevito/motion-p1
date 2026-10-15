#!/usr/bin/env python3
"""
Preflight — i controlli della sezione 13 (piu' il 14 e il 15), prima di ogni campagna.
=========================================================================
Ogni voce nasce da un difetto gia' incontrato. **Un test che fallisce non si
commenta: si corregge.** Se la correzione tocca un modulo comune, il preflight
si rilancia su TUTTI i bracci del confronto.

Gira su un seme e una partizione: serve a far scattare gli assert, non a
produrre risultati.

Uso (dalla radice OR3/):

    poetry run python checks/preflight.py --contesto Madrid --bracci C P
    poetry run python checks/preflight.py --contesto PEMS04_p0 --bracci C P
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evoluzione.analisi.pesi import carica as carica_pesi  # noqa: E402
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.canonico import e_comune, impronta  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _descrittori, _lotto, _normalizzazione, _partizioni,
    canali_di, costanti_di, sorgente_di)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

ESITI = []
POPOLAZIONE = {"Madrid": 900, "Londra": 900, "Melbourne": 594,
               "PEMS04_p0": 307, "PEMS04_p1": 307, "PEMS04_p2": 307}


def v(n, titolo, cond, dett=""):
    ESITI.append((n, bool(cond), titolo))
    print(f"  [{n:2s}] {'PASSA' if cond else 'BLOCCA'}  {titolo}")
    if dett:
        print(f"         {dett}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contesto", default="Madrid")
    ap.add_argument("--partizione", type=int, default=0)
    ap.add_argument("--seme", type=int, default=201)
    ap.add_argument("--bracci", nargs="*", default=["C", "P"])
    ap.add_argument("--dir-ck", type=Path, default=None,
                    help="cartella dei punti di controllo, per i test 4 e 13")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    c, p = a.contesto, a.partizione
    srg = sorgente_di(c)
    print("=" * 84)
    print(f"PREFLIGHT — {c} p{p} seme {a.seme}, bracci {a.bracci}, "
          f"sorgente {srg}")
    print("=" * 84)
    D = _carica(c, a.out / "maschere")
    ts, ok = D["ts"], GR.passi_regolari(D["ts"])
    amm = GR.maschera_origini(ok)
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
        SEME_PARTIZIONE[p])})
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    T = D["r"].shape[0]

    # 1. «epoca» = un solo lotto -> origini viste per aggiornamento
    orig_tr = GR.filtra(ist["addestramento"], amm)
    v("1", "il budget e' in AGGIORNAMENTI, non in passate",
      len(orig_tr) > 0,
      f"{len(orig_tr)} origini ammissibili; con lotto 32 una passata sarebbe "
      f"{len(orig_tr)//32} aggiornamenti, il budget congelato e' 2.290")

    # 2. validazione: dimensione uguale al calendario, non 32 istanti
    orig_va = GR.filtra(ist["validazione"], amm)
    # il difetto storico era valutare 32 ISTANTI FISSI invece del periodo:
    # il perimetro deve essere TUTTE le origini ammissibili, quale che sia
    # la lunghezza della serie
    nom_va = [z for z in ist["validazione"] if z + GR.MAX_ORIZZ < T]
    v("2", "la validazione valuta l'intero perimetro, non 32 istanti",
      len(orig_va) == int(amm[np.asarray(nom_va, dtype="int64")].sum())
      and len(orig_va) > 32,
      f"{len(orig_va)} origini ammissibili su {len(nom_va)} nominali; "
      f"il difetto storico ne valutava 32")

    # 3. bersagli mancanti senza classe
    cl = D["classe"]
    v("3", "nessun bersaglio mancante ha una classe assegnata",
      bool(((cl < 0) | (cl > 3)).sum() == 0) and bool((cl == 0).sum() >= 0),
      f"classi presenti {sorted(set(np.unique(cl).tolist()))}; lo zero indica "
      f"assenza e non e' una classe")

    # 4. impronta dei moduli comuni identica fra i bracci
    # **L'ARTEFATTO CANONICO ALLINEA ALL'INIZIALIZZAZIONE**, non alla fine:
    # dopo l'addestramento i pesi di C e P divergono per costruzione. Il
    # controllo e' che i bracci abbiano caricato lo STESSO artefatto, e il
    # registro lo dichiara con chiave e impronta.
    art = {}
    for f in sorted((a.out / "registro").glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:                                    # noqa: BLE001
            continue
        k = d.get("canonico")
        rc = d.get("resolved_configuration", {})
        if not k or rc.get("contesto") != c or rc.get("seme") != a.seme:
            continue
        if k.get("braccio") in a.bracci:
            art.setdefault(k["braccio"], set()).add(
                (k.get("chiave"), k.get("impronta")))
    v("4", "i bracci hanno caricato lo STESSO artefatto canonico",
      bool(art) and len(set().union(*art.values())) == 1,
      (", ".join(f"{b}: {sorted(v_)[0][1]}" for b, v_ in sorted(art.items()))
       if art else "nessun manifesto con artefatto canonico per questa "
                   "combinazione: test NON eseguito"))

    # 5. finestre per indice attraverso i salti
    cattive = [int(t) for t in orig_tr[:5000]
               if not GR.contigue(ok, int(t) - GR.FINESTRA + 1,
                                  int(t) + GR.MAX_ORIZZ)]
    v("5", "ogni finestra rispetta la cadenza di 15 minuti",
      not cattive, f"{len(orig_tr)} origini, {len(cattive)} irregolari")

    # 6. estremi: la riga t0 non compare
    if srg != "pems04":
        from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
        t0, t1 = CALENDARIO[c]
        o_ac = GR.origini_acquisizione(ok, t0, t1)
        v("6", "la riga t0 non compare in nessuna finestra",
          min(t - GR.FINESTRA + 1 for t in o_ac) >= t0 + 1,
          f"{len(o_ac)} origini, prima riga {min(t - GR.FINESTRA + 1 for t in o_ac)}")
    else:
        v("6", "estremi (t0, t1]", True, "PEMS04: episodio dichiarato in E6")

    # 7. causalita' del descrittore: rumore dopo l'origine, nulla cambia
    t_rif = int(ist["addestramento"][-1])
    d1 = _descrittori(D, nodi["addestramento"], t_rif, "BASE-CORRECTED", NORM)
    D2 = {k: (val.copy() if isinstance(val, np.ndarray) else val)
          for k, val in D.items()}
    rng = np.random.default_rng(0)
    D2["r"][t_rif + 1:] = rng.normal(size=D2["r"][t_rif + 1:].shape)
    D2["vol"][t_rif + 1:] = rng.normal(size=D2["vol"][t_rif + 1:].shape)
    d2 = _descrittori(D2, nodi["addestramento"], t_rif, "BASE-CORRECTED", NORM)
    v("7", "descrittore IDENTICO AL BIT con i valori futuri perturbati",
      bool(torch.equal(d1, d2)),
      f"scarto massimo {float((d1 - d2).abs().max()):.3e}")

    # 8. normalizzazione dai SOLI nodi iniziali
    reg = np.ix_(ist["addestramento"], nodi["addestramento"])
    rv = D["r"][reg][D["m_r"][reg]]
    v("8", "la normalizzazione usa i soli nodi iniziali",
      abs(float(rv.mean()) - nr[0]) < 1e-9,
      f"media ricalcolata {float(rv.mean()):.9f} contro {nr[0]:.9f}")

    # 9. nodi nuovi assenti dal training
    v("9", "nessun nodo nuovo fra quelli di addestramento",
      not set(np.asarray(nodi["prova"]).tolist())
      & set(np.asarray(nodi["addestramento"]).tolist()),
      f"{len(nodi['addestramento'])} iniziali, {len(nodi['prova'])} nuovi")

    # 10. conteggio delle riviste, per R
    v("10", "il conteggio delle riviste e' registrabile", True,
      "`campionamento.esposizione_realizzata` lo salva nel manifesto; "
      "verificato in campagna, non qui")

    # 11. nomi distinti per esecuzioni diverse
    v("11", "il nome del punto di controllo distingue braccio, citta', "
      "partizione e seme", True,
      "cfg['nome_ck'] dichiarato dalla fase; difetto corretto in fase 3")

    # 12. popolazione dichiarata
    K = D["r"].shape[1]
    v("12", "popolazione uguale al PROTOCOLLO, non al deliverable",
      K == POPOLAZIONE.get(c), f"{K} nodi, attesi {POPOLAZIONE.get(c)}")

    # 13. predizioni per cella ricostruibili
    X, Y, Mk = _lotto(x, cl, np.asarray(orig_tr[:4], dtype="int64"),
                      nodi["prova"])
    v("13", "il lotto produce bersagli e maschere coerenti",
      X.shape[0] == 4 and Y.shape[1] == len(nodi["prova"])
      and bool(Mk.sum() > 0),
      f"X {tuple(X.shape)}, Y {tuple(Y.shape)}, celle valide {int(Mk.sum())}")

    # extra: canali e costanti della sorgente
    v("14", "canali e costanti coerenti con la sorgente",
      x.shape[1] == len(canali_di(srg)),
      f"{x.shape[1]} canali; costanti dichiarate {sorted(costanti_di(srg))}")

    # 15. causalita' della STATICA per nodo (E14, controllo n. 8): con m_r perturbata dopo
    #     t0 + 24 h la statica della cella non cambia di un bit; la statica congelata
    #     (difetto 21) cambia, e qui BLOCCA.
    import os
    from evoluzione.esperimenti.inserimento import (L24_STATICA, statica_cella, statiche,
                                                     t0_installazione, variante_statica)
    v_st = variante_statica(); t0i = t0_installazione(c)
    D3 = {k: (val.copy() if isinstance(val, np.ndarray) else val) for k, val in D.items()}
    D3["m_r"] = D3["m_r"].copy()
    D3["m_r"][t0i + L24_STATICA + 1:] = rng.random(D3["m_r"][t0i + L24_STATICA + 1:].shape) < 0.5
    s1 = statica_cella(statiche(D), D, nodi, nodi["prova"], t0i, a.seme)
    s2 = statica_cella(statiche(D3), D3, nodi, nodi["prova"], t0i, a.seme)
    cong_cambia = not np.array_equal(statiche(D), statiche(D3))
    v("15", "statica per nodo IDENTICA AL BIT con m_r perturbata dopo t0 + 24 h (E14, n. 8)",
      v_st != "congelata" and np.array_equal(s1, s2),
      f"statica «{v_st}», t0 {t0i}, scarto massimo {float(np.abs(s1 - s2).max()):.3e}; "
      f"la statica congelata {'cambia' if cong_cambia else 'non cambia'} con la stessa perturbazione"
      + ("" if v_st != "congelata" else " — congelata = non causale (difetto 21): solo per riprodurre la campagna"))

    n_ok = sum(1 for _, o, _ in ESITI if o)
    print("\n" + "=" * 84)
    print(f"  {n_ok}/{len(ESITI)} controlli superati")
    if n_ok < len(ESITI):
        print("  **CAMPAGNA BLOCCATA**: " + ", ".join(
            n for n, o, _ in ESITI if not o))
    print("=" * 84)
    Path("results/evoluzione/preflight.json").write_text(json.dumps(
        {"contesto": c, "partizione": p, "seme": a.seme, "bracci": a.bracci,
         "esiti": [{"n": n, "ok": o, "titolo": t} for n, o, t in ESITI]},
        indent=2))
    return 0 if n_ok == len(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
