#!/usr/bin/env python3
"""
Prova di adeguatezza del budget di addestramento.
==================================================
**27 traiettorie complete, senza arresto anticipato**, fino a 2.290
aggiornamenti dell'ottimizzatore.

    3 citta' x 1 partizione (seme 1000) x 3 semi (301, 302, 303) x 3 modelli

IL TETTO: `max_optimizer_updates = 2290`, cioe' **circa dieci ESPOSIZIONI
NOMINALI del corpus temporale** — 32 x 2290 / N_origini — non dieci passate
effettive. Il protocollo precedente dichiarava 35 epoche, e questo tetto **non
riproduce integralmente quel budget inteso**: e' un tetto pilota per osservare
se il miglioramento prosegua molto oltre 35 aggiornamenti.

> **Se la curva migliora fino al tetto, la conclusione sara' «plateau non
> osservato entro il budget esplorato», NON «addestramento adeguato».**

IL CAMPIONAMENTO RESTA QUELLO ATTUALE: 32 istanti distinti dentro ogni
aggiornamento, nuove estrazioni ai successivi, con possibile riutilizzo nel
corso del training. E' un regime stocastico legittimo, purche' descritto
correttamente.

**La sequenza degli istanti e' IDENTICA fra C, P ed E della stessa
combinazione**, e indipendente dalla costruzione del modello: si pre-genera
prima di costruirlo.

I QUINDICI PUNTI DI CONTROLLO, a spaziatura crescente:

    1, 2, 5, 10, 20, 35, 50, 100, 200, 350, 500, 750, 1000, 1500, 2290

**Nessuna «pazienza 8» su questi punti**: otto verifiche avrebbero durate molto
diverse a seconda della posizione. I criteri di arresto si simulano a
posteriori, sul minimo osservato fra gli stessi quindici candidati; a parita',
il precedente.

**Nessun utilizzo del test.**

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/prova_adeguatezza.py --piano
    poetry run python evoluzione/esperimenti/prova_adeguatezza.py
"""
import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.analisi.pesi import carica as carica_pesi  # noqa: E402
from evoluzione.componente.canonico import (  # noqa: E402
    applica as applica_canonico, carica as carica_canonico,
    verifica as verifica_canonico)
from evoluzione.componente.identita import (  # noqa: E402
    LearnedNodeEmbedding, NoIdentity, ObservableIdentityEncoder)
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, N_CLASSI, NASCOSTI, ORIZZONTI, PredittorePerNodo)
from evoluzione.componente.valutazione import valuta_scomposto  # noqa: E402
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _canali, _carica, _descrittori, _lotto, _normalizzazione, _partizioni,
    _perdita)
from evoluzione.esperimenti.semi import SEME_PARTIZIONE, configurazione  # noqa

CONTESTI = ("Madrid", "Londra", "Melbourne")
MODELLI = ("C", "P", "E")
PARTIZIONE = 0                     # seme 1000
TETTO = 4580                       # il tetto della SENSIBILITA'
TETTO_PRINCIPALE = 2290            # il budget della campagna principale
# il calendario dei PILOTI, invariato fino a 2.290, piu' i punti dell'estensione
PUNTI = (1, 2, 5, 10, 20, 35, 50, 100, 200, 350, 500, 750, 1000, 1500, 2290,
         3000, 3500, 4000, 4580)
LOTTO = 32
PASSO = 1e-3
PREFISSO = 32                      # la finestra storicamente usata
D_STAT = 5


def sequenza_istanti(istanti, seme: int, tetto: int, lotto: int):
    """Gli istanti di OGNI aggiornamento, pre-generati.

    **Identica fra C, P ed E**: si costruisce prima del modello, sicche' non
    dipende da quante estrazioni il costruttore consumi.
    """
    g = np.random.default_rng(seme)
    return [np.sort(g.choice(istanti, size=min(lotto, len(istanti)),
                             replace=False)) for _ in range(tetto)]


def esposizioni(seq, n_origini: int) -> dict:
    """Origini distinte visitate e distribuzione delle esposizioni."""
    tutte = np.concatenate(seq)
    u, c = np.unique(tutte, return_counts=True)
    return {"estrazioni_totali": int(len(tutte)),
            "origini_distinte": int(len(u)),
            "origini_disponibili": int(n_origini),
            "copertura": float(len(u) / n_origini),
            "esposizioni_per_origine": {
                "minimo": int(c.min()), "mediana": float(np.median(c)),
                "massimo": int(c.max()), "media": float(c.mean())},
            "mai_visitate": int(n_origini - len(u))}


def scrivi_atomico(percorso: Path, salva_su) -> None:
    """Scrittura ATOMICA: un file incompleto non deve mai risultare valido.

    Si scrive su un temporaneo nella stessa cartella, si forza su disco, poi si
    rinomina: `os.replace` e' atomico sullo stesso filesystem.
    """
    percorso = Path(percorso)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    tmp = percorso.with_suffix(percorso.suffix + ".tmp")
    with open(tmp, "wb") as f:
        salva_su(f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, percorso)


def stato_completo(m, opt, u: int, seq_pos: int, gen_stati: dict,
                   meta: dict, migliore: dict) -> dict:
    """Tutto cio' che serve a RIPRENDERE, non a valutare.

    **Il punto CORRENTE e quello MIGLIORE sono distinti**: riprendere dal
    migliore altererebbe la traiettoria.
    """
    return {"tipo": "corrente",
            "model_state_dict": m.state_dict(),      # buffer inclusi
            "optimizer_state_dict": opt.state_dict(),
            "scheduler_state_dict": None,            # nessuno scheduler
            "ultimo_aggiornamento": int(u),
            "posizione_sequenza": int(seq_pos),
            "generatori": gen_stati,
            "selezione": migliore,                   # stato della selezione
            **meta}


def costruisci(modello: str, seme: int, d_desc: int, nodi_add, dir_can, cfg):
    """Il modello, con l'artefatto canonico applicato e verificato."""
    forn = {"C": lambda: NoIdentity(),
            "P": lambda: ObservableIdentityEncoder(d_desc),
            "E": lambda: LearnedNodeEmbedding(nodi_add)}[modello]()
    torch.manual_seed(seme)
    m = PredittorePerNodo(d_desc, D_STAT, sorgente="traffic4cast",
                          identita=forn)
    art = carica_canonico(seme, cfg, dir_can)
    applica_canonico(m, art)
    verifica_canonico(m, art, modello)          # BLOCCA se non conforme
    return m, art["impronta"]


def main() -> int:
    ap = argparse.ArgumentParser(description="prova di adeguatezza")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--modello", nargs="*", default=list(MODELLI))
    ap.add_argument("--piano", action="store_true")
    ap.add_argument("--riparti", action="store_true",
                    help="ignora i punti correnti e ricomincia da zero")
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    _, dich, semi = configurazione(adeguatezza=True)
    dir_p = a.out / "adeguatezza"
    cfg_comuni = {"c_in": len(CANALI_T4C), "nascosti": NASCOSTI, "blocchi": 4,
                  "d_statiche": D_STAT, "d_statiche_uscita": 8,
                  "n_orizzonti": len(ORIZZONTI), "n_classi": N_CLASSI}

    print("=" * 84)
    print(f"PROVA DI ADEGUATEZZA — tetto {TETTO} aggiornamenti")
    print("=" * 84)
    print(f"  {len(a.contesto)} citta' x 1 partizione (seme "
          f"{SEME_PARTIZIONE[PARTIZIONE]}) x {len(semi)} semi x "
          f"{len(a.modello)} modelli = "
          f"{len(a.contesto)*len(semi)*len(a.modello)} traiettorie")
    print(f"  semi dichiarati {list(dich)}")
    print(f"  punti di controllo: {list(PUNTI)}")
    print(f"  **nessun arresto anticipato**: i criteri si simulano a posteriori")
    print(f"  campionamento INVARIATO: {LOTTO} istanti distinti per "
          f"aggiornamento")

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        return 0

    dir_p.mkdir(parents=True, exist_ok=True)
    tempi = []
    for c in a.contesto:
        D = _carica(c, a.out / "maschere")
        nodi, ist = _partizioni(D, {"partizione": np.random.default_rng(
            SEME_PARTIZIONE[PARTIZIONE])})
        NORM, nr, nv = _normalizzazione(D, nodi, ist)
        x = _canali(D, nr, nv)
        K = D["r"].shape[1]
        stat = np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K),
                         np.zeros(K), np.ones(K)], 1).astype("float32")
        w = torch.as_tensor(
            carica_pesi(a.out / "pesi", c, PARTIZIONE).vettore(),
            dtype=torch.float32)
        n_or = len(ist["addestramento"])
        print(f"\n{'=' * 84}\n{c}  —  32 x {TETTO} / {n_or} = "
              f"{32*TETTO/n_or:.1f} esposizioni nominali\n{'=' * 84}")

        for i_s, s in enumerate(semi):
            s = int(s)
            # LA SEQUENZA, pre-generata: identica fra i tre modelli
            seq = sequenza_istanti(ist["addestramento"], s, TETTO, LOTTO)
            esp = esposizioni(seq, n_or)
            for mod in a.modello:
                f_out = dir_p / f"traj_{c}_{mod}_s{dich[i_s]}.json"
                if f_out.exists():
                    continue
                d_desc = 0
                dtr = None
                if mod == "P":
                    from evoluzione.componente.estrattore import SCHEMI_T4C
                    S = SCHEMI_T4C["BASE-CORRECTED"]
                    d_desc = len(S["statistiche"]) + len(S["disponibilita"])
                    dtr = _descrittori(D, nodi["addestramento"],
                                       int(ist["addestramento"][-1]),
                                       "BASE-CORRECTED", NORM)
                m, imp_can = costruisci(mod, s, d_desc, nodi["addestramento"],
                                        a.out / "canonico", cfg_comuni)
                opt = torch.optim.Adam(m.parameters(), lr=PASSO)
                St = torch.as_tensor(stat[nodi["addestramento"]])
                righe, t0 = [], time.time()
                u0 = 0
                migliore = {"aggiornamento": None, "V-full": float("inf")}
                # ---- RIPRESA dal punto CORRENTE, mai dal migliore ---------
                f_ck = dir_p / f"ck_{c}_{mod}_s{dich[i_s]}_corrente.pt"
                if f_ck.exists() and not a.riparti:
                    d_ck = torch.load(f_ck, map_location="cpu",
                                      weights_only=False)
                    if d_ck.get("tipo") != "corrente":
                        raise RuntimeError(
                            f"{f_ck.name} non e' un punto CORRENTE: "
                            f"riprendere dal migliore altererebbe la "
                            f"traiettoria")
                    m.load_state_dict(d_ck["model_state_dict"], strict=True)
                    opt.load_state_dict(d_ck["optimizer_state_dict"])
                    u0 = int(d_ck["ultimo_aggiornamento"])
                    righe = d_ck.get("curve", [])
                    migliore = d_ck.get("selezione", migliore)
                    torch.set_rng_state(
                        torch.as_tensor(d_ck["generatori"]["torch"],
                                        dtype=torch.uint8))
                    print(f"  ripresa {c[:3]} {mod} s{dich[i_s]} da u{u0}",
                          flush=True)
                for u in range(u0 + 1, TETTO + 1):
                    m.train()
                    X, Y, Mk = _lotto(x, D["classe"], seq[u - 1],
                                      nodi["addestramento"])
                    out = m(X, node_ids=nodi["addestramento"],
                            descriptor=dtr, static_inputs=St)
                    L, _ = _perdita(out, Y, Mk, w)
                    opt.zero_grad(); L.backward(); opt.step()
                    if u in PUNTI:
                        r = valuta_scomposto(
                            m, x, D["classe"], stat, nodi["addestramento"],
                            ist["validazione"], w, prefisso=PREFISSO,
                            descrittore=_descrittori(
                                D, nodi["addestramento"],
                                int(ist["validazione"][0]), "BASE-CORRECTED",
                                NORM) if mod == "P" else None)
                        righe.append({
                            "aggiornamento": u, "training": float(L.detach()),
                            "V-prefix": r["V-prefix"]["perdita"],
                            "V-full": r["V-full"]["perdita"],
                            "V-rest": r["V-rest"]["perdita"],
                            "celle_full": r["V-full"]["celle_totali"]})
                        if r["V-full"]["perdita"] < migliore["V-full"]:
                            migliore = {"aggiornamento": u,
                                        "V-full": r["V-full"]["perdita"]}
                        print(f"  {c[:3]} {mod} s{dich[i_s]} u{u:5d}  "
                              f"train {float(L.detach()):.5f}  "
                              f"prefix {r['V-prefix']['perdita']:.5f}  "
                              f"full {r['V-full']['perdita']:.5f}",
                              flush=True)
                        # ---- il punto CORRENTE, per la ripresa ------------
                        meta = {"contesto": c, "modello": mod,
                                "seme": int(dich[i_s]), "seme_torch": s,
                                "partizione": PARTIZIONE, "tetto": TETTO,
                                "impronta_canonico": imp_can,
                                "curve": righe,
                                "impronta_sequenza": hashlib.sha256(
                                    np.concatenate(seq).tobytes()
                                ).hexdigest()[:16]}
                        st = stato_completo(
                            m, opt, u, u,
                            {"torch": torch.get_rng_state().tolist()},
                            meta, migliore)
                        scrivi_atomico(f_ck, lambda f: torch.save(st, f))
                        # ---- e il punto MIGLIORE, per la valutazione ------
                        if migliore["aggiornamento"] == u:
                            f_mi = dir_p / (f"ck_{c}_{mod}_s{dich[i_s]}"
                                            f"_migliore.pt")
                            mi = {"tipo": "migliore",
                                  "model_state_dict": m.state_dict(),
                                  "aggiornamento": u,
                                  "V-full": r["V-full"]["perdita"], **meta}
                            scrivi_atomico(f_mi,
                                           lambda f: torch.save(mi, f))
                dt = time.time() - t0
                tempi.append(dt)
                scrivi_atomico(f_out, lambda f: f.write(json.dumps({
                    "contesto": c, "modello": mod, "seme": int(dich[i_s]),
                    "seme_torch": s, "partizione": PARTIZIONE,
                    "tetto": TETTO, "punti": list(PUNTI),
                    "esposizioni_nominali": 32 * TETTO / n_or,
                    "impronta_canonico": imp_can,
                    "campionamento": esp,
                    "curve": righe, "secondi": dt,
                    "tetto_principale": TETTO_PRINCIPALE,
                    "istante": datetime.now(timezone.utc).isoformat()},
                    indent=2, ensure_ascii=False).encode()))
                # ---- CONFRONTO con la traiettoria pilota originaria -----
                # **Non si assume l'identita': si verifica.** Stessi semi e
                # sequenza la rendono plausibile, non garantita.
                f_vec = dir_p / "originali" / f"traj_{c}_{mod}_s{dich[i_s]}.json"
                if f_vec.exists():
                    vec = json.loads(f_vec.read_text())
                    com = {r["aggiornamento"]: r for r in vec["curve"]}
                    scarti = [(r["aggiornamento"],
                               abs(r["V-full"] - com[r["aggiornamento"]]["V-full"]))
                              for r in righe if r["aggiornamento"] in com]
                    if scarti:
                        mx = max(z for _, z in scarti)
                        print(f"     confronto col pilota originario su "
                              f"{len(scarti)} punti comuni: scarto massimo "
                              f"{mx:.2e} "
                              f"{'IDENTICHE' if mx == 0 else 'DIVERGENTI'}")
                        if mx > 1e-6:
                            print(f"     > divergenza INATTESA: va indagata "
                                  f"PRIMA di interpretare l'estensione")
                print(f"     -> {dt/60:.1f} min")
                if len(tempi) == 1:
                    print(f"\n  PREVISIONE aggiornata dalla prima traiettoria: "
                          f"{dt*27/3600:.1f} ore per 27")
                    print(f"  (la previsione si aggiorna, il BUDGET no)\n")

    print(f"\n{'=' * 84}")
    if tempi:
        print(f"  {len(tempi)} traiettorie, mediana {np.median(tempi)/60:.1f} "
              f"min, totale {sum(tempi)/3600:.1f} ore")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
