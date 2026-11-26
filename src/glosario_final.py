"""
Arma los glosarios es -> en que usa la evaluación extrínseca, con la regla de votos y la revisión de Flo.

python src/glosario_final.py --excel RUTA/revision_glosario_es_en.xlsx RUTA/revision_glosario_es_en_muestra2.xlsx --hechas RUTA/revisiones_glosario_hechas.csv

Escribe en data/diccionario/ (formato termino;reemplazo_es;acepta_en;fuente, como glosario_es_en_test.csv):
  glosario_es_en_final.csv        : lo que se usa. 93 términos revisados por Carlos + decisiones de Flo (hojas «revisar» y
                                    «muestra») + glosas aceptadas por votos (5 de 7 familias) en el resto.
  glosario_es_en_solo_diccionarios.csv : control. Carlos + lo que dicen solo los diccionarios (Wikcionario y glosas [EN]); sin LLM ni Flo.
  glosario_es_en_sin_claude.csv   : control. Igual que el final, pero los votos se calculan sin la familia Claude
                                    (6 familias, umbral 4), porque Sonnet escribió los pares con que se entrenan los mT5.
La fuente de cada fila (carlos / flo / votos / diccionarios) queda en la última columna.
"""
import argparse
import csv
import os
import sys

import pandas as pd
from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(__file__))
import glosario_votos as V  # noqa: E402

SALIDA = "data/diccionario/"


def partir(texto):
    return [g.strip() for g in str(texto or "").split("|") if g.strip()]


def escribir(nombre, filas, reemplazos):
    ruta = SALIDA + nombre
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["termino", "reemplazo_es", "acepta_en", "fuente"])
        for t in sorted(filas):
            glosas, fuente = filas[t]
            w.writerow([t, reemplazos.get(t, ""), " | ".join(dict.fromkeys(glosas)), fuente])
    return ruta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--excel", required=True, nargs="+", help="uno o más Excel de revisión (hojas revisar, muestra y muestra2)")
    ap.add_argument("--hechas", required=True, help="CSV con las respuestas de Flo que ya se habían quitado del Excel")
    ap.add_argument("--umbral", type=int, default=5)
    args = ap.parse_args()

    g = pd.read_csv(V.GLOSARIO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    T = [t for t in g["termino"] if "�" not in t]
    reemplazos = dict(zip(g["termino"], g["reemplazo_es"]))
    fam = V.cargar(T)
    fam.pop("mistral", None)   # incompleta
    carlos_df = pd.read_csv(V.REVISADO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    carlos = {r.termino: partir(r.acepta_en) for r in carlos_df.itertuples() if r.acepta_en.strip()}

    # decisiones de Flo
    flo, quitar, muestra_ok = {}, set(), []
    for r in csv.DictReader(open(args.hechas, encoding="utf-8-sig"), delimiter=";"):
        flo[r["termino"]] = partir(r["glosas_finales"])
    libros = [load_workbook(ruta, data_only=True) for ruta in args.excel]
    for wb, hoja in [(wb, h) for wb in libros for h in ("revisar", "muestra", "muestra2") if h in wb.sheetnames]:
        ws = wb[hoja]
        enc = [c.value for c in ws[1]]
        iG, iD = enc.index("glosas_finales"), (enc.index("decision") if "decision" in enc else None)
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not r[0]:
                continue
            t, glosas, dec = r[0], partir(r[iG]), (str(r[iD]).strip().casefold() if iD is not None and r[iD] else "")
            if dec == "quitar":
                quitar.add(t)
            elif glosas:
                flo[t] = glosas
            elif dec == "ok" or (hoja.startswith("muestra") and not dec):
                muestra_ok.append(t)   # ok: se queda con lo aceptado por votos
    for t in quitar:
        flo.pop(t, None)

    def votos(familias, umbral):
        return {t: [x for x, _ in V.votar(familias, t, umbral)] for t in T}

    final_v = votos(fam, args.umbral)
    fam_sin = {f: v for f, v in fam.items() if f != "claude"}
    sin_claude_v = votos(fam_sin, 4)
    dicc = {f: v for f, v in fam.items() if f == "diccionario"}

    def armar(votos_por_termino, con_flo, solo_dicc=False):
        filas = {}
        for t in T:
            if t in quitar:
                continue
            if t in carlos:
                filas[t] = (carlos[t], "carlos")
            elif con_flo and t in flo:
                filas[t] = (flo[t], "flo")
            elif solo_dicc:
                gl = [x for x in dicc["diccionario"].get(t, []) if x != V.norm(t)]
                if gl:
                    filas[t] = (gl, "diccionarios")
            elif votos_por_termino.get(t):
                filas[t] = (votos_por_termino[t], "votos")
        return filas

    final = armar(final_v, True)
    sin_claude = armar(sin_claude_v, True)
    solo = armar(None, False, solo_dicc=True)
    rutas = [escribir("glosario_es_en_final.csv", final, reemplazos),
             escribir("glosario_es_en_sin_claude.csv", sin_claude, reemplazos),
             escribir("glosario_es_en_solo_diccionarios.csv", solo, reemplazos)]
    for nombre, filas in (("final", final), ("sin_claude", sin_claude), ("solo_diccionarios", solo)):
        por = pd.Series([f for _, f in filas.values()]).value_counts().to_dict()
        print(f"{nombre}: {len(filas)} de {len(T)} términos con glosas {por}")
    sin = [t for t in T if t not in final and t not in quitar]
    print("términos sin glosa en el final:", sin)
    print("quitados por Flo:", sorted(quitar))
    print("muestra con 'ok' (se quedan con los votos):", len(muestra_ok))
    print("escritos:", ", ".join(rutas))


if __name__ == "__main__":
    main()
