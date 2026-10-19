"""The area of interest: continental Argentina, as one GeoJSON MultiPolygon.

Shared by scripts/h3_cells_argentina.py (how many cells) and workflow/01-hex_grid.py (the grid
itself), so both count the same cells. Every function takes an initialised ``ee``; nothing runs at
import time.
"""
from utils import constants as C


def continental_polygon(ee):
    """MultiPolygon GeoJSON of continental Argentina, simplified to C.AOI_SIMPLIFY_M metres."""
    fc = ee.FeatureCollection(C.ECOREGIONS_13).filter(ee.Filter.neq(C.ECOREGION_NAME_FIELD, C.AOI_EXCLUDE))
    geom = (fc.geometry(maxError=C.AOI_SIMPLIFY_M).simplify(maxError=C.AOI_SIMPLIFY_M)
            .transform("EPSG:4326", maxError=C.AOI_SIMPLIFY_M).getInfo())
    # Simplification leaves degenerate points and lines in a GeometryCollection: keep polygons only.
    parts = geom["geometries"] if geom["type"] == "GeometryCollection" else [geom]
    polys = []
    for g in parts:
        if g["type"] == "Polygon":
            polys.append(g["coordinates"])
        elif g["type"] == "MultiPolygon":
            polys.extend(g["coordinates"])
    return {"type": "MultiPolygon", "coordinates": polys}


def geodesic_area_km2(multipolygon):
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    total = 0.0
    for poly in multipolygon["coordinates"]:
        for i, ring in enumerate(poly):
            a, _ = geod.polygon_area_perimeter([c[0] for c in ring], [c[1] for c in ring])
            total += abs(a) if i == 0 else -abs(a)
    return total / 1e6
