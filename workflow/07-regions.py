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
  --force           add the pieces of C.FORCED_SPLIT_POINTS, each taken from its own deeper k level of
                    the same tree (decisions D14 and D15); adds _forced to the names.
  --log-offset X    another offset for the log of the rate (sensitivity); adds _off<X> to the names.
  --team-edits      with --force, the edits the MapBiomas team asked for (D16): one forest region, no
                    branch one hexagon wide, map clipped to the country; adds _edited.
  --pool            the variables of 06-variables.py --pool (sensitivity, 2026-10-28); adds _pool.
  --cover-by-fire   candidate (2026-10-28): family weight by the fire each cell saw, up to
                    C.COVER_BY_FIRE_TOP, and the pieces of C.COVER_BY_FIRE_FORCED with --force;
                    names from C.PYROREGION_NAMES_BY_FIRE; adds _coverfire.
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
# One colour per region (Ramón, 2026-10-27), so the legend table in the map names each one. Named
# regions take theirs from C.PYROREGION_NAMES; the others, in order, from the categorical palette
# of the dataviz skill (references/palette.md, light mode) and ours after it. Up to 16 regions.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948",
           "#7fc6e8", "#a0522d", "#b8d36b", "#9e9ac8", "#f2c6a0", "#4f7f8f", "#c9a227", "#d4a5d9"]
# Legend of the map: provinces holding at least this share of a region, three at most, read from the
# places file of step 09 when it exists.
LEGEND_MIN_SHARE = 10


def load(pool=False):
    """Res 5 variables (with pool, those of 06-variables.py --pool), res 6 grid with each child's parent id, the area of each res 5 cell, and
    whether it enters the clustering (burnable share at least C.MIN_BURNABLE_SHARE)."""
    import geopandas as gpd
    import numpy as np
    import pandas as pd

    name = f"variables_r{C.REGIONS_RES}{'_pool' if pool else ''}.parquet"
    v = pd.read_parquet(TABLES / name).rename(columns={"region": "region_mb"})
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


def design(v, offset, cover_w=None):
    """The clustering matrix of the given cells: log rate and recurrence, z-scores, the family
    shares weighted by C.COMPOSITION_WEIGHT, or by `cover_w` per cell when given."""
    import numpy as np

    X = v[FIRE_VARS + FAM_VARS].astype("float")
    X["rate"] = np.log10(X.rate + offset)
    X["recurrence"] = np.log1p(X.recurrence)
    X = (X - X.mean()) / X.std(ddof=0).where(lambda s: s > 0, 1)
    if cover_w is None:
        X[FAM_VARS] *= C.COMPOSITION_WEIGHT
    else:
        X[FAM_VARS] = X[FAM_VARS].mul(cover_w, axis=0)
    return X


def fire_records(v):
    """Months of a year with fire on burnable classes in each res 5 cell of `v` (its own history,
    not pooled), from the step 05 tables: the records of C.POOL_MIN_EVENTS."""
    import numpy as np
    import pandas as pd

    cells = pd.read_parquet(TABLES / "cells.parquet")
    sweep = pd.read_parquet(TABLES / "sweep.parquet", columns=["cell", "year", "cls", "month", "ha"])
    burned = sweep[sweep.cls.isin(C.BURNABLE_CLASSES) & (sweep.month > 0) & (sweep.ha > 0)]
    parent = np.searchsorted(v.h3.to_numpy(), cells.h3_r5.to_numpy())
    assert (v.h3.to_numpy()[parent] == cells.h3_r5.to_numpy()).all()
    lookup = np.empty(cells.cell.max() + 1, dtype="int32")
    lookup[cells.cell.to_numpy()] = parent
    b = pd.DataFrame({"cell": lookup[burned.cell.to_numpy()], "ym": burned.year.to_numpy() * 100 + burned.month.to_numpy()})
    return b.drop_duplicates().groupby("cell").size().reindex(v.cell).fillna(0).astype(int).to_numpy()


def cover_by_fire(rec, top, min_records=C.POOL_MIN_EVENTS):
    """Family weight per cell: C.COMPOSITION_WEIGHT with `min_records` fire records or more, rising
    linearly to `top` with none."""
    import numpy as np

    seen = np.minimum(rec, min_records) / min_records
    return C.COMPOSITION_WEIGHT + (top - C.COMPOSITION_WEIGHT) * (1 - seen)


def redcap(k, w, X, area):
    import pygeoda

    # One thread: with pygeoda's default threads, runs died at random k with a C++ length_error,
    # even one k per process (2026-10-27); single-threaded, k = 5..30 ran with the same ratios.
    r = pygeoda.redcap(k, w, X, method="fullorder-wardlinkage", bound_variable=area,
                       min_bound=C.MIN_REGION_KM2, scale_method="raw", cpu_threads=1)
    return r["Clusters"], r["The ratio of between to total sum of squares"]


def cluster(v, nb_raw, k, offset):
    """REDCAP on the clustered cells. Returns their labels (indexed like v[v.clustered]), the
    between/total ratio, the graph used and its links. A `cover_w` column of v, when there is one,
    is the family weight of each cell."""
    import pandas as pd

    kept = v[v.clustered]
    nb_kept, links = connected(nb_raw, kept.cell, v)
    X = design(kept, offset, kept.cover_w if "cover_w" in kept else None)
    labels, ratio = redcap(k, weights(nb_kept, list(kept.cell)), X, kept.area_km2)
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
            "burned_share": fh.sum() / v.burned_ha.sum(),
            "no_fire_area_share": d.area_km2[d.no_fire].sum() / d.area_km2.sum(),
            "excluded_area_share": d.area_km2[~d.clustered].sum() / d.area_km2.sum(),
        })
    return pd.DataFrame(rows)


def ss_ratio(v, offset):
    """Between-to-total sum of squares of the final regions, over the clustered cells."""
    kept = v[v.clustered]
    X = design(kept, offset, kept.cover_w if "cover_w" in kept else None)
    lab = v.region[v.clustered]
    within = sum(((X[lab == r] - X[lab == r].mean()) ** 2).sum().sum() for r in lab.unique())
    return 1 - within / float((X ** 2).sum().sum())


def force_splits(v, nb_raw, nb_all, offset, points):
    """Give each piece of `points` (name: lat, lon, k), taken from its own k level, a region of its
    own. Each piece must lie inside one region of the current map."""
    import h3
    import pandas as pd

    deep_at = {}
    for k in sorted({k for _, _, k in points.values()}):
        labels, _, _, _ = cluster(v, nb_raw, k, offset)
        deep_at[k] = assign_excluded(v, labels, nb_all)
    region = v.region.to_numpy().copy()
    for name, (lat, lon, k) in points.items():
        deep = deep_at[k]
        at = (v.h3 == h3.latlng_to_cell(lat, lon, C.REGIONS_RES)).to_numpy()
        assert at.sum() == 1, f"{name}: the point is in no res {C.REGIONS_RES} cell of the grid"
        piece = deep == deep[at][0]
        parents = set(region[piece])
        assert len(parents) == 1, f"{name}: the piece spans regions {parents}"
        region[piece] = region.max() + 1
        print(f"  info  forced: {name}, {v.area_km2[piece].sum():,.0f} km² out of region {parents.pop()}")
    # The cells left out of the clustering follow the final map, as in the unforced one: the most
    # common region of their neighbours. Taken from the deeper level instead, a water cell at the
    # mouth of the Uruguay was cut off from its region by the delta piece (2026-10-27).
    kept = v.clustered.to_numpy()
    return assign_excluded(v, pd.Series(region[kept], index=v.index[kept]), nb_all)


def is_thin(c, region, nb):
    """Whether cell `c` is one hexagon wide: no two neighbours of its region touch each other."""
    same = [n for n in nb[c] if region[n] == region[c]]
    return not any(b in nb[a] for i, a in enumerate(same) for b in same[i + 1:])


def strips(region, r, nb):
    """Parts of region `r` that are two hexagons wide everywhere: its triangles of mutual neighbours,
    joined when they share an edge. Sets of cells, largest first."""
    import numpy as np

    cells = set(np.where(region == r)[0])
    tris = set()
    for c in cells:
        s = nb[c] & cells
        for a in s:
            for b in nb[a] & s:
                tris.add(frozenset((c, a, b)))
    tris = list(tris)
    parent = list(range(len(tris)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edge = {}
    for i, t in enumerate(tris):
        for a in t:
            for b in t:
                if a < b:
                    if (a, b) in edge:
                        parent[find(i)] = find(edge[(a, b)])
                    else:
                        edge[(a, b)] = i
    groups = {}
    for i, t in enumerate(tris):
        groups.setdefault(find(i), set()).update(t)
    return sorted(groups.values(), key=len, reverse=True)


def join_forest(v, region, nb):
    """One forest region (D16): the blocks of C.FOREST_BLOCKS, the cheapest path between them across
    the steppe, preferring forest, and the forest cells beside it. Returns the region's id."""
    import heapq

    import h3
    import numpy as np

    def at(lat, lon):
        return region[(v.h3 == h3.latlng_to_cell(lat, lon, C.REGIONS_RES)).to_numpy()][0]

    north, south = (at(*C.FORCED_SPLIT_POINTS[b][:2]) for b in C.FOREST_BLOCKS)
    steppe = at(*C.PYROREGION_NAMES["Estepa patagónica"][:2])
    ll = np.array([h3.cell_to_latlng(x) for x in v.h3])
    lat, lon = ll[:, 0], ll[:, 1]
    block_n, block_s = set(np.where(region == north)[0]), set(np.where(region == south)[0])
    allowed = set(np.where(region == steppe)[0])
    cost, prev = {c: 0.0 for c in block_n}, {}
    queue = [(0.0, c) for c in block_n]
    heapq.heapify(queue)
    end = None
    while queue:
        d, c = heapq.heappop(queue)
        if d > cost[c]:
            continue
        if c in block_s:
            end = c
            break
        for n in nb[c]:
            if n in allowed or n in block_s:
                nd = d + 0.05 + 1 - v.fam_forest.iat[n]
                if nd < cost.get(n, 1e9):
                    cost[n], prev[n] = nd, c
                    heapq.heappush(queue, (nd, n))
    path = []
    c = end
    while c in prev:
        path.append(c)
        c = prev[c]
    margin = C.FOREST_CORRIDOR_LAT_MARGIN
    beside = np.where((region == steppe) & (lat > lat[list(block_s)].max() - margin)
                      & (lat < lat[list(block_n)].min() + margin) & (lon < C.FOREST_CORRIDOR_WEST_OF)
                      & (v.fam_forest >= C.FOREST_CORRIDOR_MIN_SHARE))[0]
    corridor = {c for c in path if c in allowed} | set(beside)
    region[list(corridor)] = north
    region[region == south] = north
    print(f"  info  forest corridor: {len(corridor)} cells, {v.area_km2.iloc[list(corridor)].sum():,.0f} km²")
    return north


def min_width(v, region, nb, nb_all, forest):
    """No branch or neck one hexagon wide (D16). Thin cells go to the neighbouring region where they
    stop being thin, or its most common one; the forest region keeps its cells and widens instead."""
    import numpy as np
    import pandas as pd

    moves = {}

    def target(c):
        counts = pd.Series([region[n] for n in nb[c] if region[n] != region[c]]).value_counts()
        if counts.empty:
            return None
        good = []
        for o in counts.index:
            own, region[c] = region[c], o
            if not is_thin(c, region, nb):
                good.append(o)
            region[c] = own
        return min(good or list(counts.index), key=lambda o: (-counts[o], o))

    def move(c, new):
        moves[c] = moves.get(c, 0) + 1
        region[c] = new

    for _ in range(40):
        changed = 0
        for c in np.where(region == forest)[0]:
            if is_thin(c, region, nb):
                same = [x for x in nb[c] if region[x] == forest]
                cand = [x for x in nb[c] if region[x] != forest and any(x in nb[s] for s in same)]
                if cand:
                    region[max(cand, key=lambda x: (v.fam_forest.iat[x], -x))] = forest
                    changed += 1
        for c in v.cell:
            if region[c] != forest and moves.get(c, 0) < C.MIN_WIDTH_MAX_MOVES and is_thin(c, region, nb):
                t = target(c)
                if t is not None:
                    move(c, t)
                    changed += 1
        # Pieces cut off from their region go to its most common neighbour.
        for r in np.unique(region):
            comps = sorted(components(nb_all, set(np.where(region == r)[0])), key=len, reverse=True)
            for comp in comps[1:]:
                out = pd.Series([region[n] for c in comp for n in nb_all[c] if region[n] != r]).value_counts()
                region[list(comp)] = out.index[0]
                changed += 1
        # Strips joined only by a vertex or an edge: the small ones go, the others get a wider neck.
        for r in np.unique(region):
            parts = strips(region, r, nb)
            for s in parts[1:]:
                rest = set().union(*[o for o in parts if o is not s])
                shared = s & rest
                if not shared:  # by an edge, or none at all: another land mass, not a neck
                    for a, b in ((a, b) for a in s for b in nb[a] & rest):
                        cand = [x for x in nb[a] & nb[b] if region[x] != r]
                        if cand:
                            region[max(cand, key=lambda x: v.fam_forest.iat[x] if r == forest else -x)] = r
                            changed += 1
                            break
                elif len(s) < C.MIN_WIDTH_SMALL_PIECE and r != forest:
                    for c in s - shared:
                        t = target(c)
                        if t is not None and t != r:
                            move(c, t)
                            changed += 1
                else:
                    widened = False
                    for c in shared:
                        for x in nb[c]:
                            if region[x] != r and (nb[x] & s) and (nb[x] & rest):
                                region[x] = r
                                changed += 1
                                widened = True
                                break
                        if widened:
                            break
        if not changed:
            return region
    raise RuntimeError("min_width did not settle")


def clip_to_country(poly):
    """The regions clipped to the outline of the country, from the provinces of step 09."""
    import geopandas as gpd
    import shapely
    from shapely.geometry import MultiPolygon, Polygon

    provinces = gpd.read_parquet(REPO / C.ANCILLARY_DIR / "provinces.parquet")
    closed = shapely.make_valid(shapely.union_all(provinces.geometry.values)).buffer(C.COUNTRY_CLOSE_DEG).buffer(-C.COUNTRY_CLOSE_DEG)
    country = MultiPolygon([Polygon(p.exterior) for p in closed.geoms])
    poly = poly.copy()
    poly["geometry"] = shapely.intersection(shapely.make_valid(poly.geometry.values), country, grid_size=1e-7)
    return poly.set_crs(provinces.crs, allow_override=True)


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


def top_places(text):
    """'Salta 46%; La Rioja 12%; Chaco 11%' -> 'Salta, La Rioja y Chaco': the names above
    LEGEND_MIN_SHARE, three at most, never the part outside the country."""
    names = []
    for item in text.split("; "):
        name, share = item.rsplit(" ", 1)
        if name != "(fuera)" and float(share.rstrip("%")) >= LEGEND_MIN_SHARE:
            names.append(name.replace(" Del ", " del "))  # GAUL writes "Santiago Del Estero"
    names = names[:3]
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} y {names[-1]}"


def region_names(poly, names=C.PYROREGION_NAMES):
    """Name and colour of each region from `names` (name: lat, lon, colour), by the polygon holding
    each point. Only when every region gets exactly one name; otherwise none (another map)."""
    from shapely.geometry import Point

    found = {}
    for name, (lat, lon, colour) in names.items():
        hit = poly.region[poly.contains(Point(lon, lat))].tolist()
        if len(hit) == 1:
            found.setdefault(hit[0], []).append((name, colour))
    if sorted(found) == sorted(poly.region) and all(len(n) == 1 for n in found.values()):
        return {r: n[0] for r, n in found.items()}
    return {}


def draw(poly, s, title, path, places_path, names=C.PYROREGION_NAMES):
    """The map, one colour per region, with a legend table: colour, number, name with its provinces
    (from the places file of step 09, if there is one) and burn rate."""
    import matplotlib.pyplot as plt
    import pandas as pd
    from matplotlib.patches import Rectangle

    named = region_names(poly, names)
    colour = ({r: c for r, (_, c) in named.items()} if named
              else {r: PALETTE[i] for i, r in enumerate(sorted(poly.region))})
    places = (pd.read_csv(places_path).set_index("region") if places_path.exists() else None)
    if places is not None and set(places.index) != set(poly.region):
        print(f"  info  {places_path.name} is from another map: legend without places; run step 09 "
              "--overlay and this step again")
        places = None
    fig, (ax, leg) = plt.subplots(1, 2, figsize=(13, 11), gridspec_kw=dict(width_ratios=[1, 1.25], wspace=0.02))
    poly.plot(ax=ax, color=[colour[r] for r in poly.region], edgecolor="white", linewidth=0.8)
    for _, p in poly.iterrows():
        pt = p.geometry.representative_point()
        ax.annotate(str(p.region), (pt.x, pt.y), ha="center", va="center", fontsize=9,
                    fontweight="bold", color="#1a1a19",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_axis_off()

    leg.set_axis_off()
    leg.set_xlim(0, 1)
    leg.set_ylim(0, 1)
    rows = s.sort_values("region")
    step = min(0.055, 0.8 / (len(rows) + 1))
    top = 0.5 + step * (len(rows) + 1) / 2
    leg.text(0.12, top, "Región (provincias)", fontsize=10, fontweight="bold", va="center")
    leg.text(1.0, top, "%/año", fontsize=10, fontweight="bold", va="center", ha="right")
    for i, r in enumerate(rows.itertuples(), start=1):
        y = top - i * step
        leg.add_patch(Rectangle((0, y - step * 0.35), 0.05, step * 0.7, color=colour[r.region], lw=0))
        leg.text(0.07, y, str(r.region), fontsize=10, fontweight="bold", va="center")
        label = named[r.region][0] if named else ""
        if places is not None:
            provinces = top_places(places.loc[r.region, "provinces"])
            label = f"{label} ({provinces})" if label else provinces
        leg.text(0.12, y, label, fontsize=10, va="center")
        leg.text(1.0, y, f"{r.rate_pct:.2f}".replace(".", ","), fontsize=10, va="center", ha="right")
    leg.text(0, top - (len(rows) + 1) * step,
             "%/año: área quemada sobre área quemable, 1999 a 2025.\n"
             f"Provincias con al menos {LEGEND_MIN_SHARE} % del área de la región. Nombres propuestos.",
             fontsize=8.5, color="#555", va="top")
    FIGS.mkdir(exist_ok=True)
    plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def build(k, offset, force=False, pool=False, cover_fire=False, team_edits=False):
    import pandas as pd

    v, g = load(pool)
    points, names = C.FORCED_SPLIT_POINTS, C.PYROREGION_NAMES_EDITED if team_edits else C.PYROREGION_NAMES
    if cover_fire:
        rec = fire_records(v)
        v["cover_w"] = cover_by_fire(rec, C.COVER_BY_FIRE_TOP)
        points = C.COVER_BY_FIRE_FORCED
        names = C.PYROREGION_NAMES_BY_FIRE
        kept = v.clustered.to_numpy()
        print(f"  info  family weight by fire seen: {(v.cover_w[kept] > C.COMPOSITION_WEIGHT).sum():,} of "
              f"{kept.sum():,} clustered cells above {C.COMPOSITION_WEIGHT}, {(rec[kept] == 0).sum():,} at "
              f"{C.COVER_BY_FIRE_TOP} (no fire record)")
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
        v["region"] = number_north_to_south(v, force_splits(v, nb_raw, nb_all, offset, points))
        n_regions = k + len(points)
        # ss_ratio, not pygeoda's ratio: the two differ (k = 12: 0.523 against 0.469, 2026-10-27; not
        # explained yet), so compare forced and unforced maps with ss_ratio only.
        print(f"with the forced pieces: {n_regions} regions, between/total (ss_ratio) {ss_ratio(v, offset):.3f}")
    if team_edits:
        region = v.region.to_numpy().copy()
        forest = join_forest(v, region, nb_raw)
        region = min_width(v, region, nb_raw, nb_all, forest)
        v["region"] = number_north_to_south(v, region)
        n_regions -= len(C.FOREST_BLOCKS) - 1
        print(f"with the team edits: {n_regions} regions, between/total (ss_ratio) {ss_ratio(v, offset):.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    tag = (f"r{C.REGIONS_RES}_k{k}" + ("_forced" if force else "") + ("_edited" if team_edits else "")
           + ("_pool" if pool else "") + ("_coverfire" if cover_fire else "")
           + ("" if offset == C.LOG_RATE_OFFSET else f"_off{offset:g}"))
    v[["cell", "h3", "region", "clustered"]].to_parquet(OUT / f"regions_{tag}.parquet", index=False)
    poly = clip_to_country(polygons(v, g)) if team_edits else polygons(v, g)
    poly.to_parquet(OUT / f"regions_{tag}_polygons.parquet", index=False)
    s = summary(v, poly)
    s.to_csv(OUT / f"summary_{tag}.csv", index=False, float_format="%.4g")
    fig = FIGS / f"07-regions_{tag}.png"
    km2 = f"{C.MIN_REGION_KM2:,.0f}".replace(",", ".")
    extra = (f" + {len(points)} pieza{'s' if len(points) > 1 else ''} forzada{'s' if len(points) > 1 else ''}"
             if force else "")
    extra += ", ajustes del equipo" if team_edits else ""
    extra += ", historia de celdas con poco fuego sumada a sus vecinas" if pool else ""
    extra += (",\ncobertura con peso según el fuego visto "
                  f"({C.COMPOSITION_WEIGHT:g} a {C.COVER_BY_FIRE_TOP:g})".replace(".", ",")) if cover_fire else ""
    draw(poly, s, f"Pirorregiones de Argentina, borrador\nH3 res 5, REDCAP Ward, k = {k}{extra}, "
         f"mínimo {km2} km²", fig, OUT / f"places_{tag}.csv", names)
    for p in (OUT / f"regions_{tag}.parquet", OUT / f"regions_{tag}_polygons.parquet",
              OUT / f"summary_{tag}.csv", fig):
        print(f"wrote {p.relative_to(REPO)}")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(s.round(3).to_string(index=False))
    if team_edits:
        region = v.region.to_numpy()
        # Coast and border cells with one or two neighbours in the grid cannot be two wide.
        thin = [c for c in v.cell if is_thin(c, region, nb_raw)]
        print(f"  info  thin cells left: {len(thin)}, all with fewer than 3 neighbours in the grid")
        assert all(len(nb_raw[c]) < 3 for c in thin), "a branch one hexagon wide is left"
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
    ap.add_argument("--team-edits", action="store_true", help="with --force, the MapBiomas team's edits (D16)")
    ap.add_argument("--pool", action="store_true", help="sensitivity: variables of 06-variables.py --pool")
    ap.add_argument("--cover-by-fire", action="store_true", help="candidate: family weight by the fire each cell saw")
    args = ap.parse_args()
    if args.team_edits and not args.force:
        ap.error("--team-edits needs --force: it edits the forced pieces")
    if args.curve:
        curve(args.log_offset)
    if args.build or not args.curve:
        for k in args.k:
            build(k, args.log_offset, args.force, args.pool, args.cover_by_fire, args.team_edits)


if __name__ == "__main__":
    main()
