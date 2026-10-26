#!/usr/bin/env python
"""scripts/bench_redcap.py: how long REDCAP (pygeoda, full order, Ward) takes on N contiguous H3 res 6
cells, to choose the resolution of step 07. Reads data/tables/variables.parquet; writes nothing.

The N cells are the nearest to (-61, -30). Only the seven fire variables, standardized; k = 10.
pygeoda is not a project dependency yet, so run it in a throwaway environment:

    uv run --with pygeoda python scripts/bench_redcap.py 2000
    /usr/bin/time -l uv run --with pygeoda python scripts/bench_redcap.py 24000   # also peak memory

Results: docs/notes/07-redcap_scaling.md.
"""
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from utils import constants as C  # noqa: E402

FIRE_VARS = ["rate", "cv", "recurrence", "peak_sin", "peak_cos", "season_len", "large_share"]


def main():
    import geopandas as gpd
    import pandas as pd
    import pygeoda

    n = int(sys.argv[1])
    g = gpd.read_parquet(REPO / C.H3_GRID_DIR / f"h3_res{C.H3_RES}.parquet")
    v = pd.read_parquet(REPO / C.TABLES_DIR / "variables.parquet").set_index("cell")
    c = g.geometry.representative_point()
    sub = g.loc[((c.x + 61.0) ** 2 + (c.y + 30.0) ** 2).sort_values().index[:n]].reset_index(drop=True)
    X = v.loc[sub.cell, FIRE_VARS]
    X = (X - X.mean()) / X.std(ddof=0)
    w = pygeoda.rook_weights(pygeoda.open(sub[["cell", "geometry"]]))
    t = time.time()
    r = pygeoda.redcap(10, w, pd.DataFrame(X.to_numpy(), columns=FIRE_VARS),
                       method="fullorder-wardlinkage", scale_method="raw")
    print(f"n {n}  mean neighbours {w.mean_neighbors():.2f}  redcap k=10 {time.time() - t:.1f} s  "
          f"between/total {r['The ratio of between to total sum of squares']:.3f}")


if __name__ == "__main__":
    main()
