import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

INPUT = (
    BASE
    / "data"
    / "processed"
    / "ml"
    / "real_event_training_dataset_coords.csv"
)

OUTPUT = (
    BASE
    / "data"
    / "processed"
    / "ml"
    / "real_event_training_dataset_final.csv"
)

print("=" * 70)
print("FIXING REMAINING NEGATIVE-SAMPLE COORDINATES")
print("=" * 70)

print("\n[1] Loading dataset...")

df = pd.read_csv(INPUT)

print("Rows:", len(df))

# ---------------------------------------------------------
# Verified district reference coordinates
# ---------------------------------------------------------
#
# These are district-town / district-HQ reference points.
# They are used ONLY for the six negative samples that
# could not inherit coordinates from real GSI events.
#
# They are NOT being presented as landslide-event locations.
# ---------------------------------------------------------

REFERENCE_COORDS = {
    ("NAGALAND", "kiphire"): (25.8867, 94.7863),

    ("ASSAM", "nagaon"): (26.3500, 92.6800),

    ("ASSAM", "biswanath"): (26.72836, 93.14955),

    ("ASSAM", "goalpara"): (26.184151, 90.633153),

    ("ASSAM", "kokrajhar"): (26.401070, 90.272860),
}

# ---------------------------------------------------------
# Normalize
# ---------------------------------------------------------

df["state"] = (
    df["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["district"] = (
    df["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# ---------------------------------------------------------
# Find missing coordinates
# ---------------------------------------------------------

missing = (
    (df["landslide_event"] == 0)
    &
    (
        df["latitude"].isna()
        |
        df["longitude"].isna()
    )
)

print("\n[2] Missing negative coordinates:")
print(
    df.loc[
        missing,
        ["state", "district", "event_date", "event_id"]
    ].to_string(index=False)
)

# ---------------------------------------------------------
# Fill coordinates
# ---------------------------------------------------------

print("\n[3] Applying reference coordinates...")

filled = 0

for idx in df.index[missing]:

    state = df.loc[idx, "state"]
    district = df.loc[idx, "district"]

    key = (state, district)

    if key not in REFERENCE_COORDS:
        print(
            "WARNING: No reference coordinate for:",
            state,
            district
        )
        continue

    lat, lon = REFERENCE_COORDS[key]

    df.loc[idx, "latitude"] = lat
    df.loc[idx, "longitude"] = lon

    filled += 1

    print(
        f"Filled {state} / {district}: "
        f"{lat}, {lon}"
    )

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

print("\n[4] Validation...")

positive_missing = (
    (
        df["landslide_event"] == 1
    )
    &
    (
        df["latitude"].isna()
        |
        df["longitude"].isna()
    )
).sum()

negative_missing = (
    (
        df["landslide_event"] == 0
    )
    &
    (
        df["latitude"].isna()
        |
        df["longitude"].isna()
    )
).sum()

print("Coordinates filled:", filled)
print("Positive samples missing coordinates:", positive_missing)
print("Negative samples missing coordinates:", negative_missing)

# ---------------------------------------------------------
# Final checks
# ---------------------------------------------------------

if positive_missing != 0:
    raise RuntimeError(
        "ERROR: Positive samples still have missing coordinates."
    )

if negative_missing != 0:
    raise RuntimeError(
        "ERROR: Negative samples still have missing coordinates."
    )

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

print("\n[5] Saving final coordinate-enabled dataset...")

df.to_csv(
    OUTPUT,
    index=False
)

print("\n" + "=" * 70)
print("FINAL COORDINATE DATASET COMPLETE")
print("=" * 70)

print("Output:")
print(OUTPUT)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nLABEL DISTRIBUTION:")
print(
    df["landslide_event"]
    .value_counts()
    .sort_index()
)

print("\nCOORDINATE NULL COUNTS:")
print(
    df[["latitude", "longitude"]]
    .isna()
    .sum()
)

print("\nSAMPLE:")
print(
    df.loc[
        df["event_id"].isin(
            ["NEG_1101", "NEG_1102", "NEG_1103",
            "NEG_1105", "NEG_1106", "NEG_1107"]
        ),
        [
            "event_id",
            "state",
            "district",
            "event_date",
            "latitude",
            "longitude",
            "landslide_event"
        ]
    ].to_string(index=False)
)

print("\nSUCCESS")