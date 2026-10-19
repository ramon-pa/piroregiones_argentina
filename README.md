# Pirorregiones de Argentina

Delimitación de regiones de régimen de fuego para Argentina, como las ecorregiones pero definidas
por cómo se quema el territorio. Insumos: MapBiomas Argentina Fuego (colección 1, 1999 a 2025) y
cobertura MapBiomas Argentina (colección 3), a 30 m. Trabajo final del curso Geo Data Scientist de
Geo Dojo, para presentar en el taller de MapBiomas.

**Este README es el mapa y la instalación.** No lleva estado: el estado está en
[`ROADMAP.md`](ROADMAP.md). El método en una página está en
[`docs/00-overview.md`](docs/00-overview.md).

---

## Instalación

Requiere [uv](https://docs.astral.sh/uv/) y una cuenta de Google Earth Engine con lectura sobre
`projects/mapbiomas-argentina`.

```bash
git clone git@github.com:ramon-pa/piroregiones_argentina.git
cd piroregiones_argentina
uv sync                                   # crea .venv con Python 3.12
earthengine authenticate                  # una sola vez por máquina
uv run python scripts/check_assets.py     # debe terminar en "9/9 checks passed"
```

El proyecto de cómputo de GEE sale de `utils/constants.py`. Para usar otro, exportar
`GEE_PROJECT` en la terminal (ver `.env.example`).

En Positron, elegir como kernel el Python de `.venv/`, no el del sistema.

---

## Dónde está cada cosa

| Carpeta / archivo | Qué tiene |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | índice del proyecto: assets verificados, números, problemas conocidos, reglas de trabajo |
| [`ROADMAP.md`](ROADMAP.md) | qué sigue, en orden |
| [`BACKLOG.md`](BACKLOG.md) | ideas sin agendar |
| `utils/constants.py` | **única fuente de verdad**: assets, años, grilla, nombres de tareas |
| `scripts/` | lo que no es un paso del pipeline: chequeos, lanzadores |
| `workflow/` | los pasos numerados del pipeline (se crea con el primer paso) |
| [`docs/`](docs/) | `00-overview.md`, un doc por paso, `TEMPLATE.md`, `decisions.md`, `references.md` |
| [`docs/notes/`](docs/notes/) | cuaderno de laboratorio: pruebas, caminos abandonados, resultados con fecha |
| `data/` | datos locales, fuera de git |
| `outputs/` | figuras |
