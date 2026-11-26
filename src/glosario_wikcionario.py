"""
Glosas en inglés de los términos ancla desde el Wikcionario (CC BY-SA), por la API pública. Solo se envía el término.

python src/glosario_wikcionario.py

Escribe dos archivos {termino: [glosas]} en data/interim/:
  glosas_wikcionario_en.json : sección Spanish del Wikcionario en inglés (glosas de todos los sentidos, no solo los chilenos)
  glosas_wikcionario_es.json : traducciones al inglés ({{trad|en|...}}) del Wikcionario en español
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

UA = "glosario-chilenismos/0.1 (proyecto de curso)"
GLOSARIO = "data/diccionario/glosario_es_en_test.csv"


def pedir(api, titulos):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                                "titles": "|".join(titulos), "format": "json", "formatversion": "2", "redirects": "1"})
    req = urllib.request.Request(f"{api}?{q}", headers={"User-Agent": UA})
    for n in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == 5:
                raise
            time.sleep(int(e.headers.get("Retry-After", 10)) + 5 * n)


def limpiar_en(linea):
    s = linea.lstrip("#").strip()
    s = re.sub(r"\{\{(?:lb|lbl|label|qualifier|q|qual)\|[^}]*\}\}", "", s)
    s = re.sub(r"\{\{(?:l|m|link|mention)\|en\|([^|}]+)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{(?:gloss|non-gloss definition|n-g|ng)\|([^}|]*)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'''?|<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" .;,")


def glosas_en(texto):
    m = re.search(r"^==\s*Spanish\s*==\s*$(.*?)(?=^==[^=]|\Z)", texto, re.M | re.S)
    out = []
    for l in (m.group(1) if m else "").splitlines():
        if re.match(r"#(?![:*#])", l) and not re.search(
                r"\{\{(?:inflection of|form of|alternative form of|alt form|misspelling of|obsolete spelling)", l, re.I):
            g = limpiar_en(l)
            if g:
                out.append(g)
    return out


def glosas_es(texto):
    """Traducciones al inglés de la plantilla {{t|en|t1=hold|t2=grab}}."""
    out = []
    for m in re.finditer(r"\{\{t\+?\|en\|([^}]*)\}\}", texto):
        out += [v.strip() for v in re.findall(r"\|?t\d+=([^|}]*)", "|" + m.group(1)) if v.strip()]
    return list(dict.fromkeys(out))


def correr(api, terminos, extraer):
    res = {}
    for i in range(0, len(terminos), 20):
        d = pedir(api, terminos[i:i + 20])
        time.sleep(1)
        norm = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        redir = {r["to"]: r["from"] for r in d["query"].get("redirects", [])}
        for p in d["query"]["pages"]:
            if p.get("missing"):
                continue
            origen = redir.get(p["title"], p["title"])
            res[norm.get(origen, origen)] = extraer(p["revisions"][0]["slots"]["main"]["content"])
    return res


if __name__ == "__main__":
    g = pd.read_csv(GLOSARIO, sep=";", encoding="utf-8-sig", keep_default_na=False, dtype=str)
    terminos = [t for t in g["termino"] if "\ufffd" not in t]
    import sys
    for nombre, api, f in [("en", "https://en.wiktionary.org/w/api.php", glosas_en),
                           ("es", "https://es.wiktionary.org/w/api.php", glosas_es)]:
        if len(sys.argv) > 1 and nombre not in sys.argv[1:]:
            continue
        r = correr(api, terminos, f)
        json.dump(r, open(f"data/interim/glosas_wikcionario_{nombre}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"Wikcionario {nombre}: {sum(1 for v in r.values() if v)} de {len(terminos)} términos con glosas")
