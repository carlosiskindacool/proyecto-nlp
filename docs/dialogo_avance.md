## Diapositiva 2 · El problema y la propuesta
Los traductores automáticos fallan habitualmente con la jerga: por ejemplo, «hueón» puede terminar como «erección» y «tuto» como «etiqueta». En la propuesta planteamos normalizar los chilenismos antes de traducir, utilizando un modelo mT5 extendido con capas Mixture of Experts. Este avance aborda precisamente esa etapa de normalización: pasar de *«el carrete estuvo fome»* a *«la fiesta estuvo aburrida»*, modificando exclusivamente la jerga y preservando el resto de la oración.

## Diapositiva 3 · Graphical abstract
Este es el graphical abstract de nuestra propuesta original. El flujo general parte con la recolección de datos: el corpus chileno y el diccionario de jerga para extraer oraciones reales. Luego construimos el corpus paralelo mediante un borrador inicial propuesto por un LLM y una revisión humana estricta, separando el conjunto de prueba. Esos pares alimentan el entrenamiento de nuestro modelo mT5 con Sparse MoE, para finalmente generar la versión en español neutro y evaluar con métricas automáticas y revisión manual.

## Diapositiva 4 · Recolección de datos: corpus y fuentes
Utilizamos el *Chilean Spanish Corpus*, que reúne cerca de 37 millones de textos reales. Para el diccionario consolidamos 3.403 términos a partir de Wikcionario en español e inglés y el diccionario histórico de Román. Constatamos que armar un diccionario de forma puramente automática produce fallas críticas: al tomar la primera definición como reemplazo, *buena onda* se traduce como «expresión de saludo» y *cancha* como «terreno despejado».

## Diapositiva 5 · Recolección de datos: diccionario revisado
Por ello realizamos una curación manual. Ordenamos los términos por frecuencia en tuits y revisamos el primer libro con los 650 más recurrentes. Validamos 433 términos vigentes, corregimos sus definiciones y fijamos un reemplazo neutro por cada sentido. Asimismo, marcamos como ambiguas palabras que también tienen un uso estándar frecuente como *andar*, *pesado* u *once*, para evitar sustituciones erróneas a ciegas.

## Diapositiva 6 · Recolección de datos: pares paralelos
Para evaluar disponemos de tres conjuntos: un lote general de 213 pares, uno de noticias con 72 y uno de tuits con 165. En noticias y tuits el LLM propuso una versión neutra y una persona revisó cada caso; solo evaluamos sobre pares revisados. Para el entrenamiento de nuestro modelo generamos además 1.491 pares con borrador sin revisión humana, garantizando que no exista solapamiento con los conjuntos de evaluación.

## Diapositiva 7 · Código de datos: extracción, borradores y limpieza
En el repositorio dejamos implementado cada paso en código reproducible: en `diccionario.py` consultamos la API de MediaWiki filtrando sentidos chilenos y extrayendo reemplazos breves; en `oraciones.py` procesamos los 63 archivos Parquet en paralelo con multiprocessing, filtrando largo, descartando retuits y anonimizando usuarios como `@usuario`; y en `baselines.py` limpiamos emojis y exigimos la validación del revisor humano para incluir un par en la evaluación.

## Diapositiva 8 · Diseño experimental: los sistemas
Con estos datos comparamos ocho sistemas agrupados en tres familias: la Familia A con reglas y diccionario automático; la Familia B con las mismas reglas pero el diccionario curado; y la Familia C con un LLM con y sin diccionario, además de nuestro modelo propio mT5 ajustado. Como piso de comparación usamos la identidad, y como referencias externas sumamos dos traductores neuronales genéricos.

## Diapositiva 9 · Código de modelos: reglas, LLM y ajuste de mT5
En cuanto al modelamiento, en `dicc.py` compilamos expresiones regulares ordenadas por longitud para priorizar locuciones antes que palabras aisladas, respetando mayúsculas. Para el LLM, en `llm.py` inyectamos dinámicamente un glosario con las alternativas neutras solo de los términos presentes en la oración. Y en `entrenar_mt5.py` ajustamos `mt5-small` con optimizador Adafactor en `bfloat16`, enmascarando el padding con `-100` y decodificando con beam search de 4 haces.

## Diapositiva 10 · Diseño experimental: qué comparamos y cómo medimos
El diseño experimental aísla variables clave: comparar A con B mide el valor de la curación manual; LLM con versus sin diccionario mide cuánto aporta la base léxica; y reglas frente al LLM evalúa la necesidad de entender el contexto sintáctico. Medimos BLEU y chrF mediante SacreBLEU sobre texto limpio. Dado que la mayor parte de la oración no cambia, la identidad ya parte en valores altos de 83 a 94; lo relevante es la diferencia respecto a ella.

## Diapositiva 11 · Resultados: tabla principal
En los tres conjuntos de evaluación el ganador absoluto es el LLM con diccionario revisado, alcanzando 89,4 de BLEU en tuits frente al 82,7 de la identidad. Las reglas con diccionario automático empeoran el texto base en todos los casos. En cambio, con el diccionario revisado, el mismo código de sustitución sube de 84,1 a 89,6 en el lote general, logrando que 76 de 117 sustituciones coincidan exactamente con la referencia humana.

## Diapositiva 12 · Resultados: qué aprendimos
De los resultados cuantitativos extraemos cuatro aprendizajes clave: primero, curar el diccionario aporta más de 5 puntos de BLEU; segundo, el diccionario potencia al LLM especialmente donde hay mayor densidad de jerga, sumando 6,2 puntos en tuits; tercero, reemplazar palabras ambiguas con reglas fijas perjudica el rendimiento sistemáticamente; y cuarto, los traductores genéricos colapsan a 38 y 44 de BLEU porque reescriben toda la frase y distorsionan el mensaje.

## Diapositiva 13 · Resultados: análisis cualitativo y ejemplos de traducción
Al examinar cualitativamente las oraciones traducidas se hace evidente la raíz de estos comportamientos. Frente a *«el hueón sale corriendo para sapear»*, los traductores genéricos alucinan cosas como «la erección corre a savia» o «el huevo para freír», mientras que las reglas curadas y el LLM aciertan con «delatar». En *«una yapa»*, la regla fija comete un error de concordancia sintáctica al generar «una regalo adicional», mientras que el LLM ajusta el género a «un regalo». Y en expresiones complejas no cubiertas por reglas como *«15 lucas q wea»*, el LLM sin diccionario tiende a sobredimensionar la vulgaridad traduciendo «qué mierda», mientras que con el diccionario revisado modula el registro neutro apropiado: «qué cosa».

## Diapositiva 14 · Resultados: modelo propio mT5-small ajustado
Respecto a nuestro modelo propio, `mT5-small` ajustado demuestra haber aprendido la tarea: pasa de 0,1 de BLEU sin entrenar a 81,0 tras 8 épocas de fine-tuning sobre texto limpio. Sin embargo, aún no supera el piso de la identidad de 85,7. Tiende a copiar la oración casi completa o a cometer errores locales al modificar palabras. Esto demuestra que 1.416 pares de borrador no son suficientes para un modelo denso de este tamaño, confirmando la necesidad de incorporar la arquitectura Sparse MoE propuesta.

## Diapositiva 15 · Limitaciones que declaramos
Declaramos con transparencia las limitaciones del avance: los conjuntos propios fueron revisados por una sola persona, por lo que aún no medimos acuerdo interanotador y existe un sesgo hacia el diccionario curado; falta documentar con certeza cómo se generó el lote general de 213 pares; y el diccionario revisado abarca por el momento solo el primer libro de frecuencia.

## Diapositiva 16 · Próximos pasos hacia la entrega final
Para la entrega final del 25 de noviembre nuestros pasos son claros: incorporaremos un segundo revisor independiente para medir acuerdo con kappa y aplicaremos el filtro de similitud semántica con LaBSE planteado en la propuesta; implementaremos la capa Sparse MoE con 4 expertos y router softmax sobre mT5 aumentando los pares de entrenamiento; y realizaremos la evaluación humana final, comprobando si esta normalización optimiza la traducción definitiva al inglés.
