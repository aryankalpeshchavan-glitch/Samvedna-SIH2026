import os
import shutil
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ML_DATASET = r"data\processed\rainfall\ml_training_dataset.csv"
LANDSLIDE_EVENTS = r"data\landslide_events.csv"

AUDIT_DIR = r"data\processed\audit"

PROXY_OUTPUT = os.path.join(
    AUDIT_DIR,
    "rainfall_proxy_dataset.csv"
)

EVENT_OUTPUT = os.path.join(
    AUDIT_DIR,
    "real_landslide_events.csv"
)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(AUDIT_DIR, exist_ok=True)


print("\n==============================================")
print("     CRISISCORE LABEL SEPARATION")
print("==============================================")


# ============================================================
# LOAD RAINFALL DATASET
# ============================================================

print("\nLoading rainfall ML dataset...")

rainfall_df = pd.read_csv(ML_DATASET)

print("Rows:", len(rainfall_df))
print("Columns:", len(rainfall_df.columns))


# ============================================================
# IDENTIFY PROXY LABEL COLUMNS
# ============================================================

proxy_columns = [
    "risk_score",
    "risk_class",
    "risk_label"
]

existing_proxy_columns = [
    col for col in proxy_columns
    if col in rainfall_df.columns
]

print("\nProxy label columns found:")

for col in existing_proxy_columns:
    print("-", col)


# ============================================================
# SAVE RAINFALL PROXY DATASET
# ============================================================

rainfall_df.to_csv(
    PROXY_OUTPUT,
    index=False
)

print("\nRainfall proxy dataset saved:")
print(PROXY_OUTPUT)


# ============================================================
# LOAD REAL LANDSLIDE EVENTS
# ============================================================

print("\nLoading real landslide events...")

events_df = pd.read_csv(LANDSLIDE_EVENTS)

print("Event rows:", len(events_df))

print("\nEvent columns:")

for col in events_df.columns:
    print("-", col)


# ============================================================
# SAVE REAL EVENT DATASET
# ============================================================

events_df.to_csv(
    EVENT_OUTPUT,
    index=False
)

print("\nReal landslide event dataset saved:")
print(EVENT_OUTPUT)


# ============================================================
# EVENT SUMMARY
# ============================================================

print("\n==============================================")
print("           EVENT DATA SUMMARY")
print("==============================================")

print("\nEvents by state:")

print(
    events_df["state"]
    .value_counts()
)


print("\nEvents with district:")

if "district" in events_df.columns:

    district_available = (
        events_df["district"]
        .notna()
        .sum()
    )

    district_missing = (
        events_df["district"]
        .isna()
        .sum()
    )

    print("With district:", district_available)
    print("Without district:", district_missing)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n==============================================")
print("       STEP 2 COMPLETE")
print("==============================================")

print("""
RAINFAILL PROXY DATA:
  Kept for baseline/reference.
  NOT treated as ground-truth landslide labels.

REAL LANDSLIDE EVENTS:
  Separated into independent dataset.
  Will be used to construct 24h / 48h / 72h targets.

Next:
  STEP 3 - Create proper 24h / 48h / 72h targets
""")

print("==============================================")