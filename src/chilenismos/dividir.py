"""
Paso 4 del flujo: divide los pares revisados en train / val / test.

El test son pares revisados hasta --max-test: con --revisores 1 (por defecto) basta revisor1; con --revisores 2 hacen falta
revisor1 y revisor2 (doble revisión, permite medir acuerdo).
El resto se reparte entre train y val sin repetir oraciones entre conjuntos.

python src/chilenismos/dividir.py [--pares annotation/pares_revisados.csv] [--max-test 300]
    [--revisores 1|2] [--val 0.1] [--semilla 1] [--out data/processed]
"""
import argparse
import csv
import os
import random

from rutas import PARES_REVISADOS, SPLITS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", default=PARES_REVISADOS)
    ap.add_argument("--max-test", type=int, default=300)
    ap.add_argument("--revisores", type=int, choices=[1, 2], default=1)
    ap.add_argument("--val", type=float, default=0.1)
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--out", default=SPLITS)
    args = ap.parse_args()

    with open(args.pares, encoding="utf-8") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    vistas, unicas = set(), []
    for r in filas:
        if r["oracion"] in vistas or not r["neutro"].strip():
            continue
        vistas.add(r["oracion"])
        unicas.append(r)
    random.seed(args.semilla)
    random.shuffle(unicas)
    dobles = [r for r in unicas if r.get("revisor1", "").strip() and (args.revisores == 1 or r.get("revisor2", "").strip())]
    test = dobles[:args.max_test]
    ids = {id(r) for r in test}
    resto = [r for r in unicas if id(r) not in ids]
    n_val = round(len(resto) * args.val)
    conjuntos = {"test": test, "val": resto[:n_val], "train": resto[n_val:]}

    os.makedirs(args.out, exist_ok=True)
    for nombre, rs in conjuntos.items():
        with open(os.path.join(args.out, f"{nombre}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["termino", "chileno", "neutro"])
            w.writerows((r["termino"], r["oracion"], r["neutro"]) for r in rs)
    print({k: len(v) for k, v in conjuntos.items()}, "| pares revisados disponibles para test:", len(dobles))


if __name__ == "__main__":
    main()
