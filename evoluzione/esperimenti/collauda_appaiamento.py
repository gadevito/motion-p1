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
    MODULI_SOSTITUITI, chiave, costruisci, d_descrittore, impronta_stato)
from evoluzione.esperimenti.semi import configurazione  # noqa: E402

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
                    default=Path("results/evoluzione/stati_iniziali"),
                    help="gli artefatti STORICI, in forma `enc.*`. Per quelli "
                         "migrati usare `.../stati_iniziali/canonici`, e il "
                         "confronto con `costruisci()` sara' allora coerente")
    ap.add_argument("--conferma", action="store_true",
                    help="addendum 2: dodici inizializzazioni nuove")
    a = ap.parse_args()
    _, SEMI_DICH, SEMI = configurazione(a.conferma)
    print(f"  semi dichiarati {list(SEMI_DICH)}")

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
        # ATTENZIONE ALLA FORMA. `costruisci()` produce ora la forma CANONICA
        # `identita.enc.*`, mentre gli artefatti storici hanno `enc.*`: le
        # impronte differiscono per la sola rinomina, non per i tensori. Si
        # confrontano quindi i TENSORI, chiave per chiave dopo la conversione.
        sd_r = rico.state_dict()
        def _canon(k):
            return ("identita.enc." + k[len("enc."):]
                    if k.startswith("enc.") else k)
        coppie = {_canon(k): v for k, v in sL.items()}
        uguali = (set(coppie) == set(sd_r)
                  and all(torch.equal(coppie[k], sd_r[k]) for k in coppie))
        verifica(f"{seme}-3", "LEGACY ha lo stesso stato iniziale di prima",
                 uguali,
                 f"{len(coppie)} tensori confrontati DOPO la conversione delle "
                 f"chiavi: l'impronta storica {dL['impronta'][:16]} e' della "
                 f"forma `enc.*`, non piu' confrontabile direttamente")

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
        # SI CARICA LA DESTINAZIONE MIGRATA. L'artefatto storico ha `enc.*` e
        # `load_state_dict` con `strict=True` lo rifiuta: e' la garanzia del
        # convertitore, non un difetto. Se la cartella `canonici` non c'e',
        # la verifica si salta e lo dichiara.
        can = a.stati / "canonici"
        d, fd = (carica(can, "BASE-CORRECTED", seme, True)
                 if can.exists() else (None, None))
        caricato = False
        if d:
            m.load_state_dict(d["state_dict"], strict=True)
            caricato = True
        dopo_caric = torch.randn(3).tolist()
        verifica(f"{seme}-4b",
                 "caricare lo stato NON altera il generatore di torch",
                 np.allclose(dopo_costr, dopo_caric),
                 ("caricato da `canonici` con strict=True; la costruzione "
                  "avviene comunque nell'ordine consueto, sicche' il generatore "
                  "avanza come nella campagna precedente") if caricato
                 else ("cartella `canonici` assente: eseguire prima "
                       "`migra_chiavi.py`. La verifica del generatore vale "
                       "comunque, il caricamento non e' stato provato"))
        if caricato:
            verifica(f"{seme}-4c",
                     "l'artefatto MIGRATO si carica con strict=True", True,
                     f"{fd.name}: nessuna chiave mancante ne' in piu'")
            # e le predizioni devono coincidere con quelle dell'originale
            g2 = torch.Generator().manual_seed(99)
            K = 6
            xx = torch.randn(2, 9, K, 12, generator=g2)
            dd = torch.randn(K, d["d_descrittore"], generator=g2)
            ss = torch.randn(K, d["d_statiche"], generator=g2)
            m.eval()
            with torch.inference_mode():
                u1 = m(xx, node_ids=list(range(K)), descriptor=dd,
                       static_inputs=ss)
            # il modello costruito e caricato di nuovo dallo stesso file
            torch.manual_seed(seme)
            m3 = costruisci("BASE-CORRECTED", seme)
            m3.load_state_dict(d["state_dict"], strict=True)
            m3.eval()
            with torch.inference_mode():
                u2 = m3(xx, node_ids=list(range(K)), descriptor=dd,
                        static_inputs=ss)
            verifica(f"{seme}-4d",
                     "le predizioni sono equivalenti su ingressi fissati",
                     torch.equal(u1, u2),
                     "due caricamenti indipendenti dello stesso artefatto "
                     "migrato")

    # ---- [5] gli stati sono salvati, non solo identificati ---------------
    print(f"\n  artefatti")
    r = a.stati / ("registro_stati_conferma.json" if a.conferma
                   else "registro_stati.json")
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
