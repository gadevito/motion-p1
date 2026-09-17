#!/usr/bin/env python3
"""
Collaudo dell'INTEGRAZIONE, attraverso l'orchestratore vero.
============================================================
Una coppia tecnica ridotta, con entrambe le varianti, che passa dal collegamento
appena completato. **Le prove precedenti non verificano questo.**

    1. produzione dei manifesti e delle uscite;
    2. ricaricamento del punto di controllo SELEZIONATO;
    3. analisi appaiata;
    4. ripresa dell'orchestrazione senza duplicare esecuzioni completate;
    5. separazione degli artefatti dei tentativi falliti da quelli validi.

**IDENTIFICATIVO DISTINTO.** Questa prova usa l'etichetta `collaudo_integrazione`
e scrive in una cartella propria: **non entra nelle 54 esecuzioni**, e le sue
prestazioni non orientano modifiche.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_integrazione.py
    poetry run python evoluzione/esperimenti/collauda_integrazione.py --contesto Madrid
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_raccordo import (  # noqa: E402
    COMPLETATA, DIFETTO, METODO, TECNICO, Esecuzione, Tentativo, _sposta_falliti,
    esegui_una, gia_completate, matrice)

ESITI = []
ETICHETTA = "collaudo_integrazione"


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def main() -> int:
    ap = argparse.ArgumentParser(description="collaudo dell'integrazione")
    ap.add_argument("--contesto", default="Madrid")
    ap.add_argument("--epoche", type=int, default=3)
    ap.add_argument("--lotto", type=int, default=16)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    out = a.out or Path(tempfile.mkdtemp(prefix="collaudo_integrazione_"))
    (out / "raccordo").mkdir(parents=True, exist_ok=True)
    # le maschere servono all'addestramento: si riusano quelle della campagna
    reali = Path("results/evoluzione/maschere")
    if reali.exists():
        d = out / "maschere"
        d.mkdir(exist_ok=True)
        for f in reali.glob("maschere_*.npz"):
            if not (d / f.name).exists():
                (d / f.name).symlink_to(f.resolve())

    print(f"COLLAUDO DELL'INTEGRAZIONE — etichetta «{ETICHETTA}»")
    print(f"  NON entra nelle 54 esecuzioni; le prestazioni non orientano "
          f"modifiche")
    print(f"  {a.contesto} | p0 s0 | {a.epoche} epoche | deposito {out}\n")

    cfg = {"epoche": a.epoche, "lotto": a.lotto, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": ETICHETTA}

    from evoluzione.esperimenti.addestramento import addestra_una

    def addestra(E, reg, c, gen):
        return addestra_una(E, reg, c, gen, out)

    # ------------------------------------------------------------- [1] ----
    print("[1] una coppia attraverso l'orchestratore")
    P = [Esecuzione(a.contesto, 0, 0, v)
         for v in ("LEGACY", "BASE-CORRECTED")]
    for E in P:
        print(f"     {E.variante:16s}", end=" ", flush=True)
        try:
            esegui_una(E, addestra, cfg, out)
            print(f"-> {E.esito}")
        except Exception as exc:                        # noqa: BLE001
            print(f"-> SOSPESA: {type(exc).__name__}: {exc}")
            break
    verifica(1, "entrambe completate", all(e.esito == COMPLETATA for e in P),
             " | ".join(f"{e.variante} {e.esito}" for e in P))
    if not all(e.esito == COMPLETATA for e in P):
        print("\n  l'integrazione non e' percorribile: si interrompe qui")
        return 1

    man = sorted((out / "registro").glob("*.json"))
    verifica("1b", "un manifesto per ogni tentativo", len(man) >= 2,
             f"{len(man)} manifesti")
    m0 = json.loads(man[0].read_text())
    verifica("1c", "il manifesto riporta entrambe le versioni",
             "schema_version" in m0["resolved_configuration"]
             and "implementation_version" in m0["resolved_configuration"],
             f"schema {m0['resolved_configuration'].get('schema_version')}, "
             f"implementazione "
             f"{m0['resolved_configuration'].get('implementation_version')}")
    verifica("1d", "le due finestre sono distinte nel manifesto",
             m0["resolved_configuration"].get("storia_descrittore_passi") == 96
             and m0["resolved_configuration"].get("finestra_dinamica_passi") == 12)
    verifica("1e", "l'etichetta e' quella del collaudo, non della campagna",
             all(json.loads(x.read_text())["esperimento"].startswith(ETICHETTA)
                 for x in man))

    # ------------------------------------------------------------- [2] ----
    print("\n[2] ricaricamento del punto SELEZIONATO")
    import torch
    for E in P:
        ck = list((out / "raccordo").glob(
            f"ck_{E.contesto}_p0_s0_{E.variante}.pt"))
        verifica(f"2-{E.variante[:6]}", f"{E.variante}: il punto esiste",
                 len(ck) == 1)
        if ck:
            d = torch.load(ck[0], map_location="cpu", weights_only=False)
            verifica(f"2-{E.variante[:6]}b",
                     f"{E.variante}: riporta epoca e validazione scelte",
                     "epoca" in d and "validazione" in d,
                     f"epoca {d.get('epoca')}, validazione "
                     f"{d.get('validazione', float('nan')):.6f}")

    # ------------------------------------------------------------- [3] ----
    print("\n[3] analisi appaiata")
    PR = {}
    for E in P:
        f = list((out / "raccordo").glob(
            f"pred_{E.contesto}_p0_s0_{E.variante}.csv"))
        if f:
            PR[E.variante] = pd.read_csv(f[0])
    verifica(3, "le predizioni esistono per entrambe", len(PR) == 2,
             " | ".join(f"{k} {len(v):,} righe" for k, v in PR.items()))
    if len(PR) == 2:
        A, B = PR["LEGACY"], PR["BASE-CORRECTED"]
        ch = ["contesto", "partizione", "inizializzazione", "nodo", "istante",
              "orizzonte"]
        verifica("3b", "le chiavi coincidono fra le varianti",
                 A[ch].equals(B[ch]),
                 "e' il controllo che impedisce di confrontare popolazioni "
                 "diverse")
        verifica("3c", "i bersagli coincidono", A.vero.equals(B.vero))
        w = np.array([0.6, 0.9, 10.0])
        L = {}
        for k, v in PR.items():
            p = v[["p1", "p2", "p3"]].to_numpy()
            pt = np.clip(p[np.arange(len(v)), v.vero.to_numpy()], 1e-7, 1)
            ww = w[v.vero.to_numpy()]
            L[k] = float(np.sum(ww * -np.log(pt)) / np.sum(ww))
        delta = 100 * (L["BASE-CORRECTED"] - L["LEGACY"]) / L["LEGACY"]
        verifica("3d", "la differenza appaiata e' calcolabile",
                 np.isfinite(delta),
                 f"delta = {delta:+.3f}% — valore del COLLAUDO, non un "
                 f"risultato")

    # ------------------------------------------------------------- [3bis] -
    print("\n[3bis] popolazione valutata: i non assegnati sono ESCLUSI")
    # NIENTE `import numpy as np` qui: renderebbe `np` locale a tutta la
    # funzione, e le righe PRECEDENTI che lo usano fallirebbero. E' gia'
    # importato in testa al modulo.
    T4 = "data_collection/traffic4cast"
    tp = {"Madrid": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
          "Londra": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
          "Melbourne": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz"
          }[a.contesto]
    C = np.load(tp, allow_pickle=True)["congestion_emp"]
    if len(PR) == 2:
        A = PR["LEGACY"]
        nodi_pr = np.unique(A.nodo.to_numpy())
        ist_pr = np.unique(A.istante.to_numpy())
        att = np.zeros(3)
        for h in (1, 2, 4, 8):
            tt = ist_pr + h
            tt = tt[tt < C.shape[0]]
            y = C[np.ix_(tt, nodi_pr)]
            for k in (1, 2, 3):
                att[k - 1] += float((y == k).sum())
        att /= att.sum()
        oss = np.array([(A.vero.to_numpy() == k).mean() for k in range(3)])
        scarto = float(np.abs(oss - att).max())
        verifica("3e", "la distribuzione valutata coincide con quella delle "
                 "celle VALIDE",
                 scarto < 1e-6,
                 f"valutata {np.round(oss, 5).tolist()}, valide "
                 f"{np.round(att, 5).tolist()}, scarto {scarto:.2e}")
        # quante celle sono state escluse: devono essere quelle non assegnate
        tot = 0
        for h in (1, 2, 4, 8):
            tt = ist_pr + h
            tt = tt[tt < C.shape[0]]
            tot += int(C[np.ix_(tt, nodi_pr)].size)
        nz = tot - len(A)
        verifica("3f", "le celle escluse sono quelle senza bersaglio assegnato",
                 nz > 0 and abs(nz / tot
                                - float((C[np.ix_(ist_pr + 1, nodi_pr)] == 0).mean())
                                ) < 0.05,
                 f"{nz:,} escluse su {tot:,} ({nz/tot:.2%}) — su questo contesto "
                 f"i non assegnati sono attesi in quella proporzione")
        verifica("3g", "nessuna classe fuori intervallo",
                 bool(((A.vero >= 0) & (A.vero <= 2)).all()))

    # ------------------------------------------------------------- [4] ----
    print("\n[4] ripresa senza duplicare i completati")
    matrice(P, out / "raccordo")
    fatte = gia_completate(out / "raccordo")
    verifica(4, "la matrice registra le due completate", len(fatte) == 2,
             f"{len(fatte)} riprese")
    chiamate = []

    def addestra_conta(E, reg, c, gen):
        chiamate.append(E.chiave)
        return addestra_una(E, reg, c, gen, out)

    P2 = [Esecuzione(a.contesto, 0, 0, v) for v in ("LEGACY", "BASE-CORRECTED")]
    for E in P2:
        if E.chiave in fatte:
            E.esito = COMPLETATA
            continue
        esegui_una(E, addestra_conta, cfg, out)
    verifica("4b", "nessun addestramento ripetuto alla ripresa",
             not chiamate, f"chiamate: {chiamate or 'nessuna'}")
    verifica("4c", "i fallimenti NON si riprendono automaticamente",
             all(v.get("esito") == COMPLETATA for v in fatte.values()),
             "ritentarli aggirerebbe la regola dei tentativi")

    # ------------------------------------------------------------- [5] ----
    print("\n[5] separazione degli artefatti dei tentativi falliti")
    E = Esecuzione(a.contesto, 9, 9, "LEGACY")        # coordinate fittizie
    base = out / "raccordo"
    finto = base / f"ck_{a.contesto}_p9_s9_LEGACY.pt"
    finto.write_bytes(b"parziale")
    mossi = _sposta_falliti(out, E, 2)
    verifica(5, "l'artefatto parziale e' spostato fuori dai validi",
             not finto.exists() and mossi,
             f"spostato in tentativi_falliti/: {mossi}")
    verifica("5b", "il nome conserva il numero del tentativo",
             any("tentativo2" in x for x in mossi))
    validi = list(base.glob("ck_*.pt"))
    verifica("5c", "fra i validi restano i soli punti delle riuscite",
             all("p9_s9" not in x.name for x in validi),
             f"{len(validi)} punti validi")

    print("\n" + "=" * 74)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 74)
    print(f"\n  Etichetta «{ETICHETTA}»: questa prova NON entra nelle 54")
    print("  esecuzioni, e le sue prestazioni non orientano modifiche.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
