"""
Análisis de errores de los modelos propios: cuánto cambian de más y ejemplos concretos.

python src/extras/errores_modelos.py [--ejemplos]

Por conjunto de pares: de las oraciones que **no** debían cambiar (la referencia es igual a la original), qué porcentaje cambia cada
sistema; y de las que sí debían cambiar, qué porcentaje queda igual a la referencia, cambia sin acertar o no cambia. Con --ejemplos
imprime candidatos para la tabla de ejemplos del informe (4.5). Lee `data/processed/predicciones_*.csv`; escribe
`resultados/extras/errores_modelos.csv`.
"""
import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO)
leer = lambda p: pd.read_csv(p, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def norm(s):
    s = unicodedata.normalize("NFKC", str(s)).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w@#\s]", " ", s)).strip()


CONJ = [("lote1", "lote base"), ("lote_1_tuits", "primera fase tuits"), ("lote_1_noticias", "primera fase noticias"),
        ("lote_1_2_tuits", "lote ampliado tuits"), ("lote_1_2_noticias", "lote ampliado noticias")]
MT5 = {"mt5_flo_fp32": "predicciones_mt5_flo_fp32.csv", "mt5_flo_fp32_s2": "predicciones_mt5_flo_fp32_s2.csv", "mt5_flo_fp32_s3": "predicciones_mt5_flo_fp32_s3.csv"}
moe, byt5 = leer("data/processed/predicciones_mt5_moe_fp32.csv"), leer("data/processed/predicciones_byt5_flo_fp32.csv")
byt5_s2, byt5_s3 = leer("data/processed/predicciones_byt5_flo_fp32_s2.csv"), leer("data/processed/predicciones_byt5_flo_fp32_s3.csv")
mt5 = {c: leer("data/processed/" + f) for c, f in MT5.items()}


def salidas(clave):
    """DataFrame por oración con la original, la referencia y la salida de cada sistema."""
    base = leer(f"data/processed/predicciones_{clave}.csv").drop_duplicates("chileno").set_index("chileno")
    a = {c: d[d.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno") for c, d in mt5.items()}
    b = moe[moe.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
    c_ = byt5[byt5.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
    c2 = byt5_s2[byt5_s2.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
    c3 = byt5_s3[byt5_s3.conjunto == clave + ".csv"].drop_duplicates("chileno").set_index("chileno")
    idx = [i for i in a["mt5_flo_fp32"].index if i in base.index and i in b.index and i in c_.index and i in c2.index and i in c3.index and all(i in a[k].index for k in a)]
    df = pd.DataFrame({"original": idx, "referencia": a["mt5_flo_fp32"].loc[idx, "referencia"].values, "termino": a["mt5_flo_fp32"].loc[idx, "termino"].values,
                       "reglas_curado": base.loc[idx, "reglas_flo"].values, "mt5_s1": a["mt5_flo_fp32"].loc[idx, "mt5_flo_fp32"].values,
                       "mt5_s2": a["mt5_flo_fp32_s2"].loc[idx, "mt5_flo_fp32_s2"].values, "mt5_s3": a["mt5_flo_fp32_s3"].loc[idx, "mt5_flo_fp32_s3"].values,
                       "mt5_moe": b.loc[idx, "mt5_moe_fp32"].values, "byt5": c_.loc[idx, "byt5_flo_fp32"].values,
                       "byt5_s2": c2.loc[idx, "byt5_flo_fp32_s2"].values, "byt5_s3": c3.loc[idx, "byt5_flo_fp32_s3"].values})
    return df


SIST = ["reglas_curado", "mt5_s1", "mt5_s2", "mt5_s3", "mt5_moe", "byt5", "byt5_s2", "byt5_s3"]
filas = []
todos = {}
for clave, nombre in CONJ:
    df = salidas(clave)
    todos[nombre] = df
    quieto = df.apply(lambda r: norm(r.original) == norm(r.referencia), axis=1)
    for s in SIST:
        cambia = df.apply(lambda r: norm(r[s]) != norm(r.original), axis=1)
        igual_ref = df.apply(lambda r: norm(r[s]) == norm(r.referencia), axis=1)
        filas.append({"conjunto": nombre, "sistema": s, "oraciones": len(df), "no_debian_cambiar": int(quieto.sum()),
                      "cambia_las_que_no_debian_pct": round(100 * cambia[quieto].mean(), 1) if quieto.any() else None,
                      "debian_cambiar": int((~quieto).sum()),
                      "acierta_pct": round(100 * igual_ref[~quieto].mean(), 1), "cambia_sin_acertar_pct": round(100 * (cambia & ~igual_ref)[~quieto].mean(), 1),
                      "no_cambia_pct": round(100 * (~cambia)[~quieto].mean(), 1)})
r = pd.DataFrame(filas)
r.to_csv("resultados/extras/errores_modelos.csv", index=False)
pd.set_option("display.width", 250)
print(r.to_string(index=False))

if "--ejemplos" in sys.argv:
    PROHIBIDAS = re.compile(r"\b(mierda|weon|weón|conch|puta|culia|culiao|ctm|chucha|maric|pico|pene|sexo|violad|nazi)", re.I)
    out = []
    for nombre, df in todos.items():
        df = df[~df.original.str.contains(PROHIBIDAS) & (df.original.str.len() < 140)]
        for _, x in df.iterrows():
            ok = lambda s: norm(x[s]) == norm(x.referencia)
            tipo = None
            if norm(x.original) == norm(x.referencia) and norm(x.mt5_s1) != norm(x.original) and norm(x.byt5) == norm(x.original):
                tipo = "mT5 cambia lo que no debía, ByT5 no"
            elif ok("byt5") and not ok("mt5_s1") and not ok("mt5_s2") and not ok("mt5_s3"):
                tipo = "ByT5 acierta, mT5 (3 semillas) no"
            elif ok("mt5_s1") and ok("mt5_s2") and ok("mt5_s3") and not ok("byt5"):
                tipo = "mT5 (3 semillas) acierta, ByT5 no"
            elif ok("reglas_curado") and not ok("byt5") and not ok("mt5_s1"):
                tipo = "solo reglas_curado acierta"
            elif not ok("byt5") and not ok("mt5_s1") and not ok("reglas_curado") and norm(x.byt5) != norm(x.original):
                tipo = "todos fallan"
            if tipo:
                out.append((tipo, nombre, x))
    rs = np.random.default_rng(1)
    for tipo in dict.fromkeys(t for t, _, _ in out):
        cand = [(n, x) for t, n, x in out if t == tipo]
        print(f"\n#### {tipo} ({len(cand)} oraciones)")
        for k in rs.permutation(len(cand))[:6]:
            n, x = cand[k]
            print(f"[{n}] término: {x.termino}\n  original  : {x.original}\n  referencia: {x.referencia}\n  reglas    : {x.reglas_curado}\n  mT5 s1    : {x.mt5_s1}\n  mT5 s2    : {x.mt5_s2}\n  ByT5      : {x.byt5}")
