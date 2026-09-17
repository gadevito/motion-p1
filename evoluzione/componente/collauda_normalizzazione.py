#!/usr/bin/env python3
"""
Collaudo del contratto di normalizzazione.
==========================================
Nessun addestramento.

    1. corrispondenza fra schema delle caratteristiche e schema della
       normalizzazione;
    2. chiave mancante o errata: errore BLOCCANTE, non trasformazione saltata;
    3. esenzioni esplicite per maschere e caratteristiche non standardizzate;
    4. parametri finiti e scale utilizzabili;
    5. una caratteristica non classificata solleva.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_normalizzazione.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    SCHEMI, SCHEMI_T4C, Osservazioni, estrai_diretto)
from evoluzione.componente.normalizzazione import (  # noqa: E402
    ContrattoViolato, applica, chiave_e_centratura, verifica_contratto)

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def solleva(fn, *a, **k):
    try:
        fn(*a, **k)
        return None
    except ContrattoViolato as e:
        return str(e)


def main() -> int:
    print("[1] corrispondenza fra i due schemi")
    for eti, S in (("GO-MO", SCHEMI), ("Traffic4cast", SCHEMI_T4C)):
        for v, sch in S.items():
            ns, nq = sch["statistiche"], sch["disponibilita"]
            # la normalizzazione MINIMA che soddisfa il contratto
            chiavi = sorted({chiave_e_centratura(n)[0] for n in ns + nq
                             if chiave_e_centratura(n)})
            norm = {k: (0.5, 0.2) for k in chiavi}
            r = verifica_contratto(ns, nq, norm, f"{eti}/{v}")
            verifica(f"1-{eti[:4]}-{v[:4]}", f"{eti} {v}: contratto soddisfatto",
                     r["n_normalizzate"] + r["n_esenti"] == len(ns) + len(nq),
                     f"{r['n_normalizzate']} normalizzate, {r['n_esenti']} esenti, "
                     f"chiavi {r['chiavi_usate']}")

    print("\n[2] chiave mancante o errata: BLOCCANTE")
    S = SCHEMI_T4C["EXTENDED"]
    ns, nq = S["statistiche"], S["disponibilita"]
    buone = {"media_r": (0.5, 0.2), "media_volume_class": (2.0, 1.5)}
    msg = solleva(verifica_contratto, ns, nq, {"media_r": (0.5, 0.2)})
    verifica(2, "una chiave assente solleva",
             msg and "media_volume_class" in msg)
    # la chiave STORICA, che era il difetto trovato
    msg = solleva(verifica_contratto, ns, nq,
                  {"media_r": (0.5, 0.2), "media_f": (2.0, 1.5)})
    verifica("2b", "la chiave con il nome VECCHIO non basta",
             msg and "media_volume_class" in msg,
             "era il difetto: con `media_f` la standardizzazione non si "
             "applicava e le statistiche uscivano grezze")
    verifica("2c", "il messaggio elenca le chiavi fornite",
             msg and "chiavi fornite" in msg)
    # e `applica` solleva anche a valle
    verifica("2d", "anche l'applicazione solleva, non restituisce il grezzo",
             solleva(applica, "media_volume_class", 3.0, {"media_r": (0, 1)})
             is not None)

    print("\n[3] esenzioni dichiarate")
    for nome in ("freq_classe_1", "autocorr_1", "quota_incremento",
                 "copertura_r", "disponibilita_banda_3", "durata_nominale",
                 "maschera_r", "quota_validi", "codice_durata"):
        verifica(f"3-{nome[:14]}", f"«{nome}» esente",
                 chiave_e_centratura(nome) is None)
    verifica("3z", "un esente attraversa `applica` invariato",
             applica("freq_classe_1", 0.37, buone) == 0.37)

    print("\n[4] parametri finiti e scale utilizzabili")
    for perche, cattiva in (("scala nulla", {"media_r": (0.5, 0.0)}),
                            ("scala negativa", {"media_r": (0.5, -1.0)}),
                            ("media non finita", {"media_r": (np.nan, 1.0)}),
                            ("scala non finita", {"media_r": (0.5, np.inf)}),
                            ("non e' una coppia", {"media_r": 0.5})):
        n2 = dict(buone); n2.update(cattiva)
        msg = solleva(verifica_contratto, ns, nq, n2)
        verifica(f"4-{perche[:12]}", perche, msg is not None,
                 (msg or "").splitlines()[1].strip() if msg else "NON solleva")

    print("\n[4bis] canale costante: accidentale contro dichiarato")
    L = SCHEMI_T4C["LEGACY"]
    nL = {"media_r": (0.7, 0.2), "media_conteggio": (2.0, 1.5),
          "media_occupazione": (0.0, 1e-6)}
    msg = solleva(verifica_contratto, L["statistiche"], L["disponibilita"], nL)
    verifica("4b1", "una scala minuscola NON dichiarata solleva",
             msg is not None and "dichiarato costante" in msg,
             "i numeri non distinguono una scala accidentale da una "
             "convenzionale: lo fa la dichiarazione")
    r = verifica_contratto(L["statistiche"], L["disponibilita"], nL,
                           canali_costanti={"occupazione"})
    verifica("4b2", "dichiarato costante: ammesso e registrato",
             r["n_costanti_dichiarate"] == 1
             and "media_occupazione" in r["convenzionali"])
    verifica("4b3", "i due conteggi sono distinti e non si confondono",
             r["nominali_totali"] == 16 and r["variabili_totali"] == 14
             and r["n_normalizzate"] == 14 and r["normalizzate_variabili"] == 12,
             f"LEGACY su Traffic4cast: {r['nominali_totali']} componenti nominali "
             f"e {r['variabili_totali']} variabili sull'INTERO schema; "
             f"{r['n_normalizzate']} e {r['normalizzate_variabili']} fra le sole "
             f"NORMALIZZATE. Le due dell'occupazione sono costanti a zero.")

    print("\n[5] una caratteristica non classificata solleva")
    verifica(5, "un nome ignoto non passa per difetto",
             solleva(chiave_e_centratura, "grandezza_nuova") is not None,
             "estendere lo schema senza dichiarare il trattamento e' un difetto")

    print("\n[6] il contratto e' attivo dentro l'estrattore")
    n = 200
    O = Osservazioni(np.arange(n), np.full(n, .5), np.full(n, 2.),
                     np.full(n, 1.), np.ones(n, dtype=int),
                     (np.arange(n) // 4) % 24, t0=0)
    ok = solleva(estrai_diretto, O, t=150, L=96, schema="EXTENDED",
                 sorgente="traffic4cast", norm={"media_r": (0.5, 0.2)})
    verifica(6, "estrarre con normalizzazione incompleta SOLLEVA",
             ok is not None and "media_volume_class" in ok)
    e = estrai_diretto(O, t=150, L=96, schema="EXTENDED",
                       sorgente="traffic4cast", norm=buone)
    verifica("6b", "con la normalizzazione completa l'estrazione riesce",
             np.isfinite(e.statistics).all())
    e2 = estrai_diretto(O, t=150, L=96, schema="EXTENDED",
                        sorgente="traffic4cast")
    verifica("6c", "senza `norm` si estrae il grezzo, senza sollevare",
             np.isfinite(e2.statistics).all()
             and not np.allclose(e.statistics, e2.statistics),
             "l'assenza TOTALE di normalizzazione e' una scelta esplicita; "
             "una chiave mancante su una normalizzazione dichiarata no")

    print("\n" + "=" * 68)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 68)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
