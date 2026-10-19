# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al cierre del 2026-10-19)

Lo que corre en GEE está definido: el barrido D6 (27 tareas, con mes y clase de tamaño), la
frecuencia desde `frequency_burned_v2` (D8) y la subida de la grilla H3. Salidas según D7: grilla al
asset `ANALYSES/pyrorregions` (escritura probada), tablas CSV al Drive propio. Lo próximo es la
prueba de D6 en Córdoba (ítem 1 de "Siguiente").

## Ahora

- [ ] Preguntarle a Iván, cuando surja (sin apuro, no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región.
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.
- [ ] Cerrar D2 (período), D3 y D5 (`docs/decisions.md`). D2 y D5 no bloquean GEE: se exportan los
  27 años y el método de regionalización trabaja sobre las tablas.

## Siguiente

1. [ ] Probar D6 en el recuadro de Córdoba, en interactivo (`scripts/bench_interactive.py`). Tiene que
   cumplir, o se corrige antes de seguir:
   - tiempo y cantidad de filas por año (para estimar el país);
   - área disponible y quemada iguales a las de dos resúmenes por separado;
   - 0 filas con mes > 0 y tamaño 0, o al revés;
   - ninguna clase ≥ 100 ni mes > 12 al decodificar;
   - suma de todas las áreas igual al área del recuadro (salvo bordes);
   - área quemada sobre clases no quemables o no observadas: informarla (D9).
2. [ ] Paso 01, grilla H3 en res 6: `workflow/01-hex_grid.py` + `docs/01-hex_grid.md`. Ids enteros
   0..N−1 con tabla de equivalencia al índice H3. Subir los ~97 mil hexágonos a `OUTPUT_ROOT` como
   shapefile zip por la UI (`gee-gotchas.md`, límite de ~17k features al exportar desde memoria).
   Control: el área de los hexágonos pintados cubre el país sin huecos ni solapes.
3. [ ] Paso 02 (barrido D6) sobre una región, en interactivo, con los controles del ítem 1.
4. [ ] Lanzador batch para todo el país: una tarea por año, CSV a `DRIVE_FOLDER`, se puede volver a
   correr sin duplicar, descripciones con prefijo `piro`. Modelo: `statistics/*_export.py` del repo
   de fuego.
5. [ ] Paso 04, frecuencia por celda (D8): una tarea, CSV a `DRIVE_FOLDER`, con el control contra D6.
6. [ ] Pasos 05 a 07, luego 09, 10 y la presentación.

## Hecho (borrar en la próxima pasada)

- [x] Primer commit y push del esqueleto (2026-10-17).
- [x] Repo renombrado a `ramon-pa/piroregiones_argentina` (2026-10-17).
- [x] Grilla y cómputo medidos sin exportar; D1 cerrada (2026-10-17).
- [x] Carpeta de salida creada por Iván y escritura probada; D6 a D9 acordadas (2026-10-19).
