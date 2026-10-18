#!/usr/bin/env python
"""scripts/bench_interactive.py: interactive (no export) benchmarks of the cell summaries.

Read-only, over a 1 x 1 degree box in Córdoba, with synthetic square cells built from the native
grid (no upload): 200 px per side (~30 km2, like H3 res 6) and 520 px (~200 km2, like H3 res 5).

  --cells   does the cell size change the cost? Grouped sums of pixel area, one year, for the
            available-cover summary (land cover Y-1, every pixel) and the burned summary (land
            cover Y-1 x month, burned pixels only).
  --scale   what does reading the land cover at a coarser pyramid level (60, 120, 240 m; the
            asset's pyramiding policy is MODE) cost in accuracy, against 30 m? Then a timing pass.

TIMINGS ARE ONLY VALID THE FIRST TIME a (year, scale, cell) computation is requested: GEE caches
results, so a repeat comes back in a fraction of a second. Pass years never used before
(--year, --timing-years) to time honestly. Accuracies do not depend on the cache.

Results and their reading: docs/notes/01-grid_and_compute.md. Run from the repo root:

    uv run python scripts/bench_interactive.py --cells --year 2020
    uv run python scripts/bench_interactive.py --scale --year 2019 --timing-years 1986 1987 1988 1989
"""
import argparse
import collections
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import constants as C  # noqa: E402

BOX = [-64.5, -32.0, -63.5, -31.0]                  # W, S, E, N, Córdoba, ~10,500 km2
CELLS = {"res6-like": 200, "res5-like": 520}         # pixels per side of the synthetic cell
SCALES = (1, 2, 4, 8)                                # multiples of the 30 m native step


def setup():
    import ee
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    return ee, ee.Geometry.Rectangle(BOX, None, False)


def cell_id(ee, cell_px):
    """Integer id of a square cell of cell_px native pixels per side, aligned to the native grid."""
    step, x0, y0 = C.GRID_TRANSFORM[0], C.GRID_TRANSFORM[2], C.GRID_TRANSFORM[5]
    ll = ee.Image.pixelLonLat()
    cx = ll.select("longitude").subtract(x0).divide(cell_px * step).floor()
    cy = ll.select("latitude").subtract(y0).divide(-cell_px * step).floor()
    return cx.multiply(100000).add(cy).toInt64()


def grouped_area(ee, box, code, k=1):
    """{code: hectares}, summing pixel area per code at k times the native step. Plus seconds taken."""
    step, x0, y0 = C.GRID_TRANSFORM[0], C.GRID_TRANSFORM[2], C.GRID_TRANSFORM[5]
    t = time.time()
    groups = ee.Image.pixelArea().divide(1e4).addBands(code.rename("code")).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName="code"), geometry=box,
        crs=C.GRID_CRS, crsTransform=[step * k, 0, x0, 0, -step * k, y0], maxPixels=1e10,
    ).getInfo()["groups"]
    return {int(g["code"]): g["sum"] for g in groups}, time.time() - t


def lulc_band(ee, year):
    return ee.Image(C.LULC).select(C.LULC_BAND.format(year=year)).unmask(0)


def bench_cells(ee, box, year):
    lulc = lulc_band(ee, year + C.LULC_YEAR_OFFSET)
    month = ee.Image(f"{C.MONTH_OF_BURN_COL}/{C.MONTH_OF_BURN_IMAGE.format(year=year)}").select(C.MONTH_OF_BURN_BAND)
    print(f"cell size vs cost, fire year {year}, land cover {year + C.LULC_YEAR_OFFSET}")
    for name, px in CELLS.items():
        cid = cell_id(ee, px)
        for label, code in (("available cover", cid.multiply(100).add(lulc)),
                            ("burned", cid.multiply(10000).add(lulc.multiply(100)).add(month).updateMask(month.gt(0)))):
            res, sec = grouped_area(ee, box, code)
            print(f"  {label:<16} {name:<10} groups {len(res):>7,}   area {sum(res.values()):>12,.0f} ha   {sec:5.1f} s")


def bench_scale(ee, box, year, timing_years):
    lulc = lulc_band(ee, year)
    print(f"land cover {year} read at coarser scales vs 30 m (accuracy)")
    for name, px in CELLS.items():
        code = cell_id(ee, px).multiply(100).add(lulc)
        ref, _ = grouped_area(ee, box, code, 1)
        total = sum(ref.values())
        cls_ref = collections.Counter()
        for c, v in ref.items():
            cls_ref[c % 100] += v
        print(f"  {name}: {len(ref):,} cell-class groups at 30 m")
        for k in SCALES[1:]:
            got, _ = grouped_area(ee, box, code, k)
            moved = sum(abs(ref.get(c, 0) - got.get(c, 0)) for c in set(ref) | set(got)) / 2 / total
            cls_got = collections.Counter()
            for c, v in got.items():
                cls_got[c % 100] += v
            worst = sorted(((abs(cls_got[c] - cls_ref[c]) / cls_ref[c], c, cls_ref[c] / total)
                            for c in cls_ref if cls_ref[c] / total > 0.005), reverse=True)[:3]
            lost = sum(1 for c in ref if c not in got)
            print(f"    {30 * k:>3} m: area moved to another cell-class {moved * 100:5.2f} %   "
                  f"groups lost {lost}/{len(ref)}   worst classes (rel. error, class, share of box): "
                  + ", ".join(f"{e * 100:.0f}% c{c} ({s * 100:.1f}%)" for e, c, s in worst))
    if timing_years:
        need = len(SCALES)
        years = iter(timing_years)
        print("\ntiming, res6-like cells, one never-requested year per scale")
        for rep in range(len(timing_years) // need):
            parts = []
            for k in SCALES:
                code = cell_id(ee, CELLS["res6-like"]).multiply(100).add(lulc_band(ee, next(years)))
                parts.append(f"{30 * k:>3} m: {grouped_area(ee, box, code, k)[1]:4.1f} s")
            print(f"  rep {rep + 1}  " + "  ".join(parts))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cells", action="store_true", help="cell size vs cost")
    ap.add_argument("--scale", action="store_true", help="coarser land-cover reads vs accuracy")
    ap.add_argument("--year", type=int, default=2020, help="fire year for --cells, land-cover year for --scale")
    ap.add_argument("--timing-years", type=int, nargs="*", default=[],
                    help="never-requested land-cover years for the --scale timing pass, 4 per repetition")
    args = ap.parse_args()
    if not (args.cells or args.scale):
        ap.error("choose --cells and/or --scale")
    ee, box = setup()
    if args.cells:
        bench_cells(ee, box, args.year)
    if args.scale:
        bench_scale(ee, box, args.year, args.timing_years)


if __name__ == "__main__":
    main()
