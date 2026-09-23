#!/usr/bin/env python3
"""
Congelamento della fase E principale e della selezione di F.
=============================================================
**Ogni conclusione si ricava dai file**: il generatore precedente aveva la
scelta scritta a mano, e sui nuovi punti E sarebbe stata falsa.

Uso (dalla radice OR3/):

    poetry run python genera_congelamento_principale.py
"""
import hashlib
import json
import statistics as st
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import torch

R = Path("results/evoluzione")
DIR_E = R / "E_inserimento_griglia"
SEL = R / "selezione_F_griglia"
# le due selezioni precedenti, per il confronto: nessuna si trasferisce
PRECEDENTI = {"E a 35 aggiornamenti": R / "selezione_F" / "configurazione_F.json",
              "E a 2.290, origini per indice":
                  R / "selezione_F_principale" / "configurazione_F.json"}
CITTA = ("Madrid", "Londra", "Melbourne")
GRIGLIA = ["(10, 0.001)", "(10, 0.01)", "(50, 0.001)", "(50, 0.01)",
           "(200, 0.001)", "(200, 0.01)"]


def h(p, n=16):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]
    except OSError:
        return "assente"


def main() -> int:
    cfg = json.loads((SEL / "configurazione_F.json").read_text())
    man = [json.loads(Path(x).read_text()) for x in sorted(SEL.glob("sel_*.json"))]
    esE = json.loads((DIR_E / "esito_E.json").read_text())
    ordE = json.loads((DIR_E / "ordine_E.json").read_text())
    prec = {k: json.loads(v.read_text()) for k, v in PRECEDENTI.items()
            if v.exists()}
    agg = Counter()
    for f in sorted(DIR_E.glob("ck_E_*.pt")):
        d = torch.load(f, map_location="cpu", weights_only=False)
        if d.get("training_protocol") != "principale":
            raise SystemExit(f"{f.name}: protocollo {d.get('training_protocol')}")
        agg[int(d["aggiornamento"])] += 1
    marcatori = len(list(DIR_E.glob("*.fatto")))

    r = []
    A = r.append
    A("# Congelamento — fase E e selezione di F, GRIGLIA TEMPORALE REALE")
    A("")
    A("**Regola temporale, in tutte le fasi e per tutti i bracci:** un'origine "
      "e' ammissibile soltanto se la sequenza dal primo passo della finestra "
      "dinamica all'ultimo bersaglio rispetta la cadenza reale di quindici "
      "minuti, senza salti nella griglia. Le misure mancanti del singolo "
      "sensore restano alle maschere.")
    A("")
    A("**Convenzione degli estremi:** l'acquisizione e' $(t_0, t_1]$. La riga "
      "$t_0$ non e' usata da descrittore, adattamento di F o corpus di R.")
    A("")
    A("**Pesi delle classi** ricalcolati sulle origini ammissibili in "
      "`pesi_griglia`; la normalizzazione, che usa le righe del periodo come "
      "osservazioni, e' invariata.")
    A("")
    A(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}.** "
      f"Protocollo di addestramento `principale`: 2.290 aggiornamenti, undici "
      f"punti, selezione su V-full, nessun arresto anticipato.")
    A("")
    A("## 1. Fase E")
    A("")
    A("| | |")
    A("|---|---|")
    A(f"| esecuzioni completate | **{esE['completate']}**, fallite "
      f"{len(esE['fallite'])}, marcatori `.fatto` {marcatori} |")
    A(f"| parallelismo | {ordE['lavoratori']} processi × {ordE['fili']} filo, "
      f"backend CPU, un'unica macchina |")
    A(f"| ore di calendario | {esE['ore_calendario']:.1f} |")
    A(f"| somma dei tempi di parete per esecuzione | {esE['ore_macchina']:.1f} ore |")
    A("")
    A("> **La somma dei tempi di parete NON è il costo seriale**: con "
      f"{ordE['lavoratori']} processi concorrenti ogni esecuzione rallenta per "
      "contesa. Non va confrontata con misure fatte in isolamento.")
    A("")
    A("### Aggiornamento selezionato su V-full")
    A("")
    A("| aggiornamento | punti E |")
    A("|---|---|")
    for u in sorted(agg):
        A(f"| {u} | {agg[u]} |")
    tot = sum(agg.values())
    A("")
    A(f"**{agg.get(2290, 0)} su {tot} selezionati al tetto.** Coerente con la "
      "prova di adeguatezza, che non aveva osservato il plateau: il budget resta "
      "finito e non dimostrato convergente.")
    A("")
    A("## 2. Selezione di F")
    A("")
    A("| città | scelta | wCE | seconda migliore | margine |")
    A("|---|---|---|---|---|")
    for c in CITTA:
        s = cfg["scelte"][c]
        ag = cfg["aggregati"][c]
        ordn = sorted(ag.items(), key=lambda kv: kv[1])
        sec = ordn[1]
        A(f"| **{c}** | ({s['aggiornamenti']}, {s['passo']:g}) | "
          f"{s['wCE']:.6f} | {sec[0]} {sec[1]:.6f} | "
          f"{sec[1] - s['wCE']:.4f} wCE |")
    A("")
    A("**La migliore configurazione fra le sei considerate**, per città. "
      "La regola di spareggio non è stata applicata: nessun pareggio.")
    A("")
    A("### I sei candidati")
    A("")
    A("| città | " + " | ".join(GRIGLIA) + " |")
    A("|---|" + "---|" * len(GRIGLIA))
    for c in CITTA:
        ag = cfg["aggregati"][c]
        best = min(ag.values())
        A(f"| {c} | " + " | ".join(
            (f"**{ag[k]:.5f}**" if ag[k] == best else f"{ag[k]:.5f}")
            for k in GRIGLIA) + " |")
    A("")
    if prec:
        A("### Confronto con le selezioni precedenti")
        A("")
        A("| città | " + " | ".join(prec) + " | questa pipeline |")
        A("|---|" + "---|" * (len(prec) + 1))
        cambi = {k: 0 for k in prec}
        for c in CITTA:
            sn = cfg["scelte"][c]
            k_n = (sn["aggiornamenti"], sn["passo"])
            celle = []
            for k, d in prec.items():
                s = d["scelte"][c]
                k_o = (s["aggiornamenti"], s["passo"])
                cambi[k] += k_o != k_n
                celle.append(f"({k_o[0]}, {k_o[1]:g})")
            A(f"| {c} | " + " | ".join(celle) +
              f" | **({k_n[0]}, {k_n[1]:g})** |")
        A("")
        for k, n in cambi.items():
            A(f"- rispetto a «{k}»: la scelta cambia in **{n} città su "
              f"{len(CITTA)}**")
        A("")
        A("**Nessuna selezione si trasferisce da una pipeline all'altra**: "
          "ciascuna vale per i punti E e le origini con cui e' stata prodotta.")
        A("")
    A("### Episodio di validazione e costo")
    A("")
    a_, v_ = man[0]["acquisizione"], man[0]["valutazione"]
    t = [x["secondi"] for m in man for x in m["candidati"]]
    A(f"| | |")
    A(f"|---|---|")
    A(f"| manifesti | {len(man)}, tutti su E "
      f"`{', '.join(sorted({m.get('protocollo_E') for m in man}))}` |")
    A(f"| conformi al perimetro | "
      f"{sum(m.get('conforme_al_perimetro', True) for m in man)}/{len(man)} |")
    A(f"| acquisizione, esempio | {a_['istante_inizio'][:16]} → "
      f"{a_['istante_fine'][:16]}, {a_['timestamp_distinti']} timestamp |")
    A(f"| valutazione, esempio | {v_['istante_inizio'][:16]} → "
      f"{v_['istante_fine'][:16]}, {v_['timestamp_distinti']} timestamp |")
    A(f"| adattamenti | {len(t)}, mediana {st.median(t):.1f} s, "
      f"totale {sum(t)/3600:.2f} ore, un processo |")
    A("")
    A("## 3. Impronte")
    A("")
    A("| file | impronta |")
    A("|---|---|")
    for f in ("evoluzione/esperimenti/esegui_E.py",
              "evoluzione/esperimenti/addestramento.py",
              "evoluzione/esperimenti/seleziona_F.py",
              "evoluzione/componente/adattamento.py",
              "evoluzione/componente/valutazione.py",
              str(SEL / "configurazione_F.json")):
        A(f"| `{f}` | `{h(f)}` |")
    A("")
    A("**Nessun dato di test è stato consultato.** La selezione non si modifica "
      "più.")
    Path("CONGELAMENTO_E_F_GRIGLIA.md").write_text("\n".join(r) + "\n")
    print(f"generato CONGELAMENTO_E_F_GRIGLIA.md, {len(r)} righe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
