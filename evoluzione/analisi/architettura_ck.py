#!/usr/bin/env python3
"""
Architettura asserita dai checkpoint di E ed E′ (sezione III del paper).
=========================================================================
Per ogni punto di controllo `ck_*.pt` nelle cartelle di E ed E′ (citta': `E_inserimento_griglia`,
`E1_inserimento_griglia`; PEMS08: `E_e6_pems08`, `E1_e6_pems08`; PEMS04: `E1_e6_pems04`) si leggono
**dai pesi**, non dal deliverable:

    d_emb      dimensione dell'embedding      = identita.embedding.shape[1]
    K          nodi iniziali                   = identita.embedding.shape[0] = len(nodi_iniziali)
    token      riga del nodo ignoto            = presenza di identita.ignoto (E′ si', E no)
    c_in       canali dinamici in ingresso     = start.weight.shape[1]
    nascosti   larghezza del backbone          = start.weight.shape[0]
    parametri  numero di parametri             = somma dei numel dello state_dict
    impronta   la stessa di `carica_E` (sha256 di chiavi e pesi, 16 esadecimali)

e dal codice (costanti di `predittore.py`, non nei pesi): finestra di 12 passi, nucleo 2, dilatazioni
(1, 2, 4, 8) → campo ricettivo 16 ≥ 12, orizzonti (1, 2, 4, 8) passi, 3 classi. Si ferma se due
checkpoint della stessa sorgente non concordano. Scrive `results/evoluzione/architettura_ck.json`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/architettura_ck.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))

from evoluzione.componente import predittore as P  # noqa: E402
from evoluzione.componente.adattamento import carica_E  # noqa: E402
from evoluzione.esperimenti.addestramento import sorgente_di  # noqa: E402

CARTELLE = ("E_inserimento_griglia", "E1_inserimento_griglia", "E_e6_pems08", "E1_e6_pems08", "E1_e6_pems04")
D_STAT = 5


def _scheda(f: Path) -> dict:
    d, nodi, imp = carica_E(f, D_STAT)
    sd = d["state_dict"]
    emb = sd["identita.embedding"]
    ctx = str(d.get("contesto", "_".join(f.stem.split("_")[2:-2])))   # ck_<braccio>_<contesto>_p<p>_s<seme>
    return {"file": f.name, "impronta": imp, "contesto": ctx, "sorgente": sorgente_di(ctx),
            "K": int(emb.shape[0]), "nodi_iniziali": len(nodi), "d_emb": int(emb.shape[1]),
            "token": "identita.ignoto" in sd,
            "d_token": (int(sd["identita.ignoto"].numel()) if "identita.ignoto" in sd else None),
            "c_in": int(sd["start.weight"].shape[1]), "nascosti": int(sd["start.weight"].shape[0]),
            "n_blocchi": len({k.split(".")[1] for k in sd if k.startswith("blocchi.")}),
            "uscita": int(sd["e2.weight"].shape[0]),
            "parametri": int(sum(v.numel() for v in sd.values()))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    schede = []
    for cart in CARTELLE:
        for f in sorted((a.out / cart).glob("ck_*.pt")) if (a.out / cart).exists() else []:
            s = _scheda(f); s["cartella"] = cart; schede.append(s)
    if not schede:
        raise SystemExit("nessun checkpoint trovato")
    chiavi = ("d_emb", "c_in", "nascosti", "n_blocchi", "uscita", "token", "sorgente")
    gruppi = {}
    for s in schede:
        gruppi.setdefault((s["cartella"], s["sorgente"]), []).append(s)
    print("=" * 96)
    print("ARCHITETTURA DAI CHECKPOINT DI E ED E′")
    print("=" * 96)
    print(f"  {'cartella':26s} {'sorgente':12s} {'n':>3} {'K':>8} {'d_emb':>5} {'token':>5} {'c_in':>4} "
          f"{'nasc.':>5} {'blocchi':>7} {'uscita':>6} {'parametri':>10}")
    sintesi = {}
    for (cart, sorg), g in gruppi.items():
        for k in chiavi:
            v = {s[k] for s in g}
            if len(v) != 1:
                raise RuntimeError(f"{cart} ({sorg}): {k} discorde fra i checkpoint: {sorted(map(str, v))}")
        for s in g:
            if s["K"] != s["nodi_iniziali"]:
                raise RuntimeError(f"{s['file']}: righe dell'embedding {s['K']} ≠ nodi iniziali {s['nodi_iniziali']}")
            if s["uscita"] != len(P.ORIZZONTI) * P.N_CLASSI:
                raise RuntimeError(f"{s['file']}: uscita {s['uscita']} ≠ {len(P.ORIZZONTI)}×{P.N_CLASSI}")
        Ks = sorted({s["K"] for s in g}); par = sorted({s["parametri"] for s in g})
        s0 = g[0]
        sintesi[cart] = {k: s0[k] for k in chiavi} | {"n": len(g), "K": Ks, "parametri": par,
                                                      "impronte": {s["file"]: s["impronta"] for s in g}}
        print(f"  {cart:26s} {sorg:12s} {len(g):3d} {('/'.join(map(str, Ks))):>8} {s0['d_emb']:5d} "
              f"{str(s0['token']):>5} {s0['c_in']:4d} {s0['nascosti']:5d} {s0['n_blocchi']:7d} {s0['uscita']:6d} "
              f"{('/'.join(map(str, par))):>10}")
    codice = {"finestra_passi": P.FINESTRA, "nucleo": P.NUCLEO, "dilatazioni": list(P.DILATAZIONI),
              "campo_ricettivo": P.campo_ricettivo(), "orizzonti_passi": list(P.ORIZZONTI), "classi": P.N_CLASSI,
              "canali": {"traffic4cast": P.CANALI_T4C, "pems04": P.CANALI_PEMS04}}
    print(f"\n  dal codice (predittore.py): finestra {codice['finestra_passi']} passi, nucleo {codice['nucleo']}, "
          f"dilatazioni {codice['dilatazioni']} → campo ricettivo {codice['campo_ricettivo']} ≥ {codice['finestra_passi']}; "
          f"orizzonti {codice['orizzonti_passi']} passi, {codice['classi']} classi")
    for sorg, can in codice["canali"].items():
        print(f"  canali {sorg} ({len(can)}): {', '.join(can)}")
    doc = {"sintesi": sintesi, "codice": codice, "checkpoint": schede,
           "istante": datetime.now(timezone.utc).isoformat()}
    f = a.out / "architettura_ck.json"
    f.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    print(f"\n  {len(schede)} checkpoint; salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
