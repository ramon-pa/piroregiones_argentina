# 07 · REDCAP a res 6: cuánto cuesta (2026-10-26)

Cuaderno de laboratorio. Script: `scripts/bench_redcap.py` (entorno descartable con `pygeoda`).

## Pregunta

¿Se puede correr REDCAP de orden completo con Ward (el método de Boulanger et al. 2014) sobre las
96.461 celdas de res 6 en esta Mac?

## Medido

N celdas contiguas de res 6 alrededor de (−61, −30), las 7 variables de fuego estandarizadas, k = 10:

| Celdas | Tiempo | Memoria máxima |
|---|---|---|
| 2.000 | 0,2 a 0,3 s | |
| 8.000 | 4,1 a 4,5 s | |
| 24.000 | 158 s | 2,5 GB (`/usr/bin/time -l`) |

El tiempo crece con una potencia cercana a 3 del número de celdas. Extrapolado a 96.461: varias
horas por corrida y mucha más memoria. **Extrapolación, no corrido.**

Trampa encontrada: `pygeoda.redcap` estandariza por defecto (`scale_method='standardize'`), lo que
anularía los pesos de D12 (composición 0,2). Pasar `scale_method='raw'` con los pesos ya aplicados.
La variante de primer orden (`firstorder-singlelinkage`) terminó con un error de C++ en 24.000 celdas;
no se investigó.

## Opciones (pendiente de decisión, ver `ROADMAP.md`)

- A. Res 5 (14.124 celdas) con REDCAP: el método de Boulanger con tamaño mínimo; D1 ya lo preveía.
  Requiere calcular las variables del paso 06 a res 5 sumando áreas, no promediando variables.
- B. Res 6 con Ward con contigüidad de scikit-learn o `spopt`: más rápido, no es REDCAP, sin tamaño
  mínimo.
- C. Res 6 con REDCAP por región de MapBiomas: fuerza límites; descartada en la propuesta.
