# Decisiones de diseño

Cada decisión lleva su estado (**abierta**, **acordada**, **descartada**) y su fundamento.
Una decisión acordada se cambia solo agregando una entrada nueva que la reemplace, nunca borrándola.

---

## D1 · Unidad de análisis · abierta

**Propuesta.** Calcular a 30 m en la grilla nativa de MapBiomas y regionalizar sobre celdas gruesas.

- Para calcular, la grilla nativa: fuego col-1 y cobertura col-3 comparten la misma red de píxeles
  (`CLAUDE.md`, "GEE asset paths"), así que cruzarlos no requiere remuestrear.
- Para regionalizar, celdas de entre 10 y 25 km. En los antecedentes con grilla que leímos, las
  celdas van de 5 km (Naval-Fernández et al. 2025 probó 5, 10 y 25 km) a 60 km (Boulanger et al. 2014).
- Cuadrados alineados a la grilla o hexágonos H3: sin decidir. Iván recomienda hexágonos
  (15-oct-2026): es lo que se usa para regionalizaciones de este tipo. Los cuadrados evitan subir
  geometrías a GEE. Los hexágonos dan vecinos sin ambigüedad (Birch et al. 2007, resumen) y bordes
  más suaves. Ninguno elimina el efecto borde del país ni de la costa.
- Toda área se suma con `pixelArea()`: el píxel nativo no es de área constante (`CLAUDE.md`,
  "Key verified numbers", exploratorio).
- Los cruces de fuego y cobertura se calculan desde la colección mensual `fire_mask_v2` y la LULC
  col-3, que están en la grilla nativa. Los subproductos `_v2` derivados (`annual_burned_coverage`,
  `frequency_burned`, etc.) están guardados en EPSG:3857 y no se usan (`CLAUDE.md`, "GEE asset paths").

Pendiente: prueba en GEE de si la agregación entra sin tareas de exportación.

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
