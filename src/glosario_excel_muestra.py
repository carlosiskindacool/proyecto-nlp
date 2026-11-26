"""
Excel con una segunda muestra de términos aceptados por votos, para medir con más precisión qué tan buena es la regla.

python src/glosario_excel_muestra.py --previo RUTA/revision_glosario_es_en.xlsx --salida RUTA/revision_glosario_es_en_muestra2.xlsx
    [--n 40] [--semilla 1]

Se eligen al azar (semilla fija) entre los términos del glosario final que se aceptaron solo por votos (fuente = votos),
sin los que ya salieron en la primera muestra. Mismo formato de columnas que `glosario_excel.py`.
"""
import argparse
import csv
import os
import random
import sys

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(__file__))
import glosario_votos as V  # noqa: E402
from glosario_excel import NOMBRES, candidatas  # noqa: E402
from glosario_modelos import separar_en  # noqa: E402

FINAL = "data/diccionario/glosario_es_en_final.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previo", required=True, help="Excel de la primera revisión (hoja 'muestra')")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--semilla", type=int, default=1)
    ap.add_argument("--umbral", type=int, default=5)
    args = ap.parse_args()

    ya = {r[0] for r in load_workbook(args.previo, read_only=True)["muestra"].iter_rows(min_row=2, values_only=True) if r[0]}
    final = {r["termino"]: r for r in csv.DictReader(open(FINAL, encoding="utf-8-sig"), delimiter=";")}
    pool = sorted(t for t, r in final.items() if r["fuente"] == "votos" and t not in ya)
    random.Random(args.semilla).shuffle(pool)
    elegidos = sorted(pool[:args.n])

    g = pd.read_csv(V.GLOSARIO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    T = [t for t in g["termino"] if "�" not in t]
    fam = V.cargar(T)
    fam.pop("mistral", None)
    fams = [f for f in NOMBRES if f in fam]
    t = pd.read_csv("data/diccionario/procesado/terminos.csv", encoding="utf-8-sig", keep_default_na=False, dtype=str).drop_duplicates("termino").set_index("termino")
    d = pd.read_csv(V.DICCIONARIO, encoding="utf-8-sig", keep_default_na=False, dtype=str).drop_duplicates("termino").set_index("termino")

    def definicion(x):
        propia = separar_en(d.loc[x, "definicion"])[0] if x in d.index else ""
        return propia or (t.loc[x, "definiciones_es"] if x in t.index else "")

    wb = Workbook()
    ws = wb.active
    ws.title = "muestra2"
    enc = ["termino", "definicion", "glosas_aceptadas_por_votos", "candidatas (familias que coinciden)"] + [NOMBRES[f] for f in fams] + ["decision", "glosas_finales", "notas"]
    ws.append(enc)
    for x in elegidos:
        cand = candidatas(fam, x)
        ws.append([x, definicion(x)[:400], final[x]["acepta_en"], "\n".join(f"{y} ({len(z)})" for y, z in cand[:8])] +
                  [" | ".join(dict.fromkeys(fam[f].get(x, [])[:6])) for f in fams] + ["", "", ""])
    azul, gris = PatternFill("solid", fgColor="E5CBF2"), PatternFill("solid", fgColor="F4EADF")
    for c in ws[1]:
        c.fill, c.font, c.alignment = azul, Font(bold=True), Alignment(wrap_text=True, vertical="center")
    for j, a in enumerate([18, 50, 28, 30] + [26] * len(fams) + [16, 30, 30], 1):
        ws.column_dimensions[get_column_letter(j)].width = a
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"
    col = 4 + len(fams) + 1
    dv = DataValidation(type="list", formula1='"ok,corregir,quitar,no se"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{get_column_letter(col)}2:{get_column_letter(col)}{len(elegidos) + 1}")
    for fila in ws.iter_rows(min_row=2, min_col=col, max_col=col + 2):
        for c in fila:
            c.fill = gris
    lm = wb.create_sheet("leeme", 0)
    for linea in [
        "Segunda muestra para comprobar la regla de votos del glosario es -> en.",
        f"Son {len(elegidos)} términos que la regla aceptó (coinciden al menos {args.umbral} de {len(fam)} familias) y que no estaban en la primera muestra. Elegidos al azar (semilla {args.semilla}).",
        "",
        "Rellena las columnas grises:",
        "  decision: ok = las glosas aceptadas sirven para el sentido que tiene el término en los tuits; corregir = faltan glosas o hay alguna mala (escribe la lista final en glosas_finales); quitar = el término no se puede evaluar; no se.",
        "  glosas_finales: las traducciones que aceptas, separadas por ' | '. Si pones ok y la dejas vacía, se usan las aceptadas por votos.",
        "  Si solo faltan glosas (las aceptadas están bien), igual pon corregir y escribe la lista completa: así se distingue «correcta pero incompleta» de «ok».",
        "",
        "Las columnas de cada familia muestran lo que propuso cada una (normalizado, sin 'to'). El número entre paréntesis en 'candidatas' es cuántas familias coinciden.",
    ]:
        lm.append([linea])
    lm.column_dimensions["A"].width = 150
    wb.save(args.salida)
    print(f"{args.salida}: {len(elegidos)} términos (de {len(pool)} disponibles)")


if __name__ == "__main__":
    main()
