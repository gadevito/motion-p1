#!/usr/bin/env python3
"""
Patch a `stats_tests.py`: test di Friedman del protocollo e valore p esatto.
============================================================================
NON CANCELLA NULLA. Modifica `stats_tests.py` in luogo dopo averne salvato una
copia; se la patch e' gia' applicata non fa nulla.

DUE COSE CHE AGGIUNGE.

  1. IL TEST DEL PROTOCOLLO. §7.2.10 dichiara il test di Friedman sui QUATTRO
     modelli presenti in tutte le configurazioni — le due varianti di Graph
     WaveNet, il metodo tabellare a parita' di informazione e il riferimento
     non addestrato — sui blocchi disponibili. `stats_tests.py` calcola invece
     il test su TUTTI i modelli comuni e quello ristretto alla fascia di testa:
     nessuno dei due e' quello dichiarato, ed e' la ragione per cui il valore
     riportato nel documento non e' riproducibile dallo script.

  2. IL VALORE P ESATTO PER ENUMERAZIONE. La procedura attuale usa permutazione
     campionaria a 200.000 estrazioni. Con quattro trattamenti e sei blocchi il
     valore vero e' dell'ordine di 2e-6: il campionamento non vedrebbe quasi mai
     un successo e restituirebbe il proprio limite inferiore, 1/(B+1) ~ 5e-6,
     sovrastimando il valore p di un fattore due e presentandolo come esito.

     L'enumerazione esatta di (k!)^n assegnazioni sarebbe proibitiva — 191
     milioni per quattro trattamenti e sei blocchi — ma i MULTIINSIEMI di
     permutazioni sono 475.020, e pesarli con il coefficiente multinomiale da'
     lo stesso valore in pochi secondi. La funzione ricade sul campionamento
     quando l'enumerazione non e' praticabile, e DICHIARA sempre quale delle due
     procedure ha usato, come §8.8.1 prescrive.

Uso (dalla radice OR3/):

    poetry run python patch_stats_friedman.py --verifica    # diagnosi
    poetry run python patch_stats_friedman.py               # applica
"""
from pathlib import Path
import argparse
import ast
import shutil
import sys

BLOCCO = '''

# --- aggiunto: valore p esatto per enumerazione dei multiinsiemi -------------
def _p_friedman_esatto(mat, q0, max_multiinsiemi=3_000_000):
    """Valore p esatto sotto l'ipotesi nulla di Friedman.

    Sotto l'ipotesi nulla ogni blocco contribuisce una permutazione dei ranghi
    1..k con uguale probabilita'. Anziche' enumerare (k!)^n assegnazioni si
    enumerano i MULTIINSIEMI di permutazioni, pesati con il coefficiente
    multinomiale: la statistica dipende infatti dalle sole SOMME dei ranghi, che
    non cambiano permutando l'ordine dei blocchi.

    Restituisce (p, numero di assegnazioni pesate) oppure (None, 0) se
    l'enumerazione non e' praticabile.
    """
    import itertools, math
    from collections import Counter
    nb, nk = mat.shape
    np_ = math.factorial(nk)
    if math.comb(np_ + nb - 1, nb) > max_multiinsiemi:
        return None, 0
    perm = list(itertools.permutations(range(1, nk + 1)))

    def _q(R):
        rm = np.asarray(R, float) / nb
        return 12 * nb / (nk * (nk + 1)) * ((rm - (nk + 1) / 2) ** 2).sum()

    tot = favor = 0
    for combo in itertools.combinations_with_replacement(range(len(perm)), nb):
        c = Counter(combo)
        w = math.factorial(nb)
        for v in c.values():
            w //= math.factorial(v)
        R = [sum(perm[i][j] for i in combo) for j in range(nk)]
        tot += w
        if _q(R) >= q0 - 1e-9:
            favor += w
    return favor / tot, tot
'''

CHIAMATA_VECCHIA = '''        q0 = Q(mat); rng = np.random.default_rng(0); B = 200000
        c = sum(Q(np.apply_along_axis(rng.permutation, 1, mat.copy())) >= q0-1e-9 for _ in range(B))
        pe = (c+1)/(B+1); pa = stats.chi2.sf(q0, nk-1)
        out(f"  {etichetta}: {nk} modelli x {nb} contesti -> chi2={q0:.2f}, "
            f"p asintotico({nk-1} gdl)={pa:.4g}, p ESATTO={pe:.4g}")'''

CHIAMATA_NUOVA = '''        q0 = Q(mat); pa = stats.chi2.sf(q0, nk-1)
        # esatto per enumerazione dove praticabile, campionario altrimenti:
        # con pochi trattamenti il campionamento non risolve valori p molto piccoli
        pe, n_ass = _p_friedman_esatto(mat, q0)
        if pe is not None:
            proc = f"ESATTO per enumerazione ({n_ass:,} assegnazioni)"
        else:
            rng = np.random.default_rng(0); B = 200000
            c = sum(Q(np.apply_along_axis(rng.permutation, 1, mat.copy())) >= q0-1e-9
                    for _ in range(B))
            pe = (c+1)/(B+1); proc = f"per permutazione campionaria ({B:,} estrazioni)"
        out(f"  {etichetta}: {nk} modelli x {nb} contesti -> chi2={q0:.3f}, "
            f"p asintotico({nk-1} gdl)={pa:.4g}, p {proc} = {pe:.4g}")'''

PROTOCOLLO = '''    # --- Friedman DEL PROTOCOLLO: i quattro modelli di §7.2.10 ---------------
    # Le due varianti di Graph WaveNet, il metodo tabellare a parita' di
    # informazione e il riferimento non addestrato: sono i quattro modelli
    # presenti in tutte le configurazioni sperimentali. E' il test dichiarato
    # nel disegno, ed e' quello il cui valore va citato nel documento.
    QUATTRO = ["gwn_adaptive", "gwn_none", "lgb_fair", "hist_prior"]
    prot = piv[piv.index.isin(QUATTRO)].dropna(axis=0)
    mancanti = [m for m in QUATTRO if m not in prot.index]
    if mancanti:
        out(f"  ATTENZIONE: Friedman del protocollo non eseguibile, mancano {mancanti}")
    else:
        _friedman(prot, "FRIEDMAN DEL PROTOCOLLO (§7.2.10)")
        out("    (i quattro modelli presenti in tutte le configurazioni)")
    out("")
'''


def main() -> int:
    ap = argparse.ArgumentParser(description="patch del test di Friedman")
    ap.add_argument("--file", type=Path, default=Path("stats_tests.py"))
    ap.add_argument("--verifica", action="store_true")
    a = ap.parse_args()

    if not a.file.exists():
        print(f"ERRORE: {a.file} non trovato", file=sys.stderr)
        return 1
    t = a.file.read_text()

    stato = []
    stato.append(("enumerazione esatta", "_p_friedman_esatto" in t))
    stato.append(("test del protocollo", "FRIEDMAN DEL PROTOCOLLO" in t))
    stato.append(("chiamata da sostituire", CHIAMATA_VECCHIA in t))
    stato.append(("punto di innesto", '_friedman(piv_all, "FRIEDMAN su tutti' in t))
    for k, v in stato:
        print(f"  {k:26s} {'presente' if v else 'assente'}")

    if stato[0][1] and stato[1][1]:
        print("\nla patch e' gia' applicata: nulla da fare")
        return 0
    if not stato[2][1] or not stato[3][1]:
        print("\nERRORE: lo schema atteso non corrisponde. Applicare a mano:", file=sys.stderr)
        print("  1. aggiungere la funzione `_p_friedman_esatto` a livello di modulo")
        print("  2. sostituire il blocco del campionamento dentro `_friedman`")
        print("  3. aggiungere il blocco del test del protocollo prima di `_friedman(piv_all, ...)`")
        return 2
    if a.verifica:
        print("\nnessuna modifica applicata (--verifica)")
        return 0

    copia = a.file.with_suffix(".py.prima_della_patch")
    shutil.copy(a.file, copia)
    print(f"\ncopia di sicurezza -> {copia}")

    t = t.replace(CHIAMATA_VECCHIA, CHIAMATA_NUOVA, 1)
    i = t.index('    _friedman(piv_all, "FRIEDMAN su tutti')
    t = t[:i] + PROTOCOLLO + t[i:]
    # La funzione va definita PRIMA di essere usata: `stats_tests.py` esegue a
    # livello di modulo e non ha un `def main()`, quindi inserirla in coda la
    # renderebbe indefinita al momento della chiamata. La si colloca subito
    # dopo gli import, individuati come ultima riga `import`/`from` in testa.
    righe = t.split("\n")
    ultimo = max(k for k, l in enumerate(righe[:80])
                 if l.startswith("import ") or l.startswith("from "))
    righe[ultimo + 1:ultimo + 1] = BLOCCO.strip("\n").split("\n") + [""]
    t = "\n".join(righe)

    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"ERRORE DI SINTASSI dopo la patch: {e}", file=sys.stderr)
        print(f"il file originale e' intatto in {copia}", file=sys.stderr)
        return 3
    a.file.write_text(t)
    print("PATCHATO, sintassi ok")
    print("\nAtteso sul perimetro a sei contesti: chi2 = 17,000 (massimo 18,000),")
    print("p esatto = 2,386e-06, ranghi medi 1,17 / 1,83 / 3,00 / 4,00.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
