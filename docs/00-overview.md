# 00 · El método en una página

Este proyecto convierte 27 años de área quemada a 30 m en un mapa de pirorregiones: zonas continuas
del país donde el fuego se comporta parecido. La cadena tiene cuatro etapas: un **cruce** por píxel
en Earth Engine, una **agregación** a celdas, una **regionalización** y una **comparación** con las
ecorregiones. Este doc fija ese encuadre una vez; cada doc de paso lo da por sabido.

## Las cuatro etapas

**Cruce (GEE, 30 m).** Cada píxel quemado en el año Y recibe la cobertura del año Y−1 y su mes de
quema. Se usa Y−1 porque la cobertura del año del fuego puede ser ya consecuencia del fuego; es la
regla de todo el trabajo del equipo de MapBiomas Fuego. Fuego y cobertura están en la misma grilla,
así que el cruce no remuestrea nada (`CLAUDE.md`, "GEE asset paths").

**Agregación (GEE → local).** El régimen de fuego es una propiedad de una zona, no de un píxel. De
GEE se extraen solo **áreas** por celda: área disponible de cada cobertura, área quemada por año,
mes, cobertura y tamaño de cicatriz, y área quemada 1, 2, 3 o más veces. Como las áreas se suman,
una extracción a la resolución más fina sirve para armar localmente las más gruesas.

**Regionalización (local).** Con las áreas se calculan las variables del régimen: tasa de quema
por cobertura, frecuencia, variabilidad entre años, estacionalidad y tamaño de fuego. Las celdas
vecinas con régimen parecido se agrupan en regiones continuas con un tamaño mínimo, con el método
de Boulanger et al. 2014 (REDCAP, Ward).

**Comparación (local).** Cuánta variación del fuego explica el mapa de pirorregiones frente al de
ecorregiones de Burkart et al. 1999, y dónde los límites coinciden o se separan.

## Pasos

| Paso | Hace | Doc |
|---|---|---|
| 00 | chequeo de solo lectura de todos los insumos de GEE | `scripts/check_assets.py` (docstring) |
| 01 | grilla de celdas sobre Argentina | pendiente |
| 02 | área disponible por cobertura, por celda y año | pendiente |
| 03 | área quemada por celda × año × mes × cobertura × tamaño | pendiente |
| 04 | frecuencia de quema por celda | pendiente |
| 05 | tabla única por celda, con controles | pendiente |
| 06 | variables del régimen | pendiente |
| 07 | pirorregiones | pendiente |
| 08 | tipos de régimen (opcional) | pendiente |
| 09 | comparación con ecorregiones | pendiente |
| 10 | figuras y fichas | pendiente |

Las decisiones abiertas que afectan a varios pasos (tipo y tamaño de celda, período, niveles) están
en [`decisions.md`](decisions.md) hasta que cada una tenga su paso.
