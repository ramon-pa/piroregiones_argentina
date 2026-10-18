# Antecedentes

Cada entrada dice **qué se leyó** y cuándo. Niveles:

- **completo**: leído el PDF entero.
- **parcial**: leídas las páginas indicadas del PDF.
- **resumen**: solo el resumen o la ficha del editor.
- **resumen automático**: resumen de la página generado por una herramienta, sin leer el PDF.
  No usar para citar sin releer.
- **citado vía**: solo se conoce por lo que dice otro paper.

Todo dato que va al manuscrito tiene que venir de un nivel **completo** o **parcial**, con página.

---

## Zonificación de regímenes de fuego (modelo metodológico)

### Boulanger, Gauthier & Burton 2014 · completo (2026-10-14)

*A refinement of models projecting future Canadian fire regimes using homogeneous fire regime zones.*
Can. J. For. Res. 44: 365–376. doi:10.1139/cjfr-2013-0372. Leídas las pp. 365–376; el material
suplementario (Fig. S1 a S4, Tabla S1) no.

- **Datos** (p. 366): base nacional de incendios de Canadá, 1959–2011, solo fuegos > 200 ha
  (los menores están incompletos, sobre todo antes de 1980 y en zonas remotas). Los fuegos > 200 ha
  suman el 97 % del área quemada en 1959–1997 (citan a Stocks et al. 2003). 14.955 fuegos. Cada
  fuego es un punto, representado como un círculo con el área informada.
- **Período de las zonas** (p. 366): 1959–1999. 2000–2010 como validación.
- **Unidad** (p. 366): grilla de 60 × 60 km; elegida porque es más grande que todos los fuegos salvo
  nueve (0,08 %).
- **Variables de fuego** (p. 366): número medio anual de fuegos > 200 ha (FireOcc) y área quemada
  media anual (AAB). Fuegos humanos y por rayo juntos. Ambas expresadas en función del área de
  combustible de la celda.
- **Combustible** (pp. 366 y 368): cobertura EOSD de 250 m. Área de combustible = píxeles de 6,25 ha
  con árboles, arbustos, pastos, herbáceas, briófitas o humedales vegetados. En el clustering entran
  además cinco variables de combustible: área de bosque conífero, mixto, caducifolio, humedales y
  resto no arbóreo.
- **Pesos** (p. 368): todo estandarizado a media 0 y desvío 1; combustible con peso 0,2, fuego con
  peso 1,0. Sumar combustible mejoró la predicción de los modelos clima-fuego (R² +3 a +6 %) y bajó
  levemente la homogeneidad de las zonas (R² ≈ −3 %).
- **Método** (pp. 366 y 368): clustering aglomerativo con restricción espacial y partición
  (Guo 2008), con REDCAP v2.0.1 (Guo 2011). Grafo de vecindad tipo torre (celdas que comparten borde).
  Criterio de Ward con restricción de contigüidad. El árbol se parte para minimizar la suma de
  cuadrados dentro de regiones contiguas.
- **Tamaño mínimo** (p. 368): 200.000 km², aproximadamente la ecozona más chica con actividad de
  fuego significativa (Pacific Maritime, ~208.000 km²).
- **Número de zonas** (p. 368): partición sucesiva desde 2 zonas hasta que el tamaño mínimo impide
  seguir. Para cada solución, 1000 validaciones cruzadas con `mvpart` 1.4.0 (R 2.13.1). Se elige la
  más parsimoniosa: la de menor variación del coeficiente de error (Segal & Xiao 2011).
- **Evaluación** (p. 368): R² ajustado de FireOcc y AAB (juntos) explicado por la zonificación,
  comparado con el de las ecozonas (cada celda asignada a la ecozona de su centroide).
- **Resultados** (p. 370): 16 zonas. R² ajustado 0,477 contra 0,190 de las ecozonas (1959–1999);
  0,317 contra 0,098 en la validación 2000–2010. Los límites casi nunca coinciden con los de las
  ecozonas, salvo en Montane Cordillera y Hudson Plains. Máximos en la zona Lake Athabasca:
  AAB 1,55 %/año y 15,4 fuegos por 100.000 km² por año.
- **Discusión útil** (p. 372): a escalas chicas la estimación del régimen es muy estocástica, porque
  uno o pocos eventos la mueven (citan a Metsaranta 2010); las zonas grandes dan estimaciones más
  estables. Las zonas son una foto del régimen reciente; límites estáticos suponen estabilidad
  temporal, y las zonas con poca actividad son las más sensibles a cambios.
- **Limitaciones** (p. 374): no consideran diferencias de manejo y supresión entre jurisdicciones.
- El resto del paper (modelos MARS y proyecciones 2011–2100) no es relevante para este proyecto.

Para nosotros: el precedente cuantitativo y reproducible del nivel de regiones (D5) y el precedente
de normalizar por área de combustible (D4). Su evaluación con R² ajustado contra ecozonas es la
plantilla para comparar con las ecorregiones argentinas.

### Erni, Wang, Taylor, Boulanger, Swystun, Flannigan & Parisien 2020 · completo, manuscrito (2026-10-14)

*Developing a two-level fire regime zonation system for Canada.* Can. J. For. Res. Leído el
**manuscrito aceptado** completo (ID cjfr-2019-0191.R1, enviado el 09-oct-2019, 41 páginas,
incluidos tablas A1 y A2 y figuras 1 a 4, A1 y A2). No leída la versión final de la revista.
Volumen 50(3) de 2020 según un registro bibliográfico **[no verificado contra la revista]**.
Páginas citadas abajo = páginas del manuscrito.

- **Datos** (p. 6): base nacional de incendios de Canadá, 1970–2016, temporada 1 abr–30 sep,
  fuegos ≥ 50 ha. 20.372 fuegos; 23,5 % de causa humana y 76,5 % por rayo. Área quemable del
  estudio: 519,4 Mha (p. 5).
- **Nivel 1, 60 unidades (FRU)** (pp. 8–10 y 12; Fig. 1 y 3): delimitadas a mano por peso de
  evidencia, al estilo de las ecorregiones de Omernik, en tres pasos (nacional, regional, local), con
  revisión de expertos. Variables (p. 8): tamaño de fuego, frecuencia (fuegos por año por Mha), tasa
  de quema (% del área por año), causa de ignición y estacionalidad (quincenas de la temporada), con
  media, mediana y p95. Superficies entre 40,24 y 0,4 Mha (p. 12). Valores por unidad en la Tabla A1
  (pp. 36–38).
- **Principios para trazar límites** (p. 8):
  1. Las métricas de fuego son el criterio principal.
  2. Una unidad cubre al menos el doble del fuego más grande registrado en la región desde 1970
     (citan a O'Neill et al. 1996).
  3. Una unidad es distinta si difiere claramente en al menos un parámetro principal; el ambiente
     tiene que corroborar el límite.
  4. Una variación ambiental sin variación concomitante del régimen no es límite: el mismo tipo de
     combustible puede estar en dos unidades vecinas.
- **Nivel 2, 15 tipos (FRT)** (p. 11; Fig. 4; Tabla A2): Ward **sin** restricción de contigüidad
  (`hclust` en R) sobre cinco métricas por unidad (frecuencia, tamaño, tasa de quema, causa,
  estacionalidad); la mediana de cada métrica se calcula por año y se promedia. Dos análisis
  separados: 22 unidades de montaña y 38 del resto. Número de tipos por método del codo y lectura del
  dendrograma. Cada tipo recibe un código: actividad (FA1 a FA5, suma de tamaño, frecuencia y tasa
  clasificadas contra la mediana nacional), estación dominante (más de 65 % del área en primavera o
  en verano; si no, mixta) y causa dominante (mismo umbral de 65 %) (pp. 11–12).
- **Limitaciones** (p. 17): faltan severidad, intensidad y tipo de fuego; el período es más corto
  que el intervalo de retorno en casi todo el área; las praderas quedaron afuera por falta de
  monitoreo de fuegos de pastizal; suponen que 1970–2016 representa el régimen actual.
- **Fig. A2** (p. 41): mapas de los polígonos de fuego sobre ecozonas, zonas HFR y tipos FRT. Es
  visual; no trae un número de comparación.

Para nosotros: la distinción región (continua) y tipo (no continua), los cuatro principios para
trazar límites (D5) y la forma de codificar los tipos con umbrales legibles.

### Boulanger, Gauthier, Burton & Vaillancourt 2012 · citado vía Boulanger et al. 2014

*An alternative fire regime zonation for Canada.* Int. J. Wildland Fire 21: 1052–1064.
doi:10.1071/WF11073. Según Boulanger et al. 2014 (p. 368): 33 zonas para 1980–1999, con fuegos chicos
y grandes, a escala más fina y sin vegetación.

---

## Pirorregiones y pyromes

### Naval-Fernández, Elia, Giannico, Bellis, Bravo & Argañaraz 2025 · completo (2026-10-14)

*The Pyrogeography of the Gran Chaco's Dry Forest: A Comparison of Clustering Algorithms and the
Scale of Analysis.* Forests 16: 1114. doi:10.3390/f16071114. Leídas las 20 páginas.

- Área (p. 3): Chaco Seco argentino, 675.000 km².
- Datos (pp. 4–7): MODIS MCD64A1 (área quemada, 500 m), FIRED (perímetros de eventos) y MCD14ML
  (focos, FRP), 2001–2021, procesados en GEE.
- Unidades (p. 6): celdas cuadradas de 5 × 5 km (25.846), 10 × 10 km (6.741) y 25 × 25 km (1.132).
- Métricas (pp. 6–7): área quemada anual media; variabilidad interanual (CV del área quemada anual);
  intensidad (p95 de FRP, focos de vegetación con confianza ≥ 60 %); tamaño (p80 a 5 km, p95 a 10 y
  25 km); índice de concentración estacional. Mínimo de 10 registros por celda para tamaño e
  intensidad (5 para tamaño a 5 km).
- Métodos (p. 7): Box-Cox, z-score; K-means (`stats`) y GMM (`mclust`); validación interna con BIC,
  Connectivity y Dunn. Sin restricción de contigüidad.
- Resultados (pp. 8–10, Tabla 1): Connectivity y Dunn eligen la escala de 25 km para ambos
  algoritmos. GMM a 25 km elige 6 grupos por BIC. Para K-means, Connectivity elige 2 grupos en todas las escalas y Dunn entre 9 y 10; los autores lo
  descartan por razones ecológicas y de agregación espacial aunque sus índices eran mejores. A 5 y
  10 km queda sin datos suficientes el 52 % y el 40 % del Chaco, contra el 21 % a 25 km (p. 9).
- Las seis pirorregiones (pp. 10–13): LRM 22 %, ROI 19 %, ROM 14 %, LOM 10 %, ROL 9 %, HFL 4 %, más
  una región "indeterminada" del 21 % (celdas sin datos suficientes, sobre todo en el Chaco Árido y
  Semiárido). HFL tiene el mayor área quemada anual (9480 ha) y está en humedales no forestales.
- Apéndice A (p. 16): PAM a 5 km da un patrón de "sal y pimienta".
- Limitaciones (p. 14): falta severidad; la resolución de MODIS limita la detección de fuegos chicos.

Para nosotros: el antecedente argentino directo. Muestra dos problemas que el diseño propuesto
ataca: celdas sin datos por la resolución de MODIS (a 30 m debería haber menos) y grupos dispersos
sin contigüidad.

### Neger, Toledo-Jaime, Galicia & Romero-Cuapio 2025 · parcial (2026-10-14)

*Pyrogeographic zonation: Implications for fire management at the local level.* PLoS One 20(8):
e0328233. doi:10.1371/journal.pone.0328233. Leídas las pp. 1–8 de 18 (introducción, Tabla 1,
métodos, comienzo de resultados).

- Reserva La Sepultura, Chiapas, 1673 km² (p. 3). Grilla de 5 × 5 km, unas cinco veces el fuego más
  grande de 2010–2020 (5,5 km²) (p. 5). 101 celdas (p. 7).
- Ward con ClustGeo (p. 6). Probaron sin restricción, con contigüidad estricta y con contigüidad
  suave (α = 0,2 y 0,3) (p. 7). Con contigüidad las regiones quedaron muy heterogéneas por dentro;
  el resultado final no impone contigüidad (p. 7).
- Tabla 1 (p. 3): resumen de antecedentes. Incluye Moreno & Chuvieco (2013, España, 10 × 10 km,
  k-means, 4 grupos), Boulanger et al. (**2013**, este de Canadá, 60 × 60 km, Random Forests),
  Conedera et al. (2018, Alpes, NUTS3), Elia et al. (2022, Italia, NUTS3, affinity propagation, 7),
  Resco de Dios et al. (2023, ecorregiones, k-means), Galizia et al. (2023, Europa, 50 × 50 km, 5) y
  Cunningham et al. (2024, Australia, unidades delimitadas con mezcla de gaussianas, Random Forests, 17 grupos).

Nota: Naval-Fernández et al. citan Moreno & Chuvieco como 2012, Int. J. Wildland Fire 22: 296–305;
Neger et al. lo fechan en 2013. Verificar el año antes de citar.

### Galizia, Barbero, Rodrigues, Ruffault, Pimont & Curt 2023 · parcial (2026-10-14)

*Global warming reshapes European pyroregions.* Earth's Future 11, e2022EF003182.
doi:10.1029/2022EF003182. Leída la versión HAL, pp. 1–5 de 14 (hasta el comienzo de resultados).

- Datos (p. 2): GlobFire (de MCD64A1, 500 m) y FRP de MCD14ML, 2001–2018. Excluyen tierras
  artificiales (agricultura y urbano) con Corine (p. 2), y celdas con más de 80 % de cobertura no
  quemable (p. 3).
- Grilla de 50 km, 1663 celdas (p. 3). Seis componentes del régimen: área quemada, número de
  fuegos, % de fuegos grandes (> 100 ha), % de fuegos en la estación fría, duración del período de
  fuego e intensidad (p. 3).
- Las pirorregiones se delimitan con K-means difuso sobre los componentes **simulados** por modelos
  GAM, no sobre los observados; número de grupos con NbClust (30 índices) (p. 4).

### Archibald, Lehmann, Gómez-Dans & Bradstock 2013 · resumen automático

*Defining pyromes and global syndromes of fire regimes.* PNAS 110(16): 6442–6447. No se pudo bajar
el PDF (descarga bloqueada en PMC, Europe PMC y ResearchGate). Según el resumen automático de PMC:
celdas de 0,5°, 1997–2010, cinco variables (área quemada anual, CV del área quemada como proxy del
intervalo, p95 de FRP, duración de la temporada y p95 del tamaño de fuego), clustering por mezcla de
gaussianas con `mclust`, cinco pyromes (FIL, FCS, RIL, RCS, ICS). **Releer el PDF antes de citar.**

---

## Argentina

### Ferro, Barberá, Foguet, Kitzberger & Aráoz 2026 · resumen

*Why are you burning? The interplay between land cover, climatic variability and fire activity in the
dry forests of Argentina.* Int. J. Wildland Fire 35(3), WF25126. doi:10.1071/WF25126. Ficha del
editor leída con una herramienta automática. Chaco Seco 2000–2023: los bosques perdieron ~17 % del
área; la actividad de fuego baja; pastizales, pasturas y agricultura tienen la mayor probabilidad de
quema; en tierras manejadas el fuego se desacopla del clima. Según el resumen automático: fuego con
MCD64A1 (500 m) y cobertura MapBiomas Chaco colección 4 llevada a 500 m. **Releer antes de citar.**

### Cavallero, Peinetti & López 2023 · citado vía Naval-Fernández et al. 2025

*Incidencia de fuegos en la Argentina durante las últimas dos décadas y su asociación con coberturas
y usos del suelo en distintos contextos ambientales.* Ecol. Austral 33: 773–797 (referencia 37 de
Naval-Fernández et al.). Las cifras que aparecieron antes en la búsqueda (47,84 Mha) **no están
verificadas**.

### Argañaraz, Pizarro, Zak & Bellis 2015 · citado vía Naval-Fernández et al. 2025

*Fire regime, climate, and vegetation in the Sierras de Córdoba, Argentina.* Fire Ecol. 11: 55–73
(referencia 34 de Naval-Fernández et al.).

### Oyarzabal et al. 2018 · citado vía Naval-Fernández et al. 2025

*Unidades de vegetación de la Argentina.* Ecol. Austral 28: 40–63 (referencia 32 de Naval-Fernández
et al.). Referencia verificada; el contenido no se leyó.

### Burkart, Bárbaro, Sánchez & Gómez 1999 · referencia en bibliografías secundarias

*Eco-regiones de la Argentina.* Administración de Parques Nacionales y Secretaría de Recursos
Naturales y Desarrollo Sustentable, Buenos Aires. Autores, año y editor coinciden en dos
bibliografías encontradas; el documento original no se vio. Las fuentes secundarias hablan de 15
ecorregiones continentales. **La capa digital ya está en GEE** (versiones de 16 y 13 clases, ver
`CLAUDE.md`, "GEE asset paths"); la atribución a Burkart et al. viene de `statistics.md` del repo de
fuego. Falta el documento original para la cita.

---

## Grillas

### Birch, Oom & Beecham 2007 · resumen

*Rectangular and hexagonal grids used for observation, experiment and simulation in ecology.*
Ecol. Model. 206: 347–359. doi:10.1016/j.ecolmodel.2007.03.041. Las grillas hexagonales tienen
relaciones de vecindad más simples y menos ambiguas.

---

## Herramientas (verificadas instalándolas, 2026-10-14)

Instaladas en un entorno descartable con `uv`; se leyeron las firmas y la documentación interna.
No se corrió ningún análisis con ellas.

| Paquete | Versión | Qué ofrece | Relevancia |
|---|---|---|---|
| `pygeoda` | 0.1.3 | `redcap` con variantes primer orden y orden completo; enlace simple, completo, promedio y **Ward**; parámetros `bound_variable` y `min_bound` (suma mínima de una variable por región) | reproduce el método de Boulanger et al. 2014 (REDCAP, Ward) y permite imponer un tamaño mínimo de región. También trae `skater`, `schc`, `maxp_greedy`, `azp_greedy` |
| `spopt` | 0.8.0 | `WardSpatial` (Ward con restricción de conectividad), `Skater` (con `floor`), `MaxPHeuristic` (con umbral mínimo sobre una variable extensiva), `AZP`, `RegionKMeansHeuristic`, `SA3`, `Spenc` | alternativas en el ecosistema PySAL |

Guo 2008, el paper de REDCAP: *Regionalization with dynamically constrained agglomerative clustering
and partitioning (REDCAP).* Int. J. Geogr. Inf. Sci. 22: 801–823. doi:10.1080/13658810701674970
(referencia tomada de la bibliografía de Boulanger et al. 2014). El paper no se leyó: la descarga fue
bloqueada.

---

## Pendientes de lectura

| Referencia | Por qué | Estado |
|---|---|---|
| Burkart et al. 1999, documento | base de la comparación | capa en GEE; referencia verificada en fuentes secundarias; falta el original |
| Oyarzabal et al. 2018, contenido | base de la comparación | referencia verificada; sin leer |
| Guo 2008, REDCAP | método de Boulanger et al. 2014 | sin leer (descarga bloqueada) |
| Archibald et al. 2013, PDF | definición de variables | solo resumen automático |
| Ferro et al. 2026, PDF | fuego y cobertura en el Chaco | solo resumen automático |
| Cavallero et al. 2023 | único análisis nacional | sin leer |
| Neger et al. 2025, pp. 9–18 | resultados y discusión | sin leer |
| Galizia et al. 2023, pp. 6–14 | resultados | sin leer |
| Moreno & Chuvieco, año | discrepancia 2012 o 2013 | sin verificar |
