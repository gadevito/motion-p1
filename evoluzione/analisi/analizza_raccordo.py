#!/usr/bin/env python3
"""
Analisi del raccordo LEGACY ↔ BASE-CORRECTED.
==============================================
Scritta PRIMA di guardare i risultati. Nessuna scelta dipende dai numeri.

IL CRITERIO, fissato nel disegno congelato alla versione 5.

    delta[p,s] = 100 * (L_CORRECTED[p,s] - L_LEGACY[p,s]) / L_LEGACY[p,s]

con le perdite mediate PRIMA sui quattro orizzonti. **Valori positivi indicano
peggioramento.**

    non inferiorita'  limite superiore UNILATERALE al 95% sotto +1%
    equivalenza       intervallo BILATERALE al 90% dentro ±1%

**NESSUN VERDETTO AGGREGATO.** Per ciascuna citta' si riportano differenza
stimata, limite di non inferiorita', intervallo di equivalenza, metriche
secondarie ed eventuale esito non conclusivo. Due citta' favorevoli su tre non
equivalgono a non inferiorita' generale.

IL RICAMPIONAMENTO RICOSTRUISCE LA STRUTTURA DELLO STIMATORE: tre partizioni con
reinserimento, per ciascuna occorrenza tre inizializzazioni con reinserimento, e i
nodi di prova con MOLTEPLICITA' PRESERVATE. Gli stessi campioni per entrambe le
varianti, perche' il confronto e' appaiato.

I CINQUE CONTROLLI SUL PERIMETRO SONO BLOCCANTI: un manifesto che non corrisponda
ferma l'analisi, non produce un avviso.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_raccordo.py
    poetry run python evoluzione/analisi/analizza_raccordo.py --repliche 2000
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import (  # noqa: E402
    carica as carica_pesi, media_orizzonti)

CONTESTI = ("Madrid", "Londra", "Melbourne")
VARIANTI = ("LEGACY", "BASE-CORRECTED")
ORIZZONTI = (1, 2, 4, 8)
MARGINE = 1.0                 # per cento relativo, fissato prima
LIVELLO_NI = 0.95             # unilaterale, non inferiorita'
LIVELLO_EQ = 0.90             # bilaterale, equivalenza
CHIAVE = ["nodo", "istante", "orizzonte"]


class PerimetroViolato(RuntimeError):
    """Un controllo bloccante e' fallito. L'analisi si ferma."""


# ------------------------------------------------------------ caricamento ---
def coppie_presenti(dir_racc: Path, contesto):
    """Le coppie (partizione, inizializzazione) EFFETTIVAMENTE presenti.

    Si scoprono dai file, non si fissano: la campagna di sensibilita' ne ha tre
    per partizione, quella di conferma dodici, e un elenco fisso ne perderebbe
    nove in silenzio.
    """
    fuori = set()
    for f in Path(dir_racc).glob(f"pred_{contesto}_p*_s*_LEGACY.csv"):
        m = re.match(rf"pred_{re.escape(contesto)}_p(\d+)_s(\d+)_LEGACY\.csv",
                     f.name)
        if m:
            fuori.add((int(m.group(1)), int(m.group(2))))
    return sorted(fuori)


def partizioni_presenti(dir_racc: Path, contesto):
    return sorted({p for p, _ in coppie_presenti(dir_racc, contesto)})


def carica(dir_racc: Path, contesto, p, s):
    fuori = {}
    for v in VARIANTI:
        f = dir_racc / f"pred_{contesto}_p{p}_s{s}_{v}.csv"
        if not f.exists():
            return None
        fuori[v] = pd.read_csv(f)
    return fuori


def pesi_classe(contesto, partizione, dir_pesi: Path):
    """I pesi dall'ARTEFATTO che l'addestramento ha consumato.

    Non si ricalcolano: due calcoli indipendenti possono divergere, ed e'
    precisamente cio' che e' accaduto nella prima campagna. Uno per citta' e
    PARTIZIONE, condiviso fra inizializzazioni e varianti.
    """
    return carica_pesi(dir_pesi, contesto, partizione)


# --------------------------------------------------- controlli bloccanti ----
def controlla(D, contesto, p, s):
    """I cinque controlli. Ciascuno BLOCCA."""
    A, B = D["LEGACY"], D["BASE-CORRECTED"]
    if A[CHIAVE].duplicated().any() or B[CHIAVE].duplicated().any():
        raise PerimetroViolato(f"{contesto} p{p} s{s}: chiavi duplicate")
    if len(A) != len(B):
        raise PerimetroViolato(
            f"{contesto} p{p} s{s}: {len(A)} contro {len(B)} istanze")
    if not A[CHIAVE].equals(B[CHIAVE]):
        raise PerimetroViolato(
            f"{contesto} p{p} s{s}: le chiavi NON coincidono fra le varianti")
    if not A.vero.equals(B.vero):
        raise PerimetroViolato(f"{contesto} p{p} s{s}: bersagli diversi")
    if set(A.orizzonte.unique()) != set(ORIZZONTI):
        raise PerimetroViolato(
            f"{contesto} p{p} s{s}: orizzonti {sorted(A.orizzonte.unique())}")
    for nome, d in (("LEGACY", A), ("BASE-CORRECTED", B)):
        pp = d[["p1", "p2", "p3"]].to_numpy()
        if not np.isfinite(pp).all():
            raise PerimetroViolato(f"{contesto} p{p} s{s} {nome}: probabilita' "
                                   "non finite")
        if (pp < 0).any() or not np.allclose(pp.sum(1), 1.0, atol=1e-4):
            raise PerimetroViolato(f"{contesto} p{p} s{s} {nome}: probabilita' "
                                   "non normalizzate")
    return len(A)


# ---------------------------------------------- aggregati per nodo e orizzonte
def aggregati(d, w):
    """(S, W) per (nodo, orizzonte): somma pesata dei termini e dei pesi.

    Gli orizzonti restano SEPARATI: la metrica e' la media delle quattro
    perdite, non la perdita delle somme.
    """
    p = d[["p1", "p2", "p3"]].to_numpy()
    y = d.vero.to_numpy()
    pt = np.clip(p[np.arange(len(y)), y], 1e-7, 1.0)
    wy = w[y]
    nodi = np.unique(d.nodo.to_numpy())
    pos = {n: i for i, n in enumerate(nodi)}
    idx = np.array([pos[n] for n in d.nodo.to_numpy()])
    S = np.zeros((len(nodi), len(ORIZZONTI)))
    W = np.zeros((len(nodi), len(ORIZZONTI)))
    for j, h in enumerate(ORIZZONTI):
        m = d.orizzonte.to_numpy() == h
        S[:, j] = np.bincount(idx[m], weights=(wy * -np.log(pt))[m],
                              minlength=len(nodi))
        W[:, j] = np.bincount(idx[m], weights=wy[m], minlength=len(nodi))
    return nodi, S, W


def perdita(S, W, c):
    """Media delle quattro perdite, su una replica descritta da `c`."""
    num = c @ S
    den = c @ W
    v = np.divide(num, den, out=np.full(len(ORIZZONTI), np.nan),
                  where=den > 0)
    # un orizzonte senza bersagli validi NON contribuisce
    m, _ = media_orizzonti(v)
    return m


# ------------------------------------------------------- ricampionamento ----
def intervalli(dati, repliche, seme=0):
    """Tre livelli: partizioni, inizializzazioni, nodi con molteplicita'.

    `dati[(p, s)] = (nodi, S_legacy, W_legacy, S_corr, W_corr)`
    Gli STESSI campioni per entrambe le varianti.
    """
    rng = np.random.default_rng(seme)
    parti = sorted({p for p, _ in dati})
    per_part = {p: sorted(s for q, s in dati if q == p) for p in parti}
    K = len(next(iter(dati.values()))[0])

    def stima(occorrenze, c):
        """`occorrenze` = [(partizione, [inizializzazioni]), ...].

        Ogni OCCORRENZA porta la propria estrazione: se una partizione compare
        due volte, le due non condividono le inizializzazioni. LEGACY e
        BASE-CORRECTED restano appaiate ENTRO ciascuna occorrenza.
        """
        d = []
        for p, sel_s in occorrenze:
            e = []
            for s in sel_s:
                nodi, Sa, Wa, Sb, Wb = dati[(p, s)]
                la = perdita(Sa, Wa, c)
                lb = perdita(Sb, Wb, c)
                if np.isfinite(la) and np.isfinite(lb) and la > 0:
                    e.append(100.0 * (lb - la) / la)
            if e:
                d.append(float(np.mean(e)))     # media sulle inizializzazioni
        return float(np.mean(d)) if d else np.nan   # poi sulle occorrenze

    uno = np.ones(K)
    punto = stima([(p, per_part[p]) for p in parti], uno)

    rep = []
    for _ in range(repliche):
        # tre partizioni con reinserimento; per CIASCUNA OCCORRENZA tre
        # inizializzazioni con reinserimento, estratte indipendentemente
        occ = []
        for i in rng.integers(len(parti), size=len(parti)):
            p = parti[i]
            q = per_part[p]
            occ.append((p, [q[j] for j in rng.integers(len(q), size=len(q))]))
        sel = rng.integers(K, size=K)
        c = np.bincount(sel, minlength=K).astype("float64")
        x = stima(occ, c)
        if np.isfinite(x):
            rep.append(x)
    if len(rep) < 50:
        return None
    rep = np.array(rep)

    def ric(q):
        return punto + np.percentile(rep, q) - rep.mean()

    return {
        "stima": punto, "repliche": len(rep),
        # non inferiorita': limite SUPERIORE unilaterale
        "ni_sup": ric(100 * LIVELLO_NI),
        # equivalenza: intervallo BILATERALE
        "eq_inf": ric(100 * (1 - LIVELLO_EQ) / 2),
        "eq_sup": ric(100 * (1 - (1 - LIVELLO_EQ) / 2)),
    }


def esito_ni(r):
    if r is None:
        return "non conclusiva"
    if r["ni_sup"] < -MARGINE:
        return "miglioramento rilevante"
    if r["ni_sup"] < MARGINE:
        return "SOSTENUTA"
    if r["eq_inf"] > MARGINE:
        return "deterioramento rilevante"
    return "non conclusiva"


def esito_eq(r):
    if r is None:
        return "non conclusiva"
    if r["eq_inf"] > -MARGINE and r["eq_sup"] < MARGINE:
        return "SOSTENUTA"
    if r["eq_inf"] > MARGINE or r["eq_sup"] < -MARGINE:
        return "non sostenuta"
    return "non conclusiva"


# ------------------------------------------------------ metriche secondarie -
def _average_precision(p3, y):
    o = np.argsort(-p3, kind="stable")
    yy = y[o]
    tp = np.cumsum(yy)
    prec = tp / np.arange(1, len(yy) + 1)
    return float((prec * yy).sum() / max(yy.sum(), 1))


def secondarie(dati_per_coppia, w_per_partizione):
    """Average precision sulla classe critica, e perdita sui soli positivi.

    **SI RICALCOLANO PER OGNI CAMPAGNA.** Non si trasferiscono da una campagna
    all'altra: un modello diverso ha ordinamenti diversi, e il peggioramento
    osservato altrove non vale qui.

    FUORI dal criterio principale, riportate anche se contraddicono.

    Su TUTTE le coppie, non su una sola: con tre inizializzazioni un valore
    preso da `p0 s0` descriverebbe una colonna della matrice, non la campagna.
    """
    fuori = {}
    for v in VARIANTI:
        ap, lp, n = [], [], []
        for (p, s), D in sorted(dati_per_coppia.items()):
            d = D[v]
            y = (d.vero.to_numpy() == 2).astype(int)
            ap.append(_average_precision(d.p3.to_numpy(), y))
            # la perdita sui soli POSITIVI: il peso si cancella nel rapporto
            m = y == 1
            pt = np.clip(d.p3.to_numpy()[m], 1e-7, 1.0)
            lp.append(float(np.mean(-np.log(pt))) if m.any() else np.nan)
            n.append(int(m.sum()))
        fuori[v] = {
            "average_precision_critica": float(np.mean(ap)),
            "ap_per_coppia": [float(x) for x in ap],
            "ap_minimo": float(np.min(ap)), "ap_massimo": float(np.max(ap)),
            "perdita_sui_positivi": float(np.nanmean(lp)),
            "positivi": int(np.sum(n)), "coppie": len(ap)}
    return fuori


def main() -> int:
    ap = argparse.ArgumentParser(description="analisi del raccordo")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/raccordo"))
    ap.add_argument("--maschere", type=Path,
                    default=Path("results/evoluzione/maschere"))
    ap.add_argument("--pesi", type=Path,
                    default=Path("results/evoluzione/pesi"),
                    help="l'artefatto che l'ADDESTRAMENTO ha consumato")
    ap.add_argument("--repliche", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    M = json.loads((a.dir / "matrice.json").read_text())
    print("=" * 84)
    print("ANALISI DEL RACCORDO — criterio fissato prima delle esecuzioni")
    print("=" * 84)
    print(f"  schema {M.get('schema_version')} | implementazione "
          f"{M.get('implementation_version')}")
    print(f"  coppie utilizzabili {M['coppie_utilizzabili']}/"
          f"{M['coppie_utilizzabili'] + M['coppie_incomplete']}")
    print(f"  margine ±{MARGINE}% | non inferiorita' al {LIVELLO_NI:.0%} "
          f"unilaterale | equivalenza al {LIVELLO_EQ:.0%} bilaterale")
    if M["coppie_incomplete"]:
        print(f"\n  ATTENZIONE: {M['coppie_incomplete']} coppie incomplete. "
              f"L'analisi e' CONDIZIONATA alle esecuzioni completate.")

    risultati = {}
    for c in CONTESTI:
        print(f"\n{'=' * 84}\n{c}\n{'=' * 84}")
        CP = coppie_presenti(a.dir, c)
        if not CP:
            print(f"\n{'=' * 84}\n{c}\n{'=' * 84}\n  nessuna coppia")
            continue
        PZ = {p: pesi_classe(c, p, a.pesi)
              for p in partizioni_presenti(a.dir, c)}
        dati, righe = {}, 0
        for p, s in CP:
            if True:
                D = carica(a.dir, c, p, s)
                if D is None:
                    print(f"  p{p} s{s}: coppia assente")
                    continue
                righe += controlla(D, c, p, s)       # BLOCCANTE
                w = PZ[p].vettore()                  # per PARTIZIONE
                na, Sa, Wa = aggregati(D["LEGACY"], w)
                nb, Sb, Wb = aggregati(D["BASE-CORRECTED"], w)
                if not np.array_equal(na, nb):
                    raise PerimetroViolato(
                        f"{c} p{p} s{s}: nodi diversi fra le varianti")
                dati[(p, s)] = (na, Sa, Wa, Sb, Wb)
        if not dati:
            print("  nessuna coppia: contesto non analizzabile")
            continue
        print(f"  {len(dati)} coppie | {righe:,} predizioni per variante")
        for p in sorted(PZ):
            print(f"     p{p}: pesi {np.round(PZ[p].vettore(), 4).tolist()} "
                  f"| impronta {PZ[p].impronta} | N {PZ[p].n_train:,}")

        r = intervalli(dati, a.repliche)
        if r is None:
            print("  ricampionamento non riuscito")
            continue
        ni, eq = esito_ni(r), esito_eq(r)
        print(f"\n  differenza stimata           {r['stima']:+8.3f}%"
              f"   (positivo = peggioramento)")
        print(f"  limite di NON INFERIORITA'   {r['ni_sup']:+8.3f}%"
              f"   (unilaterale al {LIVELLO_NI:.0%}, margine +{MARGINE})")
        print(f"  intervallo di EQUIVALENZA    [{r['eq_inf']:+7.3f};"
              f"{r['eq_sup']:+7.3f}]  (bilaterale al {LIVELLO_EQ:.0%})")
        print(f"\n  NON INFERIORITA': {ni}")
        print(f"  EQUIVALENZA:      {eq}")

        # metriche secondarie, fuori dal criterio, su TUTTE le coppie
        per_coppia = {}
        for p, s in CP:
            D = carica(a.dir, c, p, s)
            if D is not None:
                per_coppia[(p, s)] = D
        sec = secondarie(per_coppia, PZ) if per_coppia else {}
        if sec:
            print(f"\n  metriche secondarie, FUORI dal criterio, su "
                  f"{sec['LEGACY']['coppie']} coppie:")
            print(f"     {'':16s} {'AP critica':>11} {'estremi':>18} "
                  f"{'perdita positivi':>18}")
            for v in VARIANTI:
                x = sec[v]
                print(f"     {v:16s} {x['average_precision_critica']:11.4f} "
                      f"[{x['ap_minimo']:.4f};{x['ap_massimo']:.4f}] "
                      f"{x['perdita_sui_positivi']:18.4f}")
            dap = (sec["BASE-CORRECTED"]["average_precision_critica"]
                   - sec["LEGACY"]["average_precision_critica"])
            dlp = (sec["BASE-CORRECTED"]["perdita_sui_positivi"]
                   - sec["LEGACY"]["perdita_sui_positivi"])
            print(f"     {'differenza':16s} {dap:+11.4f} "
                  f"{'':18} {dlp:+18.4f}")
            print(f"     ricalcolate su QUESTA campagna: non si trasferiscono "
                  f"da un'altra")
        risultati[c] = {"stima": r["stima"], "ni_sup": r["ni_sup"],
                        "eq": [r["eq_inf"], r["eq_sup"]],
                        "non_inferiorita": ni, "equivalenza": eq,
                        "coppie": len(dati), "secondarie": sec}

    print(f"\n{'=' * 84}\nRIEPILOGO PER CITTA'\n{'=' * 84}")
    print(f"  {'citta':11s} {'stima':>9} {'lim. NI':>9} "
          f"{'equivalenza':>20}  {'non inf.':<22} equivalenza")
    for c, v in risultati.items():
        print(f"  {c:11s} {v['stima']:+8.3f}% {v['ni_sup']:+8.3f}% "
              f"[{v['eq'][0]:+7.3f};{v['eq'][1]:+7.3f}]  "
              f"{v['non_inferiorita']:<22} {v['equivalenza']}")
    print("\n  NESSUN VERDETTO AGGREGATO: due citta' favorevoli su tre non")
    print("  equivalgono a non inferiorita' generale.")
    print("\n  Gli intervalli descrivono la variabilita' rispetto a partizioni,")
    print("  inizializzazioni e nodi valutati, CONDIZIONATAMENTE al periodo di")
    print("  prova. Non quantificano la trasferibilita' ad altri periodi, e la")
    print("  dipendenza spaziale fra nodi non e' modellata esplicitamente.")

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"margine": MARGINE, "livello_ni": LIVELLO_NI,
             "livello_eq": LIVELLO_EQ, "repliche": a.repliche,
             "schema_version": M.get("schema_version"),
             "implementation_version": M.get("implementation_version"),
             "risultati": risultati}, indent=2, ensure_ascii=False))
        print(f"\n  salvato in {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
