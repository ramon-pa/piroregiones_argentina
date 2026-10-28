# Decisiones de diseño

Cada decisión lleva su estado (**abierta**, **acordada**, **descartada**) y su fundamento.
Una decisión acordada se cambia solo agregando una entrada nueva que la reemplace, nunca borrándola.

---

## D1 · Unidad de análisis · acordada (2026-10-17)

**Hexágonos H3.** Se extrae una vez en **res 6** y se arma localmente **res 5** sumando áreas
(`h3.cell_to_parent`). El mapa final usa una sola resolución, elegida entre res 5 y res 6 por
criterio ecológico después de los pasos 06 y 07. Res 4 y res 7 quedan descartadas.

- **Cálculo a 30 m en la grilla nativa.** Fuego col-1 y cobertura col-3 comparten la misma red de
  píxeles (`CLAUDE.md`, "GEE asset paths"): cruzarlos no remuestrea. Toda área se suma con
  `pixelArea()`. El cruce sale de la colección mensual `fire_mask_v2` y la LULC col-3; los
  subproductos `_v2` derivados están en EPSG:3857 y no se usan.
- **Por qué hexágonos.** Iván los recomienda (15-oct-2026) como lo que se usa para regionalizaciones
  de este tipo; dan vecinos sin ambigüedad (Birch et al. 2007, resumen). Ninguna grilla elimina el
  efecto borde del país ni de la costa.
- **Por qué la deformación de H3 no pesa.** En Argentina el 90 % de las celdas varía como mucho
  1,38 veces en área (extremos 1,59), del mismo orden que el píxel nativo, y no cae ningún pentágono.
  Todas las variables son tasas sobre el área disponible, así que no dependen del tamaño de la celda.
  El tamaño mínimo de región se mide en área, no en cantidad de celdas. Plan B si se objeta:
  hexágonos planos de igual área en Albers para Sudamérica (cada tamaño se extrae aparte).
- **Por qué res 5 y res 6.** En los antecedentes con grilla, las celdas van de 5 a 60 km. Res 4
  (~1.450 km² de media) deja ~3 celdas por región mínima (criterio de Erni, ~4.388 km²); res 7
  (~668 mil celdas) no entra en el código empaquetado de 32 bits y obliga a subir ~668 mil polígonos.
- **Por qué no es una decisión de cómputo.** Medido: el tamaño de celda no cambia el costo de la
  reducción; lo que cuesta es recorrer los píxeles (`docs/notes/01-grid_and_compute.md`).
- **Res 5 armada desde res 6 (precisión del 2026-10-19).** Los 7 hijos no llenan exacto su padre de
  res 5 (su unión tiene forma de copo): sumar las áreas de los hijos es exacto, pero en un mapa en
  res 5 cada celda se dibuja como la unión de sus hijos, no con el contorno H3 de res 5. Los 96.461
  hexágonos de res 6 tienen 14.137 padres (`workflow/01-hex_grid.py`; `docs/01-hex_grid.md`, "Trampas").

## D2 · Período · acordada (2026-10-26)

**Acordado** (Ramón, 2026-10-26): 1999 a 2025 completo. El control de estabilidad entre dos
mitades del período queda como agregado opcional para el paso 09, si el tiempo lo permite.


**Propuesta.** 1999 a 2025, la ventana completa de fuego col-1.

Un régimen es una estadística de varios años: frecuencia, variabilidad interanual e intervalo no
existen con un solo año. Erni et al. 2020 declaran como limitación que su registro de 47 años es
más corto que el intervalo de retorno en casi todo Canadá, así que una ventana más corta empeora el
problema en las zonas de fuego raro.

## D3 · Dónde vive el estado del proyecto · abierta

**Propuesta.** `ROADMAP.md` es la fuente de verdad; la página de seguimiento es una vista que se
actualiza al cerrar cada sesión.

## D4 · Tasa de quema por cobertura · acordada (2026-10-14)

Variable: área quemada de una clase sobre el área disponible de esa clase, por celda y por año.
No se usa la composición cruda de lo quemado.

Por qué: la composición reproduce el mapa de vegetación (donde solo hay pastizal, se quema
pastizal). La tasa separa una misma clase con regímenes distintos.

Precedentes:
- Boulanger et al. 2014 expresan las variables de fuego en función del área de combustible de cada
  celda, y además suman la composición de combustible al clustering con peso 0,2 frente a 1,0 de las
  variables de fuego.
- Erni et al. 2020, principio 4: una variación ambiental que no viene con una variación del régimen
  no es un límite.

Advertencia: la tasa de la clase agrícola está subestimada por las reglas de exclusión del producto
(`CLAUDE.md`, "Known issues and fixes"). Excluirla de las variables o declararla como artefacto.

Qué cobertura usar para cada fuego: **la del año previo** (`classification_<Y−1>` para un fuego del
año Y). Es la regla de todo el mapeo y el análisis del equipo de fuego: la cobertura del año del
fuego puede ser ya consecuencia del fuego (`CLAUDE.md`, "GEE asset paths"; corrección de Iván,
15-oct-2026). El denominador de la tasa (área disponible de cada clase) también se toma en Y−1.
Para 1999 se usa 1998, disponible en la col-3.

Riesgo: la validación preliminar del producto sugiere omisión alta (`CLAUDE.md`, "Known issues and
fixes"). La tasa de quema estaría subestimada, quizás de forma desigual entre regiones.

## D5 · Dos niveles: regiones y tipos · abierta

**Estado al 2026-10-27, segunda pasada** (Ramón): k = 12, más dos piezas forzadas en Patagonia
(D14). La curva de k no tiene codo: desde k = 12 cada partición del árbol suma entre 0,7 y 0,4 % de
la variación total (`data/regions/splits_r5.csv`, `scripts/region_review.py --splits`). El mínimo de
4.388 km² sigue sin restringir.

**Estado al 2026-10-27**: primer borrador con k = 15 y mínimo de 4.388 km² (Ramón). A k = 15 el
mínimo no restringe nada: la región más chica tiene 19.058 km², y a k = 16, 17 y 20 REDCAP da la
misma varianza explicada con mínimo y sin él. Por ahora el tamaño lo fija k
(`docs/notes/07-regions_draft.md`).

**Estado al 2026-10-26** (Ramón): sigue abierta. En el paso 07 se prueban dos criterios de tamaño, el
doble de la cicatriz más grande (Erni et al. 2020) y una cantidad fija de regiones del orden de las
ecorregiones, y se elige con los resultados a la vista. Preguntarle también a Iván.

**Propuesta**, siguiendo a Erni et al. 2020:

- Nivel 1, **pirorregiones**: zonas continuas, con nombre. Se obtienen con regionalización con
  restricción de contigüidad, como hicieron Boulanger et al. 2014 (Ward con contigüidad, REDCAP).
  Erni et al. dibujaron este nivel a mano; acá se propone hacerlo cuantitativo para que sea
  reproducible.
- Nivel 2, **tipos de régimen**: agrupamiento de las pirorregiones sin contigüidad, de modo que dos
  regiones lejanas puedan compartir tipo (Erni et al. 2020: Ward sin restricción espacial).

Tamaño mínimo de región: sin decidir. Los dos criterios publicados son distintos:

| Criterio | Fuente | Valor para Argentina |
|---|---|---|
| Doble del fuego más grande registrado en la región | Erni et al. 2020 (citando a O'Neill et al. 1996) | 2 × 219.410 ha = 438.820 ha ≈ 4.388 km², si se toma la cicatriz más grande del país |
| La ecozona más chica con actividad de fuego significativa | Boulanger et al. 2014 (200.000 km²) | no tiene equivalente directo; habría que definirlo con ecorregiones argentinas |

Evaluación propuesta, de Boulanger et al. 2014: comparar el R² ajustado que explica la
regionalización con el que explican las ecorregiones, y repetirlo en un período reservado.

Herramienta: sin decidir. Candidata principal: `pygeoda.redcap` en su variante de orden completo
con enlace de Ward, que es el método de Boulanger et al. 2014, con `min_bound` sobre el área para el
tamaño mínimo. Alternativas en `spopt`. Ver `docs/references.md`, "Herramientas". Se verificaron las
firmas y la documentación; no se corrió ningún análisis.

## D6 · Un solo barrido por año · acordada (2026-10-19)

Cobertura disponible y quemado salen de **una sola reducción por año**, con un código empaquetado
`celda × 13.000 + clase(Y−1) × 130 + mes (0 = no quemado) × 10 + clase de tamaño (0 = no quemado)`.
Sumando todas las filas de una celda y clase sale el área disponible; sumando las de mes > 0, el
área quemada. Los multiplicadores viven en `utils/constants.py`.

**El mes se queda en el código** (Ramón, 2026-10-19): en qué mes se quema cada hexágono, y cada
cobertura dentro de él, es una variable central para separar regiones. No agrega pasadas: lo que
cuesta es recorrer los píxeles, no la cantidad de grupos (`docs/notes/01-grid_and_compute.md`).

Por qué un solo barrido: la cobertura del año previo se lee una vez por año en vez de dos, y
numerador y denominador salen de la misma lectura a 30 m. El código entra en un entero de 32 bits
hasta res 6 (máximo 1.253.990.138 con 96.461 celdas y clase 77, sobre 2.147.483.647). Una tarea por
año, para acotar la memoria del reductor agrupado.

De este barrido salen la tasa por cobertura (D4), la fracción quemada por año, la estacionalidad
(total y por cobertura) y los tamaños. Por eso no se usan `annual_burned_v2` ni `monthly_burned_v2`:
darían lo mismo desde otra grilla (EPSG:3857).

Insumos, todos en la grilla nativa (`CLAUDE.md`, "GEE asset paths"):
- mes: `fire_mask_v2` del año Y;
- clase de tamaño: `annual_burned_scar_size_range_v2`, banda del año Y (clases 1 a 8);
- cobertura: col-3, `classification_<Y−1>`;
- celda: la grilla H3 pintada sobre un fondo enmascarado (un píxel fuera de toda celda no entra).

Reglas que evitan errores silenciosos (medidas el 2026-10-19, recuadro de Córdoba, 2003, 2013 y 2020):
- **Lo no quemado viene enmascarado, no en 0**, en el mes y en el tamaño. Hacer `unmask(0)` en los
  dos antes de armar el código; si no, el área disponible saldría solo de lo quemado.
- **Mes y tamaño coinciden píxel a píxel**: 0 píxeles con mes y sin tamaño, 0 al revés. Se vuelve a
  comprobar en cada corrida (fila con mes > 0 y tamaño 0, o al revés, es un error).
- **Cobertura enmascarada → clase 0** (`unmask(0)`), para que su área quede a la vista como "no
  observada" en vez de desaparecer.

Descartado: leer la cobertura a menor resolución. Ahorra ~2 a 3 veces el tiempo, pero las pirámides
por moda subestiman hasta 26 % la clase Pasturas a 240 m (`docs/notes/01-grid_and_compute.md`).

Pendiente: la prueba en el recuadro de Córdoba (`ROADMAP.md`, ítem 1 de "Siguiente").

## D7 · Dónde van las salidas · acordada (2026-10-19)

- **Asset** `FIRE/COLLECTION-1/ANALYSES/pyrorregions` (`OUTPUT_ROOT`): solo lo que GEE vuelve a
  leer, la grilla H3, y al final, si se quiere mostrar en GEE, los polígonos de pirorregiones.
  Iván pidió esa carpeta (mail del 2026-10-19) porque no hay espacio en Google Cloud, solo en la
  cuota de assets, y que lo guardado sea entero. La creó el 2026-10-19; la escritura con la cuenta
  ramonpagis se probó ese día creando y borrando una subcarpeta.
- **Tablas** (27 de D6 y 1 de frecuencia): CSV con `Export.table.toDrive` a la carpeta
  `DRIVE_FOLDER` del Drive propio, y de ahí a `data/` (fuera de git). Todo el análisis es local, así
  que guardarlas como asset obligaría a bajarlas igual. Así exporta sus tablas el equipo de fuego
  (`statistics.md`, sección del denominador quemable). Se pueden regenerar volviendo a correr.
- **Ningún ráster**, salvo que pintar la grilla en cada tarea resulte lento: en ese caso, el ráster
  de ids de celda, en `int32`, en `OUTPUT_ROOT`.
- Compute: proyecto `mapbiomas-argentina` (Iván: "mapbiomas-argentina o mapbiomas-fuego, da igual").

## D8 · Frecuencia desde el producto publicado · acordada (2026-10-19)

La frecuencia (paso 04) sale de `frequency_burned_v2`, banda `fire_frequency_1999_2025` (años
calendario quemados de 27). No se calcula: necesitaría los 27 años de cada píxel juntos.

Está en EPSG:3857, fuera de la grilla nativa. No importa porque **no se cruza píxel a píxel con la
cobertura**: solo se resume por celda (área quemada 1, 2, 3... veces). El equipo de fuego lo usa así
y lo comprobó: el promedio ponderado por área da 0,838 % nacional, igual a 63,23 Mha / 279,5 Mha /
27 años (`statistics/burn_perc_export.py`; `statistics.md`, "EPSG:3857 is a display grid, not a
measurement grid"). Medido por ellos, no por nosotros.

Sus dos trampas aplican igual:
- el producto tiene `selfMask`: lo nunca quemado falta. No se resume el área de 0 veces desde el
  producto (incluiría agua y roca); sale del denominador quemable (D9) menos lo quemado 1 o más veces;
- en 3857 el área real del píxel cae con la latitud: sumar con `pixelArea()`, nunca contar píxeles.

Control: por celda, `Σ k × área quemada k veces` (frecuencia) tiene que igualar la suma de las áreas
quemadas de los 27 años (D6). La diferencia mide el efecto de mezclar las dos grillas; sin medir.

No se usa `frequency_burned_coverage_v2`: en la ventana completa su clase es la de 2025
(`07-published_products.md`, "Frequency windows are two-sided"), no la del año previo a cada fuego.

## D9 · Denominador quemable · acordada (2026-10-19)

Los porcentajes que no van por cobertura (fracción quemada por año, frecuencia) se calculan sobre el
**área quemable** de la celda, no sobre su área total (Ramón, 2026-10-19). Así una celda con mucha
agua, salina o roca no parece quemarse poco.

Quemable = suma de las clases de `BURNABLE_CLASSES` del año Y−1, que sale del barrido D6 sin nada
extra en GEE. Las listas de clases son las del equipo de fuego (`statistics/legends.py`), para que
los porcentajes sean comparables con los suyos; 22 y 26 los decidió no quemables Iván (2026-09-11,
según ese archivo). Clases 0 y 27, no observadas: fuera del numerador y del denominador.

Diferencia con el equipo de fuego: ellos usan **una** capa quemable fija (mayoría 1998 a 2024); acá
es la del año Y−1 de cada año, coherente con D4. Para la frecuencia, que no tiene año, se usa el
promedio de las 27 áreas quemables anuales de la celda.

Control: se informa el área quemada sobre clases no quemables o no observadas. Se espera chica pero
no nula: el producto no admite **semillas** sobre clases no quemables del año previo (verificado por
el equipo de fuego en FY2000, 2014 y 2023, comentario de `CLASSIFICATION_COLLECTIONS` en
`utils/constants.py` de su repo), pero la cicatriz que crece desde una semilla sí puede cubrirlas.
Ese área queda fuera de las tasas y se reporta, no se descarta en silencio.

## D10 · La agricultura fuera de las tasas por cobertura · acordada (2026-10-26)

**Acordado** (Ramón, 2026-10-26): las clases agrícolas no entran como variables de tasa de quema por
cobertura (D4). Su área sigue en el denominador quemable (D9), porque las listas son las del equipo
de fuego. Consecuencia que se declara al presentar: la fracción quemada por celda baja en las zonas
agrícolas.

Por qué: el producto descarta todo objeto con más de 40 % de agricultura, en todo el país y en
cualquier estación (regla B, `docs/07-vector_to_raster.md`, "Object exclusion ruleset", repo de
fuego). La tasa agrícola es baja por construcción, no por el fuego.

**Qué clases: solo la 19** (Ramón, 2026-10-26). Es la única que la regla B descarta en todas las
regiones donde aparece, y es casi toda el área agrícola. 9 y 21 quedan como tasas, porque la regla
las toca solo en una región. Pendiente preguntarle a Iván si el remapeo es sobre la col-3.

La regla B cuenta como agricultura las clases `agriculture_*` de su
remapeo (`config/veg_fire_remap.csv` del repo de fuego), y ese remapeo depende de la región:

| Clase col-3 | En la regla B | Área media 1998 a 2024 | Tasa de quema media anual |
|---|---|---|---|
| 19 Cultivos temporarios | sí, en Cuyo, Pampa y Chaco | 38,18 Mha | 0,20 % |
| 9 Silvicultura | solo en Cuyo | 0,96 Mha | 0,65 % |
| 21 Mosaico de usos | solo en Patagonia | 2,03 Mha | 0,34 % |
| 36 Cultivos perennes | no (la regla excluye los perennes a propósito) | 1,24 Mha | 0,74 % |
| 15 Pastura | no | 6,78 Mha | 1,65 % |

Áreas y tasas: `workflow/05-cell_table.py --classes`, 2026-10-26. [no verificado] si ese remapeo se armó sobre la col-3 o sobre una colección anterior:
el repo de fuego dice que `veg_fire` queda congelado en la colección con la que se entrenó.


## D11 · Familias de cobertura del equipo de fuego, con región · acordada (2026-10-26)

**Acordado** (Ramón, 2026-10-26): las clases de cobertura se agrupan en las familias de la
reclasificación para fuego del equipo de fuego (`config/veg_fire_remap.csv`, documentada en su
`docs/02-vegetation_remap.md`): bosque, arbustal, pastizal, pastura, agricultura y cultivos
perennes. La familia depende de la región de MapBiomas (por ejemplo, la 63 es arbustal en el Chaco y
pastizal en Cuyo y Patagonia), así que cada celda toma su región mayoritaria del ráster de regiones
del equipo de fuego (`REGION_RASTER`). Copiado a `FAMILY_BY_REGION_CLASS`, generado desde el CSV.

Ese remapeo se armó sobre la col-2 (comentario de `statistics/legends.py` del repo de fuego); los
códigos de clase que usa existen igual en la col-3. Un par región-clase que no figura toma la familia
más común de esa clase: 0,52 Mha por año, 0,2 % del área quemable (`06-variables.py`, 2026-10-26).

## D12 · Qué describe a cada celda en el clustering · acordada (2026-10-26)

**Acordado** (Ramón, 2026-10-26, las cinco recomendaciones). Reemplaza el papel de D4 en el
clustering: la tasa por cobertura deja de ser variable de celda.

1. **Variables de fuego**: tasa de quema, variabilidad interanual, recurrencia, pico de la
   temporada, duración de la temporada y proporción de lo quemado en cicatrices grandes. Más la
   composición del área quemable por familia (D11) con peso 0,2 frente a 1,0, como Boulanger et al.
   2014 (p. 368). La tasa por familia (D4) se calcula **por región** ya formada, donde las áreas son
   grandes, y va a la ficha de cada región.
2. **Celdas sin fuego**: se quedan, con valores como en Segura-Garcia et al. 2025 ("Methods",
   (b)(i)): tasa, recurrencia y tamaño en el mínimo; pico y duración de la temporada, promedio de las
   vecinas (acá anillo por anillo, porque los bloques sin fuego son grandes).
3. **Recurrencia**: cuantil 99 de las veces quemado de cada hectárea, 0 incluido (Segura-Garcia).
4. **Pico de la temporada**: mediana del área mensual en un año de fuego centrado en el mes de más
   quema (Segura-Garcia); entra al clustering como seno y coseno, porque el mes es circular.
   **Duración**: 2 desvíos del mes en ese año (Cattau et al. 2022, Tabla 1, p. 4, allí en días
   julianos). El índice de concentración de Naval-Fernández et al. 2025 no se usó: el PDF no se pudo
   bajar (403) y su fórmula no estaba en la ficha.
5. **Ruido de celdas con poco fuego**: nada en el paso 06; en el paso 07 se prueba también res 5
   (D1).

Elecciones nuestras, sin paper, declaradas en `docs/06-variables.md`: el corte de 500 ha del tamaño,
el CV de las celdas sin fuego, la posición del mes pico dentro del año centrado y la falta de
suavizado de la ECDF.

## D13 · El borrador del paso 07 a res 5, con REDCAP · acordada (2026-10-27)

**Acordado** (Ramón, 2026-10-27): opción A de `docs/notes/07-redcap_scaling.md`. Las variables del
paso 06 se recalculan a res 5 sumando las áreas de los hijos (D1) y REDCAP (orden completo, Ward)
corre sobre las 14.137 celdas. Primer borrador: k = 15, del orden de las 13 y 16 ecorregiones, con
mínimo de 4.388 km² (D5).

Por qué no res 6: REDCAP crece con una potencia cercana a 3 del número de celdas; extrapolado,
unas 4 horas por corrida y más memoria que los 8 GB de la Mac (no corrido). Una máquina en la nube
lo correría, pero el borrador necesita decenas de corridas y no hay presupuesto de Google Cloud
(Iván, 2026-10-19). A res 5 una corrida tarda entre 15 y 40 s (`workflow/07-regions.py`,
2026-10-27). La región mínima son ~18 celdas de res 5, así que res 6 no cambia la escala de las
regiones.

Si el mapa a res 5 resulta demasiado grueso: res 6 con Ward con contigüidad de scikit-learn
(opción B), sin tamaño mínimo, o REDCAP en la nube.

## D14 · Rate en logaritmo, celdas sin área quemable afuera, y dos piezas patagónicas forzadas · acordada (2026-10-27)

**Acordado** (Ramón, 2026-10-27), tres cambios al paso 07:

1. **Tasa y recurrencia en logaritmo** antes de estandarizar, como Segura-Garcia et al. 2025
   ("Methods", (c)(i)) con el área quemada y la frecuencia. La tasa por celda va de 1e-5 a 20 % por
   año; en escala lineal, la diferencia entre bosque y estepa en Patagonia (0,185 contra 0,050 %)
   valía 0,002 en las unidades del agrupamiento, y en logaritmo 0,223. El valor sumado antes del
   logaritmo (`LOG_RATE_OFFSET`, 0,001 %) es nuestro: con 0,01 o 0,0001, el 83 a 85 % del área queda
   en la misma región (k = 15).
2. **Celdas con menos de 10 % de área quemable fuera del agrupamiento** (`MIN_BURNABLE_SHARE`): 571
   celdas, 91.695 km². Después se suman a la región vecina más común. En el primer borrador formaban
   una región propia en el Río de la Plata (15,5 % quemable). Umbral nuestro.
3. **k = 12 más dos piezas del nivel k = 20 del mismo árbol** (`FORCED_SPLIT_*`, `--force`): oeste de
   Neuquén (9.698 km², 0,41 %/año) y oeste de Chubut (22.071 km², 0,34 %/año), dentro de una Patagonia
   que se quema 0,05 %/año. Las regiones están anidadas, así que cada pieza cae entera en una región.

Por qué las piezas y no la franja de bosque entera: el bosque andino-patagónico no tiene un régimen
único. Las celdas con ≥ 50 % de bosque se queman 0,29 a 0,30 %/año al norte de 43°S y 0,008 a
0,022 %/año al sur de 46°S. Al norte de 46°S, más de la mitad del área de bosque (15.834 km²) queda
fuera de las piezas, con una celda mediana de 0,005 %/año. Cortar por la cobertura juntaría celdas de
regímenes distintos y pondría un límite de vegetación en un mapa de fuego (principio 4 de Erni et
al. 2020). Las piezas tienen 24 a 35 % de bosque: son la transición bosque-estepa.

Costo: 0,532 de varianza explicada contra 0,537 del k = 14 sin forzar (medido con `ss_ratio`, que
no coincide con la cifra de pygeoda; ver la nota del paso).

## D15 · El Delta del Paraná como tercera pieza forzada · acordada (2026-10-27)

**Acordado** (Ramón, 2026-10-27, opción A). Ramón vio a ojo una franja de fuego sobre el Paraná,
entre Santa Fe, Entre Ríos y Buenos Aires, metida en la región del Espinal. Medido (revisión ad hoc,
sin script en el repo): las 174 celdas de esa región con el centro en la ecorregión Delta e Islas del
Paraná se queman 3,08 %/año, el resto de la región 1,10 %. El árbol de REDCAP la separa recién en
k = 25: una pieza de 84 celdas, 85 % en el Delta, entre 32,2 y 34°S.

1. **La pieza del nivel k = 25** se fuerza como las patagónicas (D14). Cada pieza toma ahora su
   propio nivel (`FORCED_SPLIT_POINTS` lleva el k). Resultado: 15.401 km², 4,32 %/año, la tasa más
   alta del mapa; el Espinal queda en 1,14 %/año. Mapa de 15 regiones, `ss_ratio` 0,536.
2. **Las celdas fuera del agrupamiento** (D14, punto 2) se reasignan sobre el mapa final, con las
   piezas ya puestas. Sin esto, una celda de agua en la desembocadura del Uruguay quedó separada del
   Espinal y falló el control de conexión. El cambio movió unas pocas celdas sin área quemable: los
   conteos de las regiones 1, 5, 6, 11 y 15 cambian en 1 o 2 celdas.

Opción descartada: toda la ecorregión Delta dentro del Espinal como región. Cubre el Paraná al norte
de Rosario, pero impone un límite de vegetación (principio 4 de Erni et al. 2020). El tramo al
norte de 32°S sigue en el Espinal hasta k = 30: queda como pregunta abierta, igual que la región
continua de bosque andino-patagónico norte (slide "A discutir" del taller).

