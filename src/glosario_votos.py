"""
Regla de votos para el glosario es -> en de los términos ancla.

python src/glosario_votos.py [--umbral 3] [--salida data/interim/glosario_votos.csv]

Cada fuente propone glosas en inglés para un término. Los votos se cuentan por FAMILIA, no por modelo: Sonnet y Haiku son
una sola familia (Claude); el Wikcionario en inglés, el Wikcionario en español y las glosas [EN] del diccionario curado
son una sola (diccionario), porque se copian entre sí. Una glosa se acepta si al menos --umbral familias distintas
proponen una glosa equivalente (misma frase, o una contenida en la otra como palabras completas).

Calibración: con los términos revisados a mano por Carlos (glosario_es_en_test_revisado.csv) se mide, para cada umbral,
cuántas glosas aceptadas están respaldadas por Carlos y en cuántos de sus términos la regla acepta algo.

Salida: una fila por término con las glosas aceptadas, las familias que votaron y el estado (aceptado / revisar / sin_glosa).
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from functools import lru_cache

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from glosario_modelos import separar_en  # noqa: E402

GLOSARIO = "data/diccionario/glosario_es_en_test.csv"
REVISADO = "data/diccionario/glosario_es_en_test_revisado.csv"
DICCIONARIO = "data/curado/diccionario_flo.csv"
# archivo (glosas_<x>.json) -> familia
FUENTES = {"wikcionario_en": "diccionario", "wikcionario_es": "diccionario", "sonnet": "claude", "haiku": "claude",
           "gemini": "gemini", "cohere": "cohere", "openrouter": "nvidia", "cf_llama": "meta", "cf_mistral": "mistral", "mistral": "mistral",
           "cf_gptoss": "openai", "cf_qwen": "alibaba", "ibm": "ibm"}


def norm(g):
    g = unicodedata.normalize("NFKC", g).replace("‐", "-").replace("‑", "-").casefold()
    g = re.sub(r"\(.*?\)", " ", g)
    g = re.sub(r"[^a-z' -]", " ", g)
    g = re.sub(r"\s+", " ", g).strip(" -")
    return re.sub(r"^(to|a|an|the) ", "", g)


PALABRAS_VACIAS = {"to", "a", "an", "the", "of", "one's", "ones", "someone", "somebody", "something", "oneself", "your", "his", "her", "it"}


def _raiz(w):
    """Raíz muy simple (sin librerías): plurales, -ing, -ed y la 'e' final."""
    if len(w) > 4 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
        if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "aeiouls":
            w = w[:-1]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
        if len(w) > 3 and w[-1] == w[-2] and w[-1] not in "aeiouls":
            w = w[:-1]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w[:-1] if len(w) > 4 and w.endswith("e") else w


@lru_cache(maxsize=None)
def clave(g):
    """Forma para comparar: guiones como espacios, sin artículos ni «someone», cada palabra en su raíz."""
    palabras = [_raiz(w) for w in re.split(r"[\s-]+", g) if w and w not in PALABRAS_VACIAS]
    return tuple(palabras)


def par(a, b):
    """Dos glosas son equivalentes si, ya normalizadas, son la misma frase (también sin espacios: «lightbulb»),
    o una está contenida en la otra como palabras completas."""
    ka, kb = clave(a), clave(b)
    if not ka or not kb:
        return False
    if ka == kb or "".join(ka) == "".join(kb):
        return True
    c, l = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
    if len("".join(c)) < 3:
        return False
    return any(l[i:i + len(c)] == c for i in range(len(l) - len(c) + 1))


def cargar(terminos):
    """{familia: {termino: [glosas normalizadas]}}"""
    fam = {}
    for f, familia in FUENTES.items():
        ruta = f"data/interim/glosas_{f}.json"
        if not os.path.exists(ruta):
            continue
        d = json.load(open(ruta, encoding="utf-8"))
        for t, v in d.items():
            fam.setdefault(familia, {}).setdefault(t, []).extend(n for n in map(norm, v) if n)
    d = pd.read_csv(DICCIONARIO, encoding="utf-8-sig", keep_default_na=False, dtype=str).drop_duplicates("termino").set_index("termino")
    for t in terminos:
        if t in d.index:
            en = separar_en(d.loc[t, "definicion"])[1]
            fam.setdefault("diccionario", {}).setdefault(t, []).extend(n for n in map(lambda x: norm(x.rstrip(": ")), en) if n)
    return fam


def votar(fam, termino, umbral):
    """[(glosa, familias que la apoyan)] ordenadas, solo las que llegan al umbral."""
    candidatas = {g for f in fam for g in fam[f].get(termino, [])} - {norm(termino)}   # una sigla devuelta tal cual no es una traducción
    res = []
    for g in sorted(candidatas):
        apoyan = sorted(f for f in fam if any(par(g, x) for x in fam[f].get(termino, [])))
        if len(apoyan) >= umbral:
            res.append((g, apoyan))
    # quita glosas que otra aceptada ya contiene
    return [(g, a) for g, a in res if not any(h != g and par(g, h) and len(h) < len(g) for h, _ in res)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=int, default=3)
    ap.add_argument("--salida", default="data/interim/glosario_votos.csv")
    args = ap.parse_args()
    g = pd.read_csv(GLOSARIO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    terminos = [t for t in g["termino"] if "�" not in t]
    fam = cargar(terminos)
    print("Familias:", {f: len(v) for f, v in fam.items()})

    carlos = pd.read_csv(REVISADO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    carlos = {r.termino: [n for n in map(norm, r.acepta_en.split("|")) if n] for r in carlos.itertuples() if r.acepta_en.strip()}
    # la calibración no puede usar a Carlos como votante: el diccionario [EN] nunca es su revisión
    print(f"\nCalibración con los {len(carlos)} términos de Carlos:")
    print(f"{'umbral':>7} {'términos con alguna glosa aceptada':>38} {'de esos, comparten una con Carlos':>36} {'glosas aceptadas respaldadas':>30}")
    for k in range(1, 6):
        con = comp = tot = ok = 0
        for t, ref in carlos.items():
            acept = votar(fam, t, k)
            if acept:
                con += 1
                comp += any(par(g, r) for g, _ in acept for r in ref)
                tot += len(acept)
                ok += sum(any(par(g, r) for r in ref) for g, _ in acept)
        print(f"{k:>7} {con:>30} de {len(carlos)} {comp:>22} de {con:<6} {ok:>14}/{tot} ({100 * ok / max(tot, 1):.0f} %)")

    filas = []
    for t in terminos:
        acept = votar(fam, t, args.umbral)
        hay = any(t in fam[f] for f in fam)
        estado = "aceptado" if acept else ("revisar" if hay else "sin_glosa")
        filas.append({"termino": t, "estado": estado, "glosas_aceptadas": " | ".join(x for x, _ in acept),
                      "n_familias": max((len(a) for _, a in acept), default=0),
                      "familias": "; ".join(sorted({f for _, a in acept for f in a})),
                      "en_revision_carlos": "si" if t in carlos else ""})
    out = pd.DataFrame(filas)
    out.to_csv(args.salida, index=False, sep=";", encoding="utf-8-sig")
    print(f"\nUmbral {args.umbral}: {out['estado'].value_counts().to_dict()}  ->  {args.salida}")


if __name__ == "__main__":
    main()
