#!/usr/bin/env python3
"""
Congelamento di E7 — copertura e adattamento, stadio 1.
========================================================
**Ogni numero e' derivato da `e7_stadio1.json`** (gruppi, correlazioni,
ipotesi, decisione); N da `e4_scelta_gated.json`, k da `e5_k_secondaria.json`.
La decisione sullo stadio 2a e' quella calcolata dallo script con la regola
pre-registrata, non scritta qui.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e7.py
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
EPISODI = (1, 2, 3)
FILE = ["evoluzione/analisi/e7_stadio1.py", "evoluzione/analisi/e7_posthoc.py", "protocol/E7.md"]
ET = {"D1": "F′(1 sett.) − C (eta' > 1 sett.)", "D2": "F′(24 h) − C", "D3": "F′(24 h, k) − C"}


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
    S = R["stadio1"]; D = S["decisione"]
    a("# Congelamento — E7, copertura e adattamento (stadio 1)")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione `protocol/E7.md` "
      f"(impronta `{R['impronte']['protocol/E7.md']}`), firmata al commit `faf27f2e0c15a83f` prima di "
      f"eseguire lo stadio 1. **Ogni numero e' calcolato da `genera_congelamento_e7.py`** da "
      f"`e7_stadio1.json`; la decisione sullo stadio 2a e' quella della regola pre-registrata.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a("| stadio 1 | a costo zero, dai 162 npz di E5 (nessun modello eseguito); N da `e4_scelta_gated.json` "
      f"(impronta `{S['impronta_scelta_e4']}`), k da `e5_k_secondaria.json` (impronta `{S['impronta_k']}`); "
      "v₇ dalle maschere con `celle_valide` |")
    a(f"| ricampionamento | gruppi {S['repliche']['gruppi']} repliche (partizioni × semi × nodi del gruppo), "
      f"ρ {S['repliche']['rho']} repliche sulle unita' (partizione, nodo); seme {S['seme']}; soglia di gruppo "
      f"{S['min_nodi']} nodi |")
    a("| stadio 2a | " + ("**NON eseguito**: la regola pre-registrata non lo richiede (sotto)" if not D["stadio_2a"]
                        else "**richiesto dalla regola**: da eseguire") + " |")
    a("")
    a("## 2. Gruppi sotto e sopra la soglia N (nodi per cella)")
    a("")
    a("| citta' | ep. | N | sotto N | Δ₁ sotto | Δ₁ sopra | Δ₂ sotto | Δ₂ sopra | Δ₃ sotto | Δ₃ sopra |")
    a("|---|---|---|---|---|---|---|---|---|---|")

    def cella(k):
        r = S["gruppi"].get(k)
        if r is None or r.get("nd"):
            return f"n.d. ({r['nodi_per_cella']:.0f} nodi)" if r else "n.d."
        return f"{_f(r['media'])} {_ic(r['ic'])}{' *' if r['esclude_zero'] else ''}"
    for c in CITTA:
        for e in EPISODI:
            n_s = S["gruppi"].get(f"{c}/ep{e}/D1/sotto", {}).get("nodi_per_cella", 0.0)
            a(f"| {c} | {e} | {S['N'][c]} | {n_s:.0f} | " + " | ".join(
                cella(f"{c}/ep{e}/{d}/{g}") for d in ("D1", "D2", "D3") for g in ("sotto", "sopra")) + " |")
    a("")
    a("\\* intervallo che esclude lo zero. n.d. = gruppo con meno di 10 nodi per cella (soglia pre-registrata).")
    a("")
    sotto = S["ipotesi"]["gruppi_esistenti"]
    a(f"**Ipotesi pre-registrata** («l'adattamento su una settimana paga anche per i nodi sotto soglia»): "
      f"{'**VALE**' if S['ipotesi']['vale'] else ('NON vale' if S['ipotesi']['vale'] is False else 'non verificabile')} "
      f"nei {len(sotto)} gruppi sotto soglia esistenti (" + ", ".join(
          f"{k.split('/')[0]} ep. {k.split('/')[1][2:]} {_f(S['gruppi'][k]['media'])}" for k in sotto) + ").")
    a("")
    a("## 3. Correlazioni di rango (segno atteso negativo)")
    a("")
    a("| citta' | ep. | ρ(v, Δ₁) | ρ(v₇, Δ₁) | ρ(v, Δ₂) | ρ(v₇, Δ₂) | ρ(v, Δ₃) | ρ(v₇, Δ₃) |")
    a("|---|---|---|---|---|---|---|---|")
    for c in CITTA:
        for e in EPISODI:
            def rr(d, cov):
                r = S["rho"][f"{c}/ep{e}/{d}/{cov}"]
                return (f"{_f(r['rho'], 2)} {_ic(r['ic_nodi'], 2)}"
                        + (" *" if r["esclude_zero"] else "") + (" **A**" if r["anomalia_positiva"] else ""))
            a(f"| {c} | {e} | " + " | ".join(rr(d, cov) for d in ("D1", "D2", "D3") for cov in ("v", "v7")) + " |")
    a("")
    a("\\* esclude lo zero; **A** = anomalia dichiarata (ρ positiva che esclude lo zero: i nodi meno coperti "
      "traggono piu' beneficio).")
    a("")
    neg2 = [(c, e) for c in CITTA for e in EPISODI if S["rho"][f"{c}/ep{e}/D2/v"]["negativa_esclude_zero"]]
    neg1 = [(c, e) for c in CITTA for e in EPISODI if S["rho"][f"{c}/ep{e}/D1/v"]["negativa_esclude_zero"]]
    a(f"ρ(v, Δ₂) negativa con intervallo sotto lo zero in {len(neg2)}/9 (" + ", ".join(f"{c} ep. {e}" for c, e in neg2)
      + f"); ρ(v, Δ₁) negativa con intervallo sotto lo zero in {len(neg1)}/9 (" + ", ".join(f"{c} ep. {e}" for c, e in neg1)
      + "). Anomalie: " + (", ".join(D["anomalie_rho_positiva"]) if D["anomalie_rho_positiva"] else "nessuna") + ".")
    a("")
    a("## 4. Decisione sullo stadio 2a (regola pre-registrata)")
    a("")
    a(f"- (i) ipotesi fallita in almeno un gruppo: **{'si' if D['ipotesi_fallita_in_almeno_un_gruppo'] else 'no'}**")
    a(f"- (ii) ρ(v, Δ₁) o ρ(v₇, Δ₁) negativa che esclude lo zero in ≥ 2 citta' nell'episodio 1 o in 2 episodi: "
      f"**{'si' if (D['rho_negativa']['v']['vale'] or D['rho_negativa']['v7']['vale']) else 'no'}** "
      f"(v: {D['rho_negativa']['v']['vale']}, v₇: {D['rho_negativa']['v7']['vale']})")
    a(f"- stadio 2a: **{'SI ESEGUE' if D['stadio_2a'] else 'NON si esegue'}**; stadio 2b, condizionato a 2a, "
      f"{'da decidere dopo 2a' if D['stadio_2a'] else 'non si esegue'}.")
    a("")
    a("## 5. Che cosa cambia nel paper")
    a("")
    if S["ipotesi"]["vale"] and not D["stadio_2a"]:
        sotto2 = [k for k in S["gruppi"] if k.endswith("/D2/sotto") and not S["gruppi"][k].get("nd")
                  and S["gruppi"][k]["esclude_zero"] and S["gruppi"][k]["media"] > 0]
        a(f"La copertura delle prime 24 ore e' una condizione dell'adattamento a 24 ore **in alcuni "
          f"contesti** — per gradiente in {len(neg2)}/9 (ρ(v, Δ₂) sotto lo zero) e per gruppi in "
          f"{len(sotto2)} (F′(24 h) − C sopra lo zero sotto soglia: "
          + ", ".join(f"{k.split('/')[0]} ep. {k.split('/')[1][2:]} {_f(S['gruppi'][k]['media'])}" for k in sotto2)
          + ") — e **in nessun contesto** dell'adattamento a una settimana, che paga sotto soglia quanto "
            "sopra. La raccomandazione: «dopo una settimana, adattare tutti i nodi; la soglia serve solo a "
            "chi adatta prima». Londra: a 24 ore copertura e budget (E5, secondaria); a una settimana "
            "nulla da spiegare. Cambia quanto si promette, non la raccomandazione.")
    else:
        a("Vedi sezioni 2–4: la copertura resta una domanda aperta e lo stadio 2a e' richiesto.")
    a("")
    PH = R.get("post_hoc")
    if PH:
        a("## 5b. Post hoc dichiarato (richiesto dal revisore dopo il congelamento, costo zero)")
        a("")
        a("Le anomalie dello stadio 1 (ρ(v, Δ₁) > 0) sono F′ che guadagna o C che perde sui nodi radi? "
          "ρ(v, wCE per nodo) di C e di F′(1 sett.), stessi file, stesso ricampionamento:")
        a("")
        a("| citta' | ep. | v mediana | v₇ mediana | ρ(v, wCE C) | ρ(v, wCE F′(1 sett.)) | anomalia st. 1 |")
        a("|---|---|---|---|---|---|---|")
        for c in CITTA:
            for e in EPISODI:
                k = f"{c}/ep{e}"; cp = PH["copertura_episodio"][k]
                rc, rf = PH["rho"][f"{k}/wCE_C/v"], PH["rho"][f"{k}/wCE_Fp672/v"]
                an = f"{k}/D1/v" in PH["anomalie_stadio1"]
                a(f"| {c} | {e} | {cp['v_mediana']:.0f} | {cp['v7_mediana']:.0f} | {_f(rc['rho'], 2)} {_ic(rc['ic_nodi'], 2)}"
                  f"{' *' if rc['esclude_zero'] else ''} | {_f(rf['rho'], 2)} {_ic(rf['ic_nodi'], 2)}{' *' if rf['esclude_zero'] else ''} | "
                  f"{'si' if an else '—'} |")
        a("")
        a("\\* esclude lo zero.")
        a("")
        s = PH["segno_C"]
        a(f"ρ(v, wCE C) negativa con intervallo sotto lo zero in **{s['negative']}/{s['celle']}** celle; "
          f"celle con anomalia {s['anomale']}, di cui con ρ negativa {s['anomale_negative']}; "
          f"celle **senza** anomalia con ρ negativa {s['non_anomale_negative']}.")
        a("")
        if s["discrimina"]:
            a("Il segno di ρ(v, wCE C) coincide con le celle anomale: l'anomalia e' **spiegata da C**, "
              "che perde sui nodi radi dove F′ guadagna.")
        else:
            dove = ("in ogni citta' e in ogni episodio" if s["negative"] == s["celle"]
                    else f"in {s['negative']} celle su {s['celle']}")
            a("Il segno di ρ(v, wCE C) **non discrimina** le celle anomale: i nodi con ingressi radi hanno "
              f"errore maggiore per C e per F′(1 sett.) {dove}, dove l'anomalia "
              "compare e dove non compare. Il post hoc quindi **non spiega** l'anomalia: la registra come un "
              "guadagno relativo di F′ sui nodi radi in quegli episodi, senza una causa identificabile nei "
              "file di E5. Resta dichiarata come tale.")
        a("")
        a("**Copertura per episodio**: e' una proprieta' dell'episodio oltre che della citta' (colonne v e v₇), "
          "e va nella riga del paper sulla struttura del calendario, accanto ai salti settimanali.")
        a("")
    a("## 6. Impronte")
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
    print("[1/2] stadio 1"); S = leggi(a.out / "e7_stadio1.json")
    SC = leggi(a.out / "e4_scelta_gated.json"); KS = leggi(a.out / "e5_k_secondaria.json")
    if S["impronta_scelta_e4"] != SC["impronta"] or S["impronta_k"] != KS["impronta"]:
        raise IngressoMancante("impronte di N o k non coerenti")
    print("[2/2] documento")
    f_ph = a.out / "e7_posthoc.json"
    PH = json.loads(f_ph.read_text()) if f_ph.exists() else None
    R = {"data": datetime.now(timezone.utc).date().isoformat(), "commit": commit_git(),
         "stadio1": S, "post_hoc": PH, "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e7.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    Path("CONGELAMENTO_E7.md").write_text(documento(R))
    print("  generato CONGELAMENTO_E7.md; stadio 2a: "
          + ("si esegue" if S["decisione"]["stadio_2a"] else "non si esegue"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
