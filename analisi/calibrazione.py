#!/usr/bin/env python3
"""
Calibrazione e discriminazione (§8.7.4, Tabelle 86 e 87).
==========================================================
Nessun addestramento: dai dump di test e di validazione.

LE DUE GRANDEZZE SONO INDIPENDENTI, e la loro separazione e' il risultato.

  affidabilita' - quanto le probabilita' dichiarate corrispondono alle
                  frequenze osservate. Si misura come CADUTA di entropia
                  pesata prodotta da una ricalibrazione: se il modello e' gia'
                  calibrato la caduta e' nulla.
  risoluzione   - quanto il modello separa le celle critiche dalle altre. Si
                  misura a richiamo appaiato, ed e' invariante per
                  trasformazioni monotone delle probabilita'.

Un modello puo' discriminare benissimo e dichiarare probabilita' sbagliate.
E' la stessa dissociazione misurata sulla ricostruzione da flusso e occupazione
(§8.6.4), qui applicata al modello anziche' al bersaglio.

IL PERIMETRO DELLA MISURA DI CALIBRAZIONE CAMBIA IL VERDETTO, e va scelto.

  * termine di affidabilita' sulla METRICA DI CONFRONTO (entropia pesata,
    tutte e tre le classi): la rete e' da tre a trentacinque volte MEGLIO
    calibrata del riferimento;
  * errore di calibrazione atteso sulla SOLA classe critica, NON pesato, su
    dieci intervalli: la rete e' PEGGIO calibrata in tutti e sei i contesti.

Non e' un surrogato impreciso della stessa grandezza: e' una grandezza diversa,
e inverte la conclusione. La misura di calibrazione va scelta sul perimetro
della metrica su cui si decide. Lo script calcola ENTRAMBE e le riporta
affiancate, perche' la nota metodologica e' il risultato.

QUATTRO VINCOLI IMPLEMENTATIVI, nessuno prudenziale:

  1. la regressione isotonica va PESATA. Senza pesi l'entropia pesata peggiora
     del 17,08%, perche' calibrando sulla frequenza non pesata le probabilita'
     della classe rara vengono schiacciate proprio dove la metrica le pesa 3,76;
  2. il calibratore va stimato PER ORIZZONTE;
  3. va stimato per CLASSE VERA e non per classe predetta: la prima recupera il
     doppio, 3,06% contro 1,68%;
  4. va applicato a ENTRAMBE le varianti, che e' cio' che rende la misura
     informativa anziche' asimmetrica.

Lo script verifica i primi tre eseguendo anche le varianti sbagliate, cosi' che
i numeri stiano accanto all'affermazione.

Uso (dalla radice OR3/):

    poetry run python analisi/calibrazione.py
    poetry run python analisi/calibrazione.py --sezioni vincoli
"""
from pathlib import Path
import argparse
import glob as globmod
import math

import numpy as np
from sklearn.isotonic import IsotonicRegression

BASE = Path("data_collection")
GOMO = BASE / "go-mo" / "gomo"
T4C = BASE / "traffic4cast"
ORIZZONTI = ("15m", "30m", "60m", "120m")

CONTESTI = {
    "d8_2024": (GOMO / "targets_2024_urb_d8.npz", "d8/2024"),
    "d15_2024": (GOMO / "targets_2024_urb_d15.npz", "d15/2024"),
    "d8_2023": (GOMO / "targets_2023_urb_d8.npz", "d8/2023"),
    "t4cmad": (T4C / "MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz", "Madrid"),
    "t4clon": (T4C / "LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz", "Londra"),
    "t4cmel": (T4C / "MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz", "Melbourne"),
}


def st(v):
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def pesi(percorso):
    z = np.load(percorso, allow_pickle=True)
    C = z["congestion_emp"]
    T = C.shape[0]
    fr = np.array([(C[: int((T - 8) * 0.7)] == k).sum() for k in (1, 2, 3)], dtype=float)
    return (fr.sum() / (np.maximum(fr, 1) * 3)).astype("float64")


def blocchi(percorso, tag):
    if not globmod.glob(percorso):
        return None
    z = np.load(percorso, allow_pickle=True)
    fuori = []
    for h in ORIZZONTI:
        ch = [k[3:] for k in z.files if k.startswith("tag") and str(z[k]) == f"{tag}|{h}"]
        if not ch:
            return None
        i = ch[0]
        fuori.append((z[f"p{i}"].astype("float32"), z[f"y{i}"].astype(int)))
    return fuori


def wce(blocco, w):
    v = []
    for P, Y in blocco:
        pt = np.clip(P[np.arange(len(Y)), Y], 1e-7, 1)
        v.append(np.sum(w[Y] * -np.log(pt)) / np.sum(w[Y]))
    return float(np.mean(v))


def calibra(stima, applica, w, pesata=True, per_orizzonte=True, per_classe_vera=True):
    """Le tre varianti dei vincoli 1, 2 e 3, per poterli verificare."""
    if not per_orizzonte:                       # un solo calibratore per tutti
        Pv = np.concatenate([b[0] for b in stima])
        Yv = np.concatenate([b[1] for b in stima])
        stima = [(Pv, Yv)] * len(applica)
    fuori = []
    for (Pv, Yv), (Pt, Yt) in zip(stima, applica):
        Q = np.empty((len(Pt), 3), dtype="float32")
        base = Yv if per_classe_vera else Pv.argmax(1)
        for k in range(3):
            ir = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
            ir.fit(Pv[:, k], (base == k).astype(float),
                   sample_weight=w[Yv] if pesata else None)
            Q[:, k] = ir.predict(Pt[:, k])
        Q = np.clip(Q, 1e-7, None)
        fuori.append((Q / Q.sum(1, keepdims=True), Yt))
    return fuori


def ece(blocco, intervalli=10, conteggi=False):
    """Errore di calibrazione atteso sulla SOLA classe critica, NON pesato.

    Le tre scelte di definizione, tutte verificabili in queste otto righe:

      confini    a LARGHEZZA COSTANTE, `np.linspace(0, 1, 11)`. Non sono
                 quantili: i gruppi hanno ampiezza uguale e numerosita' molto
                 diversa. La formulazione corretta e' quindi «dieci parti di
                 uguale ampiezza», non «dieci gruppi di uguale numerosita'».
      probabilita'  la SOLA classe critica, `P[:, 2]`. NON quella della classe
                 piu' probabile, che e' la variante piu' diffusa in letteratura
                 e misura una cosa diversa.
      pesatura   ciascuno scarto e' moltiplicato per `m.mean()`, la frazione di
                 celle che cadono nel gruppo. E' la definizione standard, e con
                 una classe critica al 3% non e' una scelta indifferente: il
                 primo gruppo contiene circa il 59% delle celle su d8/2024 e gli
                 ultimi due insieme restano sotto il 2%. Con una media semplice
                 sui dieci gruppi, scaglioni quasi vuoti peserebbero quanto
                 quello che ne contiene quasi il sessanta per cento.

    L'ultimo gruppo e' chiuso a destra per non perdere le celle a probabilita'
    unitaria, ed e' quindi formalmente piu' ampio dei nove precedenti. Con le
    frequenze osservate l'effetto e' nullo, ma va scritto se la definizione
    viene riportata per esteso.

    Con `conteggi=True` restituisce anche la numerosita' di ciascun gruppo, che
    e' il controllo che distingue senza ambiguita' la partizione a larghezza
    costante da quella a frequenza costante: nella prima i conteggi differiscono
    di uno o due ordini di grandezza, nella seconda sarebbero quasi identici.
    """
    v, n = [], None
    for P, Y in blocco:
        p = P[:, 2]
        y = (Y == 2).astype(float)
        bordi = np.linspace(0, 1, intervalli + 1)
        e = 0.0
        q = []
        for i in range(intervalli):
            m = (p >= bordi[i]) & (p < bordi[i + 1] if i < intervalli - 1 else p <= 1)
            q.append(int(m.sum()))
            if m.sum():
                e += m.mean() * abs(p[m].mean() - y[m].mean())
        v.append(e)
        if n is None:
            n = q                      # conteggi del primo orizzonte, 15 minuti
    return (float(np.mean(v)), n) if conteggi else float(np.mean(v))


def sez_tabella(a):
    print("=" * 104)
    print("TABELLE 86 e 87 - le due misure di calibrazione, affiancate")
    print("=" * 104)
    print(f"{'contesto':10s} | {'affidabilita (metrica di confronto)':>36} | "
          f"{'ECE (sola classe critica, non pesato)':>38}")
    print(f"{'':10s} | {'rete':>16} {'riferimento':>18} | "
          f"{'rete':>12} {'riferimento':>13} {'scarto':>10}")
    for c, (tp, nome) in CONTESTI.items():
        if not tp.exists():
            continue
        w = pesi(tp)
        an, ag, en, eg = [], [], [], []
        for s in range(a.semi):
            nt = blocchi(f"{a.probsval}/nn_test_{c}_s{s}.npz", "gwn_none")
            nv = blocchi(f"{a.probsval}/nn_{c}_s{s}.npz", "gwn_none")
            gt = blocchi(f"{a.probsval}/gb_test_{c}_s{s}.npz", "lgb_fair")
            gv = blocchi(f"{a.probsval}/gb_{c}_s{s}.npz", "lgb_fair")
            if not all([nt, nv, gt, gv]):
                break
            n0, g0 = wce(nt, w), wce(gt, w)
            an.append(100 * (n0 - wce(calibra(nv, nt, w), w)) / n0)
            ag.append(100 * (g0 - wce(calibra(gv, gt, w), w)) / g0)
            en.append(ece(nt))
            eg.append(ece(gt))
        if len(an) < a.semi:
            print(f"{nome:10s} dump incompleti ({len(an)}/{a.semi})")
            continue
        mn, mg = st(an)[0], st(ag)[0]
        pn, pg = st(en)[0], st(eg)[0]
        print(f"{nome:10s} | {mn:+8.2f}% ± {st(an)[1]:5.2f} "
              f"{mg:+10.2f}% ± {st(ag)[1]:5.2f} | {pn:12.4f} {pg:13.4f} "
              f"{100 * (pn - pg) / pg:+9.1f}%")
    print("\n  Le due colonne danno verdetti OPPOSTI. Sulla metrica di confronto la rete e'")
    print("  meglio calibrata; sulla sola classe critica non pesata e' peggio calibrata in")
    print("  tutti e sei i contesti. Non e' un surrogato impreciso: e' una grandezza")
    print("  diversa. La misura di calibrazione va scelta sul perimetro della metrica su")
    print("  cui si decide, altrimenti puo' dire il contrario di quel che serve sapere.\n")


def sez_gruppi(a):
    """Numerosita' dei dieci gruppi dell'errore di calibrazione atteso.

    E' il controllo che risponde senza ambiguita' alla domanda su come sia
    costruita la partizione, e che va riportato accanto ai valori dell'ECE
    invece di essere una verifica una tantum.
    """
    print("=" * 104)
    print("NUMEROSITA' DEI DIECI GRUPPI (seme 0, orizzonte 15 minuti, ramo neurale)")
    print("=" * 104)
    print("Confini a larghezza costante 0,1. A frequenza costante i conteggi sarebbero")
    print("quasi identici: un rapporto elevato fra il piu' pieno e il meno pieno conferma")
    print("che la partizione e' per AMPIEZZA e non per numerosita'.\n")
    print(f"{'contesto':10s} " + "".join(f"{f'{i/10:.1f}':>9}" for i in range(10))
          + f"{'max/min':>10}{'>=0,1%':>8}")
    for c, (tp, nome) in CONTESTI.items():
        b = blocchi(f"{a.probsval}/nn_test_{c}_s0.npz", "gwn_none")
        if not b:
            print(f"{nome:10s} dump non trovato")
            continue
        _, n = ece(b, conteggi=True)
        tot = max(sum(n), 1)
        nz = [x for x in n if x]
        pop = sum(1 for x in n if 100 * x / tot >= 0.1)
        print(f"{nome:10s} " + "".join(f"{100 * x / tot:8.1f}%" for x in n)
              + f"{max(n) / max(min(nz), 1):9.0f}x{pop:7d}")
    print("\n  Percentuali di celle per gruppo. La concentrazione nel primo gruppo segue")
    print("  la RARITA' della classe critica: dove gli episodi sono rari il modello")
    print("  assegna probabilita' basse quasi ovunque. Ne discende che il numero di")
    print("  gruppi effettivamente popolati NON e' lo stesso fra contesti, quindi l'ECE")
    print("  e' calcolato su risoluzioni diverse — terza ragione, oltre a quella del")
    print("  perimetro, per riportarlo come nota metodologica e non come confronto.\n")


def sez_vincoli(a):
    print("=" * 104)
    print("I QUATTRO VINCOLI IMPLEMENTATIVI - verificati eseguendo le varianti sbagliate")
    print("=" * 104)
    c = a.contesto
    tp, nome = CONTESTI[c]
    w = pesi(tp)
    nt = blocchi(f"{a.probsval}/nn_test_{c}_s0.npz", "gwn_none")
    nv = blocchi(f"{a.probsval}/nn_{c}_s0.npz", "gwn_none")
    if not (nt and nv):
        print(f"dump di {nome} seme 0 non trovati")
        return
    base = wce(nt, w)
    print(f"contesto {nome}, seme 0 | entropia pesata non calibrata: {base:.6f}\n")
    print(f"{'variante':44s} {'wCE':>10} {'caduta':>10}")
    prove = [
        ("corretta (pesata, per orizzonte, classe vera)", dict()),
        ("1. NON pesata", dict(pesata=False)),
        ("2. un solo calibratore per tutti gli orizzonti", dict(per_orizzonte=False)),
        ("3. per classe PREDETTA anziche' vera", dict(per_classe_vera=False)),
    ]
    for eti, kw in prove:
        v = wce(calibra(nv, nt, w, **kw), w)
        print(f"{eti:44s} {v:10.6f} {100 * (base - v) / base:+9.2f}%")
    print("\n  La variante non pesata deve PEGGIORARE: calibrando sulla frequenza non")
    print("  pesata le probabilita' della classe rara vengono schiacciate proprio dove la")
    print("  metrica le pesa di piu'. La variante per classe predetta deve recuperare circa")
    print("  la meta'. Se non e' cosi', la procedura non e' quella dichiarata.")
    print("\n  Il quarto vincolo — applicare a ENTRAMBE le varianti — non e' verificabile")
    print("  qui: e' cio' che rende la misura simmetrica, e la sua violazione produrrebbe")
    print("  un confronto asimmetrico anziche' un numero sbagliato.\n")

    print("VERIFICHE ACCESSORIE")
    q = calibra(nv, nt, w)
    somme = np.concatenate([P.sum(1) for P, _ in q])
    print(f"  rinormalizzazione dopo la calibrazione: scarto massimo dalla somma unitaria "
          f"{np.abs(somme - 1).max():.6f}")
    print("  (deve essere trascurabile: la rinormalizzazione non e' distruttiva)")
    meta = [(P[: len(P) // 2], Y[: len(Y) // 2]) for P, Y in nv]
    altra = [(P[len(P) // 2:], Y[len(Y) // 2:]) for P, Y in nv]
    v1 = wce(calibra(meta, nt, w), w)
    v2 = wce(calibra(altra, nt, w), w)
    print(f"  sovraadattamento del calibratore, due meta' della validazione: "
          f"{abs(v1 - v2):.6f}")
    print(f"  (da confrontare con la caduta totale, {base - wce(calibra(nv, nt, w), w):.6f})")


def main() -> int:
    ap = argparse.ArgumentParser(description="calibrazione e discriminazione")
    ap.add_argument("--probsval", default="replication/probsval")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--contesto", default="d8_2024",
                    help="contesto su cui verificare i vincoli implementativi")
    ap.add_argument("--sezioni", nargs="*",
                    default=["tabella", "gruppi", "vincoli"])
    a = ap.parse_args()

    if "tabella" in a.sezioni:
        sez_tabella(a)
    if "gruppi" in a.sezioni:
        sez_gruppi(a)
    if "vincoli" in a.sezioni:
        sez_vincoli(a)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
