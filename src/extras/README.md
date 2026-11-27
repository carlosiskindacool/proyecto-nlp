# Scripts de los experimentos adicionales

Son los scripts de la sección 4.5 del informe (`docs/informe_interno.md`) y de la variación entre semillas de 4.4. **No forman parte del pipeline final.** Se corren desde la raíz del repo; todos calculan sus rutas a partir de la ubicación del archivo.

| Script | Qué hace | Entrada | Salida |
|---|---|---|---|
| `incertidumbre.py` | Intervalo de confianza de cada Exact Match y comparación pareada (diferencia con bootstrap y prueba de McNemar) | `data/processed/eval_extrinseca.csv` y los archivos por oración de `resultados/extras/` | `resultados/extras/incertidumbre_exact_match*.csv` |
| `errores_modelos.py` | Cuánto cambian de más y cómo fallan reglas, mT5, MoE y ByT5 (tres semillas cada uno); con `--ejemplos` imprime candidatos para la tabla de ejemplos | `data/processed/predicciones_*.csv` | `resultados/extras/errores_modelos.csv` |
| `llm_dicc_594.py` | Un LLM con el diccionario como contexto sobre las 594 oraciones de prueba (el «techo» de la fase 1: `llm_dicc_curado`); funciona con Gemini, Sonnet y Haiku (Cohere no respondió en un tiempo razonable e IBM devolvió «cupo de tokens agotado»; el script los soporta igual) | `data/curado/diccionario_flo.csv`, `data/processed/predicciones_mt5_flo_fp32.csv` (oraciones y referencias) | `resultados/extras/llm_dicc/predicciones_llm_<modelo>.csv` y `salidas_llm_<modelo>.json` |
| `auditoria_sobrecorreccion.py` | Muestra al azar de oraciones con sobrecorrección (cambios de más) de un sistema, para clasificarlas a mano como jerga no anotada, reformulación, error real o dudosa | predicciones | `resultados/extras/auditoria_sobrecorreccion_<sistema>.csv` |
| `em_estricto.py` | Exact Match **estricto**: término ancla bien traducido **y** sin cambiar palabras que la referencia dejó igual (reconcilia ERR y Exact Match) | predicciones y Exact Match por oración | `resultados/extras/em_estricto.csv` |
| `err_incertidumbre_tolerante.py` | ERR y F1 con intervalo bootstrap, y ERR tolerante a las alternativas válidas del diccionario | predicciones | `resultados/extras/err_incertidumbre.csv` |
| `traduccion_oracion_completa.py` | chrF y BLEU de la traducción de la oración completa de cada sistema contra la traducción de la referencia (sustituto automático de la evaluación humana). Hay que correrlo con un Python que tenga `torch` y `transformers` | traducciones existentes; traduce solo las referencias | `resultados/extras/traduccion_oracion_completa*.csv`, `traducciones_referencias.csv` |
| `hibrido.py` | Híbrido: la salida de las reglas si cambiaron la oración y la del modelo si no | predicciones | `resultados/extras/hibrido*.csv` |
| `fuga_entrenamiento.py` | Busca oraciones de prueba casi repetidas en el entrenamiento | `data/interim/borrador_entrenamiento.csv` | `resultados/extras/fuga_entrenamiento.md` |
| `comun.py` | Funciones compartidas (carga de salidas y de Exact Match por oración) | | |
| `sensibilidad_ruido.py` | Copia las predicciones sin risas ni hashtags (los comandos para repetir las métricas están en su encabezado) | `data/processed/predicciones_*.csv` | `data/processed/sensibilidad/` (no se versiona) |
| `piloto_terminos.py` | Lista de términos del piloto del diccionario con LLM (`1`: 488 términos de las oraciones de prueba; `2`: 500 términos más del entrenamiento) | `data/curado/`, `annotation/`, `data/diccionario/procesado/terminos.csv` | `resultados/extras/piloto/terminos_piloto*.csv` |
| `piloto_dicc_modelos.py` | Le pide a un modelo que decida cada término (prompt en el Anexo A.4 del informe); guarda cada respuesta cruda y retoma lo ya hecho | `terminos_piloto*.csv` | `resultados/extras/piloto/decisiones_<modelo>*.json` y `crudas_<modelo>*.jsonl` |
| `piloto_analisis.py` | `acuerdo` (acuerdo y kappa con el humano), `variantes` (arma los diccionarios), `metricas` (ERR y F1 de las reglas) y `extrinseca` (Exact Match) | decisiones de los modelos | `acuerdo*.csv`, `metricas_variantes.csv`; diccionarios y predicciones en `data/processed/piloto/` |
| `piloto_resumen.py` | Junta todo en `resultados/extras/piloto/RESUMEN.md` | lo anterior | `RESUMEN.md`, `eval_extrinseca_variantes.csv` |

## Cómo se obtuvo cada cosa

- **Predicciones de las semillas 2 y 3 de mT5 y de ByT5** (`predicciones_byt5_flo_fp32_s2.csv` y `..._s3.csv`; con `git add -f` si `data/processed/` está ignorado): de los cuadernos `models/mt5/mt5_semillas_kaggle.ipynb`, `models/byt5/byt5.ipynb` y `models/byt5/byt5_kaggle.ipynb` (se bajan de Drive o de la pestaña *Output* de Kaggle y se dejan en `data/processed/`).
- **Exact Match por oración de las salidas de los LLM** (`resultados/extras/llm_dicc/eval_extrinseca_llm_<modelo>.csv`): `python src/eval_extrinseca.py --entrada resultados/extras/llm_dicc/predicciones_llm_<modelo>.csv --out <ese archivo>` y luego `eval_extrinseca_resumen.py` sobre él.
- **Exact Match por oración de esas corridas** (`resultados/extras/eval_extrinseca_*_oraciones*.csv`): se traducen con `python src/eval_extrinseca.py --entrada <predicciones> --out <traducciones.csv>` y se calcula con `python src/eval_extrinseca_resumen.py --traducciones <traducciones.csv> --glosario data/diccionario/glosario_es_en_final.csv --out <resumen.csv> --md <resumen.md>`. El script de resumen agrega las columnas `acepta_en` y `exact_match` a las traducciones.
- **Métricas intrínsecas** (`resultados/extras/metricas_normalizador_mt5_semillas_byt5.csv`): `python src/chilenismos/metricas_normalizador.py --entrada "data/processed/predicciones_*fp32*.csv"`.
- **Qué fija la semilla** en los cuadernos de mT5 y ByT5: el reparto aleatorio de entrenamiento y validación, el orden de los datos en cada época y el *dropout*. Los pesos iniciales son siempre los mismos.

El piloto usa modelos de nube: las claves se leen de variables de entorno desde `src/pares/llm.py` y nunca se guardan en el repo. Las respuestas ya están guardadas en `resultados/extras/piloto/`, así que `piloto_analisis.py` y `piloto_resumen.py` se pueden correr sin llamar a ningún modelo.
