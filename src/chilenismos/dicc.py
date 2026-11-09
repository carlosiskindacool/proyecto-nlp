"""Carga de diccionarios de chilenismos para los baselines.

Escenarios (--escenario): las rutas están en rutas.DICCIONARIOS.
  equipo : data/processed/diccionario.csv (automático, de diccionario.py)
  flo    : data/curado/diccionario_flo_parte1.csv (revisado a mano, parte 1)
"""
import csv
import re

from rutas import DICCIONARIOS as RUTAS  # noqa: F401  (se reexporta para los scripts)


def _si(valor, defecto="0"):
    return str(valor if valor not in (None, "") else defecto).strip().lower() in ("1", "si", "sí", "true")


def cargar_entradas(path, incluir_ambiguos=False, solo_validados=False):
    """Filas del diccionario que pueden usarse como regla: keep=1, con `reemplazo`.

    `ambiguo`, `reemplazo_validado` y `variantes` solo existen en el diccionario de flo;
    si faltan, se asume no ambiguo, validado y sin variantes."""
    with open(path, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    entradas = []
    for r in filas:
        if not _si(r.get("keep"), "1") or not (r.get("reemplazo") or "").strip():
            continue
        if _si(r.get("ambiguo")) and not incluir_ambiguos:
            continue
        if solo_validados and not _si(r.get("reemplazo_validado"), "1"):
            continue
        formas = [r["termino"]] + [v for v in (r.get("variantes") or "").split(";") if v.strip()]
        # `reemplazo` puede traer alternativas por sentido: "arruinar | engañar". La regla usa la primera.
        alternativas = [x.strip() for x in r["reemplazo"].split("|") if x.strip()]
        entradas.append({**r, "formas": [x.strip().lower() for x in formas],
                         "alternativas": alternativas, "reemplazo": alternativas[0]})
    return entradas


def construir_reglas(entradas):
    """(forma -> reemplazo, forma -> entrada, regex que reconoce cualquiera de las formas)."""
    reglas, indice = {}, {}
    for e in entradas:
        for forma in e["formas"]:
            reglas.setdefault(forma, e["reemplazo"].strip())
            indice.setdefault(forma, e)
    if not reglas:
        raise SystemExit("El diccionario no tiene términos con keep=1 y `reemplazo` (¿todos ambiguos?).")
    alternativas = "|".join(re.escape(t) for t in sorted(reglas, key=len, reverse=True))
    return reglas, indice, re.compile(rf"(?<!\w)({alternativas})(?!\w)", re.I)


def cargar_reglas(path, **opciones):
    reglas, indice, patron = construir_reglas(cargar_entradas(path, **opciones))
    return reglas, patron


def entradas_en(oracion, indice, patron):
    """Entradas del diccionario cuyos términos aparecen en la oración (sin repetir)."""
    vistas, out = set(), []
    for m in patron.finditer(oracion):
        e = indice[m.group(0).lower()]
        if e["termino"] not in vistas:
            vistas.add(e["termino"])
            out.append(e)
    return out
