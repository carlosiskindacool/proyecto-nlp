"""
ERR y F1 con intervalos de confianza (bootstrap) y con una versión tolerante a las alternativas válidas.

python src/extras/err_incertidumbre_tolerante.py

- **Estricto:** el ERR y el F1 de siempre (metricas_normalizador.py), con intervalo bootstrap al 95 % (2.000 remuestreos de las oraciones, semilla 0).
- **Tolerante:** «español neutro» admite varias respuestas válidas (achuntar -> acertar o atinar), pero la referencia trae una sola. Para cada oración
  se prueban variantes de la referencia en que el reemplazo de cada término del diccionario presente en la oración se cambia por cualquiera de sus
  alternativas (`reemplazo` con «|» en data/curado/diccionario_flo.csv); se queda la variante que más palabras hace coincidir con la salida del
  sistema. Es una cota **optimista**: las alternativas salen del mismo diccionario que usan las reglas, y solo se prueban sustituciones del término
  del diccionario, no otras paráfrasis válidas.

Para el ERR: ERR = 1 - (palabras incorrectas) / (palabras que debían cambiar), así que se puede sumar por oración. Escribe
resultados/extras/err_incertidumbre.csv (por conjunto y «todos», las oraciones únicas).
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from comun import CONJUNTOS, REPO, cargar_salidas  # noqa: E402
from dicc import RUTAS, cargar_entradas, construir_reglas, entradas_en  # noqa: E402
from metricas_normalizador import contar, normalizar  # noqa: E402

os.chdir(REPO)
CAMPOS = ["n_palabras", "a_normalizar", "correctas", "tp", "fp", "fn"]
_, INDICE, PATRON = construir_reglas(cargar_entradas(RUTAS["flo"], incluir_ambiguos=True))


def con_subsecuencia(tokens, sub):
    return [i for i in range(len(tokens) - len(sub) + 1) if tuple(tokens[i:i + len(sub)]) == tuple(sub)]


def mejor_referencia(original, referencia, salida):
    """Variante de la referencia que más coincide con la salida (probando las alternativas del diccionario)."""
    mejor_tokens = list(normalizar(referencia))
    mejor = contar([original], [" ".join(mejor_tokens)], [salida])["correctas"]
    for e in entradas_en(original, INDICE, PATRON):
        alts = [tuple(normalizar(a)) for a in e["alternativas"] if normalizar(a)]
        for a in alts:
            for pos in con_subsecuencia(mejor_tokens, a):
                for b in alts:
                    if b == a:
                        continue
                    cand = mejor_tokens[:pos] + list(b) + mejor_tokens[pos + len(a):]
                    c = contar([original], [" ".join(cand)], [salida])["correctas"]
                    if c > mejor:
                        mejor, mejor_tokens = c, cand
                break
    return " ".join(mejor_tokens)


def conteos(original, referencia, salida):
    c = contar([original], [referencia], [salida])
    return [c[k] for k in CAMPOS]


def err_f1(m):
    n, a, ok, tp, fp, fn = m.sum(axis=0)
    err = 100 * (1 - (n - ok) / a) if a else np.nan
    p, r = (tp / (tp + fp) if tp + fp else np.nan), (tp / (tp + fn) if tp + fn else np.nan)
    f1 = 100 * 2 * p * r / (p + r) if p == p and r == r and p + r else np.nan
    return err, f1


def main():
    df = cargar_salidas()
    sistemas = ["reglas_equipo", "reglas_curado", "mt5_s1", "mt5_s2", "mt5_s3", "mt5_moe", "byt5", "byt5_s2", "byt5_s3"] + [c for c in df.columns if c.startswith("llm_")]
    rng = np.random.default_rng(0)
    grupos = {nombre: df[df.conjunto == clave] for clave, nombre in CONJUNTOS}
    grupos["todos (594 oraciones únicas)"] = df.drop_duplicates("original")
    filas = []
    for nombre, g in grupos.items():
        idx = rng.integers(0, len(g), size=(2000, len(g)))
        for s in sistemas:
            for variante in ("estricto", "tolerante"):
                m = np.array([conteos(o, mejor_referencia(o, r, x) if variante == "tolerante" else r, x)
                              for o, r, x in zip(g.original, g.referencia, g[s])], dtype=float)
                err, f1 = err_f1(m)
                boots = [err_f1(m[i]) for i in idx]
                e_b, f_b = np.array([b[0] for b in boots]), np.array([b[1] for b in boots])
                filas.append({"conjunto": nombre, "sistema": s, "variante": variante, "oraciones": len(g), "err": round(err, 1),
                              "err_ic95_inferior": round(float(np.nanpercentile(e_b, 2.5)), 1), "err_ic95_superior": round(float(np.nanpercentile(e_b, 97.5)), 1),
                              "f1": round(f1, 1), "f1_ic95_inferior": round(float(np.nanpercentile(f_b, 2.5)), 1), "f1_ic95_superior": round(float(np.nanpercentile(f_b, 97.5)), 1)})
        print("listo", nombre, flush=True)
    r = pd.DataFrame(filas)
    r.to_csv("resultados/extras/err_incertidumbre.csv", index=False)
    pd.set_option("display.width", 220)
    print(r[r.conjunto.str.startswith("todos")].to_string(index=False))


if __name__ == "__main__":
    main()
