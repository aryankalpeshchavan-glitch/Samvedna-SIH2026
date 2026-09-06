import os
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

RAINFALL_FILE = "data/processed/rainfall/nrt/imerg_current_district_features.csv"
SOIL_FILE = "data/processed/soil/smap_current_district_features.csv"

OUTPUT_DIR = "data/processed/features"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "current_ner_risk_features.csv"
)


# ============================================================
# STATE NORMALIZATION
# ============================================================

STATE_MAP = {
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

NER_STATES = {
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
}


def normalize_state(series):
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map(STATE_MAP)
    )


def normalize_district(series):
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )


# ============================================================
# 1. LOAD RAINFALL
# ============================================================

print("\n[1/6] Loading rainfall features...")

rain = pd.read_csv(RAINFALL_FILE)

print("Rainfall shape:", rain.shape)
print("Rainfall columns:")
print(rain.columns.tolist())


# ============================================================
# 2. LOAD SOIL
# ============================================================

print("\n[2/6] Loading soil features...")

soil = pd.read_csv(SOIL_FILE)

print("Soil shape:", soil.shape)
print("Soil columns:")
print(soil.columns.tolist())


# ============================================================
# 3. NORMALIZE KEYS
# ============================================================

print("\n[3/6] Normalizing district keys...")

rain["state"] = normalize_state(rain["state"])
soil["state"] = normalize_state(soil["state"])

rain["district_key"] = normalize_district(rain["district"])
soil["district_key"] = normalize_district(soil["district"])

if rain["state"].isna().any():
    raise ValueError("Unknown state found in rainfall data.")

if soil["state"].isna().any():
    raise ValueError("Unknown state found in soil data.")

rain = rain[rain["state"].isin(NER_STATES)].copy()
soil = soil[soil["state"].isin(NER_STATES)].copy()

print("Rainfall districts:", len(rain))
print("Soil districts:", len(soil))


# ============================================================
# DUPLICATE CHECK
# ============================================================

if rain.duplicated(
    subset=["state", "district_key"]
).any():
    raise ValueError(
        "Duplicate district found in rainfall data."
    )

if soil.duplicated(
    subset=["state", "district_key"]
).any():
    raise ValueError(
        "Duplicate district found in soil data."
    )


# ============================================================
# COVERAGE CHECK
# ============================================================

rain_keys = set(
    zip(rain["state"], rain["district_key"])
)

soil_keys = set(
    zip(soil["state"], soil["district_key"])
)

missing_from_rain = soil_keys - rain_keys
missing_from_soil = rain_keys - soil_keys

if missing_from_rain:
    print("\nMissing from rainfall:")
    for key in sorted(missing_from_rain):
        print(key)

if missing_from_soil:
    print("\nMissing from soil:")
    for key in sorted(missing_from_soil):
        print(key)

if missing_from_rain or missing_from_soil:
    raise ValueError(
        "Rainfall and soil district coverage do not match."
    )

print("Coverage check: 116/116 districts matched.")


# ============================================================
# PREPARE DATES
# ============================================================

rain = rain.rename(
    columns={"date": "rainfall_date"}
)

soil["observation_time"] = pd.to_datetime(
    soil["observation_time"],
    utc=True,
    errors="coerce"
)

if soil["observation_time"].isna().any():
    raise ValueError(
        "Invalid soil observation timestamps found."
    )

soil = soil.rename(
    columns={
        "observation_time": "soil_observation_time"
    }
)


# ============================================================
# 4. MERGE
# ============================================================

print("\n[4/6] Merging rainfall + soil...")

merged = pd.merge(
    rain,
    soil,
    on=["state", "district_key"],
    how="inner",
    suffixes=("_rain", "_soil")
)

print("Merged rows:", len(merged))

if len(merged) != 116:
    raise ValueError(
        f"Expected 116 districts, got {len(merged)}"
    )


# ============================================================
# DISTRICT NAME
# ============================================================

merged["district"] = merged["district_rain"]

merged.drop(
    columns=[
        "district_rain",
        "district_soil"
    ],
    inplace=True,
    errors="ignore"
)


# ============================================================
# 5. DATA FRESHNESS
# ============================================================

print("\n[5/6] Calculating data freshness...")

merged["rainfall_date"] = pd.to_datetime(
    merged["rainfall_date"],
    errors="coerce"
)

rainfall_timestamp = (
    merged["rainfall_date"]
    .dt.tz_localize("UTC")
)

merged["rainfall_age_hours"] = (
    merged["soil_observation_time"]
    - rainfall_timestamp
).dt.total_seconds() / 3600


# All soil records are already the latest
# observation for each district.
latest_soil_time = merged[
    "soil_observation_time"
].max()

merged["soil_age_hours"] = (
    latest_soil_time
    - merged["soil_observation_time"]
).dt.total_seconds() / 3600


# ============================================================
# 6. SELECT MODEL FEATURES
# ============================================================

print("\n[6/6] Selecting model features...")

feature_columns = [

    # -------------------------
    # IDENTIFIERS
    # -------------------------

    "state",
    "district",
    "district_key",

    # -------------------------
    # RAINFALL
    # -------------------------

    "rainfall_date",
    "rainfall_24h_mm",
    "rainfall_24h_max_mm",
    "rainfall_24h_min_mm",
    "rainfall_24h_std_mm",
    "rainfall_grid_cells",

    # -------------------------
    # SOIL TIME
    # -------------------------

    "soil_observation_time",

    # -------------------------
    # SOIL MOISTURE
    # -------------------------

    "soil_surface_moisture",
    "soil_rootzone_moisture",
    "soil_profile_moisture",

    # -------------------------
    # SOIL WETNESS
    # -------------------------

    "soil_surface_wetness",
    "soil_rootzone_wetness",
    "soil_profile_wetness",

    # -------------------------
    # SOIL PERCENTILES
    # -------------------------

    "soil_rootzone_percentile",
    "soil_profile_percentile",

    # -------------------------
    # SURFACE MOISTURE CHANGE
    # -------------------------

    "sm_surface_change_3h",
    "sm_surface_change_6h",
    "sm_surface_change_24h",

    # -------------------------
    # ROOTZONE MOISTURE CHANGE
    # -------------------------

    "sm_rootzone_change_3h",
    "sm_rootzone_change_6h",
    "sm_rootzone_change_24h",

    # -------------------------
    # PROFILE MOISTURE CHANGE
    # -------------------------

    "sm_profile_change_3h",
    "sm_profile_change_6h",
    "sm_profile_change_24h",

    # -------------------------
    # SURFACE WETNESS CHANGE
    # -------------------------

    "sm_surface_wetness_change_3h",
    "sm_surface_wetness_change_6h",
    "sm_surface_wetness_change_24h",

    # -------------------------
    # ROOTZONE WETNESS CHANGE
    # -------------------------

    "sm_rootzone_wetness_change_3h",
    "sm_rootzone_wetness_change_6h",
    "sm_rootzone_wetness_change_24h",

    # -------------------------
    # PROFILE WETNESS CHANGE
    # -------------------------

    "sm_profile_wetness_change_3h",
    "sm_profile_wetness_change_6h",
    "sm_profile_wetness_change_24h",

    # -------------------------
    # GRID COVERAGE
    # -------------------------

    "soil_moisture_grid_cells",

    # -------------------------
    # FRESHNESS
    # -------------------------

    "soil_moisture_age_hours",
    "rainfall_age_hours",
    "soil_age_hours",
]


# ============================================================
# VERIFY COLUMNS
# ============================================================

missing = [
    col
    for col in feature_columns
    if col not in merged.columns
]

if missing:

    print("\nERROR: Missing columns:")

    for col in missing:
        print("  ", col)

    raise ValueError(
        "Required feature columns are missing."
    )


features = merged[
    feature_columns
].copy()


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n==============================================")
print("FINAL VALIDATION")
print("==============================================")

print("Rows:", len(features))
print("Columns:", len(features.columns))

print("\nState coverage:")

print(
    features[
        "state"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nUnique districts:")

print(
    features[
        ["state", "district"]
    ]
    .drop_duplicates()
    .shape[0]
)

print("\nMissing values:")

missing_values = (
    features
    .isna()
    .sum()
    .sort_values(
        ascending=False
    )
)

print(
    missing_values[
        missing_values > 0
    ].to_string()
)

print("\nRainfall age statistics:")

print(
    features[
        "rainfall_age_hours"
    ]
    .describe()
    .to_string()
)

print("\nSoil age statistics:")

print(
    features[
        "soil_age_hours"
    ]
    .describe()
    .to_string()
)


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

features.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUCCESS
# ============================================================

print("\n==============================================")
print("CURRENT NER FEATURE TABLE CREATED")
print("==============================================")

print("Output:")
print(OUTPUT_FILE)

print("\nRows:", len(features))
print("Columns:", len(features.columns))
print("Districts:", features["district"].nunique())
print("States:", features["state"].nunique())

print("\nRainfall date:")
print(
    features["rainfall_date"].min(),
    "->",
    features["rainfall_date"].max()
)

print("\nSoil observation:")
print(
    features["soil_observation_time"].min(),
    "->",
    features["soil_observation_time"].max()
)

print("\nSUCCESS")
print("==============================================")