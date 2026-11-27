"""
Cuánta incertidumbre tiene el Exact Match de la evaluación extrínseca (594 oraciones).

python src/extras/incertidumbre.py

Para cada sistema y traductor: Exact Match con intervalo de confianza de Wilson al 95 %. Para pares de sistemas: diferencia de Exact Match
con intervalo bootstrap al 95 % (se remuestrean las oraciones, así que la comparación es pareada) y prueba de McNemar exacta (binomial)
sobre las oraciones en que uno acierta y el otro no.

Lee `data/processed/eval_extrinseca.csv` (sistemas oficiales, mT5 semilla 1) y los archivos de `resultados/extras/` (también los de `llm_dicc/`) con el Exact Match por
oración de las semillas 2 y 3 de mT5 y de ByT5. Escribe `resultados/extras/incertidumbre_exact_match.csv` y `..._pares.csv`.
"""
import glob
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import binomtest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO)
rng = np.random.default_rng(0)
leer = lambda p: pd.read_csv(p, encoding="utf-8-sig", keep_default_na=False, dtype=str)

oficial = leer("data/processed/eval_extrinseca.csv")
oficial = oficial[oficial.exact_match != ""].assign(sistema=lambda d: d.sistema.replace({"mt5": "mt5_s1", "reglas_flo": "reglas_curado"}))
extra = pd.concat([leer("resultados/extras/eval_extrinseca_mt5_semillas_oraciones.csv"), leer("resultados/extras/eval_extrinseca_oraciones_byt5.csv"),
                   leer("resultados/extras/eval_extrinseca_oraciones_byt5_s2.csv"), leer("resultados/extras/eval_extrinseca_oraciones_byt5_s3.csv")]
                  + [leer(f) for f in sorted(glob.glob("resultados/extras/llm_dicc/eval_extrinseca_llm_*.csv"))])
datos = pd.concat([oficial[["chileno", "sistema", "traductor", "exact_match"]], extra[["chileno", "sistema", "traductor", "exact_match"]]])
datos = datos.drop_duplicates(["chileno", "sistema", "traductor"])
datos["em"] = datos.exact_match.astype(int)
M = {t: datos[datos.traductor == t].pivot(index="chileno", columns="sistema", values="em") for t in ("mt", "nllb")}


def wilson(k, n, z=1.96):
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    mitad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return 100 * (centro - mitad), 100 * (centro + mitad)


LLM = sorted(c for c in M["mt"].columns if c.startswith("llm_"))
SIST = ["identidad", "reglas_equipo", "reglas_curado", "mt5_s1", "mt5_s2", "mt5_s3", "mt5_moe", "byt5", "byt5_s2", "byt5_s3"] + LLM
filas = []
for t, m in M.items():
    for s in SIST:
        x = m[s].dropna()
        lo, hi = wilson(int(x.sum()), len(x))
        filas.append({"traductor": t, "sistema": s, "n": len(x), "aciertos": int(x.sum()), "em": round(100 * x.mean(), 1), "ic95_inferior": round(lo, 1), "ic95_superior": round(hi, 1)})
pd.DataFrame(filas).to_csv("resultados/extras/incertidumbre_exact_match.csv", index=False)
print(pd.DataFrame(filas).to_string(index=False))

PARES = [("byt5", "reglas_curado"), ("byt5", "mt5_s1"), ("byt5", "mt5_s2"), ("byt5", "mt5_s3"),
         ("byt5_s2", "reglas_curado"), ("byt5_s3", "reglas_curado"), ("byt5_s2", "byt5"), ("byt5_s3", "byt5"), ("byt5_s3", "byt5_s2"),
         ("mt5_moe", "mt5_s1"), ("mt5_moe", "mt5_s2"), ("mt5_moe", "mt5_s3"),
         ("reglas_curado", "mt5_s1"), ("reglas_curado", "mt5_s2"), ("reglas_curado", "mt5_s3"), ("reglas_curado", "mt5_moe"),
         ("mt5_s2", "mt5_s1"), ("mt5_s3", "mt5_s1"), ("mt5_s3", "mt5_s2"), ("reglas_curado", "reglas_equipo"), ("reglas_equipo", "identidad")]
PARES += [(b, m) for b in ("byt5_s2", "byt5_s3") for m in ("mt5_s1", "mt5_s2", "mt5_s3")]
PARES += [(m, "reglas_curado") for m in LLM] + [(m, "byt5") for m in LLM]
if "llm_sonnet" in LLM and "llm_gemini" in LLM:
    PARES.append(("llm_sonnet", "llm_gemini"))
filas = []
for t, m in M.items():
    for a, b in PARES:
        d = m[[a, b]].dropna()
        x, y = d[a].values, d[b].values
        solo_a, solo_b = int(((x == 1) & (y == 0)).sum()), int(((x == 0) & (y == 1)).sum())
        p = binomtest(solo_a, solo_a + solo_b, 0.5).pvalue if solo_a + solo_b else 1.0
        idx = rng.integers(0, len(d), size=(10000, len(d)))
        dif = 100 * (x[idx].mean(axis=1) - y[idx].mean(axis=1))
        filas.append({"traductor": t, "a": a, "b": b, "n": len(d), "em_a": round(100 * x.mean(), 1), "em_b": round(100 * y.mean(), 1),
                      "diferencia": round(100 * (x.mean() - y.mean()), 1), "ic95_inferior": round(float(np.percentile(dif, 2.5)), 1),
                      "ic95_superior": round(float(np.percentile(dif, 97.5)), 1), "solo_a_acierta": solo_a, "solo_b_acierta": solo_b, "p_mcnemar": round(float(p), 4)})
r = pd.DataFrame(filas)
r.to_csv("resultados/extras/incertidumbre_exact_match_pares.csv", index=False)
print(r.to_string(index=False))
