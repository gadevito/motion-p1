#!/usr/bin/env python3
"""
Riconciliazione della popolazione: IDENTITA' degli insiemi, non numerosita'.
=============================================================================
**Verifica di conformita', non un esperimento nuovo.**

Confronta gli identificativi effettivi dei nodi usati da:

    1. le partizioni, ricostruite dal seme
    2. i punti di controllo E, dalla mappa salvata
    3. la selezione di F, dai manifesti
    4. i corpus di C, P, A, R — quando esisteranno
    5. l'insieme finale di valutazione

**Non basta confrontare le numerosita'**: due insiemi di 630 nodi possono essere
diversi. Si confrontano gli **insiemi ordinati** e la loro impronta.

LA DISCREPANZA DA CHIARIRE. La popolazione congelata nel deliverable era
828 / 774 / 587 nodi; i conteggi attuali — 630 iniziali e 135 nuovi — derivano
dal 70/15/15 su 900, cioe' dalla popolazione INTERA.

    se tutte le fasi usano coerentemente la popolazione ampliata
        -> si documenta QUANDO e' stata adottata, e si corregge il protocollo
    se le fasi usano popolazioni diverse
        -> si FERMA l'integrazione e si identificano gli artefatti da rigenerare

**Non si restringe ne' si amplia automaticamente la popolazione.**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/riconcilia_popolazione.py
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.addestramento import _carica, _partizioni  # noqa
from evoluzione.esperimenti.fasi import CONTESTI, PARTIZIONI, percorso_E  # noqa
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

# la popolazione congelata nel deliverable, da confrontare
DELIVERABLE = {"Madrid": 828, "Londra": 774, "Melbourne": 587}
ORIZZONTI = (1, 2, 4, 8)
FINESTRA = 12
CAL = {"Madrid": (8887, 8983), "Londra": (8966, 9062),
       "Melbourne": (8806, 8902)}


def impronta(ids) -> str:
    """L'impronta dell'INSIEME ORDINATO: identita', non numerosita'."""
    a = np.sort(np.asarray(ids, dtype="int64"))
    return hashlib.sha256(a.tobytes()).hexdigest()[:16]


def origini_per_nodo(D, nodi, t0, t1) -> dict:
    """Le origini ammissibili **per ciascun nodo**, non sull'unione.

    Un'origine e' ammissibile per un nodo se ha almeno un bersaglio valido
    per quel nodo.
    """
    nodi = np.asarray(nodi, dtype="int64")
    orig = [t for t in range(t0 + FINESTRA - 1, t1 + 1)
            if t + max(ORIZZONTI) <= t1]
    per = np.zeros(len(nodi), dtype="int64")
    for t in orig:
        ok = np.zeros(len(nodi), dtype=bool)
        for o in ORIZZONTI:
            ok |= D["classe"][t + o][nodi] > 0
        per += ok.astype("int64")
    return {"candidate": len(orig), "minimo": int(per.min()),
            "mediana": float(np.median(per)), "massimo": int(per.max()),
            "nodi_senza_esempi": int((per == 0).sum()),
            "media": float(per.mean())}


def main() -> int:
    ap = argparse.ArgumentParser(description="riconciliazione della popolazione")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--rapporto", type=Path, default=None)
    a = ap.parse_args()
    _, dich, semi = configurazione(inserimento=True)

    print("=" * 84)
    print("RICONCILIAZIONE DELLA POPOLAZIONE — identita', non numerosita'")
    print("=" * 84)

    fuori, guai = {}, []
    for c in CONTESTI:
        D = _carica(c, a.out / "maschere")
        K = D["r"].shape[1]
        print(f"\n{'=' * 84}\n{c}\n{'=' * 84}")
        print(f"  nodi nella sorgente: {K}")
        print(f"  popolazione del deliverable: {DELIVERABLE[c]}  "
              f"{'COINCIDE' if K == DELIVERABLE[c] else 'DIVERSA'}")
        if K != DELIVERABLE[c]:
            guai.append(f"{c}: la sorgente ha {K} nodi, il deliverable ne "
                        f"dichiarava {DELIVERABLE[c]}")
        ctx = {}
        for p in PARTIZIONI:
            gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])}
            nodi, ist = _partizioni(D, gen)
            imp = {k: impronta(v) for k, v in nodi.items()}
            n = {k: len(v) for k, v in nodi.items()}
            ctx[p] = {"numerosita": n, "impronte": imp,
                      "nodi": {k: [int(x) for x in v] for k, v in nodi.items()}}
            print(f"\n  p{p}  addestramento {n['addestramento']:4d} "
                  f"({imp['addestramento']}) | validazione "
                  f"{n['validazione']:4d} ({imp['validazione']}) | prova "
                  f"{n['prova']:4d} ({imp['prova']})")
            # sovrapposizioni: NON devono esistere
            s = {k: set(int(x) for x in v) for k, v in nodi.items()}
            for x, y in (("addestramento", "validazione"),
                         ("addestramento", "prova"), ("validazione", "prova")):
                if s[x] & s[y]:
                    guai.append(f"{c} p{p}: {x} e {y} si sovrappongono in "
                                f"{len(s[x] & s[y])} nodi")
            tot = sum(n.values())
            if tot != K:
                guai.append(f"{c} p{p}: le partizioni coprono {tot} nodi su {K}")

            # ---- i punti di controllo E ---------------------------------
            for s_ in semi:
                f = percorso_E(a.out / "E_inserimento", c, p, int(s_))
                if not f.exists():
                    guai.append(f"{c} p{p} s{s_}: punto E assente")
                    continue
                d = torch.load(f, map_location="cpu", weights_only=False)
                for chiave, atteso in (("nodi_iniziali", "addestramento"),
                                       ("nodi_validazione", "validazione"),
                                       ("nodi_prova", "prova")):
                    if chiave not in d:
                        guai.append(f"{c} p{p} s{s_}: manca «{chiave}»")
                        continue
                    if impronta(d[chiave]) != imp[atteso]:
                        guai.append(
                            f"{c} p{p} s{s_}: «{chiave}» non coincide con la "
                            f"partizione ({impronta(d[chiave])} contro "
                            f"{imp[atteso]})")
            # ---- la selezione di F ---------------------------------------
            fs = a.out / "selezione_F" / f"sel_{c}_p{p}_s{int(semi[0])}.json"
            if fs.exists():
                m = json.loads(fs.read_text())
                nv = m.get("valutazione", {}).get("nodi")
                if nv is not None and nv != n["validazione"]:
                    guai.append(f"{c} p{p}: la selezione di F usa {nv} nodi, "
                                f"la partizione di validazione ne ha "
                                f"{n['validazione']}")
        # ---- le origini PER NODO, non sull'unione -----------------------
        t0, t1 = CAL[c]
        nodi0, _ = _partizioni(D, {"partizione":
                                   np.random.default_rng(SEME_PARTIZIONE[0])})
        o = origini_per_nodo(D, nodi0["prova"], t0, t1)
        print(f"\n  origini ammissibili PER NODO (p0, nodi di prova):")
        print(f"     candidate {o['candidate']} | minimo {o['minimo']} | "
              f"mediana {o['mediana']:.0f} | massimo {o['massimo']} | "
              f"media {o['media']:.1f}")
        print(f"     nodi senza esempi: {o['nodi_senza_esempi']}")
        fuori[c] = {"nodi_sorgente": K, "deliverable": DELIVERABLE[c],
                    "partizioni": {p: {"numerosita": v["numerosita"],
                                       "impronte": v["impronte"]}
                                   for p, v in ctx.items()},
                    "origini_per_nodo": o}

    print(f"\n{'=' * 84}\nESITO\n{'=' * 84}")
    if guai:
        print(f"  {len(guai)} DISCREPANZE — l'integrazione si FERMA:\n")
        for g in guai[:14]:
            print(f"     {g}")
        if len(guai) > 14:
            print(f"     … e altre {len(guai) - 14}")
        print(f"\n  Vanno identificati gli artefatti da rigenerare.")
        print(f"  **Non si restringe ne' si amplia automaticamente la")
        print(f"  popolazione.**")
    else:
        print(f"  Nessuna discrepanza: tutte le fasi usano la MEDESIMA")
        print(f"  popolazione, verificata per IMPRONTA degli insiemi.")
        print(f"\n  La popolazione e' quella INTERA della sorgente, non quella")
        print(f"  del deliverable: va documentato QUANDO e' stata adottata, e")
        print(f"  il protocollo va corretto di conseguenza.")
    if a.rapporto:
        a.rapporto.parent.mkdir(parents=True, exist_ok=True)
        a.rapporto.write_text(json.dumps(
            {"discrepanze": guai, "contesti": fuori}, indent=2,
            ensure_ascii=False))
        print(f"\n  rapporto in {a.rapporto}")
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
