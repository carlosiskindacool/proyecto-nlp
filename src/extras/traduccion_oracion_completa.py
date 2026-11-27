"""
Calidad de la traducción de la oración completa (no solo del término ancla).

python src/extras/traduccion_oracion_completa.py        # con un Python que tenga torch y transformers (los modelos de traducción se bajan una vez)

El Exact Match mira solo el término ancla. Aquí se traduce al inglés la **referencia neutra** de cada oración con los mismos traductores (Opus-MT y
NLLB) y se compara, con chrF y BLEU, la traducción de la salida de cada sistema contra la traducción de la referencia. Es un sustituto automático de
la evaluación humana (que no se hizo): mide si la oración traducida se parece a la que saldría de la versión neutra correcta, y castiga la
sobrecorrección. Se informa el chrF por oración (promedio con intervalo bootstrap al 95 %) y el chrF y BLEU de corpus.

Lee las traducciones que ya existen (data/processed/eval_extrinseca.csv y resultados/extras/*) y traduce solo las referencias
(resultados/extras/traducciones_referencias.csv). Escribe resultados/extras/traduccion_oracion_completa.csv y ..._pares.csv.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
import sacrebleu

sys.path.insert(0, os.path.dirname(__file__))
from comun import EXTRAS, LLM, REPO, leer  # noqa: E402

os.chdir(REPO)
RUTA_REF = os.path.join(EXTRAS, "traducciones_referencias.csv")


def traducir_referencias(referencias):
    if os.path.exists(RUTA_REF):
        return leer(RUTA_REF)
    sys.path.insert(0, os.path.join(REPO, "src"))
    import eval_extrinseca as E
    unicas = list(dict.fromkeys(referencias.values()))
    filas = []
    for trad in ("mt", "nllb"):
        mapa = E.traducir(unicas, trad, 16)
        filas += [{"referencia": r, "traductor": trad, "traduccion_en": mapa.get(r, "")} for r in unicas]
    d = pd.DataFrame(filas)
    d.to_csv(RUTA_REF, index=False, encoding="utf-8-sig")
    return d


def traducciones_de_sistemas():
    """DataFrame chileno, sistema, traductor, traduccion_en de todas las fuentes."""
    nombres = {"mt5": "mt5_s1", "reglas_flo": "reglas_curado"}
    partes = [leer("data/processed/eval_extrinseca.csv").assign(sistema=lambda d: d.sistema.replace(nombres)),
              leer(os.path.join(EXTRAS, "traducciones_mt5_semillas.csv")), leer(os.path.join(EXTRAS, "eval_extrinseca_oraciones_byt5.csv")),
              leer(os.path.join(EXTRAS, "eval_extrinseca_oraciones_byt5_s2.csv")), leer(os.path.join(EXTRAS, "eval_extrinseca_oraciones_byt5_s3.csv"))]
    partes += [leer(f) for f in sorted(glob.glob(os.path.join(LLM, "eval_extrinseca_llm_*.csv")))]
    d = pd.concat([p[["chileno", "sistema", "traductor", "traduccion_en"]] for p in partes])
    return d[d.traduccion_en != ""].drop_duplicates(["chileno", "sistema", "traductor"])


def main():
    base = leer("data/processed/predicciones_mt5_flo_fp32.csv").drop_duplicates("chileno")
    referencias = dict(zip(base.chileno, base.referencia))
    ref_trad = traducir_referencias(referencias)
    tr = traducciones_de_sistemas()
    rng = np.random.default_rng(0)
    filas, por_sistema = [], {}
    for trad in ("mt", "nllb"):
        rt = dict(zip(ref_trad[ref_trad.traductor == trad].referencia, ref_trad[ref_trad.traductor == trad].traduccion_en))
        for s in sorted(tr.sistema.unique()):
            t = tr[(tr.sistema == s) & (tr.traductor == trad)].set_index("chileno").traduccion_en
            oraciones = [o for o in referencias if o in t.index and referencias[o] in rt]
            if len(oraciones) < 594:
                continue
            hip = [t[o] for o in oraciones]
            ref = [rt[referencias[o]] for o in oraciones]
            por_oracion = np.array([sacrebleu.sentence_chrf(h, [r]).score for h, r in zip(hip, ref)])
            boots = por_oracion[rng.integers(0, len(oraciones), size=(2000, len(oraciones)))].mean(axis=1)
            por_sistema[(s, trad)] = por_oracion
            filas.append({"traductor": trad, "sistema": s, "oraciones": len(oraciones), "chrf_por_oracion": round(por_oracion.mean(), 1),
                          "ic95_inferior": round(float(np.percentile(boots, 2.5)), 1), "ic95_superior": round(float(np.percentile(boots, 97.5)), 1),
                          "chrf_corpus": round(sacrebleu.corpus_chrf(hip, [ref]).score, 1), "bleu_corpus": round(sacrebleu.corpus_bleu(hip, [ref]).score, 1),
                          "traducciones_identicas_a_la_de_la_referencia_pct": round(100 * np.mean([h == r for h, r in zip(hip, ref)]), 1)})
    r = pd.DataFrame(filas)
    r.to_csv(os.path.join(EXTRAS, "traduccion_oracion_completa.csv"), index=False)
    print(r.to_string(index=False))

    pares = [("byt5", "reglas_curado"), ("byt5", "mt5_s1"), ("byt5", "mt5_s2"), ("byt5", "mt5_s3"), ("byt5_s2", "reglas_curado"), ("byt5_s3", "reglas_curado"),
             ("byt5_s2", "byt5"), ("byt5_s3", "byt5"), ("mt5_moe", "mt5_s1"), ("mt5_moe", "mt5_s2"),
             ("mt5_moe", "mt5_s3"), ("reglas_curado", "mt5_s1"), ("reglas_curado", "mt5_s2"), ("reglas_curado", "mt5_s3"), ("reglas_curado", "mt5_moe")]
    pares += [(s, "reglas_curado") for s in sorted(r.sistema.unique()) if s.startswith("llm_")]
    filas = []
    for trad in ("mt", "nllb"):
        for a, b in pares:
            if (a, trad) not in por_sistema or (b, trad) not in por_sistema:
                continue
            d = por_sistema[(a, trad)] - por_sistema[(b, trad)]
            boots = d[rng.integers(0, len(d), size=(2000, len(d)))].mean(axis=1)
            filas.append({"traductor": trad, "a": a, "b": b, "diferencia_chrf": round(d.mean(), 1), "ic95_inferior": round(float(np.percentile(boots, 2.5)), 1),
                          "ic95_superior": round(float(np.percentile(boots, 97.5)), 1)})
    p = pd.DataFrame(filas)
    p.to_csv(os.path.join(EXTRAS, "traduccion_oracion_completa_pares.csv"), index=False)
    print(p.to_string(index=False))


if __name__ == "__main__":
    main()
