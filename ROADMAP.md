# ROADMAP

Qué hacer después, en orden. Tildar cuando se cumple; borrar en la pasada siguiente.
El historial de git es el archivo.

Destino: trabajo final de Geo Dojo y taller de MapBiomas (`CLAUDE.md`, "Overview").

## Para retomar (estado al 2026-10-27)

Todo lo de GEE está hecho (pasos 00 a 05). Las variables por celda están listas (paso 06). El paso
07 tiene un borrador: 15 pirorregiones con nombres propuestos (D14, D15), que es el mapa del taller.
Estado por paso: `CLAUDE.md`, "Current state".

## Ahora

- [ ] Decidir si se adopta el mapa candidato `--cover-by-fire` (14 regiones: bosque y ecotono
  andino norte continuo, Delta y valles del Río Negro forzados; `docs/notes/07-regions_drivers.md`).
  Reabre D12 y D14. Si se adopta: renombrar la región 1 (ya no es "Chaco occidental y pedemonte",
  la leyenda se pisa), registrar la decisión y actualizar el deck.
- [ ] Pruebas que siguen del plan del 2026-10-28: B, vecinos por distancia (< 30 km) para saltar la
  frontera con Chile; A, tipos de régimen con Ward sin contigüidad sobre las regiones (D5).
- [ ] Llevar al taller las dos preguntas abiertas del mapa y anotar lo que surja:
  - una región continua de bosque andino-patagónico norte, del Lanín a Los Alerces (slide "A
    discutir");
  - el valle del Paraná al norte de Rosario, que sigue dentro del Espinal (D15).
- [ ] Preguntarle a Iván, cuando surja (no bloquea nada):
  - quiénes trabajan en pirorregiones en la red MapBiomas;
  - si la omisión alta de la validación preliminar se confirma y si varía por región;
  - si `config/veg_fire_remap.csv` (regla B) se armó sobre la col-3 (D10).
- [ ] Averiguar fecha de entrega, formato y criterios del trabajo final de Geo Dojo.

## Siguiente

1. [ ] Ajustar el mapa según lo que salga del taller; confirmar los nombres de las regiones.
2. [ ] Paso 10: fichas de las 15 regiones (alcance A: tabla y texto, con la tasa por familia de D12).
3. [ ] Revisar las regiones de fuego raro (Andes áridos, Estepa patagónica): ¿el relleno de celdas
   sin fuego las arma? Cerrar D5.
4. [ ] Averiguar por qué `ss_ratio` y la cifra de pygeoda no coinciden.
5. [ ] Paso 09: comparación cuantitativa con las ecorregiones.
6. [ ] Cerrar D3 (`docs/decisions.md`).
