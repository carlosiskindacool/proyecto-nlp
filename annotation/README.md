# annotation: pares chileno → neutro para anotar

Aquí viven los **pares** (oración con jerga y su versión en español neutro) con que se evalúan y se entrenan los sistemas.
Visión general del proyecto: [`../README.md`](../README.md). Cómo se generan los lotes: [`../idea_flo/README.md`](../idea_flo/README.md).

## Archivos

| Archivo | Qué es | ¿Se sube a git? |
|---|---|---|
| `lote1.csv` | Primer lote del equipo: 213 pares, 96 términos. Con él se comparan los 8 sistemas de [`../resultados/`](../resultados/comparacion_baselines.csv). No se sabe de qué fuente salen las oraciones ni cómo se escribió la versión neutra (probablemente un modelo). | Sí |
| `lote_1_noticias.csv` | Lote 1 generado con el plan de Flo, con oraciones de **noticias**. El borrador neutro lo propuso un LLM y lo revisó Flo (72 pares usados, 21 descartados). | Sí |
| `lote_1_tuits.csv` | Lote 1 generado con oraciones de **tuits**. El borrador neutro lo propuso un LLM y lo revisó Flo (165 pares usados, 29 descartados). | **No** (ver «Tuits») |
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

Son los 100 términos más frecuentes del diccionario revisado (sin especies) y hasta 2 oraciones por término. Las noticias traen poca jerga: de los 100 términos, solo 51 aparecen en ellas.

## Concordancia entre revisores

Para saber cuánto coinciden las personas, 237 pares de `lote_1_tuits.csv` y `lote_1_noticias.csv` (180 de tuits y 57 de noticias, muestra al azar con semilla fija) los revisan además cuatro integrantes del equipo, **a ciegas**: cada par lo ve Flo (su decisión ya existente) y 2 de los 4 integrantes. Las 6 parejas posibles (2-3, 2-4, 2-5, 3-4, 3-5 y 4-5) ven unos 40 pares cada una, y cada integrante revisa unos 120. El diseño tolera que un integrante no entregue: sus pares quedan con 2 votos en lugar de 3 y el análisis sigue con los demás.

- Los Excel `revision_concordancia_integrante{2,3,4,5}.xlsx` y la clave `clave_concordancia.csv` **no se suben**: traen texto de tuits y las decisiones de Flo. Están en `PLN/Proyecto/archivos_fuera_del_repo/annotation/`.
- El script `concordancia.py` (no está en el repo: Flo lo guarda junto a los Excel, en `archivos_fuera_del_repo/annotation/`) calcula el **alfa de Krippendorff** (global, admite que cada par lo vean distintas personas), el **kappa de Cohen** entre cada pareja con intervalo bootstrap, el % de acuerdo, la matriz de confusión y el acuerdo en el texto corregido (igual exacto y chrF). `python concordancia.py --autoprueba` valida las fórmulas con datos simulados (alfa 1 con acuerdo perfecto y cerca de 0 con azar, también con huecos).
- Limitaciones para el informe: pocas revisiones por pareja (~40), por lo que los intervalos son amplios; la muestra es proporcional (hay pocos «corregir» y «descartar»); la decisión de Flo se tomó antes y con el contexto completo del proyecto.
- Flo revisa aparte `lote1.csv` (213 pares sin revisor) en `revision_lote1_flo.xlsx`, para ampliar el conjunto de prueba. Esos pares no entran al cálculo de concordancia porque los ve una sola persona.

## Qué modelo se usó (registro)

Hay que citar el modelo en el informe. Todo lo que Flo hizo con un LLM se hizo con **`claude-sonnet-5-5`** (Claude, vía Claude Code); así lo confirma Flo, que siempre usa ese modelo, y las sesiones de trabajo registran el mismo ID.

| Uso | Modelo | Cómo se llamó |
|---|---|---|
| Borrador neutro de `lote_1_noticias.csv` y `lote_1_tuits.csv` (`borrador.py`, 8-nov-2026) | `claude-sonnet-5-5` | CLI de Claude Code (`--backend claude-code`); el código no fija `--modelo`, usa el de la cuenta de Flo |
| Borrador de entrenamiento (`data/interim/borrador_entrenamiento.csv`) y baselines C (`baselines_llm.py`) | `claude-sonnet-5-5` | Igual |
| Propuestas de Claude sobre el diccionario (decisiones, definiciones, reemplazos), 23-24 nov 2026 | `claude-sonnet-5-5` | Claude Code |
| `lote1.csv` | Desconocido (no se sabe quién ni cómo lo escribió) | – |

El ID no quedó guardado en ningún archivo de salida, solo en esta nota: para las próximas corridas conviene pasar `--modelo claude-sonnet-5-5` y anotar aquí la fecha. Si se usa a Claude como anotador de los pares, hay que registrar su ID y la fecha, y que no vio las decisiones de las personas.
