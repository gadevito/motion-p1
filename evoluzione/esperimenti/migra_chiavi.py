#!/usr/bin/env python3
"""
Migrazione degli artefatti storici alla forma canonica.
========================================================
    enc.*  ->  identita.enc.*

**MIGRAZIONE, NON RIGENERAZIONE.** Una nuova costruzione dai semi potrebbe
consumare numeri casuali in ordine diverso — e' precisamente il difetto gia'
incontrato. **Ricostruibilita' rapida non equivale a conservazione dello stato
storico.**

LE SEI GARANZIE:

    1. artefatti originali IMMUTATI;
    2. conversione delle SOLE chiavi previste;
    3. ERRORE in presenza di collisioni o chiavi inattese;
    4. tensori identici per valore, forma e tipo;
    5. caricamento della destinazione con `strict=True`;
    6. manifesto con impronta dell'origine, della destinazione e versione del
       convertitore.

**Per i punti di controllo completi si preservano anche i metadati.** Lo stato
dell'ottimizzatore richiede una verifica separata se deve servire a riprendere
l'addestramento: questo convertitore **non lo migra** e lo dichiara.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/migra_chiavi.py --dry-run
    poetry run python evoluzione/esperimenti/migra_chiavi.py
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

VERSIONE_CONVERTITORE = "1.0"
PREFISSO_VECCHIO = "enc."
PREFISSO_NUOVO = "identita.enc."


class MigrazioneImpossibile(RuntimeError):
    """Collisione, chiave inattesa, o tensore alterato."""


def impronta(sd) -> str:
    h = hashlib.sha256()
    for k, v in sorted(sd.items()):
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()[:16]


def converti(sd: dict) -> dict:
    """Le sole chiavi previste. Solleva su collisione o chiave inattesa."""
    fuori = {}
    for k, v in sd.items():
        if k.startswith(PREFISSO_NUOVO):
            raise MigrazioneImpossibile(
                f"«{k}» e' gia' nella forma canonica: l'artefatto sembra gia' "
                f"migrato, e rimigrarlo nasconderebbe un errore")
        nk = (PREFISSO_NUOVO + k[len(PREFISSO_VECCHIO):]
              if k.startswith(PREFISSO_VECCHIO) else k)
        if nk in fuori:
            raise MigrazioneImpossibile(
                f"collisione: «{k}» e un'altra chiave darebbero «{nk}»")
        fuori[nk] = v
    return fuori


def verifica(orig: dict, nuovo: dict) -> dict:
    """Tensori identici per valore, forma e tipo; nessuna chiave persa."""
    if len(orig) != len(nuovo):
        raise MigrazioneImpossibile(
            f"{len(orig)} chiavi in origine, {len(nuovo)} a destinazione")
    attese = {(PREFISSO_NUOVO + k[len(PREFISSO_VECCHIO):]
               if k.startswith(PREFISSO_VECCHIO) else k): k for k in orig}
    if set(attese) != set(nuovo):
        mancanti = set(attese) - set(nuovo)
        inattese = set(nuovo) - set(attese)
        raise MigrazioneImpossibile(
            f"chiavi mancanti {sorted(mancanti)[:4]}, "
            f"inattese {sorted(inattese)[:4]}")
    rinominate = 0
    for nk, k in attese.items():
        a, b = orig[k], nuovo[nk]
        if a.shape != b.shape or a.dtype != b.dtype:
            raise MigrazioneImpossibile(
                f"«{k}»: forma o tipo alterati, {tuple(a.shape)}/{a.dtype} "
                f"contro {tuple(b.shape)}/{b.dtype}")
        if not torch.equal(a, b):
            raise MigrazioneImpossibile(f"«{k}»: valori alterati")
        rinominate += nk != k
    return {"chiavi": len(orig), "rinominate": rinominate}


def migra(f: Path, dest: Path, dry: bool = False) -> dict:
    d = torch.load(f, map_location="cpu", weights_only=False)
    if "state_dict" not in d:
        raise MigrazioneImpossibile(f"{f.name}: nessuno `state_dict`")
    orig = d["state_dict"]
    nuovo = converti(orig)
    ver = verifica(orig, nuovo)
    # i METADATI si preservano per intero
    d2 = {k: v for k, v in d.items() if k != "state_dict"}
    d2["state_dict"] = nuovo
    d2["migrazione"] = {
        "versione_convertitore": VERSIONE_CONVERTITORE,
        "da": PREFISSO_VECCHIO, "a": PREFISSO_NUOVO,
        "impronta_origine": impronta(orig),
        "impronta_destinazione": impronta(nuovo),
        "chiavi_rinominate": ver["rinominate"],
        "istante": datetime.now(timezone.utc).isoformat(),
        "nota_ottimizzatore": (
            "lo stato dell'ottimizzatore NON e' migrato: richiede una verifica "
            "separata se deve servire a riprendere l'addestramento"),
    }
    if "optimizer_state_dict" in d:
        d2["migrazione"]["avvertenza"] = (
            "l'artefatto contiene uno stato dell'ottimizzatore, conservato "
            "immutato e NON verificato per la ripresa")
    if not dry:
        dest.parent.mkdir(parents=True, exist_ok=True)
        torch.save(d2, dest)
    return {"file": f.name, "destinazione": dest.name, **ver,
            "impronta_origine": d2["migrazione"]["impronta_origine"],
            "impronta_destinazione": d2["migrazione"]["impronta_destinazione"],
            "metadati_preservati": sorted(k for k in d if k != "state_dict")}


def main() -> int:
    ap = argparse.ArgumentParser(description="migrazione delle chiavi")
    ap.add_argument("--stati", type=Path,
                    default=Path("results/evoluzione/stati_iniziali"))
    ap.add_argument("--dest", type=Path, default=None,
                    help="cartella di destinazione; predefinita `<stati>/canonici`")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dest = a.dest or (a.stati / "canonici")

    print("=" * 84)
    print(f"MIGRAZIONE DELLE CHIAVI — convertitore {VERSIONE_CONVERTITORE}")
    print("=" * 84)
    print(f"  {PREFISSO_VECCHIO}*  ->  {PREFISSO_NUOVO}*")
    print(f"  origine {a.stati}  ->  destinazione {dest}")
    print(f"\n  **Gli artefatti originali restano IMMUTATI.** La migrazione")
    print(f"  scrive copie: una rigenerazione dai semi potrebbe consumare")
    print(f"  numeri casuali in ordine diverso.")
    if a.dry_run:
        print(f"\n  --dry-run: nessun file scritto.")

    f = sorted(a.stati.glob("*.pt"))
    if not f:
        print(f"\n  nessun artefatto in {a.stati}")
        return 1
    reg, guai = [], []
    print(f"\n  {'artefatto':58s} {'chiavi':>7} {'rinom.':>7} esito")
    for x in f:
        try:
            r = migra(x, dest / x.name, a.dry_run)
            reg.append(r)
            print(f"  {x.name:58s} {r['chiavi']:7d} {r['rinominate']:7d} "
                  f"{r['impronta_origine']} -> {r['impronta_destinazione']}")
        except MigrazioneImpossibile as e:
            guai.append({"file": x.name, "errore": str(e)})
            print(f"  {x.name:58s} {'':7} {'':7} FALLISCE: {str(e)[:60]}")

    print(f"\n  {len(reg)}/{len(f)} migrati")
    if reg:
        print(f"  chiavi rinominate per artefatto: "
              f"{sorted({r['rinominate'] for r in reg})}")
        print(f"  metadati preservati: {reg[0]['metadati_preservati']}")
    if guai:
        print(f"\n  DIFETTI:")
        for g in guai:
            print(f"     {g['file']}: {g['errore'][:96]}")
    if not a.dry_run and reg:
        m = dest / "manifesto_migrazione.json"
        m.write_text(json.dumps(
            {"versione_convertitore": VERSIONE_CONVERTITORE,
             "da": PREFISSO_VECCHIO, "a": PREFISSO_NUOVO,
             "origine": str(a.stati), "destinazione": str(dest),
             "istante": datetime.now(timezone.utc).isoformat(),
             "artefatti": reg, "falliti": guai}, indent=2, ensure_ascii=False))
        print(f"\n  manifesto in {m}")
    print("\n  Il caricamento della destinazione va verificato con "
          "`strict=True`:")
    print("  e' il controllo che accerta l'assenza di chiavi mancanti o in piu'.")
    return 0 if not guai else 1


if __name__ == "__main__":
    raise SystemExit(main())
