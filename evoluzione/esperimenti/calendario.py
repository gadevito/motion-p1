#!/usr/bin/env python3
"""
Calendario degli episodi di inserimento, per REQUISITO DI AMMISSIBILITA'.
==========================================================================
**La regola e' deterministica e si applica a validazione E test.**

    il PRIMO t0 del periodo tale che l'intervallo [t0, t0 + 24 h] contenga
    almeno N = 90 marche temporali

Con **N = 90** su 96 attese: tollera qualche marca mancante senza ammettere
episodi sostanzialmente vuoti. **Fissato PRIMA di osservare qualunque
prestazione.**

**Non e' una scelta in funzione della copertura**: e' un requisito di
ammissibilita', che il disegno prevede esplicitamente. La regola non guarda le
prestazioni ne' la qualita' dei dati, solo la **presenza delle marche**.

SI APPLICA ANCHE AL TEST. Il calendario di test congelato — 1 dicembre per
Madrid, 1 gennaio per Londra, 30 novembre per Melbourne — ha 97 marche in
ventiquattro ore su tutti e tre, sicche' **soddisfa gia' il requisito**. Se la
regola lo confermasse, resta invariato; se lo spostasse, la campagna E andrebbe
rieseguita e la cosa va dichiarata.

**La finestra e' una DURATA di calendario**, non un conteggio di passi: 96 passi
possono coprire otto giorni se la serie ha interruzioni, ed e' quanto accade nel
periodo di validazione di Madrid e Londra.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/calendario.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

N_MINIMO = 90            # marche richieste in ventiquattro ore
ORE = 24
ORIZZONTI = (1, 2, 4, 8)
FINESTRA = 12
T4 = "data_collection/traffic4cast"
CTX = {"Madrid": f"{T4}/MADRID_2022/gomo_fmt/targets_t4cmad_d8.npz",
       "Londra": f"{T4}/LONDON_2022/gomo_fmt/targets_t4cmad_d8.npz",
       "Melbourne": f"{T4}/MELBOURNE_2022/gomo_fmt/targets_t4cmel_d8.npz"}
# il calendario di TEST congelato, da confermare con la regola
TEST_CONGELATO = {"Madrid": 8887, "Londra": 8966, "Melbourne": 8806}


class EpisodioNonAmmissibile(RuntimeError):
    """Nessun t0 del periodo soddisfa il requisito."""


def marche_in_24h(ts, t0: int) -> int:
    """Quante marche cadono in [t0, t0 + 24 h]. **Durata, non passi.**"""
    fine = ts[t0] + pd.Timedelta(hours=ORE)
    j = int(np.searchsorted(ts.values, np.datetime64(fine), side="right"))
    return j - t0


def primo_ammissibile(ts, inizio: int, fine: int, n_minimo: int = N_MINIMO):
    """Il PRIMO t0 in [inizio, fine) che soddisfa il requisito.

    Si richiede anche che dopo l'episodio resti spazio per la valutazione:
    almeno un'origine con tutti i bersagli entro `fine`.
    """
    for t0 in range(inizio, fine):
        n = marche_in_24h(ts, t0)
        if n < n_minimo:
            continue
        # la fine dell'episodio, per DURATA
        t1 = t0 + n - 1
        if t1 + FINESTRA + max(ORIZZONTI) >= fine:
            continue                    # niente spazio per valutare
        return {"t0": t0, "t1": t1, "marche": n,
                "istante_t0": str(ts[t0]), "istante_t1": str(ts[t1]),
                "durata_h": (ts[t1] - ts[t0]).total_seconds() / 3600,
                "scarto_dall_inizio": t0 - inizio}
    raise EpisodioNonAmmissibile(
        f"nessun t0 in [{inizio}; {fine}) con almeno {n_minimo} marche in "
        f"{ORE} ore e spazio per la valutazione")


def calendario(contesto: str, n_minimo: int = N_MINIMO) -> dict:
    z = np.load(CTX[contesto], allow_pickle=True)
    ts = pd.to_datetime(z["timestamps"])
    T = len(ts)
    e = T - max(ORIZZONTI)
    conf = {"addestramento": (FINESTRA - 1, int(e * 0.70)),
            "validazione": (int(e * 0.70), int(e * 0.85)),
            "prova": (int(e * 0.85), e)}
    fuori = {"contesto": contesto, "n_minimo": n_minimo, "confini": conf}
    for eti in ("validazione", "prova"):
        a, b = conf[eti]
        try:
            fuori[eti] = primo_ammissibile(ts, a, b, n_minimo)
        except EpisodioNonAmmissibile as exc:
            fuori[eti] = {"errore": str(exc)}
    # il confronto col calendario di TEST congelato
    t0c = TEST_CONGELATO.get(contesto)
    if t0c is not None:
        fuori["test_congelato"] = {
            "t0": t0c, "istante": str(ts[t0c]),
            "marche_24h": marche_in_24h(ts, t0c),
            "soddisfa_il_requisito": marche_in_24h(ts, t0c) >= n_minimo}
        p = fuori.get("prova", {})
        fuori["test_confermato"] = p.get("t0") == t0c
    return fuori


def main() -> int:
    print("=" * 84)
    print(f"CALENDARIO DEGLI EPISODI — requisito: almeno {N_MINIMO} marche "
          f"in {ORE} ore")
    print("=" * 84)
    print("  Regola deterministica, fissata PRIMA di osservare prestazioni.")
    print("  Si applica a VALIDAZIONE e TEST: nessuna regola ad hoc per l'una.")
    print("  La finestra e' una DURATA di calendario, non un conteggio di passi.")
    fuori = {}
    for c in CTX:
        d = calendario(c)
        fuori[c] = d
        print(f"\n{'=' * 84}\n{c}\n{'=' * 84}")
        for eti in ("validazione", "prova"):
            x = d[eti]
            if "errore" in x:
                print(f"  {eti:12s} NON AMMISSIBILE: {x['errore'][:60]}")
                continue
            print(f"  {eti:12s} t0 {x['t0']:6d} {x['istante_t0']}  ->  "
                  f"t1 {x['t1']:6d} {x['istante_t1']}")
            print(f"  {'':12s} {x['marche']} marche in {x['durata_h']:.0f} ore | "
                  f"scarto dall'inizio del periodo: {x['scarto_dall_inizio']} "
                  f"passi")
        tc = d.get("test_congelato", {})
        if tc:
            print(f"\n  calendario di TEST congelato: t0 {tc['t0']} "
                  f"{tc['istante']}")
            print(f"     {tc['marche_24h']} marche in 24 ore, requisito "
                  f"{'SODDISFATTO' if tc['soddisfa_il_requisito'] else 'NON soddisfatto'}")
            print(f"     la regola {'CONFERMA' if d.get('test_confermato') else 'SPOSTA'} "
                  f"il calendario congelato")
    print(f"\n{'=' * 84}")
    spostati = [c for c, d in fuori.items() if not d.get("test_confermato")]
    if spostati:
        print(f"  ATTENZIONE: la regola sposta il test su {spostati}.")
        print(f"  La campagna E va rieseguita e la cosa va DICHIARATA.")
    else:
        print(f"  La regola CONFERMA il calendario di test su tutte le citta':")
        print(f"  nessuna riesecuzione necessaria.")
    non_amm = [c for c, d in fuori.items() if "errore" in d.get("validazione", {})]
    if non_amm:
        print(f"\n  EPISODI DI VALIDAZIONE NON AMMISSIBILI: {non_amm}")
        print(f"  Va deciso se escludere quelle citta' dalla selezione di F o")
        print(f"  rilassare il requisito — decisione da PRENDERE, non da")
        print(f"  aggirare.")
    print(f"\n  **L'episodio di validazione e quello di test possono avere")
    print(f"  copertura diversa**: la configurazione di F e' scelta in")
    print(f"  condizioni che possono non coincidere con quelle di")
    print(f"  applicazione, e la differenza va riportata coi risultati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
