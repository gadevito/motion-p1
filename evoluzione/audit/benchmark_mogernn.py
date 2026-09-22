#!/usr/bin/env python3
"""
Benchmark MoGERNN, lotto 32, CPU e GPU (MPS). Nessun addestramento completo.
============================================================================
Commit esaminato: 86b153fb4bf9358e32079930ccaea1cbcffa66f8. **DiffConv non
viene modificato.**

**Lanciarlo SOLO quando nessun'altra campagna e' in esecuzione**: i tempi e la
memoria misurati in concorrenza con altri processi non sono attendibili.

PROTOCOLLO, per entrambi i dispositivi

    stessi tensori, grafo, maschere e precisione (float32)
    stessa configurazione del modello
    aggiornamento COMPLETO: forward, perdita, backward, optimizer.step()
    `--riscaldamento` aggiornamenti esclusi, `--misurati` cronometrati:
    mediana e variabilita'
    su MPS: sincronizzazione PRIMA e DOPO ogni tratto misurato

**Il lotto da 32 e' la configurazione del confronto**, non un'ottimizzazione:
32 finestre per aggiornamento come gli altri bracci. L'uguaglianza del lotto
non implica uguale costo ne' uguale velocita' di convergenza fra architetture.

MEMORIA. Sul Mac CPU e GPU condividono la stessa memoria: **non e' memoria
aggiuntiva**. Si riportano separatamente il picco del processo (RSS) e la
memoria allocata dal dispositivo, **senza sommarli**: possono sovrapporsi.

Uso:

    poetry run python evoluzione/audit/benchmark_mogernn.py --repo PERCORSO \\
        --dispositivo cpu
    poetry run python evoluzione/audit/benchmark_mogernn.py --repo PERCORSO \\
        --dispositivo mps
    poetry run python evoluzione/audit/benchmark_mogernn.py --repo PERCORSO \\
        --dispositivo cpu --concorrenza 1x14,3x4,5x2
"""
import argparse
import json
import multiprocessing as mp
import os
import platform
import resource
import statistics as st
import sys
import time
import warnings
from pathlib import Path
from types import SimpleNamespace


def cfg():
    return SimpleNamespace(
        input_len=12, pred_len=12, look_back=0, d_model=64, e_layers=2,
        k_hop=1, enc_in=1, num_experts=5, num_used_experts=3,
        mean_expert=True, weight_expert=True, max_expert=True,
        min_expert=True, diffusion_expert=True)


def dati(N, B, seme=0, densita=0.05):
    """Tensori e grafo IDENTICI per ogni dispositivo: generati su CPU."""
    import torch
    g = torch.Generator().manual_seed(seme)
    A = (torch.rand(N, N, generator=g) < densita).float() * \
        torch.rand(N, N, generator=g)
    A.fill_diagonal_(1.0)
    X = torch.randn(B, 12, N, 1, generator=g)
    X[:, :, : N // 4] = 0.0                      # un quarto dei nodi ignoti
    Y = torch.randn(B, 12, N, 1, generator=g)
    archi = int((A > 0).sum()) - N
    return A, X, Y, {"nodi": N, "archi_senza_autoanelli": archi,
                     "densita": archi / (N * (N - 1)),
                     "pesi": "uniformi in (0, 1), sintetici",
                     "normalizzazione": "random walk D^-1 A, calcolata dal "
                                        "modello (gnn.py 32-45)",
                     "nota": "con DiffConv denso il costo NON dipende dalla "
                             "densita'; conta solo per una variante sparsa"}


def sincronizza(dev):
    import torch
    if dev == "mps":
        torch.mps.synchronize()


def memoria_dispositivo(dev):
    import torch
    if dev == "mps":
        return {"allocata_GB": torch.mps.current_allocated_memory() / 1e9,
                "driver_GB": torch.mps.driver_allocated_memory() / 1e9}
    return {}


def rss_picco_GB():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e9 if sys.platform == "darwin" else r / 1e6


def misura(repo, dev, N, B, risc, mis, fili=None):
    """Aggiornamento completo e inferenza, sincronizzati."""
    import torch
    if fili:
        torch.set_num_threads(fili)
    sys.path.insert(0, str(Path(repo).resolve()))
    import model.MoGERNN as M
    A, X, Y, grafo = dati(N, B)
    torch.manual_seed(1)
    m = M.Model(cfg()).float().to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=1e-3)
    A, X, Y = A.to(dev), X.to(dev), Y.to(dev)
    avvisi = []
    t_agg, t_inf, picco_dev = [], [], {}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for i in range(risc + mis):
            sincronizza(dev); t0 = time.perf_counter()
            m.train(); opt.zero_grad()
            out = m(A, X, None, None, Y, None, 1)
            torch.nn.functional.mse_loss(out, Y).backward(); opt.step()
            sincronizza(dev); dt = time.perf_counter() - t0
            if i >= risc:
                t_agg.append(dt)
            for k, v in memoria_dispositivo(dev).items():
                picco_dev[k] = max(picco_dev.get(k, 0.0), v)
        for i in range(risc + mis):
            sincronizza(dev); t0 = time.perf_counter()
            m.eval()
            with torch.no_grad():
                m(A, X, None, None, None, None, 0)
            sincronizza(dev); dt = time.perf_counter() - t0
            if i >= risc:
                t_inf.append(dt)
        avvisi = sorted({str(x.message)[:160] for x in w
                         if "fall back" in str(x.message).lower()
                         or "mps" in str(x.message).lower()})

    def riass(t):
        return {"mediana_s": st.median(t), "minimo_s": min(t),
                "massimo_s": max(t),
                "dev_std_s": st.pstdev(t) if len(t) > 1 else 0.0, "n": len(t)}

    return {"dispositivo": dev, "nodi": N, "lotto": B,
            "fili_torch": torch.get_num_threads(),
            "aggiornamento": riass(t_agg), "inferenza": riass(t_inf),
            "rss_picco_processo_GB": rss_picco_GB(),
            "memoria_dispositivo_picco": picco_dev,
            "avvisi_fallback": avvisi, "grafo": grafo,
            "nota_random_walk": ("calculate_random_walk_matrix passa per numpy "
                                 "su CPU a ogni forward (4 chiamate): su MPS "
                                 "sono andate e ritorni dispositivo-host")}


def correttezza(repo, N, B):
    """CPU contro MPS: stessi pesi iniziali, stesso ingresso."""
    import copy
    import torch
    sys.path.insert(0, str(Path(repo).resolve()))
    import model.MoGERNN as M
    A, X, Y, _ = dati(N, B)
    torch.manual_seed(1)
    mc = M.Model(cfg()).float()
    mg = copy.deepcopy(mc).to("mps")
    fuori = {}
    # valutazione: nessun teacher forcing, nessuna casualita'
    mc.eval(); mg.eval()
    with torch.no_grad():
        oc = mc(A, X, None, None, None, None, 0)
        og = mg(A.to("mps"), X.to("mps"), None, None, None, None, 0).cpu()
    fuori["uscita_eval_max_abs"] = float((oc - og).abs().max())
    # addestramento: lo stesso seme per il teacher forcing (torch.rand su CPU)
    mc.train(); mg.train()
    torch.manual_seed(5)
    lc = torch.nn.functional.mse_loss(mc(A, X, None, None, Y, None, 1), Y)
    lc.backward()
    torch.manual_seed(5)
    Yg = Y.to("mps")
    lg = torch.nn.functional.mse_loss(
        mg(A.to("mps"), X.to("mps"), None, None, Yg, None, 1), Yg)
    lg.backward()
    fuori["perdita_abs"] = float(abs(lc.item() - lg.item()))
    fuori["gradienti_max_abs"] = max(
        float((pc.grad - pg.grad.cpu()).abs().max())
        for pc, pg in zip(mc.parameters(), mg.parameters())
        if pc.grad is not None)
    return fuori


def _lavora(args):
    return misura(*args)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--dispositivo", choices=("cpu", "mps"), default="cpu")
    ap.add_argument("--nodi", type=int, default=765)
    ap.add_argument("--lotto", type=int, default=32)
    ap.add_argument("--riscaldamento", type=int, default=3)
    ap.add_argument("--misurati", type=int, default=10)
    ap.add_argument("--concorrenza", default="",
                    help="es. 1x14,3x4,5x2: processi x fili, solo CPU")
    ap.add_argument("--out", default="results/evoluzione/audit_mogernn")
    a = ap.parse_args()
    import torch
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    amb = {"piattaforma": platform.platform(), "python":
           platform.python_version(), "torch": torch.__version__,
           "nuclei": os.cpu_count(),
           "mps_disponibile": torch.backends.mps.is_available(),
           "fallback_mps_abilitato":
               os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK", "0")}

    print("=" * 78)
    print(f"BENCHMARK MoGERNN — {a.dispositivo.upper()}, {a.nodi} nodi, "
          f"lotto {a.lotto}")
    print("=" * 78)
    for k, v in amb.items():
        print(f"  {k:24s} {v}")

    if a.concorrenza:
        if a.dispositivo != "cpu":
            print("la concorrenza si misura solo su CPU"); return 1
        ris = []
        for voce in a.concorrenza.split(","):
            k, f = (int(z) for z in voce.split("x"))
            ctx = mp.get_context("spawn")
            t0 = time.perf_counter()
            with ctx.Pool(k) as p:
                r = p.map(_lavora, [(a.repo, "cpu", a.nodi, a.lotto,
                                     a.riscaldamento, a.misurati, f)] * k)
            parete = time.perf_counter() - t0
            med = st.median(x["aggiornamento"]["mediana_s"] for x in r)
            tp = k / med                       # aggiornamenti al secondo
            ris.append({"processi": k, "fili": f, "mediana_per_processo_s": med,
                        "throughput_agg_s": tp, "parete_s": parete,
                        "rss_picco_GB_per_processo":
                            max(x["rss_picco_processo_GB"] for x in r)})
            print(f"  {k} x {f} fili: {med:6.2f} s per aggiornamento, "
                  f"{tp:5.3f} agg/s in totale, RSS {ris[-1]['rss_picco_GB_per_processo']:.1f} GB/proc")
        (out / "concorrenza_cpu.json").write_text(json.dumps(
            {"ambiente": amb, "risultati": ris}, indent=2))
        print("\n  **Il calendario si stima da questo throughput misurato**, non")
        print("  dividendo il costo seriale per il numero di processi.")
        return 0

    try:
        r = misura(a.repo, a.dispositivo, a.nodi, a.lotto, a.riscaldamento,
                   a.misurati)
    except (NotImplementedError, RuntimeError) as e:
        print(f"\n  ESECUZIONE NON COMPLETATA su {a.dispositivo}: "
              f"{type(e).__name__}: {str(e)[:300]}")
        print("  Operazione non supportata: registrarla. Con "
              "PYTORCH_ENABLE_MPS_FALLBACK=1 si misura il ricorso alla CPU.")
        return 1
    if a.dispositivo == "mps":
        r["correttezza_cpu_contro_mps"] = correttezza(a.repo, a.nodi, a.lotto)
    r["ambiente"] = amb
    (out / f"benchmark_{a.dispositivo}.json").write_text(
        json.dumps(r, indent=2))

    ag, inf = r["aggiornamento"], r["inferenza"]
    print(f"\n  aggiornamento completo  mediana {ag['mediana_s']:6.2f} s "
          f"(min {ag['minimo_s']:.2f}, max {ag['massimo_s']:.2f}, "
          f"n {ag['n']})")
    print(f"  inferenza               mediana {inf['mediana_s']:6.2f} s")
    print(f"  RSS di picco, processo  {r['rss_picco_processo_GB']:.1f} GB")
    if r["memoria_dispositivo_picco"]:
        print(f"  memoria MPS di picco    {r['memoria_dispositivo_picco']}")
        print("     (NON sommarla all'RSS: sul Mac la memoria e' condivisa)")
    print(f"  avvisi di fallback      {r['avvisi_fallback'] or 'nessuno'}")
    if "correttezza_cpu_contro_mps" in r:
        print(f"  CPU contro MPS          {r['correttezza_cpu_contro_mps']}")
    print(f"  grafo                   {r['grafo']['archi_senza_autoanelli']} "
          f"archi, densita' {r['grafo']['densita']:.3f}, sintetico")
    print(f"\n  salvato in {out}")
    print("  Prima stima: non stabilisce il throughput sostenuto per ore.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
