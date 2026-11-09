# Proyecto NLP: Chilenismos

## Objetivo

Traducir oraciones con jerga chilena (*«el carrete estuvo fome»*) a español neutro (*«la fiesta estuvo aburrida»*), y medir qué enfoque lo hace mejor.
Proyecto del curso de PLN (UC Chile).

Este README explica los **tres sistemas** que hay en el repo y cómo se comparan. Cada uno tiene su propio detalle:

| Documento | De qué trata |
|---|---|
| **este README** | Visión general: los tres sistemas, qué tienen de parecido y de diferente, resultados y qué falta |
| [`README_flo.md`](README_flo.md) | Sistema B: el diccionario revisado a mano, sus columnas y cómo se integra con el código del equipo |
| [`idea_flo/README.md`](idea_flo/README.md) | Sistema C: el plan de datos original (oraciones, borrador con LLM, revisión humana, partición) y los baselines con LLM |

## Los tres sistemas

Los tres se evalúan con los **mismos tres conjuntos de pares** (`annotation/lote1.csv` del equipo y los dos lotes de Flo, `lote_1_noticias.csv` y `lote_1_tuits.csv`) para poder compararlos. Cada uno de los tres se corre en una o más variantes, así que en total se comparan **8 sistemas** (las filas de `resultados/comparacion_baselines.csv`): identidad; `reglas_equipo` y `reglas_equipo_con_ambiguos` (A); `reglas_flo` y `reglas_flo_con_ambiguos` (B); `llm_zero_shot`, `llm_dicc_flo` y `mt5_flo` (C). Los diagramas muestran las 8 líneas, cada una con su resultado.

![Los 8 sistemas en paralelo](docs/pipelines_1.png)

| Sistema | Qué hace | Estado |
|---|---|---|
| **A. Reglas + diccionario automático (equipo)** | `diccionario.py` baja el Wikcionario (es y en) y arma un diccionario sin revisión; el reemplazo de cada término es la primera frase de su definición. `baselines.py` sustituye con esas reglas (y corre identidad y mT5 sin entrenar). | Hecho y ejecutado. |
| **B. Reglas + diccionario revisado (Flo)** | El mismo código que A, pero con un diccionario revisado a mano: se decidió qué términos entran, se corrigieron las definiciones y se validó un reemplazo por sentido. Detalle en [`README_flo.md`](README_flo.md). | Hecho y ejecutado, **pero solo para el libro 1 de 5** (ver «Pendiente de revisar»). |
| **C. LLM + diccionario revisado (idea de Flo)** | No usa reglas: le entrega al LLM la oración y los términos del diccionario revisado que aparecen en ella. Además arma sus propios pares (oraciones del corpus → borrador con LLM) y con ellos ajusta mT5. Detalle en [`idea_flo/README.md`](idea_flo/README.md). | Baselines con LLM hechos y ejecutados; pares de entrenamiento generados (borrador sin revisar); mT5-small ajustado en la GPU de Flo (`mt5_flo`), que todavía no supera a la identidad. |

### Qué tienen de parecido y de diferente
- **A y B** usan el mismo script (`baselines.py`) y los mismos pares. **Solo cambia el diccionario**: automático en A, revisado a mano en B.
- **B y C** comparten el mismo diccionario revisado.
- **C** es la única que no usa reglas fijas (el LLM decide según el contexto) y la única que arma sus propios pares.
- **Los tres** terminan en el mismo archivo de resultados.

### Qué archivos entran y salen de cada paso

![Archivos involucrados](docs/pipelines_3.png)

### Cómo se llegó al diccionario revisado (sistema B)

![Cómo se hizo el diccionario revisado](docs/pipelines_2.png)

Los diagramas se pueden editar con [draw.io](https://app.diagrams.net) abriendo `docs/pipelines.drawio` (tiene las tres páginas).

## Organización del repo

```
proyecto-nlp/
├── README.md                 este documento: visión general de los tres sistemas
├── README_flo.md             sistema B: el diccionario revisado
├── requirements.txt
├── src/chilenismos/          código del equipo (sistemas A y B)
│   ├── diccionario.py        baja Wikcionario es + en y arma data/processed/diccionario.csv
│   ├── baselines.py          identidad, reglas y mT5; elige el diccionario con ESCENARIO
│   ├── baseline_mt.py, baseline_nllb.py    traductores genéricos (Opus-MT y NLLB), ida y vuelta por inglés
│   ├── dicc.py               carga un diccionario (equipo o Flo) y arma las reglas
│   └── tabla.py              arma la tabla con una columna por conjunto de pares
├── idea_flo/                 sistema C: LLM + plan de datos (ver idea_flo/README.md)
│   ├── llm.py, baselines_llm.py
│   └── oraciones.py, borrador.py, entrenar_mt5.py
├── annotation/               los tres conjuntos de pares y su README
│   ├── lote1.csv             213 pares del equipo
│   └── lote_1_noticias.csv, lote_1_tuits.csv    72 y 165 pares revisados por Flo
├── data/
│   ├── curado/               diccionario revisado: diccionario_flo_parte1.csv y términos descartados
│   ├── diccionario/          el trabajo previo de Flo (ver abajo)
│   ├── raw/, interim/, processed/   salidas de los scripts; no se suben a git
├── resultados/
│   ├── comparacion_baselines.csv    BLEU y chrF de cada sistema y conjunto
│   └── tabla_por_conjunto.md/.csv   la misma tabla, una columna por conjunto
├── docs/                     informe_interno.md y diagramas (pipelines.drawio y sus PNG)
└── configs/, models/, notebooks/, reports/, tests/    vacías por ahora (.gitkeep)
```

El trabajo previo de revisión tiene esta estructura. En el repo solo están `terminos.csv`, las acepciones, `roman_entradas.jsonl` y el resumen por regla; **el resto no se subió: lo tiene solo Flo** (en `PLN/Proyecto/archivos_fuera_del_repo/data/diccionario/`):

```
data/diccionario/
├── crudo/                    descargas en bruto: Wikcionario (es), kaikki.org (en) y Román
├── procesado/                términos unidos, acepciones, planillas variantes_parte*.xlsx
│   ├── revision/             los 5 libros por frecuencia y lo ya revisado del libro 1
│   ├── informes/             registros de lo aplicado
│   └── reemplazadas/         copias de seguridad
└── reglas_medicion/          medición de las reglas de ortografía (solo el resumen por regla se sube)
```

**Lo que no se sube a git no está en esta carpeta.** Flo lo guarda aparte, en `PLN/Proyecto/archivos_fuera_del_repo/` (misma estructura que el repo): los Excel y planillas de `data/diccionario/` (traen ejemplos de tuits), `crudo/` (descargas en bruto y texto de artículos con derechos de autor), `informes/`, `reemplazadas/`, `revision/` (los 5 libros), los intermedios `es_acepciones.jsonl` y `terminos.jsonl`, las listas de `reglas_medicion/`, y los Excel de revisión de los lotes. `annotation/lote_1_tuits.csv` **sí está en la carpeta del repo**, pero `.gitignore` lo excluye y no se sube. Ningún sistema de este repo lee `data/diccionario/`: es el respaldo del trabajo previo de revisión.

## Resultados hasta ahora

BLEU / chrF de cada sistema en los tres conjuntos de pares (`resultados/comparacion_baselines.csv`; la tabla ancha está en `resultados/tabla_por_conjunto.md`). **Todos se miden sobre texto limpio**: se quitaron los `@usuario` y los emojis de las oraciones y de las referencias, para todos los sistemas. Los resultados con el texto original quedaron en `resultados/comparacion_baselines_texto_original.csv`.

| Sistema | lote1.csv (213 pares) | lote_1_noticias.csv (72) | lote_1_tuits.csv (165) |
|---|---|---|---|
| Identidad (no cambia nada) | 85,7 / 88,9 | 94,0 / 95,2 | 82,7 / 85,8 |
| **A.** Reglas con el diccionario automático (`reglas_equipo`) | 84,1 / 87,9 | 91,2 / 93,7 | 81,3 / 85,6 |
| **A.** … incluyendo ambiguos (`reglas_equipo_con_ambiguos`) | 84,1 / 87,9 | 91,2 / 93,7 | 81,3 / 85,6 |
| **B.** Reglas con el diccionario revisado (`reglas_flo`) | 89,6 / 92,1 | 94,8 / 96,3 | 86,1 / 89,3 |
| **B.** … incluyendo ambiguos (`reglas_flo_con_ambiguos`) | 88,5 / 91,2 | 90,6 / 94,4 | 83,5 / 88,9 |
| **C.** LLM zero-shot (`llm_zero_shot`) | 90,1 / 92,9 | 94,2 / 96,0 | 83,2 / 86,8 |
| **C.** LLM con el diccionario revisado (`llm_dicc_flo`) | **91,1 / 93,6** | **95,7 / 97,3** | **89,4 / 92,6** |
| **C.** mT5-small ajustado con pares propios (`mt5_flo`) | 81,0 / 87,1 | 91,6 / 94,1 | 80,4 / 84,6 |
| mT5-small sin ajustar (`mt5_sin_ajustar`, referencia) | 0,1 / 2,2 | 0,6 / 3,1 | 0,2 / 2,3 |
| Traductor genérico, ida y vuelta por inglés: Opus-MT (`mt_ida_vuelta`, referencia) | 44,5 / 65,1 | 50,0 / 68,8 | 33,9 / 54,6 |
| Traductor genérico, ida y vuelta por inglés: NLLB (`nllb_ida_vuelta`, referencia) | 38,5 / 60,5 | 34,5 / 55,4 | 25,2 / 47,7 |

Cómo leerlo:
- **`llm_dicc_flo` queda primero en los tres conjuntos.** Le siguen `reglas_flo` y `llm_zero_shot`; las reglas del equipo quedan **por debajo de no hacer nada**. Sustituir los ambiguos empeora en los tres. Que `reglas_flo` gane también en `lote1.csv`, que Flo no escribió, es lo que más peso tiene.
- **El diccionario ayuda más donde hay más jerga.** En los tuits `llm_dicc_flo` (89,4) queda 6 puntos de BLEU sobre `llm_zero_shot` (83,2). En las noticias la diferencia es chica porque 42 de los 72 pares (58 %) no cambian (en los tuits, 22 %), así que la identidad ya parte en 94.
- **Los traductores genéricos quedan muy por debajo de la identidad.** Google Translate no se pudo usar (la versión gratuita bloquea las consultas automáticas y la API oficial exige facturación), así que se usaron dos traductores abiertos y gratuitos, Opus-MT y NLLB, con el pivote español → inglés → español (`src/chilenismos/baseline_mt.py` y `baseline_nllb.py`). Reescriben toda la oración y cambian el sentido de la jerga; el informe interno muestra ejemplos.
- **mT5 ajustado todavía no supera a la identidad** (81,0 contra 85,7 en `lote1.csv`; 80,4 contra 82,7 en tuits). Aprendió la tarea (sin ajustar da cerca de 0) pero con 1.500 pares sin revisar y un modelo chico no basta. Mejoró mucho al limpiar las menciones y los emojis y subir de 3 a 8 épocas (de 66 a 81 de BLEU en `lote1.csv`). Con más pares y la variante con Mixture of Experts debería acercarse; es lo que falta.
- **Cuidado: posible favoritismo hacia B y C.** Flo revisó las referencias de `lote_1_noticias` y `lote_1_tuits`, y con ese mismo diccionario validó los reemplazos. Por eso `reglas_flo`, `llm_dicc_flo` y `mt5_flo` (cuyos pares de entrenamiento se escribieron con ese diccionario) podrían salir algo favorecidos en esos dos conjuntos. Se corregirá con **otro revisor** en el futuro. `lote1.csv` no lo escribió Flo, y ahí también gana B sobre A.
- **Tamaño.** Son muestras chicas (72 y 165 pares revisados por una sola persona); las diferencias de décimas no son concluyentes.
- **Los reemplazos del diccionario automático** salen de la primera frase de la definición y varios quedan mal (*buena onda* → «expresión de saludo»). Con el diccionario revisado, 76 de 117 sustituciones coinciden con la referencia; con el automático, 12 de 95.
- **Los términos ambiguos** (*andar*, *pesado*, *once*) no se sustituyen por defecto: hacerlo empeora el resultado.
- **LLM:** las filas `llm_*` usan el modelo de Claude Code (backend `claude-code`), anotado en la columna `nota`. Si las referencias de `lote1.csv` también las redactó un LLM, esto puede favorecerlo. Conviene comprobar cómo se generaron.

## Pendiente de revisar

Esto es trabajo de revisión humana que **todavía no se hace**:

- **Libros 2 a 5 del diccionario.** Solo el libro 1 (las ~650 filas más frecuentes) está revisado. Las ~2.600 filas restantes están en `archivos_fuera_del_repo/data/diccionario/procesado/revision/revision_2_de_5.xlsx` … `revision_5_de_5.xlsx` y siguen sin decisión (sí / no), sin definiciones corregidas y sin reemplazos. Mientras tanto, **los sistemas B y C solo conocen los términos del libro 1**: en el diccionario que se extrajo se separó en 5 partes por frecuencia en los tuits y se revisó la primera (la de mayor frecuencia); **faltan por revisar las otras cuatro**. La idea es revisarlos solo si los resultados muestran que vale la pena (retorno decreciente: son los menos frecuentes).
- **Segundo revisor de los dos lotes de Flo** (`lote_1_noticias.csv`, 72 pares usados, y `lote_1_tuits.csv`, 165). Los revisó solo Flo, y es la misma persona que validó los reemplazos del diccionario; ver «Cómo leerlo» arriba. Otro revisor, sin ver las decisiones de Flo, lo resuelve.
- **Faltan palabras por revisar (lotes de pares).** Los lotes se armaron con los 100 términos más frecuentes del diccionario, y el diccionario se dividió en 5 libros por frecuencia en los tuits; solo está revisado el primero. Los términos de los libros 2 a 5 no tienen pares ni se miden.
- **Pares de entrenamiento.** Son borradores del LLM sin revisión humana (datos plata); si el ajuste de mT5 rinde bien, conviene que alguien revise una muestra. Se decidió empezar con **un solo revisor** para los pares de prueba y declararlo como limitación.
- **Reemplazos de los términos de los libros 2 a 5** y revisión de sus definiciones, que dependen del punto anterior.

## Qué más falta
- La variante con Mixture of Experts (la idea del *graphical abstract*) y más pares de entrenamiento para mT5: hoy `mt5_flo` usa 1.500 y no supera a la identidad.
- BERTScore y evaluación humana.

## Cómo correr

```
pip install -r requirements.txt
python src/chilenismos/diccionario.py                                   # crea data/processed/diccionario.csv (sistema A)

# los sistemas sobre los tres conjuntos de pares (todos con texto limpio)
P="annotation/lote1.csv annotation/lote_1_noticias.csv annotation/lote_1_tuits.csv"
python src/chilenismos/baselines.py     --escenario ambos --sin-mt5 --pares $P --resumen resultados/comparacion_baselines.csv
python src/chilenismos/baselines.py     --escenario ambos --sin-mt5 --incluir-ambiguos --pares $P --resumen resultados/comparacion_baselines.csv
python idea_flo/baselines_llm.py        --pares $P --resumen resultados/comparacion_baselines.csv   # sistema C
python idea_flo/entrenar_mt5.py --resumen resultados/comparacion_baselines.csv   # mT5-small en la GPU (necesita torch con CUDA y data/interim/borrador_entrenamiento.csv)
python src/chilenismos/baseline_mt.py   --resumen resultados/comparacion_baselines.csv   # traductor genérico (Opus-MT), en la GPU
python src/chilenismos/baseline_nllb.py --resumen resultados/comparacion_baselines.csv   # traductor genérico (NLLB), en la GPU
python src/chilenismos/tabla.py         # tabla con una columna por conjunto: resultados/tabla_por_conjunto.md
```

La variable `ESCENARIO` de `baselines.py` (o `--escenario equipo|flo|ambos`) elige con qué diccionario se corren las reglas.

## Licencias y datos
Wikcionario y Wiktionary son CC BY-SA, así que el diccionario derivado se publica con la misma licencia. Román (1901–1918) es dominio público.
El *Chilean Spanish Corpus* es CC-BY-SA-4.0 y no se redistribuye. No se suben tuits al repo: `annotation/lote_1_tuits.csv` **sí se sube** (decisión de Flo: el repo es de trabajo interno; Flo lo revisó y no hay nombres ni datos personales; menciones cambiadas por `@usuario`, sin links). Los Excel se guardan fuera del repo. Nota: el repo de GitHub es público; si eso cambia, conviene reconsiderarlo. Las claves de API van siempre en variables de entorno.
