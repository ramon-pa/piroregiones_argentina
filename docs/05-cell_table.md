# 05 · Tablas por celda, decodificadas y controladas

Convierte las tablas bajadas de GEE (27 CSV del barrido y uno de frecuencia, con códigos
empaquetados) en tres Parquet tipados y decodificados, y corre los controles que cruzan pasos. Todo
local, sin GEE. Es la única puerta de entrada de los pasos locales: el 06 en adelante lee
`TABLES_DIR` y no vuelve a los CSV.

## Entradas → Salidas

`27 CSV del paso 02 + CSV del paso 04 + grilla del paso 01` → **`05-cell_table.py --build`** →
`sweep.parquet` + `frequency.parquet` + `cells.parquet` → **`--check`**

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| Barrido, 27 años | `code`, `sum` por año | `SWEEP_DIR` |
| Frecuencia | `code`, `sum` | `FREQ_DIR` |
| Grilla | `cell`, `h3`, `h3_r5`, `area_km2`, geometría | `H3_GRID_DIR` |
| `sweep.parquet` | `cell`, `year`, `cls`, `month`, `size`, `ha`; larga, sin agregar | `TABLES_DIR` (fuera de git) |
| `frequency.parquet` | `cell`, `k` (años quemados), `ha` | `TABLES_DIR` |
| `cells.parquet` | la grilla sin geometría | `TABLES_DIR` |

## Cómo funciona

- **Decodificación** con los multiplicadores de `utils/constants.py` (D6 y paso 04), a enteros
  chicos (`int8`, `int16`, `int32`). La tabla larga no agrega nada: cualquier variable del paso 06
  sale de agrupar.
- **Controles** (`--check`, también al final de `--build`):
  - todos los años tienen todas las celdas;
  - el área total de cada celda es la misma en los 27 años (solo el redondeo del CSV la mueve);
  - las columnas vuelven a armar exactamente los códigos originales (la decodificación no pierde
    nada);
  - frecuencia y barrido coinciden a nivel nacional y en las celdas con al menos 100 ha quemadas
    (los mismos criterios del paso 04).
- **`--classes`**: área disponible, área quemada y tasa anual por clase de cobertura, nacional. Es la
  tabla de D10.

## Correr

```bash
uv run python workflow/05-cell_table.py --build     # decodifica y controla
uv run python workflow/05-cell_table.py --check     # solo los controles
uv run python workflow/05-cell_table.py --classes   # la tabla de D10
```

## Decisiones clave

- Tabla larga sin agregar (Ramón, 2026-10-26): no cierra ninguna puerta para el paso 06.
- Parquet: el formato de tablas del proyecto; 193 MB frente a ~510 MB de los CSV.
- La ecorregión de cada celda no entra acá: hace falta recién en el paso 09.

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/05-cell_table.py` | decodifica (`--build`), controla (`--check`), resume por clase (`--classes`) |
| `utils/constants.py` | multiplicadores de los códigos, `SWEEP_DIR`, `FREQ_DIR`, `TABLES_DIR` |

## Relacionado

- `docs/02-sweep.md`, `docs/04-frequency.md`: de dónde vienen las tablas.
- `docs/decisions.md`: D6 (el código), D10 (la tabla por clase).
