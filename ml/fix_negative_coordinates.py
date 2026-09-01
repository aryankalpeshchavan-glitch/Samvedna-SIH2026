import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "data" / "processed" / "ml" / "real_event_training_dataset.csv"
OUTPUT = BASE / "data" / "processed" / "ml" / "real_event_training_dataset_coords.csv"

print("=" * 70)
print("FIXING NEGATIVE-SAMPLE COORDINATES")
print("=" * 70)

print("\n[1] Loading dataset...")
df = pd.read_csv(INPUT)

print("Rows:", len(df))
print("Positive:", (df["landslide_event"] == 1).sum())
print("Negative:", (df["landslide_event"] == 0).sum())

# Normalize district names
df["state"] = df["state"].astype(str).str.strip().str.upper()
df["district"] = df["district"].astype(str).str.strip().str.lower()

# ---------------------------------------------------------
# Build location lookup from REAL GSI EVENTS
# ---------------------------------------------------------

print("\n[2] Building district coordinate lookup...")

positive = df[df["landslide_event"] == 1].copy()

positive["latitude"] = pd.to_numeric(
    positive["latitude"], errors="coerce"
)

positive["longitude"] = pd.to_numeric(
    positive["longitude"], errors="coerce"
)

positive = positive.dropna(
    subset=["latitude", "longitude"]
)

# Median coordinate for each state/district
location_lookup = (
    positive
    .groupby(["state", "district"])[["latitude", "longitude"]]
    .median()
    .reset_index()
)

print("District coordinate groups:", len(location_lookup))

# ---------------------------------------------------------
# Assign coordinates to negative samples
# ---------------------------------------------------------

print("\n[3] Assigning coordinates to negative samples...")

df = df.merge(
    location_lookup,
    on=["state", "district"],
    how="left",
    suffixes=("", "_lookup")
)

negative = df["landslide_event"] == 0

df.loc[negative, "latitude"] = df.loc[
    negative, "latitude_lookup"
]

df.loc[negative, "longitude"] = df.loc[
    negative, "longitude_lookup"
]

df.drop(
    columns=["latitude_lookup", "longitude_lookup"],
    inplace=True
)

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("\n[4] Validation...")

print(
    "Positive coordinates:",
    df.loc[
        df["landslide_event"] == 1,
        ["latitude", "longitude"]
    ].notna().all(axis=1).sum()
)

print(
    "Negative coordinates:",
    df.loc[
        df["landslide_event"] == 0,
        ["latitude", "longitude"]
    ].notna().all(axis=1).sum()
)

missing_negative = df.loc[
    negative,
    ["latitude", "longitude"]
].isna().any(axis=1).sum()

print("Negative samples still missing coordinates:", missing_negative)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

df.to_csv(OUTPUT, index=False)

print("\n" + "=" * 70)
print("COORDINATE-ENABLED DATASET COMPLETE")
print("=" * 70)

print("Output:")
print(OUTPUT)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nLABEL DISTRIBUTION:")
print(df["landslide_event"].value_counts())

print("\nNULL COORDINATES:")
print(
    df[["latitude", "longitude"]]
    .isna()
    .sum()
)

print("\nSUCCESS")