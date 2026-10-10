#!/usr/bin/env python3
"""
Paper 1 — rigenerazione di ogni numero e confronto con i congelamenti.
=======================================================================
Un solo script. Parte dalle predizioni per cella e dagli aggregati salvati in
`results/evoluzione/`, riesegue **con il codice statistico gia' nel repository**
ogni fase di analisi che non addestra e non valuta modelli (scelte su
validazione, confronti con ricampionamento congiunto, curve, copertura), poi
ogni generatore dei congelamenti, e confronta numero per numero:

    *_risultati.json, scelte, soglie   contro i file congelati omonimi
    congelamento_e*.json               contro i file congelati omonimi
    CONGELAMENTO_E*.md                 contro i documenti nel repository
                                       (righe con date e impronte mascherate)
    tabelle del Paper 1                contro `analysis/tabelle_paper1.py`
                                       (il valore stampato nel manoscritto)

Le figure si ottengono **chiamando gli script esistenti** (nessuna copia della
loro logica): analizza_e4, analizza_e5, e7_stadio1, figura2_51, figura_e8bis.

Niente viene scritto in `results/` ne' alla radice del repository. Tutto gira
in una cartella di lavoro (`analysis/rigenerazione/<istante>/radice/`) che
contiene:
    results/evoluzione   CLONE dei risultati (APFS, `cp -c`: copia a costo
                         zero e indipendente: una scrittura non tocca
                         l'originale); dove il clone non e' disponibile,
                         albero di collegamenti simbolici + controllo
    il resto             collegamenti simbolici al repository (codice, protocolli)
Gli script usano percorsi relativi (`results/evoluzione`, `CONGELAMENTO_*.md`):
eseguiti con quella cartella come directory corrente, scrivono li'.
Prima e dopo l'esecuzione si prende l'impronta (dimensione, mtime) di ogni file
di `results/evoluzione` reale: se cambia qualcosa lo script fallisce.

Le fasi di **scelta** (tau, N; soglie di E8) vengono rigenerate e confrontate,
poi il file congelato viene rimesso al suo posto: le fasi a valle usano
esattamente la scelta registrata prima del test, come nel protocollo.

Non si rieseguono (sono ingressi, con l'impronta stampata nel log):
addestramenti, valutazioni dei modelli sulle celle (`--fase valuta/prova/
curve`), adattamenti (k della secondaria, E2, sensibilita' a rho), costi
misurati. Il confronto copre cio' che da quei file si ricava.

Uso (dalla radice OR3/):

    poetry run python analysis/main.py                  # tutto
    poetry run python analysis/main.py --solo E4 E5     # solo alcuni esperimenti
    poetry run python analysis/main.py --elenco         # fasi, senza eseguire
    poetry run python analysis/main.py --tex ../paper1/main.tex

Uscita: `analysis/rigenerazione/<istante>/rapporto.md` e `rapporto.json`, un
log per fase in `log/`, le figure in `radice/figure/`. Codice d'uscita 0 solo
se ogni numero coincide entro la tolleranza e ogni fase e' andata a buon fine.
"""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE))
RIS = Path("results/evoluzione")

# chiavi di metadati: si riportano se differiscono, non fanno fallire
METADATI = re.compile(r"(istante|impronta|impronte|hash|^sha|commit|generat|^data$|^data_|percorso|^file$|"
                      r"durata|secondi_parete|^ora$|macchina|python|versione)", re.I)


def e_metadato(p: str) -> bool:
    """Un punto e' metadato se lo e' una qualunque delle sue chiavi."""
    return any(METADATI.search(re.sub(r"\[\d+\]$", "", k)) for k in p.split("/") if k)
# nei documenti: date, istanti, impronte esadecimali, commit
MASCHERA_MD = [re.compile(r"\b[0-9a-f]{7,64}\b"),
               re.compile(r"\d{4}-\d{2}-\d{2}([T ][\d:.+Z-]+)?"),
               re.compile(r"\b\d{1,2}/\d{1,2}(/\d{2,4})?\b")]


def F(e, cmd, uscite, scelta=False, figure=()):
    """Una fase: `cmd` relativo alla radice del repository, `uscite` relative
    alla cartella di lavoro. `scelta=True`: dopo il confronto si ripristina il
    file congelato. `figure`: file in figure/ attesi (solo esistenza)."""
    return {"esperimento": e, "cmd": cmd, "uscite": list(uscite), "scelta": scelta,
            "figure": list(figure)}


E = "evoluzione/esperimenti/"
A = "evoluzione/analisi/"
R_ = str(RIS) + "/"
FASI = [
    # §III: architettura letta dai pesi dei checkpoint di E ed E' (nessun addestramento)
    F("ARCH", [A + "architettura_ck.py"], [R_ + "architettura_ck.json"]),
    # E2: il generatore esegue `analizza_e2.calcola` sulle predizioni per cella
    F("E2", ["genera_congelamento_e2.py"], [R_ + "congelamento_e2.json", "CONGELAMENTO_E2.md"]),
    # E3
    F("E3", [A + "analizza_e3.py", "--out", R_ + "analisi_e3.json"], [R_ + "analisi_e3.json"]),
    F("E3", [A + "analizza_veterani_e3.py", "--out", R_ + "veterani_e3.json"], [R_ + "veterani_e3.json"]),
    F("E3", [A + "riselezione_rmon.py", "--out", R_ + "riselezione_rmon.json"], [R_ + "riselezione_rmon.json"]),
    F("E3", [A + "costi_e3.py", "--out", R_ + "costi_e3.json"], [R_ + "costi_e3.json"]),
    F("E3", ["genera_congelamento_e3.py"], [R_ + "congelamento_e3.json", "CONGELAMENTO_E3.md"]),
    # E4
    F("E4", [E + "esegui_e4.py", "--fase", "scegli"], [R_ + "e4_scelta_gated.json"], scelta=True),
    F("E4", [E + "esegui_e4.py", "--fase", "test"], [R_ + "e4_risultati.json"]),
    F("E4", [A + "analizza_e4.py"], [R_ + "e4_griglia_test.json"],
      figure=["curva_e4.png", "traiettoria_e4.png", "griglia_e4.png"]),
    F("E4", [A + "analizza_copertura_e4.py", "--out", R_ + "copertura_e4.json"], [R_ + "copertura_e4.json"]),
    F("E4", ["genera_congelamento_e4.py"], [R_ + "congelamento_e4.json", "CONGELAMENTO_E4.md"]),
    # E3-bis (usa gli aggregati di E4)
    F("E3bis", [A + "analizza_e3bis.py"], [R_ + "e3bis_risultati.json"]),
    F("E3bis", ["genera_congelamento_e3bis.py"], [R_ + "congelamento_e3bis.json", "CONGELAMENTO_E3bis.md"]),
    # E5
    # prepara ricontrolla i nove t0 registrati in preparazione_e5.json (ingresso) e scrive e5_prepara.json
    F("E5", [E + "esegui_e5.py", "--fase", "prepara"], [R_ + "e5_prepara.json"], scelta=True),
    F("E5", [A + "settimana_vs_A_e5.py"], [R_ + "e5_settimana_vs_A.json"]),
    F("E5", [E + "esegui_e5.py", "--fase", "test"], [R_ + "e5_risultati.json"]),
    F("E5", [A + "analizza_e5.py"], [], figure=["episodi_e5.png", "secondaria_e5.png"]),
    F("E5", ["genera_congelamento_e5.py"], [R_ + "congelamento_e5.json", "CONGELAMENTO_E5.md"]),
    # E6 (parte B PEMS08, E6-bis, parte A PEMS04)
    F("E6", [E + "esegui_e6.py", "--fase", "scegli"], [R_ + "e6_scelta_gated.json"], scelta=True),
    F("E6", [E + "esegui_e6.py", "--fase", "test"], [R_ + "e6_risultati.json"]),
    F("E6", [E + "esegui_e6.py", "--fase", "test-bis"], [R_ + "e6bis_risultati.json"]),
    F("E6", [E + "esegui_e6a.py", "--fase", "scegli"], [R_ + "e6a_scelta_gated.json"], scelta=True),
    F("E6", [E + "esegui_e6a.py", "--fase", "test"], [R_ + "e6a_risultati.json"]),
    F("E6", [E + "esegui_e6.py", "--fase", "origini"], [R_ + "e6_origini_comuni.json"]),
    F("E6", ["genera_congelamento_e6.py"], ["CONGELAMENTO_E6.md"]),
    # E7
    F("E7", [A + "e7_stadio1.py"], [R_ + "e7_stadio1.json"], figure=["e7_stadio1.png"]),
    F("E7", [A + "e7_posthoc.py"], [R_ + "e7_posthoc.json"]),
    F("E7", ["genera_congelamento_e7.py"], [R_ + "congelamento_e7.json", "CONGELAMENTO_E7.md"]),
    # E8 ed E8-bis
    F("E8", [E + "esegui_e8.py", "--fase", "soglie"], [R_ + "e8_soglie.json"], scelta=True),
    F("E8", [E + "esegui_e8.py", "--fase", "test"], [R_ + "e8_risultati.json"]),
    F("E8", [E + "esegui_e8.py", "--fase", "test-curve"], [R_ + "e8bis_risultati.json"]),
    F("E8", [A + "figura_e8bis.py"], [R_ + "curve_e8bis_punti.json"], figure=["curve_e8bis.png"]),
    F("E8", [A + "figura2_51.py"], [], figure=["figura2_51.png"]),
    F("E8", ["genera_congelamento_e8.py"], ["CONGELAMENTO_E8.md"]),
]
# figure del manoscritto: gli stessi script, con --lingua en, verso <paper>/figures/
FIGURE_PAPER = [("E4", A + "analizza_e4.py", ["curva_e4.pdf", "traiettoria_e4.pdf"]),
                ("E5", A + "analizza_e5.py", ["episodi_e5.pdf"]),
                ("E8", A + "figura2_51.py", ["figura2_51.pdf"]),
                ("E8", A + "figura_e8bis.py", ["curve_e8bis.pdf"])]
ESPERIMENTI = ["ARCH", "E2", "E3", "E4", "E3bis", "E5", "E6", "E7", "E8"]


# ---------------------------------------------------------------- impronte --
def sha256(f: Path, blocco=1 << 20) -> str:
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        while b := fh.read(blocco):
            h.update(b)
    return h.hexdigest()


def istantanea(d: Path) -> dict:
    """(dimensione, mtime_ns) di ogni file sotto d, senza seguire i collegamenti."""
    s = {}
    for r, _, ff in os.walk(d):
        for n in ff:
            p = Path(r) / n
            st = p.lstat()
            s[str(p.relative_to(d))] = (st.st_size, st.st_mtime_ns)
    return s


def impronte_ingressi(ris: Path, completo: bool) -> dict:
    """SHA-256 dei file di primo livello (json, log) e, per ogni cartella, di
    un elenco ordinato (nome, dimensione) dei suoi file; con `completo` lo
    SHA-256 di ogni file (lento: decine di GB)."""
    out = {}
    for p in sorted(ris.iterdir()):
        if p.is_file():
            out[p.name] = sha256(p)
        elif p.is_dir():
            if completo:
                for q in sorted(p.rglob("*")):
                    if q.is_file():
                        out[str(q.relative_to(ris))] = sha256(q)
            else:
                h = hashlib.sha256()
                n = 0
                for q in sorted(p.rglob("*")):
                    if q.is_file():
                        h.update(f"{q.relative_to(p)}\t{q.stat().st_size}\n".encode()); n += 1
                out[p.name + "/"] = f"elenco:{h.hexdigest()} ({n} file)"
    return out


# ---------------------------------------------------------------- sandbox --
def clona(src: Path, dst: Path) -> str:
    """Clone APFS se possibile; altrimenti albero di collegamenti simbolici."""
    if platform.system() == "Darwin":
        prova = dst.parent / ".prova_clone"
        campione = next(p for p in src.iterdir() if p.is_file())
        r = subprocess.run(["cp", "-c", str(campione), str(prova)], capture_output=True)
        if r.returncode == 0:
            prova.unlink()
            r = subprocess.run(["cp", "-cR", str(src), str(dst)], capture_output=True, text=True)
            if r.returncode == 0:
                return "clone APFS"
            shutil.rmtree(dst, ignore_errors=True)
    for r, dd, ff in os.walk(src):
        rel = Path(r).relative_to(src)
        (dst / rel).mkdir(parents=True, exist_ok=True)
        for n in ff:
            os.symlink(Path(r) / n, dst / rel / n)
    return "collegamenti simbolici (con controllo d'integrita')"


def prepara_radice(lavoro: Path) -> tuple:
    radice = lavoro / "radice"
    radice.mkdir(parents=True)
    escludi = {"results", "figure", "analysis", ".git", "__pycache__", ".DS_Store"}
    for p in RADICE.iterdir():
        if p.name in escludi or re.fullmatch(r"CONGELAMENTO_.*\.md", p.name):
            continue
        os.symlink(p, radice / p.name)
    (radice / "figure").mkdir()
    (radice / "results").mkdir()
    for p in (RADICE / "results").iterdir():
        if p.name != "evoluzione":
            os.symlink(p, radice / "results" / p.name)
    modo = clona(RADICE / RIS, radice / RIS)
    return radice, modo


# -------------------------------------------------------------- confronto --
def confronta(a, b, tol_rel: float, tol_abs: float, via="") -> tuple:
    """(differenze numeriche o strutturali, differenze di metadati, ogni coppia
    numerica confrontata come (dove, congelato, rigenerato))."""
    diff, meta, tutti = [], [], []

    def rec(x, y, p):
        if e_metadato(p) and not (isinstance(x, dict) and isinstance(y, dict)):
            if x != y:
                meta.append({"dove": p, "atteso": y, "ottenuto": x})
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(set(x) | set(y), key=str):
                q = f"{p}/{k}"
                if k not in x or k not in y:
                    (meta if e_metadato(q) else diff).append(
                        {"dove": q, "atteso": "assente" if k not in y else "presente",
                         "ottenuto": "assente" if k not in x else "presente"})
                else:
                    rec(x[k], y[k], q)
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                diff.append({"dove": p, "atteso": f"lista di {len(y)}", "ottenuto": f"lista di {len(x)}"})
            for i, (u, v) in enumerate(zip(x, y)):
                rec(u, v, f"{p}[{i}]")
        elif isinstance(x, bool) or isinstance(y, bool):
            if x != y:
                diff.append({"dove": p, "atteso": y, "ottenuto": x})
        elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
            tutti.append((p, y, x))
            if isinstance(x, float) and isinstance(y, float) and math.isnan(x) and math.isnan(y):
                return
            if abs(x - y) > max(tol_abs, tol_rel * max(abs(x), abs(y))):
                diff.append({"dove": p, "atteso": y, "ottenuto": x, "scarto": x - y})
        elif x != y:
            diff.append({"dove": p, "atteso": y, "ottenuto": x})

    rec(a, b, via)
    return diff, meta, tutti


def fmt(v) -> str:
    """Rappresentazione stabile fra macchine: 12 cifre significative."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, int):
        return str(v)
    return "nan" if math.isnan(v) else f"{v:.12g}"


def fmt_scarto(d) -> str:
    return "0" if d == 0 else f"{d:+.2e}"


def impronta_numeri(tutti, i: int) -> str:
    """SHA-256 dell'elenco ordinato (punto, valore a 12 cifre): uguale fra due
    esecuzioni se e solo se ogni numero coincide a 12 cifre significative."""
    return hashlib.sha256("\n".join(f"{t[0]}\t{fmt(t[i])}" for t in sorted(tutti, key=lambda t: t[0]))
                          .encode()).hexdigest()[:16]


def maschera(riga: str) -> str:
    for r in MASCHERA_MD:
        riga = r.sub("·", riga)
    return riga.rstrip()


NUMERO = re.compile(r"[-+−]?\d+(?:[.,]\d+)*")


def solo_testo(righe: list) -> bool:
    """Le righe cambiate contengono gli stessi numeri (come multinsieme) prima e dopo:
    la differenza e' di sola prosa, non di numeri."""
    from collections import Counter
    tolte = Counter(n for r in righe if r.startswith("-") for n in NUMERO.findall(r[1:]))
    messe = Counter(n for r in righe if r.startswith("+") for n in NUMERO.findall(r[1:]))
    return tolte == messe


def confronta_md(nuovo: Path, congelato: Path) -> list:
    a = [maschera(r) for r in nuovo.read_text().splitlines()]
    b = [maschera(r) for r in congelato.read_text().splitlines()]
    import difflib
    return [r for r in difflib.unified_diff(b, a, "congelato", "rigenerato", n=0, lineterm="")
            if r[:1] in "+-" and not r.startswith(("+++", "---"))]


# ------------------------------------------------------------- esecuzione --
def esegui(fase, radice: Path, lavoro: Path, i: int, tol) -> dict:
    nome = f"{i:02d}_{fase['esperimento']}_" + "_".join(
        re.sub(r"[^A-Za-z0-9]+", "", Path(c).stem) for c in fase["cmd"][:1] + fase["cmd"][2:3])
    for u in fase["uscite"]:
        (radice / u).unlink(missing_ok=True)
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONHASHSEED": "0"}
    t = time.time()
    with open(lavoro / "log" / f"{nome}.log", "w") as log:
        log.write("$ " + " ".join([sys.executable, *fase["cmd"]]) + f"\n  (cwd {radice})\n\n")
        log.flush()
        r = subprocess.run([sys.executable, str(RADICE / fase["cmd"][0]), *fase["cmd"][1:]],
                           cwd=radice, env=env, stdout=log, stderr=subprocess.STDOUT)
    esito = {"fase": nome, "cmd": " ".join(fase["cmd"]), "codice": r.returncode,
             "secondi": round(time.time() - t, 1), "uscite": {}, "figure": {}}
    for u in fase["uscite"]:
        nuovo, congelato = radice / u, RADICE / u
        rec = {"rigenerato": nuovo.exists(), "congelato_presente": congelato.exists()}
        if nuovo.exists() and congelato.exists():
            if u.endswith(".json"):
                d, m, tutti = confronta(json.loads(nuovo.read_text()), json.loads(congelato.read_text()), *tol)
                sc = [abs(t[2] - t[1]) for t in tutti
                      if not (isinstance(t[1], float) and math.isnan(t[1]))]
                rec.update(numeri=len(tutti), differenze=d, metadati_diversi=m,
                           max_scarto=max(sc, default=0.0),
                           impronta_congelato=impronta_numeri(tutti, 1),
                           impronta_rigenerato=impronta_numeri(tutti, 2))
                with open(lavoro / "NUMERI.tsv", "a") as fh:
                    for t in tutti:
                        fh.write(f"{u}\t{t[0]}\t{fmt(t[1])}\t{fmt(t[2])}\t{fmt_scarto(t[2] - t[1])}\n")
            elif u.endswith(".md"):
                rr = confronta_md(nuovo, congelato)
                if rr and solo_testo(rr):
                    rec.update(righe_diverse=[], righe_solo_testo=rr)
                else:
                    rec.update(righe_diverse=rr)
        if fase["scelta"] and congelato.exists():
            shutil.copy2(congelato, nuovo)               # a valle si usa la scelta registrata
            rec["ripristinato"] = True
        esito["uscite"][u] = rec
    for f in fase["figure"]:
        esito["figure"][f] = (radice / "figure" / f).exists()
    return esito


def esito_fase(e) -> str:
    if e["codice"] != 0:
        return "FALLITA"
    for u, r in e["uscite"].items():
        if not r["rigenerato"]:
            return "NON RIGENERATO"
        if r.get("differenze") or r.get("righe_diverse"):
            return "DIVERSO"
    if not all(e["figure"].values()):
        return "FIGURA MANCANTE"
    return "ok"


# --------------------------------------------------------------- CONFRONTO --
def scrivi_confronto(f: Path, meta: dict, esiti: list, paper: list, ok: bool):
    """Il rapporto tracciato in git. Deterministico: nessun istante, macchina,
    durata o percorso assoluto, cosi' che due esecuzioni su macchine diverse si
    confrontino con `diff` e le sole differenze siano nei numeri."""
    L = ["# Paper 1 — confronto fra numeri rigenerati e congelati", "",
         "Generato da `analysis/main.py` (non modificare a mano). Ogni numero e' rigenerato dalle predizioni "
         "per cella con il codice del repository e confrontato con il file congelato omonimo. "
         "Valori a 12 cifre significative; scarto = rigenerato − congelato.", "",
         f"- esito: **{'TUTTO COINCIDE' if ok else 'DIFFERENZE O ERRORI'}**",
         f"- esperimenti: {', '.join(meta['esperimenti'])}",
         f"- tolleranza: relativa {meta['tol_rel']:g}, assoluta {meta['tol_abs']:g}",
         f"- risultati reali dopo l'esecuzione: {meta['integrita_risultati']}",
         f"- non coperto (ingressi, non rigenerati): {meta['non_coperto']}", "",
         "## 1. Tabelle del Paper 1", "",
         "| tabella | voce | stampato | congelato | rigenerato | scarto | esito |",
         "|---|---|---|---:|---:|---:|---|"]
    for p in paper:
        L.append(f"| {p['tabella']} | {p['voce']} | {p['stampato']} | {fmt(p.get('congelato_valore', '—'))} | "
                 f"{fmt(p.get('rigenerato_valore', '—'))} | {p.get('scarto', '—')} | {p['esito']} |")
    L += ["", "## 2. File rigenerati", "",
          "Impronta = SHA-256 (16 cifre) dell'elenco ordinato (punto, valore a 12 cifre) di tutti i numeri "
          "del file: coincide fra congelato e rigenerato se e solo se coincidono tutti i numeri.", "",
          "| fase | file | esito | numeri | diversi | scarto massimo | impronta congelato | impronta rigenerato |",
          "|---|---|---|---:|---:|---:|---|---|"]
    for e in esiti:
        for u, r in e["uscite"].items():
            nd = len(r.get("differenze", [])) + len(r.get("righe_diverse", []))
            if u.endswith(".md"):
                L.append(f"| `{e['cmd']}` | `{u}` | {esito_fase(e)} | — | {nd} righe | — | — | — |")
            else:
                L.append(f"| `{e['cmd']}` | `{Path(u).name}` | {esito_fase(e)} | {r.get('numeri', '—')} | {nd} | "
                         f"{fmt_scarto(r['max_scarto']) if 'max_scarto' in r else '—'} | "
                         f"{r.get('impronta_congelato', '—')} | {r.get('impronta_rigenerato', '—')} |")
        if not e["uscite"]:
            L.append(f"| `{e['cmd']}` | (solo figure) | {esito_fase(e)} | — | — | — | — | — |")
    L += ["", "## 3. Ogni numero diverso oltre la tolleranza", ""]
    righe = []
    for e in esiti:
        for u, r in e["uscite"].items():
            if not r["rigenerato"]:
                righe.append(f"- `{u}`: **non rigenerato** (fase `{e['cmd']}`, codice {e['codice']})")
            for d in r.get("differenze", []):
                sc = fmt_scarto(d["scarto"]) if "scarto" in d else "—"
                righe.append(f"- `{Path(u).name}` `{d['dove']}`: congelato {fmt(d['atteso'])}, "
                             f"rigenerato {fmt(d['ottenuto'])}, scarto {sc}")
            for d in r.get("righe_diverse", []):
                righe.append(f"- `{u}` (date e impronte mascherate): `{d}`")
    L += righe or ["Nessuno."]
    L += ["", "## 4. Impronte degli ingressi citate nei congelamenti", "",
          "Ogni impronta di file citata in un congelamento (e nella tabella dei costi), ricalcolata sul file del "
          "repository: SHA-256 dei byte (16 cifre) o campo interno `impronta`. Un dato diverso fa fallire; un "
          "file di codice cambiato dopo il congelamento e' informativo.", "",
          "| congelamento | file | tipo | impronta citata | esito |", "|---|---|---|---|---|"]
    for r in meta["impronte_citate"]:
        L.append(f"| `{r['documento']}` | `{r['file'] or r.get('trovato') or '—'}` | {r['tipo']} | `{r['impronta']}` | {r['esito']} |")
    L += ["", "## 5. Documenti: differenze di sola prosa (stessi numeri)", "",
          "Informativo, non fa fallire: righe del documento rigenerato diverse da quelle congelate ma con gli "
          "stessi numeri (per esempio una frase che dipende da quali esperimenti esistevano al momento del "
          "congelamento).", ""]
    tt = [f"- `{u}`: `{r}`" for e in esiti for u, x in e["uscite"].items() for r in x.get("righe_solo_testo", [])]
    L += tt or ["Nessuna."]
    L += ["", "## 6. File di codice cambiati dopo il congelamento che li cita (registro, Paper 2)", "",
          "Informativo. Per ogni file di codice con impronta citata diversa da quella attuale: il commit della "
          "versione citata (se la storia git la contiene) e i commit successivi che lo cambiano.", "",
          "| file | congelamento | impronta citata | versione citata (commit, data) | cambiato in (commit, data, oggetto) |",
          "|---|---|---|---|---|"]
    for r in meta["impronte_citate"]:
        if r["esito"] != "cambiato dopo il congelamento":
            continue
        st = r.get("storia") or {}
        vc = st.get("versione_citata")
        vc = f"`{vc[0]}` {vc[1]}" if vc else "non presente nella storia git (stato non committato al congelamento)"
        cc = "<br>".join(f"`{c}` {d} {o}" for c, d, o in st.get("commit", [])) or "—"
        L.append(f"| `{r['trovato']}` | `{r['documento']}` | `{r['impronta']}` | {vc} | {cc} |")
    L += ["", "## 7. Impronte del codice diverse da quelle registrate nel congelamento (json)", "",
          "Informativo, non fa fallire: il file di codice e' cambiato dopo il congelamento, i numeri no "
          "(sezione 3). Date, commit e istanti non sono elencati.", ""]
    imp = sorted({(Path(u).name, m["dove"], fmt(m["atteso"]), fmt(m["ottenuto"]))
                  for e in esiti for u, r in e["uscite"].items() for m in r.get("metadati_diversi", [])
                  if re.search(r"impront", m["dove"], re.I) and not re.search(r"istante|data|commit", m["dove"])})
    L += [f"- `{f}` `{d}`: congelato {a}, attuale {b}" for f, d, a, b in imp] or ["Nessuna."]
    L += ["", "## 8. Figure (script esistenti)", ""]
    for e in esiti:
        for g, c in e["figure"].items():
            dove = g.replace("paper:", "<paper>/figures/") if g.startswith("paper:") else f"figure/{g}"
            L.append(f"- `{dove}` da `{e['cmd']}`: {'prodotta' if c else 'MANCANTE'}")
    L += ["", "## 9. Impronte degli ingressi (`results/evoluzione`)", "",
          "SHA-256 dei file di primo livello; per le cartelle, dell'elenco (nome, dimensione) dei file." , "", "```"]
    L += [f"{k}  {v}" for k, v in sorted(meta["impronte_ingressi"].items())] + ["```"]
    f.write_text("\n".join(L) + "\n")


# ---------------------------------------------------------------- rapporto --
def rapporto(lavoro: Path, meta: dict, esiti: list, paper: list) -> bool:
    ok = all(esito_fase(e) == "ok" for e in esiti) and all(p["esito"].startswith(("ok", "non rigenerato")) for p in paper) \
        and meta["integrita_risultati"] == "invariati" \
        and not any(r["esito"] in ("DIVERSO", "file non trovato") for r in meta["impronte_citate"])
    L = [f"# Rigenerazione Paper 1 — {meta['istante']}", "",
         f"Esito complessivo: **{'TUTTO COINCIDE' if ok else 'DIFFERENZE O ERRORI'}**", "",
         f"- commit {meta['commit']} ({'pulito' if not meta['git_status'] else 'con modifiche locali'}); "
         f"macchina {meta['macchina']}; Python {meta['python']}; numpy {meta['numpy']}",
         f"- sandbox: {meta['sandbox']}; risultati reali: **{meta['integrita_risultati']}**",
         f"- tolleranza: relativa {meta['tol_rel']}, assoluta {meta['tol_abs']}",
         f"- impronte degli ingressi: `rapporto.json` → `impronte_ingressi` ({len(meta['impronte_ingressi'])} voci)",
         "", "## Fasi", "",
         "| fase | esito | s | numeri confrontati | differenze | metadati diversi |",
         "|---|---|---:|---:|---:|---:|"]
    for e in esiti:
        n = sum(r.get("numeri", 0) for r in e["uscite"].values())
        d = sum(len(r.get("differenze", [])) + len(r.get("righe_diverse", [])) for r in e["uscite"].values())
        m = sum(len(r.get("metadati_diversi", [])) for r in e["uscite"].values())
        L.append(f"| `{e['cmd']}` | {esito_fase(e)} | {e['secondi']} | {n} | {d} | {m} |")
    for e in esiti:
        for u, r in e["uscite"].items():
            if r.get("differenze") or r.get("righe_diverse") or not r["rigenerato"]:
                L += ["", f"### {u}  (`{e['cmd']}`)", ""]
                if not r["rigenerato"]:
                    L.append("non rigenerato: vedere il log della fase")
                for d in r.get("differenze", [])[:40]:
                    L.append(f"- `{d['dove']}`: congelato {d['atteso']!r}, rigenerato {d['ottenuto']!r}")
                for d in r.get("righe_diverse", [])[:40]:
                    L.append(f"    {d}")
    L += ["", "## Tabelle del Paper 1", "",
          "| tabella | voce | stampato | congelato | rigenerato | esito |", "|---|---|---|---|---|---|"]
    for p in paper:
        L.append(f"| {p['tabella']} | {p['voce']} | {p['stampato']} | {fmt(p.get('congelato_valore', '—'))} | "
                 f"{fmt(p.get('rigenerato_valore', '—'))} | {p['esito']} |")
    L += ["", "Non coperto da questo script (ingressi, non rigenerati): " + meta["non_coperto"]]
    (lavoro / "rapporto.md").write_text("\n".join(L) + "\n")
    (lavoro / "rapporto.json").write_text(json.dumps(
        {"meta": meta, "fasi": esiti, "paper": paper, "ok": ok}, indent=2, ensure_ascii=False, default=str))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--solo", nargs="*", choices=ESPERIMENTI, default=ESPERIMENTI)
    ap.add_argument("--lavoro", type=Path, default=None)
    ap.add_argument("--tol-rel", type=float, default=1e-9)
    ap.add_argument("--tol-abs", type=float, default=1e-12)
    ap.add_argument("--tex", type=Path, default=None,
                    help="manoscritto: verifica anche che ogni valore stampato compaia nel .tex")
    ap.add_argument("--impronte-complete", action="store_true",
                    help="SHA-256 di ogni file d'ingresso (lento)")
    ap.add_argument("--paper", type=Path, default=None,
                    help="cartella del manoscritto (es. ../paper1): figure in inglese in <paper>/figures/ e "
                         "tabella C1 del supplementare, dai risultati rigenerati")
    ap.add_argument("--elenco", action="store_true")
    ap.add_argument("--tieni", action="store_true", help="non cancellare il clone dei risultati alla fine")
    a = ap.parse_args()
    fasi = [f for f in FASI if f["esperimento"] in a.solo]
    if a.elenco:
        for i, f in enumerate(fasi):
            print(f"{i:02d} {f['esperimento']:6s} {' '.join(f['cmd']):60s} -> {', '.join(f['uscite'] + f['figure'])}"
                  + ("   [scelta: ripristinata]" if f["scelta"] else ""))
        return 0
    os.chdir(RADICE)
    ist = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lavoro = (a.lavoro or RADICE / "analysis" / "rigenerazione" / ist).resolve()
    (lavoro / "log").mkdir(parents=True, exist_ok=False)
    print(f"cartella di lavoro {lavoro}")
    import numpy
    git = lambda *c: subprocess.run(["git", *c], cwd=RADICE, capture_output=True, text=True).stdout.strip()
    print("impronte degli ingressi…", flush=True)
    meta = {"istante": ist, "commit": git("rev-parse", "HEAD"), "git_status": git("status", "--porcelain"),
            "macchina": f"{platform.node()} {platform.platform()}", "python": platform.python_version(),
            "numpy": numpy.__version__, "tol_rel": a.tol_rel, "tol_abs": a.tol_abs, "esperimenti": a.solo,
            "impronte_ingressi": impronte_ingressi(RADICE / RIS, a.impronte_complete),
            "non_coperto": ("addestramenti e valutazioni dei modelli sulle celle, adattamenti di E2, k della "
                            "secondaria di E5, sensibilita' a rho, costi misurati (manifesti isolati), "
                            "numeri del resoconto della campagna principale, dati di disegno (sensori, "
                            "partizioni, semi)")}
    for k, v in sorted(meta["impronte_ingressi"].items()):
        print(f"  {k}  {v}")
    from analysis.impronte import verifica as verifica_impronte
    meta["impronte_citate"] = verifica_impronte(RADICE)
    from analysis.impronte import storia_codice
    for r in meta["impronte_citate"]:
        if r["esito"] == "cambiato dopo il congelamento":
            r["storia"] = storia_codice(RADICE, r["trovato"], r["impronta"])
    n_div = sum(r["esito"] in ("DIVERSO", "file non trovato") for r in meta["impronte_citate"])
    print(f"impronte citate nei congelamenti: {len(meta['impronte_citate'])}, ingressi diversi: {n_div}")
    prima = istantanea(RADICE / RIS)
    print("sandbox…", flush=True)
    radice, meta["sandbox"] = prepara_radice(lavoro)
    print(f"  {meta['sandbox']}")
    esiti, paper = [], []
    try:
        for i, f in enumerate(fasi):
            print(f"[{i + 1}/{len(fasi)}] {f['esperimento']}: {' '.join(f['cmd'])}", flush=True)
            e = esegui(f, radice, lavoro, i, (a.tol_rel, a.tol_abs))
            esiti.append(e)
            print(f"    {esito_fase(e)}  ({e['secondi']} s)", flush=True)
        from analysis.tabelle_paper1 import scrivi_tabella_C1, verifica
        paper = verifica(radice / RIS, RADICE / RIS, a.tex, a.solo)
        if a.paper is not None:
            dfig = (RADICE / a.paper).resolve() / "figures"
            for esp, script, attese in FIGURE_PAPER:
                if esp not in a.solo:
                    continue
                f = F(esp, [script, "--lingua", "en", "--figure", str(dfig)], [])
                print(f"[paper] {' '.join(f['cmd'][:3])} -> {dfig}", flush=True)
                e = esegui(f, radice, lavoro, len(esiti), (a.tol_rel, a.tol_abs))
                e["cmd"] = f"{script} --lingua en"                 # nel rapporto senza percorsi assoluti
                e["figure"] = {f"paper:{g}": (dfig / g).exists() for g in attese}
                esiti.append(e)
                print(f"    {esito_fase(e)}", flush=True)
            if "E5" in a.solo:
                scrivi_tabella_C1(radice / RIS, dfig / "tableC1_episodes.tex")
    finally:
        dopo = istantanea(RADICE / RIS)
        meta["integrita_risultati"] = "invariati" if dopo == prima else \
            f"CAMBIATI: {sorted(set(prima.items()) ^ set(dopo.items()))[:10]}"
        if not a.tieni and meta["sandbox"].startswith("clone"):
            shutil.rmtree(radice / RIS, ignore_errors=True)
    ok = rapporto(lavoro, meta, esiti, paper)
    confronto = RADICE / "analysis" / "rigenerazione" / "CONFRONTO.md"
    scrivi_confronto(confronto, meta, esiti, paper, ok)
    print(f"\n{'TUTTO COINCIDE' if ok else 'DIFFERENZE O ERRORI'} — {confronto.relative_to(RADICE)}; "
          f"dettaglio in {lavoro / 'rapporto.md'}, ogni numero in {lavoro / 'NUMERI.tsv'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
