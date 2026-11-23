"""
Limpia el texto de la plantilla de anotación.

python src/process_annot_template.py [--entrada data/interim/chilenismos_annot_template.csv]
    [--salida data/interim/chilenismos_annot_template_procesado.csv]

Quita marcas editoriales de Wikcionario (^([cita requerida]), ^[[añadir cita]], [1]), URLs,
listas incrustadas (:*Sinónimos: ...), subíndices y espacios o puntuación sobrantes.
De los enlaces como [cóndor] conserva la palabra. No elimina filas.
"""
import argparse
import os
import re
import unicodedata

import pandas as pd

COLUMNAS = ["termino", "categoria_gramatical", "definicion", "ambito", "uso", "sinonimos"]

MARCAS = re.compile(
    r"\^\s*\(?\s*\[+[^\]]*\]+\s*\)?"   # ^([cita requerida]), ^[[añadir cita]]
    r"|\[\[[^\]]*\]\]"                 # [[añadir cita]]
    r"|\[\d+\]"                        # [1]
    r"|https?://\S+|www\.\S+"          # URLs
    r"|:\*[^\n]*"                      # :*Sinónimos: ...
)
SUBINDICES = re.compile(r"[₀-₎̲]")  # subíndices y subrayado combinable
ENLACE = re.compile(r"\[([^\[\]]+)\]")
PARENTESIS_MAL_CERRADO = re.compile(r"\(([^()\[\]]*)\]")


def limpiar(texto):
    texto = SUBINDICES.sub("", unicodedata.normalize("NFC", texto))
    texto = PARENTESIS_MAL_CERRADO.sub(r"(\1)", MARCAS.sub(" ", texto))
    texto = ENLACE.sub(r"\1", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\(\s*\)", " ", texto)
    texto = re.sub(r"\(\s+", "(", texto)
    texto = re.sub(r"\s+([.,;:!?)])", r"\1", texto)
    texto = re.sub(r"(?<!\.)\.\.(?!\.)", ".", texto)
    texto = re.sub(r";(?:\s*;)+", ";", texto)
    return re.sub(r"\s+", " ", texto).strip(" ;,")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/interim/chilenismos_annot_template.csv")
    ap.add_argument("--salida", default="data/interim/chilenismos_annot_template_procesado.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.entrada, encoding="utf-8-sig", keep_default_na=False)
    for columna in COLUMNAS:
        limpia = df[columna].astype(str).map(limpiar)
        print(f"{columna:<22} {(limpia != df[columna]).sum():>5} filas modificadas")
        df[columna] = limpia
    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    df.to_csv(args.salida, index=False, encoding="utf-8-sig")
    print(f"{len(df):,} filas -> {args.salida}")


if __name__ == "__main__":
    main()
