# 02 · El barrido único (D6) en Córdoba: lo medido el 2026-10-19

> Cuaderno de laboratorio: el registro de probar el barrido antes de escribir el paso 02.
> Script: `scripts/bench_interactive.py --sweep` (commit de este archivo). Solo lectura, nada exportado.

## Pregunta

¿El barrido único de D6 (un código por píxel con celda, clase del año previo, mes y clase de tamaño)
da lo mismo que calcular por separado el área disponible y la quemada? ¿Hay algo que lo rompa sin
avisar? ¿Cuánto cuesta y cuántas filas da?

## Antes de la prueba: dos supuestos comprobados

Comando suelto, recuadro −64,6/−64,2, −31,4/−31,0, años 2003, 2013 y 2020, histogramas de valores:

- **Lo no quemado viene enmascarado, no en 0**, en el mes (`fire_mask_v2`) y en la clase de tamaño
  (`annual_burned_scar_size_range_v2`). Sin `unmask(0)`, el área disponible saldría solo de lo
  quemado. Pasó a regla en D6.
- **Mes y clase de tamaño coinciden píxel a píxel**: 0 píxeles con uno y sin el otro en los tres
  años. Pasó a control del barrido.

## Montaje

- Recuadro de 1° × 1° (`BOX` del script: −64,5/−63,5, −32/−31), 10.542 km².
- **Hexágonos H3 reales** de res 6: los 401 que tocan el recuadro, armados con `h3` en Python y
  pintados en GEE sobre un fondo enmascarado. Es el mismo camino que la corrida nacional, salvo que
  allá la grilla vendrá de un asset.
- Años 1999 (cobertura 1998, el borde inferior), 2010 y 2025 (el borde superior).

## Resultados

| Control | 1999 | 2010 | 2025 |
|---|---|---|---|
| Píxeles del recuadro sin celda | 0 ha | 0 ha | 0 ha |
| Tipo del código | entero | entero | entero |
| Área total frente al recuadro (1.054.220 ha) | −0,083 % | −0,083 % | −0,083 % |
| Filas fuera de rango o clases que no están en ninguna lista | 0 | 0 | 0 |
| Área con mes y sin tamaño, o al revés | 0 ha | 0 ha | 0 ha |
| Diferencia máxima con los dos resúmenes separados (por celda y clase; por celda, clase y mes) | 0,0000 ha | 0,0000 ha | 0,0000 ha |
| Filas | 2.525 | 2.892 | 3.522 |
| Tiempo, primera vez que se pide | 5,5 s | 3,3 s | 4,8 s |
| Área quemada | 1.168,9 ha | 495,6 ha | 1.928,0 ha |
| Sobre clases no quemables o no observadas | 7,0 ha (0,60 %) | 2,9 ha (0,59 %) | 18,3 ha (0,95 %) |

Lectura:

- **D6 queda confirmada**: el barrido único reproduce exacto los dos resúmenes por separado.
- **El código es entero.** GEE informa un rango de ±2,8 × 10¹³, o sea que lo trata como entero de
  64 bits: el tipo sale del tipo de los operandos, no de los valores, así que en el país pasará lo
  mismo. No se guarda, así que el tamaño del tipo no ocupa cuota.
- **El −0,083 % del área total** (872 ha) es igual en los tres años: depende solo de la geometría.
  Equivale a una franja de menos de un píxel alrededor del recuadro, así que probablemente es el
  tratamiento de los píxeles del borde. **No explicado del todo.** No afecta la corrida nacional, que
  suma por celda y no por recuadro.
- **Quemado sobre clases no quemables**: casi todo clase 24 (urbano, la ciudad de Córdoba), algo de
  25 (otras no vegetadas) y 33 (agua). Coincide con lo esperado en D9: chico, no nulo.

## Lo que queda abierto: memoria a escala nacional

Escalando las filas por área (2.795.123 km² del país sobre 10.542 km²), un año daría del orden de
**0,67 a 0,93 millones de filas**. Es una estimación gruesa: la cantidad real depende de cuán variada
es cada región. Para Drive no es problema (decenas de MB por año), pero la reducción agrupada arma
todo el resultado en memoria y con ~1 millón de grupos puede fallar. Se prueba con un año nacional
en batch antes de lanzar los 27 (`ROADMAP.md`). Si falla: partir cada año por regiones, o reducir
celda por celda con `reduceRegions`.
