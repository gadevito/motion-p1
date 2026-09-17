#!/usr/bin/env python3
"""genera_tabella_verifiche.py — MOTION OR3
Genera tabella_verifiche_preregistrate.csv (una riga per verifica x contesto:
valore, soglia, esito, natura del mancato, perimetro, fonte) LEGGENDO i risultati:
  - replication/FINDINGS_check.csv          -> R1/R2/R3 (principale + esteso) e V4 (p85)
  - models/onboard_{mad,lon,mel}_s?.csv     -> R4 (ricalcolo curve, formula dell'aggregatore)
  - models/sparse_geoF_{short,long}_s?.csv  -> V1 geometria (criteri di make_geo_graphs)
  - models/winabl_w*_s?.csv, stae_full_*    -> V2/V3 (presenza + esito dichiarato)
Uso: poetry run python genera_tabella_verifiche.py   (dalla radice OR3/)
"""
import csv, glob, sys
import pandas as pd

OUT = "tabella_verifiche_preregistrate.csv"
S_F1 = 0.10   # soglia R1/R3 (>= +10%)
S_F2 = 0.03   # margine R2 (TOST +/-3%)
S_R4 = 70.0   # soglia R4 (>= 70% divario colmato a 24h)
GEO_SANITY, GEO_TOL, GEO_LONG, GEO_DELTA = 11.4, 5.0, 10.0, 5.0
CITTA = {"t4cmad": "Madrid", "t4clon": "Londra", "t4cmel": "Melbourne",
         "d8_2024": "d8/2024", "d15_2024": "d15/2024", "d8_2023": "d8/2023",
         "t4cmad_g075": "Madrid g=0,75", "t4cmad_g085": "Madrid g=0,85"}
pct = lambda x: f"{100*float(x):+.1f}%".replace(".", ",")
pc2 = lambda x: f"{100*float(x):.2f}%".replace(".", ",")
rows, err = [], []

def add(verifica, ctx, val, soglia, esito, natura, perim, fonte):
    rows.append([verifica, ctx, val, soglia, esito, natura, perim, fonte])

# ---------- R1/R2/R3 dal FINDINGS ----------
try:
    d = pd.read_csv("replication/FINDINGS_check.csv")
except Exception as e:
    sys.exit(f"ERRORE: replication/FINDINGS_check.csv non leggibile ({e})")
for _, r in d.iterrows():
    ctx = str(r["context"])
    if "p85" in ctx:
        continue  # V4, trattato sotto
    perim = "esteso" if "g0" in ctx else "principale"
    nome = CITTA.get(ctx, ctx)
    f1, f2, f3 = float(r.iloc[1]), float(r.iloc[2]), float(r.iloc[3])
    # R1
    ok = f1 >= S_F1
    add("R1 neurale > GBDT" + ("" if perim == "principale" else " (sensibilita)"), nome,
        pct(f1), ">= +10%", "SUPERATO" if ok else "SOTTO SOGLIA",
        "-" if ok else ("ampiezza (segno preservato)" if perim == "principale"
                        else "ampiezza (rarita del rosso, v. §8.7)"), perim, "FINDINGS_check")
    # R2
    ok = abs(f2) <= S_F2
    add("R2 grafo ~ 0 (denso)" + ("" if perim == "principale" else " (sensibilita)"), nome,
        pc2(f2), "entro +/-3% (TOST)", "SUPERATO" if ok else "FUORI MARGINE",
        "-" if ok else "da discutere", perim, "FINDINGS_check")
    # R3
    ok = f3 >= S_F1
    nat = "-"
    if not ok:
        nat = ("spiegazione candidata: spaziatura fra i sensori (V1 ne mostra la sufficienza su Madrid; disegno definito dopo l'esito, esplorativo)" if ctx == "t4cmel"
               else "ampiezza (rarita del rosso, v. §8.7)")
    add("R3 grafo >> 0 (severo)" + ("" if perim == "principale" else " (sensibilita)"), nome,
        pct(f3), ">= +10%", "SUPERATO" if ok else "SOTTO SOGLIA", nat, perim, "FINDINGS_check")

# ---------- R4 dalle curve di onboarding (formula dell'aggregatore) ----------
def rec24(path):
    c = pd.read_csv(path)
    w = c[c.history.isin(["0h", "24h"])].groupby(["history", "split"]).wCE.mean()
    g0 = w["0h", "held-out"] - w["0h", "seen"]
    g24 = w["24h", "held-out"] - w["24h", "seen"]
    return 100 * (1 - g24 / g0)

for tag, nome in [("mad", "Madrid"), ("lon", "Londra"), ("mel", "Melbourne")]:
    files = sorted(glob.glob(f"models/onboard_{tag}_s?.csv"))
    files = [f for f in files if "pernode" not in f]
    if not files:
        add("R4 inserimento a 24h", nome, "FILE MANCANTI", ">= 70%", "VERIFICARE", "-",
            "principale", f"models/onboard_{tag}_s?.csv")
        err.append(f"R4 {nome}: nessun file")
        continue
    vals = [rec24(f) for f in files]
    m = sum(vals) / len(vals)
    ok = m >= S_R4
    nat = "-" if ok else "spiegazione candidata: identita di forma (profilo orario: 21->53%, sotto criterio e senza tabella dedicata; differenziale di difficolta -0,0354 su divario 0,079 non escluso)"
    nota_semi = " [estensione a 5 semi decisa dopo il primo esito]" if len(vals) > 3 else ""
    add("R4 inserimento a 24h", nome, f"{m:.1f}% ({len(vals)} semi{nota_semi}; Tab.18 arrotonda dai medesimi semi)",
        ">= 70% divario colmato", "SUPERATO" if ok else "SOTTO SOGLIA", nat,
        "principale", "onboard_*_s?.csv (ricalcolo)")

# ---------- V1 geometria dai run geoF ----------
try:
    r3s, r3l, sane = [], [], []
    for s in range(3):
        sh = pd.read_csv(f"models/sparse_geoF_short_s{s}.csv")
        lg = pd.read_csv(f"models/sparse_geoF_long_s{s}.csv")
        w = lambda df, m: df[df.model == m].wCE.mean()
        n = w(sh, "gwn_none")
        r3s.append((n - w(sh, "gwn_fixed")) / n * 100)
        r3l.append((n - w(lg, "gwn_fixed")) / n * 100)
        sane.append((n - w(sh, "gwn_adaptive")) / n * 100)
    okv = all(abs(a - GEO_SANITY) <= GEO_TOL for a in sane) and \
          all(l < GEO_LONG for l in r3l) and \
          all(s - l >= GEO_DELTA for s, l in zip(r3s, r3l))
    add("V1 geometria (seguito R3)", "Madrid, grafo 50 m vs 272 m",
        f"short {'/'.join(f'{v:+.1f}' for v in r3s)} vs long {'/'.join(f'{v:+.1f}' for v in r3l)}; Delta {'/'.join(f'{round(s,1)-round(l,1):.1f}' for s,l in zip(r3s,r3l))}",
        f"long < {GEO_LONG:.0f}% E Delta >= {GEO_DELTA:.0f} pt; sanity {GEO_SANITY} +/- {GEO_TOL:.0f}",
        "SUPERATO (3/3 semi)" if okv else "VERIFICARE", "-", "validita", "sparse_geoF_*.csv (ricalcolo)")
except Exception as e:
    add("V1 geometria (seguito R3)", "Madrid", "FILE MANCANTI", "v. geo_criteri_printout",
        "VERIFICARE", "-", "validita", f"models/sparse_geoF_* ({e})")
    err.append(f"V1: {e}")

# ---------- V2: scarto fra finestre (Tab.12: < 1%), medie PER FINESTRA sui semi ----------
fs = sorted(glob.glob("models/winabl_w*_s?.csv"))
if fs:
    import os
    rec = {}
    for f in fs:
        w = os.path.basename(f).split("_")[1]          # w4 / w12 / w24
        c = pd.read_csv(f)
        if "model" in c.columns:  c = c[c.model == "base"]     # solo il braccio base (Tab.27)
        if "subset" in c.columns: c = c[c.subset == "all"]     # tutto il test, non i sottoinsiemi rain/dry
        col = "wCE" if "wCE" in c.columns else c.select_dtypes("number").columns[-1]
        rec.setdefault(w, []).append(c[col].mean())
    m = {w: sum(v)/len(v) for w, v in rec.items()}
    sc = 100 * (max(m.values()) - min(m.values())) / min(m.values())
    add("V2 finestra d'ingresso", "Madrid, finestra 1/3/6 h",
        f"scarto max {sc:.2f}% (medie per finestra: " + ", ".join(f"{k}={v:.4f}" for k, v in sorted(m.items())) + ")",
        "differenze < 1% fra finestre (Tab.12)",
        "SUPERATO" if sc < 1.0 else "SOTTO SOGLIA", "-", "validita", f"winabl ({len(fs)} file; filtro model=base, subset=all; media per finestra sui semi)")
else:
    add("V2 finestra d'ingresso", "Madrid", "FILE MANCANTI", "differenze < 1% (Tab.12)",
        "VERIFICARE", "-", "validita", "models/winabl_w*_s?.csv"); err.append("V2: file assenti")

# ---------- V3: scala piena vs configurazione della SUITE (Tab.12: |scarto| < 1% per citta) ----------
try:
    lb = pd.read_csv("replication/MODEL_leaderboard.csv")
    ref = lb[lb.model.str.contains("stae", case=False)].set_index("context")["wCE_mean"]
    out, worst = [], 0.0
    for ctx, nome in [("t4cmad", "Madrid"), ("t4clon", "Londra")]:
        fls = sorted(glob.glob(f"stae_full_*{ctx.replace('t4c','')}*.csv")) or sorted(glob.glob("stae_full_*.csv"))
        vals = []
        for f in fls:
            c = pd.read_csv(f)
            if "context" in c.columns: c = c[c.context == ctx]
            if len(c): vals.append(c["wCE" if "wCE" in c.columns else c.select_dtypes("number").columns[-1]].mean())
        if vals and ctx in ref.index:
            full = sum(vals)/len(vals); s = 100*(full - ref[ctx])/ref[ctx]
            worst = max(worst, abs(s)); sfmt = f"{s:+.2f}%" if abs(s) >= 0.095 else f"{s:+.3f}%"   # sotto lo 0,1% una cifra in piu, mai finta precisione
            out.append(f"{nome} {ref[ctx]:.5f}->{full:.5f} ({sfmt})")
        else:
            out.append(f"{nome}: DATI NON TROVATI"); err.append(f"V3 {ctx}: file o riferimento assenti")
    esito = "VERIFICARE" if any("NON TROVATI" in o for o in out) else ("SUPERATO" if worst < 1.0 else "SOTTO SOGLIA")
    add("V3 scala piena STAEformer", "Madrid + Londra", "; ".join(out),
        "|scarto| < 1% dalla configurazione della suite, per citta (Tab.12)",
        esito, "-", "validita", "stae_full_* vs MODEL_leaderboard (ricalcolo per citta)")
except Exception as e:
    add("V3 scala piena STAEformer", "Madrid + Londra", "ERRORE", "|scarto| < 1% (Tab.12)",
        "VERIFICARE", "-", "validita", f"{e}"); err.append(f"V3: {e}")

# ---------- V4 p85 train-only dal FINDINGS ----------
p85 = d[d.context.str.contains("p85")]
base = d[d.context == "d8_2024"]
if len(p85) and len(base):
    same = (p85.iloc[0][["F1", "F2", "F3"]].tolist() == base.iloc[0][["F1", "F2", "F3"]].tolist())
    v = p85.iloc[0]
    add("V4 riferimento p85 train-only", "d8/2024 (variante)",
        f"R1 {pct(v.iloc[1])}, R2 {pc2(v.iloc[2])}, R3 {pct(v.iloc[3])}",
        "gerarchia e segni invariati vs d8/2024",
        "SUPERATO" if same else "VERIFICARE", "-", "validita", "FINDINGS riga d8_p85tr")
else:
    add("V4 riferimento p85 train-only", "d8/2024 (variante)", "RIGA MANCANTE",
        "gerarchia e segni invariati", "VERIFICARE", "-", "validita", "FINDINGS_check")
    err.append("V4: riga p85 assente")

# ---------- scrittura + validazione dei conteggi ----------
with open(OUT, "w", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["verifica", "contesto", "valore", "soglia pre-registrata", "esito",
                "natura del mancato", "perimetro", "fonte"])
    w.writerows(rows)

princ = [r for r in rows if r[6] == "principale"]
vali = [r for r in rows if r[6] == "validita"]
este = [r for r in rows if r[6] == "esteso"]
sotto = lambda rs: sum("SOTTO" in r[4] or "FUORI" in r[4] for r in rs)
print(f"scritto -> {OUT}")
print(f"principale: {len(princ)} verifiche, {sotto(princ)} sotto | "
      f"validita: {len(vali)}, superate: {sum('SUPER' in r[4] for r in vali)}/{len(vali)} | "
      f"esteso: {len(este)}, sotto: {sotto(este)}")
if err:
    print("AVVISI:", *err, sep="\n  - ")
assert len(princ) == 21, f"perimetro principale atteso 21, trovato {len(princ)}: aggiornare i conteggi NEL DOCUMENTO"
assert sotto(princ) == 4, f"attesi 4 sotto soglia nel principale, trovati {sotto(princ)}: aggiornare §8.4/§12/Tab.15"
print("Conteggi COERENTI con §8.4/§12/Tabella 15 (21 verifiche, 4 sotto).")
