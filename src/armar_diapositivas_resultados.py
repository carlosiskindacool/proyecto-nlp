"""
Arma docs/diapositivas_resultados_estilo_entrega_final.pptx: diapositivas sueltas (16:9) con el estilo del deck de la entrega final
(fondo crema, pastilla lila, tablas y barra inferior; Arial) con los
resultados que ya existen y, con «–» o «por correr», los que faltan. No modifica ningún deck: se importan con
«Reutilizar diapositivas» de PowerPoint.

python src/armar_diapositivas_resultados.py
"""
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Pt

W, H = 18288000, 10287000
AZUL, GRIS, CLARO = RGBColor(0x27, 0x26, 0x26), RGBColor(0x27, 0x26, 0x26), RGBColor(0xF4, 0xEA, 0xDF)   # texto, texto, filas
ROJO, BLANCO = RGBColor(0xB4, 0x53, 0x2A), RGBColor(255, 255, 255)
FONDO, LILA, BORDE, NARANJA = RGBColor(0xFB, 0xF6, 0xF1), RGBColor(0xE5, 0xCB, 0xF2), RGBColor(0xE3, 0xD6, 0xC6), RGBColor(0xFF, 0x94, 0x6C)
DY = 0.7        # el contenido empieza más abajo: el título ocupa hasta y = 5,2 cm
FUENTE = "Arial"
PENDIENTE = ("–", "por correr", "en curso")

import os
BASE = os.environ.get("BASE_PPTX")        # deck al que se agregan las diapositivas (por ejemplo el de la entrega final)
SALIDA = os.environ.get("SALIDA_PPTX", "docs/diapositivas_resultados_estilo_entrega_final.pptx")
prs = Presentation(BASE) if BASE else Presentation()
if not BASE:
    prs.slide_width, prs.slide_height = W, H
N0 = len(prs.slides._sldIdLst)
VACIA = next(l for l in prs.slide_layouts if l.name == "Blank") if BASE else prs.slide_layouts[6]


def cm(x):
    return int(x * 360000)


def nueva():
    s = prs.slides.add_slide(VACIA)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = FONDO
    return s


def ajustar(x, y):
    return (2.3 if x == 2 else x), (y + DY if 5 <= y < 22 else y)


def texto(s, x, y, w, h, lineas, size=24, bold=False, color=GRIS, ajusta=True):
    if ajusta:
        x, y = ajustar(x, y)
    tb = s.shapes.add_textbox(cm(x), cm(y), cm(w), cm(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, linea in enumerate(lineas if isinstance(lineas, list) else [lineas]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = linea
        r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, FUENTE
        p.space_after = Pt(6)


def encabezado(s, seccion, titulo):
    ancho = max(4.5, len(seccion) * 0.42 + 1.4)
    pastilla = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cm(2.3), cm(1.4), cm(ancho), cm(1.1))
    pastilla.fill.solid()
    pastilla.fill.fore_color.rgb = LILA
    pastilla.line.fill.background()
    pastilla.text_frame.text = seccion
    r = pastilla.text_frame.paragraphs[0].runs[0]
    r.font.size, r.font.name, r.font.color.rgb = Pt(14), FUENTE, AZUL
    pastilla.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    texto(s, 2.0, 2.9, 46.2, 2.3, titulo, 34, True, AZUL, ajusta=False)


def tabla(s, x, y, filas, anchos, size=15, alto=1.2, resaltar=()):
    x, y = ajustar(x, y)
    t = s.shapes.add_table(len(filas), len(filas[0]), cm(x), cm(y), cm(sum(anchos)), cm(alto * len(filas))).table
    for j, a in enumerate(anchos):
        t.columns[j].width = cm(a)
    for i, fila in enumerate(filas):
        t.rows[i].height = cm(alto)
        for j, v in enumerate(fila):
            c = t.cell(i, j)
            c.text = str(v)
            p = c.text_frame.paragraphs[0]
            p.font.size = Pt(size)
            p.font.bold = i == 0 or i in resaltar
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            c.fill.solid()
            c.fill.fore_color.rgb = LILA if i == 0 else (CLARO if i % 2 == 1 else FONDO)
            p.font.name = FUENTE
            p.font.color.rgb = AZUL if i == 0 else (ROJO if (str(v) in PENDIENTE or str(v).startswith('se espera')) else GRIS)


def pie(s, t):
    barra = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, cm(2.3), cm(25.1), cm(46.2), cm(2.5))
    barra.fill.solid()
    barra.fill.fore_color.rgb = LILA
    barra.line.fill.background()
    tb = s.shapes.add_textbox(cm(3.0), cm(25.1), cm(44.7), cm(2.5))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = tf.paragraphs[0].add_run()
    r.text = t
    r.font.size, r.font.name, r.font.color.rgb = Pt(13), FUENTE, AZUL


# 1. Datos: reúne la diapositiva de datos y la de pares (pares de evaluación, de entrenamiento, lote 2 y diccionario)
def tarjeta(s, x, y, w, h, relleno=BLANCO, titulo=None, cuerpo=None, size=17):
    c = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, cm(x), cm(y), cm(w), cm(h))
    c.fill.solid()
    c.fill.fore_color.rgb = relleno
    c.line.color.rgb = BORDE
    if titulo:
        texto(s, x + 0.4, y + 0.3, w - 0.8, 1.4, titulo, 21, True, AZUL, ajusta=False)
    if cuerpo:
        texto(s, x + 0.4, y + 1.9, w - 0.8, h - 2.0, cuerpo, size, False, GRIS, ajusta=False)


s = nueva()
encabezado(s, "Datos", "Datos: fuentes, diccionario, pares, borradores de LLM y revisión")
tarjeta(s, 2.3, 5.6, 22.8, 7.7, BLANCO, "Diccionario revisado a mano", [
    "1.985 términos revisados; 1.929 con reemplazo validado por sentido; 282 ambiguos (también son palabras estándar) se dejan sin cambiar; 5 se unificaron.",
    "Con un diccionario automático el reemplazo suena raro («buena onda» → «expresión de saludo»)."], 14)
tarjeta(s, 25.7, 5.6, 22.8, 7.7, CLARO, "Pares", [
    "Para evaluar: 598 pares revisados por una persona (213 del lote general, 72 de noticias, 165 de tuits y 148 de palabras nuevas); nunca se usan para entrenar.",
    "Para entrenar: 10.490 pares cuya versión neutra escribió Claude Sonnet 5.5 (claude-sonnet-5-5, vía Claude Code), sin revisión humana (9.966 para entrenar y 524 para validar; antes 1.491)."], 14)
tarjeta(s, 2.3, 13.7, 22.8, 7.9, CLARO, "Borradores: ¿qué LLM sirve?", [
    "200 pares, borradores a ciegas revisados por Flo.",
    "Haiku 5.5: 85,0 % aceptados (IC 95 %: 78,8 a 89,6). Gemini 3.5 flash-lite: 82,9 % (76,6 a 87,9). No se distinguen (McNemar p = 1,0).",
    "Llama 3.1 8B (local): 40,2 %; 19 respuestas vacías y 10 devolvieron el prompt. Se descarta."], 14)
tarjeta(s, 25.7, 13.7, 22.8, 7.9, BLANCO, "Revisión: un solo revisor", [
    "Un segundo revisor (integrante 2) revisó 120 pares a ciegas: coinciden en el 72 %, pero kappa = 0,04 (IC 95 %: −0,06 a 0,16).",
    "Marcó ok en 111 de 120 y Flo en unos 90; el desacuerdo está en «descartar». No llegarán más revisiones: queda como limitación."], 14)
tarjeta(s, 2.3, 22.0, 46.2, 2.9, BLANCO, None, None)
texto(s, 2.7, 22.1, 45.4, 2.8, [
    "Fuentes. Corpus: Chilean Spanish Corpus (jorgeortizfuentes/chilean-spanish-corpus, CC-BY-SA-4.0), ≈37 M de textos: 27,3 M tuits, 8,7 M web, 1,08 M noticias y 31 mil reclamos. "
    "Diccionario: Wikcionario (es), Wiktionary (en, vía kaikki.org) y diccionario de Román (1901–1918), 3.403 términos candidatos. Borradores: claude-sonnet-5-5."], 12, False, GRIS, ajusta=False)
pie(s, "Se quitaron del entrenamiento las oraciones de los conjuntos de prueba. Las menciones de usuarios van como @usuario y las claves de API no están en el repo. "
       "Modelos comparados con temperatura 0 el 24-nov-2026.")

# 2-4. Resultados de Carlos (leídos de resultados/anterior/) y lo que se espera de las corridas nuevas
import csv
import re


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))


MET = leer("resultados/anterior/metricas_normalizador.csv")
EXT = leer("resultados/anterior/eval_extrinseca.csv")
SIS = [("identidad", "Identidad (no cambia nada)"), ("reglas_equipo", "Reglas + dicc. automático"), ("reglas_flo", "Reglas + dicc. revisado"),
       ("mt5_flo_fp32", "mT5 (1.500 pares)"), ("mt5_moe_fp32", "mT5 + MoE (1.500 pares)")]
CONJ = [("lote1", "Lote general (213)"), ("lote_1_noticias", "Noticias (72)"), ("lote_1_tuits", "Tuits (165)")]


def coma(x, nd=1):
    return f"{float(x):.{nd}f}".replace(".", ",")


def met(s, c, k):
    return next(r[k] for r in MET if r["sistema"] == s and r["conjunto"] == c)


s = nueva()
encabezado(s, "Resultados", "BLEU / chrF: los números de Carlos y lo que esperamos")
filas = [["Sistema"] + [n for _, n in CONJ]]
for sis, nom in SIS:
    filas.append([nom] + [f"{coma(met(sis, c, 'bleu'))} / {coma(met(sis, c, 'chrf'))}" for c, _ in CONJ])
filas.append(["mT5 (10.490 pares)"] + ["se espera: mejora"] * 3)
filas.append(["mT5 + MoE (10.490 pares)"] + ["se espera: mejora"] * 3)
tabla(s, 2, 5.0, filas, [13, 11, 11, 11], 16, 1.35, resaltar=(3,))
pie(s, "Números de Carlos: resultados/metricas_normalizador.md (texto normalizado). Reglas con el diccionario de 1.985 entradas; mT5 y MoE entrenados con 1.500 pares (Colab, T4, fp32). "
       "«se espera» es una hipótesis, no un resultado: la corrida con 10.490 pares está en curso y su resultado final va en el informe (termina el 25/11 en la madrugada).")

s = nueva()
encabezado(s, "Resultados", "Evaluación intrínseca: ERR, los números de Carlos")
filas = [["Sistema"] + [n for _, n in CONJ]]
for sis, nom in SIS:
    filas.append([nom] + [coma(met(sis, c, "err")) for c, _ in CONJ])
filas.append(["mT5 (10.490 pares)"] + ["se espera: menos negativo"] * 3)
filas.append(["mT5 + MoE (10.490 pares)"] + ["se espera: menos negativo"] * 3)
tabla(s, 2, 5.0, filas, [13, 11, 11, 11], 16, 1.35, resaltar=(3,))
texto(s, 2, 16.3, 46, 5, ["ERR 0 = no cambiar nada; un valor negativo significa que el sistema estropea más palabras de las que corrige.",
                          "Solo las reglas con el diccionario revisado mejoran el español. El MoE queda sobre el mT5 denso en los tres conjuntos."], 17)
pie(s, "Números de Carlos (ERR de van der Goot, 2019; MultiLexNorm). «se espera» es una hipótesis: con 7 veces más pares de entrenamiento el ERR debería subir, "
       "pero probablemente siga bajo 0. Resultado final en el informe.")

s = nueva()
encabezado(s, "Resultados", "Evaluación extrínseca: ¿normalizar ayuda a traducir al inglés?")


def ema(traductor, sis):
    return next(r["ema"] for r in EXT if r["conjunto"] == "todos" and r["traductor"] == traductor and r["sistema"] == sis)


NOMBRE_EXT = {"identidad": "identidad", "reglas_equipo": "reglas_equipo", "reglas_flo": "reglas_flo", "mt5_flo_fp32": "mt5", "mt5_moe_fp32": "mt5_moe"}
filas = [["Sistema", "Opus-MT (446 oraciones)", "NLLB (446 oraciones)"]]
for sis, nom in SIS:
    filas.append([nom, coma(ema("mt", NOMBRE_EXT[sis])) + " %", coma(ema("nllb", NOMBRE_EXT[sis])) + " %"])
filas.append(["mT5 (10.490 pares)"] + ["se espera: sube algo"] * 2)
filas.append(["mT5 + MoE (10.490 pares)"] + ["se espera: sube algo"] * 2)
tabla(s, 2, 5.0, filas, [13, 12, 12], 16, 1.35, resaltar=(3,))
texto(s, 2, 16.3, 46, 5, ["Exact-Match Accuracy: la traducción contiene alguna traducción aceptada del término chileno.",
                          "Con las reglas revisadas se traducen bien cerca de 3 veces más chilenismos que sin normalizar."], 17)
pie(s, "Números de Carlos: resultados/eval_extrinseca.md (Opus-MT opus-mt-es-en y NLLB nllb-200-distilled-600M; glosario es→en de 180 términos revisado a mano). "
       "«se espera» es una hipótesis; resultado final en el informe.")

# 5. Efecto del diccionario
s = nueva()
encabezado(s, "Resultados", "Ampliar el diccionario ayuda en las palabras nuevas")
cd = CategoryChartData()
cd.categories = ["Identidad", "Dicc. libro 1 (443)", "Dicc. completo (1.985)"]
cd.add_series("BLEU", (86.2, 86.5, 88.2))
ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cm(2.3), cm(5.7), cm(26), cm(15), cd).chart
ch.has_legend = False
pl = ch.plots[0]
pl.has_data_labels = True
pl.data_labels.font.size = Pt(18)
pl.data_labels.number_format, pl.data_labels.number_format_is_linked = "0.0", False
ch.value_axis.minimum_scale, ch.value_axis.maximum_scale = 84, 89
ch.value_axis.tick_labels.font.size = ch.category_axis.tick_labels.font.size = Pt(14)
ch.series[0].format.fill.solid()
ch.series[0].format.fill.fore_color.rgb = NARANJA
texto(s, 30, 6, 16, 13, ["Solo palabras nuevas (143 tuits).", "", "El diccionario del libro 1 casi no se separa de la identidad: esas palabras no estaban.", "",
                         "Con el diccionario completo el BLEU sube 1,7 puntos.", "",
                         "En los conjuntos originales casi no cambia (89,6 → 90,6 en el lote general; 86,1 → 85,7 en tuits), porque sus palabras ya estaban en el libro 1."], 19)
pie(s, "Eje desde 84 para que se vea la diferencia. BLEU de las reglas (sin LLM, sin entrenamiento) sobre los tuits de palabras nuevas, con el diccionario de 443 entradas (libro 1) y con el de 1.985 (24-nov).")

# 6. LLM y acuerdo
s = nueva()
encabezado(s, "Evaluación humana", "Otros LLM como generadores de borradores, y acuerdo entre revisores")
tabla(s, 2, 5.0, [["Modelo", "Borradores aceptados", "IC 95 %"], ["Claude Haiku 5.5", "85,0 %", "78,8 a 89,6"], ["Gemini 3.5 flash-lite", "82,9 %", "76,6 a 87,9"],
                  ["Llama 3.1 8B (local)", "40,2 %", "31,9 a 49,0"], ["Claude Sonnet 5.5 (referencia)", "80,8 %", "–"]], [10.5, 6.5, 6], 16, 1.4)
texto(s, 2, 12.6, 23, 7, ["200 pares válidos; borradores a ciegas revisados por Flo.", "Haiku y Gemini no se distinguen (McNemar p = 1,0). Llama no sirve como generador."], 16)
texto(s, 27, 5.0, 19, 2, "Acuerdo entre revisores", 24, True, AZUL)
tabla(s, 27, 7.2, [["Pareja", "Kappa", "Pares"], ["Flo – integrante 2", "0,04", "120"], ["Flo – integrante 3", "por correr", "–"],
                   ["Flo – integrante 4", "por correr", "–"], ["Flo – integrante 5", "por correr", "–"]], [9, 5, 5], 16, 1.3)
texto(s, 27, 14.2, 19, 6, "Primer resultado: 72 % de acuerdo pero kappa 0,04. El desacuerdo está en «descartar» (uso estándar de la palabra): hay que aclarar esa regla antes de enviar los otros Excel.", 16)
pie(s, "Modelos: claude-sonnet-5-5, claude-haiku-5-5, gemini-3.5-flash-lite y llama3.1:8b, todos con temperatura 0 el 24-nov-2026.")

# 6b. Progreso real del entrenamiento (se lee de logs/cadena_mt5_denso.log; vuelve a correr este script para actualizarlo)
import os
import re
pasos, epocas = [], []
log = "logs/cadena_mt5_denso.log"
if os.path.exists(log):
    for linea in open(log, encoding="utf-8", errors="ignore"):
        m = re.search(r"época (\d+) paso (\d+)/(\d+) pérdida ([\d.]+)", linea)
        if m:
            e, st, tot, per = int(m[1]), int(m[2]), int(m[3]), float(m[4])
            pasos.append(((e - 1) * (tot + 1) + st, per))
        m = re.search(r"época (\d+): pérdida de entrenamiento ([\d.]+) \| validación ([\d.]+)", linea)
        if m:
            epocas.append((int(m[1]), float(m[2]), float(m[3])))
s = nueva()
encabezado(s, "Resultados", "mT5 denso con 10.490 pares: la pérdida baja (medido)")
if pasos:
    from pptx.chart.data import XyChartData
    xy = XyChartData()
    serie = xy.add_series("pérdida de entrenamiento")
    for st, per in pasos:
        serie.add_data_point(st, per)
    ch = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, cm(2.3), cm(5.7), cm(28), cm(15), xy).chart
    ch.has_legend = False
    ch.value_axis.tick_labels.font.size = ch.category_axis.tick_labels.font.size = Pt(14)
    ch.value_axis.has_title = ch.category_axis.has_title = True
    ch.value_axis.axis_title.text_frame.text = "pérdida"
    ch.category_axis.axis_title.text_frame.text = "pasos de entrenamiento (lote 4)"
filas = [["Época", "Pérdida de entrenamiento", "Pérdida de validación"]] +         [[str(e), f"{a:.3f}".replace(".", ","), f"{v:.3f}".replace(".", ",")] for e, a, v in epocas] +         [[str(e), "en curso", "en curso"] for e in range(len(epocas) + 1, 9)]
tabla(s, 32, 5.0, filas[:10], [3, 7, 7], 14, 1.05)
texto(s, 2, 20.2, 44, 1.2, f"Último paso medido: {pasos[-1][0]} de 19.928 (8 épocas); pérdida {pasos[-1][1]:.2f}".replace(".", ",") if pasos else "Sin datos todavía", 16, True, AZUL)
pie(s, "Datos reales del log de entrenamiento (GPU local, fp32, lote 4). La pérdida de validación se calcula al final de cada época. No son métricas de la tarea (BLEU, ERR): esas llegan al terminar.")

# 6c. Con qué se corrió cada resultado
s = nueva()
encabezado(s, "Transparencia", "Con qué se corrió cada resultado")
tabla(s, 2, 5.0, [
    ["Resultado", "Diccionario y datos", "Modelo / herramienta", "Dónde y quién"],
    ["Reglas (identidad, dicc. automático, dicc. revisado)", "Automático: 3.609 términos (809 con reemplazo). Revisado: 1.985 entradas, con el diccionario unificado", "baselines.py y metricas_normalizador.py (sin LLM ni entrenamiento)", "Rama combinado, recalculado el 24-nov-2026"],
    ["mT5 y MoE, 1.500 pares", "1.500 borradores de un LLM (claude-sonnet-5-5), sin revisión humana; 1.416 para entrenar y 75 para validar", "google/mt5-small, 8 épocas, Adafactor 5e-4, lote 8, fp32; MoE: 4 expertos, top-2", "Carlos, Google Colab (GPU T4)"],
    ["Evaluación extrínseca", "446 oraciones; glosario es→en de 180 términos revisado a mano", "Opus-MT (opus-mt-es-en) y NLLB (nllb-200-distilled-600M)", "Carlos"],
    ["Corridas nuevas (en curso; todavía sin resultados)", "10.490 pares cuya versión neutra escribió Claude Sonnet 5.5 (claude-sonnet-5-5) con el diccionario de 1.985 entradas, sin revisión humana", "Mismos notebooks y parámetros, lote 4 (memoria de 4 GB), transformers 5.24.0", "Flo, GPU local RTX 3050, 24-25 nov"],
    ["Borradores de otros LLM", "200 pares válidos; mismo prompt y diccionario como contexto", "claude-haiku-5-5, gemini-3.5-flash-lite, llama3.1:8b; temperatura 0", "Flo, 24-nov-2026"],
    ["Acuerdo entre revisores", "120 pares, a ciegas, sin ver la decisión de Flo", "Kappa de Cohen y alfa de Krippendorff", "Integrante 2 (único Excel recibido)"]],
    [11, 15, 12, 8], 12, 2.3)
pie(s, "Los conjuntos de prueba están revisados por una persona y nunca se usan para entrenar. Referencias de los borradores: claude-sonnet-5-5, esfuerzo por defecto de la cuenta de Flo.")

# 7. Qué esperamos de las corridas nuevas (hipótesis, no resultados)
s = nueva()
encabezado(s, "Próximos pasos", "Qué esperamos de las corridas nuevas (hipótesis)")
tabla(s, 2, 5.0, [
    ["Qué se mide", "Hoy (Carlos, 1.500 pares)", "Se espera con los datos nuevos"],
    ["ERR del mT5 denso", "−21,8 · −106,5 · −23,7", "se espera: menos negativo (7 veces más pares), probablemente bajo 0"],
    ["ERR del mT5 + MoE", "−16,2 · −80,4 · −11,8", "se espera: menos negativo y sobre el denso"],
    ["ERR de las reglas revisadas", "29,0 · 13,0 · 19,8", "se espera: sin cambio (no usan los pares de entrenamiento)"],
    ["Exact match con Opus-MT", "mT5 9,4 % · MoE 10,3 % · reglas 23,3 %", "se espera: mT5 y MoE suben algo; las reglas siguen primeras"],
    ["Palabras nuevas del diccionario", "–", "se espera: las reglas ganan sobre la identidad; falta revisar el glosario es→en para medirlo"]],
    [10, 15, 21], 15, 1.7)
_pasos, _perd = None, None
if os.path.exists("logs/cadena_mt5_denso.log"):
    for _l in open("logs/cadena_mt5_denso.log", encoding="utf-8", errors="ignore"):
        _m = re.search(r"época (\d+) paso (\d+)/(\d+) pérdida ([\d.]+)", _l)
        if _m:
            _pasos, _perd = (int(_m[1]) - 1) * 2491 + int(_m[2]), float(_m[4])
if _pasos:
    texto(s, 2, 16.6, 46, 3, f"Avance medido del entrenamiento (mT5 denso): paso {_pasos} de 19.928; la pérdida bajó de 28,5 al inicio a {str(_perd).replace('.', ',')}. "
                             "Es el único dato de las corridas nuevas que existe hoy.", 17, True)
pie(s, "Las columnas «se espera» son hipótesis basadas en que los datos de entrenamiento pasaron de 1.500 a 10.490 pares y el modelo sigue siendo chico. "
       "Resultado final en el informe; la corrida termina el 25/11 en la madrugada.")

# 8. Gráficos de resultados (números de Carlos; las barras de las corridas nuevas se agregan cuando existan)
def barras(s, x, y, w, h, categorias, series, formato="0.0", leyenda=True, size=12, colores=None):
    cd = CategoryChartData()
    cd.categories = categorias
    for nombre, valores in series:
        cd.add_series(nombre, valores)
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, cm(x), cm(y), cm(w), cm(h), cd).chart
    ch.font.name, ch.font.size = FUENTE, Pt(size)
    ch.has_legend = leyenda
    if leyenda:
        ch.legend.position = XL_LEGEND_POSITION.BOTTOM
        ch.legend.include_in_layout = False
    pl = ch.plots[0]
    pl.gap_width = 60
    pl.has_data_labels = True
    pl.data_labels.font.size = Pt(size - 1)
    pl.data_labels.number_format, pl.data_labels.number_format_is_linked = formato, False
    ch.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    ch.value_axis.major_gridlines.format.line.color.rgb = BORDE
    paleta = colores or [AZUL, NARANJA, RGBColor(0xC9, 0xA0, 0xDC)]
    for k, serie in enumerate(pl.series):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = paleta[k % len(paleta)]
    return ch


CORTOS = {"identidad": "Identidad", "reglas_equipo": "Reglas, dicc. automático", "reglas_flo": "Reglas, dicc. revisado",
          "mt5_flo_fp32": "mT5", "mt5_moe_fp32": "mT5 + MoE"}
sistemas_met = [k for k, _ in SIS]

s = nueva()
encabezado(s, "Resultados", "Solo las reglas con el diccionario revisado mejoran el texto")
texto(s, 2.3, 5.7, 22.7, 1.2, "ERR por sistema (0 = no cambiar nada)", 18, True, AZUL, ajusta=False)
barras(s, 2.3, 6.9, 22.7, 11.6, [CORTOS[k] for k in sistemas_met],
       [(n, [float(met(k, c, "err")) for k in sistemas_met]) for c, n in CONJ])
texto(s, 25.8, 5.7, 22.7, 1.2, "BLEU ganado o perdido frente a no hacer nada", 18, True, AZUL, ajusta=False)
barras(s, 25.8, 6.9, 22.7, 11.6, [CORTOS[k] for k in sistemas_met[1:]],
       [(n, [float(met(k, c, "bleu")) - float(met("identidad", c, "bleu")) for k in sistemas_met[1:]]) for c, n in CONJ])
tarjeta(s, 2.3, 18.9, 22.7, 5.8, NARANJA, "Corrida de Carlos (1.500 pares)", [
    "Las reglas con el diccionario revisado son las únicas con ERR positivo (13 a 29). mT5 y MoE tienen ERR negativo: cambian palabras que no debían. El MoE queda sobre el denso."], 14)
tarjeta(s, 25.8, 18.9, 22.7, 5.8, CLARO, "Se espera de las corridas nuevas (hipótesis)", [
    "Con 10.490 pares, mT5 y MoE deberían quedar menos negativos, probablemente todavía bajo 0. Las reglas no cambian. Resultado final en el informe."], 14)
pie(s, "Números de Carlos: resultados/metricas_normalizador.csv (texto normalizado; ERR de van der Goot, 2019). Reglas con el diccionario de 1.985 entradas; mT5 y MoE con 1.500 pares (Colab, T4, fp32). "
       "«se espera» es una hipótesis, no un resultado.")

s = nueva()
encabezado(s, "Resultados", "Normalizar antes de traducir: el traductor acierta unas 3 veces más")
texto(s, 2.3, 5.7, 28, 1.2, "% de chilenismos bien traducidos al inglés (446 oraciones)", 18, True, AZUL, ajusta=False)
barras(s, 2.3, 6.9, 28.5, 12.2, [CORTOS[k] for k in sistemas_met],
       [("Opus-MT", [float(ema("mt", NOMBRE_EXT[k])) for k in sistemas_met]), ("NLLB", [float(ema("nllb", NOMBRE_EXT[k])) for k in sistemas_met])],
       colores=[AZUL, NARANJA])
tarjeta(s, 31.5, 6.9, 17, 5.4, BLANCO, "Un ejemplo", [
    "Sin normalizar, Opus-MT traduce «chela» como «célula hecha a mano». Con las reglas revisadas dice «cerveza»."], 14)
tarjeta(s, 31.5, 12.7, 17, 6.4, CLARO, "Qué mide (exact match)", [
    "Proporción de oraciones cuya traducción contiene una traducción aceptada del término chileno (glosario es→en revisado a mano, 180 términos)."], 14)
tarjeta(s, 2.3, 19.6, 46.2, 5.1, NARANJA, "Se espera de las corridas nuevas (hipótesis)", [
    "mT5 y MoE con 10.490 pares deberían subir algo sobre su 9 a 10 % actual, sin alcanzar a las reglas revisadas (23 %). Para las palabras nuevas falta revisar el glosario es→en: solo 59 de 237 términos nuevos traen traducción."], 14)
pie(s, "Números de Carlos: resultados/eval_extrinseca.csv (Opus-MT opus-mt-es-en y NLLB nllb-200-distilled-600M). Depende del glosario: un sinónimo correcto que no esté en él cuenta como error. "
       "Resultado final de las corridas nuevas en el informe.")

if BASE:
    # Deck de la entrega final: se conservan título, resumen, graphical abstract, diseño (8), efecto del diccionario (9),
    # conclusiones (13) y limitaciones (14); el glosario (3) pasa al final. Las diapositivas de datos (4 a 7) y de resultados
    # (10 a 12) se reemplazan por las nuevas: datos con fuentes, resultados con gráficos, procedencia y lo que se espera.
    lista = prs.slides._sldIdLst
    originales, nuevas = list(lista)[:N0], list(lista)[N0:]
    datos, ref_graficos, extrinseca, procedencia, esperado = nuevas[0], nuevas[9], nuevas[10], nuevas[7], nuevas[8]
    conservadas = [datos, ref_graficos, extrinseca, procedencia, esperado]
    for el in originales[4:8] + originales[10:13] + [e for e in nuevas if e not in conservadas]:
        prs.part.drop_rel(el.rId)
        lista.remove(el)
    orden = originales[0:3] + [datos, originales[8], originales[9], ref_graficos, extrinseca,
                               originales[13], originales[14], esperado, procedencia, originales[3]]
    for el in orden:
        lista.remove(el)
        lista.append(el)
if BASE:
    # Glosario: se agrega «Diccionario unificado» (después de «Diccionario curado») y se baja la letra para que quepa
    import copy
    for diapo in prs.slides:
        titulos = [sh.text_frame.text for sh in diapo.shapes if sh.has_text_frame]
        if "Glosario: las palabras del proyecto" not in titulos:
            continue
        cajas = [sh for sh in diapo.shapes if sh.has_text_frame and sh.text_frame.text.startswith("Diccionario curado")]
        if cajas:
            tf = cajas[0].text_frame
            nuevo_p = copy.deepcopy(tf.paragraphs[0]._p)
            tf.paragraphs[0]._p.addnext(nuevo_p)
            runs = tf.paragraphs[1].runs
            runs[0].text = "Diccionario unificado: "
            runs[1].text = ("el diccionario curado completo. Junta en un solo archivo la revisión de las 5 secciones (1.985 términos) "
                            "y agrupa las variantes de una palabra, como el verbo y su forma en -se.")
        for sh in diapo.shapes:
            if sh.has_text_frame and sh.text_frame.paragraphs and sh.text_frame.text.startswith(("Diccionario curado", "reglas_curado")):
                for par in sh.text_frame.paragraphs:
                    for r in par.runs:
                        r.font.size = Pt(20)
if BASE:
    # texto que quedó viejo en las diapositivas originales: ya no llegarán más revisiones (solo respondió el integrante 2)
    def _cambiar(shapes, buscado, nuevo):
        for sh in shapes:
            if sh.shape_type == 6:
                _cambiar(sh.shapes, buscado, nuevo)
            elif sh.has_text_frame:
                for par in sh.text_frame.paragraphs:
                    if buscado in "".join(r.text for r in par.runs) and par.runs:
                        par.runs[0].text = "".join(r.text for r in par.runs).replace(buscado, nuevo)
                        for r in par.runs[1:]:
                            r.text = ""
    for diapo in prs.slides:
        _cambiar(diapo.shapes, "Si llegan los otros 3 Excel, se recalcula; si no, queda como limitación.",
                 "No llegarán más revisiones: queda como limitación y el resultado es preliminar.")
prs.save(SALIDA)
print("ok", len(prs.slides._sldIdLst), "diapositivas ->", SALIDA)
