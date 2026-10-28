# 07 · Borradores de pirorregiones (2026-10-27)

Cuaderno de laboratorio. Scripts: `workflow/06-variables.py --res 5`, `workflow/07-regions.py`.
Doc: `docs/07-regions.md`. Decisión: D13.

## Variables a res 5

`06-variables.py --build --res 5`, 5/5 controles: 14.137 celdas, mismos totales que res 6 (63,177 Mha
quemadas y 250,797 Mha quemables). Celdas sin fuego: 3.099 (22 %), contra 38 % a res 6. La primera
corrida tenía un error (región de MapBiomas elegida antes de sumar los hijos) que marcó 14.135 celdas
con `region_share < 0.9`; corregido, quedan 1.145. Res 6 se volvió a correr: idéntica a la anterior.

## El grafo

Vecindad desde H3. Tres componentes sueltas, unidas a la celda más cercana: 8113 → 8117 (13 km),
14050 → 14052 (28 km), 14135 → 14091 (41 km). Las regiones 14 y 15 quedan unidas solo a través de
una de esas uniones.

## REDCAP, k = 15, mínimo 4.388 km²

`07-regions.py --build`, 4/4 controles. Between/total 0,460. 15 a 40 s por corrida (más con un hilo).
Mapa: `outputs/07-regions_r5_k15.png`.

| Región | Dónde (punto interior, lon/lat) | km² | Tasa %/año | Pico | En cicatrices ≥ 500 ha | Familia dominante | Área sin fuego |
|---|---|---|---|---|---|---|---|
| 1 | −64,5 / −26,4 | 357.261 | 0,68 | sep | 42 % | bosque | 5 % |
| 2 | −54,5 / −27,0 | 37.378 | 0,59 | ago | 6 % | bosque | 5 % |
| 3 | −61,7 / −29,2 | 229.091 | 2,42 | sep | 41 % | bosque | 0 % |
| 4 | −56,9 / −29,0 | 54.688 | 3,14 | feb | 38 % | pastizal | 2 % |
| 5 | −61,0 / −29,0 | 38.951 | 7,44 | ago | 57 % | pastizal | 0 % |
| 6 | −67,2 / −30,3 | 424.648 | 0,16 | oct | 59 % | arbustal | 46 % |
| 7 | −58,7 / −31,0 | 82.241 | 0,78 | sep | 6 % | pastizal | 0 % |
| 8 | −63,3 / −33,4 | 142.350 | 0,45 | sep | 13 % | agricultura | 1 % |
| 9 | −65,7 / −34,0 | 95.290 | 2,59 | oct | 67 % | bosque | 0 % |
| 10 | −56,7 / −35,4 | 19.058 | 0,03 | ene | 0 % | pastizal | 88 % |
| 11 | −61,0 / −34,9 | 351.761 | 0,23 | ene | 8 % | agricultura | 0 % |
| 12 | −67,9 / −37,3 | 110.041 | 2,38 | dic | 92 % | arbustal | 0 % |
| 13 | −65,3 / −37,7 | 50.812 | 5,38 | ene | 90 % | pastizal | 0 % |
| 14 | −62,3 / −39,3 | 42.301 | 1,29 | ene | 62 % | pastizal | 0 % |
| 15 | −68,4 / −42,0 | 809.383 | 0,06 | ene | 76 % | pastizal | 48 % |

Tasa: exacta. Pico, cicatrices grandes y familia: promedios ponderados de las celdas, primera mirada.
Tabla completa en `data/regions/summary_r5_k15.csv`.

## Lo que se ve

- **El tamaño mínimo no restringe.** La región más chica tiene 19.058 km², más de 4 veces el mínimo.
  A k = 16, 17 y 20, REDCAP da la misma varianza explicada con mínimo y sin él. Hoy el tamaño lo fija k.
- **La región 10 es un artefacto de borde.** Solo el 15,5 % de su área es quemable (país: 88,1 %) y
  el 77 % de sus celdas tiene menos de 10 % quemable: son celdas del Río de la Plata y la costa, casi
  agua, sin fuego, con la temporada rellenada por vecinas. Hay que tratar estas celdas antes del
  próximo borrador (por ejemplo, sacar del agrupamiento las de poca área quemable y asignarlas
  después a la región vecina).
- **Dos regiones gigantes de fuego raro**: la 15 (Patagonia, 809 mil km², 0,06 %/año) y la 6 (oeste
  andino y Puna, 425 mil km², 0,16 %/año), con casi la mitad del área sin fuego en 27 años. Juntas
  son el 44 % del país. Pesa el relleno de las celdas sin fuego (D12): mirar si dentro de ellas hay
  estructura que el relleno borra.
- **El fuego frecuente se parte fino en el centro-este**: 5 (7,4 %/año, pico en agosto), 13 (5,4 %,
  enero, cicatrices grandes), 4 (3,1 %, febrero), 9, 3 y 12 (2,4 a 2,6 %). Pico de fin de invierno en
  el norte y de verano en el centro y sur, como en el paso 06.
- **Pampa agrícola** (8 y 11): tasas bajas por construcción del producto (D10). Se separan por el
  pico (septiembre contra enero).

Lectura geográfica de cada región: **[no verificado]**, solo por la posición del punto interior. Se
confirma en el paso 09 cruzándolas con las ecorregiones.

## Curva de k

`07-regions.py --curve` (un hilo), between/total:

| k | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | 0,319 | 0,335 | 0,345 | 0,369 | 0,388 | 0,412 | 0,419 | 0,442 | 0,448 | 0,453 | 0,460 | 0,469 | 0,473 | 0,477 | 0,486 | 0,491 | 0,495 |

El proceso murió después de k = 21 con código 137 (matado por el sistema, probablemente por memoria:
pygeoda parece no liberarla entre corridas) y no escribió el CSV. k = 22 a 30, de corridas de prueba
fuera del repo: 0,502, 0,506, 0,51, 0,512, 0,53, 0,532, 0,534, 0,536, 0,538.

Lectura: no hay codo claro. Los saltos más grandes (~0,024) están en 7→8, 9→10 y 11→12; desde 12 la
curva sube de a ~0,005 por región. k = 12 aparece como candidato, a mirar en el mapa.

Pendiente: correr cada k en un proceso propio (con un hilo) para que `--curve` termine.

## pygeoda: caídas con varios hilos

Con los hilos por defecto, `--curve` se cortó con `std::length_error` de C++ en k = 16 en la primera
corrida y en k = 7 en la segunda (rearmando los pesos en cada k), y también con un proceso por k.
k = 16 solo, tres veces, corrió bien. Con `cpu_threads=1` corrieron k = 5 a 23 en un proceso y 24 a
30 en otro, con los mismos valores que las corridas con hilos. La primera corrida de un hilo se
detuvo después de k = 23 sin mensaje (no se vio el código de salida); la de 24 a 30 terminó con
código 0. Las regiones de k = 15 con un hilo son idénticas a las de varios hilos.

## Segunda pasada (2026-10-27): log, umbral de área quemable, k = 12 + 2

Cambios de D14. Corridas con `07-regions.py`, 4/4 controles en todas.

- k = 15 con los cambios: 571 celdas fuera del agrupamiento; desaparece la región del Río de la
  Plata. Patagonia sigue entera aunque la diferencia de tasa entre bosque y estepa pasó de 0,002 a
  0,223 (unidades del agrupamiento). Pesa más el pico (1,47).
- Curva de k = 2 a 30 completa (`--curve`, un proceso por k, 3 a la vez): sin codo. Regiones de cada
  k en `labels_r5.parquet`. Las regiones están anidadas en todos los k.
- Árbol de particiones (`scripts/region_review.py --splits 21`): k = 3, 4 y 5 explican 8,5, 5,5 y
  2,7 % de la variación total (tamaño de cicatriz, temporada, tasa); de k = 12 en adelante, 0,4 a
  0,7 % cada una. Patagonia se parte en k = 17 (Chubut) y k = 20 (Neuquén).
- REDCAP solo dentro de Patagonia (k = 2 a 4) da las mismas piezas que el árbol nacional.
- Bosque (≥ 50 %) en Patagonia por latitud, tasa por año: Neuquén 0,298 %; 40 a 43°S 0,291 %;
  43 a 46°S 0,132 %; 46 a 50°S 0,008 %; sur de 50°S 0,022 %.
- Quemado al menos una vez (`region_review.py --burned-once 12`): 38,554 Mha de 250,797 quemables
  (15,4 %), igual al paso 04. Varios bordes de k = 12 siguen cambios del acumulado.
- **Las dos medidas de varianza explicada no coinciden.** `ss_ratio` (nuestra) da 0,523 para k = 12,
  0,537 para k = 14 y 0,566 para k = 20; pygeoda da 0,469, 0,480 y 0,509. No se investigó qué calcula
  pygeoda. Comparar mapas solo con una de las dos.
- Mapa elegido: k = 12 + 2 (`regions_r5_k12_forced*`), 14 regiones, `ss_ratio` 0,532.


## Tercera pasada (2026-10-27): Delta del Paraná, nombres y parecidos

- **Chequeo contra el acumulado y la cobertura** (mapas ad hoc, sin script): las regiones de fuego
  frecuente caen sobre los núcleos del quemado al menos una vez, y las de fuego raro sobre lo nunca
  quemado. Varios bordes siguen la cobertura (Pampa agrícola y bonaerense, Chaco y Corrientes). Las
  regiones del Chaco occidental y del Espinal son mezclas de coberturas y de niveles de fuego.
- **Delta del Paraná** (D15): metido en el Espinal, se quemaba bastante más que el resto. El árbol lo
  separa en k = 25; se fuerza como tercera pieza: 15.401 km², 4,32 %/año. Al forzarlo, una celda de
  agua en la desembocadura del Uruguay quedó separada de su región y falló el control de conexión;
  se corrigió reasignando las celdas fuera del agrupamiento sobre el mapa final. 15 regiones,
  `ss_ratio` 0,536, 4/4 controles.
- **Bosque andino-patagónico norte** (revisión ad hoc, sin script): entre las piezas de Neuquén y
  Chubut, el bosque de Río Negro queda en la Estepa patagónica. Entre 41 y 42°S se quema como en
  Neuquén; entre 40 y 41°S (Nahuel Huapi) casi no registra fuego. El árbol no arma una región continua
  en ningún k hasta 30. Queda como pregunta para el taller.
- **Nombres y colores**: propuestos, en `PYROREGION_NAMES`, atados a un punto de cada región. La
  leyenda del mapa lee las provincias del paso 09.
- **Regiones parecidas** (`scripts/region_review.py --similar`): los pares más cercanos son vecinos
  (Andes áridos con Estepa patagónica 0,98; Chaco central con Espinal 1,12; las dos Pampas 1,13). La
  Selva misionera queda más cerca de la Pampa agrícola (1,62): fuegos chicos y temporada larga.
