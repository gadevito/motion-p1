#!/usr/bin/env python3
"""
Applica la selezione dell'attributo di distanza agli script che ne sono privi.
==============================================================================
Il campo `weight` degli archi NON ha lo stesso significato nelle due famiglie
di contesti:

  * grafi Traffic4cast : `weight` E' la distanza in metri (mediana ~60 m);
  * grafo GO-MO        : `weight` e' una SIMILARITA' gia' normalizzata in
                         [0,01; 1] e decrescente nella distanza; la distanza
                         in metri sta nell'attributo separato `distance`
                         (mediana ~644 m).

Tutti gli harness applicano poi un nucleo gaussiano

        Aff = exp(-(Araw / sd)^2),   sd = deviazione standard di Araw

che ha senso su una DISTANZA. Applicato a una similarita' prossima a 1 con
deviazione standard ~0,15, l'esponente vale circa -45 e l'adiacenza collassa:
i nodi VICINI vengono azzerati e sopravvivono solo i piu' LONTANI, quelli con
similarita' bassa. Sui contesti a spire l'adiacenza effettiva diventa quasi la
matrice identita'.

`gomo_sparse.py` e `gomo_classify.py` sono gia' stati corretti. Questo script
applica la stessa correzione agli altri harness, che leggono `weight` senza
condizione. La modifica e' idempotente e si limita a due righe per file:

    _wattr = "distance" if any("distance" in _a
                               for *_, _a in list(rg.edges(data=True))[:50]) else "weight"
    Araw = nx.to_numpy_array(..., weight=_wattr)
    Araw[Araw > 0] = np.maximum(Araw[Araw > 0], 1.0)   # sensori coincidenti

Chi e' interessato, in ordine di conseguenza:

  * `gomo_rnn_baselines.py` e `gomo_sota_baselines.py` sono eseguiti su TUTTI e sei i
    contesti, quindi sui tre a spire l'adiacenza e' degenere. Ne risentono il DCRNN,
    la cui diffusione bidirezionale si riduce a un percettrone per nodo, e il GCN in
    stile Traffic4cast, i cui tre strati su grafo diventano tre strati per nodo. NON
    ne risentono l'AGCRN, che apprende la propria adiacenza, ne' lo STAEformer, che
    usa attenzione fra i sensori e non tocca la matrice. Il DCRNN e' pero' il modello
    su cui ricade l'onere probatorio per la fascia priva di identita' di nodo (§6.3):
    le sue righe sui contesti a spire vanno rigenerate dopo la patch.

  * `gomo_ign.py` e `gomo_onboard.py` applicano lo stesso nucleo in `norm_adj`, ma
    per disegno sono eseguiti sui soli contesti primari (§7.2.4, §7.2.6), dove
    `weight` E' la distanza. Non sono quindi interessati in pratica; la patch li
    copre per sicurezza, in caso di estensione ai contesti a spire.

  * `gomo_gwn.py` e `gomo_stgnn.py` sono harness di REGRESSIONE e alimentano il solo
    confronto regressione contro classificazione (§7.2.7), non le tabelle di
    prestazione assoluta.

Uso (dalla radice OR3/, o da qualunque cartella indicando la radice):

    poetry run python patch_attributo_distanza.py --verifica     # solo diagnosi
    poetry run python patch_attributo_distanza.py                # applica
    poetry run python patch_attributo_distanza.py --radice ~/OR3

Gli script sono cercati per NOME sotto la radice, a qualunque profondita', quindi
la disposizione delle cartelle non conta.
"""
from pathlib import Path
import argparse
import ast
import re
import sys

BERSAGLI = {
    "gomo_rnn_baselines.py": "DCRNN consuma il grafo; AGCRN no",
    "gomo_sota_baselines.py": "t4c_gnn consuma il grafo; STAEformer no",
    "gomo_ign.py": "in pratica eseguito sui soli contesti primari",
    "gomo_onboard.py": "in pratica eseguito sui soli contesti primari",
    "gomo_gwn.py": "harness di regressione (§7.2.7)",
    "gomo_stgnn.py": "harness di regressione (§7.2.7)",
}
GIA_CORRETTI = ["gomo_sparse.py", "gomo_classify.py"]
IGNORA = {".git", "__MACOSX", "__pycache__", ".venv", "node_modules",
          "replication", "results", "data_collection"}

RIGA = re.compile(
    r'^(?P<ind>\s*)(?P<var>\w+)\s*=\s*nx\.to_numpy_array\('
    r'(?P<args>[^\n]*?)weight="weight"\)(?P<coda>[^\n]*)$',
    re.M)


def trova(radice: Path, nome: str) -> list:
    """Cerca il file per nome sotto la radice, saltando le cartelle di rumore."""
    trovati = []
    for p in radice.rglob(nome):
        if any(parte in IGNORA for parte in p.parts):
            continue
        if p.name.startswith("._"):          # risorse macOS negli archivi zip
            continue
        trovati.append(p)
    return sorted(trovati)


def diagnosi(radice: Path) -> None:
    """Stampa che cosa la scansione vede davvero. Serve quando `trova` non
    restituisce nulla: quasi sempre la radice e' sbagliata, oppure gli script
    hanno nomi diversi da quelli attesi."""
    print("\n" + "=" * 72)
    print("DIAGNOSI: nessuno script atteso e' stato trovato sotto la radice.")
    print("=" * 72)
    try:
        tutti = [p for p in radice.rglob("*.py")
                 if not any(parte in IGNORA for parte in p.parts)
                 and not p.name.startswith("._")]
    except OSError as e:
        print(f"errore durante la scansione: {e}")
        return
    print(f"file .py trovati sotto la radice (escluse le cartelle di rumore): {len(tutti)}")
    if not tutti:
        print("\nNessun file .py: la radice indicata non e' quella del repository.")
        print("Indicare la cartella che contiene models/ e baselines/, per esempio:")
        print("    --radice ~/Personal/MOTION/deliverables/OR3")
        return
    simili = sorted({p.name for p in tutti if "gomo" in p.name.lower()})
    if simili:
        print(f"\nfile con 'gomo' nel nome ({len(simili)}):")
        for n in simili[:40]:
            print(f"  {n}")
    print("\nprime venti cartelle che contengono file .py:")
    cartelle = sorted({p.parent.relative_to(radice) for p in tutti})
    for c in cartelle[:20]:
        print(f"  {c}")


def patcha(percorso: Path, applica: bool) -> str:
    testo = percorso.read_text()
    if "_wattr" in testo:
        return "gia' patchato"
    m = RIGA.search(testo)
    if not m:
        return "riga to_numpy_array non trovata (schema diverso: patchare a mano)"
    if not applica:
        return f"DA PATCHARE ({m.group('var')} = nx.to_numpy_array(...))"

    ind, var, argomenti, coda = (m.group("ind"), m.group("var"),
                                 m.group("args"), m.group("coda"))
    nuovo = (
        f'{ind}_wattr = "distance" if any("distance" in _a '
        f'for *_, _a in list(rg.edges(data=True))[:50]) else "weight"\n'
        f'{ind}{var} = nx.to_numpy_array({argomenti}weight=_wattr){coda}\n'
        f'{ind}{var}[{var} > 0] = np.maximum({var}[{var} > 0], 1.0)   '
        f'# archi a distanza nulla: sensori coincidenti\n'
        f'{ind}print(f"[grafo] attributo di distanza: {{_wattr}} | '
        f'archi {{({var}>0).sum()}} | mediana {{np.median({var}[{var}>0]):.1f}}")'
    )
    percorso.write_text(testo.replace(m.group(0), nuovo, 1))
    return "PATCHATO"


def main() -> int:
    ap = argparse.ArgumentParser(description="patch dell'attributo di distanza")
    ap.add_argument("--radice", type=Path, default=Path("."),
                    help="radice del repository (default: cartella corrente)")
    ap.add_argument("--verifica", action="store_true",
                    help="riporta lo stato senza modificare i file")
    args = ap.parse_args()

    radice = args.radice.expanduser().resolve()
    if not radice.is_dir():
        print(f"ERRORE: {radice} non e' una cartella", file=sys.stderr)
        return 1
    print(f"radice: {radice}\n")

    print("script che devono gia' avere la correzione:")
    mancanti = 0
    for nome in GIA_CORRETTI:
        trovati = trova(radice, nome)
        if not trovati:
            print(f"  {nome:26s} NON TROVATO sotto la radice")
            mancanti += 1
            continue
        for p in trovati:
            stato = "ok" if "_wattr" in p.read_text() else "PRIVO DI _wattr — da patchare"
            print(f"  {nome:26s} {stato}   ({p.relative_to(radice)})")

    print("\nharness da correggere:")
    da_controllare = []
    localizzati = 0
    for nome, nota in BERSAGLI.items():
        trovati = trova(radice, nome)
        if not trovati:
            print(f"  {nome:26s} non trovato sotto la radice")
            continue
        localizzati += len(trovati)
        for p in trovati:
            esito = patcha(p, applica=not args.verifica)
            print(f"  {nome:26s} {esito:52s} ({p.relative_to(radice)})")
            if esito == "PATCHATO":
                da_controllare.append(p)
            if esito.startswith("riga to_numpy_array"):
                print(f"  {'':26s}   -> {nota}")

    if localizzati == 0 and mancanti == len(GIA_CORRETTI):
        diagnosi(radice)
        return 1

    if args.verifica:
        print("\nnessuna modifica applicata (--verifica).")
        return 0

    if da_controllare:
        print("\nControllo di sintassi:")
        for p in da_controllare:
            try:
                ast.parse(p.read_text())
                print(f"  {p.name:26s} sintassi ok")
            except SyntaxError as e:
                print(f"  {p.name:26s} ERRORE DI SINTASSI: {e}", file=sys.stderr)
                return 1
    else:
        print("\nNessun file modificato: tutti gli harness sono gia' corretti,")
        print("oppure la riga da patchare ha uno schema diverso da quello atteso.")

    print("\nDopo la patch vanno rigenerate le righe che consumano il grafo fornito")
    print("sui tre contesti a spire: DCRNN e GCN stile Traffic4cast.")
    print("AGCRN e STAEformer non sono interessati (adiacenza appresa / attenzione).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
