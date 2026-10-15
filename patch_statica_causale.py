#!/usr/bin/env python3
"""
Ramo esecutore/statica-causale — la statica causale diventa la predefinita (correzione del difetto 21).
========================================================================================================
Dopo E14 (stadi 0, A, B): `OR3_STATICA` assente vale **causale** (= variante (a) dello stadio B:
iniziali media di m_r su [0, t0), nuovi media su (t0, t0 + 24 h]); `--statica=congelata` (o
`OR3_STATICA=congelata`) riproduce la campagna del Paper 1 bit per bit. Tocca:

  inserimento.py        predefinita `causale`; `t0_installazione(contesto, fine_periodo)`;
                        `statica_addestramento(D, nodi, cfg, contesto)` per l'addestramento;
                        `adatta_F` e `valuta_prova` passano da `statica_cella`;
                        `argomento_statica(ap)` / `applica_statica(valore)` per l'interruttore `--statica`
  addestramento.py      la statica dell'addestramento (r. 801) da `statica_addestramento`, non costruita a mano
  seleziona_F.py, esegui_e6.py (seleziona-F), esegui_e6a.py (seleziona-F), esegui_refresh.py,
  costi_e4.py, sensibilita_rho_e2.py        statica della cella da `statica_cella`
  18 esecutori          `--statica {congelata,causale,a,b,c}` (predefinito: ambiente, poi causale)
  collauda_protocolli   fissa `congelata` (deve RIPRODURRE un punto E della campagna)
  checks/preflight.py   controllo 15 (E14, n. 8): statica identica al bit con m_r perturbata dopo t0 + 24 h

Uso (dalla radice OR3/):

    poetry run python patch_statica_causale.py
"""
import py_compile
import sys
from pathlib import Path

PARSE = "    a = ap.parse_args()\n"
PARSE_NUOVO = ('''    from evoluzione.esperimenti.inserimento import applica_statica, argomento_statica
    argomento_statica(ap)
    a = ap.parse_args()
    applica_statica(a.statica)
''')
ESECUTORI = [f"evoluzione/esperimenti/{n}.py" for n in (
    "esegui_inserimento", "esegui_E", "esegui_f0", "esegui_e2", "ricostruisci_predizioni", "veterani_e3",
    "riselezione_rmon_test", "esegui_e4", "esegui_e5", "esegui_e6", "esegui_e6a", "esegui_e8", "seleziona_F",
    "esegui_refresh", "costi_e4", "sensibilita_rho_e2")] + ["evoluzione/analisi/e14b_livelli.py", "checks/preflight.py"]

SOST = {
    "evoluzione/esperimenti/inserimento.py": [(
        '''VARIANTI_STATICA = ("congelata", "a", "b", "c")
L24_STATICA = 96


def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA` (E14); assente = congelata."""
    v = os.environ.get("OR3_STATICA", "") or "congelata"
    if v not in VARIANTI_STATICA:
        raise ValueError(f"OR3_STATICA={v!r}: ammessi {VARIANTI_STATICA}")
    return v
''',
        '''VARIANTI_STATICA = ("congelata", "causale", "a", "b", "c")
STATICA_PREDEFINITA = "causale"      # dopo E14 (difetto 21): causale; `congelata` riproduce la campagna
L24_STATICA = 96


def variante_statica() -> str:
    """La variante della statica, da `OR3_STATICA`; assente = `causale` (variante (a) di E14).
    `congelata` e' la statica non causale della campagna del Paper 1 (difetto 21)."""
    v = os.environ.get("OR3_STATICA", "") or STATICA_PREDEFINITA
    if v not in VARIANTI_STATICA:
        raise ValueError(f"OR3_STATICA={v!r}: ammessi {VARIANTI_STATICA}")
    return v


def argomento_statica(ap):
    """`--statica`: l'interruttore degli esecutori; assente, vale l'ambiente e poi la predefinita."""
    ap.add_argument("--statica", choices=VARIANTI_STATICA, default=None,
                    help=f"statica per nodo: congelata (campagna Paper 1, non causale) oppure causale "
                         f"(predefinita); a, b, c = varianti di E14 (OR3_STATICA)")
    return ap


def applica_statica(valore):
    """Scrive `OR3_STATICA` per il processo e per i figli (`spawn` eredita l'ambiente)."""
    if valore:
        os.environ["OR3_STATICA"] = valore
    return variante_statica()


def t0_installazione(contesto: str, fine_periodo=None) -> int:
    """Il t0 dell'episodio: `fine_periodo` se dato (E5 episodi 2 e 3, E6: il periodo finisce a t0),
    altrimenti il calendario di prova del contesto."""
    if fine_periodo is not None:
        return int(fine_periodo)
    if contesto.startswith("PEMS08"):
        from evoluzione.esperimenti.esegui_e6 import T0_PROVA
        return int(T0_PROVA)
    if contesto.startswith("PEMS04"):
        from evoluzione.esperimenti.esegui_e6a import T0_PROVA
        return int(T0_PROVA)
    from evoluzione.esperimenti.esegui_inserimento import CALENDARIO
    return int(CALENDARIO[contesto][0])


def statica_addestramento(D, nodi, cfg, contesto):
    """La statica dell'ADDESTRAMENTO (addestramento.py): `statiche(D)` passata da `statica_cella`
    con i nodi nuovi dichiarati dalla configurazione (vuoti per E, E') e il t0 dell'episodio."""
    nn = np.asarray(cfg.get("nodi_nuovi", []), dtype="int64")
    t0 = t0_installazione(contesto, cfg.get("fine_periodo"))
    return statica_cella(statiche(D), D, nodi, nn, t0, int(cfg.get("seme_dichiarato", 0)))
'''), (
        '''    if v in ("a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v == "a":
''',
        '''    if v in ("causale", "a", "b"):
        cov_c = m[:t0].mean(0)
        stat[:, 0] = cov_c.astype("float32")
        if v in ("causale", "a"):
'''), (
        '''        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1)
        a           iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
''',
        '''        congelata   `stat` com'e' (bit per bit; la campagna del Paper 1, non causale)
        causale, a  iniziali: media di m_r su [0, t0); nn: media su (t0, t0 + 24 h]
'''), (
        '''    stat = statiche(D) if stat is None else stat
    m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
''',
        '''    if stat is None:
        stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0_installazione(c), int(seme_torch))
    m, forn = copia_da_E(dE, nodi_in, nodi["prova"], D_STAT)
'''), (
        '''    x = _canali(D, nr, nv)
    stat = statiche(D)
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
''',
        '''    x = _canali(D, nr, nv)
    stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0_installazione(c), int(s))
    w = torch.as_tensor(carica_pesi(out / "pesi_griglia", c, p).vettore(),
''')],
    "evoluzione/esperimenti/addestramento.py": [(
        '''    stat = torch.as_tensor(np.stack([
        D["m_r"].mean(0), np.zeros(K), np.ones(K), np.zeros(K), np.ones(K)],
        1).astype("float32"))
''',
        '''    from evoluzione.esperimenti.inserimento import statica_addestramento
    stat = torch.as_tensor(statica_addestramento(D, nodi, cfg, E.contesto))   # causale; congelata = campagna
''')],
    "evoluzione/esperimenti/seleziona_F.py": [(
        '''            K = D["r"].shape[1]
            stat = np.stack([D["m_r"].mean(0), np.zeros(K), np.ones(K),
                             np.zeros(K), np.ones(K)], 1).astype("float32")
''',
        '''            from evoluzione.esperimenti.inserimento import statica_cella, statiche
            stat = statica_cella(statiche(D), D, nodi, nodi["validazione"], t0v, 0)
''')],
    "evoluzione/esperimenti/esegui_e6.py": [(
        '''        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0v, t1v, fine_v, _ = episodio("validazione", D)
        nodi_ep = nodi["validazione"]
        w = torch.as_tensor(carica_pesi(out / "pesi_pems08", c, p).vettore(), dtype=torch.float32)
''',
        '''        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0v, t1v, fine_v, _ = episodio("validazione", D)
        nodi_ep = nodi["validazione"]
        from evoluzione.esperimenti.inserimento import statica_cella
        stat = statica_cella(stat, D, nodi, nodi_ep, t0v, 0)
        w = torch.as_tensor(carica_pesi(out / "pesi_pems08", c, p).vettore(), dtype=torch.float32)
''')],
    "evoluzione/esperimenti/esegui_e6a.py": [(
        '''        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0v, t1v, fine_v, _ = episodio("validazione", D)
        nodi_ep = nodi["validazione"]
        w = torch.as_tensor(carica_pesi(out / DIR_PESI, c, p).vettore(), dtype=torch.float32)
''',
        '''        D, ok, nodi, ist, x, stat = _dati(c, out)
        t0v, t1v, fine_v, _ = episodio("validazione", D)
        nodi_ep = nodi["validazione"]
        from evoluzione.esperimenti.inserimento import statica_cella
        stat = statica_cella(stat, D, nodi, nodi_ep, t0v, 0)
        w = torch.as_tensor(carica_pesi(out / DIR_PESI, c, p).vettore(), dtype=torch.float32)
''')],
    "evoluzione/esperimenti/esegui_refresh.py": [(
        '''            x = _canali(D, nr, nv)
            stat = statiche(D)
            pesi = np.asarray(carica_pesi(
''',
        '''            x = _canali(D, nr, nv)
            from evoluzione.esperimenti.inserimento import statica_cella
            stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0, 0)
            pesi = np.asarray(carica_pesi(
''')],
    "evoluzione/esperimenti/costi_e4.py": [(
        '''    x = _canali(D, nr, nv)
    stat = statiche(D)
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
''',
        '''    x = _canali(D, nr, nv)
    from evoluzione.esperimenti.inserimento import statica_cella
    stat = statica_cella(statiche(D), D, nodi, nn, t0, int(s))
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", c, p).vettore(), dtype="float64")
''')],
    "evoluzione/esperimenti/sensibilita_rho_e2.py": [(
        '''    x = _canali(D, nr, nv)
    stat = statiche(D)
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", CONTESTO, PARTIZIONE)
''',
        '''    x = _canali(D, nr, nv)
    from evoluzione.esperimenti.inserimento import statica_cella
    stat = statica_cella(statiche(D), D, nodi, nodi["prova"], t0, 0)
    pesi = np.asarray(carica_pesi(out / "pesi_griglia", CONTESTO, PARTIZIONE)
''')],
    "evoluzione/esperimenti/collauda_protocolli.py": [(
        '''from evoluzione.esperimenti.addestramento import addestra_una  # noqa: E402
''',
        '''from evoluzione.esperimenti.addestramento import addestra_una  # noqa: E402

# Il protocollo STORICO deve RIPRODURRE un punto E della campagna: statica congelata
# (non causale, difetto 21), come allora. Fissata qui, non dall'ambiente.
import os  # noqa: E402
os.environ["OR3_STATICA"] = "congelata"
''')],
    "checks/preflight.py": [(
        '''    n_ok = sum(1 for _, o, _ in ESITI if o)
''',
        '''    # 15. causalita' della STATICA per nodo (E14, controllo n. 8): con m_r perturbata dopo
    #     t0 + 24 h la statica della cella non cambia di un bit; la statica congelata
    #     (difetto 21) cambia, e qui BLOCCA.
    import os
    from evoluzione.esperimenti.inserimento import (L24_STATICA, statica_cella, statiche,
                                                     t0_installazione, variante_statica)
    v_st = variante_statica(); t0i = t0_installazione(c)
    D3 = {k: (val.copy() if isinstance(val, np.ndarray) else val) for k, val in D.items()}
    D3["m_r"] = D3["m_r"].copy()
    D3["m_r"][t0i + L24_STATICA + 1:] = rng.random(D3["m_r"][t0i + L24_STATICA + 1:].shape) < 0.5
    s1 = statica_cella(statiche(D), D, nodi, nodi["prova"], t0i, a.seme)
    s2 = statica_cella(statiche(D3), D3, nodi, nodi["prova"], t0i, a.seme)
    cong_cambia = not np.array_equal(statiche(D), statiche(D3))
    v("15", "statica per nodo IDENTICA AL BIT con m_r perturbata dopo t0 + 24 h (E14, n. 8)",
      v_st != "congelata" and np.array_equal(s1, s2),
      f"statica «{v_st}», t0 {t0i}, scarto massimo {float(np.abs(s1 - s2).max()):.3e}; "
      f"la statica congelata {'cambia' if cong_cambia else 'non cambia'} con la stessa perturbazione"
      + ("" if v_st != "congelata" else " — congelata = non causale (difetto 21): solo per riprodurre la campagna"))

    n_ok = sum(1 for _, o, _ in ESITI if o)
'''), (
        '''Preflight — i tredici controlli della sezione 13, prima di ogni campagna.
''',
        '''Preflight — i controlli della sezione 13 (piu' il 14 e il 15), prima di ogni campagna.
''')],
}


def main() -> int:
    for f, coppie in SOST.items():
        p = Path(f); t = p.read_text()
        for vecchio, nuovo in coppie:
            assert t.count(vecchio) == 1, f"{f}: atteso una volta:\\n{vecchio}"
            t = t.replace(vecchio, nuovo)
        p.write_text(t)
    for f in ESECUTORI:
        p = Path(f); t = p.read_text()
        assert t.count(PARSE) == 1, f"{f}: `a = ap.parse_args()` atteso una volta"
        p.write_text(t.replace(PARSE, PARSE_NUOVO))
    for f in sorted(set(SOST) | set(ESECUTORI)):
        py_compile.compile(f, doraise=True)
        print(f"  {f}: compila")
    print(f"  fatto: {len(SOST)} file con sostituzioni, {len(ESECUTORI)} esecutori con --statica")
    return 0


if __name__ == "__main__":
    sys.exit(main())
