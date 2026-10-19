# 01 · Grilla de hexágonos H3

Produce la grilla de celdas sobre la que se suman todas las áreas del trabajo: los hexágonos H3 de
resolución 6 que tocan la Argentina continental, numerados con un id entero. Consume solo las
ecorregiones (para el contorno del país). Es el primer paso: el barrido D6 (paso 02) y la
frecuencia (paso 04) pintan esta grilla en GEE; los pasos locales la usan para unir tablas y
dibujar.

## Fundamentos

H3 y la resolución están en D1 (`decisions.md`). Lo propio de este paso es que la grilla se arma en
Python y no en GEE: H3 no existe en GEE, y una colección de ~96 mil polígonos armada en memoria no
se puede exportar a asset (límite de ~17k features, `gee-gotchas.md`). Por eso se escribe un
shapefile y se sube a mano.

## Entradas → Salidas

`ecorregiones (13)` → **`01-hex_grid.py --build`** → `h3_res6.parquet` + `h3_res6.zip` → subida
manual → asset `H3_GRID_ASSET` → **`--check`**

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| Ecorregiones 13 | contorno del país (menos Islas del Atlántico Sur, simplificado) | `ECOREGIONS_13`, `utils/aoi.py` |
| `h3_res6.parquet` | grilla completa para trabajo local: `cell`, `h3`, `h3_r5`, `area_km2` | `H3_GRID_DIR` (fuera de git) |
| `h3_res6.zip` | shapefile para GEE: solo `cell` y `h3` | `H3_GRID_DIR` |
| Asset de la grilla | la misma grilla en GEE | `H3_GRID_ASSET` |

## Cómo funciona

- **Qué celdas.** Las que tocan el polígono del país (`contain="overlap"`), no solo las que tienen
  el centro adentro: así ningún píxel del borde queda sin celda. Las celdas del borde salen en
  parte del país; no importa, porque todo se suma por área real y las tasas usan el área disponible.
- **Ids.** Las celdas se ordenan por índice H3 y se numeran 0..N−1. El id entero es lo que entra al
  código empaquetado de D6; el índice H3 viaja al lado para unir de vuelta. El orden es
  determinístico: volver a correr da los mismos ids si el polígono no cambia.
- **Controles al construir** (cortan el script si fallan): sin celdas repetidas, sin pentágonos, y
  el código máximo de D6 entra en 32 bits.
- **Controles después de subir** (`--check`, solo lectura): el asset tiene exactamente las mismas
  celdas con los mismos ids que el parquet local, y pintado en GEE no deja huecos en el recuadro de
  Córdoba de la prueba del barrido.

## Correr

```bash
uv run python workflow/01-hex_grid.py --build
# subir data/h3_grid/h3_res6.zip en el Code Editor: Assets > NEW > Shape files,
# con el id de H3_GRID_ASSET (utils/constants.py)
uv run python workflow/01-hex_grid.py --check
```

## Decisiones clave

- Celdas que tocan el país, no solo las de centro adentro: ningún píxel sin celda.
- Ids por orden de índice H3: reproducibles sin guardar estado.
- Al shapefile van solo `cell` y `h3`: lo demás se calcula local, y el asset ocupa cuota.

## Trampas

- **`contain="overlap"` repite celdas.** `h3` devuelve una celda una vez por cada polígono que toca,
  y el país son 176 polígonos: en res 6 eran 182 copias. Se deduplica antes de numerar. Lo detectó el
  control de este paso, y corrigió los conteos del 17-oct (`docs/notes/01-grid_and_compute.md`).
- **Res 5 no es "hexágonos de res 5".** Los 7 hijos de res 6 no llenan exacto su padre de res 5:
  su unión tiene forma de copo. La res 5 se arma sumando las áreas de los hijos (`h3_r5`), que es
  exacto; si el mapa final va en res 5, cada celda se dibuja como la unión de sus hijos, nunca con
  el contorno H3 de res 5. Por eso hay más padres (`h3_r5` distintos) que celdas de res 5 que tocan
  el país.

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/01-hex_grid.py` | arma la grilla (`--build`) y controla el asset subido (`--check`) |
| `utils/aoi.py` | el polígono del país, compartido con `scripts/h3_cells_argentina.py` |
| `utils/constants.py` | `H3_RES`, `H3_GRID_DIR`, `H3_GRID_ASSET`, `AOI_*` |

## Relacionado

- `docs/decisions.md`, D1 (por qué H3 y res 6) y D6 (el código que usa el id).
- `docs/notes/01-grid_and_compute.md`: conteos de celdas y deformación de H3.
