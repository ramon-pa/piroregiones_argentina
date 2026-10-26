# 02 · Área disponible y quemada por celda, cobertura, mes y tamaño

Produce, para cada año de fuego, una tabla con el área de cada combinación de celda H3, clase de
cobertura del año previo, mes de quema y clase de tamaño de cicatriz. De ella salen el área
disponible por cobertura (sumando todas las filas de una celda y clase) y el área quemada (las filas
con mes > 0): son los pasos 02 y 03 de `00-overview.md` en una sola pasada. Consume la grilla del
paso 01 y tres insumos en la grilla nativa. Lo usan todos los pasos locales que arman variables.

## Fundamentos

Por qué un solo barrido por año y por qué el mes se queda en el código: D6 (`decisions.md`). Por qué
las tablas van a Drive y no a asset: D7. La forma del cómputo (todo el cruce en un entero, una
reducción agrupada, el territorio pintado, un rectángulo como geometría) es la del equipo de fuego,
`statistics/burnable_export.py`.

## Entradas → Salidas

`mes de quema (Y) + tamaño (Y) + cobertura (Y−1) + grilla H3` → **`02-sweep.py --export`** →
CSV en Drive → **`--fetch`** (baja y corre `--check`)

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| Mes de quema | `fire_mask_v2` del año Y, 0 = no quemado | `MONTH_OF_BURN_*` |
| Clase de tamaño | banda del año Y, 1 a 8, 0 = no quemado | `SCAR_SIZE*` |
| Cobertura | col-3, banda del año Y−1, 0 = no observada | `LULC*`, `LULC_YEAR_OFFSET` |
| Grilla | celdas H3 res 6 con su id | `H3_GRID_ASSET` |
| Tabla por año | `code`, `sum` (ha) | Drive `DRIVE_FOLDER`, luego `SWEEP_DIR` (fuera de git) |

## Cómo funciona

- **El código.** `celda × CODE_CELL + clase × CODE_CLASS + mes × CODE_MONTH + tamaño`
  (`utils/constants.py`). Se decodifica en Python con divisiones enteras.
- **Máscaras.** Mes, tamaño y cobertura pasan por `unmask(0)`. Lo único que enmascara es la grilla
  pintada: un píxel fuera de toda celda no entra, y uno dentro siempre entra.
- **Geometría.** El rectángulo fijo `GRID_BBOX`. Fuera de las celdas el código está enmascarado, así
  que el rectángulo no agrega cómputo.
- **Una tarea por año**, `Export.table.toDrive`, con el nombre `SWEEP_TASK`. Un año cuya tarea ya
  está esperando, corriendo o terminada se saltea.
- **Controles** (`--check`, sobre el CSV bajado, sin GEE):
  - todo código decodifica en rango y toda clase está en alguna lista;
  - 0 ha con mes y sin tamaño, o al revés;
  - el área total de cada celda iguala su área H3 del parquet (tolerancia `CELL_AREA_TOL` del
    script: H3 es esférico, `pixelArea()` elipsoidal), y no falta ninguna celda.
  - Informa el área quemada sobre clases no quemables o no observadas (D9).

## Correr

```bash
uv run python workflow/02-sweep.py --export --years 2025
uv run python workflow/02-sweep.py --status
uv run python workflow/02-sweep.py --fetch --years 2025   # baja de Drive y corre --check
uv run python workflow/02-sweep.py --check --years 2025   # solo los controles, sin red
uv run python workflow/02-sweep.py --summary              # quemado por año y suma contra el equipo de fuego
```

## Decisiones clave

- Un año nacional primero, para medir memoria, filas y tiempo antes de lanzar los 27 (`ROADMAP.md`).
- La grilla se pinta en cada tarea; si resulta lento, se guarda el ráster de ids (D7).
- El CSV se baja con las credenciales de GEE de la máquina, que ya traen permiso de Drive (igual que
  `burnable_export.py --fetch` del equipo de fuego). El conector de Drive de Claude no sirve: pasa
  el archivo por la conversación, y una tabla nacional pesa decenas de MB.

## Trampas

- **Lo no quemado viene enmascarado**: sin `unmask(0)` el área disponible saldría solo de lo
  quemado (D6).
- **`unmask(0)` solo rellena dentro de la huella del asset.** Fuera de ella el píxel sigue
  enmascarado y se cae de la suma sin aviso. La primera corrida de 2025 perdió área en 17 celdas de
  los bordes (Santa Cruz oeste, el extremo norte, Misiones, Tierra del Fuego; la peor con 2 % de su
  área). Se usa `unmask(0, False)` (`sameFootprint=False`); lo detectó el control de área por celda.
- **`.geometry().bounds()` sobre la grilla** falla por demasiados vértices: por eso `GRID_BBOX` fijo.

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/02-sweep.py` | lanza las tareas (`--export`), las lista (`--status`), baja las tablas (`--fetch`), las controla (`--check`) y resume lo quemado (`--summary`) |
| `utils/constants.py` | insumos, multiplicadores del código, `GRID_BBOX`, `SWEEP_TASK`, `SWEEP_DIR` |

## Relacionado

- `docs/decisions.md`: D4, D6, D7, D9.
- `docs/notes/02-sweep_cordoba.md`: la prueba del barrido en Córdoba.
- `docs/notes/03-sweep_national.md`: la corrida nacional, los controles y la serie anual.
- `scripts/bench_interactive.py --sweep`: la misma cuenta, interactiva, en el recuadro de Córdoba.
