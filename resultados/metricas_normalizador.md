Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).

### lote1 (213 pares, 4145 palabras, 303 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 84,7 | 88,8 |
| reglas_equipo | -7,6 | 11,4 | 4,0 | 5,9 | 82,9 | 87,8 |
| reglas_flo | 23,4 | 58,7 | 24,4 | 34,5 | 88,8 | 91,9 |
| mt5_flo | -24,4 | 7,8 | 4,3 | 5,5 | 81,8 | 87,3 |
| mt5_flo_fp32 | -21,8 | 8,8 | 4,6 | 6,1 | 82,1 | 87,7 |
| mt5_moe_fp32 | -16,2 | 11,6 | 5,6 | 7,6 | 82,7 | 87,7 |
| mt5_sin_ajustar | -1252,8 | 0,7 | 8,9 | 1,2 | 0,1 | 2,1 |

### lote_1_noticias (72 pares, 1789 palabras, 46 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,5 | 95,1 |
| reglas_equipo | -54,3 | 5,6 | 4,3 | 4,9 | 90,6 | 93,7 |
| reglas_flo | 13,0 | 55,0 | 23,9 | 33,3 | 94,6 | 96,4 |
| mt5_flo | -56,5 | 0,0 | 0,0 | 0,0 | 91,3 | 94,1 |
| mt5_flo_fp32 | -106,5 | 0,0 | 0,0 | 0,0 | 88,2 | 92,2 |
| mt5_moe_fp32 | -80,4 | 0,0 | 0,0 | 0,0 | 90,4 | 93,5 |
| mt5_sin_ajustar | -3717,4 | 0,0 | 0,0 | 0,0 | 0,3 | 3,2 |

### lote_1_tuits (165 pares, 2668 palabras, 262 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 80,3 | 85,4 |
| reglas_equipo | -3,8 | 18,8 | 6,1 | 9,2 | 78,7 | 85,2 |
| reglas_flo | 21,0 | 62,9 | 23,3 | 34,0 | 84,4 | 89,4 |
| mt5_flo | -16,8 | 14,0 | 6,9 | 9,2 | 78,3 | 84,4 |
| mt5_flo_fp32 | -23,7 | 10,6 | 5,7 | 7,4 | 77,2 | 83,9 |
| mt5_moe_fp32 | -11,8 | 20,0 | 9,9 | 13,3 | 79,4 | 85,1 |
| mt5_sin_ajustar | -905,0 | 1,0 | 10,3 | 1,8 | 0,0 | 2,4 |
