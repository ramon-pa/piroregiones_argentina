# 07 · Las pirorregiones

Agrupa las celdas H3 de res 5 en regiones continuas con un régimen de fuego parecido. Consume las
variables por celda del paso 06 calculadas a res 5 (`variables_r5.parquet`) y la grilla de res 6, y
produce el mapa de pirorregiones, sus polígonos y una tabla resumen por región que sirve para
nombrarlas. El paso 09 compara este mapa con las ecorregiones.

## Fundamentos

El método es REDCAP de orden completo con enlace de Ward, el de Boulanger et al. 2014: un
agrupamiento jerárquico que solo une celdas vecinas, así que cada región sale de una sola pieza, con
un tamaño mínimo medido en área (D5). Corre a res 5 porque a res 6 no entra en la Mac (D13,
`docs/notes/07-redcap_scaling.md`).

## Entradas → Salidas

`variables_r5.parquet + h3_res6.parquet` → **`07-regions.py --build`** → regiones, polígonos,
resumen, mapa

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| `variables_r5.parquet` | variables del paso 06 a res 5 (`06-variables.py --res 5`) | `TABLES_DIR` |
| `h3_res6.parquet` | la grilla de res 6, con el padre de res 5 de cada celda | `H3_GRID_DIR` |
| `regions_r5_k<k>.parquet` | celda de res 5, índice H3, región (1 a k, de norte a sur) | `REGIONS_DIR` |
| `regions_r5_k<k>_polygons.parquet` | un polígono por región (GeoParquet, EPSG:4326) | `REGIONS_DIR` |
| `summary_r5_k<k>.csv` | área y régimen de cada región | `REGIONS_DIR` |
| `k_curve_r5.csv` | varianza explicada para k = 5 a 30 (`--curve`) | `REGIONS_DIR` |
| `07-regions_r5_k<k>.png` | el mapa | `outputs/` |

## Cómo funciona

- **Celdas y vecinas.** Cada celda de res 5 es la unión de sus 7 hijos de res 6 (D1). Dos celdas
  son vecinas si algún hijo de una comparte un lado con algún hijo de la otra (vecindad tipo torre,
  sacada de H3, no de los polígonos).
- **Islas.** REDCAP necesita un grafo conectado. Cada componente suelta se une a la celda más cercana
  de afuera, por distancia entre centros. El script informa cada unión.
- **Celdas casi sin área quemable** (menos de `MIN_BURNABLE_SHARE`): fuera del agrupamiento; después
  toman la región vecina más común (D14).
- **Variables.** Las 7 de fuego y las 6 proporciones por familia del paso 06; tasa y recurrencia en
  logaritmo (D14); todo en puntaje z. Las
  familias se multiplican por `COMPOSITION_WEIGHT` (D12). REDCAP recibe la matriz con
  `scale_method='raw'`, porque por defecto estandariza y borraría el peso.
- **Agrupamiento.** `pygeoda.redcap`, `fullorder-wardlinkage`, k = `REGIONS_K`, con el área de cada
  celda como variable de tamaño y `MIN_REGION_KM2` como mínimo. Las regiones se numeran por la
  latitud de su centro, de norte a sur.
- **Piezas forzadas** (`--force`, D14 y D15): cada punto de `FORCED_SPLIT_POINTS` toma su región del
  nivel k que lleva (20 las patagónicas, 25 el Delta) y pasa a ser una región propia. Después, las
  celdas fuera del agrupamiento se reasignan sobre el mapa final.
- **Nombres y colores** (`PYROREGION_NAMES`): cada nombre propuesto va atado a un punto dentro de su
  región, no al número. Si todas las regiones del mapa tienen exactamente un nombre, el mapa los usa
  con sus colores; si no (otro k), quedan sin nombre y con la paleta.
- **Resumen por región.** La tasa de quema es exacta (área quemada sobre área quemable, sumadas). El
  resto son promedios de las variables de celda ponderados por área (quemable o quemada, según la
  variable): una primera mirada, no la ficha de D12.
- **Controles.** Todas las celdas tienen región y hay k regiones; ninguna región es menor que el
  mínimo; cada región es una sola pieza en el grafo; las áreas suman la de la grilla. Se informa
  qué regiones quedan unidas solo a través de una isla.

## Correr

```bash
uv run python workflow/06-variables.py --build --res 5   # antes, una vez
uv run python workflow/07-regions.py --build             # k = REGIONS_K
uv run python workflow/07-regions.py --build --k 20      # otro k
uv run python workflow/07-regions.py --build --k 12 --force   # el mapa elegido: k = 12 + 3 (D14, D15)
uv run python workflow/09-ecoregions.py --overlay --k 12 --forced
uv run python workflow/07-regions.py --build --k 12 --force   # otra vez: la leyenda lee las provincias del 09
uv run python workflow/07-regions.py --curve             # k = 2 a 30, un proceso por k, ~10 min
uv run python scripts/region_review.py --splits 21       # el árbol de particiones
uv run python scripts/region_review.py --burned-once 12  # quemado al menos una vez con los bordes
uv run python workflow/09-ecoregions.py --overlay --k 12 --forced   # provincias y ecorregiones
```

## Decisiones clave

- Res 5 con REDCAP y no res 6 con otro método: D13.
- Islas unidas a la celda más cercana: elección nuestra, sin paper.
- Vecindad tipo torre: los hexágonos no tienen vecinos solo por un vértice, así que torre y reina
  dan lo mismo.
- Un color por región (`PALETTE`, hasta 16), con una tabla de referencia dentro del mapa: color,
  número, provincias y ecorregiones con al menos `LEGEND_MIN_SHARE` % del área (del archivo `places`
  del paso 09, si existe) y tasa. Antes era coloreo de grafo, con colores repetidos.

## Trampas

- **pygeoda con varios hilos se cae.** Con los hilos por defecto, REDCAP se cortó con un
  `std::length_error` de C++ en un k al azar (16, 7, y también con un proceso por k). Con
  `cpu_threads=1` corrieron k = 5 a 30 con los mismos valores. Ver la nota del paso.
- **`read_gal` necesita el encabezado completo** (`0 N capa campo`) y los ids como texto; si no,
  devuelve un objeto vacío sin avisar.
- **La unión de los hexágonos deja costuras.** Los lados compartidos no coinciden exacto: la unión
  rápida (`coverage`) falla y la común deja líneas finas cruzando las regiones. Se une sobre una
  grilla de precisión de 1e-7°.

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/07-regions.py` | grafo, REDCAP, polígonos, resumen, mapa, curva de k y controles |
| `workflow/06-variables.py` | `--res 5`: las variables a res 5 |
| `utils/constants.py` | `REGIONS_RES`, `REGIONS_K`, `MIN_REGION_KM2`, `COMPOSITION_WEIGHT`, `REGIONS_DIR`, `FORCED_SPLIT_POINTS`, `PYROREGION_NAMES` |
| `scripts/region_review.py` | revisión del mapa: quemado al menos una vez, árbol de particiones, regiones parecidas |

## Relacionado

- `docs/decisions.md`: D1, D5, D12, D13, D14, D15.
- `docs/notes/07-redcap_scaling.md`: por qué res 5.
- `docs/notes/07-regions_draft.md`: los borradores, medidos, de k = 15 al mapa de 15 regiones.
