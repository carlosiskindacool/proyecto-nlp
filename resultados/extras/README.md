# Resultados de los experimentos adicionales

Datos de las secciones 4.4 (semillas e incertidumbre) y 4.5 del informe. Los scripts que los generan están en `src/extras/` (ver su `README.md`).

| Archivo | Contenido |
|---|---|
| `metricas_normalizador_mt5_semillas_byt5.csv` | Métricas intrínsecas por conjunto de mT5 y de ByT5 (semillas 1, 2 y 3) y del MoE |
| `eval_extrinseca_mt5_semillas.csv` | Exact Match del mT5 denso por semilla, glosario, conjunto y traductor |
| `eval_extrinseca_byt5_mt5_s2_s3.csv` | Exact Match de ByT5 (semillas 1, 2 y 3; la 1 figura como `byt5`) y de las semillas 2 y 3 de mT5, con el glosario final |
| `eval_extrinseca_mt5_semillas_oraciones.csv` | Exact Match por oración de las semillas 2 y 3 de mT5 |
| `eval_extrinseca_oraciones_byt5.csv`, `..._byt5_s2.csv`, `..._byt5_s3.csv` | Salida, traducción y Exact Match por oración de ByT5, semillas 1, 2 y 3 |
| `incertidumbre_exact_match.csv`, `incertidumbre_exact_match_pares.csv` | Intervalos de confianza y comparaciones pareadas (McNemar) |
| `errores_modelos.csv` | Sobrecorrección y tipos de resultado por oración, por sistema y conjunto |
| `llm_dicc/` | Un LLM con el diccionario sobre las 594 oraciones: salidas, Exact Match (con la traducción de cada oración), ERR y F1 de cada modelo |
| `em_estricto.csv` | Exact Match estricto (sin sobrecorrección) por sistema y traductor |
| `auditoria_sobrecorreccion.xlsx` (y los dos CSV `auditoria_sobrecorreccion_llm_haiku.csv` y `..._mt5_s1.csv`) | 40 y 30 oraciones sobrecorregidas con cada cambio de más y su clasificación a mano (A jerga no anotada, B reformulación, C error real, D dudosa; en la de Haiku, además, la clasificación final tras la revisión del integrante 1, E = error de la referencia y M = mixta) |
| `err_incertidumbre.csv` | ERR y F1 con intervalos bootstrap, estrictos y tolerantes |
| `traduccion_oracion_completa.csv`, `..._pares.csv`, `traducciones_referencias.csv` | chrF y BLEU de la traducción de la oración completa |
| `hibrido.csv`, `hibrido_pares.csv` | Híbrido reglas + modelo |
| `fuga_entrenamiento.md`, `fuga_entrenamiento_candidatas.csv` | Revisión de oraciones repetidas entre entrenamiento y prueba |
| `frecuencia_terminos_revisados.csv` | Frecuencia en tuits de cada término revisado (para la figura 10) |
| `traducciones_mt5_semillas.csv` | Salida y traducción de las semillas 2 y 3 de mT5 |
| `sensibilidad_texto_limpio.md` | Métricas sin risas ni hashtags |
| `piloto/` | Piloto «un LLM decide el diccionario»: términos, decisiones y respuestas crudas de cada modelo, acuerdo con el humano y `RESUMEN.md` |

En `piloto/`, los archivos con sufijo `2` son del piloto 2. `decisiones_nvidia.json` y `crudas_nvidia.jsonl` quedaron incompletos (cupo gratuito agotado) y no se usan en ningún resultado.
