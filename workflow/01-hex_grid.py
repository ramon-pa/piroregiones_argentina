#!/usr/bin/env python
"""workflow/01-hex_grid.py: the H3 grid every later step sums into (decision D1).

  --build   (default) the H3 cells of resolution C.H3_RES that touch continental Argentina
            (utils/aoi.py), sorted by H3 index and numbered 0..N-1. Writes to C.H3_GRID_DIR:
              h3_res<r>.parquet   every column, for local work (cell, h3, h3_r5, area_km2)
              h3_res<r>.zip       shapefile with cell and h3 only, to upload to GEE by hand
            Reads GEE only to build the country polygon; writes nothing to GEE.
  --check   read-only, after the upload: the asset C.H3_GRID_ASSET has the same cells with the
            same ids as the local parquet, and the painted grid leaves no gap in a Córdoba box.

Doc: docs/01-hex_grid.md. Run from the repo root:

    uv run python workflow/01-hex_grid.py --build
    uv run python workflow/01-hex_grid.py --check
"""
import argparse
import os
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402
from utils.aoi import continental_polygon  # noqa: E402

OUT = REPO / C.H3_GRID_DIR
NAME = f"h3_res{C.H3_RES}"
CHECK_BOX = [-64.5, -32.0, -63.5, -31.0]  # the Córdoba box of scripts/bench_interactive.py


def init_ee():
    import ee
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    return ee


def build():
    import geopandas as gpd
    import h3
    from shapely.geometry import Polygon

    ee = init_ee()
    shape = h3.geo_to_h3shape(continental_polygon(ee))
    # With contain="overlap" a cell touching two of the country's polygons comes back once per
    # polygon (measured 2026-10-19: 182 extra copies at res 6), so deduplicate before numbering.
    cells = sorted(set(h3.h3shape_to_cells_experimental(shape, C.H3_RES, contain="overlap")))

    # Gates: these are the conditions the packed code of D6 and the later sums rely on.
    n = len(cells)
    assert len(set(cells)) == n, "duplicate cells"
    assert not any(h3.is_pentagon(c) for c in cells), "a pentagon fell inside"
    assert (n - 1) * C.CODE_CELL + 99 * C.CODE_CLASS < 2**31 - 1, "packed code would overflow int32"

    gdf = gpd.GeoDataFrame(
        {"cell": range(n), "h3": cells,
         "h3_r5": [h3.cell_to_parent(c, 5) for c in cells],
         "area_km2": [h3.cell_area(c, "km^2") for c in cells]},
        geometry=[Polygon([(lng, lat) for lat, lng in h3.cell_to_boundary(c)]) for c in cells],
        crs="EPSG:4326")

    OUT.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(OUT / f"{NAME}.parquet")
    with tempfile.TemporaryDirectory() as tmp:
        gdf[["cell", "h3", "geometry"]].to_file(Path(tmp) / f"{NAME}.shp", engine="pyogrio")
        with zipfile.ZipFile(OUT / f"{NAME}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(Path(tmp).iterdir()):
                z.write(f, f.name)

    print(f"{n:,} cells, res {C.H3_RES}, ids 0..{n - 1}, no pentagons")
    print(f"area {gdf.area_km2.sum():,.0f} km2 in total, {gdf.area_km2.min():.1f} to {gdf.area_km2.max():.1f} km2 per cell")
    print(f"res 5 parents: {gdf.h3_r5.nunique():,}")
    print(f"wrote {OUT / (NAME + '.parquet')}")
    print(f"wrote {OUT / (NAME + '.zip')} ({(OUT / (NAME + '.zip')).stat().st_size / 1e6:.1f} MB)")
    print(f"\nnext: upload the zip in the Code Editor (Assets > NEW > Shape files) as\n  {C.H3_GRID_ASSET}")


def check():
    import geopandas as gpd

    ee = init_ee()
    local = gpd.read_parquet(OUT / f"{NAME}.parquet")
    fc = ee.FeatureCollection(C.H3_GRID_ASSET)
    results = []

    ids, idx = fc.aggregate_array("cell").getInfo(), fc.aggregate_array("h3").getInfo()
    asset = dict(zip(ids, idx))
    same = len(ids) == len(local) and len(asset) == len(ids) and all(
        asset.get(c) == h for c, h in zip(local.cell, local.h3))
    results.append((f"asset has the local cells, same ids ({len(ids):,} vs {len(local):,})",
                    [] if same else ["cell -> h3 differs from the local parquet"]))

    box = ee.Geometry.Rectangle(CHECK_BOX, None, False)
    painted = ee.Image().int32().paint(fc, "cell")
    gap = ee.Image.pixelArea().divide(1e4).updateMask(painted.mask().Not()).reduceRegion(
        ee.Reducer.sum(), box, crs=C.GRID_CRS, crsTransform=C.GRID_TRANSFORM, maxPixels=1e10).getInfo()
    gap_ha = list(gap.values())[0] or 0
    results.append((f"no gap when painted, Córdoba box ({gap_ha:,.2f} ha unpainted)",
                    [] if gap_ha < 1 else [f"{gap_ha:,.2f} ha with no cell"]))

    failed = 0
    for label, problems in results:
        print(f"{'OK  ' if not problems else 'FAIL'}  {label}")
        for msg in problems:
            print(f"        {msg}")
        failed += bool(problems)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true", help="build the grid and the zip to upload (default)")
    ap.add_argument("--check", action="store_true", help="check the uploaded asset against the local grid")
    args = ap.parse_args()
    if args.check:
        check()
    else:
        build()


if __name__ == "__main__":
    main()
