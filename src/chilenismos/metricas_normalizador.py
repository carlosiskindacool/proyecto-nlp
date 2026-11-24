"""
Métricas del normalizador (chileno -> español neutro), por sistema y conjunto de pares.

python src/chilenismos/metricas_normalizador.py [--entrada "data/processed/predicciones_*.csv"]
    [--out resultados/metricas_normalizador.csv] [--md resultados/metricas_normalizador.md]

Texto comparado: Unicode NFKC, minúsculas y sin puntuación. Se conservan las tildes (tú/tu, más/mas)
y los prefijos # y @.

Alineación: la oración chilena se alinea por separado con la referencia y con la salida del sistema
(distancia de edición por palabra). Cada palabra de origen queda con su forma normalizada, que puede
ser vacía (n-1) o tener varias palabras (1-n), como en MultiLexNorm.

Métricas por palabra (micro, sobre todo el conjunto):
  TP = debía cambiar y quedó igual a la referencia
  FP = el sistema la cambió y no quedó igual a la referencia
  FN = debía cambiar y no quedó igual a la referencia
  precisión = TP / (TP + FP)    recall = TP / (TP + FN)    F1 = media armónica

  ERR = (accuracy - LAI) / (1 - LAI), con LAI = proporción de palabras que no cambian en la referencia
  (van der Goot, 2019; MultiLexNorm, W-NUT 2021). Dejar el texto igual da 0; un valor negativo indica
  que el sistema estropea más palabras de las que corrige.

Todo se informa de 0 a 100. BLEU y chrF se calculan sobre el texto normalizado; el CSV también guarda
`bleu_crudo` y `chrf_crudo`, sobre el texto original, comparables con archivo/resultados/tabla_por_conjunto.md.
"""
import argparse
import csv
import glob
import math
import os
import re
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache

import sacrebleu

COLUMNAS_NO_SISTEMA = {"conjunto", "chileno", "neutro", "referencia", "termino"}
TOKEN = re.compile(r"[#@]?\w+(?:[-']\w+)*")
CAMPOS = ["sistema", "conjunto", "n_pares", "n_palabras", "a_normalizar", "tp", "fp", "fn", "sobre_normalizadas",
          "accuracy", "lai", "err", "precision", "recall", "f1", "bleu", "chrf", "bleu_crudo", "chrf_crudo"]


@lru_cache(maxsize=None)
def normalizar(texto):
    """Palabras del texto en NFKC, minúsculas y sin puntuación."""
    texto = unicodedata.normalize("NFKC", texto).replace("’", "'").casefold()
    return tuple(TOKEN.findall(texto))


@lru_cache(maxsize=None)
def costo_sustitucion(a, b):
    """0 si son iguales; entre 1 y 2 si no, más barato cuanto más se parecen."""
    return 0.0 if a == b else 1 + 0.99 * (1 - SequenceMatcher(None, a, b, autojunk=False).ratio())


def operaciones(fuente, destino):
    """Alineación de mínimo costo: lista de (operación, índice en fuente, índice en destino)."""
    n, m = len(fuente), len(destino)
    costo = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        costo[i][0] = float(i)
    for j in range(m + 1):
        costo[0][j] = float(j)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            costo[i][j] = min(costo[i - 1][j - 1] + costo_sustitucion(fuente[i - 1], destino[j - 1]),
                              costo[i - 1][j] + 1, costo[i][j - 1] + 1)
    ops, i, j = [], n, m
    while i or j:
        if i and j and math.isclose(costo[i][j], costo[i - 1][j - 1] + costo_sustitucion(fuente[i - 1], destino[j - 1])):
            ops.append(("par", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i and math.isclose(costo[i][j], costo[i - 1][j] + 1):
            ops.append(("borra", i - 1, None))
            i -= 1
        else:
            ops.append(("inserta", None, j - 1))
            j -= 1
    return ops[::-1]


@lru_cache(maxsize=None)
def alinear(fuente, destino):
    """Forma normalizada de cada palabra de `fuente`. Las inserciones se suman a la palabra cambiada
    contigua o, si no hay, a la palabra anterior (a la primera si van al inicio)."""
    if not fuente:
        return ()
    salida = [[] for _ in fuente]
    pendientes, ultima_cambiada = [], None
    for op, i, j in operaciones(fuente, destino):
        if op == "inserta":
            if ultima_cambiada is None:
                pendientes.append(destino[j])
            else:
                salida[ultima_cambiada].append(destino[j])
        elif op == "par" and fuente[i] == destino[j]:
            if pendientes:
                salida[max(i - 1, 0)].extend(pendientes)
                pendientes = []
            salida[i].append(destino[j])
            ultima_cambiada = None
        else:
            salida[i] = pendientes + ([destino[j]] if op == "par" else [])
            pendientes, ultima_cambiada = [], i
    salida[-1].extend(pendientes)
    return tuple(" ".join(x) for x in salida)


def contar(fuente, referencia, hipotesis):
    """Conteos por palabra de un sistema sobre un conjunto de oraciones."""
    c = dict(n_palabras=0, a_normalizar=0, tp=0, fp=0, fn=0, sobre_normalizadas=0, correctas=0)
    for s, r, h in zip(fuente, referencia, hipotesis):
        palabras = normalizar(s)
        for palabra, oro, salida in zip(palabras, alinear(palabras, normalizar(r)), alinear(palabras, normalizar(h))):
            debe_cambiar, cambio, correcta = oro != palabra, salida != palabra, salida == oro
            c["n_palabras"] += 1
            c["a_normalizar"] += debe_cambiar
            c["correctas"] += correcta
            c["tp"] += debe_cambiar and correcta
            c["fp"] += cambio and not correcta
            c["fn"] += debe_cambiar and not correcta
            c["sobre_normalizadas"] += cambio and not debe_cambiar
    return c


def razon(a, b):
    return 100 * a / b if b else None


def calcular(fuente, referencia, hipotesis):
    c = contar(fuente, referencia, hipotesis)
    accuracy = razon(c["correctas"], c["n_palabras"])
    lai = razon(c["n_palabras"] - c["a_normalizar"], c["n_palabras"])
    err = 100 * (accuracy - lai) / (100 - lai) if c["a_normalizar"] else None
    precision = razon(c["tp"], c["tp"] + c["fp"])
    recall = razon(c["tp"], c["tp"] + c["fn"])
    f1 = None
    if precision is not None and recall is not None:
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    hip_norm = [" ".join(normalizar(x)) for x in hipotesis]
    ref_norm = [" ".join(normalizar(x)) for x in referencia]
    del c["correctas"]
    return {**c, "n_pares": len(fuente), "accuracy": accuracy, "lai": lai, "err": err,
            "precision": precision, "recall": recall, "f1": f1,
            "bleu": sacrebleu.corpus_bleu(hip_norm, [ref_norm]).score,
            "chrf": sacrebleu.corpus_chrf(hip_norm, [ref_norm]).score,
            "bleu_crudo": sacrebleu.corpus_bleu(hipotesis, [referencia]).score,
            "chrf_crudo": sacrebleu.corpus_chrf(hipotesis, [referencia]).score}


def nombre_conjunto(ruta, fila):
    if fila.get("conjunto"):
        return os.path.splitext(os.path.basename(fila["conjunto"]))[0]
    base = os.path.splitext(os.path.basename(ruta))[0]
    m = re.search(r"lote.*", base)
    return m.group(0) if m else base.removeprefix("predicciones_")


def cargar_predicciones(patron):
    """{(conjunto, sistema): (fuente, referencia, hipótesis)} desde los CSV de los distintos baselines."""
    datos = {}
    rutas = sorted(glob.glob(patron))
    if not rutas:
        raise SystemExit(f"No hay archivos que coincidan con {patron}")
    for ruta in rutas:
        with open(ruta, encoding="utf-8-sig", newline="") as f:
            lector = csv.DictReader(f)
            filas = list(lector)
            sistemas = [c for c in lector.fieldnames if c not in COLUMNAS_NO_SISTEMA]
        grupos = {}
        for r in filas:
            grupos.setdefault(nombre_conjunto(ruta, r), []).append(r)
        for conjunto, grupo in grupos.items():
            fuente = [r["chileno"] for r in grupo]
            referencia = [r.get("neutro") or r.get("referencia") or "" for r in grupo]
            for sistema in sistemas:
                if (conjunto, sistema) in datos:
                    print(f"Aviso: {sistema} en {conjunto} aparece en más de un archivo; se usa {ruta}")
                datos[(conjunto, sistema)] = (fuente, referencia, [r[sistema] or "" for r in grupo])
    return datos


def celda(valor):
    return "–" if valor is None else f"{valor:.1f}".replace(".", ",")


def escribir_csv(ruta, filas):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for r in filas:
            w.writerow({k: "" if r[k] is None else f"{r[k]:.2f}" if isinstance(r[k], float) else r[k] for k in CAMPOS})


def tabla_md(filas):
    lineas = []
    for conjunto in dict.fromkeys(r["conjunto"] for r in filas):
        grupo = [r for r in filas if r["conjunto"] == conjunto]
        p = grupo[0]
        lineas += [f"### {conjunto} ({p['n_pares']} pares, {p['n_palabras']} palabras, {p['a_normalizar']} por normalizar)", "",
                   "| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |", "|---|---:|---:|---:|---:|---:|---:|"]
        for r in grupo:
            valores = " | ".join(celda(r[k]) for k in ("err", "precision", "recall", "f1", "bleu", "chrf"))
            lineas.append(f"| {r['sistema']} | {valores} |")
        lineas.append("")
    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="data/processed/predicciones_*.csv")
    ap.add_argument("--out", default="resultados/metricas_normalizador.csv")
    ap.add_argument("--md", default="resultados/metricas_normalizador.md")
    args = ap.parse_args()

    filas = [{"sistema": sistema, "conjunto": conjunto, **calcular(*valores)}
             for (conjunto, sistema), valores in cargar_predicciones(args.entrada).items()]
    escribir_csv(args.out, filas)
    texto = tabla_md(filas)
    os.makedirs(os.path.dirname(args.md) or ".", exist_ok=True)
    with open(args.md, "w", encoding="utf-8") as f:
        f.write("Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. "
                "ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).\n\n" + texto)
    print(texto)
    print(f"Escrito {args.out} y {args.md}")


if __name__ == "__main__":
    main()
