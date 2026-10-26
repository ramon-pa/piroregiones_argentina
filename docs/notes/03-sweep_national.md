# 03 · El barrido D6 nacional: lo medido el 2026-10-26

Cuaderno de laboratorio: la corrida nacional del paso 02, los 27 años.
Script: `workflow/02-sweep.py` (`--export`, `--fetch`, `--summary`). Doc: `docs/02-sweep.md`.

## Pregunta

¿El barrido probado en Córdoba aguanta el país entero en una sola reducción por año (el riesgo era la
memoria con ~1 millón de grupos)? ¿Los números coinciden con fuentes independientes?

## Un año primero: 2025

- Terminó en 2,1 min, 25.249 EECU-s, 646.922 filas. La memoria no fue problema.
- **Primera corrida, un control en rojo**: 17 celdas de borde con menos área que su hexágono (la
  peor, al oeste de Santa Cruz, con 2 %). Causa: `unmask(0)` rellena solo dentro de la huella del
  asset. Probado celda por celda con la cobertura 2024 (celda 85914: 0,65 km² con el `unmask` por
  defecto, 33,80 con `unmask(0, False)`, hexágono 33,68). Corregido con `unmask(0, False)` y vuelto a
  correr: 3/3. Lo quemado no cambió (1.817.069 ha); el total subió 23.000 ha, todo clase 0.
- **Contra la plataforma MapBiomas Argentina** (leído por Ramón): 1.817.067 ha. Diferencia 2 ha.

## Los 27 años

Los 26 restantes, lanzados juntos; GEE los corrió de a tres. Terminaron todos sin error.

- `--check`: 27/27 años pasan los tres controles. Todas las celdas en todos los años; área por celda
  entre 0,997 y 1,006 de la H3; área total 284,507 Mha, igual todos los años.
- Filas por año: 571.183 (2015) a 815.332 (2020); archivos de 16 a 23 MB.
- Área quemable (clases de `BURNABLE_CLASSES` del año previo): 250,42 a 251,20 Mha.
- **Suma de lo quemado 1999 a 2025: 63,235 Mha.** El equipo de fuego informa 63,23 Mha con su toolkit
  (`statistics.md`, control "National annual burned: toolkit vs the object database"): +0,008 %,
  dentro del redondeo de su cifra.

Quemado por año (ha), de `--summary`:

| Año | ha | Año | ha | Año | ha |
|---|---|---|---|---|---|
| 1999 | 2.266.676 | 2008 | 3.041.084 | 2017 | 2.674.995 |
| 2000 | 4.467.040 | 2009 | 2.308.313 | 2018 | 2.293.399 |
| 2001 | 5.082.351 | 2010 | 796.676 | 2019 | 1.257.474 |
| 2002 | 3.548.342 | 2011 | 1.466.614 | 2020 | 4.348.614 |
| 2003 | 3.898.630 | 2012 | 863.318 | 2021 | 1.581.324 |
| 2004 | 3.007.957 | 2013 | 1.689.676 | 2022 | 4.021.959 |
| 2005 | 2.032.519 | 2014 | 1.114.022 | 2023 | 1.548.253 |
| 2006 | 2.284.493 | 2015 | 1.028.582 | 2024 | 1.162.149 |
| 2007 | 1.353.818 | 2016 | 2.279.702 | 2025 | 1.817.069 |

## Lectura

- El paso 02 está completo: las 27 tablas existen, pasan los controles y su suma reproduce el total
  del equipo de fuego. El plan B (partir por regiones) no hizo falta.
- Lo que valida cada comparación: la de la plataforma (un año) y la del equipo de fuego (27 años)
  vienen de cálculos que no comparten la grilla H3 ni el código empaquetado; que coincidan dice que
  el barrido no pierde ni duplica área quemada.
- Sigue abierto el −0,083 % del recuadro de Córdoba (`02-sweep_cordoba.md`): no afecta las sumas por
  celda, que cierran contra el área H3.
