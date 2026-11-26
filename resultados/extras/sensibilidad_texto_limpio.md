# Sensibilidad: texto sin risas ni hashtags

## Métricas intrínsecas

Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).

### lote1 (213 pares, 4138 palabras, 303 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 84,8 | 88,8 |
| reglas_equipo | -7,6 | 11,4 | 4,0 | 5,9 | 82,9 | 87,8 |
| reglas_flo | 30,0 | 50,7 | 34,3 | 40,9 | 90,0 | 93,1 |
| mt5_flo_fp32 | -9,2 | 28,0 | 27,1 | 27,5 | 84,0 | 89,4 |
| mt5_moe_fp32 | -5,9 | 27,1 | 25,1 | 26,1 | 84,5 | 89,8 |

### lote_1_2_noticias (77 pares, 1949 palabras, 50 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,6 | 95,2 |
| reglas_equipo | -56,0 | 5,1 | 4,0 | 4,5 | 90,7 | 93,8 |
| reglas_flo | 2,0 | 39,3 | 22,0 | 28,2 | 94,0 | 96,2 |
| mt5_flo_fp32 | -100,0 | 16,9 | 28,0 | 21,1 | 88,4 | 93,8 |
| mt5_moe_fp32 | -86,0 | 17,8 | 26,0 | 21,1 | 89,5 | 94,2 |

### lote_1_2_tuits (308 pares, 4995 palabras, 452 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 82,0 | 86,6 |
| reglas_equipo | -6,2 | 16,4 | 5,3 | 8,0 | 79,6 | 85,8 |
| reglas_flo | 18,6 | 49,8 | 30,1 | 37,5 | 85,2 | 89,7 |
| mt5_flo_fp32 | -4,2 | 31,3 | 26,5 | 28,7 | 81,5 | 87,6 |
| mt5_moe_fp32 | 0,4 | 32,8 | 26,8 | 29,5 | 82,6 | 88,4 |

### lote_1_noticias (72 pares, 1788 palabras, 46 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 93,5 | 95,1 |
| reglas_equipo | -54,3 | 5,6 | 4,3 | 4,9 | 90,6 | 93,6 |
| reglas_flo | 10,9 | 45,8 | 23,9 | 31,4 | 94,5 | 96,4 |
| mt5_flo_fp32 | -91,3 | 17,8 | 28,3 | 21,8 | 88,8 | 93,8 |
| mt5_moe_fp32 | -73,9 | 19,4 | 26,1 | 22,2 | 89,8 | 94,1 |

### lote_1_tuits (165 pares, 2619 palabras, 262 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| identidad | 0,0 | – | 0,0 | – | 79,8 | 84,7 |
| reglas_equipo | -3,8 | 18,8 | 6,1 | 9,2 | 78,1 | 84,5 |
| reglas_flo | 19,5 | 56,2 | 24,0 | 33,7 | 83,7 | 88,6 |
| mt5_flo_fp32 | -5,0 | 29,9 | 25,6 | 27,6 | 79,4 | 85,9 |
| mt5_moe_fp32 | -2,7 | 30,3 | 25,2 | 27,5 | 80,8 | 87,0 |


## Evaluación extrínseca

Exact-Match Accuracy (%) del término ancla al traducir al inglés la salida de cada sistema. Generado por src/eval_extrinseca_resumen.py.

### todos (594 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 6,9 | 6,4 |
| reglas_flo | 24,2 | 21,0 |
| reglas_equipo | 12,3 | 10,3 |
| mt5 | 18,4 | 16,2 |
| mt5_moe | 19,7 | 16,7 |

### lote1.csv (213 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 4,7 | 7,5 |
| reglas_flo | 30,5 | 31,9 |
| reglas_equipo | 4,7 | 8,0 |
| mt5 | 22,1 | 23,9 |
| mt5_moe | 23,5 | 23,9 |

### lote_1_2_noticias.csv (73 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 9,6 | 4,1 |
| reglas_flo | 17,8 | 12,3 |
| reglas_equipo | 21,9 | 12,3 |
| mt5 | 9,6 | 5,5 |
| mt5_moe | 12,3 | 6,8 |

### lote_1_2_tuits.csv (308 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 7,8 | 6,2 |
| reglas_flo | 21,4 | 15,6 |
| reglas_equipo | 15,3 | 11,4 |
| mt5 | 17,9 | 13,3 |
| mt5_moe | 18,8 | 14,0 |

### lote_1_noticias.csv (68 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 8,8 | 4,4 |
| reglas_flo | 14,7 | 10,3 |
| reglas_equipo | 22,1 | 13,2 |
| mt5 | 10,3 | 5,9 |
| mt5_moe | 13,2 | 7,4 |

### lote_1_tuits.csv (165 oraciones evaluables)

| Sistema | Opus-MT | NLLB |
|---|---:|---:|
| identidad | 3,6 | 2,4 |
| reglas_flo | 17,6 | 12,7 |
| reglas_equipo | 16,4 | 12,1 |
| mt5 | 18,2 | 13,3 |
| mt5_moe | 19,4 | 13,9 |
