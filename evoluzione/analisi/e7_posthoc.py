#!/usr/bin/env python3
"""
E7 — analisi POST HOC dichiarata, a costo zero (richiesta dal revisore il 7/10
dopo il congelamento dello stadio 1). Non tocca la conclusione di E7.

Domanda: le anomalie (rho(v, D1) > 0 a Londra ep. 2 e Melbourne ep. 2) sono
F' che guadagna o C che perde sui nodi con ingressi radi? Si verifica con
rho(v, wCE di C per nodo) e rho(v, wCE di F'(1 sett.) per nodo), sugli stessi
file di E5, con lo stesso ricampionamento dello stadio 1. Se rho(v, wCE_C) e'
negativa dove l'anomalia compare **e non altrove**, l'anomalia e' spiegata da C;
se e' negativa ovunque, il segno non discrimina e non spiega nulla.

Inoltre: la copertura per episodio (mediana di v e di v7 per citta' x
episodio), perche' la figura dello stadio 1 mostra che e' una proprieta'
dell'episodio oltre che della citta'.

Scrive results/evoluzione/e7_posthoc.json.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/e7_posthoc.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.e7_stadio1 import B_RHO, SEME, _spearman, _wce_nodi  # noqa: E402
from evoluzione.esperimenti.esegui_e5 import (  # noqa: E402
    CITTA, EPISODI, _carica_celle_e5, _fine_periodo, episodi_registrati)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    S1 = json.loads((a.out / "e7_stadio1.json").read_text())
    anomalie = set(S1["decisione"]["anomalie_rho_positiva"])
    celle = _carica_celle_e5(a.out)
    rng = np.random.default_rng(SEME + 1)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    ep_reg = episodi_registrati(a.out)
    R = {"post_hoc": True, "rho": {}, "copertura_episodio": {}, "anomalie_stadio1": sorted(anomalie)}
    print("=" * 84); print("E7 — post hoc dichiarato: C perde o F' guadagna sui nodi radi?"); print("=" * 84)
    for c in CITTA:
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        for e in EPISODI:
            cc = {(p, s): z for (k, c_, p, s), z in celle.items() if k == e and c_ == c}
            parts = sorted({p for p, _ in cc}); semi = sorted({s for _, s in cc})
            t0 = ep_reg[c][e]["t0"]; o7 = GR.origini_acquisizione(ok, t0, t0 + 672)
            v, v7, wC, wF = [], [], [], []
            for p in parts:
                nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])},
                                      _fine_periodo(e, ep_reg[c]))
                vv7, _ = celle_valide(D, nodi["prova"], o7, t0, t0 + 672)
                z0 = cc[(p, semi[0])]
                v.append(z0["celle_valide"].astype("int64")); v7.append(vv7.astype("int64"))
                wC.append(np.mean([_wce_nodi(cc[(p, s)]["A_C"][2], cc[(p, s)]["B_C"][2]) for s in semi], axis=0))
                wF.append(np.mean([_wce_nodi(cc[(p, s)]["A_Fp_672"][2], cc[(p, s)]["B_Fp_672"][2]) for s in semi], axis=0))
            v = np.concatenate(v); v7 = np.concatenate(v7); wC = np.concatenate(wC); wF = np.concatenate(wF)
            R["copertura_episodio"][f"{c}/ep{e}"] = {
                "v_mediana": float(np.median(v)), "v7_mediana": float(np.median(v7)),
                "v_quota": float(np.median(v) / 308), "v7_quota": float(np.median(v7) / (4 * len(o7)))}
            riga = f"{c:11s} ep{e}: v mediana {np.median(v):.0f}/308, v7 {np.median(v7):.0f}/{4 * len(o7)}"
            for nome, w in (("wCE_C", wC), ("wCE_Fp672", wF)):
                for cov_n, cov in (("v", v), ("v7", v7)):
                    okm = np.isfinite(w)
                    r0 = _spearman(cov[okm], w[okm]); rr = []
                    for _ in range(B_RHO):
                        i = rng.integers(0, okm.sum(), okm.sum())
                        if len(np.unique(cov[okm][i])) < 3:
                            continue
                        rr.append(_spearman(cov[okm][i], w[okm][i]))
                    q = np.percentile(rr, [2.5, 97.5])
                    R["rho"][f"{c}/ep{e}/{nome}/{cov_n}"] = {"rho": r0, "ic_nodi": q.tolist(),
                                                              "esclude_zero": bool(q[0] * q[1] > 0)}
            rc, rf = R["rho"][f"{c}/ep{e}/wCE_C/v"], R["rho"][f"{c}/ep{e}/wCE_Fp672/v"]
            an = f"{c}/ep{e}/D1/v" in anomalie
            print(riga + f"; rho(v, wCE_C) {rc['rho']:+.2f} [{rc['ic_nodi'][0]:+.2f}, {rc['ic_nodi'][1]:+.2f}]"
                  f"{'*' if rc['esclude_zero'] else ' '}; rho(v, wCE_F'(1 sett.)) {rf['rho']:+.2f} "
                  f"[{rf['ic_nodi'][0]:+.2f}, {rf['ic_nodi'][1]:+.2f}]{'*' if rf['esclude_zero'] else ' '}"
                  + ("   <- anomalia dello stadio 1" if an else ""))
    # Il segno di rho(v, wCE_C) spiega l'anomalia solo se DISCRIMINA: negativo
    # dove l'anomalia compare e non altrove. Si contano le celle, non si assume.
    celle = [f"{c}/ep{e}" for c in CITTA for e in EPISODI]
    an_celle = {f"{c}/ep{e}" for c in CITTA for e in EPISODI if f"{c}/ep{e}/D1/v" in anomalie}
    neg = {k for k in celle if R["rho"][f"{k}/wCE_C/v"]["esclude_zero"] and R["rho"][f"{k}/wCE_C/v"]["ic_nodi"][1] < 0}
    R["segno_C"] = {"celle": len(celle), "negative": len(neg), "anomale": len(an_celle),
                    "anomale_negative": len(neg & an_celle), "non_anomale_negative": len(neg - an_celle),
                    "discrimina": bool(neg == an_celle)}
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (a.out / "e7_posthoc.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    s = R["segno_C"]
    print("\n" + "=" * 84)
    print(f"  rho(v, wCE_C) negativa che esclude lo zero in {s['negative']}/{s['celle']} celle; "
          f"celle anomale {s['anomale']}, di cui negative {s['anomale_negative']}; "
          f"celle non anomale negative {s['non_anomale_negative']}")
    print("  -> il segno di rho(v, wCE_C) " + ("DISCRIMINA le celle anomale: anomalia spiegata da C"
                                               if s["discrimina"] else
                                               "NON discrimina le celle anomale: l'anomalia non e' spiegata da C"))
    print(f"  salvato in {a.out / 'e7_posthoc.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
