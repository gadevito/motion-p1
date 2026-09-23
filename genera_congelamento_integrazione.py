#!/usr/bin/env python3
"""Congelamento della versione dell'integrazione della fase 3."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

FILE = ["evoluzione/esperimenti/esegui_inserimento.py",
        "evoluzione/esperimenti/inserimento.py",
        "evoluzione/esperimenti/prova_inserimento.py",
        "evoluzione/esperimenti/addestramento.py",
        "evoluzione/esperimenti/seleziona_F.py",
        "evoluzione/componente/griglia.py",
        "evoluzione/componente/corpus.py",
        "evoluzione/componente/campionamento.py",
        "evoluzione/componente/adattamento.py",
        "evoluzione/componente/episodio.py",
        "evoluzione/componente/valutazione.py"]


def h(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
    except OSError:
        return "assente"


def main() -> int:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()[:12]
    except Exception:                                        # noqa: BLE001
        commit = "n.d."
    r, A = [], None
    r = []; A = r.append
    A("# Congelamento — versione dell'integrazione della fase 3")
    A("")
    A(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}**, "
      f"commit `{commit}`. Prova tecnica ridotta: **19 controlli su 19**, "
      f"log in `results/evoluzione/prova_fase3.log`.")
    A("")
    A("## I cinque bracci, attraverso gli stessi esecutori")
    A("")
    A("| braccio | popolazione | corpus | campionamento | esecutore |")
    A("|---|---|---|---|---|")
    A("| **C** | iniziale | originario | uniforme sugli istanti | `addestra_una` |")
    A("| **P** | iniziale | originario | uniforme sugli istanti | `addestra_una` |")
    A("| **A** | ampliata | privilegiato | uniforme sugli istanti | `addestra_una` |")
    A("| **R** | ampliata | post-installazione | **uniforme per nodo** | `addestra_una` |")
    A("| **F** | — | acquisizione | — | `adattamento.adatta` |")
    A("")
    A("**Valutazione unica per tutti e cinque**, con `valutazione.valuta`: "
      "stesse chiavi di prova, stesso perimetro, accumulo per orizzonte.")
    A("")
    A("## Regole in vigore")
    A("")
    A("| | |")
    A("|---|---|")
    A("| budget | `max_optimizer_updates` = 2.290, undici punti, nessun arresto anticipato |")
    A("| selezione | minimo di V-full sulla **rete iniziale**; a parità, il precedente |")
    A("| griglia temporale | **reale**: nessuna finestra attraversa un salto |")
    A("| estremi | acquisizione $(t_0, t_1]$: la riga $t_0$ non si usa |")
    A("| pesi | ricalcolati sulle origini ammissibili, `pesi_griglia` |")
    A("| budget di R | 32 × K iniziali finestre per aggiornamento, invariato |")
    A("| perimetro di prova | tutte le origini ammissibili dopo $t_1$ |")
    A("| fasce temporali | prima giornata, fino a una settimana, oltre — **fissate prima dell'analisi** |")
    A("")
    A("## Misure distinte")
    A("")
    A("| misura | modalità | serve a |")
    A("|---|---|---|")
    A("| prestazioni | campagna in parallelo, registrato | qualità dei modelli |")
    A("| **costi** | **campione isolato**: 3 città, partizione 1000, semi 201–203, un processo | costo delle strategie |")
    A("| durata | come eseguita | costo operativo |")
    A("")
    A("> **I tempi delle esecuzioni concorrenti non dimostrano che un braccio "
      "sia più veloce di un altro.**")
    A("")
    A("## Impronte del codice congelato")
    A("")
    A("| file | impronta |")
    A("|---|---|")
    for f in FILE:
        A(f"| `{f}` | `{h(f)}` |")
    A("")
    A("**Nessun dato di prova è stato consultato** prima del lancio. Le "
      "prestazioni della prova tecnica non hanno orientato alcun iperparametro.")
    Path("CONGELAMENTO_INTEGRAZIONE_FASE3.md").write_text("\n".join(r) + "\n")
    print(f"generato CONGELAMENTO_INTEGRAZIONE_FASE3.md, {len(r)} righe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
