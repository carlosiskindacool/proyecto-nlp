# Chilenismos → español neutro

Traducir oraciones con jerga chilena (*«el carrete estuvo fome»*) a español neutro (*«la fiesta estuvo aburrida»*) con mT5 y una variante con *sparse Mixture of Experts*. Proyecto del curso de PLN (UC Chile).

## Estado

**Ahora estamos en la fase de generación del dataset**, es decir, los pares chileno → neutro con que se entrenará el modelo.

- [x] Diccionario de chilenismos: el automático y el curado (este último, solo el libro 1 de 5).
- [ ] **Ejecutar el flujo de generación de pares.** `oraciones.py`, `borrador.py` y `dividir.py` están escritos, pero **nunca se han ejecutado**, y **nadie ha revisado todavía un borrador a mano**.
- [ ] EDA del dataset (ver más abajo).
- [ ] **Modelos.** Falta implementar el fine-tune de mT5 y la variante mT5 + sparse MoE. Hoy solo existe mT5 *sin entrenar*, dentro de los [baselines](docs/baselines.md).

## Flujo de generación del dataset

```
diccionario.py → oraciones.py → borrador.py → (revisión humana) → dividir.py
```

Todos los scripts están en `src/chilenismos/` y toman sus rutas por defecto de [`rutas.py`](src/chilenismos/rutas.py).

| Paso | Qué hace | Entrada | Salida |
|---|---|---|---|
| 1. `diccionario.py` | Arma un diccionario de chilenismos. | API de **Wikcionario** (es, categoría ES:Chile) y **Wiktionary** (en, Chilean Spanish). La caché queda en `data/raw/cache_{es,en}.jsonl`. | `data/processed/diccionario.csv` (automático, escenario `equipo`) |
| | *Curado a mano (ya hecho, sin script)* | Wikcionario, Wiktionary vía kaikki.org y el diccionario de **Román** (respaldo en `data/diccionario/`) | `data/curado/diccionario_flo_parte1.csv` (escenario `flo`, el que se usa por defecto). Detalle en [docs/diccionario_curado.md](docs/diccionario_curado.md). |
| 2. `oraciones.py` | Busca en el corpus oraciones que contienen términos del diccionario. | **Chilean Spanish Corpus** (`.parquet`) en `data/raw/corpus/`, más el diccionario | `data/interim/candidatas.csv` (`termino;oracion;fuente`) |
| 3. `borrador.py` | Un **LLM** propone la versión neutra de cada oración, con el diccionario como contexto. | `data/interim/candidatas.csv` y el diccionario | `annotation/borrador.csv` (`termino;oracion;neutro;revisor1;revisor2`) |
| *Revisión humana* | Una persona corrige `neutro` y anota su nombre en `revisor1`. | `annotation/borrador.csv` | `annotation/pares_revisados.csv` |
| 4. `dividir.py` | Separa los pares revisados en train / val / test. | `annotation/pares_revisados.csv` | `data/processed/{train,val,test}.csv` |

## Decisiones pendientes

**`diccionario.py` / diccionario curado**
1. Los libros 2 a 5 del diccionario curado (unos 2.600 términos, los menos frecuentes) siguen sin revisar. Hay que decidir si vale la pena hacerlo.

**`oraciones.py`**
1. Hoy busca las oraciones por coincidencia exacta con los términos del diccionario. Mejora: cambiarlo por una búsqueda más apropiada (que reconozca, por ejemplo, conjugaciones y variantes de escritura).
2. Hoy, si un texto contiene más de un término, sale repetido en la salida, una vez por término. Mejora: evitar los duplicados.
3. Hoy no filtra los textos del corpus por datos personales ni por contenido de odio. Mejora: implementar esos dos filtros.

**`borrador.py` / revisión humana**
1. Por ahora hay un solo revisor, así que no se puede medir el acuerdo entre personas. Hay que declararlo como limitación, o bien pedir a una segunda persona que revise una muestra del test.

**`dividir.py`**
1. Hoy la división es al azar. Mejora: hacer una división que asegure que las oraciones de cada término queden bien repartidas entre train, val y test.

## EDA (después de generar los datos)

Hay que hacerlo en dos momentos. Los cuadernos van en `notebooks/` y las figuras en `reports/figures/`.

1. **Después de `oraciones.py`**, antes de gastar LLM y revisión humana. El objetivo es decidir los filtros y el muestreo.
   - Cuántas oraciones hay por término y qué términos quedan sin ninguna (cobertura del diccionario).
   - De qué fuente del corpus vienen (mc4, noticias, reclamos).
   - Largo de las oraciones y duplicados.
2. **Después de `dividir.py`**, sobre el dataset final.
   - Tamaño de cada división y cuántos términos distintos hay en cada una.
   - Distribución de términos por división, y términos de test que no aparecen en train.
   - Cuánto cambia cada par, medido como la proporción de palabras distintas entre `chileno` y `neutro`, y en cuántos pares no cambia nada.
   - Cuánto corrigió el revisor el borrador del LLM, medido como el porcentaje de borradores editados.

## Estructura del repo

```
proyecto-nlp/
├── README.md
├── requirements.txt
├── src/chilenismos/
│   ├── rutas.py            todas las rutas y los diccionarios (equipo / flo)
│   ├── dicc.py             carga un diccionario y arma las reglas
│   ├── diccionario.py      paso 1
│   ├── oraciones.py        paso 2
│   ├── borrador.py         paso 3 (usa llm.py)
│   ├── dividir.py          paso 4
│   ├── llm.py              llamadas al LLM (backend claude-code o anthropic)
│   └── baselines.py, baselines_llm.py   comparación preliminar (docs/baselines.md)
├── data/
│   ├── raw/                caché de Wikcionario y corpus (no se sube a git)
│   ├── interim/            candidatas.csv (no se sube a git)
│   ├── processed/          diccionario automático, train/val/test y predicciones (no se sube a git)
│   ├── curado/             diccionario curado y términos descartados
│   └── diccionario/        respaldo del trabajo de curación (ningún script lo lee)
├── annotation/             lote1.csv (pares de evaluación), borrador.csv, pares_revisados.csv
├── reports/                comparacion_baselines.csv y figures/
├── docs/                   diccionario curado, baselines y diagramas
├── notebooks/              EDA (pendiente)
├── models/                 mT5 y mT5 + sparse MoE (pendiente)
├── configs/, tests/        vacías
```

## Cómo correr

Los comandos se pueden lanzar desde cualquier carpeta.

```
pip install -r requirements.txt
python src/chilenismos/diccionario.py                # 1
python src/chilenismos/oraciones.py                  # 2  (corpus en data/raw/corpus/ o --corpus RUTA)
python src/chilenismos/borrador.py --seco            # 3  muestra el prompt sin llamar al LLM
python src/chilenismos/borrador.py                   # 3
#   revisión humana: annotation/borrador.csv -> annotation/pares_revisados.csv
python src/chilenismos/dividir.py                    # 4
```

`--escenario equipo|flo` elige el diccionario (por defecto, `flo`).

## Licencias y datos

Wikcionario y Wiktionary son CC BY-SA, así que el diccionario derivado se publica con la misma licencia. Román (1901–1918) es dominio público.
El *Chilean Spanish Corpus* es CC-BY-SA-4.0 y no se redistribuye. `oraciones.py` excluye los tuits por defecto; antes de usarlos hay que consultar al profesor. Las claves de API van siempre en variables de entorno.
