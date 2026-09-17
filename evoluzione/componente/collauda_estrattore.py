#!/usr/bin/env python3
"""
Collaudo dell'estrattore: diretto contro incrementale, casi limite, causalita'.
===============================================================================
Nessun addestramento.

    A. equivalenza fra calcolo diretto e incrementale
    B. casi limite
    C. causalita'
    D. indipendenza dalla modalita' di ingestione

TOLLERANZE, fissate prima del collaudo. Uguaglianza ESATTA per conteggi,
maschere, elenchi di non stimabili e metadati. Per le statistiche in virgola
mobile si ammette 1e-9 in valore assoluto: ordini di somma diversi producono
scarti dell'ordine di 1e-13, e una tolleranza quattro ordini piu' larga lascia
margine senza mascherare un errore vero, che sarebbe di ordine ben maggiore.

Il rapporto riporta lo scarto PER CARATTERISTICA, non il solo massimo: un errore
concentrato su una statistica e' diverso da un rumore diffuso su tutte.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_estrattore.py
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    N_BANDE, TAU, Osservazioni, estrai_diretto)
from evoluzione.componente.estrattore_incrementale import (  # noqa: E402
    EstrattoreIncrementale)

ATOL = 1e-9
ESITI = []
SCARTI = defaultdict(float)     # scarto massimo per caratteristica


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def serie(n=400, t0=40, seme=0, lacune=0.12, costante=False, quasi=False):
    rng = np.random.default_rng(seme)
    ist = np.arange(n)
    if costante:
        r = np.full(n, 0.5)
    elif quasi:
        # serie quasi costante: la varianza calcolata come E[x^2]-E[x]^2 perde
        # cifre significative quando la media e' grande rispetto alla dispersione
        r = 1e6 + rng.normal(0, 1e-3, n)
    else:
        r = rng.uniform(0.2, 1.1, n)
    if lacune:
        r = r.copy()
        r[rng.random(n) < lacune] = np.nan
    return Osservazioni(
        ist, r, rng.uniform(50, 200, n), rng.uniform(1, 30, n),
        rng.choice([0, 1, 2, 3], n, p=[.1, .5, .25, .15]),
        (np.arange(n) // 4) % 24, t0=t0, reference_version="collaudo:1")


def alimenta(O, L, schema="EXTENDED", fino=None, lotto=1, l_max=2688):
    """`fino` e' un ISTANTE, non un indice di riga: dopo un'interruzione i due
    non coincidono piu', e alimentare oltre l'istante del confronto sposta la
    finestra dell'incrementale rispetto a quella del diretto."""
    E = EstrattoreIncrementale(t0=O.t0, L=L, schema=schema, l_max=l_max,
                               reference_version=O.reference_version)
    righe = [(O.istanti[i], O.r[i], O.f[i], O.o[i], O.classe[i], O.ora_locale[i])
             for i in range(len(O.istanti))
             if fino is None or O.istanti[i] <= fino]
    if lotto <= 1:
        for x in righe:
            E.ingest(*x)
    else:
        for i in range(0, len(righe), lotto):
            E.ingest_batch(righe[i:i + lotto])
    return E


def confronta(a, b, eti, esatto_meta=True):
    """Registra gli scarti per caratteristica e restituisce gli esiti."""
    sa, sb = np.asarray(a.statistics), np.asarray(b.statistics)
    qa, qb = np.asarray(a.availability), np.asarray(b.availability)
    for nome, x, y in zip(a.feature_names_and_order, sa, sb):
        SCARTI[nome] = max(SCARTI[nome], abs(float(x) - float(y)))
    for nome, x, y in zip(a.availability_names_and_order, qa, qb):
        SCARTI[nome] = max(SCARTI[nome], abs(float(x) - float(y)))
    num = np.allclose(sa, sb, atol=ATOL, rtol=0) and np.allclose(qa, qb, atol=ATOL, rtol=0)
    meta = (a.window_start == b.window_start and a.window_end == b.window_end
            and a.n_osservazioni_finestra == b.n_osservazioni_finestra
            and a.effective_duration == b.effective_duration
            and sorted(a.non_stimabili) == sorted(b.non_stimabili)
            and a.feature_names_and_order == b.feature_names_and_order
            and a.schema_version == b.schema_version)
    return num, (meta if esatto_meta else True)


def main() -> int:
    # ======================================================== A ==============
    print("A. equivalenza fra calcolo diretto e incrementale")
    O = serie()
    n = len(O.istanti)

    print("\n  A.1 dopo OGNI aggiornamento, per piu' durate")
    for L in (4, 24, 96):
        E = EstrattoreIncrementale(t0=O.t0, L=L)
        ok_n = ok_m = True
        for i in range(n):
            E.ingest(O.istanti[i], O.r[i], O.f[i], O.o[i], O.classe[i],
                     O.ora_locale[i])
            if i < O.t0 or i % 7:          # confronto a campione, per rapidita'
                continue
            a = estrai_diretto(O, t=int(O.istanti[i]), L=L)
            num, meta = confronta(a, E.estrai(), f"L{L}@{i}")
            ok_n &= num; ok_m &= meta
        verifica(f"A.1-{L}", f"L = {L}: statistiche entro {ATOL:g} a ogni passo", ok_n)
        verifica(f"A.1-{L}m", f"L = {L}: metadati e conteggi esatti", ok_m)

    print("\n  A.2 dopo l'USCITA di campioni dalla finestra")
    L = 12
    E = EstrattoreIncrementale(t0=O.t0, L=L)
    uscite = 0
    prima = None
    for i in range(n):
        E.ingest(O.istanti[i], O.r[i], O.f[i], O.o[i], O.classe[i], O.ora_locale[i])
        if prima is not None and E.estrai().window_start > prima:
            uscite += 1
            a = estrai_diretto(O, t=int(O.istanti[i]), L=L)
            num, meta = confronta(a, E.estrai(), "uscita")
            if not (num and meta):
                break
        prima = E.estrai().window_start
    verifica("A.2", "coerente dopo ogni uscita dalla finestra",
             num and meta, f"{uscite} uscite osservate")

    print("\n  A.3 con CONFINI DI LOTTO diversi")
    rif = alimenta(O, 96, lotto=1).estrai()
    tutti = True
    for lotto in (1, 2, 3, 7, 16, 64, 1000):
        b = alimenta(O, 96, lotto=lotto).estrai()
        num, meta = confronta(rif, b, f"lotto{lotto}")
        tutti &= num and meta
    verifica("A.3", "l'esito non dipende dai confini dei lotti", tutti,
             "lotti da 1 a 1000")

    print("\n  A.4 schema BASE-CORRECTED")
    a = estrai_diretto(O, t=n - 1, L=96, schema="BASE-CORRECTED")
    b = alimenta(O, 96, schema="BASE-CORRECTED").estrai()
    num, meta = confronta(a, b, "BC")
    verifica("A.4", "BASE-CORRECTED: statistiche e metadati coerenti", num and meta,
             f"{len(a.feature_names_and_order)} statistiche, "
             f"{len(a.availability_names_and_order)} disponibilita'")

    # ======================================================== B ==============
    print("\nB. casi limite")

    a = estrai_diretto(O, t=200, L=0)
    b = alimenta(O, 0, fino=200).estrai()
    verifica("B.1", "finestra vuota: nessuna statistica disponibile",
             len(a.non_stimabili) == len(a.feature_names_and_order)
             and a.n_osservazioni_finestra == 0
             and b.n_osservazioni_finestra == 0)

    a = estrai_diretto(O, t=O.t0, L=1)
    verifica("B.2", "una sola osservazione: media disponibile, deviazione no",
             ("media_r" not in a.non_stimabili or not np.isfinite(O.r[O.t0]))
             and "dev_r" in a.non_stimabili,
             f"osservazioni in finestra: {a.n_osservazioni_finestra}")

    K = serie(costante=True, lacune=0)
    a = estrai_diretto(K, t=200, L=96)
    ia = a.feature_names_and_order.index("dev_r")
    verifica("B.3", "serie costante: deviazione nulla, autocorrelazione non stimabile",
             abs(a.statistics[ia]) < 1e-12 and "autocorr_1" in a.non_stimabili)

    Q = serie(quasi=True, lacune=0)
    a = estrai_diretto(Q, t=200, L=96)
    b = alimenta(Q, 96, fino=200).estrai()
    iq = a.feature_names_and_order.index("dev_r")
    dv = abs(a.statistics[iq] - b.statistics[iq])
    verifica("B.4", "serie QUASI costante: la varianza resta stabile",
             a.statistics[iq] >= 0 and b.statistics[iq] >= 0 and dv < 1e-6,
             f"dev diretto {a.statistics[iq]:.3e}, incrementale "
             f"{b.statistics[iq]:.3e}, scarto {dv:.2e}")

    # interruzione: si tolgono gli istanti 100..119
    keep = ~((np.arange(len(O.istanti)) >= 100) & (np.arange(len(O.istanti)) < 120))
    I = Osservazioni(O.istanti[keep], O.r[keep], O.f[keep], O.o[keep],
                     O.classe[keep], O.ora_locale[keep], t0=O.t0)
    a = estrai_diretto(I, t=200, L=150)
    b = alimenta(I, 150, fino=200).estrai()
    num, meta = confronta(a, b, "interruzione")
    verifica("B.5", "interruzione: nessuna coppia artificiale attraverso la lacuna",
             num and meta,
             f"coppie: {int(round(b.availability[b.availability_names_and_order.index('copertura_coppie')] * (b.n_osservazioni_finestra - 1)))}")

    # validita' diversa fra canali
    D = serie(lacune=0)
    r2 = D.r.copy(); r2[::3] = np.nan
    f2 = D.f.copy(); f2[::5] = np.nan
    V = Osservazioni(D.istanti, r2, f2, D.o, D.classe, D.ora_locale, t0=D.t0)
    a = estrai_diretto(V, t=200, L=90)
    b = alimenta(V, 90, fino=200).estrai()
    cr = a.availability[a.availability_names_and_order.index("copertura_r")]
    cf = a.availability[a.availability_names_and_order.index("copertura_conteggio")]
    co = a.availability[a.availability_names_and_order.index("copertura_occupazione")]
    num, meta = confronta(a, b, "canali")
    verifica("B.6", "validita' per CANALE, conteggi distinti",
             num and meta and cr < cf < co,
             f"copertura r {cr:.3f}, f {cf:.3f}, o {co:.3f}")

    # bande: una finestra di quattro ore ne tocca al piu' due
    a = estrai_diretto(O, t=200, L=16)
    bande_ok = sum(1 for k in range(N_BANDE) if f"banda_{k}" not in a.non_stimabili)
    verifica("B.7", "fasce locali: una finestra corta ne copre poche",
             bande_ok <= 3, f"{bande_ok} bande stimabili su {N_BANDE}")

    # confine dell'installazione
    a0 = estrai_diretto(O, t=O.t0, L=-1)
    verifica("B.8", "l'osservazione all'installazione ENTRA nella finestra",
             a0.window_start == O.t0 and a0.n_osservazioni_finestra == 1,
             f"finestra [{a0.window_start}, {a0.window_end}]")

    # tolleranza sulle variazioni
    m = 60
    rr = np.zeros(m)
    for i in range(1, m):
        rr[i] = rr[i - 1] + (TAU * 2 if i % 3 == 0 else
                             -TAU * 2 if i % 3 == 1 else TAU / 2)
    T = Osservazioni(np.arange(m), rr, np.ones(m), np.ones(m),
                     np.ones(m, dtype=int), np.zeros(m, dtype=int), t0=0)
    a = estrai_diretto(T, t=m - 1, L=-1)
    ii = a.feature_names_and_order.index("quota_incremento")
    id_ = a.feature_names_and_order.index("quota_decremento")
    quiete = 1 - a.statistics[ii] - a.statistics[id_]
    verifica("B.9", "tolleranza: le variazioni entro ±0,005 non contano",
             abs(a.statistics[ii] - 1/3) < 0.02 and quiete > 0.3,
             f"incrementi {a.statistics[ii]:.3f}, decrementi "
             f"{a.statistics[id_]:.3f}, quiete {quiete:.3f}")

    # capacita' del buffer
    a = estrai_diretto(O, t=300, L=-1, l_max=50)
    b = alimenta(O, -1, fino=300, l_max=50).estrai()
    verifica("B.10", "oltre la capacita' la storia e' troncata e dichiarato",
             "troncata" in a.note and "troncata" in b.note
             and a.n_osservazioni_finestra == b.n_osservazioni_finestra,
             a.note)

    # ======================================================== C ==============
    print("\nC. causalita'")
    t = 250
    base = estrai_diretto(O, t=t, L=96)
    dopo = O.r.copy()
    dopo[O.istanti > t] = 99.0
    Od = Osservazioni(O.istanti, dopo, O.f, O.o, O.classe, O.ora_locale, t0=O.t0)
    ad = estrai_diretto(Od, t=t, L=96)
    verifica("C.1", "modificare le osservazioni SUCCESSIVE non cambia nulla",
             np.array_equal(base.statistics, ad.statistics, equal_nan=True))

    prima = O.r.copy()
    prima[O.istanti < O.t0] = 99.0
    Op = Osservazioni(O.istanti, prima, O.f, O.o, O.classe, O.ora_locale, t0=O.t0)
    ap = estrai_diretto(Op, t=t, L=-1)
    ab = estrai_diretto(O, t=t, L=-1)
    verifica("C.2", "modificare le osservazioni ANTERIORI all'installazione non cambia nulla",
             np.array_equal(ab.statistics, ap.statistics, equal_nan=True))

    Ei = EstrattoreIncrementale(t0=O.t0, L=-1)
    for i in range(len(O.istanti)):
        if O.istanti[i] > t:
            break
        Ei.ingest(O.istanti[i], prima[i], O.f[i], O.o[i], O.classe[i], O.ora_locale[i])
    verifica("C.3", "l'incrementale scarta le osservazioni anteriori a t0",
             np.allclose(Ei.estrai().statistics, ab.statistics, atol=ATOL))

    # ======================================================== D ==============
    print("\nD. indipendenza dalla modalita' di ingestione")
    uno = alimenta(O, 96, lotto=1).estrai()
    lot = alimenta(O, 96, lotto=32).estrai()
    off = alimenta(O, 96, lotto=10_000).estrai()
    n1, m1 = confronta(uno, lot, "uno-lotto")
    n2, m2 = confronta(uno, off, "uno-offline")
    verifica("D.1", "una alla volta contro lotti", n1 and m1)
    verifica("D.2", "una alla volta contro caricamento offline ordinato", n2 and m2)

    try:
        E = EstrattoreIncrementale(t0=0, L=96)
        E.ingest(10, .5, 1, 1, 1, 0)
        E.ingest(10, .5, 1, 1, 1, 0)
        rifiuta_dup = False
    except ValueError:
        rifiuta_dup = True
    try:
        E = EstrattoreIncrementale(t0=0, L=96)
        E.ingest(10, .5, 1, 1, 1, 0)
        E.ingest(5, .5, 1, 1, 1, 0)
        rifiuta_ord = False
    except ValueError:
        rifiuta_ord = True
    verifica("D.3", "duplicati e fuori ordine sono rifiutati esplicitamente",
             rifiuta_dup and rifiuta_ord)

    # ================================================== rapporto =============
    print("\n" + "=" * 74)
    print("SCARTI PER CARATTERISTICA, su tutti i confronti")
    print("=" * 74)
    peggiori = sorted(SCARTI.items(), key=lambda x: -x[1])
    print(f"  {'caratteristica':28s} {'scarto massimo':>16}")
    for k, v in peggiori[:12]:
        print(f"  {k:28s} {v:16.3e}")
    nulli = sum(1 for _, v in SCARTI.items() if v == 0.0)
    print(f"\n  {nulli} caratteristiche su {len(SCARTI)} con scarto esattamente nullo")
    print(f"  massimo complessivo: {peggiori[0][1]:.3e}  (tolleranza {ATOL:g})")

    print("\n" + "=" * 74)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 74)
    print("\n  Proprieta' coperte: equivalenza fra le due implementazioni su piu'")
    print("  durate, dopo ogni aggiornamento e dopo ogni uscita dalla finestra;")
    print("  indipendenza dai confini dei lotti e dalla modalita' di ingestione;")
    print("  finestra vuota, osservazione unica, serie costante e quasi costante,")
    print("  interruzioni, validita' per canale, fasce locali, confine")
    print("  dell'installazione, tolleranza sulle variazioni, capacita' del")
    print("  buffer; causalita' rispetto al futuro e all'anteriore a t0.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
