#!/usr/bin/env python3
"""
Paper 4, fase 1, punto 1 (richiesta del revisore, 6/11/2026): il controllo negativo della geometria (criterio 4 di
`analisi/geometria_criteri.py`, dopo la correzione dell'accoppiamento) rieseguito sui CSV conservati, e il confronto
riga per riga con le Tabelle 34-35 del deliverable UC-04 v1 (pag. 95; terza esecuzione, Melbourne, nel testo di
pag. 96). Nessun addestramento: legge `replication/geo/geo_<citta>_<grafo>_s<s>.csv` e `geo_sweep/covariate_*.csv`.
Scrive `protocol/paper4/fase1/GEOMETRIA_CRITERIO4_rigenerato.md`. Solo registro: nessun numero del paper.

    poetry run python analisi/p4_fase1_criterio4.py --geo-dir ../OR3_vecchia_storia/replication/geo --covariate geo_sweep
"""
import argparse
import hashlib
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "analisi"))

# Trascrizione delle Tabelle 34-35 (pag. 95) e della terza esecuzione (testo, pag. 96) del deliverable UC-04 v1.
# "±" = deviazione standard fra i cinque semi, come stampata dallo script (st()).
DELIV = {
    ("madrid", "comp_q2080"): {"tabella": "34 (prima esecuzione, Madrid, 42,3 m)",
                               "vero": 1.96, "vero_sd": 0.61, "arco_v": 42.3, "rand": 2.09, "rand_sd": 0.48, "arco_c": 390.7,
                               "diff": -0.12, "ic": (-0.44, 0.20), "segni": 2, "grado_medio": 5.23},
    ("madrid", "comp_q5020"): {"tabella": "35 (seconda esecuzione, Madrid, 56,3 m)",
                               "vero": 8.75, "vero_sd": 0.68, "arco_v": 56.3, "rand": 8.93, "rand_sd": 0.86, "arco_c": 494.3,
                               "vero_semi": (9.72, 9.13, 8.32, 8.52, 8.05), "rand_semi": (9.98, 9.62, 8.35, 8.78, 7.94),
                               "diff": -0.18, "ic": (-0.47, 0.10), "segni": 1},
    ("melbourne", "comp_q5080"): {"tabella": "testo di pag. 96 (terza esecuzione, Melbourne, 396 m; nessuna tabella)",
                                  "vero": 3.09, "diff": 0.36, "ic": (-9.11, 9.83), "arco_v": 396.0},
}


def _sha(f: Path) -> str:
    return hashlib.sha256(f.read_bytes()).hexdigest()[:16]


def esito(rig, dev, dec=2):
    if dev is None:
        return "assente nel deliverable"
    return "uguale" if round(rig, dec) == round(dev, dec) else f"diversa (deliverable {dev:+.{dec}f})"


def main() -> int:
    import pandas as pd
    from geometria_criteri import _csv_tag, st, vantaggio
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo-dir", type=Path, required=True)
    ap.add_argument("--covariate", type=Path, default=Path("geo_sweep"))
    ap.add_argument("--semi", type=int, default=5)
    ap.add_argument("--out", type=Path, default=RADICE / "protocol" / "paper4" / "fase1" / "GEOMETRIA_CRITERIO4_rigenerato.md")
    a = ap.parse_args()
    cov = []
    for f in sorted(a.covariate.glob("covariate_*.csv")):
        d = pd.read_csv(f); d["citta"] = f.stem.replace("covariate_", ""); cov.append(d)
    cov = pd.concat(cov, ignore_index=True)
    ingressi = {str(f.relative_to(RADICE)) if RADICE in f.parents else str(f): _sha(f) for f in sorted(a.covariate.glob("covariate_*.csv"))}
    L = ["# Paper 4, fase 1 — criterio 4 (controllo negativo della geometria) rieseguito sui CSV conservati", "",
         f"Generato da `analisi/p4_fase1_criterio4.py` il {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
         f"(non modificare a mano). Nessun addestramento: i vantaggi per seme vengono dai CSV conservati in `{a.geo_dir}` "
         "(bracci `gwn_none` e `gwn_fixed` nello stesso file, come in `geometria_criteri.vantaggio`), le covariate da "
         f"`{a.covariate}/covariate_*.csv`. Accoppiamento `comp_q<xy>` ↔ `neg_rand_q<xy>` della stessa citta' "
         "(`make_geo_sweep.py`); fino al 6/11/2026 lo script cercava «knn» nel nome del grafo e non trovava coppie. "
         "Intervallo = t a 5 semi (2,776·sd/√5), come nello script. Confronto con le Tabelle 34-35 del deliverable UC-04 v1 "
         "(pag. 95) e con la terza esecuzione descritta nel testo (pag. 96). **Solo registro: nessun numero del Paper 4.**", ""]
    righe_tab, dettagli, senza = [], [], []
    coppie = [(r["citta"], r["grafo"], "neg_rand_" + str(r["grafo"]).split("_", 1)[1]) for _, r in cov.iterrows()
              if str(r["grafo"]).startswith("comp_q")]

    def covariata(citta, grafo, campo):
        """arco_medio o grado_medio dalla riga di covariate; se manca (make_geo_sweep.py scrive un solo controllo
        per citta'), dal pkl `geo_sweep/<citta>_<grafo>.pkl` con la stessa definizione (peso - 1 m; 2·archi/nodi)."""
        sel = (cov.citta == citta) & (cov.grafo == grafo)
        if sel.any():
            return float(cov.loc[sel, campo].iloc[0]), "covariate"
        p = a.covariate / f"{citta}_{grafo}.pkl"
        if not p.exists():
            return float("nan"), "assente"
        import pickle
        with open(p, "rb") as h:
            G = pickle.load(h)
        ingressi[str(p)] = _sha(p)
        if campo == "arco_medio":
            return float(sum(d["weight"] - 1.0 for *_, d in G.edges(data=True)) / max(G.number_of_edges(), 1)), "pkl"
        return float(2 * G.number_of_edges() / max(G.number_of_nodes(), 1)), "pkl"
    for citta, vero, casuale in coppie:
        tv, tc = _csv_tag(a.geo_dir, citta, vero, a.semi), _csv_tag(a.geo_dir, citta, casuale, a.semi)
        vv, vc = vantaggio(str(a.geo_dir / f"geo_{tv}_s{{s}}.csv"), a.semi), vantaggio(str(a.geo_dir / f"geo_{tc}_s{{s}}.csv"), a.semi)
        if vv is None or vc is None:
            senza.append(f"{citta} {vero}")
            continue
        for s in range(a.semi):
            for tag in (tv, tc):
                f = next(a.geo_dir.glob(f"geo_{tag}_s{s}.csv")); ingressi[str(f)] = _sha(f)
        diff = [vv[i] - vc[i] for i in range(a.semi)]
        m, sd = st(diff); hw = 2.776 * sd / math.sqrt(a.semi)
        mv, sv = st(vv); mc, sc = st(vc)
        arco_v, _ = covariata(citta, vero, "arco_medio")
        arco_c, fonte_c = covariata(citta, casuale, "arco_medio")
        grado, _ = covariata(citta, vero, "grado_medio")
        if fonte_c == "pkl":
            dettagli.append(f"- {citta} {casuale}: riga assente in covariate_{citta}.csv (lo script attuale genera un solo "
                            f"controllo per citta'); arco medio calcolato dal pkl `{a.covariate}/{citta}_{casuale}.pkl`")
        D = DELIV.get((citta, vero), {})
        tab = D.get("tabella", "— (non nel deliverable)")
        R = [("vantaggio grafo vero (%)", mv, D.get("vero")), ("sd grafo vero", sv, D.get("vero_sd")),
             ("arco medio vero (m)", arco_v, D.get("arco_v")), ("vantaggio randomizzato (%)", mc, D.get("rand")),
             ("sd randomizzato", sc, D.get("rand_sd")), ("arco medio randomizzato (m)", arco_c, D.get("arco_c")),
             ("grado medio", grado, D.get("grado_medio")), ("differenza appaiata (punti)", m, D.get("diff")),
             ("IC inferiore", m - hw, D["ic"][0] if "ic" in D else None), ("IC superiore", m + hw, D["ic"][1] if "ic" in D else None),
             ("segni positivi su 5", float(sum(x > 0 for x in diff)), float(D["segni"]) if "segni" in D else None)]
        dec = {"arco medio vero (m)": 1, "arco medio randomizzato (m)": 1, "segni positivi su 5": 0}
        for nome, rig, dev in R:
            d_ = dec.get(nome, 2)
            righe_tab.append(f"| {citta} | {vero} ↔ {casuale} | {tab} | {nome} | {rig:+.{d_}f} | "
                             + (f"{dev:+.{d_}f}" if dev is not None else "—") + f" | {esito(rig, dev, d_)} |")
        for etich, chiave, val in (("vero", "vero_semi", vv), ("randomizzato", "rand_semi", vc)):
            if chiave in D:
                for s in range(a.semi):
                    righe_tab.append(f"| {citta} | {vero} ↔ {casuale} | {tab} | per seme, {etich}, s{s} | {val[s]:+.2f} | "
                                     f"{D[chiave][s]:+.2f} | {esito(val[s], D[chiave][s])} |")
            else:
                dettagli.append(f"- {citta} {vero}: valori per seme {etich} = " + " / ".join(f"{x:.2f}" for x in val)
                                + " (assenti nel deliverable)")
        margine = mv
        esito4 = ("REFUTAZIONE" if m <= 0 else "attribuibile alla prossimita'" if m - hw > 1.68 else "non distinguibili")
        dettagli.append(f"- {citta} {vero} ↔ {casuale}: differenza appaiata {m:+.2f} [{m - hw:+.2f}; {m + hw:+.2f}], "
                        f"margine {margine:.2f} punti → {esito4}" + (" (margine sotto i due punti: non conclusiva)" if margine < 2 else ""))
    L += ["| citta' | coppia | tabella del deliverable | grandezza | rigenerato | deliverable | esito |", "|---|---|---|---|---:|---:|---|"]
    L += righe_tab
    L += ["", "## Esiti del criterio 4 (regola dello script)", ""] + dettagli
    if senza:
        L += ["", f"Configurazioni del braccio principale senza controllo randomizzato (nessun CSV `neg_rand_q<xy>`): "
              + ", ".join(senza) + ". Il deliverable ne riporta tre (pag. 95-96), tutte ritrovate."]
    # l'uscita integrale dello script corretto
    cmd = [sys.executable, str(RADICE / "analisi" / "geometria_criteri.py"), "--geo-dir", str(a.geo_dir), "--covariate", str(a.covariate), "--semi", str(a.semi)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    L += ["", "## Uscita integrale di `analisi/geometria_criteri.py` (dopo la correzione)", "",
          "```", "$ " + " ".join(cmd[1:]), r.stdout.rstrip(), (r.stderr.rstrip() if r.stderr.strip() else ""), f"[codice di uscita {r.returncode}]", "```"]
    L += ["", "## Ingressi (impronte sha256, 16 esadecimali)", ""] + [f"- `{k}` `{v}`" for k, v in sorted(ingressi.items())]
    L += ["", f"Script: `analisi/geometria_criteri.py` `{_sha(RADICE / 'analisi' / 'geometria_criteri.py')}`; "
          f"`analisi/p4_fase1_criterio4.py` `{_sha(Path(__file__))}`.", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text("\n".join(L))
    print("\n".join(righe_tab)); print("\n".join(dettagli)); print(f"  -> {a.out} ({_sha(a.out)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
