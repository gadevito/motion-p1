#!/usr/bin/env python3
"""
Patch — le origini comuni di E6 (PEMS08 e PEMS04) scritte in un JSON dallo script di E6.
==========================================================================================
Oggi i conteggi stanno nel testo di `CONGELAMENTO_E6.md` §1: PEMS08 calcolato dal generatore
da una sola cella, PEMS04 («168») scritto come costante nel generatore. Due sostituzioni letterali:

  1. `esegui_e6.py`: fase nuova `origini` — da TUTTE le celle di prova di `predizioni_e6` e
     `predizioni_e6a` conta le origini dopo t₁ e quelle comuni (eta' > 1 settimana), verifica che
     siano costanti per contesto e scrive `results/evoluzione/e6_origini_comuni.json`;
  2. `genera_congelamento_e6.py`: legge quel JSON (si ferma se manca), lo usa in §1, §3c, §6 e §7
     al posto delle costanti, ne riporta l'impronta e verifica che coincida con il conteggio
     dalla cella.

Uso (dalla radice OR3/):

    poetry run python patch_e6_origini.py
    poetry run python evoluzione/esperimenti/esegui_e6.py --fase origini
    poetry run python genera_congelamento_e6.py
"""
from pathlib import Path

SOSTITUZIONI = {
    "evoluzione/esperimenti/esegui_e6.py": [(
        '''# --------------------------------------------------------------------- main --
def main() -> int:
    ap = argparse.ArgumentParser(description="E6 parte B (PEMS08)")
    ap.add_argument("--fase", choices=("pilota", "addestra", "seleziona-F", "valuta", "scegli", "test", "costi",
                                       "addestra-E", "valuta-E", "test-bis"), required=True)
''',
        '''def fase_origini(out: Path) -> int:
    """Le origini dell'episodio di prova, per contesto, da TUTTE le celle di prova di
    E6 (PEMS08, `predizioni_e6`) ed E6 parte A (PEMS04, `predizioni_e6a`): dopo t₁ e
    comuni (eta' > 1 settimana). Costanti per contesto per costruzione del calendario:
    se una cella differisce, si ferma. Scrive `e6_origini_comuni.json`."""
    import hashlib
    import numpy as np
    fuori = {}
    for cart, nome in (("predizioni_e6", "PEMS08"), ("predizioni_e6a", "PEMS04")):
        file = sorted((out / cart).glob("prova_*_p*_s*.npz"))
        if not file:
            raise RuntimeError(f"{cart}: nessuna cella di prova")
        conte = set()
        for f in file:
            with np.load(f, allow_pickle=True) as z:
                per = z["origini"].astype("int64")
                com = int((z["eta"] > SETTIMANA).sum()) if "eta" in z.files else int((per > int(z["t0"]) + SETTIMANA).sum())
                conte.add((int(z["t0"]), int(len(per)), com))
        if len(conte) != 1:
            raise RuntimeError(f"{nome}: origini non costanti fra le celle: {sorted(conte)}")
        t0, dopo, com = next(iter(conte))
        fuori[nome] = {"t0": t0, "t1": t0 + L24, "origini_dopo_t1": dopo, "origini_comuni": com,
                       "celle": len(file), "cartella": cart}
        print(f"  {nome}: t0 {t0}, origini dopo t1 {dopo}, comuni (eta' > {SETTIMANA}) {com}, su {len(file)} celle")
    testo = json.dumps(fuori, indent=2, ensure_ascii=False, sort_keys=True)
    fuori["impronta"] = hashlib.sha256(testo.encode()).hexdigest()[:16]
    _scrivi_atomico(out / "e6_origini_comuni.json", json.dumps(fuori, indent=2, ensure_ascii=False, sort_keys=True))
    print(f"  salvato in {out / 'e6_origini_comuni.json'} (impronta {fuori['impronta']})")
    return 0


# --------------------------------------------------------------------- main --
def main() -> int:
    ap = argparse.ArgumentParser(description="E6 parte B (PEMS08)")
    ap.add_argument("--fase", choices=("pilota", "addestra", "seleziona-F", "valuta", "scegli", "test", "costi",
                                       "addestra-E", "valuta-E", "test-bis", "origini"), required=True)
'''), (
        '''    if a.fase == "test-bis":
        fase_test_bis(a.out); return 0
''',
        '''    if a.fase == "test-bis":
        fase_test_bis(a.out); return 0
    if a.fase == "origini":
        return fase_origini(a.out)
''')],
    "genera_congelamento_e6.py": [(
        '''      f"origini dopo t₁ nel test {R['origini_prova']}, comuni (eta' > 1 sett.) {R['origini_comuni']} |")
''',
        '''      f"origini dopo t₁ nel test {R['origini_prova']}, comuni (eta' > 1 sett.) {R['origini_comuni']} "
      f"(`e6_origini_comuni.json`, impronta `{R['origini']['impronta']}`, da {R['origini']['PEMS08']['celle']} celle) |")
'''), (
        '''        a("## 3c. Parte A — PEMS04, bracci definitivi (completamento, 168 origini comuni)")
''',
        '''        a(f"## 3c. Parte A — PEMS04, bracci definitivi (completamento, {R['origini']['PEMS04']['origini_comuni']} "
          f"origini comuni su {R['origini']['PEMS04']['origini_dopo_t1']} dopo t₁, `e6_origini_comuni.json`)")
'''), (
        '''             + " su 168 origini comuni: limite dichiarato prima")
''',
        '''             + f" su {R['origini']['PEMS04']['origini_comuni']} origini comuni: limite dichiarato prima")
'''), (
        '''          "dichiarato nel protocollo, con il suo limite (168 origini comuni).")
''',
        '''          f"dichiarato nel protocollo, con il suo limite ({R['origini']['PEMS04']['origini_comuni']} origini comuni).")
'''), (
        '''    t0 = int(z["t0"]); per = z["origini"].astype("int64")
''',
        '''    t0 = int(z["t0"]); per = z["origini"].astype("int64")
    OR = leggi(a.out / "e6_origini_comuni.json")
    if OR["PEMS08"]["origini_dopo_t1"] != int(len(per)) or OR["PEMS08"]["origini_comuni"] != int((per > t0 + 672).sum()):
        raise IngressoMancante("e6_origini_comuni.json non coincide con la cella p0 s201")
'''), (
        '''         "origini_comuni": int((per > t0 + 672).sum()),
''',
        '''         "origini_comuni": int((per > t0 + 672).sum()), "origini": OR,
''')],
}

for f, subs in SOSTITUZIONI.items():
    p = Path(f); s = p.read_text()
    for vecchio, nuovo in subs:
        n = s.count(vecchio)
        assert n == 1, f"{f}: testo atteso trovato {n} volte, non 1:\\n{vecchio[:100]}"
        s = s.replace(vecchio, nuovo)
    compile(s, f, "exec")
    p.write_text(s)
    print(f"  {f}: {len(subs)} sostituzioni, compila")
