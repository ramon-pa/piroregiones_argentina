#!/usr/bin/env python
"""scripts/h3_cells_argentina.py: how many H3 cells cover Argentina, and how much their area varies.

Read-only. The country polygon is the union of the 13 Burkart ecoregions minus Islas del Atlántico
Sur (continental Argentina), simplified to 500 m in GEE. It prints:

  * the polygon's geodesic area;
  * per resolution 4-7, the cells that touch the polygon (contain="overlap") and their area range;
  * per resolution 5-6, the area spread of the cells whose centre is inside (p5, p50, p95), and
    whether any of the 12 H3 pentagons falls inside.

Results and their reading: docs/notes/01-grid_and_compute.md. Run from the repo root:

    uv run python scripts/h3_cells_argentina.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import constants as C  # noqa: E402
from utils.aoi import continental_polygon, geodesic_area_km2  # noqa: E402


def main():
    import ee
    import h3
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    geom = continental_polygon(ee)
    print(f"continental Argentina: {len(geom['coordinates'])} polygons, "
          f"{geodesic_area_km2(geom):,.0f} km2 (simplified to {C.AOI_SIMPLIFY_M} m)\n")
    shape = h3.geo_to_h3shape(geom)

    print("cells touching the polygon (contain='overlap')")
    for r in (4, 5, 6, 7):
        # A cell touching two of the polygons comes back once per polygon: deduplicate.
        cells = set(h3.h3shape_to_cells_experimental(shape, r, contain="overlap"))
        areas = [h3.cell_area(c, "km^2") for c in cells]
        print(f"  res {r}: {len(cells):>8,} cells   area {min(areas):8.1f} to {max(areas):8.1f} km2")

    print("\narea spread of cells whose centre is inside (contain='center')")
    for r in (5, 6):
        cells = h3.h3shape_to_cells_experimental(shape, r, contain="center")
        a = sorted(h3.cell_area(c, "km^2") for c in cells)
        q = lambda p: a[int(p * (len(a) - 1))]  # noqa: E731
        pentagons = set(h3.get_pentagons(r)) & set(cells)
        print(f"  res {r}: n={len(a):,}  p5 {q(.05):.1f}  p50 {q(.5):.1f}  p95 {q(.95):.1f} km2   "
              f"p95/p5 {q(.95) / q(.05):.2f}   max/min {a[-1] / a[0]:.2f}   pentagons inside: {len(pentagons)}")


if __name__ == "__main__":
    main()
