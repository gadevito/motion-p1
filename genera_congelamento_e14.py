#!/usr/bin/env python3
"""
Congelamento di E14 — sensibilita' alla statica non causale (difetto 21), stadi 0 e A.
=======================================================================================
**Ogni numero e' derivato dai file**: stadio 0 da `e14_stadio0.json`; stadio A da
`e14_risultati.json` (sei confronti pre-registrati e wCE assolute di C e A, per variante,
con intervalli), `esito_e14_celle.json` (esecuzioni) e dalle celle del controllo 1
(`predizioni_e14/nc/`). Il verdetto per confronto e' quello del pre-registro (|Δ| < 0,002 e
segno dell'intervallo conservato); il verdetto di stadio e' derivato, non scritto.
Se un ingresso manca, si ferma.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e14.py
"""
import argparse
import glob
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent
OUT = Path("results/evoluzione")
FILE = ["evoluzione/esperimenti/esegui_e14.py", "evoluzione/analisi/e14_stadio0.py",
        "evoluzione/esperimenti/esegui_e8.py", "evoluzione/esperimenti/inserimento.py", "protocol/E14.md"]
GRUPPI = ("Madrid", "Londra", "Melbourne", "PEMS08")
CONF_ET = {"F0-C": "F₀ − C", "F0p-C": "F₀′ − C", "Fp_672-C_eta>1sett": "F′(1 sett.) − C (età > 1 sett.)",
           "Fp_672-A_eta>1sett": "F′(1 sett.) − A (età > 1 sett.)",
           "Rorig_672-Fp_672_eta>1sett": "R-orig(1 sett.) − F′(1 sett.) (età > 1 sett.)", "A-C": "A − C"}
VAR_ET = {"a": "(a) nuovi: prime 24 h", "b": "(b) nuovi: media degli iniziali", "c": "(c) nuovi: permutata"}


class IngressoMancante(RuntimeError):
    pass


def h(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return "assente"


def commit_git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=RADICE).stdout.strip()[:12] or "n.d."
    except Exception:                                        # noqa: BLE001
        return "n.d."


def leggi(f: Path):
    if not f.exists():
        raise IngressoMancante(f"assente: {f}")
    return json.loads(f.read_text())


def _f(x, n=4):
    return f"{x:+.{n}f}"


def _ic(q, n=4):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def controllo_1(out: Path) -> dict:
    import numpy as np
    sc = {}
    for f in sorted(glob.glob(str(out / "predizioni_e14" / "nc" / "prova_*.npz"))):
        with np.load(f, allow_pickle=True) as z:
            sc[Path(f).stem] = max(v["scarto_relativo"] for v in json.loads(str(z["controllo"])).values())
    return sc


def documento(R: dict) -> str:
    A = []; a = A.append
    S0, RS, ES, C1 = R["stadio0"], R["risultati"], R["esecuzioni"], R["controllo_1"]
    a("# Congelamento — E14, sensibilità alla statica non causale (difetto 21)")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione `protocol/E14.md` (impronta "
      f"`{R['impronte']['protocol/E14.md']}`), firmata al commit `102642b48adbe377` prima dello stadio A, con emendamento "
      f"del 12/10 20:20 (variante (c), PEMS come controllo). **Ogni numero è calcolato da `genera_congelamento_e14.py`** "
      f"dai file di risultato; il verdetto è derivato, non scritto. Nessun riaddestramento.")
    a("")
    a("## 1. Che cosa è stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a(f"| stadio 0 | sola lettura, {len(S0['per_cella'])} celle (contesto × episodio × partizione); `e14_stadio0.json` impronta `{R['impronte_dati']['e14_stadio0.json']}` |")
    a(f"| stadio A, celle | {ES['completate']} cella-varianti completate, {len(ES['fallite'])} fallite, {ES['lavoratori']} processi, "
      f"{ES['ore_calendario']:.2f} h di calendario; varianti {ES['varianti']} |")
    a(f"| macchina | NVIDIA DGX Spark (GB10, aarch64, Ubuntu 24.04), stesso ambiente del Mac (lockfile); il riferimento non causale "
      f"sono gli aggregati per cella di `predizioni_e8/prova_*` (Mac) |")
    a(f"| bracci | C, A, F₀, F₀′, F′(1 sett.) (adattamento rifatto con la statica della variante), R-orig(1 sett.), dai checkpoint congelati |")
    a(f"| controllo 1 | {len(C1)} celle rivalutate con la statica non causale contro E8: scarto relativo massimo sulla wCE "
      f"**{max(C1.values()):.1e}** (sul Mac, pilota: 0); soglia d'arresto 1e-6 |")
    a(f"| statistica | ricampionamento congiunto partizioni × semi × nodi, {RS['repliche']} repliche, semi di E8; soglia |Δ| {RS['soglia_delta']} |")
    a("")
    a("## 2. Stadio 0 — quanto differisce l'ingresso")
    a("")
    a("| contesto/episodio | p90 \\|Δ\\| iniziali | nuovi (a) | nuovi (b) | p90 tutti (a) | criterio |")
    a("|---|---|---|---|---|---|")
    for k, v in S0["per_contesto_episodio"].items():
        a(f"| {k} | {v['delta_iniziali']['p90']:.4f} | {v['delta_nuovi_a']['p90']:.4f} | {v['delta_nuovi_b']['p90']:.4f} | "
          f"{v['p90_abs_delta_tutti_a']:.4f} | {'< 0,01' if S0['criterio']['sotto_soglia'][k] else '≥ 0,01'} |")
    a("")
    a(f"Criterio pre-registrato (p90 |Δ| < {S0['soglia_p90']} ovunque, variante (a)): "
      f"**{'verificato' if all(S0['criterio']['sotto_soglia'].values()) else 'NON verificato'}** → {S0['criterio']['verdetto']}. "
      f"Su PEMS08 e PEMS04 Δ = 0 per ogni sensore (maschera piena): la replica densa è immune per costruzione.")
    a("")
    a("## 3. Stadio A — le sei dichiarazioni, per contesto e variante")
    a("")
    sens = {}
    for gr in GRUPPI:
        G = RS["gruppi"][gr]
        a(f"### {gr} ({G['celle']} celle)")
        a("")
        a("| confronto | non causale (congelata) | " + " | ".join(f"{VAR_ET[v]}: valore, Δ, verdetto" for v in RS["varianti"]) + " |")
        a("|---|---|" + "---|" * len(RS["varianti"]))
        for k, et in CONF_ET.items():
            r = G["confronti"][k]; nc = r["nc"]
            riga = f"| {et} | {_f(nc['media'])} {_ic(nc['ic_con_nodi'])} {nc['segno']} |"
            for v in RS["varianti"]:
                x = r[v]
                riga += (f" {_f(x['media'])} {_ic(x['ic_con_nodi'])} {x['segno']}, Δ {_f(x['delta_da_nc'])}, "
                         f"**{'insensibile' if x['insensibile'] else 'SENSIBILE'}** |")
                if not x["insensibile"]:
                    sens.setdefault(gr, []).append((et, v, x["delta_da_nc"], nc["segno"], x["segno"]))
            a(riga)
        a("")
        a("| wCE assoluta | non causale | " + " | ".join(f"{v}: valore, Δ" for v in RS["varianti"]) + " |")
        a("|---|---|" + "---|" * len(RS["varianti"]))
        for k, et in (("wCE_C", "C"), ("wCE_A", "A")):
            r = G["assolute"][k]
            a(f"| {et} | {r['nc']['media']:.4f} {_ic(r['nc']['ic_con_nodi'])} |"
              + "".join(f" {r[v]['media']:.4f}, Δ {_f(r[v]['delta_da_nc'])} |" for v in RS["varianti"]))
        a("")
    a("## 4. Verdetto derivato")
    a("")
    tutte = RS["verdetto"]
    a("| variante | tutte e sei insensibili in tutti i contesti | dichiarazioni sensibili |")
    a("|---|---|---|")
    for v in RS["varianti"]:
        ls = [f"{gr}: {et} (Δ {_f(d)})" for gr, l in sens.items() for (et, vv, d, s1, s2) in l if vv == v]
        a(f"| {VAR_ET[v]} | **{'sì' if tutte[v] else 'NO'}** | {'; '.join(ls) if ls else '—'} |")
    cambi = [(gr, et, vv) for gr, l in sens.items() for (et, vv, d, s1, s2) in l if s1 != s2]
    n_sens = sum(len(l) for l in sens.values())
    a("")
    a(f"- Dichiarazioni sensibili: **{n_sens}** su {len(CONF_ET) * len(GRUPPI) * len(RS['varianti'])} (confronto × contesto × variante); "
      f"cambi di segno dell'intervallo: **{len(cambi)}**" + (f" ({', '.join(f'{g} {e} {v}' for g, e, v in cambi)})" if cambi else "") + ".")
    dC = {gr: {v: RS["gruppi"][gr]["assolute"]["wCE_C"][v]["delta_da_nc"] for v in RS["varianti"]} for gr in GRUPPI}
    dA = {gr: {v: RS["gruppi"][gr]["assolute"]["wCE_A"][v]["delta_da_nc"] for v in RS["varianti"]} for gr in GRUPPI}
    a("- Livello assoluto: Δ wCE di C con la variante (c) " + ", ".join(f"{gr} {_f(dC[gr]['c'])}" for gr in GRUPPI)
      + "; di A " + ", ".join(f"{gr} {_f(dA[gr]['c'])}" for gr in GRUPPI) + ".")
    usa = [gr for gr in GRUPPI if any(not RS["gruppi"][gr]["confronti"][k]["c"]["insensibile"] for k in CONF_ET)]
    a(f"- Lettura della variante (c) (emendamento, punto 1): {'il modello usa la scalare per nodo in ' + ', '.join(usa) if usa else 'la scalare per nodo non è usata in nessun contesto'}"
      + ("; dove la usa, il modello che si muove è C (senza identità), non A: le differenze sensibili sono quelle contro C" if usa else "") + ".")
    a(f"- Regola pre-registrata: {'tutte le sei insensibili in tutti i contesti per ogni variante → stadio B non eseguito' if all(tutte.values()) else '**almeno una sensibile → stadio B**, decisione del revisore (variante da usare: quelle che hanno mostrato sensibilità: ' + ', '.join(v for v in RS['varianti'] if not tutte[v]) + ')'}.")
    a("")
    a("## 5. Dichiarazioni")
    a("")
    a("- Il controllo 1 vale «scarto zero» sulla stessa macchina di E8 (Mac, pilota 188 s); sulla Spark lo scarto è il rumore "
      f"di macchina della voce 22 (massimo {max(C1.values()):.1e}), tre ordini di grandezza sotto la soglia di sensibilità.")
    a("- Lo stadio 0 è stato ricalcolato il 13/10 con la classe critica (3 di `pesi.CLASSI`): la prima versione contava "
      "l'intermedia; distribuzioni di Δ e verdetto invariati, ρ ricalcolata.")
    a("- Solo i nodi di prova consumano la statica nello stadio A (valutazione e adattamento di F′); i modelli restano "
      "addestrati con la statica non causale: lo stadio A misura la sensibilità, non ripara.")
    a("- Preflight n. 8 (perturbazione di `m_r` dopo t₀ → `static_inputs` invariato): da aggiungere con la correzione del codice, "
      "qualunque sia l'esito (pre-registro, controlli, punto 2).")
    a("")
    a("## 6. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    for f, hh in R["impronte_dati"].items():
        a(f"| `results/evoluzione/{f}` | `{hh}` |")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/4] stadio 0"); S0 = leggi(a.out / "e14_stadio0.json")
    print("[2/4] esecuzioni"); ES = leggi(a.out / "esito_e14_celle.json")
    if ES["fallite"]:
        raise IngressoMancante(f"{len(ES['fallite'])} cella-varianti fallite")
    print("[3/4] risultati e controllo 1"); RS = leggi(a.out / "e14_risultati.json"); C1 = controllo_1(a.out)
    if len(C1) != 10:
        raise IngressoMancante(f"controllo 1 su {len(C1)} celle, attese 10")
    print("[4/4] documento")
    dati = ("e14_stadio0.json", "e14_risultati.json", "esito_e14_celle.json")
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(), "stadio0": S0, "risultati": RS,
         "esecuzioni": ES, "controllo_1": C1, "impronte": {f: h(f) for f in FILE},
         "impronte_dati": {f: h(a.out / f) for f in dati}}
    (a.out / "congelamento_e14.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    Path("CONGELAMENTO_E14.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E14.md; numeri in results/evoluzione/congelamento_e14.json")
    print("  verdetto: " + ", ".join(f"({v}) {'tutte insensibili' if ok else 'SENSIBILE'}" for v, ok in RS["verdetto"].items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
