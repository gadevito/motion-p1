#!/usr/bin/env python3
"""
Modello a effetti misti e covariata di copertura (§8.8, Tabella 89).
=====================================================================
`stats_tests.py` copre i test dei segni, Friedman, la validazione incrociata e
il blocco delle statiche. NON copre le due analisi di questa sezione, che sono
qui.

IL PUNTO NON E' LA STIMA PUNTUALE, E' IL RAPPORTO FRA LE DUE INCERTEZZE.

I sei contesti NON sono sei unita' indipendenti: quattro appartengono a Madrid,
e due di essi condividono anche la rete di sensori. Raggruppando per CONTESTO si
sfrutta l'appaiamento fra configurazioni valutate sugli stessi dati e con lo
stesso seme; raggruppando per CITTA' si adotta la lettura conservativa sulla
generalizzabilita'. Il fattore fra i due errori standard e' la misura ONESTA di
quanto quella lettura costi, e va riportato ACCANTO all'esito e non dopo.

PERCHE' LA COMPONENTE DI CITTA' RISULTA NULLA. Nel modello annidato la varianza
attribuita alla citta' e' stimata al bordo inferiore dello spazio dei parametri.
NON va letta come assenza di variabilita' fra citta': e' mancata
identificabilita' del parametro con tre gruppi, di cui uno contiene quattro dei
sei contesti. Con questi dati il modello non discrimina fra la struttura per
citta' e quella per contesto, ed e' la ragione per cui si riportano ENTRAMBI gli
errori standard anziche' sceglierne uno.

LA COVARIATA DI COPERTURA VA CENTRATA ENTRO CONTESTO. Il coefficiente misura
cosi' la variazione ENTRO contesto — la componente di compito che si voleva
isolare — e non l'effetto complessivo della copertura fra contesti diversi.
Senza il centramento le due cose si confondono.

Uso (dalla radice OR3/):

    poetry run python analisi/effetti_misti.py
    poetry run python analisi/effetti_misti.py --copertura replication/copertura.csv
"""
from pathlib import Path
import argparse
import glob as globmod

import numpy as np
import pandas as pd

CITTA = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
         "d8_2024": "Madrid", "d15_2024": "Madrid", "d8_2023": "Madrid"}
ETICHETTA = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
             "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}


def raccogli(a) -> pd.DataFrame:
    """Una riga per contesto, seme e ramo, con la wCE media sugli orizzonti."""
    righe = []
    for c in CITTA:
        for s in range(a.semi):
            for schema, ramo, modello in (
                    (a.classify, "neurale", "gwn_none"),
                    (a.lgb, "tabellare", "lgb_fair")):
                f = globmod.glob(schema.format(c=c, s=s))
                if not f:
                    continue
                d = pd.read_csv(f[0])
                q = d[d.model == modello]
                if not len(q):
                    continue
                righe.append(dict(contesto=c, citta=CITTA[c], seme=s,
                                  ramo=ramo, wCE=q.wCE.mean()))
    return pd.DataFrame(righe)


def misto(d: pd.DataFrame, gruppo: str):
    """Modello a effetti misti con intercetta casuale sul gruppo indicato."""
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        return None
    m = smf.mixedlm("wCE ~ ramo", d, groups=d[gruppo]).fit(reml=True)
    nome = [x for x in m.params.index if x.startswith("ramo")]
    if not nome:
        return None
    k = nome[0]
    vg = float(m.cov_re.iloc[0, 0]) if m.cov_re.size else 0.0
    return dict(stima=float(m.params[k]), se=float(m.bse[k]),
                var_gruppo=vg, var_res=float(m.scale),
                icc=vg / (vg + float(m.scale)) if (vg + m.scale) > 0 else 0.0,
                llf=float(m.llf), n=len(d), gruppi=d[gruppo].nunique())


def main() -> int:
    ap = argparse.ArgumentParser(description="effetti misti e covariata di copertura")
    ap.add_argument("--classify", default="replication/classify_{c}_s{s}.csv")
    ap.add_argument("--lgb", default="replication/lgbristr_{c}_s{s}.csv")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--copertura", type=Path, default=None,
                    help="CSV con colonne contesto, seme, copertura, wCE_none, wCE_fixed")
    a = ap.parse_args()

    d = raccogli(a)
    if d.empty:
        print("nessun CSV trovato: verificare gli schemi --classify e --lgb")
        return 1
    print(f"osservazioni raccolte: {len(d)}  "
          f"({d.contesto.nunique()} contesti, {d.citta.nunique()} citta, "
          f"{d.seme.nunique()} semi)\n")

    print("=" * 92)
    print("TABELLA 89 - specificazioni alternative del raggruppamento")
    print("=" * 92)
    esiti = {}
    for eti, g in (("Solo citta (3 gruppi)", "citta"),
                   ("Solo contesto (6 gruppi)", "contesto")):
        r = misto(d, g)
        if r is None:
            print(f"{eti:28s} statsmodels non disponibile: poetry add statsmodels")
            continue
        esiti[g] = r
        print(f"{eti:28s} varianza di gruppo {r['var_gruppo']:.6f}  "
              f"residua {r['var_res']:.6f}  ICC {r['icc']:.3f}  "
              f"log-verosimiglianza {r['llf']:.2f}")

    if len(esiti) == 2:
        print()
        print(f"{'raggruppamento':22s} {'gruppi':>7} {'stima':>12} {'errore standard':>17}")
        for g, eti in (("contesto", "per contesto"), ("citta", "per citta")):
            r = esiti[g]
            print(f"{eti:22s} {r['gruppi']:7d} {r['stima']:+12.4f} {r['se']:17.4f}")
        f = esiti["citta"]["se"] / max(esiti["contesto"]["se"], 1e-12)
        print(f"\n  rapporto fra gli errori standard: {f:.1f}x")
        print("  E' la misura ONESTA di quanto costa la lettura conservativa, e va")
        print("  riportata ACCANTO all'esito e non dopo di esso.")
        print("\n  La componente di citta' stimata al bordo inferiore NON significa assenza")
        print("  di variabilita' fra citta': e' mancata identificabilita' con tre gruppi,")
        print("  di cui uno contiene quattro dei sei contesti. Per questo si riportano")
        print("  ENTRAMBI gli errori standard anziche' sceglierne uno.")

    if a.copertura and a.copertura.exists():
        print("\n" + "=" * 92)
        print("COVARIATA DI COPERTURA, centrata entro contesto")
        print("=" * 92)
        cv = pd.read_csv(a.copertura)
        cv["vantaggio"] = 100 * (cv.wCE_none - cv.wCE_fixed) / cv.wCE_none
        cv["cop_c"] = cv.copertura - cv.groupby("contesto").copertura.transform("mean")
        try:
            import statsmodels.formula.api as smf
            m = smf.mixedlm("vantaggio ~ cop_c", cv, groups=cv["contesto"]).fit(reml=True)
            b, se = float(m.params["cop_c"]), float(m.bse["cop_c"])
            lo, hi = b - 1.96 * se, b + 1.96 * se
            esc = float(cv.copertura.max() - cv.copertura.min())
            print(f"coefficiente {b:+.3f}  errore standard {se:.3f}  "
                  f"p = {float(m.pvalues['cop_c']):.3f}  n = {len(cv)}")
            print(f"intervallo [{lo:+.3f}; {hi:+.3f}]")
            print(f"escursione della copertura {esc:.3f}  "
                  f"-> effetto all'estremo dell'intervallo {abs(hi) * esc:.4f}")
            print("\n  La covariata e' CENTRATA ENTRO CONTESTO: il coefficiente misura la")
            print("  variazione entro contesto, cioe' la componente di compito che si voleva")
            print("  isolare, non l'effetto della copertura fra contesti diversi.")
            print("\n  La lettura corretta e' che NON vi sia evidenza di un effetto E che la")
            print("  potenza non basti a escluderlo: l'intervallo e' ampio e all'estremo")
            print("  corrisponderebbe a una quota non trascurabile dell'effetto misurato.")
        except ImportError:
            print("statsmodels non disponibile")
    else:
        print("\ncovariata di copertura: passare --copertura con il CSV di copertura")
        print("(colonne: contesto, seme, copertura, wCE_none, wCE_fixed)")
        print("La copertura realizzata e' stampata da gomo_sparse.py a ogni invocazione.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
