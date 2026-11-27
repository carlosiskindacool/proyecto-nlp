"""Funciones compartidas por los scripts de src/extras: carga de las salidas de cada sistema y del Exact Match por oración."""
import glob
import os
import sys

import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "src", "chilenismos"))
EXTRAS = os.path.join(REPO, "resultados", "extras")
LLM = os.path.join(EXTRAS, "llm_dicc")
CONJUNTOS = [("lote1", "lote base"), ("lote_1_tuits", "primera fase tuits"), ("lote_1_noticias", "primera fase noticias"),
             ("lote_1_2_tuits", "lote ampliado tuits"), ("lote_1_2_noticias", "lote ampliado noticias")]
leer = lambda p: pd.read_csv(p, encoding="utf-8-sig", keep_default_na=False, dtype=str)

# columna del CSV de predicciones -> nombre usado en los resultados de resultados/extras
SISTEMAS_PRED = {"mt5_flo_fp32": ("predicciones_mt5_flo_fp32.csv", "mt5_s1"), "mt5_flo_fp32_s2": ("predicciones_mt5_flo_fp32_s2.csv", "mt5_s2"),
                 "mt5_flo_fp32_s3": ("predicciones_mt5_flo_fp32_s3.csv", "mt5_s3"), "mt5_moe_fp32": ("predicciones_mt5_moe_fp32.csv", "mt5_moe"),
                 "byt5_flo_fp32": ("predicciones_byt5_flo_fp32.csv", "byt5"),
                 "byt5_flo_fp32_s2": ("predicciones_byt5_flo_fp32_s2.csv", "byt5_s2"), "byt5_flo_fp32_s3": ("predicciones_byt5_flo_fp32_s3.csv", "byt5_s3")}


def cargar_salidas(con_llm=True):
    """Una fila por (conjunto, oración): conjunto, termino, original, referencia y la salida de cada sistema.

    Sistemas: identidad, reglas_equipo, reglas_curado, mt5_s1, mt5_s2, mt5_s3, mt5_moe, byt5 (semilla 1), byt5_s2, byt5_s3 y, si existen sus archivos en
    resultados/extras/llm_dicc/, llm_gemini y llm_sonnet."""
    filas = []
    for clave, _ in CONJUNTOS:
        base = leer(os.path.join(REPO, "data", "processed", f"predicciones_{clave}.csv")).drop_duplicates("chileno").set_index("chileno")
        partes = {}
        for col, (archivo, nombre) in SISTEMAS_PRED.items():
            d = leer(os.path.join(REPO, "data", "processed", archivo))
            partes[nombre] = d[d.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
        if con_llm:
            for ruta in sorted(glob.glob(os.path.join(LLM, "predicciones_llm_*.csv"))):
                nombre = os.path.basename(ruta)[len("predicciones_"):-4]
                d = leer(ruta)
                partes[nombre] = d[d.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
        ref = partes["mt5_s1"]
        idx = [i for i in ref.index if i in base.index and all(i in p.index for p in partes.values())]
        df = pd.DataFrame({"conjunto": clave, "original": idx, "termino": ref.loc[idx, "termino"].values, "referencia": ref.loc[idx, "referencia"].values,
                           "identidad": base.loc[idx, "identidad"].values, "reglas_equipo": base.loc[idx, "reglas_equipo"].values,
                           "reglas_curado": base.loc[idx, "reglas_flo"].values})
        for nombre, p in partes.items():
            col = [c for c in p.columns if c not in ("conjunto", "chileno", "referencia", "termino")][0]
            df[nombre] = p.loc[idx, col].values
        filas.append(df)
    return pd.concat(filas, ignore_index=True)


def em_por_oracion():
    """{(sistema, traductor): Series 0/1 indexada por oración} con el glosario final.

    Fuentes: el eval_extrinseca.csv oficial (mT5 semilla 1, MoE, reglas e identidad) y los archivos por oración de resultados/extras/."""
    nombres = {"mt5": "mt5_s1", "reglas_flo": "reglas_curado"}
    partes = [leer(os.path.join(REPO, "data", "processed", "eval_extrinseca.csv")).assign(sistema=lambda d: d.sistema.replace(nombres))]
    for f in ("eval_extrinseca_mt5_semillas_oraciones.csv", "eval_extrinseca_oraciones_byt5.csv", "eval_extrinseca_oraciones_byt5_s2.csv", "eval_extrinseca_oraciones_byt5_s3.csv"):
        partes.append(leer(os.path.join(EXTRAS, f)))
    for f in sorted(glob.glob(os.path.join(LLM, "eval_extrinseca_llm_*.csv"))):
        partes.append(leer(f))
    d = pd.concat([p[["chileno", "sistema", "traductor", "exact_match"]] for p in partes])
    d = d[d.exact_match != ""].drop_duplicates(["chileno", "sistema", "traductor"])
    d["em"] = d.exact_match.astype(int)
    return {(s, t): g.set_index("chileno").em for (s, t), g in d.groupby(["sistema", "traductor"])}
