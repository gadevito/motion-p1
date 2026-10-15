#!/usr/bin/env python3
"""
E4 — la tabella dei costi: F' e la politica gated, dal campione isolato.
========================================================================
**Soltanto dal campione isolato** (un processo, macchina libera): le stesse
celle di E3 (`esegui_inserimento.ISOLATO`: partizione 0, semi 201-203) nelle
tre citta'. I tempi in concorrenza non entrano.

Per ogni cella si misura, in questo processo e con un filo di torch:

    F0'       il modello unico al token: nessun calcolo, nessuna attesa
    F'(24 h)  adattamento di F' su (t0, t0+96]      attesa dati 24 h
    gated     F0' da subito; a tau della citta' (e4_scelta_gated.json)
              adattamento di F' su (t0, t0+tau]     attesa dati tau

Ogni adattamento rimisurato deve riprodurre la wCE concorrente della fase
`valuta` (predizioni_e4) entro 1e-6 relativo, come la rimisura di E3.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/costi_e4.py --piano
    poetry run python evoluzione/esperimenti/costi_e4.py
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.esperimenti.esegui_e4 import (  # noqa: E402
    CITTA, D_STAT, DIR_PRED, _nome_e_token, calendario)
from evoluzione.esperimenti.esegui_inserimento import ISOLATO  # noqa: E402

PASSO_S = 900                                   # un passo della griglia: 15 minuti
TOLLERANZA = 1e-6


def _misura(c, p, s, out: Path, tau, fili):
    import numpy as np
    import torch
    torch.set_num_threads(fili)
    from evoluzione.analisi.pesi import carica as carica_pesi
    from evoluzione.componente import griglia as GR
    from evoluzione.componente.adattamento import adatta, carica_E
    from evoluzione.componente.episodio import lotti_episodio
    from evoluzione.componente.predittore import ORIZZONTI
    from evoluzione.esperimenti.addestramento import (
        _canali, _carica, _normalizzazione, _partizioni)
    from evoluzione.esperimenti.esegui_e2 import da_E1, valuta
    from evoluzione.esperimenti.fasi import percorso_E
    from evoluzione.esperimenti.inserimento import statiche
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE, seme_torch
    E_TOK = _nome_e_token()
    t0, t1 = calendario("prova", c)
    D = _carica(c, out / "maschere")
    ok = GR.passi_regolari(D["ts"])
    fine = D["r"].shape[0] - max(ORIZZONTI)
    per = np.asarray(GR.origini_dopo(ok, t1, fine), dtype="int64")
    nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])})
    nn = nodi["prova"]
    NORM, nr, nv = _normalizzazione(D, nodi, ist)
    x = _canali(D, nr, nv)
    from evoluzione.esperimenti.inserimento import statica_cella
    stat = statica_cella(statiche(D), D, nodi, nn, t0, int(s))
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
    w_t = torch.as_tensor(pesi, dtype=torch.float32)
    S = torch.as_tensor(stat[nn])
    cfgF = json.loads((out / "selezione_F_griglia" / "configurazione_F.json")
                      .read_text())["scelte"][c]
    dEp, nodi_in, imp = carica_E(
        percorso_E(out / f"{E_TOK}_inserimento_griglia", c, p, seme_torch(s), braccio=E_TOK), D_STAT)
    rif = np.load(out / DIR_PRED / f"prova_{c}_p{p}_s{s}.npz", allow_pickle=True)
    if str(rif["impronta_Ep"]) != imp:
        raise RuntimeError(f"{c} p{p} s{s}: impronta di E' diversa dalla fase valuta")
    riga = {"contesto": c, "partizione": p, "seme": s, "tau": tau, "fili_torch": fili,
            "modalita_misura": "isolata", "impronta_Ep": imp, "misure": {}}
    # con tau = mai la politica e' F0' per sempre: nessun adattamento da misurare
    da_misurare = [("Fp_96", 96)] + ([(f"Fp_{tau}", tau)] if tau is not None else [])
    for nome, L in da_misurare:
        if nome in riga["misure"]:
            continue
        o_L = GR.origini_acquisizione(ok, t0, t0 + L)
        # il tempo misurato e' TUTTO cio' che l'installazione richiede dopo
        # i dati: copia del punto, lotti, adattamento
        t_in = time.time()
        m, forn = da_E1(dEp, nodi_in, nn, "token")
        lotti = lotti_episodio(x, D["classe"], stat, nn, o_L)
        n = adatta(m, forn, lotti, w_t, cfgF["passo"], cfgF["aggiornamenti"])
        dt = time.time() - t_in
        _, _, _, w, _, _ = valuta(m, x, D["classe"], nn, per, S, pesi)
        w_conc = float(rif[f"wce_{nome}"])
        rel = abs(w - w_conc) / abs(w_conc)
        if rel > TOLLERANZA:
            raise RuntimeError(f"{c} p{p} s{s} {nome}: wCE isolata {w:.6f} contro "
                               f"concorrente {w_conc:.6f}, scarto {rel:.1e}")
        riga["misure"][nome] = {"L": L, "origini": len(o_L), "aggiornamenti": n,
                                "inserimento_s": dt, "attesa_dati_s": L * PASSO_S,
                                "disponibilita_s": L * PASSO_S + dt,
                                "wce": w, "wce_concorrente": w_conc, "scarto_relativo": rel}
        print(f"  {c:11s} p{p} s{s} {nome:7s} {len(o_L):4d} origini  {dt:7.1f}s  "
              f"wCE {w:.6f} = concorrente (scarto {rel:.1e})", flush=True)
    return riga


def main() -> int:
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--fili", type=int, default=1)
    ap.add_argument("--piano", action="store_true")
    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
    SC = json.loads((a.out / "e4_scelta_gated.json").read_text())["scelta"]
    celle = [(c, ISOLATO["partizione"], s) for c in CITTA for s in ISOLATO["semi"]]
    print("=" * 84)
    print("E4 — COSTI dal campione isolato, un processo")
    print("=" * 84)
    print(f"  {len(celle)} celle: partizione {ISOLATO['partizione']}, semi {ISOLATO['semi']}, "
          f"{a.fili} filo di torch")
    print("  tau per citta' (da e4_scelta_gated.json): "
          + ", ".join(f"{c} {SC[c]['tau']}" for c in CITTA))
    print("  misure: F'(24 h) e F'(tau); ogni wCE deve riprodurre la fase valuta entro 1e-6")
    if a.piano:
        return 0
    righe = []
    for c, p, s in celle:
        righe.append(_misura(c, p, s, a.out, SC[c]["tau"], a.fili))
    med = lambda v: float(np.median(v))  # noqa: E731
    tab = {"F0p": {"esecuzioni_isolate": len(righe), "inserimento_s": 0.0,
                   "attesa_dati_s": 0.0, "disponibilita_s": 0.0,
                   "nota": "il modello unico al token: pronto all'installazione"},
           "Fp": {"esecuzioni_isolate": len(righe),
                  "inserimento_s": med([r["misure"]["Fp_96"]["inserimento_s"] for r in righe]),
                  "attesa_dati_s": 96 * PASSO_S,
                  "disponibilita_s": med([r["misure"]["Fp_96"]["disponibilita_s"] for r in righe])},
           "gated": {}}
    for c in CITTA:
        rc = [r for r in righe if r["contesto"] == c]
        tau = SC[c]["tau"]
        if tau is None:                           # politica = F0' per sempre
            tab["gated"][c] = {"tau": None, "N": SC[c]["N"], "esecuzioni_isolate": len(rc),
                               "primo_modello_s": 0.0, "adattamento_s": 0.0,
                               "attesa_dati_s": 0.0, "disponibilita_adattamento_s": 0.0}
            continue
        k = f"Fp_{tau}"
        tab["gated"][c] = {"tau": tau, "N": SC[c]["N"], "esecuzioni_isolate": len(rc),
                           "primo_modello_s": 0.0,
                           "adattamento_s": med([r["misure"][k]["inserimento_s"] for r in rc]),
                           "attesa_dati_s": tau * PASSO_S,
                           "disponibilita_adattamento_s": med([r["misure"][k]["disponibilita_s"] for r in rc])}
    print("\n  " + f"{'configurazione':16s} {'n':>3} {'calcolo':>9} {'attesa dati':>12} {'disponibile':>12}")
    print(f"  {'F0p':16s} {len(righe):3d} {0:8.1f}s {0:11.0f}h {0:11.1f}h")
    print(f"  {'Fp (24 h)':16s} {len(righe):3d} {tab['Fp']['inserimento_s']:8.1f}s "
          f"{tab['Fp']['attesa_dati_s']/3600:11.0f}h {tab['Fp']['disponibilita_s']/3600:11.1f}h")
    for c in CITTA:
        g = tab["gated"][c]
        print(f"  {'gated ' + c:16s} {g['esecuzioni_isolate']:3d} {g['adattamento_s']:8.1f}s "
              f"{g['attesa_dati_s']/3600:11.0f}h {g['disponibilita_adattamento_s']/3600:11.1f}h"
              f"   (F0' da subito; adattamento a tau = {g['tau']} passi)")
    doc = {"tabella": tab, "celle": righe, "tolleranza": TOLLERANZA,
           "rimisure_che_riproducono_la_concorrente": sum(len(r["misure"]) for r in righe),
           "istante": datetime.now(timezone.utc).isoformat()}
    f = a.out / "costi_e4.json"
    f.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"\n  salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
