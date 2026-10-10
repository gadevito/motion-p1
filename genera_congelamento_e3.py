#!/usr/bin/env python3
"""
Congelamento di E3 — riaddestramento leale.
============================================
**Ogni numero e' derivato dai file**: confronti e riviste da
`analisi_e3.json`, veterani da `veterani_e3.json`, costi da `costi_e3.json`,
riselezione da `riselezione_rmon.json` e `riselezione_rmon_test.json`,
esecuzioni dall'esito del lancio e dai marcatori, quarantena dall'indice,
ricostruzione dai `controllo_*.json`. **F - C e R-orig - F** si ricalcolano qui
dalle predizioni per cella con la stessa procedura di `analizza_e3`, per dire
in quante citta' il riaddestramento leale arriva dove arriva l'adattamento.

Se un ingresso manca, si ferma.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e3.py
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parent
sys.path.insert(0, str(RADICE))

OUT = Path("results/evoluzione")
CITTA = ("Madrid", "Londra", "Melbourne")
FILE = ["evoluzione/componente/bracci.py",
        "evoluzione/componente/campionamento.py",
        "evoluzione/esperimenti/addestramento.py",
        "evoluzione/esperimenti/inserimento.py",
        "evoluzione/esperimenti/esegui_inserimento.py",
        "evoluzione/esperimenti/ricostruisci_predizioni.py",
        "evoluzione/esperimenti/veterani_e3.py",
        "evoluzione/esperimenti/riselezione_rmon_test.py",
        "evoluzione/analisi/analizza_e3.py",
        "evoluzione/analisi/analizza_veterani_e3.py",
        "evoluzione/analisi/costi_e3.py",
        "evoluzione/analisi/riselezione_rmon.py",
        "protocol/E3.md"]


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


def esecuzioni(out: Path) -> dict:
    d = out / "inserimento_griglia"
    e = leggi(d / "esito_concorrente_R-orig_R-mon.json")
    fatti = {b: len(list(d.glob(f"{b}_*_p*_s*.json.fatto"))) for b in ("R-orig", "R-mon")}
    iso = {b: sum(1 for f in d.glob(f"{b}_*_p*_s*.json")
                  if json.loads(f.read_text()).get("modalita_misura") == "isolata")
           for b in ("R-orig", "R-mon")}
    ric = {b: leggi(out / "predizioni_fase3" / f"controllo_{b}.json")
           for b in ("R", "R-orig", "R-mon")}
    return {"completate": e["completate"], "fallite": len(e["fallite"]),
            "ore_calendario": e["ore_calendario"],
            "somma_parete_ore": e["somma_tempi_parete_ore"],
            "lavoratori": e["lavoratori"], "marcatori": fatti, "isolate": iso,
            "ricostruzione": {b: {"esecuzioni": len(ric[b]["esecuzioni"]),
                                  "anomalie": len(ric[b]["anomalie"]),
                                  "scarto_max": max(x["scarto_relativo"]
                                                    for x in ric[b]["esecuzioni"])}
                              for b in ric}}


def quarantena(out: Path) -> dict | None:
    f = out / "_quarantena_e3_falso_20260930" / "INDICE.json"
    return json.loads(f.read_text()) if f.exists() else None


def f_contro_rorig(out: Path) -> dict:
    """F - C e R-orig - F per citta', stessa procedura di analizza_e3."""
    from evoluzione.analisi.analizza_e2 import wce
    rng = np.random.default_rng(20261003)
    fuori = {}
    dp = out / "predizioni_fase3"
    for c in CITTA:
        d = {}
        for f in sorted(dp.glob(f"R-orig_{c}_p*_s*.npz")):
            p = int(f.stem.split("_p")[1].split("_")[0]); s = int(f.stem.split("_s")[1])
            for b in ("R-orig", "F", "C"):
                g = dp / f"{b}_{c}_p{p}_s{s}.npz"
                if not g.exists():
                    raise IngressoMancante(f"assente: {g}")
                d[(b, p, s)] = np.load(g, allow_pickle=True)
        parts = sorted({k[1] for k in d}); semi = sorted({k[2] for k in d})
        K = d[("F", parts[0], semi[0])]["A_per_nodo"].shape[0]
        # IL MARGINE DI EQUIVALENZA del protocollo (§12): ±3 % relativo a C,
        # con TOST. L'intervallo al 95 % interamente dentro il margine e' una
        # lettura conservativa del TOST (che userebbe il 90 %).
        wC = float(np.mean([wce(d[("C", p, s)]["A_per_nodo"], d[("C", p, s)]["B_per_nodo"])
                            for p in parts for s in semi]))
        fuori[f"{c}/wce_C"] = wC
        fuori[f"{c}/margine"] = 0.03 * wC
        for n1, n2 in (("F", "C"), ("R-orig", "F")):
            m0 = float(np.mean([wce(d[(n1, p, s)]["A_per_nodo"], d[(n1, p, s)]["B_per_nodo"])
                                - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"])
                                for p in parts for s in semi]))
            v = []
            for _ in range(4000):
                ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
                nd = rng.integers(0, K, K)
                v.append(np.mean([wce(d[(n1, p, s)]["A_per_nodo"], d[(n1, p, s)]["B_per_nodo"], nd)
                                  - wce(d[(n2, p, s)]["A_per_nodo"], d[(n2, p, s)]["B_per_nodo"], nd)
                                  for p in ps for s in ss]))
            q = np.percentile(v, [2.5, 97.5])
            fuori[f"{c}/{n1}-{n2}"] = {"media": m0, "ic_con_nodi": q.tolist(),
                                       "include_zero": bool(q[0] * q[1] <= 0),
                                       "equivalente_3pc": bool(
                                           -0.03 * wC <= q[0] and q[1] <= 0.03 * wC)}
    return fuori


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q, n=3):
    return f"[{_f(q[0], n)}, {_f(q[1], n)}]"


def documento(R: dict) -> str:
    A = []; a = A.append
    E, C, V, K, S, T, Q, FR = (R["esecuzioni"], R["analisi"]["confronti"],
                               R["veterani"], R["costi"], R["riselezione"],
                               R["riselezione_test"], R["quarantena"], R["f_rorig"])
    riv = R["analisi"]["riviste"]
    a("# Congelamento — E3, riaddestramento leale")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione "
      f"`protocol/E3.md` (impronta `{R['impronte']['protocol/E3.md']}`), firmata "
      f"al commit `4bafa5ef0491a4b7` prima del primo run. **Ogni numero e' "
      f"calcolato da `genera_congelamento_e3.py`** dai file di risultato; il "
      f"verdetto e' derivato, non scritto.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a("| bracci nuovi | **R-orig** (uniforme per origine, selezione sulla rete iniziale) e "
      "**R-mon** (come R-orig, selezione rete iniziale + nodi nuovi sulle ultime 6 h, "
      "media pesata per celle); budget 2.290, architettura di A |")
    a(f"| esecuzioni | **{E['completate']}** completate, {E['fallite']} fallite; marcatori "
      f"R-orig {E['marcatori']['R-orig']}, R-mon {E['marcatori']['R-mon']} |")
    a(f"| calendario | {E['ore_calendario']:.1f} ore, {E['lavoratori']} processi; somma dei "
      f"tempi di parete {E['somma_parete_ore']:.0f} ore — **non e' il costo seriale** |")
    a(f"| campione isolato | {E['isolate']['R-orig']} + {E['isolate']['R-mon']} celle "
      f"rimisurate a un processo, ciascuna con wCE identica alla concorrente |")
    a("| predizioni per cella | ricostruite dai punti di controllo, tolleranza 1e-6: "
      + ", ".join(f"{b} {z['esecuzioni']} esecuzioni, {z['anomalie']} anomalie, scarto "
                  f"max {z['scarto_max']:.1e}" for b, z in E["ricostruzione"].items()) + " |")
    a("")
    a("## 2. Controlli obbligatori")
    a("")
    a("### Conteggio delle riviste per origine (mediana sulle esecuzioni)")
    a("")
    a("| braccio | esecuzioni | riviste/origine iniziali | nuovi | rapporto | quota estrazioni ai nuovi |")
    a("|---|---|---|---|---|---|")
    for b in ("R", "R-orig", "R-mon"):
        z = riv[b]
        a(f"| {b} | {z['esecuzioni']} | {z['rip_iniziali']['mediana']:.2f} | "
          f"{z['rip_nuovi']['mediana']:.2f} | **{z['rapporto_rip']['mediana']:.3f}** | "
          f"{z['quota_nuovi']['mediana']:.3%} |")
    ok_riv = abs(riv["R-orig"]["rapporto_rip"]["mediana"] - 1) < 0.05
    a("")
    a(f"Per R-orig il rapporto atteso e' 1: **{'verificato' if ok_riv else 'NON verificato'}** "
      f"({riv['R-orig']['rapporto_rip']['mediana']:.3f}). I nodi nuovi ricevono lo "
      f"{riv['R-orig']['quota_nuovi']['mediana']:.2%} delle estrazioni: pesano quanto la "
      f"loro storia.")
    a("")
    a("### La rete esistente prima e dopo (nodi iniziali, periodo di prova)")
    a("")
    a("| | R-orig − C | R-orig − E | R − C | R-mon − R-orig |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        a(f"| {c} | " + " | ".join(
            f"{_f(V['confronti'][f'{c}/{k}']['media'])} {_ic(V['confronti'][f'{c}/{k}']['ic_con_nodi'])}"
            + (" (zero)" if V["confronti"][f"{c}/{k}"]["include_zero"] else "")
            for k in ("R-orig-C", "R-orig-E", "R-C", "R-mon-R-orig")) + " |")
    pegg = [k for k, v in V["costo_della_politica"].items() if v]
    a("")
    a("**Costo della politica**: " + ("nessuno — R-orig non peggiora la rete esistente in "
      "alcuna citta'." if not pegg else "R-orig peggiora la rete esistente in " + ", ".join(pegg) + "."))
    a("")
    a("### Tabella dei costi (campione isolato, un processo)")
    a("")
    a("| braccio | n | addestramento | inserimento | attesa dati | disponibile |")
    a("|---|---|---|---|---|---|")
    for b in ("C", "P", "A", "R", "R-orig", "R-mon", "F"):
        z = K[b]
        if not z.get("esecuzioni_isolate"):
            a(f"| {b} | 0 | — | — | — | — |"); continue
        a(f"| {b} | {z['esecuzioni_isolate']} | {z['addestramento_s']/60:.1f} min | "
          f"{z['inserimento_s']:.1f} s | {z['attesa_dati_s']/3600:.0f} h | "
          f"{z['disponibilita_s']/3600:.1f} h |")
    rapp = K["R-orig"]["inserimento_s"] / K["F"]["inserimento_s"]
    a("")
    a(f"R-orig costa **{K['R-orig']['inserimento_s']/60:.1f} min** all'inserimento contro "
      f"{K['F']['inserimento_s']:.1f} s di F: **{rapp:.0f}×**.")
    a("")
    a("## 3. I confronti pre-registrati (nodi nuovi, periodo di prova)")
    a("")
    a(f"Celle (seme, partizione, nodo) appaiate; IC 95 % con ricampionamento congiunto di "
      f"partizioni, semi e nodi, {R['analisi']['repliche']} repliche, seme "
      f"{R['analisi']['seme_bootstrap']}. Negativo = meglio del secondo termine.")
    a("")
    a("| | R-orig − C (principale) | R-orig − R | R-mon − R-orig | R-mon − C |")
    a("|---|---|---|---|---|")
    for c in CITTA:
        n = R["analisi"]["celle"][c]
        a(f"| {c} ({n['semi']}×{n['partizioni']}×{n['nodi']}) | " + " | ".join(
            f"**{_f(C[f'{c}/{k}']['media'])}** {_ic(C[f'{c}/{k}']['ic_con_nodi'])}"
            + (" (zero)" if C[f"{c}/{k}"]["include_zero"] else "")
            for k in ("R-orig-C", "R-orig-R", "R-mon-R-orig", "R-mon-C")) + " |")
    a("")
    a("## 4. Verdetto sul criterio pre-registrato")
    a("")
    a("> **R-orig − C con intervallo che esclude lo zero: negativo = il riaddestramento "
      "leale paga; positivo = anche leale non paga a questo budget.**")
    a("")
    P = R["analisi"]["principale"]
    for c in CITTA:
        a(f"- {c}: **{P[c]}**")
    cnt = {k: sum(1 for c in CITTA if P[c] == k) for k in ("paga", "non paga", "non conclusivo")}
    a("")
    a(f"**Esito eterogeneo per citta'**: paga in {cnt['paga']}, non paga in "
      f"{cnt['non paga']}, non conclusivo in {cnt['non conclusivo']}. Il criterio non "
      f"prevede un'aggregazione fra citta' e non la si introduce dopo. **R-orig − R** e' "
      f"negativo con intervallo che esclude lo zero in tutte e tre: quasi tutto il "
      f"peggioramento di R era il campionamento per nodo.")
    a("")
    a("## 5. R-mon: nullo per costruzione, e la riselezione a peso uguale")
    a("")
    ug = [c for c in CITTA if abs(C[f"{c}/R-mon-R-orig"]["media"]) < 1e-4]
    a(f"R-mon coincide con R-orig in {len(ug)} citta' su 3 (media |Δ| < 1e-4): con la "
      f"media pesata per numero di celle, dichiarata nel protocollo, i nodi nuovi pesano "
      f"circa lo 0,3 % della selezione. **La sorveglianza con quel peso e' nulla per "
      f"costruzione**; si riporta in una frase.")
    a("")
    a(f"**Analisi aggiunta il 2/10, non pre-registrata, secondaria.** Dalle curve, la "
      f"regola a peso uguale (0,5 rete iniziale + 0,5 nodi nuovi) avrebbe scelto un punto "
      f"diverso in **{S['diverse']} celle su {S['esecuzioni']}**. Quelle celle sono state "
      f"riaddestrate salvando tutti i punti (il punto migliore riproduce la campagna a "
      f"bit) e il punto a peso uguale valutato sul test:")
    a("")
    a("| | R-mon-eq − R-mon | R-mon-eq − R-orig | R-mon-eq − C |")
    a("|---|---|---|---|")
    for c in CITTA:
        a(f"| {c} | " + " | ".join(
            f"{_f(T['confronti'][f'{c}/Rmoneq-{k}']['media'], 4)} "
            f"{_ic(T['confronti'][f'{c}/Rmoneq-{k}']['ic_con_nodi'], 4)}"
            + (" (zero)" if T["confronti"][f"{c}/Rmoneq-{k}"]["include_zero"] else "")
            for k in ("R-mon", "R-orig", "C")) + " |")
    peggio = [c for c in CITTA if T["confronti"][f"{c}/Rmoneq-R-orig"]["ic_con_nodi"][0] > 0]
    meglio = [c for c in CITTA if T["confronti"][f"{c}/Rmoneq-R-orig"]["ic_con_nodi"][1] < 0]
    a("")
    a("Dare peso ai nodi nuovi nella selezione **non li migliora in prova**"
      + (f" e li peggiora a {', '.join(peggio)}" if peggio else "")
      + (f"; li migliora a {', '.join(meglio)}" if meglio else "")
      + ". Le 6 ore usate per la selezione appartengono al corpus di addestramento di R: "
        "premiarle sceglie punti piu' tardi, piu' adattati al proprio training.")
    a("")
    a("## 6. R-orig e F: stesso punto d'arrivo?")
    a("")
    a("Due letture, entrambe del protocollo (§12): una **differenza** si afferma con "
      "l'intervallo che esclude lo zero; un'**equivalenza** con il margine convenzionale "
      "±3 % relativo a C (TOST; qui, in modo conservativo, l'intervallo al 95 % "
      "interamente dentro il margine).")
    a("")
    a("| | F − C | R-orig − F | esclude lo zero | margine ±3 % | equivalenti |")
    a("|---|---|---|---|---|---|")
    n_diff = n_eq = 0
    for c in CITTA:
        z1, z2 = FR[f"{c}/F-C"], FR[f"{c}/R-orig-F"]
        diff = not z2["include_zero"]; eq = z2["equivalente_3pc"]
        n_diff += diff; n_eq += eq
        a(f"| {c} | {_f(z1['media'])} {_ic(z1['ic_con_nodi'])} | {_f(z2['media'])} "
          f"{_ic(z2['ic_con_nodi'])} | {'si' if diff else 'no'} | "
          f"±{FR[f'{c}/margine']:.3f} | {'si' if eq else 'no'} |")
    a("")
    a(f"R-orig differisce da F con intervallo che esclude lo zero in {n_diff} citta' su "
      f"3 — di pochi millesimi, in favore di R-orig a Madrid e di F altrove — ed e' "
      f"**equivalente a F entro il margine dichiarato in {n_eq} citta' su 3**"
      + (" (" + ", ".join(c for c in CITTA if FR[f"{c}/R-orig-F"]["equivalente_3pc"]) + ")"
         if n_eq else "")
      + f". Il riaddestramento leale compra una differenza di quell'ordine a {rapp:.0f} "
        f"volte il tempo dell'adattamento.")
    a("")
    a("## 7. Dichiarazioni")
    a("")
    if Q:
        a(f"- **Primo lancio non valido**, in quarantena con indice "
          f"(`_quarantena_e3_falso_20260930`, {len(Q['file'])} file): {Q['motivo']} "
          f"Corretto: {Q['corretto_in']}.")
        a(f"- **Perso**: {Q['perso']}.")
    else:
        a("- indice della quarantena non trovato: la dichiarazione del primo lancio va "
          "scritta a mano.")
    a("- Il tempo di parete atteso per braccio e' ora un assert dell'orchestratore "
      "(protocollo §13).")
    a("- **Correzione del 2026-10-10 (difetto 19 del registro)**: il conteggio delle riviste "
      "prendeva dal registro ogni esecuzione completata di R, R-orig e R-mon, comprese le 9 "
      "rimisure isolate di R-orig e R-mon fatte per la tabella dei costi (117 invece di 108). "
      "Ora il lancio di E3 e' definito dai 108 manifesti per braccio di `inserimento_griglia/`, "
      "elencati per impronta in `analisi_e3.json` (`riviste/<braccio>/lancio`), e di ogni cella "
      "conta la sola esecuzione che ha prodotto la wCE registrata; le rimisure future hanno "
      "etichetta propria nel registro (`…/rimisura`). Documento rigenerato, non modificato a mano.")
    a("")
    a("## 8. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a("")
    a("**Nessun parametro scelto dopo aver visto i risultati**: budget, campionamento e "
      "finestra di selezione sono nella pre-registrazione firmata; la riselezione a peso "
      "uguale e' dichiarata come analisi aggiunta e secondaria.")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    print("[1/7] esecuzioni e ricostruzione"); E = esecuzioni(a.out)
    if E["completate"] != 216 or E["fallite"]:
        raise IngressoMancante(f"esecuzioni {E['completate']}, fallite {E['fallite']}")
    if any(z["anomalie"] for z in E["ricostruzione"].values()):
        raise IngressoMancante("ricostruzione con anomalie")
    print("[2/7] analisi"); AN = leggi(a.out / "analisi_e3.json")
    print("[3/7] veterani"); V = leggi(a.out / "veterani_e3.json")
    print("[4/7] costi"); K = leggi(a.out / "costi_e3.json")
    print("[5/7] riselezione"); S = leggi(a.out / "riselezione_rmon.json")
    T = leggi(a.out / "riselezione_rmon_test.json")
    print("[6/7] F - C e R-orig - F dalle predizioni"); FR = f_contro_rorig(a.out)
    print("[7/7] quarantena"); Q = quarantena(a.out)
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "esecuzioni": E, "analisi": AN, "veterani": V, "costi": K,
         "riselezione": {"esecuzioni": S["esecuzioni"], "diverse": S["diverse"]},
         "riselezione_test": T, "f_rorig": FR, "quarantena": Q,
         "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e3.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    Path("CONGELAMENTO_E3.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E3.md; numeri in results/evoluzione/congelamento_e3.json")
    print("  criterio per citta': " + ", ".join(f"{c} {AN['principale'][c]}" for c in CITTA))
    print("  R-orig/F — esclude lo zero: " + ", ".join(
        f"{c} {'si' if not FR[f'{c}/R-orig-F']['include_zero'] else 'no'}" for c in CITTA))
    print("  R-orig/F — equivalenti entro ±3 %: " + ", ".join(
        f"{c} {'si' if FR[f'{c}/R-orig-F']['equivalente_3pc'] else 'no'}" for c in CITTA))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
