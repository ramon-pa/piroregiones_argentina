#!/usr/bin/env python
"""workflow/06-variables.py: the fire-regime variables of each cell, from the step 05 tables.

Six fire variables and the land-cover composition by family (docs/06-variables.md has the
definitions and their sources), one row per cell, to C.TABLES_DIR/variables.parquet. Cells with no
fire in 1999-2025 get values instead of gaps, following Segura-Garcia et al. 2025, so the
contiguity graph of step 07 has no holes.

  --export  GEE, one task: area of each MapBiomas fire region per cell (C.REGION_RASTER), CSV to
            Drive. The families depend on the region (decision D11).
  --status  state of that task.
  --fetch   download its CSV into C.REGION_DIR.
  --build   (default) compute the variables, then run --check.
  --check   controls on variables.parquet: no gaps, national totals equal step 05's, shares add up.
  --res 5   the same at res 5, to variables_r5.parquet: the areas of the seven res 6 children are
            summed into their parent before any variable is computed (decision D1), so the cell id
            becomes the parent's (0..14,136, in h3_r5 order) and h3 its res 5 index.

Run from the repo root:

    uv run python workflow/06-variables.py --export
    uv run python workflow/06-variables.py --fetch
    uv run python workflow/06-variables.py --build
    uv run python workflow/06-variables.py --build --res 5
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402
from utils.gee_tasks import LIVE, export_grouped_area, fetch_csvs, init_ee, print_status, task_states  # noqa: E402

TABLES = REPO / C.TABLES_DIR
REGION_CSV = REPO / C.REGION_DIR / f"{C.REGION_TASK}.csv"
N_YEARS = len(C.FIRE_YEARS)
LARGE_SIZE_CLASS = 4  # scars of 500 ha or more (fire repo, SCAR_SIZE_LOWER_HA); our cut, not a paper's
RECURRENCE_Q = 0.99   # Segura-Garcia et al. 2025, "Methods" (b)(i): 99th quantile of times burned
# CV of a cell that burned in exactly one year of N_YEARS (population standard deviation). Given to
# cells with no fire at all: the most episodic value the data can show. Our choice, not a paper's.
CV_NO_FIRE = (N_YEARS - 1) ** 0.5


def export(force):
    ee = init_ee()
    state = task_states(ee, C.REGION_TASK).get(C.REGION_TASK)
    if state in LIVE and not force:
        print(f"skip    {C.REGION_TASK}: already {state}")
        return
    cell = ee.Image().int32().paint(ee.FeatureCollection(C.H3_GRID_ASSET), "cell")
    region = ee.Image(C.REGION_RASTER).select(C.REGION_BAND).unmask(0, False)
    task = export_grouped_area(ee, cell.multiply(10).add(region).rename("code"), C.REGION_TASK,
                               C.GRID_CRS, C.GRID_TRANSFORM)
    print(f"started {C.REGION_TASK} -> Drive/{C.DRIVE_FOLDER}/{C.REGION_TASK}.csv  (task {task.id})")


def variables_path(res):
    return TABLES / ("variables.parquet" if res == C.H3_RES else f"variables_r{res}.parquet")


def to_parent(cells, *tables):
    """Relabel the res 6 `cell` column of each table with its res 5 parent's id. Returns the res 5
    cells (cell, h3) and the relabelled tables; every later groupby on `cell` then sums children."""
    import numpy as np
    import pandas as pd

    parents = np.sort(cells.h3_r5.unique())
    lookup = np.empty(cells.cell.max() + 1, dtype="int32")
    lookup[cells.cell.to_numpy()] = np.searchsorted(parents, cells.h3_r5.to_numpy())
    out = []
    for t in tables:
        t = t.copy()
        t["cell"] = lookup[t.cell.to_numpy()]
        out.append(t)
    return pd.DataFrame({"cell": np.arange(len(parents), dtype="int32"), "h3": parents}), out


def cell_region(cells, res=C.H3_RES):
    """Majority MapBiomas region (1-5) per cell and its share of the cell. Cells entirely outside
    every region take the majority region of their neighbours (filled ring by ring)."""
    import pandas as pd

    df = pd.read_csv(REGION_CSV)
    d = pd.DataFrame({"cell": df["code"] // 10, "region": df["code"] % 10, "ha": df["sum"]})
    if res != C.H3_RES:
        _, (d,) = to_parent(pd.read_parquet(TABLES / "cells.parquet"), d)
        d = d.groupby(["cell", "region"], as_index=False).ha.sum()  # one row per child before this
    inside = d[d.region > 0]
    top = inside.sort_values("ha").groupby("cell").tail(1).set_index("cell")
    share = (top.ha / d.groupby("cell").ha.sum()).rename("region_share")
    out = pd.DataFrame({"region": top.region, "region_share": share}).reindex(cells.cell)
    out["region_share"] = out.region_share.fillna(0)
    filled = fill_from_neighbours(cells, out.region.astype("float"), how="mode")
    out["region"] = filled.astype("int8")
    return out


def fill_from_neighbours(cells, values, how):
    """Give each missing value the mean (or mode) of its known H3 neighbours, ring by ring, until
    every cell has one. `values` is indexed by cell; `how` is "mean" or "mode"."""
    import h3
    import pandas as pd

    by_h3 = dict(zip(cells.h3, cells.cell))
    nb = {c: [by_h3[n] for n in h3.grid_ring(h, 1) if n in by_h3] for c, h in zip(cells.cell, cells.h3)}
    vals = values.copy()
    while vals.isna().any():
        todo = vals.index[vals.isna()]
        new = {}
        for c in todo:
            known = [vals[n] for n in nb[c] if pd.notna(vals[n])]
            if known:
                new[c] = (sum(known) / len(known)) if how == "mean" else pd.Series(known).mode().iloc[0]
        if not new:
            raise RuntimeError(f"{len(todo)} cells cannot be filled: no known neighbour")
        for c, v in new.items():
            vals[c] = v
    return vals


def build(res):
    import numpy as np
    import pandas as pd

    cells = pd.read_parquet(TABLES / "cells.parquet")
    sweep = pd.read_parquet(TABLES / "sweep.parquet")
    freq = pd.read_parquet(TABLES / "frequency.parquet")
    if res != C.H3_RES:
        cells, (sweep, freq) = to_parent(cells, sweep, freq)
    idx = cells.cell
    burnable = sweep[sweep.cls.isin(C.BURNABLE_CLASSES)]
    burned = burnable[burnable.month > 0]

    v = pd.DataFrame(index=idx)
    reg = cell_region(cells, res)
    v["region"], v["region_share"] = reg.region, reg.region_share

    # Areas. Burnable = classes of BURNABLE_CLASSES in the year before each fire (D9); only fire on
    # burnable classes enters the variables, the rest is reported by step 02.
    v["burnable_ha"] = (burnable.groupby("cell").ha.sum() / N_YEARS).reindex(idx).fillna(0)
    v["burned_ha"] = burned.groupby("cell").ha.sum().reindex(idx).fillna(0)
    v["no_fire"] = v.burned_ha == 0

    # 1. Burn rate, % of burnable area per year (Boulanger et al. 2014, p. 366; Erni et al. 2020, p. 8).
    v["rate"] = np.where(v.burnable_ha > 0, v.burned_ha / N_YEARS / v.burnable_ha * 100, 0.0)

    # 2. Interannual variability, CV of the yearly burned area (Naval-Fernández et al. 2025, pp. 6-7).
    yearly = burned.groupby(["cell", "year"]).ha.sum().unstack(fill_value=0).reindex(
        index=idx, columns=C.FIRE_YEARS, fill_value=0)
    mean = yearly.mean(axis=1)
    v["cv"] = np.where(mean > 0, yearly.std(axis=1, ddof=0) / mean.where(mean > 0, 1), CV_NO_FIRE)

    # 3. Recurrence: 99th quantile of the times each hectare of the cell burned, 0 included
    # (Segura-Garcia et al. 2025, "Methods" (b)(i); no smoothing of the ECDF here). The 0 area is the
    # mean burnable area minus the area burned at least once (D8, D9).
    k = freq.pivot_table(index="cell", columns="k", values="ha", aggfunc="sum").reindex(idx).fillna(0)
    k[0] = (v.burnable_ha - k.sum(axis=1)).clip(lower=0)
    k = k[sorted(k.columns)]
    cum = k.cumsum(axis=1).div(k.sum(axis=1).where(k.sum(axis=1) > 0, 1), axis=0)
    v["recurrence"] = (cum < RECURRENCE_Q).sum(axis=1).map(lambda i: k.columns[min(i, len(k.columns) - 1)])
    v.loc[k.sum(axis=1) == 0, "recurrence"] = 0

    # 4. Peak of the fire season and 5. its length. The fire-year of each cell is the 12 months
    # around its month of highest burned area (that month in position 6); the peak is the month
    # where half the burned area is reached (Segura-Garcia et al. 2025). Length = 2 standard
    # deviations of the month in that fire-year (Cattau et al. 2022, Table 1, p. 4, there in Julian
    # days). The peak is circular, so it enters step 07 as sine and cosine.
    monthly = burned.groupby(["cell", "month"]).ha.sum().unstack(fill_value=0).reindex(
        index=idx, columns=range(1, 13), fill_value=0).to_numpy()
    top = monthly.argmax(axis=1)                                    # 0-based month of the maximum
    order = (top[:, None] + np.arange(-5, 7)[None, :]) % 12         # calendar index per position
    ordered = np.take_along_axis(monthly, order, axis=1)
    tot = ordered.sum(axis=1)
    has = tot > 0
    pos = np.argmax(np.cumsum(ordered, axis=1) >= 0.5 * tot[:, None], axis=1)
    peak = np.where(has, np.take_along_axis(order, pos[:, None], axis=1)[:, 0] + 1, np.nan)
    p = np.arange(1, 13)
    mu = (ordered * p).sum(axis=1) / np.where(has, tot, 1)
    sd = np.sqrt((ordered * (p - mu[:, None]) ** 2).sum(axis=1) / np.where(has, tot, 1))
    ang = 2 * np.pi * (peak - 1) / 12
    v["peak_sin"], v["peak_cos"] = np.sin(ang), np.cos(ang)
    v["season_len"] = np.where(has, 2 * sd, np.nan)
    v["season_imputed"] = ~has
    for col in ("peak_sin", "peak_cos", "season_len"):
        v[col] = fill_from_neighbours(cells, v[col].astype("float"), how="mean").to_numpy()
    v["peak_month"] = (np.round(np.arctan2(v.peak_sin, v.peak_cos) / (2 * np.pi) * 12) % 12 + 1).astype("int8")

    # 6. Size: share of the burned area in scars of 500 ha or more (Galizia et al. 2023, p. 3, by
    # number of fires over 100 ha; here by area). No fire: 0, the smallest size (Segura-Garcia).
    large = burned[burned["size"] >= LARGE_SIZE_CLASS].groupby("cell").ha.sum().reindex(idx).fillna(0)
    v["large_share"] = np.where(v.burned_ha > 0, large / v.burned_ha.where(v.burned_ha > 0, 1), 0.0)

    # Composition of the burnable area by family, with the cell's region (Boulanger et al. 2014,
    # p. 368: fuel composition enters the clustering with weight 0.2; D11).
    comp = burnable.groupby(["cell", "cls"]).ha.sum().reset_index()
    comp["region"] = comp.cell.map(v.region)
    common = {}
    for (r, c), f in C.FAMILY_BY_REGION_CLASS.items():
        common.setdefault(c, []).append(f)
    fallback = {c: max(set(fs), key=fs.count) for c, fs in common.items()}
    pair = list(zip(comp.region, comp.cls))
    comp["family"] = [C.FAMILY_BY_REGION_CLASS.get(p, fallback.get(p[1])) for p in pair]
    comp["fallback"] = [p not in C.FAMILY_BY_REGION_CLASS for p in pair]
    fam = comp.pivot_table(index="cell", columns="family", values="ha", aggfunc="sum").reindex(
        index=idx, columns=C.FAMILIES).fillna(0)
    fam_tot = fam.sum(axis=1)
    for f in C.FAMILIES:
        v[f"fam_{f}"] = np.where(fam_tot > 0, fam[f] / fam_tot.where(fam_tot > 0, 1), 0.0)

    v = v.reset_index()
    v["h3"] = cells.h3.to_numpy()
    out = variables_path(res)
    v.to_parquet(out, index=False)
    print(f"wrote {out.relative_to(REPO)}  {len(v):,} cells")
    unmapped = comp[comp.family.isna()].ha.sum()
    fb = comp[comp.fallback & comp.family.notna()]
    print(f"  info  family by fallback (region-class pair not in the fire team's remap): "
          f"{fb.ha.sum() / N_YEARS / 1e6:.3f} Mha per year, classes {sorted(fb.cls.unique())}; "
          f"with no family at all {unmapped / N_YEARS:,.0f} ha per year")
    check(res, burned_total=burned.ha.sum(), burnable_total=burnable.ha.sum() / N_YEARS)


def check(res, burned_total=None, burnable_total=None):
    import pandas as pd

    v = pd.read_parquet(variables_path(res))
    if burned_total is None:
        sweep = pd.read_parquet(TABLES / "sweep.parquet", columns=["cls", "month", "ha"])
        b = sweep[sweep.cls.isin(C.BURNABLE_CLASSES)]
        burned_total, burnable_total = b[b.month > 0].ha.sum(), b.ha.sum() / N_YEARS
    model = ["rate", "cv", "recurrence", "peak_sin", "peak_cos", "season_len", "large_share"] + \
        [f"fam_{f}" for f in C.FAMILIES]
    results = []
    gaps = int(v[model].isna().sum().sum())
    results.append((f"no gaps in the {len(model)} clustering columns: {gaps} missing", gaps == 0))
    d = abs(v.burned_ha.sum() - burned_total) / burned_total
    results.append((f"burned on burnable classes, cells vs tables: {v.burned_ha.sum() / 1e6:.3f} vs "
                    f"{burned_total / 1e6:.3f} Mha", d < 1e-9))
    d = abs(v.burnable_ha.sum() - burnable_total) / burnable_total
    results.append((f"mean burnable area, cells vs tables: {v.burnable_ha.sum() / 1e6:.3f} vs "
                    f"{burnable_total / 1e6:.3f} Mha", d < 1e-9))
    fam = v[[f"fam_{f}" for f in C.FAMILIES]].sum(axis=1)
    bad = int(((fam - 1).abs() > 1e-9)[v.burnable_ha > 0].sum())
    results.append((f"family shares add to 1 where there is burnable area: {bad} cells off", bad == 0))
    rng = (v.rate.between(0, 100) & v.large_share.between(0, 1) & v.recurrence.between(0, N_YEARS)
           & v.season_len.between(0, 12) & v.region.between(1, 5)).all()
    results.append(("values in range (rate 0-100, shares 0-1, recurrence 0-27, length 0-12, region 1-5)", rng))

    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    nat = v.burned_ha.sum() / N_YEARS / v.burnable_ha.sum() * 100
    print(f"  info  national burn rate {nat:.3f} % of burnable area per year")
    print(f"  info  cells with no fire {v.no_fire.sum():,}; season imputed {v.season_imputed.sum():,}; "
          f"region share < 0.9 in {(v.region_share < 0.9).sum():,} cells")
    print("  info  peak month by region (cells with fire), most common three:")
    for r, g in v[~v.no_fire].groupby("region"):
        top3 = g.peak_month.value_counts().head(3)
        print(f"        {C.REGION_NAMES[r]:<6} " + ", ".join(f"{m}: {n:,}" for m, n in top3.items()))
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--export", action="store_true", help="launch the region-per-cell task")
    ap.add_argument("--status", action="store_true", help="state of that task")
    ap.add_argument("--fetch", action="store_true", help="download its CSV from Drive")
    ap.add_argument("--build", action="store_true", help="compute the variables, then --check (default)")
    ap.add_argument("--check", action="store_true", help="controls on variables.parquet")
    ap.add_argument("--force", action="store_true", help="--export even if the task already exists")
    ap.add_argument("--res", type=int, choices=[5, C.H3_RES], default=C.H3_RES,
                    help="resolution of --build and --check (5 = children summed into parents)")
    args = ap.parse_args()
    if args.export:
        export(args.force)
    if args.status:
        print_status(C.REGION_TASK)
    if args.fetch:
        fetch_csvs([f"{C.REGION_TASK}.csv"], REGION_CSV.parent)
    if args.check:
        check(args.res)
    elif args.build or not (args.export or args.status or args.fetch):
        build(args.res)


if __name__ == "__main__":
    main()
