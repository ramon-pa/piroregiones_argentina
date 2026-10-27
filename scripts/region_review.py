#!/usr/bin/env python
"""scripts/region_review.py: looks at the step 07 regions, to decide how many and which to keep.
Local only; reads the step 05, 06 and 07 outputs.

  --burned-once K  map of the share of burnable area burned at least once in 1999-2025, per res 6
                   hexagon, with the borders of the k = K regions on top, to
                   outputs/review-burned_once_k<K>.png. Burned at least once = frequency >= 1 of
                   frequency_burned_v2 (step 04): the same thing the published accumulated_burned
                   product maps, so no new GEE run. Denominator: mean burnable area (D9).
  --splits KMAX    the tree of splits k -> k+1 for k = 2..KMAX-1, from labels_r5.parquet (07 --curve):
                   which region splits, how much of the total sum of squares the split explains, and
                   the variables that set the two parts apart most. To splits_r5.csv.

Run from the repo root:

    uv run python scripts/region_review.py --burned-once 12
    uv run python scripts/region_review.py --splits 20
"""
import argparse
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

TABLES = REPO / C.TABLES_DIR
REGIONS = REPO / C.REGIONS_DIR
FIGS = REPO / "outputs"
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
# Classes of the share burned at least once (%), and a one-hue sequential ramp (dataviz skill,
# references/palette.md, blue steps 100 to 700); never burned in grey.
BINS = [0, 1, 5, 20, 50, 100]
RAMP = ["#ecebe6", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
LABELS = ["nunca", "hasta 1 %", "1 a 5 %", "5 a 20 %", "20 a 50 %", "más de 50 %"]
VAR_NAMES = {"rate": "tasa (log)", "cv": "variabilidad", "recurrence": "recurrencia (log)",
             "peak_sin": "pico (sen)", "peak_cos": "pico (cos)", "season_len": "duración",
             "large_share": "cicatrices grandes"}


def step07():
    spec = importlib.util.spec_from_file_location("step07", REPO / "workflow" / "07-regions.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def burned_once(k):
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from matplotlib.patches import Patch

    g = gpd.read_parquet(GRID)
    v = pd.read_parquet(TABLES / "variables.parquet").set_index("cell")
    f = pd.read_parquet(TABLES / "frequency.parquet")
    once = f.groupby("cell").ha.sum().reindex(g.cell).fillna(0).to_numpy()
    burnable = v.burnable_ha.reindex(g.cell).to_numpy()
    share = np.where(burnable > 0, np.clip(once / np.where(burnable > 0, burnable, 1) * 100, 0, 100), 0)
    g["cls"] = np.where(once <= 0, 0, np.digitize(share, BINS[1:-1], right=True) + 1)
    print(f"  info  burned at least once: {once.sum() / 1e6:.3f} Mha of {np.nansum(burnable) / 1e6:.3f} Mha "
          f"burnable ({once.sum() / np.nansum(burnable):.1%}); hexagons never burned {(once <= 0).sum():,}; "
          f"share above 100 % clipped in {(once > burnable).sum():,}")
    poly = gpd.read_parquet(REGIONS / f"regions_r{C.REGIONS_RES}_k{k}_polygons.parquet")
    fig, ax = plt.subplots(figsize=(7, 12))
    g.plot(ax=ax, color=[RAMP[c] for c in g.cls], linewidth=0)
    poly.boundary.plot(ax=ax, color="#1a1a19", linewidth=1.1)
    for _, p in poly.iterrows():
        pt = p.geometry.representative_point()
        ax.annotate(str(p.region), (pt.x, pt.y), ha="center", va="center", fontsize=10, fontweight="bold",
                    color="#1a1a19", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.legend(handles=[Patch(color=c, label=lab) for c, lab in zip(RAMP, LABELS)], loc="lower right",
              title="área quemable quemada\nal menos una vez, 1999 a 2025", fontsize=10, title_fontsize=10,
              frameon=False)
    ax.set_title(f"Quemado al menos una vez por hexágono (~30 km²)\ny bordes de las {k} pirorregiones",
                 fontsize=12, loc="left")
    ax.set_axis_off()
    FIGS.mkdir(exist_ok=True)
    path = FIGS / f"review-burned_once_k{k}.png"
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"wrote {path.relative_to(REPO)}")


def splits(kmax):
    import numpy as np
    import pandas as pd

    m = step07()
    v, _ = m.load()
    lab = pd.read_parquet(REGIONS / f"labels_r{C.REGIONS_RES}.parquet")
    assert (lab.cell.to_numpy() == v.cell.to_numpy()).all()
    kept = v.clustered.to_numpy()
    X = m.design(v[kept], C.LOG_RATE_OFFSET)
    fire = X[m.FIRE_VARS]
    total = float((X ** 2).sum().sum())  # X is centred: total sum of squares
    rows = []
    for k in range(2, kmax):
        a, b = lab[f"k{k}"].to_numpy()[kept], lab[f"k{k + 1}"].to_numpy()[kept]
        t = pd.crosstab(a, b)
        nested = bool(((t > 0).sum(axis=0) == 1).all())
        parent = t.index[(t > 0).sum(axis=1) > 1]
        if len(parent) != 1 or not nested:
            rows.append({"k": k + 1, "nested": nested})
            continue
        p = parent[0]
        kids = t.columns[t.loc[p] > 0]
        inside = a == p
        sub = X[inside]
        gain = float(((sub - sub.mean()) ** 2).sum().sum()
                     - sum(((X[b == c] - X[b == c].mean()) ** 2).sum().sum() for c in kids))
        c1, c2 = kids[:2]
        d = (fire[b == c1].mean() - fire[b == c2].mean()) / fire[inside].std(ddof=0).where(lambda s: s > 0, 1)
        top = d.abs().sort_values(ascending=False).head(3)
        area = v.area_km2[kept]
        rows.append({"k": k + 1, "nested": True, "parent_at_k": int(p), "children": " y ".join(str(int(c)) for c in kids),
                     "parent_km2": round(area[inside].sum()), "small_child_km2": round(min(area[b == c].sum() for c in kids)),
                     "gain_pct_total": gain / total * 100,
                     "top_vars": "; ".join(f"{VAR_NAMES[n]} {d[n]:+.2f}" for n in top.index)})
    out = pd.DataFrame(rows)
    path = REGIONS / f"splits_r{C.REGIONS_RES}.csv"
    out.to_csv(path, index=False, float_format="%.3f")
    with pd.option_context("display.width", 250, "display.max_colwidth", 90):
        print(out.round(2).to_string(index=False))
    print(f"wrote {path.relative_to(REPO)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--burned-once", type=int, metavar="K", help="map of burned at least once with k = K borders")
    ap.add_argument("--splits", type=int, metavar="KMAX", help="tree of splits up to k = KMAX")
    args = ap.parse_args()
    if args.burned_once:
        burned_once(args.burned_once)
    if args.splits:
        splits(args.splits)


if __name__ == "__main__":
    main()
