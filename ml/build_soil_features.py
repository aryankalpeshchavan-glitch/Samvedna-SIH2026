from pathlib import Path
import pandas as pd
import numpy as np


INPUT_FILE = Path(
    "data/processed/soil/smap_current_district_soil_moisture.csv"
)

OUTPUT_FILE = Path(
    "data/processed/soil/smap_current_district_features.csv"
)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("[1] Loading district soil-moisture data...")

df = pd.read_csv(INPUT_FILE)

print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")


# ============================================================
# 2. TIMESTAMP
# ============================================================

print("\n[2] Processing timestamps...")

if "observation_time" not in df.columns:
    raise ValueError(
        "Missing required column: observation_time"
    )

df["observation_time"] = pd.to_datetime(
    df["observation_time"],
    utc=True,
    errors="coerce"
)

if df["observation_time"].isna().any():
    raise ValueError(
        "Some observation_time values could not be parsed."
    )

df = df.sort_values(
    ["state", "district", "observation_time"]
).reset_index(drop=True)

print(
    "Observation range:",
    df["observation_time"].min(),
    "->",
    df["observation_time"].max()
)


# ============================================================
# 3. DEFINE PRIMARY SOIL FEATURES
# ============================================================

print("\n[3] Selecting primary soil-moisture features...")

soil_features = [
    "sm_surface_mean",
    "sm_rootzone_mean",
    "sm_profile_mean",

    "sm_surface_wetness_mean",
    "sm_rootzone_wetness_mean",
    "sm_profile_wetness_mean",

    "sm_rootzone_pctl_mean",
    "sm_profile_pctl_mean",
]

missing = [
    col for col in soil_features
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing expected soil columns: {missing}"
    )

print("Using:")
for col in soil_features:
    print("  -", col)


# ============================================================
# 4. CREATE TEMPORAL CHANGE FEATURES
# ============================================================

print("\n[4] Creating temporal soil-moisture features...")

group_cols = ["state", "district"]

# SMAP observations are approximately every 3 hours.
# 1 step  = ~3h
# 2 steps = ~6h
# 8 steps = ~24h

for base_col in [
    "sm_surface_mean",
    "sm_rootzone_mean",
    "sm_profile_mean",
]:
    short_name = base_col.replace("_mean", "")

    df[f"{short_name}_change_3h"] = (
        df.groupby(group_cols)[base_col]
        .diff(1)
    )

    df[f"{short_name}_change_6h"] = (
        df.groupby(group_cols)[base_col]
        .diff(2)
    )

    df[f"{short_name}_change_24h"] = (
        df.groupby(group_cols)[base_col]
        .diff(8)
    )


# ============================================================
# 5. CREATE WETNESS CHANGE FEATURES
# ============================================================

print("\n[5] Creating soil-wetness change features...")

for base_col in [
    "sm_surface_wetness_mean",
    "sm_rootzone_wetness_mean",
    "sm_profile_wetness_mean",
]:
    short_name = base_col.replace("_mean", "")

    df[f"{short_name}_change_3h"] = (
        df.groupby(group_cols)[base_col]
        .diff(1)
    )

    df[f"{short_name}_change_6h"] = (
        df.groupby(group_cols)[base_col]
        .diff(2)
    )

    df[f"{short_name}_change_24h"] = (
        df.groupby(group_cols)[base_col]
        .diff(8)
    )


# ============================================================
# 6. KEEP LATEST OBSERVATION FOR EACH DISTRICT
# ============================================================

print("\n[6] Selecting latest observation per district...")

latest = (
    df.sort_values("observation_time")
      .groupby(group_cols, as_index=False)
      .tail(1)
      .copy()
)

latest = latest.sort_values(
    ["state", "district"]
).reset_index(drop=True)

print(f"Latest district rows: {len(latest):,}")


# ============================================================
# 7. RENAME PRIMARY FEATURES
# ============================================================

print("\n[7] Creating model-friendly feature names...")

rename_map = {
    "sm_surface_mean":
        "soil_surface_moisture",

    "sm_rootzone_mean":
        "soil_rootzone_moisture",

    "sm_profile_mean":
        "soil_profile_moisture",

    "sm_surface_wetness_mean":
        "soil_surface_wetness",

    "sm_rootzone_wetness_mean":
        "soil_rootzone_wetness",

    "sm_profile_wetness_mean":
        "soil_profile_wetness",

    "sm_rootzone_pctl_mean":
        "soil_rootzone_percentile",

    "sm_profile_pctl_mean":
        "soil_profile_percentile",
}

latest = latest.rename(columns=rename_map)


# ============================================================
# 8. SOIL MOISTURE AGE
# ============================================================

print("\n[8] Calculating soil-moisture data age...")

latest_timestamp = latest["observation_time"].max()

latest["soil_moisture_age_hours"] = (
    latest_timestamp - latest["observation_time"]
).dt.total_seconds() / 3600.0


# ============================================================
# 9. DATA QUALITY
# ============================================================

print("\n[9] Checking data quality...")

latest["soil_moisture_grid_cells"] = (
    pd.to_numeric(
        latest["soil_moisture_grid_cells"],
        errors="coerce"
    )
)

numeric_cols = latest.select_dtypes(
    include=[np.number]
).columns

missing_summary = (
    latest[numeric_cols]
    .isna()
    .sum()
)

print("\nMissing values in important features:")

for col in numeric_cols:
    missing_count = missing_summary[col]

    if missing_count > 0:
        print(
            f"  {col}: {missing_count}"
        )


# ============================================================
# 10. SAVE SELECTED FEATURES
# ============================================================

print("\n[10] Selecting final feature columns...")

final_features = [
    "observation_time",
    "state",
    "district",

    # Soil moisture
    "soil_surface_moisture",
    "soil_rootzone_moisture",
    "soil_profile_moisture",

    # Wetness
    "soil_surface_wetness",
    "soil_rootzone_wetness",
    "soil_profile_wetness",

    # Percentiles
    "soil_rootzone_percentile",
    "soil_profile_percentile",

    # Moisture changes
    "sm_surface_change_3h",
    "sm_surface_change_6h",
    "sm_surface_change_24h",

    "sm_rootzone_change_3h",
    "sm_rootzone_change_6h",
    "sm_rootzone_change_24h",

    "sm_profile_change_3h",
    "sm_profile_change_6h",
    "sm_profile_change_24h",

    # Wetness changes
    "sm_surface_wetness_change_3h",
    "sm_surface_wetness_change_6h",
    "sm_surface_wetness_change_24h",

    "sm_rootzone_wetness_change_3h",
    "sm_rootzone_wetness_change_6h",
    "sm_rootzone_wetness_change_24h",

    "sm_profile_wetness_change_3h",
    "sm_profile_wetness_change_6h",
    "sm_profile_wetness_change_24h",

    # Metadata
    "soil_moisture_grid_cells",
    "soil_moisture_age_hours",
]

missing_final = [
    col for col in final_features
    if col not in latest.columns
]

if missing_final:
    raise ValueError(
        f"Final feature columns missing: {missing_final}"
    )

output = latest[final_features].copy()


# ============================================================
# 11. SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

output.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n============================================")
print("SOIL FEATURE ENGINEERING COMPLETE")
print("============================================")

print(f"Output: {OUTPUT_FILE}")
print(f"Rows: {len(output):,}")
print(f"Columns: {len(output.columns)}")

print(
    "\nStates:",
    output["state"].nunique()
)

print(
    "Districts:",
    output["district"].nunique()
)

print(
    "Latest timestamp:",
    output["observation_time"].max()
)

print("\nSample:")
print(
    output[
        [
            "state",
            "district",
            "soil_surface_moisture",
            "soil_rootzone_moisture",
            "soil_profile_moisture",
            "sm_surface_change_3h",
            "sm_surface_change_24h",
        ]
    ].head(10).to_string(index=False)
)