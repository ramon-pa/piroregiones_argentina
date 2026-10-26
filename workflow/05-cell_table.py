#!/usr/bin/env python
"""workflow/05-cell_table.py: the downloaded GEE tables, decoded into typed Parquet, with the
controls that cross steps. Local only, no GEE. Everything after this step reads C.TABLES_DIR.

  --build    (default) writes to C.TABLES_DIR:
               sweep.parquet      cell, year, cls, month, size, ha    (step 02, the 27 years, long)
               frequency.parquet  cell, k, ha                         (step 04; k = years burned)
               cells.parquet      cell, h3, h3_r5, area_km2           (step 01, without geometry)
             then runs --check.
  --check    the controls, on the Parquet files:
               every year has every cell; each cell's total area is the same in the 27 years;
               the columns re-encode to the original codes; frequency and sweep agree per cell
               and nationally; national burned area still equals step 02's.
  --classes  available area, burned area and yearly burn rate per land-cover class, national,
             1999-2025 (the table of decision D10).

Doc: docs/05-cell_table.md. Run from the repo root:

    uv run python workflow/05-cell_table.py --build
    uv run python workflow/05-cell_table.py --check
    uv run python workflow/05-cell_table.py --classes
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

TABLES = REPO / C.TABLES_DIR
SWEEP_DIR = REPO / C.SWEEP_DIR
FREQ_CSV = REPO / C.FREQ_DIR / f"{C.FREQ_TASK}.csv"
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
YEAR_AREA_TOL = 1e-6  # relative spread of a cell's total area across years (CSV rounding only)
NATIONAL_TOL = 0.005  # frequency vs sweep, the same tolerance as step 04


def decode_sweep(code):
    return {"cell": (code // C.CODE_CELL).astype("int32"),
            "cls": (code % C.CODE_CELL // C.CODE_CLASS).astype("int8"),
            "month": (code % C.CODE_CLASS // C.CODE_MONTH).astype("int8"),
            "size": (code % C.CODE_MONTH).astype("int8")}


def build():
    import pandas as pd

    TABLES.mkdir(parents=True, exist_ok=True)
    parts = []
    for year in C.FIRE_YEARS:
        path = SWEEP_DIR / f"{C.SWEEP_TASK.format(year=year)}.csv"
        if not path.exists():
            sys.exit(f"{path.relative_to(REPO)} not found: run step 02 --fetch first")
        df = pd.read_csv(path)
        part = pd.DataFrame(decode_sweep(df["code"].astype("int64")))
        part.insert(1, "year", pd.Series(year, index=df.index, dtype="int16"))
        part["ha"] = df["sum"]
        parts.append(part)
    sweep = pd.concat(parts, ignore_index=True)
    sweep.to_parquet(TABLES / "sweep.parquet", index=False)

    if not FREQ_CSV.exists():
        sys.exit(f"{FREQ_CSV.relative_to(REPO)} not found: run step 04 --fetch first")
    df = pd.read_csv(FREQ_CSV)
    pd.DataFrame({"cell": (df["code"] // C.FREQ_CODE_CELL).astype("int32"),
                  "k": (df["code"] % C.FREQ_CODE_CELL).astype("int8"),
                  "ha": df["sum"]}).to_parquet(TABLES / "frequency.parquet", index=False)

    pd.read_parquet(GRID, columns=["cell", "h3", "h3_r5", "area_km2"]).to_parquet(TABLES / "cells.parquet", index=False)

    for name in ("sweep", "frequency", "cells"):
        f = TABLES / f"{name}.parquet"
        print(f"wrote {f.relative_to(REPO)}  {f.stat().st_size / 1e6:.1f} MB")
    check(sweep)


def check(sweep=None):
    import pandas as pd

    sweep = pd.read_parquet(TABLES / "sweep.parquet") if sweep is None else sweep
    freq = pd.read_parquet(TABLES / "frequency.parquet")
    cells = pd.read_parquet(TABLES / "cells.parquet")
    n = len(cells)
    print(f"\nsweep {len(sweep):,} rows, frequency {len(freq):,} rows, {n:,} cells")
    results = []

    per_year = sweep.groupby("year").cell.nunique()
    results.append((f"every year has every cell: {(per_year == n).sum()}/{len(C.FIRE_YEARS)} years",
                    len(per_year) == len(C.FIRE_YEARS) and (per_year == n).all()))

    area = sweep.groupby(["cell", "year"]).ha.sum().unstack()
    spread = ((area.max(axis=1) - area.min(axis=1)) / area.mean(axis=1)).max()
    results.append((f"each cell's total area equal across years: largest relative spread {spread:.1e}",
                    spread <= YEAR_AREA_TOL))

    # Round trip, per year: the columns re-encode to exactly the codes in the CSV.
    bad = 0
    for year, part in sweep.groupby("year"):
        code = (part.cell.astype("int64") * C.CODE_CELL + part.cls.astype("int64") * C.CODE_CLASS
                + part.month.astype("int64") * C.CODE_MONTH + part["size"].astype("int64"))
        orig = pd.read_csv(SWEEP_DIR / f"{C.SWEEP_TASK.format(year=year)}.csv")["code"]
        bad += int((code.to_numpy() != orig.to_numpy()).sum())
    results.append((f"columns re-encode to the original codes: {bad} rows differ", bad == 0))

    burned = sweep[sweep.month > 0]
    b_cell = burned.groupby("cell").ha.sum()
    f_cell = (freq.k * freq.ha).groupby(freq.cell).sum()
    diff = (f_cell.sum() - b_cell.sum()) / b_cell.sum()
    results.append((f"frequency vs sweep, national: {f_cell.sum() / 1e6:.3f} vs {b_cell.sum() / 1e6:.3f} Mha "
                    f"({diff:+.3%})", abs(diff) <= NATIONAL_TOL))
    both = pd.DataFrame({"f": f_cell, "s": b_cell}).fillna(0)
    big = both[both.s >= 100]
    off = int(((big.f - big.s).abs() / big.s > 0.05).sum())
    results.append((f"frequency vs sweep, cells with >= 100 ha burned: {off} of {len(big):,} off by > 5 %", off == 0))

    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"  info  burned 1999-2025: {burned.ha.sum():,.0f} ha")
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def classes():
    import pandas as pd

    sweep = pd.read_parquet(TABLES / "sweep.parquet", columns=["year", "cls", "month", "ha"])
    years = sweep.year.nunique()
    avail = sweep.groupby("cls").ha.sum() / years
    burned = sweep[sweep.month > 0].groupby("cls").ha.sum()
    t = pd.DataFrame({"avail_Mha_mean": avail / 1e6, "burned_Mha_total": burned / 1e6}).fillna(0)
    t["rate_pct_per_year"] = t.burned_Mha_total / years / t.avail_Mha_mean * 100
    t["burnable"] = t.index.isin(C.BURNABLE_CLASSES)
    print(f"national, land cover of the year before each fire, {years} fire years")
    print(t.sort_values("avail_Mha_mean", ascending=False).round(3).to_string())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true", help="decode the CSVs into Parquet, then --check (default)")
    ap.add_argument("--check", action="store_true", help="controls on the Parquet files")
    ap.add_argument("--classes", action="store_true", help="area and burn rate per land-cover class")
    args = ap.parse_args()
    if args.check:
        check()
    elif args.classes:
        classes()
    else:
        build()


if __name__ == "__main__":
    main()
