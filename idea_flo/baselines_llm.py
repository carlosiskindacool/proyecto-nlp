"""
Baselines con LLM (idea de Flo): zero-shot y con el diccionario como contexto.

python idea_flo/baselines_llm.py [--pares annotation/lote1.csv ...] [--escenario flo] [--backend claude-code|anthropic]
    [--limite 0] [--resumen resultados/comparacion_baselines.csv] [--seco]

--pares acepta varios archivos (cada sistema se evalúa en cada uno). Los lotes con columna `revisor1`
solo usan los pares revisados. --seco muestra el prompt del primer lote sin llamar al LLM. Ver llm.py para los backends.
"""
import argparse
import csv
import os
import sys

import sacrebleu

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "chilenismos"))
from baselines import PARES_POR_DEFECTO, cargar_pares, guardar_resumen, ruta_salida  # noqa: E402
from dicc import RUTAS, cargar_entradas, construir_reglas, entradas_en  # noqa: E402
from llm import TAM_LOTE, prompt_usuario, traducir  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", nargs="+", default=[next((p for p in PARES_POR_DEFECTO if os.path.exists(p)), PARES_POR_DEFECTO[0])])
    ap.add_argument("--escenario", default="flo", choices=["equipo", "flo"])
    ap.add_argument("--backend", default="claude-code", choices=["claude-code", "anthropic"])
    ap.add_argument("--modelo", help="modelo del backend (por defecto el del backend)")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--resumen")
    ap.add_argument("--out", default="data/processed/predicciones_llm.csv")
    ap.add_argument("--solo-dicc", action="store_true", help="solo llm_dicc_<escenario> (si cambió el diccionario)")
    ap.add_argument("--seco", action="store_true")
    args = ap.parse_args()

    _, indice, patron = construir_reglas(cargar_entradas(RUTAS[args.escenario], incluir_ambiguos=True))
    nombre_dicc = f"llm_dicc_{args.escenario}"
    for ruta_pares in args.pares:
        pares = cargar_pares(ruta_pares)
        if args.limite:
            pares = pares[:args.limite]
        fuente, ref = [p["chileno"] for p in pares], [p["neutro"] for p in pares]
        con_dicc = [(s, entradas_en(s, indice, patron)) for s in fuente]
        sin_dicc = [(s, None) for s in fuente]
        if args.seco:
            print(prompt_usuario(con_dicc[:TAM_LOTE][:3]))
            return

        print(f"\n{os.path.basename(ruta_pares)}: {len(pares)} pares")
        preds = {}
        if not args.solo_dicc:
            print("LLM zero-shot"); preds["llm_zero_shot"] = traducir(sin_dicc, args.backend, args.modelo)
        print(nombre_dicc); preds[nombre_dicc] = traducir(con_dicc, args.backend, args.modelo)
        resumen = []
        for nombre, hip in preds.items():
            bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
            print(f"{nombre:<18} {bleu:6.1f} {chrf:6.1f}")
            resumen.append({"sistema": nombre, "escenario": args.escenario if "dicc" in nombre else "", "bleu": f"{bleu:.1f}",
                            "chrf": f"{chrf:.1f}", "n_pares": len(pares), "pares": os.path.basename(ruta_pares),
                            "nota": f"backend {args.backend}" + (f", modelo {args.modelo}" if args.modelo else "")})
        if args.resumen:
            guardar_resumen(args.resumen, resumen)
        salida = ruta_salida(args.out, ruta_pares, len(args.pares) > 1)
        os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
        with open(salida, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["chileno", "neutro", *preds])
            w.writerows(zip(fuente, ref, *preds.values()))


if __name__ == "__main__":
    main()
