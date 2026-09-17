#!/usr/bin/env python3
"""
Costruttore delle maschere di validita', dalla sorgente e prima del riempimento.
================================================================================
Produce un artefatto versionato con, per nodo e istante: i valori dinamici PRIMA
del riempimento, le due maschere, e identificativi e marche temporali allineati
ai bersagli.

**Le maschere non si ricavano dai valori gia' riempiti.** Si risale ai file
`speed_classes`, dove l'assenza di una riga e l'invalidita' di un valore sono
distinguibili — cosa che l'artefatto denso, dove entrambe diventano zero, non
consente.

LE REGOLE, approvate e verificate sui dati:

    maschera_volume_class = riga presente
                          ∧ volume_class ∈ {1, 3, 5}

    maschera_r            = riga presente
                          ∧ median_speed_kph finita
                          ∧ median_speed_kph ≥ 0
                          ∧ riferimento RISOLTO finito
                          ∧ riferimento RISOLTO > 0
                          ∧ rapporto non troncato finito

IL RIFERIMENTO E' QUELLO RISOLTO PER SEGMENTO, non la copia presente in ogni riga.
E' il medesimo denominatore che costruisce `r`, sicche' la validita' del rapporto
deve dipendere da esso: una riga priva della copia del riferimento, con velocita'
valida e riferimento del segmento gia' disponibile, non rende invalido quel
rapporto. La validita' del riferimento di RIGA si conserva come indicatore
DIAGNOSTICO della sorgente, non come condizione aggiuntiva.

LA VELOCITA' ZERO RESTA VALIDA — rappresenta traffico fermo. **La velocita'
negativa non deve diventare valida grazie al troncamento**: il rapporto si verifica
PRIMA di troncarlo.

LA VERIFICA DI APPARTENENZA alle classi ammesse resta nel codice anche dove
equivale alla sola presenza della riga: sui dati controllati `volume_class` vale
soltanto 1, 3, 5 e non ha valori mancanti, ma la regola non si affida a quella
constatazione.

QUESTE NON SONO LE MASCHERE UFFICIALI TRAFFIC4CAST. Sono maschere della nostra
pipeline: non si applica alcun filtro di affidabilita' basato sulla numerosita'
delle sonde, e l'eventuale corrispondenza con i filtri del protocollo ufficiale
non e' stata verificata.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/costruisci_maschere.py --contesto Madrid
    poetry run python evoluzione/esperimenti/costruisci_maschere.py --giorni 5
"""
import argparse
import glob as globmod
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.riferimento import (  # noqa: E402
    AnagraficaRiferimenti, resolve_reference)

VERSIONE_COSTRUTTORE = "1.0"
T4 = "data_collection/traffic4cast"
CLASSI_VOLUME = (1, 3, 5)
TRONCAMENTO = (0.0, 1.5)

CTX = {
    "Madrid": (f"{T4}/MADRID_2022", "targets_t4cmad_d8.npz"),
    "Londra": (f"{T4}/LONDON_2022", "targets_t4cmad_d8.npz"),
    "Melbourne": (f"{T4}/MELBOURNE_2022", "targets_t4cmel_d8.npz"),
}


def impronta(a) -> str:
    x = np.ascontiguousarray(a)
    h = hashlib.sha256(x.tobytes())
    h.update(str((x.shape, x.dtype.str)).encode())
    return h.hexdigest()[:16]


def costruisci(nome: str, radice: str, bersagli: str, giorni=None,
               out: Path | None = None) -> dict:
    tp = f"{radice}/gomo_fmt/{bersagli}"
    if not globmod.glob(tp):
        return {"contesto": nome, "errore": f"bersagli non trovati: {tp}"}
    z = np.load(tp, allow_pickle=True)
    sid = z["sensor_ids"].astype(str)
    ts = pd.to_datetime(z["timestamps"])
    S, T = len(sid), len(ts)

    # -- la griglia: da (u, v) e (day, t) alle posizioni dei bersagli --------
    pos_sensore = {}
    for i, s in enumerate(sid):
        p = s.split("_")
        if len(p) == 2:
            pos_sensore[(int(p[0]), int(p[1]))] = i
    # gli istanti: `day` e `t` della sorgente contro le marche dei bersagli
    per_data = {}
    for j, x in enumerate(ts):
        per_data.setdefault(x.date(), {})[x.hour * 4 + x.minute // 15] = j

    # -- i valori PRIMA del riempimento -------------------------------------
    speed = np.full((T, S), np.nan, dtype="float32")
    vol = np.full((T, S), np.nan, dtype="float32")
    ff_riga = np.full((T, S), np.nan, dtype="float32")
    riga = np.zeros((T, S), dtype=bool)

    f = (sorted(globmod.glob(f"{radice}/speed_classes/*/speed_classes_*.parquet"))
         or sorted(globmod.glob(f"{radice}/speed_classes/*/speed_classes_*.csv")))
    if giorni:
        f = f[:giorni]
    if not f:
        return {"contesto": nome, "errore": "file sorgente non trovati"}
    righe_lette = righe_usate = 0
    for x in f:
        col = ["u", "v", "day", "t", "volume_class", "median_speed_kph",
               "free_flow_kph"]
        d = (pd.read_parquet(x, columns=col) if str(x).endswith(".parquet")
             else pd.read_csv(x, usecols=col))
        righe_lette += len(d)
        giorno = pd.to_datetime(d.day.iloc[0]).date() if len(d) else None
        mappa_t = per_data.get(giorno)
        if mappa_t is None:
            continue
        si = np.array([pos_sensore.get((u, v), -1)
                       for u, v in zip(d.u.to_numpy(), d.v.to_numpy())])
        ti = np.array([mappa_t.get(int(k), -1) for k in d.t.to_numpy()])
        ok = (si >= 0) & (ti >= 0)
        righe_usate += int(ok.sum())
        si, ti = si[ok], ti[ok]
        speed[ti, si] = d.median_speed_kph.to_numpy("float32")[ok]
        vol[ti, si] = d.volume_class.to_numpy("float32")[ok]
        ff_riga[ti, si] = d.free_flow_kph.to_numpy("float32")[ok]
        riga[ti, si] = True

    # -- il riferimento RISOLTO per segmento --------------------------------
    An = AnagraficaRiferimenti.da_artefatto(tp)
    rif = np.full(S, np.nan, dtype="float64")
    stati = {}
    for i, s in enumerate(sid):
        r = resolve_reference(An, s)
        stati[r["status"]] = stati.get(r["status"], 0) + 1
        if r["reference_value"] is not None:
            rif[i] = r["reference_value"]
    rif_ok = np.isfinite(rif) & (rif > 0)

    # -- le maschere, secondo le regole approvate ---------------------------
    m_vol = riga & np.isin(vol, CLASSI_VOLUME)
    sp_ok = riga & np.isfinite(speed) & (speed >= 0)      # lo zero resta valido
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        grezzo = np.where(sp_ok & rif_ok[None, :],
                          speed / np.where(rif_ok, rif, 1.0)[None, :], np.nan)
    m_r = sp_ok & rif_ok[None, :] & np.isfinite(grezzo)   # PRIMA del troncamento

    # diagnostico: la validita' del riferimento di RIGA, che NON entra nella regola
    diag_riga = riga & np.isfinite(ff_riga) & (ff_riga > 0)

    man = {
        "versione_costruttore": VERSIONE_COSTRUTTORE,
        "contesto": nome,
        "istante": datetime.now(timezone.utc).isoformat(),
        "file_sorgente": len(f),
        "righe_lette": righe_lette,
        "righe_agganciate": righe_usate,
        "forma": [T, S],
        "reference_policy": "external_fixed_resolved",
        "reference_row_validity": "diagnostic_only",
        "speed_validity": "finite_and_nonnegative",
        "volume_class_validity": "membership_1_3_5",
        "ratio_validity": "checked_before_clipping",
        "additional_probe_reliability_filter": "none",
        "official_reliability_protocol": "unverified",
        "dynamic_validity_policy": "per_channel",
        # proprieta' dei DATI, non requisito: le due maschere devono poter
        # divergere su sorgenti future
        "r_and_volume_masks_equal": bool(np.array_equal(m_r, m_vol)),
        "verified_scope": "intero_periodo_e_popolazione_selezionata",
        "nota_ridondanza": (
            "dove le due maschere coincidono, la seconda e' RIDONDANTE rispetto "
            "alla prima — non costante nel tempo: entrambe variano, e variano "
            "insieme"),
        "stati_riferimento": stati,
        "impronte": {"maschera_r": impronta(m_r),
                     "maschera_volume_class": impronta(m_vol),
                     "speed_grezza": impronta(speed),
                     "volume_class_grezza": impronta(vol),
                     "riferimento_risolto": impronta(rif)},
        "conteggi": {
            "celle": int(T * S),
            "riga_presente": int(riga.sum()),
            "maschera_r": int(m_r.sum()),
            "maschera_volume_class": int(m_vol.sum()),
            "r_valida_su_righe_presenti": float(m_r.sum() / max(riga.sum(), 1)),
            "vol_valida_su_righe_presenti": float(m_vol.sum() / max(riga.sum(), 1)),
            "vol_valida_ma_r_no": int((m_vol & ~m_r).sum()),
            "r_valida_ma_vol_no": int((m_r & ~m_vol).sum()),
            "riferimento_di_riga_invalido_su_righe": int((riga & ~diag_riga).sum()),
        },
        "regole": {
            "maschera_volume_class": "riga_presente ∧ volume_class ∈ {1,3,5}",
            "maschera_r": ("riga_presente ∧ finite(median_speed) ∧ median_speed ≥ 0 "
                           "∧ finite(rif_risolto) ∧ rif_risolto > 0 "
                           "∧ finite(rapporto_non_troncato)"),
        },
        "avvertenza": ("maschere della NOSTRA pipeline, non ufficiali "
                       "Traffic4cast: nessun filtro di affidabilita' basato sulla "
                       "numerosita' delle sonde, e la corrispondenza con il "
                       "protocollo ufficiale non e' stata verificata"),
    }

    if out:
        out.mkdir(parents=True, exist_ok=True)
        p = out / f"maschere_{nome.replace('/', '-')}.npz"
        np.savez_compressed(
            p, maschera_r=m_r, maschera_volume_class=m_vol,
            speed_grezza=speed, volume_class_grezza=vol,
            riferimento_risolto=rif, riga_presente=riga,
            riferimento_di_riga=ff_riga, sensor_ids=sid,
            timestamps=ts.values)
        (out / f"manifesto_{nome.replace('/', '-')}.json").write_text(
            json.dumps(man, indent=2, ensure_ascii=False))
        man["artefatto"] = str(p)
    return man


def main() -> int:
    ap = argparse.ArgumentParser(description="costruttore delle maschere")
    ap.add_argument("--contesto", nargs="*", default=list(CTX))
    ap.add_argument("--giorni", type=int, default=None)
    ap.add_argument("--out", type=Path,
                    default=Path("results/evoluzione/maschere"))
    a = ap.parse_args()

    for nome in a.contesto:
        radice, bers = CTX[nome]
        print("=" * 78)
        print(nome)
        print("=" * 78)
        m = costruisci(nome, radice, bers, a.giorni, a.out)
        if "errore" in m:
            print(f"  {m['errore']}\n")
            continue
        c = m["conteggi"]
        print(f"  {m['file_sorgente']} file | {m['righe_lette']:,} righe lette, "
              f"{m['righe_agganciate']:,} agganciate")
        print(f"  griglia {m['forma'][0]:,} x {m['forma'][1]} = {c['celle']:,} celle")
        print(f"\n  riga presente            {c['riga_presente']:>12,}  "
              f"({100*c['riga_presente']/c['celle']:6.2f}% delle celle)")
        print(f"  maschera_r               {c['maschera_r']:>12,}  "
              f"({100*c['r_valida_su_righe_presenti']:6.3f}% delle righe presenti)")
        print(f"  maschera_volume_class    {c['maschera_volume_class']:>12,}  "
              f"({100*c['vol_valida_su_righe_presenti']:6.3f}% delle righe presenti)")
        print(f"\n  volume valida ma r no    {c['vol_valida_ma_r_no']:>12,}")
        print(f"  r valida ma volume no    {c['r_valida_ma_vol_no']:>12,}")
        print(f"  [diagnostico] righe con riferimento di RIGA invalido: "
              f"{c['riferimento_di_riga_invalido_su_righe']:,}")
        print(f"     non entra nella regola: la validita' usa il riferimento "
              f"RISOLTO")
        print(f"\n  le due maschere coincidono: "
              f"{'sì' if m['r_and_volume_masks_equal'] else 'no'}"
              + ("  (ridondanza sui dati, non requisito)"
                 if m["r_and_volume_masks_equal"] else ""))
        print(f"  stati del riferimento: {m['stati_riferimento']}")
        print(f"  impronte: " + ", ".join(f"{k}={v}" for k, v in
                                          list(m["impronte"].items())[:2]))
        if "artefatto" in m:
            print(f"  -> {m['artefatto']}")
        print()
    print("=" * 78)
    print("  Maschere della NOSTRA pipeline, non ufficiali Traffic4cast.")
    print("  Nessun filtro di affidabilita' sulla numerosita' delle sonde; la")
    print("  corrispondenza con il protocollo ufficiale non e' stata verificata.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
