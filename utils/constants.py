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

# Scar area (ha) per burned pixel, one band per year, on the native grid.
SCAR_AREA = (f"{_FIRE_ROOT}/FINAL_PRODUCTS/"
             "mapbiomas_argentina_fire_collection1_annual_burned_area_ha_v2")
SCAR_AREA_BAND = "scar_area_ha_{year}"

# NOT used: the 07d subproducts (annual_burned_coverage_v2, frequency_burned_v2, ...) are stored in
# EPSG:3857, off the native grid, and their *_coverage variants cross the SAME year, not Y-1.

# --- Land cover, MapBiomas Argentina collection 3 ----------------------------------------------
LULC = ("projects/mapbiomas-argentina/assets/LAND-COVER/COLLECTION-3/INTEGRATION/"
        "mapbiomas_argentina_collection3_pb")
LULC_BAND = "classification_{year}"

# --- Ecoregions, Burkart et al. 1999 (APN) -----------------------------------------------------
_ANC_VEC = "projects/mapbiomas-argentina/assets/ANCILLARY_DATA/VECTOR/ARG"
ECOREGIONS_13 = f"{_ANC_VEC}/ARG-Political_Level_2-13Ecorregiones_3857"  # GEOCODE is a number
ECOREGIONS_16 = f"{_ANC_VEC}/ARG-Political_Level_2-16Ecorregiones_3857"  # GEOCODE is a STRING
ECOREGION_NAME_FIELD = "LEVEL_2"

# --- Native grid -------------------------------------------------------------------------------
# The fire product's 30 m lattice (the fire team's SNIC_CRS / SNIC_TRANSFORM). Pin both on every
# export: scale=30 in EPSG:4326 is a different grid.
GRID_CRS = "EPSG:4326"
GRID_TRANSFORM = [0.000269494585236, 0, -73.58468801489491,
                  0, -0.000269494585236, -21.764113209062533]
