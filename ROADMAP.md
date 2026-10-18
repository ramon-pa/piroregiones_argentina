# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al cierre del 2026-10-17)

D1 cerrada: H3, extracción en res 6, mapa final en res 5 o res 6. D6 propuesta: un solo barrido por
año para cobertura disponible y quemado. Lo medido está en `docs/notes/01-grid_and_compute.md`. Lo
próximo es probar D6 en Córdoba (ítem 1 de "Siguiente").

## Ahora

- [ ] Preguntarle a Iván:
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región.
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.
- [ ] Cerrar D2, D3 y D5 (`docs/decisions.md`).

## Siguiente

1. [ ] Probar D6 en el recuadro de Córdoba, en interactivo: tiempo, filas, y que el área disponible y
   la quemada cierren contra los dos resúmenes por separado (`scripts/bench_interactive.py`).
2. [ ] Paso 01, grilla H3 en res 6: `workflow/01-hex_grid.py` + `docs/01-hex_grid.md`. Incluye subir
   ~97 mil hexágonos a GEE (shapefile zip por la UI; ver `gee-gotchas.md` por el límite de ~17k
   features al exportar desde memoria).
3. [ ] Paso 02 (barrido único, si D6 se confirma) sobre una región, en interactivo.
4. [ ] Lanzador batch para todo el país: una tarea por año, se puede volver a correr sin duplicar,
   descripciones con prefijo `piro`, baja automática de Drive. Modelo: `statistics/*_export.py` del
   repo de fuego.
5. [ ] Paso 04 (frecuencia), pasos 05 a 07, luego 09, 10 y la presentación.

## Hecho (borrar en la próxima pasada)

- [x] Primer commit y push del esqueleto (2026-10-17).
- [x] Repo renombrado a `ramon-pa/piroregiones_argentina` (2026-10-17).
- [x] Grilla y cómputo medidos sin exportar; D1 cerrada (2026-10-17).
