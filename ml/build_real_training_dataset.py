import os
import numpy as np
import pandas as pd
print("SCRIPT STARTED", flush=True)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

POSITIVE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_landslide_event_dataset.csv"
)

RAINFALL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "rainfall",
    "risk_prediction_dataset.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_event_training_dataset.csv"
)

RANDOM_SEED = 42

# Number of negatives per real event
NEGATIVE_RATIO = 1


# ============================================================
# FEATURES
# ============================================================

FEATURE_COLUMNS = [
    "state",
    "district",
    "rainfall_mm",
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


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("BUILDING REAL-EVENT ML TRAINING DATASET")
print("=" * 70)


# ============================================================
# LOAD POSITIVE EVENTS
# ============================================================

print("\n[1] Loading real GSI landslide events...")

if not os.path.exists(POSITIVE_FILE):
    raise FileNotFoundError(
        f"Positive dataset not found:\n{POSITIVE_FILE}"
    )

positive = pd.read_csv(POSITIVE_FILE)

positive["event_date"] = pd.to_datetime(
    positive["event_date"],
    errors="coerce"
)

positive["state"] = (
    positive["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)

positive["district"] = (
    positive["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)

positive = positive.dropna(
    subset=["event_date", "state", "district"]
)

positive = positive.drop_duplicates(
    subset=["event_id"]
)

positive["landslide_event"] = 1

print("Real positive events:", len(positive))


# ============================================================
# LOAD RAINFALL
# ============================================================

print("\n[2] Loading rainfall dataset...")

if not os.path.exists(RAINFALL_FILE):
    raise FileNotFoundError(
        f"Rainfall dataset not found:\n{RAINFALL_FILE}"
    )

rainfall = pd.read_csv(RAINFALL_FILE)

rainfall["date"] = pd.to_datetime(
    rainfall["date"],
    errors="coerce"
)

rainfall["state"] = (
    rainfall["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)

rainfall["district"] = (
    rainfall["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)

print("Rainfall rows:", len(rainfall))


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_rainfall = [
    "date",
    "state",
    "district",
    "rainfall_mm",
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

missing = [
    c for c in required_rainfall
    if c not in rainfall.columns
]

if missing:
    raise ValueError(
        "Missing rainfall columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# REMOVE INVALID RAINFALL ROWS
# ============================================================

rainfall = rainfall.dropna(
    subset=["date", "state", "district"]
).copy()


# ============================================================
# CREATE EVENT KEY
# ============================================================

print("\n[3] Creating event exclusion keys...")

positive["event_key"] = (
    positive["state"].astype(str)
    + "|"
    + positive["district"].astype(str)
    + "|"
    + positive["event_date"].dt.strftime("%Y-%m-%d")
)

event_keys = set(
    positive["event_key"]
)

print("Known event dates:", len(event_keys))


# ============================================================
# REMOVE GSI EVENT DAYS
# ============================================================

print("\n[4] Removing known landslide-event days...")

rainfall["event_key"] = (
    rainfall["state"].astype(str)
    + "|"
    + rainfall["district"].astype(str)
    + "|"
    + rainfall["date"].dt.strftime("%Y-%m-%d")
)

before = len(rainfall)

rainfall = rainfall[
    ~rainfall["event_key"].isin(event_keys)
].copy()

after = len(rainfall)

print("Rainfall candidates before:", before)
print("Rainfall candidates after :", after)


# ============================================================
# TEMPORAL SAFETY WINDOW
# ============================================================

print("\n[5] Applying temporal exclusion window...")

# Avoid sampling negatives immediately around known events.
#
# We exclude:
# event date
# 1 day before
# 1 day after
#
# This prevents an event's precursor rainfall from being
# incorrectly labelled as a negative sample.

event_windows = set()

for d in positive["event_date"].dropna():

    for offset in [-1, 0, 1]:

        event_windows.add(
            d + pd.Timedelta(days=offset)
        )

rainfall["date_only"] = rainfall["date"].dt.normalize()

before = len(rainfall)

rainfall = rainfall[
    ~rainfall["date_only"].isin(event_windows)
].copy()

after = len(rainfall)

print("Candidates before window:", before)
print("Candidates after window :", after)


# ============================================================
# STATE / DISTRICT BALANCING
# ============================================================

print("\n[6] Selecting negative samples...")

rng = np.random.default_rng(
    RANDOM_SEED
)

negative_parts = []

# Number of negatives required
required_negative_count = (
    len(positive) * NEGATIVE_RATIO
)

# ------------------------------------------------------------
# First try: sample negatives from same state/district
# distribution as positives.
# ------------------------------------------------------------

positive_groups = (
    positive
    .groupby(
        ["state", "district"],
        dropna=False
    )
    .size()
    .reset_index(name="positive_count")
)

for _, group in positive_groups.iterrows():

    state = group["state"]
    district = group["district"]

    n_required = int(
        group["positive_count"]
        * NEGATIVE_RATIO
    )

    candidates = rainfall[
        (rainfall["state"] == state)
        &
        (rainfall["district"] == district)
    ].copy()

    if len(candidates) == 0:
        continue

    n = min(
        n_required,
        len(candidates)
    )

    if n > 0:

        selected_indices = rng.choice(
            candidates.index.to_numpy(),
            size=n,
            replace=False
        )

        selected = candidates.loc[
            selected_indices
        ].copy()

        negative_parts.append(
            selected
        )


# ============================================================
# COMBINE NEGATIVES
# ============================================================

if not negative_parts:

    raise RuntimeError(
        "Could not generate any negative samples."
    )

negative = pd.concat(
    negative_parts,
    ignore_index=True
)


# ============================================================
# GLOBAL FILL IF REQUIRED
# ============================================================

if len(negative) < required_negative_count:

    remaining_needed = (
        required_negative_count
        - len(negative)
    )

    used_keys = set(
        negative["event_key"]
    )

    candidates = rainfall[
        ~rainfall["event_key"].isin(
            used_keys
        )
    ].copy()

    remaining_needed = min(
        remaining_needed,
        len(candidates)
    )

    if remaining_needed > 0:

        selected_indices = rng.choice(
            candidates.index.to_numpy(),
            size=remaining_needed,
            replace=False
        )

        extra = candidates.loc[
            selected_indices
        ].copy()

        negative = pd.concat(
            [
                negative,
                extra
            ],
            ignore_index=True
        )


# ============================================================
# NEGATIVE LABEL
# ============================================================

negative["event_id"] = (
    "NEG_"
    + negative.index.astype(str)
)

negative["event_date"] = (
    negative["date"]
)

negative["latitude"] = np.nan
negative["longitude"] = np.nan

negative["landslide_event"] = 0


# ============================================================
# PREPARE POSITIVES
# ============================================================

positive_final = positive.copy()

positive_final["date"] = (
    positive_final["event_date"]
)


# ============================================================
# BUILD FINAL DATASET
# ============================================================

print("\n[7] Building final dataset...")

positive_final = positive_final[
    [
        "event_id",
        "event_date",
        "state",
        "district",
        "latitude",
        "longitude",
        "rainfall_mm",
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
        "landslide_event",
    ]
].copy()


negative_final = negative[
    [
        "event_id",
        "event_date",
        "state",
        "district",
        "latitude",
        "longitude",
        "rainfall_mm",
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
        "landslide_event",
    ]
].copy()


# ============================================================
# COMBINE
# ============================================================

final = pd.concat(
    [
        positive_final,
        negative_final
    ],
    ignore_index=True
)


# ============================================================
# SHUFFLE
# ============================================================

final = final.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

final.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("REAL-EVENT ML DATASET COMPLETE")
print("=" * 70)

print("\nOutput:")
print(OUTPUT_FILE)

print("\nRows:", len(final))
print("Columns:", len(final.columns))

print("\nLABEL DISTRIBUTION:")
print(
    final["landslide_event"]
    .value_counts()
    .sort_index()
)

print("\nLABEL PERCENTAGES:")
print(
    (
        final["landslide_event"]
        .value_counts(normalize=True)
        * 100
    )
    .sort_index()
    .round(2)
)

print("\nSTATES:")
print(
    final["state"]
    .value_counts()
)

print("\nDISTRICTS:", final["district"].nunique())

print("\nNULL COUNTS:")
print(
    final.isna().sum()
)

print("\nSAMPLE:")
print(
    final.head(10).to_string(index=False)
)

print("\n" + "=" * 70)
print("SUCCESS")
print("=" * 70)