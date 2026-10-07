#!/usr/bin/env python3
"""
E7, stadio 1 — copertura e adattamento, a costo zero dai file di E5.
=====================================================================
Legge `predizioni_e5/*.npz` (162 celle), `e4_scelta_gated.json` (N per
citta') ed `e5_k_secondaria.json` (k). Nessun modello si esegue.

Per episodio x citta':
  * per nodo: D1 = F'(1 sett.) - C sulle origini comuni (fascia eta' > 1 sett.),
    D2 = F'(24 h) - C sull'intero periodo, D3 = F'(24 h, k) - C; v = celle
    valide nelle prime 24 h;
  * gruppi v < N e v >= N: media di ciascuna D con ricampionamento congiunto
    (partizioni x semi x nodi del gruppo), solo se il gruppo ha >= 10 nodi in
    media per cella;
  * due covariate: v (celle valide nelle prime 24 h, dal npz) e v7 (celle
    valide nella settimana (t0, t0+672], dalle maschere con `celle_valide`);
  * rho di Spearman (v, D) e (v7, D) sulle unita' (partizione, nodo), D media
    sui semi, intervallo a ricampionamento delle unita' (2000 repliche, seme
    20261008); segno atteso NEGATIVO, una rho positiva che esclude lo zero e'
    un'anomalia dichiarata;
  * tabella per quartili di v.

Ipotesi (protocol/E7.md, punto 4): D1 < 0 con intervallo che esclude lo zero
nel gruppo v < N in ogni (episodio, citta') dove il gruppo esiste.
Regola di decisione per lo stadio 2a (E7.md): si esegue se e solo se
(i) l'ipotesi fallisce in almeno un gruppo E (ii) rho(v, D1) < 0 con
intervallo che esclude lo zero in almeno due citta' nell'episodio 1, oppure
in almeno due citta' in ciascuno di due episodi (in alternativa, lo stesso
per rho(v7, D1)).

Scrive results/evoluzione/e7_stadio1.json e figure/e7_stadio1.png.

Uso (dalla radice OR3/):

    poetry run python evoluzione/analisi/e7_stadio1.py
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.esperimenti.esegui_e5 import (  # noqa: E402
    CITTA, EPISODI, _carica_celle_e5, _fine_periodo, episodi_registrati)

B_GRUPPI, B_RHO, SEME = 4000, 2000, 20261008
MIN_NODI = 10
DELTE = {"D1": ("Fp_672", "C", 2), "D2": ("Fp_96", "C", None), "D3": ("Fp_96k", "C", None)}
ETICHETTE = {"D1": "F′(1 sett.) − C, eta' > 1 sett.", "D2": "F′(24 h) − C", "D3": "F′(24 h, k) − C"}


def _wce_nodi(A, B):
    """wCE per nodo: media sugli orizzonti di A[k,h]/B[k,h]. A, B (K,H)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.where(B > 0, A / np.maximum(B, 1e-12), np.nan)
    return np.nanmean(r, axis=1)


def _delta_nodi(z, n1, n2, fascia):
    def AB(n):
        A, Bm = z[f"A_{n}"], z[f"B_{n}"]
        return (A.sum(0), Bm.sum(0)) if fascia is None else (A[fascia], Bm[fascia])
    return _wce_nodi(*AB(n1)) - _wce_nodi(*AB(n2))


def _wce_gruppo(z, n1, n2, fascia, idx):
    """Differenza di wCE AGGREGATA sui nodi idx (sum A / sum B per orizzonte)."""
    def w(n):
        A, Bm = z[f"A_{n}"], z[f"B_{n}"]
        A, Bm = (A.sum(0), Bm.sum(0)) if fascia is None else (A[fascia], Bm[fascia])
        A, Bm = A[idx].sum(0), Bm[idx].sum(0)
        with np.errstate(invalid="ignore", divide="ignore"):
            return float(np.nanmean(np.where(Bm > 0, A / np.maximum(Bm, 1e-12), np.nan)))
    return w(n1) - w(n2)


def _boot_gruppo(cc, gruppo, n1, n2, fascia, rng):
    """cc: {(p, s): z}; gruppo: {p: indici dei nodi del gruppo}. Ricampiona
    partizioni, semi e nodi dentro il gruppo di ciascuna partizione."""
    parts = sorted({p for p, _ in cc}); semi = sorted({s for _, s in cc})
    if any(len(gruppo[p]) == 0 for p in parts):
        return None
    m0 = float(np.mean([_wce_gruppo(cc[(p, s)], n1, n2, fascia, gruppo[p]) for p in parts for s in semi]))
    v = []
    for _ in range(B_GRUPPI):
        ps = rng.choice(parts, len(parts), True); ss = rng.choice(semi, len(semi), True)
        nd = {p: rng.choice(gruppo[p], len(gruppo[p]), True) for p in parts}
        v.append(np.mean([_wce_gruppo(cc[(p, s)], n1, n2, fascia, nd[p]) for p in ps for s in ss]))
    q = np.percentile(v, [2.5, 97.5])
    return {"media": m0, "ic": q.tolist(), "esclude_zero": bool(q[0] * q[1] > 0),
            "nodi_per_cella": float(np.mean([len(gruppo[p]) for p in parts]))}


def _spearman(x, y):
    from scipy.stats import spearmanr
    return float(spearmanr(x, y).statistic)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results/evoluzione"))
    ap.add_argument("--figure", type=Path, default=Path("figure"))
    a = ap.parse_args()
    SC = json.loads((a.out / "e4_scelta_gated.json").read_text())
    KS = json.loads((a.out / "e5_k_secondaria.json").read_text())
    celle = _carica_celle_e5(a.out)
    rng = np.random.default_rng(SEME)
    # v7: celle valide nella settimana, dalle maschere (stessa funzione di v)
    from evoluzione.analisi.analizza_copertura_e4 import celle_valide
    from evoluzione.componente import griglia as GR
    from evoluzione.esperimenti.addestramento import _carica, _partizioni
    from evoluzione.esperimenti.semi import SEME_PARTIZIONE
    ep_reg = episodi_registrati(a.out)
    V7 = {}
    for c in CITTA:
        D = _carica(c, a.out / "maschere")
        ok = GR.passi_regolari(D["ts"])
        for e in EPISODI:
            t0 = ep_reg[c][e]["t0"]
            o7 = GR.origini_acquisizione(ok, t0, t0 + 672)
            for p in (0, 1, 2):
                nodi, _ = _partizioni(D, {"partizione": np.random.default_rng(SEME_PARTIZIONE[p])},
                                      _fine_periodo(e, ep_reg[c]))
                v7, _ = celle_valide(D, nodi["prova"], o7, t0, t0 + 672)
                V7[(c, e, p)] = (np.asarray(nodi["prova"], dtype="int64"), v7.astype("int64"))
    R = {"impronta_scelta_e4": SC["impronta"], "impronta_k": KS["impronta"], "N": {c: SC["scelta"][c]["N"] for c in CITTA},
         "gruppi": {}, "rho": {}, "quartili": {}, "ipotesi": {}, "decisione": {}}
    print("=" * 84); print("E7, stadio 1 — copertura e adattamento dai file di E5"); print("=" * 84)
    punti_fig = {}
    for c in CITTA:
        N = SC["scelta"][c]["N"]
        for e in EPISODI:
            cc = {(p, s): z for (k, c_, p, s), z in celle.items() if k == e and c_ == c}
            if len(cc) != 18:
                raise RuntimeError(f"{c} ep{e}: {len(cc)} celle, attese 18")
            for z in cc.values():
                if str(z["impronta_k_secondaria"]) != KS["impronta"]:
                    raise RuntimeError("impronta di k diversa da quella registrata")
            parts = sorted({p for p, _ in cc}); semi = sorted({s for _, s in cc})
            v = {p: cc[(p, semi[0])]["celle_valide"].astype("int64") for p in parts}
            v7 = {}
            for p in parts:
                nodi7, vv7 = V7[(c, e, p)]
                if not np.array_equal(nodi7, cc[(p, semi[0])]["nodi"].astype("int64")):
                    raise RuntimeError(f"{c} ep{e} p{p}: nodi di v7 diversi dalla cella")
                v7[p] = vv7
            gruppi = {"sotto": {p: np.flatnonzero(v[p] < N) for p in parts},
                      "sopra": {p: np.flatnonzero(v[p] >= N) for p in parts}}
            print(f"\n{c} episodio {e}: N = {N}; nodi sotto per partizione "
                  + ", ".join(f"p{p} {len(gruppi['sotto'][p])}/{len(v[p])}" for p in parts))
            # per nodo, media sui semi: unita' (partizione, nodo)
            D = {}
            for d, (n1, n2, fascia) in DELTE.items():
                D[d] = {p: np.mean([_delta_nodi(cc[(p, s)], n1, n2, fascia) for s in semi], axis=0) for p in parts}
            vv = np.concatenate([v[p] for p in parts])
            vv7 = np.concatenate([v7[p] for p in parts])
            print(f"  v7 (settimana): mediana {np.median(vv7):.0f} su {4 * len(GR.origini_acquisizione(ok, ep_reg[c][e]['t0'], ep_reg[c][e]['t0'] + 672))} possibili")
            for d in DELTE:
                dd = np.concatenate([D[d][p] for p in parts])
                for nome_cov, cov in (("v", vv), ("v7", vv7)):
                    ok_ = np.isfinite(dd)
                    r0 = _spearman(cov[ok_], dd[ok_])
                    rr = []
                    for _ in range(B_RHO):
                        i = rng.integers(0, ok_.sum(), ok_.sum())
                        if len(np.unique(cov[ok_][i])) < 3:
                            continue
                        rr.append(_spearman(cov[ok_][i], dd[ok_][i]))
                    q = np.percentile(rr, [2.5, 97.5])
                    escl = bool(q[0] * q[1] > 0)
                    R["rho"][f"{c}/ep{e}/{d}/{nome_cov}"] = {
                        "rho": r0, "ic_nodi": q.tolist(), "esclude_zero": escl,
                        "negativa_esclude_zero": bool(escl and q[1] < 0),
                        "anomalia_positiva": bool(escl and q[0] > 0), "unita": int(ok_.sum())}
                    print(f"  rho({nome_cov:2s}, {d}) = {r0:+.3f} [{q[0]:+.3f}, {q[1]:+.3f}]"
                          + ("  esclude lo zero" if escl else "")
                          + ("  **ANOMALIA: positiva**" if escl and q[0] > 0 else ""))
                # gruppi
                for g in ("sotto", "sopra"):
                    npc = np.mean([len(gruppi[g][p]) for p in parts])
                    if npc < MIN_NODI or any(len(gruppi[g][p]) == 0 for p in parts):
                        R["gruppi"][f"{c}/ep{e}/{d}/{g}"] = {"nd": True, "nodi_per_cella": float(npc)}
                        continue
                    n1, n2, fascia = DELTE[d]
                    r = _boot_gruppo(cc, gruppi[g], n1, n2, fascia, rng)
                    R["gruppi"][f"{c}/ep{e}/{d}/{g}"] = r
                    print(f"    {d} {g:5s} N: {r['media']:+.4f} [{r['ic'][0]:+.4f}, {r['ic'][1]:+.4f}] "
                          f"({r['nodi_per_cella']:.0f} nodi/cella)" + ("  esclude lo zero" if r["esclude_zero"] else ""))
                # quartili di v
                qs = np.percentile(vv, [25, 50, 75])
                fasce = np.digitize(vv, qs)
                R["quartili"][f"{c}/ep{e}/{d}"] = [{"quartile": i + 1, "v_max": float(vv[fasce == i].max()) if (fasce == i).any() else None,
                                                   "media": float(np.nanmean(dd[fasce == i])), "n": int((fasce == i).sum())} for i in range(4)]
            punti_fig[(c, e)] = (vv, np.concatenate([D["D1"][p] for p in parts]))
    # ipotesi: D1 < 0 sotto soglia ovunque il gruppo esiste
    sotto = {k: r for k, r in R["gruppi"].items() if k.endswith("/D1/sotto") and not r.get("nd")}
    # None = non verificabile (nessun gruppo sotto soglia con >= 10 nodi)
    vale = (all(r["esclude_zero"] and r["media"] < 0 for r in sotto.values()) if sotto else None)
    R["ipotesi"] = {"gruppi_esistenti": sorted(sotto), "vale": vale,
                    "testo": "l'adattamento su una settimana paga anche per i nodi sotto soglia"}
    # regola di decisione per lo stadio 2a (E7.md): (i) ipotesi fallita in >= 1
    # gruppo E (ii) rho NEGATIVA che esclude lo zero in >= 2 citta' nell'ep. 1
    # o in 2 episodi, per v oppure per v7
    fallita = bool(sotto) and any(not (r["esclude_zero"] and r["media"] < 0) for r in sotto.values())
    cond_rho = {}
    for cov in ("v", "v7"):
        neg = {(c, e): R["rho"][f"{c}/ep{e}/D1/{cov}"]["negativa_esclude_zero"] for c in CITTA for e in EPISODI}
        ep1 = sum(neg[(c, 1)] for c in CITTA) >= 2
        due_ep = sum(1 for e in EPISODI if sum(neg[(c, e)] for c in CITTA) >= 2) >= 2
        cond_rho[cov] = {"ep1": bool(ep1), "due_episodi": bool(due_ep), "vale": bool(ep1 or due_ep),
                         "per_cella": {f"{c}/ep{e}": bool(x) for (c, e), x in neg.items()}}
    anomalie = [k for k, r in R["rho"].items() if r["anomalia_positiva"]]
    R["decisione"] = {"ipotesi_fallita_in_almeno_un_gruppo": fallita, "ipotesi_vale": vale,
                      "rho_negativa": cond_rho, "anomalie_rho_positiva": anomalie,
                      "stadio_2a": bool(fallita and (cond_rho["v"]["vale"] or cond_rho["v7"]["vale"]))}
    aperta = cond_rho["v"]["vale"] or cond_rho["v7"]["vale"]
    R["repliche"] = {"gruppi": B_GRUPPI, "rho": B_RHO}; R["seme"] = SEME; R["min_nodi"] = MIN_NODI
    R["istante"] = datetime.now(timezone.utc).isoformat()
    (a.out / "e7_stadio1.json").write_text(json.dumps(R, indent=2, ensure_ascii=False))
    # figura
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
    for ax, c in zip(axs, CITTA):
        for e, mk in zip(EPISODI, ("o", "s", "^")):
            vv, dd = punti_fig[(c, e)]
            ax.scatter(vv, dd, s=10, marker=mk, alpha=0.6, label=f"episodio {e}")
        ax.axhline(0, color="k", lw=0.8); ax.axvline(SC["scelta"][c]["N"], color="C3", ls=":", label=f"N = {SC['scelta'][c]['N']}")
        ax.set_title(c); ax.set_xlabel("celle valide nelle prime 24 h")
    axs[0].set_ylabel("F′(1 sett.) − C per nodo (eta' > 1 sett.)"); axs[0].legend(fontsize=8)
    a.figure.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(); fig.savefig(a.figure / "e7_stadio1.png", dpi=150)
    print("\n" + "=" * 84)
    print(f"IPOTESI (D1 < 0 sotto soglia ovunque il gruppo esiste, {len(sotto)} gruppi): "
          f"{'non verificabile' if vale is None else ('VALE' if vale else 'NON vale')}")
    print(f"(i) ipotesi fallita in almeno un gruppo: {'si' if fallita else 'no'}")
    print(f"(ii) rho(v o v7, D1) negativa che esclude lo zero in >= 2 citta' nell'ep. 1 o in 2 episodi: "
          f"{'si' if aperta else 'no'} (v {cond_rho['v']['vale']}, v7 {cond_rho['v7']['vale']})")
    if anomalie:
        print(f"ANOMALIE (rho positiva che esclude lo zero): {anomalie}")
    print(f"STADIO 2a (mascheramento del nodo nuovo): {'SI ESEGUE' if R['decisione']['stadio_2a'] else 'NON si esegue'}")
    print(f"  salvato in {a.out / 'e7_stadio1.json'}, figura {a.figure / 'e7_stadio1.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
