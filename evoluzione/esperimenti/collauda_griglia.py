#!/usr/bin/env python3
"""
Collaudo della correzione della griglia temporale, prima di ogni rigenerazione.
================================================================================
    [1] origini: nessuna, in nessun periodo, attraversa un salto
    [2] addestramento reale, tetto ridotto: OGNI istante passato a `_lotto`,
        per il training e per V-full, e' un'origine ammissibile
    [3] pesi: con la griglia si leggono da `pesi_griglia`; se mancano, SI
        FERMA invece di calcolarli al volo
    [4] descrittore: le finestre di riferimento reali coprono 24 ore; una
        finestra compressa viene BLOCCATA
    [5] F: convenzione (t0, t1] — nessuna finestra usa la riga t0 — e giornata
        di valutazione completa
    [6] calendario: la regola approvata riproduce le tabelle

Il percorso STORICO si verifica a parte con `collauda_protocolli.py`: deve
continuare a riprodurre il punto E congelato a scarto zero.

Scrive in `results/evoluzione/E_collaudo_griglia/`, mai nelle cartelle vere.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prepara_pesi_griglia.py
    poetry run python evoluzione/esperimenti/collauda_griglia.py
"""
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import evoluzione.esperimenti.addestramento as ADD  # noqa: E402
from evoluzione.componente import griglia as GR  # noqa: E402
from evoluzione.componente.registro import Registro  # noqa: E402
from evoluzione.esperimenti.semi import SEME_PARTIZIONE  # noqa: E402

OUT = Path("results/evoluzione")
ESITI = []
TEST = {"Madrid": (8887, 8983), "Londra": (8966, 9062), "Melbourne": (8806, 8902)}
VAL = {"Madrid": (7392, 7488), "Londra": (7389, 7485), "Melbourne": (7392, 7488)}


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


def ammissibile_lento(ts, t):
    """Verifica indipendente: le 20 righe t-11..t+8 distano 15 minuti."""
    if t - 11 < 0 or t + 8 >= len(ts):
        return False
    d = np.diff(ts[t - 11: t + 9].values).astype("timedelta64[m]").astype(int)
    return bool((d == 15).all())


class Esec:
    contesto, partizione, inizializzazione, variante = "Madrid", 0, 0, None


def main() -> int:
    print("=" * 78)
    print("COLLAUDO DELLA GRIGLIA TEMPORALE")
    print("=" * 78)

    # ---- [1] origini ---------------------------------------------------
    print("\n[1] origini per periodo, verifica indipendente")
    for c in ("Madrid", "Londra", "Melbourne"):
        D = ADD._carica(c, OUT / "maschere")
        ok = GR.passi_regolari(D["ts"])
        amm = GR.maschera_origini(ok)
        _, ist = ADD._partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[0])})
        cattive = 0
        for k, v_ in ist.items():
            for t in GR.filtra(v_, amm):
                cattive += not ammissibile_lento(D["ts"], int(t))
        v(f"1-{c[:3]}", f"{c}: nessuna origine filtrata attraversa un salto",
          cattive == 0, f"{sum(len(GR.filtra(x, amm)) for x in ist.values())} "
                        f"origini controllate, {cattive} irregolari")

    # ---- [2] addestramento reale, tetto ridotto -------------------------
    print("\n[2] addestramento con griglia reale: che cosa arriva a `_lotto`")
    visti = []
    orig_lotto = ADD._lotto

    def spia(x, classe, istanti, nodi):
        visti.extend(int(t) for t in np.asarray(istanti).ravel())
        return orig_lotto(x, classe, istanti, nodi)

    ADD._lotto = spia
    cfg = {"epoche": 35, "lotto": 32, "passo": 1e-3, "pazienza": 8,
           "storia_descrittore_passi": 96, "finestra_dinamica_passi": 12,
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": "E_collaudo_griglia", "braccio": "E",
           "training_protocol": "principale", "griglia_temporale": "reale",
           "max_optimizer_updates": 20, "punti": [5, 10, 20],
           "dir_pesi": str(OUT / "pesi_griglia"),
           "checkpoint_selection_population": "initial_network",
           "dir_canonico": str(OUT / "canonico"),
           "dir_stati_completi": str(OUT / "stati_completi_collaudo_griglia")}
    gen = {"partizione": np.random.default_rng(SEME_PARTIZIONE[0]),
           "inizializzazione": np.random.default_rng(201)}
    reg = Registro.avvia("E_collaudo_griglia/E", note="collaudo griglia",
                         radice=OUT / "registro_collaudo")
    reg.configurazione(cfg)
    try:
        ADD.addestra_una(Esec(), reg, cfg, gen, OUT)
        reg.completa()
    finally:
        ADD._lotto = orig_lotto
    D = ADD._carica("Madrid", OUT / "maschere")
    amm = GR.maschera_origini(GR.passi_regolari(D["ts"]))
    irregolari = [t for t in set(visti) if not amm[t]]
    v(2, "ogni istante dato a `_lotto` e' un'origine ammissibile",
      visti and not irregolari,
      f"{len(visti):,} istanti, {len(set(visti)):,} distinti, "
      f"{len(irregolari)} irregolari")
    man = json.loads(Path(reg._p).read_text())
    pp = man.get("protocollo_principale", {})
    _, ist = ADD._partizioni(D, {"partizione": np.random.default_rng(
        SEME_PARTIZIONE[0])})
    n_amm = len(GR.filtra(ist["addestramento"], amm))
    v("2b", "il manifesto registra le origini AMMISSIBILI come disponibili",
      pp.get("origini_disponibili") == n_amm,
      f"{pp.get('origini_disponibili')} contro {n_amm} attese")
    eventi = " ".join(str(e) for e in man.get("eventi", []))
    v("2c", "il manifesto dichiara la griglia reale",
      "griglia_temporale = reale" in eventi)

    # ---- [3] pesi --------------------------------------------------------
    print("\n[3] pesi")
    vuota = Path(tempfile.mkdtemp())
    try:
        ADD._pesi(Esec(), D, *ADD._partizioni(D, {"partizione":
                  np.random.default_rng(SEME_PARTIZIONE[0])}), OUT, "",
                  dir_pesi=vuota, solo_carica=True)
        ferma = False
    except ADD.FallimentoMetodo:
        ferma = True
    v(3, "con la griglia, pesi assenti -> SI FERMA", ferma,
      "calcolarli al volo con processi paralleli darebbe scritture concorrenti")
    r = json.loads((OUT / "pesi_griglia" / "rapporto_pesi_griglia.json")
                   .read_text())
    v("3b", "i pesi della griglia sono calcolati sulle origini ammissibili",
      all(x["origini"] < x["origini_storiche"] for x in r.values()),
      " | ".join(f"{k} {x['origini']}/{x['origini_storiche']}"
                 for k, x in list(r.items())[:3]))

    # ---- [4] descrittore ---------------------------------------------------
    print("\n[4] finestre del descrittore")
    for c in ("Madrid", "Londra", "Melbourne"):
        D = ADD._carica(c, OUT / "maschere"); ok = GR.passi_regolari(D["ts"])
        e = D["r"].shape[0] - 8
        rif = [int(e * .70) - 1, int(e * .70), TEST[c][1], VAL[c][1]]
        try:
            for t in rif:
                GR.verifica_finestra_descrittore(ok, t)
            buone = True
        except GR.GrigliaViolata:
            buone = False
        v(f"4-{c[:3]}", f"{c}: le quattro finestre di riferimento coprono 24 ore",
          buone, f"t = {rif}")
    salto = int(np.flatnonzero(~ok)[0])
    try:
        GR.verifica_finestra_descrittore(ok, salto + 10)
        bloccata = False
    except GR.GrigliaViolata:
        bloccata = True
    v("4b", "una finestra che attraversa un salto e' BLOCCATA", bloccata,
      f"t = {salto + 10}, salto fra le righe {salto} e {salto + 1}")

    # ---- [5] F: estremi e giornata di valutazione --------------------------
    print("\n[5] adattamento di F: convenzione (t0, t1]")
    for c in ("Madrid", "Londra", "Melbourne"):
        D = ADD._carica(c, OUT / "maschere"); ok = GR.passi_regolari(D["ts"])
        for nome, (t0, t1) in (("validazione", VAL[c]), ("prova", TEST[c])):
            o = GR.origini_acquisizione(ok, t0, t1)
            v(f"5-{c[:3]}-{nome[:3]}",
              f"{c}, {nome}: nessuna finestra usa t0, bersagli entro t1",
              o and min(t - 11 for t in o) >= t0 + 1 and max(o) + 8 <= t1,
              f"{len(o)} origini, prima riga {min(t - 11 for t in o)}, t0 = {t0}")
        fine_g = VAL[c][1] + 96
        ov = GR.origini_dopo(ok, VAL[c][1], fine_g + 1)
        v(f"5-{c[:3]}-gv", f"{c}: giornata di valutazione completa", len(ov) == 88,
          f"{len(ov)} origini (attese 88)")

    # ---- [6] calendario ------------------------------------------------------
    print("\n[6] calendario con la regola approvata")
    for c in ("Madrid", "Londra", "Melbourne"):
        D = ADD._carica(c, OUT / "maschere"); ok = GR.passi_regolari(D["ts"])
        e = D["r"].shape[0] - 8
        tv = GR.primo_t0(D["ts"], ok, int(e * .70), int(e * .85), True)
        tp = GR.primo_t0(D["ts"], ok, int(e * .85), e, False)
        v(f"6-{c[:3]}", f"{c}: validazione {tv}, prova {tp}",
          tv == VAL[c][0] and tp == TEST[c][0],
          f"attesi {VAL[c][0]} e {TEST[c][0]}")

    print("\n" + "=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    print("\n  Poi: collauda_protocolli.py, lo storico deve riprodurre E a scarto 0.")
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
