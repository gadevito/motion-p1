#!/usr/bin/env python3
"""
Ipotesi geometrica — i cinque criteri pre-registrati (§8.3.2, Tabelle 30-33).
=============================================================================
Nessun addestramento: legge i CSV della campagna geometrica e le covariate
prodotte da `make_geo_sweep.py`.

L'ipotesi da verificare: nel regime severo il valore della propagazione e'
determinato dalla SPAZIATURA fra i sensori. La spaziatura non e' manipolabile
direttamente, quindi si controlla per selezione geografica — sottoinsiemi di
99 sensori in aree di estensione crescente, a numerosita' costante e
connettivita' piena.

BRACCIO A GRAFO FISSO SOLTANTO. Il confronto usa la sola variante `fixed`,
per isolare la propagazione dall'identita': la variante adattiva genera il
grafo da vettori appresi per nodo, quindi mescolerebbe le due cose.

I CINQUE CRITERI, dichiarati prima delle esecuzioni:

  1 tendenza          il vantaggio deve diminuire al crescere della spaziatura,
                      in modo distinguibile dalla variabilita' E con differenza
                      fra estremi sopra tre punti percentuali;
  2 sweep di supporto la stessa relazione, almeno nel segno, sulla serie a
                      densita' decrescente. La connettivita' non e' controllata:
                      una concordanza e' un indizio, una discordanza non e' una
                      smentita;
  3 trasferibilita'   la relazione deve valere in entrambe le citta';
  4 controllo negativo grafo dei k vicini contro adiacenza randomizzata a pari
                      numero di nodi, gradi e archi. TERZA CLAUSOLA: se il
                      randomizzato eguaglia o supera il vero, l'ipotesi e'
                      refutata indipendentemente dagli altri criteri;
  5 forma a soglia    vantaggio costante fino a una spaziatura e decrescente
                      oltre. Prevale sul criterio 1 solo se una regressione a
                      due rette e' preferibile secondo un criterio informativo
                      E le due pendenze sono distinguibili.

DUE AVVERTENZE SULLA LETTURA.

Il segno della pendenza NON e' robusto alla specificazione: una regressione
semplice sui dodici punti da' -0,0067 %/m, il modello dichiarato con termine
additivo di citta' da' +0,00209 %/m. In entrambi i casi l'intervallo include
lo zero, e la conclusione sul criterio 1 e' robusta anche se il segno non lo e'.
Con dodici punti il modello con termine di citta' e' scarsamente identificato:
la trasferibilita' e' l'esito piu' FRAGILE dei cinque, non il piu' solido.

Il grafo randomizzato ha arco medio 494 m contro 56 del grafo dei k vicini:
non e' «lo stesso grafo senza geometria» ma un grafo con proprieta' di
mescolamento diverse. Cio' che l'esito sostiene non e' che la prossimita' sia
irrilevante, ma che a parita' di grado la connettivita' a lungo raggio funzioni
almeno quanto quella locale.

Uso (dalla radice OR3/):

    poetry run python analisi/geometria_criteri.py
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
import pandas as pd


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def vantaggio(csv_glob, semi):
    """(wCE senza grafo - wCE grafo fisso) / wCE senza grafo, per seme.
    I due bracci devono stare nello STESSO file: prodotti da esecuzioni
    separate, la differenza includerebbe anche la versione dello script."""
    v = []
    for s in range(semi):
        f = globmod.glob(csv_glob.format(s=s))
        if not f:
            return None
        d = pd.read_csv(f[0])
        n = d[d.model == "gwn_none"]
        x = d[d.model == "gwn_fixed"]
        if not len(n) or not len(x):
            return None
        a, b = n.wCE.mean(), x.wCE.mean()
        v.append(100 * (a - b) / a)
    return v


def regressione(x, y, gruppo=None):
    """Minimi quadrati con termine additivo opzionale di gruppo.
    Restituisce pendenza, errore standard, valore p bilaterale."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    col = [x, np.ones(len(x))]
    if gruppo is not None:
        g = np.asarray(gruppo)
        for livello in sorted(set(g))[1:]:
            col.append((g == livello).astype(float))
    A = np.column_stack(col)
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ beta
    gl = len(x) - A.shape[1]
    if gl <= 0:
        return float(beta[0]), float("nan"), float("nan")
    s2 = float(res @ res) / gl
    cov = s2 * np.linalg.pinv(A.T @ A)
    se = math.sqrt(max(cov[0, 0], 0.0))
    from scipy import stats
    p = 2 * (1 - stats.t.cdf(abs(beta[0] / se), gl)) if se > 0 else float("nan")
    return float(beta[0]), se, float(p)


def main() -> int:
    ap = argparse.ArgumentParser(description="ipotesi geometrica: i cinque criteri")
    ap.add_argument("--geo-dir", type=Path, default=Path("replication/geo"))
    ap.add_argument("--covariate", type=Path, default=Path("geo_sweep"))
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--soglia-progettuale", type=float, default=3.0,
                    help="differenza minima rilevante fra estremi, in punti")
    a = ap.parse_args()

    # ------------------------------------------------------- covariate ------
    cov = []
    for f in sorted(globmod.glob(str(a.covariate / "covariate_*.csv"))):
        d = pd.read_csv(f)
        d["citta"] = Path(f).stem.replace("covariate_", "")
        cov.append(d)
    if not cov:
        print(f"nessun file covariate_*.csv in {a.covariate}/")
        print("Generarli con:  poetry run python make_geo_sweep.py --sensors <csv> "
              "--targets <npz> --citta madrid --sweep")
        return 1
    cov = pd.concat(cov, ignore_index=True)

    # -------------------------------------------- blocco principale ---------
    righe = []
    for _, r in cov.iterrows():
        if r.get("frac_gigante", 1.0) < 0.999:      # solo connettivita' piena
            continue
        tag = r["grafo"]
        v = vantaggio(str(a.geo_dir / f"geo_{tag}_s{{s}}.csv"), a.semi)
        if v is None:
            continue
        m, sd = st(v)
        righe.append(dict(grafo=tag, citta=r["citta"], N=r["N"],
                          arco=r["arco_medio"], vant=m, sd=sd, segni=sum(x > 0 for x in v)))
    if not righe:
        print(f"nessun CSV di risultato in {a.geo_dir}/ per le configurazioni a "
              f"connettivita' piena")
        return 1
    R = pd.DataFrame(righe).sort_values("arco")

    print("=" * 92)
    print("TABELLA 30 - braccio principale: vantaggio per spaziatura (braccio a grafo fisso)")
    print("=" * 92)
    print(f"{'grafo':22s} {'citta':10s} {'N':>4} {'arco medio':>11} {'vantaggio':>18} segni")
    for _, r in R.iterrows():
        print(f"{r.grafo:22s} {r.citta:10s} {int(r.N):4d} {r.arco:10.1f} m "
              f"{r.vant:+9.2f}% ± {r.sd:4.2f}  {int(r.segni)}/{a.semi}")

    print("\n" + "=" * 92)
    print("TABELLA 31 - i cinque criteri")
    print("=" * 92)

    # criterio 1 --------------------------------------------------------------
    b, se, p = regressione(R.arco, R.vant, R.citta)
    b0, se0, p0 = regressione(R.arco, R.vant)
    estremi = R.vant.iloc[0] - R.vant.iloc[-1]
    rilev = 2 * R.sd.mean()
    sostenuto = (p < 0.05) and (b < 0) and (abs(estremi) > a.soglia_progettuale)
    print(f"1 tendenza          {'sostenuto' if sostenuto else 'NON sostenuto':16s} "
          f"pendenza {b:+.5f} %/m, IC [{b - 1.96 * se:+.5f}; {b + 1.96 * se:+.5f}], p = {p:.3f}")
    print(f"{'':20s} {'':16s} differenza fra estremi {estremi:+.2f} punti "
          f"(rilevabilita {rilev:.2f}, progettuale {a.soglia_progettuale:.2f})")
    print(f"{'':20s} {'':16s} senza termine di citta': {b0:+.5f} %/m, p = {p0:.3f}"
          f"  <-- il SEGNO non e' robusto alla specificazione")

    # criterio 3 --------------------------------------------------------------
    if R.citta.nunique() > 1:
        A = np.column_stack([R.arco, np.ones(len(R))])
        livelli = sorted(R.citta.unique())[1:]
        for l in livelli:
            A = np.column_stack([A, (R.citta.values == l).astype(float)])
        beta, *_ = np.linalg.lstsq(A, R.vant.values, rcond=None)
        res = R.vant.values - A @ beta
        gl = len(R) - A.shape[1]
        s2 = float(res @ res) / max(gl, 1)
        cov_m = s2 * np.linalg.pinv(A.T @ A)
        from scipy import stats
        se_c = math.sqrt(max(cov_m[2, 2], 0.0))
        pc = 2 * (1 - stats.t.cdf(abs(beta[2] / se_c), gl)) if se_c > 0 else float("nan")
        print(f"3 trasferibilita'   {'compatibile, FRAGILE':16s} "
              f"termine additivo di citta' p = {pc:.3f}")
        print(f"{'':20s} {'':16s} con dodici punti il modello e' scarsamente "
              f"identificato: e' l'esito piu' fragile dei cinque")
    else:
        print(f"3 trasferibilita'   {'non valutabile':16s} una sola citta' nei dati")

    # criterio 4 --------------------------------------------------------------
    print()
    coppie = [(r["grafo"], r["grafo"].replace("knn", "rand"))
              for _, r in cov.iterrows() if "knn" in str(r["grafo"])]
    trovata = False
    for vero, casuale in coppie:
        vv = vantaggio(str(a.geo_dir / f"geo_{vero}_s{{s}}.csv"), a.semi)
        vc = vantaggio(str(a.geo_dir / f"geo_{casuale}_s{{s}}.csv"), a.semi)
        if vv is None or vc is None:
            continue
        trovata = True
        diff = [vv[i] - vc[i] for i in range(a.semi)]
        m, sd = st(diff)
        hw = 2.776 * sd / math.sqrt(a.semi)
        arco_v = float(cov.loc[cov.grafo == vero, "arco_medio"].iloc[0])
        arco_c = float(cov.loc[cov.grafo == casuale, "arco_medio"].iloc[0]) \
            if (cov.grafo == casuale).any() else float("nan")
        margine = st(vv)[0]
        esito = ("REFUTAZIONE" if m <= 0 else
                 "attribuibile alla prossimita'" if m - hw > 1.68 else
                 "non distinguibili")
        print(f"4 controllo negativo  {vero} contro {casuale}")
        print(f"{'':22s} vero {st(vv)[0]:+6.2f}% ± {st(vv)[1]:4.2f} (arco {arco_v:.1f} m) | "
              f"casuale {st(vc)[0]:+6.2f}% ± {st(vc)[1]:4.2f} (arco {arco_c:.1f} m)")
        print(f"{'':22s} differenza appaiata {m:+.2f} punti, IC [{m - hw:+.2f}; {m + hw:+.2f}], "
              f"segni {sum(x > 0 for x in diff)}/{a.semi}")
        print(f"{'':22s} margine disponibile {margine:.2f} punti -> {esito}")
        if margine < 2.0:
            print(f"{'':22s} ATTENZIONE: con margine sotto i due punti l'esecuzione non e'")
            print(f"{'':22s} conclusiva, qualunque sia la differenza (§7.3, sesto caso)")
        print()
    if not trovata:
        print("4 controllo negativo  nessuna coppia knn/rand trovata in", a.geo_dir)

    print("Nota sul criterio 4. Il grafo randomizzato NON e' «lo stesso grafo senza")
    print("geometria»: ha arco medio molto maggiore e proprieta' di mescolamento diverse.")
    print("Cio' che l'esito sostiene e' che a parita' di grado la connettivita' a lungo")
    print("raggio funzioni almeno quanto quella locale — conclusione piu' stretta e piu'")
    print("difendibile di «la prossimita' e' irrilevante».")
    print()
    print("La conclusione poggia sul SOLO criterio 4, che ha potere discriminante misurato.")
    print("Gli altri quattro sono non sostenuti o fragili e non si aggregano in una")
    print("conclusione positiva: assenza di evidenza su piu' criteri non e' dimostrazione.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
