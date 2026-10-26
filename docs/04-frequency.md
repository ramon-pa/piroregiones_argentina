# 04 · Frecuencia de quema por celda

Produce una tabla con el área de cada celda H3 quemada 1, 2, ... hasta 27 veces entre 1999 y 2025.
Consume la grilla del paso 01 y el producto publicado de frecuencia. Lo usan los pasos locales que
arman variables de recurrencia (proporción de área quemada más de una vez, intervalo de retorno).

## Fundamentos

Por qué el producto publicado y no un cálculo propio: D8 (`decisions.md`). La frecuencia pide los 27
años de cada píxel juntos; el producto ya los tiene. Está en EPSG:3857, fuera de la grilla nativa,
pero acá solo se resume por celda y nunca se cruza con la cobertura.

## Entradas → Salidas

`frecuencia 1999-2025 + grilla H3` → **`04-frequency.py --export`** → CSV en Drive → **`--fetch`**
(baja y corre `--check`)

| Entrada / Salida | Qué es | Dónde |
|---|---|---|
| Frecuencia | años quemados por píxel; lo nunca quemado, enmascarado | `FREQUENCY`, `FREQUENCY_BAND` |
| Grilla | celdas H3 res 6 con su id | `H3_GRID_ASSET` |
| Tabla | `code`, `sum` (ha); `code = celda × FREQ_CODE_CELL + años quemados` | Drive `DRIVE_FOLDER`, luego `FREQ_DIR` (fuera de git) |
| Control | las 27 tablas del paso 02 | `SWEEP_DIR` |

## Cómo funciona

- **Una reducción agrupada** de `pixelArea()` sobre `GRID_BBOX`, en la **grilla del propio
  producto** (`FREQUENCY_CRS`, `FREQUENCY_TRANSFORM`): ningún píxel se remuestrea. La grilla H3 se
  pinta en esa misma grilla. `pixelArea()` da el área real del píxel, que en 3857 cae con la latitud.
- **Máscaras.** Acá se quiere solo lo quemado: la máscara del producto queda como está, sin
  `unmask`. El área quemada 0 veces sale del denominador quemable del paso 02 (D9).
- **Una sola tarea** (`FREQ_TASK`), con el lanzador, el estado y la descarga compartidos con el paso
  02 en `utils/gee_tasks.py`.
- **Controles** (`--check`, sin GEE):
  - todo código decodifica en una celda válida y entre 1 y 27 años quemados;
  - la suma nacional de años quemados × área iguala la suma de lo quemado en las 27 tablas del paso
    02, con tolerancia `NATIONAL_TOL` del script (elegida por nosotros, no sale de un paper);
  - celda por celda, la misma comparación se informa sin cortar: mide el efecto de mezclar las dos
    grillas (D8).

## Correr

```bash
uv run python workflow/04-frequency.py --export
uv run python workflow/04-frequency.py --status
uv run python workflow/04-frequency.py --fetch   # baja de Drive y corre --check
uv run python workflow/04-frequency.py --check   # solo los controles, sin red
```

## Decisiones clave

- Reducir en la grilla del producto, no en la nativa: remuestrear movería píxeles de un producto
  que solo se resume.
- El control por celda informa y no corta: el desvío esperable entre grillas no estaba medido. Lo
  medido está en `docs/notes/04-frequency.md`.

## Trampas

- **`selfMask`**: no sacar el área de 0 veces de este producto (incluiría agua y roca, D8).
- **Contar píxeles en 3857 da mal**: el área del píxel cambia con la latitud. Siempre `pixelArea()`.

## Archivos

| Archivo | Rol |
|---|---|
| `workflow/04-frequency.py` | lanza la tarea, la lista, baja la tabla y la controla |
| `utils/gee_tasks.py` | lanzador, estado y descarga de Drive, compartidos con el paso 02 |
| `utils/constants.py` | `FREQUENCY*`, `FREQ_CODE_CELL`, `FREQ_TASK`, `FREQ_DIR` |

## Relacionado

- `docs/decisions.md`: D8, D9.
- `docs/02-sweep.md`: las tablas contra las que se controla.
- `docs/notes/04-frequency.md`: la corrida y lo medido.
