#!/usr/bin/env python
"""workflow/09-ecoregions.py: where each pyroregion falls, by ecoregion (Burkart et al. 1999, the 13
classes) and by province. The first part of step 09; the quantitative comparison comes later.

  --fetch    GEE, interactive: the 13 ecoregions (C.ECOREGIONS_13) and the provinces (C.PROVINCES),
             simplified by C.ANCILLARY_SIMPLIFY_M, to C.ANCILLARY_DIR as GeoParquet.
  --overlay  (default) each res 6 hexagon goes to the ecoregion and the province holding its centre;
             their areas are summed per region of regions_r5_k<k>.parquet (step 07), to
             places_r5_k<k>.csv: the share of each region in each ecoregion and province.
  --k N      which step 07 output to read (default C.REGIONS_K).
  --forced   read the output of 07-regions.py --force (decision D14).
  --cover-by-fire  read the output of 07-regions.py --cover-by-fire (candidate, 2026-10-28).

Run from the repo root:

    uv run python workflow/09-ecoregions.py --fetch
    uv run python workflow/09-ecoregions.py --overlay --k 15
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

ANC = REPO / C.ANCILLARY_DIR
GRID = REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet"
REGIONS = REPO / C.REGIONS_DIR
TOP = 3  # ecoregions and provinces listed per region


def polygons_only(geom):
    import shapely

    parts = [p for p in shapely.get_parts(geom) if p.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(parts)


def fetch():
    import geopandas as gpd
    from utils.gee_tasks import init_ee

    ee = init_ee()
    layers = {
        "ecoregions13": (ee.FeatureCollection(C.ECOREGIONS_13), C.ECOREGION_NAME_FIELD),
        "provinces": (ee.FeatureCollection(C.PROVINCES).filter(ee.Filter.eq("ISO3_CODE", C.PROVINCE_ISO3)),
                      C.PROVINCE_NAME_FIELD),
    }
    ANC.mkdir(parents=True, exist_ok=True)
    for name, (fc, field) in layers.items():
        fc = fc.map(lambda f: ee.Feature(f.geometry().simplify(C.ANCILLARY_SIMPLIFY_M), {"name": f.get(field)}))
        gdf = gpd.GeoDataFrame.from_features(fc.getInfo()["features"], crs="EPSG:4326")
        # GEE's simplify returns GeometryCollections with stray lines and points; keep the polygons.
        gdf["geometry"] = gdf.geometry.make_valid().apply(polygons_only)
        gdf = gdf.dissolve("name").reset_index()[["name", "geometry"]]
        gdf.to_parquet(ANC / f"{name}.parquet", index=False)
        print(f"wrote {(ANC / f'{name}.parquet').relative_to(REPO)}  {len(gdf)} features")


def overlay(k, forced=False, cover_fire=False, team_edits=False):
    import geopandas as gpd
    import numpy as np
    import pandas as pd

    g = gpd.read_parquet(GRID)
    tag = (f"r{C.REGIONS_RES}_k{k}" + ("_forced" if forced else "") + ("_edited" if team_edits else "")
           + ("_coverfire" if cover_fire else ""))
    r = pd.read_parquet(REGIONS / f"regions_{tag}.parquet")
    g["region"] = r.region.to_numpy()[np.searchsorted(r.h3.to_numpy(), g.h3_r5.to_numpy())]
    pts = gpd.GeoDataFrame(g[["cell", "region", "area_km2"]], geometry=g.geometry.representative_point(), crs=g.crs)
    rows = {}
    for layer in ("ecoregions13", "provinces"):
        poly = gpd.read_parquet(ANC / f"{layer}.parquet")
        j = gpd.sjoin(pts, poly, how="left", predicate="within").drop_duplicates("cell")
        j["name"] = j["name"].fillna("(fuera)")
        print(f"  info  {layer}: {(j.name == '(fuera)').sum():,} hexagons with the centre outside every polygon")
        t = j.groupby(["region", "name"]).area_km2.sum()
        share = t / t.groupby("region").transform("sum")
        for reg, s in share.groupby(level="region"):
            top = s.droplevel("region").sort_values(ascending=False).head(TOP)
            rows.setdefault(reg, {})[layer] = "; ".join(f"{n} {v:.0%}" for n, v in top.items())
    out = pd.DataFrame([{"region": reg, **d} for reg, d in sorted(rows.items())])
    path = REGIONS / f"places_{tag}.csv"
    out.to_csv(path, index=False)
    print(f"wrote {path.relative_to(REPO)}")
    with pd.option_context("display.width", 250, "display.max_colwidth", 120):
        print(out.to_string(index=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fetch", action="store_true", help="download ecoregions and provinces from GEE")
    ap.add_argument("--overlay", action="store_true", help="share of each region per ecoregion and province (default)")
    ap.add_argument("--k", type=int, default=C.REGIONS_K, help="which step 07 output to read")
    ap.add_argument("--forced", action="store_true", help="read the --force output of step 07 (D14)")
    ap.add_argument("--cover-by-fire", action="store_true", help="read the --cover-by-fire output of step 07")
    ap.add_argument("--team-edits", action="store_true", help="read the --team-edits output of step 07 (D16)")
    args = ap.parse_args()
    if args.fetch:
        fetch()
    if args.overlay or not args.fetch:
        overlay(args.k, args.forced, args.cover_by_fire, args.team_edits)


if __name__ == "__main__":
    main()
