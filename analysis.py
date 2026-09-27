# ============================================================
# DYNAMIC WORLD V1 + SENTINEL-2
# KECAMATAN MEDAN MAIMUN
# PERIODE: 1 JANUARI 2016 - 31 DESEMBER 2016
# ============================================================

import ee
import geemap

# ------------------------------------------------------------
# 1. INITIALIZE GOOGLE EARTH ENGINE
# ------------------------------------------------------------

try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()


# ------------------------------------------------------------
# 2. LOAD maimun.geojson
# ------------------------------------------------------------

# Pastikan file berada di folder yang sama dengan notebook/script
maimun_fc = geemap.geojson_to_ee("maimun.geojson")

# Geometry seluruh Kecamatan Medan Maimun
maimun = maimun_fc.geometry()


# ------------------------------------------------------------
# 3. DATE RANGE
# ------------------------------------------------------------

START = ee.Date("2016-01-01")
END   = ee.Date("2017-01-01")


# ------------------------------------------------------------
# 4. FILTER DYNAMIC WORLD + SENTINEL-2
# ------------------------------------------------------------

col_filter = ee.Filter.And(
    ee.Filter.bounds(maimun),
    ee.Filter.date(START, END)
)


# Dynamic World
dw_col = (
    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filter(col_filter)
)


# Sentinel-2
s2_col = (
    ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
    .filter(col_filter)
)


# ------------------------------------------------------------
# 5. PRINT INFORMATION
# ------------------------------------------------------------

print(
    "Jumlah Dynamic World images:",
    dw_col.size().getInfo()
)

print(
    "Jumlah Sentinel-2 images:",
    s2_col.size().getInfo()
)


# ------------------------------------------------------------
# 6. LINK DYNAMIC WORLD TO SENTINEL-2
# ------------------------------------------------------------

linked_col = dw_col.linkCollection(
    s2_col,
    ["B4", "B3", "B2"]
)


# ------------------------------------------------------------
# 7. TAKE ONE EXAMPLE IMAGE
# ------------------------------------------------------------

linked_image = ee.Image(
    linked_col
    .sort("system:time_start")
    .first()
)


print(
    "Tanggal image:",
    ee.Date(
        linked_image.get("system:time_start")
    ).format("YYYY-MM-dd").getInfo()
)


# ------------------------------------------------------------
# 8. DYNAMIC WORLD CLASSES
# ------------------------------------------------------------

CLASS_NAMES = [
    "water",
    "trees",
    "grass",
    "flooded_vegetation",
    "crops",
    "shrub_and_scrub",
    "built",
    "bare",
    "snow_and_ice"
]


VIS_PALETTE = [
    "419bdf",  # water
    "397d49",  # trees
    "88b053",  # grass
    "7a87c6",  # flooded vegetation
    "e49635",  # crops
    "dfc35a",  # shrub & scrub
    "c4281b",  # built
    "a59b8f",  # bare
    "b39fe1"   # snow & ice
]


# ------------------------------------------------------------
# 9. CREATE DYNAMIC WORLD RGB
# ------------------------------------------------------------

dw_rgb = (
    linked_image
    .select("label")
    .visualize({
        "min": 0,
        "max": 8,
        "palette": VIS_PALETTE
    })
    .divide(255)
)


# ------------------------------------------------------------
# 10. GET TOP-1 CLASS PROBABILITY
# ------------------------------------------------------------

top1_prob = (
    linked_image
    .select(CLASS_NAMES)
    .reduce(ee.Reducer.max())
)


# ------------------------------------------------------------
# 11. HILLSHADE
# ------------------------------------------------------------

top1_prob_hillshade = (
    ee.Terrain
    .hillshade(
        top1_prob.multiply(100)
    )
    .divide(255)
)


# ------------------------------------------------------------
# 12. BLEND LABEL + PROBABILITY
# ------------------------------------------------------------

dw_rgb_hillshade = (
    dw_rgb
    .multiply(top1_prob_hillshade)
)


# ------------------------------------------------------------
# 13. DISPLAY MAP
# ------------------------------------------------------------

m = geemap.Map()

m.center_object(maimun, 13)


# Boundary Medan Maimun
m.add_layer(
    maimun_fc,
    {"color": "red"},
    "Kecamatan Medan Maimun"
)


# Sentinel-2 RGB
m.add_layer(
    linked_image,
    {
        "min": 0,
        "max": 3000,
        "bands": ["B4", "B3", "B2"]
    },
    "Sentinel-2"
)


# Dynamic World
m.add_layer(
    dw_rgb_hillshade,
    {
        "min": 0,
        "max": 0.65
    },
    "Dynamic World V1 - Land Cover"
)


m
