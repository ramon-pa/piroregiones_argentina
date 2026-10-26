# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al 2026-10-26)

Lo que corre en GEE está definido: el barrido D6 (27 tareas, con mes y clase de tamaño), la
frecuencia desde `frequency_burned_v2` (D8). Salidas según D7: grilla al asset `ANALYSES/pyrorregions`,
tablas CSV al Drive propio. D6 pasó la prueba de Córdoba (`docs/notes/02-sweep_cordoba.md`). Paso 01
listo: grilla H3 en el asset `h3_res6`, `--check` 2/2 el 2026-10-26. Paso 02: 2025 nacional pasó
los controles y coincide con la plataforma; los otros 26 años lanzados el 2026-10-26. Al retomar:
`--status`, luego `--fetch --years <los terminados>`.

## Ahora

- [ ] Preguntarle a Iván, cuando surja (sin apuro, no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región.
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.
- [ ] Cerrar D2 (período), D3 y D5 (`docs/decisions.md`). D2 y D5 no bloquean GEE: se exportan los
  27 años y el método de regionalización trabaja sobre las tablas.

## Siguiente

1. [ ] Paso 02, los otros 26 años: bajar y controlar cada uno (`--fetch`). Control de conjunto:
   la suma de los 27 años quemados contra los 63,23 Mha del equipo de fuego (`statistics.md`).
2. [ ] Borrar de Drive el CSV viejo de 2025 (`--fetch` toma el más nuevo; el viejo confunde).
3. [ ] Paso 04, frecuencia por celda (D8): una tarea, CSV a `DRIVE_FOLDER`, con el control contra D6.
4. [ ] Pasos 05 a 07, luego 09, 10 y la presentación.

## Hecho (borrar en la próxima pasada)

- [x] Primer commit y push del esqueleto (2026-10-17).
- [x] Repo renombrado a `ramon-pa/piroregiones_argentina` (2026-10-17).
- [x] Grilla y cómputo medidos sin exportar; D1 cerrada (2026-10-17).
- [x] Carpeta de salida creada por Iván y escritura probada; D6 a D9 acordadas (2026-10-19).
- [x] Barrido D6 probado en Córdoba con hexágonos reales, todo en verde (2026-10-19).
- [x] Paso 01: grilla H3 res 6 subida a `h3_res6` y `--check` 2/2 (2026-10-26).
- [x] Paso 02 escrito; 2025 nacional en 2,1 min, 3/3 controles, igual a la plataforma (2026-10-26).
