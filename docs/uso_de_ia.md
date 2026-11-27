# Uso de IA en el proyecto

**Proyecto:** normalizador de jerga chilena a español neutro (PLN, UC Chile). Este documento declara cómo se usó la IA en cada etapa, qué decidió una persona y qué quedó sin revisión humana. Está escrito a partir de los registros de las sesiones de trabajo con el asistente y de lo que está documentado en `docs/informe_interno.md` (Anexo A) y en `annotation/README.md`.

> **Alcance.** Cubre el trabajo del **integrante 1**, que es quien usó un asistente de IA de forma interactiva y cuyas sesiones están registradas. El trabajo de los integrantes 2 a 5 (por ejemplo, el entrenamiento inicial del mT5 y parte de la revisión del glosario, del integrante 5) está descrito en el informe, pero no tenemos registro de qué herramientas de IA usaron, así que **cada uno debe completar su propio uso de IA en la sección 9**.

## 1. Resumen

| Cómo se usó la IA | Para qué | Quién decidió |
|---|---|---|
| **Asistente de programación y análisis** (Claude Code, `claude-sonnet-5-5`) | Ideación, código, análisis, documentación, diagramas, presentaciones | El integrante 1 aprobó cada paso; nada se aplicó a los datos sin validación |
| **Anotador sobre el diccionario** (mismo modelo) | Proponer decisiones y reemplazos sobre palabras sin revisar | Una persona validó las propuestas antes de aplicarlas |
| **Generador de datos** (Claude, Gemini, Haiku) | Borradores de la versión neutra de cada oración | Una persona revisó los pares de evaluación (`ok` / `corregir` / `descartar`). **Los 10.490 pares de entrenamiento no tienen revisión humana** |
| **Componente del sistema** (mT5, ByT5, Opus-MT, NLLB) | Los modelos que se entrenan y los traductores que miden el efecto | Se entrenaron y se midieron; no son asistentes |
| **Objeto de estudio** (LLM con diccionario, LLM que decide el diccionario) | Medir el «techo» y si un LLM puede reemplazar la revisión humana | Medición con intervalos y análisis de errores |

**Principios que se aplicaron:** (1) la IA propone y una persona valida antes de aplicar; (2) todo lo que hizo un LLM se declara y se distingue de lo hecho por personas; (3) los prompts y las respuestas crudas se guardan en el repo; (4) las claves de API nunca van al repo; (5) los números del informe se verifican contra los archivos de resultados.

## 2. Herramientas y modelos

| Herramienta / modelo | Identificador | Uso |
|---|---|---|
| Claude Code (asistente interactivo) | `claude-sonnet-5-5` | Todo lo que el integrante 1 hizo con un LLM: borradores, baselines, propuestas sobre el diccionario, código, análisis y redacción |
| Claude Haiku | `claude-haiku-5-5` | Generador de borradores (comparación), votante del glosario, LLM con diccionario, piloto |
| Gemini | `gemini-3.5-flash-lite` (API de Google AI Studio) | Generador de borradores (comparación), votante del glosario, LLM con diccionario, piloto |
| Llama | `llama3.1:8b` (Ollama, local) | Generador de borradores (comparación; descartado: 40,2 % de aceptación) |
| Cohere | `command-a-plus-05-2026` | Votante del glosario; piloto |
| Llama 3.3 70B (Cloudflare Workers AI) | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Votante del glosario |
| IBM Granite (watsonx) | `ibm/granite-4-h-small` | Votante del glosario; piloto |
| Nemotron (OpenRouter, gratuito) | `nvidia/nemotron-3-ultra-550b-a55b:free` | Votante del glosario |
| mT5-small, mT5 con MoE, ByT5-small | `google/mt5-small`, `google/byt5-small` | Modelos de normalización que se entrenan |
| Opus-MT y NLLB-200 | `Helsinki-NLP/opus-mt-es-en`, `facebook/nllb-200-distilled-600M` | Traductores al inglés para la evaluación extrínseca |

Los modelos de nube se usaron con temperatura 0 cuando la API lo permite. Lo que no funcionó (Groq, OpenAI sin crédito, GitHub Models, Mistral, DeepSeek, Cloudflare sin cupo, IBM sin cupo el 26-nov) está en el informe (3.4 y 3.5) y no se cuenta como resultado.

## 3. Uso de IA por etapa

### 3.1 Ideación y elección del proyecto (24 al 25 de octubre)

- **Qué se hizo con IA:** el asistente propuso ideas de proyecto y validó, buscando en papers y repositorios, que existieran conjuntos de datos utilizables. Se pidió repetir el proceso hasta tener 10 ideas y luego 10 más distintas, y se armó una tabla (idea, resumen, conjunto de datos, tamaño medido, veredicto), que el asistente exportó a PDF.
- **Qué decidió el equipo:** elegir la idea de los chilenismos (era una idea previa del equipo) entre las candidatas. También se pidió explícitamente buscar ideas «novedosas», no solo relacionadas con Chile.
- **Cómo se definió el diseño:** en conversación se concluyó que el dataset tiene dos partes (el diccionario de términos y el mapeo oración chilena → oración neutra) y por qué se separan entrenamiento, validación y prueba.

### 3.2 Diseño del pipeline y diagramas (25 de octubre; luego 8 de noviembre y 26 de noviembre)

- **Qué se hizo con IA:** rehacer el graphical abstract y el diagrama en draw.io (cajas con subtítulo, colores con significado, en español, sin emojis), citar las fuentes en APA y corregir la parte de datos; más tarde, los tres diagramas de pipelines (`docs/pipelines.drawio`) y su reexportación a PNG.
- **Qué decidió una persona:** el contenido, los nombres de las etapas y los criterios de diseño (por ejemplo, colores por tipo de elemento).

### 3.3 Construcción y limpieza del diccionario (25 de octubre al 7 de noviembre)

- **Descarga y extracción de términos:** el asistente guió paso a paso la descarga del corpus desde Hugging Face y escribió los scripts para extraer los términos de los diccionarios.
- **Reglas de variantes escritas** (por ejemplo `ado → ao`, `ch → sh`): el integrante 1 investigó en la literatura y el asistente ayudó a documentar las reglas como no inventadas por nosotros y las validó contra todos los tuits. Una persona decidió cuáles se conservaban (borrando en el Excel las que no servían).
- **Unificación de formas y excels de revisión:** el asistente propuso candidatos a unificar (variantes, verbos con y sin *se*), revisó en lotes de 25 filas, armó los Excel de revisión (hojas por tipo: verbos, `-ado`, especies, otros; ordenados por frecuencia; divididos en 5 y luego en 4 repartos) y redactó las instrucciones de la primera hoja.
- **Definiciones:** el asistente propuso definiciones nuevas o combinadas cuando faltaban sentidos (con tuits de ejemplo); el integrante 1 aprobó, rechazó o editó fila por fila.
- **Qué decidió una persona:** qué términos se quedan, qué definición va y qué se unifica. El asistente no decidió nada que no pasara por esa revisión.

### 3.4 Claude como anotador del diccionario (23 al 24 de noviembre)

Quedaron palabras sin decisión de los compañeros (1.474 en total; 931 tras recibir una versión más reciente de un reparto). Se las repartió entre el integrante 1 y el asistente (371 y 560).

- **Prueba ciega de calibración antes de aplicar nada:** el asistente decidió 200 palabras que los compañeros ya habían decidido, sin ver su decisión. Resultado: acuerdo 70,5 %, kappa de Cohen 0,18; el asistente quitaba más (27 % contra 20 %).
- **Revisión del integrante 1 sobre las propuestas del asistente:** en las primeras 127 filas el acuerdo fue de 64,6 % (kappa 0,35, el integrante 1 quitaba mucho más); tras ajustar al criterio del integrante 1, en las filas 129 a 300 fue de 88 % (kappa 0,74).
- **Reemplazos:** el asistente propuso reemplazos para 852 palabras que quedaron sin ninguno (alternativas por sentido separadas por `|`); el integrante 1 los validó. Las que dejó en blanco se contaron como «quitar».
- **Criterios que se le dieron:** «dejar» es un chilenismo real con definición correcta; «quitar» es léxico estándar, ruido, término técnico o no chilenismo, o duplicado; «dejar y revisar definiciones» si el término vale pero la definición es mala; «no sé» solo si no se puede decidir.
- **Limitación declarada:** los compañeros que revisaron antes no son la verdad absoluta, y no existe un acuerdo humano-humano porque cada palabra la revisó una sola persona.

### 3.5 Pares de oraciones: borradores y revisión (8 de noviembre al 24 de noviembre)

- **Borradores de la versión neutra:** `claude-sonnet-5-5` por Claude Code, en lotes de 10 oraciones, con el diccionario como contexto, sin herramientas y sin memoria de sesiones (`src/pares/llm.py`; prompt completo en el Anexo A.1 del informe).
- **Revisión humana de los pares de evaluación:** el integrante 1 revisó cada borrador (`ok` / `corregir` / `descartar`). Tasa de aceptación sin cambios: **80,8 %** (189 de 234 pares válidos). Se declara el sesgo de anclaje (corregir es más fácil que escribir desde cero).
- **Concordancia entre revisores:** solo entregó la revisión el integrante 2 (kappa 0,04); el estudio no es concluyente.
- **Otros generadores como comparación (24 de noviembre):** Haiku 85,0 %, Gemini 82,9 % y Llama 3.1 8B 40,2 % de `ok`. Las pruebas con Llama local y con modelos de Cloudflare se descartaron cuando no funcionaron.
- **Selección del lote 2** (148 pares más, con términos de frecuencia media, media baja y alta): un script (`src/pares/seleccionar_lote.py`), no un prompt.
- **Datos de entrenamiento:** **10.490 pares escritos por un LLM sin revisión humana** (9.966 para entrenar y 524 para validar). Es una limitación declarada en el informe (sección 6): el modelo aprende de borradores de otro modelo.

### 3.6 Modelos de normalización y evaluación (9 de noviembre al 26 de noviembre)

- **Código:** el asistente escribió y ajustó los scripts de métricas (ERR, precisión, recall, F1, BLEU, chrF), de evaluación extrínseca y los cuadernos de entrenamiento de mT5 y ByT5 (Colab y Kaggle).
- **Entrenamiento:** lo corrieron personas (en la GPU local, en Colab y en Kaggle); el asistente preparó los cuadernos y verificó los resultados. mT5 y ByT5 son modelos que se afinan, no asistentes.
- **Traductores para la evaluación extrínseca:** se descartó Google Translate (de pago) y se probaron Argos (descartado) y finalmente Opus-MT y NLLB, ambos gratuitos y locales.
- **Glosario es → en de los términos ancla (25 y 26 de noviembre):** varios modelos (Claude Sonnet y Haiku, Gemini, Cohere, Cloudflare Llama, IBM, Nemotron) escribieron glosas en inglés, y se aceptó una glosa cuando la respaldaban al menos tres de las fuentes (**regla de votos**; calibrada con 93 términos revisados a mano). El integrante 1 revisó a mano los términos con pocos votos y los términos nuevos. El prompt está en el Anexo A.2. Se tuvo el cuidado de que los modelos no vieran oraciones de tuits ni salidas de los sistemas.
- **Análisis estadístico:** intervalos de Wilson, bootstrap y prueba de McNemar. El asistente escribió los scripts (`src/extras/`) y se verificaron las cifras contra los CSV.

### 3.7 Experimentos adicionales (26 de noviembre)

Todos documentados en `docs/informe_interno.md`, sección 4.5, con scripts en `src/extras/` y resultados en `resultados/extras/`.

- **Semillas de mT5 y ByT5:** el asistente adaptó los cuadernos y evaluó los resultados que el integrante 1 descargó de Colab y Kaggle.
- **LLM con diccionario como contexto (el «techo»):** Gemini, Sonnet y Haiku sobre las 594 oraciones de prueba. **Aviso de sesgo:** Sonnet escribió los borradores de las que luego fueron las referencias; Gemini no participó y da casi lo mismo.
- **Piloto «un LLM decide el diccionario»:** Gemini, Haiku, Cohere e IBM decidieron qué términos van en el diccionario; se midió el acuerdo con el humano (prompt en el Anexo A.4). La conclusión del informe es que no puede reemplazar la revisión humana.
- **Auditoría de la sobrecorrección:** el asistente hizo la primera clasificación de 40 oraciones de Haiku y 30 de mT5 y el integrante 1 la revisó fila por fila (corrigió 11 de 40 en Haiku, con cuatro errores reales que el asistente no vio). **El asistente fue más indulgente con Haiku, que es de su misma familia.**
- **Evaluación crítica de los resultados:** se evaluaron críticas externas (de otras IA y de personas) sobre el informe, y se corrigieron las afirmaciones que no se sostenían (por ejemplo, «mejor en todas las métricas», comparaciones múltiples, ERR tolerante).

### 3.8 Documentación y presentaciones (todo el proyecto)

- **Informe interno** (`docs/informe_interno.md`), READMEs, figuras (`notebooks/graficos_informe.ipynb`) y diapositivas: el asistente escribió y reescribió texto, tablas y gráficos a partir de los resultados, y el integrante 1 pidió cambios de estructura, de nombres (integrante N, `reglas_curado`, nombres de los lotes) y de contenido. Hubo una reescritura completa del informe el 26 de noviembre.
- **Verificaciones:** se pidió validar que los números del informe coincidieran con los CSV y que no faltara explicar ni justificar nada; se retiraron afirmaciones sin sustento.
- **Búsqueda del estado del arte:** el integrante 1 pidió un prompt para herramientas de investigación profunda y una lectura del estado del arte (qué dice, qué aporta al proyecto). Aún no se cita en el informe.

### 3.9 Tareas operativas

Control de versiones (commits, ramas, `git worktree`, push solo a `entrega-final`), organización de archivos, descarga de resultados de Kaggle por consola, estimación de tiempos de entrenamiento y avisos de estado.

## 4. Qué decidió y qué no decidió la IA

- **La IA no decidió:** qué términos entran al diccionario (las propuestas se validaron fila por fila), qué pares de evaluación son correctos, qué se descarta, qué experimentos se hacen ni las conclusiones del informe.
- **Qué tiene revisión humana:** el diccionario curado, los pares de evaluación (un solo revisor), 93 términos del glosario, las 40 + 30 oraciones auditadas.
- **Qué NO tiene revisión humana:** los 10.490 pares de entrenamiento, las glosas en inglés con 3 o más votos, las salidas de los LLM y el resto de las predicciones.

## 5. Sesgos y riesgos que se identificaron

- **Misma familia de modelos:** Sonnet escribió los borradores y fue también el votante y el sistema evaluado; Haiku es de su familia. Se incluyó a Gemini y a otros proveedores para contrastar.
- **Sesgo de anclaje:** revisar un borrador no es lo mismo que escribirlo; por eso se hizo la prueba ciega de calibración (3.4).
- **Un solo revisor** de los pares; el único acuerdo medido (kappa 0,04) no es concluyente.
- **Referencia única por oración:** el ERR y el Exact Match penalizan alternativas válidas; el ERR tolerante mitiga solo en parte y favorece a quien usa el diccionario.
- **Reproducibilidad de los modelos de nube:** el proveedor puede cambiar el modelo; las respuestas crudas están guardadas (`data/interim/respuestas_crudas/`, `resultados/extras/llm_dicc/`, `resultados/extras/piloto/`).
- **Errores del asistente que se detectaron:** afirmaciones sin sustento (retiradas del informe), cifras que no coincidían con los CSV (corregidas), un glosario equivocado en una evaluación (se corrigió el valor por defecto) y la indulgencia con Haiku en la auditoría (corregida por el integrante 1).

## 6. Datos y privacidad

- Las claves de API se guardan como variables de entorno y nunca en el repo (`src/glosario_modelos.py` las lee del entorno).
- A los modelos se les enviaron solo términos, definiciones y oraciones de los corpus de trabajo; en las tareas de glosario no se les enviaron oraciones de tuits ni salidas de los sistemas.
- Los textos que se envían a los modelos se declaran como datos y no como instrucciones (defensa básica contra instrucciones escondidas en un tuit).

## 7. Trazabilidad: dónde está cada cosa

| Qué | Dónde |
|---|---|
| Prompts de código (borradores, glosario, piloto) | `docs/informe_interno.md`, Anexo A.1, A.2 y A.4 |
| Lo hecho en sesiones interactivas, sin prompt guardado | Anexo A.3 |
| Registro de modelos, fechas y parámetros | `annotation/README.md` y sección 3.4–3.5 del informe |
| Respuestas crudas de los modelos | `data/interim/respuestas_crudas/`, `resultados/extras/llm_dicc/`, `resultados/extras/piloto/` |
| Scripts de los experimentos adicionales | `src/extras/` (con README) |
| Auditoría de la sobrecorrección | `resultados/extras/auditoria_sobrecorreccion.xlsx` y CSV |

## 8. Cosas por confirmar antes de entregar

1. **Modelo de los borradores:** una lámina de un compañero decía «Claude Opus 5, effort high», pero lo que hizo el integrante 1 fue con `claude-sonnet-5-5` (effort medio). Hay que confirmar con el compañero qué modelo usó él, si usó uno distinto, y que figure en este documento.
2. **Esfuerzo de razonamiento (effort):** el informe registra el modelo, pero no el nivel de esfuerzo. Si se quiere declarar, es «medio» para todo lo del integrante 1.
3. **Fecha de las sesiones de octubre:** las sesiones de ideación y de datos de octubre están registradas, pero no sabemos qué modelo exacto se usó en ellas; no lo afirmamos.

## 9. Uso de IA de los demás integrantes

*(Cada integrante completa su parte: herramienta o modelo, para qué, qué decidió una persona. Sugerencia de formato: una tabla como la de la sección 1.)*

| Integrante | Etapa | Herramienta / modelo | Para qué | Qué se revisó a mano |
|---|---|---|---|---|
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |
