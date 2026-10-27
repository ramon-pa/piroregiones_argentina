#!/usr/bin/env python
"""workflow/07-regions.py: the pyroregions, contiguous regions of H3 res 5 cells with a similar
fire regime, by REDCAP (full order, Ward linkage; Boulanger et al. 2014) with a minimum area.

Reads variables_r5.parquet (step 06 with --res 5) and the res 6 grid. Each res 5 cell is the union
of its seven res 6 children (decision D1), so two cells are neighbours when any of their children
share an edge. Cells with less than C.MIN_BURNABLE_SHARE of burnable area stay out of the
clustering and join their most common neighbouring region afterwards. Components cut off from the
rest (Tierra del Fuego, cells isolated by the excluded ones) are linked to their nearest cell so the
graph is connected, which REDCAP needs: our choice, not a paper's. Rate and recurrence enter as
logarithms (C.LOG_RATE_OFFSET); then the seven fire variables and the six family shares are
standardized, the shares weighted by C.COMPOSITION_WEIGHT (D12), and REDCAP gets them raw so the
weights survive (pygeoda standardizes by default).

  --build  (default) k = C.REGIONS_K regions of at least C.MIN_REGION_KM2, to C.REGIONS_DIR:
             regions_r5_k<k>.parquet           cell, h3, region (numbered north to south), clustered
             regions_r5_k<k>_polygons.parquet  one polygon per region (GeoParquet)
             summary_r5_k<k>.csv               area and regime of each region, to name them
           the map to outputs/07-regions_r5_k<k>.png, then the controls.
  --k N [N ...]     other k for --build, one set of outputs each.
  --force           add the pieces of C.FORCED_SPLIT_POINTS, taken from the k = C.FORCED_SPLIT_K level of
                    the same tree (decision D14); adds _forced to the names.
  --log-offset X    another offset for the log of the rate (sensitivity); adds _off<X> to the names.
  --curve  between-to-total sum of squares for k = 2..30, one process per k, to k_curve_r5.csv,
           and the region of every cell at each k (numbered as in --build) to labels_r5.parquet.

Doc: docs/07-regions.md. Run from the repo root:

    uv run python workflow/07-regions.py --build
    uv run python workflow/07-regions.py --build --k 10 12 15 20
    uv run python workflow/07-regions.py --curve
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

TABLES = REPO / C.TABLES_DIR
OUT = REPO / C.REGIONS_DIR
FIGS = REPO / "outputs"
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
N_YEARS = len(C.FIRE_YEARS)
FIRE_VARS = ["rate", "cv", "recurrence", "peak_sin", "peak_cos", "season_len", "large_share"]
FAM_VARS = [f"fam_{f}" for f in C.FAMILIES]
CURVE_K = range(2, 31)
CURVE_WORKERS = 3
MONTHS = "ene feb mar abr may jun jul ago sep oct nov dic".split()
# Categorical palette of the dataviz skill (references/palette.md, light mode). Regions get colours
# by graph colouring, so neighbours differ; the number on the map, not the colour, names a region.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def load():
    """Res 5 variables, res 6 grid with each child's parent id, the area of each res 5 cell, and
    whether it enters the clustering (burnable share at least C.MIN_BURNABLE_SHARE)."""
    import geopandas as gpd
    import numpy as np
    import pandas as pd

    v = pd.read_parquet(TABLES / f"variables_r{C.REGIONS_RES}.parquet").rename(columns={"region": "region_mb"})
    g = gpd.read_parquet(GRID)
    g["parent"] = np.searchsorted(v.h3.to_numpy(), g.h3_r5.to_numpy())
    assert (v.h3.to_numpy()[g.parent] == g.h3_r5.to_numpy()).all(), "res 6 parent not in variables_r5"
    v["area_km2"] = g.groupby("parent").area_km2.sum().reindex(v.cell).to_numpy()
    v["burnable_share"] = v.burnable_ha / (v.area_km2 * 100)
    v["clustered"] = v.burnable_share >= C.MIN_BURNABLE_SHARE
    return v, g


def adjacency(v, g):
    """Rook neighbours of the res 5 cells, from their res 6 children: {cell: set of cells}."""
    import h3

    parent = dict(zip(g.h3, g.parent))
    nb = {c: set() for c in v.cell}
    for h, p in parent.items():
        for n in h3.grid_ring(h, 1):
            q = parent.get(n)
            if q is not None and q != p:
                nb[p].add(q)
    return nb


def connected(nb, members, v):
    """The graph `nb` restricted to `members`, with each cut-off component linked to the nearest
    member outside it (great-circle distance between cell centres) until it is one piece. Returns the
    graph and the added links (cell, cell, km)."""
    import h3
    import numpy as np

    members = set(members)
    sub = {c: nb[c] & members for c in members}
    ll = np.radians(np.array([h3.cell_to_latlng(h) for h in v.h3]))  # indexed by cell id
    links = []
    while True:
        comps = components(sub)
        if len(comps) == 1:
            return sub, links
        island = np.array(sorted(min(comps, key=len)))
        rest = np.array(sorted(members - set(island)))
        la, lb = ll[island][:, None, :], ll[rest][None, :, :]
        hav = (np.sin((lb[..., 0] - la[..., 0]) / 2) ** 2
               + np.cos(la[..., 0]) * np.cos(lb[..., 0]) * np.sin((lb[..., 1] - la[..., 1]) / 2) ** 2)
        i, j = np.unravel_index(np.argmin(hav), hav.shape)
        a, b = int(island[i]), int(rest[j])
        sub[a].add(b)
        sub[b].add(a)
        links.append((a, b, 2 * 6371.0 * np.arcsin(np.sqrt(hav[i, j]))))


def components(nb, members=None):
    """Connected components of the graph `nb`, restricted to `members` if given."""
    members = set(nb) if members is None else set(members)
    seen, comps = set(), []
    for start in members:
        if start in seen:
            continue
        comp, stack = {start}, [start]
        while stack:
            for n in nb[stack.pop()]:
                if n in members and n not in comp:
                    comp.add(n)
                    stack.append(n)
        seen |= comp
        comps.append(comp)
    return comps


def weights(nb, ids):
    """pygeoda Weight from the neighbour sets, through a GAL file (pygeoda has no other way in)."""
    import pygeoda

    with tempfile.NamedTemporaryFile("w", suffix=".gal", delete=False) as f:
        f.write(f"0 {len(ids)} cells cell\n")
        for c in ids:
            f.write(f"{c} {len(nb[c])}\n{' '.join(str(n) for n in sorted(nb[c]))}\n")
    return pygeoda.read_gal(f.name, [str(c) for c in ids])


def design(v, offset):
    """The clustering matrix of the given cells: log rate and recurrence, z-scores, the family
    shares weighted by C.COMPOSITION_WEIGHT."""
    import numpy as np

    X = v[FIRE_VARS + FAM_VARS].astype("float")
    X["rate"] = np.log10(X.rate + offset)
    X["recurrence"] = np.log1p(X.recurrence)
    X = (X - X.mean()) / X.std(ddof=0).where(lambda s: s > 0, 1)
    X[FAM_VARS] *= C.COMPOSITION_WEIGHT
    return X


def redcap(k, w, X, area):
    import pygeoda

    # One thread: with pygeoda's default threads, runs died at random k with a C++ length_error,
    # even one k per process (2026-10-27); single-threaded, k = 5..30 ran with the same ratios.
    r = pygeoda.redcap(k, w, X, method="fullorder-wardlinkage", bound_variable=area,
                       min_bound=C.MIN_REGION_KM2, scale_method="raw", cpu_threads=1)
    return r["Clusters"], r["The ratio of between to total sum of squares"]


def cluster(v, nb_raw, k, offset):
    """REDCAP on the clustered cells. Returns their labels (indexed like v[v.clustered]), the
    between/total ratio, the graph used and its links."""
    import pandas as pd

    kept = v[v.clustered]
    nb_kept, links = connected(nb_raw, kept.cell, v)
    labels, ratio = redcap(k, weights(nb_kept, list(kept.cell)), design(kept, offset), kept.area_km2)
    return pd.Series(labels, index=kept.index), ratio, nb_kept, links


def assign_excluded(v, labels, nb_all):
    """Region of each cell: REDCAP's for the clustered cells; for the others, the most common region
    of their already assigned neighbours, ring by ring (ties to the lowest label)."""
    import pandas as pd

    lab = pd.Series(pd.NA, index=v.cell, dtype="Int64")
    lab[v.cell[labels.index]] = labels.to_numpy()
    while lab.isna().any():
        new = {}
        for c in lab.index[lab.isna()]:
            known = [lab[n] for n in nb_all[c] if pd.notna(lab[n])]
            if known:
                new[c] = pd.Series(known).mode().min()
        if not new:
            raise RuntimeError(f"{int(lab.isna().sum())} cells cannot be assigned: no assigned neighbour")
        for c, r in new.items():
            lab[c] = r
    return lab.to_numpy()


def number_north_to_south(v, labels):
    """Renumber the regions 1..k by the latitude of their area-weighted centre, north first."""
    import h3
    import pandas as pd

    lat = pd.Series([h3.cell_to_latlng(h)[0] for h in v.h3], index=v.index)
    d = pd.DataFrame({"lab": labels, "lat": lat * v.area_km2, "a": v.area_km2}, index=v.index)
    centre = d.groupby("lab").lat.sum() / d.groupby("lab").a.sum()
    order = {lab: i + 1 for i, lab in enumerate(centre.sort_values(ascending=False).index)}
    return pd.Series(labels, index=v.index).map(order).astype("int16")


def summary(v, poly):
    """Area and regime of each region from its cells' variables, weighted by area. The burn rate is
    exact (summed areas); the other columns are weighted means of cell values, a first look."""
    import numpy as np
    import pandas as pd

    pt = poly.set_index("region").geometry.representative_point()
    rows = []
    for r, d in v.groupby("region"):
        bh, fh = d.burnable_ha, d.burned_ha
        fw = fh if fh.sum() > 0 else bh
        ang = np.arctan2((d.peak_sin * fw).sum(), (d.peak_cos * fw).sum())
        fam = {f: (d[f"fam_{f}"] * bh).sum() for f in C.FAMILIES}
        reg = d.groupby("region_mb").area_km2.sum()
        rows.append({
            "region": r, "cells": len(d), "area_km2": round(d.area_km2.sum()),
            "lon": round(pt[r].x, 2), "lat": round(pt[r].y, 2),
            "burnable_share": bh.sum() / (d.area_km2.sum() * 100),
            "rate_pct": fh.sum() / N_YEARS / bh.sum() * 100 if bh.sum() > 0 else 0.0,
            "cv": np.average(d.cv, weights=bh) if bh.sum() > 0 else np.nan,
            "recurrence": np.average(d.recurrence, weights=bh) if bh.sum() > 0 else np.nan,
            "peak": MONTHS[int(round(ang / (2 * np.pi) * 12)) % 12],
            "season_len": np.average(d.season_len, weights=fw),
            "large_share": (d.large_share * fh).sum() / fh.sum() if fh.sum() > 0 else 0.0,
            "family": max(fam, key=fam.get),
            "family_share": max(fam.values()) / bh.sum() if bh.sum() > 0 else np.nan,
            "mapbiomas_region": C.REGION_NAMES[reg.idxmax()],
            "no_fire_area_share": d.area_km2[d.no_fire].sum() / d.area_km2.sum(),
            "excluded_area_share": d.area_km2[~d.clustered].sum() / d.area_km2.sum(),
        })
    return pd.DataFrame(rows)


def ss_ratio(v, offset):
    """Between-to-total sum of squares of the final regions, over the clustered cells."""
    X = design(v[v.clustered], offset)
    lab = v.region[v.clustered]
    within = sum(((X[lab == r] - X[lab == r].mean()) ** 2).sum().sum() for r in lab.unique())
    return 1 - within / float((X ** 2).sum().sum())


def force_splits(v, nb_raw, nb_all, offset):
    """Give each piece of C.FORCED_SPLIT_POINTS, taken from the k = C.FORCED_SPLIT_K level, a region
    of its own. Each piece must lie inside one region of the current map."""
    import h3

    labels, _, _, _ = cluster(v, nb_raw, C.FORCED_SPLIT_K, offset)
    deep = assign_excluded(v, labels, nb_all)
    region = v.region.to_numpy().copy()
    for name, (lat, lon) in C.FORCED_SPLIT_POINTS.items():
        at = (v.h3 == h3.latlng_to_cell(lat, lon, C.REGIONS_RES)).to_numpy()
        assert at.sum() == 1, f"{name}: the point is in no res {C.REGIONS_RES} cell of the grid"
        piece = deep == deep[at][0]
        parents = set(region[piece])
        assert len(parents) == 1, f"{name}: the piece spans regions {parents}"
        region[piece] = region.max() + 1
        print(f"  info  forced: {name}, {v.area_km2[piece].sum():,.0f} km² out of region {parents.pop()}")
    return region


def polygons(v, g):
    """One polygon per region, unioned on a 1e-7 degree (~1 cm) precision grid: the res 6 hexagons
    are not exactly noded, and a plain union leaves sliver seams across the regions."""
    import geopandas as gpd
    import shapely

    g = g.assign(region=v.region.to_numpy()[g.parent])
    parts = g.groupby("region").geometry.apply(lambda s: shapely.union_all(s.values, grid_size=1e-7))
    poly = gpd.GeoDataFrame({"region": parts.index}, geometry=list(parts), crs=g.crs)
    poly["area_km2"] = v.groupby("region").area_km2.sum().reindex(poly.region).to_numpy()
    return poly


def draw(poly, v, nb, title, path):
    """The map. Neighbouring regions come from the cell graph, not from the polygons, whose shared
    edges are not exactly noded."""
    import matplotlib.pyplot as plt

    region = dict(zip(v.cell, v.region))
    adj = {r: set() for r in poly.region}
    for c, ns in nb.items():
        adj[region[c]].update(region[n] for n in ns if region[n] != region[c])
    colour = {}
    for r in sorted(adj, key=lambda r: -len(adj[r])):  # greedy colouring, most neighbours first
        used = {colour.get(n) for n in adj[r]}
        colour[r] = next(c for c in PALETTE if c not in used)
    fig, ax = plt.subplots(figsize=(6, 11))
    poly.plot(ax=ax, color=[colour[r] for r in poly.region], edgecolor="white", linewidth=0.8, alpha=0.85)
    for _, p in poly.iterrows():
        pt = p.geometry.representative_point()
        ax.annotate(str(p.region), (pt.x, pt.y), ha="center", va="center", fontsize=9,
                    fontweight="bold", color="#1a1a19",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_axis_off()
    FIGS.mkdir(exist_ok=True)
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def build(k, offset, force=False):
    import pandas as pd

    v, g = load()
    nb_raw = adjacency(v, g)
    nb_all, links_all = connected(nb_raw, v.cell, v)
    print(f"  info  clustered {v.clustered.sum():,} cells; left out (burnable < "
          f"{C.MIN_BURNABLE_SHARE:.0%}) {(~v.clustered).sum():,} cells, {v.area_km2[~v.clustered].sum():,.0f} km²")
    t = time.time()
    labels, ratio, _, links = cluster(v, nb_raw, k, offset)
    for a, b, km in links:
        print(f"  info  linked: cell {a} -> {b} ({km:.0f} km between centres)")
    print(f"redcap k={k}: {time.time() - t:.1f} s, between/total sum of squares {ratio:.3f}")
    v["region"] = number_north_to_south(v, assign_excluded(v, labels, nb_all))
    n_regions = k
    if force:
        v["region"] = number_north_to_south(v, force_splits(v, nb_raw, nb_all, offset))
        n_regions = k + len(C.FORCED_SPLIT_POINTS)
        # ss_ratio, not pygeoda's ratio: the two differ (k = 12: 0.523 against 0.469, 2026-10-27; not
        # explained yet), so compare forced and unforced maps with ss_ratio only.
        print(f"with the forced pieces: {n_regions} regions, between/total (ss_ratio) {ss_ratio(v, offset):.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    tag = (f"r{C.REGIONS_RES}_k{k}" + ("_forced" if force else "")
           + ("" if offset == C.LOG_RATE_OFFSET else f"_off{offset:g}"))
    v[["cell", "h3", "region", "clustered"]].to_parquet(OUT / f"regions_{tag}.parquet", index=False)
    poly = polygons(v, g)
    poly.to_parquet(OUT / f"regions_{tag}_polygons.parquet", index=False)
    s = summary(v, poly)
    s.to_csv(OUT / f"summary_{tag}.csv", index=False, float_format="%.4g")
    fig = FIGS / f"07-regions_{tag}.png"
    km2 = f"{C.MIN_REGION_KM2:,.0f}".replace(",", ".")
    extra = f" + {len(C.FORCED_SPLIT_POINTS)} piezas patagónicas" if force else ""
    draw(poly, v, nb_all, f"Pirorregiones de Argentina, borrador\nH3 res 5, REDCAP Ward, k = {k}{extra}, "
         f"mínimo {km2} km²", fig)
    for p in (OUT / f"regions_{tag}.parquet", OUT / f"regions_{tag}_polygons.parquet",
              OUT / f"summary_{tag}.csv", fig):
        print(f"wrote {p.relative_to(REPO)}")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(s.round(3).to_string(index=False))
    check(v, nb_all, links + links_all, n_regions)


def check(v, nb, links, k):
    """Controls on the final regions. `nb` is the whole graph with its island links; `links` are all
    added links, to report regions that hold together only through one."""
    graph = {c: set(s) for c, s in nb.items()}
    for a, b, _ in links:
        graph[a].add(b)
        graph[b].add(a)
    results = []
    n = v.region.nunique()
    results.append((f"every cell has a region, {n} regions (k = {k})",
                    v.region.notna().all() and n == k))
    area = v.groupby("region").area_km2.sum()
    results.append((f"smallest region {area.min():,.0f} km² >= {C.MIN_REGION_KM2:,.0f} km²",
                    area.min() >= C.MIN_REGION_KM2))
    split = [r for r, d in v.groupby("region") if len(components(graph, d.cell)) > 1]
    results.append((f"every region is one connected piece (links included): {split or 'all'}", not split))
    plain = {c: set(s) for c, s in graph.items()}
    for a, b, _ in links:
        plain[a].discard(b)
        plain[b].discard(a)
    by_link = [r for r, d in v.groupby("region") if len(components(plain, d.cell)) > 1]
    print(f"  info  regions that hold together only through a link: {by_link or 'none'}")
    total = abs(v.area_km2.sum() - area.sum())
    results.append((f"region areas add up to the grid: {area.sum():,.0f} km²", total < 1e-6))
    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def ratio_for(k, offset):
    """Between-to-total sum of squares and final regions of one run. Run in a fresh process per k:
    in one process, pygeoda's memory grew run after run until the system killed it (exit 137 after
    k = 21)."""
    v, g = load()
    nb_raw = adjacency(v, g)
    nb_all, _ = connected(nb_raw, v.cell, v)
    t = time.time()
    labels, ratio, _, _ = cluster(v, nb_raw, k, offset)
    region = number_north_to_south(v, assign_excluded(v, labels, nb_all))
    return k, ratio, time.time() - t, region.to_numpy()


def curve(offset):
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor

    import pandas as pd

    ctx = multiprocessing.get_context("spawn")
    v, _ = load()
    rows, labels = [], pd.DataFrame({"cell": v.cell, "h3": v.h3})
    with ProcessPoolExecutor(CURVE_WORKERS, mp_context=ctx, max_tasks_per_child=1) as pool:
        for k, ratio, sec, region in pool.map(ratio_for, CURVE_K, [offset] * len(CURVE_K)):
            rows.append({"k": k, "between_total": ratio, "seconds": sec})
            labels[f"k{k}"] = region
            print(f"k {k:>2}  between/total {ratio:.3f}  {sec:.1f} s", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"k_curve_r{C.REGIONS_RES}.csv"
    pd.DataFrame(rows).to_csv(path, index=False, float_format="%.4f")
    labels.to_parquet(OUT / f"labels_r{C.REGIONS_RES}.parquet", index=False)
    print(f"wrote {path.relative_to(REPO)}, labels_r{C.REGIONS_RES}.parquet")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", action="store_true", help="regions, polygons, summary, map, controls (default)")
    ap.add_argument("--curve", action="store_true", help="between/total sum of squares for k = 5..30")
    ap.add_argument("--k", type=int, nargs="+", default=[C.REGIONS_K], help="number(s) of regions for --build")
    ap.add_argument("--log-offset", type=float, default=C.LOG_RATE_OFFSET, help="offset of log10(rate + offset)")
    ap.add_argument("--force", action="store_true", help="add the forced pieces of decision D14")
    args = ap.parse_args()
    if args.curve:
        curve(args.log_offset)
    if args.build or not args.curve:
        for k in args.k:
            build(k, args.log_offset, args.force)


if __name__ == "__main__":
    main()
