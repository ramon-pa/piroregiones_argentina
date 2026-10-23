# Antecedentes

Cada entrada dice **qué se leyó** y cuándo. Niveles:

- **completo**: leído el PDF entero.
- **parcial**: leídas las páginas indicadas del PDF.
- **resumen**: solo el resumen o la ficha del editor.
- **resumen automático**: resumen de la página generado por una herramienta, sin leer el PDF.
  No usar para citar sin releer.
- **citado vía**: solo se conoce por lo que dice otro paper.

Todo dato que va al manuscrito tiene que venir de un nivel **completo** o **parcial**, con página.

Copias locales en `papers/` (fuera de git, por derechos de autor), con nombre `autor_año`. El 2026-10-23:
Boulanger 2014, Cattau 2022, Pais 2023, San Martín 2026 y Vidal-Riveros 2024 en PDF; Segura-Garcia
2025 como HTML de PMC (el PDF no se pudo bajar).

---

## Zonificación de regímenes de fuego (modelo metodológico)

### Boulanger, Gauthier & Burton 2014 · completo (2026-10-14)

*A refinement of models projecting future Canadian fire regimes using homogeneous fire regime zones.*
Can. J. For. Res. 44: 365–376. doi:10.1139/cjfr-2013-0372. Leídas las pp. 365–376; el material
suplementario (Fig. S1 a S4, Tabla S1) no. Copia local: `papers/boulanger_2014.pdf`
(13 páginas; resumen con 16 zonas y 47,7 %, igual a esta ficha; comprobado el 2026-10-23). Copia en
línea de la cátedra AFD de UQAT:
`https://chaireafd.uqat.ca/publication/articlePDF/CanJForRes2014_44(4)_%20365-376.pdf` (no respondió
el 2026-10-23).

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

### Segura-Garcia, Alencar, Arruda, Bauman, Silva, Conciani & Oliveras Menor 2025 · parcial (2026-10-23)

*The fire regimes of the Cerrado and their changes through time.* Phil. Trans. R. Soc. B 380:
20230460. doi:10.1098/rstb.2023.0460. Leída la versión HTML de PMC (PMC12004096), sin páginas:
completos el resumen, "Introduction", "Methods", "Discussion" (párrafos sobre actividad de fuego y
ecorregiones) y "Conclusion"; de "Results" solo el comienzo de la sección (a). Material
suplementario (figshare, doi:10.6084/m9.figshare.c.7756897) no.

- **Autores.** Alencar, Arruda, Silva y Conciani son autores del producto MapBiomas Fogo (Alencar et
  al. 2022, referencia 41 del paper). Agradecen al equipo científico de IPAM ("Acknowledgements").
  Es probable que este sea parte del trabajo de la red que mencionó Iván el 17-oct; **no
  confirmado**, preguntarle.
- **Datos** ("Methods", (b)(i) y (ii)): MapBiomas Fogo colección 2.0 (Landsat, 30 m, mensual,
  1985 a 2022) y cobertura MapBiomas colección 8.0, bajados de GEE con el toolkit de MapBiomas.
- **Polígonos de fuego** ((b)(i)): píxeles contiguos de meses consecutivos más polígonos separados
  hasta 150 m de borde a borde = un mismo evento. Se quedan con los de más de 3 ha. Razón: sin la
  regla de los 150 m salían demasiados fuegos chicos respecto de la distribución de cola pesada
  esperada.
- **Unidad** ("Methods", (a)): grilla de 30 × 30 km, elegida para limitar los polígonos más grandes
  que una celda y las celdas casi sin fuego. Cuatro períodos de 9 años (1985 a 1993, 1994 a 2002,
  2003 a 2011, 2012 a 2020), cada uno con su propia regionalización.
- **Seis variables** ((b)(i)): número de fuegos por área quemable; mediana y p99 del tamaño de los
  polígonos; área quemada por área quemable; frecuencia (p99 de la ECDF suavizada de las veces que
  se quemó cada píxel, 0 a 9); pico de la temporada (mediana de la ECDF del área quemada mensual en
  un año de fuego centrado en el mes de mayor quema de cada celda).
- **Área quemable** ((b)(ii)): todas las clases salvo planicies hipersalinas, afloramientos
  rocosos, áreas no vegetadas y agua. Incluye la agricultura.
- **Celdas sin fuego** ((b)(i)): les asignan tamaño mínimo de 3 ha, frecuencia y número de 1, y el
  pico promedio de sus 8 vecinas.
- **Método** ((c)(i)): logaritmo de tamaños, área, número y frecuencia; PCA sobre las variables
  estandarizadas; clustering sobre los 3 primeros ejes (más del 95 % de la varianza). Clustering
  jerárquico **con restricción de contigüidad** (`constr.hclust` del paquete R `adespatial`, Guénard
  & Legendre 2022). Número de regiones por BIC, mirando también Dunn y silueta.
- **Resultados** ("Results", (a); "Discussion"): 5 regiones en 1985 a 1993 y 3 en cada uno de los
  otros períodos. Lo que más separa las regiones es el nivel de actividad de fuego (PC1: área,
  frecuencia, fuego más grande y número juntos). Hay un compromiso entre tamaño y número de fuegos.
  Una región norte se distingue por el pico tardío de la temporada.
- **Comparación con ecorregiones** ("Discussion"): **solo cualitativa**, sin un número. Ni la
  cantidad ni la forma de las ecorregiones coinciden con las regiones de fuego; hay coincidencias
  parciales (Bananal, Chapadão do São Francisco) y un desacuerdo marcado (Paraná Guimarães).
- **Conclusión** ("Conclusion"): la actividad de fuego baja donde avanza la ocupación humana
  moderna (agricultura mecanizada, fragmentación); piden estudiar escalas más finas.

Para nosotros: **el antecedente más parecido**, más que Boulanger et al. 2014. Mismo tipo de
insumo (MapBiomas a 30 m, fuego mensual más cobertura, GEE), regiones continuas por clustering con
restricción de contigüidad, grilla de unos 30 km y la pregunta frente a las ecorregiones. Lo que
nosotros agregamos: Argentina; cobertura del año previo (en el paper la cobertura es promedio del
período); comparación cuantitativa con las ecorregiones (al estilo de Boulanger); y celdas de área
parecida y vecindad sin ambigüedad (H3). Diferencias a pensar: ellos usan polígonos de evento y
nosotros clases de tamaño de cicatriz (D6); ellos regionalizan por períodos de 9 años.

### Cattau, Mahood, Balch & Wessman 2022 · parcial (2026-10-23)

*Modern pyromes: biogeographical patterns of fire characteristics across the contiguous United
States.* Fire 5: 95. doi:10.3390/fire5040095. Leídos el resumen y "Materials and Methods"
(pp. 2–6); de "Results" y "Discussion" solo los párrafos sobre ecorregiones.

- Datos (pp. 2–3): focos MODIS (2003 a 2020), MTBS (perímetros Landsat de fuegos grandes, 1984 a
  2020) y FPA-FOD (registros oficiales, 1992 a 2018). Grilla de 50 km, elegida por ser del tamaño de
  un condado y para reducir el efecto del ángulo de visión de MODIS (p. 3).
- 15 variables por celda y año (Tabla 1, p. 4): frecuencia, FRP media y máxima, tamaño medio y
  máximo, área quemada, duración de la temporada (2 desvíos del día juliano). La causa de ignición
  queda afuera del clustering por no ser una característica física (p. 4).
- Método (pp. 4–5): PCA para elegir variables; k-means con k de 2 a 150; tope por BIC y niveles
  por máximos locales del índice de Dunn. Sin restricción de contigüidad. Reportan k = 8.
- Comparación con ecorregiones (pp. 5–6 y "Results"): porcentaje de cada pyrome en cada ecorregión
  EPA nivel 1. Ninguno salvo el pyrome 7 tiene más del 63 % de su área en una sola ecorregión; lo
  leen como desajuste entre pyromes y ecorregiones.

Para nosotros: otra forma simple de comparar con las ecorregiones (porcentaje de cada región en
cada ecorregión), complementaria del R² de Boulanger.

### Pais, Gonzalez-Olabarria, Elimbi Moudio, Garcia-Gonzalo, González & Shen 2023 · parcial (2026-10-23)

*Global scale coupling of pyromes and fire regimes.* Commun. Earth Environ. 4: 267.
doi:10.1038/s43247-023-00881-8. Leídos el resumen y "Methods" completos (HTML de la revista, sin
páginas); de "Results and discussion" solo la comparación con Archibald et al. 2013.

- Datos ("Methods", "Data description"): fuegos individuales de Global Fire Atlas y GlobFire (de
  MCD64A1, 500 m), 2000 a 2018, unidos para reducir la fragmentación de eventos. Grilla de 1°
  (probaron de 0,05° a 1,5°; más grueso que 1° daba resultados inestables).
- Citan para MCD64A1, frente a Landsat 8 a 30 m, comisión de 40,2 % y omisión de 72,6 %, peor en
  bosques tropicales, templados y mediterráneos.
- Variables: frecuencia, tamaño, perímetro, duración, expansión diaria y perímetro/área. Sin FRP.
- Método ("Clustering analysis"): varios algoritmos (DBSCAN, OPTICS, k-means, mapas
  autoorganizados, con PCA y t-SNE); k-means como principal. Convergen en 15 pyromes, subdivididos en
  62 regímenes por densidad espacial. Sin restricción de contigüidad; suavizan con un kernel
  gaussiano. Código: `github.com/humnetlab/Vulcano`.

Para nosotros: escala global, poco aplicable al método. Útil la cifra de omisión de MCD64A1 para
justificar 30 m, **pero es de segunda mano** (su referencia 69): leer la fuente antes de citarla.

### Vidal-Riveros, Watler Reyes, Ngo Bieng & Souza-Alonso 2024 · completo (2026-10-23)

*Assessing fire regimes in the Paraguayan Chaco: implications for ecological and fire management.*
Fire 7: 347. doi:10.3390/fire7100347. Leídas las 10 páginas; material suplementario (SM1, SM2) no.

- Área (p. 2): Chaco paraguayo, 230.000 km² (Chaco Seco, Chaco Húmedo y Pantanal).
- Datos (pp. 3–4): MCD64A1 (500 m) para frecuencia y área quemada; MOSEV (dNBR de MODIS, 2000 a
  2020) para severidad. El período de MCD64A1 no se dice explícitamente.
- Variables (p. 4): frecuencia (veces quemado por año), área quemada en una ventana circular de
  7 × 7 píxeles y dNBR medio 2001 a 2020.
- Método (pp. 4–5): z-score y k-means **por píxel**, sin celdas ni contigüidad. k por el codo y por
  lectura ecológica de diagramas de caja.
- Resultados (pp. 5–6): 4 regímenes (alto, moderado alto, moderado bajo, bajo); bajo 45,76 %,
  moderado alto 28,96 %, alto 5,98 %.

Para nosotros: completa el Chaco del lado paraguayo. Metodológicamente débil (píxel a píxel, sin
regiones). De su bibliografía salen tres pistas: García et al. 2022, Galizia et al. 2021 y San
Martín et al. 2023 (ver "Pendientes de lectura").

### Jasso-Flores & Corona-Núñez 2026 · resumen (2026-10-23)

*Pyro-socioecological zoning: A proposal for fire management in the tropical dry forest.* Global
Environmental Change (mayo de 2026), doi:10.1016/j.gloenvcha.2026.103135. Resumen leído de OpenAlex;
ScienceDirect bloqueó el texto (es de acceso abierto híbrido). Bosque tropical seco de **México**.
Definen 8 zonas con 91 variables de **causas** (combustible, terreno, clima, humanas) y un conjunto
de 10 métodos de clustering (confianza del 81 %), y después evalúan cada zona contra severidad,
extensión y frecuencia del fuego.

Para nosotros: el camino inverso al nuestro (zonas por causas, validadas con el fuego). Sirve de
contraste en la discusión.

### Simon & Dantas 2025 · resumen automático

*Fire as an evolutionary driver in South America.* En *Fire in the South American Ecosystems*,
serie Ecological Studies, Springer. doi:10.1007/978-3-031-89372-8_2. Acceso cerrado; solo se vio el
resumen de un buscador: agruparía 115 ecorregiones sudamericanas en pyromes. **No verificado**:
leer antes de citar.

### Cappelluti et al. 2025 · resumen (2026-10-23)

*A tridimensional framework for governance in the wildland-urban interface using
Pyro-Socio-Ecological Zones.* Nat. Commun. 16: 11232. doi:10.1038/s41467-025-66452-x. Zonas de
interfaz urbano-forestal en el sur de Italia y de California con indicadores ecológicos,
socioeconómicos y de gobernanza. **Fuera de tema**: se anota solo para no volver a buscarlo.

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

### San Martín, Ottlé, Sörensson, Vaittinada Ayar, Mouillot & Malfante 2026 · parcial (2026-10-23)

*What controls fire size in the South American Gran Chaco? Exploring atmospheric and landscape
drivers through remote sensing.* Nat. Hazards Earth Syst. Sci. 26: 1479–1513.
doi:10.5194/nhess-26-1479-2026. Leídos el resumen, la parte de "Introduction" sobre
clasificaciones de régimen, "Fire patches" y "Fire size classification".

- **No es una regionalización**: estudia qué controla el tamaño final del fuego en el Gran Chaco
  (Chaco Húmedo, Seco y Muy Seco), 2001 a 2022, con más de 100.000 parches.
- Datos ("Fire patches"): FRYv2.0 sobre FireCCI51 (250 m), elegido sobre la versión MCD64A1 por
  resolución. Rasgos de parche solo con 5 o más píxeles (~0,3 km²).
- Clases de tamaño ("Fire size classification"): la tipología de Linley et al. 2022 (megafuego más
  de 100 km², gigafuego más de 1000 km²) más cuatro clases chicas: menos de 1, 1 a 5, 5 a 10 y 10 a
  100 km².
- Resultados (resumen): más del 80 % de los fuegos mide menos de 5 km², pero los grandes dominan el
  área quemada. Hay megafuegos en las tres subregiones y gigafuegos sobre todo en el Chaco Seco.
  Topografía y cobertura suman ~60 % de la importancia SHAP de los modelos; las variables
  demográficas, muy poca.
- Critica a Vidal-Riveros et al. 2024 y Naval-Fernández et al. 2025 por no incluir meteorología
  ("Introduction").

Para nosotros: argumento para la discusión (el tiempo meteorológico no entra en nuestras regiones)
y una tipología de tamaños con fuente, para comparar con las clases 1 a 8 del producto (D6).

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
| Segura-Garcia et al. 2025, "Results" (b) y (c) y suplemento | el antecedente más parecido; ver ecorregiones (Fig. S10) y el criterio BIC (Fig. S1) | parcial |
| Guénard & Legendre 2022, *J. Stat. Softw.* 103: 1–22, doi:10.18637/jss.v103.i07 | `constr.hclust`, el método de Segura-Garcia et al. | sin leer |
| Silva Arruda et al. 2024, *Fire Ecol.* 20: 64 | cuatro décadas de fuego en el Cerrado con MapBiomas (equipo de MapBiomas Fogo) | citado vía Segura-Garcia et al. |
| Silva et al. 2021, *J. Environ. Manag.* 296: 113098 | régimen de fuego por ecorregión en el Cerrado | citado vía Segura-Garcia et al. y Vidal-Riveros et al. |
| García et al. 2022, *Forests* 13: 699 | regímenes de fuego globales desde satélite | citado vía Vidal-Riveros et al. |
| Galizia et al. 2021, *Int. J. Wildland Fire* 31: 56–66 | regímenes de fuego en Europa | citado vía Vidal-Riveros et al. |
| San Martín et al. 2023, *Fire Ecol.* 19: 57 | fuego en el Chaco: la respuesta al clima depende de la cobertura | citado vía Vidal-Riveros et al. |
| Linley et al. 2022, *Global Ecol. Biogeogr.* 31: 1906–1922, doi:10.1111/geb.13499 | tipología de tamaños de fuego | citado vía San Martín et al. 2026 |
| Simon & Dantas 2025 | pyromes de ecorregiones sudamericanas | acceso cerrado; solo resumen automático |
