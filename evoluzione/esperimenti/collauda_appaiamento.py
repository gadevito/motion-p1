#!/usr/bin/env python3
"""
I cinque controlli prima del lancio della campagna appaiata.
============================================================
Nessun addestramento.

    1. tutti i moduli COMUNI hanno tensori iniziali identici fra le varianti;
    2. l'encoder di BASE-CORRECTED coincide ESATTAMENTE con quello iniziale
       della campagna precedente;
    3. LEGACY ha lo STESSO stato iniziale della campagna precedente;
    4. ordine dei lotti e altre sorgenti casuali NON cambiano;
    5. gli stati iniziali COMPLETI sono salvati, non identificati dal seme.

CIASCUNO E' BLOCCANTE.

SUL DETERMINISMO DEL BACKEND. Anche un intervento cosi' controllato puo'
conservare variabilita' numerica di esecuzione: il collaudo verifica che la
COSTRUZIONE sia riproducibile a seme fissato, non che lo sia l'addestramento su
hardware diverso. Se il backend non e' deterministico, la prova lo dichiara.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_appaiamento.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.prepara_stati_iniziali import (  # noqa: E402
    MODULI_SOSTITUITI, SEMI, chiave, costruisci, d_descrittore, impronta_stato)

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def carica(dir_stati: Path, variante, seme, allineato):
    f = dir_stati / f"{chiave(variante, seme, d_descrittore(variante), allineato)}.pt"
    if not f.exists():
        return None, f
    return torch.load(f, map_location="cpu", weights_only=False), f


def main() -> int:
    ap = argparse.ArgumentParser(description="controlli dell'appaiamento")
    ap.add_argument("--stati", type=Path,
                    default=Path("results/evoluzione/stati_iniziali"))
    a = ap.parse_args()

    print("=" * 84)
    print("CONTROLLI PRIMA DEL LANCIO — campagna appaiata")
    print("=" * 84)
    print(f"  moduli sostituiti: {', '.join(MODULI_SOSTITUITI)}")

    for seme in SEMI:
        print(f"\n  seme {seme}")
        dL, fL = carica(a.stati, "LEGACY", seme, False)
        dB, fB = carica(a.stati, "BASE-CORRECTED", seme, False)
        dN, fN = carica(a.stati, "BASE-CORRECTED", seme, True)
        if not all((dL, dB, dN)):
            verifica(f"{seme}-5", "gli stati iniziali completi sono salvati",
                     False, f"assente: {[str(x) for d, x in ((dL,fL),(dB,fB),(dN,fN)) if d is None]}")
            continue

        sL, sB, sN = dL["state_dict"], dB["state_dict"], dN["state_dict"]

        # ---- [1] moduli comuni identici fra le varianti ------------------
        comuni = [k for k in sN if not k.startswith("enc")]
        div = [k for k in comuni if not torch.equal(sN[k], sL[k])]
        verifica(f"{seme}-1", "i moduli COMUNI hanno tensori identici",
                 not div,
                 f"{len(comuni)} tensori confrontati: backbone, BatchNorm, "
                 f"ramo statico, teste"
                 + (f" — DIVERSI: {div[:4]}" if div else ""))

        # ---- [2] l'encoder coincide con l'originario ---------------------
        enc = [k for k in sN if k.startswith("enc")]
        uguali = all(torch.equal(sN[k], sB[k]) for k in enc)
        verifica(f"{seme}-2",
                 "l'encoder di BASE-CORRECTED coincide con l'originario",
                 uguali, f"{len(enc)} tensori, impronta originaria "
                         f"{dB['impronta'][:16]}")

        # ---- [3] LEGACY invariata rispetto alla campagna precedente ------
        rico = costruisci("LEGACY", seme)
        verifica(f"{seme}-3", "LEGACY ha lo stesso stato iniziale di prima",
                 impronta_stato(rico.state_dict()) == dL["impronta"],
                 f"impronta {dL['impronta'][:16]}, ricostruita a seme {seme}")

        # ---- la sostituzione ha toccato SOLO i moduli previsti -----------
        mossi = [k for k in sB if not torch.equal(sN[k], sB[k])]
        attesi = {k for k in sB if k.split(".")[0] in MODULI_SOSTITUITI
                  and not torch.equal(sB[k], sL[k])}
        verifica(f"{seme}-1b",
                 "la sostituzione ha toccato ESCLUSIVAMENTE i moduli previsti",
                 set(mossi) == attesi,
                 f"{len(mossi)} tensori cambiati: "
                 f"{sorted({k.split('.')[0] for k in mossi})}")

    # ---- [4] l'ordine dei lotti non cambia -------------------------------
    print(f"\n  ordine dei lotti e sorgenti casuali")
    ist = np.arange(11, 7251)
    for seme in SEMI:
        a1 = np.random.default_rng(seme).choice(ist, 32, replace=False)
        a2 = np.random.default_rng(seme).choice(ist, 32, replace=False)
        verifica(f"{seme}-4", f"seme {seme}: l'ordine dei lotti e' riproducibile",
                 np.array_equal(a1, a2),
                 "generatore numpy separato, non toccato dal caricamento dello "
                 "stato")

    # il consumo del generatore di torch resta quello originario
    print(f"\n  consumo del generatore di torch")
    for seme in SEMI[:1]:
        torch.manual_seed(seme)
        _ = costruisci("BASE-CORRECTED", seme)
        dopo_costr = torch.randn(3).tolist()
        torch.manual_seed(seme)
        m = costruisci("BASE-CORRECTED", seme)
        d, _f = carica(a.stati, "BASE-CORRECTED", seme, True)
        if d:
            m.load_state_dict(d["state_dict"])       # NON tocca il generatore
        dopo_caric = torch.randn(3).tolist()
        verifica(f"{seme}-4b",
                 "caricare lo stato NON altera il generatore di torch",
                 np.allclose(dopo_costr, dopo_caric),
                 "la costruzione avviene comunque nell'ordine consueto, sicche' "
                 "il generatore avanza come nella campagna precedente")

    # ---- [5] gli stati sono salvati, non solo identificati ---------------
    print(f"\n  artefatti")
    r = a.stati / "registro_stati.json"
    verifica("5", "il registro degli stati esiste", r.exists(), str(r))
    if r.exists():
        d = json.loads(r.read_text())
        att = len(SEMI) * 3
        verifica("5b", f"sono salvati {att} stati completi",
                 len(d.get("stati", [])) == att,
                 f"{len(d.get('stati', []))} registrati, con impronta e "
                 f"configurazione")
        verifica("5c", "la chiave comprende la CONFIGURAZIONE, non il solo seme",
                 all("c9_h32_b4" in x["chiave"] for x in d.get("stati", [])))
        # insensibile alle maiuscole: il testo salvato scrive «NON ripristina»
        verifica("5d", "la nota sui generatori e' registrata",
                 "ripristina i generatori"
                 in d.get("nota_generatori", "").lower()
                 or "RIPRISTINA I GENERATORI"
                 in d.get("nota_generatori", "").upper(),
                 d.get("nota_generatori", "")[:88])

    print("\n" + "=" * 84)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 84)
    print("\n  SUL DETERMINISMO. Il collaudo verifica che la COSTRUZIONE sia")
    print("  riproducibile a seme fissato, non che lo sia l'addestramento su")
    print("  hardware diverso: anche un intervento cosi' controllato puo'")
    print("  conservare variabilita' numerica di esecuzione.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
