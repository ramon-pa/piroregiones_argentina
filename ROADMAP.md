# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al cierre del 2026-10-19)

Lo que corre en GEE está definido: el barrido D6 (27 tareas, con mes y clase de tamaño), la
frecuencia desde `frequency_burned_v2` (D8) y la subida de la grilla H3. Salidas según D7: grilla al
asset `ANALYSES/pyrorregions` (escritura probada), tablas CSV al Drive propio. D6 pasó la prueba de
Córdoba (`docs/notes/02-sweep_cordoba.md`). Grilla H3 armada (96.461 celdas) y **subiéndose al asset
`h3_res6`** desde el 2026-10-19 (tarea de carga de Ramón). Al retomar: ver en Tasks que terminó y
correr `uv run python workflow/01-hex_grid.py --check`; si da 2/2, el paso 01 está listo y sigue el 02.

## Ahora

- [ ] Preguntarle a Iván, cuando surja (sin apuro, no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región.
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.
- [ ] Cerrar D2 (período), D3 y D5 (`docs/decisions.md`). D2 y D5 no bloquean GEE: se exportan los
  27 años y el método de regionalización trabaja sobre las tablas.

## Siguiente

1. [ ] Paso 01, grilla H3 en res 6 (`docs/01-hex_grid.md`). Armada (`--build`) y zip subido por la UI
   a `H3_GRID_ASSET` el 2026-10-19 (carga en curso). Falta: `--check` y registrar su resultado en
   `CLAUDE.md` (fila "Grilla H3 res 6 armada").
2. [ ] Paso 02, el barrido D6: `workflow/02-sweep.py` + `docs/02-sweep.md`, una tarea batch por año,
   CSV a `DRIVE_FOLDER`, se puede volver a correr sin duplicar, descripciones con prefijo `piro`.
   Modelo: `statistics/*_export.py` del repo de fuego. Los controles de `--sweep` corren sobre cada
   tabla bajada.
3. [ ] **Un solo año nacional primero**, para medir memoria, filas y tiempo reales (riesgo de ~1
   millón de grupos, `docs/notes/02-sweep_cordoba.md`). Si falla, partir por regiones o usar
   `reduceRegions`. Recién después, los otros 26.
4. [ ] Paso 04, frecuencia por celda (D8): una tarea, CSV a `DRIVE_FOLDER`, con el control contra D6.
5. [ ] Pasos 05 a 07, luego 09, 10 y la presentación.

## Hecho (borrar en la próxima pasada)

- [x] Primer commit y push del esqueleto (2026-10-17).
- [x] Repo renombrado a `ramon-pa/piroregiones_argentina` (2026-10-17).
- [x] Grilla y cómputo medidos sin exportar; D1 cerrada (2026-10-17).
- [x] Carpeta de salida creada por Iván y escritura probada; D6 a D9 acordadas (2026-10-19).
- [x] Barrido D6 probado en Córdoba con hexágonos reales, todo en verde (2026-10-19).
