"""
Baselines con LLM (idea de Flo): zero-shot y con el diccionario como contexto.

python src/chilenismos/baselines_llm.py [--pares annotation/lote1.csv] [--escenario flo] [--backend claude-code|anthropic]
    [--limite 0] [--resumen reports/comparacion_baselines.csv] [--seco]

--seco muestra el prompt del primer lote sin llamar al LLM. Ver llm.py para los backends.
"""
import argparse
import csv
import os

import sacrebleu

import rutas
from baselines import cargar_pares, guardar_resumen
from dicc import RUTAS, cargar_entradas, construir_reglas, entradas_en
from llm import TAM_LOTE, prompt_usuario, traducir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", default=rutas.PARES_EVAL)
    ap.add_argument("--escenario", default=rutas.ESCENARIO, choices=["equipo", "flo"])
    ap.add_argument("--backend", default="claude-code", choices=["claude-code", "anthropic"])
    ap.add_argument("--modelo", help="modelo del backend (por defecto el del backend)")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--resumen", nargs="?", const=rutas.RESULTADOS)
    ap.add_argument("--out", default=rutas.PREDICCIONES_LLM)
    ap.add_argument("--seco", action="store_true")
    args = ap.parse_args()

    pares = cargar_pares(args.pares)
    if args.limite:
        pares = pares[:args.limite]
    fuente, ref = [p["chileno"] for p in pares], [p["neutro"] for p in pares]
    _, indice, patron = construir_reglas(cargar_entradas(RUTAS[args.escenario], incluir_ambiguos=True))
    con_dicc = [(s, entradas_en(s, indice, patron)) for s in fuente]
    sin_dicc = [(s, None) for s in fuente]
    if args.seco:
        print(prompt_usuario(con_dicc[:TAM_LOTE][:3]))
        return

    nombre_dicc = f"llm_dicc_{args.escenario}"
    preds = {}
    print("LLM zero-shot"); preds["llm_zero_shot"] = traducir(sin_dicc, args.backend, args.modelo)
    print(nombre_dicc); preds[nombre_dicc] = traducir(con_dicc, args.backend, args.modelo)
    resumen = []
    for nombre, hip in preds.items():
        bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
        print(f"{nombre:<18} {bleu:6.1f} {chrf:6.1f}")
        resumen.append({"sistema": nombre, "escenario": args.escenario if "dicc" in nombre else "", "bleu": f"{bleu:.1f}",
                        "chrf": f"{chrf:.1f}", "n_pares": len(pares), "pares": os.path.basename(args.pares),
                        "nota": f"backend {args.backend}" + (f", modelo {args.modelo}" if args.modelo else "")})
    if args.resumen:
        guardar_resumen(args.resumen, resumen)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["chileno", "neutro", *preds])
        w.writerows(zip(fuente, ref, *preds.values()))


if __name__ == "__main__":
    main()
