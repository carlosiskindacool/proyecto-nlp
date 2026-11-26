# Resumen de los pilotos (LLM decide el diccionario)

## Piloto 1: 488 términos que aparecen en las oraciones de prueba

Acuerdo con el humano (dejar/quitar, ambiguo, reemplazos):

| modelo   |   términos | acuerdo dejar/quitar   |   kappa | quita lo que el humano quitó   | quita lo que el humano dejó   | ambiguo igual   | 1er reemplazo igual   | algún reemplazo en común   |
|:---------|-----------:|:-----------------------|--------:|:-------------------------------|:------------------------------|:----------------|:----------------------|:---------------------------|
| gemini   |        488 | 66 %                   |    0.17 | 43/68                          | 143/420                       | 239/277         | 103/254               | 134/254                    |
| haiku    |        488 | 71 %                   |    0.25 | 46/68                          | 119/420                       | 257/301         | 126/274               | 151/274                    |
| cohere   |        487 | 70 %                   |    0.18 | 38/68                          | 118/419                       | 261/301         | 94/268                | 108/268                    |
| ibm      |        488 | 65 %                   |    0.05 | 26/68                          | 130/420                       | 209/290         | 64/253                | 77/253                     |
| consenso |        488 | 65 %                   |    0.17 | 44/68                          | 149/420                       | 240/271         | 101/247               | 132/247                    |

## Piloto 2: 500 términos revisados más frecuentes en las oraciones de entrenamiento (sin efecto medible en ERR)

Acuerdo con el humano (dejar/quitar, ambiguo, reemplazos):

| modelo   |   términos | acuerdo dejar/quitar   |   kappa | quita lo que el humano quitó   | quita lo que el humano dejó   | ambiguo igual   | 1er reemplazo igual   | algún reemplazo en común   |
|:---------|-----------:|:-----------------------|--------:|:-------------------------------|:------------------------------|:----------------|:----------------------|:---------------------------|
| gemini   |        500 | 63 %                   |    0.04 | 12/21                          | 174/479                       | 239/305         | 111/281               | 144/281                    |
| haiku    |        500 | 65 %                   |    0.06 | 13/21                          | 166/479                       | 255/313         | 127/287               | 149/287                    |
| cohere   |        498 | 68 %                   |    0.02 | 8/21                           | 144/477                       | 274/333         | 90/302                | 99/302                     |
| consenso |        500 | 69 %                   |    0.07 | 12/21                          | 145/479                       | 281/334         | 127/310               | 163/310                    |

## Piloto 1: ERR de reglas por conjunto (variantes del diccionario)

| variante           |   lote1 |   lote_1_2_noticias |   lote_1_2_tuits |   lote_1_noticias |   lote_1_tuits |
|:-------------------|--------:|--------------------:|-----------------:|------------------:|---------------:|
| cohere             |    16.5 |                 -22 |              2.2 |             -19.6 |            5   |
| cohere_seleccion   |    24.4 |                 -20 |             14.1 |             -13   |           15.6 |
| consenso           |    16.8 |                 -10 |              7.3 |              -8.7 |            8   |
| consenso_seleccion |    27.7 |                  -8 |             16.3 |              -2.2 |           15.3 |
| gemini             |    18.2 |                   8 |              8.6 |              10.9 |            9.5 |
| gemini_seleccion   |    30.7 |                  10 |             16.1 |              17.4 |           14.5 |
| haiku              |    20.5 |                  -2 |              9   |               0   |            5   |
| haiku_seleccion    |    30.4 |                   2 |             17.4 |              10.9 |           15.6 |
| humano             |    30   |                   2 |             18.5 |              10.9 |           19.5 |
| ibm                |    -5.6 |                 -84 |            -12.1 |             -87   |          -11.1 |
| ibm_seleccion      |    14.8 |                 -22 |              9.5 |             -21.7 |           11.4 |

F1 por palabra:

| variante           |   lote1 |   lote_1_2_noticias |   lote_1_2_tuits |   lote_1_noticias |   lote_1_tuits |
|:-------------------|--------:|--------------------:|-----------------:|------------------:|---------------:|
| cohere             |    27.1 |                15.9 |             15.5 |              17.1 |           11.6 |
| cohere_seleccion   |    34.8 |                19.3 |             32.2 |              21.3 |           28.3 |
| consenso           |    26.6 |                18   |             20.7 |              19.2 |           17.3 |
| consenso_seleccion |    38.7 |                20.8 |             32.4 |              22.9 |           27.1 |
| gemini             |    27.8 |                17.9 |             20.2 |              19.4 |           18.1 |
| gemini_seleccion   |    41   |                25.7 |             31.4 |              28.6 |           26.6 |
| haiku              |    30.6 |                20.8 |             22   |              22.2 |           12.4 |
| haiku_seleccion    |    41.2 |                28.2 |             34   |              31.4 |           27.8 |
| humano             |    40.9 |                28.2 |             37.4 |              31.4 |           33.7 |
| ibm                |    13.2 |                 1.8 |              8   |               1.9 |            7.7 |
| ibm_seleccion      |    29.3 |                16.7 |             28   |              17.7 |           24.8 |

## Piloto 1: Exact Match de traducción (594 oraciones, reglas con cada diccionario)

| variante           |   mt |   nllb |
|:-------------------|-----:|-------:|
| cohere             | 21.4 |   18.9 |
| cohere_seleccion   | 20.5 |   19.5 |
| consenso           | 19.7 |   17.3 |
| consenso_seleccion | 20   |   18.9 |
| gemini             | 17   |   16.8 |
| gemini_seleccion   | 19.4 |   19.4 |
| haiku              | 16.8 |   14.3 |
| haiku_seleccion    | 21.4 |   19.7 |
| humano (oficial)   | 23.9 |   21   |
| ibm                | 21.4 |   18.4 |
| ibm_seleccion      | 19   |   16.8 |
