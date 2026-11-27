"""Junta los resultados de los dos pilotos en resultados/extras/piloto/RESUMEN.md (usa lo que dejaron piloto_analisis.py acuerdo, metricas y extrinseca)."""
import glob
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PILOTO = os.path.join(REPO, "resultados", "extras", "piloto")
TRABAJO = os.path.join(REPO, "data", "processed", "piloto")
os.chdir(REPO)
out = ["# Resumen de los pilotos (LLM decide el diccionario)\n"]


def md(df):
    return df.to_markdown(index=False) if len(df) else "(sin datos)"


for suf, titulo in (("", "Piloto 1: 488 términos que aparecen en las oraciones de prueba"),
                    ("2", "Piloto 2: 500 términos revisados más frecuentes en las oraciones de entrenamiento (sin efecto medible en ERR)")):
    p = os.path.join(PILOTO, f"acuerdo{suf}.csv")
    out.append(f"## {titulo}\n\nAcuerdo con el humano (dejar/quitar, ambiguo, reemplazos):\n")
    out.append(md(pd.read_csv(p)) if os.path.exists(p) else "(no calculado)")
    out.append("")

m = pd.read_csv(os.path.join(PILOTO, "metricas_variantes.csv"))
out.append("## Piloto 1: ERR de reglas por conjunto (variantes del diccionario)\n")
out.append(md(m.pivot(index="variante", columns="conjunto", values="err").round(1).reset_index()))
out.append("\nF1 por palabra:\n")
out.append(md(m.pivot(index="variante", columns="conjunto", values="f1").round(1).reset_index()))

# Exact Match de las variantes: se consolida en un CSV versionado a partir de las carpetas de trabajo
ruta_ev = os.path.join(PILOTO, "eval_extrinseca_variantes.csv")
filas = []
for r in sorted(glob.glob(os.path.join(TRABAJO, "pred", "*", "eval_resumen.csv"))):
    v = os.path.basename(os.path.dirname(r))
    d = pd.read_csv(r)
    d = d[d.sistema == "reglas_flo"].assign(variante=v)
    filas.append(d[["variante", "conjunto", "traductor", "n_evaluables", "aciertos", "ema"]])
if filas:
    pd.concat(filas).to_csv(ruta_ev, index=False)
ev = pd.read_csv(ruta_ev)
ev = ev[ev.conjunto == "todos"]
ref = pd.read_csv(os.path.join(REPO, "resultados", "eval_extrinseca.csv"))
ref = ref[(ref.conjunto == "todos") & (ref.sistema == "reglas_flo")].assign(variante="humano (oficial)")
tabla = pd.concat([ev, ref[ev.columns]]).pivot(index="variante", columns="traductor", values="ema").reset_index()
out.append("\n## Piloto 1: Exact Match de traducción (594 oraciones, reglas con cada diccionario)\n")
out.append(md(tabla))
open(os.path.join(PILOTO, "RESUMEN.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("RESUMEN.md escrito")
