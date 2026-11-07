"""
python src/chilenismos/baselines.py [--pares data/processed/pares.csv]
    [--diccionario data/processed/diccionario.csv] [--modelo google/mt5-base]
    [--sin-mt5] [--out data/processed/predicciones.csv]
"""
import argparse
import csv
import re

import sacrebleu


def cargar_reglas(path):
    with open(path, encoding="utf-8") as f:
        reglas = {r["termino"]: r["reemplazo"] for r in csv.DictReader(f)
                  if r["keep"] == "1" and r["reemplazo"]}
    if not reglas:
        raise SystemExit("El diccionario no tiene términos con keep=1 y `reemplazo`.")
    alternativas = "|".join(re.escape(t) for t in sorted(reglas, key=len, reverse=True))
    return reglas, re.compile(rf"(?<!\w)({alternativas})(?!\w)", re.I)


def traducir_reglas(s, reglas, patron):
    def reemplazar(m):
        nuevo = reglas[m.group(0).lower()]
        return nuevo.capitalize() if m.group(0)[0].isupper() else nuevo
    return patron.sub(reemplazar, s)


def traducir_mt5(frases, modelo, lote=16):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(modelo)
    mod = AutoModelForSeq2SeqLM.from_pretrained(modelo).to(dev).eval()
    salidas = []
    for i in range(0, len(frases), lote):
        enc = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True,
                  max_length=128).to(dev)
        with torch.no_grad():
            out = mod.generate(**enc, max_new_tokens=64, num_beams=4)
        salidas += tok.batch_decode(out, skip_special_tokens=True)
    return salidas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", default="data/processed/pares.csv")
    ap.add_argument("--diccionario", default="data/processed/diccionario.csv")
    ap.add_argument("--modelo", default="google/mt5-base")
    ap.add_argument("--out", default="data/processed/predicciones.csv")
    ap.add_argument("--sin-mt5", action="store_true")
    args = ap.parse_args()

    with open(args.pares, encoding="utf-8") as f:
        pares = [r for r in csv.DictReader(f) if r["chileno"].strip() and r["neutro"].strip()]
    fuente = [p["chileno"] for p in pares]
    ref = [p["neutro"] for p in pares]

    reglas, patron = cargar_reglas(args.diccionario)
    preds = {"identidad": fuente, "reglas": [traducir_reglas(s, reglas, patron) for s in fuente]}
    if not args.sin_mt5:
        preds["mt5"] = traducir_mt5(fuente, args.modelo)

    print(f"{len(pares)} pares | {len(reglas)} reglas\n")
    print(f"{'sistema':<10} {'BLEU':>6} {'chrF':>6}")
    for nombre, hip in preds.items():
        print(f"{nombre:<10} {sacrebleu.corpus_bleu(hip, [ref]).score:6.1f} "
              f"{sacrebleu.corpus_chrf(hip, [ref]).score:6.1f}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["chileno", "neutro", *preds])
        w.writerows(zip(fuente, ref, *preds.values()))
    print(f"\nEscrito {args.out}")


if __name__ == "__main__":
    main()
