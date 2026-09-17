#!/usr/bin/env python3
"""
Preparazione degli stati iniziali, ISOLATA dall'addestramento.
==============================================================
Costruisce e salva, per ciascun seme e configurazione del modello:

    LEGACY originario
    BASE-CORRECTED originario
    BASE-CORRECTED ALLINEATA — con `stat`, `e1` ed `e2` presi da LEGACY

**LA PREPARAZIONE E' SEPARATA DALL'ADDESTRAMENTO.** Caricare uno `state_dict` non
ripristina i generatori casuali, e costruzioni ausiliarie ne altererebbero lo
stato: se avvenissero dentro l'addestramento, l'ordine dei campionamenti
cambierebbe rispetto alla campagna precedente.

Il consumo del generatore resta quello originario perche' l'addestramento, dopo
aver caricato lo stato, **ricostruisce comunque il modello nell'ordine consueto**
e vi sovrascrive i pesi: il generatore avanza allora esattamente come prima.

LA CHIAVE COMPRENDE LA CONFIGURAZIONE, non il solo seme. Nella campagna in corso
il modello e' identico fra contesti e partizioni — nove canali, 32 nascosti,
quattro blocchi, cinque statiche — ma la chiave lo dichiara comunque, cosi' una
configurazione diversa non riusa per sbaglio lo stato sbagliato.

MODULI SOSTITUITI, e SOLO QUELLI:

    stat    ramo statico
    e1, e2  teste previsionali

Il collaudo verifica che la sostituzione non tocchi backbone, encoder o BatchNorm.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prepara_stati_iniziali.py
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    SCHEMA_VERSIONE, SCHEMI_T4C, VERSIONE_IMPLEMENTAZIONE)
from evoluzione.esperimenti.semi import configurazione  # noqa: E402
from evoluzione.componente.predittore import PredittorePerNodo  # noqa: E402

VERSIONE_ADDENDUM = "1"
SEMI = SEMI_DICHIARATI = ()        # fissati in `main` dalla configurazione

# I SEMI DICHIARATI NON SONO QUELLI PASSATI A `torch.manual_seed`. L'orchestratore
# semina un generatore numpy con SEME_INIZIALIZZAZIONE[s] e ne ESTRAE il seme di
# torch:
#
#     seme_i = int(gen["inizializzazione"].integers(0, 2**31 - 1))
#
# sicche' 7, 18 e 29 diventano 2.029.167.940, 1.918.988.776 e 2.007.055.255.
# Derivarli qui con la stessa formula, anziche' copiarli, impedisce che una
# modifica dell'orchestratore li disallinei in silenzio.
D_STAT = 5
SORGENTE = "traffic4cast"
MODULI_SOSTITUITI = ("stat", "e1", "e2")
VARIANTI = ("LEGACY", "BASE-CORRECTED")


def impronta_stato(sd) -> str:
    h = hashlib.sha256()
    for k, v in sorted(sd.items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def d_descrittore(variante: str) -> int:
    S = SCHEMI_T4C[variante]
    return len(S["statistiche"]) + len(S["disponibilita"])


def chiave(variante: str, seme: int, d_desc: int, allineato: bool) -> str:
    """La chiave comprende la CONFIGURAZIONE, non il solo seme."""
    cfg = f"c9_h32_b4_s{D_STAT}_d{d_desc}"
    suf = "_allineato" if allineato else ""
    return f"{variante}_seme{seme}_{cfg}{suf}"


def costruisci(variante: str, seme: int):
    """Costruzione nell'ordine consueto, con il seme dichiarato."""
    torch.manual_seed(seme)
    return PredittorePerNodo(d_descrittore(variante), D_STAT, sorgente=SORGENTE)


def allinea(sd_corr, sd_leg):
    """Sostituisce SOLO `stat`, `e1`, `e2`. Restituisce (nuovo, sostituiti)."""
    nuovo = {k: v.clone() for k, v in sd_corr.items()}
    sostituiti = []
    for k in sd_corr:
        if k.split(".")[0] in MODULI_SOSTITUITI:
            if k not in sd_leg:
                raise KeyError(f"{k} assente in LEGACY")
            if sd_leg[k].shape != sd_corr[k].shape:
                raise ValueError(
                    f"{k}: forme incompatibili {tuple(sd_leg[k].shape)} / "
                    f"{tuple(sd_corr[k].shape)} — la sostituzione richiede "
                    f"moduli di dimensione uguale")
            nuovo[k] = sd_leg[k].clone()
            sostituiti.append(k)
    return nuovo, sostituiti


def verifica_sostituzione(sd_corr, sd_leg, sd_new, sostituiti):
    """La sostituzione tocca ESCLUSIVAMENTE i moduli previsti."""
    guai = []
    for k in sd_corr:
        atteso_da_leg = k.split(".")[0] in MODULI_SOSTITUITI
        if atteso_da_leg:
            if not torch.equal(sd_new[k], sd_leg[k]):
                guai.append(f"{k}: doveva venire da LEGACY e non coincide")
            if k not in sostituiti:
                guai.append(f"{k}: doveva essere sostituito e non lo e'")
        else:
            if not torch.equal(sd_new[k], sd_corr[k]):
                guai.append(f"{k}: NON doveva cambiare e invece e' cambiato")
    return guai


def main() -> int:
    ap = argparse.ArgumentParser(description="prepara gli stati iniziali")
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/stati_iniziali"))
    ap.add_argument("--conferma", action="store_true",
                    help="addendum 2: dodici inizializzazioni nuove")
    a = ap.parse_args()
    global SEMI, SEMI_DICHIARATI
    _, SEMI_DICHIARATI, SEMI = configurazione(a.conferma)
    a.out.mkdir(parents=True, exist_ok=True)

    print("=" * 84)
    print("PREPARAZIONE DEGLI STATI INIZIALI — isolata dall'addestramento")
    print("=" * 84)
    print(f"  moduli sostituiti: {', '.join(MODULI_SOSTITUITI)}")
    print(f"  semi dichiarati {list(SEMI_DICHIARATI)} -> semi di torch "
          f"{list(SEMI)}")
    print(f"  d_descrittore: "
          + ", ".join(f"{v} {d_descrittore(v)}" for v in VARIANTI))

    reg = []
    ok = True
    for seme in SEMI:
        L = costruisci("LEGACY", seme)
        B = costruisci("BASE-CORRECTED", seme)
        sd_l = {k: v.clone() for k, v in L.state_dict().items()}
        sd_b = {k: v.clone() for k, v in B.state_dict().items()}
        sd_n, sost = allinea(sd_b, sd_l)
        guai = verifica_sostituzione(sd_b, sd_l, sd_n, sost)
        if guai:
            ok = False

        voci = [("LEGACY", sd_l, d_descrittore("LEGACY"), False),
                ("BASE-CORRECTED", sd_b, d_descrittore("BASE-CORRECTED"), False),
                ("BASE-CORRECTED", sd_n, d_descrittore("BASE-CORRECTED"), True)]
        print(f"\n  seme {seme}")
        for var, sd, dd, allin in voci:
            k = chiave(var, seme, dd, allin)
            f = a.out / f"{k}.pt"
            torch.save({"state_dict": sd, "variante": var, "seme": seme,
                        "d_descrittore": dd, "d_statiche": D_STAT,
                        "sorgente": SORGENTE, "allineato": allin,
                        "moduli_sostituiti": list(MODULI_SOSTITUITI) if allin else [],
                        "schema_version": SCHEMA_VERSIONE,
                        "implementation_version": VERSIONE_IMPLEMENTAZIONE,
                        "versione_addendum": VERSIONE_ADDENDUM,
                        "impronta": impronta_stato(sd),
                        "istante": datetime.now(timezone.utc).isoformat()}, f)
            eti = f"{var}{' ALLINEATA' if allin else ' originaria'}"
            print(f"     {eti:28s} impronta {impronta_stato(sd)[:16]}  -> {f.name}")
            reg.append({"chiave": k, "variante": var, "seme": seme,
                        "allineato": allin, "d_descrittore": dd,
                        "impronta": impronta_stato(sd), "file": f.name})
        print(f"     sostituiti {len(sost)} tensori: {', '.join(sost)}")
        if guai:
            print(f"     DIFETTI: {guai}")
        else:
            print(f"     la sostituzione tocca ESCLUSIVAMENTE i moduli previsti")
        # e l'allineata deve differire dall'originaria SOLO li'
        div = [k for k in sd_b if not torch.equal(sd_n[k], sd_b[k])]
        print(f"     differenze fra originaria e allineata: {len(div)} tensori "
              f"({'solo i previsti' if set(x.split('.')[0] for x in div) <= set(MODULI_SOSTITUITI) else 'ALTRI COINVOLTI'})")

    # UN REGISTRO PER CAMPAGNA: scriverne uno solo sovrascriverebbe quello
    # precedente, e i suoi stati sparirebbero dalla documentazione pur restando
    # su disco. E' accaduto: dodici semi hanno soppiantato i tre della campagna
    # appaiata.
    nome_reg = ("registro_stati_conferma.json" if a.conferma
                else "registro_stati.json")
    (a.out / nome_reg).write_text(json.dumps(
        {"versione_addendum": VERSIONE_ADDENDUM,
         "schema_version": SCHEMA_VERSIONE,
         "implementation_version": VERSIONE_IMPLEMENTAZIONE,
         "moduli_sostituiti": list(MODULI_SOSTITUITI),
         "semi_dichiarati": list(SEMI_DICHIARATI), "semi_torch": list(SEMI),
         "configurazione": {"canali": 9, "nascosti": 32, "blocchi": 4,
                            "d_statiche": D_STAT, "sorgente": SORGENTE},
         "nota_generatori": (
             "caricare uno state_dict NON ripristina i generatori casuali. "
             "L'addestramento ricostruisce il modello nell'ordine consueto con "
             "il seme dichiarato e vi sovrascrive i pesi: il generatore avanza "
             "allora esattamente come nella campagna precedente."),
         "campagna": "conferma" if a.conferma else "appaiamento",
         "stati": reg, "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))

    print(f"\n{'=' * 84}")
    print(f"  {len(reg)} stati salvati in {a.out}")
    print(f"  registro in {a.out / nome_reg}")
    print("\n  Caricare uno `state_dict` NON ripristina i generatori casuali.")
    print("  L'addestramento ricostruisce il modello nell'ordine consueto con il")
    print("  seme dichiarato e vi sovrascrive i pesi: il generatore avanza")
    print("  allora esattamente come nella campagna precedente.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
