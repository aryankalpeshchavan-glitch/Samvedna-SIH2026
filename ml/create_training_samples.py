import os
import pandas as pd


INPUT_FILE = r"data\processed\events\landslide_event_targets.csv"

OUTPUT_DIR = r"data\processed\events"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "landslide_training_samples.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("\n==============================================")
print(" CRISISCORE - STEP 5 TRAINING SAMPLES")
print("==============================================")


# ============================================================
# LOAD
# ============================================================

print("\nLoading event target dataset...")

df = pd.read_csv(INPUT_FILE)

print("Rows:", len(df))


# ============================================================
# PREPARE DATE
# ============================================================

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)


# ============================================================
# CREATE ONE TARGET AT A TIME
# ============================================================
#
# We create three separate datasets:
#
#   24h prediction
#   48h prediction
#   72h prediction
#
# Target:
#   1 = landslide in prediction window
#   0 = no recorded landslide
#
# ============================================================


def create_samples(target_column, horizon):

    data = df.copy()

    data["target"] = data[target_column].astype(int)

    data["prediction_horizon_hours"] = horizon

    data["target_name"] = target_column

    return data


samples_24h = create_samples(
    "landslide_24h",
    24
)

samples_48h = create_samples(
    "landslide_48h",
    48
)

samples_72h = create_samples(
    "landslide_72h",
    72
)


# ============================================================
# COMBINE
# ============================================================

training = pd.concat(
    [
        samples_24h,
        samples_48h,
        samples_72h
    ],
    ignore_index=True
)


# ============================================================
# REMOVE OLD PROXY TARGETS
# ============================================================

proxy_columns = [
    "risk_class",
    "risk_label"
]

training = training.drop(
    columns=[
        c for c in proxy_columns
        if c in training.columns
    ]
)


# ============================================================
# SUMMARY
# ============================================================

print("\n==============================================")
print("             SAMPLE SUMMARY")
print("==============================================")


for horizon in [24, 48, 72]:

    subset = training[
        training["prediction_horizon_hours"] == horizon
    ]

    positive = int(
        subset["target"].sum()
    )

    negative = int(
        len(subset) - positive
    )

    print(
        f"\n{horizon}-HOUR TARGET"
    )

    print(
        "Total:",
        len(subset)
    )

    print(
        "Positive:",
        positive
    )

    print(
        "Negative:",
        negative
    )


# ============================================================
# LOCATION SUMMARY
# ============================================================

print("\n==============================================")
print("             LOCATION SUMMARY")
print("==============================================")


print(
    "\nStates:",
    training["state"].nunique()
)

print(
    "Districts:",
    training["district"].nunique()
)


# ============================================================
# SAVE
# ============================================================

training.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n==============================================")
print("Output:")
print(OUTPUT_FILE)
print("==============================================")


print("\nSTEP 5 COMPLETE")