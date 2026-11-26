"""
Elige las oraciones de un lote nuevo repartidas por frecuencia del término (alta, media, media-baja).

python src/pares/seleccionar_lote.py --candidatas data/interim/candidatas_lote2.csv
    --excluir annotation/lote_1_tuits.csv annotation/lote_1_noticias.csv annotation/lote1.csv
    --por-nivel 50 --out data/interim/seleccion_lote2.csv

Niveles (según `n_tuits_muestra` del diccionario; la columna `frecuencia` no existe para el libro 1):
  alta        >= 198 tuits
  media       67 a 197
  media_baja  14 a 66
Los términos con menos de 14 tuits («baja») no se usan: casi no hay oraciones. Una oración por término,
sin repetir términos ni oraciones de los lotes de `--excluir`. Si hay noticias, se prefieren hasta
`--max-noticias` por nivel (traen poca jerga, así que suelen ser pocas).
"""
import argparse
import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chilenismos"))
from dicc import RUTAS  # noqa: E402

NIVELES = [("alta", 198, 10**9), ("media", 67, 198), ("media_baja", 14, 67)]


def nivel(n):
    for nombre, a, b in NIVELES:
        if a <= n < b:
            return nombre
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidatas", required=True)
    ap.add_argument("--excluir", nargs="*", default=[])
    ap.add_argument("--por-nivel", type=int, default=50)
    ap.add_argument("--max-noticias", type=int, default=15, help="máximo de oraciones de noticias por nivel")
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--out", default="data/interim/seleccion_lote.csv")
    args = ap.parse_args()

    dic = {}
    with open(RUTAS["flo"], encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["keep"] == "1" and r["tipo"] != "especie":
                dic[r["termino"]] = (int(r["n_tuits_muestra"] or 0), r["ambiguo"] == "1")
    usados_t, usadas_o = set(), set()
    for p in args.excluir:
        with open(p, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f, delimiter=";"):
                usados_t.add(r["termino"])
                usadas_o.add(r["oracion"])
    cand = {}
    with open(args.candidatas, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if r["termino"] in usados_t or r["oracion"] in usadas_o or r["termino"] not in dic:
                continue
            cand.setdefault(r["termino"], []).append(r)
    rnd = random.Random(args.semilla)
    por_nivel = {n: [] for n, _, _ in NIVELES}
    for t, filas in cand.items():
        niv = nivel(dic[t][0])
        if niv:
            por_nivel[niv].append(t)
    elegidas, vistas = [], set()
    for nombre, _, _ in NIVELES:
        terminos = sorted(por_nivel[nombre])
        rnd.shuffle(terminos)
        # los ambiguos son los más útiles para evaluar (importa el contexto): entran primero hasta ~1/4 del nivel
        amb = [t for t in terminos if dic[t][1]][:max(1, args.por_nivel // 4)]
        resto = [t for t in terminos if t not in amb]
        orden = amb + resto
        n_noticias = n = 0
        for t in orden:
            if n >= args.por_nivel:
                break
            filas = cand[t][:]
            rnd.shuffle(filas)
            r = next((x for x in filas if x["fuente"] != "twitter" and n_noticias < args.max_noticias
                      and x["oracion"] not in vistas),
                     next((x for x in filas if x["fuente"] == "twitter" and x["oracion"] not in vistas), None))
            if r is None:
                continue
            vistas.add(r["oracion"])
            n_noticias += r["fuente"] != "twitter"
            n += 1
            elegidas.append({"termino": t, "oracion": r["oracion"], "fuente": r["fuente"], "nivel": nombre,
                             "n_tuits": dic[t][0], "ambiguo": int(dic[t][1])})
        print(f"{nombre}: {n} oraciones ({n_noticias} de noticias) de {len(terminos)} términos con oraciones")
    rnd.shuffle(elegidas)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["termino", "oracion", "fuente", "nivel", "n_tuits", "ambiguo"], delimiter=";")
        w.writeheader()
        w.writerows(elegidas)
    print(f"{len(elegidas)} pares -> {args.out}")


if __name__ == "__main__":
    main()
