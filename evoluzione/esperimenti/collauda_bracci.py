#!/usr/bin/env python3
"""
Collaudo della tabella unica dei bracci.
=========================================
La tabella (`componente/bracci.py`) ha sostituito sei punti del codice in cui
i bracci erano confrontati per nome. Questo collaudo verifica che:

    [1] per i bracci CONGELATI (C, P, E, E1, A, R, F) la tabella riproduce
        ESATTAMENTE i predicati che ha sostituito — copiati qui alla lettera
        dal codice precedente, come oracolo;
    [2] le viste derivate (CARICANO, PREPARATORI, ...) coincidono;
    [3] `fasi` legge dalla tabella e i suoi controlli trattano R-orig e R-mon
        come R;
    [4] i valori di campionamento e selezione dichiarati in tabella che
        `addestra_una` NON accetta ancora sono esattamente quelli di E3:
        l'esecutore mancante e' dichiarato, non scoperto a meta' campagna;
    [5] nel codice non restano confronti sul nome del braccio fuori da un
        elenco chiuso di eccezioni motivate.

**Non importa torch**: gira ovunque, anche senza dati.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/collauda_bracci.py
"""
import ast
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RADICE))
from evoluzione.componente import bracci as B  # noqa: E402

ESITI = []


def v(n, titolo, cond, dett=""):
    ESITI.append(bool(cond))
    print(f"  [{n}] {'PASSA' if cond else 'FALLISCE'}  {titolo}")
    if dett:
        print(f"        {dett}")


# ---------------------------------------------------------------- ORACOLI --
# copiati alla lettera dal codice che la tabella ha sostituito
CONGELATI = ("C", "P", "E", "E1", "A", "R", "F")
FORNITORE_PRIMA = {"C": "NoIdentity", "P": "ObservableIdentityEncoder",
                   "E": "LearnedNodeEmbedding", "A": "LearnedNodeEmbedding",
                   "R": "LearnedNodeEmbedding",
                   "E1": "LearnedNodeEmbedding(token_ignoto)", "F": None}
USA_DESC_PRIMA = {"C": False, "P": True, "E": False, "A": False, "R": False,
                  "E1": False, "F": False}
CARICANO_PRIMA = ("C", "P", "E", "E1", "A", "R")           # canonico.py
SENZA_DESCRITTORE_PRIMA = ("C", "E", "E1", "A", "R")       # addestra_una
PREFISSO_PRIMA = ("E", "E1")                               # nome_ck
PREPARATORI_PRIMA = ("E", "E1")                            # uscita = ck
POPOLAZIONE_PRIMA = {                                      # fasi.py
    "C": "nodi iniziali",
    "P": "nodi iniziali",
    "E": "nodi iniziali",
    "A": "nodi iniziali + nodi che simulano le nuove installazioni",
    "R": "nodi iniziali + nodi nuovi",
    "F": "nodi iniziali (da E) + nodi nuovi registrati separatamente",
}
CORPUS_PRIMA = {
    "C": "addestramento originario",
    "P": "addestramento originario",
    "E": "addestramento originario",
    "A": "addestramento originario ESTESO, con la storia anteriore a t0 dei "
         "nodi privilegiati",
    "R": "addestramento originario + esempi ammissibili delle prime 24 ore "
         "dei nodi nuovi, SENZA storia anteriore a t0",
    "F": "esempi ammissibili delle prime 24 ore dei soli nodi nuovi",
}
# inserimento.cfg_braccio ed esegui_inserimento, alla lettera
VARIANTE_PRIMA = {b: ("BASE-CORRECTED" if b == "P" else None)
                  for b in ("C", "P", "A", "R")}
POPOLAZIONE_CFG_PRIMA = {b: ("ampliata" if b in ("A", "R") else "iniziale")
                         for b in ("C", "P", "A", "R")}
CAMPIONAMENTO_PRIMA = {b: ("uniforme_nodo" if b == "R" else "uniforme_istanti")
                       for b in ("C", "P", "A", "R")}
ADDESTRANO_PRIMA = ("C", "P", "A", "R")
COSTO_INSERIMENTO_PRIMA = {b: (b == "R") for b in ("C", "P", "A", "R")}
ATTESA_PRIMA = {b: (b in ("P", "F", "R")) for b in ("C", "P", "A", "R", "F")}
CORPUS_COSTRUTTORE_PRIMA = {"C": "originario", "P": "originario",
                            "A": "privilegiato", "R": "post_installazione",
                            "F": "acquisizione"}

FORNITORE_TABELLA = {"nessuna": "NoIdentity",
                     "descrittore": "ObservableIdentityEncoder",
                     "embedding": "LearnedNodeEmbedding",
                     "embedding_token": "LearnedNodeEmbedding(token_ignoto)",
                     "adattato_da_E": None}

# [5] i confronti sul nome del braccio che RESTANO, con il motivo. Ogni voce
# e' (file, riga della sorgente senza spazi iniziali). Un confronto nuovo non
# elencato qui fa fallire il collaudo.
ECCEZIONI = {
    ("evoluzione/esperimenti/esegui_E.py",
     'if a.braccio == "E1" and a.protocollo != "griglia_E1":'):
        "guardia dell'orchestratore: la cartella dei punti E1 e' propria",
    ("evoluzione/esperimenti/esegui_inserimento.py", 'if b == "A" else "")}'):
        "nota testuale sulla disponibilita' di A",
    ("evoluzione/esperimenti/prova_inserimento.py",
     'if b == "F" else None)'):
        "prova tecnica: F e' l'unico braccio con un modello in memoria",
    ("evoluzione/esperimenti/prova_inserimento.py", 'if b == "F":'):
        "prova tecnica: idem",
    ("evoluzione/esperimenti/ricostruisci_predizioni.py",
     'if a.braccio == "F":'):
        "ricostruzione: F si ricostruisce dal punto E, gli altri dal proprio",
    ("evoluzione/componente/corpus.py", 'if b == "A":'):
        "etichetta del MANIFESTO del corpus, non del braccio",
    ("evoluzione/componente/corpus.py", 'elif b == "R":'):
        "etichetta del manifesto del corpus, non del braccio",
}
NOMI_VARIABILI = {"b", "braccio", "braccio_", "nome"}


def confronti_letterali():
    """(file, riga) di ogni confronto `<var> == "<braccio>"` nel codice."""
    nomi = set(B.TABELLA)
    fuori = []
    for d in ("evoluzione/esperimenti", "evoluzione/componente",
              "evoluzione/analisi", "checks"):
        for f in sorted((RADICE / d).glob("*.py")):
            if f.name in ("bracci.py", "collauda_bracci.py"):
                continue
            src = f.read_text()
            righe = src.splitlines()
            for n in ast.walk(ast.parse(src)):
                if not isinstance(n, ast.Compare):
                    continue
                sx = n.left
                var = (sx.id if isinstance(sx, ast.Name) else
                       sx.attr if isinstance(sx, ast.Attribute) else None)
                if var not in NOMI_VARIABILI:
                    continue
                for c in n.comparators:
                    vals = ([c.value] if isinstance(c, ast.Constant) else
                            [e.value for e in getattr(c, "elts", [])
                             if isinstance(e, ast.Constant)])
                    if any(z in nomi for z in vals):
                        fuori.append((str(f.relative_to(RADICE)),
                                      righe[n.lineno - 1].strip()))
                        break
    return fuori


def tuple_dopo(src: str, testo: str) -> tuple:
    """La tupla di stringhe nel primo `if X not in (...)` che segue `testo`."""
    t = ast.parse(src)
    righe = src.splitlines()
    for n in ast.walk(t):
        if (isinstance(n, ast.Compare) and isinstance(n.ops[0], ast.NotIn)
                and testo in righe[n.lineno - 1]):
            c = n.comparators[0]
            return tuple(e.value for e in c.elts)
    raise LookupError(testo)


def main() -> int:
    print("=" * 80)
    print("COLLAUDO DELLA TABELLA UNICA DEI BRACCI")
    print("=" * 80)
    T = B.TABELLA

    # ------------------------------------------------------------ [1] ----
    print("\n[1] i bracci congelati riproducono i predicati sostituiti")
    v("1a", "tutti i bracci congelati sono dichiarati",
      all(b in T for b in CONGELATI), ", ".join(T))
    v("1b", "fornitore per braccio come in `_fornitore`",
      all(FORNITORE_TABELLA[T[b].fornitore] == FORNITORE_PRIMA[b]
          for b in CONGELATI))
    v("1c", "`usa_descrittore` come il secondo valore di `_fornitore`",
      all(T[b].usa_descrittore == USA_DESC_PRIMA[b] for b in CONGELATI))
    v("1d", "carica il canonico esattamente chi era in `CARICANO`",
      all(T[b].carica_canonico == (b in CARICANO_PRIMA) for b in CONGELATI))
    v("1e", "senza descrittore esattamente l'elenco di `addestra_una`",
      all((not T[b].usa_descrittore) == (b in SENZA_DESCRITTORE_PRIMA)
          for b in CONGELATI if b != "F"))
    v("1f", "prefisso del punto di controllo per E ed E1 soltanto",
      all(T[b].prefisso_ck == (b in PREFISSO_PRIMA) for b in CONGELATI))
    v("1g", "preparatori: E ed E1 soltanto",
      all(T[b].preparatorio == (b in PREPARATORI_PRIMA) for b in CONGELATI))
    v("1h", "descrizioni di popolazione identiche a `fasi.POPOLAZIONE`",
      all(T[b].descrizione_popolazione == POPOLAZIONE_PRIMA[b]
          for b in POPOLAZIONE_PRIMA))
    v("1i", "descrizioni di corpus identiche a `fasi.CORPUS`",
      all(T[b].descrizione_corpus == CORPUS_PRIMA[b] for b in CORPUS_PRIMA))
    v("1j", "variante come in `cfg_braccio`",
      all(T[b].variante == VARIANTE_PRIMA[b] for b in VARIANTE_PRIMA))
    v("1k", "popolazione come in `cfg_braccio`",
      all(T[b].popolazione == POPOLAZIONE_CFG_PRIMA[b]
          for b in POPOLAZIONE_CFG_PRIMA))
    v("1l", "campionamento come in `cfg_braccio`",
      all(T[b].campionamento == CAMPIONAMENTO_PRIMA[b]
          for b in CAMPIONAMENTO_PRIMA))
    v("1m", "addestrano esattamente C, P, A, R fra i cinque della fase 3",
      tuple(b for b in ("C", "P", "A", "R", "F") if T[b].addestra)
      == ADDESTRANO_PRIMA)
    v("1n", "costo all'inserimento: solo R, come `costo_addestramento`",
      all(T[b].costo_all_inserimento == COSTO_INSERIMENTO_PRIMA[b]
          for b in COSTO_INSERIMENTO_PRIMA))
    v("1o", "attesa delle 24 ore: P, F, R, come `tempo_disponibilita`",
      all(T[b].attende_acquisizione == ATTESA_PRIMA[b] for b in ATTESA_PRIMA))
    v("1p", "corpus per braccio come i costruttori di `esegui_inserimento`",
      all(T[b].corpus == CORPUS_COSTRUTTORE_PRIMA[b]
          for b in CORPUS_COSTRUTTORE_PRIMA))
    v("1q", "rho richiesto da E1 soltanto",
      all(T[b].richiede_rho == (b == "E1") for b in CONGELATI))

    # ------------------------------------------------------------ [2] ----
    print("\n[2] le viste derivate")
    v("2a", "CARICANO contiene i sei di prima e non F",
      all(b in B.CARICANO for b in CARICANO_PRIMA) and "F" not in B.CARICANO,
      str(B.CARICANO))
    v("2b", "PREPARATORI == (E, E1)", B.PREPARATORI == PREPARATORI_PRIMA)
    v("2c", "`proprieta` solleva con il nome per un braccio ignoto",
      _solleva(lambda: B.proprieta("X"), B.BraccioIgnoto))
    v("2d", "`bracci_con` rifiuta una proprieta' inesistente",
      _solleva(lambda: B.bracci_con(colore="rosso"), ValueError))
    v("2e", "ogni riga della tabella e' coerente (nessuna eccezione al "
      "caricamento)", True)
    # canonico.py importa torch: si legge l'albero sintattico, non il modulo
    tc = ast.parse((RADICE / "evoluzione/componente/canonico.py").read_text())
    importa = any(isinstance(n, ast.ImportFrom)
                  and n.module == "evoluzione.componente.bracci"
                  and any(a.name == "CARICANO" for a in n.names)
                  for n in ast.walk(tc))
    ridefinisce = any(isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "CARICANO" for t in n.targets)
        for n in ast.walk(tc))
    v("2f", "`canonico.CARICANO` e' importato dalla tabella, non ridefinito",
      importa and not ridefinisce)

    # ------------------------------------------------------------ [3] ----
    print("\n[3] `fasi` legge dalla tabella")
    from evoluzione.esperimenti import fasi
    v("3a", "fasi.BRACCI == tabella", fasi.BRACCI == tuple(T))
    v("3b", "fasi.POPOLAZIONE e CORPUS coincidono con le righe congelate",
      all(fasi.POPOLAZIONE[b] == POPOLAZIONE_PRIMA[b] and
          fasi.CORPUS[b] == CORPUS_PRIMA[b] for b in POPOLAZIONE_PRIMA))
    d = {b: fasi.descrivi_braccio(b) for b in T}
    v("3c", "`descrivi_braccio` funziona per ogni braccio, E1 e R-orig inclusi",
      all(d[b]["braccio"] == b for b in T)
      and d["F"]["carica_canonico"] is False and d["E1"]["carica_canonico"])
    v("3d", "`descrivi_braccio` solleva per un braccio ignoto",
      _solleva(lambda: fasi.descrivi_braccio("X"), ValueError))
    ini, nuo, ist = [0, 1, 2, 3], [4, 5], [10, 11, 12, 13]
    ok_R = fasi.controlli_A_R("R", ini + nuo, nuo, ist, t0=12)
    ok_Ro = fasi.controlli_A_R("R-orig", ini + nuo, nuo, ist, t0=12)
    ok_Rm = fasi.controlli_A_R("R-mon", ini + nuo, nuo, ist, t0=12)
    v("3e", "controlli di R applicati identici a R-orig e R-mon",
      all(z["conforme"] for z in (ok_R, ok_Ro, ok_Rm)))
    v("3f", "R-orig senza nodi nuovi in popolazione e' rifiutato come R",
      _solleva(lambda: fasi.controlli_A_R("R-orig", ini, nuo, ist, t0=12),
               fasi.PrerequisitoMancante)
      and _solleva(lambda: fasi.controlli_A_R("R", ini, nuo, ist, t0=12),
                   fasi.PrerequisitoMancante))
    v("3g", "A senza storia anteriore a t0 e' rifiutato",
      _solleva(lambda: fasi.controlli_A_R("A", ini + nuo, nuo, ist, t0=5),
               fasi.PrerequisitoMancante))
    v("3h", "C con nodi nuovi in addestramento e' rifiutato",
      _solleva(lambda: fasi.controlli_A_R("C", ini + nuo, nuo, ist, t0=12),
               fasi.PrerequisitoMancante))

    # ------------------------------------------------------------ [4] ----
    print("\n[4] esecutori mancanti, dichiarati")
    src = (RADICE / "evoluzione/esperimenti/addestramento.py").read_text()
    camp_ok = tuple_dopo(src, "camp not in")
    sel_ok = tuple_dopo(src, "politica_ck not in")
    senza = sorted(b for b in T if T[b].addestra and
                   (T[b].campionamento not in camp_ok or
                    T[b].selezione_ck not in sel_ok))
    v("4a", "i bracci senza esecutore sono esattamente quelli di E3",
      senza == ["R-mon", "R-orig"],
      f"campionamenti accettati {camp_ok}, selezioni {sel_ok}; senza "
      f"esecutore: {senza}")

    # ------------------------------------------------------------ [5] ----
    print("\n[5] confronti sul nome del braccio rimasti nel codice")
    rest = confronti_letterali()
    ignoti = [r for r in rest if r not in ECCEZIONI]
    sparite = [e for e in ECCEZIONI if e not in rest]
    v("5a", "nessun confronto letterale fuori dalle eccezioni motivate",
      not ignoti, "\n        ".join(f"{f}: {r}" for f, r in ignoti))
    v("5b", "le eccezioni elencate esistono ancora (altrimenti si tolgono)",
      not sparite, "\n        ".join(f"{f}: {r}" for f, r in sparite))
    for f, r in rest:
        print(f"        {f}: {r}\n            -> {ECCEZIONI.get((f, r), '?')}")

    print("\n" + "=" * 80)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 80)
    return 0 if all(ESITI) else 1


def _solleva(fn, ecc) -> bool:
    try:
        fn()
    except ecc:
        return True
    except Exception:                                        # noqa: BLE001
        return False
    return False


if __name__ == "__main__":
    raise SystemExit(main())
