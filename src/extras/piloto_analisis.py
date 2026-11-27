"""
Piloto: compara los diccionarios decididos por LLM con el humano.

python src/extras/piloto_analisis.py acuerdo      -> acuerdo etiqueta a etiqueta con el humano (dejar/quitar, ambiguo, reemplazo)
python src/extras/piloto_analisis.py variantes    -> arma los diccionarios variante (csv con el formato de diccionario_flo.csv)
python src/extras/piloto_analisis.py metricas     -> corre las reglas con cada variante y las métricas intrínsecas
python src/extras/piloto_analisis.py extrinseca   -> traduce y calcula Exact Match de cada variante

Variables de entorno: PILOTO_SUF=2 usa el piloto 2 (terminos_piloto2.csv); PILOTO_MODELOS=gemini,haiku,cohere limita los modelos;
PILOTO_SEL=1 incluye las variantes _seleccion en `extrinseca`.
"""
import csv
import glob
import json
import math
import os
import re
import subprocess
import sys
import unicodedata

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PILOTO = os.path.join(REPO, "resultados", "extras", "piloto")            # términos, decisiones y resultados que se versionan
TRABAJO = os.path.join(REPO, "data", "processed", "piloto")              # diccionarios variante y predicciones (se regeneran; no se versionan)
DICC = os.path.join(TRABAJO, "dicc")
SUF = os.environ.get("PILOTO_SUF", "")
MODELOS = os.environ.get("PILOTO_MODELOS", "gemini,haiku,cohere,ibm").split(",")
PARES = ["annotation/lote1.csv", "annotation/lote_1_noticias.csv", "annotation/lote_1_tuits.csv", "annotation/lote_1_2_noticias.csv", "annotation/lote_1_2_tuits.csv"]
os.makedirs(DICC, exist_ok=True)
os.chdir(REPO)
PY = sys.executable
norm = lambda x: unicodedata.normalize("NFKC", str(x)).casefold().strip()

term = pd.read_csv(os.path.join(PILOTO, f"terminos_piloto{SUF}.csv"), sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
humano = {r.termino: r for r in term.itertuples()}


def decisiones(m):
    p = os.path.join(PILOTO, f"decisiones_{m}{SUF}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def consenso():
    """Mayoría estricta de los modelos (más de la mitad dejan; un empate cuenta como quitar); reemplazos del primer modelo que dejó."""
    d = {m: decisiones(m) for m in MODELOS}
    res = {}
    for t in term.termino:
        votos = [d[m][t] for m in MODELOS if t in d[m]]
        if len(votos) < 2:
            continue
        dejan = [v for v in votos if v["decision"] == "dejar"]
        if len(dejan) * 2 > len(votos):
            amb = sum(1 for v in dejan if v["ambiguo"]) * 2 > len(dejan)
            rep = next((v["reemplazos"] for v in dejan if v["reemplazos"]), [])
            res[t] = {"decision": "dejar", "ambiguo": amb, "reemplazos": rep}
        else:
            res[t] = {"decision": "quitar", "ambiguo": False, "reemplazos": []}
    return res


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def acuerdo():
    filas = []
    for m in MODELOS + ["consenso"]:
        d = consenso() if m == "consenso" else decisiones(m)
        ts = [t for t in term.termino if t in d]
        if not ts:
            continue
        h = [humano[t].humano for t in ts]
        l = [d[t]["decision"] for t in ts]
        acc = sum(x == y for x, y in zip(h, l)) / len(ts)
        tp = sum(1 for x, y in zip(h, l) if x == "quitar" and y == "quitar")
        fn = sum(1 for x, y in zip(h, l) if x == "quitar" and y == "dejar")
        fp = sum(1 for x, y in zip(h, l) if x == "dejar" and y == "quitar")
        # sobre los que ambos dejan
        ambos = [t for t in ts if humano[t].humano == "dejar" and d[t]["decision"] == "dejar"]
        amb_igual = sum(1 for t in ambos if (humano[t].humano_ambiguo == "1") == bool(d[t]["ambiguo"]))
        con_rep = [t for t in ambos if humano[t].humano_reemplazo.strip() and d[t]["reemplazos"]]
        primero = sum(1 for t in con_rep if norm(d[t]["reemplazos"][0]) == norm(humano[t].humano_reemplazo.split("|")[0]))
        alguno = sum(1 for t in con_rep if {norm(x) for x in d[t]["reemplazos"]} & {norm(x) for x in humano[t].humano_reemplazo.split("|")})
        filas.append({"modelo": m, "términos": len(ts), "acuerdo dejar/quitar": f"{100 * acc:.0f} %", "kappa": f"{kappa(h, l):.2f}",
                      "quita lo que el humano quitó": f"{tp}/{tp + fn}", "quita lo que el humano dejó": f"{fp}/{fp + sum(1 for x in h if x == 'dejar') - fp}",
                      "ambiguo igual": f"{amb_igual}/{len(ambos)}", "1er reemplazo igual": f"{primero}/{len(con_rep)}", "algún reemplazo en común": f"{alguno}/{len(con_rep)}"})
    print(pd.DataFrame(filas).to_string(index=False))
    pd.DataFrame(filas).to_csv(os.path.join(PILOTO, f"acuerdo{SUF}.csv"), index=False, encoding="utf-8-sig")


def leer_humano():
    with open("data/curado/diccionario_flo.csv", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        return list(lector), lector.fieldnames


def construir(nombre, d, seleccion_solo=False):
    """Diccionario variante: para los términos del piloto manda el modelo; el resto queda como el humano.
    seleccion_solo=True: el modelo decide qué términos van, pero reemplazo y ambiguo vienen del humano cuando existen."""
    filas, campos = leer_humano()
    salida, vistos = [], set()
    for r in filas:
        t = r["termino"]
        if t in d and t in humano and humano[t].humano == "dejar":
            vistos.add(t)
            if d[t]["decision"] == "quitar":
                continue
            if not (seleccion_solo and r.get("reemplazo", "").strip()):
                r = dict(r)
                r["reemplazo"] = " | ".join(d[t]["reemplazos"])
                r["ambiguo"] = "1" if d[t]["ambiguo"] else "0"
                r["reemplazo_validado"] = "1"
        salida.append(r)
    nuevos = 0
    for t, v in d.items():
        if t in humano and humano[t].humano == "quitar" and v["decision"] == "dejar":
            salida.append({c: "" for c in campos} | {"termino": t, "grupo": t, "tipo": "otro", "reemplazo": " | ".join(v["reemplazos"]),
                                                   "ambiguo": "1" if v["ambiguo"] else "0", "reemplazo_validado": "1", "keep": "1"})
            nuevos += 1
    ruta = os.path.join(DICC, f"{nombre}.csv")
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(salida)
    return ruta, len(salida), nuevos


def variantes():
    construir("humano", {})
    for m in MODELOS + ["consenso"]:
        d = consenso() if m == "consenso" else decisiones(m)
        if not d:
            continue
        for sufijo, solo in (("", False), ("_seleccion", True)):
            ruta, n, nuevos = construir(m + sufijo, d, solo)
            print(f"{m + sufijo:22} {n} filas ({nuevos} términos agregados que el humano había quitado)")


def correr(cmd, log=None):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if r.returncode:
        print("ERROR", " ".join(cmd[:4]), r.stderr[-400:])
    return r


def metricas():
    resumen = []
    for ruta in sorted(glob.glob(os.path.join(DICC, "*.csv"))):
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        carpeta = os.path.join(TRABAJO, "pred", nombre)
        os.makedirs(carpeta, exist_ok=True)
        correr([PY, "src/chilenismos/baselines.py", "--escenario", "flo", "--diccionario", ruta, "--pares", *PARES, "--sin-mt5",
                "--out", os.path.join(carpeta, "predicciones.csv")])
        correr([PY, "src/chilenismos/metricas_normalizador.py", "--entrada", os.path.join(carpeta, "predicciones_*.csv"),
                "--out", os.path.join(carpeta, "metricas.csv"), "--md", os.path.join(carpeta, "metricas.md")])
        m = pd.read_csv(os.path.join(carpeta, "metricas.csv"))
        for _, r in m[m.sistema == "reglas_flo"].iterrows():
            resumen.append({"variante": nombre, "conjunto": r.conjunto, "err": r.err, "precision": r.precision, "recall": r.recall, "f1": r.f1})
    out = pd.DataFrame(resumen)
    out.to_csv(os.path.join(PILOTO, "metricas_variantes.csv"), index=False)
    print(out.pivot(index="variante", columns="conjunto", values="err").round(1).to_string())


def extrinseca():
    for ruta in sorted(glob.glob(os.path.join(DICC, "*.csv"))):
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if (nombre.endswith("_seleccion") and not os.environ.get("PILOTO_SEL")) or nombre == "humano":
            continue
        carpeta = os.path.join(TRABAJO, "pred", nombre)
        tr = os.path.join(carpeta, "eval.csv")
        if os.path.exists(os.path.join(carpeta, "eval_resumen.csv")):
            continue
        correr([PY, "src/eval_extrinseca.py", "--entrada", os.path.join(carpeta, "predicciones_*.csv"), "--out", tr])
        correr([PY, "src/eval_extrinseca_resumen.py", "--traducciones", tr, "--glosario", "data/diccionario/glosario_es_en_final.csv",
                "--out", os.path.join(carpeta, "eval_resumen.csv"), "--md", os.path.join(carpeta, "eval_resumen.md")])
        print("extrínseca lista:", nombre, flush=True)


if __name__ == "__main__":
    {"acuerdo": acuerdo, "variantes": variantes, "metricas": metricas, "extrinseca": extrinseca}[sys.argv[1]]()
