#!/usr/bin/env python3
"""
Collaudo di `resolve_reference`.
================================
Nessun addestramento. Copre tutti gli stati, compresi quelli che nei tre contesti
non ricorrono: che oggi non ci siano conflitti non garantisce che non ve ne siano
in una campagna futura o in un altro contesto.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_riferimento.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.riferimento import (  # noqa: E402
    AnagraficaRiferimenti, resolve_reference, riepilogo)

ESITI = []
T4 = "data_collection/traffic4cast"
BERSAGLI = {
    "t4cmad": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4clon": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
    "t4cmel": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz",
}


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def main() -> int:
    print("[1] i sei stati, su un'anagrafica costruita")
    A = AnagraficaRiferimenti.da_valori(
        {"ok": [50.0], "vuoto": [], "zero": [0.0], "negativo": [-30.0],
         "infinito": [np.inf], "conflitto": [50.0, 55.0]},
        versione="prova:1", sorgente="anagrafica di collaudo")
    atteso = {"ok": "valido", "vuoto": "mancante", "zero": "non_positivo",
              "negativo": "non_positivo", "infinito": "non_finito",
              "conflitto": "conflitto", "mai_visto": "sensore_sconosciuto"}
    print(f"\n  {'sensore':12s} {'stato':22s} {'valore':>9} {'validi':>7}  nota")
    for s, att in atteso.items():
        r = resolve_reference(A, s)
        v = "—" if r["reference_value"] is None else f"{r['reference_value']:.1f}"
        print(f"  {s:12s} {r['status']:22s} {v:>9} {r['valid_count']:7d}  "
              f"{r['note'][:44]}")
        verifica(f"1-{s}", f"stato atteso «{att}»", r["status"] == att)

    verifica("1z", "il conflitto NON viene mediato",
             resolve_reference(A, "conflitto")["reference_value"] is None,
             "la mediana nasconderebbe il conflitto anziche' risolverlo")
    verifica("1y", "un sensore senza riferimento non ha valore zero",
             resolve_reference(A, "vuoto")["reference_value"] is None)

    print("\n[2] provenienza, versione e disponibilita'")
    r = resolve_reference(A, "ok")
    verifica(2, "sorgente e versione sono sempre presenti",
             r["reference_source"] and r["reference_version"],
             f"{r['reference_source']} | {r['reference_version']}")
    verifica("2b", "la disponibilita' NON e' dedotta",
             r["available_at"] is None and r["availability_verified"] is False,
             "nessuna data assegnata retrospettivamente")
    verifica("2c", "lo stato valido lo dichiara esplicitamente",
             "non verificata" in r["note"])

    print("\n[3] la politica online e' separata e non implementata")
    r = resolve_reference(A, "ok", reference_policy="locale_online_p85")
    verifica(3, "restituisce stato esplicito, non un valore",
             r["status"] == "politica_non_implementata"
             and r["reference_value"] is None)
    r = resolve_reference(A, "ok", reference_policy="inventata")
    verifica("3b", "una politica sconosciuta e' rifiutata",
             r["status"] == "politica_non_implementata")

    print("\n[4] versione: dipende dai valori, non dal nome del file")
    B = AnagraficaRiferimenti.da_valori({"ok": [50.0]}, "prova:1", "altra sorgente")
    verifica(4, "stessa versione dichiarata, sorgenti diverse",
             resolve_reference(A, "ok")["reference_version"]
             == resolve_reference(B, "ok")["reference_version"]
             and resolve_reference(A, "ok")["reference_source"]
             != resolve_reference(B, "ok")["reference_source"])

    print("\n[5] sugli artefatti dei tre contesti")
    for c, p in BERSAGLI.items():
        if not Path(p).exists():
            print(f"  {c}: artefatto non trovato")
            continue
        try:
            An = AnagraficaRiferimenti.da_artefatto(p)
        except KeyError as e:
            print(f"  {c}: {e}")
            continue
        ri = riepilogo(An)
        print(f"  {c}: {len(An):4d} sensori | {ri}")
        verifica(f"5-{c}", "tutti i sensori hanno riferimento valido",
                 ri.get("valido", 0) == len(An))
        # l'impronta dipende dal vettore: due letture dello stesso file coincidono
        An2 = AnagraficaRiferimenti.da_artefatto(p)
        verifica(f"5-{c}b", "la versione e' riproducibile",
                 An.versione == An2.versione, An.versione)

    print("\n" + "=" * 64)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 64)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
