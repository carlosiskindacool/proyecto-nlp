"""
Paso 1 del flujo: baja Wikcionario (es) y Wiktionary (en) y arma el diccionario automático.

python src/chilenismos/diccionario.py [--out data/processed/diccionario.csv]
La caché de la API queda en data/raw/cache_{es,en}.jsonl.
"""
import argparse
import csv
import json
import os
import re
import time
from collections import Counter
 
import requests

from rutas import CACHE_WIKCIONARIO, DICCIONARIOS
 
FUENTES = {
    "es": ("https://es.wiktionary.org/w/api.php", "Categoría:ES:Chile"),
    "en": ("https://en.wiktionary.org/w/api.php", "Category:Chilean Spanish"),
}
HEADERS = {"User-Agent": "IIC3670-jerga-chilena/0.1"}
 
TERMINO_OK = re.compile(r"[a-záéíóúüñ]+(?:[ -][a-záéíóúüñ]+)*")
FLEXION = re.compile(
    r"^(forma|plural|femenino|masculino|participio|gerundio|variante|abreviatura"
    r"|(primera|segunda|tercera) persona)\b"
    r"|^(plural|feminine|masculine|alternative|obsolete|misspelling)\b"
    r"|\b(form|plural|feminine|masculine|participle) of\b",
    re.I,
)
 
 
def api(url, **params):
    for intento in range(6):
        r = requests.get(url, params={**params, "format": "json"}, headers=HEADERS, timeout=60)
        if r.status_code not in (429, 503):
            r.raise_for_status()
            return r.json()
        pedida = r.headers.get("Retry-After", "")
        espera = min(int(pedida) if pedida.isdigit() else 2 ** (intento + 2), 120)
        print(f"  HTTP {r.status_code}: reintentando en {espera}s", flush=True)
        time.sleep(espera)
    r.raise_for_status()
 
 
def titulos_categoria(url, categoria):
    titulos, cont = [], {}
    while True:
        d = api(url, action="query", list="categorymembers", cmtitle=categoria,
                cmlimit=500, cmnamespace=0, cmtype="page", **cont)
        titulos += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d:
            return titulos
        cont = d["continue"]
 
 
def wikitextos(url, titulos, cache):
    """Descarga el wikitexto en lotes; lo guarda en cache (jsonl) para no repetir peticiones."""
    hechos = {}
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            hechos = dict(json.loads(linea) for linea in f)
    faltan = [t for t in titulos if t not in hechos]
    print(f"  {len(hechos)} páginas en caché, {len(faltan)} por descargar", flush=True)
    with open(cache, "a", encoding="utf-8") as f:
        for i in range(0, len(faltan), 50):
            d = api(url, action="query", prop="revisions", rvprop="content", rvslots="main",
                    titles="|".join(faltan[i:i + 50]))
            for p in d["query"]["pages"].values():
                if "revisions" in p:
                    hechos[p["title"]] = p["revisions"][0]["slots"]["main"]["*"]
                    f.write(json.dumps([p["title"], hechos[p["title"]]], ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {min(i + 50, len(faltan))}/{len(faltan)}", flush=True)
            time.sleep(1)
    for t in titulos:
        if t in hechos:
            yield t, hechos[t]
 
 
def resolver_enlaces(s):
    s = re.sub(r"\[https?://\S+(?: ([^\]]*))?\]", r"\1", s)  
    return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)


def plantilla(m):
    nombre, *args = [a.strip() for a in m.group(1).split("|")]
    args = [a for a in args if "=" not in a] 
    n = nombre.lower()
    if n in ("plm", "ucf"):  
        return args[0][:1].upper() + args[0][1:] if args else ""
    if n in ("gloss", "gl", "vern", "w", "taxlink", "taxfmt", "impropia", "gentilicio"):
        return args[0] if args else ""
    if n.startswith(("variante", "grafía")): 
        return f"Variante de {args[0]}" if args else "Variante"
    if n.startswith("forma"): 
        return f"Forma de {args[0]}" if args else "Forma"
    if n == "sustantivo de verbo":
        return f"Sustantivo de {args[0]}" if args else ""
    if n == "adjetivo de sustantivo":
        return f"Relativo a {args[0]}" if args else ""
    if n in ("l", "m", "link"):  
        return args[1] if len(args) > 1 else ""
    if n.endswith(" of"):  
        return f"{nombre} {args[-1]}" if args else ""
    return ""  


def limpiar(s):
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<[^>]+>", "", s, flags=re.S)
    s = resolver_enlaces(s)
    while True: 
        s2 = re.sub(r"\{\{([^{}]*)\}\}", plantilla, s)
        if s2 == s:
            break
        s = s2
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s).strip(" :;")


NATURALEZA = {"aves", "plantas", "hongos", "mamíferos", "insectos", "árboles", "moluscos", "peces", "anfibios",
              "zoología", "botánica", "hierba", "arbustos", "arbusto", "algas", "frutos", "reptiles",
              "crustáceos", "flora", "fauna", "taxon"}
NATURALEZA_GLOSA = re.compile(
    r"^(ave|planta|hongo|árbol|arbusto|pez|insecto|mamífero|molusco|anfibio|reptil|crustáceo|hierba|alga|fruto|flor)\b",
    re.I)


def ejemplo_es(lineas):
    for linea in lineas:
        m = (re.match(r"\{\{ejemplo\|(?:1=)?(.*)\}\}\s*$", linea.strip())
             or re.match(r":+\*?\s*'''\s*Ejemplo:?\s*'''\s*:?\s*(.+)", linea.strip()))
        if m:
            return limpiar(re.split(r"\|\s*\w+=", m.group(1))[0])
    return ""


def parse_es(wt):
    """Primer sentido marcado {{ámbito|...Chile...}}; devuelve dict o None si no hay."""
    m = re.search(r"==\s*\{\{lengua\|es\}\}\s*==(.*?)(?=\n==\s*\{\{lengua\||\Z)", wt, re.S)
    bloques, cur = [], None
    for linea in (m.group(1) if m else wt).splitlines():
        if re.match(r";\s*\d+", linea):
            cur = [linea]
            bloques.append(cur)
        elif linea.startswith("="):  
            cur = None
        elif cur is not None:
            cur.append(linea)
    for b in bloques:
        texto = "\n".join(b)
        if re.search(r"\{\{ámbito\|[^}\n]*\bChile\b", texto):
            usos = (a.strip().lower() for u in re.findall(r"\{\{uso\|([^}]+)\}\}", texto)
                    for a in u.split("|") if "=" not in a)
            return {"glosa": limpiar(re.sub(r"^;\s*\d+", "", b[0])), "ejemplo": ejemplo_es(b[1:]),
                    "campo": "/".join(re.findall(r"\{\{csem\|([^}|]+)", b[0])),
                    "registro": "|".join(dict.fromkeys(usos))}
    return None


def parse_en(wt):
    """Primer sentido con {{lb|es|...Chile...}}; devuelve dict o None si no hay."""
    m = re.search(r"^==Spanish==\s*$(.*?)(?=^==[^=]|\Z)", wt, re.S | re.M)
    defs = []
    for linea in (m.group(1) if m else "").splitlines():
        if re.match(r"#(?![#*:])", linea):
            defs.append([linea, ""])
        elif defs and not defs[-1][1] and re.match(r"#+[*:]", linea):
            e = re.search(r"\{\{(?:ux|uxi|usex)\|es\|([^}]*)\}\}", resolver_enlaces(linea))
            if e:
                defs[-1][1] = limpiar(e.group(1).split("|")[0])
    for linea, ejemplo in defs:
        if re.search(r"\{\{lb\|es\|[^}\n]*\bChile\b", linea):
            taxon = re.search(r"\{\{(?:taxlink|taxfmt|vern)\|", linea)
            return {"glosa": limpiar(linea.lstrip("#")), "ejemplo": ejemplo,
                    "campo": "taxon" if taxon else "", "registro": ""}
    return None


def reemplazo(glosa):
    """Primera cláusula/sinónimo de la glosa en español si es corta (<=3 palabras)."""
    g = re.split(r"[.;(:,]", glosa)[0].strip().lower()
    return g if 0 < len(g.split()) <= 3 else ""


def motivo_descarte(termino, s):
    if termino[0].isupper():
        return "nombre propio"
    if len(termino.split()) > 3:
        return "más de 3 palabras"
    if not TERMINO_OK.fullmatch(termino):
        return "caracteres no alfabéticos"
    if s is None:
        return "sin sentido chileno"
    if not s["glosa"]:
        return "sin definición"
    if FLEXION.search(s["glosa"]):
        return "forma flexionada/variante"
    if NATURALEZA & set(s["campo"].lower().split("/")) or NATURALEZA_GLOSA.search(s["glosa"]):
        return "flora/fauna"
    return ""


def construir():
    por_termino = {}
    for fuente, (url, categoria) in FUENTES.items():
        titulos = titulos_categoria(url, categoria)
        print(f"{fuente}: {len(titulos)} páginas en la categoría")
        parse = parse_es if fuente == "es" else parse_en
        for titulo, wt in wikitextos(url, titulos, os.path.join(CACHE_WIKCIONARIO, f"cache_{fuente}.jsonl")):
            s = parse(wt)
            f = por_termino.setdefault(titulo, {"fuentes": [], "sentido": None, "de_es": False})
            f["fuentes"].append(fuente)
            if s and (fuente == "es" or not f["sentido"]):
                f["sentido"], f["de_es"] = s, fuente == "es"
    filas = []
    for termino, f in sorted(por_termino.items(), key=lambda kv: kv[0].lower()):
        s = f["sentido"] or {"glosa": "", "ejemplo": "", "campo": "", "registro": ""}
        motivo = motivo_descarte(termino, f["sentido"])
        filas.append({"termino": termino, "fuentes": "+".join(sorted(set(f["fuentes"]))), **s,
                      "reemplazo": reemplazo(s["glosa"]) if f["de_es"] else "",
                      "keep": int(not motivo), "motivo": motivo})
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DICCIONARIOS["equipo"])
    args = ap.parse_args()
    os.makedirs(CACHE_WIKCIONARIO, exist_ok=True)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    filas = construir()
    cols = ["termino", "fuentes", "glosa", "ejemplo", "campo", "registro", "reemplazo", "keep", "motivo"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(filas)
    keep = [f for f in filas if f["keep"]]
    print(f"\nTérminos únicos: {len(filas)} | keep=1: {len(keep)} | con reemplazo: "
          f"{sum(bool(f['reemplazo']) for f in keep)} | con registro (coloquial, vulgar...): "
          f"{sum(bool(f['registro']) for f in keep)}")
    print("Descartados por motivo:", dict(Counter(f["motivo"] for f in filas if f["motivo"])))
    print("\nMuestra:")
    for f in keep[:10]:
        print(f"  {f['termino']!r} [{f['fuentes']}] glosa={f['glosa'][:50]!r} reemplazo={f['reemplazo']!r}")
    print(f"\nEscrito en {args.out}.")


if __name__ == "__main__":
    main()