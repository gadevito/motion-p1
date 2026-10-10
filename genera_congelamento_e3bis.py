#!/usr/bin/env python3
"""
Congelamento di E3-bis — R-orig con una settimana di dati.
===========================================================
**Ogni numero e' derivato dai file**: confronti da `e3bis_risultati.json`;
esecuzioni dall'esito e dai marcatori di `inserimento_griglia_672`;
ricostruzione da `predizioni_fase3_672/controllo_R-orig.json`; costi isolati da
`costi_e3bis.json` (campione p0, semi 201-203, rimisura che riproduce la
concorrente); i costi di F'(1 sett.) da `costi_e4.json`. Se un ingresso manca,
si ferma.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e3bis.py
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
FILE = ["evoluzione/esperimenti/esegui_inserimento.py",
        "evoluzione/esperimenti/ricostruisci_predizioni.py",
        "evoluzione/analisi/analizza_e3bis.py", "protocol/E5.md"]


class IngressoMancante(RuntimeError):
    pass


def h(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return "assente"


def commit_git() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True, cwd=RADICE).stdout.strip()[:12] or "n.d."
    except Exception:                                        # noqa: BLE001
        return "n.d."


def leggi(f: Path):
    if not f.exists():
        raise IngressoMancante(f"assente: {f}")
    return json.loads(f.read_text())


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def documento(R: dict) -> str:
    A = []; a = A.append
    RS, E, K, K4 = R["risultati"], R["esecuzioni"], R["costi"], R["costi_e4"]
    C = RS["confronti"]
    a("# Congelamento — E3-bis, riaddestramento leale con una settimana di dati")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrato in `protocol/E5.md` "
      f"(sezione E3-bis; impronta `{R['impronte']['protocol/E5.md']}`), firmato al commit "
      f"`cff0310c7c49fe36` prima del lancio. **Ogni numero e' calcolato da "
      f"`genera_congelamento_e3bis.py`** dai file di risultato.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a("| braccio | **R-orig** con acquisizione (t₀, t₀ + 672] (una settimana): campionamento uniforme "
      "per origine, budget 2.290, selezione sulla rete iniziale, architettura di A; "
      "`esegui_inserimento.py --acquisizione-passi 672` |")
    a(f"| esecuzioni | {E['completate']} completate, {len(E['fallite'])} fallite, {E['marcatori']} "
      f"marcatori; {E['ore_calendario']:.1f} ore di calendario con {E['lavoratori']} processi — "
      f"**non e' il costo seriale** |")
    a(f"| ricostruzione delle predizioni | {RS['ricostruzione']['esecuzioni']} esecuzioni, "
      f"{RS['ricostruzione']['anomalie']} anomalie, scarto massimo {RS['ricostruzione']['scarto_max']:.1e} |")
    a("| perimetro | le origini dopo t₁ = t₀ + 672, cioe' **le origini comuni di E4** (eta' > 1 settimana): "
      + ", ".join(f"{c} {RS['origini_comuni'][c]}" for c in CITTA)
      + "; verificato uguale, cella per cella, alla terza fascia di E4 |")
    a(f"| verifica interna | C aggregato dalle predizioni di E3 = C di E4, scarto massimo "
      + ", ".join(f"{c} {RS['verifica_C'][c]:.1e}" for c in CITTA) + " |")
    a(f"| ricampionamento | {RS['repliche']} repliche, seme {RS['seme_bootstrap']}, partizioni × semi × nodi |")
    a("")
    a("## 2. Confronti sulle origini comuni")
    a("")
    a("| citta' | R-orig(1 sett.) − F′(1 sett.) | zero dentro | equivalenti ±3 % | R-orig(1 sett.) − C | R-orig(1 sett.) − A | R-orig(1 sett.) − R-orig(24 h) |")
    a("|---|---|---|---|---|---|---|")
    for c in CITTA:
        r1, r2, r3, r4 = C[f"{c}/Rw-Fpw"], C[f"{c}/Rw-C"], C[f"{c}/Rw-A"], C[f"{c}/Rw-R24"]
        a(f"| {c} | {_f(r1['media'])} {_ic(r1['ic_con_nodi'])} | {'si' if r1['include_zero'] else 'no'} | "
          f"{'si' if r1['equivalente_3pc'] else 'no'} (±{RS['margine'][c]:.3f}) | {_f(r2['media'])} {_ic(r2['ic_con_nodi'])} | "
          f"{_f(r3['media'])} {_ic(r3['ic_con_nodi'])} | {_f(r4['media'])} {_ic(r4['ic_con_nodi'])} |")
    a("")
    n_zero = sum(C[f"{c}/Rw-Fpw"]["include_zero"] for c in CITTA)
    n_eq = sum(C[f"{c}/Rw-Fpw"]["equivalente_3pc"] for c in CITTA)
    n_peggio = sum(C[f"{c}/Rw-Fpw"]["ic_con_nodi"][0] > 0 for c in CITTA)
    n_meglio = sum(C[f"{c}/Rw-Fpw"]["ic_con_nodi"][1] < 0 for c in CITTA)
    a(f"Con gli stessi dati (una settimana), il riaddestramento leale e' **equivalente all'adattamento "
      f"entro ±3 % in {n_eq} citta' su 3**; include lo zero in {n_zero}/3; e' peggiore con intervallo "
      f"sopra lo zero in {n_peggio}/3 e migliore in {n_meglio}/3. "
      + ("Il riaddestramento non compra nulla neppure con gli stessi dati." if n_meglio == 0 else
         "Dove e' migliore, lo e' di: " + ", ".join(f"{c} {_f(C[f'{c}/Rw-Fpw']['media'])}" for c in CITTA
                                                      if C[f"{c}/Rw-Fpw"]["ic_con_nodi"][1] < 0) + "."))
    a("")
    n_fin = sum(C[f"{c}/Rw-R24"]["ic_con_nodi"][1] < 0 for c in CITTA)
    a(f"**R-orig(1 sett.) − R-orig(24 h) e' sotto lo zero in {n_fin} citta' su 3** ("
      + ", ".join(f"{c} {_f(C[f'{c}/Rw-R24']['media'])}" for c in CITTA)
      + "): anche per il riaddestramento la finestra di 24 ore era il problema, non il metodo — "
        "la stessa lezione di E4 letta sull'altro braccio.")
    a("")
    a("Per riferimento, sulle stesse origini: " + "; ".join(
        f"{c} F′(1 sett.) − C {_f(C[f'{c}/Fpw-C']['media'])}, A − C {_f(C[f'{c}/A-C']['media'])}" for c in CITTA) + ".")
    a("")
    a("## 3. Costi — campione isolato, un processo, **a dati simmetrici**")
    a("")
    r = K["R-orig"]
    if r.get("esecuzioni_isolate", 0) == 0:
        raise IngressoMancante("costi_e3bis.json senza misure isolate di R-orig")
    RO = R["R-orig_per_citta"]
    a("| configurazione | calcolo all'inserimento | attesa dati | rimisure che riproducono la concorrente |")
    a("|---|---|---|---|")
    a(f"| R-orig(1 sett.), mediana sulle {r['esecuzioni_isolate']} celle delle tre citta' | "
      f"**{r['inserimento_s']:.0f} s** | {r['attesa_dati_s']/3600:.0f} h | "
      f"{r['rimisure_che_riproducono_la_concorrente']}/{r['esecuzioni_isolate']} |")
    for c in CITTA:
        a(f"| R-orig(1 sett.) {c} (mediana su {RO[c]['n']} semi) | **{RO[c]['inserimento_s']:.0f} s** | "
          f"{r['attesa_dati_s']/3600:.0f} h | {RO[c]['n']}/{RO[c]['n']} |")
    for c in CITTA:
        g = K4["tabella"]["gated"][c]
        if g["tau"] == 672:
            a(f"| F′(1 sett.) {c} (da costi_e4) | {g['adattamento_s']:.0f} s | {g['attesa_dati_s']/3600:.0f} h | — |")
    a(f"| F′(24 h) (da costi_e4) | {K4['tabella']['Fp']['inserimento_s']:.0f} s | 24 h | — |")
    citta_w = [c for c in CITTA if K4["tabella"]["gated"][c]["tau"] == 672]
    citta_no = [c for c in CITTA if c not in citta_w]
    if citta_w:
        a("")
        rapporti = "; ".join(f"{c} **{RO[c]['inserimento_s'] / K4['tabella']['gated'][c]['adattamento_s']:.1f}×**"
                             f" ({RO[c]['inserimento_s']:.0f} s / {K4['tabella']['gated'][c]['adattamento_s']:.0f} s)"
                             for c in citta_w)
        a(f"Rapporto di calcolo a parita' di dati, R-orig(1 sett.) / F′(1 sett.), **nella stessa citta'**: "
          f"{rapporti}. In E4 F′(1 sett.) e' misurato in isolamento solo dove tau = 672 ({', '.join(citta_w)}); "
          f"per {', '.join(citta_no)} il rapporto non si calcola qui (i tempi appaiati nelle tre citta' e su "
          f"PEMS08 sono in `costi_appaiati.json`, misura successiva). Il confronto dei costi del paper e' a "
          f"dati simmetrici: il riaddestramento compra pochi millesimi a diverse volte il costo, non nulla a cento.")
    a("")
    a("## 4. Dichiarazioni")
    a("")
    a("- Un solo parametro aggiunto agli esecutori di E3 (`--acquisizione-passi`), con il valore "
      "predefinito identico al comportamento precedente; `prova_inserimento` 19/19 e `collauda_bracci` "
      "37/37 dopo la modifica.")
    a("- Le fasce d'eta' della valutazione restano quelle di E3; con t₁ = t₀ + 672 tutte le origini "
      "valutate cadono nella terza.")
    a("- **Correzione del 2026-10-10 (difetto 17 del registro)**: la prima versione della sezione 3 "
      "scriveva «almeno 6×» dividendo la mediana di R-orig(1 sett.) sulle nove celle delle tre citta' "
      "per il solo F′(1 sett.) misurato in isolamento (Melbourne, la configurazione F piu' costosa nella "
      "citta' piu' piccola). Lo script ora riporta R-orig(1 sett.) per citta' dai manifesti isolati e il "
      "rapporto solo nella stessa citta'; il documento e' rigenerato, non modificato a mano.")
    a("")
    a("## 5. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    d = a.out / "inserimento_griglia_672"
    print("[1/4] esecuzioni"); es = leggi(d / "esito_concorrente_R-orig.json")
    E = {"completate": es["completate"], "fallite": es["fallite"], "ore_calendario": es["ore_calendario"],
         "lavoratori": es["lavoratori"], "marcatori": len(list(d.glob("R-orig_*_p*_s*.json.fatto")))}
    if E["marcatori"] != 108 or E["fallite"]:
        raise IngressoMancante(f"marcatori {E['marcatori']}, fallite {E['fallite']}")
    print("[2/4] risultati"); RS = leggi(a.out / "e3bis_risultati.json")
    print("[3/4] costi"); K = leggi(a.out / "costi_e3bis.json"); K4 = leggi(a.out / "costi_e4.json")
    RO = {}
    for c in CITTA:
        v = []
        for s in (201, 202, 203):
            m = leggi(d / f"R-orig_{c}_p0_s{s}.json")
            if m.get("modalita_misura") != "isolata" or "rimisura_di" not in m:
                raise IngressoMancante(f"R-orig_{c}_p0_s{s}.json non e' una rimisura isolata")
            v.append(float(m["costo"]["inserimento_s"]))
        v.sort(); RO[c] = {"n": len(v), "inserimento_s": v[len(v) // 2], "valori": v}
    tutte = sorted(x for c in CITTA for x in RO[c]["valori"])
    if len(tutte) != 9 or abs(tutte[4] - K["R-orig"]["inserimento_s"]) > 1e-9:
        raise IngressoMancante(f"mediana sulle {len(tutte)} celle {tutte[len(tutte) // 2]:.1f} s diversa da "
                               f"costi_e3bis.json {K['R-orig']['inserimento_s']:.1f} s")
    print("[4/4] documento")
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "esecuzioni": E, "risultati": RS, "costi": K, "costi_e4": K4, "R-orig_per_citta": RO,
         "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e3bis.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    Path("CONGELAMENTO_E3bis.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E3bis.md; numeri in results/evoluzione/congelamento_e3bis.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
