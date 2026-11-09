"""
Borrador de pares chileno -> neutro con un LLM, usando el diccionario como contexto.
Una persona revisa y corrige el borrador después (columna `neutro`) y anota su nombre en `revisor1`
(un solo revisor por ahora).

python idea_flo/borrador.py [--entrada data/interim/candidatas.csv] [--escenario flo]
    [--backend claude-code|anthropic] [--salida annotation/borrador.csv] [--limite 0] [--semilla 1] [--seco]

--limite N toma N oraciones al azar (misma semilla = mismas oraciones), repartidas entre los términos.
Guarda cada 100 oraciones y, si la salida ya existe, retoma sin repetir las que ya tiene.
--seco imprime el prompt del primer lote sin llamar al LLM. Ver llm.py para los backends.
"""
import argparse
import csv
import os
import random
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
    ap.add_argument("--limite", type=int, default=0, help="solo N oraciones, elegidas al azar")
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--guardar-cada", type=int, default=100)
    ap.add_argument("--seco", action="store_true")
    args = ap.parse_args()

    _, indice, patron = construir_reglas(cargar_entradas(RUTAS[args.escenario], incluir_ambiguos=True, exigir_reemplazo=False))
    with open(args.entrada, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    if args.limite:
        random.Random(args.semilla).shuffle(filas)
        filas = filas[:args.limite]
    items = [(r["oracion"], entradas_en(r["oracion"], indice, patron)) for r in filas]
    if args.seco:
        print("SISTEMA:", SISTEMA, "\n")
        print(prompt_usuario(items[:TAM_LOTE]))
        return

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    hechas = set()
    if os.path.exists(args.salida):
        with open(args.salida, encoding="utf-8") as f:
            hechas = {r["oracion"] for r in csv.DictReader(f, delimiter=";")}
    nuevo = not hechas
    pendientes = [(r, it) for r, it in zip(filas, items) if r["oracion"] not in hechas]
    print(f"{len(hechas)} ya hechas, {len(pendientes)} por hacer", flush=True)
    with open(args.salida, "a" if hechas else "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["termino", "oracion", "neutro", "revisor1"], delimiter=";")
        if nuevo:
            w.writeheader()
        for i in range(0, len(pendientes), args.guardar_cada):
            trozo = pendientes[i:i + args.guardar_cada]
            neutros = traducir([it for _, it in trozo], args.backend, args.modelo)
            w.writerows({"termino": r["termino"], "oracion": r["oracion"], "neutro": n, "revisor1": ""}
                        for (r, _), n in zip(trozo, neutros))
            f.flush()
            print(f"  {min(i + args.guardar_cada, len(pendientes))}/{len(pendientes)}", flush=True)
    print(f"borradores -> {args.salida}")

if __name__ == "__main__":
    main()
