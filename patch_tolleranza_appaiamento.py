#!/usr/bin/env python3
"""
Patch per la voce 22 del registro — tolleranza del controllo di appaiamento (E2).
===================================================================================
`verifica_appaiamento.py` ricalcola in numpy gli aggregati per nodo dalle probabilita'
salvate in float32 e li confronta con quelli salvati a `rtol = 1e-12`: una tolleranza
valida sulla stessa macchina (sul Mac lo scarto e' zero) ma non fra architetture. Sulla
NVIDIA Spark (aarch64, glibc) il `log` in float32 differisce di qualche ulp: scarto
relativo massimo per elemento 4,9e-9, sulla wCE di cella 3,8e-11, coerenza interna
(wCE dalle celle contro wCE dagli aggregati ricalcolati sulla stessa macchina) 1,2e-14
(`riproducibilita_spark.json`). A 1e-7 il controllo resta un controllo di identita'
dei DATI (uno scambio di nodi o di origini produce scarti di ordine 1) e smette di
essere un controllo di numerica.

Una sostituzione letterale; se il testo atteso non c'e' una volta sola, si ferma.

Uso (dalla radice OR3/):

    poetry run python patch_tolleranza_appaiamento.py
    poetry run python evoluzione/analisi/verifica_appaiamento.py
"""
from pathlib import Path

F = Path("evoluzione/analisi/verifica_appaiamento.py")
S = F.read_text()
VECCHIO = '''                # e gli aggregati salvati coincidono con quelli ricalcolati?
                if not np.allclose(A, z["A_per_nodo"], atol=0, rtol=1e-12):
'''
NUOVO = '''                # e gli aggregati salvati coincidono con quelli ricalcolati?
                # Tolleranza 1e-7, non 1e-12 (voce 22 del registro): le probabilita'
                # sono float32 e il ricalcolo su un'altra architettura (NVIDIA Spark,
                # aarch64/glibc, 12/10/2026) differisce per elemento fino a 4,9e-9
                # relativo (wCE di cella 3,8e-11; coerenza interna 1,2e-14). A 1e-7 il
                # controllo resta un controllo di identita' dei dati — nodi o origini
                # scambiati danno scarti di ordine 1 — e non di numerica.
                if not np.allclose(A, z["A_per_nodo"], atol=0, rtol=RTOL_APPAIAMENTO):
'''
n = S.count(VECCHIO)
assert n == 1, f"testo atteso trovato {n} volte, non 1"
S = S.replace(VECCHIO, NUOVO)
VECCHIO2 = '''from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)
'''
NUOVO2 = '''from evoluzione.esperimenti.ricostruisci_predizioni import (  # noqa: E402
    aggregati_per_nodo, wce_da_predizioni)

RTOL_APPAIAMENTO = 1e-7      # fra architetture: vedi il commento al controllo [4]
'''
n = S.count(VECCHIO2)
assert n == 1, f"import atteso trovato {n} volte, non 1"
S = S.replace(VECCHIO2, NUOVO2)
compile(S, str(F), "exec")
F.write_text(S)
print(f"  {F}: 2 sostituzioni, compila")
