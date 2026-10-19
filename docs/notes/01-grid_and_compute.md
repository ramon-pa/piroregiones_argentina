# 01 · Grilla H3 y costo de cómputo: lo medido el 2026-10-17

> Cuaderno de laboratorio: el registro de elegir la grilla, no su documentación.
> Scripts: `scripts/h3_cells_argentina.py` y `scripts/bench_interactive.py` (commit de este archivo).
> Todo es de solo lectura: ninguna medición exportó nada.
> Las filas "fuego 2020" y las tandas 1 y 2 de tiempos salieron de versiones previas de esos mismos
> scripts en el scratchpad de la sesión (misma lógica); el resto, de los scripts del repo.

## Pregunta

Antes de cerrar la resolución de H3 (D1): cuánto cómputo de GEE cuesta cada resolución, cuánto se
deforma H3 en Argentina, y si se puede trabajar sin exportar.

## Cuántas celdas y cuánto varía su área

`scripts/h3_cells_argentina.py`. Polígono: las 13 ecorregiones de Burkart menos Islas del Atlántico
Sur, simplificado a 500 m en GEE; 176 polígonos, 2.795.123 km² geodésicos.

| H3 | Celdas que tocan el país | Área por celda |
|---|---|---|
| res 4 | 2.125 | 1.102 a 1.761 km² |
| res 5 | 14.124 | 157 a 251 km² |
| res 6 | 96.461 | 22 a 36 km² |
| res 7 | 668.344 | 3,2 a 5,1 km² |

> **Corrección del 2026-10-19.** La primera versión de esta tabla decía 2.310, 14.312, 96.643 y
> 668.539: contaba celdas repetidas. Con `contain="overlap"`, `h3` devuelve una celda una vez por
> cada polígono del país que toca (son 176), y en res 6 eso agregaba 182 copias. Lo detectó el
> control de duplicados de `workflow/01-hex_grid.py`; el script ahora deduplica y se volvió a
> correr. Las áreas y la tabla de abajo (modo `center`, sin duplicados) no cambian.

Celdas con centro dentro del país:

| H3 | n | p5 | mediana | p95 | p95/p5 | máx./mín. | Pentágonos dentro |
|---|---|---|---|---|---|---|---|
| res 5 | 13.533 | 171,7 | 207,6 | 237,3 km² | 1,38 | 1,59 | 0 |
| res 6 | 94.798 | 24,5 | 29,7 | 33,9 km² | 1,38 | 1,59 | 0 |

Comparación: el píxel nativo de MapBiomas varía ~1,6 veces entre −22° y −55° (829 contra 513 m²,
cuenta exploratoria del 2026-10-14). La deformación de H3 en Argentina es del mismo orden.

Antes se había estimado res 5 en 209 a 245 km² con 3 puntos de prueba y res 6 en ~77 mil celdas
dividiendo por el área media global. Ambas cosas subestimaban: quedan reemplazadas por esta tabla.

## ¿El tamaño de celda cambia el costo?

`scripts/bench_interactive.py --cells`. Recuadro de 1° × 1° en Córdoba (1.053.347 ha), celdas
cuadradas sintéticas alineadas a la grilla nativa: 200 px de lado (~30 km², como res 6) y 520 px
(~200 km², como res 5). Una reducción agrupada interactiva por caso.

| Año | Resumen | Celdas tipo res 6 | Celdas tipo res 5 |
|---|---|---|---|
| fuego 2020, cobertura 2019 | cobertura disponible | 4,0 s, 2.641 grupos | 5,4 s, 627 grupos |
| | quemado | 5,7 s, 1.238 grupos | 3,8 s, 664 grupos |
| fuego 2016, cobertura 2015 | cobertura disponible | 4,2 s, 2.653 grupos | 3,2 s, 637 grupos |
| | quemado | 3,9 s, 464 grupos | 2,6 s, 355 grupos |

Lectura: **el tamaño de celda no cambia el costo de forma consistente**; lo que cuesta es recorrer
los píxeles. **Enmascarar a lo quemado tampoco abarata**: para saber qué píxel está quemado hay que
leer la banda de fuego en todos. La resolución se elige por criterio ecológico.

## ¿Se puede hacer todo el país sin exportar?

El país equivale a ~265 recuadros como el de Córdoba (2.795.123 / ~10.533 km²). Con ~5 s por
recuadro, año y paso: ~265 × 27 × 3 ≈ 21.000 pedidos interactivos, ~30 h en serie. Extrapolación
gruesa: Córdoba es diversa y los recuadros con océano o Chile son más baratos.

Referencia batch: el equipo de fuego hizo una reducción nacional de 27 bandas de cobertura a 30 m en
**una tarea de 2 min 15 s** (`statistics/docs/statistics.md` de su repo, sección del denominador
quemable, corrida del 2026-09-14). Su conclusión fue la misma: interactivo no escala al país.

Decisión: desarrollar y probar en interactivo sobre una región; exportar solo la corrida nacional,
como tablas chicas a Drive.

## ¿Conviene leer la cobertura a menor resolución?

La cobertura col-3 tiene pirámides con `pyramidingPolicy = MODE` en sus 41 bandas (leído del asset).
`scripts/bench_interactive.py --scale`: cobertura 2019 en el recuadro de Córdoba, área por celda y
clase leída a 60, 120 y 240 m contra 30 m.

| Lectura | Área asignada a otra celda-clase (res 6 / res 5) | Peor error por clase |
|---|---|---|
| 60 m | 0,29 % / 0,22 % | 3 % clase 15 (Pasturas, 3,0 % del recuadro) |
| 120 m | 1,06 % / 0,86 % | 12 % clase 15; 4 % clase 12 (Herbáceas) |
| 240 m | 2,63 % / 2,25 % | **26 % clase 15**; 11 % clase 12 |

Tiempos sin caché, celdas tipo res 6, cuatro corridas en dos tandas:

| | 30 m | 60 m | 120 m | 240 m |
|---|---|---|---|---|
| tanda 1 (años 1986 a 1989) | 3,7 s | 1,3 s | 0,7 s | 1,5 s |
| tanda 2 (años 1990 a 1993) | 3,8 s | 1,6 s | 1,5 s | 0,8 s |
| tanda 3 (años 1994 a 1997) | 6,5 s | 2,8 s | 5,4 s | 1,3 s |
| tanda 4 (años 1998 a 2001) | 4,0 s | 1,5 s | 1,7 s | 1,3 s |

Lectura: leer más grueso ahorra ~2 a 3 veces el tiempo, pero la moda achica las clases minoritarias
y fragmentadas, y Pasturas y Herbáceas son de las que más se queman. El numerador (lo quemado) se lee
a 30 m; un denominador más grueso sesgaría la tasa justo en esas clases. **No se usa.** A 30 m el
costo ya es de minutos en batch.

## Trampa: la caché de GEE

La primera corrida de `--scale` dio 0,5 s a 30 m: GEE devolvió de caché un cálculo idéntico pedido
minutos antes. Un tiempo interactivo solo vale la primera vez que se pide esa combinación de año,
escala y celda. Por eso `bench_interactive.py` toma años "nunca pedidos" como argumento.

## Qué queda decidido

- D1: H3, comparando res 5 y res 6; res 4 y res 7 descartadas (`docs/decisions.md`).
- D6 (propuesta): un solo barrido por año para cobertura disponible y quemado (`docs/decisions.md`).
