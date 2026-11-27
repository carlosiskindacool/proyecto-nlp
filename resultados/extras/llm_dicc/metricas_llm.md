Métricas por palabra sobre texto normalizado (NFKC, minúsculas, sin puntuación), de 0 a 100. ERR según van der Goot (2019) y MultiLexNorm (W-NUT 2021).

### lote1 (213 pares, 4145 palabras, 303 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| llm_gemini | 25,1 | 46,8 | 47,5 | 47,1 | 89,5 | 93,1 |
| llm_haiku | 6,9 | 39,2 | 53,8 | 45,3 | 87,4 | 91,6 |
| llm_sonnet | 31,0 | 48,8 | 52,8 | 50,7 | 90,5 | 93,6 |

### lote_1_noticias (72 pares, 1789 palabras, 46 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| llm_gemini | 26,1 | 55,3 | 56,5 | 55,9 | 95,8 | 97,3 |
| llm_haiku | -54,3 | 31,3 | 67,4 | 42,8 | 91,5 | 94,8 |
| llm_sonnet | 17,4 | 52,7 | 63,0 | 57,4 | 95,4 | 97,4 |

### lote_1_tuits (165 pares, 2668 palabras, 262 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| llm_gemini | 33,2 | 55,4 | 49,2 | 52,1 | 86,8 | 91,8 |
| llm_haiku | 1,1 | 38,1 | 54,6 | 44,9 | 81,6 | 88,4 |
| llm_sonnet | 33,6 | 54,7 | 58,0 | 56,3 | 88,6 | 92,4 |

### lote_1_2_noticias (77 pares, 1950 palabras, 50 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| llm_gemini | 24,0 | 55,3 | 52,0 | 53,6 | 95,8 | 97,3 |
| llm_haiku | -46,0 | 32,0 | 66,0 | 43,1 | 91,9 | 95,1 |
| llm_sonnet | 20,0 | 54,4 | 62,0 | 57,9 | 95,7 | 97,5 |

### lote_1_2_tuits (308 pares, 5083 palabras, 454 por normalizar)

| Sistema | ERR | Precisión | Recall | F1 | BLEU | chrF |
|---|---:|---:|---:|---:|---:|---:|
| llm_gemini | 33,9 | 56,8 | 51,5 | 54,0 | 88,2 | 92,3 |
| llm_haiku | 9,5 | 42,1 | 58,6 | 49,0 | 84,6 | 90,2 |
| llm_sonnet | 46,9 | 63,3 | 63,9 | 63,6 | 91,3 | 94,2 |
