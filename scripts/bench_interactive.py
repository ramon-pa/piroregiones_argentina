#!/usr/bin/env python
"""scripts/bench_interactive.py: interactive (no export) benchmarks of the cell summaries.

Read-only, over a 1 x 1 degree box in Córdoba, with synthetic square cells built from the native
grid (no upload): 200 px per side (~30 km2, like H3 res 6) and 520 px (~200 km2, like H3 res 5).

  --cells   does the cell size change the cost? Grouped sums of pixel area, one year, for the
            available-cover summary (land cover Y-1, every pixel) and the burned summary (land
            cover Y-1 x month, burned pixels only).
  --scale   what does reading the land cover at a coarser pyramid level (60, 120, 240 m; the
            asset's pyramiding policy is MODE) cost in accuracy, against 30 m? Then a timing pass.
  --sweep   the yearly sweep of decision D6 on REAL H3 cells (res C.H3_RES, built locally and
            painted in GEE, as the national run will do), with its gates: the code stays an
            integer, no gaps in the painted grid, total area = box area, available and burned
            areas equal two separate summaries, month and size class agree, decoded values in
            range, and burned area on non-burnable / not-observed classes reported.

TIMINGS ARE ONLY VALID THE FIRST TIME a (year, scale, cell) computation is requested: GEE caches
results, so a repeat comes back in a fraction of a second. Pass years never used before
(--year, --timing-years) to time honestly. Accuracies do not depend on the cache.

Results and their reading: docs/notes/01-grid_and_compute.md. Run from the repo root:

    uv run python scripts/bench_interactive.py --cells --year 2020
    uv run python scripts/bench_interactive.py --scale --year 2019 --timing-years 1986 1987 1988 1989
    uv run python scripts/bench_interactive.py --sweep --sweep-years 1999 2010 2025
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


def h3_cells_image(ee):
    """Image of local cell ids 0..N-1 for the H3 cells touching BOX, on a masked background."""
    import h3
    w, s, e, n = BOX
    ring = [(w, s), (e, s), (e, n), (w, n), (w, s)]
    shape = h3.geo_to_h3shape({"type": "Polygon", "coordinates": [ring]})
    cells = sorted(h3.h3shape_to_cells_experimental(shape, C.H3_RES, contain="overlap"))
    feats = [ee.Feature(ee.Geometry.Polygon([[(lng, lat) for lat, lng in h3.cell_to_boundary(c)]]),
                        {"cell": i}) for i, c in enumerate(cells)]
    return ee.Image().int32().paint(ee.FeatureCollection(feats), "cell"), len(cells)


def sweep_code(ee, cell, year):
    """The D6 code: cell * CODE_CELL + class(Y-1) * CODE_CLASS + month * CODE_MONTH + size class."""
    lulc = lulc_band(ee, year + C.LULC_YEAR_OFFSET)
    month = ee.Image(f"{C.MONTH_OF_BURN_COL}/{C.MONTH_OF_BURN_IMAGE.format(year=year)}").select(C.MONTH_OF_BURN_BAND).unmask(0)
    size = ee.Image(C.SCAR_SIZE).select(C.SCAR_SIZE_BAND.format(year=year)).unmask(0)
    code = (cell.toInt32().multiply(C.CODE_CELL).add(lulc.multiply(C.CODE_CLASS))
            .add(month.multiply(C.CODE_MONTH)).add(size))
    return code, lulc, month


def bench_sweep(ee, box, years):
    cell, n_cells = h3_cells_image(ee)
    box_ha = box.area(1).getInfo() / 1e4
    print(f"D6 sweep on {n_cells} H3 res {C.H3_RES} cells touching the box ({box_ha:,.0f} ha)")

    gap = ee.Image.pixelArea().divide(1e4).updateMask(cell.mask().Not()).reduceRegion(
        ee.Reducer.sum(), box, crs=C.GRID_CRS, crsTransform=C.GRID_TRANSFORM, maxPixels=1e10).getInfo()
    gap_ha = list(gap.values())[0] or 0
    print(f"  [{'OK' if gap_ha < 1 else 'FAIL'}] pixels in the box with no cell: {gap_ha:,.2f} ha")

    burnable, not_burnable = set(C.BURNABLE_CLASSES), set(C.NON_BURNABLE_CLASSES) | set(C.NOT_OBSERVED_CLASSES)
    for year in years:
        print(f"\n fire year {year}, land cover {year + C.LULC_YEAR_OFFSET}")
        code, lulc, month = sweep_code(ee, cell, year)
        ctype = code.bandTypes().getInfo()
        ctype = list(ctype.values())[0]
        print(f"  [{'OK' if ctype.get('precision') == 'int' else 'FAIL'}] code band type: {ctype}")

        rows, sec = grouped_area(ee, box, code)
        dec = [(c // C.CODE_CELL, c % C.CODE_CELL // C.CODE_CLASS, c % C.CODE_CLASS // C.CODE_MONTH,
                c % C.CODE_MONTH, ha) for c, ha in rows.items()]
        print(f"  rows {len(rows):,}   time {sec:.1f} s   (first request of this year only; GEE caches)")

        total = sum(r[4] for r in dec)
        print(f"  [{'OK' if abs(total - box_ha) / box_ha < 1e-3 else 'FAIL'}] total area "
              f"{total:,.1f} ha vs box {box_ha:,.1f} ha ({(total - box_ha) / box_ha * 100:+.3f} %)")

        bad = [r for r in dec if not (0 <= r[0] < n_cells and r[1] < 100 and r[2] <= 12 and r[3] <= 8)]
        unknown = sorted({r[1] for r in dec} - burnable - not_burnable)
        print(f"  [{'OK' if not bad and not unknown else 'FAIL'}] decoded out of range: {len(bad)} rows; "
              f"classes in no list: {unknown}")

        mismatch = sum(r[4] for r in dec if (r[2] > 0) != (r[3] > 0))
        print(f"  [{'OK' if mismatch == 0 else 'FAIL'}] area with month xor size class: {mismatch:,.2f} ha")

        # Same two summaries computed separately, as in --cells.
        avail_ref, _ = grouped_area(ee, box, cell.toInt32().multiply(100).add(lulc))
        burn_ref, _ = grouped_area(ee, box, cell.toInt32().multiply(10000).add(lulc.multiply(100)).add(month)
                                   .updateMask(month.gt(0)))
        avail, burn = collections.Counter(), collections.Counter()
        for c, k, m, _, ha in dec:
            avail[c * 100 + k] += ha
            if m > 0:
                burn[c * 10000 + k * 100 + m] += ha
        d_avail = max(abs(avail[k] - avail_ref.get(k, 0)) for k in set(avail) | set(avail_ref))
        d_burn = max((abs(burn[k] - burn_ref.get(k, 0)) for k in set(burn) | set(burn_ref)), default=0)
        print(f"  [{'OK' if d_avail < 0.01 and d_burn < 0.01 else 'FAIL'}] largest difference against the "
              f"separate summaries: available {d_avail:.4f} ha, burned {d_burn:.4f} ha")

        burned = sum(r[4] for r in dec if r[2] > 0)
        off = sum(r[4] for r in dec if r[2] > 0 and r[1] not in burnable)
        by_cls = collections.Counter()
        for r in dec:
            if r[2] > 0 and r[1] not in burnable:
                by_cls[r[1]] += r[4]
        print(f"  [info] burned {burned:,.1f} ha; on non-burnable or not-observed classes {off:,.1f} ha "
              f"({off / burned * 100 if burned else 0:.2f} %) {dict(sorted(by_cls.items()))}")
        print(f"  [info] country estimate: ~{len(rows) * 2_795_123 / (box_ha / 100):,.0f} rows "
              f"(rows scaled by area; the real count depends on how varied each region is)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cells", action="store_true", help="cell size vs cost")
    ap.add_argument("--scale", action="store_true", help="coarser land-cover reads vs accuracy")
    ap.add_argument("--year", type=int, default=2020, help="fire year for --cells, land-cover year for --scale")
    ap.add_argument("--timing-years", type=int, nargs="*", default=[],
                    help="never-requested land-cover years for the --scale timing pass, 4 per repetition")
    ap.add_argument("--sweep", action="store_true", help="the D6 yearly sweep on real H3 cells, with gates")
    ap.add_argument("--sweep-years", type=int, nargs="*", default=[1999, 2010, 2025],
                    help="fire years for --sweep")
    args = ap.parse_args()
    if not (args.cells or args.scale or args.sweep):
        ap.error("choose --cells, --scale and/or --sweep")
    ee, box = setup()
    if args.cells:
        bench_cells(ee, box, args.year)
    if args.scale:
        bench_scale(ee, box, args.year, args.timing_years)
    if args.sweep:
        bench_sweep(ee, box, args.sweep_years)


if __name__ == "__main__":
    main()
