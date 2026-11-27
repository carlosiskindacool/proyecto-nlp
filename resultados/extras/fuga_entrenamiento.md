# Revisión de fuga entre entrenamiento y prueba

- Oraciones únicas de prueba: 594; oraciones únicas de entrenamiento: 10492.
- Con las mismas palabras (en cualquier orden) que alguna de entrenamiento: 0.
- Similitud de Jaccard con la oración de entrenamiento más parecida: ≥ 0,9: 0; ≥ 0,8: 0; ≥ 0,6: 1; mediana 0.21; máxima 0.75.
- Oraciones de prueba (de 20 caracteres o más) contenidas dentro de una de entrenamiento: 2; que contienen una de entrenamiento: 0.
- Términos ancla de la prueba (321) que aparecen en alguna oración de entrenamiento: 304 (95 %). Es esperable: el entrenamiento se armó con los mismos términos del diccionario; lo que no debe repetirse es la oración.

Las 25 oraciones de prueba más parecidas a alguna de entrenamiento están en `fuga_entrenamiento_candidatas.csv`.
