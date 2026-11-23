"""
Cuenta cuántas veces aparece cada término de Wikcionario en el Chilean Spanish Corpus
y genera la plantilla de anotación.

python src/generate_annot_template.py [--limite 100000] [--workers 9] [--lote 2000]
    [--entrada data/raw/chilenismos_acepciones.csv] [--salida data/interim/chilenismos_annot_template.csv]

El corpus requiere aceptar sus términos en https://huggingface.co/datasets/jorgeortizfuentes/chilean-spanish-corpus
e iniciar sesión con `hf auth login`. Se lee en streaming para no guardar sus ~50 GB en disco.

Conteo: ocurrencias exactas de palabras completas, sin distinguir mayúsculas y respetando tildes.
No cuenta dentro de URLs ni menciones. `conteo` es por término: se repite en cada acepción,
así que no debe sumarse por fila.
"""
import argparse
import itertools
import os
import re
import time
import unicodedata
from collections import Counter
from multiprocessing import Pool

import pandas as pd

DATASET = "jorgeortizfuentes/chilean-spanish-corpus"
COLUMNAS_EXCLUIDAS = ["ipa", "etimologia", "url"]
URL_O_MENCION = re.compile(r"https?://\S+|www\.\S+|@\w+")
TOKEN = re.compile(r"\w+(?:[-']\w+)*")

_claves, _largos = None, None


def tokenizar(texto):
    texto = unicodedata.normalize("NFC", texto).replace("̲", "").replace("’", "'").casefold()
    return TOKEN.findall(URL_O_MENCION.sub(" ", texto))


def construir_indice(terminos):
    """Términos como tuplas de palabras, y largos posibles según la primera palabra."""
    claves = {tuple(tokenizar(t)) for t in terminos} - {()}
    largos = {}
    for clave in claves:
        largos.setdefault(clave[0], set()).add(len(clave))
    return claves, {k: tuple(sorted(v)) for k, v in largos.items()}


def contar_textos(textos, claves, largos):
    """Cuenta todas las ocurrencias, incluidos términos dentro de otros (toque en «al toque»)."""
    conteo = Counter()
    for texto in textos:
        if not texto:
            continue
        palabras = tokenizar(texto)
        for i, palabra in enumerate(palabras):
            for n in largos.get(palabra, ()):
                candidato = tuple(palabras[i:i + n])
                if candidato in claves:
                    conteo[candidato] += 1
    return conteo


def _iniciar(claves, largos):
    global _claves, _largos
    _claves, _largos = claves, largos


def _contar(textos):
    return contar_textos(textos, _claves, _largos)


def contar_corpus(claves, largos, limite, workers, tam_lote):
    from datasets import load_dataset
    from datasets.exceptions import DatasetNotFoundError

    try:
        ds = load_dataset(DATASET, split="train", streaming=True).select_columns("text")
    except DatasetNotFoundError as e:
        raise SystemExit(f"No se pudo acceder a {DATASET}. Acepta sus términos en "
                         f"https://huggingface.co/datasets/{DATASET} y ejecuta `hf auth login`.") from e
    if limite:
        ds = ds.take(limite)

    lotes = (b["text"] for b in ds.iter(batch_size=tam_lote))
    total, filas, inicio, proximo_aviso = Counter(), 0, time.time(), 500_000
    with Pool(workers, initializer=_iniciar, initargs=(claves, largos)) as pool:
        # Se leen pocos lotes por vez para que la memoria no crezca si la red es más rápida que los workers.
        while grupo := list(itertools.islice(lotes, workers * 2)):
            for parcial in pool.map(_contar, grupo):
                total.update(parcial)
            filas += sum(map(len, grupo))
            if filas >= proximo_aviso:
                print(f"{filas:,} textos | {filas / (time.time() - inicio):,.0f} textos/s", flush=True)
                proximo_aviso += 500_000
    return total, filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/raw/chilenismos_acepciones.csv")
    ap.add_argument("--salida", default="data/interim/chilenismos_annot_template.csv")
    ap.add_argument("--limite", type=int, default=0, help="procesa solo los primeros N textos (0 = todos)")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--lote", type=int, default=2000)
    args = ap.parse_args()

    df = pd.read_csv(args.entrada, encoding="utf-8-sig", keep_default_na=False)
    claves, largos = construir_indice(df["termino"])
    total, filas = contar_corpus(claves, largos, args.limite, args.workers, args.lote)

    df = df.drop(columns=COLUMNAS_EXCLUIDAS)
    df.insert(df.columns.get_loc("termino") + 1, "conteo", [total.get(tuple(tokenizar(t)), 0) for t in df["termino"]])
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    df.to_csv(args.salida, index=False, encoding="utf-8-sig")

    por_termino = df.drop_duplicates("termino")
    print(f"{filas:,} textos | {len(df):,} acepciones | {len(por_termino):,} términos | "
          f"{(por_termino['conteo'] > 0).sum():,} con al menos una ocurrencia")
    print(f"Escrito {args.salida}")


if __name__ == "__main__":
    main()
