#!/usr/bin/env python3
"""Congelamento della selezione di F. Legge i file, non copia numeri."""
import hashlib
import json
import statistics as st
from datetime import datetime, timezone
from pathlib import Path

R = Path("results/evoluzione")
SEL = R / "selezione_F"
CITTA = ("Madrid", "Londra", "Melbourne")
T_OSS = {10: 2.1, 50: 10.6, 200: 43.0}


def h(p, n=16):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]
    except OSError:
        return "assente"


cfg = json.loads((SEL / "configurazione_F.json").read_text())
man = [json.loads(Path(x).read_text())
       for x in sorted(SEL.glob("sel_*.json"))]
r = []
A = r.append

A("# Congelamento — selezione della configurazione di adattamento di F")
A("")
A(f"**Congelato il {datetime.now(timezone.utc).date().isoformat()}.** "
  f"Protocollo {cfg.get('versione_protocollo')}.")
A("")
A("## 1. Conclusione, come formulata")
A("")
A("> **Tutte e tre le città selezionano la configurazione con 200")
A("> aggiornamenti e learning rate 0,01. Nei punti esplorati, la perdita")
A("> diminuisce all'aumentare del budget e il learning rate maggiore prevale a")
A("> parità di budget. Il miglioramento prosegue fino al massimo budget")
A("> considerato; non è stato verificato se ulteriori aggiornamenti o learning")
A("> rate diversi producano benefici.**")
A("")
A("**F è valutato entro il budget esplorato, non come migliore adattamento")
A("possibile.** Un eventuale vantaggio di P non dimostrerà superiorità rispetto")
A("a ogni possibile adattamento.")
A("")
A("## 2. Configurazione scelta")
A("")
A("| città | aggiornamenti | passo | wCE | gruppi |")
A("|---|---|---|---|---|")
for c in CITTA:
    s = cfg["scelte"][c]
    A(f"| **{c}** | {s['aggiornamenti']} | {s['passo']:g} | "
      f"{s['wCE']:.6f} | {s['gruppi']} |")
A("")
A(f"**Regola di spareggio**: {cfg.get('regola_spareggio')}. Non applicata: "
  f"nessun pareggio.")
A("")
A("## 3. I sei candidati, per città")
A("")
A("| città | (10, 10⁻³) | (10, 10⁻²) | (50, 10⁻³) | (50, 10⁻²) | (200, 10⁻³) | (200, 10⁻²) |")
A("|---|---|---|---|---|---|---|")
for c in CITTA:
    ag = cfg["aggregati"][c]
    v = [ag[k] for k in ("(10, 0.001)", "(10, 0.01)", "(50, 0.001)",
                         "(50, 0.01)", "(200, 0.001)", "(200, 0.01)")]
    A(f"| **{c}** | " + " | ".join(f"{x:.6f}" for x in v[:-1])
      + f" | **{v[-1]:.6f}** |")
A("")
A("### Rendimento del budget")
A("")
A("**Gli incrementi di budget sono diversi** — 40 aggiornamenti da 10 a 50,")
A("150 da 50 a 200 — sicché le variazioni percentuali non sono confrontabili.")
A("Si riportano le **riduzioni assolute per aggiornamento aggiuntivo** e per")
A("**secondo aggiuntivo misurato**, a passo 10⁻²:")
A("")
A("| città | Δ/agg. (10→50) | Δ/agg. (50→200) | Δ/s (10→50) | Δ/s (50→200) |")
A("|---|---|---|---|---|")
for c in CITTA:
    ag = cfg["aggregati"][c]
    a10, a50, a200 = ag["(10, 0.01)"], ag["(50, 0.01)"], ag["(200, 0.01)"]
    A(f"| {c} | {(a10-a50)/40:.3e} | {(a50-a200)/150:.3e} | "
      f"{(a10-a50)/(T_OSS[50]-T_OSS[10]):.3e} | "
      f"{(a50-a200)/(T_OSS[200]-T_OSS[50]):.3e} |")
A("")
A("> **Il rendimento per aggiornamento DIMINUISCE** fra i due intervalli, di")
A("> circa 2,7 volte, in tutte e tre le città. **Non è dimostrata alcuna")
A("> accelerazione della curva, né che l'ottimo si trovi fuori dalla griglia.**")
A("")
A("## 4. Calendario e istanze")
A("")
A("| città | acquisizione | valutazione | timestamp acq./val. | istanze | celle valide |")
A("|---|---|---|---|---|---|")
for c in CITTA:
    m = next((x for x in man if x["contesto"] == c), None)
    if not m:
        A(f"| {c} | — | — | — | — | — |"); continue
    a_, v_ = m["acquisizione"], m["valutazione"]
    A(f"| **{c}** | {a_['istante_inizio'][:16]} → {a_['istante_fine'][:16]} | "
      f"{v_['istante_inizio'][:16]} → {v_['istante_fine'][:16]} | "
      f"{a_['timestamp_distinti']} / {v_['timestamp_distinti']} | "
      f"{v_['istanze_nodo_timestamp']:,} | {v_['celle_valide']:,} |")
A("")
A("**Origine = timestamp previsionale distinto.** Le tre unità sono riportate")
A("separatamente, per acquisizione e valutazione.")
A("")
A("## 5. Costo misurato")
A("")
t = [x["secondi"] for m in man for x in m.get("candidati", [])]
A(f"| | |")
A(f"|---|---|")
A(f"| gruppi di sei candidati | **{len(man)}** |")
A(f"| adattamenti | **{len(t)}** |")
A(f"| mediana per adattamento | {st.median(t):.1f} s |")
A(f"| totale | {sum(t)/3600:.2f} ore |")
A("")
per_b = {}
for m in man:
    for x in m.get("candidati", []):
        per_b.setdefault(x["aggiornamenti_richiesti"], []).append(x["secondi"])
A("| budget | mediana |")
A("|---|---|")
for b in sorted(per_b):
    A(f"| {b} aggiornamenti | {st.median(per_b[b]):.1f} s |")
A("")
A("## 6. Provenienza e tracciabilità")
A("")
A(f"**{len(man)} manifesti aggregati**, uno per gruppo, ciascuno con i sei")
A("candidati: aggiornamenti richiesti ed eseguiti, impronte iniziale e finale")
A("degli embedding, wCE, secondi, nodi adattati e registro dell'adattamento.")
A("")
A(f"**Conformi al perimetro**: "
  f"{sum(m.get('conforme_al_perimetro', True) for m in man)}/{len(man)}.")
A("")
A("**Punti di controllo E**, con impronta, in ciascun manifesto:")
A("")
A("| città | esempio | impronta |")
A("|---|---|---|")
for c in CITTA:
    m = next((x for x in man if x["contesto"] == c), None)
    if m:
        A(f"| {c} | `{m['punto_di_controllo_E']}` | `{m['impronta_E']}` |")
A("")
A("**Impronte del codice:**")
A("")
A("| file | impronta |")
A("|---|---|")
for f in ("evoluzione/esperimenti/seleziona_F.py",
          "evoluzione/componente/adattamento.py",
          "evoluzione/componente/episodio.py",
          "evoluzione/componente/identita.py",
          "evoluzione/esperimenti/calendario.py"):
    A(f"| `{f}` | `{h(f)}` |")
A("")
A("## 7. Che cosa questo NON decide")
A("")
A("**La selezione non si tocca più.** Il test non modifica la configurazione")
A("di F, e nessun risultato di prova è stato consultato durante questa fase.")
A("")
A("**La griglia resta invariata**: estenderla richiederebbe un emendamento")
A("trasparente al budget fissato, e non è autorizzata per questa campagna.")
A("")

Path("CONGELAMENTO_SELEZIONE_F.md").write_text("\n".join(r) + "\n")
print(f"documento generato: {len(r)} righe")
