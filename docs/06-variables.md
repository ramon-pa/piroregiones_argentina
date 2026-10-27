# 06 · Variables del régimen de fuego por celda

Calcula, para cada hexágono, los números que describen cómo se quema: seis variables de fuego y la
composición de su área quemable por familia de cobertura. Consume las tablas del paso 05 y una
tabla chica de GEE (la región de MapBiomas de cada celda). Su salida, `variables.parquet`, es lo que
agrupa el paso 07.

## Fundamentos

Qué variables y por qué: D12 (`decisions.md`). Las familias de cobertura: D11. Todas salen de áreas
ya sumadas por celda, así que el paso es local salvo la región.

## Entradas → Salidas

`sweep + frequency + cells (paso 05) + región por celda (GEE)` → **`06-variables.py --build`** →
`variables.parquet`

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| Tablas del paso 05 | barrido largo, frecuencia, celdas | `TABLES_DIR` |
| Región por celda | área de cada región de MapBiomas en cada celda | `REGION_RASTER` → Drive → `REGION_DIR` |
| `variables.parquet` | una fila por celda: variables, composición, banderas | `TABLES_DIR` |
| `variables_r5.parquet` | lo mismo a res 5: áreas de los hijos sumadas antes de calcular (D1) | `TABLES_DIR` |

## Cómo funciona

Solo entra el fuego sobre clases quemables del año previo (D9). Las variables:

| Columna | Qué es | Fuente |
|---|---|---|
| `rate` | % del área quemable quemado por año, media 1999 a 2025 | Boulanger et al. 2014, p. 366; Erni et al. 2020, p. 8 |
| `cv` | CV del área quemada anual | Naval-Fernández et al. 2025, pp. 6–7 |
| `recurrence` | cuantil 99 de las veces que se quemó cada hectárea, 0 incluido | Segura-Garcia et al. 2025, "Methods" (b)(i) |
| `peak_sin`, `peak_cos` (y `peak_month`) | mes en que se junta la mitad de lo quemado, en el año centrado en el mes de más quema | Segura-Garcia et al. 2025 |
| `season_len` | 2 desvíos del mes en ese año, en meses | Cattau et al. 2022, Tabla 1, p. 4 |
| `large_share` | proporción de lo quemado en cicatrices de 500 ha o más | Galizia et al. 2023, p. 3 (allí por número de fuegos > 100 ha) |
| `fam_*` | proporción del área quemable de cada familia (D11) | Boulanger et al. 2014, p. 368 |

- **Celdas sin fuego** (`no_fire`): tasa, recurrencia y `large_share` en 0; `cv` en `CV_NO_FIRE`;
  pico y duración, promedio de las vecinas, anillo por anillo (`season_imputed`).
- **Región** de cada celda: la de mayor área; `region_share` dice cuánto de la celda cubre. Las
  celdas fuera de toda región toman la región más común de sus vecinas.
- **Controles** (`--check`): sin huecos en las columnas del clustering; lo quemado y lo quemable
  sumados por celda igualan las tablas del paso 05; las proporciones por familia suman 1; valores en
  rango.

## Correr

```bash
uv run python workflow/06-variables.py --export   # GEE: región por celda, una tarea
uv run python workflow/06-variables.py --fetch
uv run python workflow/06-variables.py --build    # variables y controles
uv run python workflow/06-variables.py --build --res 5   # lo mismo a res 5, para el paso 07 (D13)
```

## Decisiones clave

Elecciones nuestras, sin paper:
- Corte de 500 ha para "cicatriz grande" (`LARGE_SIZE_CLASS`): parte lo quemado del país en dos
  mitades parecidas (48,8 % del área en cicatrices menores, según el equipo de fuego).
- `cv` de una celda sin fuego = el de una celda quemada un solo año (`CV_NO_FIRE`), el valor más
  episódico que admiten los datos.
- Año centrado: el mes de más quema en la posición 6 de 12. "Centrado" en 12 meses es ambiguo por
  un mes.
- La ECDF de la recurrencia no se suaviza (Segura-Garcia la suaviza).
- El pico entra al clustering como seno y coseno: el mes es circular.

## Trampas

- A res 5, la región de MapBiomas se elige después de sumar el área de cada región entre los hijos;
  elegirla antes daba la de un solo hijo (la primera corrida marcó 14.135 celdas con
  `region_share < 0.9`).

- Celdas sin fuego son el 38 %: el relleno de la temporada se hace anillo por anillo porque hay
  bloques grandes sin ninguna vecina con fuego.
- 143 celdas cuentan como sin fuego acá aunque tienen área quemada en el paso 04: todo su fuego
  cayó en clases no quemables (33 agua, 25 otras no vegetadas), que no entran a las variables (D9).

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/06-variables.py` | región por celda (GEE), variables y controles |
| `utils/constants.py` | `REGION_*`, `FAMILY_BY_REGION_CLASS`, `FAMILIES`, `BURNABLE_CLASSES` |

## Relacionado

- `docs/decisions.md`: D9, D11, D12.
- `docs/notes/06-variables.md`: lo medido.
