#!/usr/bin/env python3
"""
Audit dell'inizializzazione: che cosa rappresenta davvero il fattore «seme».
=============================================================================
Nessun addestramento: ricostruisce i modelli INIZIALI e ne confronta i tensori.

IL SOSPETTO, verificabile leggendo l'ordine di costruzione. `PredittorePerNodo`
costruisce nell'ordine:

    start -> blocchi -> enc -> stat -> e1 -> e2

e `enc` ha dimensioni DIVERSE fra le varianti: 16 ingressi contro 26, cioe' 1.608
parametri contro 2.248. Consuma quindi 640 estrazioni in piu' dal generatore di
torch, e **tutti i moduli costruiti dopo di esso ricevono estrazioni diverse**.

    start, blocchi   costruiti PRIMA dell'encoder  -> attesi IDENTICI
    stat, e1, e2     costruiti DOPO                -> attesi DIVERSI

**«Stesso seme» non garantisce «stessa inizializzazione del backbone».** Non
invalida il confronto — le due varianti restano appaiate su dati, partizioni e
iperparametri — ma puo' contribuire alla forte struttura per colonna osservata
nella matrice.

NON SI CORREGGE RETROATTIVAMENTE LA CAMPAGNA. L'audit registra che cosa cambi
insieme all'encoder; un eventuale nuovo esperimento usera' un appaiamento
controllato.

L'ordine dei lotti e' invece governato da un generatore NUMPY separato, seminato
con lo stesso valore in entrambe le varianti: quello e' atteso identico, e
l'audit lo verifica.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/audit_inizializzazione.py
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import SCHEMI_T4C  # noqa: E402
from evoluzione.componente.predittore import PredittorePerNodo  # noqa: E402
from evoluzione.esperimenti.semi import configurazione  # noqa: E402

ESITI = []
# i semi si fissano in `main` dalla configurazione della campagna
SEMI = SEMI_DICHIARATI = ()
D_STAT = 5


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def costruisci(variante, seme):
    S = SCHEMI_T4C[variante]
    d = len(S["statistiche"]) + len(S["disponibilita"])
    torch.manual_seed(seme)
    return PredittorePerNodo(d, D_STAT, sorgente="traffic4cast"), d


def confronta(a, b):
    """Per ciascun gruppo di moduli: identico, diverso, o forma incompatibile."""
    sa, sb = a.state_dict(), b.state_dict()
    fuori = {}
    for k in sorted(set(sa) | set(sb)):
        if k not in sa or k not in sb:
            fuori[k] = "assente in una"
            continue
        x, y = sa[k], sb[k]
        if x.shape != y.shape:
            fuori[k] = f"forme diverse {tuple(x.shape)} / {tuple(y.shape)}"
        elif torch.equal(x, y):
            fuori[k] = "identico"
        else:
            d = float((x - y).abs().max())
            fuori[k] = f"DIVERSO (scarto max {d:.3e})"
    return fuori


def gruppo(k):
    if k.startswith("start"):
        return "start"
    if k.startswith("blocchi"):
        return "blocchi (backbone temporale)"
    if k.startswith("enc"):
        return "enc (encoder, dimensioni diverse)"
    if k.startswith("stat"):
        return "stat (ramo statico)"
    if k.startswith("e1") or k.startswith("e2"):
        return "e1, e2 (teste previsionali)"
    return k


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="audit dell'inizializzazione")
    ap.add_argument("--conferma", action="store_true",
                    help="addendum 2: dodici inizializzazioni nuove")
    a = ap.parse_args()
    global SEMI, SEMI_DICHIARATI
    _, SEMI_DICHIARATI, SEMI = configurazione(a.conferma)
    print("=" * 84)
    print("AUDIT DELL'INIZIALIZZAZIONE")
    print("=" * 84)
    print("  Ordine di costruzione: start -> blocchi -> enc -> stat -> e1 -> e2")
    print("  `enc` ha dimensioni diverse fra le varianti e consuma 640 estrazioni")
    print("  in piu' su BASE-CORRECTED: i moduli costruiti DOPO ne risentono.")

    for dich, seme in zip(SEMI_DICHIARATI, SEMI):
        print(f"\n{'=' * 84}\nseme dichiarato {dich} -> torch {seme}\n{'=' * 84}")
        A, da = costruisci("LEGACY", seme)
        B, db = costruisci("BASE-CORRECTED", seme)
        C = confronta(A, B)
        per_g = {}
        for k, v in C.items():
            per_g.setdefault(gruppo(k), []).append(v)
        print(f"  {'gruppo':34s} {'tensori':>8}  esito")
        for g, vv in per_g.items():
            ident = sum(x == "identico" for x in vv)
            div = sum(x.startswith("DIVERSO") for x in vv)
            forme = sum(x.startswith("forme") for x in vv)
            if forme:
                e = f"{forme} con forme diverse (atteso: dimensioni dell'encoder)"
            elif div == 0:
                e = "TUTTI IDENTICI"
            elif ident == 0:
                e = "TUTTI DIVERSI"
            else:
                e = f"{ident} identici, {div} diversi"
            print(f"  {g:34s} {len(vv):8d}  {e}")

        # -- le attese, verificate ----------------------------------------
        comuni = {k: v for k, v in C.items() if not k.startswith("enc")}
        prima = {k: v for k, v in comuni.items()
                 if k.startswith(("start", "blocchi"))}
        dopo = {k: v for k, v in comuni.items()
                if k.startswith(("stat", "e1", "e2"))}
        verifica(f"{seme}-prima",
                 "i moduli costruiti PRIMA dell'encoder sono identici",
                 all(v == "identico" for v in prima.values()),
                 f"{len(prima)} tensori: start e backbone temporale")
        verifica(f"{seme}-dopo",
                 "quelli costruiti DOPO sono DIVERSI",
                 all(v.startswith("DIVERSO") for v in dopo.values()),
                 f"{len(dopo)} tensori: ramo statico e teste — "
                 f"e' il disallineamento")
        # la BatchNorm: parametri appresi e buffer
        bn = {k: v for k, v in C.items() if ".bn." in k}
        verifica(f"{seme}-bn",
                 "i parametri e i buffer della BatchNorm sono identici",
                 all(v == "identico" for v in bn.values()),
                 f"{len(bn)} tensori, backbone costruito prima dell'encoder")

    # -- l'ordine dei lotti: generatore NUMPY separato ---------------------
    print(f"\n{'=' * 84}\nordine dei lotti\n{'=' * 84}")
    ist = np.arange(11, 7251)
    for seme in SEMI_DICHIARATI:
        a = np.random.default_rng(seme).choice(ist, 32, replace=False)
        b = np.random.default_rng(seme).choice(ist, 32, replace=False)
        verifica(f"{seme}-lotti",
                 f"seme {seme}: l'ordine dei lotti e' identico fra le varianti",
                 np.array_equal(a, b),
                 "governato da un generatore NUMPY separato, seminato con lo "
                 "stesso valore")

    print("\n" + "=" * 84)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 84)
    print("\n  CHE COSA REGISTRARE. «Stesso seme» significa: stesso backbone")
    print("  temporale, stessa BatchNorm, stesso ordine dei lotti — ma ramo")
    print("  statico e teste previsionali DIVERSI, perche' costruiti dopo un")
    print("  encoder di dimensione diversa.")
    print("\n  Non invalida il confronto: le varianti restano appaiate su dati,")
    print("  partizioni e iperparametri. Ma il fattore «seme» non isola la sola")
    print("  inizializzazione dell'encoder, e puo' contribuire alla struttura")
    print("  per colonna osservata nella matrice.")
    print("\n  La campagna NON si corregge retroattivamente: un eventuale nuovo")
    print("  esperimento usera' un appaiamento controllato — per esempio")
    print("  costruendo l'encoder per ULTIMO, o seminando ciascun modulo.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
