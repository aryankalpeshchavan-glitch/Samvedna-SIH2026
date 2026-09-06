from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "ml_training_dataset.csv"
)

TARGET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "events"
    / "landslide_event_targets.csv"
)

TERRAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
    / "terrain_district_features.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "landslide_ml_dataset.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

RAIN_FEATURES = [
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
]

TERRAIN_FEATURES = [
    "elevation_mean_m",
    "elevation_min_m",
    "elevation_max_m",
    "elevation_std_m",
    "slope_mean_deg",
    "slope_max_deg",
    "slope_std_deg",
]

TARGET = "landslide_24h"


# ============================================================
# HELPER
# ============================================================

def make_key(state, district):

    return (
        state.astype(str)
        .str.strip()
        .str.lower()
        + "|"
        +
        district.astype(str)
        .str.strip()
        .str.lower()
    )


# ============================================================
# LOAD RAINFALL DATA
# ============================================================

print("\n[1/6] Loading historical rainfall data...")

rain = pd.read_csv(
    RAIN_FILE
)

print(
    f"Rainfall shape: "
    f"{rain.shape}"
)

print(
    f"Rainfall date range: "
    f"{rain['date'].min()} -> "
    f"{rain['date'].max()}"
)


# ============================================================
# LOAD TARGET DATA
# ============================================================

print("\n[2/6] Loading landslide targets...")

targets = pd.read_csv(
    TARGET_FILE
)

print(
    f"Target shape: "
    f"{targets.shape}"
)

print(
    f"Target columns: "
    f"{targets.columns.tolist()}"
)


# ============================================================
# LOAD TERRAIN
# ============================================================

print("\n[3/6] Loading terrain features...")

terrain = pd.read_csv(
    TERRAIN_FILE
)

print(
    f"Terrain shape: "
    f"{terrain.shape}"
)


# ============================================================
# CREATE DISTRICT KEYS
# ============================================================

print("\n[4/6] Creating district keys...")


rain["district_key"] = make_key(
    rain["state"],
    rain["district"]
)

targets["district_key"] = make_key(
    targets["state"],
    targets["district"]
)

terrain["district_key"] = (
    terrain["district_key"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ============================================================
# CHECK DISTRICT COVERAGE
# ============================================================

rain_districts = set(
    rain["district_key"]
    .dropna()
    .unique()
)

target_districts = set(
    targets["district_key"]
    .dropna()
    .unique()
)

terrain_districts = set(
    terrain["district_key"]
    .dropna()
    .unique()
)

print(
    f"Rainfall districts: "
    f"{len(rain_districts)}"
)

print(
    f"Target districts: "
    f"{len(target_districts)}"
)

print(
    f"Terrain districts: "
    f"{len(terrain_districts)}"
)

print(
    "Rainfall ∩ terrain: "
    f"{len(rain_districts & terrain_districts)}"
)


# ============================================================
# SELECT TARGET COLUMNS
# ============================================================

target_columns = [
    "date",
    "state",
    "district",
    "district_key",
    TARGET,
    "landslide_48h",
    "landslide_72h",
]

missing_target_columns = [
    c
    for c in target_columns
    if c not in targets.columns
]

if missing_target_columns:

    raise KeyError(
        "Missing target columns: "
        +
        str(
            missing_target_columns
        )
    )

targets_small = targets[
    target_columns
].copy()


# ============================================================
# CHECK TARGET DUPLICATES
# ============================================================

duplicate_targets = (
    targets_small
    .duplicated(
        subset=[
            "date",
            "district_key",
        ]
    )
    .sum()
)

print(
    f"Duplicate target rows: "
    f"{duplicate_targets}"
)

if duplicate_targets > 0:

    raise ValueError(
        "Duplicate date + district "
        "target rows detected."
    )


# ============================================================
# MERGE RAINFALL + TARGET
# ============================================================

print(
    "\nMerging rainfall with targets..."
)

df = rain.merge(
    targets_small,
    on=[
        "date",
        "state",
        "district",
        "district_key",
    ],
    how="left",
    suffixes=(
        "",
        "_target"
    ),
)


# ============================================================
# TARGET MISSINGNESS
# ============================================================

print(
    f"Merged rows: "
    f"{len(df)}"
)

target_missing = (
    df[TARGET]
    .isna()
    .sum()
)

print(
    f"Missing {TARGET}: "
    f"{target_missing}"
)


# ============================================================
# MISSING TARGET = NO EVENT
# ============================================================
#
# The target file contains event positives.
# Dates without a recorded event are therefore treated
# as negative examples (0).
#
# This is appropriate for this inventory-based target,
# but source limitations will be documented later.
# ============================================================

df[TARGET] = (
    df[TARGET]
    .fillna(0)
    .astype(int)
)

df["landslide_48h"] = (
    df["landslide_48h"]
    .fillna(0)
    .astype(int)
)

df["landslide_72h"] = (
    df["landslide_72h"]
    .fillna(0)
    .astype(int)
)


# ============================================================
# MERGE TERRAIN
# ============================================================

print(
    "\nMerging terrain features..."
)

terrain_small = terrain[
    [
        "district_key"
    ]
    +
    TERRAIN_FEATURES
    +
    [
        "terrain_grid_cells"
    ]
].copy()


# ------------------------------------------------------------
# Check duplicate terrain keys
# ------------------------------------------------------------

duplicate_terrain = (
    terrain_small
    .duplicated(
        subset=[
            "district_key"
        ]
    )
    .sum()
)

print(
    f"Duplicate terrain districts: "
    f"{duplicate_terrain}"
)

if duplicate_terrain > 0:

    raise ValueError(
        "Duplicate terrain district keys."
    )


df = df.merge(
    terrain_small,
    on="district_key",
    how="left",
)


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n[5/6] Validating ML dataset..."
)

print(
    f"Final shape: "
    f"{df.shape}"
)

print(
    f"Date range: "
    f"{df['date'].min()} -> "
    f"{df['date'].max()}"
)

print(
    f"Unique districts: "
    f"{df['district_key'].nunique()}"
)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print(
    "\nTarget distribution:"
)

print(
    df[TARGET]
    .value_counts()
    .sort_index()
    .to_string()
)

positive_count = int(
    df[TARGET].sum()
)

negative_count = (
    len(df)
    -
    positive_count
)

positive_rate = (
    positive_count
    /
    len(df)
    *
    100
)

print(
    f"\nPositive samples: "
    f"{positive_count}"
)

print(
    f"Negative samples: "
    f"{negative_count}"
)

print(
    f"Positive rate: "
    f"{positive_rate:.4f}%"
)


# ============================================================
# TERRAIN MISSINGNESS
# ============================================================

print(
    "\nTerrain missing values:"
)

terrain_missing = (
    df[TERRAIN_FEATURES]
    .isna()
    .sum()
)

print(
    terrain_missing.to_string()
)


# ============================================================
# TERRAIN COVERAGE
# ============================================================

zero_terrain = (
    df["terrain_grid_cells"]
    .fillna(0)
    == 0
)

print(
    f"\nRows with zero terrain cells: "
    f"{zero_terrain.sum()}"
)


# ============================================================
# CHECK INF VALUES
# ============================================================

numeric_columns = (
    RAIN_FEATURES
    +
    TERRAIN_FEATURES
)

inf_count = np.isinf(
    df[numeric_columns]
    .select_dtypes(
        include=[np.number]
    )
).sum().sum()

print(
    f"Infinity values: "
    f"{inf_count}"
)

if inf_count > 0:

    print(
        "Replacing infinity with NaN..."
    )

    df[numeric_columns] = (
        df[numeric_columns]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )


# ============================================================
# SELECT FINAL ML COLUMNS
# ============================================================

final_columns = [
    "date",
    "state",
    "district",
    "district_key",
]
final_columns += RAIN_FEATURES
final_columns += TERRAIN_FEATURES
final_columns += [
    "terrain_grid_cells",
    TARGET,
    "landslide_48h",
    "landslide_72h",
]

df = df[
    final_columns
].copy()


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df["date"] = pd.to_datetime(
    df["date"]
)

df = (
    df
    .sort_values(
        [
            "date",
            "district_key",
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# FINAL DUPLICATE CHECK
# ============================================================

duplicates = (
    df
    .duplicated(
        subset=[
            "date",
            "district_key",
        ]
    )
    .sum()
)

print(
    f"\nFinal duplicate "
    f"date-district rows: "
    f"{duplicates}"
)

if duplicates > 0:

    raise ValueError(
        "Final dataset contains "
        "duplicate date-district rows."
    )


# ============================================================
# SAVE
# ============================================================

print(
    "\n[6/6] Saving ML dataset..."
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    f"\nSUCCESS!"
)

print(
    f"Saved to:\n{OUTPUT_FILE}"
)

print(
    f"\nFinal shape: "
    f"{df.shape}"
)

print(
    "\nFinal columns:"
)

for i, col in enumerate(
    df.columns,
    start=1
):

    print(
        f"{i:2d}. {col}"
    )