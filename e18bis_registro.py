#!/usr/bin/env python3
"""
E18-bis, passo 2 (registro): riga 29 in `protocol/REGISTRO_CORREZIONI.md`, con le impronte prima/dopo di
`CONGELAMENTO_E18.md` (prima = versione in HEAD, dopo = file rigenerato nell'albero di lavoro). Si ferma se il
congelamento rigenerato non porta «voce 29» e la tabella delle metriche di F16, o se la riga 29 esiste gia'.

Dalla radice OR3/ (ramo esecutore/e18-bis), dopo aver copiato CONGELAMENTO_E18.md, e18_risultati.json,
congelamento_e18.json rigenerati sulla Spark:  python3 e18bis_registro.py
"""
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

R = Path(__file__).resolve().parent
OGGI = date.today().isoformat()


def imp_b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def main() -> int:
    cong = R / "CONGELAMENTO_E18.md"; reg = R / "protocol" / "REGISTRO_CORREZIONI.md"
    t_cong = cong.read_text()
    if "voce 29" not in t_cong or "Metriche di F16 sulla finestra" not in t_cong:
        print("FERMO: CONGELAMENTO_E18.md non e' la versione rigenerata (manca «voce 29» o la tabella di F16)"); return 1
    prima = imp_b(subprocess.run(["git", "show", "HEAD:CONGELAMENTO_E18.md"], cwd=R, capture_output=True, check=True).stdout)
    dopo = imp_b(cong.read_bytes())
    if prima == dopo:
        print("FERMO: CONGELAMENTO_E18.md e' identico a HEAD"); return 1
    j_res = imp_b((R / "results/evoluzione/e18_risultati.json").read_bytes())
    j_con = imp_b((R / "results/evoluzione/congelamento_e18.json").read_bytes())
    t = reg.read_text()
    if "| 29 |" in t:
        print("FERMO: la riga 29 e' gia' presente"); return 1
    riga = ("| 29 | l'AUC di E8-bis era calcolata su 19 soglie fisse (seconda revisione esterna, punto 3); le affermazioni che ne "
            "dipendevano sono ri-valutate sulla ROC empirica su tutti i punteggi distinti (E18 parte A, `CONGELAMENTO_E18.md` §2c). "
            "Il protocollo E18 §1 r. 61 chiamava questa voce «28»: il numero 28 era gia' assegnato (nomi di ruolo), quindi e' la 29; "
            "il protocollo firmato non si modifica, la deviazione e' dichiarata in `CONGELAMENTO_E18.md` §6 | E18 parte A (nessun "
            "addestramento); `CONGELAMENTO_E18.md` rigenerato il " + OGGI + " con nota datata, e con la parte C completata dalle stesse "
            "probabilita' con ECE per classe, log-loss e Brier sulla finestra > 1 settimana (protocollo §3; la prima versione riportava "
            "la sola wCE). Impronte prima → dopo: `CONGELAMENTO_E18.md` `" + prima + "` → `" + dopo + "`; `e18_risultati.json` `" + j_res
            + "`; `congelamento_e18.json` `" + j_con + "` | `CONGELAMENTO_E18.md`; `results/evoluzione/e18_risultati.json`; "
            "`analysis/tabelle_suppl.py` (F17) |")
    righe = t.rstrip("\n").split("\n")
    i28 = [i for i, l in enumerate(righe) if l.startswith("| 28 |")]
    if len(i28) != 1:
        print(f"FERMO: la riga 28 compare {len(i28)} volte"); return 1
    righe.insert(i28[0] + 1, riga)
    t = "\n".join(righe) + "\n"
    v, n = "alla pipeline (voci 1–16, 17a, 19–27),", "alla pipeline (voci 1–16, 17a, 19–27, 29),"
    if t.count(v) != 1:
        print(f"FERMO: l'intestazione attesa compare {t.count(v)} volte"); return 1
    reg.write_text(t.replace(v, n, 1))
    print(f"  protocol/REGISTRO_CORREZIONI.md: riga 29 aggiunta; CONGELAMENTO_E18.md {prima} → {dopo}; "
          f"e18_risultati.json {j_res}; congelamento_e18.json {j_con}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
