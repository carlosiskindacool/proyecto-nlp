"""
Evaluación extrínseca: traduce al inglés la salida de cada normalizador y mide si el término ancla
quedó bien traducido según el glosario.

python src/eval_extrinseca.py [--entrada "data/processed/predicciones_*.csv"]
    [--glosario data/diccionario/glosario_es_en_test.csv] [--traductores mt nllb] [--limite N]
    [--out data/processed/eval_extrinseca.csv] [--resumen resultados/eval_extrinseca.csv]

En un Mac conviene correrlo como `caffeinate -i python src/eval_extrinseca.py`: si el equipo entra en
reposo, el proceso se congela. Con los modelos ya descargados, HF_HUB_OFFLINE=1 evita consultas a Hugging Face.

Sistemas (columna del CSV -> nombre): identidad, reglas_flo, reglas_equipo, mt5_flo_fp32 -> mt5,
mt5_moe_fp32 -> mt5_moe. Las demás columnas (mt5_flo, mt5_sin_ajustar, ...) se ignoran.

Traductores español -> inglés, los mismos de los baselines de ida y vuelta (solo la ida):
  mt   : Opus-MT (src/chilenismos/baseline_mt.py)
  nllb : NLLB-200 (src/chilenismos/baseline_nllb.py)

Salida: una fila por oración única x sistema x traductor.

Exact-Match Accuracy (EMA): proporción de oraciones en que la traducción contiene, como frase completa,
alguna de las traducciones aceptadas del término ancla (columna acepta_en del glosario, separadas por "|").
Se compara en minúsculas, NFKC y sin puntuación; en los verbos se acepta también la forma sin "to"
("to steal" -> "steal"), pero no las conjugaciones. Las oraciones cuyo término no tiene acepta_en
quedan con exact_match vacío y no cuentan.
"""
import argparse
import glob
import os
import re
import sys
import time
import unicodedata

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "chilenismos"))
import baseline_mt  # noqa: E402
import baseline_nllb  # noqa: E402

SISTEMAS = {"identidad": "identidad", "reglas_flo": "reglas_flo", "reglas_equipo": "reglas_equipo",
            "mt5_flo_fp32": "mt5", "mt5_moe_fp32": "mt5_moe"}
NO_SISTEMA = {"conjunto", "chileno", "neutro", "referencia", "termino"}
MODELO_MT = "Helsinki-NLP/opus-mt-es-en"
MODELO_NLLB = "facebook/nllb-200-distilled-600M"
TOKEN = re.compile(r"\w+(?:[-']\w+)*")


def leer(ruta, sep=","):
    return pd.read_csv(ruta, sep=sep, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def cargar_salidas(patron):
    """Una fila por oración única y sistema: conjunto, termino, chileno, sistema, salida_es."""
    partes = []
    for ruta in sorted(glob.glob(patron)):
        df = leer(ruta)
        if "conjunto" not in df:
            df["conjunto"] = os.path.basename(ruta).removeprefix("predicciones_")
        for col in df.columns:
            if col in SISTEMAS:
                partes.append(pd.DataFrame({"conjunto": df["conjunto"], "termino": df["termino"],
                                            "chileno": df["chileno"], "sistema": SISTEMAS[col], "salida_es": df[col]}))
            elif col not in NO_SISTEMA:
                print(f"Se ignora {col} ({os.path.basename(ruta)})")
    if not partes:
        raise SystemExit(f"No hay columnas de sistemas en {patron}")
    datos = pd.concat(partes, ignore_index=True)

    distintas = datos.groupby(["chileno", "sistema"])["salida_es"].nunique()
    if (distintas > 1).any():
        print(f"Aviso: {(distintas > 1).sum()} oraciones con más de una salida en un mismo sistema; se usa la primera")
    datos = datos.drop_duplicates(["chileno", "sistema"]).reset_index(drop=True)

    por_oracion = datos.groupby("chileno")["sistema"].nunique()
    incompletas = por_oracion[por_oracion < len(set(SISTEMAS.values()))]
    if len(incompletas):
        print(f"Aviso: {len(incompletas)} oraciones no tienen salida de todos los sistemas")
    return datos


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


def traducir(textos, traductor, lote):
    """{texto: traducción}; cada texto distinto se traduce una sola vez."""
    unicos = [t for t in dict.fromkeys(textos) if t.strip()]
    inicio = time.time()
    if traductor == "mt":
        en = baseline_mt.traducir(unicos, MODELO_MT, lote=lote)
    else:
        tok, mod, dev = baseline_nllb.cargar(MODELO_NLLB)
        en = baseline_nllb.traducir(unicos, tok, mod, dev, "spa_Latn", "eng_Latn", lote=lote)
        del mod
    print(f"{traductor}: {len(unicos)} textos distintos en {time.time() - inicio:.0f} s", flush=True)
    return {"": "", **dict(zip(unicos, en))}


def resumen(datos):
    evaluables = datos[datos["exact_match"].notna()]
    filas = []
    for conjunto, grupo in [("todos", evaluables), *evaluables.groupby("conjunto")]:
        tabla = (grupo.groupby(["traductor", "sistema"], sort=False)["exact_match"]
                      .agg(n_evaluables="size", aciertos="sum", ema="mean").reset_index())
        tabla.insert(0, "conjunto", conjunto)
        filas.append(tabla)
    tabla = pd.concat(filas, ignore_index=True)
    tabla["aciertos"] = tabla["aciertos"].astype(int)
    tabla["ema"] = (100 * tabla["ema"]).round(1)
    return tabla


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/processed/predicciones_*.csv")
    ap.add_argument("--glosario", default="data/diccionario/glosario_es_en_test.csv")
    ap.add_argument("--traductores", nargs="+", choices=["mt", "nllb"], default=["mt", "nllb"])
    ap.add_argument("--lote", type=int, default=16)
    ap.add_argument("--limite", type=int, default=0, help="usa solo las primeras N oraciones (0 = todas)")
    ap.add_argument("--out", default="data/processed/eval_extrinseca.csv")
    ap.add_argument("--resumen", default="resultados/eval_extrinseca.csv")
    args = ap.parse_args()

    salidas = cargar_salidas(args.entrada)
    if args.limite:
        salidas = salidas[salidas["chileno"].isin(salidas["chileno"].drop_duplicates()[:args.limite])]
    glosario = leer(args.glosario, sep=";").set_index("termino")["acepta_en"]
    sin_glosa = ~salidas["termino"].map(glosario).fillna("").str.strip().astype(bool)
    print(f"{salidas['chileno'].nunique()} oraciones únicas x {salidas['sistema'].nunique()} sistemas | "
          f"{salidas.loc[sin_glosa, 'chileno'].nunique()} oraciones sin acepta_en para su término")

    partes = []
    for traductor in args.traductores:
        en = traducir(salidas["salida_es"].tolist(), traductor, args.lote)
        partes.append(salidas.assign(traductor=traductor, traduccion_en=salidas["salida_es"].map(en)))
    datos = pd.concat(partes, ignore_index=True)
    datos["acepta_en"] = datos["termino"].map(glosario).fillna("")
    datos["exact_match"] = [exact_match(t, aceptadas(a)) for t, a in zip(datos["traduccion_en"], datos["acepta_en"])]
    datos["exact_match"] = datos["exact_match"].astype("Int64")
    columnas = ["conjunto", "termino", "chileno", "sistema", "traductor", "salida_es", "traduccion_en",
                "acepta_en", "exact_match"]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    datos[columnas].to_csv(args.out, index=False, encoding="utf-8-sig")

    tabla = resumen(datos)
    os.makedirs(os.path.dirname(args.resumen) or ".", exist_ok=True)
    tabla.to_csv(args.resumen, index=False, encoding="utf-8")
    vista = tabla[tabla["conjunto"] == "todos"].pivot(index="sistema", columns="traductor", values="ema")
    vista = vista.reindex([s for s in dict.fromkeys(SISTEMAS.values()) if s in vista.index])
    n = tabla.loc[tabla["conjunto"] == "todos", "n_evaluables"].max()
    print(f"\nExact-Match Accuracy (%), {n} oraciones evaluables por sistema y traductor:\n{vista.to_string()}")
    print(f"\n{len(datos):,} filas -> {args.out}\nResumen -> {args.resumen}")


if __name__ == "__main__":
    main()
