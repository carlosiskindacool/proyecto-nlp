# annotation: pares chileno → neutro para anotar

Aquí viven los **pares** (oración con jerga y su versión en español neutro) con que se evalúan y se entrenan los sistemas.
Visión general del proyecto: [`../README.md`](../README.md). Cómo se generaron los lotes: [`../archivo/idea_flo/README.md`](../archivo/idea_flo/README.md).

## Archivos

| Archivo | Qué es | ¿Se sube a git? |
|---|---|---|
| `lote1.csv` | Primer lote del equipo: 213 pares, 96 términos. Con él se evalúan los sistemas (ver [`../resultados/`](../resultados/)). No se sabe de qué fuente salen las oraciones ni cómo se escribió la versión neutra (probablemente un modelo). | Sí |
| `lote_1_noticias.csv` | Lote 1 generado con el plan de Flo, con oraciones de **noticias**. El borrador neutro lo propuso un LLM y lo revisó Flo (72 pares usados, 21 descartados). | Sí |
| `lote_1_tuits.csv` | Lote 1 generado con oraciones de **tuits**. El borrador neutro lo propuso un LLM y lo revisó Flo (165 pares usados, 29 descartados). | Sí (ver «Tuits») |
| `lote_2_noticias.csv`, `lote_2_tuits.csv`, `lote_2.csv` | 150 pares nuevos (148 usables) de palabras que no estaban en el lote 1: 145 de tuits y 5 de noticias. Borrador de `claude-sonnet-5-5`, revisado por Flo. | Los de tuits **no** (ver «Tuits») |
| `lote_1_2_noticias.csv`, `lote_1_2_tuits.csv` | El lote 1 más el lote nuevo: 98 y 339 pares (77 y 308 usables). | Los de tuits **no** (ver «Tuits») |
| `revision_lote_1_noticias.xlsx`, `revision_lote_1_tuits.xlsx` | El mismo contenido en Excel, para revisar cómodamente (ver «Cómo se revisa un par»). | **No** |

## Formato

Los archivos del plan de Flo son CSV con separador `;` y estas columnas:

| Columna | Contenido |
|---|---|
| `termino` | El término del diccionario revisado que aparece en la oración |
| `oracion` | La oración original, con jerga |
| `neutro` | Su versión en español neutro. **Es un borrador del LLM hasta que una persona lo revise** |
| `revisor1` | Nombre de quien revisó el par (vacío = sin revisar) |

`lote1.csv` solo trae `termino;oracion;neutro`.

## Cómo se revisa un par

Se revisa en el Excel `revision_lote_1_<fuente>.xlsx`, que trae por cada par el borrador del LLM y la definición y el reemplazo del diccionario para ayudar a decidir. En la columna **`decision`**:

- **`ok`**: la oración usa el sentido chileno y el borrador está bien. Se queda como está.
- **`corregir`**: el sentido es chileno pero el borrador falla. Escribe la versión correcta en `neutro_corregido`. Debe **cambiar solo la jerga** y conservar el resto de la oración, y concordar en género y número.
- **`descartar`**: no sirve (sentido estándar, nombre propio, texto sin sentido, solo menciones). Por ejemplo, *Colonia* la ciudad no cuenta; *colonia* de perfume sí.

Después, el Excel se pasa al CSV: `ok` conserva el borrador, `corregir` usa `neutro_corregido`, `descartar` deja `DESCARTAR` en `neutro`, y `revisor1` queda con el nombre de quien revisó. **Los sistemas solo evalúan con los pares que tienen `revisor1` y no están descartados**; mientras un lote esté sin revisar, `baselines.py` se niega a usarlo.

Se revisa con **un solo revisor**. Hay que declararlo en el informe como limitación (ver el `README.md` de la raíz).

## Tuits


Aun así, **`lote_1_tuits.csv` se sube al repo**: es una decisión de Flo (el repo es de trabajo interno) y Flo lo revisó y no encontró nombres ni datos personales. Ojo: el repo de GitHub es público. Los Excel de revisión Flo los guarda fuera del repo, en `PLN/Proyecto/archivos_fuera_del_repo/annotation/`. En ese archivo las menciones (`@nombre`) se reemplazan por `@usuario` y se quitan los links, pero igual puede haber nombres u otros datos personales dentro del texto.
No subas pares con texto de tuits hasta tener esa respuesta.

## Cómo se generaron

```
python idea_flo/oraciones.py --corpus RUTA/AL/CORPUS --escenario flo --fuentes news    --terminos 100 --max-por-termino 2 --out data/interim/candidatas_noticias.csv
python idea_flo/oraciones.py --corpus RUTA/AL/CORPUS --escenario flo --fuentes twitter --terminos 100 --max-por-termino 2 --out data/interim/candidatas_tuits.csv
python idea_flo/borrador.py --entrada data/interim/candidatas_noticias.csv --salida annotation/lote_1_noticias.csv
python idea_flo/borrador.py --entrada data/interim/candidatas_tuits.csv    --salida annotation/lote_1_tuits.csv
```

**Lote 2 (24-nov-2026, 150 pares, tuits y noticias):** términos nuevos repartidos por frecuencia (50 alta, 50 media, 50 media-baja; un par por término, sin repetir los de los lotes anteriores). Borradores con `claude-sonnet-5-5`.

```
python idea_flo/oraciones.py --corpus RUTA/AL/CORPUS --escenario flo --fuentes news --incluir-tuits --max-por-termino 6 --out data/interim/candidatas_lote2.csv
python idea_flo/seleccionar_lote.py --candidatas data/interim/candidatas_lote2.csv --excluir annotation/lote_1_tuits.csv annotation/lote_1_noticias.csv annotation/lote1.csv --por-nivel 50 --out data/interim/seleccion_lote2.csv
python idea_flo/borrador.py --entrada data/interim/seleccion_lote2.csv --backend claude-code --modelo claude-sonnet-5-5 --salida data/interim/borrador_lote2.csv
python idea_flo/revision_excel.py crear --borrador data/interim/borrador_lote2.csv --seleccion data/interim/seleccion_lote2.csv --salida revision_lote_2.xlsx
# después de revisar: Excel -> CSV que leen los sistemas (revisor1 queda con el nombre)
python idea_flo/revision_excel.py a-csv --excel revision_lote_2.xlsx --salida annotation/lote_2.csv --revisor Flo
```

Flo revisó los 150 pares (129 `ok`, 19 `corregir`, 2 `descartar`). El lote 2 se separó por fuente en `lote_2_tuits.csv` (145 pares) y `lote_2_noticias.csv` (5 pares), y se combinó con el lote 1 en `lote_1_2_tuits.csv` (339 pares, 308 usables) y `lote_1_2_noticias.csv` (98 pares, 77 usables). `lote1.csv` no se mezcla porque se desconoce quién escribió su versión neutra. `lote_2.csv` y los archivos `lote_2_*` traen texto de tuits: no se suben a git sin que Flo lo decida.

Los lotes 1 salieron de los 100 términos más frecuentes del diccionario revisado (sin especies) y hasta 2 oraciones por término. Las noticias traen poca jerga: de los 100 términos, solo 51 aparecen en ellas.

## Concordancia entre revisores

Para saber cuánto coinciden las personas, 237 pares de `lote_1_tuits.csv` y `lote_1_noticias.csv` (180 de tuits y 57 de noticias, muestra al azar con semilla fija) los revisan además cuatro integrantes del equipo, **a ciegas**: cada par lo ve Flo (su decisión ya existente) y 2 de los 4 integrantes. Las 6 parejas posibles (2-3, 2-4, 2-5, 3-4, 3-5 y 4-5) ven unos 40 pares cada una, y cada integrante revisa unos 120. El diseño tolera que un integrante no entregue: sus pares quedan con 2 votos en lugar de 3 y el análisis sigue con los demás.

- Los Excel `revision_concordancia_integrante{2,3,4,5}.xlsx` y la clave `clave_concordancia.csv` **no se suben**: traen texto de tuits y las decisiones de Flo. Están en `PLN/Proyecto/archivos_fuera_del_repo/annotation/`.
- El script `concordancia.py` (no está en el repo: Flo lo guarda junto a los Excel, en `archivos_fuera_del_repo/annotation/`) calcula el **alfa de Krippendorff** (global, admite que cada par lo vean distintas personas), el **kappa de Cohen** entre cada pareja con intervalo bootstrap, el % de acuerdo, la matriz de confusión y el acuerdo en el texto corregido (igual exacto y chrF). `python concordancia.py --autoprueba` valida las fórmulas con datos simulados (alfa 1 con acuerdo perfecto y cerca de 0 con azar, también con huecos).
- Limitaciones para el informe: pocas revisiones por pareja (~40), por lo que los intervalos son amplios; la muestra es proporcional (hay pocos «corregir» y «descartar»); la decisión de Flo se tomó antes y con el contexto completo del proyecto.
- Flo revisa aparte `lote1.csv` (213 pares sin revisor) en `revision_lote1_flo.xlsx`, para ampliar el conjunto de prueba. Esos pares no entran al cálculo de concordancia porque los ve una sola persona.
- **Resultado final (24-nov-2026):** solo entregó su Excel el integrante 2 (120 pares). Acuerdo con Flo 72 %, kappa de Cohen 0,04 (IC 95 %: −0,06 a 0,16) y alfa de Krippendorff 0,01. Marcó `ok` en 111 de 120 pares y Flo en unos 90; el desacuerdo está en `descartar` (palabras en uso estándar). **No llegarán más revisiones**, así que el estudio queda con una sola pareja de revisores: se declara como limitación y el resultado es preliminar.

## Qué modelo se usó (registro)

Hay que citar el modelo en el informe. Todo lo que Flo hizo con un LLM se hizo con **`claude-sonnet-5-5`** (Claude, vía Claude Code); así lo confirma Flo, que siempre usa ese modelo, y las sesiones de trabajo registran el mismo ID.

| Uso | Modelo | Cómo se llamó |
|---|---|---|
| Borrador neutro de `lote_1_noticias.csv` y `lote_1_tuits.csv` (`borrador.py`, 8-nov-2026) | `claude-sonnet-5-5` | CLI de Claude Code (`--backend claude-code`); el código no fija `--modelo`, usa el de la cuenta de Flo |
| Borrador de entrenamiento (`data/interim/borrador_entrenamiento.csv`) y baselines C (`baselines_llm.py`) | `claude-sonnet-5-5` | Igual |
| Propuestas de Claude sobre el diccionario (decisiones, definiciones, reemplazos), 23-24 nov 2026 | `claude-sonnet-5-5` | Claude Code |
| `lote1.csv` | Desconocido (no se sabe quién ni cómo lo escribió) | – |

El ID no quedó guardado en ningún archivo de salida, solo en esta nota: para las próximas corridas conviene pasar `--modelo claude-sonnet-5-5` y anotar aquí la fecha. Si se usa a Claude como anotador de los pares, hay que registrar su ID y la fecha, y que no vio las decisiones de las personas.

### Otros LLM como generadores de borradores (24-nov-2026)

Para saber si otro modelo puede escribir los borradores, tres modelos tradujeron los 200 pares válidos de la concordancia (los que Flo dejó `ok` o `corregir`) con el mismo prompt, el mismo diccionario como contexto y temperatura 0. Flo revisó los borradores **a ciegas y mezclados** (`ok` / `corregir` / `descartar`). Un borrador idéntico a la versión final ya aceptada cuenta como `ok` sin revisar.

| Letra | Backend | Modelo (ID exacto) | Fecha | Notas |
|---|---|---|---|---|
| A | `gemini` | `gemini-3.5-flash-lite` | 24-nov-2026 | Los modelos `gemini-3.5-flash`, `3.7-flash`, `3.8-flash` y `flash-latest` fallaron por sobrecarga (503 / tiempo agotado); `gemini-2.5-*` ya no está disponible para cuentas nuevas |
| B | `ollama` (local, CPU) | `llama3.1:8b` | 24-nov-2026 | `llama3.2:3b` falló en una prueba (8 de 20 respuestas vacías) y se descartó |
| C | `openai` | `gpt-4.1-2025-04-14` | no se ejecutó | La cuenta no tenía crédito (HTTP 429) |
| D | `claude-code` | `claude-haiku-5-5` | 24-nov-2026 | |
| Referencia | `claude-code` | `claude-sonnet-5-5` | 8-nov-2026 | Origen de los borradores originales revisados por Flo |

Resultados (`ok` = borrador idéntico a la versión final o marcado `ok`; solo sobre los pares que Flo revisó):

| Modelo | `ok` | IC 95 % (Wilson) | `corregir` | `descartar` o vacío | Pares revisados |
|---|---|---|---|---|---|
| Haiku 5.5 (D) | 85,0 % | 78,8 a 89,6 | 22 | 3 | 167 de 200 |
| Gemini 3.5 flash-lite (A) | 82,9 % | 76,6 a 87,9 | 25 | 4 | 170 de 200 |
| Llama 3.1 8B (B) | 40,2 % | 31,9 a 49,0 | 36 | 18 + 19 vacíos | 122 de 200 |
| Sonnet 5.5 (referencia, otra medición) | 80,8 % | – | – | – | 234 |

- **Haiku y Gemini no se distinguen:** McNemar sobre los pares revisados por ambos da p = 1,0 (11 pares donde solo acierta Gemini y 12 donde solo acierta Haiku). Con `ok` + `corregir` (el borrador sirve) los dos llegan a ~98 %. chrF contra la versión final: Gemini 93,2, Haiku 91,3.
- **Llama 8B queda descartado:** solo el 70 % de sus borradores sirven (`ok` + `corregir`), 19 respuestas vinieron vacías y 10 devolvieron el prompt en lugar de traducir (chrF 77,0). Flo dejó de revisar sus filas: 74 filas exclusivas de Llama quedaron sin revisar, así que su cifra sale de una muestra al azar de 122 pares, sin intervalos finos.
- **Sin revisar:** 61 filas del Excel único quedaron sin revisar (Gemini 30, Haiku 33 y Llama 78 de los 200 pares, con filas compartidas). Las tasas se calculan solo sobre lo revisado; en el peor y el mejor caso (todo lo no revisado fracasa o acierta) Haiku va de 71,0 a 87,5 % y Gemini de 70,5 a 85,5 %.
- **Límites:** (1) la versión final salió del borrador de Sonnet, así que Haiku (misma familia) parte con ventaja; (2) los 200 pares excluyen los que Flo descartó de Sonnet, lo que también lo favorece; (3) Flo es la única revisora; (4) las filas con texto corregido pero sin decisión marcada se contaron como `corregir`, y las vacías dentro de un bloque ya revisado como `ok`; (5) los borradores idénticos a la oración original se contaron como `ok` (según Flo, esas oraciones no debían traducirse).
- **Archivos** (fuera del repo, traen texto de tuits): `modelos/borradores_{A,B,D}.json`, `modelos/decisiones_ya_resueltas.json` (decisiones y notas de Flo), `modelos/resultado_por_par_y_modelo.json` y `modelos/clave_revision_todos.json` (qué modelo escribió cada fila).
