"""
Un LLM con el diccionario como contexto, sobre las 594 oraciones de prueba (el «techo» de la fase 1: `llm_dicc_curado`).

python src/extras/llm_dicc_594.py --backend gemini --modelo gemini-3.8-flash --etiqueta gemini [--hilos 2] [--sin-diccionario]
python src/extras/llm_dicc_594.py --backend claude-code --modelo claude-sonnet-5-5 --etiqueta sonnet
python src/extras/llm_dicc_594.py --backend claude-code --modelo claude-haiku-5-5 --etiqueta haiku
python src/extras/llm_dicc_594.py --backend cohere --modelo command-a-plus-05-2026 --etiqueta cohere
python src/extras/llm_dicc_594.py --backend ibm --modelo ibm/granite-4-h-small --etiqueta ibm

Usa el mismo prompt y el mismo formato de pedido que los baselines con LLM de la fase 1 (src/pares/llm.py: `SISTEMA`, `prompt_usuario`), con el
diccionario revisado unificado (data/curado/diccionario_flo.csv) y lotes de 10 oraciones. Cada oración única se manda una sola vez. Retoma lo ya hecho.

Escribe resultados/extras/llm_dicc/predicciones_llm_<etiqueta>.csv con las mismas columnas que data/processed/predicciones_*.csv (conjunto, chileno,
referencia, termino, llm_<etiqueta>), de modo que sirve de entrada a metricas_normalizador.py y a eval_extrinseca.py.

Ojo con la interpretación: Sonnet escribió los borradores sobre los que se hicieron las referencias de los conjuntos de prueba, así que un LLM de otra
familia (Gemini) es una comparación más limpia.
"""
import argparse
import json
import os
import sys

import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(REPO)
sys.path.insert(0, "src")
sys.path.insert(0, "src/chilenismos")
sys.path.insert(0, "src/pares")
from dicc import RUTAS, cargar_entradas, construir_reglas, entradas_en  # noqa: E402
from llm import traducir  # noqa: E402
import glosario_modelos as G  # noqa: E402  (src/; `clave` lee las claves del entorno o del registro de Windows)

import llm as _llm  # noqa: E402

# Cohere, IBM y los demás backends de src/glosario_modelos.py se conectan al mismo lector de lotes (con el mismo prompt de traducción)
G.SISTEMA = _llm.SISTEMA


def _conectar(backend):
    def completar(usuario, modelo=None):
        try:
            return G.completar(backend, modelo, usuario)
        except OSError as e:          # desconexiones de red: el lector de lotes reintenta
            raise RuntimeError(str(e))
    return completar


for _b in ("cohere", "ibm", "mistral", "openrouter", "cloudflare"):
    _llm.COMPLETAR.setdefault(_b, _conectar(_b))

for _nombre in ("GEMINI_API_KEY",):
    try:
        os.environ.setdefault(_nombre, G.clave(_nombre))
    except SystemExit:
        pass

SALIDA = os.path.join(REPO, "resultados", "extras", "llm_dicc")
os.makedirs(SALIDA, exist_ok=True)
leer = lambda p: pd.read_csv(p, encoding="utf-8-sig", keep_default_na=False, dtype=str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True)
    ap.add_argument("--modelo")
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--hilos", type=int, default=1)
    ap.add_argument("--sin-diccionario", action="store_true", help="zero-shot: solo la oración, sin diccionario")
    ap.add_argument("--limite", type=int, default=0)
    args = ap.parse_args()

    base = leer("data/processed/predicciones_mt5_flo_fp32.csv")[["conjunto", "chileno", "referencia", "termino"]]
    unicas = list(dict.fromkeys(base.chileno))
    if args.limite:
        unicas = unicas[:args.limite]
    cache = os.path.join(SALIDA, f"salidas_llm_{args.etiqueta}.json")
    hechas = json.load(open(cache, encoding="utf-8")) if os.path.exists(cache) else {}
    faltan = [o for o in unicas if not hechas.get(o)]
    print(f"{args.etiqueta}: {len(unicas)} oraciones únicas, {len(faltan)} por pedir", flush=True)

    _, indice, patron = construir_reglas(cargar_entradas(RUTAS["flo"], incluir_ambiguos=True))
    items = [(o, None if args.sin_diccionario else entradas_en(o, indice, patron)) for o in faltan]
    # de a 100 oraciones, para guardar el avance
    for i in range(0, len(items), 100):
        parte = items[i:i + 100]
        salidas = traducir(parte, args.backend, args.modelo, hilos=args.hilos, progreso=False)
        for (o, _), s in zip(parte, salidas):
            hechas[o] = s
        json.dump(hechas, open(cache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"  {min(i + 100, len(items))}/{len(items)}", flush=True)

    vacias = sum(1 for o in unicas if not hechas.get(o))
    nombre = f"llm_{args.etiqueta}"
    out = base[base.chileno.isin(unicas)].copy()
    out[nombre] = out.chileno.map(lambda o: hechas.get(o) or o)   # una oración sin respuesta se deja como la original (y se avisa)
    ruta = os.path.join(SALIDA, f"predicciones_{nombre}.csv")
    out.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"{len(out)} filas ({len(unicas)} oraciones únicas; {vacias} sin respuesta) -> {ruta}")


if __name__ == "__main__":
    main()
