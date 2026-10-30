#!/usr/bin/env python3
"""
Priore storico CALIBRATO nel regime severo.
============================================
Aggiunge a `gomo_sparse.py` la variante calibrata del priore, che oggi non e'
calcolata: la riga che lo produce non applica la mappa di calibrazione, e i suoi
dump sono esplicitamente esclusi dal salvataggio.

PERCHE' NON BASTA UNA RIELABORAZIONE. La calibrazione `p ∝ w·f` richiede la
distribuzione predetta, e `gomo_sparse.py` alla riga del salvataggio esclude il
priore con una condizione esplicita. Le probabilita' non esistono quindi su
disco per alcun contesto, e la variante calibrata va prodotta durante
l'esecuzione.

CHE COSA FA LA PATCH. Aggiunge una riga di risultato accanto a quella esistente,
con il priore calibrato secondo la stessa mappa usata per gli interpolatori. Non
tocca la riga non calibrata, che resta per confronto, ne' il resto del calcolo.

Uso (dalla radice OR3/):

    poetry run python patch_priore_calibrato.py --verifica     # non modifica
    poetry run python patch_priore_calibrato.py                # applica
    poetry run python patch_priore_calibrato.py --ripristina   # annulla
"""
from pathlib import Path
import argparse
import re
import shutil

SORGENTE = Path("models/gomo_sparse.py")

# La riga che produce il priore non calibrato. Si cerca per SCHEMA e non per
# numero di riga, perche' il file puo' essere cambiato da quando e' stato letto.
ANCORA = re.compile(
    r'^(?P<ind>\s*)rows\.append\(\("hist_prior",\s*HL\[h\],\s*\*scores\((?P<args>[^)]*)\)\)\)',
    re.M)

AGGIUNTA = '''{ind}# PRIORE CALIBRATO. La riga sopra produce il priore grezzo, che nel regime
{ind}# severo risulta peggiore del predittore uniforme su cinque contesti su sei.
{ind}# La calibrazione applica la medesima mappa degli interpolatori — la
{ind}# probabilita' e' riponderata per il peso di classe e rinormalizzata — ed e'
{ind}# quella descritta in §8.1 per il compito denso, qui estesa al regime severo.
{ind}if args.calib_mode == "weighted":
{ind}    # Pt ha forma (tempo, nodi, 3): i pesi vanno allineati all'ULTIMO asse e
{ind}    # la rinormalizzazione fatta su quello, come alle righe degli interpolatori.
{ind}    # Con `Wnp[None, :]` e `sum(1)` si sommerebbe sui nodi anziche' sulle classi.
{ind}    _Pc = {P} * Wnp[None, None, :]
{ind}    _Pc = _Pc / np.maximum(_Pc.sum(-1, keepdims=True), 1e-12)
{ind}    rows.append(("hist_prior_cal", HL[h], *scores(_Pc, {Y})))
'''


def trova(t):
    m = ANCORA.search(t)
    if not m:
        return None
    args = [x.strip() for x in m.group("args").split(",")]
    if len(args) < 2:
        return None
    return m, args[0], args[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="priore calibrato nel regime severo")
    ap.add_argument("--sorgente", type=Path, default=SORGENTE)
    ap.add_argument("--verifica", action="store_true")
    ap.add_argument("--ripristina", action="store_true")
    a = ap.parse_args()

    if not a.sorgente.exists():
        print(f"sorgente non trovato: {a.sorgente}")
        return 1
    bak = a.sorgente.with_suffix(".py.pre_priorecal")

    if a.ripristina:
        if not bak.exists():
            print("nessuna copia da ripristinare")
            return 1
        shutil.copy2(bak, a.sorgente)
        print(f"ripristinato da {bak.name}")
        return 0

    t = a.sorgente.read_text()
    if "hist_prior_cal" in t:
        print("patch gia' applicata")
        return 0

    r = trova(t)
    if r is None:
        print("SCHEMA NON RICONOSCIUTO: la riga che produce il priore non")
        print("corrisponde a quella attesa. Righe candidate nel sorgente:")
        for i, l in enumerate(t.split("\n"), 1):
            if "hist_prior" in l:
                print(f"  {i:5d}  {l.strip()[:88]}")
        return 1
    m, P, Y = r
    ind = m.group("ind")

    print("riga riconosciuta:")
    print(f"  {m.group(0).strip()}")
    print(f"\n  distribuzione predetta: {P}")
    print(f"  bersagli:               {Y}")
    print("\nverifiche di contesto:")
    # `calib_mode` compare come `--calib-mode` fra gli argomenti e come
    # `args.calib_mode` nell'uso: si cerca la radice, non una delle due forme
    for nome, cerca, atteso in (("Wnp", "Wnp", "vettore dei pesi di classe"),
                                ("calib_mode", "calib-mode", "opzione di calibrazione"),
                                ("numpy", "np.", "numpy importato")):
        print(f"  {nome:12s} {'presente' if cerca in t else 'ASSENTE'}   ({atteso})")
    if "Wnp" not in t or "calib-mode" not in t:
        print("\nUno degli elementi richiesti non compare: non applico.")
        return 1

    if a.verifica:
        print("\n--verifica: nessuna modifica applicata.")
        print("Rilanciare senza l'opzione per applicare.")
        return 0

    shutil.copy2(a.sorgente, bak)
    nuovo = m.group(0) + "\n" + AGGIUNTA.format(ind=ind, P=P, Y=Y).rstrip()
    a.sorgente.write_text(t[:m.start()] + nuovo + t[m.end():])
    import ast
    try:
        ast.parse(a.sorgente.read_text())
    except SyntaxError as e:
        shutil.copy2(bak, a.sorgente)
        print(f"errore di sintassi dopo la modifica ({e}): ripristinato")
        return 1
    print(f"\napplicata. Copia di sicurezza in {bak.name}")
    print("Il priore calibrato comparira' come `hist_prior_cal` accanto a `hist_prior`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
