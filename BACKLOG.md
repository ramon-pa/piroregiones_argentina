# Backlog

Ideas sin agendar. Ordenadas por tema, no por prioridad: nada de acá es lo próximo. Lo próximo está
en [`ROADMAP.md`](ROADMAP.md); un ítem pasa de acá al ROADMAP cuando se agenda, nunca al revés.

## Método

- Tipos de régimen (nivel 2): Ward sin contigüidad sobre las pirorregiones (Erni et al. 2020).
- Medir cuánto cambian las regiones si la omisión del producto varía por región.
- Variables de eventos (cuántos fuegos distintos por celda) desde la tabla de cicatrices
  `FINAL_PRODUCTS/burned_area_polygons_v2` (1.012.648 cicatrices, con `area_ha`, fechas,
  `calendar_year` y `fire_year`). Descartado por ahora (2026-10-19): tamaño, estación y frecuencia
  ya salen de los rásters. Antes de usarla: averiguar cómo se define `fire_year` (la primera
  cicatriz es de enero de 1999 y tiene `fire_year = 1998`), comprobar que coincide con el ráster, y
  asignar por centroide solo variables de eventos, nunca de área.
- Estabilidad temporal de las regiones con las ventanas parciales de `frequency_burned_v2`
  (`1999_<y>` y `<y>_2025`), como período reservado de la evaluación de D5.
