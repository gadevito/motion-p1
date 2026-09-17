#!/usr/bin/env python3
"""
Collaudo del registro — le cinque verifiche richieste, senza addestramento.
===========================================================================

  1. un cambiamento nell'ORDINE delle caratteristiche e' rilevabile;
  2. una modifica al CONTENUTO di un file ne cambia l'impronta;
  3. la configurazione registrata permette di ricostruire modello ed estrattore;
  4. un'esecuzione INTERROTTA resta identificata come incompleta;
  5. ogni uscita e' associabile senza ambiguita' alla propria esecuzione.

Uso (dalla radice OR3/):

    poetry run python evoluzione/componente/collauda_registro.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evoluzione.componente.registro import (  # noqa: E402
    Registro, impronta_file, impronta_oggetto)

ESITI = []


def verifica(n, titolo, condizione, dettaglio=""):
    ESITI.append(bool(condizione))
    print(f"  [{n}] {'PASSA' if condizione else 'FALLISCE'}  {titolo}")
    if dettaglio:
        print(f"        {dettaglio}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="collaudo_registro_"))
    print(f"registro di prova in {tmp}\n")

    NOMI = ["media_r", "dev_r", "media_f", "dev_f", "media_o", "dev_o"]
    D = np.arange(60, dtype="float32").reshape(10, 6)

    # ---------------------------------------------------------------- [1] ---
    print("[1] ordine delle caratteristiche")
    a = Registro.avvia("collaudo", radice=tmp)
    a.artefatto("descrittore", oggetto=D, nomi=NOMI, schema="1.0")
    a.completa()
    b = Registro.avvia("collaudo", radice=tmp)
    b.artefatto("descrittore", oggetto=D, nomi=list(reversed(NOMI)), schema="1.0")
    b.completa()
    ja = json.loads(a.percorso.read_text())
    jb = json.loads(b.percorso.read_text())
    ia = ja["descrittore"]["impronta_ordine_caratteristiche"]
    ib = jb["descrittore"]["impronta_ordine_caratteristiche"]
    verifica(1, "invertire l'ordine cambia l'impronta", ia != ib,
             f"{ia[:12]} contro {ib[:12]}")
    verifica("1b", "il contenuto, invariato, ha la stessa impronta",
             ja["descrittore"]["impronta_contenuto_caricato"]
             == jb["descrittore"]["impronta_contenuto_caricato"],
             "ordine e contenuto sono improntati separatamente")

    # ---------------------------------------------------------------- [2] ---
    print("\n[2] contenuto dei file")
    f = tmp / "art.npy"
    np.save(f, D)
    h1 = impronta_file(f)
    E = D.copy()
    E[0, 0] += np.float32(1e-3)
    np.save(f, E)
    h2 = impronta_file(f)
    verifica(2, "modificare un valore cambia l'impronta del file", h1 != h2,
             f"{h1[:12]} contro {h2[:12]}")
    verifica("2b", "l'impronta del contenuto caricato distingue le due matrici",
             impronta_oggetto(D) != impronta_oggetto(E))
    verifica("2c", "matrici uguali con forma diversa hanno impronta diversa",
             impronta_oggetto(D.reshape(6, 10)) != impronta_oggetto(D),
             "la forma entra nell'impronta")

    # ---------------------------------------------------------------- [3] ---
    print("\n[3] ricostruibilita' della configurazione")
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb", type=int, default=0)
    ap.add_argument("--desc-proj", type=int, default=8)
    ap.add_argument("--desc-hidden", type=int, default=32)
    ap.add_argument("--node-desc", default="descrittori/x_raw.npy")
    args = ap.parse_args([])                     # NESSUNA opzione sulla riga
    c = Registro.avvia("collaudo", radice=tmp)
    c.configurazione(vars(args))
    c.completa()
    jc = json.loads(c.percorso.read_text())["resolved_configuration"]
    verifica(3, "i predefiniti non indicati sono registrati",
             jc.get("desc_hidden") == 32 and jc.get("desc_proj") == 8,
             f"desc_hidden={jc.get('desc_hidden')}, desc_proj={jc.get('desc_proj')}")
    verifica("3b", "la riga di comando da sola non basta",
             "--desc-hidden" not in " ".join(sys.argv),
             "nessuna opzione sulla riga, ma la configurazione e' completa")

    # ---------------------------------------------------------------- [4] ---
    print("\n[4] esecuzione interrotta")
    codice = f'''
import sys; sys.path.insert(0, {str(Path(__file__).resolve().parents[2])!r})
from evoluzione.componente.registro import Registro
r = Registro.avvia("interrotta", radice={str(tmp)!r})
r.evento("prima del guasto")
raise SystemExit(1)
'''
    subprocess.run([sys.executable, "-c", codice], capture_output=True)
    rotti = [p for p in tmp.glob("*.json")
             if json.loads(p.read_text()).get("esperimento") == "interrotta"]
    st = json.loads(rotti[0].read_text()) if rotti else {}
    verifica(4, "resta marcata come interrotta",
             st.get("run_status") == "interrotto",
             f"stato: {st.get('run_status')}")
    verifica("4b", "l'uscita anomala e' annotata",
             any("senza chiamata a completa" in e.get("testo", "")
                 for e in st.get("eventi", [])))

    # ---------------------------------------------------------------- [5] ---
    print("\n[5] associazione fra uscite ed esecuzione")
    out = tmp / "risultato.csv"
    out.write_text("a,b\n1,2\n")
    d = Registro.avvia("collaudo", radice=tmp)
    d.uscita(out)
    d.completa()
    jd = json.loads(d.percorso.read_text())
    u = jd["uscite"][0]
    verifica(5, "l'uscita e' registrata con la propria impronta",
             u["impronta"] == impronta_file(out))
    # unicita' degli identificativi
    ids = [json.loads(p.read_text())["run_id"] for p in tmp.glob("*.json")]
    verifica("5b", "gli identificativi sono unici",
             len(ids) == len(set(ids)), f"{len(ids)} manifesti")
    # se il file cambia dopo, l'impronta non corrisponde piu': e' rilevabile
    out.write_text("a,b\n9,9\n")
    verifica("5c", "una modifica successiva all'uscita e' rilevabile",
             u["impronta"] != impronta_file(out))

    # -------------------------------------------------------- retrospettivo --
    print("\n[6] manifesto retrospettivo")
    p = Registro.retrospettivo(
        "Tabella 54",
        campi_noti={"descrittore": "16 statistiche, proiezione appresa",
                    "formula": "media dei rapporti appaiati per seme"},
        campi_mancanti=["code_commit", "collegamento file-esecuzione",
                        "assenza di parametri per nodo"],
        radice=tmp)
    jr = json.loads(p.read_text())
    verifica(6, "e' marcato come ricostruzione",
             jr["tipo"] == "ricostruzione retrospettiva")
    verifica("6b", "i campi mancanti restano espliciti",
             "code_commit" in jr["campi_mancanti"],
             f"{len(jr['campi_mancanti'])} campi dichiarati mancanti")

    print("\n" + "=" * 62)
    print(f"  {sum(ESITI)}/{len(ESITI)} verifiche superate")
    print("=" * 62)
    return 0 if all(ESITI) else 1


if __name__ == "__main__":
    raise SystemExit(main())
