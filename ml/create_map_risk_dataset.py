import os
import json
import joblib
import numpy as np
import pandas as pd


# ============================================================
# CRISISCORE - MAP RISK DATASET GENERATOR
# ============================================================

print("=" * 70)
print("CRISISCORE - MAP RISK DATASET GENERATOR")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "landslide_calibrated_v1.joblib"
)

TERRAIN_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_event_training_dataset_terrain.csv"
)

RAINFALL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "rainfall",
    "risk_prediction_dataset.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "map_risk_dataset.csv"
)

OUTPUT_JSON = os.path.join(
    OUTPUT_DIR,
    "map_risk_dataset_summary.json"
)


# ============================================================
# CHECK FILES
# ============================================================

print("\n[1] Checking required files...")

required_files = {
    "MODEL": MODEL_FILE,
    "TERRAIN": TERRAIN_FILE,
    "RAINFALL": RAINFALL_FILE
}

for name, path in required_files.items():

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"{name} file not found:\n{path}"
        )

    print(f"FOUND: {path}")


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n[2] Loading calibrated ML model...")

artifact = joblib.load(
    MODEL_FILE
)

if isinstance(artifact, dict):

    if "model" in artifact:

        model = artifact["model"]

    elif "calibrated_model" in artifact:

        model = artifact["calibrated_model"]

    else:

        model = None

        for key, value in artifact.items():

            if hasattr(
                value,
                "predict_proba"
            ):

                model = value

                print(
                    "Using model stored under:",
                    key
                )

                break

        if model is None:

            raise ValueError(
                "Could not find prediction model "
                "inside joblib artifact."
            )

else:

    model = artifact


print(
    "Estimator:",
    type(model).__name__
)


# ============================================================
# READ ACTUAL MODEL FEATURE SCHEMA
# ============================================================

print("\n[2.1] Reading trained model feature schema...")

if hasattr(
    model,
    "feature_names_in_"
):

    MODEL_FEATURES = list(
        model.feature_names_in_
    )

elif hasattr(
    model,
    "estimator"
) and hasattr(
    model.estimator,
    "feature_names_in_"
):

    MODEL_FEATURES = list(
        model.estimator.feature_names_in_
    )

else:

    MODEL_FEATURES = [
        "rainfall_mm",
        "rainfall_24h",
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_14day",
        "rainfall_30day",
        "rainfall_previous_day",
        "rainfall_2day_lag",
        "rainfall_3day_lag",
        "heavy_rain_flag",
        "very_heavy_rain_flag",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "terrain_roughness"
    ]


print(
    "Model features:",
    MODEL_FEATURES
)

print(
    "N features:",
    len(MODEL_FEATURES)
)


# ============================================================
# LOAD TERRAIN DATA
# ============================================================

print("\n[3] Loading terrain dataset...")

terrain_df = pd.read_csv(
    TERRAIN_FILE
)

print(
    "Terrain rows:",
    len(terrain_df)
)

print(
    "Terrain columns:",
    len(terrain_df.columns)
)


# ============================================================
# LOAD RAINFALL DATA
# ============================================================

print("\n[4] Loading rainfall dataset...")

rainfall_df = pd.read_csv(
    RAINFALL_FILE
)

print(
    "Rainfall rows:",
    len(rainfall_df)
)

print(
    "Rainfall columns:",
    len(rainfall_df.columns)
)


# ============================================================
# PREPARE TERRAIN
# ============================================================

print("\n[5] Preparing terrain data...")


terrain_df.columns = [
    str(c).strip()
    for c in terrain_df.columns
]


terrain_df["state"] = (
    terrain_df["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)


terrain_df["district"] = (
    terrain_df["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# Remove duplicate terrain locations if necessary

terrain_df = terrain_df.drop_duplicates(
    subset=[
        "state",
        "district",
        "latitude",
        "longitude"
    ]
)


# ============================================================
# PREPARE RAINFALL
# ============================================================

print("\n[6] Preparing rainfall data...")


rainfall_df.columns = [
    str(c).strip()
    for c in rainfall_df.columns
]


rainfall_df["state"] = (
    rainfall_df["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)


rainfall_df["district"] = (
    rainfall_df["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)


rainfall_df["date"] = pd.to_datetime(
    rainfall_df["date"],
    errors="coerce"
)


rainfall_df = rainfall_df.dropna(
    subset=["date"]
)


# ============================================================
# CHECK RAINFALL COLUMNS
# ============================================================

required_rainfall_columns = [
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day"
]


for col in required_rainfall_columns:

    if col not in rainfall_df.columns:

        raise ValueError(
            f"Required rainfall column missing: {col}"
        )


# ============================================================
# SELECT LATEST RAINFALL
# ============================================================

print(
    "\n[7] Selecting latest rainfall observation "
    "for each state/district..."
)


rainfall_df = rainfall_df.sort_values(
    "date"
)


latest_rainfall = (
    rainfall_df
    .groupby(
        ["state", "district"],
        as_index=False
    )
    .tail(1)
    .copy()
)


print(
    "Latest rainfall records:",
    len(latest_rainfall)
)


# ============================================================
# PREPARE RAINFALL LAG FEATURES
# ============================================================

print(
    "\n[8] Preparing rainfall lag features..."
)


# If lag columns already exist, keep them.
# Otherwise create safe defaults.

for col in [
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag"
]:

    if col not in latest_rainfall.columns:

        latest_rainfall[col] = 0.0


# ============================================================
# PREPARE RAINFALL FLAGS
# ============================================================

if "heavy_rain_flag" not in latest_rainfall.columns:

    latest_rainfall[
        "heavy_rain_flag"
    ] = (
        latest_rainfall[
            "rainfall_24h"
        ]
        >= 64.5
    ).astype(int)


if "very_heavy_rain_flag" not in latest_rainfall.columns:

    latest_rainfall[
        "very_heavy_rain_flag"
    ] = (
        latest_rainfall[
            "rainfall_24h"
        ]
        >= 115.6
    ).astype(int)


# ============================================================
# MERGE TERRAIN + RAINFALL
# ============================================================

print(
    "\n[9] Joining terrain and rainfall data..."
)


map_df = terrain_df.merge(
    latest_rainfall,
    on=[
        "state",
        "district"
    ],
    how="left",
    suffixes=(
        "_terrain",
        "_rainfall"
    )
)


print(
    "Rows after merge:",
    len(map_df)
)


print(
    "Map dataset columns:",
    len(map_df.columns)
)


# ============================================================
# RESTORE EXPECTED RAINFALL COLUMN NAMES
# ============================================================

# Because the merge may create suffixes,
# explicitly resolve rainfall columns.

def resolve_column(
    dataframe,
    column
):

    candidates = [
        column,
        column + "_rainfall",
        column + "_terrain"
    ]

    for candidate in candidates:

        if candidate in dataframe.columns:

            return candidate

    return None


for col in [
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
    "heavy_rain_flag",
    "very_heavy_rain_flag"
]:

    resolved = resolve_column(
        map_df,
        col
    )

    if resolved is not None:

        if resolved != col:

            map_df[col] = map_df[
                resolved
            ]


# ============================================================
# CHECK MISSING RAINFALL
# ============================================================

missing_rainfall = map_df[
    map_df["rainfall_24h"].isna()
]


print(
    "Rows without rainfall:",
    len(missing_rainfall)
)


if not missing_rainfall.empty:

    print(
        "\nWARNING: Some terrain locations "
        "do not have matching rainfall data."
    )

    print(
        missing_rainfall[
            ["state", "district"]
        ]
        .drop_duplicates()
        .to_string(index=False)
    )


# ============================================================
# REMOVE INVALID RAINFALL ROWS
# ============================================================

before_filter = len(
    map_df
)


map_df = map_df[
    map_df["rainfall_24h"].notna()
].copy()


removed_rows = (
    before_filter
    - len(map_df)
)


print(
    "\nInvalid terrain rows removed:",
    removed_rows
)


print(
    "Rows remaining after rainfall filtering:",
    len(map_df)
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness"
]


for col in numeric_columns:

    if col in map_df.columns:

        map_df[col] = pd.to_numeric(
            map_df[col],
            errors="coerce"
        )


# ============================================================
# FILL SAFE RAINFALL DEFAULTS
# ============================================================

for col in [
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag"
]:

    if col in map_df.columns:

        map_df[col] = map_df[
            col
        ].fillna(0.0)


# ============================================================
# RECALCULATE FLAGS IF NECESSARY
# ============================================================

map_df[
    "heavy_rain_flag"
] = (
    map_df[
        "rainfall_24h"
    ]
    >= 64.5
).astype(int)


map_df[
    "very_heavy_rain_flag"
] = (
    map_df[
        "rainfall_24h"
    ]
    >= 115.6
).astype(int)


# ============================================================
# CHECK TERRAIN FEATURES
# ============================================================

terrain_features = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness"
]


for col in terrain_features:

    if col not in map_df.columns:

        raise ValueError(
            f"Terrain feature missing: {col}"
        )


# ============================================================
# CHECK ML FEATURE VALIDITY
# ============================================================

print(
    "\nChecking ML feature validity..."
)


invalid_mask = pd.Series(
    False,
    index=map_df.index
)


for feature in MODEL_FEATURES:

    if feature not in map_df.columns:

        raise ValueError(
            f"MODEL FEATURE MISSING: {feature}"
        )

    invalid_mask |= (
        map_df[feature].isna()
    )


print(
    "Rows with invalid ML features:",
    int(invalid_mask.sum())
)


if invalid_mask.any():

    print(
        "\nInvalid rows:"
    )

    print(
        map_df.loc[
            invalid_mask,
            [
                "state",
                "district"
            ]
        ]
        .drop_duplicates()
        .to_string(index=False)
    )


    map_df = map_df[
        ~invalid_mask
    ].copy()


print(
    "Rows available for prediction:",
    len(map_df)
)


# ============================================================
# PREPARE EXACT ML FEATURES
# ============================================================

print(
    "\n[10] Preparing ML prediction features..."
)


# IMPORTANT:
# These MUST be exactly the features and
# order used during model training.

X = map_df[
    MODEL_FEATURES
].copy()


# Ensure numerical values are numeric

for feature in MODEL_FEATURES:

    X[feature] = pd.to_numeric(
        X[feature],
        errors="coerce"
    )


# Final missing-value check

if X.isna().any().any():

    print(
        "\nMissing values detected:"
    )

    print(
        X.isna()
        .sum()[
            X.isna().sum() > 0
        ]
    )

    raise ValueError(
        "ML feature dataframe contains NaN values."
    )


# ============================================================
# FINAL FEATURE ORDER CHECK
# ============================================================

print(
    "\nFinal ML feature order:"
)

for i, feature in enumerate(
    X.columns,
    start=1
):

    print(
        f"{i:2d}. {feature}"
    )


if list(X.columns) != MODEL_FEATURES:

    raise ValueError(
        "ML feature order does not match "
        "trained model."
    )


print(
    "\nFeature count:",
    X.shape[1]
)


# ============================================================
# RUN MODEL
# ============================================================

print(
    "\n[11] Running landslide probability prediction..."
)


probabilities = model.predict_proba(
    X
)


# Binary classification:
# class 0 = no landslide
# class 1 = landslide

if hasattr(
    model,
    "classes_"
):

    classes = list(
        model.classes_
    )

    if 1 in classes:

        landslide_index = (
            classes.index(1)
        )

    else:

        raise ValueError(
            "Model does not contain "
            "landslide class 1."
        )

else:

    landslide_index = 1


landslide_probabilities = (
    probabilities[
        :,
        landslide_index
    ]
)


landslide_probabilities = np.clip(
    landslide_probabilities,
    0.0,
    1.0
)


map_df[
    "landslide_probability"
] = (
    landslide_probabilities
)


# ============================================================
# RISK LEVEL
# ============================================================

def classify_risk(
    probability
):

    if probability < 0.10:

        return "LOW"

    elif probability < 0.50:

        return "MEDIUM"

    else:

        return "HIGH"


map_df[
    "risk_level"
] = map_df[
    "landslide_probability"
].apply(
    classify_risk
)


# ============================================================
# EARLY WARNING
# ============================================================

map_df[
    "early_warning"
] = (
    map_df[
        "landslide_probability"
    ]
    >= 0.10
)


# ============================================================
# WARNING LEVEL
# ============================================================

def warning_level(
    risk
):

    if risk == "HIGH":

        return "HIGH"

    elif risk == "MEDIUM":

        return "MODERATE"

    return "NONE"


map_df[
    "warning_level"
] = map_df[
    "risk_level"
].apply(
    warning_level
)


# ============================================================
# ROUND VALUES
# ============================================================

for col in [
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness"
]:

    if col in map_df.columns:

        map_df[col] = map_df[
            col
        ].round(4)


map_df[
    "landslide_probability"
] = map_df[
    "landslide_probability"
].round(6)


# ============================================================
# SELECT MAP OUTPUT COLUMNS
# ============================================================

preferred_columns = [
    "state",
    "district",
    "latitude",
    "longitude",

    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness",

    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",

    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",

    "heavy_rain_flag",
    "very_heavy_rain_flag",

    "landslide_probability",
    "risk_level",
    "early_warning",
    "warning_level"
]

output_columns = [
    col
    for col in preferred_columns
    if col in map_df.columns
]

map_output = map_df[
    output_columns
].copy()


output_columns = [
    col
    for col in preferred_columns
    if col in map_df.columns
]


map_output = map_df[
    output_columns
].copy()


# ============================================================
# SAVE CSV
# ============================================================

print(
    "\n[12] Saving map risk dataset..."
)


map_output.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    "Saved:",
    OUTPUT_FILE
)


# ============================================================
# SUMMARY
# ============================================================

risk_counts = (
    map_output[
        "risk_level"
    ]
    .value_counts()
    .to_dict()
)


summary = {

    "dataset": "CrisisCore Map Risk Dataset",

    "model":
        "landslide_calibrated_v1",

    "model_feature_count":
        len(MODEL_FEATURES),

    "model_features":
        MODEL_FEATURES,

    "rows":
        int(len(map_output)),

    "risk_distribution":
        {
            str(k): int(v)
            for k, v in risk_counts.items()
        },

    "min_probability":
        float(
            map_output[
                "landslide_probability"
            ].min()
        ),

    "max_probability":
        float(
            map_output[
                "landslide_probability"
            ].max()
        ),

    "mean_probability":
        float(
            map_output[
                "landslide_probability"
            ].mean()
        ),

    "high_risk_locations":
        int(
            (
                map_output[
                    "risk_level"
                ] == "HIGH"
            ).sum()
        ),

    "medium_risk_locations":
        int(
            (
                map_output[
                    "risk_level"
                ] == "MEDIUM"
            ).sum()
        ),

    "low_risk_locations":
        int(
            (
                map_output[
                    "risk_level"
                ] == "LOW"
            ).sum()
        )
}


with open(
    OUTPUT_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=2
    )


# ============================================================
# DISPLAY SAMPLE
# ============================================================

print(
    "\n[13] MAP RISK SAMPLE"
)

print(
    "=" * 70
)


sample_columns = [
    "state",
    "district",
    "latitude",
    "longitude",
    "elevation_m",
    "slope_deg",
    "rainfall_24h",
    "rainfall_7day",
    "landslide_probability",
    "risk_level",
    "early_warning"
]


sample_columns = [
    col
    for col in sample_columns
    if col in map_output.columns
]


print(
    map_output[
        sample_columns
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n"
    + "=" * 70
)

print(
    "CRISISCORE MAP RISK DATASET COMPLETE"
)

print(
    "=" * 70
)

print(
    "\nRows generated:",
    len(map_output)
)

print(
    "ML features used:",
    len(MODEL_FEATURES)
)

print(
    "\nRisk distribution:"
)

for risk, count in risk_counts.items():

    print(
        f"  {risk}: {count}"
    )


print(
    "\nOutput CSV:"
)

print(
    OUTPUT_FILE
)


print(
    "\nSummary JSON:"
)

print(
    OUTPUT_JSON
)


print(
    "\n"
    + "=" * 70
)