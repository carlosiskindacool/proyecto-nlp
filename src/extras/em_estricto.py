"""
Exact Match estricto: reconcilia el ERR (que ve la sobrecorrección) con el Exact Match (que mira solo el término ancla).

python src/extras/em_estricto.py

Una oración cuenta como acierto **estricto** si (a) el término ancla se traduce bien al inglés (Exact Match) **y** (b) la salida no cambió ninguna
palabra de la oración que la referencia dejó igual. Una palabra «cambia» si la alineación por palabras (difflib, texto normalizado como en
metricas_normalizador.py) la modifica; las inserciones se asignan a la palabra anterior. Se informa, por sistema y traductor, el Exact Match, el
porcentaje de oraciones con sobrecorrección y el Exact Match estricto. Escribe resultados/extras/em_estricto.csv.
"""
import os
import sys
from difflib import SequenceMatcher

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from comun import REPO, em_por_oracion, cargar_salidas  # noqa: E402
from metricas_normalizador import normalizar  # noqa: E402

os.chdir(REPO)


def indices_cambiados(a, b):
    """Posiciones de las palabras de `a` que cambian al pasar a `b`."""
    idx = set()
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        idx.update(range(i1, i2)) if i2 > i1 else idx.add(max(i1 - 1, 0))
    return idx


def sobrecorrige(original, referencia, salida):
    o = normalizar(original)
    return bool(indices_cambiados(o, normalizar(salida)) - indices_cambiados(o, normalizar(referencia)))


def main():
    df = cargar_salidas()
    em = em_por_oracion()
    sistemas = ["identidad", "reglas_equipo", "reglas_curado", "mt5_s1", "mt5_s2", "mt5_s3", "mt5_moe", "byt5", "byt5_s2", "byt5_s3"] + [c for c in df.columns if c.startswith("llm_")]
    unicas = df.drop_duplicates("original")
    filas = []
    for s in sistemas:
        sobre = {o: sobrecorrige(o, r, x) for o, r, x in zip(unicas.original, unicas.referencia, unicas[s])}
        for trad in ("mt", "nllb"):
            if (s, trad) not in em:
                continue
            serie = em[(s, trad)]
            oraciones = [o for o in unicas.original if o in serie.index]
            e = pd.Series({o: serie[o] for o in oraciones})
            sb = pd.Series({o: sobre[o] for o in oraciones})
            filas.append({"sistema": s, "traductor": trad, "oraciones": len(oraciones), "exact_match": round(100 * e.mean(), 1),
                          "con_sobrecorreccion": round(100 * sb.mean(), 1), "exact_match_estricto": round(100 * (e.astype(bool) & ~sb).mean(), 1),
                          "acierta_con_sobrecorreccion": round(100 * (e.astype(bool) & sb).mean(), 1)})
    r = pd.DataFrame(filas)
    r.to_csv("resultados/extras/em_estricto.csv", index=False)
    print(r.to_string(index=False))


if __name__ == "__main__":
    main()
