# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al 2026-11-04)

Todo lo de GEE está hecho (pasos 00 a 05). Las variables por celda están listas (paso 06). El paso
07 tiene un mapa preliminar: 14 pirorregiones con los ajustes del equipo (D16).
Estado por paso: `CLAUDE.md`, "Current state".

## Ahora

- [ ] Pasar al repo lo que falta de la diapo del factsheet: estacionalidad por región y comparación con
  ecorregiones (paso 09). Hoy solo está en cálculos ad hoc.
- [ ] Actualizar el deck del taller al mapa de 14 regiones.
- [ ] Pruebas que siguen del plan del 2026-10-28: B, vecinos por distancia (< 30 km) para saltar la
  frontera con Chile; A, tipos de régimen con Ward sin contigüidad sobre las regiones (D5).
- [ ] Llevar al taller la pregunta abierta del mapa y anotar lo que surja:
  - el valle del Paraná al norte de Rosario, que sigue dentro del Espinal (D15).
- [ ] Preguntarle a Iván, cuando surja (no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región;
  - si `config/veg_fire_remap.csv` (regla B) se armó sobre la col-3 (D10).
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.

## Siguiente

1. [ ] Ajustar el mapa según lo que salga del taller; confirmar los nombres de las regiones.
2. [ ] Paso 10: fichas de las 14 regiones (alcance A: tabla y texto, con la tasa por familia de D12).
3. [ ] Revisar las regiones de fuego raro (Andes áridos, Estepa patagónica): ¿el relleno de celdas
   sin fuego las arma? Cerrar D5.
4. [ ] Averiguar por qué `ss_ratio` y la cifra de pygeoda no coinciden.
5. [ ] Paso 09: comparación cuantitativa con las ecorregiones.
6. [ ] Cerrar D3 (`docs/decisions.md`).
