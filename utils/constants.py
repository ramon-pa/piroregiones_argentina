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

# --- MapBiomas fire regions (for the fire team's land-cover families, step 06) -----------------
# Region-id raster of the fire repo (utils/constants.py REGION_RASTER, built by its
# scripts/export_region_raster.py), on the land-cover grid, with a 2 km buffer past the border:
# 1 CUYO, 2 PAT, 3 PAMPA, 4 CHACO, 5 BA (Bosque Atlántico), 0 outside. Same numbering as
# region_num in its config/veg_fire_remap.csv.
REGION_RASTER = "projects/mapbiomas-argentina/assets/ANCILLARY_DATA/RASTER/ARG/ARG-Regiones-MapBiomas-buffer2km"
REGION_BAND = "region_id"
REGION_NAMES = {1: "CUYO", 2: "PAT", 3: "PAMPA", 4: "CHACO", 5: "BA"}
# Land-cover family per (region, class): the fire team's veg_fire classes (fire repo,
# collection-01/config/veg_fire_remap.csv, built on col-2 per statistics/legends.py) with the region
# suffix dropped, e.g. forest-cerr_chaco and forest_pat are both "forest". Generated from that CSV
# on 2026-10-26, not typed by hand. Non-burnable and non-observed rows left out. A (region, class)
# pair missing here falls back to the class's most common family (step 06 reports that area).
FAMILY_BY_REGION_CLASS = {
    (1, 3): "forest",
    (1, 4): "forest",
    (1, 9): "agriculture",
    (1, 11): "grassland",
    (1, 12): "grassland",
    (1, 19): "agriculture",
    (1, 21): "grassland",
    (1, 63): "grassland",
    (1, 66): "shrubland",
    (1, 77): "shrubland",
    (2, 3): "forest",
    (2, 6): "forest",
    (2, 9): "forest",
    (2, 11): "grassland",
    (2, 12): "grassland",
    (2, 21): "agriculture",
    (2, 63): "grassland",
    (2, 73): "grassland",
    (2, 77): "shrubland",
    (3, 3): "forest",
    (3, 4): "forest",
    (3, 6): "forest",
    (3, 9): "forest",
    (3, 11): "grassland",
    (3, 12): "grassland",
    (3, 15): "grassland",
    (3, 19): "agriculture",
    (3, 36): "forest",
    (3, 66): "shrubland",
    (3, 77): "shrubland",
    (4, 3): "forest",
    (4, 4): "forest",
    (4, 6): "forest",
    (4, 9): "forest",
    (4, 11): "grassland",
    (4, 12): "grassland",
    (4, 15): "pasture",
    (4, 19): "agriculture",
    (4, 36): "agri_perennial",
    (4, 63): "shrubland",
    (4, 66): "shrubland",
    (4, 77): "shrubland",
    (5, 3): "forest",
    (5, 9): "forest",
    (5, 11): "grassland",
    (5, 12): "grassland",
    (5, 15): "pasture",
    (5, 19): "pasture",
    (5, 36): "agri_perennial",
}
FAMILIES = ["forest", "shrubland", "grassland", "pasture", "agriculture", "agri_perennial"]

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
REGION_TASK = TASK_PREFIX + "_cell_region"  # step 06: area of each region per cell
REGION_DIR = "data/region"  # where the step 06 region CSV is downloaded, out of git
TABLES_DIR = "data/tables"  # step 05: the decoded Parquet tables every local step reads, out of git

# --- Step 07: pyroregions (decisions D5, D13) --------------------------------------------------
REGIONS_RES = 5  # REDCAP at res 6 does not fit this Mac (docs/notes/07-redcap_scaling.md); D13
REGIONS_K = 12   # Ramón, 2026-10-27, from the maps of k = 12, 15 and 20 and the tree of splits (D5, D14)
# Minimum region area: twice the largest fire recorded (Erni et al. 2020, citing O'Neill et al.
# 1996), with the largest scar of the country, 219,410 ha in 2003 (fire repo constants.py).
MIN_REGION_KM2 = 2 * 219_410 / 100
COMPOSITION_WEIGHT = 0.2  # land-cover families vs 1.0 for each fire variable (Boulanger et al. 2014, p. 368; D12)
REGIONS_DIR = "data/regions"  # step 07 outputs, out of git
# Burn rate and recurrence enter the clustering as logarithms, as Segura-Garcia et al. 2025 do with
# burned area and frequency ("Methods", (c)(i)): the rate spans 1e-5 to 20 % per year, and on a
# linear scale everything under ~1 % looks alike. log10(rate + LOG_RATE_OFFSET) for the rate, whose
# 0 (cells without fire) has no logarithm; the offset is our choice, not a paper's.
LOG_RATE_OFFSET = 0.001  # % of burnable area per year
# Cells with less burnable area than this share of their area (water, salt flats, rock) stay out of
# the clustering and join their most common neighbouring region afterwards: in the first draft they
# made a region of their own in the Rio de la Plata. Our threshold, not a paper's (D13).
MIN_BURNABLE_SHARE = 0.10
# Decision D14: the k = REGIONS_K map plus pieces of a deeper level of the same REDCAP tree (the
# regions are nested, so a deeper piece lies inside one region). Each piece is named by a point in
# it, not by its number, which depends on k. The two Patagonian pieces are where the northern
# Andean-Patagonian forest and its ecotone burn: 0.34 and 0.41 % per year against 0.05 % for the
# rest of Patagonia (docs/notes/07-regions_draft.md). `07-regions.py --force`.
FORCED_SPLIT_K = 20
FORCED_SPLIT_POINTS = {"oeste de Chubut": (-43.0, -71.4), "oeste de Neuquén": (-40.0, -70.9)}  # lat, lon

# --- Step 09: where each region falls -----------------------------------------------------------
# Provinces: FAO GAUL 2025, the 500 m simplified version (the 2015 one is deprecated in GEE).
PROVINCES = "FAO/GAUL_SIMPLIFIED_500m/2025/level1"
PROVINCE_ISO3 = "ARG"
PROVINCE_NAME_FIELD = "GAUL1_NAME"
ANCILLARY_SIMPLIFY_M = 1000  # simplification before download; cells are matched by their centre
ANCILLARY_DIR = "data/ancillary"  # ecoregions and provinces as GeoParquet, out of git
