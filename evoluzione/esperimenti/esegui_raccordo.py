#!/usr/bin/env python3
"""
Esecutore del raccordo: 54 esecuzioni, con la regola dei fallimenti approvata.
==============================================================================
3 contesti x 3 partizioni x 3 inizializzazioni x 2 varianti.

LE DUE CATEGORIE DI FALLIMENTO, trattate diversamente.

  TECNICO RECUPERABILE — interruzione, ingresso/uscita, ambiente.
      Tre tentativi complessivi, stesso seme, dati, configurazione e codice.
      Ogni tentativo registrato. Si usa il PRIMO completato e valido, non quello
      con la prestazione migliore.

  DEL METODO — perdita non finita, divergenza, risorse superate in modo
      riproducibile.
      E' un esito da RIPORTARE, non un risultato da cancellare ripetendo. Se una
      ripetizione riesce, si riportano ENTRAMBE: il backend puo' non essere
      deterministico a seme fissato, sicche' ripetere fino al successo
      selezionerebbe anche senza cambiare seme.

NON SONO FALLIMENTI una prestazione scarsa, un arresto anticipato regolare, il
mancato raggiungimento della non inferiorita'.

NESSUNA MODIFICA IMPLICITA durante i tentativi: dimensione del lotto, precisione,
troncamento del gradiente ed epoche restano quelli dichiarati. **Un errore nel
codice sospende le esecuzioni interessate** — nuova versione registrata e
valutazione di cosa rigenerare — e non e' un nuovo tentativo.

COPPIE INCOMPLETE. Nessun seme sostitutivo, nessuna imputazione. Una coppia e'
utilizzabile solo se ENTRAMBE le varianti hanno un risultato valido; le altre si
riportano nella matrice, con i tassi di completamento distinti per variante.

Uso (dalla radice OR3/):

    poetry run python evoluzione/esperimenti/esegui_raccordo.py --piano
    poetry run python evoluzione/esperimenti/esegui_raccordo.py --contesto Madrid
    poetry run python evoluzione/esperimenti/esegui_raccordo.py
"""
import argparse
import json
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import (  # noqa: E402
    SCHEMA_VERSIONE, SCHEMI_T4C, VERSIONE_IMPLEMENTAZIONE)
from evoluzione.componente.registro import Registro  # noqa: E402
from evoluzione.esperimenti.addestramento import addestra_una  # noqa: E402

CONTESTI = ("Madrid", "Londra", "Melbourne")
VARIANTI = ("LEGACY", "BASE-CORRECTED")
PARTIZIONI = (0, 1, 2)
INIZIALIZZAZIONI = (0, 1, 2)
# semi SEPARATI: partizione e inizializzazione non condividono la sequenza
SEME_PARTIZIONE = {p: 1000 + 37 * p for p in PARTIZIONI}
SEME_INIZIALIZZAZIONE = {s: 7 + 11 * s for s in INIZIALIZZAZIONI}
TENTATIVI_MAX = 3            # complessivi, per i soli fallimenti tecnici

COMPLETATA = "completata"
TECNICO = "fallimento_tecnico"
METODO = "fallimento_metodo"
DIFETTO = "difetto_del_codice"     # sospende, non e' un tentativo

# eccezioni che indicano un fallimento TECNICO, quindi ripetibile
TECNICHE = (OSError, IOError, TimeoutError, ConnectionError, InterruptedError)


# UNA sola definizione, in `addestramento`: due classi omonime non sarebbero
# riconosciute da `isinstance`, e il fallimento del metodo sospenderebbe le
# esecuzioni invece di essere registrato.
from evoluzione.esperimenti.addestramento import FallimentoMetodo  # noqa: E402


@dataclass
class Tentativo:
    numero: int
    istante: str
    esito: str
    causa: str = ""
    durata_s: float = 0.0


@dataclass
class Esecuzione:
    contesto: str
    partizione: int
    inizializzazione: int
    variante: str
    tentativi: list = field(default_factory=list)
    esito: str = "non_avviata"
    run_id: str = ""
    uscita: str = ""

    @property
    def chiave(self):
        return (self.contesto, self.partizione, self.inizializzazione,
                self.variante)

    def as_dict(self):
        return {"contesto": self.contesto, "partizione": self.partizione,
                "inizializzazione": self.inizializzazione,
                "variante": self.variante, "esito": self.esito,
                "run_id": self.run_id, "uscita": self.uscita,
                "tentativi": [t.__dict__ for t in self.tentativi]}


def classifica(exc) -> str:
    """Tecnico o del metodo. La distinzione decide se ripetere."""
    if isinstance(exc, FallimentoMetodo):
        return METODO
    if isinstance(exc, TECNICHE):
        return TECNICO
    m = str(exc).lower()
    if "nan" in m or "inf" in m or "diverg" in m:
        return METODO
    # ESAURIMENTO DELLE RISORSE richieste dalla configurazione: e' del METODO,
    # perche' riproducibile — la configurazione non entra in memoria.
    if "out of memory" in m or "insufficient memory" in m or "oom" in m:
        return METODO
    # INDISPONIBILITA' TEMPORANEA dell'acceleratore: e' tecnica. Non ogni errore
    # dell'acceleratore e' recuperabile, e la distinzione non si fa dal nome del
    # dispositivo ma dalla natura del guasto.
    if any(k in m for k in ("device not available", "device unavailable",
                            "failed to initialize", "driver", "timeout",
                            "connection reset")):
        return TECNICO
    # ogni altra eccezione e' un DIFETTO DEL CODICE: sospende le esecuzioni
    # interessate, e va trattata con una nuova versione registrata — non e' un
    # nuovo tentativo. Si restituisce l'esito, senza `raise` nudo: quello
    # funzionerebbe solo dentro un blocco `except` e renderebbe la funzione
    # inutilizzabile altrove, collaudi compresi.
    return DIFETTO


def esegui_una(E: Esecuzione, addestra, cfg, radice: Path) -> Esecuzione:
    """Applica la regola dei tentativi. `addestra` fa il lavoro vero."""
    import time
    for n in range(1, TENTATIVI_MAX + 1):
        t0 = time.time()
        reg = Registro.avvia(f"{cfg.get('etichetta', 'raccordo')}/{E.variante}",
                             note=f"{E.contesto} p{E.partizione} "
                                  f"s{E.inizializzazione} tentativo {n}",
                             radice=radice / "registro")
        reg.configurazione({
            **cfg, "contesto": E.contesto, "partizione": E.partizione,
            "inizializzazione": E.inizializzazione, "variante": E.variante,
            "tentativo": n, "schema_version": SCHEMA_VERSIONE,
            "implementation_version": VERSIONE_IMPLEMENTAZIONE})
        # GENERATORI DISTINTI, non soltanto numeri diversi. E ogni variante li
        # REINIZIALIZZA: la seconda non eredita lo stato consumato dalla prima.
        gen = {"partizione": np.random.default_rng(
                   SEME_PARTIZIONE[E.partizione]),
               "inizializzazione": np.random.default_rng(
                   SEME_INIZIALIZZAZIONE[E.inizializzazione])}
        reg.semi(partizione=SEME_PARTIZIONE[E.partizione],
                 inizializzazione=SEME_INIZIALIZZAZIONE[E.inizializzazione],
                 generatori="distinti, reinizializzati per variante")
        try:
            uscita = addestra(E, reg, cfg, gen)
            reg.uscita(uscita).completa()
            E.tentativi.append(Tentativo(n, datetime.now(timezone.utc).isoformat(),
                                         COMPLETATA, durata_s=time.time() - t0))
            E.esito, E.run_id, E.uscita = COMPLETATA, reg.run_id, str(uscita)
            # si usa il PRIMO completato e valido, non il migliore
            return E
        except Exception as exc:                       # noqa: BLE001
            tipo = classifica(exc)
            causa = f"{type(exc).__name__}: {exc}"[:300]
            reg.evento(f"{tipo}: {causa}")
            reg.completa(tipo)
            if tipo == DIFETTO:
                E.esito = DIFETTO
                E.tentativi.append(Tentativo(
                    n, datetime.now(timezone.utc).isoformat(), DIFETTO, causa,
                    time.time() - t0))
                raise      # sospende le esecuzioni: non e' un tentativo
            E.tentativi.append(Tentativo(n, datetime.now(timezone.utc).isoformat(),
                                         tipo, causa, time.time() - t0))
            # gli artefatti del tentativo fallito NON restano fra quelli validi
            _sposta_falliti(radice, E, n)
            if tipo == METODO:
                # NON si ripete per ottenere un risultato favorevole: e' un esito
                E.esito = METODO
                return E
            if n == TENTATIVI_MAX:
                E.esito = TECNICO
                return E
            print(f"       tentativo {n} fallito ({tipo}): {causa[:90]}")
    return E


def gia_completate(out: Path) -> dict:
    """Le esecuzioni gia' completate, dalla matrice precedente.

    Si riprende SOLO cio' che e' `completata`: un fallimento tecnico esaurito o
    del metodo resta tale, e ritentarlo automaticamente alla ripresa
    aggirerebbe la regola dei tentativi.
    """
    f = out / "matrice.json"
    if not f.exists():
        return {}
    try:
        d = json.loads(f.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    fuori = {}
    for e in d.get("esecuzioni", []):
        if e.get("esito") == COMPLETATA:
            fuori[(e["contesto"], e["partizione"], e["inizializzazione"],
                   e["variante"])] = e
    return fuori


def _sposta_falliti(radice: Path, E, n: int):
    """Sposta i residui di un tentativo fallito in una cartella separata.

    Un punto di controllo parziale accanto a quelli validi verrebbe raccolto
    dall'analisi come se fosse buono.
    """
    base = radice / "raccordo"
    dest = base / "tentativi_falliti"
    radice_nome = (f"{E.contesto}_p{E.partizione}_s{E.inizializzazione}_"
                   f"{E.variante}")
    mossi = []
    for pref in ("ck_", "pred_"):
        for f in base.glob(f"{pref}{radice_nome}.*"):
            dest.mkdir(parents=True, exist_ok=True)
            g = dest / f"{f.stem}__tentativo{n}{f.suffix}"
            try:
                f.replace(g)
                mossi.append(g.name)
            except OSError:
                pass
    return mossi


def piano():
    """L'ordine approvato, fissato PRIMA del lancio e non modificabile dopo.

        partizione -> inizializzazione -> contesti INTERCALATI -> due varianti
        adiacenti, con la prima ALTERNATA

    Le coppie restano adiacenti, sicche' un'interruzione rompe al piu' una
    coppia anziche' una variante intera. I contesti ruotano fra blocchi, sicche'
    una lunga interruzione non si concentra sistematicamente su una citta'. Quale
    variante vada per prima alterna in modo prefissato e approssimativamente
    bilanciato: se una fosse sempre prima, un'interruzione la colpirebbe sempre
    meno.
    """
    fuori = []
    for p in PARTIZIONI:
        for s in INIZIALIZZAZIONI:
            r = (p * len(INIZIALIZZAZIONI) + s) % len(CONTESTI)
            contesti = CONTESTI[r:] + CONTESTI[:r]          # rotazione
            for i, c in enumerate(contesti):
                inverti = (p + s + i) % 2 == 1
                vv = VARIANTI[::-1] if inverti else VARIANTI
                for v in vv:
                    fuori.append(Esecuzione(c, p, s, v))
    return fuori


def salva_ordine(P, out: Path):
    """L'ordine completo, salvato PRIMA del lancio."""
    out.mkdir(parents=True, exist_ok=True)
    f = out / "ordine_esecuzioni.json"
    f.write_text(json.dumps(
        {"istante": datetime.now(timezone.utc).isoformat(),
         "regola": ("partizione -> inizializzazione -> contesti intercalati "
                    "(rotazione) -> due varianti adiacenti, prima alternata"),
         "avvertenza": "NON modificabile in funzione dei risultati",
         "ordine": [{"n": i, "contesto": e.contesto, "partizione": e.partizione,
                     "inizializzazione": e.inizializzazione,
                     "variante": e.variante} for i, e in enumerate(P, 1)]},
        indent=2, ensure_ascii=False))
    return f


def matrice(esecuzioni, out: Path):
    """La MATRICE COMPLETA di esecuzioni e fallimenti, e le coppie utilizzabili."""
    per = {e.chiave: e for e in esecuzioni}
    print("\n" + "=" * 80)
    print("MATRICE DELLE ESECUZIONI")
    print("=" * 80)
    simbolo = {COMPLETATA: "·", TECNICO: "T", METODO: "M",
               DIFETTO: "X", "non_avviata": " "}
    print(f"  {'contesto':11s} {'p/s':>5}  {'LEGACY':>8} {'BASE-CORR':>10}   coppia")
    coppie_ok = coppie_no = 0
    # solo i contesti NEL PERIMETRO: una riga mai pianificata non e' incompleta,
    # e' fuori perimetro — confonderle gonfierebbe i fallimenti
    nel_perimetro = sorted({e.contesto for e in esecuzioni}, key=CONTESTI.index)
    for c in nel_perimetro:
        for p in PARTIZIONI:
            for s in INIZIALIZZAZIONI:
                a = per.get((c, p, s, "LEGACY"))
                b = per.get((c, p, s, "BASE-CORRECTED"))
                if a is None and b is None:
                    continue
                ea = a.esito if a else "non_avviata"
                eb = b.esito if b else "non_avviata"
                ok = ea == COMPLETATA and eb == COMPLETATA
                coppie_ok += ok; coppie_no += not ok
                print(f"  {c:11s} {p}/{s:<3}  {simbolo[ea]:>8} {simbolo[eb]:>10}"
                      f"   {'utilizzabile' if ok else 'INCOMPLETA'}")
    fuori = [c for c in CONTESTI if c not in nel_perimetro]
    if fuori:
        print(f"\n  fuori perimetro, non pianificati: {fuori}")
    print(f"\n  legenda: · completata | T tecnico | M del metodo | "
          f"X difetto del codice")

    # tassi di completamento DISTINTI per variante
    print(f"\n  {'variante':16s} {'completate':>11} {'tecnici':>9} {'metodo':>8}"
          f" {'tasso':>8}")
    for v in VARIANTI:
        q = [e for e in esecuzioni if e.variante == v]
        c_ = sum(e.esito == COMPLETATA for e in q)
        t_ = sum(e.esito == TECNICO for e in q)
        m_ = sum(e.esito == METODO for e in q)
        print(f"  {v:16s} {c_:11d} {t_:9d} {m_:8d} {c_/max(len(q),1):8.1%}")

    print(f"\n  coppie utilizzabili: {coppie_ok}/{coppie_ok + coppie_no}")
    if coppie_no:
        print("  ATTENZIONE: coppie incomplete. L'analisi e' CONDIZIONATA alle")
        print("  esecuzioni completate, mantiene uguale peso alle partizioni")
        print("  rappresentate, e NON ricalcola una media piatta sui superstiti.")
    if any(e.esito == METODO for e in esecuzioni):
        print("\n  UN FALLIMENTO DEL METODO e' presente: impedisce di assumere che")
        print("  il verdetto sulle sole esecuzioni riuscite valga per l'intera")
        print("  configurazione prevista.")

    out.mkdir(parents=True, exist_ok=True)
    (out / "matrice.json").write_text(json.dumps(
        {"esecuzioni": [e.as_dict() for e in esecuzioni],
         "coppie_utilizzabili": coppie_ok, "coppie_incomplete": coppie_no,
         "contesti_nel_perimetro": nel_perimetro,
         "schema_version": SCHEMA_VERSIONE,
         "implementation_version": VERSIONE_IMPLEMENTAZIONE,
         "istante": datetime.now(timezone.utc).isoformat()},
        indent=2, ensure_ascii=False))
    print(f"\n  matrice in {out / 'matrice.json'}")
    return coppie_ok, coppie_no


def main() -> int:
    ap = argparse.ArgumentParser(description="esecutore del raccordo")
    ap.add_argument("--contesto", nargs="*", default=list(CONTESTI))
    ap.add_argument("--piano", action="store_true",
                    help="mostra il piano e si ferma, senza addestrare")
    ap.add_argument("--epoche", type=int, default=35)
    ap.add_argument("--lotto", type=int, default=32)
    ap.add_argument("--passo", type=float, default=1e-3)
    ap.add_argument("--pazienza", type=int, default=8)
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--riparti", action="store_true",
                    help="ignora la matrice precedente e rifa' tutto")
    ap.add_argument("--etichetta", default="raccordo",
                    help="identificativo della campagna: il collaudo "
                         "dell'integrazione ne usa uno DISTINTO, e non entra "
                         "nelle 54 esecuzioni")
    a = ap.parse_args()

    cfg = {"epoche": a.epoche, "lotto": a.lotto, "passo": a.passo,
           "pazienza": a.pazienza,
           # DUE FINESTRE DISTINTE, da non confondere nel manifesto
           "storia_descrittore_passi": 96,      # ventiquattro ore
           "finestra_dinamica_passi": 12,       # tre ore
           "orizzonti": [1, 2, 4, 8], "sorgente": "traffic4cast",
           "etichetta": a.etichetta}
    P = [e for e in piano() if e.contesto in a.contesto]

    print("=" * 80)
    print(f"RACCORDO LEGACY ↔ BASE-CORRECTED — {len(P)} esecuzioni")
    print("=" * 80)
    print(f"  contesti {a.contesto} | partizioni {list(PARTIZIONI)} | "
          f"inizializzazioni {list(INIZIALIZZAZIONI)}")
    print(f"  semi di PARTIZIONE      {SEME_PARTIZIONE}")
    print(f"  semi di INIZIALIZZAZIONE {SEME_INIZIALIZZAZIONE}")
    print(f"  dimensioni: " + ", ".join(
        f"{v} {len(SCHEMI_T4C[v]['statistiche']) + len(SCHEMI_T4C[v]['disponibilita'])}"
        for v in VARIANTI))
    print(f"  schema {SCHEMA_VERSIONE} | implementazione {VERSIONE_IMPLEMENTAZIONE}")
    print(f"  iperparametri: {cfg}")
    print(f"\n  regola dei tentativi: {TENTATIVI_MAX} complessivi per i "
          f"fallimenti TECNICI, stesso seme e configurazione.")
    print(f"  I fallimenti del METODO sono esiti da riportare, non risultati da")
    print(f"  cancellare ripetendo.")

    if a.piano:
        print(f"\n  --piano: nessuna esecuzione avviata.")
        for e in P[:6]:
            print(f"     {e.contesto:11s} p{e.partizione} s{e.inizializzazione} "
                  f"{e.variante}")
        print(f"     … e altre {max(len(P) - 6, 0)}")
        return 0

    def addestra(E, reg, cfg, gen):
        """Il lavoro vero, in `addestramento.py`.

        Solleva `FallimentoMetodo` su perdita non finita o divergenza; lascia
        propagare le eccezioni tecniche perche' la regola dei tentativi le
        riconosca; ogni altra le sospende.
        """
        return addestra_una(E, reg, cfg, gen, a.out)

    fatte = gia_completate(a.out / "raccordo") if not a.riparti else {}
    if fatte:
        print(f"\n  RIPRESA: {len(fatte)} esecuzioni gia' completate, non "
              f"ripetute.")
        print(f"  I fallimenti NON si riprendono automaticamente: ritentarli "
              f"aggirerebbe la regola dei tentativi.")
        for E in P:
            if E.chiave in fatte:
                d = fatte[E.chiave]
                E.esito, E.run_id = COMPLETATA, d.get("run_id", "")
                E.uscita = d.get("uscita", "")
                E.tentativi = [Tentativo(**x) for x in d.get("tentativi", [])]

    f = salva_ordine(P, a.out / "raccordo")
    print(f"\n  ordine salvato in {f} — NON modificabile in funzione dei "
          f"risultati\n")
    for i, E in enumerate(P, 1):
        if E.esito == COMPLETATA:
            continue                      # ripresa: gia' fatta
        print(f"  [{i:2d}/{len(P)}] {E.contesto:11s} p{E.partizione} "
              f"s{E.inizializzazione} {E.variante:16s}", end=" ", flush=True)
        try:
            esegui_una(E, addestra, cfg, a.out)
            print(f"-> {E.esito}")
        except NotImplementedError as exc:
            print(f"-> SOSPESA: {exc}")
            break
        except Exception:                               # noqa: BLE001
            print("-> ERRORE NEL CODICE: esecuzioni SOSPESE")
            traceback.print_exc()
            break

    matrice(P, a.out / "raccordo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
