import os
import json
import random
import pandas as pd

BASE = r"D:\sih project"

EVENT_FILE = os.path.join(
    BASE, "data", "processed", "landslide",
    "gsi_ner_exact_date_events.csv"
)

RAINFALL_FILE = os.path.join(
    BASE, "data", "processed", "rainfall",
    "ml_training_dataset.csv"
)

OUT_DIR = os.path.join(
    BASE, "data", "processed", "ml"
)

OUT_FILE = os.path.join(
    OUT_DIR, "final_landslide_ml_dataset.csv"
)

AUDIT_FILE = os.path.join(
    OUT_DIR, "final_ml_dataset_audit.json"
)

SEED = 42


def norm_state(s):
    return (
        s.astype(str)
        .str.strip()
        .str.upper()
    )


def norm_district(s):
    return (
        s.astype(str)
        .str.strip()
        .str.lower()
        .str.replace("-", " ", regex=False)
        .str.replace("_", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def main():

    print("=" * 70)
    print("CRISISCORE PHASE 2 - FINAL ML DATASET")
    print("=" * 70)

    os.makedirs(OUT_DIR, exist_ok=True)

    # ---------------------------------------------------------
    # 1. LOAD GSI EVENTS
    # ---------------------------------------------------------

    print("\n[1] Loading GSI events...")

    events = pd.read_csv(EVENT_FILE)

    events["event_date"] = pd.to_datetime(
        events["event_date"],
        errors="coerce"
    )

    events = events[
        (events["event_date"] >= "2015-01-01") &
        (events["event_date"] <= "2025-12-31")
    ].copy()

    events["_state"] = norm_state(events["state"])
    events["_district"] = norm_district(events["district"])

    events = events.drop_duplicates(
        subset=["event_id"],
        keep="first"
    )

    print("In-range GSI events:", len(events))

    # ---------------------------------------------------------
    # 2. LOAD RAINFALL
    # ---------------------------------------------------------

    print("\n[2] Loading rainfall dataset...")

    rain = pd.read_csv(RAINFALL_FILE)

    rain["date"] = pd.to_datetime(
        rain["date"],
        errors="coerce"
    )

    rain["_state"] = norm_state(rain["state"])
    rain["_district"] = norm_district(rain["district"])

    # IMPORTANT:
    # Remove duplicate rainfall keys.
    # We need exactly one rainfall feature row
    # for each state + district + date.

    key = ["_state", "_district", "date"]

    duplicate_keys = rain.duplicated(
        subset=key,
        keep=False
    ).sum()

    print("Duplicate rainfall key rows:", duplicate_keys)

    rain = (
        rain
        .sort_values(key)
        .drop_duplicates(
            subset=key,
            keep="first"
        )
        .copy()
    )

    print("Rainfall rows after key deduplication:", len(rain))

    # ---------------------------------------------------------
    # 3. JOIN POSITIVE EVENTS
    # ---------------------------------------------------------

    print("\n[3] Joining landslide events with rainfall...")

    joined = events.merge(
        rain,
        left_on=["_state", "_district", "event_date"],
        right_on=["_state", "_district", "date"],
        how="inner",
        suffixes=("_event", "_rain")
    )

    joined = joined.drop_duplicates(
        subset=["event_id"],
        keep="first"
    )

    print("Unique positive events joined:", len(joined))

    # ---------------------------------------------------------
    # 4. CREATE POSITIVE DATASET
    # ---------------------------------------------------------

    feature_cols = [
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
        "rainfall_risk_score",
    ]

    feature_cols = [
        c for c in feature_cols
        if c in joined.columns
    ]

    positive_cols = [
        "event_id",
        "event_date",
        "state_event",
        "district_event",
        "latitude",
        "longitude",
    ] + feature_cols

    positive_cols = [
        c for c in positive_cols
        if c in joined.columns
    ]

    positive = joined[positive_cols].copy()

    positive = positive.rename(
        columns={
            "state_event": "state",
            "district_event": "district",
        }
    )

    positive["landslide_event"] = 1

    # ---------------------------------------------------------
    # 5. BUILD NEGATIVE POOL
    # ---------------------------------------------------------

    print("\n[4] Building negative/background pool...")

    # Only use rainfall rows belonging to the 8 NER states.
    ner_states = {
        "ARUNACHAL PRADESH",
        "ASSAM",
        "MANIPUR",
        "MEGHALAYA",
        "MIZORAM",
        "NAGALAND",
        "SIKKIM",
        "TRIPURA",
    }

    negative_pool = rain[
        rain["_state"].isin(ner_states)
    ].copy()

    # We must NOT select a rainfall row that is already
    # associated with a known GSI event.

    positive_keys = set(
        zip(
            positive["_state"] if "_state" in positive.columns
            else norm_state(positive["state"]),
            positive["_district"] if "_district" in positive.columns
            else norm_district(positive["district"]),
            pd.to_datetime(positive["event_date"])
        )
    )

    negative_pool["_event_key"] = list(
        zip(
            negative_pool["_state"],
            negative_pool["_district"],
            negative_pool["date"]
        )
    )

    negative_pool = negative_pool[
        ~negative_pool["_event_key"].isin(positive_keys)
    ].copy()

    print("Negative candidate rows:", len(negative_pool))

    # ---------------------------------------------------------
    # 6. SAMPLE 1:1 NEGATIVES
    # ---------------------------------------------------------

    n_positive = len(positive)

    if len(negative_pool) < n_positive:
        raise RuntimeError(
            f"Not enough negative samples: "
            f"{len(negative_pool)} available, "
            f"{n_positive} required."
        )

    random.seed(SEED)

    negative = negative_pool.sample(
        n=n_positive,
        random_state=SEED
    ).copy()

    negative["event_id"] = [
        f"NEG_{i:05d}"
        for i in range(1, len(negative) + 1)
    ]

    negative["event_date"] = negative["date"]

    negative = negative.rename(
        columns={
            "state": "state",
            "district": "district",
        }
    )

    negative["landslide_event"] = 0

    # ---------------------------------------------------------
    # 7. STANDARDIZE NEGATIVE COLUMNS
    # ---------------------------------------------------------

    negative_cols = [
        "event_id",
        "event_date",
        "state",
        "district",
    ] + feature_cols + [
        "landslide_event"
    ]

    negative_cols = [
        c for c in negative_cols
        if c in negative.columns
    ]

    negative = negative[negative_cols].copy()

    # ---------------------------------------------------------
    # 8. STANDARDIZE POSITIVE COLUMNS
    # ---------------------------------------------------------

    positive["_state"] = norm_state(positive["state"])
    positive["_district"] = norm_district(positive["district"])

    positive_cols_final = [
        "event_id",
        "event_date",
        "state",
        "district",
    ] + feature_cols + [
        "landslide_event"
    ]

    positive = positive[positive_cols_final].copy()

    # ---------------------------------------------------------
    # 9. COMBINE
    # ---------------------------------------------------------

    print("\n[5] Combining positive + negative samples...")

    final = pd.concat(
        [positive, negative],
        ignore_index=True
    )

    final = final.sort_values(
        ["event_date", "event_id"]
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # 10. VALIDATION
    # ---------------------------------------------------------

    print("\n[6] Validating final dataset...")

    print("Total rows:", len(final))
    print("Positive:", int((final["landslide_event"] == 1).sum()))
    print("Negative:", int((final["landslide_event"] == 0).sum()))

    print("\nMissing values:")
    print(
        final[
            feature_cols
        ].isna().sum()
    )

    print("\nClass distribution:")
    print(
        final["landslide_event"].value_counts()
    )

    print("\nDate range:")
    print(
        final["event_date"].min(),
        "to",
        final["event_date"].max()
    )

    print("\nStates:")
    print(final["state"].nunique())

    print("\nDistricts:")
    print(final["district"].nunique())

    # ---------------------------------------------------------
    # 11. SAVE
    # ---------------------------------------------------------

    final.to_csv(
        OUT_FILE,
        index=False
    )

    audit = {
        "source_gsi_events": EVENT_FILE,
        "source_rainfall": RAINFALL_FILE,
        "random_seed": SEED,
        "in_range_gsi_events": int(len(events)),
        "unique_joined_positive_events": int(len(positive)),
        "duplicate_rainfall_key_rows_removed": int(duplicate_keys),
        "negative_candidates": int(len(negative_pool)),
        "negative_samples": int(len(negative)),
        "final_rows": int(len(final)),
        "positive_rows": int(
            (final["landslide_event"] == 1).sum()
        ),
        "negative_rows": int(
            (final["landslide_event"] == 0).sum()
        ),
        "feature_columns": feature_cols,
        "target": "landslide_event",
        "target_definition": {
            "1": "confirmed GSI landslide event",
            "0": "pseudo-absence/background rainfall observation"
        }
    }

    with open(
        AUDIT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            audit,
            f,
            indent=2
        )

    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)

    print("FINAL DATASET:")
    print(OUT_FILE)

    print("\nAUDIT:")
    print(AUDIT_FILE)

    print("\nPOSITIVE:", len(positive))
    print("NEGATIVE:", len(negative))
    print("TOTAL:", len(final))

    print("=" * 70)


if __name__ == "__main__":
    main()