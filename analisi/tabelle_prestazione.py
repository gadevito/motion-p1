#!/usr/bin/env python3
"""
Tabelle di prestazione assoluta (§8.1, Tabelle 18, 19, 20) e loro lettura.
==========================================================================
Aggrega i CSV della campagna a cinque semi e produce:

  * Tabella 18 - entropia pesata per modello e contesto;
  * Tabella 19 - richiamo sulla classe critica, con dispersione fra semi;
  * Tabella 20 - precisione sulla classe critica al punto di lavoro predefinito;
  * le correlazioni di rango fra le tre metriche entro ciascun contesto, che
    sostengono l'affermazione che l'ordinamento della precisione NON coincide
    con quello dell'entropia ed e' invece inverso a quello del richiamo;
  * il rapporto di sovra-predizione della classe critica sotto la regola
    predefinita, calcolato dai dump di probabilita' quando disponibili.

Avvertenza sul filtro. `replication/ALL_results.csv` contiene piu' esperimenti
nella stessa tabella (`classify`, `lgb`, `rnn`, `sota`, `sparse`). Le medie
della suite densa vanno prese dalle righe `classify` / `lgb` / `rnn` / `sota`:
senza filtrare la colonna `experiment` le righe `sparse`, che appartengono al
regime severo, contaminano i modelli GWN e il priore.

Perche' la precisione e il richiamo vanno letti insieme. Entrambi sono
conseguenza della regola di decisione predefinita, che assegna la classe a
probabilita' massima, e non proprieta' indipendenti dei modelli: il
classificatore neurale assegna la classe critica da 1,9 a 4,1 volte piu'
spesso della sua frequenza vera, il riferimento tabellare da 1,4 a 2,6 volte.
Il richiamo elevato e la precisione bassa sono la stessa distorsione vista da
due lati. Il punto di lavoro dispiegabile si ottiene tarando le soglie sulla
validazione (§8.6.6).

Uso (dalla radice OR3/):

    poetry run python analisi/tabelle_prestazione.py \
        --risultati "replication/ALL_results.csv" \
        --dump-dir replication/probs
"""
from pathlib import Path
import argparse
import glob as globmod

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ORDINE = [
    ("gwn_adaptive", "Graph WaveNet (con grafo)"),
    ("gwn_none", "Graph WaveNet (senza grafo)"),
    ("stid", "MLP per-nodo (STID-style)"),
    ("agcrn", "AGCRN"),
    ("staeformer", "STAEformer"),
    ("dcrnn", "DCRNN"),
    ("lgb_fair", "LightGBM a parita' di informazione"),
    ("hist_prior", "Priore storico"),
]
CONTESTI = ["t4cmad", "t4clon", "t4cmel", "d8_2024", "d15_2024", "d8_2023"]
ETICHETTE = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
             "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023"}
ESPERIMENTI_DENSI = ("classify", "lgb", "rnn", "sota")


def carica(percorso_glob: str) -> pd.DataFrame:
    file = sorted(globmod.glob(percorso_glob))
    if not file:
        raise SystemExit(f"nessun file corrisponde a {percorso_glob}")
    d = pd.concat([pd.read_csv(f) for f in file], ignore_index=True)
    if "experiment" in d.columns:
        prima = len(d)
        d = d[d.experiment.isin(ESPERIMENTI_DENSI)]
        print(f"filtro sulla colonna `experiment`: {prima:,} -> {len(d):,} righe "
              f"(escluse le righe del regime severo)")
    return d


def componi(a) -> pd.DataFrame:
    """Ricompone le metriche dalle campagne che le contengono davvero.

    `ALL_results.csv` NON ha la colonna della precisione — quella nasce dalla
    campagna dedicata — e vi entra il riferimento tabellare sulla popolazione
    PIENA, mentre le Tabelle 18-20 usano quella ristretta (§6.2.1). Leggere un
    solo file darebbe quindi tabelle e correlazioni incoerenti fra loro.

    Per ciascun modello si prende quindi la prima campagna disponibile fra
    quelle dichiarate, e si stampa da quale: la provenienza fa parte del
    risultato, non e' un dettaglio di implementazione.
    """
    SORGENTI = {
        "gwn_adaptive": ["fix_classify", "prec_classify", "camp_classify", "classify"],
        "gwn_none":     ["fix_classify", "prec_classify", "camp_classify", "classify"],
        "hist_prior":   ["fix_classify", "prec_classify", "camp_classify", "classify"],
        "gwn_stid":     ["prec_classify", "fix_classify", "camp_classify", "stid"],
        "agcrn":        ["fixgraph_rnn", "prec_rnn", "camp_rnn", "rnn"],
        "dcrnn":        ["fixgraph_rnn", "prec_rnn", "camp_rnn", "rnn"],
        "staeformer":   ["fixgraph_sota", "prec_sota", "camp_sota", "sota"],
        "t4c_gnn":      ["fixgraph_sota", "prec_sota", "camp_sota", "sota"],
        "lgb_fair":     [a.lgb_ristretto],
    }
    righe, prov = [], {}
    for c in CONTESTI:
        for m, prefissi in SORGENTI.items():
            for pref in prefissi:
                v = []
                for s in range(a.semi):
                    f = sorted(set(globmod.glob(f"**/{pref}_{c}_s{s}.csv", recursive=True)))
                    if not f:
                        break
                    d = pd.read_csv(f[0])
                    q = d[d.model == m]
                    if not len(q):
                        break
                    v.append({k: q[k].mean() for k in ("wCE", "red_recall", "red_prec")
                              if k in q.columns})
                if len(v) >= 3:
                    for s, r in enumerate(v):
                        righe.append(dict(model=m, context=c, seed=s, **r))
                    prov[(m, c)] = (pref, len(v))
                    break
    if not righe:
        return pd.DataFrame()
    print("provenienza dei valori (campagna, semi):")
    for m in SORGENTI:
        p = {prov[(m, c)] for c in CONTESTI if (m, c) in prov}
        if p:
            print(f"   {m:14s} " + ", ".join(f"{x[0]} ({x[1]} semi)" for x in sorted(p)))
    mancanti = [(m, c) for m in SORGENTI for c in CONTESTI if (m, c) not in prov]
    if mancanti:
        print(f"   non trovati: {len(mancanti)} coppie modello-contesto")
    print()
    return pd.DataFrame(righe)


def tabella(d: pd.DataFrame, colonna: str, con_dispersione: bool) -> None:
    print(f"\n{'modello':36s} " + " ".join(f"{ETICHETTE[c]:>16}" for c in CONTESTI))
    for chiave, nome in ORDINE:
        celle = []
        for c in CONTESTI:
            q = d[(d.model == chiave) & (d.context == c)] if "context" in d.columns \
                else d[d.model == chiave]
            if not len(q) or colonna not in q.columns or q[colonna].isna().all():
                celle.append(f"{'—':>16}")
                continue
            per_seme = q.groupby("seed")[colonna].mean() if "seed" in q.columns \
                else pd.Series([q[colonna].mean()])
            m = per_seme.mean()
            if con_dispersione and len(per_seme) > 1:
                celle.append(f"{m:9.3f} ± {per_seme.std(ddof=1):4.3f}")
            else:
                celle.append(f"{m:16.4f}")
        print(f"{nome:36s} " + " ".join(celle))


def correlazioni(d: pd.DataFrame) -> None:
    """Correlazioni di rango fra le tre metriche, ENTRO ciascun contesto.

    Descrivono l'ordinamento dei modelli dentro un contesto, non una relazione
    fra contesti: sono sei coefficienti per ciascuna coppia di metriche, e NON
    sono stime corredate da incertezza.

    LA COMPOSIZIONE VA DICHIARATA. I coefficienti dipendono da quali modelli
    entrano nell'ordinamento, e con otto punti l'inversione di due modelli
    vicini sposta sensibilmente il valore. Lo script stampa quindi sempre i
    modelli effettivamente usati e il loro numero, contesto per contesto.

    E DIPENDONO DALLA POPOLAZIONE DEL RIFERIMENTO TABELLARE. Il metodo
    tabellare entra nelle Tabelle 18-20 con la popolazione ristretta (§6.2.1):
    calcolare le correlazioni su valori di popolazione piena le rende
    incoerenti con le tabelle che commentano. Il filtro sulla colonna
    `experiment` e la scelta della campagna vanno quindi fatti UNA volta sola,
    a monte, e valere per tabelle e correlazioni insieme.
    """
    print(f"\n{'contesto':10s} {'modelli':>8} {'wCE vs precisione':>20} "
          f"{'richiamo vs precisione':>24}")
    a, b, comp = [], [], None
    for c in CONTESTI:
        q = d[d.context == c] if "context" in d.columns else d
        agg = q.groupby("model")[["wCE", "red_recall", "red_prec"]].mean().dropna()
        if len(agg) < 4:
            print(f"{ETICHETTE[c]:10s} dati insufficienti ({len(agg)} modelli)")
            continue
        r1 = spearmanr(agg.wCE, agg.red_prec).statistic
        r2 = spearmanr(agg.red_recall, agg.red_prec).statistic
        a.append(r1); b.append(r2)
        if comp is None:
            comp = sorted(agg.index)
        elif sorted(agg.index) != comp:
            print(f"{'':10s} ATTENZIONE: composizione diversa dagli altri contesti")
        print(f"{ETICHETTE[c]:10s} {len(agg):8d} {r1:+20.3f} {r2:+24.3f}")
    if comp:
        print(f"\n  composizione ({len(comp)} modelli): {', '.join(comp)}")
    if a:
        print(f"  precisione vs entropia: [{min(a):+.2f}; {max(a):+.2f}]   "
              f"positiva in {sum(1 for x in a if x > 0)}/{len(a)} contesti")
        print(f"  precisione vs richiamo: [{min(b):+.2f}; {max(b):+.2f}]   "
              f"negativa in {sum(1 for x in b if x < 0)}/{len(b)} contesti")
    print("\n  I due coefficienti vanno letti insieme alle Tabelle 17-19 e ricalcolati")
    print("  ogni volta che quelle cambiano: la posizione del metodo tabellare")
    print("  nell'ordinamento dipende dalla popolazione con cui vi entra, e con nove")
    print("  punti basta uno scambio fra modelli vicini a spostare il valore.")


def sovra_predizione(dump_dir: Path) -> None:
    coppie = [("classify", "gwn_none", "neurale senza grafo"),
              ("lgbristr", "lgb_fair", "riferimento tabellare")]
    print(f"\n{'contesto':10s} " + " ".join(f"{e:>24}" for _, _, e in coppie))
    for c in CONTESTI:
        riga = []
        for prefisso, tag, _ in coppie:
            rapporti = []
            for s in range(5):
                f = dump_dir / f"{prefisso}_{c}_s{s}.npz"
                if not f.exists():
                    continue
                z = np.load(f, allow_pickle=True)
                for k in z.files:
                    if not k.startswith("tag"):
                        continue
                    if not str(z[k]).startswith(tag + "|"):
                        continue
                    i = k[3:]
                    P, Y = z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int)
                    freq = max((Y == 2).mean(), 1e-9)
                    rapporti.append((P.argmax(1) == 2).mean() / freq)
            riga.append(f"{np.mean(rapporti):23.2f}x" if rapporti else f"{'—':>24}")
        print(f"{ETICHETTE[c]:10s} " + " ".join(riga))
    print("\n  Rapporto fra la quota di celle cui la regola della classe piu'")
    print("  probabile assegna la classe critica e la frequenza vera di quella")
    print("  classe. Calcolato sui DUMP di probabilita', sulla configurazione")
    print("  priva di scambio spaziale, mediando sui quattro orizzonti e sui semi.")


def main() -> int:
    ap = argparse.ArgumentParser(description="tabelle di prestazione assoluta")
    ap.add_argument("--risultati", default="replication/ALL_results.csv",
                    help="file o glob dei CSV di risultato")
    ap.add_argument("--dump-dir", type=Path, default=Path("replication/probs"))
    ap.add_argument("--semi", type=int, default=5,
                    help="numero massimo di semi da cercare per campagna")
    ap.add_argument("--lgb-ristretto", default="lgbristr",
                    help="prefisso della campagna del riferimento tabellare. "
                         "Le Tabelle 18-20 usano la POPOLAZIONE RISTRETTA (§6.2.1): "
                         "passare qui la campagna piena rende le correlazioni "
                         "incoerenti con le tabelle che commentano")
    args = ap.parse_args()

    d = carica(args.risultati)
    if "red_prec" not in d.columns:
        print("\nLa colonna della precisione non e' negli aggregati: ricompongo dalle")
        print("campagne che la contengono.\n")
        comp = componi(args)
        if len(comp):
            d = comp
        else:
            print("nessuna campagna con precisione trovata: le Tabelle 20 e le")
            print("correlazioni non sono calcolabili.\n")

    print("\n" + "=" * 118)
    print("TABELLA 18 - entropia incrociata pesata (valori minori sono migliori)")
    print("=" * 118)
    tabella(d, "wCE", con_dispersione=False)
    print(f"\n{'Predittore uniforme':36s} " + " ".join(f"{np.log(3):16.4f}" for _ in CONTESTI))
    print("\nIl priore storico e' qui nella variante NON calibrata (Laplace, alpha = 1).")
    print("Per la versione calibrata: poetry run python analisi/priore_calibrato.py")

    print("\n" + "=" * 118)
    print("TABELLA 19 - richiamo sulla classe critica (valori maggiori sono migliori)")
    print("=" * 118)
    tabella(d, "red_recall", con_dispersione=True)

    print("\n" + "=" * 118)
    print("TABELLA 20 - precisione sulla classe critica al punto di lavoro predefinito")
    print("=" * 118)
    if "red_prec" not in d.columns:
        print("colonna `red_prec` assente: la campagna e' anteriore alla patch di `scores()`.")
        print("Rieseguire la campagna della precisione (§8.1) per popolarla.")
    else:
        tabella(d, "red_prec", con_dispersione=True)

    print("\n" + "=" * 118)
    print("CORRELAZIONI DI RANGO FRA LE METRICHE, ENTRO CIASCUN CONTESTO")
    print("=" * 118)
    if "red_prec" in d.columns:
        correlazioni(d)
    else:
        print("non calcolabili senza la colonna `red_prec`.")

    print("\n" + "=" * 118)
    print("RAPPORTO DI SOVRA-PREDIZIONE DELLA CLASSE CRITICA (regola predefinita)")
    print("=" * 118)
    if args.dump_dir.exists():
        sovra_predizione(args.dump_dir)
    else:
        print(f"cartella dei dump non trovata: {args.dump_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
