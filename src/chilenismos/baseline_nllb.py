"""
Baseline de traducción automática genérica con NLLB-200 (Meta): ida y vuelta español -> inglés -> español.

Igual que baseline_mt.py (Opus-MT) pero con otro traductor abierto, para tener más de una referencia.
Corre en la GPU local y no envía texto a ningún servicio; solo baja el modelo público de Hugging Face (sin clave).
Licencia del modelo: CC-BY-NC 4.0 (uso no comercial, sirve para el curso).

python src/chilenismos/baseline_nllb.py [--pares annotation/lote1.csv ...] [--resumen resultados/comparacion_baselines.csv]
    [--modelo facebook/nllb-200-distilled-600M] [--out data/processed/predicciones_nllb.csv]
"""
import argparse
import csv
import os
import sys

import sacrebleu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baselines import cargar_pares, guardar_resumen  # noqa: E402


def cargar(modelo):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(modelo)
    mod = AutoModelForSeq2SeqLM.from_pretrained(modelo, dtype=torch.float16 if dev == "cuda" else torch.float32).to(dev).eval()
    return tok, mod, dev


def traducir(frases, tok, mod, dev, origen, destino, lote=16, haces=4):
    import torch
    tok.src_lang = origen
    salida = []
    for i in range(0, len(frases), lote):
        enc = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True, max_length=256).to(dev)
        with torch.no_grad():
            out = mod.generate(**enc, forced_bos_token_id=tok.convert_tokens_to_ids(destino), max_new_tokens=256, num_beams=haces)
        salida += tok.batch_decode(out, skip_special_tokens=True)
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", nargs="+", default=["annotation/lote1.csv", "annotation/lote_1_noticias.csv",
                                                  "annotation/lote_1_tuits.csv"])
    ap.add_argument("--modelo", default="facebook/nllb-200-distilled-600M")
    ap.add_argument("--resumen")
    ap.add_argument("--out", default="data/processed/predicciones_nllb.csv")
    args = ap.parse_args()

    conjuntos = {ruta: cargar_pares(ruta) for ruta in args.pares}
    tok, mod, dev = cargar(args.modelo)
    filas, resumen = [], []
    for ruta, ps in conjuntos.items():
        fuente, ref = [p["chileno"] for p in ps], [p["neutro"] for p in ps]
        en = traducir(fuente, tok, mod, dev, "spa_Latn", "eng_Latn")
        hip = traducir(en, tok, mod, dev, "eng_Latn", "spa_Latn")
        bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
        print(f"{os.path.basename(ruta):<24} nllb_ida_vuelta BLEU {bleu:5.1f} chrF {chrf:5.1f}", flush=True)
        filas += [(os.path.basename(ruta), f, r, h) for f, r, h in zip(fuente, ref, hip)]
        resumen.append({"sistema": "nllb_ida_vuelta", "escenario": "", "bleu": f"{bleu:.1f}", "chrf": f"{chrf:.1f}",
                        "n_pares": len(ps), "pares": ruta, "nota": args.modelo})
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "chileno", "referencia", "nllb_ida_vuelta"])
        w.writerows(filas)
    if args.resumen:
        guardar_resumen(args.resumen, resumen)


if __name__ == "__main__":
    main()
