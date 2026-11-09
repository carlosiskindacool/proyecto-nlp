# data

Datos del proyecto. Visión general: [`../README.md`](../README.md).

## Qué hay en cada carpeta

| Carpeta | Contenido | ¿Se sube a git? |
|---|---|---|
| [`curado/`](curado/) | **El diccionario revisado a mano** (libro 1): `diccionario_flo_parte1.csv` (443 filas con definición, reemplazo, marca de ambiguo y variantes) y `terminos_descartados_parte1.csv` (los 220 que no entran). Es lo que leen los sistemas B y C. | Sí |
| [`diccionario/`](diccionario/) | El trabajo previo de revisión: términos unidos, acepciones del Wikcionario, entradas de Román y el resumen de las reglas de ortografía. Ningún sistema lo lee; es respaldo y documentación. | Solo en parte (ver abajo) |
| `raw/` | Descargas que hace `src/chilenismos/diccionario.py` (la caché del Wikcionario). | No |
| `interim/` | Intermedios: candidatas de oraciones (`candidatas_*.csv`). Pueden traer texto de tuits. | No |
| `processed/` | Salidas de los scripts: `diccionario.csv` del equipo, `predicciones*.csv`, y el borrador de entrenamiento en `interim/`. | No |

## `curado/diccionario_flo_parte1.csv`

| Columna | Qué es |
|---|---|
| `termino` | El término (los pares verbo / verbo-se se separan en dos filas) |
| `grupo` | El término unido original, si venía como «verbo / verbo-se» |
| `tipo` | `verbo`, `adjetivo_participio`, `especie` u `otro` |
| `definicion` | La definición final, ya corregida |
| `reemplazo` | Palabra neutra que lo sustituye; admite alternativas por sentido separadas por `\|`. Vacío si no hay equivalente estable |
| `ambiguo` | 1 si la palabra también se usa mucho con su sentido estándar: el baseline de reglas no la sustituye |
| `reemplazo_validado` | 1 si Flo validó el reemplazo |
| `keep` | Siempre 1 |
| `variantes` | Formas escritas alternativas (solo para no-verbos) |
| `n_tuits_muestra` | En cuántos tuits de la muestra aparece |
| `notas` | Notas de la revisión |

Más detalle en [`../README_flo.md`](../README_flo.md).

## `diccionario/`

```
diccionario/
├── crudo/                    descargas en bruto                                 (no se sube)
├── procesado/
│   ├── terminos.csv, es_acepciones_chile.csv, en_acepciones_chile.csv, roman_entradas.jsonl   (se suben)
│   ├── es_acepciones.jsonl, terminos.jsonl   intermedios y duplicados            (no se suben)
│   ├── variantes_parte*.xlsx                  planillas de revisión              (no se suben: traen tuits)
│   ├── revision/                              los 5 libros por frecuencia y lo ya revisado (no se suben)
│   ├── informes/, reemplazadas/               registros y copias de seguridad    (no se suben)
└── reglas_medicion/          medición de las reglas de ortografía; solo `resumen_por_regla.csv` se sube
```

Los Excel no se suben porque incluyen ejemplos tomados de tuits, y **Flo los guarda fuera del repo**, en `PLN/Proyecto/archivos_fuera_del_repo/data/diccionario/` (con esta misma estructura). Aquí solo quedan `terminos.csv`, las acepciones, `roman_entradas.jsonl` y el resumen por regla. Los detalles están en el `.gitignore` de la raíz.

## Licencias

El Wikcionario y Wiktionary son CC BY-SA, así que el diccionario derivado se publica con la misma licencia. Román (1901–1918) es dominio público.
El *Chilean Spanish Corpus* (CC-BY-SA-4.0) no se redistribuye: no hay corpus ni texto de tuits en el repo.
