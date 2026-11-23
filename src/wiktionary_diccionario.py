"""
Extrae las entradas de la categoría ES:Chile del Wikcionario en español
a partir del volcado estructurado de kaikki.org (wiktextract).

1) Descarga en data/raw (98 MB comprimido):
   https://kaikki.org/dictionary/downloads/es/es-extract.jsonl.gz
2) Ejecuta:
   python src/wiktionary_diccionario.py data/raw/es-extract.jsonl.gz

Salidas (en data/raw/):
  chilenismos_acepciones.csv  -> una fila por acepción (formato "largo", ideal para análisis)
  chilenismos_terminos.csv    -> una fila por término, con listas agregadas
  chilenismos.jsonl           -> entradas completas originales (por si necesitas más campos)
"""
import gzip
import json
import os
import sys

import pandas as pd

CATEGORIA = "ES:Chile"
TAG_PAIS = "Chile"
SALIDA = "data/raw"

# Etiquetas geográficas (ámbito). El resto de las etiquetas se trata como "uso"
# (coloquial, despectivo, rural, etc.) o como etiqueta gramatical.
GEO = {
    "Chile", "Argentina", "Uruguay", "Peru", "Bolivia", "Ecuador", "Colombia",
    "Venezuela", "Paraguay", "Mexico", "Cuba", "Spain", "Central-America",
    "Guatemala", "Honduras", "El-Salvador", "Nicaragua", "Costa-Rica", "Panama",
    "Dominican-Republic", "Puerto-Rico", "Latin-America", "Andes", "Rioplatense",
    "Caribbean", "Canary-Islands", "Philippines", "US",
}
GRAMATICALES = {"adverbial", "adjective", "noun", "verb", "masculine", "feminine",
                "transitive", "intransitive", "pronominal", "plural", "singular"}


def nombres_categorias(obj):
    """Las categorías vienen como strings (raw) u objetos {"name": ...} (postprocesado)."""
    out = []
    for c in obj.get("categories", []) or []:
        out.append(c if isinstance(c, str) else c.get("name", ""))
    return out


def es_de_chile(sentido):
    return CATEGORIA in nombres_categorias(sentido) or TAG_PAIS in (sentido.get("tags") or [])


def relacion_por_acepcion(entrada, campo):
    """Agrupa sinónimos/antónimos/etc. por índice de acepción ('' = toda la entrada)."""
    d = {}
    for r in entrada.get(campo, []) or []:
        clave = str(r.get("sense_index", "") or "")
        palabra = r.get("word", "")
        if r.get("note"):
            palabra += f" ({r['note']})"
        d.setdefault(clave, []).append(palabra)
    return d


def main(ruta, solo_acepciones_chilenas=False):
    filas, completas = [], []
    abrir = gzip.open if ruta.endswith(".gz") else open
    with abrir(ruta, "rt", encoding="utf-8") as f:
        for linea in f:
            e = json.loads(linea)
            if e.get("lang_code") != "es":
                continue
            sentidos = e.get("senses", []) or []
            if not (CATEGORIA in nombres_categorias(e) or any(es_de_chile(s) for s in sentidos)):
                continue
            completas.append(e)

            sin = relacion_por_acepcion(e, "synonyms")
            ant = relacion_por_acepcion(e, "antonyms")
            rel = relacion_por_acepcion(e, "related")
            etim = " ".join(e.get("etymology_texts", []) or [])

            for i, s in enumerate(sentidos, 1):
                chilena = es_de_chile(s)
                if solo_acepciones_chilenas and not chilena:
                    continue
                idx = str(s.get("sense_index", i))
                tags = s.get("tags", []) or []
                filas.append({
                    "termino": e.get("word"),
                    "categoria_gramatical": e.get("pos_title") or e.get("pos"),
                    "n_acepcion": idx,
                    "definicion": " ".join(s.get("glosses", []) or []),
                    "ambito": ", ".join(t for t in tags if t in GEO),
                    "uso": ", ".join(t for t in tags if t not in GEO and t not in GRAMATICALES),
                    "acepcion_chilena": chilena,
                    "sinonimos": "; ".join(sin.get(idx, []) + sin.get("", [])),
                    "antonimos": "; ".join(ant.get(idx, []) + ant.get("", [])),
                    "relacionados": "; ".join(rel.get(idx, []) + rel.get("", [])),
                    "ejemplos": " || ".join(x.get("text", "") for x in s.get("examples", []) or []),
                    "etimologia": etim,
                    "ipa": ", ".join(x["ipa"] for x in e.get("sounds", []) or [] if "ipa" in x),
                    "url": "https://es.wiktionary.org/wiki/" + e.get("word", "").replace(" ", "_"),
                })

    df = pd.DataFrame(filas)
    os.makedirs(SALIDA, exist_ok=True)
    df.to_csv(os.path.join(SALIDA, "chilenismos_acepciones.csv"), index=False, encoding="utf-8-sig")

    agg = (df.groupby(["termino", "categoria_gramatical"], sort=True)
             .agg(definiciones=("definicion", lambda x: " | ".join(f"{n}. {d}" for n, d in enumerate(x, 1))),
                  ambitos=("ambito", lambda x: ", ".join(sorted({a for v in x for a in v.split(", ") if a}))),
                  usos=("uso", lambda x: ", ".join(sorted({a for v in x for a in v.split(", ") if a}))),
                  sinonimos=("sinonimos", lambda x: "; ".join(dict.fromkeys(a for v in x for a in v.split("; ") if a))),
                  n_acepciones=("definicion", "size"),
                  url=("url", "first"))
             .reset_index())
    agg.to_csv(os.path.join(SALIDA, "chilenismos_terminos.csv"), index=False, encoding="utf-8-sig")

    with open(os.path.join(SALIDA, "chilenismos.jsonl"), "w", encoding="utf-8") as out:
        for e in completas:
            out.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"{len(completas)} entradas, {len(df)} acepciones, {df['termino'].nunique()} términos únicos")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "es-extract.jsonl.gz",
         solo_acepciones_chilenas="--solo-chile" in sys.argv)