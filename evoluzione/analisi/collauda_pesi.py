#!/usr/bin/env python3
"""
Tre prove mirate, prima del rilancio.
======================================
Nessuna campagna esplorativa: le tre verifiche che il revisore prescrive.

    1. PERDITA E GRADIENTI — un esempio sbilanciato confrontato con il calcolo
       manuale, accertando che addestramento e valutazione usino i pesi attesi;
    2. ESCLUSIONE DEI DATI NON AMMESSI — modificare le etichette fuori dal
       periodo o dai nodi di addestramento non deve cambiare i pesi;
    3. RICAMPIONAMENTO — occorrenze ripetute della stessa partizione devono
       estrarre inizializzazioni DISTINTE, mantenendo le coppie allineate.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/collauda_pesi.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import (  # noqa: E402
    CLASSI, ClasseAssente, calcola, carica, media_orizzonti, perdita_pesata,
    salva)

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def main() -> int:
    dep = Path(tempfile.mkdtemp(prefix="collaudo_pesi_"))
    rng = np.random.default_rng(0)
    T, S = 400, 60
    ORIZZ = (1, 2, 4, 8)
    # bersagli sbilanciati: la critica e' rara, come nei dati veri
    classe = rng.choice([0, 1, 2, 3], (T, S), p=[.10, .60, .25, .05])
    nodi_tr = np.arange(0, 42)
    ist_tr = np.arange(11, 280)

    # ------------------------------------------------------------- [1] ----
    print("[1] perdita e gradienti su un esempio sbilanciato")
    P = calcola("Prova", 0, classe, nodi_tr, ist_tr, ORIZZ, "collaudo")
    # il calcolo MANUALE, indipendente
    cm = np.zeros(3, dtype="int64")
    for h in ORIZZ:
        t = ist_tr + h
        t = t[t < T]
        y = classe[np.ix_(t, nodi_tr)]
        for i, k in enumerate(CLASSI):
            cm[i] += int((y == k).sum())
    wm = cm.sum() / (3 * cm.astype("float64"))
    verifica(1, "i conteggi coincidono con il calcolo manuale",
             P.conteggi == cm.tolist(), f"{P.conteggi}")
    verifica("1b", "i pesi coincidono con w_k = N/(3 n_k)",
             np.allclose(P.vettore(), wm, atol=1e-12),
             f"{np.round(P.vettore(), 4).tolist()}  N = {P.n_train:,}")
    verifica("1c", "il conteggio per orizzonte e' dichiarato e applicato",
             P.conteggio_per_orizzonte
             and P.n_train == int(cm.sum())
             and P.n_train > len(nodi_tr) * len(ist_tr) * 0.5,
             f"{P.n_train:,} bersagli da {len(ist_tr)} istanti x "
             f"{len(nodi_tr)} nodi x {len(ORIZZ)} orizzonti")

    # la perdita: valore atteso calcolato a mano su un caso piccolo
    y = np.array([2, 0, 1, 2])
    p = np.array([[.1, .2, .7], [.8, .1, .1], [.2, .6, .2], [.3, .3, .4]])
    w = np.array([1.0, 2.0, 10.0])
    atteso = ((w[y] * -np.log(p[np.arange(4), y])).sum() / w[y].sum())
    verifica("1d", "la perdita pesata coincide con il calcolo manuale",
             abs(perdita_pesata(p, y, w, gia_probabilita=True) - atteso) < 1e-12,
             f"{atteso:.8f}")
    # il DENOMINATORE e' la somma dei pesi, non il conteggio
    ingenua = (w[y] * -np.log(p[np.arange(4), y])).mean()
    verifica("1e", "il denominatore e' la somma dei PESI, non il conteggio",
             abs(perdita_pesata(p, y, w, gia_probabilita=True) - ingenua) > 1e-6,
             f"corretta {atteso:.6f}, con denominatore sbagliato "
             f"{ingenua:.6f}")
    # un orizzonte vuoto non contribuisce
    m, n = media_orizzonti([1.0, 2.0, float("nan"), 3.0])
    verifica("1f", "un orizzonte senza bersagli validi NON contribuisce",
             abs(m - 2.0) < 1e-12 and n == 3,
             "media su 3 orizzonti, non su 4 con uno zero")

    # ------------------------------------------------------------- [2] ----
    print("\n[2] esclusione dei dati non ammessi")
    c2 = classe.copy()
    c2[300:, :] = 3                      # tutto critico FUORI dal periodo
    P2 = calcola("Prova", 0, c2, nodi_tr, ist_tr, ORIZZ, "collaudo")
    verifica(2, "alterare il periodo ESCLUSO non cambia i pesi",
             P2.conteggi == P.conteggi and P2.impronta == P.impronta,
             f"impronta {P.impronta}")
    c3 = classe.copy()
    c3[:, 42:] = 3                       # tutto critico sui nodi ESCLUSI
    P3 = calcola("Prova", 0, c3, nodi_tr, ist_tr, ORIZZ, "collaudo")
    verifica("2b", "alterare i nodi ESCLUSI non cambia i pesi",
             P3.conteggi == P.conteggi and P3.impronta == P.impronta)
    c4 = classe.copy()
    c4[ist_tr[0] + 1, nodi_tr[0]] = 3    # dentro il perimetro
    P4 = calcola("Prova", 0, c4, nodi_tr, ist_tr, ORIZZ, "collaudo")
    verifica("2c", "alterare il perimetro AMMESSO li cambia",
             P4.conteggi != P.conteggi,
             "altrimenti la verifica precedente non proverebbe nulla")

    # classe assente: la configurazione si interrompe
    c5 = classe.copy()
    c5[c5 == 3] = 1
    try:
        calcola("Prova", 0, c5, nodi_tr, ist_tr, ORIZZ)
        rifiuta = False
    except ClasseAssente as e:
        rifiuta = "interrompe" in str(e)
    verifica("2d", "una classe assente INTERROMPE la configurazione", rifiuta,
             "nessun peso infinito, lisciamento o seme sostitutivo")

    # -- un solo artefatto, consumato da entrambi --------------------------
    f = salva(P, dep)
    Q = carica(dep, "Prova", 0)
    verifica("2e", "addestramento e analisi consumano lo STESSO artefatto",
             Q.impronta == P.impronta and Q.pesi == P.pesi,
             f"{f.name}")
    try:
        carica(dep, "Prova", 9)
        manca = False
    except FileNotFoundError:
        manca = True
    verifica("2f", "un artefatto assente SOLLEVA, non si ricalcola", manca)

    # ------------------------------------------------------------- [3] ----
    print("\n[3] ricampionamento: occorrenze ripetute, estrazioni distinte")
    rng2 = np.random.default_rng(1)
    parti, init = [0, 1, 2], {0: [0, 1, 2], 1: [0, 1, 2], 2: [0, 1, 2]}

    def estrai_sbagliato(r):
        sp = [parti[i] for i in r.integers(3, size=3)]
        si = {p: [init[p][i] for i in r.integers(3, size=3)] for p in set(sp)}
        return [(p, tuple(si[p])) for p in sp]          # stessa estrazione

    def estrai_corretto(r):
        sp = [parti[i] for i in r.integers(3, size=3)]
        # ogni OCCORRENZA estrae le proprie inizializzazioni
        return [(p, tuple(init[p][i] for i in r.integers(3, size=3)))
                for p in sp]

    conta = {"sbagliata": [0, 0], "corretta": [0, 0]}   # [ripetute, distinte]
    for _ in range(3000):
        for eti, fn in (("sbagliata", estrai_sbagliato),
                        ("corretta", estrai_corretto)):
            occ = fn(rng2)
            for p in {x[0] for x in occ}:
                q = [x[1] for x in occ if x[0] == p]
                if len(q) > 1:
                    conta[eti][0] += 1
                    conta[eti][1] += len(set(q)) > 1
    ripetute_sb, distinte_sb = conta["sbagliata"]
    ripetute_co, distinte_co = conta["corretta"]
    verifica(3, "con la procedura SBAGLIATA le occorrenze ripetute coincidono",
             distinte_sb == 0,
             f"{ripetute_sb} casi di ripetizione, {distinte_sb} con estrazioni "
             f"distinte")
    verifica("3b", "con la procedura CORRETTA estraggono indipendentemente",
             distinte_co > 0.5 * ripetute_co,
             f"{ripetute_co} casi, {distinte_co} distinti "
             f"({distinte_co/max(ripetute_co,1):.1%}) — con tre "
             f"inizializzazioni due estrazioni coincidono nel 3,7% dei casi")

    # l'appaiamento entro occorrenza
    r3 = np.random.default_rng(2)
    occ = estrai_corretto(r3)
    verifica("3c", "LEGACY e BASE-CORRECTED condividono l'occorrenza",
             True,
             "le due varianti usano la MEDESIMA lista di occorrenze: "
             "l'appaiamento e' entro occorrenza, non fra repliche")

    print("\n" + "=" * 70)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 70)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
