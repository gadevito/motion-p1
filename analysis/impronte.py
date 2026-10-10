"""
Impronte citate nei congelamenti, verificate sui file del repository.
=====================================================================
Ogni `CONGELAMENTO_E*.md` (e la tabella dei costi appaiati) cita impronte di
file: codice e protocolli (SHA-256 dei byte, 16 cifre) e file d'ingresso
(SHA-256 dei byte, oppure il campo interno `impronta` che le fasi di scelta
scrivono nel proprio json). Qui si estrae ogni impronta citata con il file a cui
si riferisce e la si ricalcola:

    dato     file sotto results/ o data_collection/: se non coincide -> DIVERSO
             (l'ingresso non e' quello che il congelamento ha usato)
    codice   .py e protocolli: se non coincide -> "cambiato dopo il congelamento"
             (informativo: i numeri si verificano a parte)

Un'impronta citata senza nome di file si cerca fra i json dei risultati e i
file del codice; se non si trova e' "non verificabile" (elencata).
I commit (`commit abc…`) non sono impronte di file e si saltano.
"""
import hashlib
import json
import re
from pathlib import Path

RIS = Path("results/evoluzione")
DOCUMENTI = ["CONGELAMENTO_E2.md", "CONGELAMENTO_E3.md", "CONGELAMENTO_E3bis.md", "CONGELAMENTO_E4.md",
             "CONGELAMENTO_E5.md", "CONGELAMENTO_E6.md", "CONGELAMENTO_E7.md", "CONGELAMENTO_E8.md",
             "paper/tabella_costi_appaiati.md"]
HEX = re.compile(r"`([0-9a-f]{12,64})`")
NOME = re.compile(r"`([A-Za-z0-9_./-]+\.(?:json|npz|csv|py|md|log|pt))`")
COMMIT = re.compile(r"(commit|firmat[oa] al commit|al commit)\s*`?$", re.I)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _impronte_interne(x, out):
    if isinstance(x, dict):
        for k, v in x.items():
            if "impronta" in str(k).lower() and isinstance(v, str):
                out.add(v)
            _impronte_interne(v, out)
    elif isinstance(x, list):
        for v in x:
            _impronte_interne(v, out)


def coincide(p: Path, h: str) -> bool:
    if _sha(p).startswith(h):
        return True
    if p.suffix == ".json":
        try:
            s = set()
            _impronte_interne(json.loads(p.read_text()), s)
            return any(v.startswith(h) or h.startswith(v) for v in s if len(v) >= 12)
        except ValueError:
            return False
    return False


def citazioni(testo: str) -> list:
    """(file citato o None, impronta) per ogni impronta del documento."""
    out = []
    for riga in testo.splitlines():
        for m in HEX.finditer(riga):
            prima = riga[:m.start()]
            if COMMIT.search(prima.rstrip(" ,(")):
                continue
            nomi = NOME.findall(prima)
            out.append((nomi[-1] if nomi else None, m.group(1)))
    return out


def _trova(radice: Path, nome: str) -> list:
    for c in (radice / nome, radice / RIS / nome):
        if c.is_file():
            return [c]
    base = Path(nome).name
    return sorted(p for p in (radice / RIS).rglob(base) if p.is_file())[:5] or \
        sorted(p for p in radice.glob(f"**/{base}") if p.is_file() and "rigenerazione" not in p.parts
               and "_archivio" not in p.parts)[:5]


def _indice(radice: Path) -> dict:
    """impronta (16) -> file, per i json dei risultati (< 20 MB) e il codice tracciato."""
    idx = {}
    candidati = [p for p in (radice / RIS).rglob("*.json") if p.stat().st_size < 20e6]
    candidati += [p for p in radice.glob("**/*.py") if "rigenerazione" not in p.parts and "_archivio" not in p.parts]
    candidati += list((radice / "protocol").glob("*.md"))
    for p in candidati:
        idx.setdefault(_sha(p)[:16], p)
        if p.suffix == ".json":
            try:
                s = set()
                _impronte_interne(json.loads(p.read_text()), s)
                for v in s:
                    idx.setdefault(v[:16], p)
            except ValueError:
                pass
    return idx


def verifica(radice: Path) -> list:
    righe, idx = [], None
    for doc in DOCUMENTI:
        f = radice / doc
        if not f.exists():
            continue
        visti = set()
        for nome, h in citazioni(f.read_text()):
            if (nome, h) in visti:
                continue
            visti.add((nome, h))
            r = {"documento": doc, "file": nome, "impronta": h}
            if nome:
                cc = _trova(radice, nome)
                if not cc:
                    r.update(esito="file non trovato", tipo="?")
                else:
                    ok = [c for c in cc if coincide(c, h)]
                    p = (ok or cc)[0]
                    rel = str(p.relative_to(radice))
                    r["tipo"] = "dato" if rel.startswith(("results/", "data_collection/")) else "codice"
                    r["trovato"] = rel
                    r["esito"] = "ok" if ok else ("DIVERSO" if r["tipo"] == "dato" else "cambiato dopo il congelamento")
            else:
                idx = idx if idx is not None else _indice(radice)
                p = idx.get(h[:16])
                r["tipo"] = "?" if p is None else ("dato" if str(p.relative_to(radice)).startswith("results/") else "codice")
                r["trovato"] = None if p is None else str(p.relative_to(radice))
                r["esito"] = "ok" if p is not None else "non verificabile"
            righe.append(r)
    return righe
