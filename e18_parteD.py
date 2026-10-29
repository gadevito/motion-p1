#!/usr/bin/env python3
"""
E18 parte D: ricerca storica limitata ai commit fino alla firma del protocollo E18 (28/10/2026).
===================================================================================================
Richiesta del revisore (29/10, 18:30): il `git log -S` delle stringhe della politica gated(1 sett., 0) nella storia
del protocollo (OR3) e del manoscritto, e il `git log --diff-filter=A` dei file CONGELAMENTO_*, vanno limitati ai
commit raggiungibili dalla firma del protocollo: OR3 `964e4f5`, manoscritto `ae12921` (= `manoscritto-20261028j`).
La ricostruzione storica non deve dipendere dalle modifiche successive. Esito atteso invariato: prima formulazione
2026-10-22, 11 contesti su 11 osservati prima.

Passi (sostituzioni letterali, si ferma se un testo atteso non compare esattamente una volta):
1. `evoluzione/analisi/analizza_e18.py`: costante `LIMITE_D`, `_prima_data(..., fino_a=...)`, limite registrato in
   `R["D"]["limite_storia"]` (commit, data, motivo) e verifica che i due commit esistano.
2. `genera_congelamento_e18.py`: nota datata in §4 con il limite dichiarato; riga in §6.
3. `analizza_e18.py --parte D` e il generatore, con l'interprete del progetto (sul Mac: parte D legge solo json e git).
4. Riga 29 del registro: aggiunta datata con la nuova impronta.

Dalla radice OR3/ (ramo esecutore/e18-parteD):  python3 e18_parteD.py --python <interprete>
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent
OGGI = date.today().isoformat()
AN = R / "evoluzione" / "analisi" / "analizza_e18.py"
GEN = R / "genera_congelamento_e18.py"
REG = R / "protocol" / "REGISTRO_CORREZIONI.md"
CONG = R / "CONGELAMENTO_E18.md"


def imp(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


SOST = {AN: [
    ('''SEME_BOOT = 20261028
TOLLERANZA_C = 1e-6''',
     '''SEME_BOOT = 20261028
TOLLERANZA_C = 1e-6
# parte D: la ricerca storica (git log) e' limitata ai commit raggiungibili dalla firma del protocollo E18 (28/10/2026),
# cosi' la ricostruzione non dipende dalle modifiche successive (richiesta del revisore, 29/10/2026)
LIMITE_D = {"OR3": "964e4f5", "manoscritto": "ae12921"}'''),
    ('''def _prima_data(cwd, percorso=None, testo=None):
    """La data (YYYY-MM-DD) e il commit del primo commit che aggiunge `percorso` o che introduce `testo`."""
    if testo is not None:
        o = _git(["log", "--reverse", "--format=%ad %h", "--date=short", "-S", testo, "--"] + ([percorso] if percorso else []), cwd)
    else:
        o = _git(["log", "--reverse", "--diff-filter=A", "--format=%ad %h", "--date=short", "--", percorso], cwd)''',
     '''def _prima_data(cwd, percorso=None, testo=None, fino_a="HEAD"):
    """La data (YYYY-MM-DD) e il commit del primo commit, fra quelli raggiungibili da `fino_a`, che aggiunge `percorso`
    o che introduce `testo`."""
    if testo is not None:
        o = _git(["log", "--reverse", "--format=%ad %h", "--date=short", "-S", testo, fino_a, "--"] + ([percorso] if percorso else []), cwd)
    else:
        o = _git(["log", "--reverse", "--diff-filter=A", "--format=%ad %h", "--date=short", fino_a, "--", percorso], cwd)'''),
    ('''    rep = Path(__file__).resolve().parents[2]; paper = rep.parent / "paper1"
    E17 = json.loads((out / "e17_risultati.json").read_text())''',
     '''    rep = Path(__file__).resolve().parents[2]; paper = rep.parent / "paper1"
    limite = {}
    for nome, cwd in (("OR3", rep), ("manoscritto", paper)):
        if nome == "manoscritto" and not paper.exists():
            continue
        o = _git(["log", "-1", "--format=%ad %h", "--date=short", LIMITE_D[nome]], cwd)
        if not o:
            raise RuntimeError(f"parte D: il commit limite {LIMITE_D[nome]} ({nome}) non esiste in {cwd}")
        limite[nome] = {"commit": LIMITE_D[nome], "data": o.split()[0]}
    f_oss = lambda f: _prima_data(rep, f, fino_a=LIMITE_D["OR3"])  # noqa: E731
    E17 = json.loads((out / "e17_risultati.json").read_text())'''),
    ('''    for k, f in FILE_CTX.items():
        d = _prima_data(rep, f)
        oss[k] = {**d, "file": f} if d else None''',
     '''    for k, f in FILE_CTX.items():
        d = f_oss(f)
        oss[k] = {**d, "file": f} if d else None'''),
    ('''    for f in ("CONGELAMENTO_E_F_GRIGLIA.md", "CONGELAMENTO_E2.md"):
        d = _prima_data(rep, f)''',
     '''    for f in ("CONGELAMENTO_E_F_GRIGLIA.md", "CONGELAMENTO_E2.md"):
        d = f_oss(f)'''),
    ('''            d = _prima_data(rep, f, t)
            if d:
                form["protocollo"][f"{f} «{t}»"] = d''',
     '''            d = _prima_data(rep, f, t, fino_a=LIMITE_D["OR3"])
            if d:
                form["protocollo"][f"{f} «{t}»"] = d'''),
    ('''            d = _prima_data(paper, None, t)
            if d:
                form["manoscritto"][f"«{t}»"] = d''',
     '''            d = _prima_data(paper, None, t, fino_a=LIMITE_D["manoscritto"])
            if d:
                form["manoscritto"][f"«{t}»"] = d'''),
    ('''         "prima_formulazione": {"data": prima_form, "dettaglio": form}, "osservazioni": oss, "contesti": {}, "istante": None}''',
     '''         "limite_storia": {"motivo": "ricostruzione storica: git log limitato ai commit raggiungibili dalla firma del protocollo "
                                     "E18 (28/10/2026), indipendente dalle modifiche successive (richiesta del revisore, 29/10/2026)",
                           **limite},
         "prima_formulazione": {"data": prima_form, "dettaglio": form}, "osservazioni": oss, "contesti": {}, "istante": None}'''),
], GEN: [
    ('''        L += ["## 4. Parte D — provenienza della politica gated(1 sett., 0) (documentaria)", "",
              f"{Dq['definizione']}.", "",''',
     '''        lim = Dq.get("limite_storia", {})
        L += ["## 4. Parte D — provenienza della politica gated(1 sett., 0) (documentaria)", "",
              f"{Dq['definizione']}.", "",
              "Nota del 29/10/2026 (richiesta del revisore): la ricerca storica (`git log -S` delle stringhe della politica, "
              "`git log --diff-filter=A` dei file CONGELAMENTO_*) e' limitata ai commit raggiungibili dalla firma del protocollo E18 "
              "(28/10/2026): " + "; ".join(f"{k} `{v['commit']}` ({v['data']})" for k, v in lim.items() if isinstance(v, dict))
              + ". Motivo: la ricostruzione e' storica e non deve dipendere dalle modifiche successive al protocollo e al manoscritto. "
              "Esito invariato rispetto alla versione del 28/10.", "",'''),
    ('''          "copiati nel registro `protocol/e18/tempi_parte_A.json` e il documento li legge da li'; `main.py` tratta `A/tempi` del "
          "json come metadati.", ""]''',
     '''          "copiati nel registro `protocol/e18/tempi_parte_A.json` e il documento li legge da li'; `main.py` tratta `A/tempi` del "
          "json come metadati.",
          "- 29/10/2026, parte D: ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, manoscritto "
          "`ae12921` = `manoscritto-20261028j`), su richiesta del revisore; il protocollo §4 non fissava un limite. Stesso esito "
          "(prima formulazione 2026-10-22, 11 contesti su 11 osservati prima); `analizza_e18.py --parte D` rieseguito, parti A, B, C "
          "invariate.", ""]'''),
]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", default=sys.executable)
    a = ap.parse_args()
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, _ in coppie:
            if t.count(v) != 1:
                print(f"FERMO: in {f.relative_to(R)} il testo atteso compare {t.count(v)} volte:\n{v[:150]}"); return 1
    if "| 29 |" not in REG.read_text():
        print("FERMO: riga 29 assente nel registro"); return 1
    fj = R / "results" / "evoluzione" / "e18_risultati.json"
    J0 = json.loads(fj.read_text()); D0 = J0["D"]
    prima = imp(CONG)
    for f, coppie in SOST.items():
        t = f.read_text()
        for v, n in coppie:
            t = t.replace(v, n)
        f.write_text(t); print(f"  {f.relative_to(R)}: {len(coppie)} sostituzioni")
    import py_compile
    for f in SOST:
        py_compile.compile(str(f), doraise=True)
    r = subprocess.run([a.python, str(AN), "--parte", "D"], cwd=R, capture_output=True, text=True)
    print(r.stdout[-400:])
    if r.returncode != 0:
        print(r.stderr[-1500:]); print("FERMO: parte D fallita"); return 1
    J1 = json.loads(fj.read_text()); D1 = J1["D"]
    # stesso esito e stessi numeri: tutto uguale tranne istante e limite_storia
    for k in ("A", "B", "C"):
        if J0[k] != J1[k]:
            print(f"FERMO: la parte {k} e' cambiata"); return 1
    chiavi = set(D0) | set(D1)
    diverse = [k for k in chiavi if k not in ("istante", "limite_storia") and D0.get(k) != D1.get(k)]
    if diverse:
        print(f"FERMO: la parte D cambia in {diverse}"); return 1
    if D1["esito"]["osservati_prima_della_formulazione"] != 11 or D1["prima_formulazione"]["data"] != "2026-10-22":
        print(f"FERMO: esito diverso da quello atteso: {D1['esito']}, {D1['prima_formulazione']['data']}"); return 1
    print(f"  parte D: limite {D1['limite_storia']}; esito invariato (2026-10-22, 11/11)")
    r = subprocess.run([a.python, str(GEN)], cwd=R, capture_output=True, text=True)
    print(r.stdout[-300:])
    if r.returncode != 0:
        print(r.stderr[-1500:]); print("FERMO: il generatore e' fallito"); return 1
    dopo = imp(CONG)
    if "Nota del 29/10/2026 (richiesta del revisore)" not in CONG.read_text():
        print("FERMO: il congelamento non porta la nota della parte D"); return 1
    tr = REG.read_text(); righe = tr.rstrip("\n").split("\n")
    i29 = [i for i, l in enumerate(righe) if l.startswith("| 29 |")]
    if len(i29) != 1:
        print("FERMO: riga 29 non univoca"); return 1
    l = righe[i29[0]]; k = l.rfind(" | ")
    agg = (f". Rigenerato il {OGGI} (parte D): ricerca storica limitata ai commit fino alla firma del protocollo (OR3 `964e4f5`, "
           f"manoscritto `ae12921`), stesso esito; impronta `CONGELAMENTO_E18.md` `{prima}` → `{dopo}`, `e18_risultati.json` "
           f"`{imp(fj)}`, `congelamento_e18.json` `{imp(R / 'results/evoluzione/congelamento_e18.json')}`")
    righe[i29[0]] = l[:k].rstrip() + agg + l[k:]
    REG.write_text("\n".join(righe) + "\n")
    print(f"  registro: riga 29 integrata; CONGELAMENTO_E18.md {prima} → {dopo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
