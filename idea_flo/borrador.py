"""
Borrador de pares chileno -> neutro con un LLM, usando el diccionario como contexto.
Una persona revisa y corrige el borrador después (columna `neutro`) y anota su nombre en `revisor1`
(y en `revisor2` si hay segunda revisión).

python idea_flo/borrador.py [--entrada data/interim/candidatas.csv] [--escenario flo]
    [--backend claude-code|anthropic] [--salida annotation/borrador.csv] [--limite 0] [--seco]

--seco imprime el prompt del primer lote sin llamar al LLM. Ver llm.py para los backends.
"""
import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "chilenismos"))
from dicc import RUTAS, cargar_entradas, construir_reglas, entradas_en  # noqa: E402
from llm import SISTEMA, TAM_LOTE, prompt_usuario, traducir  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/interim/candidatas.csv")
    ap.add_argument("--escenario", default="flo", choices=["equipo", "flo"])
    ap.add_argument("--backend", default="claude-code", choices=["claude-code", "anthropic"])
    ap.add_argument("--modelo")
    ap.add_argument("--salida", default="annotation/borrador.csv")
    ap.add_argument("--limite", type=int, default=0, help="solo las primeras N oraciones")
    ap.add_argument("--seco", action="store_true")
    args = ap.parse_args()

    _, indice, patron = construir_reglas(cargar_entradas(RUTAS[args.escenario], incluir_ambiguos=True))
    with open(args.entrada, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    if args.limite:
        filas = filas[:args.limite]
    items = [(r["oracion"], entradas_en(r["oracion"], indice, patron)) for r in filas]
    if args.seco:
        print("SISTEMA:", SISTEMA, "\n")
        print(prompt_usuario(items[:TAM_LOTE]))
        return

    neutros = traducir(items, args.backend, args.modelo)
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["termino", "oracion", "neutro", "revisor1", "revisor2"], delimiter=";")
        w.writeheader()
        w.writerows({"termino": r["termino"], "oracion": r["oracion"], "neutro": n, "revisor1": "", "revisor2": ""}
                    for r, n in zip(filas, neutros))
    print(f"{len(filas)} borradores -> {args.salida}")


if __name__ == "__main__":
    main()
