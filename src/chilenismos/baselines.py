"""
python src/chilenismos/baselines.py [--pares annotation/lote1.csv ...] [--escenario equipo|flo|ambos]
    [--incluir-ambiguos] [--solo-validados] [--resumen resultados/comparacion_baselines.csv] [--modelo google/mt5-base] [--sin-mt5]
    [--out data/processed/predicciones.csv]

Escenario de diccionario para el baseline de reglas (variable ESCENARIO o --escenario):
  equipo : diccionario automático del equipo (data/processed/diccionario.csv)
  flo    : diccionario revisado a mano (data/curado/diccionario_flo_parte1.csv)
  ambos  : corre los dos y los compara con los mismos pares

--pares acepta varios archivos: cada sistema se evalúa en cada conjunto de pares y el resumen
guarda una fila por (sistema, conjunto). Los archivos con columna `revisor1` (los lotes de Flo)
solo usan los pares ya revisados y sin `DESCARTAR`.
"""
import argparse
import csv
import os
import re

import sacrebleu

from dicc import RUTAS, cargar_reglas

ESCENARIO = "equipo"  # "equipo" | "flo" | "ambos"
PARES_POR_DEFECTO = ("data/processed/pares.csv", "annotation/lote1.csv")


MENCION = re.compile(r"@usuario\b\s*")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\uFE0F\u200d\u2190-\u21FF]+")
LIMPIAR = True   # quita las menciones (@usuario) y los emojis de oración y referencia, para todos los sistemas


def limpiar(texto):
    """Quita menciones `@usuario` y emojis, y deja los espacios en orden."""
    return re.sub(r"\s+", " ", EMOJI.sub("", MENCION.sub("", texto))).strip()


def cargar_pares(path, limpio=None):
    """Acepta `chileno,neutro` (coma) o `termino;oracion;neutro` (como annotation/lote1.csv).

    Si el archivo trae la columna `revisor1` (lotes de Flo), solo cuentan los pares revisados y no descartados.
    Por defecto se limpian las menciones y los emojis (ver `limpiar`); con limpio=False quedan tal cual."""
    with open(path, encoding="utf-8") as f:
        cabecera = f.readline()
        f.seek(0)
        filas = list(csv.DictReader(f, delimiter=";" if cabecera.count(";") > cabecera.count(",") else ","))
    con_revisor = bool(filas) and "revisor1" in filas[0]
    pares = []
    for r in filas:
        chileno = (r.get("chileno") or r.get("oracion") or "").strip()
        neutro = (r.get("neutro") or "").strip()
        if not chileno or not neutro or neutro.upper() == "DESCARTAR":
            continue
        if con_revisor and not (r.get("revisor1") or "").strip():
            continue
        if LIMPIAR if limpio is None else limpio:
            chileno, neutro = limpiar(chileno), limpiar(neutro)
            if not chileno or not neutro:
                continue
        pares.append({"chileno": chileno, "neutro": neutro, "termino": r.get("termino", "")})
    if not pares:
        raise SystemExit(f"{path}: no hay pares revisados (la columna revisor1 está vacía).")
    return pares


def traducir_reglas(s, reglas, patron):
    def reemplazar(m):
        nuevo = reglas[m.group(0).lower()]
        return nuevo.capitalize() if m.group(0)[0].isupper() else nuevo
    return patron.sub(reemplazar, s)


def traducir_mt5(frases, modelo, lote=16):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(modelo)
    mod = AutoModelForSeq2SeqLM.from_pretrained(modelo).to(dev).eval()
    salidas = []
    for i in range(0, len(frases), lote):
        enc = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True,
                  max_length=128).to(dev)
        with torch.no_grad():
            out = mod.generate(**enc, max_new_tokens=64, num_beams=4)
        salidas += tok.batch_decode(out, skip_special_tokens=True)
    return salidas


def guardar_resumen(path, filas):
    """Agrega o actualiza filas (clave: sistema y conjunto de pares) en un CSV de resultados."""
    campos = ["sistema", "escenario", "bleu", "chrf", "n_pares", "pares", "nota"]
    previas = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            previas = {(r["sistema"], r["pares"]): r for r in csv.DictReader(f)}
    for r in filas:
        # el conjunto se identifica por su nombre, aunque el archivo esté fuera del repo (lote_1_tuits.csv)
        r["pares"] = "annotation/" + os.path.basename(r["pares"])
        previas[(r["sistema"], r["pares"])] = r
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(previas.values())


def ruta_salida(base, par_path, varios):
    """data/processed/predicciones.csv -> data/processed/predicciones_<conjunto>.csv si hay varios conjuntos."""
    if not varios:
        return base
    raiz, ext = os.path.splitext(base)
    return f"{raiz}_{os.path.splitext(os.path.basename(par_path))[0]}{ext}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", nargs="+", default=[next((p for p in PARES_POR_DEFECTO if os.path.exists(p)), PARES_POR_DEFECTO[0])])
    ap.add_argument("--escenario", default=ESCENARIO, choices=["equipo", "flo", "ambos"])
    ap.add_argument("--diccionario", help="ruta propia; reemplaza la del escenario (solo con equipo o flo)")
    ap.add_argument("--incluir-ambiguos", action="store_true",
                    help="usar también términos marcados ambiguo=1 (palabras con uso estándar muy frecuente)")
    ap.add_argument("--solo-validados", action="store_true", help="solo reemplazos con reemplazo_validado=1")
    ap.add_argument("--resumen", help="CSV donde agregar BLEU y chrF de cada sistema")
    ap.add_argument("--modelo", default="google/mt5-base")
    ap.add_argument("--out", default="data/processed/predicciones.csv")
    ap.add_argument("--sin-mt5", action="store_true")
    ap.add_argument("--sin-limpiar", action="store_true", help="no quitar menciones ni emojis (texto original)")
    args = ap.parse_args()

    global LIMPIAR
    LIMPIAR = not args.sin_limpiar
    opciones = dict(incluir_ambiguos=args.incluir_ambiguos, solo_validados=args.solo_validados)
    sufijo = "_con_ambiguos" if args.incluir_ambiguos else ""
    escenarios = ["equipo", "flo"] if args.escenario == "ambos" else [args.escenario]
    todas = {}
    for esc in escenarios:
        ruta = args.diccionario if args.diccionario and len(escenarios) == 1 else RUTAS[esc]
        todas[esc] = cargar_reglas(ruta, **opciones)

    for ruta_pares in args.pares:
        pares = cargar_pares(ruta_pares)
        fuente = [p["chileno"] for p in pares]
        ref = [p["neutro"] for p in pares]
        preds = {"identidad": fuente}
        for esc, (reglas, patron) in todas.items():
            preds[f"reglas_{esc}{sufijo}"] = [traducir_reglas(s, reglas, patron) for s in fuente]
        if not args.sin_mt5:
            preds["mt5"] = traducir_mt5(fuente, args.modelo)

        print(f"\n{os.path.basename(ruta_pares)}: {len(pares)} pares | formas con regla: {({e: len(r[0]) for e, r in todas.items()})}")
        print(f"{'sistema':<28} {'BLEU':>6} {'chrF':>6}")
        resumen = []
        for nombre, hip in preds.items():
            bleu, chrf = sacrebleu.corpus_bleu(hip, [ref]).score, sacrebleu.corpus_chrf(hip, [ref]).score
            print(f"{nombre:<28} {bleu:6.1f} {chrf:6.1f}")
            esc = nombre.split("_")[1] if nombre.startswith("reglas_") else ""
            resumen.append({"sistema": nombre, "escenario": esc, "bleu": f"{bleu:.1f}", "chrf": f"{chrf:.1f}",
                            "n_pares": len(pares), "pares": os.path.basename(ruta_pares),
                            "nota": "incluye términos ambiguos" if sufijo and esc else ""})
        if args.resumen:
            guardar_resumen(args.resumen, resumen)

        salida = ruta_salida(args.out, ruta_pares, len(args.pares) > 1)
        os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
        with open(salida, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["chileno", "neutro", *preds])
            w.writerows(zip(fuente, ref, *preds.values()))
        print(f"Escrito {salida}")


if __name__ == "__main__":
    main()
