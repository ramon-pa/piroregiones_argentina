#!/usr/bin/env python
"""workflow/04-frequency.py: area burned 1, 2, ... 27 times per cell, 1999-2025 (decision D8).

One grouped sum of pixel area over the code cell * FREQ_CODE_CELL + years burned, from the
published frequency product, on the product's own grid (C.FREQUENCY_CRS, C.FREQUENCY_TRANSFORM).
It is only summarised per cell, never crossed with land cover, so its EPSG:3857 grid does no harm.
The product is selfMask'ed: never-burned pixels are masked and stay out. The area burned 0 times
comes from the burnable denominator of step 02 (D9), not from here.

  --export  one task, CSV (code, sum) to the Drive folder C.DRIVE_FOLDER. Skipped if it is
            already waiting, running or finished; --force launches it again.
  --status  state of the step 04 task.
  --fetch   download the CSV into C.FREQ_DIR, then run --check.
  --check   read-only, no GEE: codes decode in range, and the burned area counted with its
            repetitions (sum of k * area) equals the sum of the 27 years of step 02, nationally
            (gate, NATIONAL_TOL) and per cell (reported, not gated: the gap between the two grids
            is what this run measures).

Doc: docs/04-frequency.md. Run from the repo root:

    uv run python workflow/04-frequency.py --export
    uv run python workflow/04-frequency.py --status
    uv run python workflow/04-frequency.py --fetch
    uv run python workflow/04-frequency.py --check
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402
from utils.gee_tasks import LIVE, export_grouped_area, fetch_csvs, init_ee, print_status, task_states  # noqa: E402

FREQ_DIR = REPO / C.FREQ_DIR
SWEEP_DIR = REPO / C.SWEEP_DIR
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
N_YEARS = len(C.FIRE_YEARS)
NATIONAL_TOL = 0.005  # our choice, not from a paper: the fire team found this product reproduces their total


def freq_code(ee):
    cell = ee.Image().int32().paint(ee.FeatureCollection(C.H3_GRID_ASSET), "cell")
    freq = ee.Image(C.FREQUENCY).select(C.FREQUENCY_BAND)
    return cell.multiply(C.FREQ_CODE_CELL).add(freq).rename("code")


def export(force):
    ee = init_ee()
    state = task_states(ee, C.FREQ_TASK).get(C.FREQ_TASK)
    if state in LIVE and not force:
        print(f"skip    {C.FREQ_TASK}: already {state}")
        return
    task = export_grouped_area(ee, freq_code(ee), C.FREQ_TASK, C.FREQUENCY_CRS, C.FREQUENCY_TRANSFORM)
    print(f"started {C.FREQ_TASK} -> Drive/{C.DRIVE_FOLDER}/{C.FREQ_TASK}.csv  (task {task.id})")


def sweep_burned_per_cell():
    """Hectares burned per cell, summed over the 27 yearly tables of step 02."""
    import pandas as pd

    parts = []
    for year in C.FIRE_YEARS:
        path = SWEEP_DIR / f"{C.SWEEP_TASK.format(year=year)}.csv"
        if not path.exists():
            sys.exit(f"{path.relative_to(REPO)} not found: run step 02 --fetch first")
        df = pd.read_csv(path)
        df = df[df["code"] % C.CODE_CLASS // C.CODE_MONTH > 0]
        parts.append(df.groupby(df["code"] // C.CODE_CELL)["sum"].sum())
    return pd.concat(parts).groupby(level=0).sum()


def check():
    import pandas as pd

    path = FREQ_DIR / f"{C.FREQ_TASK}.csv"
    if not path.exists():
        sys.exit(f"{path.relative_to(REPO)} not found: run --fetch first")
    n_cells = len(pd.read_parquet(GRID, columns=["cell"]))
    df = pd.read_csv(path)
    d = pd.DataFrame({"cell": df["code"] // C.FREQ_CODE_CELL, "k": df["code"] % C.FREQ_CODE_CELL,
                      "ha": df["sum"]})
    print(f"{path.relative_to(REPO)}: rows {len(d):,}, cells with some burn {d.cell.nunique():,} of {n_cells:,}")
    results = []

    bad = d[~(d.cell.between(0, n_cells - 1) & d.k.between(1, N_YEARS))]
    results.append((f"decoded out of range: {len(bad)} rows (k seen {d.k.min()} to {d.k.max()})", len(bad) == 0))

    freq = (d.k * d.ha).groupby(d.cell).sum()
    sweep = sweep_burned_per_cell()
    diff = (freq.sum() - sweep.sum()) / sweep.sum()
    results.append((f"national burned with repetitions: frequency {freq.sum() / 1e6:.3f} Mha vs step 02 "
                    f"{sweep.sum() / 1e6:.3f} Mha ({diff:+.3%}, tolerance {NATIONAL_TOL:.1%})",
                    abs(diff) <= NATIONAL_TOL))

    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok

    both = pd.DataFrame({"freq": freq, "sweep": sweep}).fillna(0)
    only = ((both.freq > 0) != (both.sweep > 0)).sum()
    rel = ((both.freq - both.sweep) / both.sweep).where(both.sweep > 0)
    q = rel.quantile([0.01, 0.05, 0.5, 0.95, 0.99])
    print(f"  info  per cell, (frequency - step 02) / step 02: "
          + ", ".join(f"p{int(p * 100)} {v:+.2%}" for p, v in q.items()))
    for lo in (10, 100, 1000):
        r = rel[both.sweep >= lo]
        print(f"  info  cells with >= {lo:>4} ha burned in step 02: {len(r):,}, "
              f"{(r.abs() > 0.05).sum():,} off by > 5 %")
    print(f"  info  cells burned in one source only: {only:,} "
          f"({both.freq[both.sweep == 0].sum() + both.sweep[both.freq == 0].sum():,.0f} ha)")
    print(f"  info  area burned at least once: {d.ha.sum() / 1e6:.3f} Mha")

    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--export", action="store_true", help="launch the batch task")
    ap.add_argument("--status", action="store_true", help="state of the step 04 task")
    ap.add_argument("--fetch", action="store_true", help="download the CSV from Drive, then --check")
    ap.add_argument("--check", action="store_true", help="gates on the downloaded CSV")
    ap.add_argument("--force", action="store_true", help="--export even if the task already exists")
    args = ap.parse_args()
    if not (args.export or args.status or args.fetch or args.check):
        ap.error("choose --export, --status, --fetch or --check")
    if args.export:
        export(args.force)
    if args.status:
        print_status(C.FREQ_TASK)
    if args.fetch:
        fetch_csvs([f"{C.FREQ_TASK}.csv"], FREQ_DIR)
        check()
    elif args.check:
        check()


if __name__ == "__main__":
    main()
