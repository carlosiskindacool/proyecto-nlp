"""
¿Hay oraciones de prueba (casi) repetidas en el entrenamiento?

python src/extras/fuga_entrenamiento.py

El entrenamiento de los modelos propios excluye por construcción las oraciones de prueba **idénticas** (`prohibidas` en los cuadernos). Aquí se
comprueba que no haya además oraciones casi idénticas (retuits, citas, titulares repetidos con pequeños cambios), que inflarían los resultados de los
modelos. Para cada oración única de prueba (594) se busca la oración de entrenamiento (10.490 pares) más parecida, con la similitud de Jaccard entre
conjuntos de palabras normalizadas, y se cuentan las que superan 0,6, 0,8 y 0,9. También se mide cuántos términos ancla de la prueba aparecen en alguna
oración de entrenamiento (eso es esperable: el entrenamiento se armó con los mismos términos). Escribe resultados/extras/fuga_entrenamiento.md y
resultados/extras/fuga_entrenamiento_candidatas.csv (las 25 más parecidas).
"""
import os
import re
import sys
import unicodedata

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from comun import EXTRAS, REPO, leer  # noqa: E402

os.chdir(REPO)


def palabras(texto):
    t = unicodedata.normalize("NFKC", str(texto)).casefold()
    return frozenset(re.findall(r"[#@]?\w+", t))


def main():
    entren = pd.read_csv("data/interim/borrador_entrenamiento.csv", sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    col = "oracion" if "oracion" in entren.columns else entren.columns[0]
    train = list(dict.fromkeys(entren[col]))
    pruebas = leer("data/processed/predicciones_mt5_flo_fp32.csv").drop_duplicates("chileno")
    pt = list(pruebas.chileno)
    tr_sets = [palabras(o) for o in train]
    indice = {}
    for i, s in enumerate(tr_sets):
        for w in s:
            indice.setdefault(w, []).append(i)
    exactas = {" ".join(sorted(s)) for s in tr_sets}
    filas = []
    for o in pt:
        s = palabras(o)
        if not s:
            continue
        candidatos = {}
        for w in s:
            for i in indice.get(w, ()):
                candidatos[i] = candidatos.get(i, 0) + 1
        mejor, mj = None, 0.0
        for i, inter in candidatos.items():
            j = inter / (len(s) + len(tr_sets[i]) - inter)
            if j > mj:
                mejor, mj = i, j
        filas.append({"oracion_de_prueba": o, "mas_parecida_en_entrenamiento": train[mejor] if mejor is not None else "", "jaccard": round(mj, 3),
                      "mismas_palabras": " ".join(sorted(s)) in exactas})
    r = pd.DataFrame(filas).sort_values("jaccard", ascending=False)
    r.head(25).to_csv(os.path.join(EXTRAS, "fuga_entrenamiento_candidatas.csv"), index=False, encoding="utf-8-sig")
    n = len(r)
    # contención: la oración de prueba (o la de entrenamiento) está dentro de la otra (por ejemplo, con menciones agregadas)
    norm = lambda t: " ".join(re.findall(r"[#@]?\w+", unicodedata.normalize("NFKC", str(t)).casefold()))
    tn = [norm(o) for o in train]
    largas = [x for x in tn if len(x) >= 20]
    pn = [norm(o) for o in pt]
    contenidas = [o for o, n_ in zip(pt, pn) if len(n_) >= 20 and any(n_ in x for x in tn)]
    contienen = [o for o, n_ in zip(pt, pn) if len(n_) >= 20 and any(x in n_ for x in largas)]
    ancla = pruebas.termino.str.lower().unique()
    texto_train = " \n ".join(unicodedata.normalize("NFKC", o).casefold() for o in train)
    con_term = sum(1 for t in ancla if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", texto_train))
    lineas = ["# Revisión de fuga entre entrenamiento y prueba", "",
              f"- Oraciones únicas de prueba: {n}; oraciones únicas de entrenamiento: {len(train)}.",
              f"- Con las mismas palabras (en cualquier orden) que alguna de entrenamiento: {int(r.mismas_palabras.sum())}.",
              f"- Similitud de Jaccard con la oración de entrenamiento más parecida: ≥ 0,9: {int((r.jaccard >= 0.9).sum())}; ≥ 0,8: {int((r.jaccard >= 0.8).sum())}; "
              f"≥ 0,6: {int((r.jaccard >= 0.6).sum())}; mediana {r.jaccard.median():.2f}; máxima {r.jaccard.max():.2f}.",
              f"- Oraciones de prueba (de 20 caracteres o más) contenidas dentro de una de entrenamiento: {len(contenidas)}; que contienen una de entrenamiento: {len(contienen)}.",
              f"- Términos ancla de la prueba ({len(ancla)}) que aparecen en alguna oración de entrenamiento: {con_term} ({100 * con_term / len(ancla):.0f} %). "
              "Es esperable: el entrenamiento se armó con los mismos términos del diccionario; lo que no debe repetirse es la oración.", "",
              "Las 25 oraciones de prueba más parecidas a alguna de entrenamiento están en `fuga_entrenamiento_candidatas.csv`."]
    open(os.path.join(EXTRAS, "fuga_entrenamiento.md"), "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print("\n".join(lineas))
    print(r.head(8).to_string(index=False))


if __name__ == "__main__":
    main()
