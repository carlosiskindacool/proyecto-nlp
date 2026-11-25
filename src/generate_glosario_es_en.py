"""
Glosario de prueba con todos los términos ancla únicos de los lotes anotados.

python src/generate_glosario_es_en.py [--revisado data/diccionario/glosario_es_en_test_revisado.csv]
    [--salida data/diccionario/glosario_es_en_test.csv]

Una fila por término, separada por ";":
  termino       término ancla de annotation/lote*.csv
  reemplazo_es  reemplazo neutro del diccionario revisado de Flo (vacío si no lo tiene)
  acepta_en     glosas en inglés de sus acepciones chilenas en Wikcionario, separadas por " | "
                (vacío si el término no está en en_acepciones_chile.csv)

Si existe el archivo --revisado, sus filas se copian tal cual y solo se agregan al final,
en orden alfabético, los términos ancla que no tiene.
"""
import argparse
import csv
import glob
import io
import os

import pandas as pd

LOTES = "annotation/lote*.csv"
GLOSAS_EN = "data/diccionario/procesado/en_acepciones_chile.csv"
DICCIONARIO = "data/curado/diccionario_flo.csv"
COLUMNAS = ["termino", "reemplazo_es", "acepta_en"]


def leer(ruta, sep=","):
    return pd.read_csv(ruta, sep=sep, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def filas_nuevas(anclas):
    en = leer(GLOSAS_EN)
    en = en[en["termino"].isin(anclas) & (en["glosa_en"].str.strip() != "")]
    glosas = en.groupby("termino")["glosa_en"].agg(lambda x: " | ".join(dict.fromkeys(g.strip() for g in x)))
    reemplazos = leer(DICCIONARIO).set_index("termino")["reemplazo"]
    return [[t, reemplazos.get(t, ""), glosas.get(t, "")] for t in sorted(anclas)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--revisado", default="data/diccionario/glosario_es_en_test_revisado.csv")
    ap.add_argument("--salida", default="data/diccionario/glosario_es_en_test.csv")
    args = ap.parse_args()

    anclas = set()
    for ruta in sorted(glob.glob(LOTES)):
        anclas |= set(leer(ruta, sep=";")["termino"].str.strip())

    lineas, ya_estan = [";".join(COLUMNAS)], set()
    if os.path.exists(args.revisado):
        with open(args.revisado, encoding="utf-8-sig", newline="") as f:
            revisadas = [l for l in f.read().splitlines() if l.strip()]
        if revisadas[0].split(";") != COLUMNAS:
            raise SystemExit(f"{args.revisado} no tiene las columnas {COLUMNAS}")
        lineas += revisadas[1:]
        ya_estan = {next(csv.reader([l], delimiter=";"))[0] for l in revisadas[1:]}

    nuevas = [f for f in filas_nuevas(anclas - ya_estan)]
    buffer = io.StringIO()
    csv.writer(buffer, delimiter=";", lineterminator="\n").writerows(nuevas)
    lineas += buffer.getvalue().splitlines()

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    with open(args.salida, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\r\n".join(lineas) + "\r\n")
    print(f"{len(anclas)} términos ancla | {len(ya_estan)} filas revisadas | {len(nuevas)} agregadas "
          f"({sum(1 for f in nuevas if not f[1])} sin reemplazo_es, {sum(1 for f in nuevas if not f[2])} sin acepta_en) "
          f"-> {args.salida}")


if __name__ == "__main__":
    main()
