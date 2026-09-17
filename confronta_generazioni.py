#!/usr/bin/env python3
"""
Due casi che il censimento non decide da solo.
===============================================
NON MODIFICA NULLA. Risponde a due domande che richiedono di CONFRONTARE i file
fra loro, cosa che una classificazione per firma non puo' fare.

CASO 1 — COPIE IN PIU' CARTELLE. Alcune famiglie stanno sia in `models/` sia in
`results/componenti/` (per esempio `sparse_geoF_*`). Il confronto va fatto sul
CONTENUTO e non sulla data: una copia puo' avere data diversa per il solo fatto
di essere stata copiata. Lo script confronta il digest del contenuto normalizzato
— ordinato per colonne e senza indice — cosi' due file identici nella sostanza
risultano identici anche se differiscono per ordine delle righe.

CASO 2 — GENERAZIONI DELLA STESSA CAMPAGNA. `classify_*` e `sparse_*` senza
prefisso sono la campagna originale a tre semi, precedente sia a `camp_*` sia a
`fix_*`. Il nome non basta a deciderlo, perche' `classify_t4cmad_g075_s0` e' una
verifica di validita' mentre `classify_t4cmad_s0` e' la campagna base.

Lo script distingue i due casi con una regola sul SUFFISSO del contesto: se il
contesto e' uno dei sei canonici, e' campagna base; se e' una variante
(`_g0\\d+`, `_p85tr`), e' una verifica di validita' e va tenuta comunque.

E per la campagna base riporta, per ciascun contesto e seme, le tre generazioni
affiancate con data e valore, cosi' che la decisione poggi su un confronto e non
su un'impressione. ATTENZIONE: se le tre generazioni danno valori diversi sugli
stessi semi, la differenza NON e' rumore di inizializzazione — a parita' di seme
lo stesso script deve dare lo stesso risultato — ed e' il segnale che qualcosa e'
cambiato fra le esecuzioni.

Uso (dalla radice OR3/):

    poetry run python confronta_generazioni.py
    poetry run python confronta_generazioni.py --famiglia sparse_geoF
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import re
from collections import defaultdict

import pandas as pd

CANONICI = ("d8_2024", "d15_2024", "d8_2023", "t4cmad", "t4clon", "t4cmel")
GENERAZIONI = [
    ("classify", ["classify_{c}_s{s}.csv", "camp_classify_{c}_s{s}.csv",
                  "fix_classify_{c}_s{s}.csv", "prec_classify_{c}_s{s}.csv"]),
    ("sparse", ["sparse_{c}_s{s}.csv", "camp_sparse_{c}_s{s}.csv",
                "fix_sparse_{c}_s{s}.csv"]),
]


METRICHE = ("wCE", "macroF1", "red_recall", "red_prec", "MAE_r", "RMSE_r", "acc")
CHIAVI = ("model", "mode", "horizon", "split", "history", "subset", "epoca")


def digest(p: Path) -> str:
    """Digest del contenuto normalizzato: colonne ordinate, righe ordinate,
    indice scartato. Insensibile all'ordine in cui le righe sono state scritte."""
    try:
        d = pd.read_csv(p)
    except Exception:
        return "ILLEGGIBILE"
    d = d.reindex(sorted(d.columns), axis=1)
    d = d.sort_values(list(d.columns)).reset_index(drop=True)
    return hashlib.sha256(d.to_csv(index=False).encode()).hexdigest()[:12]


def confronta(a: Path, b: Path):
    """Confronta due CSV distinguendo tre esiti, che il solo digest confonde.

    Un digest diverso NON basta a dire che i due file vengano da esecuzioni
    diverse: due file possono contenere gli stessi identici numeri e differire
    per colonne aggiunte, ordine o tipi. E' esattamente il caso di
    `camp_classify` e `fix_classify`, dove le entropie coincidono a nove
    decimali e la seconda ha in piu' `city`, `config`, `context` e `red_prec`.

    Restituisce (esito, scarto massimo sulle metriche comuni, nota):

      IDENTICI      stessi numeri, stesse colonne. Copia o riesecuzione
                    perfettamente riproducibile.
      ARRICCHITO    stessi numeri, colonne diverse. NON e' una riesecuzione:
                    su MPS una riesecuzione vera non da' valori bit-identici.
      RIESEGUITO    numeri diversi entro l'ordine del non determinismo (1e-6
                    ÷ 1e-3). E' una riesecuzione vera dello stesso codice.
      DIVERSO       numeri diversi oltre quell'ordine: e' cambiato qualcosa nel
                    calcolo — lo script, i dati o l'adiacenza.
    """
    try:
        A, B = pd.read_csv(a), pd.read_csv(b)
    except Exception as e:
        return "ILLEGGIBILE", float("nan"), str(e)[:40]
    solo_a = sorted(set(A.columns) - set(B.columns))
    solo_b = sorted(set(B.columns) - set(A.columns))
    k = [c for c in CHIAVI if c in A.columns and c in B.columns]
    met = [c for c in METRICHE if c in A.columns and c in B.columns]
    if not met:
        return "NON CONFRONTABILE", float("nan"), "nessuna metrica in comune"
    if not k:
        return "NON CONFRONTABILE", float("nan"), "nessuna chiave in comune"
    m = A.merge(B, on=k, suffixes=("_a", "_b"))
    if not len(m):
        return "NON CONFRONTABILE", float("nan"), "nessuna riga appaiabile"
    scarto = max(float((m[f"{c}_a"] - m[f"{c}_b"]).abs().max()) for c in met)
    nota = ""
    if solo_a or solo_b:
        nota = ("+" + ",".join(solo_b) if solo_b else "") + \
               (" -" + ",".join(solo_a) if solo_a else "")
    if scarto == 0.0:
        return ("IDENTICI" if not nota else "ARRICCHITO"), scarto, nota.strip()
    if scarto < 1e-3:
        return "RIESEGUITO", scarto, nota.strip()
    return "DIVERSO", scarto, nota.strip()


def data(p: Path) -> str:
    return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")


def caso_copie(radice: Path, famiglia: str) -> None:
    print("=" * 94)
    print(f"CASO 1 — copie della stessa famiglia in cartelle diverse: {famiglia}*")
    print("=" * 94)
    trovati = defaultdict(list)
    for p in radice.rglob(f"{famiglia}*"):
        if p.is_file() and p.suffix == ".csv" and "_archivio" not in p.parts:
            trovati[p.name].append(p)
    if not trovati:
        print(f"   nessun file {famiglia}* trovato")
        return
    identici = diversi = unici = 0
    for nome in sorted(trovati):
        f = sorted(trovati[nome])
        if len(f) == 1:
            unici += 1
            continue
        dig = {str(p.relative_to(radice)): digest(p) for p in f}
        uguali = len(set(dig.values())) == 1
        identici += uguali
        diversi += not uguali
        print(f"\n   {nome}  ->  {'IDENTICHE' if uguali else 'DIVERSE'}")
        for p in f:
            print(f"      {data(p)}  {dig[str(p.relative_to(radice))]}  "
                  f"{p.relative_to(radice)}")
    print(f"\n   riepilogo: {identici} nomi con copie identiche, "
          f"{diversi} con copie diverse, {unici} presenti una volta sola")
    if identici and not diversi:
        print("   Tutte le copie sono identiche nel contenuto: se ne puo' tenere una.")
        print("   Conservare quella sotto `results/`, che e' la cartella dei risultati")
        print("   consolidati; `models/` e' la cartella di lavoro degli script.")
    if diversi:
        print("   ATTENZIONE: alcune copie DIFFERISCONO nel contenuto. Non sono")
        print("   duplicati ma esecuzioni distinte, e vanno tenute entrambe finche'")
        print("   non si stabilisce quale alimenta le tabelle.")


def caso_generazioni(radice: Path, semi: int) -> None:
    print("\n" + "=" * 94)
    print("CASO 2 — generazioni successive della stessa campagna")
    print("=" * 94)
    print("La colonna `contesto` distingue i due usi dello stesso prefisso:")
    print("   contesto canonico  -> campagna base, confrontabile fra generazioni")
    print("   contesto variante  -> verifica di validita' (§8.7.2), da tenere comunque\n")

    for etichetta, schemi in GENERAZIONI:
        print("-" * 94)
        print(f"famiglia: {etichetta}")
        print("-" * 94)
        varianti = sorted({p.name for p in radice.rglob(f"{etichetta}_*.csv")
                           if re.search(r"_(g0\d+|p85tr)_s\d+\.csv$", p.name)})
        if varianti:
            print(f"   verifiche di validita' ({len(varianti)} file): "
                  f"{', '.join(sorted({re.sub(r'_s\d+.csv$', '', v) for v in varianti}))}")
            print("   -> destinazione `validita`, non confrontabili con la campagna base\n")

        nomi = [s.split("_{")[0] for s in schemi]
        print(f"   {'contesto':10s} {'seme':>4}  " +
              "  ".join(f"{n:>16}" for n in nomi))
        esiti = defaultdict(list)
        note = {}
        for c in CANONICI:
            for s in range(semi):
                celle, trovati = [], {}
                for sch, n in zip(schemi, nomi):
                    f = list(radice.rglob(sch.format(c=c, s=s)))
                    if not f:
                        celle.append(f"{'—':>16}")
                        continue
                    trovati[n] = f[0]
                    try:
                        d = pd.read_csv(f[0])
                        col = "wCE" if "wCE" in d.columns else d.columns[-1]
                        celle.append(f"{data(f[0])[:5]} {d[col].mean():9.4f}")
                    except Exception:
                        celle.append(f"{data(f[0])[:5]}  illegg.")
                if len(trovati) > 1:
                    print(f"   {c:10s} {s:4d}  " + "  ".join(f"{x:>16}" for x in celle))
                # confronto a piena precisione fra generazioni consecutive
                v = list(trovati.items())
                for (na, pa), (nb, pb) in zip(v, v[1:]):
                    es, sc, nota = confronta(pa, pb)
                    esiti[(na, nb, es)].append((c, s, sc))
                    if nota:
                        note[(na, nb)] = nota

        if esiti:
            print(f"\n   {'confronto':30s} {'esito':16s} {'casi':>5} {'scarto max':>12}"
                  f"  contesti")
            for (na, nb, es), casi in sorted(esiti.items()):
                ctx = sorted({c for c, _, _ in casi})
                sc = max(x for _, _, x in casi if x == x) if casi else float("nan")
                print(f"   {na + ' -> ' + nb:30s} {es:16s} {len(casi):5d} {sc:12.9f}"
                      f"  {', '.join(ctx)[:38]}")
                if note.get((na, nb)):
                    print(f"   {'':30s} {'':16s} colonne: {note[(na, nb)][:52]}")
        print()

    print("Come decidere, secondo l'esito del confronto a piena precisione:")
    print()
    print("  IDENTICI    stessi numeri, stesse colonne -> copia: tenerne una.")
    print("  ARRICCHITO  stessi numeri, colonne in piu' -> NON e' una riesecuzione,")
    print("              perche' su MPS una riesecuzione vera non da' valori")
    print("              bit-identici. Tenere la versione con piu' colonne e")
    print("              archiviare l'altra come STORICA, non come superata.")
    print("  RIESEGUITO  numeri diversi sotto 1e-3 -> riesecuzione dello stesso")
    print("              codice: la differenza e' il non determinismo di MPS.")
    print("  DIVERSO     numeri diversi sopra 1e-3 -> e' cambiato qualcosa nel")
    print("              calcolo. La piu' recente e' valida, la precedente va")
    print("              SEGREGATA e non cancellata: documenta il cambiamento.")
    print()
    print("Attenzione a non leggere ARRICCHITO come un difetto. Se la campagna nuova")
    print("gira su bracci che non consumano cio' che e' stato corretto, valori identici")
    print("sono l'esito ATTESO: e' il caso di `--modes none,adaptive`, dove ne' il")
    print("braccio senza grafo ne' quello adattivo toccano l'adiacenza fornita.")


def main() -> int:
    ap = argparse.ArgumentParser(description="confronto fra copie e generazioni")
    ap.add_argument("--radice", type=Path, default=Path("."))
    ap.add_argument("--famiglia", default="sparse_geoF",
                    help="prefisso della famiglia da confrontare nel caso 1")
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--casi", nargs="*", default=["copie", "generazioni"])
    a = ap.parse_args()

    radice = a.radice.resolve()
    if "copie" in a.casi:
        caso_copie(radice, a.famiglia)
    if "generazioni" in a.casi:
        caso_generazioni(radice, a.semi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
