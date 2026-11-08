"""Rutas del proyecto, en un solo lugar. Todos los scripts toman de aquí sus valores por defecto.

Las rutas son absolutas (relativas a la raíz del repo), así que los scripts se pueden correr desde cualquier carpeta.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
ANOTACION = RAIZ / "annotation"
REPORTES = RAIZ / "reports"

# --- Diccionarios ------------------------------------------------------------
# "equipo": automático, lo genera diccionario.py desde Wikcionario (es) y Wiktionary (en). No se sube a git.
# "flo":    revisado a mano (libro 1 de 5). Se armó desde data/diccionario/ (Wikcionario, kaikki.org y Román).
DICCIONARIOS = {
    "equipo": DATA / "processed" / "diccionario.csv",
    "flo": DATA / "curado" / "diccionario_flo_parte1.csv",
}
ESCENARIO = "flo"  # diccionario por defecto de todos los scripts

# --- Flujo de generación del dataset -----------------------------------------
# 1. diccionario.py
CACHE_WIKCIONARIO = DATA / "raw"                  # cache_es.jsonl, cache_en.jsonl (descargas de la API)
# 2. oraciones.py
CORPUS = DATA / "raw" / "corpus"                  # .parquet del Chilean Spanish Corpus (no se sube a git)
CANDIDATAS = DATA / "interim" / "candidatas.csv"
# 3. borrador.py
BORRADOR = ANOTACION / "borrador.csv"
# (revisión humana: se corrige el borrador y se guarda como)
PARES_REVISADOS = ANOTACION / "pares_revisados.csv"
# 4. dividir.py
SPLITS = DATA / "processed"                       # train.csv, val.csv, test.csv

# --- Evaluación (baselines) --------------------------------------------------
PARES_EVAL = ANOTACION / "lote1.csv"
RESULTADOS = REPORTES / "comparacion_baselines.csv"
PREDICCIONES = DATA / "processed" / "predicciones.csv"
PREDICCIONES_LLM = DATA / "processed" / "predicciones_llm.csv"
