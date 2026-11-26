"""
Excel de revisión del glosario es -> en, a partir de la regla de votos (src/glosario_votos.py).

python src/glosario_excel.py [--umbral 5] [--muestra 20] [--semilla 0] [--salida revision_glosario_es_en.xlsx]

Hojas:
  revisar  : términos sin acuerdo suficiente (menos de --umbral familias coinciden) y términos aceptados por votos cuya
             definición es propia (no viene del Wikcionario en español). Sin los términos que ya revisó Carlos.
  muestra  : una muestra al azar (semilla fija) de términos aceptados por votos, para comprobar que la regla funciona.
  leeme    : cómo rellenar.
El Excel NO se sube al repo si trae texto de tuits: este solo trae términos, definiciones y glosas.
También escribe data/interim/glosario_votos.csv (una fila por término).
"""
import argparse
import os
import random
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(__file__))
import glosario_votos as V  # noqa: E402
from glosario_modelos import separar_en  # noqa: E402

NOMBRES = {"claude": "Claude", "gemini": "Google", "cohere": "Cohere", "meta": "Meta (Llama)", "ibm": "IBM (Granite)",
           "nvidia": "Nvidia", "diccionario": "Diccionario", "mistral": "Mistral", "openai": "OpenAI", "alibaba": "Alibaba"}


def candidatas(fam, t):
    """[(glosa, n_familias)] de mayor a menor apoyo, con la lista de familias que la apoyan."""
    todas = {g for f in fam for g in fam[f].get(t, [])} - {V.norm(t)}
    res = []
    for g in todas:
        ap = sorted(f for f in fam if any(V.par(g, x) for x in fam[f].get(t, [])))
        res.append((g, ap))
    res.sort(key=lambda x: (-len(x[1]), x[0]))
    # una glosa contenida en otra mejor apoyada no se repite
    out = []
    for g, ap in res:
        if not any(V.par(g, h) for h, _ in out):
            out.append((g, ap))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=int, default=5)
    ap.add_argument("--muestra", type=int, default=20)
    ap.add_argument("--semilla", type=int, default=0)
    ap.add_argument("--salida", default="revision_glosario_es_en.xlsx")
    args = ap.parse_args()

    g = pd.read_csv(V.GLOSARIO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    T = [t for t in g["termino"] if "�" not in t]
    fam = V.cargar(T)
    fam.pop("mistral", None)   # incompleta (191 de 330): no vota hasta que esté completa
    c = pd.read_csv(V.REVISADO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    carlos = {r.termino for r in c.itertuples() if r.acepta_en.strip()}
    t = pd.read_csv(V.DICCIONARIO.replace("data/curado/diccionario_flo.csv", "data/diccionario/procesado/terminos.csv"),
                    encoding="utf-8-sig", keep_default_na=False, dtype=str).drop_duplicates("termino").set_index("termino")
    d = pd.read_csv(V.DICCIONARIO, encoding="utf-8-sig", keep_default_na=False, dtype=str).drop_duplicates("termino").set_index("termino")

    def definicion(x):
        propia = separar_en(d.loc[x, "definicion"])[0] if x in d.index else ""
        return propia or (t.loc[x, "definiciones_es"] if x in t.index else "")

    def def_propia(x):
        return "si" if (x not in t.index or not t.loc[x, "definiciones_es"].strip()) else ""

    filas, aceptados = [], {}
    for x in T:
        a = V.votar(fam, x, args.umbral)
        aceptados[x] = a
        filas.append({"termino": x, "estado": "aceptado" if a else "revisar", "glosas_aceptadas": " | ".join(y for y, _ in a),
                      "n_familias": max((len(z) for _, z in a), default=0), "revision_carlos": "si" if x in carlos else "",
                      "definicion_propia": def_propia(x)})
    pd.DataFrame(filas).to_csv("data/interim/glosario_votos.csv", index=False, sep=";", encoding="utf-8-sig")

    revisar = [x for x in T if x not in carlos and (not aceptados[x] or def_propia(x))]
    pool = [x for x in T if x not in carlos and aceptados[x] and not def_propia(x)]
    random.Random(args.semilla).shuffle(pool)
    muestra = sorted(pool[:args.muestra])

    wb = Workbook()
    azul, gris = PatternFill("solid", fgColor="E5CBF2"), PatternFill("solid", fgColor="F4EADF")
    fams = [f for f in NOMBRES if f in fam]

    def hoja(ws, terminos, con_propuesta):
        enc = ["termino", "definicion", "definicion_propia", "glosas_aceptadas_por_votos"] if con_propuesta else ["termino", "definicion", "definicion_propia", "glosas_aceptadas_por_votos"]
        enc += ["candidatas (familias que coinciden)"] + [NOMBRES[f] for f in fams] + ["decision", "glosas_finales", "notas"]
        ws.append(enc)
        for x in terminos:
            cand = candidatas(fam, x)
            ws.append([x, definicion(x)[:400], def_propia(x), " | ".join(y for y, _ in aceptados[x]),
                       "\n".join(f"{y} ({len(z)})" for y, z in cand[:8])] +
                      [" | ".join(dict.fromkeys(fam[f].get(x, [])[:6])) for f in fams] + ["", "", ""])
        for j, celda in enumerate(ws[1], 1):
            celda.fill, celda.font = azul, Font(bold=True)
            celda.alignment = Alignment(wrap_text=True, vertical="center")
        anchos = [18, 50, 10, 28, 30] + [26] * len(fams) + [16, 30, 30]
        for j, a in enumerate(anchos, 1):
            ws.column_dimensions[get_column_letter(j)].width = a
        for fila in ws.iter_rows(min_row=2):
            for celda in fila:
                celda.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "B2"
        col = 5 + len(fams) + 1
        dv = DataValidation(type="list", formula1='"ok,corregir,quitar,no se"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{get_column_letter(col)}2:{get_column_letter(col)}{len(terminos) + 1}")
        for fila in ws.iter_rows(min_row=2, min_col=col, max_col=col + 2):
            for celda in fila:
                celda.fill = gris

    ws = wb.active
    ws.title = "revisar"
    hoja(ws, revisar, True)
    hoja(wb.create_sheet("muestra"), muestra, True)
    lm = wb.create_sheet("leeme")
    for linea in [
        "Revisión del glosario es -> en (traducciones al inglés de los términos ancla).",
        "",
        f"Regla: una glosa se acepta si coinciden al menos {args.umbral} de {len(fam)} familias de modelos y diccionarios "
        f"({', '.join(NOMBRES[f] for f in fams)}). Sonnet y Haiku cuentan como una sola (Claude).",
        "Hoja 'revisar': términos sin acuerdo suficiente, y términos aceptados cuya definición no es del Wikcionario (definicion_propia = si).",
        "Hoja 'muestra': términos aceptados por votos elegidos al azar. Sirven para comprobar que la regla funciona.",
        "",
        "Cómo rellenar (columnas grises):",
        "  decision: ok = la glosa aceptada / la más votada sirve; corregir = escribo otra en glosas_finales; quitar = el término no se evalúa; no se.",
        "  glosas_finales: las traducciones que acepto, separadas por ' | ' (ej: right away | immediately). Si es 'ok' y está vacío, se usan las aceptadas por votos.",
        "  Lo que importa es el SENTIDO que tiene el término en los tuits, no solo que la glosa sea una traducción posible.",
        "",
        "Las glosas de las columnas de cada familia están normalizadas (minúsculas, sin 'to'). El número entre paréntesis es cuántas familias coinciden.",
        "Los 93 términos que ya revisó Carlos no están aquí.",
    ]:
        lm.append([linea])
    lm.column_dimensions["A"].width = 150
    wb.move_sheet("leeme", offset=-2)
    wb.save(args.salida)
    print(f"{args.salida}: {len(revisar)} términos en 'revisar' ({sum(1 for x in revisar if not aceptados[x])} sin acuerdo, "
          f"{sum(1 for x in revisar if aceptados[x])} con definición propia) y {len(muestra)} en 'muestra'")


if __name__ == "__main__":
    main()
