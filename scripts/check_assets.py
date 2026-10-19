#!/usr/bin/env python
"""scripts/check_assets.py: read-only check of every GEE input in utils/constants.py.

For each input it confirms the asset exists and is readable, that the band names and counts are
the ones constants.py assumes, and that every raster sits on the native grid: same pixel step and
an origin offset that is a whole number of pixels. Exits with status 1 if anything fails.

Nothing is exported and nothing is written. Run from the repo root:

    uv run python scripts/check_assets.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import constants as C  # noqa: E402

TOL = 1e-6  # tolerance, in pixels, for "whole number of pixels"


def grid_offset(transform):
    """Offset of a transform's origin from the native grid, in pixels (columns east, rows south)."""
    step, x0, y0 = C.GRID_TRANSFORM[0], C.GRID_TRANSFORM[2], C.GRID_TRANSFORM[5]
    same_step = abs(transform[0] - step) < 1e-12 and abs(abs(transform[4]) - step) < 1e-12
    return same_step, (transform[2] - x0) / step, (y0 - transform[5]) / step


def check_raster(ee, label, image, expected_bands):
    bands = image.bandNames().getInfo()
    proj = image.select(0).projection().getInfo()
    problems = []
    if bands != expected_bands:
        problems.append(f"bands {bands[:2]}...{bands[-1:]} (n={len(bands)}), "
                        f"expected {expected_bands[:2]}...{expected_bands[-1:]} (n={len(expected_bands)})")
    if proj.get("crs") != C.GRID_CRS:
        problems.append(f"crs {proj.get('crs')}, expected {C.GRID_CRS}")
    else:
        same_step, cols, rows = grid_offset(proj["transform"])
        whole = abs(cols - round(cols)) < TOL and abs(rows - round(rows)) < TOL
        if not (same_step and whole):
            problems.append(f"off the native grid: step equal={same_step}, offset {cols:.4f} cols, {rows:.4f} rows")
        else:
            label += f"  [offset {round(cols):+d} cols, {round(rows):+d} rows]"
    return label, problems


def main():
    import ee
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    years = C.FIRE_YEARS
    results = []

    # Month of burn: one image per year, each with one band.
    col = ee.ImageCollection(C.MONTH_OF_BURN_COL)
    ids = col.aggregate_array("system:index").getInfo()
    expected_ids = [C.MONTH_OF_BURN_IMAGE.format(year=y) for y in years]
    probs = [] if ids == expected_ids else [f"{len(ids)} images, expected {len(expected_ids)} named per constants"]
    for y in (years[0], years[-1]):
        img = ee.Image(f"{C.MONTH_OF_BURN_COL}/{C.MONTH_OF_BURN_IMAGE.format(year=y)}")
        lab, p = check_raster(ee, f"month of burn {y}", img, [C.MONTH_OF_BURN_BAND])
        results.append((lab, p))
    results.append(("month of burn collection", probs))

    # Scar size class: one band per fire year.
    results.append(check_raster(ee, "scar size class", ee.Image(C.SCAR_SIZE),
                                [C.SCAR_SIZE_BAND.format(year=y) for y in years]))

    # Frequency: off the native grid by design (D8), so check that it is still where we expect it.
    freq = ee.Image(C.FREQUENCY)
    freq_bands = freq.bandNames().getInfo()
    freq_crs = freq.select(C.FREQUENCY_BAND).projection().crs().getInfo() if C.FREQUENCY_BAND in freq_bands else None
    p = [] if freq_crs == C.FREQUENCY_CRS else [f"band {C.FREQUENCY_BAND} crs {freq_crs}, expected {C.FREQUENCY_CRS}"]
    results.append((f"frequency ({C.FREQUENCY_BAND}, {C.FREQUENCY_CRS})", p))

    # Land cover: must cover Y-1 for the first fire year through the last fire year.
    lulc = ee.Image(C.LULC)
    first = years[0] + C.LULC_YEAR_OFFSET
    lulc_bands = lulc.bandNames().getInfo()
    needed = [C.LULC_BAND.format(year=y) for y in range(first, years[-1] + 1)]
    missing = [b for b in needed if b not in lulc_bands]
    lab, p = check_raster(ee, f"land cover col-3 ({lulc_bands[0]}..{lulc_bands[-1]})",
                          lulc.select(needed[:1]), needed[:1])
    results.append((lab, p + ([f"missing bands {missing}"] if missing else [])))

    # Ecoregions: vectors, only existence, size and names.
    for label, asset, n in (("ecoregions 13", C.ECOREGIONS_13, 13), ("ecoregions 16", C.ECOREGIONS_16, 16)):
        fc = ee.FeatureCollection(asset)
        size = fc.size().getInfo()
        names = fc.aggregate_array(C.ECOREGION_NAME_FIELD).getInfo()
        p = [] if size == n and all(names) else [f"{size} features, expected {n}; empty names: {names.count(None)}"]
        results.append((f"{label} ({size} features)", p))

    # Output folder: exists and is a folder (write access is not tested here: this script is read-only).
    try:
        kind = ee.data.getAsset(C.OUTPUT_ROOT)["type"]
    except ee.EEException as e:
        kind = f"missing ({e})"
    results.append(("output folder", [] if kind == "FOLDER" else [f"{C.OUTPUT_ROOT}: {kind}"]))

    failed = 0
    for label, problems in results:
        print(f"{'OK  ' if not problems else 'FAIL'}  {label}")
        for msg in problems:
            print(f"        {msg}")
        failed += bool(problems)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
