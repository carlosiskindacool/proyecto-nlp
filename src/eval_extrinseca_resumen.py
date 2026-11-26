"""
Evaluación extrínseca, paso 2 de 2: Exact-Match Accuracy de las traducciones de eval_extrinseca.py.

python src/eval_extrinseca_resumen.py [--traducciones data/processed/eval_extrinseca.csv]
    [--glosario data/diccionario/glosario_es_en_final.csv]
    [--out resultados/eval_extrinseca.csv] [--md resultados/eval_extrinseca.md]

No traduce nada: tarda segundos. Si se corrige el glosario, basta con volver a correr este paso.
Agrega (o reemplaza) en el archivo de traducciones las columnas acepta_en y exact_match, sin tocar las
traducciones, y escribe el resumen por conjunto, traductor y sistema.

Exact-Match Accuracy (EMA): proporción de oraciones en que la traducción contiene, como frase completa,
alguna de las traducciones aceptadas del término ancla (columna acepta_en del glosario, separadas por "|").
Se compara en minúsculas, NFKC y sin puntuación; en los verbos se acepta también la forma sin "to"
("to steal" -> "steal"), pero no las conjugaciones. Las oraciones cuyo término no tiene acepta_en
quedan con exact_match vacío y no cuentan.
"""
import argparse
import os
import re
import unicodedata

import pandas as pd

ORDEN_SISTEMAS = ["identidad", "reglas_flo", "reglas_equipo", "mt5", "mt5_moe"]
TRADUCTORES = {"mt": "Opus-MT", "nllb": "NLLB"}
TOKEN = re.compile(r"\w+(?:[-']\w+)*")


def leer(ruta, sep=","):
    return pd.read_csv(ruta, sep=sep, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def normalizar(texto):
    texto = unicodedata.normalize("NFKC", texto).replace("’", "'").casefold()
    return " ".join(TOKEN.findall(texto))


def aceptadas(acepta_en):
    formas = set()
    for glosa in acepta_en.split("|"):
        glosa = normalizar(glosa)
        if glosa:
            formas.add(glosa)
            if glosa.startswith("to "):
                formas.add(glosa[3:])
    return formas


def exact_match(traduccion, formas):
    if not formas:
        return None
    texto = f" {normalizar(traduccion)} "
    return int(any(f" {forma} " in texto for forma in formas))


def resumen(datos):
    evaluables = datos[datos["exact_match"].notna()]
    filas = []
    for conjunto, grupo in [("todos", evaluables.drop_duplicates(["chileno", "sistema", "traductor"])), *evaluables.groupby("conjunto")]:
        tabla = (grupo.groupby(["traductor", "sistema"], sort=False)["exact_match"]
                      .agg(n_evaluables="size", aciertos="sum", ema="mean").reset_index())
        tabla.insert(0, "conjunto", conjunto)
        filas.append(tabla)
    tabla = pd.concat(filas, ignore_index=True)
    tabla["aciertos"] = tabla["aciertos"].astype(int)
    tabla["ema"] = (100 * tabla["ema"]).round(1)
    return tabla


def tabla_md(tabla):
    lineas = ["Exact-Match Accuracy (%) del término ancla al traducir al inglés la salida de cada sistema. "
              "Generado por src/eval_extrinseca_resumen.py.", ""]
    for conjunto in dict.fromkeys(tabla["conjunto"]):
        grupo = tabla[tabla["conjunto"] == conjunto]
        traductores = [t for t in TRADUCTORES if t in set(grupo["traductor"])]
        lineas += [f"### {conjunto} ({grupo['n_evaluables'].max()} oraciones evaluables)", "",
                   "| Sistema | " + " | ".join(TRADUCTORES[t] for t in traductores) + " |",
                   "|---|" + "---:|" * len(traductores)]
        sistemas = [s for s in ORDEN_SISTEMAS if s in set(grupo["sistema"])]
        sistemas += sorted(set(grupo["sistema"]) - set(sistemas))
        for sistema in sistemas:
            celdas = []
            for t in traductores:
                fila = grupo[(grupo["sistema"] == sistema) & (grupo["traductor"] == t)]
                celdas.append(f"{fila['ema'].iloc[0]:.1f}".replace(".", ",") if len(fila) else "–")
            lineas.append(f"| {sistema} | " + " | ".join(celdas) + " |")
        lineas.append("")
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traducciones", default="data/processed/eval_extrinseca.csv")
    ap.add_argument("--glosario", default="data/diccionario/glosario_es_en_final.csv")
    ap.add_argument("--out", default="resultados/eval_extrinseca.csv")
    ap.add_argument("--md", default="resultados/eval_extrinseca.md")
    args = ap.parse_args()

    datos = leer(args.traducciones).drop(columns=["acepta_en", "exact_match"], errors="ignore")
    glosario = leer(args.glosario, sep=";").set_index("termino")["acepta_en"]
    datos["acepta_en"] = datos["termino"].map(glosario).fillna("")
    datos["exact_match"] = pd.array([exact_match(t, aceptadas(a))
                                     for t, a in zip(datos["traduccion_en"], datos["acepta_en"])], dtype="Int64")
    sin_glosa = datos.loc[datos["exact_match"].isna(), "chileno"].nunique()
    print(f"{datos['chileno'].nunique()} oraciones únicas | {sin_glosa} sin acepta_en para su término (no cuentan)")

    temporal = args.traducciones + ".tmp"
    datos.to_csv(temporal, index=False, encoding="utf-8-sig")
    os.replace(temporal, args.traducciones)

    tabla = resumen(datos)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    tabla.to_csv(args.out, index=False, encoding="utf-8")
    texto = tabla_md(tabla)
    with open(args.md, "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)
    print(f"Escrito {args.out} y {args.md}; columnas acepta_en y exact_match en {args.traducciones}")


if __name__ == "__main__":
    main()
