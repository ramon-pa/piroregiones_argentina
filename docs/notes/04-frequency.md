# 04 · La frecuencia por celda: lo medido el 2026-10-26

Cuaderno de laboratorio: la corrida del paso 04. Script: `workflow/04-frequency.py`.
Doc: `docs/04-frequency.md`.

## Pregunta

¿El producto publicado de frecuencia, en EPSG:3857, da por celda lo mismo que las 27 tablas anuales
del paso 02, en la grilla nativa? ¿Cuánto se separan celda por celda?

## Antes de lanzar

- Grilla del producto leída del asset: EPSG:3857, `[30, 0, -8189460, 0, -30, -2483190]`, entero.
- Prueba interactiva en el recuadro de Córdoba (`BOX` de `bench_interactive.py`): código entero,
  850 filas, de 1 a 12 años quemados.

## La corrida

Una tarea, terminada sin error en 2,9 min, 26.745 EECU-s. CSV de 4,5 MB, 172.925 filas.

`--check`, 2/2:

| Control | Resultado |
|---|---|
| Códigos en rango | 0 filas fuera; años quemados de 1 a 18 |
| Suma nacional de años quemados × área frente a la suma de las 27 tablas del paso 02 | 63,235 Mha en los dos (−0,001 %) |

Lo informado (no corta):

- Celdas con algo quemado: 59.692 de 96.461. Área quemada al menos una vez: 38,554 Mha.
- Diferencia relativa por celda (frecuencia menos paso 02, sobre paso 02): p1 −7,27 %, p5 −1,78 %,
  mediana 0,00 %, p95 +1,76 %, p99 +6,91 %.
- Celdas desviadas más de 5 %: 84 de las 53.723 con al menos 10 ha quemadas; ninguna entre las
  40.882 con al menos 100 ha.
- Celdas quemadas según una sola de las dos fuentes: 29, que suman 2 ha.

## Lectura

- D8 queda confirmada a nivel nacional y por celda: mezclar las dos grillas no cambia el total y
  solo mueve área en celdas con poco quemado. Probablemente por los bordes de las cicatrices, que
  caen en píxeles distintos en cada grilla; no comprobado.
- Las celdas con algo quemado pero menos de 100 ha en 27 años (unas 18.800) tienen la frecuencia
  menos firme: tenerlo en cuenta si una variable de recurrencia pesa mucho en ellas.
- Máximo de 18 años quemados sobre 27 en algún píxel del país.
