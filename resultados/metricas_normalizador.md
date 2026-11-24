Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).

### lote1 (213 pares, 4145 palabras, 303 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 84,7 | 88,8 |
| reglas_equipo | -7,6 | 11,4 | 4,0 | 5,9 | 82,9 | 87,8 |
| reglas_flo | 30,0 | 50,7 | 34,3 | 40,9 | 90,0 | 93,1 |
| mt5_flo_fp32 | -21,8 | 8,8 | 4,6 | 6,1 | 82,1 | 87,7 |
| mt5_moe_fp32 | -16,2 | 11,6 | 5,6 | 7,6 | 82,7 | 87,7 |

### lote_1_noticias (72 pares, 1789 palabras, 46 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,5 | 95,1 |
| reglas_equipo | -54,3 | 5,6 | 4,3 | 4,9 | 90,6 | 93,7 |
| reglas_flo | 10,9 | 45,8 | 23,9 | 31,4 | 94,5 | 96,4 |
| mt5_flo_fp32 | -106,5 | 0,0 | 0,0 | 0,0 | 88,2 | 92,2 |
| mt5_moe_fp32 | -80,4 | 0,0 | 0,0 | 0,0 | 90,4 | 93,5 |

### lote_1_tuits (165 pares, 2668 palabras, 262 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 80,3 | 85,4 |
| reglas_equipo | -3,8 | 18,8 | 6,1 | 9,2 | 78,7 | 85,2 |
| reglas_flo | 19,5 | 56,2 | 24,0 | 33,7 | 84,1 | 89,1 |
| mt5_flo_fp32 | -23,7 | 10,6 | 5,7 | 7,4 | 77,2 | 83,9 |
| mt5_moe_fp32 | -11,8 | 20,0 | 9,9 | 13,3 | 79,4 | 85,1 |
