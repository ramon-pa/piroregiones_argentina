"""Single source of truth: asset ids, years, the native grid, task naming.

Every value here was read from GEE or from the fire team's repo; where each one was verified is
recorded in CLAUDE.md, "GEE asset paths". Docs and scripts import from here and never restate a
value. No ``ee.*`` call at module level: this file must import without ``ee.Initialize()``.
"""

# --- GEE ---------------------------------------------------------------------------------------
# Compute project. Overridable with the GEE_PROJECT environment variable (see .env.example).
GEE_PROJECT = "mapbiomas-argentina"

# Every task description starts with this, so our tasks are distinguishable in a shared project.
TASK_PREFIX = "piro"

# --- Years -------------------------------------------------------------------------------------
FIRE_YEARS = list(range(1999, 2026))  # 1999-2025 inclusive, fire collection 1

# Land cover is read from the year BEFORE the fire: the cover of a burned pixel in the fire year can
# already be a consequence of the fire. Same rule as the fire team's ATBD ("MapBiomas Argentina
# land cover") and statistics ("The land-cover year: we cross the PREVIOUS one").
LULC_YEAR_OFFSET = -1

# --- Fire, MapBiomas Argentina Fuego collection 1 ----------------------------------------------
_FIRE_ROOT = "projects/mapbiomas-argentina/assets/FIRE/COLLECTION-1"

# Month of burn, one image per calendar year, on the native grid.
MONTH_OF_BURN_COL = f"{_FIRE_ROOT}/CLASSIFICATION_COLLECTIONS/collection1_fire_mask_v2"
MONTH_OF_BURN_IMAGE = "mapbiomas_argentina_fire_collection1_fire_mask_v2_{year}"
MONTH_OF_BURN_BAND = "burned_monthly"

# Scar size class (1-8) per burned pixel, one band per year, on the native grid. The band is named
# scar_area_ha_<year> on purpose (fire repo, 07-published_products.md). Unburned pixels are MASKED,
# exactly where the month of burn is masked (checked in Córdoba for 2003, 2013, 2020).
SCAR_SIZE = (f"{_FIRE_ROOT}/FINAL_PRODUCTS/"
             "mapbiomas_argentina_fire_collection1_annual_burned_scar_size_range_v2")
SCAR_SIZE_BAND = "scar_area_ha_{year}"

# Years burned 1999-2025 per pixel (decision D8). Stored in EPSG:3857 @ 30 m, OFF the native grid:
# it is reduced on its own grid, weighted by pixelArea(), and never crossed pixel by pixel with
# land cover. selfMask'ed: never burned is MASKED, not 0.
FREQUENCY = f"{_FIRE_ROOT}/FINAL_PRODUCTS/mapbiomas_argentina_fire_collection1_frequency_burned_v2"
FREQUENCY_BAND = "fire_frequency_1999_2025"
FREQUENCY_CRS = "EPSG:3857"
# Its own 30 m grid, read from the asset (projection().getInfo(), 2026-10-26). Step 04 reduces on
# it, so no pixel of the product is resampled.
FREQUENCY_TRANSFORM = [30, 0, -8189460, 0, -30, -2483190]

# NOT used: the other 07d subproducts. They are in EPSG:3857, off the native grid, and the
# *_coverage variants cross the SAME land-cover year, not Y-1 (CLAUDE.md, "GEE asset paths").

# --- Land cover, MapBiomas Argentina collection 3 ----------------------------------------------
LULC = ("projects/mapbiomas-argentina/assets/LAND-COVER/COLLECTION-3/INTEGRATION/"
        "mapbiomas_argentina_collection3_pb")
LULC_BAND = "classification_{year}"

# Burnable verdict per col-3 class, copied from the fire repo (statistics/legends.py, BURNABLE and
# NON_BURNABLE) so our percentages share their denominator (decision D9). 0 and 27 are "not
# observed": in neither list, they enter no denominator. Highest class code is 77.
BURNABLE_CLASSES = [1, 3, 4, 6, 9, 14, 15, 18, 19, 21, 36, 10, 11, 12, 63, 66, 73, 77]
NON_BURNABLE_CLASSES = [22, 24, 25, 26, 33, 34]
NOT_OBSERVED_CLASSES = [0, 27]  # masked LULC pixels are unmasked to 0 so their area stays visible
# Classes with no burn-rate variable of their own (decision D10): the product drops every object
# over 40 % agriculture (fire repo, 07-vector_to_raster.md, "Object exclusion ruleset"), so their
# rate is low by construction. They stay in the burnable denominator (D9).
RATE_EXCLUDED_CLASSES = [19]

# --- Ecoregions, Burkart et al. 1999 (APN) -----------------------------------------------------
_ANC_VEC = "projects/mapbiomas-argentina/assets/ANCILLARY_DATA/VECTOR/ARG"
ECOREGIONS_13 = f"{_ANC_VEC}/ARG-Political_Level_2-13Ecorregiones_3857"  # GEOCODE is a number
ECOREGIONS_16 = f"{_ANC_VEC}/ARG-Political_Level_2-16Ecorregiones_3857"  # GEOCODE is a STRING
ECOREGION_NAME_FIELD = "LEVEL_2"

# Area of interest (utils/aoi.py): the 13 ecoregions minus this one, simplified in GEE. With these
# two values the H3 res 6 grid has 96,461 cells (scripts/h3_cells_argentina.py, 2026-10-19).
AOI_EXCLUDE = "Islas del Atlántico Sur"
AOI_SIMPLIFY_M = 500

# --- Native grid -------------------------------------------------------------------------------
# The fire product's 30 m lattice (the fire team's SNIC_CRS / SNIC_TRANSFORM). Pin both on every
# export: scale=30 in EPSG:4326 is a different grid.
GRID_CRS = "EPSG:4326"
GRID_TRANSFORM = [0.000269494585236, 0, -73.58468801489491,
                  0, -0.000269494585236, -21.764113209062533]

# --- H3 grid and the packed code of the yearly sweep (decision D6) ------------------------------
H3_RES = 6  # extraction resolution; res 5 is built locally by summing children (decision D1)
H3_GRID_DIR = "data/h3_grid"  # local copy (GeoParquet) and the shapefile zip to upload, out of git
# Rectangle every national reduction runs over (W, S, E, N): the bounds of the H3 res 6 grid
# (-73.654, -55.102, -53.578, -21.743, from h3_res6.parquet, 2026-10-26) padded outward. Hardcoded
# because .geometry().bounds() on the 96k-feature asset fails ("too many edges").
GRID_BBOX = [-73.7, -55.2, -53.5, -21.7]

# code = cell * CODE_CELL + class * CODE_CLASS + month * CODE_MONTH + size_class
# month 0..12 and size 0..8 (0 = not burned) fit below CODE_CLASS (12*10 + 8 = 128 < 130); class
# 0..77 fits below 100; ~96.5k cells * 13,000 = ~1.26e9 < 2**31 - 1. GEE computes it as a wider
# integer, never a float (measured, docs/notes/02-sweep_cordoba.md).
CODE_CELL = 13_000
CODE_CLASS = 130
CODE_MONTH = 10

# --- Outputs (decision D7) ---------------------------------------------------------------------
# GEE assets: only what GEE reads again (the H3 grid) and the final regions. Folder created by Iván
# on 2026-10-19; write access checked the same day.
OUTPUT_ROOT = "projects/mapbiomas-argentina/assets/FIRE/COLLECTION-1/ANALYSES/pyrorregions"
H3_GRID_ASSET = f"{OUTPUT_ROOT}/h3_res{H3_RES}"  # uploaded by hand from H3_GRID_DIR (step 01)
# Tables (one CSV per task) go to this folder of the user's own Drive and are analysed locally.
DRIVE_FOLDER = "piro_gee"
SWEEP_TASK = TASK_PREFIX + "_sweep_{year}"  # task description and CSV name of step 02, per year
SWEEP_DIR = "data/sweep"  # where the step 02 CSVs are downloaded from Drive, out of git
# Step 04: code = cell * FREQ_CODE_CELL + years burned (1..27).
FREQ_CODE_CELL = 100
FREQ_TASK = TASK_PREFIX + "_freq_1999_2025"  # task description and CSV name of step 04
FREQ_DIR = "data/frequency"  # where the step 04 CSV is downloaded from Drive, out of git
TABLES_DIR = "data/tables"  # step 05: the decoded Parquet tables every local step reads, out of git
