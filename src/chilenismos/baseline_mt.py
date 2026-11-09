"""
Baseline de traducción automática genérica: ida y vuelta español -> inglés -> español con Opus-MT (Helsinki-NLP).

Un traductor general no pasa «chileno» a «neutro» (el origen y el destino son el mismo idioma), así que se usa
el pivote por inglés: la jerga suele salir normalizada en el viaje de vuelta. Es gratis y corre en la GPU local;
no envía texto a ningún servicio (solo baja los modelos públicos de Hugging Face, sin clave).

python src/chilenismos/baseline_mt.py [--pares annotation/lote1.csv ...] [--resumen resultados/comparacion_baselines.csv]
    [--ida Helsinki-NLP/opus-mt-es-en] [--vuelta Helsinki-NLP/opus-mt-en-es] [--out data/processed/predicciones_mt.csv]
"""
import argparse
import csv
import os
import sys

import sacrebleu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baselines import cargar_pares, guardar_resumen  # noqa: E402


def traducir(frases, modelo, lote=16, haces=4):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(modelo)
    mod = AutoModelForSeq2SeqLM.from_pretrained(modelo).to(dev).eval()
    salida = []
    for i in range(0, len(frases), lote):
        enc = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True, max_length=256).to(dev)
        with torch.no_grad():
            out = mod.generate(**enc, max_new_tokens=256, num_beams=haces)
        salida += tok.batch_decode(out, skip_special_tokens=True)
    del mod
    if dev == "cuda":
        torch.cuda.empty_cache()
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", nargs="+", default=["annotation/lote1.csv", "annotation/lote_1_noticias.csv",
                                                  "annotation/lote_1_tuits.csv"])
    ap.add_argument("--ida", default="Helsinki-NLP/opus-mt-es-en")
    ap.add_argument("--vuelta", default="Helsinki-NLP/opus-mt-en-es")
    ap.add_argument("--resumen")
    ap.add_argument("--out", default="data/processed/predicciones_mt.csv")
    args = ap.parse_args()

    conjuntos = {ruta: cargar_pares(ruta) for ruta in args.pares}
    todas = [p["chileno"] for ps in conjuntos.values() for p in ps]
    en = traducir(todas, args.ida)
    hip_todas = traducir(en, args.vuelta)

    filas, resumen, i = [], [], 0
    for ruta, ps in conjuntos.items():
        hip = hip_todas[i:i + len(ps)]
        i += len(ps)
        fuente, ref = [p["chileno"] for p in ps], [p["neutro"] for p in ps]
        bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
        print(f"{os.path.basename(ruta):<24} mt_ida_vuelta BLEU {bleu:5.1f} chrF {chrf:5.1f}")
        filas += [(os.path.basename(ruta), f, r, h) for f, r, h in zip(fuente, ref, hip)]
        resumen.append({"sistema": "mt_ida_vuelta", "escenario": "", "bleu": f"{bleu:.1f}", "chrf": f"{chrf:.1f}",
                        "n_pares": len(ps), "pares": ruta, "nota": f"{args.ida} + {args.vuelta}"})
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "chileno", "referencia", "mt_ida_vuelta"])
        w.writerows(filas)
    if args.resumen:
        guardar_resumen(args.resumen, resumen)


if __name__ == "__main__":
    main()
