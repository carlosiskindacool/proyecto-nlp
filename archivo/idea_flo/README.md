# idea_flo: sistema C, el plan de datos original de Flo

Código aparte del que usa el equipo. Es el **sistema C** del proyecto: le entrega al LLM la oración y el diccionario revisado, y además arma sus propios pares.
Visión general de los tres sistemas: [`../README.md`](../README.md). El diccionario revisado que usa: [`../README_flo.md`](../README_flo.md).

![Los 8 sistemas en paralelo](../docs/pipelines_1.png)

![Archivos involucrados](../docs/pipelines_3.png)

## Estado

| Script | Qué hace | Estado |
|---|---|---|
| `llm.py` | Llama al LLM (backend `claude-code` o `anthropic`) | Ejecutado (a través de `baselines_llm.py`) |
| `baselines_llm.py` | Baselines LLM zero-shot y LLM con diccionario | **Ejecutado** en los tres conjuntos; resultados en `../resultados/comparacion_baselines.csv` |
| `oraciones.py` | Busca oraciones del corpus con términos del diccionario | **Ejecutado**: los dos lotes de Flo y 3.382 candidatas de entrenamiento |
| `borrador.py` | El LLM propone la versión neutra de cada oración (guarda cada 100 y retoma si se corta) | **Ejecutado**: lotes de Flo (ya revisados) y borrador de entrenamiento (sin revisar) |
| `entrenar_mt5.py` | Ajusta mT5-small con el borrador de entrenamiento y lo evalúa en los tres conjuntos (usa la GPU) | **Ejecutado**: 8 épocas en la GPU de Flo (RTX 3050, 4 GB); resultados abajo |

**Qué está revisado y qué no:** los pares de **prueba** (`lote1.csv`, `lote_1_noticias.csv`, `lote_1_tuits.csv`) están revisados (los dos lotes de Flo, por un solo revisor). Los pares de **entrenamiento** son borradores del LLM **sin revisión humana** («datos plata»): sirven para entrenar, nunca para evaluar, y se les quitan las oraciones que están en alguna prueba.

Todos importan `src/chilenismos/dicc.py` para leer el diccionario (`--escenario equipo|flo`).
**No se usó clave de API de Anthropic.** Todas las corridas usaron el backend `claude-code` (el que viene por defecto): llama al CLI de Claude Code con la sesión de Flo ya iniciada, sin clave y gastando el uso del plan, no un cobro por token.
`llm.py` también trae un backend `anthropic` (con `ANTHROPIC_API_KEY` en el entorno y cobro por uso), pero **nunca se ejecutó ni se probó**; se dejó solo por si el equipo prefiere una clave compartida. Por eso el paquete `anthropic` de `requirements.txt` es opcional.

## Resultados

BLEU / chrF en los tres conjuntos de pares (`../resultados/comparacion_baselines.csv`), con las reglas del sistema B como punto de comparación:

| Sistema | lote1.csv (213) | lote_1_noticias (72) | lote_1_tuits (165) |
|---|---|---|---|
| Identidad (no cambia nada) | 85,7 / 88,9 | 94,0 / 95,2 | 82,7 / 85,8 |
| B. Reglas con el diccionario revisado | 89,6 / 92,1 | 94,8 / 96,3 | 86,1 / 89,3 |
| **C.** LLM zero-shot | 90,1 / 92,9 | 94,2 / 96,0 | 83,2 / 86,8 |
| **C.** LLM con el diccionario revisado como contexto | **91,1 / 93,6** | **95,7 / 97,3** | **89,4 / 92,6** |
| **C.** mT5-small ajustado con 1.416 pares propios (`entrenar_mt5.py`) | 81,0 / 87,1 | 91,6 / 94,1 | 80,4 / 84,6 |

- El diccionario ayuda al LLM sobre todo donde hay más jerga: en los tuits sube 6,2 BLEU sobre el LLM solo; en `lote1.csv` y noticias, menos de 2.
- **mT5 ajustado no supera a la identidad** (81,0 contra 85,7 en `lote1.csv`). Sin ajustar da cerca de 0; con 3 épocas y texto sin limpiar daba 66; limpiando menciones y emojis y con 8 épocas llegó a 81. Con 1.416 pares de entrenamiento (borradores del LLM sin revisar) y un modelo chico no alcanza; faltan más pares y la variante con Mixture of Experts.
- **Todo se mide sobre texto limpio** (sin `@usuario` ni emojis, en oraciones y referencias); los números con el texto original están en `resultados/comparacion_baselines_texto_original.csv`.
- El modelo es el de Claude Code (backend `claude-code`), traducido en lotes de 10 oraciones.
- **Cuidado:** Flo revisó las referencias de los dos lotes de Flo y validó con el mismo diccionario los reemplazos, así que `llm_dicc_flo` podría salir favorecido ahí; se corregirá con otro revisor en el futuro. `lote1.csv` no lo escribió Flo, pero si lo redactó un LLM podría favorecer a los sistemas LLM.

## Plan
1. Diccionario → `diccionario.py` (equipo) y `data/curado/` (Flo).
2. **Oraciones del corpus con esos términos** → `oraciones.py`.
3. **Borrador del par chileno → neutro con un LLM, usando el diccionario como contexto**, y revisión humana → `borrador.py`.
4. **Ajuste de mT5 con esos pares** (la validación sale de los mismos pares y la prueba son los tres conjuntos revisados) → `entrenar_mt5.py`.
5. **Baselines con LLM** (zero-shot y con diccionario) → `baselines_llm.py`.

## Uso
```
# 2. candidatas (sin tuits por defecto; con --incluir-tuits se agregan)
python idea_flo/oraciones.py --corpus RUTA/AL/CORPUS/data --escenario flo
#    -> data/interim/candidatas.csv (termino;oracion;fuente); data/interim no se sube a git
#    (con --terminos 100 --max-por-termino 2 salen los lotes de Flo; con --incluir-tuits --max-por-termino 8, las de entrenamiento)

# 3. borrador
python idea_flo/borrador.py --seco --limite 5      # solo muestra el prompt, no llama al LLM
python idea_flo/borrador.py --limite 1500 --entrada data/interim/candidatas_entrenamiento.csv --salida data/interim/borrador_entrenamiento.csv
#    --limite elige las oraciones al azar; guarda cada 100 y retoma si se corta
#    Para los lotes de prueba, quien revisa corrige `neutro` y anota su nombre en `revisor1`

# 4. ajuste de mT5 en la GPU (necesita torch con CUDA)
python idea_flo/entrenar_mt5.py --resumen resultados/comparacion_baselines.csv
python idea_flo/entrenar_mt5.py --sin-entrenar --resumen resultados/comparacion_baselines.csv   # mT5 sin ajustar, para comparar

# 5. baselines con LLM
python idea_flo/baselines_llm.py --seco
python idea_flo/baselines_llm.py --pares annotation/lote1.csv annotation/lote_1_noticias.csv annotation/lote_1_tuits.csv --resumen resultados/comparacion_baselines.csv
#    cada sistema se evalúa en cada conjunto; los lotes solo usan los pares revisados
```

## Decisión por ahora: un solo revisor
Con un revisor no se puede medir el acuerdo entre personas ni se corrige el sesgo de esa persona. Es una limitación que hay que declarar en el informe.
Opción intermedia: una segunda persona revisa solo una muestra del test (por ejemplo 100 pares) y se reporta el acuerdo sobre esa muestra.

## Qué falta del plan original
Ejecutar y revisar los pares (arriba), fine-tune de mT5 y su variante con Mixture of Experts (hoy `baselines.py` solo corre mT5 sin entrenar), BERTScore y evaluación humana.
