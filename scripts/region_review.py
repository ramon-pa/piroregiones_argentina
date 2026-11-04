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
  --similar        which regions of the chosen map (k = 12 plus the forced pieces) look most alike: distance between the mean profiles of the regions in the clustering
                   space of step 07 (same variables, logs, z-scores and family weight), over the
                   clustered cells; average linkage on those distances for the tree. Whether two
                   regions touch comes from their polygons. To similar_r5_k12_forced.csv and
                   outputs/review-similar_k12_forced.png.
  --drivers        what sets the regions of the chosen map apart: R2 of each variable and its share
                   of the variation between regions (drivers_r5_k12_forced.csv), the profile of each
                   region, the distance matrix between regions and between a sample of cells, each
                   variable in its own units per region, and how much each variable adds to each
                   split of the tree (split_vars_r5.csv). Figures outputs/review-profiles_k12_forced,
                   review-distance_k12_forced, review-variables_k12_forced, review-split_vars_r5.
  --tree           rebuilds the spanning tree of REDCAP (pygeoda does not return it) as libgeoda
                   builds it, checks that cutting it gives pygeoda's regions (TREE_CHECK_K), saves it
                   to tree_r5.parquet with the k at which each edge is cut, and follows it along the
                   northern Andean-Patagonian forest (tree_paths_r5.csv,
                   outputs/review-tree_patagonia.png). ~1.5 GB of memory for the distances.
  --fichas         one row per region of the chosen map with what its slide shows (area, places, rate,
                   season, sizes, cover, what sets it apart, closest region), to fichas_r5_k12_forced.csv,
                   and a locator map per region to outputs/fichas/. Run --similar first.

Run from the repo root:

    uv run python scripts/region_review.py --burned-once 12
    uv run python scripts/region_review.py --splits 20
    uv run python scripts/region_review.py --similar
    uv run python scripts/region_review.py --drivers
    uv run python scripts/region_review.py --tree
    uv run python scripts/region_review.py --fichas
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
FAM_NAMES = {"fam_forest": "bosque", "fam_shrubland": "arbustal", "fam_grassland": "pastizal",
             "fam_pasture": "pastura", "fam_agriculture": "agricultura", "fam_agri_perennial": "agric. perenne"}
CELLS_PER_REGION = 150  # cells per region in the cell distance matrix, so small regions still show
SPLITS_KMAX = 22  # --drivers: splits up to k = 21, the levels --splits looked at
TREE_CHECK_K = (5, 12, 20, 25)  # levels at which the rebuilt tree must give pygeoda's regions
COVER_WEIGHTS = (0.2, 0.35, 0.5, 0.75, 1.0)  # --cover: uniform weights of the family shares
COVER_ADAPTIVE_TOPS = (0.5, 1.0)  # --cover: weight with no fire record, falling to 0.2 at C.POOL_MIN_EVENTS
# --cover-grid: the weight by fire seen over a grid of tops and of the fire records at which it is
# back to C.COMPOSITION_WEIGHT, to see whether the forest region holds beyond the one --cover point.
COVER_GRID_TOPS = (0.3, 0.4, 0.5, 0.6, 0.75)
COVER_GRID_MIN_RECORDS = (5, 10, 20)
JACCARD_MATCH = 0.5  # --pool-review, --cover: a target piece "appears" when a region overlaps it this much (area)
# --cover: the forest strip "appears" when one region holds at least STRIP_RECALL of its area and the
# strip is at least STRIP_PRECISION of that region (the rest is ecotone). Our thresholds: a region of
# the strip with its ecotone is bigger than the strip, so a Jaccard of 0.5 misses it.
STRIP_RECALL, STRIP_PRECISION = 0.8, 0.4
COVER_MAP = ("según fuego, hasta 0.5", 12)  # --cover: the variant and k drawn next to the chosen map
# Points along the northern Andean-Patagonian forest, north to south. Two are the points of the forced
# pieces; the place names of the other two are approximate (lat, lon of the town, our reading).
TREE_POINTS = {
    "oeste de Neuquén": C.FORCED_SPLIT_POINTS["oeste de Neuquén"][:2],
    "Nahuel Huapi": (-41.1, -71.5),
    "El Bolsón": (-41.9, -71.5),
    "oeste de Chubut": C.FORCED_SPLIT_POINTS["oeste de Chubut"][:2],
}


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


def similar():
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import squareform

    tag = f"r{C.REGIONS_RES}_k12_forced"
    m = step07()
    v, _ = m.load()
    reg = pd.read_parquet(REGIONS / f"regions_{tag}.parquet")
    assert (reg.cell.to_numpy() == v.cell.to_numpy()).all()
    kept = v.clustered.to_numpy()
    X = m.design(v[kept], C.LOG_RATE_OFFSET)
    centre = X.groupby(reg.region.to_numpy()[kept]).mean()
    ids = centre.index.to_numpy()
    d = np.sqrt(((centre.to_numpy()[:, None, :] - centre.to_numpy()[None, :, :]) ** 2).sum(axis=2))

    poly = gpd.read_parquet(REGIONS / f"regions_{tag}_polygons.parquet").set_index("region").loc[ids]
    named = m.region_names(poly.reset_index())
    name = {r: named[r][0] if named else str(r) for r in ids}
    colour = {r: named[r][1] if named else "#888888" for r in ids}
    near = poly.buffer(1e-6)  # the unioned hexagons are not exactly noded
    rows = []
    for i, a in enumerate(ids):
        for j in range(i + 1, len(ids)):
            b = ids[j]
            rows.append({"a": a, "b": b, "name_a": name[a], "name_b": name[b], "distance": d[i, j],
                         "touch": bool(near.loc[a].intersects(near.loc[b]))})
    pairs = pd.DataFrame(rows).sort_values("distance")
    path = REGIONS / f"similar_{tag}.csv"
    pairs.to_csv(path, index=False, float_format="%.3f")
    with pd.option_context("display.width", 200):
        print("closest pairs:")
        print(pairs.head(10).round(2).to_string(index=False))
        nn = pd.DataFrame({"region": ids, "name": [name[r] for r in ids],
                           "closest": [ids[np.argsort(d[i])[1]] for i in range(len(ids))],
                           "distance": [np.sort(d[i])[1] for i in range(len(ids))]})
        print("closest region of each:")
        print(nn.round(2).to_string(index=False))
    print(f"wrote {path.relative_to(REPO)}")

    z = linkage(squareform(d, checks=False), method="average")
    fig, ax = plt.subplots(figsize=(9, 7))
    dn = dendrogram(z, orientation="left", labels=[f"{r}  {name[r]}" for r in ids], ax=ax,
                    color_threshold=0, above_threshold_color="#555555", leaf_font_size=11)
    for tick, leaf in zip(ax.get_yticklabels(), dn["leaves"]):
        ax.plot(0, tick.get_position()[1], "s", ms=11, color=colour[ids[leaf]], clip_on=False, zorder=3)
    ax.set_xlabel("distancia entre perfiles medios (variables del agrupamiento, en desvíos estándar)", fontsize=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=14)
    ax.set_title("Qué pirorregiones se parecen más entre sí", fontsize=12, loc="left")
    FIGS.mkdir(exist_ok=True)
    out = FIGS / "review-similar_k12_forced.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"wrote {out.relative_to(REPO)}")


def spanning_tree(X, nb, ids):
    """Stage 1 of REDCAP, full order with Ward linkage, as libgeoda does it (clustering/redcap.cpp,
    FullOrderWardRedCap::Clustering, read 2026-10-28): merge the two neighbouring clusters with the
    smallest distance, update the distances of every cluster to the merged one with Lance-Williams,
    and add to the tree the shortest original edge between the two. Ward on squared Euclidean
    distances: with them the cut of this tree gives exactly pygeoda's regions at k = 5, 12, 20 and
    25; with plain distances 1,223 to 2,943 cells differ (2026-10-28). Returns the tree edges as
    (row, row, merge order, linkage distance), rows indexing X."""
    import heapq

    import numpy as np

    A = X.to_numpy(dtype="float64")
    n = len(A)
    row = {c: i for i, c in enumerate(ids)}
    sq = (A ** 2).sum(axis=1)
    D = A @ A.T  # n x n, ~1.5 GB at res 5
    D *= -2
    D += sq[:, None]
    D += sq[None, :]
    np.maximum(D, 0, out=D)
    adj = [{row[c] for c in nb[ids[i]]} for i in range(n)]

    def length(i, j):  # original edge length, exact
        return ((A[i] - A[j]) ** 2).sum()

    size = np.ones(n)
    members = {i: [i] for i in range(n)}
    of = np.arange(n)  # cluster of each row
    cnb = {i: set(adj[i]) for i in range(n)}
    active = np.ones(n, dtype=bool)
    heap = [(D[i, j], i, j) for i in range(n) for j in adj[i] if i < j]
    heapq.heapify(heap)
    edges = []
    while heap and len(edges) < n - 1:
        dist, o, d = heapq.heappop(heap)
        if not (active[o] and active[d]) or d not in cnb[o] or D[o, d] != dist:
            continue
        small, big = (o, d) if len(members[o]) <= len(members[d]) else (d, o)
        best = min((length(i, j), i, j) for i in members[small] for j in adj[i] if of[j] == big)
        edges.append((best[1], best[2], len(edges), dist))
        act = np.flatnonzero(active)
        act = act[(act != o) & (act != d)]
        nc = size[act]
        new = (D[act, o] * (size[o] + nc) + D[act, d] * (size[d] + nc) - dist * nc) / (size[o] + size[d] + nc)
        D[act, o] = new
        D[o, act] = new
        active[d] = False
        size[o] += size[d]
        members[o] += members.pop(d)
        of[members[o]] = o
        cnb[o] = (cnb[o] | cnb.pop(d)) - {o, d}
        for c in cnb[o]:
            cnb[c].discard(d)
            cnb[c].add(o)
            heapq.heappush(heap, (D[o, c], min(o, c), max(o, c)))
    del D
    assert len(edges) == n - 1, f"tree has {len(edges)} edges for {n} nodes: graph not connected"
    return edges


def cut_tree(edges, X, area, k, min_area):
    """Stage 2 of REDCAP (libgeoda AbstractClusterFactory::Partitioning and Tree::Partition): every
    tree finds the edge whose cut reduces its sum of squares the most, with both sides at least
    `min_area`; the tree with the largest reduction is split, until there are k. Returns a label per
    row of X."""
    import heapq

    import numpy as np

    A = X.to_numpy(dtype="float64")
    area = np.asarray(area, dtype="float64")
    nbr = {}
    for a, b, *_ in edges:
        nbr.setdefault(a, []).append(b)
        nbr.setdefault(b, []).append(a)

    def ssd(rows):
        s = A[rows]
        return float(((s - s.mean(axis=0)) ** 2).sum())

    def best_split(nodes):
        """(reduction, child side) of the best admissible cut of the tree spanning `nodes`."""
        nodes_set = set(nodes)
        root = nodes[0]
        order, parent = [root], {root: -1}
        for u in order:
            for w in nbr.get(u, []):
                if w in nodes_set and w not in parent:
                    parent[w] = u
                    order.append(w)
        idx = {u: i for i, u in enumerate(order)}
        S = A[order].copy()
        Q = (A[order] ** 2).sum(axis=1)
        cnt = np.ones(len(order))
        ar = area[order].copy()
        for u in reversed(order[1:]):
            p = idx[parent[u]]
            i = idx[u]
            S[p] += S[i]
            Q[p] += Q[i]
            cnt[p] += cnt[i]
            ar[p] += ar[i]
        tot_S, tot_Q, tot_n, tot_a = S[0], Q[0], cnt[0], ar[0]
        ssd_tot = tot_Q - (tot_S ** 2).sum() / tot_n
        ssd_in = Q[1:] - (S[1:] ** 2).sum(axis=1) / cnt[1:]
        rS, rQ, rn = tot_S - S[1:], tot_Q - Q[1:], tot_n - cnt[1:]
        ssd_out = rQ - (rS ** 2).sum(axis=1) / rn
        red = ssd_tot - ssd_in - ssd_out
        ok = (ar[1:] >= min_area) & (tot_a - ar[1:] >= min_area)
        if not ok.any():
            return 0.0, None
        red = np.where(ok, red, -np.inf)
        j = int(np.argmax(red)) + 1
        if red[j - 1] <= 0:
            return 0.0, None
        child = order[j]
        side, stack = [child], [child]
        while stack:
            u = stack.pop()
            for w in nbr.get(u, []):
                if w in nodes_set and parent[w] == u:
                    side.append(w)
                    stack.append(w)
        return float(red[j - 1]), sorted(side)

    trees, done, tick = [], [], 0
    whole = list(range(len(A)))
    r, side = best_split(whole)
    heapq.heappush(trees, (-r, tick, whole, side))
    while trees and len(trees) + len(done) < k:
        negr, _, nodes, side = heapq.heappop(trees)
        if side is None or ssd(nodes) == 0:
            done.append(nodes)
            k -= 1
            continue
        rest = sorted(set(nodes) - set(side))
        for part in (side, rest):
            tick += 1
            r, s = best_split(part)
            heapq.heappush(trees, (-r, tick, part, s))
    labels = np.empty(len(A), dtype="int32")
    for i, (_, _, nodes, _) in enumerate(trees):
        labels[nodes] = i
    for j, nodes in enumerate(done, start=len(trees)):
        labels[nodes] = j
    return labels


def same_partition(a, b):
    """True when two labelings are the same partition (labels may differ)."""
    import pandas as pd

    t = pd.crosstab(a, b)
    return bool(((t > 0).sum(axis=0) == 1).all() and ((t > 0).sum(axis=1) == 1).all())


def chosen_map():
    """The chosen map (k = 12 plus the forced pieces) in the clustering space of step 07: step 07
    module, cell table, which cells are clustered, their design matrix, region of every cell, region
    ids in the order of the average-linkage tree of their mean profiles, names and colours."""
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import squareform

    tag = f"r{C.REGIONS_RES}_k12_forced"
    m = step07()
    v, g = m.load()
    reg = pd.read_parquet(REGIONS / f"regions_{tag}.parquet")
    assert (reg.cell.to_numpy() == v.cell.to_numpy()).all()
    region = reg.region.to_numpy()
    kept = v.clustered.to_numpy()
    X = m.design(v[kept], C.LOG_RATE_OFFSET)
    centre = X.groupby(region[kept]).mean()
    d = np.sqrt(((centre.to_numpy()[:, None, :] - centre.to_numpy()[None, :, :]) ** 2).sum(axis=2))
    leaves = dendrogram(linkage(squareform(d, checks=False), method="average"), no_plot=True)["leaves"]
    order = centre.index.to_numpy()[leaves]
    poly = gpd.read_parquet(REGIONS / f"regions_{tag}_polygons.parquet")
    named = m.region_names(poly)
    name = {r: named[r][0] if named else str(r) for r in poly.region}
    colour = {r: named[r][1] if named else "#888888" for r in poly.region}
    return dict(m=m, v=v, g=g, kept=kept, X=X, region=region, order=order, name=name, colour=colour,
                poly=poly, tag=tag)


def drivers():
    """What sets the regions of the chosen map apart: share of each variable's variation between
    regions, profile of each region, distances between regions and between cells, how each variable
    is spread in each region, and how much each variable weighs in each split of the tree."""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from matplotlib.colors import LinearSegmentedColormap

    s = chosen_map()
    m, v, kept, X, order, name, colour = s["m"], s["v"], s["kept"], s["X"], s["order"], s["name"], s["colour"]
    lab = s["region"][kept]
    cols = m.FIRE_VARS + m.FAM_VARS
    labels = {**VAR_NAMES, **FAM_NAMES}
    # Diverging: blue and red poles, grey midpoint (dataviz skill, references/palette.md).
    div = LinearSegmentedColormap.from_list("div", ["#1c5cab", "#f0efec", "#b8322f"])
    FIGS.mkdir(exist_ok=True)

    # Share of each variable's sum of squares between regions (R2 per variable). Families on their
    # z-scores, without the 0.2 weight, which scales both terms alike.
    within = sum(((X[lab == r] - X[lab == r].mean()) ** 2).sum() for r in np.unique(lab))
    r2 = 1 - within / (X ** 2).sum()
    share = (X ** 2).sum() / float((X ** 2).sum().sum())
    imp = pd.DataFrame({"variable": [labels[c] for c in cols], "r2": r2[cols].to_numpy(),
                        "share_of_total_ss": share[cols].to_numpy()})
    imp["between_share"] = imp.r2 * imp.share_of_total_ss / (imp.r2 * imp.share_of_total_ss).sum()
    path = REGIONS / f"drivers_{s['tag']}.csv"
    imp.to_csv(path, index=False, float_format="%.4f")
    print("variation between regions, by variable:")
    print(imp.sort_values("between_share", ascending=False).round(3).to_string(index=False))
    print(f"wrote {path.relative_to(REPO)}")

    # Profiles: mean z-score of each variable per region, R2 on top.
    Z = X.copy()
    Z[m.FAM_VARS] /= C.COMPOSITION_WEIGHT
    prof = Z.groupby(lab).mean().loc[order, cols]
    fig, (top, ax) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw=dict(height_ratios=[1, 6], hspace=0.05),
                                  sharex=True)
    top.bar(range(len(cols)), r2[cols], color=["#2a78d6"] * 7 + ["#86b6ef"] * 6, width=0.7)
    for i, c in enumerate(cols):
        top.text(i, r2[c] + 0.02, f"{r2[c]:.2f}".replace(".", ","), ha="center", fontsize=9, color="#52514e")
    top.set_ylim(0, 1.05)
    top.set_yticks([])
    for sp in ("top", "right", "left"):
        top.spines[sp].set_visible(False)
    top.set_title("R² de cada variable: parte de su variación que queda entre regiones", fontsize=10,
                  loc="left", color="#52514e")
    im = ax.imshow(prof.to_numpy(), cmap=div, vmin=-2, vmax=2, aspect="auto")
    for i in range(prof.shape[0]):
        for j in range(prof.shape[1]):
            val = prof.iat[i, j]
            ax.text(j, i, f"{val:+.1f}".replace(".", ","), ha="center", va="center", fontsize=8,
                    color="white" if abs(val) > 1.3 else "#1a1a19")
    ax.set_yticks(range(len(order)), [f"{r}  {name[r]}" for r in order], fontsize=10)
    ax.set_xticks(range(len(cols)), [labels[c] for c in cols], rotation=40, ha="right", fontsize=10)
    ax.axvline(6.5, color="#1a1a19", lw=1)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=[top, ax], shrink=0.5, pad=0.01)
    cb.set_label("media de la región, en desvíos del país", fontsize=9)
    fig.suptitle("Perfil de cada pirorregión (variables de fuego | familias de cobertura, peso 0,2)",
                 fontsize=12, x=0.1, ha="left")
    out = FIGS / f"review-profiles_k12_forced.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")

    # Distances: between region profiles, and between a sample of cells ordered by region.
    centre = X.groupby(lab).mean().loc[order]
    dr = np.sqrt(((centre.to_numpy()[:, None] - centre.to_numpy()[None]) ** 2).sum(axis=2))
    rng = np.random.default_rng(0)
    rows = []
    for r in order:
        idx = np.flatnonzero(lab == r)
        rows.append(np.sort(rng.choice(idx, min(len(idx), CELLS_PER_REGION), replace=False)))
    sample = np.concatenate(rows)
    A = X.to_numpy()[sample]
    dc = np.sqrt(((A[:, None] - A[None]) ** 2).sum(axis=2))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(18, 8.5), gridspec_kw=dict(wspace=0.35))
    seq = LinearSegmentedColormap.from_list("seq", ["#0d366b", "#3987e5", "#cde2fb", "#fcfcfb"])
    a1.imshow(dr, cmap=seq, vmin=0, vmax=np.percentile(dr, 95))
    for i in range(len(order)):
        for j in range(len(order)):
            if i != j:
                a1.text(j, i, f"{dr[i, j]:.1f}".replace(".", ","), ha="center", va="center", fontsize=7,
                        color="white" if dr[i, j] < np.percentile(dr, 30) else "#1a1a19")
    names = [f"{r}  {name[r]}" for r in order]
    a1.set_yticks(range(len(order)), names, fontsize=9)
    a1.set_xticks(range(len(order)), [str(r) for r in order], fontsize=9)
    a1.tick_params(length=0)
    a1.set_title("Entre regiones: distancia entre perfiles medios", fontsize=11, loc="left")
    im = a2.imshow(dc, cmap=seq, vmin=0, vmax=np.percentile(dc, 95), interpolation="nearest")
    bounds = np.cumsum([len(x) for x in rows])
    for b in bounds[:-1]:
        a2.axhline(b - 0.5, color="white", lw=0.6)
        a2.axvline(b - 0.5, color="white", lw=0.6)
    mids = bounds - np.array([len(x) for x in rows]) / 2
    a2.set_yticks(mids, [str(r) for r in order], fontsize=9)
    a2.set_xticks(mids, [str(r) for r in order], fontsize=9)
    a2.tick_params(length=0)
    a2.set_title(f"Entre celdas: hasta {CELLS_PER_REGION} celdas al azar por región", fontsize=11, loc="left")
    cb = fig.colorbar(im, ax=a2, shrink=0.7)
    cb.set_label("distancia en el espacio del agrupamiento (oscuro = parecidas)", fontsize=9)
    fig.suptitle("Matriz de distancias, regiones en el orden del árbol de parecidos", fontsize=13, x=0.1, ha="left")
    out = FIGS / "review-distance_k12_forced.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")

    # Each variable, in its own units, per region: box of the clustered cells.
    kv = v[kept].assign(region=lab)
    kv["rate_log"] = np.log10(kv.rate + C.LOG_RATE_OFFSET)
    kv["peak_fy"] = (kv.peak_month - 7) % 12  # July first, so the summer peaks do not wrap around
    kv["large_pct"] = kv.large_share * 100
    panels = [("rate_log", "tasa de quema (%/año)", True), ("recurrence", "recurrencia (años quemados, p99)", False),
              ("cv", "variabilidad entre años (CV)", False), ("peak_fy", "mes pico", False),
              ("season_len", "duración de la temporada (meses)", False),
              ("large_pct", "% quemado en cicatrices ≥ 500 ha", False)]
    fig, axes = plt.subplots(1, len(panels), figsize=(22, 8), sharey=True, gridspec_kw=dict(wspace=0.08))
    for ax, (col, title, logged) in zip(axes, panels):
        data = [kv.loc[kv.region == r, col].to_numpy() for r in order]
        bp = ax.boxplot(data, orientation="horizontal", widths=0.6, patch_artist=True, showfliers=False,
                        medianprops=dict(color="#1a1a19", lw=1.5), whiskerprops=dict(color="#8a8984"),
                        capprops=dict(color="#8a8984"), boxprops=dict(lw=0))
        for patch, r in zip(bp["boxes"], order):
            patch.set_facecolor(colour[r])
        ax.set_title(title, fontsize=10, loc="left")
        ax.grid(axis="x", color="#e5e4df", lw=0.6)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
        if logged:
            ticks = [0.001, 0.01, 0.1, 1, 10]
            ax.set_xticks(np.log10(np.array(ticks) + C.LOG_RATE_OFFSET),
                          [f"{t:g}".replace(".", ",") for t in ticks])
        if col == "peak_fy":
            ax.set_xticks(range(0, 12, 2), [m.MONTHS[(i + 6) % 12] for i in range(0, 12, 2)])
    axes[0].set_yticks(range(1, len(order) + 1), [f"{r}  {name[r]}" for r in order], fontsize=10)
    axes[0].invert_yaxis()
    fig.suptitle("Dónde cae cada pirorregión en cada variable (celdas de res 5; caja: cuartiles, "
                 "bigotes: 1,5 veces el rango intercuartil)", fontsize=12, x=0.1, ha="left")
    out = FIGS / "review-variables_k12_forced.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")

    # Each split of the tree, k -> k+1: how much each variable adds to the split's reduction of the
    # sum of squares, as % of the total. Exact: the per-variable gains add up to the split's gain.
    labk = pd.read_parquet(REGIONS / f"labels_r{C.REGIONS_RES}.parquet")
    assert (labk.cell.to_numpy() == v.cell.to_numpy()).all()
    total = float((X ** 2).sum().sum())
    rows = []
    for k in range(2, SPLITS_KMAX):
        a, b = labk[f"k{k}"].to_numpy()[kept], labk[f"k{k + 1}"].to_numpy()[kept]
        t = pd.crosstab(a, b)
        parent = t.index[(t > 0).sum(axis=1) > 1]
        if len(parent) != 1:
            continue
        inside = a == parent[0]
        sub = X[inside]
        gain = ((sub - sub.mean()) ** 2).sum()
        for c in t.columns[t.loc[parent[0]] > 0]:
            part = X[inside & (b == c)]
            gain -= ((part - part.mean()) ** 2).sum()
        rows.append({"k": k + 1, **{labels[c]: gain[c] / total * 100 for c in cols}})
    sv = pd.DataFrame(rows).set_index("k")
    path = REGIONS / f"split_vars_r{C.REGIONS_RES}.csv"
    sv.to_csv(path, float_format="%.3f")
    print(f"wrote {path.relative_to(REPO)}")
    fig, ax = plt.subplots(figsize=(12, 9))
    im = ax.imshow(sv.to_numpy(), cmap=LinearSegmentedColormap.from_list("s", ["#fcfcfb", "#86b6ef", "#1c5cab", "#0d366b"]),
                   aspect="auto", vmin=0)
    for i in range(sv.shape[0]):
        for j in range(sv.shape[1]):
            val = sv.iat[i, j]
            if val >= 0.1:
                ax.text(j, i, f"{val:.1f}".replace(".", ","), ha="center", va="center", fontsize=8,
                        color="white" if val > sv.to_numpy().max() * 0.5 else "#1a1a19")
    ax.set_yticks(range(len(sv)), [f"k = {k}  ({sv.loc[k].sum():.1f} %)".replace(".", ",") for k in sv.index], fontsize=9)
    ax.set_xticks(range(len(cols)), [labels[c] for c in cols], rotation=40, ha="right", fontsize=10)
    ax.axvline(6.5, color="#1a1a19", lw=1)
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, shrink=0.6)
    cb.set_label("% de la variación total que explica el corte, por variable", fontsize=9)
    ax.set_title("Jerarquía: qué variable separa en cada corte del árbol (entre paréntesis, el corte entero)",
                 fontsize=12, loc="left")
    out = FIGS / f"review-split_vars_r{C.REGIONS_RES}.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")


def tree_review():
    """Rebuild REDCAP's spanning tree (pygeoda does not return it), check that cutting it gives
    pygeoda's regions, save it, and follow it through the Andean-Patagonian forest."""
    import time

    import geopandas as gpd
    import h3
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from shapely.geometry import LineString, Polygon

    s = chosen_map()
    m, v, g, kept = s["m"], s["v"], s["g"], s["kept"]
    kv = v[kept].reset_index(drop=True)
    nb_raw = m.adjacency(v, g)
    nb, _ = m.connected(nb_raw, kv.cell, v)
    X = s["X"].reset_index(drop=True)
    t = time.time()
    edges = spanning_tree(X, nb, list(kv.cell))
    print(f"spanning tree: {len(edges):,} edges, {time.time() - t:.1f} s")

    labk = pd.read_parquet(REGIONS / f"labels_r{C.REGIONS_RES}.parquet")
    assert (labk.cell.to_numpy() == v.cell.to_numpy()).all()
    results = []
    for k in TREE_CHECK_K:
        mine = cut_tree(edges, X, kv.area_km2, k, C.MIN_REGION_KM2)
        results.append((f"cutting the tree at k = {k} gives pygeoda's regions",
                        same_partition(mine, labk[f"k{k}"].to_numpy()[kept])))

    E = pd.DataFrame(edges, columns=["a", "b", "order", "ward"])
    cells = kv.cell.to_numpy()
    E["cell_a"], E["cell_b"] = cells[E.a], cells[E.b]
    lk = labk.set_index("cell")
    E["cut_at_k"] = pd.NA
    for k in range(2, 31):
        cut = (lk[f"k{k}"].reindex(E.cell_a).to_numpy() != lk[f"k{k}"].reindex(E.cell_b).to_numpy())
        E.loc[cut & E.cut_at_k.isna(), "cut_at_k"] = k
    path = REGIONS / f"tree_r{C.REGIONS_RES}.parquet"
    E[["cell_a", "cell_b", "order", "ward", "cut_at_k"]].astype({"cut_at_k": "Int16"}).to_parquet(path, index=False)
    print(f"wrote {path.relative_to(REPO)}")

    # Paths in the tree between points of the northern forest strip, north to south.
    nbr = {}
    for a, b, *_ in edges:
        nbr.setdefault(a, []).append(b)
        nbr.setdefault(b, []).append(a)

    def tree_path(a, b):
        prev, queue = {a: None}, [a]
        for u in queue:
            if u == b:
                break
            for w in nbr[u]:
                if w not in prev:
                    prev[w] = u
                    queue.append(w)
        out = [b]
        while prev[out[-1]] is not None:
            out.append(prev[out[-1]])
        return out[::-1]

    ll = np.array([h3.cell_to_latlng(h) for h in kv.h3])
    at = {}
    for label, (lat, lon) in TREE_POINTS.items():
        hit = np.flatnonzero(kv.h3.to_numpy() == h3.latlng_to_cell(lat, lon, C.REGIONS_RES))
        assert len(hit) == 1, f"{label}: no clustered res {C.REGIONS_RES} cell at the point"
        at[label] = int(hit[0])
    region = s["region"][kept]
    names = list(TREE_POINTS)
    paths, rows = {}, []
    for a, b in zip(names[:-1], names[1:]):
        p = tree_path(at[a], at[b])
        paths[(a, b)] = p
        d = kv.iloc[p]
        rows.append({"from": a, "to": b, "km_apart": round(h3.great_circle_distance(ll[at[a]], ll[at[b]])),
                     "cells_on_path": len(p), "forest_ge50": round(float((d.fam_forest >= 0.5).mean()), 2),
                     "east_to_lon": round(float(ll[p, 1].max()), 1), "south_to_lat": round(float(ll[p, 0].min()), 1),
                     "regions": " ".join(str(r) for r in pd.unique(region[p]))})
    tab = pd.DataFrame(rows)
    print("paths in the tree between points of the forest strip:")
    print(tab.to_string(index=False))
    tab.to_csv(REGIONS / f"tree_paths_r{C.REGIONS_RES}.csv", index=False)

    strip = ((kv.fam_forest >= 0.5) & (ll[:, 1] < -70) & (ll[:, 0] > -46) & (ll[:, 0] < -39)).to_numpy()
    sset = set(np.flatnonzero(strip))
    row_of = {c: i for i, c in enumerate(cells)}
    graph_nb = {i: {row_of[c] for c in nb[cells[i]]} & sset for i in sset}
    tree_nb = {i: set(nbr[i]) & sset for i in sset}
    n_graph, n_tree = len(m.components(graph_nb)), len(m.components(tree_nb))
    print(f"  info  forest strip (>= 50 % forest, west of 70°W, 39 to 46°S): {len(sset)} cells; "
          f"{n_graph} piece(s) as neighbours, {n_tree} piece(s) in the tree")
    nofire = kv.no_fire.to_numpy()
    for lo, hi in ((-40, -39), (-41, -40), (-42, -41), (-43, -42), (-46, -43)):
        band = strip & (ll[:, 0] >= lo) & (ll[:, 0] < hi)
        print(f"  info  strip {-lo}..{-hi}°S: {band.sum()} cells, median rate "
              f"{np.median(kv.rate[band]):.3f} %/yr, no fire {nofire[band].mean():.0%}")

    # Map: cells of the strip and of the chosen map, the tree, and the paths.
    view = (ll[:, 0] < -37.5) & (ll[:, 0] > -47.5) & (ll[:, 1] < -64.5)
    hexes = gpd.GeoDataFrame(
        {"row": np.flatnonzero(view)},
        geometry=[Polygon([(lo, la) for la, lo in h3.cell_to_boundary(h)]) for h in kv.h3[view]], crs=4326)
    hexes["colour"] = [s["colour"][r] for r in region[hexes.row]]
    fig, ax = plt.subplots(figsize=(10, 12))
    hexes.plot(ax=ax, color=hexes.colour, alpha=0.45, linewidth=0)
    hexes[strip[hexes.row]].plot(ax=ax, facecolor="none", edgecolor="#0f5132", linewidth=1.1, hatch="///")
    seg = [LineString([ll[a, ::-1], ll[b, ::-1]]) for a, b, *_ in edges if view[a] and view[b]]
    gpd.GeoSeries(seg, crs=4326).plot(ax=ax, color="#52514e", linewidth=0.45)
    for (a, b), colour in zip(paths, ["#eb6834", "#e34948", "#6250d6"]):
        p = paths[(a, b)]
        ax.plot(ll[p, 1], ll[p, 0], color=colour, lw=2.6, label=f"{a} → {b}: {len(p)} celdas")
    for label, i in at.items():
        ax.plot(ll[i, 1], ll[i, 0], "o", ms=9, color="#1a1a19", mec="white", mew=1.5, zorder=5)
        ax.annotate(label, (ll[i, 1], ll[i, 0]), xytext=(-8, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=10, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0), fontsize=10, frameon=False, title="camino en el árbol",
              title_fontsize=10, alignment="left")
    ax.set_title("El árbol de REDCAP en el norte patagónico\nlíneas grises: aristas del árbol; rayado: "
                 "celdas con ≥ 50 % de bosque; fondo: pirorregión", fontsize=11, loc="left")
    ax.set_axis_off()
    out = FIGS / "review-tree_patagonia.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")

    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def fichas():
    """One row per region of the chosen map with what its slide shows, and a locator map per region.
    Everything comes from the step 07 and 09 outputs and the profiles of --drivers; nothing new is
    measured."""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    s = chosen_map()
    m, v, kept, X, name, colour, poly = s["m"], s["v"], s["kept"], s["X"], s["name"], s["colour"], s["poly"]
    tag = s["tag"]
    summ = pd.read_csv(REGIONS / f"summary_{tag}.csv").set_index("region")
    places = pd.read_csv(REGIONS / f"places_{tag}.csv").set_index("region")
    sim = pd.read_csv(REGIONS / f"similar_{tag}.csv")
    lab = s["region"][kept]
    prof = X[m.FIRE_VARS].groupby(lab).mean()
    v = v.assign(region=s["region"])
    burned = v.groupby("region").burned_ha.sum() / len(C.FIRE_YEARS)
    rows = []
    for r in summ.index:
        p = prof.loc[r]
        top = p.abs().sort_values(ascending=False).head(3).index
        pair = sim[(sim.a == r) | (sim.b == r)].sort_values("distance").iloc[0]
        other = int(pair.b if pair.a == r else pair.a)
        rows.append({
            "region": r, "name": name[r], "colour": colour[r],
            "area_km2": summ.area_km2[r], "country_share": summ.area_km2[r] / summ.area_km2.sum(),
            "provinces": places.provinces[r], "ecoregions": places.ecoregions13[r],
            "rate_pct": summ.rate_pct[r], "rate_rank": int(summ.rate_pct.rank(ascending=False)[r]),
            "burned_ha_per_year": round(burned[r]), "burned_share": burned[r] / burned.sum(),
            "peak": summ.peak[r], "season_len": summ.season_len[r], "large_share": summ.large_share[r],
            "cv": summ.cv[r], "recurrence": summ.recurrence[r],
            "family": FAM_NAMES[f"fam_{summ.family[r]}"], "family_share": summ.family_share[r],
            "no_fire_area_share": summ.no_fire_area_share[r],
            "distinct": "; ".join(f"{VAR_NAMES[c]} {p[c]:+.1f}" for c in top),
            "closest": f"{other} {name[other]}", "closest_distance": pair.distance,
        })
    out = pd.DataFrame(rows)
    path = REGIONS / f"fichas_{tag}.csv"
    out.to_csv(path, index=False, float_format="%.4g")
    with pd.option_context("display.width", 250, "display.max_colwidth", 60):
        print(out.drop(columns=["colour", "provinces", "ecoregions"]).round(3).to_string(index=False))
    print(f"wrote {path.relative_to(REPO)}")

    folder = FIGS / "fichas"
    folder.mkdir(parents=True, exist_ok=True)
    for r in summ.index:
        fig, ax = plt.subplots(figsize=(4, 7.5))
        poly.plot(ax=ax, color="#e5e4df", edgecolor="white", linewidth=0.5)
        poly[poly.region == r].plot(ax=ax, color=colour[r], edgecolor="#1a1a19", linewidth=0.8)
        ax.set_axis_off()
        plt.savefig(folder / f"region_{r:02d}.png", dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
    print(f"wrote {len(summ)} locator maps to {folder.relative_to(REPO)}/")


def best_jaccard(mask, labels, area):
    """Best area-weighted Jaccard between a set of rows and any region of a labelling."""
    import numpy as np

    best = 0.0
    for r in np.unique(labels[mask]):
        inter = area[mask & (labels == r)].sum()
        best = max(best, inter / area[mask | (labels == r)].sum())
    return best


def review_targets(kv, kept):
    """Pieces a sensitivity run is judged by, as row masks of the clustered cells `kv`: the forced
    pieces of the chosen map and the northern Andean-Patagonian forest strip of --tree."""
    import h3
    import numpy as np
    import pandas as pd

    chosen = pd.read_parquet(REGIONS / f"regions_r{C.REGIONS_RES}_k12_forced.parquet").region.to_numpy()[kept]
    targets = {}
    for name, (lat, lon, _) in C.FORCED_SPLIT_POINTS.items():
        at = np.flatnonzero(kv.h3.to_numpy() == h3.latlng_to_cell(lat, lon, C.REGIONS_RES))[0]
        targets[name] = chosen == chosen[at]
    ll = np.array([h3.cell_to_latlng(h) for h in kv.h3])
    targets["franja de bosque andino norte"] = ((kv.fam_forest >= 0.5) & (ll[:, 1] < -70) & (ll[:, 0] > -46)
                                                & (ll[:, 0] < -39)).to_numpy()
    return targets


def cover_setup():
    """What every --cover variant shares: the clustered cells, their neighbours, the unweighted
    design, the fire records of each cell and the pieces a variant is judged by."""
    import numpy as np
    import pandas as pd

    m = step07()
    v, g = m.load()
    kept = v.clustered.to_numpy()
    kv = v[kept].reset_index(drop=True)
    nb, _ = m.connected(m.adjacency(v, g), kv.cell, v)
    base = m.design(kv, C.LOG_RATE_OFFSET)
    base[m.FAM_VARS] /= C.COMPOSITION_WEIGHT  # unweighted z-scores of the families
    rec = m.fire_records(v)[kept]
    ref12 = pd.read_parquet(REGIONS / f"labels_r{C.REGIONS_RES}.parquet").k12.to_numpy()[kept]
    return dict(m=m, v=v, g=g, kept=kept, kv=kv, nb=nb, area=kv.area_km2.to_numpy(), base=base, rec=rec,
                targets=review_targets(kv, kept), ref12=ref12)


def judge_cover(name, w, s):
    """One --cover variant (family weight `w` per cell): rebuilt tree cut at k = 2..30, judged by the
    forced pieces, the forest strip and the whole k = 12 map. Returns its row and its cuts."""
    import numpy as np
    import pandas as pd

    m, kv, area, ref12, targets = s["m"], s["kv"], s["area"], s["ref12"], s["targets"]
    strip = targets["franja de bosque andino norte"]
    sset = set(np.flatnonzero(strip))
    X = s["base"].copy()
    X[m.FAM_VARS] = X[m.FAM_VARS].mul(w, axis=0)
    edges = spanning_tree(X, s["nb"], list(kv.cell))
    cuts = {k: cut_tree(edges, X, area, k, C.MIN_REGION_KM2) for k in range(2, 31)}
    nbr = {}
    for a, b, *_ in edges:
        nbr.setdefault(a, set()).add(b)
        nbr.setdefault(b, set()).add(a)
    row = {"variant": name}
    for tname, mask in targets.items():
        if tname == "franja de bosque andino norte":
            continue
        j = {k: best_jaccard(mask, cuts[k], area) for k in range(2, 31)}
        short = {"oeste de Neuquén": "neuquen", "oeste de Chubut": "chubut", "delta del Paraná": "delta"}[tname]
        row[f"{short}_first_k"] = next((k for k in j if j[k] >= JACCARD_MATCH), None)
        row[f"{short}_best"] = round(max(j.values()), 2)
    for k in range(2, 31):
        lab = cuts[k]
        r = max(np.unique(lab[strip]), key=lambda r: area[strip & (lab == r)].sum())
        recall = area[strip & (lab == r)].sum() / area[strip].sum()
        precision = area[strip & (lab == r)].sum() / area[lab == r].sum()
        if k == 12:
            row["franja_k12_recall"], row["franja_k12_precision"] = round(recall, 2), round(precision, 2)
        if recall >= STRIP_RECALL and precision >= STRIP_PRECISION and "franja_first_k" not in row:
            row["franja_first_k"] = k
            row["franja_km2"] = round(area[lab == r].sum())
    row.setdefault("franja_first_k", None)
    row.setdefault("franja_km2", None)
    row["franja_tree_pieces"] = len(m.components({i: nbr[i] & sset for i in sset}))
    c12 = cuts[12]
    t = pd.crosstab(c12, ref12, values=area, aggfunc="sum").fillna(0)
    row["k12_area_same"] = round(t.max(axis=0).sum() / area.sum(), 3)
    row["k12_regions_kept"] = sum(best_jaccard(ref12 == r, c12, area) >= JACCARD_MATCH for r in np.unique(ref12))
    within = sum(((X[c12 == r] - X[c12 == r].mean()) ** 2).sum() for r in np.unique(c12))
    between = (X ** 2).sum() - within
    row["k12_cover_share_between"] = round(float(between[m.FAM_VARS].sum() / between.sum()), 3)
    return row, cuts, X


def cover_review():
    """Sensitivity of the regions to the weight of land cover: a uniform weight of the family shares
    (COVER_WEIGHTS; the map uses C.COMPOSITION_WEIGHT), and a weight that grows where a cell saw
    few fires (COVER_ADAPTIVE_TOPS, step 07 cover_by_fire). Each variant judged by judge_cover."""
    import numpy as np
    import pandas as pd

    s = cover_setup()
    m, kv, rec = s["m"], s["kv"], s["rec"]
    print(f"  info  clustered cells with fewer than {C.POOL_MIN_EVENTS} fire records: "
          f"{(rec < C.POOL_MIN_EVENTS).sum():,} of {len(rec):,}; with none: {(rec == 0).sum():,}")
    variants = {f"uniforme {w:g}": np.full(len(kv), w) for w in COVER_WEIGHTS}
    variants.update({f"según fuego, hasta {t:g}": s["m"].cover_by_fire(rec, t) for t in COVER_ADAPTIVE_TOPS})

    rows, cuts_by, Xs, results = [], {}, {}, []
    for name, w in variants.items():
        row, cuts_by[name], Xs[name] = judge_cover(name, w, s)
        rows.append(row)
        print(f"  info  {name}: done", flush=True)
    tab = pd.DataFrame(rows)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(tab.to_string(index=False))
    path = REGIONS / f"cover_review_r{C.REGIONS_RES}.csv"
    tab.to_csv(path, index=False)
    print(f"wrote {path.relative_to(REPO)}")

    # The rebuilt tree is checked against pygeoda for the map's weight and the largest one.
    for name in ("uniforme 0.2", f"uniforme {max(COVER_WEIGHTS):g}", COVER_MAP[0]):
        labels, _ = m.redcap(12, m.weights(s["nb"], list(kv.cell)), Xs[name], kv.area_km2)
        results.append((f"{name}: rebuilt tree at k = 12 gives pygeoda's regions",
                        same_partition(cuts_by[name][12], np.asarray(labels))))
    cover_map(m, s["v"], s["g"], s["kept"], cuts_by[COVER_MAP[0]][COVER_MAP[1]])
    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)
    return kv, cuts_by


def cover_grid():
    """The weight by fire seen (step 07 cover_by_fire) over COVER_GRID_TOPS x COVER_GRID_MIN_RECORDS: where
    the northern forest region appears, what it holds at k = 12, and which of the 12 regions of the
    chosen map are lost. Region names from C.PYROREGION_NAMES (the forced pieces left out, since
    they are not regions of k = 12)."""
    import h3
    import numpy as np
    import pandas as pd

    s = cover_setup()
    m, kv, area, rec, ref12, targets = s["m"], s["kv"], s["area"], s["rec"], s["ref12"], s["targets"]
    strip = targets["franja de bosque andino norte"]
    cells = kv.h3.to_numpy()
    names = {}
    for name, (lat, lon, _) in C.PYROREGION_NAMES.items():
        at = np.flatnonzero(cells == h3.latlng_to_cell(lat, lon, C.REGIONS_RES))
        if len(at) and ref12[at[0]] not in names:
            names[ref12[at[0]]] = name
    for t in C.FORCED_SPLIT_POINTS:
        assert t.lower() not in {n.lower() for n in names.values()}
    rows, results = [], []
    for top in COVER_GRID_TOPS:
        for mr in COVER_GRID_MIN_RECORDS:
            w = m.cover_by_fire(rec, top, mr)
            name = f"hasta {top:g}, {mr} registros"
            row, cuts, X = judge_cover(name, w, s)
            row = {"top": top, "min_records": mr, "cells_raised": int((rec < mr).sum()), **row}
            c12 = cuts[12]
            r = max(np.unique(c12[strip]), key=lambda r: area[strip & (c12 == r)].sum())
            R = c12 == r
            row["franja_at_k12"] = row["franja_k12_recall"] >= STRIP_RECALL and row["franja_k12_precision"] >= STRIP_PRECISION
            row["franja_k12_km2"] = round(area[R].sum())
            for piece in ("oeste de Neuquén", "oeste de Chubut"):
                mask = targets[piece]
                row[f"{piece.split()[-1].lower()}_in_franja_k12"] = round(area[mask & R].sum() / area[mask].sum(), 2)
            row["k12_lost"] = "; ".join(n for r12, n in names.items()
                                        if best_jaccard(ref12 == r12, c12, area) < JACCARD_MATCH)
            rows.append(row)
            print(f"  info  {name}: done", flush=True)
            if (top, mr) == (max(COVER_GRID_TOPS), min(COVER_GRID_MIN_RECORDS)):
                labels, _ = m.redcap(12, m.weights(s["nb"], list(kv.cell)), X, kv.area_km2)
                results.append((f"{name}: rebuilt tree at k = 12 gives pygeoda's regions",
                                same_partition(c12, np.asarray(labels))))
    results.append((f"all {len(names)} regions of k = 12 named", len(names) == len(np.unique(ref12))))
    tab = pd.DataFrame(rows)
    cols = ["top", "min_records", "cells_raised", "franja_first_k", "franja_at_k12", "franja_k12_km2",
            "neuquén_in_franja_k12", "chubut_in_franja_k12", "delta_first_k", "k12_area_same",
            "k12_regions_kept", "k12_lost"]
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_colwidth", 80):
        print(tab[cols].to_string(index=False))
    path = REGIONS / f"cover_grid_r{C.REGIONS_RES}.csv"
    tab.to_csv(path, index=False)
    print(f"wrote {path.relative_to(REPO)}")
    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def cover_map(m, v, g, kept, labels):
    """The chosen map and one --cover variant side by side. Each variant region takes the colour of
    the chosen region it overlaps most, if still free; the others, a colour of their own."""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    nb_all, _ = m.connected(m.adjacency(v, g), v.cell, v)
    chosen = pd.read_parquet(REGIONS / f"regions_r{C.REGIONS_RES}_k12_forced.parquet").region.to_numpy()
    var = m.number_north_to_south(v, m.assign_excluded(v, pd.Series(labels, index=v.index[kept]), nb_all)).to_numpy()
    poly_c = m.polygons(v.assign(region=chosen), g)
    poly_v = m.polygons(v.assign(region=var), g)
    named = m.region_names(poly_c)
    col_c = {r: named[r][1] for r in poly_c.region}
    area = v.area_km2.to_numpy()
    overlap = pd.crosstab(var, chosen, values=area, aggfunc="sum").fillna(0)
    col_v, used = {}, set()
    for r in overlap.max(axis=1).sort_values(ascending=False).index:
        best = overlap.loc[r].idxmax()
        if best not in used:
            col_v[r] = col_c[best]
            used.add(best)
    extra = iter(["#0b4f2e"] + m.PALETTE)
    for r in poly_v.region:
        if r not in col_v:
            col_v[r] = next(extra)
    fig, axes = plt.subplots(1, 2, figsize=(12, 11))
    for ax, poly, col, title in ((axes[0], poly_c, col_c, "Mapa elegido: k = 12 + 3 piezas, cobertura 0,2"),
                                 (axes[1], poly_v, col_v, f"Cobertura según el fuego visto (0,2 a 0,5), k = {COVER_MAP[1]}")):
        poly.plot(ax=ax, color=[col[r] for r in poly.region], edgecolor="white", linewidth=0.8)
        ax.set_title(title, fontsize=11, loc="left")
        ax.set_axis_off()
    out = FIGS / "review-cover_k12.png"
    plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO)}")


def pool_review():
    """Sensitivity of the regions to pooling the history of cells with few fires (06-variables.py
    --pool): the rebuilt tree on the pooled variables, checked against pygeoda at k = 12, cut at
    every k, and compared with the chosen map: the forced pieces, the forest strip, the whole map."""
    import geopandas as gpd
    import h3
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    m = step07()
    out = {}
    for pool in (False, True):
        v, g = m.load(pool)
        kept = v.clustered.to_numpy()
        kv = v[kept].reset_index(drop=True)
        nb, _ = m.connected(m.adjacency(v, g), kv.cell, v)
        X = m.design(kv, C.LOG_RATE_OFFSET)
        edges = spanning_tree(X, nb, list(kv.cell))
        cuts = {k: cut_tree(edges, X, kv.area_km2, k, C.MIN_REGION_KM2) for k in range(2, 31)}
        nbr = {}
        for a, b, *_ in edges:
            nbr.setdefault(a, set()).add(b)
            nbr.setdefault(b, set()).add(a)
        out[pool] = dict(v=v, kv=kv, kept=kept, cuts=cuts, nbr=nbr, nb=nb)
    v, kv, kept = out[False]["v"], out[False]["kv"], out[False]["kept"]
    area = kv.area_km2.to_numpy()

    results = []
    ref = pd.read_parquet(REGIONS / f"regions_r{C.REGIONS_RES}_k12_pool.parquet")
    results.append(("pooled tree cut at k = 12 gives pygeoda's regions (07-regions.py --pool)",
                    same_partition(out[True]["cuts"][12], ref.region.to_numpy()[kept])))
    lab = pd.read_parquet(REGIONS / f"labels_r{C.REGIONS_RES}.parquet")
    results.append(("unpooled tree cut at k = 12 gives pygeoda's regions",
                    same_partition(out[False]["cuts"][12], lab.k12.to_numpy()[kept])))

    targets = review_targets(kv, kept)
    rows = []
    for name, rows_mask in targets.items():
        for pool in (False, True):
            j = {k: best_jaccard(rows_mask, out[pool]["cuts"][k], area) for k in range(2, 31)}
            first = next((k for k in j if j[k] >= JACCARD_MATCH), None)
            rows.append({"target": name, "pooled": pool, "km2": round(area[rows_mask].sum()),
                         "first_k_jaccard_ge": first, "jaccard_k12": round(j[12], 2),
                         "best_jaccard": round(max(j.values()), 2), "best_at_k": max(j, key=j.get)})
    tab = pd.DataFrame(rows)
    print(f"when each piece appears as a region (area Jaccard >= {JACCARD_MATCH}), unpooled vs pooled:")
    print(tab.to_string(index=False))
    strip = targets["franja de bosque andino norte"]
    sset = set(np.flatnonzero(strip))
    for pool in (False, True):
        n_tree = len(m.components({i: out[pool]["nbr"][i] & sset for i in sset}))
        print(f"  info  forest strip, {'pooled' if pool else 'unpooled'}: {n_tree} piece(s) in the tree")

    # The whole map: how much area keeps its region, matching each pooled region to its best
    # unpooled one, at k = 12 and with the chosen forced map.
    a, b = out[False]["cuts"][12], out[True]["cuts"][12]
    t = pd.crosstab(b, a, values=area, aggfunc="sum").fillna(0)
    print(f"  info  k = 12, area in the best-matching region, pooled vs unpooled: "
          f"{t.max(axis=1).sum() / area.sum():.1%}")
    path = REGIONS / f"pool_review_r{C.REGIONS_RES}.csv"
    tab.to_csv(path, index=False)
    print(f"wrote {path.relative_to(REPO)}")

    failed = 0
    for label, ok in results:
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}")
        failed += not ok
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    if failed:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--burned-once", type=int, metavar="K", help="map of burned at least once with k = K borders")
    ap.add_argument("--splits", type=int, metavar="KMAX", help="tree of splits up to k = KMAX")
    ap.add_argument("--similar", action="store_true", help="which regions of the chosen map look most alike")
    ap.add_argument("--drivers", action="store_true", help="what sets the regions of the chosen map apart")
    ap.add_argument("--cover", action="store_true", help="sensitivity of the regions to the weight of cover")
    ap.add_argument("--cover-grid", action="store_true", help="the weight of cover by fire seen, over a grid")
    ap.add_argument("--pool-review", action="store_true", help="sensitivity of the regions to 06 --pool")
    ap.add_argument("--fichas", action="store_true", help="one row and a locator map per region")
    ap.add_argument("--tree", action="store_true", help="REDCAP's spanning tree, checked, and the forest strip")
    args = ap.parse_args()
    if args.burned_once:
        burned_once(args.burned_once)
    if args.splits:
        splits(args.splits)
    if args.similar:
        similar()
    if args.drivers:
        drivers()
    if args.tree:
        tree_review()
    if args.fichas:
        fichas()
    if args.pool_review:
        pool_review()
    if args.cover:
        cover_review()
    if args.cover_grid:
        cover_grid()


if __name__ == "__main__":
    main()
