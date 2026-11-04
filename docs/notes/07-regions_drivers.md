# 07 · Qué separa a las pirorregiones y por qué crecen así (2026-10-28)

Cuaderno de laboratorio. Script: `scripts/region_review.py` (`--drivers`, `--tree`, `--fichas`).
Doc: `docs/07-regions.md`. Origen: reunión con el equipo de MapBiomas del 2026-10-28, que pidió la
matriz de distancias en bloques, dónde cae cada región en cada variable, la jerarquía de variables
en el crecimiento y por qué el bosque andino-patagónico norte no forma una región.

## Cómo crece REDCAP, leído en el código

pygeoda 0.1.3 no devuelve el árbol. Su docstring dice que REDCAP arma un árbol de expansión y
después lo poda. El detalle sale de libgeoda (`clustering/redcap.cpp`, rama master, leído el
2026-10-28):

- **Etapa 1** (`FullOrderWardRedCap::Clustering`): une los dos grupos vecinos con menor distancia,
  actualiza la distancia de todos los grupos al nuevo con Lance-Williams (Ward) y agrega al árbol la
  arista original más corta entre los dos grupos.
- **Etapa 2** (`AbstractClusterFactory::Partitioning`, `Tree::Partition`): cada árbol busca la
  arista cuyo corte más reduce su suma de cuadrados, con los dos lados por encima del área mínima;
  se parte el árbol con la mayor reducción, hasta tener k.

`--tree` reconstruye las dos etapas. **Con Ward sobre la distancia euclídea al cuadrado, el corte
da exactamente las regiones de pygeoda en k = 5, 12, 20 y 25** (4/4). Con la distancia simple
difieren entre 1.223 y 2.943 celdas. El código master de libgeoda dice que Ward usa distancias al
cuadrado; la versión instalada se comporta igual.

Consecuencias: una región es una rama del árbol, sin condición de compacidad (de ahí las formas
dendríticas), y dos zonas parecidas que el árbol unió por otro camino no se juntan en ningún k.

## Bosque andino-patagónico norte

Franja: celdas agrupadas con ≥ 50 % de bosque, al oeste de 70°W, entre 39 y 46°S.

- 136 celdas: **3 piezas** como vecinas en el grafo, **22 piezas** dentro del árbol. El árbol entra
  y sale de la franja por la estepa.
- Caminos en el árbol (`tree_paths_r5.csv`): oeste de Neuquén a Nahuel Huapi, 122 km, 101 celdas;
  Nahuel Huapi a El Bolsón, 92 km, **242 celdas**, hasta 65,6°W y 47,8°S, 11 % de bosque; El Bolsón
  al oeste de Chubut, 125 km, 16 celdas dentro de la pieza de Chubut.
- Tasa mediana y celdas sin fuego por banda: 39 a 40°S 0,060 %/año y 11 %; 40 a 41°S 0,000 y
  **47 %**; 41 a 42°S 0,106 y 13 %; 42 a 43°S 0,067 y 12 %; 43 a 46°S 0,018 y 14 %.

Lectura: el tramo del Nahuel Huapi, casi sin fuego y con valores de relleno (D12), se parece a la
estepa y corta la franja. Sin decidir si es poco fuego real u omisión del producto.

## Qué variables separan (`--drivers`)

R² por variable en el mapa k = 12 + 3: tasa 0,73, recurrencia 0,67, variabilidad 0,65, cicatrices
grandes 0,55, duración 0,48, pico coseno 0,43 y seno 0,28. Familias de cobertura: R² de 0,13
(pastura) a 0,56 (agricultura), pero con peso 0,2 suman **2,5 %** de la variación entre regiones.

Por corte del árbol (`split_vars_r5.csv`, % de la variación total): k = 3 lo domina el tamaño de
cicatriz (4,6 de 8,5); k = 4 el pico (seno 1,6, coseno 1,3); k = 5 recurrencia (1,0) y tasa (0,6).
Ninguna familia de cobertura pasa de 0,12 en ningún corte.

## Fichas (`--fichas`)

Una fila por región en `fichas_r5_k12_forced.csv` y un mapa de ubicación en `outputs/fichas/`. Dos
regiones concentran el 61 % de lo quemado: Chaco central 34,9 % y Monte y Caldenal 26,5 %.

## Sensibilidad: historia de celdas con poco fuego sumada a sus vecinas (`--pool`)

Acordado con Ramón el 2026-10-28 como prueba, sin tocar el mapa elegido. `06-variables.py --build
--res 5 --pool` y `07-regions.py --build --k 12 --pool`; comparación con
`region_review.py --pool-review`.

Regla: una celda con menos de 10 meses con fuego (`POOL_MIN_EVENTS`; Vidal-Riveros et al. 2024 piden
10 registros para tamaño e intensidad) calcula pico, duración, tamaño y CV sumando su historia con la
de sus vecinas, anillo por anillo hasta 3. Tasa, recurrencia y cobertura quedan propias.

- 5.324 celdas (38 %) tienen menos de 10 meses con fuego: 3.110 se completan en el anillo 1, 1.359 en
  el 2, 855 en el 3; 344 siguen cortas y 105 no tienen fuego ni sumando. 5/5 controles del paso 06;
  familias, tasa y recurrencia idénticas a las del mapa elegido.
- REDCAP k = 12 con estas variables: 4/4 controles. El árbol reconstruido da sus mismas regiones.
- **El bosque andino norte no forma región**: mejor Jaccard de área 0,22 en k = 2 a 30 (sin suavizar,
  0,23); 18 ramas del árbol (antes 22).
- **Las piezas de Neuquén y Chubut desaparecen**: sin suavizar aparecen idénticas en k = 20 y 17;
  suavizando, ninguna región se les parece más que 0,32 y 0,29 en k = 2 a 30. El Delta sigue
  apareciendo (k = 23, Jaccard 0,83).
- El mapa cambia mucho: a k = 12, 71,6 % del área queda en la región que mejor corresponde. En la
  Patagonia el k = 12 suavizado gasta tres regiones en piezas que no son la franja (alrededor de
  −70,8/−39,9, −71,3/−42,0 y la costa de Chubut). Los bordes no se ven menos dendríticos (a ojo).

Lectura: el suavizado no arregla la franja de bosque y borra las piezas que D14 fuerza, porque mezcla
sus descriptores con los de la estepa vecina. Recomendación: no adoptarlo; D14 queda como está.

## Encontrado de paso

- **El respaldo de familias no es reproducible.** En `06-variables.py`, la familia de respaldo de una
  clase es `max(set(fs), key=fs.count)`. La clase 21 empata entre pastizal y agricultura, y el orden de
  un `set` de textos depende de la semilla de hash de Python: cada corrida puede elegir una distinta y
  mover 50 celdas de res 5 (hasta 0,28 de `fam_grassland`). El mapa elegido se armó con pastizal
  (`PYTHONHASHSEED=1` reproduce `variables_r5.parquet` idéntico). La corrida `--pool` usó esa semilla.
  Resuelto el mismo día: pastizal (D11), desempate determinístico y `FALLBACK_FAMILY`; con las
  semillas 2 y 3 las variables de res 5 quedan idénticas a las del mapa, y también res 6 y `--pool`.
- **El Delta se separa en k = 24, no en k = 25.** En `labels_r5.parquet` la pieza ya está idéntica en
  k = 24 (y la de Chubut en k = 17). Corregido el texto de D15, del comentario de `FORCED_SPLIT_POINTS`
  y de la nota del borrador; el valor 25 del código queda, porque da la misma pieza.

## Sensibilidad: peso de la cobertura (`--cover`, 2026-10-28)

Acordado con Ramón: la cobertura tiene que pesar en la regla. Sin tocar el mapa elegido. Siete
variantes del peso de las familias: uniforme 0,2 (el del mapa), 0,35, 0,5, 0,75 y 1,0; y "según el
fuego visto", 0,2 con 10 o más meses con fuego (`POOL_MIN_EVENTS`) subiendo lineal hasta 0,5 o 1,0
sin ninguno. 4.768 de 13.566 celdas agrupadas tienen menos de 10 meses con fuego; 2.608, ninguno.
Árbol reconstruido, cortado en k = 2 a 30; a k = 12 coincide con pygeoda en 0,2, 1,0 y "según
fuego, hasta 0,5" (3/3). Tabla: `cover_review_r5.csv`; mapa: `outputs/review-cover_k12.png`.

Criterio de la franja corregido en el camino: el Jaccard ≥ 0,5 no la veía, porque la región que se
forma incluye el ecotono y es más grande que la franja. Ahora "aparece" cuando una región tiene al
menos 80 % de la franja y la franja es al menos 40 % de la región (umbrales nuestros).

| Variante | Franja aparece en k | Área de esa región | Mapa k = 12 igual | Regiones de k = 12 que siguen | Cobertura en la separación (k = 12) |
|---|---|---|---|---|---|
| uniforme 0,2 | nunca | | 100 % | 12 | 2,5 % |
| uniforme 0,35 | nunca | | 81 % | 8 | 7,8 % |
| uniforme 0,5 | 14 | 56.985 km² | 81 % | 7 | 17,9 % |
| uniforme 0,75 | 15 | 44.414 km² | 74 % | 3 | 37,8 % |
| uniforme 1,0 | nunca | | 72 % | 5 | 51,7 % |
| según fuego, hasta 0,5 | **9** | 46.743 km² | **94 %** | **10** | 5,1 % |
| según fuego, hasta 1,0 | 16 | 61.055 km² | 74 % | 8 | 14,6 % |

Lectura:
- Con peso uniforme, la región de bosque aparece desde 0,5, pero el resto del país cambia mucho
  (quedan 7 de las 12 regiones o menos). Con 1,0 la cobertura manda (52 % de la separación) y el
  bosque se mezcla con otras regiones de fuego raro.
- **"Según fuego, hasta 0,5" es la variante más quirúrgica**: a k = 12 ya tiene una región de bosque
  andino norte de 46.743 km², entre 39,4 y 45,2°S, 0,28 %/año, 37 % de bosque en su área quemable,
  13 % de celdas sin fuego. Contiene el 98 % de la pieza de Neuquén y el 100 % de la de Chubut: las
  dos piezas forzadas de D14 dejan de hacer falta. El 94 % del área queda en su región equivalente.
- Costo: a k = 12 se pierden las Sierras de Córdoba y San Luis (Jaccard 0,09, entra al Chaco
  central) y el Chaco occidental cambia de forma (0,38). El Delta sigue apareciendo recién en k = 24.
- Efecto secundario del peso por celda: entre una celda con poco fuego y una con mucho, la cobertura
  pesa distinto en cada una, y eso agrega una diferencia aunque las dos tengan la misma cobertura.
  No medido por separado.

## Robustez del peso según el fuego (`--cover-grid`, 2026-10-28)

Para ver si la región de bosque aparece solo en el punto elegido (tope 0,5, 10 meses con fuego) o en
un rango: 15 variantes, topes 0,3 / 0,4 / 0,5 / 0,6 / 0,75 por umbral de 5 / 10 / 20 meses con fuego
(el peso vuelve a 0,2 desde ese umbral). Árbol reconstruido igual a pygeoda en la esquina más
extrema (0,75 y 5 meses), 2/2 controles. Antes, `--cover` vuelto a correr tras reorganizar el código:
el mismo CSV. Tabla: `data/regions/cover_grid_r5.csv`.

A k = 12, si aparece la región de bosque, con el área del mapa actual que queda igual y las regiones
que siguen de 12:

| Tope | 5 meses | 10 meses | 20 meses |
|---|---|---|---|
| 0,3 | no | no | no |
| 0,4 | sí (97 %, 11) | nunca | nunca |
| 0,5 | sí (90 %, 8) | sí (94 %, 10) | sí (89 %, 9) |
| 0,6 | sí (88 %, 9) | sí (91 %, 10) | en k = 13 (84 %, 9) |
| 0,75 | sí (92 %, 10) | sí (79 %, 7) | sí (81 %, 6) |

Lectura:
- **La región de bosque es robusta desde tope 0,5**: aparece a k = 12 en 8 de 9 variantes y en la
  otra a k = 13. Siempre casi la misma: 45.000 a 58.000 km², 98 % de la pieza de Neuquén, 98 a 100 %
  de la de Chubut. Con 0,3 nunca aparece (el bosque queda en una región de casi 800.000 km²).
- **No es robusto el costo en el resto**: qué regiones se pierden cambia con la variante. El Chaco
  occidental cambia de forma en casi todas; Selva misionera, Pampa agrícola y Sierras entran y salen.
- El Delta aparece recién entre k = 22 y 26 en todas: sigue forzado.

## Mapa candidato (`07-regions.py --cover-by-fire`, 2026-10-28)

Pedido de Ramón: el mapa con peso según el fuego (0,2 a 0,5, 10 meses), Delta forzado y nombres.
Sin adoptar: el mapa elegido sigue siendo k = 12 + 3 (D14, D15). Salidas con sufijo `_coverfire`;
mapa `outputs/07-regions_r5_k12_forced_coverfire.png`. 14 regiones, 4/4 controles, `ss_ratio` 0,528.

- Bosque y ecotono andino norte: 47.527 km², 0,28 %/año; 50 % Bosques Patagónicos y 42 % Estepa;
  Chubut 54 %, Neuquén 25 %, Río Negro 13 %.
- Delta del Paraná: la pieza de k = 25 sale idéntica a la del mapa elegido, 15.401 km², 4,32 %/año.
- **Rama fina del Monte y Caldenal = el Alto Valle del Río Negro y Neuquén.** A k = 12, 22 celdas
  (4.307 km²) entre Neuquén y Chichinales, unidas al resto de la región por 3 celdas. Régimen muy
  distinto: 0,06 %/año contra 2,9 del resto, sin fuegos grandes, temporada ~5 meses; 81 % pastizal,
  15 % agricultura. En el espacio del agrupamiento está más cerca de la Pampa bonaerense (1,22) y de
  la Estepa (2,73) que del Caldenal (3,70): cuelga del Caldenal por la forma del árbol. El árbol la
  separa sola en k = 24 sumando el Valle Medio: 36 celdas, 6.989 km², 0,16 %/año.
  Opciones: forzarla como pieza, pasarla a la Estepa (regla nueva, mezcla regímenes) o dejarla.
  **Ramón eligió forzarla** (mismo mecanismo que el Delta): "Valles irrigados del Río Negro", Río
  Negro 70 % y Neuquén 30 %. Ojo: régimen armado por riego y quemas chicas, y el producto excluye el
  fuego agrícola, así que su tasa está subestimada por construcción.
- Pendiente: el nombre "Chaco occidental y pedemonte" ya no sirve en este mapa. El pedemonte pasó al
  Chaco central y queda una isla de Chaco seco (Salta, Chaco, Santiago del Estero) a 0,07 %/año. En
  la leyenda ese nombre largo se pisa con la tasa.
- Se pierden las Sierras de Córdoba y San Luis (dentro del Chaco central).
