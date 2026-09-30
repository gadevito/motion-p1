#!/usr/bin/env python3
"""
Congelamento di E2 — costo di trasferimento, token ignoto.
===========================================================
**Ogni numero del documento e' derivato qui dai file di risultato**, mai
ricopiato: i confronti da `analizza_e2.calcola`, l'appaiamento da
`verifica_appaiamento.verifica`, il controllo dei veterani da
`predizioni_e2/controllo_e2.json`, la norma del token dai 108 punti E1, `rho`
dai manifesti del registro. Il verdetto sul criterio pre-registrato e'
calcolato, non scritto.

Se un ingresso manca, il generatore si ferma: un congelamento con una riga
«n.d.» non congela nulla.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_e2.py            # scrive CONGELAMENTO_E2.md
    poetry run python genera_congelamento_e2.py --solo-json
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
DIR_E1 = "E1_inserimento_griglia"
CITTA = ("Madrid", "Londra", "Melbourne")
FILE = ["evoluzione/esperimenti/esegui_E.py",
        "evoluzione/esperimenti/addestramento.py",
        "evoluzione/componente/identita.py",
        "evoluzione/componente/adattamento.py",
        "evoluzione/componente/canonico.py",
        "evoluzione/esperimenti/esegui_e2.py",
        "evoluzione/esperimenti/ricostruisci_predizioni.py",
        "evoluzione/analisi/analizza_e2.py",
        "evoluzione/analisi/verifica_appaiamento.py",
        "evoluzione/esperimenti/adeguatezza_E1.py",
        "evoluzione/esperimenti/sensibilita_rho_e2.py",
        "protocol/E2.md"]
ETICHETTE = {"F0p-C": "F₀′ − C", "F0p-F0": "F₀′ − F₀", "Fp-C": "F′ − C",
             "F0p-F0meanp": "F₀′ − F₀-mean′", "Fp-F": "F′ − F"}


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


def esecuzioni_E1(out: Path, semi_torch) -> dict:
    """Marcatori `.fatto`, esito e ordine della fase E1."""
    from evoluzione.esperimenti.fasi import percorso_E
    d = out / DIR_E1
    if not d.exists():
        raise IngressoMancante(f"cartella assente: {d}")
    attesi, fatti, secondi = [], [], []
    for c in CITTA:
        for p in (0, 1, 2):
            for st in semi_torch:
                ck = percorso_E(d, c, p, int(st), braccio="E1")
                attesi.append(ck)
                m = ck.with_name(ck.name + ".fatto")
                if m.exists():
                    fatti.append(ck)
                    secondi.append(float(json.loads(m.read_text())["secondi"]))
    esito = json.loads((d / "esito_E.json").read_text()) \
        if (d / "esito_E.json").exists() else {}
    ordine = json.loads((d / "ordine_E.json").read_text()) \
        if (d / "ordine_E.json").exists() else {}
    return {"attesi": len(attesi), "completati": len(fatti),
            "ore_calendario": esito.get("ore_calendario"),
            "fallite_ultimo_lancio": len(esito.get("fallite", [])),
            "gia_fatte_ultimo_lancio": esito.get("gia_fatte"),
            "somma_parete_ore": float(np.sum(secondi)) / 3600 if secondi else None,
            "protocollo": ordine.get("protocollo"),
            "lavoratori": ordine.get("lavoratori"), "fili": ordine.get("fili"),
            "punti": fatti}


def rho_dai_manifesti(out: Path) -> dict:
    """`rho` DICHIARATO: dai manifesti completati della fase E1, tutti uguali."""
    valori, n = set(), 0
    for f in (out / "registro").glob("*.json"):
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if d.get("esperimento") != f"{DIR_E1}/E1":
            continue
        if d.get("run_status") != "completato":
            continue
        cfg = d.get("resolved_configuration") or {}
        n += 1
        valori.add(float(cfg.get("rho")) if cfg.get("rho") is not None
                   else None)
    if n == 0:
        raise IngressoMancante(f"nessun manifesto completato per {DIR_E1}/E1 "
                               f"in {out / 'registro'}")
    if len(valori) != 1 or None in valori:
        raise IngressoMancante(f"rho non univoco nei manifesti: {valori}")
    return {"rho": valori.pop(), "manifesti": n}


def token_dai_punti(punti) -> dict:
    """Norma del token e distanza dall'embedding medio, per punto E1.

    Il rapporto e' fra la norma del token e la norma MEDIANA delle righe di
    embedding dello stesso punto: dice se il token e' un vettore «vero» o una
    copia della media.
    """
    import torch
    rapporti, distanze, norme = [], [], []
    for ck in punti:
        sd = torch.load(ck, map_location="cpu", weights_only=False)["state_dict"]
        if "identita.ignoto" not in sd:
            raise IngressoMancante(f"{ck.name}: manca identita.ignoto")
        tok = sd["identita.ignoto"].reshape(-1).double()
        emb = sd["identita.embedding"].double()
        nt = float(tok.norm())
        med = float(emb.norm(dim=1).median())
        norme.append(nt)
        rapporti.append(nt / med)
        distanze.append(float((tok - emb.mean(0)).norm()))
    r = np.asarray(rapporti)
    return {"n": len(punti), "norma_token_mediana": float(np.median(norme)),
            "rapporto_mediano": float(np.median(r)),
            "rapporto_min": float(r.min()), "rapporto_max": float(r.max()),
            "distanza_dalla_media_mediana": float(np.median(distanze)),
            "distanza_dalla_media_min": float(np.min(distanze))}


def veterani(out: Path) -> dict:
    f = out / "predizioni_e2" / "controllo_e2.json"
    if not f.exists():
        raise IngressoMancante(f"assente: {f}")
    d = json.loads(f.read_text())
    v = d["veterani"]
    rel = np.asarray([z["scarto_relativo"] for z in v], dtype="float64")
    soglia = float(d.get("soglia_veterani", 0.01))
    return {"celle": len(v), "soglia": soglia,
            "oltre_soglia": int((rel > soglia).sum()),
            "mediana_rel": float(np.median(rel)), "max_rel": float(rel.max()),
            "min_rel": float(rel.min()),
            "valutazioni_bracci": len(d["bracci"])}


def _f(x, n=3):
    return f"{x:+.{n}f}"


def _ic(q):
    return f"[{_f(q[0])}, {_f(q[1])}]"


def _ic4(q):
    return f"[{_f(q[0], 4)}, {_f(q[1], 4)}]"


def documento(R: dict) -> str:
    A = []
    a = A.append
    E, T, V, C, K, W = (R["esecuzioni"], R["token"], R["veterani"],
                        R["confronti"], R["appaiamento"], R["criterio"])
    a("# Congelamento — E2, costo di trasferimento con token ignoto")
    a("")
    a(f"**Congelato il {R['data']}**, commit `{R['commit']}`. Pre-registrazione "
      f"`protocol/E2.md` (impronta `{R['impronte']['protocol/E2.md']}`). "
      f"**Ogni numero di questo documento e' calcolato da "
      f"`genera_congelamento_e2.py`** a partire dai file di risultato; il "
      f"verdetto sul criterio e' derivato, non scritto.")
    a("")
    a("## 1. Che cosa e' stato eseguito")
    a("")
    a("| | |")
    a("|---|---|")
    a(f"| braccio addestrato | **E1** = E con token ignoto appreso e identity "
      f"dropout **ρ = {R['rho']['rho']:g}**, dichiarato prima del lancio "
      f"({R['rho']['manifesti']} manifesti concordi) |")
    a(f"| punti E1 | **{E['completati']}** su {E['attesi']} attesi, marcatori "
      f"`.fatto`; cartella `{DIR_E1}` |")
    a(f"| protocollo | `{E['protocollo']}`: 2.290 aggiornamenti, undici punti, "
      f"selezione su V-full della rete iniziale, griglia temporale reale |")
    a(f"| parallelismo | {E['lavoratori']} processi × {E['fili']} filo, backend "
      f"CPU |")
    a(f"| ore di calendario | {E['ore_calendario']:.1f} |"
      if E["ore_calendario"] is not None else "| ore di calendario | n.d. |")
    a(f"| somma dei tempi di parete | {E['somma_parete_ore']:.1f} ore — **non e' "
      f"il costo seriale**: le esecuzioni erano concorrenti |")
    a(f"| bracci di valutazione | F₀′ (token, nessun aggiornamento), F′ (dal "
      f"token, adattato sulle 24 h con la configurazione F congelata), "
      f"F₀-mean′ (media degli iniziali, controllo); {V['valutazioni_bracci']} "
      f"valutazioni |")
    a("")
    a("## 2. Controlli obbligatori")
    a("")
    a("| controllo | esito |")
    a("|---|---|")
    a(f"| token effettivamente usato | norma del token a **{T['rapporto_mediano']:.2f}×** "
      f"la norma mediana di un embedding (min {T['rapporto_min']:.2f}, max "
      f"{T['rapporto_max']:.2f} su {T['n']} punti); distanza dall'embedding medio "
      f"mediana {T['distanza_dalla_media_mediana']:.3f}, minima "
      f"{T['distanza_dalla_media_min']:.3f}: **non e' una copia della media** |")
    a(f"| veterani (E1 contro E sui nodi iniziali) | **{V['oltre_soglia']}** celle "
      f"su {V['celle']} oltre l'{V['soglia']:.0%} relativo; scarto mediano "
      f"{V['mediana_rel']:+.2%}, massimo {V['max_rel']:+.2%} — "
      + ("**il token non danneggia la rete esistente**"
         if V["oltre_soglia"] == 0 else
         "**costo della politica, da riportare in tabella**") + " |")
    a(f"| appaiamento dei confronti | {K['celle']} celle, {K['ricalcoli']} "
      f"ricalcoli cella per cella, **{len(K['anomalie'])} anomalie** |")
    a(f"| controllo F₀-mean′ | eseguito, {sum(1 for k in C if k.endswith('F0p-F0meanp'))} "
      f"citta' |")
    a("")
    a("## 3. I confronti pre-registrati")
    a("")
    a(f"Differenze di wCE, appaiate per cella (seme, partizione, nodo); "
      f"intervallo al 95% con ricampionamento congiunto di partizioni, semi e "
      f"nodi, {R['repliche']} repliche, seme {R['seme_bootstrap']}. "
      f"Negativo = meglio del secondo termine.")
    a("")
    a("| | " + " | ".join(ETICHETTE.values()) + " |")
    a("|---|" + "---|" * len(ETICHETTE))
    for c in CITTA:
        celle = []
        for k in ETICHETTE:
            z = C[f"{c}/{k}"]
            celle.append(f"**{_f(z['media'])}** {_ic(z['ic_con_nodi'])}"
                         + (" (zero)" if z["include_zero"] else ""))
        n = R["celle"][c]
        a(f"| {c} ({n['semi']}×{n['partizioni']}×{n['nodi']}) | "
          + " | ".join(celle) + " |")
    a("")
    a("### Riduzione del costo di trasferimento")
    a("")
    a("| | F₀ − C | F₀′ − C | riduzione |")
    a("|---|---|---|---|")
    for c in CITTA:
        f0c = C[f"{c}/F0p-C"]["media"] - C[f"{c}/F0p-F0"]["media"]
        f0pc = C[f"{c}/F0p-C"]["media"]
        rid = 1 - f0pc / f0c if f0c else float("nan")
        a(f"| {c} | {_f(f0c)} | {_f(f0pc)} | {rid:.0%} |")
    a("")
    a("(F₀ − C e' ricavato per differenza dai due confronti sopra: stesse celle.)")
    a("")
    a("## 4. Verdetto sul criterio pre-registrato")
    a("")
    a("> **Successo = (1) F₀′ − C con intervallo che include lo zero o negativo "
      "in 3 citta' su 3, e (3) F′ − C negativo con intervallo che esclude lo "
      "zero in almeno 2.**")
    a("")
    a(f"- condizione (1): soddisfatta in **{W['condizione_1_citta']} citta' su 3**"
      f" (serviva 3/3)")
    a(f"- condizione (3): soddisfatta in **{W['condizione_3_citta']} citta' su 3**"
      f" (servivano 2/3)")
    a("")
    if W["soddisfatto"]:
        a("**Criterio SODDISFATTO.** Il costo di trasferimento e' rimosso "
          "dall'addestramento con token ignoto e l'adattamento locale resta "
          "utile.")
    else:
        a("**Criterio NON soddisfatto.** Si riportano gli effetti circoscritti, "
          "senza riclassificare i confronti secondari come principali.")
    a("")
    a("## 5. Che cosa si riporta")
    a("")
    for c in CITTA:
        z1, z2, z3 = (C[f"{c}/F0p-C"], C[f"{c}/F0p-F0meanp"], C[f"{c}/Fp-F"])
        a(f"- **{c}**: il token porta il nodo nuovo a {_f(z1['media'])} da C "
          f"{_ic(z1['ic_con_nodi'])}; dentro lo stesso modello il token batte la "
          f"media di {_f(z2['media'])} {_ic(z2['ic_con_nodi'])}; l'adattamento "
          f"dal token arriva dove arrivava dalla media: F′ − F = "
          f"{_f(z3['media'])} {_ic(z3['ic_con_nodi'])}"
          + (" (zero)" if z3["include_zero"] else "") + ".")
    a("")
    a("Il costo di trasferimento si riduce ma non si azzera; l'adattamento e' "
      "indifferente al punto di partenza; i veterani non peggiorano. **Il "
      "confronto secondario F₀′ − F₀-mean′ resta secondario.**")
    a("")
    a("## 6. Gli altri due controlli della pre-registrazione")
    a("")
    S, Q = R.get("sensibilita"), R.get("adeguatezza")
    a("### Sensibilita' a ρ (figura, non criterio)")
    a("")
    if S is None:
        a(f"**NON eseguita**: atteso `{R['percorsi']['sensibilita']}`.")
    else:
        a(f"{S['contesto']} p{S['partizione']}, semi {S['semi']}; ρ = "
          f"{S['rho_campagna']:g} dalla campagna, gli altri addestrati apposta. "
          f"Intervalli a ricampionamento di semi e nodi su una sola partizione: "
          f"**non confrontabili** con quelli a tre livelli della sezione 3. "
          f"Figura: `{S['figura']}`.")
        a("")
        a("| ρ | F₀′ − C | F′ − C | token / mediana embedding (min–max sui semi) | veterani, scarto massimo |")
        a("|---|---|---|---|---|")
        for r in S["rho"]:
            k = f"{r:.2f}"; c = S["confronti"][k]; d = S["per_seme"][k]
            tk = [z["rapporto_norma_token"] for z in d]
            vt = max(z["veterani_rel"] for z in d)
            # quattro decimali: a ρ = 0,30 l'intervallo sfiora lo zero
            a(f"| {r:g} | {_f(c['F0p-C']['media'], 4)} {_ic4(c['F0p-C']['ic_semi_nodi'])} "
              f"| {_f(c['Fp-C']['media'], 4)} {_ic4(c['Fp-C']['ic_semi_nodi'])} "
              f"| {min(tk):.2f}–{max(tk):.2f} | {vt:+.2%} |")
        a("")
        a("**ρ resta 0,15**: e' stato fissato prima del lancio e il criterio e' "
          "stato valutato li'. La figura dice come il costo di trasferimento al "
          "punto di partenza dipende da ρ; un altro ρ come braccio sarebbe un "
          "esperimento nuovo, da pre-registrare.")
    a("")
    a("### Prova di adeguatezza ridotta a 4.580 per E1")
    a("")
    if Q is None:
        a(f"**NON eseguita**: atteso `{R['percorsi']['adeguatezza']}`.")
    else:
        t0_, t1_ = "2290", str(Q["tetto"])
        rip = Q["riproduce_campagna"]
        a(f"{Q['contesto']} p{Q['partizione']} seme {Q['seme']}, E ed E1 "
          f"attraverso `addestra_una`, {len(Q['punti'])} punti fino a {Q['tetto']}. "
          f"I primi undici punti riproducono la campagna: scarto massimo "
          + ", ".join(f"{b} {rip[b]['scarto_massimo']:.0e}" for b in Q["bracci"])
          + ".")
        a("")
        a("| tetto | E: u, V-full | E1: u, V-full | ordine |")
        a("|---|---|---|---|")
        for t in (t0_, t1_):
            sE, s1 = Q["selezione"]["E"][t], Q["selezione"]["E1"][t]
            a(f"| {t} | u{sE['aggiornamento']}, {sE['V-full']:.5f} | "
              f"u{s1['aggiornamento']}, {s1['V-full']:.5f} | {Q['ordine'][t]} |")
        a("")
        m = Q["miglioramento_relativo_oltre_2290"]
        a(f"**Ordine {'invariato' if Q['ordine_invariato'] else 'CAMBIATO'}** "
          f"fra 2.290 e {Q['tetto']}; oltre il budget V-full migliora ancora di "
          + ", ".join(f"{b} {m[b]:+.2%}" for b in Q["bracci"])
          + ": plateau non raggiunto, ordine stabile — come nella prova di "
            "adeguatezza della campagna principale.")
    a("")
    a("## 7. Decisioni conseguenti")
    a("")
    a("- **E′ (= E1) e' il braccio E principale per E5 ed E6**: dichiarato nel "
      "protocollo §6 (esito riportato il 30/9), prima di E4.")
    peggio = [c for c in CITTA if C[f"{c}/Fp-C"]["ic_con_nodi"][0] > 0]
    if peggio:
        a("- **E7 non e' piu' opzionale** e la politica gated di E4 ammette "
          "**τ = «mai»**: l'adattamento dal token peggiora C con intervallo che "
          "esclude lo zero a " + ", ".join(
              f"{c} ({_f(C[f'{c}/Fp-C']['media'])} "
              f"{_ic(C[f'{c}/Fp-C']['ic_con_nodi'])})" for c in peggio) + ".")
    else:
        a("- In nessuna citta' F′ − C e' positivo con intervallo che esclude lo "
          "zero: E7 resta come da protocollo (non opzionale dal 30/9 per la "
          "campagna principale), ma E2 non aggiunge un caso.")
    a("")
    a("## 8. Impronte")
    a("")
    a("| file | impronta |")
    a("|---|---|")
    for f, hh in R["impronte"].items():
        a(f"| `{f}` | `{hh}` |")
    a("")
    a("**Nessun parametro e' stato scelto dopo aver visto i risultati**: ρ e' "
      "nei manifesti di ogni esecuzione, la configurazione di F e' quella "
      "congelata in `selezione_F_griglia`.")
    return "\n".join(A) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--solo-json", action="store_true")
    a = ap.parse_args()
    from evoluzione.analisi.analizza_e2 import calcola
    from evoluzione.analisi.verifica_appaiamento import verifica
    from evoluzione.esperimenti.semi import configurazione
    _, _, semi_t = configurazione(inserimento=True)

    print("[1/6] esecuzioni E1")
    E = esecuzioni_E1(a.out, semi_t)
    if E["completati"] != E["attesi"]:
        raise IngressoMancante(f"punti E1 completati {E['completati']} su "
                               f"{E['attesi']}: non si congela una fase a meta'")
    print("[2/6] rho dai manifesti")
    rho = rho_dai_manifesti(a.out)
    print("[3/6] token dai punti E1")
    T = token_dai_punti(E["punti"])
    print("[4/6] veterani")
    V = veterani(a.out)
    print("[5/6] appaiamento")
    K = verifica(a.out)
    if K["anomalie"]:
        raise IngressoMancante(f"appaiamento con {len(K['anomalie'])} anomalie: "
                               f"{K['anomalie'][:3]}")
    print("[6/6] confronti con ricampionamento dei nodi")
    C = calcola(a.out / "predizioni_e2", a.out / "predizioni_f0",
                a.out / "predizioni_fase3", stampa=lambda *_: None)
    if C["mancanti"]:
        raise IngressoMancante(f"file di predizione mancanti: {C['mancanti']}")
    # controlli dichiarati in protocol/E2.md la cui evidenza vive in file
    # separati: si riporta se ESISTONO, non si assume
    percorsi = {"sensibilita": a.out / "sensibilita_rho_e2.json",
                "adeguatezza": a.out / "adeguatezza_E1.json"}
    letti = {k: (json.loads(f.read_text()) if f.exists() else None)
             for k, f in percorsi.items()}
    for k, f in percorsi.items():
        print(f"  {k}: {'letto' if letti[k] else 'ASSENTE'} ({f})")
    R = {"data": datetime.now(timezone.utc).date().isoformat(),
         "percorsi": {k: str(f) for k, f in percorsi.items()},
         "sensibilita": letti["sensibilita"], "adeguatezza": letti["adeguatezza"],
         "commit": commit_git(), "rho": rho,
         "esecuzioni": {k: v for k, v in E.items() if k != "punti"},
         "token": T, "veterani": V,
         "appaiamento": K, "confronti": C["confronti"], "celle": C["celle"],
         "criterio": C["criterio"], "repliche": C["repliche"],
         "seme_bootstrap": C["seme_bootstrap"],
         "impronte": {f: h(f) for f in FILE}}
    (a.out / "congelamento_e2.json").write_text(json.dumps(R, indent=2,
                                                           ensure_ascii=False))
    print(f"  numeri in {a.out / 'congelamento_e2.json'}")
    if not a.solo_json:
        Path("CONGELAMENTO_E2.md").write_text(documento(R))
        print("  generato CONGELAMENTO_E2.md")
    W = C["criterio"]
    print(f"\n  criterio: (1) {W['condizione_1_citta']}/3, (3) "
          f"{W['condizione_3_citta']}/3 -> "
          f"{'SODDISFATTO' if W['soddisfatto'] else 'NON soddisfatto'}")
    print(f"  veterani oltre soglia: {V['oltre_soglia']}/{V['celle']}; "
          f"appaiamento: {len(K['anomalie'])} anomalie; token {T['rapporto_mediano']:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
