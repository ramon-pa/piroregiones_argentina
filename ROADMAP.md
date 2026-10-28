# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al 2026-10-27)

Lo que corre en GEE está definido: el barrido D6 (27 tareas, con mes y clase de tamaño), la
frecuencia desde `frequency_burned_v2` (D8). Salidas según D7: grilla al asset `ANALYSES/pyrorregions`,
tablas CSV al Drive propio. D6 pasó la prueba de Córdoba (`docs/notes/02-sweep_cordoba.md`). Paso 01
listo: grilla H3 en el asset `h3_res6`, `--check` 2/2 el 2026-10-26. Paso 02 listo: 27 tablas en
`data/sweep/`, 27/27 controles, suma igual a la del equipo de fuego (`docs/notes/03-sweep_national.md`).
Paso 04 listo: frecuencia por celda, 2/2
controles, igual al paso 02 (`docs/notes/04-frequency.md`). Todo lo de GEE está hecho. Paso 05 listo:
tablas en `data/tables/`, 5/5 controles. Paso 06 listo: variables
por celda, 5/5 controles. Paso 07: borrador a res 5 con REDCAP (D13); mapa elegido k = 12 más tres
piezas forzadas (D14, D15), 15 regiones con nombres propuestos, 4/4 controles
(`docs/notes/07-regions_draft.md`). Ese mapa es el único que se muestra en el taller. **Al retomar**:
lo que salga de la reunión (bosque andino-patagónico norte), después fichas de las 15 regiones
(paso 10, alcance A: tabla y texto, sin figuras por región).

## Ahora

- [ ] Preguntarle a Iván, cuando surja (sin apuro, no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región.
  - si `config/veg_fire_remap.csv` (regla B) se armó sobre la col-3 (D10).
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.
- [ ] Cerrar D2 (período), D3 y D5 (`docs/decisions.md`). D2 y D5 no bloquean GEE: se exportan los
  27 años y el método de regionalización trabaja sobre las tablas.

## Siguiente

1. [ ] Nombres y fichas de las 14 regiones; terminar la presentación del taller.
2. [ ] Revisar las regiones de temporada dispersa (Monte cuyano, Pampa) y las de fuego raro (Andes
   áridos, Patagonia): ¿el relleno de celdas sin fuego las arma? Cerrar D5.
3. [ ] Averiguar por qué `ss_ratio` y la cifra de pygeoda no coinciden.
4. [ ] Paso 09: comparación cuantitativa con las ecorregiones; luego 10.

## Hecho (borrar en la próxima pasada)

- [x] Primer commit y push del esqueleto (2026-10-17).
- [x] Repo renombrado a `ramon-pa/piroregiones_argentina` (2026-10-17).
- [x] Grilla y cómputo medidos sin exportar; D1 cerrada (2026-10-17).
- [x] Carpeta de salida creada por Iván y escritura probada; D6 a D9 acordadas (2026-10-19).
- [x] Barrido D6 probado en Córdoba con hexágonos reales, todo en verde (2026-10-19).
- [x] Paso 01: grilla H3 res 6 subida a `h3_res6` y `--check` 2/2 (2026-10-26).
- [x] Paso 02: 27 años corridos y controlados; 63,235 Mha contra 63,23 del equipo de fuego; CSV viejo de 2025 a la papelera de Drive (2026-10-26).
- [x] Paso 04: frecuencia por celda, 2/2 controles; `--status` y `--fetch` pasaron a `utils/gee_tasks.py` (2026-10-26).
- [x] D2 acordada (1999 a 2025), D10 acordada (solo la clase 19 fuera de las tasas), D5 con plan para el 07; paso 05 listo, 5/5 (2026-10-26).
- [x] D11 y D12 acordadas; paso 06 listo, 5/5 (2026-10-26).
- [x] D13 acordada (res 5 con REDCAP); variables a res 5 y primer borrador del 07, k = 15 (2026-10-27).
- [x] D14 acordada; mapa de 14 regiones (k = 12 + 2) y celdas casi sin área quemable resueltas (2026-10-27).
