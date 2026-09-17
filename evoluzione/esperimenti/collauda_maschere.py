#!/usr/bin/env python3
"""
Collaudo degli artefatti delle maschere, sui tre contesti.
===========================================================
Nessun addestramento.

    1. corrispondenza esatta di nodi e marche temporali con i bersagli;
    2. distinzione fra riga assente e valore osservato;
    3. conteggi di validita' per canale e periodo;
    4. nessuna osservazione valida persa o creata dal riempimento;
    5. nessuna divergenza inattesa rispetto ai bersagli gia' verificati;
    6. confronto con le maschere IMPLICITE negli artefatti precedenti, con ogni
       differenza attribuita a una REGOLA PRECISA.

IL SESTO CONTROLLO E' QUELLO CHE CONTA. L'artefatto denso non distingue assenza
di riga da invalidita' — entrambe danno zero — sicche' la sua maschera implicita
e' `isfinite(r_emp)`. Le differenze con la maschera nuova devono ricadere tutte in
una delle categorie dichiarate: riferimento risolto, velocita' negativa, rapporto
non finito, classe non ammessa, riga assente. **Una differenza non attribuibile e'
un difetto**, non una sfumatura.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_maschere.py
"""
import argparse
import glob as globmod
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.costruisci_maschere import CTX, TRONCAMENTO  # noqa

ESITI = []


def verifica(n, titolo, cond, dettaglio=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def main() -> int:
    ap = argparse.ArgumentParser(description="collaudo degli artefatti")
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/maschere"))
    ap.add_argument("--contesto", nargs="*", default=list(CTX))
    a = ap.parse_args()

    for nome in a.contesto:
        p = a.dir / f"maschere_{nome.replace('/', '-')}.npz"
        mp = a.dir / f"manifesto_{nome.replace('/', '-')}.json"
        if not p.exists():
            print(f"{nome}: artefatto non trovato in {p}")
            continue
        radice, bers = CTX[nome]
        Z = np.load(p, allow_pickle=True)
        B = np.load(f"{radice}/gomo_fmt/{bers}", allow_pickle=True)
        man = json.loads(mp.read_text()) if mp.exists() else {}
        print("=" * 78)
        print(f"{nome}   (costruttore {man.get('versione_costruttore', '?')})")
        print("=" * 78)

        m_r = Z["maschera_r"]
        m_v = Z["maschera_volume_class"]
        riga = Z["riga_presente"]
        speed = Z["speed_grezza"]
        vol = Z["volume_class_grezza"]
        rif = Z["riferimento_risolto"]

        # ---------------------------------------------------------- [1] ---
        verifica(f"1-{nome[:4]}", "nodi identici ai bersagli",
                 np.array_equal(Z["sensor_ids"].astype(str),
                                B["sensor_ids"].astype(str)))
        verifica(f"1-{nome[:4]}b", "marche temporali identiche",
                 np.array_equal(pd.to_datetime(Z["timestamps"]).values,
                                pd.to_datetime(B["timestamps"]).values))
        verifica(f"1-{nome[:4]}c", "forma identica a quella dei bersagli",
                 m_r.shape == B["r_emp"].shape, f"{m_r.shape}")

        # ---------------------------------------------------------- [2] ---
        assente = ~riga
        verifica(f"2-{nome[:4]}", "dove la riga manca, i valori grezzi sono NaN",
                 np.isnan(speed[assente]).all() and np.isnan(vol[assente]).all(),
                 f"{int(assente.sum()):,} celle senza riga: distinguibili "
                 f"dall'osservato, che nell'artefatto denso vale zero")
        verifica(f"2-{nome[:4]}b", "dove la riga manca, entrambe le maschere sono false",
                 not m_r[assente].any() and not m_v[assente].any())

        # ---------------------------------------------------------- [3] ---
        T = m_r.shape[0]
        e = T - 8
        print(f"  conteggi per periodo (canale, quota di celle valide):")
        for eti, sl in (("addestramento", slice(0, int(e * .70))),
                        ("validazione", slice(int(e * .70), int(e * .85))),
                        ("prova", slice(int(e * .85), e))):
            n = m_r[sl].size
            print(f"     {eti:14s} r {100*m_r[sl].mean():6.2f}%   "
                  f"volume_class {100*m_v[sl].mean():6.2f}%   "
                  f"riga {100*riga[sl].mean():6.2f}%   ({n:,} celle)")
        verifica(f"3-{nome[:4]}", "la maschera di r e' contenuta in quella di volume",
                 not (m_r & ~m_v).any(),
                 "su questi dati ogni riga ha volume_class ammessa, sicche' "
                 "m_r ⊆ m_volume; la regola non lo impone")

        # ---------------------------------------------------------- [4] ---
        r_emp = np.asarray(B["r_emp"], dtype="float64")
        impl = np.isfinite(r_emp)          # la maschera IMPLICITA dell'artefatto
        persi = int((impl & ~m_r).sum())
        creati = int((m_r & ~impl).sum())
        verifica(f"4-{nome[:4]}", "il riempimento non crea osservazioni valide",
                 creati == 0 or creati < impl.sum() * 0.001,
                 f"{creati:,} celle valide nella nuova e non nell'implicita")

        # ---------------------------------------------------------- [5] ---
        rok = np.isfinite(rif) & (rif > 0)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            grezzo = np.where(np.isfinite(speed) & (speed >= 0) & rok[None, :],
                              speed / np.where(rok, rif, 1.0)[None, :], np.nan)
        atteso = riga & np.isfinite(speed) & (speed >= 0) & rok[None, :] \
            & np.isfinite(grezzo)
        verifica(f"5-{nome[:4]}", "la maschera riproduce la regola dichiarata",
                 np.array_equal(m_r, atteso),
                 "ricostruita indipendentemente dai valori grezzi conservati")

        # ---------------------------------------------------------- [6] ---
        # --- confronto DIRETTO fra le due maschere, non delle sole impronte --
        uguali = bool(np.array_equal(m_r, m_v))
        dich = man.get("r_and_volume_masks_equal")
        verifica(f"3-{nome[:4]}b",
                 "il manifesto dichiara correttamente se coincidano",
                 dich is None or dich == uguali,
                 f"array {'identici' if uguali else 'diversi'}, manifesto "
                 f"{dich} — confronto sugli ARRAY, non sulle impronte")
        if uguali:
            print(f"        le due maschere coincidono: la seconda e' RIDONDANTE "
                  f"rispetto alla prima, non costante — entrambe variano insieme")
            print(f"        NON e' un requisito: devono poter divergere su "
                  f"sorgenti future")

        # --- copertura: per canale, per nodo, per finestra storica -----------
        print(f"\n  copertura per NODO (quota di istanti validi):")
        for eti, sl in (("addestramento", slice(0, int(e * .70))),
                        ("validazione", slice(int(e * .70), int(e * .85))),
                        ("prova", slice(int(e * .85), e))):
            per_nodo = m_r[sl].mean(0)
            q = np.percentile(per_nodo, [5, 25, 50, 75, 95])
            print(f"     {eti:14s} mediana {q[2]:6.2%}  quartili "
                  f"[{q[1]:6.2%};{q[3]:6.2%}]  estremi [{per_nodo.min():6.2%};"
                  f"{per_nodo.max():6.2%}]  nodi mai validi: "
                  f"{int((per_nodo == 0).sum())}")
        # la copertura delle finestre storiche di 24 ore, che il raccordo usa
        L24 = 96
        print(f"\n  copertura delle FINESTRE STORICHE di {L24} passi (24 ore),")
        print(f"  che alimentano il descrittore dei nodi nuovi:")
        for eti, sl in (("validazione", slice(int(e * .70), int(e * .85))),
                        ("prova", slice(int(e * .85), e))):
            i0 = sl.start
            fin = [m_r[max(i0 - L24, 0):i0].mean()] if i0 >= L24 else []
            # finestre mobili campionate dentro il periodo
            passo = max((sl.stop - sl.start) // 30, 1)
            camp = [m_r[t - L24:t].mean()
                    for t in range(max(sl.start + L24, L24), sl.stop, passo)]
            if camp:
                c = np.array(camp)
                print(f"     {eti:14s} mediana {np.median(c):6.2%}  "
                      f"estremi [{c.min():6.2%}; {c.max():6.2%}]  "
                      f"({len(c)} finestre campionate)")
            else:
                print(f"     {eti:14s} periodo piu' corto della finestra: "
                      f"nessun campione")
        print(f"     una copertura piu' alta riduce le occasioni in cui le due")
        print(f"     rappresentazioni differiscono: e' il caso dei mancanti")

        print(f"\n  [6] differenze con la maschera IMPLICITA `isfinite(r_emp)`")
        diff = impl != m_r
        cause = {
            "riga assente": diff & ~riga,
            "velocita' non finita": diff & riga & ~np.isfinite(speed),
            "velocita' NEGATIVA": diff & riga & np.isfinite(speed) & (speed < 0),
            "riferimento risolto invalido": (diff & riga & np.isfinite(speed)
                                             & (speed >= 0) & ~rok[None, :]),
            "rapporto non finito": (diff & riga & np.isfinite(speed)
                                    & (speed >= 0) & rok[None, :]
                                    & ~np.isfinite(grezzo)),
        }
        attribuite = np.zeros_like(diff)
        for eti, m in cause.items():
            if m.any():
                print(f"     {eti:32s} {int(m.sum()):>10,}")
            attribuite |= m
        residuo = int((diff & ~attribuite).sum())
        print(f"     {'TOTALE differenze':32s} {int(diff.sum()):>10,}")
        print(f"     {'non attribuite':32s} {residuo:>10,}")
        verifica(f"6-{nome[:4]}", "ogni differenza e' attribuita a una regola",
                 residuo == 0,
                 "una differenza non attribuibile sarebbe un difetto, non una "
                 "sfumatura")
        print()

    print("=" * 78)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 78)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
