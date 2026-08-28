import os
import pandas as pd
import geopandas as gpd

# ============================================================
# PATHS
# ============================================================

rainfall_file =  r"D:\sih project\data\processed\rainfall\ner_rainfall_features.csv"

boundary_file = r"D:\sih project\data\raw\boundaries\india_districts.geojson"

output_folder = r"D:\sih project\data\processed\rainfall"

output_file = os.path.join(
    output_folder,
    "ner_district_rainfall.csv"
)

os.makedirs(output_folder, exist_ok=True)

# ============================================================
# NER STATES
# ============================================================

ner_states = [
    "ARUNACHAL PRADESH",
    "ASSAM",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "SIKKIM",
    "TRIPURA"
]

# ============================================================
# LOAD RAINFALL
# ============================================================

print("Loading rainfall data...")

rainfall = pd.read_csv(rainfall_file)

rainfall["date"] = pd.to_datetime(
    rainfall["date"]
)

print("Rainfall rows:", len(rainfall))

print("\nRainfall columns:")
print(rainfall.columns.tolist())

# ============================================================
# LOAD DISTRICT BOUNDARIES
# ============================================================

print("\nLoading district boundaries...")

gdf = gpd.read_file(boundary_file)

print("Boundary records:", len(gdf))

print("Boundary columns:")
print(gdf.columns.tolist())

print("CRS:", gdf.crs)

# ============================================================
# FIND STATE AND DISTRICT COLUMNS
# ============================================================

# The downloaded district file may use different column names.
# Detect common state/district column names automatically.

state_candidates = [
    "state",
    "STATE",
    "State",
    "st_nm",
    "ST_NM",
    "state_name",
    "STATE_NAME",
    "stname"
]

district_candidates = [
    "district",
    "DISTRICT",
    "District",
    "district_name",
    "DISTRICT_NAME",
    "dt_name",
    "DT_NAME",
    "name",
    "dtname"
]

state_column = None
district_column = None

for col in state_candidates:
    if col in gdf.columns:
        state_column = col
        break

for col in district_candidates:
    if col in gdf.columns:
        district_column = col
        break

print("\nDetected state column:", state_column)
print("Detected district column:", district_column)

# ============================================================
# STOP IF COLUMNS ARE NOT FOUND
# ============================================================

if state_column is None:
    print("\nERROR: State column was not found.")
    print("Available columns:")
    print(gdf.columns.tolist())
    raise SystemExit

if district_column is None:
    print("\nERROR: District column was not found.")
    print("Available columns:")
    print(gdf.columns.tolist())
    raise SystemExit

# ============================================================
# FILTER NER DISTRICTS
# ============================================================

print("\nFiltering NER districts...")

gdf[state_column] = (
    gdf[state_column]
    .astype(str)
    .str.strip()
)

gdf[district_column] = (
    gdf[district_column]
    .astype(str)
    .str.strip()
)

ner_gdf = gdf[
    gdf[state_column].isin(ner_states)
].copy()

print(
    "NER boundary records:",
    len(ner_gdf)
)

print("\nNER state counts:")

print(
    ner_gdf[state_column]
    .value_counts()
    .sort_index()
)

# ============================================================
# PREPARE RAINFALL POINTS
# ============================================================

print("\nCreating rainfall points...")

rainfall_gdf = gpd.GeoDataFrame(
    rainfall,
    geometry=gpd.points_from_xy(
        rainfall["longitude"],
        rainfall["latitude"]
    ),
    crs="EPSG:4326"
)

# ============================================================
# SPATIAL JOIN
# ============================================================

print("\nAssigning rainfall grid points to districts...")

rainfall_gdf = gpd.sjoin(
    rainfall_gdf,
    ner_gdf[
        [state_column, district_column, "geometry"]
    ],
    how="inner",
    predicate="within"
)

print(
    "Rainfall records assigned to districts:",
    len(rainfall_gdf)
)

# ============================================================
# RENAME STATE / DISTRICT
# ============================================================

rainfall_gdf = rainfall_gdf.rename(
    columns={
        state_column: "state",
        district_column: "district"
    }
)

# ============================================================
# REMOVE UNNECESSARY COLUMNS
# ============================================================

columns_to_keep = [
    "date",
    "state",
    "district",
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day"
]

rainfall_gdf = rainfall_gdf[
    columns_to_keep
]

# ============================================================
# DISTRICT-LEVEL AGGREGATION
# ============================================================

print("\nAggregating rainfall by district and date...")

district_rainfall = (
    rainfall_gdf
    .groupby(
        [
            "date",
            "state",
            "district"
        ],
        as_index=False
    )
    .agg(
        rainfall_mm=(
            "rainfall_mm",
            "mean"
        ),
        rainfall_24h=(
            "rainfall_24h",
            "mean"
        ),
        rainfall_3day=(
            "rainfall_3day",
            "mean"
        ),
        rainfall_7day=(
            "rainfall_7day",
            "mean"
        )
    )
)

# ============================================================
# SORT
# ============================================================

district_rainfall = district_rainfall.sort_values(
    [
        "state",
        "district",
        "date"
    ]
)

# ============================================================
# SAVE
# ============================================================

print("\nSaving district rainfall data...")

district_rainfall.to_csv(
    output_file,
    index=False
)

# ============================================================
# FINAL REPORT
# ============================================================

print("\n========== COMPLETE ==========")

print(
    "Output:",
    output_file
)

print(
    "Rows:",
    len(district_rainfall)
)

print(
    "Districts:",
    district_rainfall[
        ["state", "district"]
    ].drop_duplicates().shape[0]
)

print(
    "Date range:",
    district_rainfall["date"].min(),
    "to",
    district_rainfall["date"].max()
)

print("\nState-wise district counts:")

print(
    district_rainfall[
        ["state", "district"]
    ]
    .drop_duplicates()
    .groupby("state")
    .size()
)

print("\nSample:")

print(
    district_rainfall.head(20)
    .to_string(index=False)
)