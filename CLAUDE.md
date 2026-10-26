# CLAUDE.md · Pirorregiones de Argentina

Índice y reglas del proyecto. Es el documento para reorientarse al empezar cada sesión.
Qué hacer después: [`ROADMAP.md`](ROADMAP.md). Por qué se decidió algo: [`docs/decisions.md`](docs/decisions.md).
Qué dice cada paper: [`docs/references.md`](docs/references.md).

Regla de este archivo: cada afirmación lleva su fuente. Lo no verificado se marca **[no verificado]**.

---

## 1. Overview

Objetivo: el **mapa de pirorregiones de Argentina**, regiones continuas con límites, análogas a las
ecorregiones, definidas por cómo se quema el territorio (cuánto, cada cuánto, cuándo, de qué tamaño
y qué cobertura). Pregunta: ¿el fuego se organiza según las ecorregiones o tiene su propia geografía?

Destino: **trabajo final del curso Geo Data Scientist de Geo Dojo** y presentación en el **taller de
MapBiomas**. **No es un paper**: según Iván (2026-10-17), en la red MapBiomas ya hay gente trabajando
en pirorregiones y publicar por cuenta propia sería demasiado agresivo.

Insumos: MapBiomas Argentina Fuego colección 1 (`_v2`) y cobertura MapBiomas Argentina colección 3,
a 30 m (sección 4).

Motivación: el antecedente más cercano en Argentina (Naval-Fernández et al. 2025) cubre solo el
Chaco, con MODIS a 500 m, sin cobertura y sin regiones continuas. Ver `docs/references.md`.

## 2. Current state (2026-10-26)

- Esqueleto del repo creado, siguiendo la organización del repo de fuego de Iván. Repo git local
  con remoto `git@github.com:ramon-pa/piroregiones_argentina.git` (privado).
- Paso 00 listo: `scripts/check_assets.py` verifica todos los insumos de GEE y la carpeta de salida
  (9/9 el 2026-10-19).
- Grilla y cómputo medidos sin exportar nada (`docs/notes/01-grid_and_compute.md`).
- Qué corre en GEE, definido: barrido D6 por año (con mes y tamaño), frecuencia desde el producto
  publicado (D8), salidas según D7. Nada exportado todavía.
- Barrido D6 probado en Córdoba con hexágonos reales: todos los controles en verde
  (`docs/notes/02-sweep_cordoba.md`).
- Paso 01 listo: grilla H3 res 6 (96.461 celdas, `docs/01-hex_grid.md`) subida al asset `h3_res6`;
  `workflow/01-hex_grid.py --check` 2/2 el 2026-10-26.
- Paso 02 listo (`docs/02-sweep.md`): los 27 años corridos, bajados a `data/sweep/` y controlados
  (27/27); la suma 1999 a 2025 coincide con el equipo de fuego (`docs/notes/03-sweep_national.md`).
- Paso 04 listo (`docs/04-frequency.md`): frecuencia por celda bajada a `data/frequency/`, 2/2
  controles; coincide con el paso 02 (`docs/notes/04-frequency.md`).
- Paso 05 listo (`docs/05-cell_table.md`): tablas decodificadas en `data/tables/`, 5/5 controles.
  Desde acá todo es local.
- Decisiones: `docs/decisions.md` (D1, D2, D4, D6 a D10 acordadas; D3 y D5 abiertas).
- Próximo: `ROADMAP.md`.

Página de seguimiento: https://claude.ai/artifact/Eqz68NSP4Y8vRDLTqRL5m5 (compartida por link).
Es una vista de este repo; si difieren, manda el repo.

## 3. File inventory

| Archivo | Qué es |
|---|---|
| `CLAUDE.md` | este índice |
| `README.md` | mapa del repo e instalación |
| `ROADMAP.md` | qué hacer después, en orden |
| `BACKLOG.md` | ideas sin agendar |
| `pyproject.toml`, `uv.lock`, `.python-version` | entorno (uv, Python 3.12); dependencias solo cuando un paso las necesita |
| `.env.example` | variable `GEE_PROJECT` opcional |
| `utils/constants.py` | **única fuente de verdad**: assets, años, grilla, prefijo de tareas |
| `utils/aoi.py` | el polígono de la Argentina continental, compartido por el paso 01 y el conteo de celdas |
| `workflow/01-hex_grid.py` | paso 01: arma la grilla H3 y el zip para subir (`--build`); controla el asset (`--check`) |
| `workflow/04-frequency.py` | paso 04: frecuencia por celda desde el producto publicado; mismos modos que el 02 salvo `--summary` |
| `workflow/05-cell_table.py` | paso 05: decodifica las tablas de GEE a Parquet, controles cruzados, tabla por clase (`--classes`) |
| `utils/gee_tasks.py` | lanzador de reducciones agrupadas a Drive, estado de tareas y descarga, compartidos por los pasos 02 y 04 |
| `workflow/02-sweep.py` | paso 02: barrido D6, una tarea por año (`--export`), estado (`--status`), descarga de Drive (`--fetch`) y controles (`--check`) |
| `scripts/check_assets.py` | paso 00: chequeo de solo lectura de los insumos de GEE |
| `scripts/h3_cells_argentina.py` | cuántas celdas H3 cubren el país y cuánto varía su área |
| `scripts/bench_interactive.py` | pruebas interactivas de costo y precisión de los resúmenes por celda, y del barrido D6 (`--sweep`) |
| `docs/00-overview.md` | el método en una página y la lista de pasos |
| `docs/TEMPLATE.md` | forma de los docs de paso (adaptada del repo de fuego) |
| `docs/01-hex_grid.md` | doc del paso 01 |
| `docs/02-sweep.md` | doc del paso 02 |
| `docs/04-frequency.md` | doc del paso 04 |
| `docs/05-cell_table.md` | doc del paso 05 |
| `docs/decisions.md` | decisiones de diseño, con estado y fundamento |
| `docs/references.md` | notas por paper, con qué se leyó de cada uno; herramientas verificadas |
| `docs/notes/README.md` | convenciones del cuaderno de laboratorio |
| `docs/notes/01-grid_and_compute.md` | lo medido para elegir la grilla y la estrategia de cómputo |
| `docs/notes/02-sweep_cordoba.md` | la prueba del barrido único en Córdoba, con sus controles |
| `docs/notes/03-sweep_national.md` | la corrida nacional de los 27 años, con la serie anual |
| `docs/notes/04-frequency.md` | la corrida de la frecuencia y su comparación con el paso 02 |

## 4. GEE asset paths

Los ids que usa el código viven en `utils/constants.py`; esta sección los repite para lectura y
registra lo verificado. `scripts/check_assets.py` comprueba existencia, bandas y grilla de todos los
insumos (9/9 el 2026-10-19, proyecto `mapbiomas-argentina`, cuenta ramonpagis). La tabla de
subproductos de abajo viene de un chequeo exploratorio del 2026-10-14, completado el 2026-10-19; el
pipeline usa solo `annual_burned_scar_size_range_v2` (D6) y `frequency_burned_v2` (D8).

| Qué | Asset | Bandas | Grilla |
|---|---|---|---|
| Mes de quema, 27 imágenes (1999 a 2025) | `projects/mapbiomas-argentina/assets/FIRE/COLLECTION-1/CLASSIFICATION_COLLECTIONS/collection1_fire_mask_v2` (imágenes `mapbiomas_argentina_fire_collection1_fire_mask_v2_<año>`) | 1 por imagen | **nativa** (EPSG:4326, `SNIC_TRANSFORM`) |
| Cobertura colección 3 | `projects/mapbiomas-argentina/assets/LAND-COVER/COLLECTION-3/INTEGRATION/mapbiomas_argentina_collection3_pb` | `classification_1985` a `classification_2025` (41) | **nativa**, desfase entero (abajo) |

Subproductos `_v2`, en `projects/mapbiomas-argentina/assets/FIRE/COLLECTION-1/FINAL_PRODUCTS/mapbiomas_argentina_fire_collection1_<subproducto>_v2`:

| Subproducto | Bandas | Codificación (según `07-published_products.md`) | Grilla guardada |
|---|---|---|---|
| `annual_burned` | `burned_area_1999` a `_2025` (27) | 1 si quemado | **EPSG:3857, 30 m** |
| `monthly_burned` | `burned_monthly_1999` a `_2025` (27) | mes de quema | **EPSG:3857, 30 m** |
| `accumulated_burned`, `accumulated_burned_coverage` | `fire_accumulated_1999_1999` a `_2025_2025` (53 cada uno) | quemado al menos una vez en la ventana | **EPSG:3857, 30 m** |
| `annual_burned_coverage` | `burned_coverage_1999` a `_2025` (27) | clase del píxel quemado | **EPSG:3857, 30 m** |
| `monthly_burned_coverage` | `burned_coverage_1999` a `_2025` (27) | `mes*100 + clase` | **EPSG:3857, 30 m** |
| `frequency_burned` | `fire_frequency_1999_1999` a `fire_frequency_2025_2025` (53) | años quemados en la ventana | **EPSG:3857, 30 m** |
| `frequency_burned_coverage` | 53, mismos nombres | `frecuencia*100 + clase` (ver nota) | **EPSG:3857, 30 m** |
| `annual_burned_area_ha` | `scar_area_ha_1999` a `_2025` (27) | área de la cicatriz (ha) | nativa (transform idéntico a `SNIC_TRANSFORM`) |
| `annual_burned_id` | `scar_id_1999` a `_2025` (27) | id de cicatriz | nativa (transform idéntico a `SNIC_TRANSFORM`, 2026-10-19) |
| `annual_burned_scar_size_range` | `scar_area_ha_1999` a `_2025` (27; el nombre de banda es así a propósito, ver doc 07) | clase de tamaño 1 a 8 | nativa (transform idéntico a `SNIC_TRANSFORM`, 2026-10-19) |
| `year_last_fire` | `year_last_fire_2000` a `year_last_fire_2026` (27) | año del último fuego | nativa, desfase entero |

**Importante:** los subproductos marcados EPSG:3857 (todos los del paso 07d salvo `year_last_fire`)
**no están en la grilla nativa**. Las versiones `_v1` sí lo estaban (comprobado para
`annual_burned_coverage_v1`). El equipo de fuego **ya lo sabe**: lo midió el 17-sep-2026 y lo
documentó en `statistics/docs/statistics.md` (secciones "The grid" y el punto "EPSG:3857 is a display
grid, not a measurement grid"). Solo `docs/07-published_products.md` sigue diciendo que se exportan
con `SNIC_TRANSFORM`. Consecuencia para nosotros: cruzar fuego y cobertura desde la colección
mensual y la LULC, que están en la grilla nativa. Un producto en 3857 sirve solo si se resume por
celda sin cruzarlo con la cobertura (caso de la frecuencia, D8).

Otros productos que existen y no se usan: la tabla `FINAL_PRODUCTS/burned_area_polygons_v2`
(1.012.648 cicatrices con `area_ha`, fechas, `calendar_year` y `fire_year`; contada el 2026-10-19,
sin script) y su carpeta `annual_burned_vectors_v2`. Ver `BACKLOG.md`.

**Salidas** (D7): `projects/mapbiomas-argentina/assets/FIRE/COLLECTION-1/ANALYSES/pyrorregions`
(`OUTPUT_ROOT`), creada por Iván el 2026-10-19, lectura pública. Escritura con ramonpagis probada el
2026-10-19 (subcarpeta de prueba creada y borrada; la carpeta quedó vacía).

**Año de cobertura: el previo al fuego (Y−1).** Es la regla de todo el mapeo y el análisis del
equipo de fuego (Iván, 15-oct-2026). Fuentes en su repo:
- ATBD (`collection-01/ATBD/main.tex`, sección "MapBiomas Argentina land cover"): la cobertura se
  lee siempre en `y−1`, porque la cobertura de un píxel quemado cambia **porque** se quemó.
- `statistics/docs/statistics.md`, "The land-cover year: we cross the PREVIOUS one": sus
  estadísticas cruzan `burned_area_<Y>` con `classification_<Y−1>`.
- Excepción: los assets publicados `*_coverage` usan el **mismo** año, por convención de la red
  (`07-published_products.md`, "Same year or previous year?"). Por eso tampoco sirven para nosotros.

Ecorregiones (Burkart et al. 1999, según `statistics.md`, sección "The territorial layer"),
**verificadas en GEE el 2026-10-17**:

| Asset | Features | Campo de nombre |
|---|---|---|
| `projects/mapbiomas-argentina/assets/ANCILLARY_DATA/VECTOR/ARG/ARG-Political_Level_2-13Ecorregiones_3857` | 13 | `LEVEL_2` (id `GEOCODE`, numérico) |
| `projects/mapbiomas-argentina/assets/ANCILLARY_DATA/VECTOR/ARG/ARG-Political_Level_2-16Ecorregiones_3857` | 16 | `LEVEL_2` (`GEOCODE` es texto: convertir antes de `paint`) |

El equipo de fuego midió que la de 16 clases se agrega exacto en la de 13. Advertencia de su doc:
pintar los vectores, nunca leer los rásters `_r`, que tienen otra numeración.

Nota sobre `frequency_burned_coverage`: la clase es la del **extremo móvil** de la ventana. En las
ventanas hacia atrás (`<y>_2025`) es la clase del año `y`, el **inicio**. Solo en la ventana completa
`1999_2025` es la de 2025. Fuente: `07-published_products.md`, "Frequency windows are two-sided".

Nota sobre `year_last_fire`: el doc del repo dice que las bandas se llaman `classification_<año+1>`;
en GEE se llaman `year_last_fire_<año+1>`.

Grilla nativa: `crs = EPSG:4326`, `crsTransform = [0.000269494585236, 0, -73.58468801489491, 0,
-0.000269494585236, -21.764113209062533]` (`SNIC_TRANSFORM` en `constants.py`). Desfases medidos
el 2026-10-14 con los transforms que devuelve GEE, mismo paso de píxel (diferencia ~1e-16):

| Asset | Columnas al este | Filas al sur |
|---|---|---|
| LULC col-3 `_pb` | 67 | 62 |
| `year_last_fire_v2` | 63 | −110 (al norte) |

## 5. Key verified numbers

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Años de fuego col-1 | 1999 a 2025 (27 imágenes mensuales) | `scripts/check_assets.py`, 2026-10-17 | verificado |
| Bandas de cobertura col-3 `_pb` | 1985 a 2025 (41) | `scripts/check_assets.py`, 2026-10-17 | verificado |
| Desfase de la cobertura respecto de la grilla de fuego | +67 columnas, +62 filas | `scripts/check_assets.py`, 2026-10-17 | verificado |
| Cicatriz más grande | 219.410 ha (2003) | comentario en `constants.py` del repo de fuego | medido por el equipo de fuego, no por nosotros |
| Cicatrices ≥ 100.000 ha | 24 | idem | idem |
| Cicatrices < 10 ha | 76,14 % del número, 5,67 % del área | idem | idem |
| Área del píxel nativo a −22° y −55° | ~829 y ~513 m² | cuenta exploratoria (scratchpad, 2026-10-14) | **exploratorio**: no hay script en el repo |
| Costo de una reducción agrupada interactiva, 1 año, recuadro de 1° en Córdoba | ~3 a 6 s a 30 m, sin diferencia consistente entre celdas tipo res 5 y res 6 | `scripts/bench_interactive.py`, 2026-10-17 | verificado (tiempos varían entre corridas) |
| Celdas H3 que tocan la Argentina continental (13 ecorregiones menos Islas del Atlántico Sur, simplificado a 500 m, 2.795.123 km²) | res 4: 2.125 · res 5: 14.124 · res 6: 96.461 · res 7: 668.344 (únicas; corregido el 2026-10-19, antes contaba duplicadas). Res 5 y 6: p5 a p95 de área 1,38 veces, extremos 1,59, sin pentágonos | `scripts/h3_cells_argentina.py`, 2026-10-19 | verificado |
| Mes de quema y clase de tamaño: enmascarados donde no hay quema, y coinciden píxel a píxel | 0 píxeles con uno y sin el otro (recuadro −64,6/−64,2, −31,4/−31,0; 2003, 2013, 2020) | comando ad hoc, 2026-10-19 | verificado; **sin script en el repo**: se repite en la prueba de Córdoba |
| Barrido D6 en Córdoba (401 hexágonos H3 res 6, 1999, 2010, 2025) | igual a los dos resúmenes separados (diferencia 0,0000 ha); 2.525 a 3.522 filas y 3 a 6 s por año; 0,6 a 0,95 % de lo quemado sobre clases no quemables | `scripts/bench_interactive.py --sweep`, 2026-10-19; `docs/notes/02-sweep_cordoba.md` | verificado |
| Grilla H3 res 6 armada | 96.461 celdas, ids 0..96.460, sin pentágonos ni repetidas; 14.137 padres de res 5; 2.845.253 km² sumando celdas enteras (las del borde salen del país) | `workflow/01-hex_grid.py --build`, 2026-10-19 | verificado |
| Grilla H3 res 6 subida al asset `h3_res6` | mismas 96.461 celdas e ids que la local; 0,00 ha sin pintar en el recuadro de Córdoba | `workflow/01-hex_grid.py --check`, 2026-10-26 (2/2) | verificado |
| Barrido D6 nacional, 2025 (cobertura 2024) | 646.922 filas, las 96.461 celdas; 2,1 min y 25.249 EECU-s; área por celda igual a la H3 (0,997 a 1,006); quemado 1.817.069 ha, 0,17 % sobre clases no quemables o no observadas | `workflow/02-sweep.py --fetch --years 2025`, 2026-10-26 | verificado |
| Área quemada 2025 según la plataforma MapBiomas Argentina | 1.817.067 ha (2 ha menos que el barrido) | leída por Ramón en la plataforma, 2026-10-26 | dato externo, sin script |
| Barrido D6 nacional, 27 años | 27/27 pasan `--check`; 571.183 a 815.332 filas por año; quemado 1999 a 2025: 63,235 Mha (equipo de fuego: 63,23, +0,008 %); serie anual en la nota | `workflow/02-sweep.py --fetch` y `--summary`, 2026-10-26; `docs/notes/03-sweep_national.md` | verificado |
| Frecuencia por celda (paso 04) | 2/2 controles; años quemados × área = 63,235 Mha, igual al paso 02 (−0,001 %); 38,554 Mha quemadas al menos una vez; máximo 18 años de 27; por celda p1 a p99 de −7,3 a +6,9 %, ninguna celda con ≥ 100 ha desviada más de 5 % | `workflow/04-frequency.py --check`, 2026-10-26; `docs/notes/04-frequency.md` | verificado |
| Tablas decodificadas (paso 05) | 18.090.702 filas del barrido (193 MB en Parquet), 172.925 de frecuencia; 5/5 controles; área de cada celda igual en los 27 años (dispersión máxima 5,2e-10); decodificación exacta | `workflow/05-cell_table.py --build`, 2026-10-26 | verificado |
| Tasa de quema media anual por clase, nacional 1999 a 2025 | p. ej. 19 Cultivos temporarios 0,20 %, 15 Pastura 1,65 %, 11 Herbáceas inundables 3,47 %, 6 4,06 % (tabla completa con `--classes`) | `workflow/05-cell_table.py --classes`, 2026-10-26 | verificado |
| Código máximo de D6 en res 6 | 1.253.990.138 (< 2.147.483.647) | cuenta con `utils/constants.py`, 2026-10-19 | verificado |

Antes de que cualquiera de estos números vaya a un mail o a la presentación: script en el repo, corrido, salida vista.

## 6. Known issues and fixes

- **Subproductos `_v2` fuera de la grilla nativa.** Ver sección 4.
- **`h3` con `contain="overlap"` repite celdas** que tocan más de un polígono del país (182 copias en
  res 6). Deduplicar siempre. Los conteos del 17-oct estaban inflados y se corrigieron el 19-oct.
- **Lo no quemado está enmascarado, no en 0** (mes de quema, clase de tamaño, frecuencia). Hacer
  `unmask(0)` antes de cualquier suma o código; si no, el área disponible sale solo de lo quemado.
  La cobertura enmascarada pasa a clase 0 (no observada). Ver D6 y D8.
- **`unmask(0)` solo rellena dentro de la huella del asset.** Fuera de ella el píxel sigue
  enmascarado y se cae de la suma. La primera corrida de 2025 perdió área en 17 celdas de borde.
  Usar `unmask(0, False)`. Ver `docs/02-sweep.md`, "Trampas".
- **Omisión probablemente alta en fuego col-1.** La validación en curso del equipo de fuego
  (`collection-01/validation/docs/design.md`, estado al 2026-10-06, ola 1 interpretada al 85 %)
  da exactitud del usuario de 73 a 79 % y exactitud del productor de 10 a 22 % en los tres años
  muestreados, con intervalos muy amplios. Es preliminar e interna: **no citar**. Si se confirma, el
  producto subestima el área quemada, y la tasa de quema de nuestras regiones también, quizás de
  forma distinta según la región. Esto contradice lo que decía el piloto patagónico (más comisión
  que omisión, según `geospatial-skills/MapBiomas-Fire/fire-knowledge.md`).
- **El producto excluye fuego agrícola en todo el país.** Regla B: se descarta todo objeto con más
  de 40 % de agricultura (`T_AGRI = 0.40`), sin condición de región ni estación. Regla A: se descartan
  objetos de pastizal pampeano (más de 70 %), de menos de 150 ha, quemados entre el 1 jul y el 15 nov,
  dentro del AOI agrícola de la Pampa. Fuente: `docs/07-vector_to_raster.md`, "Object exclusion
  ruleset". Consecuencia: la tasa de quema agrícola está subestimada por construcción.
- **El producto no tiene intensidad (FRP) ni causa de ignición.** Los antecedentes las usan.
- Gotchas de GEE generales: no se copian acá, están en `~/Desktop/GIS/geospatial-skills/SKILLS/gee-gotchas.md`.
  Los que más van a pesar: fijar `crsTransform` en todo export; sumar áreas con `pixelArea()` y
  nunca contar píxeles; el límite de ~17k features al exportar una FC a asset.

## 7. Step-by-step workflows

Instalación y chequeo de insumos: `README.md`, "Instalación". Cada paso que se implemente tendrá su
`docs/NN-*.md` con su bloque "Correr".

Patrones del repo de fuego para reusar (leer, no copiar sin entender), en `collection-01/statistics/`:
- `burnable_export.py`: denominador "quemable" por ecorregión, todo el cruce empaquetado en un entero
  y una sola reducción agrupada. Explica por qué usa tarea batch y no descarga interactiva (el chequeo
  de tamaño se hace sobre la resolución nativa).
- `lulc_change_export.py`: cobertura antes (Y−1) y después del fuego, para todo el país (diseño de
  Ferro et al. 2026).
- `burn_perc_export.py`: trampas medidas al agregar frecuencia (producto con `selfMask`, usar `mean`
  y no `max`, ponderar por área en 3857).

## 8. Contacts

- **Iván Barberá**: consejero del proyecto; repo de MapBiomas Fuego (solo lectura para nosotros);
  coautor de Ferro et al. 2026. El 15-oct-2026 apoyó el proyecto, lo propuso como trabajo final y
  para mostrarlo en el taller de MapBiomas, recomendó hexágonos y marcó la regla de cobertura del año
  previo. El 2026-10-17 aclaró que no conviene publicar un paper (hay gente de la red en el tema).
  El 2026-10-19 creó la carpeta de salida y pidió exportar ahí y guardar en enteros (D7); no hay
  espacio en Google Cloud, solo en la cuota de assets.
  Preguntarle quiénes son, para presentar en el taller sabiendo con quién dialoga el trabajo.
- Posibles revisores de los límites, autores de antecedentes directos: Juan Pablo Argañaraz
  (Naval-Fernández et al. 2025), Thomas Kitzberger (Ferro et al. 2026). No contactados.

---

## Reglas de trabajo en este repo

- Hablar antes de tocar archivos: plan, luz verde, recién ahí actuar. Commit y push solo cuando se pide.
- El repo de Iván es de solo lectura. Su organización es el modelo de este repo.
- Un hecho, un solo lugar: valores que usa el código en `utils/constants.py`; verificaciones y
  números en este archivo; decisiones en `docs/decisions.md`; papers en `docs/references.md`; orden
  de trabajo en `ROADMAP.md`; historia en `docs/notes/`.
- Un paso numerado = un script en `workflow/` = un doc `docs/NN-*.md` con la forma de `docs/TEMPLATE.md`.
- GEE: ningún `ee.*` a nivel de módulo; fijar `crs` + `crsTransform` (de `constants.py`) en todo
  export; sumar áreas con `pixelArea()`; un export por año; lanzadores que se pueden volver a correr
  sin duplicar tareas; descripciones de tarea con prefijo `TASK_PREFIX`.
- Dependencias con `uv add`, cuando un paso las necesita.
- Commits con el estilo del repo de fuego: `feat(02): ...`, `docs(roadmap): ...`, explicando el porqué.
- Citar secciones por nombre, nunca por número.
- Sin rayas largas en ningún texto.
