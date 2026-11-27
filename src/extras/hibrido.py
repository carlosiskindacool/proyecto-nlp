"""
Híbrido reglas + modelo: ¿se complementan?

python src/extras/hibrido.py

Regla de combinación, fijada **antes** de ver los resultados y sin entrenar nada: si `reglas_curado` cambió la oración (es decir, el diccionario encontró
un término no ambiguo), se usa la salida de las reglas; si no cambió nada, se usa la salida del modelo (ByT5 o mT5). Así las reglas, que casi no se
equivocan donde actúan, deciden primero, y el modelo cubre lo que el diccionario no sabe. Solo recombina predicciones que ya existen.

Se informa ERR y F1 por conjunto (y en las 594 oraciones únicas) y el Exact Match: como el texto del híbrido es siempre el de uno de los dos sistemas,
su traducción y su Exact Match son los de ese sistema en esa oración. Escribe resultados/extras/hibrido.csv.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(__file__))
from comun import CONJUNTOS, REPO, cargar_salidas, em_por_oracion  # noqa: E402
from metricas_normalizador import calcular, normalizar  # noqa: E402

os.chdir(REPO)
MODELOS = ["byt5", "byt5_s2", "byt5_s3", "mt5_s1", "mt5_s2", "mt5_s3", "mt5_moe"]


def main():
    df = cargar_salidas()
    em = em_por_oracion()
    reglas_actuan = df.apply(lambda r: normalizar(r.reglas_curado) != normalizar(r.original), axis=1)
    print(f"oraciones en que las reglas cambian algo: {int(reglas_actuan.sum())} de {len(df)}")
    filas = []
    unicas = df.drop_duplicates("original")
    elegido = {}
    for m in MODELOS:
        nombre = f"hibrido_reglas_{m}"
        df[nombre] = np.where(reglas_actuan, df.reglas_curado, df[m])
        elegido[nombre] = {o: ("reglas_curado" if a else m) for o, a in zip(df.original, reglas_actuan)}
    sistemas = ["reglas_curado"] + MODELOS + [f"hibrido_reglas_{m}" for m in MODELOS]
    grupos = {nombre: df[df.conjunto == clave] for clave, nombre in CONJUNTOS}
    grupos["todos (594 oraciones únicas)"] = df.drop_duplicates("original")
    for nombre, g in grupos.items():
        for s in sistemas:
            c = calcular(list(g.original), list(g.referencia), list(g[s]))
            fila = {"conjunto": nombre, "sistema": s, "err": round(c["err"], 1), "f1": round(c["f1"], 1), "precision": round(c["precision"], 1), "recall": round(c["recall"], 1)}
            for trad in ("mt", "nllb"):
                vals = []
                for o in g.original:
                    sis = elegido[s][o] if s in elegido else s
                    serie = em.get((sis, trad))
                    vals.append(serie.get(o, np.nan) if serie is not None else np.nan)
                fila[f"em_{trad}"] = round(100 * np.nanmean(vals), 1) if not np.all(np.isnan(vals)) else None
            filas.append(fila)
    r = pd.DataFrame(filas)
    r.to_csv("resultados/extras/hibrido.csv", index=False)
    pd.set_option("display.width", 200)
    print(r[r.conjunto.str.startswith("todos")].to_string(index=False))

    # comparación pareada con McNemar sobre las oraciones únicas
    pares = []
    for trad in ("mt", "nllb"):
        for m in MODELOS:
            a, b_ = f"hibrido_reglas_{m}", None
            for otro in ("reglas_curado", m):
                x = np.array([em[(elegido[a][o], trad)].get(o, np.nan) for o in unicas.original])
                y = np.array([em[(otro, trad)].get(o, np.nan) for o in unicas.original])
                solo_a, solo_b = int(((x == 1) & (y == 0)).sum()), int(((x == 0) & (y == 1)).sum())
                p = binomtest(solo_a, solo_a + solo_b, 0.5).pvalue if solo_a + solo_b else 1.0
                pares.append({"traductor": trad, "a": a, "b": otro, "em_a": round(100 * np.nanmean(x), 1), "em_b": round(100 * np.nanmean(y), 1),
                              "solo_a_acierta": solo_a, "solo_b_acierta": solo_b, "p_mcnemar": round(float(p), 4)})
    p = pd.DataFrame(pares)
    p.to_csv("resultados/extras/hibrido_pares.csv", index=False)
    print(p.to_string(index=False))


if __name__ == "__main__":
    main()
