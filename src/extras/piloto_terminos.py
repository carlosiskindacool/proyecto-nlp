"""
Piloto: lista de términos que se le dan a cada LLM para que decida (dejar o quitar y con qué reemplazos).

python src/extras/piloto_terminos.py 1    -> terminos_piloto.csv  (términos que aparecen en las 594 oraciones de prueba)
python src/extras/piloto_terminos.py 2    -> terminos_piloto2.csv (los 500 términos revisados más frecuentes en las oraciones de entrenamiento
                                              que no estaban en el piloto 1)

Escribe en resultados/extras/piloto/. Para cada término guarda la decisión humana (dejar o quitar, con su reemplazo y si es ambiguo) y lo que
vieron las personas: la categoría y la definición cruda del Wikcionario (no la curada).
"""
import os
import re
import sys
import unicodedata

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO)
sys.path.insert(0, "src/chilenismos")
from dicc import cargar_entradas, construir_reglas, entradas_en  # noqa: E402

SALIDA = os.path.join(REPO, "resultados", "extras", "piloto")
os.makedirs(SALIDA, exist_ok=True)
L = lambda p, **k: pd.read_csv(p, encoding="utf-8-sig", keep_default_na=False, dtype=str, **k)
norm = lambda x: unicodedata.normalize("NFKC", x).casefold()


def piloto1():
    oraciones = set()
    for k in ("lote1", "lote_1_2_noticias", "lote_1_2_tuits"):
        t = L(f"annotation/{k}.csv", sep=";")
        t = t[(t.neutro.str.strip() != "") & (t.neutro.str.strip().str.upper() != "DESCARTAR")]
        oraciones |= set(t.oracion)
    entradas = cargar_entradas("data/curado/diccionario_flo.csv", incluir_ambiguos=True, exigir_reemplazo=False)
    _, indice, patron = construir_reglas(entradas)
    dejados = {}
    for o in oraciones:
        for e in entradas_en(o, indice, patron):
            dejados[e["termino"]] = e
    desc = L("data/curado/terminos_descartados.csv")
    desc = desc[desc.decision.str.strip().str.lower().str.startswith(("quitar", "no", "quitra"))]
    bloque = " \n ".join(norm(o) for o in oraciones)
    quitados = []
    for t in desc.termino.dropna().unique():
        tt = norm(t).strip()
        if len(tt) >= 3 and re.search(r"(?<!\w)" + re.escape(tt) + r"(?!\w)", bloque) and t not in dejados:
            quitados.append(t)
    filas = [{"termino": t, "humano": "dejar", "humano_reemplazo": e.get("reemplazo", ""), "humano_ambiguo": e.get("ambiguo", "0")} for t, e in sorted(dejados.items())]
    filas += [{"termino": t, "humano": "quitar", "humano_reemplazo": "", "humano_ambiguo": ""} for t in sorted(quitados)]
    return pd.DataFrame(filas), "terminos_piloto.csv"


def piloto2():
    ya = set(L(os.path.join(SALIDA, "terminos_piloto.csv"), sep=";").termino)
    oraciones = sorted(set(L("data/interim/borrador_entrenamiento.csv", sep=";").oracion))
    entradas = cargar_entradas("data/curado/diccionario_flo.csv", incluir_ambiguos=True, exigir_reemplazo=False)
    _, indice, patron = construir_reglas(entradas)
    frec, info = {}, {}
    for o in oraciones:
        for e in {e["termino"]: e for e in entradas_en(o, indice, patron)}.values():
            frec[e["termino"]] = frec.get(e["termino"], 0) + 1
            info[e["termino"]] = e
    dejados = {t: (info[t].get("reemplazo", ""), info[t].get("ambiguo", "0")) for t in frec}
    desc = L("data/curado/terminos_descartados.csv")
    desc = desc[desc.decision.str.strip().str.lower().str.startswith(("quitar", "no", "quitra"))]
    bloque = [norm(o) for o in oraciones]
    quitados = {}
    for t in desc.termino.dropna().unique():
        tt = norm(t).strip()
        if len(tt) < 3 or t in dejados:
            continue
        pat = re.compile(r"(?<!\w)" + re.escape(tt) + r"(?!\w)")
        n = sum(1 for b in bloque if pat.search(b))
        if n:
            quitados[t] = n
            frec[t] = n
    candidatos = sorted(((t, frec[t]) for t in frec if t not in ya), key=lambda x: (-x[1], x[0]))
    elegidos = candidatos[:500]
    filas = []
    for t, _ in elegidos:
        rep, amb = dejados.get(t, ("", ""))
        filas.append({"termino": t, "humano": "dejar" if t in dejados else "quitar", "humano_reemplazo": rep, "humano_ambiguo": amb})
    df = pd.DataFrame(filas)
    df["frecuencia"] = [n for _, n in elegidos]
    return df, "terminos_piloto2.csv"


df, nombre = {"1": piloto1, "2": piloto2}[sys.argv[1] if len(sys.argv) > 1 else "1"]()
crudo = L("data/diccionario/procesado/terminos.csv").drop_duplicates("termino").set_index("termino")
df["pos"] = df.termino.map(lambda t: crudo.loc[t, "pos"] if t in crudo.index else "")
df["definiciones"] = df.termino.map(lambda t: crudo.loc[t, "definiciones_es"] if t in crudo.index else "")
df["glosas_en"] = df.termino.map(lambda t: crudo.loc[t, "glosas_en"] if t in crudo.index else "")
df.to_csv(os.path.join(SALIDA, nombre), index=False, sep=";", encoding="utf-8-sig")
d = df[df.humano == "dejar"]
print(f"{nombre}: {len(df)} términos | dejar {len(d)} (con reemplazo {(d.humano_reemplazo.str.strip() != '').sum()}, ambiguos {(d.humano_ambiguo == '1').sum()}) | quitar {(df.humano == 'quitar').sum()}")
