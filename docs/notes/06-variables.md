# 06 · Las variables por celda: lo medido el 2026-10-26

Cuaderno de laboratorio: la primera corrida del paso 06. Script: `workflow/06-variables.py`.
Doc: `docs/06-variables.md`.

## Región por celda (GEE)

Una tarea, 0,5 min, CSV de 2,5 MB. El ráster de regiones del equipo de fuego está exactamente en
nuestra grilla nativa (transform leído del asset el 2026-10-26). 3.249 celdas tienen menos del 90 %
de su área en su región mayoritaria: son las de los límites entre regiones.

## La corrida

`--build`, 7 s, 5/5 controles:

- sin huecos en las 13 columnas del clustering;
- quemado sobre clases quemables, sumado por celda: 63,177 Mha, igual a las tablas;
- área quemable media, sumada por celda: 250,797 Mha, igual a las tablas;
- proporciones por familia que suman 1 en todas las celdas con área quemable;
- valores en rango.

Informado:

- Tasa de quema nacional: 0,933 % del área quemable por año. No es comparable directo con el 0,838 %
  del equipo de fuego (D8): ellos dividen por otro denominador (279,5 Mha; no verifiqué qué área es).
- 36.909 celdas sin fuego en clases quemables (38 %), todas con la temporada rellenada por vecinas.
  143 de ellas tienen fuego solo en clases no quemables (agua y otras no vegetadas, 1.855 ha en total).
- Familia por respaldo (par región-clase ausente del remapeo del equipo de fuego): 0,518 Mha por año,
  clases 4, 6, 15, 19, 21, 36, 63, 66 y 77.
- Mes pico más común, en celdas con fuego:

| Región | 1.º | 2.º | 3.º |
|---|---|---|---|
| Cuyo | dic (1.408) | ene (1.362) | sep (800) |
| Patagonia | ene (2.005) | feb (1.473) | dic (1.300) |
| Pampa | ago (3.360) | sep (2.875) | feb (2.467) |
| Chaco | sep (6.851) | ago (6.590) | oct (2.552) |
| Bosque Atlántico | ago (383) | jul (164) | feb (159) |

## Lectura

- La temporada tiene sentido geográfico: verano en Patagonia y Cuyo, fin de invierno y primavera en
  el Chaco. La Pampa mezcla las dos: es una región donde la temporada puede separar subregiones.
- El 38 % de celdas sin fuego es mucho más que en Segura-Garcia (allí "unas pocas"). Su relleno pesa
  en el clustering: hay que mirar en el paso 07 si las regiones de fuego raro salen razonables.
