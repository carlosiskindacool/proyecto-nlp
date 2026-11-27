"""
Sensibilidad al ruido de los tuits: copia de las predicciones sin risas ni hashtags (oración de entrada, referencia y salidas).

python src/extras/sensibilidad_ruido.py

Escribe las predicciones limpias en data/processed/sensibilidad/ (no se versiona) e imprime cuántas oraciones cambian. Después se repiten las métricas:
  python src/chilenismos/metricas_normalizador.py --entrada "data/processed/sensibilidad/predicciones_*.csv" --out <csv> --md <md>
  python src/eval_extrinseca.py --entrada "data/processed/sensibilidad/predicciones_*.csv" --out <traducciones.csv>
  python src/eval_extrinseca_resumen.py --traducciones <traducciones.csv> --out <csv> --md <md>
Los resultados están en resultados/extras/sensibilidad_texto_limpio.md.
"""
import glob
import os
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SALIDA = os.path.join(REPO, "data", "processed", "sensibilidad")
os.makedirs(SALIDA, exist_ok=True)

RISA = re.compile(r"^(?:[jh][aeiou]+){2,}[jh]?$|^(?:x+d+|lol|lmao)$", re.I)
PUNTUACION = ".,;:!?¡¿()\"'…*-_[]{}<>~|"


def quita_ruido(texto):
    fuera = []
    for tok in str(texto).split():
        nucleo = tok.strip(PUNTUACION)
        if nucleo.startswith("#") or (nucleo and RISA.match(nucleo)):
            continue
        fuera.append(tok)
    return " ".join(fuera).strip()


NO_TEXTO = {"conjunto", "termino"}
resumen = {}
USAR = {"predicciones_lote1.csv", "predicciones_lote_1_noticias.csv", "predicciones_lote_1_tuits.csv", "predicciones_lote_1_2_noticias.csv", "predicciones_lote_1_2_tuits.csv", "predicciones_mt5_flo_fp32.csv", "predicciones_mt5_moe_fp32.csv"}
for ruta in sorted(glob.glob(os.path.join(REPO, "data", "processed", "predicciones_*.csv"))):
    nombre = os.path.basename(ruta)
    if nombre not in USAR:
        continue
    df = pd.read_csv(ruta, encoding="utf-8-sig", keep_default_na=False, dtype=str)
    original = df["chileno"].copy()
    cols = [c for c in df.columns if c not in NO_TEXTO]
    for c in cols:
        df[c] = df[c].map(quita_ruido)
    cambia = (original != df["chileno"])
    ref = "neutro" if "neutro" in df.columns else "referencia"
    vacias = (df["chileno"] == "") | (df[ref] == "")
    resumen[nombre] = (len(df), int(cambia.sum()), int(vacias.sum()), original[cambia].nunique())
    df = df[~vacias]
    df.to_csv(os.path.join(SALIDA, nombre), index=False, encoding="utf-8-sig")

print(f"{'archivo':42}{'filas':>7}{'oraciones que cambian':>24}{'quedan vacías':>16}")
for k, (n, c, v, u) in resumen.items():
    print(f"{k:42}{n:>7}{c:>16} ({100 * c / n:4.1f} %){v:>14}")

# cuántas de las oraciones únicas del conjunto de evaluación cambian (las del lote base y las ampliadas)
unicas, cambian = set(), set()
for k in ("predicciones_lote1.csv", "predicciones_lote_1_2_noticias.csv", "predicciones_lote_1_2_tuits.csv"):
    d0 = pd.read_csv(os.path.join(REPO, "data", "processed", k), encoding="utf-8-sig", keep_default_na=False, dtype=str)
    for t in d0["chileno"]:
        unicas.add(t)
        if quita_ruido(t) != t:
            cambian.add(t)
print(f"\noraciones únicas de evaluación: {len(unicas)} | con risas o hashtags: {len(cambian)} ({100 * len(cambian) / len(unicas):.1f} %)")
risa_n = sum(1 for t in unicas if any(RISA.match(w.strip(PUNTUACION)) for w in t.split() if w.strip(PUNTUACION)))
hash_n = sum(1 for t in unicas if any(w.strip(PUNTUACION).startswith("#") for w in t.split()))
print(f"   con risas: {risa_n} | con hashtags: {hash_n}")
ejemplos = sorted(cambian, key=len)[:6]
for e in ejemplos:
    print(f"   «{e[:70]}» -> «{quita_ruido(e)[:70]}»")
