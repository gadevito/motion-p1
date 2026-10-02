#!/usr/bin/env python3
"""
E3, controllo 2 — la rete esistente prima e dopo il riaddestramento.
======================================================================
**R non deve peggiorare la rete esistente.** Si valutano, sui NODI INIZIALI
e sulle stesse origini di prova dei nodi nuovi (dopo t1):

    C        il modello senza identita' gia' in esercizio
    E        il modello con identita' appresa, sui soli nodi iniziali
    R        riaddestramento ingenuo (uniforme per nodo)
    R-orig   riaddestramento leale (uniforme per origine)
    R-mon    R-orig con la selezione sorvegliata

Stesse celle (seme, partizione, nodo iniziale) per i cinque: i confronti
R-orig − C e R-orig − E sono appaiati. Si salvano gli aggregati A/B per nodo,
non le probabilita' (630 nodi x 1.500 origini x 4 x 3 per 540 valutazioni
sarebbero decine di GB), in `predizioni_veterani_e3/`.

L'analisi e' in `analisi/analizza_veterani_e3.py`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/veterani_e3.py --piano
    poetry run python evoluzione/esperimenti/veterani_e3.py --lavoratori 8
"""
import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

BRACCI = ("C", "E", "R", "R-orig", "R-mon")
DIR_PRED = "predizioni_veterani_e3"
CITTA = ("Madrid", "Londra", "Melbourne")


def _cella(args):
    c, p, s, out, fili = args
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.bracci import proprieta as proprieta_braccio
    from evoluzione.componente.adattamento import carica_E, copia_da_E
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _normalizzazione, _partizioni)
    from evoluzione.esperimenti.esegui_e2 import D_STAT, valuta
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import _modello_da_ck, statiche
    from evoluzione.esperimenti.ricostruisci_predizioni import aggregati_per_nodo
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
    out = Path(out)
    t_in = time.time()
    try:
        D = _carica(c, out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        t0, t1 = CALENDARIO[c]
        fine = D["r"].shape[0] - max(ORIZZONTI)
        per = GR.origini_dopo(ok, t1, fine)
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[p])})
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        stat = statiche(D)
        pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(),
                          dtype="float64")
        ini = nodi["addestramento"]
        S = torch.as_tensor(stat[ini])
        esiti = {}
        for b in BRACCI:
            g = out / DIR_PRED / f"{b}_{c}_p{p}_s{s}.npz"
            if g.exists():
                esiti[b] = "presente"; continue
            # E e' preparatorio: il suo punto sta in E_inserimento_griglia,
            # non nella cartella della fase 3. Lo dice la tabella.
            if proprieta_braccio(b).preparatorio:
                fE = percorso_E(out / "E_inserimento_griglia", c, p, seme_torch(s))
                dE, nodi_in, imp = carica_E(fE, D_STAT)
                if [int(z) for z in nodi_in] != [int(z) for z in ini]:
                    raise RuntimeError(f"E {c} p{p} s{s}: nodi iniziali diversi")
                m, _ = copia_da_E(dE, nodi_in, [], D_STAT)
                with torch.no_grad():
                    m.identita.iniziali.copy_(dE["state_dict"]["identita.embedding"])
            else:
                ck = out / "inserimento_griglia" / f"ck_{b}_{c}_p{p}_s{s}.pt"
                m, d = _modello_da_ck(ck, D, nodi, None)
                if (d["contesto"], d["partizione"], d["braccio"]) != (c, p, b):
                    raise RuntimeError(f"{ck.name}: provenienza incoerente")
                imp = str(d.get("aggiornamento", ""))
            PB, YY, MM, w, ph, dt = valuta(m, x, D["classe"], ini, per, S, pesi)
            A, Bm, N = aggregati_per_nodo(PB, YY, MM, pesi)
            del PB
            g.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(g, A_per_nodo=A, B_per_nodo=Bm, celle_per_nodo=N,
                                wce=w, per_orizzonte=ph,
                                nodi=np.asarray(ini, dtype="int32"),
                                origini=np.asarray(per, dtype="int32"),
                                contesto=c, partizione=p, seme=s, braccio=b,
                                t1=t1, impronta_ck=imp)
            esiti[b] = f"{w:.5f}"
        return {"contesto": c, "partizione": p, "seme": s, "esito": "ok",
                "wce": esiti, "secondi": time.time() - t_in}
    except Exception as e:                                   # noqa: BLE001
        return {"contesto": c, "partizione": p, "seme": s, "esito": "fallita",
                "errore": f"{type(e).__name__}: {e}"[:300],
                "secondi": time.time() - t_in}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lavoratori", type=int, default=8)
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    from evoluzione.esperimenti.semi import configurazione
    _, dich, _ = configurazione(inserimento=True)
    celle = [(c, p, int(s), str(a.out), a.fili)
             for c in CITTA for p in (0, 1, 2) for s in dich]
    fatte = sum(all((a.out / DIR_PRED / f"{b}_{c}_p{p}_s{s}.npz").exists()
                    for b in BRACCI) for c, p, s, _, _ in celle)
    print("=" * 84)
    print("E3 — VETERANI: la rete esistente prima e dopo il riaddestramento")
    print("=" * 84)
    print(f"  bracci {BRACCI}; {len(celle)} celle x {len(BRACCI)} valutazioni; "
          f"{fatte} celle gia' complete")
    print(f"  uscita: {a.out / DIR_PRED}; {a.lavoratori} processi")
    if a.piano:
        print("  --piano: nessuna valutazione avviata.")
        return 0
    ctx = mp.get_context("spawn")
    t0 = time.time()
    fall = 0
    with ctx.Pool(a.lavoratori) as pool:
        for i, r in enumerate(pool.imap_unordered(_cella, celle), 1):
            if r["esito"] == "fallita":
                fall += 1
                print(f"  [{i:3d}/{len(celle)}] {r['contesto']:11s} p{r['partizione']} "
                      f"s{r['seme']} FALLITA  {r['errore']}", flush=True)
            else:
                print(f"  [{i:3d}/{len(celle)}] {r['contesto']:11s} p{r['partizione']} "
                      f"s{r['seme']}  " + "  ".join(f"{b} {w}" for b, w in r["wce"].items())
                      + f"  {r['secondi']:5.0f}s", flush=True)
    print(f"\n  {len(celle) - fall} celle complete, {fall} fallite, "
          f"{(time.time() - t0) / 60:.1f} min")
    return 0 if not fall else 1


if __name__ == "__main__":
    raise SystemExit(main())
