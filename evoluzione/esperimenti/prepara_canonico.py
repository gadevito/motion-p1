#!/usr/bin/env python3
"""
Preparazione degli artefatti canonici, prima di qualunque addestramento.
=========================================================================
Uno per seme, con la configurazione dei moduli comuni. **Non si duplica per
partizione**: i moduli comuni non ne dipendono.

**L'ORDINE DI COSTRUZIONE E' QUELLO STORICO** — `start`, `blocchi`, identita',
`stat`, `e1`, `e2` — e l'allineamento resta affidato a questo artefatto, che e'
**il meccanismo unico, esplicito e verificabile** approvato dal protocollo.

Il fornitore usato per estrarre l'artefatto e' indifferente: si prendono i soli
moduli comuni, e il fornitore non vi rientra. Si usa l'encoder osservabile perche'
e' il predefinito.

`addestramento.py` lo carica OBBLIGATORIAMENTE per C, P, E, A e R, prima della
creazione dell'ottimizzatore. **F e' l'eccezione**: parte dal punto di controllo E
gia' addestrato.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prepara_canonico.py --inserimento
    poetry run python evoluzione/esperimenti/prepara_canonico.py --conferma
"""
import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.canonico import (  # noqa: E402
    CARICANO, MODULI_COMUNI, VERSIONE_CANONICO, prepara)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, N_CLASSI, NASCOSTI, ORIZZONTI, PredittorePerNodo)
from evoluzione.esperimenti.semi import configurazione  # noqa: E402

D_STAT = 5
D_DESC_RIF = 26          # indifferente: il fornitore non entra nell'artefatto


def main() -> int:
    ap = argparse.ArgumentParser(description="prepara gli artefatti canonici")
    ap.add_argument("--conferma", action="store_true")
    ap.add_argument("--inserimento", action="store_true")
    ap.add_argument("--adeguatezza", action="store_true",
                    help="i tre semi della prova del budget: 301, 302, 303")
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/canonico"))
    a = ap.parse_args()
    _, dich, semi = configurazione(conferma=a.conferma,
                                   inserimento=a.inserimento,
                                   adeguatezza=a.adeguatezza)

    cfg = {"c_in": len(CANALI_T4C), "nascosti": NASCOSTI, "blocchi": 4,
           "d_statiche": D_STAT, "d_statiche_uscita": 8,
           "n_orizzonti": len(ORIZZONTI), "n_classi": N_CLASSI}

    print("=" * 84)
    print(f"ARTEFATTI CANONICI — versione {VERSIONE_CANONICO}")
    print("=" * 84)
    print(f"  moduli comuni: {', '.join(MODULI_COMUNI)}")
    print(f"  li caricano: {', '.join(CARICANO)}  |  **F NO**: parte da E "
          f"gia' addestrato")
    print(f"  configurazione: {cfg}")
    print(f"  semi dichiarati {list(dich)}")
    print(f"\n  ordine di costruzione STORICO: start, blocchi, identita', "
          f"stat, e1, e2")
    print(f"  l'allineamento e' affidato a questo artefatto, meccanismo UNICO")

    def costruttore(seme):
        torch.manual_seed(seme)
        return PredittorePerNodo(D_DESC_RIF, D_STAT, sorgente="traffic4cast")

    campagna = ("conferma" if a.conferma else
                "inserimento" if a.inserimento else
                "adeguatezza" if a.adeguatezza else "sviluppo")
    r = prepara(costruttore, semi, cfg, a.out, campagna)
    print(f"\n  {'seme':>12} {'tensori':>8}  {'impronta':16s} file")
    for x in r:
        print(f"  {x['seme']:12d} {x['n_tensori']:8d}  {x['impronta']:16s} "
              f"{x['file'][:44]}")
    print(f"\n  {len(r)} artefatti in {a.out}")
    print(f"  registro in {a.out}/registro_canonico_{campagna}.json")
    # le impronte devono essere DISTINTE fra i semi
    imp = {x["impronta"] for x in r}
    print(f"\n  impronte distinte: {len(imp)}/{len(r)} "
          f"{'(corretto: semi diversi, moduli diversi)' if len(imp) == len(r) else '<- SOSPETTO'}")
    return 0 if len(imp) == len(r) else 1


if __name__ == "__main__":
    raise SystemExit(main())
