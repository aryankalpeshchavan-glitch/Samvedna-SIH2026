from pathlib import Path
import pandas as pd
import geopandas as gpd


# ============================================================
# PATHS
# ============================================================

RAIN_FILE = Path(
    "data/processed/rainfall/nrt/imerg_1day_grid.csv"
)

BOUNDARY_FILE = Path(
    "data/raw/boundaries/gsi_districts/district_nwic.GeoJSON"
)

OUTPUT_FILE = Path(
    "data/processed/rainfall/nrt/imerg_current_district_features.csv"
)


# ============================================================
# CANONICAL NER STATES
# ============================================================

NER_STATES = [
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
]


# ============================================================
# 1. LOAD RAINFALL
# ============================================================

print("=" * 60)
print("NRT IMERG -> NER DISTRICT RAINFALL")
print("=" * 60)

print("\n[1] Loading NRT IMERG rainfall grid...")

rain = pd.read_csv(RAIN_FILE)

print(f"Rainfall rows: {len(rain):,}")
print(f"Rainfall columns: {list(rain.columns)}")

required_rain_cols = [
    "date",
    "latitude",
    "longitude",
    "rainfall_mm",
]

missing = [
    c for c in required_rain_cols
    if c not in rain.columns
]

if missing:
    raise ValueError(
        f"Missing rainfall columns: {missing}"
    )


# ============================================================
# 2. CLEAN RAINFALL
# ============================================================

print("\n[2] Cleaning rainfall data...")

rain["date"] = pd.to_datetime(
    rain["date"],
    errors="coerce"
)

rain["latitude"] = pd.to_numeric(
    rain["latitude"],
    errors="coerce"
)

rain["longitude"] = pd.to_numeric(
    rain["longitude"],
    errors="coerce"
)

rain["rainfall_mm"] = pd.to_numeric(
    rain["rainfall_mm"],
    errors="coerce"
)

rain = rain.dropna(
    subset=[
        "date",
        "latitude",
        "longitude",
        "rainfall_mm",
    ]
).copy()

print(
    "Rainfall date:",
    rain["date"].min().date(),
    "->",
    rain["date"].max().date()
)

print(
    "Rainfall range:",
    rain["rainfall_mm"].min(),
    "->",
    rain["rainfall_mm"].max(),
    "mm"
)


# ============================================================
# 3. LOAD DISTRICT BOUNDARIES
# ============================================================

print("\n[3] Loading NER district boundaries...")

gdf = gpd.read_file(
    BOUNDARY_FILE
)

print(f"Boundary rows: {len(gdf):,}")
print("Boundary CRS:", gdf.crs)

required_boundary_cols = [
    "state",
    "state_name",
    "district",
    "geometry",
]

missing_boundary = [
    c for c in required_boundary_cols
    if c not in gdf.columns
]

if missing_boundary:
    raise ValueError(
        f"Missing boundary columns: {missing_boundary}"
    )


# ============================================================
# 4. NORMALIZE STATE NAMES
# ============================================================

print("\n[4] Normalizing state names...")

gdf["state_name_normalized"] = (
    gdf["state_name"]
    .astype(str)
    .str.strip()
    .str.lower()
)

state_name_map = {
    "arunanchal pradesh": "Arunachal Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "sikkim": "Sikkim",
    "tripura": "Tripura",
}

gdf["state"] = (
    gdf["state_name_normalized"]
    .map(state_name_map)
)


# ============================================================
# 5. FILTER NER
# ============================================================

print("\n[5] Restricting boundaries to 8 NER states...")

gdf = gdf[
    gdf["state"].isin(NER_STATES)
].copy()

print(
    f"NER boundary rows: {len(gdf):,}"
)

if len(gdf) != 116:
    raise ValueError(
        f"Expected 116 NER districts, but found {len(gdf)}."
    )

print("\nDistrict count by state:")

print(
    gdf.groupby("state")
       .size()
       .sort_index()
       .to_string()
)


# ============================================================
# 6. VALIDATE GEOMETRIES
# ============================================================

print("\n[6] Validating geometries...")

invalid_before = (
    ~gdf.geometry.is_valid
).sum()

print(
    f"Invalid geometries before repair: {invalid_before}"
)

if invalid_before > 0:
    gdf["geometry"] = gdf.geometry.make_valid()

invalid_after = (
    ~gdf.geometry.is_valid
).sum()

print(
    f"Invalid geometries after repair: {invalid_after}"
)

if invalid_after > 0:
    raise ValueError(
        "Some district geometries remain invalid."
    )


# ============================================================
# 7. CONVERT TO WGS84
# ============================================================

print("\n[7] Converting boundaries to EPSG:4326...")

gdf = gdf.to_crs("EPSG:4326")


# ============================================================
# 8. NER BOUNDING BOX
# ============================================================

print("\n[8] Restricting rainfall grid to NER bounding box...")

minx, miny, maxx, maxy = gdf.total_bounds

print(
    f"NER bbox:"
    f"\n  longitude: {minx:.4f} -> {maxx:.4f}"
    f"\n  latitude:  {miny:.4f} -> {maxy:.4f}"
)

before_bbox = len(rain)

rain = rain[
    (rain["longitude"] >= minx) &
    (rain["longitude"] <= maxx) &
    (rain["latitude"] >= miny) &
    (rain["latitude"] <= maxy)
].copy()

print(
    f"Grid rows before bbox: {before_bbox:,}"
)

print(
    f"Grid rows after bbox:  {len(rain):,}"
)

if len(rain) == 0:
    raise ValueError(
        "No rainfall grid cells found inside NER bbox."
    )


# ============================================================
# 9. CREATE POINT GEOMETRIES
# ============================================================

print("\n[9] Creating rainfall grid points...")

rain_gdf = gpd.GeoDataFrame(
    rain,
    geometry=gpd.points_from_xy(
        rain["longitude"],
        rain["latitude"]
    ),
    crs="EPSG:4326"
)

print(
    f"Rainfall points: {len(rain_gdf):,}"
)


# ============================================================
# 10. SPATIAL JOIN
# ============================================================

print("\n[10] Spatially joining rainfall points to districts...")

districts = gdf[
    [
        "state",
        "district",
        "geometry",
    ]
].copy()

joined = gpd.sjoin(
    rain_gdf,
    districts,
    how="inner",
    predicate="within"
)

print(
    f"Matched rainfall points: {len(joined):,}"
)

if len(joined) == 0:
    raise ValueError(
        "Spatial join produced zero matches."
    )


# ============================================================
# 11. DISTRICT RAINFALL AGGREGATION
# ============================================================

print("\n[11] Aggregating rainfall by district...")

district_rain = (
    joined
    .groupby(
        [
            "state",
            "district",
            "date",
        ],
        as_index=False
    )
    .agg(
        rainfall_24h_mm=(
            "rainfall_mm",
            "mean"
        ),
        rainfall_24h_max_mm=(
            "rainfall_mm",
            "max"
        ),
        rainfall_24h_min_mm=(
            "rainfall_mm",
            "min"
        ),
        rainfall_24h_std_mm=(
            "rainfall_mm",
            "std"
        ),
        rainfall_grid_cells=(
            "rainfall_mm",
            "count"
        ),
    )
)

district_rain[
    "rainfall_24h_std_mm"
] = district_rain[
    "rainfall_24h_std_mm"
].fillna(0)


# ============================================================
# 12. CHECK DISTRICT COVERAGE
# ============================================================

print("\n[12] Validating district coverage...")

found_districts = (
    district_rain[
        ["state", "district"]
    ]
    .drop_duplicates()
)

print(
    f"Districts with rainfall: "
    f"{len(found_districts):,}"
)

print(
    f"States with rainfall: "
    f"{found_districts['state'].nunique()}"
)

print("\nDistrict count by state:")

state_counts = (
    found_districts
    .groupby("state")
    .size()
    .sort_index()
)

print(
    state_counts.to_string()
)

missing_states = sorted(
    set(NER_STATES)
    - set(found_districts["state"])
)

if missing_states:
    raise ValueError(
        f"States with no rainfall: {missing_states}"
    )

if len(found_districts) != 116:
    raise ValueError(
        f"Expected rainfall for 116 districts, "
        f"but found {len(found_districts)}."
    )


# ============================================================
# 13. CHECK FOR DUPLICATE DISTRICTS
# ============================================================

print("\n[13] Checking duplicates...")

duplicates = district_rain.duplicated(
    subset=[
        "state",
        "district",
        "date",
    ]
).sum()

print(
    f"Duplicate district-date rows: {duplicates}"
)

if duplicates > 0:
    raise ValueError(
        "Duplicate district-date rows detected."
    )


# ============================================================
# 14. SAVE
# ============================================================

print("\n[14] Saving district rainfall features...")

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

district_rain = district_rain.sort_values(
    [
        "state",
        "district",
    ]
).reset_index(drop=True)

district_rain.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 15. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("NRT RAINFALL FEATURE ENGINEERING COMPLETE")
print("=" * 60)

print(
    f"Output: {OUTPUT_FILE}"
)

print(
    f"Rows: {len(district_rain):,}"
)

print(
    f"Columns: {len(district_rain.columns)}"
)

print(
    "Districts:",
    district_rain[
        ["state", "district"]
    ].drop_duplicates().shape[0]
)

print(
    "Rainfall date:",
    district_rain["date"].min().date()
)

print("\nSample:")
print(
    district_rain.head(10).to_string(
        index=False
    )
)