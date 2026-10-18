# TEMPLATE · La forma de un doc de paso

Adaptado de `collection-01/docs/TEMPLATE.md` del repo de MapBiomas Argentina Fuego (Iván Barberá).
Es una guía, no un formulario: lo fijo es la **columna** y las **reglas de dónde vive cada dato**.

## La columna

En este orden. **En negrita = siempre presente.**

| Sección | Tiene | No tiene |
|---|---|---|
| **Título + orientación** | un párrafo: qué produce el paso, qué consume, dónde está en la cadena | historia, comandos |
| Fundamentos | por qué este tipo de método, y las restricciones que lo forzaron | valores de parámetros |
| **Entradas → Salidas** | una línea de flujo y una tabla chica | cómo se calcula |
| **Cómo funciona** | la mecánica, con el detalle anidado bajo lo que detalla | comandos, pruebas |
| Correr | un bloque: la invocación y los flags que cambian el resultado | la lista completa de flags (eso es `--help`) |
| Decisiones clave | hasta 5 viñetas: la decisión, por qué en una línea, puntero a `notes/` | cómo se llegó |
| Trampas | lo que le costó un día a alguien | lo ya dicho arriba |
| **Archivos** | tabla de archivos y su rol | |
| **Relacionado** | notebooks, notas, docs hermanos | lo que no está enlazado |

Una sección ausente es la respuesta correcta cuando el paso no tiene nada que poner ahí.

## Dónde vive cada "por qué"

| Lugar | Tiene |
|---|---|
| Fundamentos (el doc) | por qué este tipo de método |
| Decisiones clave (el doc) | las elecciones dentro del método |
| `docs/notes/` | cómo se llegó: pruebas, caminos abandonados, resultados con fecha |

Al mover historia a `notes/`, el doc conserva el resultado y como mucho una frase de cómo se llegó.

## Reglas

1. El primer párrafo se entiende solo.
2. `00-overview.md` da el encuadre una vez; los docs de paso no lo repiten.
3. El nombre del título dice qué hace, no su número (el número ya está en el nombre del archivo).
4. **Citar secciones por nombre, nunca por número**, también desde el código.
5. Sin bloques largos de código, salvo el de Correr.
6. Parámetros, paths, umbrales e ids de assets viven en `utils/constants.py` (y `config/`); los docs
   apuntan ahí y nunca repiten un valor que es del código.
7. Cómo invocar un script vive en su docstring o `--help`.
8. Nada se borra: se mueve a `docs/notes/`.

## Esqueleto

```markdown
# NN · <qué produce>

<Un párrafo: qué produce, qué consume, dónde está en la cadena.>

## Entradas → Salidas
`<A> + <B>` → **`<paso>`** → `<salida>`
| Entrada / Salida | Qué es | Dónde |
|---|---|---|

## Cómo funciona

## Archivos
| Archivo | Rol |
|---|---|

## Relacionado
```
