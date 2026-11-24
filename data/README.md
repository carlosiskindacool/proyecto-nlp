# data

Datos del proyecto. Visión general: [`../README.md`](../README.md).

## Qué hay en cada carpeta

| Carpeta | Contenido | ¿Se sube a git? |
|---|---|---|
| [`curado/`](curado/) | **El diccionario revisado a mano** (libro 1 y repartos 2 a 5): `diccionario_flo.csv` (1.985 filas con definición, reemplazo, marca de ambiguo, variantes y quién lo revisó) y `terminos_descartados.csv` (1.327 que se quitan o se unifican). Es lo que leen los sistemas B y C. | Sí |
| [`diccionario/`](diccionario/) | El trabajo previo de revisión: términos unidos, acepciones del Wikcionario, entradas de Román y el resumen de las reglas de ortografía. Ningún sistema lo lee; es respaldo y documentación. | Solo en parte (ver abajo) |
| `raw/` | Descargas que hace `src/chilenismos/diccionario.py` (la caché del Wikcionario). | No |
| `interim/` | Intermedios: candidatas de oraciones (`candidatas_*.csv`) y `borrador_entrenamiento.csv`, los pares con que se entrena mT5. Pueden traer texto de tuits. | Solo `borrador_entrenamiento.csv` y `candidatas_entrenamiento.csv` |
| `processed/` | Salidas de los scripts: `diccionario.csv` del equipo, `predicciones_*.csv` y `eval_extrinseca.csv`. | Sí, esos archivos (con `git add -f`); el resto no |

## `curado/diccionario_flo.csv`

| Columna | Qué es |
|---|---|
| `termino` | El término (los pares verbo / verbo-se se separan en dos filas) |
| `grupo` | El término unido original, si venía como «verbo / verbo-se» |
| `tipo` | `verbo`, `adjetivo_participio`, `especie` u `otro` |
| `definicion` | La definición final, ya corregida |
| `reemplazo` | Palabra neutra que lo sustituye; admite alternativas por sentido separadas por `\|`. Vacío si no hay equivalente estable |
| `ambiguo` | 1 si la palabra también se usa mucho con su sentido estándar: el baseline de reglas no la sustituye |
| `reemplazo_por` | Quién escribió el reemplazo: `Flo`, `integrante 2/4`, `Claude`, o `integrante N, corregido/normalizado por Claude` |
| `reemplazo_validado` | 1 si Flo validó el reemplazo |
| `keep` | Siempre 1 |
| `variantes` | Formas escritas alternativas (solo para no-verbos) |
| `n_tuits_muestra` | En cuántos tuits de la muestra aparece |
| `frecuencia` | alta / media / baja (solo repartos 2 a 5) |
| `reviso` | Quién decidió: `Flo`, `integrante 2/3/4` o `Claude (validado por Flo)` |
| `notas` | Notas de la revisión |

Más detalle en [`../archivo/README_flo.md`](../archivo/README_flo.md).

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

## Cómo se revisó cada parte de `curado/`

- **Libro 1** (443 filas en el diccionario, 220 descartados): lo revisó Flo palabra por palabra (`reviso = Flo`).
- **Repartos 2 a 5** (1.542 filas en el diccionario, 1.106 descartados): cada integrante del equipo revisó un reparto (`reviso = integrante 2, 3 o 4`); las que nadie revisó las propuso Claude y Flo las validó (`reviso = Claude (validado por Flo)`); las de más frecuencia las decidió Flo (`reviso = Flo`).
- `reemplazo_validado` = 1 si Flo validó el reemplazo; 0 si es propuesta de Claude que Flo aún no valida (los reemplazos escritos por integrantes cuentan como revisados por Flo; `reemplazo_por` dice quién los escribió); vacío si no hay reemplazo (especies, comidas típicas y términos sin equivalente). Los reemplazos de los repartos 2 a 5 son en su mayoría propuestas de Claude.
- Los pares «verbo / verbo-se» se separan en dos filas con el mismo `grupo` y el mismo reemplazo (que reúne los sentidos de ambas formas; conviene revisarlo por forma).
- `variantes` solo se llena para no-verbos. `frecuencia` (alta/media/baja) solo existe para los repartos 2 a 5.
- En `terminos_descartados.csv`, `decision` es `quitar` o `unificar` (5 casos: se juntan con otra entrada, indicada en `nota`); en el libro 1 es el texto original de Flo («no», «no, es un pueblo»…).
