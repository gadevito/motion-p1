#!/usr/bin/env python3
"""
E17 — politica integrata, categorie di verdetto, recupero, margine minimo (protocol/E17.md). SOLA ANALISI.
=========================================================================================================
Dalle predizioni per cella gia' salvate (aggregati A, B per fascia d'eta', nodo, orizzonte):
`predizioni_e5/` (citta', episodi 1–3, semi 201–206), `predizioni_e6/prova_*` (PEMS08),
`predizioni_e6a/prova_*` (PEMS04); dai json congelati per i confronti gia' stimati (R-orig − F′).

1. **Politica gated(1 sett., 0)**: token (F₀′) fino a eta' 1 settimana, poi F′(1 sett.) per tutti
   i sensori (`_politica(z, 672, 0)` di E4, la stessa composizione per fascia della campagna), come
   politica completa: wCE integrata su tutte le origini dopo t₁. Episodi 2 e 3 (che non l'hanno
   formulata) ed episodio 1 per riferimento; PEMS08 e PEMS04 come righe aggiuntive. Confronti:
   gated(1 sett., 0) − F₀′, − gated(τ, N) selezionata, − C; intervalli con il ricampionamento
   congiunto della campagna (stesso schema di `_boot`, 4.000 repliche, seme fisso).
2. **Categorie** (dichiarate in E17, usate ovunque): superiorita' (limite superiore < 0);
   non inferiorita' (limite superiore < δ = 0,005 wCE, non superiorita'); inconclusivo. Applicate
   a gated(τ, N) − F₀′ negli 11 contesti (3 citta' × 3 episodi, PEMS08, PEMS04: dai json congelati
   e5/e6/e6a) e a R-orig(1 sett.) − F′(1 sett.) (citta': e3bis_risultati; PEMS08: e6_risultati).
3. **Recupero** (L_C − L_F′(1 sett.))/(L_C − L_A) sulle stesse origini (eta' > 1 settimana), con
   intervallo (rapporto delle medie nella stessa replica), nei contesti con A: citta' ep. 1–3, PEMS08.
4. **Margine minimo TOST** per R-orig(1 sett.) ≡ F′(1 sett.): il piu' piccolo δ a cui l'intervallo
   al 95 % della differenza sta in (−δ, δ), cioe' max(|lo|, |hi|) dell'intervallo congelato, per
   citta' e PEMS08.

Scrive `results/evoluzione/e17_risultati.json`.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/analizza_e17.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e4 import B_BOOT, _politica, _wce  # noqa: E402
from evoluzione.esperimenti.esegui_e5 import CITTA, EPISODI, _carica_celle_e5  # noqa: E402

SEME_BOOT = 20261022
DELTA_NI = 0.005                     # non inferiorita': limite superiore < 0,005 wCE (E17)
TAU_POL, N_POL = 672, 0


def categoria(ic):
    lo, hi = ic
    if hi < 0:
        return "superiorita'"
    if hi < DELTA_NI:
        return "non inferiorita'"
    return "inconclusivo"


def _boot_vec(celle, f_vec, rng):
    """Come `_boot` di E4 (stesse estrazioni: partizioni, semi, posizioni dei nodi), ma `f_vec(z, idx)`
    restituisce un vettore di statistiche per cella; si restituiscono la media puntuale e le repliche."""
    kk = sorted(celle); parts = sorted({k[1] for k in kk}); semi = sorted({k[2] for k in kk})
    K = celle[kk[0]]["celle_valide"].shape[0]
    m0 = np.mean([f_vec(celle[k], None) for k in kk], axis=0)
    rep = np.empty((B_BOOT, len(m0)))
    for b in range(B_BOOT):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = rng.integers(0, K, K)
        rep[b] = np.mean([f_vec(celle[(kk[0][0], p, s)], nd) for p in ps for s in ss], axis=0)
    return m0, rep


def _ic(v):
    q = np.nanpercentile(v, [2.5, 97.5]); return [float(q[0]), float(q[1])]


def _ab(z, nome, fascia, idx, tau=None, N=None):
    if nome == "gated":
        A, Bm = _politica(z, tau, N)
    else:
        A, Bm = z[f"A_{nome}"], z[f"B_{nome}"]
        A = A[:3].sum(0) if fascia is None else A[fascia]
        Bm = Bm[:3].sum(0) if fascia is None else Bm[fascia]
    return (A, Bm) if idx is None else (A[idx], Bm[idx])


def analizza_gruppo(celle, tau_sel, N_sel, con_A: bool, rng):
    """Politica gated(672, 0) e recupero su un gruppo di celle con chiavi (gruppo, p, s)."""
    def f(z, idx):
        g0 = _wce(*_ab(z, "gated", None, idx, TAU_POL, N_POL))
        gs = _wce(*_ab(z, "gated", None, idx, tau_sel, N_sel))
        f0p = _wce(*_ab(z, "F0p", None, idx)); c = _wce(*_ab(z, "C", None, idx))
        # recupero sulle origini con eta' > 1 settimana (fascia 2)
        c2 = _wce(*_ab(z, "C", 2, idx)); fw2 = _wce(*_ab(z, "Fp_672", 2, idx))
        a2 = _wce(*_ab(z, "A", 2, idx)) if con_A else np.nan
        return np.array([g0 - f0p, g0 - gs, g0 - c, g0, f0p, gs, c, c2, fw2, a2])
    m0, rep = _boot_vec(celle, f, rng)
    nomi = ["gated672_0-F0p", "gated672_0-gated_sel", "gated672_0-C"]
    R = {"celle": len(celle), "tau_sel": tau_sel, "N_sel": N_sel, "confronti": {}, "livelli": {}}
    for i, n in enumerate(nomi):
        ic = _ic(rep[:, i])
        R["confronti"][n] = {"media": float(m0[i]), "ic_con_nodi": ic, "categoria": categoria(ic),
                             "segno": "-" if ic[1] < 0 else ("+" if ic[0] > 0 else "0")}
    for i, n in zip(range(3, 7), ("gated672_0", "F0p", "gated_sel", "C")):
        R["livelli"][n] = {"media": float(m0[i]), "ic_con_nodi": _ic(rep[:, i])}
    if con_A:
        num0, den0 = m0[7] - m0[8], m0[7] - m0[9]
        rec = (rep[:, 7] - rep[:, 8]) / (rep[:, 7] - rep[:, 9])
        R["recupero"] = {"definizione": "(L_C - L_F'(1 sett.)) / (L_C - L_A), origini con eta' > 1 settimana",
                         "media": float(num0 / den0) if den0 != 0 else None, "ic_con_nodi": _ic(rec),
                         "L_C": float(m0[7]), "L_Fp_672": float(m0[8]), "L_A": float(m0[9]),
                         "repliche_den_non_positivo": int(np.sum((rep[:, 7] - rep[:, 9]) <= 0))}
    return R


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    a = ap.parse_args()
    rng = np.random.default_rng(SEME_BOOT)
    SC4 = json.loads((a.out / "e4_scelta_gated.json").read_text())["scelta"]
    SC6 = json.loads((a.out / "e6_scelta_gated.json").read_text())["scelta"]["PEMS08"]
    SC6a = json.loads((a.out / "e6a_scelta_gated.json").read_text())["scelta"]["PEMS04"]
    E5 = json.loads((a.out / "e5_risultati.json").read_text())
    E6 = json.loads((a.out / "e6_risultati.json").read_text())
    E6a = json.loads((a.out / "e6a_risultati.json").read_text())
    E3b = json.loads((a.out / "e3bis_risultati.json").read_text())
    print("=" * 96); print("E17 — politica integrata gated(1 sett., 0), categorie, recupero, margine minimo"); print("=" * 96)

    # ---- 1 + 3: politica e recupero dalle celle ----------------------------------------------------
    celle5 = _carica_celle_e5(a.out)
    R = {"politica": {}, "categorie": {"gated_sel-F0p": {}, "Rorig_672-Fp_672": {}}, "recupero": {}, "margine_minimo": {},
         "delta_non_inferiorita": DELTA_NI, "politica_definizione": "gated(672, 0): F0' per eta' <= 1 settimana, F'(1 sett.) oltre, per tutti i sensori (N = 0)",
         "repliche": B_BOOT, "seme_bootstrap": SEME_BOOT}
    for c in CITTA:
        for k in EPISODI:
            cc = {(c, p, s): z for (k_, c_, p, s), z in celle5.items() if k_ == k and c_ == c}
            if len(cc) != 18:
                raise RuntimeError(f"{c} ep{k}: {len(cc)} celle, attese 18")
            r = analizza_gruppo(cc, SC4[c]["tau"], SC4[c]["N"], True, rng)
            R["politica"][f"{c}/ep{k}"] = {k_: v for k_, v in r.items() if k_ != "recupero"}
            R["recupero"][f"{c}/ep{k}"] = r["recupero"]
            g = r["confronti"]
            print(f"  {c:10s} ep{k}: gated(672,0)-F0' {g['gated672_0-F0p']['media']:+.5f} {g['gated672_0-F0p']['ic_con_nodi']} "
                  f"{g['gated672_0-F0p']['categoria']:16s} | -gated(sel) {g['gated672_0-gated_sel']['media']:+.5f} | "
                  f"recupero {r['recupero']['media']:.3f} {r['recupero']['ic_con_nodi']}")
    from evoluzione.esperimenti.esegui_e6 import _carica_celle as celle_e6
    from evoluzione.esperimenti.esegui_e6a import _carica_celle as celle_e6a
    c6 = celle_e6(a.out, "prova"); r6 = analizza_gruppo(c6, SC6["tau"], SC6["N"], True, rng)
    R["politica"]["PEMS08"] = {k_: v for k_, v in r6.items() if k_ != "recupero"}; R["recupero"]["PEMS08"] = r6["recupero"]
    c6a = celle_e6a(a.out, "prova"); r6a = analizza_gruppo(c6a, SC6a["tau"], SC6a["N"], False, rng)
    R["politica"]["PEMS04"] = r6a
    for nome, r in (("PEMS08", r6), ("PEMS04", r6a)):
        g = r["confronti"]
        print(f"  {nome:10s}    : gated(672,0)-F0' {g['gated672_0-F0p']['media']:+.5f} {g['gated672_0-F0p']['ic_con_nodi']} "
              f"{g['gated672_0-F0p']['categoria']}" + (f" | recupero {r['recupero']['media']:.3f}" if "recupero" in r else ""))

    # ---- 2: categorie sui confronti congelati -------------------------------------------------------
    for c in CITTA:
        for k in EPISODI:
            z = E5["affermazioni"][f"{c}/ep{k}/b"]
            R["categorie"]["gated_sel-F0p"][f"{c}/ep{k}"] = {"media": z["media"], "ic_con_nodi": z["ic_con_nodi"], "categoria": categoria(z["ic_con_nodi"]), "fonte": "e5_risultati.json"}
    for nome, J in (("PEMS08", E6), ("PEMS04", E6a)):
        z = J["affermazioni"]["b"]
        R["categorie"]["gated_sel-F0p"][nome] = {"media": z["media"], "ic_con_nodi": z["ic_con_nodi"], "categoria": categoria(z["ic_con_nodi"]), "fonte": f"{'e6' if nome == 'PEMS08' else 'e6a'}_risultati.json"}
    for c in CITTA:
        z = E3b["confronti"][f"{c}/Rw-Fpw"]
        R["categorie"]["Rorig_672-Fp_672"][c] = {"media": z["media"], "ic_con_nodi": z["ic_con_nodi"], "categoria": categoria(z["ic_con_nodi"]), "fonte": "e3bis_risultati.json"}
        R["margine_minimo"][c] = {"delta_min": float(max(abs(z["ic_con_nodi"][0]), abs(z["ic_con_nodi"][1]))),
                                  "livello_Fp": None, "fonte": "e3bis_risultati.json"}
    z = E6["altri"]["Rorig_672-Fp_672_eta>1sett"]
    R["categorie"]["Rorig_672-Fp_672"]["PEMS08"] = {"media": z["media"], "ic_con_nodi": z["ic_con_nodi"], "categoria": categoria(z["ic_con_nodi"]), "fonte": "e6_risultati.json (altri)"}
    R["margine_minimo"]["PEMS08"] = {"delta_min": float(max(abs(z["ic_con_nodi"][0]), abs(z["ic_con_nodi"][1]))), "fonte": "e6_risultati.json (altri)"}
    # margine relativo al livello di F'(1 sett.) (E3-bis usa ±3 % del livello)
    for c in CITTA:
        if "margine" in E3b and c in E3b["margine"]:
            R["margine_minimo"][c]["margine_3pc_e3bis"] = E3b["margine"][c]
    print("\n  categorie gated(τ,N) − F0': " + ", ".join(f"{k} {v['categoria']}" for k, v in R["categorie"]["gated_sel-F0p"].items()))
    print("  categorie R-orig(1 sett.) − F'(1 sett.): " + ", ".join(f"{k} {v['categoria']}" for k, v in R["categorie"]["Rorig_672-Fp_672"].items()))
    print("  margine minimo TOST: " + ", ".join(f"{k} {v['delta_min']:.4f}" for k, v in R["margine_minimo"].items()))
    R["istante"] = datetime.now(timezone.utc).isoformat()
    f = a.out / "e17_risultati.json"
    f.write_text(json.dumps(R, indent=2, ensure_ascii=False))
    print(f"\n  salvato in {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
