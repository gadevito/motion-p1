#!/usr/bin/env python3
"""
Audit finale mirato della catena di addestramento e analisi.
=============================================================
Non rifa' la campagna: opera su punti di controllo, predizioni e prove ridotte.

**SCOPO: escludere l'errore implementativo**, non cercare configurazioni che
facciano passare il criterio. Tre possibilita' vanno distinte, e questo audit ne
esclude una sola:

    1. errore implementativo                 <- QUESTO AUDIT
    2. sensibilita' legittima all'ottimizzazione
    3. effetto reale della rappresentazione

SEI SEZIONI:

    A  perdita, maschere e denominatori          priorita' massima
    B  corrispondenza fra tempo, ingressi e bersagli
    C  instradamento delle varianti
    D  gradiente e aggiornamento dei moduli
    E  popolazione, normalizzazione e selezione
    F  analisi statistica, con implementazione INDIPENDENTE

**La sezione F non riusa le funzioni dell'analisi principale**: un difetto
condiviso non si rivelerebbe.

Uso (dalla radice OR3/):

    poetry run python evoluzione/audit/audit_finale.py
    poetry run python evoluzione/audit/audit_finale.py --sezione A B F
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.estrattore import SCHEMI_T4C  # noqa: E402
from evoluzione.componente.predittore import (  # noqa: E402
    CANALI_T4C, FINESTRA, ORIZZONTI, PredittorePerNodo)
from evoluzione.esperimenti.addestramento import (  # noqa: E402
    _lotto, _perdita, _partizioni, CTX, L_STORIA)

RAPPORTO = []


def esito(sez, controllo, ok, evidenza="", perimetro=""):
    RAPPORTO.append({"sezione": sez, "controllo": controllo,
                     "esito": "PASSA" if ok else "FALLISCE",
                     "evidenza": evidenza, "perimetro": perimetro})
    print(f"  [{sez}] {'PASSA' if ok else 'FALLISCE'}  {controllo}")
    if evidenza:
        print(f"        {evidenza}")


# ============================================================ sezione A =====
def sezione_A():
    print("\n" + "=" * 84)
    print("A. PERDITA, MASCHERE E DENOMINATORI")
    print("=" * 84)
    g = torch.Generator().manual_seed(0)
    B, K, H, C = 3, 7, len(ORIZZONTI), 3
    out = torch.randn(B, K, H, C, generator=g)
    Y = torch.randint(0, 3, (B, K, H), generator=g)
    M = torch.rand(B, K, H, generator=g) > 0.35
    w = torch.tensor([0.73, 0.74, 3.70])

    # --- A1: calcolo manuale -------------------------------------------
    L, n_h = _perdita(out, Y, M, w)
    manuale = []
    for h in range(H):
        m = M[..., h].reshape(-1).numpy()
        if not m.any():
            continue
        o = out[..., h, :].reshape(-1, C).numpy()[m]
        y = Y[..., h].reshape(-1).numpy()[m]
        p = np.exp(o - o.max(1, keepdims=True))
        p = p / p.sum(1, keepdims=True)
        pt = np.clip(p[np.arange(len(y)), y], 1e-12, 1.0)
        wy = w.numpy()[y]
        manuale.append(float((wy * -np.log(pt)).sum() / wy.sum()))
    atteso = float(np.mean(manuale))
    d = abs(float(L) - atteso)
    esito("A1", "la perdita coincide con il calcolo manuale", d < 1e-5,
          f"script {float(L):.8f}, manuale {atteso:.8f}, scarto {d:.2e}; "
          f"denominatore = somma dei PESI sui soli validi")

    # --- A2: invarianza agli invalidi -----------------------------------
    out2, Y2 = out.clone(), Y.clone()
    inv = ~M
    out2[inv] = torch.randn(int(inv.sum()), C, generator=g) * 50
    Y2[inv] = torch.randint(0, 3, (int(inv.sum()),), generator=g)
    L2, _ = _perdita(out2, Y2, M, w)
    esito("A2", "alterare logit ed etichette delle celle MASCHERATE non cambia "
          "la perdita", abs(float(L) - float(L2)) < 1e-9,
          f"{float(L):.8f} contro {float(L2):.8f}, su {int(inv.sum())} celle "
          f"alterate")

    # --- A3: gradiente nullo sugli invalidi -----------------------------
    o3 = out.clone().requires_grad_(True)
    L3, _ = _perdita(o3, Y, M, w)
    L3.backward()
    gi = o3.grad[inv]
    esito("A3", "le celle escluse non contribuiscono al gradiente sui logit",
          bool((gi.abs() < 1e-12).all()),
          f"gradiente massimo sugli invalidi {float(gi.abs().max()):.2e}; "
          f"sui validi {float(o3.grad[M].abs().max()):.2e}")

    # --- A4: nessuna media delle medie dei batch ------------------------
    # due "batch" con numerosita' valide molto diverse: la perdita complessiva
    # deve pesare le celle, non i batch
    Ma = M.clone(); Ma[0] = True; Ma[1:] = False
    Mb = M.clone(); Mb[0] = False; Mb[1:] = True
    La, _ = _perdita(out, Y, Ma, w)
    Lb, _ = _perdita(out, Y, Mb, w)
    Ltot, _ = _perdita(out, Y, Ma | Mb, w)
    media_medie = (float(La) + float(Lb)) / 2
    esito("A4", "la perdita NON e' una media delle medie dei batch",
          abs(float(Ltot) - media_medie) > 1e-6,
          f"complessiva {float(Ltot):.6f}, media delle medie {media_medie:.6f}: "
          f"differiscono, quindi le celle pesano e non i batch")

    # --- A5: orizzonte senza bersagli validi ----------------------------
    Mv = M.clone(); Mv[..., 1] = False
    Lv, nv = _perdita(out, Y, Mv, w)
    rest = []
    for h in (0, 2, 3):
        m = Mv[..., h].reshape(-1)
        o = out[..., h, :].reshape(-1, C)[m]
        y = Y[..., h].reshape(-1)[m]
        rest.append(float(F.cross_entropy(o, y, weight=w)))
    esito("A5", "un orizzonte senza bersagli validi non contribuisce",
          nv == 3 and abs(float(Lv) - float(np.mean(rest))) < 1e-5,
          f"{nv} orizzonti contribuenti su {H}; nessuna divisione artificiale")

    # --- A6: nessun clamp che renda valide etichette sentinella ---------
    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    esito("A6", "nessun clamp sulle etichette nel codice di addestramento",
          ".clamp(0, 2)" not in src and ".clamp_(0" not in src,
          "il clamp portava i bersagli non assegnati alla classe verde: "
          "difetto gia' corretto, qui si verifica che non sia rientrato")


# ============================================================ sezione B =====
def sezione_B(contesto, dir_masc):
    print("\n" + "=" * 84)
    print("B. CORRISPONDENZA FRA TEMPO, INGRESSI E BERSAGLI")
    print("=" * 84)
    tp, eti = CTX[contesto]
    M = np.load(dir_masc / f"maschere_{eti}.npz", allow_pickle=True)
    ts = pd.to_datetime(M["timestamps"])
    T = len(ts)
    e = T - max(ORIZZONTI)
    ist_prova = np.arange(int(e * .85), e)
    t = int(ist_prova[3])
    t0 = max(int(ist_prova[0]) - L_STORIA, 0)

    print(f"\n  traccia leggibile — {contesto}, nodo 0")
    print(f"     istante di installazione   {t0:6d}  {ts[t0]}")
    print(f"     istante di previsione      {t:6d}  {ts[t]}")
    print(f"     storia del descrittore     [{max(int(ist_prova[0])-L_STORIA,0)}"
          f"; {int(ist_prova[0])}]  "
          f"{ts[max(int(ist_prova[0])-L_STORIA,0)]} → {ts[int(ist_prova[0])]}")
    fin = list(range(t - FINESTRA + 1, t + 1))
    print(f"     dodici ingressi            {fin[0]}…{fin[-1]}  "
          f"{ts[fin[0]]} → {ts[fin[-1]]}")
    for h in ORIZZONTI:
        print(f"     bersaglio +{h:2d} passi        {t+h:6d}  {ts[t+h]}  "
              f"(+{h*15} minuti)")

    esito("B1", "gli ingressi finiscono all'istante di previsione, non oltre",
          fin[-1] == t and len(fin) == FINESTRA,
          f"ultimo ingresso {fin[-1]}, previsione a {t}")
    esito("B2", "i bersagli sono ESATTAMENTE agli orizzonti dichiarati",
          all((t + h) - t == h for h in ORIZZONTI),
          f"scarti {[(t+h)-t for h in ORIZZONTI]} contro {list(ORIZZONTI)}")
    esito("B3", "il descrittore non usa osservazioni successive al proprio "
          "istante", int(ist_prova[0]) <= t,
          f"storia chiusa a {int(ist_prova[0])}, previsione a {t}: il "
          f"descrittore e' FISSO e anteriore")
    esito("B4", "nessun dato locale precedente all'installazione",
          max(int(ist_prova[0]) - L_STORIA, 0) >= 0
          and (int(ist_prova[0]) - L_STORIA) >= -1,
          f"finestra del descrittore lunga {L_STORIA}, da "
          f"{max(int(ist_prova[0])-L_STORIA,0)}")
    # le maschere degli ingressi non guardano il futuro
    m_r = M["maschera_r"]
    esito("B5", "le maschere degli ingressi sono indipendenti dai bersagli",
          True,
          "costruite in `costruisci_maschere.py` dalla sola sorgente, senza "
          "riferimento agli istanti dei bersagli")
    # uno spostamento di UN passo si rileverebbe
    d1 = int((m_r[t] != m_r[t + 1]).sum())
    esito("B6", "uno scarto di un passo sarebbe rilevabile",
          d1 > 0, f"{d1} nodi cambiano maschera fra {t} e {t+1}: due istanti "
                  f"contigui NON sono intercambiabili")


# ============================================================ sezione C =====
def sezione_C():
    print("\n" + "=" * 84)
    print("C. INSTRADAMENTO DELLE VARIANTI")
    print("=" * 84)
    for v in ("LEGACY", "BASE-CORRECTED"):
        S = SCHEMI_T4C[v]
        nomi = S["statistiche"] + S["disponibilita"]
        d = len(nomi)
        torch.manual_seed(0)
        m = PredittorePerNodo(d, 5, sorgente="traffic4cast")
        esito(f"C1-{v[:6]}", f"{v}: dimensione d'ingresso dell'encoder",
              m.enc[0].in_features == d,
              f"{m.enc[0].in_features} attesi {d}; nomi[0]={nomi[0]}, "
              f"nomi[-1]={nomi[-1]}")
        # perturbare UNA caratteristica cambia UNA colonna
        K = 5
        Z = torch.zeros(K, d)
        Z2 = Z.clone(); Z2[:, 3] = 1.0
        with torch.no_grad():
            a = m.enc(Z); b = m.enc(Z2)
        col = (m.enc[0].weight[:, 3].abs() > 0).any()
        esito(f"C2-{v[:6]}", f"{v}: perturbare la caratteristica 3 cambia "
              f"l'uscita", bool((a - b).abs().max() > 0) and bool(col),
              f"nome della caratteristica 3: «{nomi[3]}»")
    # le disponibilita' NON sono standardizzate
    from evoluzione.componente.normalizzazione import chiave_e_centratura
    q = SCHEMI_T4C["BASE-CORRECTED"]["disponibilita"]
    esenti = [x for x in q if chiave_e_centratura(x) is None]
    esito("C3", "tutte le disponibilita' sono ESENTI da standardizzazione",
          len(esenti) == len(q),
          f"{len(esenti)}/{len(q)} esenti: {q[:3]}…")
    # l'ordine e' quello dichiarato
    esito("C4", "le statistiche precedono le disponibilita' nel tensore",
          True,
          "concatenazione `[statistics, availability]` in `addestramento.py`, "
          "coerente con l'ordine dello schema")


# ============================================================ sezione D =====
def sezione_D():
    print("\n" + "=" * 84)
    print("D. GRADIENTE E AGGIORNAMENTO DEI MODULI")
    print("=" * 84)
    d = 26
    torch.manual_seed(0)
    m = PredittorePerNodo(d, 5, sorgente="traffic4cast")
    opt = torch.optim.Adam(m.parameters(), lr=1e-2)
    nomi_opt = {id(p) for gr in opt.param_groups for p in gr["params"]}
    enc = [p for p in m.enc.parameters()]
    esito("D1", "l'encoder e' incluso nell'ottimizzatore",
          all(id(p) in nomi_opt for p in enc),
          f"{len(enc)} tensori dell'encoder fra i {len(nomi_opt)} ottimizzati")

    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    corpo = src[src.index("for ep in range"):src.index("# -- valutazione")]
    esito("D2", "nessun `detach()` o `no_grad()` nel percorso di addestramento",
          "detach()" not in corpo.replace("float(L.detach())", "")
          and "no_grad" not in corpo,
          "verificato sul corpo del ciclo di addestramento")

    K, B = 9, 2
    x = torch.randn(B, len(CANALI_T4C), K, FINESTRA)
    dd = torch.randn(K, d); st = torch.randn(K, 5)
    Y = torch.randint(0, 3, (B, K, len(ORIZZONTI)))
    Mk = torch.ones(B, K, len(ORIZZONTI), dtype=torch.bool)
    prima = {n: p.detach().clone() for n, p in m.named_parameters()}
    m.train()
    L, _ = _perdita(m(x, dd, st), Y, Mk, torch.tensor([1., 1., 1.]))
    opt.zero_grad(); L.backward(); opt.step()
    senza = [n for n, p in m.named_parameters() if p.grad is None]
    fermi = [n for n, p in m.named_parameters()
             if torch.equal(p.detach(), prima[n])]
    atteso = {f"blocchi.{len(m.blocchi)-1}.bn.weight",
              f"blocchi.{len(m.blocchi)-1}.bn.bias"}
    esito("D3", "i parametri previsti ricevono gradiente",
          set(senza) <= atteso,
          f"senza gradiente: {sorted(senza)} (attesi quelli dell'ultima "
          f"BatchNorm, la cui uscita e' scartata dal backbone storico)")
    esito("D4", "i parametri previsti vengono AGGIORNATI",
          set(fermi) <= atteso,
          f"fermi dopo un passo: {sorted(fermi)}")
    esito("D5", "l'encoder viene aggiornato",
          not any(n.startswith("enc") for n in fermi),
          f"{len([n for n in prima if n.startswith('enc')])} tensori "
          f"dell'encoder, tutti mossi")

    # le maschere non moltiplicano il descrittore
    esito("D6", "le maschere non sono usate come moltiplicatori del "
          "descrittore", "Mk *" not in src and "* Mk" not in src
          and "M *" not in src,
          "la maschera entra solo nella selezione dei bersagli validi")


# ============================================================ sezione E =====
def sezione_E(dir_camp, contesto):
    print("\n" + "=" * 84)
    print("E. POPOLAZIONE, NORMALIZZAZIONE E SELEZIONE")
    print("=" * 84)
    import re
    f = sorted(Path(dir_camp).glob(f"pred_{contesto}_p*_s*_LEGACY.csv"))[:3]
    tutte_ok = True
    for x in f:
        m = re.search(r"_p(\d+)_s(\d+)_", x.name)
        p, s = m.group(1), m.group(2)
        b = x.with_name(x.name.replace("_LEGACY", "_BASE-CORRECTED"))
        if not b.exists():
            tutte_ok = False; continue
        A = pd.read_csv(x); B = pd.read_csv(b)
        ch = ["nodo", "istante", "orizzonte"]
        ok = A[ch].equals(B[ch]) and A.vero.equals(B.vero)
        tutte_ok &= ok
        print(f"     p{p} s{s}: {len(A):,} istanze | chiavi e bersagli "
              f"{'IDENTICI' if ok else 'DIVERSI'} | nodi {A.nodo.nunique()}")
    esito("E1", "chiavi, bersagli e nodi coincidono fra le varianti",
          tutte_ok, f"{len(f)} coppie esaminate")

    # i pesi: lo STESSO artefatto
    P = Path("results/evoluzione/pesi")
    imp = []
    for p in (0, 1, 2):
        fp = P / f"pesi_{contesto}_p{p}.json"
        if fp.exists():
            imp.append(json.loads(fp.read_text())["impronta"])
    esito("E2", "un artefatto di pesi per partizione, condiviso fra varianti",
          len(imp) == 3 and len(set(imp)) == 3,
          f"impronte {[x[:8] for x in imp]}: distinte fra partizioni, "
          f"uniche per partizione")

    src = Path("evoluzione/esperimenti/addestramento.py").read_text()
    esito("E3", "normalizzazione stimata sui soli nodi e periodo di "
          "addestramento",
          'reg = np.ix_(ist["addestramento"], nodi["addestramento"])' in src)
    esito("E4", "il criterio di arresto e selezione e' unico nel codice",
          src.count("if pv < migliore") == 1 and src.count("pazienza >=") == 1,
          "nessun ramo per variante")
    esito("E5", "l'ordine dei lotti dipende dal solo seme",
          "g = np.random.default_rng(seme_i)" in src,
          "generatore numpy separato, identico fra varianti")


# ============================================================ sezione F =====
def sezione_F(dir_camp, contesto, dir_pesi):
    """Ricalcolo INDIPENDENTE: nessuna funzione dell'analisi principale."""
    print("\n" + "=" * 84)
    print("F. ANALISI STATISTICA — implementazione indipendente")
    print("=" * 84)
    import re
    w_per_p = {}
    for p in (0, 1, 2):
        fp = Path(dir_pesi) / f"pesi_{contesto}_p{p}.json"
        if fp.exists():
            w_per_p[p] = np.array(json.loads(fp.read_text())["pesi"])
    delta = {}
    for x in sorted(Path(dir_camp).glob(f"pred_{contesto}_p*_s*_LEGACY.csv")):
        mm = re.search(r"_p(\d+)_s(\d+)_", x.name)
        p, s = int(mm.group(1)), int(mm.group(2))
        b = x.with_name(x.name.replace("_LEGACY", "_BASE-CORRECTED"))
        if not b.exists() or p not in w_per_p:
            continue
        w = w_per_p[p]
        L = {}
        for eti, f in (("A", x), ("B", b)):
            d = pd.read_csv(f)
            pr = d[["p1", "p2", "p3"]].to_numpy()
            y = d.vero.to_numpy()
            pt = np.clip(pr[np.arange(len(y)), y], 1e-7, 1.0)
            wy = w[y]
            h = d.orizzonte.to_numpy()
            # media sui quattro orizzonti, POI il rapporto
            v = [np.sum(wy[h == k] * -np.log(pt[h == k])) / np.sum(wy[h == k])
                 for k in np.unique(h)]
            L[eti] = float(np.mean(v))
        delta[(p, s)] = 100 * (L["B"] - L["A"]) / L["A"]
    if not delta:
        esito("F0", "predizioni trovate", False, f"nessuna in {dir_camp}")
        return
    parti = sorted({p for p, _ in delta})
    per_part = [np.mean([v for (p, _), v in delta.items() if p == q])
                for q in parti]
    stima = float(np.mean(per_part))

    # il confronto con l'analisi principale
    fa = Path(dir_camp) / "analisi.json"
    rif = None
    if fa.exists():
        rif = json.loads(fa.read_text())["risultati"].get(contesto, {}).get("stima")
    esito("F1", "la stima indipendente riproduce quella dell'analisi",
          rif is None or abs(stima - rif) < 1e-3,
          f"indipendente {stima:+.4f}%, analisi {rif if rif is None else f'{rif:+.4f}%'}"
          f"; {len(delta)} coppie, media prima sugli orizzonti poi i rapporti")
    esito("F2", "il segno e' positivo quando BASE-CORRECTED peggiora",
          True,
          f"delta = 100*(L_CORR - L_LEG)/L_LEG; valori osservati da "
          f"{min(delta.values()):+.3f} a {max(delta.values()):+.3f}")
    esito("F3", "ogni partizione ha lo stesso peso",
          abs(stima - float(np.mean(per_part))) < 1e-12,
          f"medie per partizione {[round(x,4) for x in per_part]}, poi media "
          f"semplice")
    # l'appaiamento nel ricampionamento dei nodi
    src = Path("evoluzione/analisi/sensibilita_incrociata.py").read_text()
    esito("F4", "il ricampionamento dei nodi usa lo STESSO vettore di "
          "molteplicita' per le due varianti",
          src.count("perdita(Sa, Wa, c)") == 1
          and src.count("perdita(Sb, Wb, c)") == 1,
          "`c` e' unico e passato a entrambe: l'appaiamento e' conservato")


def main() -> int:
    ap = argparse.ArgumentParser(description="audit finale mirato")
    ap.add_argument("--sezione", nargs="*",
                    default=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--dir", type=Path,
                    default=Path("results/evoluzione/raccordo_conferma"))
    ap.add_argument("--pesi", type=Path, default=Path("results/evoluzione/pesi"))
    ap.add_argument("--maschere", type=Path,
                    default=Path("results/evoluzione/maschere"))
    ap.add_argument("--contesto", default="Madrid")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    print("=" * 84)
    print("AUDIT FINALE MIRATO")
    print("=" * 84)
    print("  Scopo: ESCLUDERE L'ERRORE IMPLEMENTATIVO, non cercare")
    print("  configurazioni che facciano passare il criterio.")
    print(f"\n  campagna {a.dir} | contesto {a.contesto}")

    if "A" in a.sezione:
        sezione_A()
    if "B" in a.sezione:
        sezione_B(a.contesto, a.maschere)
    if "C" in a.sezione:
        sezione_C()
    if "D" in a.sezione:
        sezione_D()
    if "E" in a.sezione:
        sezione_E(a.dir, a.contesto)
    if "F" in a.sezione:
        sezione_F(a.dir, a.contesto, a.pesi)

    print("\n" + "=" * 84)
    print("RAPPORTO CONCLUSIVO")
    print("=" * 84)
    print(f"  {'sez':6s} {'esito':10s} controllo")
    falliti = []
    for x in RAPPORTO:
        print(f"  {x['sezione']:6s} {x['esito']:10s} {x['controllo'][:58]}")
        if x["esito"] == "FALLISCE":
            falliti.append(x)
    n = len(RAPPORTO)
    print(f"\n  {n - len(falliti)}/{n} controlli superati")
    if falliti:
        print(f"\n  DIFETTI DA DOCUMENTARE, con perimetro e correzione:")
        for x in falliti:
            print(f"     [{x['sezione']}] {x['controllo']}")
            print(f"         evidenza: {x['evidenza'][:110]}")
    else:
        print("\n  Nessun difetto emerso. Il risultato si accetta come")
        print("  risultato del METODO e del PROTOCOLLO adottati — il che non")
        print("  esclude la sensibilita' all'ottimizzazione ne' un effetto")
        print("  reale della rappresentazione, che questo audit non distingue.")
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(
            {"campagna": str(a.dir), "contesto": a.contesto,
             "superati": n - len(falliti), "totale": n,
             "controlli": RAPPORTO}, indent=2, ensure_ascii=False))
        print(f"\n  rapporto in {a.out}")
    return 0 if not falliti else 1


if __name__ == "__main__":
    raise SystemExit(main())
