"""
Pasa un lote de borradores a un Excel de revisión y, ya revisado, del Excel al CSV que usan los sistemas.

python src/pares/revision_excel.py crear --borrador annotation/borrador_lote2.csv --seleccion data/interim/seleccion_lote2.csv \
    --salida revision_lote_2.xlsx
python src/pares/revision_excel.py a-csv --excel revision_lote_2.xlsx --salida annotation/lote_2.csv --revisor Flo

En la columna `decision`: ok (el borrador queda), corregir (se usa `neutro_corregido`) o descartar (el neutro queda
como DESCARTAR). `a-csv` escribe `termino;oracion;neutro;revisor1`, igual que los lotes 1; las filas sin decisión
quedan con `revisor1` vacío y los sistemas no las cuentan. Este Excel trae oraciones de tuits: no lo subas a git.
"""
import argparse
import csv
import os
import sys

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chilenismos"))
from dicc import RUTAS, cargar_entradas  # noqa: E402

COLS = ["termino", "oracion", "borrador_neutro (LLM)", "decision (ok / corregir / descartar)",
        "neutro_corregido (si corregir)", "definicion_del_diccionario", "reemplazo_del_diccionario", "notas",
        "fuente", "frecuencia"]


def crear(args):
    sel = {}
    with open(args.seleccion, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            sel[r["oracion"]] = r
    dic = {e["termino"].lower(): e for e in cargar_entradas(RUTAS["flo"], incluir_ambiguos=True, exigir_reemplazo=False)}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "revision"
    ws.append(COLS)
    with open(args.borrador, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            s = sel.get(r["oracion"], {})
            e = dic.get(r["termino"].lower(), {})
            ws.append([r["termino"], r["oracion"], r["neutro"], "", "", (e.get("definicion") or "")[:300],
                       e.get("reemplazo", ""), "", s.get("fuente", ""), s.get("nivel", "")])
    for k, ancho in enumerate([16, 70, 70, 16, 60, 40, 26, 30, 10, 12]):
        ws.column_dimensions[chr(65 + k)].width = ancho
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(wrap_text=True)
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical="top")
        fila[3].fill = PatternFill("solid", fgColor="DDEBF7")
        fila[4].fill = PatternFill("solid", fgColor="DDEBF7")
    dv = DataValidation(type="list", formula1='"ok,corregir,descartar"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"D2:D{ws.max_row}")
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(args.salida)
    print(f"{ws.max_row - 1} filas -> {args.salida}")


def a_csv(args):
    ws = openpyxl.load_workbook(args.excel, read_only=True)["revision"]
    filas = list(ws.iter_rows(min_row=2, values_only=True))
    out, pendientes = [], 0
    for r in filas:
        termino, oracion, borrador, decision, corregido = r[0], r[1], r[2], (r[3] or "").strip().lower(), r[4]
        if not termino:
            continue
        if decision == "ok":
            neutro, rev = borrador, args.revisor
        elif decision == "corregir":
            if not (corregido or "").strip():
                raise SystemExit(f"«{termino}»: decisión «corregir» sin neutro_corregido")
            neutro, rev = corregido.strip(), args.revisor
        elif decision == "descartar":
            neutro, rev = "DESCARTAR", args.revisor
        elif not decision:
            neutro, rev = borrador, ""
            pendientes += 1
        else:
            raise SystemExit(f"«{termino}»: decisión no válida «{decision}» (ok / corregir / descartar)")
        out.append({"termino": termino, "oracion": oracion, "neutro": neutro, "revisor1": rev})
    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["termino", "oracion", "neutro", "revisor1"], delimiter=";")
        w.writeheader()
        w.writerows(out)
    usados = sum(1 for r in out if r["revisor1"] and r["neutro"] != "DESCARTAR")
    print(f"{len(out)} filas -> {args.salida} ({usados} usables, {pendientes} sin decisión)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crear")
    c.add_argument("--borrador", required=True)
    c.add_argument("--seleccion", required=True)
    c.add_argument("--salida", required=True)
    c.set_defaults(f=crear)
    a = sub.add_parser("a-csv")
    a.add_argument("--excel", required=True)
    a.add_argument("--salida", required=True)
    a.add_argument("--revisor", required=True)
    a.set_defaults(f=a_csv)
    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
