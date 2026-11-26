Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).

### lote1 (213 pares, 4145 palabras, 303 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 84,7 | 88,8 |
| reglas_equipo | -7,6 | 11,4 | 4,0 | 5,9 | 82,9 | 87,8 |
| reglas_flo | 30,0 | 50,7 | 34,3 | 40,9 | 90,0 | 93,1 |
| mt5_flo_fp32 | -9,6 | 28,0 | 27,1 | 27,5 | 83,8 | 89,3 |
| mt5_moe_fp32 | -5,9 | 27,1 | 25,1 | 26,1 | 84,4 | 89,8 |

### lote_1_2_noticias (77 pares, 1950 palabras, 50 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,6 | 95,2 |
| reglas_equipo | -56,0 | 5,1 | 4,0 | 4,5 | 90,7 | 93,8 |
| reglas_flo | 2,0 | 39,3 | 22,0 | 28,2 | 94,0 | 96,2 |
| mt5_flo_fp32 | -100,0 | 16,9 | 28,0 | 21,1 | 88,5 | 93,8 |
| mt5_moe_fp32 | -86,0 | 17,8 | 26,0 | 21,1 | 89,6 | 94,2 |

### lote_1_2_tuits (308 pares, 5083 palabras, 454 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 82,3 | 87,0 |
| reglas_equipo | -6,2 | 16,4 | 5,3 | 8,0 | 80,0 | 86,2 |
| reglas_flo | 18,5 | 49,6 | 30,0 | 37,4 | 85,5 | 90,0 |
| mt5_flo_fp32 | -5,7 | 30,8 | 26,4 | 28,4 | 81,6 | 87,9 |
| mt5_moe_fp32 | -1,3 | 32,1 | 26,7 | 29,1 | 82,7 | 88,7 |

### lote_1_noticias (72 pares, 1789 palabras, 46 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,5 | 95,1 |
| reglas_equipo | -54,3 | 5,6 | 4,3 | 4,9 | 90,6 | 93,7 |
| reglas_flo | 10,9 | 45,8 | 23,9 | 31,4 | 94,5 | 96,4 |
| mt5_flo_fp32 | -91,3 | 17,8 | 28,3 | 21,8 | 88,8 | 93,8 |
| mt5_moe_fp32 | -73,9 | 19,4 | 26,1 | 22,2 | 89,8 | 94,1 |

### lote_1_tuits (165 pares, 2668 palabras, 262 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 80,3 | 85,4 |
| reglas_equipo | -3,8 | 18,8 | 6,1 | 9,2 | 78,7 | 85,2 |
| reglas_flo | 19,5 | 56,2 | 24,0 | 33,7 | 84,1 | 89,1 |
| mt5_flo_fp32 | -6,9 | 29,3 | 25,6 | 27,3 | 79,6 | 86,4 |
| mt5_moe_fp32 | -5,0 | 29,6 | 25,2 | 27,2 | 80,8 | 87,4 |
