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
  (~669 mil celdas) no entra en el código empaquetado de 32 bits y obliga a subir ~669 mil polígonos.
- **Por qué no es una decisión de cómputo.** Medido: el tamaño de celda no cambia el costo de la
  reducción; lo que cuesta es recorrer los píxeles (`docs/notes/01-grid_and_compute.md`).

## D2 · Período · abierta

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

## D6 · Un solo barrido por año · propuesta (2026-10-17)

Cobertura disponible y quemado salen de **una sola reducción por año**, con un código empaquetado
`celda × 13.000 + clase(Y−1) × 130 + mes (0 = no quemado) × 10 + clase de tamaño`. Sumando todas las
filas de una celda y clase sale el área disponible; sumando las de mes > 0, el área quemada.

Por qué: la cobertura del año previo se lee una vez por año en vez de dos, y numerador y denominador
salen de la misma lectura a 30 m. El código entra en un entero de 32 bits hasta res 6 (~1.256
millones con 96.643 celdas, sobre un máximo de 2.147 millones). Una tarea por año, para acotar la
memoria del reductor agrupado.

Descartado: leer la cobertura a menor resolución. Ahorra ~2 a 3 veces el tiempo, pero las pirámides
por moda subestiman hasta 26 % la clase Pasturas a 240 m (`docs/notes/01-grid_and_compute.md`).

Pendiente: probarlo en el recuadro de Córdoba (tiempo, filas, y que cierre contra los dos resúmenes
por separado). La frecuencia (paso 04) queda aparte: necesita los 27 años de cada píxel juntos.
