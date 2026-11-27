"""
Muestra de oraciones con sobrecorrección para auditarla a mano: ¿es un error real o jerga que la referencia dejó sin anotar?

python src/extras/auditoria_sobrecorreccion.py [--sistema llm_haiku] [--n 40]

Toma al azar (semilla 0) `n` oraciones donde el sistema cambió alguna palabra que la referencia dejó igual y escribe, por cada una, el original,
la referencia, la salida y las palabras de más (original -> salida). La columna `clasificacion` queda vacía para llenarla a mano.
Escribe resultados/extras/auditoria_sobrecorreccion_<sistema>.csv
"""
import argparse
import os
import sys
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(__file__))
from comun import REPO, cargar_salidas  # noqa: E402
from em_estricto import indices_cambiados  # noqa: E402
from metricas_normalizador import normalizar  # noqa: E402

os.chdir(REPO)


def cambios_de_mas(original, referencia, salida):
    """Pares (palabra original, lo que pone el sistema) de las palabras que el sistema cambió y la referencia no."""
    o, s = normalizar(original), normalizar(salida)
    extra = indices_cambiados(o, s) - indices_cambiados(o, normalizar(referencia))
    pares = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, o, s, autojunk=False).get_opcodes():
        if tag != "equal" and (set(range(i1, max(i2, i1 + 1))) & extra or (i2 == i1 and max(i1 - 1, 0) in extra)):
            pares.append(f"{' '.join(o[i1:i2]) or '∅'} -> {' '.join(s[j1:j2]) or '∅'}")
    return pares


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sistema", default="llm_haiku")
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    df = cargar_salidas().drop_duplicates("original")
    filas = []
    for _, r in df.iterrows():
        c = cambios_de_mas(r.original, r.referencia, r[a.sistema])
        if c:
            filas.append({"conjunto": r.conjunto, "termino": r.termino, "original": r.original, "referencia": r.referencia,
                          "salida": r[a.sistema], "cambios_de_mas": " ; ".join(c), "clasificacion": ""})
    import pandas as pd
    t = pd.DataFrame(filas)
    print(f"{len(t)} oraciones con sobrecorrección de {len(df)}")
    m = t.sample(min(a.n, len(t)), random_state=0).reset_index(drop=True)
    m.to_csv(f"resultados/extras/auditoria_sobrecorreccion_{a.sistema}.csv", index=False, encoding="utf-8-sig")
    for i, r in m.iterrows():
        print(f"{i:02d} [{r.termino}] {r.cambios_de_mas}\n    ORIG: {r.original[:200]}\n    REF : {r.referencia[:200]}")
