#!/usr/bin/env python
"""workflow/02-sweep.py: the yearly sweep of decision D6, one batch task per fire year.

One grouped sum of pixel area per year over the packed code
    cell * CODE_CELL + class(Y-1) * CODE_CLASS + month * CODE_MONTH + size class
on the native grid, cells painted from C.H3_GRID_ASSET. Summing a cell's rows gives the area of
each cover class (available); the rows with month > 0 give the burned area by class, month and size.

  --export  one task per year in --years, CSV (code, sum) to the Drive folder C.DRIVE_FOLDER.
            A year whose task is already waiting, running or finished is skipped, so re-running
            never duplicates work. Pass --force to launch it again anyway.
  --status  state of every step 02 task in the project.
  --fetch   download each year's CSV from Drive into C.SWEEP_DIR (newest file of that name), with
            the GEE credentials on this machine, then run --check.
  --summary read-only, no GEE: burned area per year from the downloaded CSVs, and their sum against
            the fire team's national total (REF_BURNED_MHA).
  --check   read-only, no GEE: decode CSVs downloaded into C.SWEEP_DIR and run the gates of the
            Córdoba test (docs/notes/02-sweep_cordoba.md) plus one more: each cell's total area
            equals its H3 area.

Doc: docs/02-sweep.md. Run from the repo root:

    uv run python workflow/02-sweep.py --export --years 2025
    uv run python workflow/02-sweep.py --status
    uv run python workflow/02-sweep.py --fetch --years 2025
    uv run python workflow/02-sweep.py --check --years 2025
    uv run python workflow/02-sweep.py --summary
"""
import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

SWEEP_DIR = REPO / C.SWEEP_DIR
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
LIVE = {"READY", "RUNNING", "COMPLETED"}  # states that mean "this year is done or on its way"
# Burned area 1999-2025 from the fire team's toolkit, given to two decimals (fire repo,
# statistics/docs/statistics.md, check "National annual burned: toolkit vs the object database").
REF_BURNED_MHA = 63.23
CELL_AREA_TOL = 0.01  # per-cell raster total vs H3 area; H3 is spherical, pixelArea() ellipsoidal


def init_ee():
    import ee
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    return ee


def sweep_code(ee, year):
    """The D6 code for one fire year. The painted grid is the only mask: everything else is
    unmasked to 0, so no pixel inside a cell can drop out of the sums. sameFootprint=False: by
    default unmask() fills only inside the asset's footprint, and the cells on its edges lost area
    (17 cells in the first 2025 run, docs/02-sweep.md, "Trampas")."""
    cell = ee.Image().int32().paint(ee.FeatureCollection(C.H3_GRID_ASSET), "cell")
    lulc = ee.Image(C.LULC).select(C.LULC_BAND.format(year=year + C.LULC_YEAR_OFFSET)).unmask(0, False)
    month = (ee.Image(f"{C.MONTH_OF_BURN_COL}/{C.MONTH_OF_BURN_IMAGE.format(year=year)}")
             .select(C.MONTH_OF_BURN_BAND).unmask(0, False))
    size = ee.Image(C.SCAR_SIZE).select(C.SCAR_SIZE_BAND.format(year=year)).unmask(0, False)
    return (cell.multiply(C.CODE_CELL).add(lulc.multiply(C.CODE_CLASS))
            .add(month.multiply(C.CODE_MONTH)).add(size).rename("code"))


def our_tasks(ee):
    """{description: state} of the step 02 tasks, newest first wins."""
    prefix = C.SWEEP_TASK.split("{")[0]
    out = {}
    for t in ee.data.getTaskList():
        d = t.get("description", "")
        if d.startswith(prefix) and d not in out:
            out[d] = t.get("state")
    return out


def export(years, force):
    ee = init_ee()
    existing = our_tasks(ee)
    box = ee.Geometry.Rectangle(C.GRID_BBOX, None, False)
    for year in years:
        desc = C.SWEEP_TASK.format(year=year)
        if existing.get(desc) in LIVE and not force:
            print(f"skip    {desc}: already {existing[desc]}")
            continue
        groups = ee.List(ee.Image.pixelArea().divide(1e4).addBands(sweep_code(ee, year)).reduceRegion(
            reducer=ee.Reducer.sum().group(groupField=1, groupName="code"), geometry=box,
            crs=C.GRID_CRS, crsTransform=C.GRID_TRANSFORM, maxPixels=1e13).get("groups"))
        fc = ee.FeatureCollection(groups.map(lambda g: ee.Feature(None, ee.Dictionary(g))))
        task = ee.batch.Export.table.toDrive(
            collection=fc, description=desc, folder=C.DRIVE_FOLDER, fileNamePrefix=desc,
            fileFormat="CSV", selectors=["code", "sum"])
        task.start()
        print(f"started {desc} -> Drive/{C.DRIVE_FOLDER}/{desc}.csv  (task {task.id})")


def status():
    ee = init_ee()
    tasks = our_tasks(ee)
    if not tasks:
        print("no step 02 tasks in the project")
    for desc, state in sorted(tasks.items()):
        print(f"{state:<10} {desc}")


def fetch(years):
    import json

    import ee
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    # The earthengine credentials carry the Drive scope. No quota project, as in the fire team's
    # burnable_export.py --fetch: the call is billed to the OAuth client and needs no API enabled.
    stored = json.loads(Path("~/.config/earthengine/credentials").expanduser().read_text())
    creds = Credentials(None, refresh_token=stored["refresh_token"], token_uri=ee.oauth.TOKEN_URI,
                        client_id=stored.get("client_id", ee.oauth.CLIENT_ID),
                        client_secret=stored.get("client_secret", ee.oauth.CLIENT_SECRET),
                        scopes=stored.get("scopes", ee.oauth.SCOPES))
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    for year in years:
        name = f"{C.SWEEP_TASK.format(year=year)}.csv"
        files = drive.files().list(q=f"name = '{name}' and trashed = false", orderBy="modifiedTime desc",
                                   fields="files(id,size,modifiedTime)").execute().get("files", [])
        if not files:
            print(f"missing {name} in Drive (check --status)")
            continue
        f = files[0]
        with open(SWEEP_DIR / name, "wb") as out:
            dl = MediaIoBaseDownload(out, drive.files().get_media(fileId=f["id"]))
            done = False
            while not done:
                done = dl.next_chunk()[1]
        print(f"fetched {name}  {int(f['size']) / 1e6:.1f} MB  modified {f['modifiedTime']}"
              + (f"  ({len(files)} files with this name, took the newest)" if len(files) > 1 else ""))
    check(years)


def summary():
    import pandas as pd

    total = 0.0
    for year in C.FIRE_YEARS:
        path = SWEEP_DIR / f"{C.SWEEP_TASK.format(year=year)}.csv"
        if not path.exists():
            sys.exit(f"{path.relative_to(REPO)} not found: --fetch every year first")
        df = pd.read_csv(path)
        burned = df.loc[df["code"] % C.CODE_CLASS // C.CODE_MONTH > 0, "sum"].sum()
        total += burned
        print(f"{year}  {burned:>12,.0f} ha")
    diff = (total / 1e6 - REF_BURNED_MHA) / REF_BURNED_MHA * 100
    print(f"\n{C.FIRE_YEARS[0]}-{C.FIRE_YEARS[-1]}  {total:,.0f} ha = {total / 1e6:.3f} Mha; "
          f"fire team {REF_BURNED_MHA} Mha ({diff:+.3f} %)")


def check(years):
    import geopandas as gpd
    import pandas as pd

    grid = gpd.read_parquet(GRID)[["cell", "area_km2"]].set_index("cell")
    burnable = set(C.BURNABLE_CLASSES)
    known = burnable | set(C.NON_BURNABLE_CLASSES) | set(C.NOT_OBSERVED_CLASSES)
    failed_years = 0

    for year in years:
        path = SWEEP_DIR / f"{C.SWEEP_TASK.format(year=year)}.csv"
        print(f"\nfire year {year}, land cover {year + C.LULC_YEAR_OFFSET}: {path.relative_to(REPO)}")
        if not path.exists():
            print("  FAIL  file not found (download it from Drive first)")
            failed_years += 1
            continue
        df = pd.read_csv(path)
        code = df["code"].astype("int64")
        d = pd.DataFrame({"cell": code // C.CODE_CELL, "cls": code % C.CODE_CELL // C.CODE_CLASS,
                          "month": code % C.CODE_CLASS // C.CODE_MONTH, "size": code % C.CODE_MONTH,
                          "ha": df["sum"]})
        print(f"  rows {len(d):,}   cells {d.cell.nunique():,} of {len(grid):,}")
        results = []

        bad = d[~(d.cell.between(0, len(grid) - 1) & (d.cls < 100) & (d.month <= 12) & (d["size"] <= 8))]
        unknown = sorted(set(d.cls) - known)
        results.append((f"decoded out of range: {len(bad)} rows; classes in no list: {unknown}",
                        len(bad) == 0 and not unknown))

        xor = d.loc[(d.month > 0) != (d["size"] > 0), "ha"].sum()
        results.append((f"area with month xor size class: {xor:,.2f} ha", xor == 0))

        per_cell = d.groupby("cell").ha.sum() / 100  # ha -> km2
        ratio = (per_cell / grid.area_km2).reindex(grid.index)
        missing = int(ratio.isna().sum())
        off = int(((ratio - 1).abs() > CELL_AREA_TOL).sum())
        results.append((f"cell total vs H3 area: ratio {ratio.min():.4f} to {ratio.max():.4f}, "
                        f"{off} cells off by > {CELL_AREA_TOL:.0%}, {missing} cells with no rows",
                        off == 0 and missing == 0))

        failed = 0
        for label, ok in results:
            print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
            failed += not ok
        failed_years += bool(failed)

        burned = d[d.month > 0]
        off_cls = burned[~burned.cls.isin(burnable)]
        print(f"  info  total {d.ha.sum() / 1e6:,.3f} Mha; burnable {d[d.cls.isin(burnable)].ha.sum() / 1e6:,.3f} Mha; "
              f"burned {burned.ha.sum():,.0f} ha")
        print(f"  info  burned on non-burnable or not-observed classes {off_cls.ha.sum():,.0f} ha "
              f"({off_cls.ha.sum() / burned.ha.sum() * 100 if len(burned) else 0:.2f} %) "
              f"{off_cls.groupby('cls').ha.sum().round(0).to_dict()}")

    print(f"\n{len(years) - failed_years}/{len(years)} years passed")
    sys.exit(1 if failed_years else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--export", action="store_true", help="launch one batch task per year")
    ap.add_argument("--status", action="store_true", help="state of the step 02 tasks")
    ap.add_argument("--fetch", action="store_true", help="download the CSVs from Drive, then --check")
    ap.add_argument("--check", action="store_true", help="gates on the downloaded CSVs")
    ap.add_argument("--summary", action="store_true", help="burned area per year and in total")
    ap.add_argument("--years", type=int, nargs="+", help="fire years (required for --export and --check)")
    ap.add_argument("--force", action="store_true", help="--export even if the task already exists")
    args = ap.parse_args()
    if not (args.export or args.status or args.fetch or args.check or args.summary):
        ap.error("choose --export, --status, --fetch, --check or --summary")
    if (args.export or args.fetch or args.check) and not args.years:
        ap.error("--years is required: run one national year first (ROADMAP.md)")
    if args.years and not set(args.years) <= set(C.FIRE_YEARS):
        ap.error(f"years must be within {C.FIRE_YEARS[0]}-{C.FIRE_YEARS[-1]}")
    if args.export:
        export(args.years, args.force)
    if args.status:
        status()
    if args.fetch:
        fetch(args.years)
    elif args.check:
        check(args.years)
    if args.summary:
        summary()


if __name__ == "__main__":
    main()
