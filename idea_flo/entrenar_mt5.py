"""
Ajusta mT5 con los pares propios (borradores del LLM) y lo evalúa en los conjuntos de pares revisados.

python idea_flo/entrenar_mt5.py [--entrenamiento data/interim/borrador_entrenamiento.csv]
    [--pares annotation/lote1.csv annotation/lote_1_noticias.csv annotation/lote_1_tuits.csv]
    [--modelo google/mt5-small] [--epocas 8] [--lote 8] [--lr 5e-4] [--out models/mt5_flo]
    [--resumen resultados/comparacion_baselines.csv] [--sin-entrenar]

Los pares de entrenamiento son borradores del LLM sin revisión humana (datos «plata»); la prueba
solo usa pares revisados. Se quitan del entrenamiento las oraciones que aparecen en algún conjunto
de prueba. Usa la GPU si hay (Adafactor + bf16: entra en 4 GB con mT5-small).
--sin-entrenar evalúa el modelo base, para medir cuánto aporta el ajuste.
"""
import argparse
import csv
import os
import random
import sys

import sacrebleu

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "chilenismos"))
from baselines import cargar_pares, guardar_resumen, limpiar  # noqa: E402


def cargar_entrenamiento(ruta, prohibidas):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    vistas, pares = set(), []
    for r in filas:
        o, n = limpiar(r["oracion"]), limpiar(r["neutro"])   # sin menciones ni emojis, igual que los conjuntos de prueba
        if not o or not n or n.upper() == "DESCARTAR" or o in prohibidas or o in vistas:
            continue
        vistas.add(o)
        pares.append((o, n))
    return pares


def traducir(mod, tok, frases, dev, lote=16):
    import torch
    salidas = []
    mod.eval()
    for i in range(0, len(frases), lote):
        enc = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True, max_length=128).to(dev)
        with torch.no_grad(), torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
            out = mod.generate(**enc, max_new_tokens=96, num_beams=4)
        salidas += tok.batch_decode(out, skip_special_tokens=True)
    return salidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrenamiento", default="data/interim/borrador_entrenamiento.csv")
    ap.add_argument("--pares", nargs="+", default=["annotation/lote1.csv", "annotation/lote_1_noticias.csv",
                                                  "annotation/lote_1_tuits.csv"])
    ap.add_argument("--modelo", default="google/mt5-small")
    ap.add_argument("--epocas", type=int, default=8)
    ap.add_argument("--lote", type=int, default=8)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--val", type=float, default=0.05)
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--out", default="models/mt5_flo")
    ap.add_argument("--resumen")
    ap.add_argument("--out-pred", default="data/processed/predicciones_mt5.csv", help="oración, referencia y salida del modelo, para revisarlas")
    ap.add_argument("--sin-entrenar", action="store_true")
    args = ap.parse_args()

    import torch
    from transformers import Adafactor, AutoModelForSeq2SeqLM, AutoTokenizer
    random.seed(args.semilla)
    torch.manual_seed(args.semilla)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("dispositivo:", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "")

    conjuntos = {ruta: cargar_pares(ruta) for ruta in args.pares}
    prohibidas = {p["chileno"] for ps in conjuntos.values() for p in ps}
    tok = AutoTokenizer.from_pretrained(args.modelo)
    mod = AutoModelForSeq2SeqLM.from_pretrained(args.modelo).to(dev)

    if not args.sin_entrenar:
        pares = cargar_entrenamiento(args.entrenamiento, prohibidas)
        random.shuffle(pares)
        n_val = max(1, round(len(pares) * args.val))
        val, train = pares[:n_val], pares[n_val:]
        print(f"entrenamiento: {len(train)} pares | validación: {len(val)}")
        opt = Adafactor(mod.parameters(), lr=args.lr, relative_step=False, scale_parameter=False, warmup_init=False)
        mod.gradient_checkpointing_enable()
        mod.config.use_cache = False
        mejor = float("inf")
        for ep in range(1, args.epocas + 1):
            mod.train()
            random.shuffle(train)
            total = 0.0
            for i in range(0, len(train), args.lote):
                b = train[i:i + args.lote]
                enc = tok([x[0] for x in b], return_tensors="pt", padding=True, truncation=True, max_length=128).to(dev)
                lab = tok(text_target=[x[1] for x in b], return_tensors="pt", padding=True, truncation=True,
                          max_length=128).input_ids.to(dev)
                lab[lab == tok.pad_token_id] = -100
                with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
                    loss = mod(**enc, labels=lab).loss
                loss.backward()
                opt.step()
                opt.zero_grad(set_to_none=True)
                total += loss.item()
                if (i // args.lote) % 100 == 0:
                    print(f"  época {ep} paso {i // args.lote}/{len(train) // args.lote} pérdida {loss.item():.3f}", flush=True)
            mod.eval()
            perd = 0.0
            with torch.no_grad():
                for i in range(0, len(val), args.lote):
                    b = val[i:i + args.lote]
                    enc = tok([x[0] for x in b], return_tensors="pt", padding=True, truncation=True, max_length=128).to(dev)
                    lab = tok(text_target=[x[1] for x in b], return_tensors="pt", padding=True, truncation=True,
                              max_length=128).input_ids.to(dev)
                    lab[lab == tok.pad_token_id] = -100
                    with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
                        perd += mod(**enc, labels=lab).loss.item() * len(b)
            perd /= len(val)
            print(f"época {ep}: pérdida de entrenamiento {total / max(1, len(train) // args.lote):.3f} | validación {perd:.3f}", flush=True)
            if perd < mejor:
                mejor = perd
                os.makedirs(args.out, exist_ok=True)
                mod.save_pretrained(args.out)
                tok.save_pretrained(args.out)
        mod = AutoModelForSeq2SeqLM.from_pretrained(args.out).to(dev)
        mod.config.use_cache = True

    nombre = "mt5_sin_ajustar" if args.sin_entrenar else "mt5_flo"
    filas, salidas = [], []
    for ruta, ps in conjuntos.items():
        hip = traducir(mod, tok, [p["chileno"] for p in ps], dev)
        ref = [p["neutro"] for p in ps]
        salidas += [(os.path.basename(ruta), p["chileno"], r, h) for p, r, h in zip(ps, ref, hip)]
        bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
        print(f"{os.path.basename(ruta):<24} {nombre:<22} BLEU {bleu:5.1f} chrF {chrf:5.1f}")
        filas.append({"sistema": nombre, "escenario": "", "bleu": f"{bleu:.1f}", "chrf": f"{chrf:.1f}", "n_pares": len(ps),
                      "pares": ruta, "nota": f"{args.modelo}; {'sin ajuste' if args.sin_entrenar else 'ajustado con borradores del LLM'}"})
    os.makedirs(os.path.dirname(args.out_pred) or ".", exist_ok=True)
    with open(args.out_pred, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "chileno", "referencia", nombre])
        w.writerows(salidas)
    if args.resumen:
        guardar_resumen(args.resumen, filas)


if __name__ == "__main__":
    main()
