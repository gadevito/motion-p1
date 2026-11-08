#!/usr/bin/env python3
"""
Paper 4, P4A — tre cause da trovare (richiesta del revisore, 8/11/2026, 15:50). Sola lettura dei dati del
deliverable, con il SUO modulo congelato (`analisi/validazione_colocalizzata.py`, f1f6340779b612d5) importato senza
modifiche; nessun numero del Paper 4 cambia. Misura sui dati le ipotesi che il codice conservato non puo' decidere:

  1. T67, classe verde: il deliverable conta 2.989.877 celle, il codice conservato (verde = 0,8 <= r_tr < 1,6 con r_tr
     tagliato a 1,5) ne da' 3.432.842. Si provano i limiti superiori 1,0 / 1,2 / 1,5 (escluso) e si cercano quello che
     riproduce il conteggio e la correlazione (+0,033) del deliverable; idem per l'«overall» (+0,255 contro 0,2491).
  2. T68, bande di vicini: conteggio dei sensori per banda con il filtro del deliverable (= quello di p4a.py) e con tre
     varianti (senza il filtro di imputazione su i; con sp_i > 0; vicino piu' prossimo invece del piu' vicino a 33 m),
     con Spearman/AUC/Gini di ciascuna, da confrontare con la Tabella 68 (+0,086/0,789/0,578; +0,076/0,726/0,452;
     +0,080/0,761/0,522; +0,037/0,598/0,196).
  3. Austin: conteggi delle sezioni sotto le definizioni possibili (con/senza direzione, >= 2 corsie, >= 1.000 celle,
     con AUC definita) per vedere quale da' 31; la sezione a 2 corsie che esce dalla correzione 3 (30 -> 29) e perche'.

    PYA analisi/p4a_cause.py --gomo ../OR3/data_collection/go-mo/gomo --austin ../OR3_vecchia_storia/austin/radar/radar_completo.json
"""
import argparse
import hashlib
import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

RADICE = Path(__file__).resolve().parents[1]
DELIV67 = {"verde": (2989877, 0.033), "overall": 0.255}
DELIV68 = {(0, 20): (14, 0.086, 0.789, 0.578), (19, 72): (31, 0.076, 0.726, 0.452), (20, 60): (31, 0.080, 0.761, 0.522),
           (60, 200): (96, 0.037, 0.598, 0.196)}


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def modulo(gomo: Path, austin: Path):
    p = RADICE / "analisi" / "validazione_colocalizzata.py"
    spec = importlib.util.spec_from_file_location("vc", p)
    vc = importlib.util.module_from_spec(spec); spec.loader.exec_module(vc)
    vc.GOMO, vc.AUSTIN = gomo, austin
    return vc, _sha(p)


def gini(a):
    return 2 * a - 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gomo", type=Path, required=True); ap.add_argument("--austin", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=RADICE / "protocol" / "paper4" / "fase2" / "CAUSE_4A.md")
    a = ap.parse_args()
    vc, imp = modulo(a.gomo, a.austin)
    L = ["# P4A — tre cause misurate sui dati (T67 verde, T68 bande, Austin sezioni)", "",
         f"Generato da `analisi/p4a_cause.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} con il modulo congelato "
         f"del deliverable `analisi/validazione_colocalizzata.py` (`{imp}`), dati `{a.gomo}` e `{a.austin}`. Sola lettura; "
         "nessun numero del Paper 4 cambia. Valori del deliverable da UC-04 v1, pag. 130-133.", ""]
    # ---------------------------------------------------------------- 1. T67 verde e overall
    d = vc.carica_m30()
    v = np.isfinite(d["r_pr"]) & np.isfinite(d["r_tr"]) & (d["sp"] > 0)
    A, B = d["r_pr"][v], d["r_tr"][v]
    L += ["## 1. T67 — classe verde e correlazione complessiva", "",
          f"Celle non imputate `v`: {int(v.sum()):,}. Il codice conservato definisce verde = 0,8 ≤ r_tr < 1,6 con r_tr tagliato a 1,5 "
          f"(`carica_m30`, `np.clip(..., 0, 1.5)`; `sez_anello`, r. 117).", "",
          "| definizione del verde | celle | scarto dal deliverable (2.989.877) | Spearman | deliverable +0,033 |", "|---|---:|---:|---:|---|"]
    for hi, et in ((1.6, "0,8 ≤ r < 1,6 (codice conservato)"), (1.5, "0,8 ≤ r < 1,5 (esclusi i tagliati a 1,5)"),
                   (1.2, "0,8 ≤ r < 1,2"), (1.0, "0,8 ≤ r < 1,0 (sotto il riferimento)")):
        m = (B >= 0.8) & (B < hi); n = int(m.sum()); rho = spearmanr(A[m], B[m]).statistic
        L.append(f"| {et} | {n:,} | {n - DELIV67['verde'][0]:+,} | {rho:+.4f} | {'**coincide**' if abs(round(rho, 3) - 0.033) < 1e-9 else 'diverso'} |")
    n_ge1 = int((B >= 1.0).sum()); n_eq15 = int((B >= 1.5).sum())
    L += ["", f"Celle di `v` con r_tr ≥ 1,0: {n_ge1:,}; con r_tr tagliato a 1,5: {n_eq15:,}; mancanti nel deliverable: 442.965.", "",
          "| insieme per l'«overall» | celle | Spearman | deliverable +0,255 |", "|---|---:|---:|---|"]
    for et, m in (("tutte le `v` (codice conservato)", np.ones(len(A), bool)), ("`v` con r_tr < 1,0", B < 1.0),
                  ("`v` con r_tr < 1,5", B < 1.5), ("`v` con r_pr < 1,5", A < 1.5), ("`v` con r_pr < 1,5 e r_tr < 1,5", (A < 1.5) & (B < 1.5)),
                  ("`v` con r_pr > 0 e r_tr > 0 (esclusi i tagliati a 0)", (A > 0) & (B > 0)),
                  ("`v` con 0 < r < 1,5 su entrambi (esclusi tutti i tagliati)", (A > 0) & (B > 0) & (A < 1.5) & (B < 1.5))):
        rho = spearmanr(A[m], B[m]).statistic
        L.append(f"| {et} | {int(m.sum()):,} | {rho:+.4f} | {'**coincide**' if abs(round(rho, 3) - 0.255) < 1e-9 else 'diverso'} |")
    # ---------------------------------------------------------------- 2. T68 bande
    s = pd.read_csv(a.gomo / "traffic_sensors.csv", dtype={"id": "string"}).dropna(subset=["utm_x", "utm_y"])
    s["id"] = s["id"].astype(str)
    XY = s.set_index("id").reindex(d["sub"])[["utm_x", "utm_y"]].to_numpy()
    D = np.sqrt(((XY[:, None, :] - XY[None, :, :]) ** 2).sum(-1)); np.fill_diagonal(D, np.inf)
    S = len(d["sub"])

    def banda(lo, hi, variante):
        Aa, Bb, dd = [], [], []
        for i in range(S):
            c = np.where((D[i] >= lo) & (D[i] < hi))[0]
            if not len(c):
                continue
            j = c[np.argmin(np.abs(D[i][c] - 33.0))] if variante != "vicino_piu_prossimo" else c[np.argmin(D[i][c])]
            m = np.isfinite(d["r_pr"][:, i]) & np.isfinite(d["r_tr"][:, j]) & (d["sp"][:, j] > 0)
            if variante != "senza_filtro_imputazione_i":
                m &= d["oc"][:, i] >= vc.OCC_VUOTA
            if variante == "con_sp_i":
                m &= d["sp"][:, i] > 0
            if variante in ("escl_r_tr_j_1.5", "escl_entrambi_1.5"):
                m &= d["r_tr"][:, j] < 1.5
            if variante == "escl_entrambi_1.5":
                m &= d["r_pr"][:, i] < 1.5
            if m.sum() > 50:
                Aa.append(d["r_pr"][m, i]); Bb.append(d["r_tr"][m, j]); dd.append(D[i, j])
        if len(Aa) < 20:
            return None
        Aa, Bb = np.concatenate(Aa), np.concatenate(Bb); y = (Bb < vc.SOGLIA_ROSSO).astype(int)
        auc = roc_auc_score(y, -Aa) if 50 < y.sum() < len(y) - 50 else np.nan
        return len(dd), float(np.median(dd)), spearmanr(Aa, Bb).statistic, auc, gini(auc), int(len(Aa))
    L += ["", "## 2. T68 — sensori per banda e varianti del filtro", "",
          "Il filtro del deliverable (`sez_accoppiamento`, r. 176-178: r_pr_i finito, r_tr_j finito, sp_j > 0, oc_i ≥ 5; > 50 celle "
          "per coppia; ≥ 20 sensori; vicino piu' prossimo a 33 m) e' lo stesso di `p4a.py` (`table67_68`): i sensori per banda "
          "coincidono per costruzione. Varianti provate per spiegare gli scarti del deliverable.", "",
          "| banda | variante | sensori | dist. mediana | celle | Spearman | AUC | Gini | deliverable (dist., ρ, AUC, Gini) |", "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for (lo, hi), dv in DELIV68.items():
        for var in ("deliverable", "senza_filtro_imputazione_i", "con_sp_i", "vicino_piu_prossimo", "escl_r_tr_j_1.5", "escl_entrambi_1.5"):
            r = banda(lo, hi, var)
            if r is None:
                L.append(f"| {lo}-{hi} m | {var} | < 20 | | | | | | {dv} |"); continue
            n, dm, rho, auc, g, nc = r
            seg = "**ρ coincide**" if abs(round(rho, 3) - dv[1]) < 1e-9 else ""
            L.append(f"| {lo}-{hi} m | {var} | {n} | {dm:.0f} | {nc:,} | {rho:+.4f} | {auc:.4f} | {g:.4f} | {dv[0]} m, {dv[1]:+.3f}, {dv[2]:.3f}, {dv[3]:.3f} {seg} |")
    # ---------------------------------------------------------------- 3. Austin
    x = vc.carica_austin()
    cps = x.groupby("sez").corsia.nunique()
    x = x.copy(); x["una_rossa"] = x.rosso
    agg = x.groupby(["sez", "ist"], as_index=False).agg(volume=("volume", "sum"), occupancy=("occupancy", "mean"),
                                                     speed=("speed", "mean"), una_rossa=("una_rossa", "max"))
    agg = agg[(agg.volume > 0) & (agg.occupancy > 0) & (agg.speed > 0)].copy()
    agg["p"] = agg.volume / agg.occupancy
    agg["r_pr"] = np.clip(agg.p / agg.groupby("sez").p.transform(lambda q: q.quantile(.85)), 0, 1.5)
    agg["r_tr"] = np.clip(agg.speed / agg.groupby("sez").speed.transform(lambda q: q.quantile(.85)), 0, 1.5)
    n_sez = agg.groupby("sez").size(); pos = agg.groupby("sez").una_rossa.sum()
    auc_ok = {s_: roc_auc_score(g_.una_rossa, -g_.r_pr) for s_, g_ in agg.groupby("sez") if g_.una_rossa.sum() > 20 and (~g_.una_rossa).sum() > 20}
    lane_n = x.groupby("corsia").size(); lanes200 = lane_n[lane_n >= 200].index
    sez_l200 = x[x.corsia.isin(lanes200)].groupby("sez").corsia.nunique()
    conteggi = {
        "sezioni (intname|direction) con direzione": int(cps.shape[0]),
        "intersezioni (intname) con direzione": int(x.intname.nunique()),
        "sezioni con >= 2 corsie": int((cps >= 2).sum()),
        "sezioni con >= 2 corsie e >= 1.000 celle aggregate": int(sum(1 for s_ in cps[cps >= 2].index if n_sez.get(s_, 0) >= 1000)),
        "sezioni con >= 2 corsie e AUC definita (> 20 rosse e > 20 non rosse)": int(sum(1 for s_ in cps[cps >= 2].index if s_ in auc_ok)),
        "sezioni con AUC definita (qualunque numero di corsie)": len(auc_ok),
        "sezioni con >= 2 corsie da almeno 200 celle": int((sez_l200 >= 2).sum()),
        "sezioni con >= 1 corsia da almeno 200 celle": int((sez_l200 >= 1).sum()),
        "sezioni + intersezioni senza direzione (3)": int(cps.shape[0]) + 3,
    }
    L += ["", "## 3. Austin — sezioni: 40 contro 31, e la sezione che esce dalla correzione 3", "",
          f"`carica_austin` esclude `direction == 'None'` (le tre intersezioni senza direzione) e definisce la sezione come "
          f"`intname|direction`. Celle {len(x):,}, corsie {x.corsia.nunique()}, sezioni {cps.shape[0]}; per numero di corsie: "
          + ", ".join(f"{k}: {int(v_)}" for k, v_ in cps.value_counts().sort_index().items()) + ".", "",
          "| definizione | sezioni | = 31? |", "|---|---:|---|"]
    L += [f"| {k} | {v_} | {'**si**' if v_ == 31 else ''} |" for k, v_ in conteggi.items()]
    L += ["", "Sezioni con ≥ 2 corsie e AUC **non** definita (escluse dalla correzione 3, che richiede > 20 celle rosse e > 20 non rosse "
          "per sezione, `p4a.py` `austin`, come `sez_austin` del deliverable per la Tabella 69):", "",
          "| sezione | corsie | celle aggregate | celle con ≥ 1 corsia rossa | celle senza |", "|---|---:|---:|---:|---:|"]
    for s_ in sorted(cps[cps >= 2].index):
        if s_ not in auc_ok:
            L.append(f"| `{s_}` | {int(cps[s_])} | {int(n_sez.get(s_, 0)):,} | {int(pos.get(s_, 0)):,} | {int(n_sez.get(s_, 0) - pos.get(s_, 0)):,} |")
    agg["rosso_sez"] = agg.r_tr < vc.SOGLIA_ROSSO
    L += ["", "Livelli per numero di corsie come li stampa `sez_austin` (Tabella 69), con la differenza di prevalenza "
          "(celle con ≥ 1 corsia rossa meno celle con la sezione rossa, punti percentuali; ≥ 0 per costruzione):", "",
          "| corsie | sezioni | celle aggregate | AUC mediana [q25; q75] (n con AUC definita) | diff. prevalenza (pp) |", "|---:|---:|---:|---|---:|"]
    for k in sorted(cps.unique()):
        sel = cps[cps == k].index; q = agg[agg.sez.isin(sel)]
        au = [auc_ok[s_] for s_ in sel if s_ in auc_ok]
        f = f"{np.median(au):.3f} [{np.percentile(au, 25):.3f}; {np.percentile(au, 75):.3f}] (n={len(au)})" if au else "n.d."
        L.append(f"| {int(k)} | {len(sel)} | {len(q):,} | {f} | {100 * (q.una_rossa.mean() - q.rosso_sez.mean()):+.2f} |")
    L += ["", "Per sezione (≥ 2 corsie): celle, AUC, differenza di prevalenza — per cercare la sezione «−45,1 punti» del deliverable:", "",
          "| sezione | corsie | celle | AUC | diff. prevalenza (pp) |", "|---|---:|---:|---:|---:|"]
    for s_ in sorted(cps[cps >= 2].index):
        q = agg[agg.sez == s_]
        au = f"{auc_ok[s_]:.3f}" if s_ in auc_ok else "n.d."
        L.append(f"| `{s_}` | {int(cps[s_])} | {len(q):,} | {au} | {100 * (q.una_rossa.mean() - q.rosso_sez.mean()):+.2f} |")
    L += ["", "Correlazione di rango fra numero di corsie e AUC per sezione (deliverable: −0,541, p = 0,002, su 31 sezioni):", ""]
    for et, ins in (("31 sezioni con AUC definita, qualunque numero di corsie", [s_ for s_ in auc_ok]),
                    ("29 sezioni con ≥ 2 corsie e AUC definita (correzione 3)", [s_ for s_ in auc_ok if cps[s_] >= 2])):
        r_ = spearmanr([cps[s_] for s_ in ins], [auc_ok[s_] for s_ in ins])
        L.append(f"- {et}: n = {len(ins)}, ρ = {r_.statistic:+.3f}, p = {r_.pvalue:.3f}" + (" **coincide con −0,541**" if abs(round(r_.statistic, 3) + 0.541) < 1e-9 else ""))
    L += ["", "Sezioni a 1 corsia (escluse dalla Tabella 69 come caso degenere): " + ", ".join(f"`{s_}`" for s_ in sorted(cps[cps == 1].index)) + ".", "",
          "Nota: la correlazione corsie/AUC «−0,541 su 31 sezioni» e la sezione esclusa per la differenza di prevalenza −45,1 punti "
          "(deliverable, pag. 133) non sono calcolate da nessuno script conservato (`validazione_colocalizzata.py`, "
          "`caratterizza_radar.py`): generatore **non trovato**.", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text("\n".join(L))
    print("\n".join(L)); print(f"  -> {a.out} ({_sha(a.out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
