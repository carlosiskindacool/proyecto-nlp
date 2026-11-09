"""
Busca en el corpus oraciones que contienen términos del diccionario (candidatas para anotar).

python idea_flo/oraciones.py --corpus RUTA/data [--escenario flo] [--fuentes mc4,news,complaints]
    [--max-por-termino 8] [--archivos 61,62] [--out data/interim/candidatas.csv]

Por defecto excluye los tuits: antes de publicar texto de tuits hay que consultar al profesor
(términos de la plataforma, datos personales). Con --incluir-tuits se agregan, y la salida queda
en data/interim (ignorada por git); no la subas al repo.
"""
import argparse
import csv
import glob
import os
import random
import re
import sys
from collections import defaultdict
from multiprocessing import Pool

import pyarrow.parquet as pq

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "chilenismos"))
from dicc import RUTAS, cargar_entradas

TOK = re.compile(r"\w+", re.U)
URL = re.compile(r"https?://\S+|www\.\S+")
MENCION = re.compile(r"@\w+")
ARCHIVOS, SIMPLES, FRASES, FUENTES, TOPE = [], set(), defaultdict(list), set(), 8


def iniciar(archivos, simples, frases, fuentes, tope):
    global ARCHIVOS, SIMPLES, FRASES, FUENTES, TOPE
    ARCHIVOS, SIMPLES, FRASES, FUENTES, TOPE = archivos, simples, frases, fuentes, tope


def buscar(i):
    out = defaultdict(list)
    for lote in pq.ParquetFile(ARCHIVOS[i]).iter_batches(batch_size=50000, columns=["text", "source"]):
        for t, fuente in zip(lote.column("text").to_pylist(), lote.column("source").to_pylist()):
            if fuente not in FUENTES or not (25 <= len(t) <= 240) or t.startswith("RT @"):
                continue
            if fuente != "twitter" and ("@" in t or "twitter.com" in t):
                continue    # algunos textos de noticias y reclamos son tuits pegados
            toks = [x.lower() for x in TOK.findall(URL.sub(" ", t))]
            hallados = set(toks) & SIMPLES
            if FRASES:
                relleno = " " + " ".join(toks) + " "
                for primera in set(toks) & FRASES.keys():
                    hallados |= {f for f in FRASES[primera] if f" {f} " in relleno}
            for h in hallados:
                if len(out[h]) < TOPE:
                    out[h].append((re.sub(r"\s+", " ", MENCION.sub("@usuario", URL.sub("", t))).strip(), fuente))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="carpeta con los .parquet (columnas text, source)")
    ap.add_argument("--escenario", default="flo", choices=["equipo", "flo"])
    ap.add_argument("--fuentes", default="mc4,news,complaints")
    ap.add_argument("--incluir-tuits", action="store_true")
    ap.add_argument("--max-por-termino", type=int, default=8)
    ap.add_argument("--terminos", type=int, default=0,
                    help="solo los N términos más frecuentes del diccionario (sin especies); 0 = todos")
    ap.add_argument("--archivos", help="índices separados por coma (para pruebas)")
    ap.add_argument("--out", default="data/interim/candidatas.csv")
    args = ap.parse_args()

    fuentes = set(args.fuentes.split(","))
    if args.incluir_tuits:
        fuentes.add("twitter")
    archivos = sorted(glob.glob(os.path.join(args.corpus, "*.parquet")))
    if args.archivos:
        archivos = [archivos[int(i)] for i in args.archivos.split(",")]
    entradas = [e for e in cargar_entradas(RUTAS[args.escenario], incluir_ambiguos=True, exigir_reemplazo=False)
                if e.get("tipo") != "especie"]
    if args.terminos:
        entradas = entradas[:args.terminos]
    simples, frases, termino_de = set(), defaultdict(list), {}
    for e in entradas:
        for forma in e["formas"]:
            termino_de.setdefault(forma, e["termino"])
            if " " in forma:
                frases[forma.split()[0]].append(forma)
            else:
                simples.add(forma)

    reunidas = defaultdict(list)
    with Pool(max(1, min(os.cpu_count() - 1, 8)), initializer=iniciar,
              initargs=(archivos, simples, dict(frases), fuentes, args.max_por_termino)) as pool:
        for out in pool.imap_unordered(buscar, range(len(archivos))):
            for forma, lista in out.items():
                reunidas[termino_de[forma]] += lista
    random.seed(1)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["termino", "oracion", "fuente"])
        for termino, lista in sorted(reunidas.items()):
            random.shuffle(lista)
            for texto, fuente in lista[:args.max_por_termino]:
                w.writerow([termino, texto, fuente])
    print(f"{len(reunidas)} términos con oraciones -> {args.out}")


if __name__ == "__main__":
    main()
