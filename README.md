# Proyecto NLP: chilenismos → español neutro

Normalizador que pasa oraciones con jerga chilena (*«el carrete estuvo fome»*) a español neutro (*«la fiesta estuvo aburrida»*), y medición de qué enfoque lo hace mejor. Proyecto del curso de PLN (UC Chile).

Se comparan cinco sistemas sobre los mismos conjuntos de pares anotados: tres de la etapa original y, desde el 24-nov-2026, dos más (`lote_1_2_noticias.csv` y `lote_1_2_tuits.csv`) que suman 148 pares de palabras nuevas del diccionario:

| Sistema | Qué hace |
|---|---|
| `identidad` | No cambia nada. Es el piso: un sistema útil debe superarlo. |
| `reglas_equipo` | Reemplaza cada chilenismo según el diccionario automático (Wikcionario, sin revisión). |
| `reglas_flo` | Lo mismo, con el diccionario revisado a mano por Flo. |
| `mt5` | `google/mt5-small` ajustado con 1.500 pares (columna `mt5_flo_fp32`). |
| `mt5_moe` | El mismo mT5 convertido en mezcla de expertos (MoE) y ajustado igual (columna `mt5_moe_fp32`). |

Y se evalúan de dos formas:
- **Intrínseca:** ¿la salida se parece a la referencia neutra? ERR, precisión, recall y F1 por palabra, y BLEU y chrF.
- **Extrínseca:** ¿normalizar ayuda a traducir? Se traduce cada salida al inglés y se mide si el chilenismo quedó bien traducido (Exact-Match Accuracy).

## Cómo correr

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

P="annotation/lote1.csv annotation/lote_1_noticias.csv annotation/lote_1_tuits.csv annotation/lote_1_2_noticias.csv annotation/lote_1_2_tuits.csv"
python src/chilenismos/baselines.py --escenario ambos --sin-mt5 --pares $P   # 1. reglas e identidad (segundos)
# 2. en Colab: models/mt5/mt5.ipynb y models/mt5_moe/mt5_moe.ipynb (GPU); copiar sus predicciones a data/processed/
#    o en un computador con GPU, sin Colab: python src/ejecutar_notebook_local.py models/mt5/mt5.ipynb
python src/chilenismos/metricas_normalizador.py                                # 3. métricas intrínsecas (segundos)
HF_HUB_OFFLINE=1 caffeinate -i python src/eval_extrinseca.py                    # 4. traducciones al inglés (~3,5 h)
python src/eval_extrinseca_resumen.py                                          # 5. Exact-Match Accuracy (segundos)
```

**Todas las salidas de los pasos 1, 2 y 4 ya están en git**, así que se puede partir del paso 3 o del 5 sin GPU y sin esperar horas. El paso 4 no hace falta volver a correrlo: si se corrige el glosario, basta con el paso 5.

**Corrida local en cadena (Windows, GPU de 4 GB).** `python src/correr_pipeline_local.py` hace los pasos 2 a 5 uno tras otro y deja los registros en `logs/` (ignorada por git): ejecuta los dos notebooks con [`src/ejecutar_notebook_local.py`](src/ejecutar_notebook_local.py), que corre el mismo código de los notebooks con una carpeta local en lugar de Google Drive. Usa lote 4 (el de Colab es 8; en fp32 no cabe en 4 GB) y, si el MoE se queda sin memoria, reintenta con lote 2. Mantiene el equipo despierto mientras corre. Con `--esperar-borradores` espera a que termine `idea_flo/borrador.py`.

En el paso 4, `caffeinate -i` (solo Mac) evita que el equipo entre en reposo y congele el proceso. `HF_HUB_OFFLINE=1` sirve una vez descargados los modelos: la primera vez hay que correrlo sin esa variable.

## Archivos del pipeline

### Datos fijos (en git, no se regeneran)

| Archivo | Qué es |
|---|---|
| `annotation/lote1.csv` | 213 pares del equipo (`termino;oracion;neutro`). |
| `annotation/lote_1_noticias.csv`, `annotation/lote_1_tuits.csv` | 72 y 165 pares usados, de noticias y tuits, revisados por Flo (columna `revisor1`). Solo cuentan los pares revisados y no descartados. Formato en [`annotation/README.md`](annotation/README.md). |
| `annotation/lote_2_noticias.csv`, `annotation/lote_2_tuits.csv` (y `lote_2.csv`) | 150 pares nuevos (148 usables) de palabras que no estaban en el lote 1: 50 de frecuencia alta, 50 media y 50 media-baja. Casi todos de tuits (145). Revisados por Flo. |
| `annotation/lote_1_2_noticias.csv`, `annotation/lote_1_2_tuits.csv` | El lote 1 más estos pares nuevos: 98 y 339 pares (77 y 308 usables). Son los conjuntos con que se miden los sistemas en la corrida nueva. |
| `data/processed/diccionario.csv` | Diccionario automático del equipo (3.609 términos de Wikcionario; 809 con reemplazo). Lo usa `reglas_equipo`. Se guarda en git porque si se regenera, el Wikcionario puede haber cambiado y `reglas_equipo` daría otros números. |
| `data/curado/diccionario_flo.csv` | Diccionario revisado a mano (1.985 términos: libro 1 y repartos 2 a 5). Lo usa `reglas_flo`. Columnas en [`data/README.md`](data/README.md). |
| `data/interim/borrador_entrenamiento.csv` | Pares chileno → neutro escritos por `claude-sonnet-5-5` y **sin revisión humana**. Solo se usan para entrenar los mT5. Desde el 24-nov tiene 10.521 filas (10.490 pares tras quitar duplicados y las oraciones de prueba: 9.966 para entrenar y 524 para validar); la versión anterior, de 1.500 pares, es la que usó la corrida de Carlos y se guarda como `borrador_entrenamiento_v1.csv`. |
| `data/diccionario/glosario_es_en_test.csv` | Glosario de los términos ancla: `termino;reemplazo_es;acepta_en` (traducciones al inglés aceptadas, separadas por `\|`). Hoy tiene 330 términos: 93 revisados a mano y 237 agregados automáticamente para las palabras nuevas (solo 59 con traducción al inglés; **faltan por revisar**). |

### Scripts y notebooks

| Paso | Archivo | Qué hace | Recibe | Genera |
|---|---|---|---|---|
| 1 | [`src/chilenismos/baselines.py`](src/chilenismos/baselines.py) | Corre `identidad`, `reglas_equipo` y `reglas_flo` en cada lote. Las reglas reemplazan cada término por su equivalente neutro, priorizando las locuciones más largas; los términos marcados como ambiguos no se reemplazan. Antes quita las menciones `@usuario` y los emojis. | Los 3 lotes y los 2 diccionarios | `data/processed/predicciones_<lote>.csv` (una por lote; columnas `chileno`, `neutro`, `termino` y una por sistema) |
| 1 | [`src/chilenismos/dicc.py`](src/chilenismos/dicc.py) | Lee un diccionario y arma las reglas de reemplazo. Lo usa `baselines.py`. | Un diccionario | — |
| 2 | [`models/mt5/mt5.ipynb`](models/mt5/mt5.ipynb) | En Colab (GPU T4): clona este repo, ajusta `google/mt5-small` (8 épocas, Adafactor, fp32) y traduce los 3 lotes. | `data/interim/borrador_entrenamiento.csv` y los 3 lotes (desde GitHub, rama `entrega-final`) | En Drive: pesos en `MyDrive/proyecto-nlp/models/mt5_flo_fp32/` y `predicciones_mt5_flo_fp32.csv` |
| 2 | [`models/mt5_moe/mt5_moe.ipynb`](models/mt5_moe/mt5_moe.ipynb) | Igual, pero antes convierte el mT5 en MoE: cada capa dispersa (una de cada dos) tiene 4 copias de la red densa y cada token pasa por las 2 mejores. Verifica que, antes de entrenar, el MoE genere lo mismo que el modelo denso. | Lo mismo | En Drive: pesos en `MyDrive/proyecto-nlp/models/mt5_moe_fp32/` y `predicciones_mt5_moe_fp32.csv` |
| 3 | [`src/chilenismos/metricas_normalizador.py`](src/chilenismos/metricas_normalizador.py) | Alinea, palabra por palabra, la oración chilena con la referencia y con la salida. Calcula ERR (van der Goot 2019; MultiLexNorm), precisión, recall y F1, y además BLEU y chrF. Compara en minúsculas, sin puntuación y conservando las tildes. | `data/processed/predicciones_*.csv` | `resultados/metricas_normalizador.csv` y `.md` |
| 4 | [`src/eval_extrinseca.py`](src/eval_extrinseca.py) | Traduce al inglés la salida de los 5 sistemas en las 446 oraciones únicas, con dos traductores: Opus-MT y NLLB. | `data/processed/predicciones_*.csv` | `data/processed/eval_extrinseca.csv` (4.460 filas: oración × sistema × traductor) |
| 2 | [`src/ejecutar_notebook_local.py`](src/ejecutar_notebook_local.py) | Ejecuta un notebook de Colab en este computador, sin cambiar su código: reemplaza Google Drive por una carpeta local, omite `!pip` y el clonado del repo. `--set NOMBRE=valor` cambia una constante de la configuración (por ejemplo `LOTE=4`). | Un notebook | Lo mismo que el notebook, en la carpeta indicada, y las predicciones copiadas a `data/processed/` |
| 2 a 5 | [`src/correr_pipeline_local.py`](src/correr_pipeline_local.py) | Encadena los pasos 2 a 5 en este computador (ver «Corrida local en cadena»). | Los datos fijos | `logs/cadena*.log` y las salidas de cada paso |
| 4 | [`src/chilenismos/baseline_mt.py`](src/chilenismos/baseline_mt.py), [`baseline_nllb.py`](src/chilenismos/baseline_nllb.py) | Cargan los traductores (Opus-MT y NLLB). `eval_extrinseca.py` los importa. | — | — |
| 5 | [`src/eval_extrinseca_resumen.py`](src/eval_extrinseca_resumen.py) | Marca cada traducción como acierto si contiene alguna traducción aceptada del término ancla, y resume por sistema, traductor y lote. | `data/processed/eval_extrinseca.csv` y el glosario | `resultados/eval_extrinseca.csv` y `.md`; agrega las columnas `acepta_en` y `exact_match` a `eval_extrinseca.csv` |

Después de los notebooks, hay que descargar las predicciones de Drive, copiarlas a `data/processed/` y subirlas con `git add -f` (`data/processed/` está en `.gitignore`). Son el puente entre la etapa con GPU y las métricas.

## Resultados

**Estado (25-nov-2026).** Los números de abajo son los de la corrida de Carlos: reglas con el diccionario de 1.985 entradas y mT5 y MoE entrenados con 1.500 pares (Colab, T4, fp32, lote 8). Los dos mT5 se están reentrenando con 10.490 pares en la GPU local (lote 4); al terminar, la cadena actualiza `resultados/` y `data/processed/` y estas tablas se rehacen. La versión anterior de los resultados está en `resultados/anterior/`.

**Intrínseca** ([`resultados/metricas_normalizador.md`](resultados/metricas_normalizador.md)). ERR por lote; 0 es no cambiar nada y un valor negativo significa que el sistema estropea más palabras de las que corrige.

| Sistema | lote1 | noticias | tuits |
|---|---:|---:|---:|
| identidad | 0,0 | 0,0 | 0,0 |
| **reglas_flo** | **29,0** | **13,0** | **19,9** |
| reglas_equipo | -7,6 | -54,4 | -3,8 |
| mt5 | -21,8 | -106,5 | -23,7 |
| mt5_moe | -16,2 | -80,4 | -11,8 |

**Extrínseca** ([`resultados/eval_extrinseca.md`](resultados/eval_extrinseca.md)). Exact-Match Accuracy (%) sobre las 446 oraciones.

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 7,0 | 5,6 |
| **reglas_flo** | **23,3** | **20,9** |
| reglas_equipo | 11,0 | 10,1 |
| mt5 | 9,4 | 9,4 |
| mt5_moe | 10,3 | 10,5 |

- Solo `reglas_flo` mejora el español; los mT5 todavía no superan a la identidad, aunque el MoE queda por encima del denso.
- Para traducir, todos ayudan: con `reglas_flo` se traducen bien cerca de 3 veces más chilenismos que sin normalizar.
- **El diccionario completo ayuda en las palabras nuevas.** Sobre los 143 tuits de palabras nuevas (`lote_2_tuits.csv`), el BLEU de las reglas es 86,2 con la identidad, 86,5 con el diccionario del libro 1 (443 entradas) y 88,2 con el completo (1.985). En los conjuntos originales casi no cambia, porque esas palabras ya estaban en el libro 1.

## Procedencia de los datos (no se vuelven a correr)

Estos scripts generaron los datos fijos. Quedan en el repo para documentar de dónde salieron.

| Archivo | Qué generó |
|---|---|
| [`src/chilenismos/diccionario.py`](src/chilenismos/diccionario.py) | `data/processed/diccionario.csv`, descargando el Wikcionario (es y en). |
| [`idea_flo/oraciones.py`](idea_flo/oraciones.py) | Oraciones del *Chilean Spanish Corpus* que contienen términos del diccionario: las de los lotes de Flo, `data/interim/candidatas_entrenamiento.csv` y, para todos los términos del diccionario, `candidatas_lote2.csv` (hasta 6 por término, tuits y noticias). |
| [`idea_flo/seleccionar_lote.py`](idea_flo/seleccionar_lote.py) y [`idea_flo/revision_excel.py`](idea_flo/revision_excel.py) | Eligen las oraciones de un lote nuevo por frecuencia del término (alta, media, media-baja) sin repetir lotes anteriores, arman el Excel de revisión y lo pasan al CSV que leen los sistemas. Se usaron para los 150 pares nuevos; comandos en [`annotation/README.md`](annotation/README.md). |
| [`idea_flo/borrador.py`](idea_flo/borrador.py) y [`idea_flo/llm.py`](idea_flo/llm.py) | La versión neutra propuesta por un LLM para esas oraciones: los lotes de Flo (después revisados) y `borrador_entrenamiento.csv`. Usaron el CLI de Claude Code, sin clave de API; el modelo es `claude-sonnet-5-5`. `borrador.py --hilos N` manda N lotes de 10 oraciones en paralelo (se usó N = 6 para los pares de entrenamiento nuevos). |
| [`src/armar_diapositivas_resultados.py`](src/armar_diapositivas_resultados.py) | Arma las diapositivas de datos, resultados, procedencia y lo que se espera de las corridas nuevas, con los números de `resultados/`. No forma parte del pipeline de medición. |
| [`src/generate_glosario_es_en.py`](src/generate_glosario_es_en.py) | La primera versión del glosario, a partir de `data/diccionario/procesado/en_acepciones_chile.csv` y del diccionario de Flo. Después se revisó a mano; el respaldo de esa revisión es `glosario_es_en_test_revisado.csv`. |

`data/curado/diccionario_flo.csv` salió de la revisión manual de Flo sobre Wikcionario, Wiktionary y el diccionario de Román. `data/diccionario/` guarda parte de ese trabajo previo; las planillas completas las tiene Flo fuera del repo. El origen de `annotation/lote1.csv` no está documentado.

## `archivo/`

Lo que ya no forma parte del pipeline. Se guardó con sus rutas originales (por ejemplo, `archivo/idea_flo/entrenar_mt5.py`) y no se mantiene: algunas rutas internas pueden no funcionar.

| Qué | Por qué se archivó |
|---|---|
| `src/wiktionary_diccionario.py`, `src/generate_annot_template.py`, `src/process_annot_template.py` | Generan el conteo de términos en el corpus y la plantilla de anotación; ninguna de sus salidas se usa más adelante. |
| `src/chilenismos/tabla.py`, `resultados/comparacion_baselines*.csv`, `resultados/tabla_por_conjunto*` | La tabla de BLEU y chrF de la etapa anterior; la reemplazan las métricas actuales. |
| `idea_flo/entrenar_mt5.py`, `models/mt5_flo/` | El primer ajuste de mT5 (en la GPU de Flo); lo reemplaza `models/mt5/mt5.ipynb`. |
| `idea_flo/baselines_llm.py` | Los baselines con LLM (zero-shot y con diccionario) de la etapa anterior. |
| `data/processed/predicciones_mt5_flo.csv`, `predicciones_mt5_sin_ajustar.csv` | Predicciones de ese primer mT5 y del mT5 sin ajustar. |
| `README_flo.md`, `idea_flo/README.md` | Documentación detallada del diccionario revisado y del plan de datos de Flo, con los resultados de la etapa anterior. Lo esencial quedó en este README. |

## Limitaciones

- **Un solo revisor.** Flo revisó los lotes de Flo y también validó los reemplazos del diccionario, así que `reglas_flo` podría salir favorecido en esos lotes. `lote1.csv` no lo escribió Flo, y ahí `reglas_flo` también gana. El único segundo revisor que entregó (integrante 2, 120 pares) coincide en el 72 % con Flo, pero con kappa 0,04: el desacuerdo está en «descartar». No llegarán más revisiones.
- **Reemplazos de Claude.** Del diccionario de 1.985 entradas, los reemplazos de los libros 2 a 5 son en su mayoría propuestas de Claude que Flo validó; los 282 términos ambiguos no se sustituyen.
- **Pares de entrenamiento sin revisar.** Los pares de mT5 (1.500 en la corrida de Carlos, 10.490 en la nueva) son borradores del LLM.
- **Muestras chicas.** En noticias (72 pares) cada oración mueve mucho los porcentajes.
- **Exact match depende del glosario.** Un sinónimo correcto que no esté en `acepta_en` cuenta como error, y una glosa genérica (*to get*) puede coincidir con otra parte de la oración.

## Otras carpetas

- `docs/`: presentación, guion e informe interno, con diagramas de la etapa anterior.
- `logs/`: registros de la corrida local (`cadena*.log`) y la copia del deck base; no se sube (`.gitignore`).
- `configs/`, `notebooks/`, `reports/`, `tests/`: vacías (`.gitkeep`).

## Licencias y datos

Wikcionario y Wiktionary son CC BY-SA, así que los diccionarios derivados se publican con la misma licencia. Román (1901–1918) es dominio público. El *Chilean Spanish Corpus* es CC-BY-SA-4.0 y no se redistribuye. `annotation/lote_1_tuits.csv` está en el repo por decisión de Flo: lo revisó, las menciones van como `@usuario` y no tiene links. Las predicciones y traducciones en `data/processed/` contienen esas mismas oraciones. El repo de GitHub es público. Las claves de API van siempre en variables de entorno.
