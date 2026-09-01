import os
import json
import joblib
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RAINFALL_DATASET = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "rainfall",
    "risk_prediction_dataset.csv"
)

TERRAIN_DATASET = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_event_training_dataset_terrain.csv"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "landslide_calibrated_v1.joblib"
)

THRESHOLD_FILE = os.path.join(
    BASE_DIR,
    "models",
    "landslide_final_threshold.json"
)


# ============================================================
# MODEL FEATURES
# ============================================================
#
# IMPORTANT:
# These MUST exactly match the features used during training.
#

FEATURES = [
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


# ============================================================
# START
# ============================================================

print("\n==============================================")
print("       CURRENT LANDSLIDE RISK ENGINE")
print("==============================================")


# ============================================================
# LOAD MODEL
# ============================================================

print("\n[1] Loading calibrated production model...")

if not os.path.exists(MODEL_FILE):

    raise FileNotFoundError(
        f"Calibrated model not found:\n{MODEL_FILE}"
    )

artifact = joblib.load(MODEL_FILE)

print("Model loaded successfully.")
print("Model:", MODEL_FILE)


# ============================================================
# HANDLE MODEL ARTIFACT
# ============================================================

if isinstance(artifact, dict):

    if "model" in artifact:

        model = artifact["model"]

    elif "calibrated_model" in artifact:

        model = artifact["calibrated_model"]

    else:

        model = None

        for key, value in artifact.items():

            if hasattr(value, "predict_proba"):

                model = value

                print(
                    "Using model stored under:",
                    key
                )

                break

        if model is None:

            raise ValueError(
                "Could not find a prediction model "
                "inside the joblib artifact."
            )

else:

    model = artifact


print(
    "Estimator:",
    type(model).__name__
)


# ============================================================
# LOAD OPERATIONAL THRESHOLD
# ============================================================

print("\n[2] Loading operational threshold...")

#
# Default early-warning threshold.
#
# Risk bands:
#
# LOW    < 0.30
# MEDIUM 0.30 - <0.60
# HIGH   >= 0.60
#

threshold = 0.30

if os.path.exists(THRESHOLD_FILE):

    try:

        with open(
            THRESHOLD_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            threshold_data = json.load(f)

        if isinstance(
            threshold_data,
            dict
        ):

            if "threshold" in threshold_data:

                threshold = float(
                    threshold_data["threshold"]
                )

            elif "final_threshold" in threshold_data:

                threshold = float(
                    threshold_data["final_threshold"]
                )

    except Exception as e:

        print(
            "Warning: could not read threshold file."
        )

        print(
            "Using default threshold:",
            threshold
        )


print(
    "Decision threshold:",
    threshold
)


# ============================================================
# LOAD RAINFALL DATASET
# ============================================================

print("\n[3] Loading rainfall dataset...")

if not os.path.exists(
    RAINFALL_DATASET
):

    raise FileNotFoundError(
        f"Rainfall dataset not found:\n"
        f"{RAINFALL_DATASET}"
    )

df = pd.read_csv(
    RAINFALL_DATASET
)

print(
    "Rainfall rows:",
    len(df)
)

print(
    "Rainfall columns:",
    len(df.columns)
)


# ============================================================
# LOAD TERRAIN DATASET
# ============================================================

print("\n[4] Loading terrain dataset...")

if not os.path.exists(
    TERRAIN_DATASET
):

    raise FileNotFoundError(
        f"Terrain dataset not found:\n"
        f"{TERRAIN_DATASET}"
    )

terrain_df = pd.read_csv(
    TERRAIN_DATASET
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
# PREPARE DATASETS
# ============================================================

print("\n[5] Preparing datasets...")


# ----------------------------
# Rainfall
# ----------------------------

if "date" not in df.columns:

    raise ValueError(
        "Rainfall dataset does not contain 'date'."
    )

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["state_clean"] = (
    df["state"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df["district_clean"] = (
    df["district"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ----------------------------
# Terrain
# ----------------------------

terrain_df["state_clean"] = (
    terrain_df["state"]
    .astype(str)
    .str.upper()
    .str.strip()
)

terrain_df["district_clean"] = (
    terrain_df["district"]
    .astype(str)
    .str.lower()
    .str.strip()
)


print("Datasets prepared.")


# ============================================================
# LATEST RAINFALL
# ============================================================

def get_latest_rainfall(
    state,
    district
):

    state_clean = (
        str(state)
        .upper()
        .strip()
    )

    district_clean = (
        str(district)
        .lower()
        .strip()
    )

    data = df[
        (df["state_clean"] == state_clean)
        &
        (df["district_clean"] == district_clean)
    ].copy()

    if data.empty:

        raise ValueError(
            "No rainfall data found for:\n"
            f"State: {state}\n"
            f"District: {district}"
        )

    data = data.sort_values(
        "date"
    )

    return data.iloc[-1]


# ============================================================
# TERRAIN LOOKUP
# ============================================================

def get_terrain(
    state,
    district
):

    state_clean = (
        str(state)
        .upper()
        .strip()
    )

    district_clean = (
        str(district)
        .lower()
        .strip()
    )

    data = terrain_df[
        (terrain_df["state_clean"] == state_clean)
        &
        (terrain_df["district_clean"] == district_clean)
    ].copy()

    if data.empty:

        raise ValueError(
            "No terrain data found for:\n"
            f"State: {state}\n"
            f"District: {district}"
        )

    required = [
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "terrain_roughness"
    ]

    for column in required:

        if column not in data.columns:

            raise ValueError(
                f"Terrain dataset missing column: "
                f"{column}"
            )

    #
    # Multiple landslide/event points may exist
    # inside the same district.
    #
    # Median gives us a representative
    # district-level terrain profile.
    #

    terrain = {

        "elevation_m":
            float(
                data["elevation_m"]
                .median()
            ),

        "slope_deg":
            float(
                data["slope_deg"]
                .median()
            ),

        "aspect_deg":
            float(
                data["aspect_deg"]
                .median()
            ),

        "terrain_roughness":
            float(
                data["terrain_roughness"]
                .median()
            )
    }

    return terrain


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_risk(
    probability
):

    if probability >= 0.60:

        return "HIGH"

    elif probability >= 0.30:

        return "MEDIUM"

    else:

        return "LOW"


# ============================================================
# CURRENT RISK
# ============================================================

def get_current_risk(
    state,
    district
):

    print("\n----------------------------------------------")
    print("Preparing current risk prediction...")
    print("----------------------------------------------")


    # --------------------------------------------------------
    # Get latest rainfall
    # --------------------------------------------------------

    latest = get_latest_rainfall(
        state,
        district
    )


    # --------------------------------------------------------
    # Get representative terrain
    # --------------------------------------------------------

    terrain = get_terrain(
        state,
        district
    )


    # --------------------------------------------------------
    # Prediction date
    # --------------------------------------------------------

    prediction_date = pd.Timestamp(
        latest["date"]
    )


    # --------------------------------------------------------
    # Rainfall values
    # --------------------------------------------------------

    rainfall_mm = float(
        latest.get(
            "rainfall_mm",
            0.0
        )
    )

    rainfall_24h = float(
        latest.get(
            "rainfall_24h",
            rainfall_mm
        )
    )

    rainfall_3day = float(
        latest.get(
            "rainfall_3day",
            0.0
        )
    )

    rainfall_7day = float(
        latest.get(
            "rainfall_7day",
            0.0
        )
    )

    rainfall_14day = float(
        latest.get(
            "rainfall_14day",
            0.0
        )
    )

    rainfall_30day = float(
        latest.get(
            "rainfall_30day",
            0.0
        )
    )

    rainfall_previous_day = float(
        latest.get(
            "rainfall_previous_day",
            0.0
        )
    )

    rainfall_2day_lag = float(
        latest.get(
            "rainfall_2day_lag",
            0.0
        )
    )

    rainfall_3day_lag = float(
        latest.get(
            "rainfall_3day_lag",
            0.0
        )
    )


    # --------------------------------------------------------
    # Rainfall flags
    # --------------------------------------------------------

    heavy_rain_flag = int(
        latest.get(
            "heavy_rain_flag",
            int(
                rainfall_24h >= 64.5
            )
        )
    )

    very_heavy_rain_flag = int(
        latest.get(
            "very_heavy_rain_flag",
            int(
                rainfall_24h >= 115.6
            )
        )
    )


    # --------------------------------------------------------
    # Build EXACT model feature row
    # --------------------------------------------------------

    prediction_row = pd.DataFrame([{

        "rainfall_mm":
            rainfall_mm,

        "rainfall_24h":
            rainfall_24h,

        "rainfall_3day":
            rainfall_3day,

        "rainfall_7day":
            rainfall_7day,

        "rainfall_14day":
            rainfall_14day,

        "rainfall_30day":
            rainfall_30day,

        "rainfall_previous_day":
            rainfall_previous_day,

        "rainfall_2day_lag":
            rainfall_2day_lag,

        "rainfall_3day_lag":
            rainfall_3day_lag,

        "heavy_rain_flag":
            heavy_rain_flag,

        "very_heavy_rain_flag":
            very_heavy_rain_flag,

        "elevation_m":
            terrain["elevation_m"],

        "slope_deg":
            terrain["slope_deg"],

        "aspect_deg":
            terrain["aspect_deg"],

        "terrain_roughness":
            terrain["terrain_roughness"]

    }])


    # --------------------------------------------------------
    # Validate features
    # --------------------------------------------------------

    missing_features = [
        feature
        for feature in FEATURES
        if feature not in prediction_row.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing model features:\n"
            +
            "\n".join(
                missing_features
            )
        )


    # --------------------------------------------------------
    # Select EXACT feature order
    # --------------------------------------------------------

    X = prediction_row[
        FEATURES
    ]


    # --------------------------------------------------------
    # Check NULLs
    # --------------------------------------------------------

    if X.isnull().any().any():

        null_columns = (
            X.columns[
                X.isnull().any()
            ].tolist()
        )

        raise ValueError(
            "NULL values found in "
            "model features:\n"
            +
            "\n".join(
                null_columns
            )
        )


    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    print(
        "\nRunning calibrated production model..."
    )

    probabilities = model.predict_proba(
        X
    )

    probability = float(
        probabilities[0][1]
    )

    probability = max(
        0.0,
        min(
            1.0,
            probability
        )
    )


    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    risk_level = classify_risk(
        probability
    )

    early_warning = bool(
        probability >= threshold
    )


    if risk_level == "HIGH":

        warning_level = "HIGH"

    elif risk_level == "MEDIUM":

        warning_level = "MODERATE"

    else:

        warning_level = "NONE"


    # ========================================================
    # OUTPUT
    # ========================================================

    print("\n======================================")
    print("       CURRENT LANDSLIDE RISK")
    print("======================================")

    print(
        "State:",
        state
    )

    print(
        "District:",
        district
    )

    print(
        "Observation date:",
        prediction_date.strftime(
            "%Y-%m-%d"
        )
    )

    print("\nRainfall:")

    print(
        "24h:",
        round(
            rainfall_24h,
            2
        ),
        "mm"
    )

    print(
        "3day:",
        round(
            rainfall_3day,
            2
        ),
        "mm"
    )

    print(
        "7day:",
        round(
            rainfall_7day,
            2
        ),
        "mm"
    )

    print(
        "14day:",
        round(
            rainfall_14day,
            2
        ),
        "mm"
    )

    print(
        "30day:",
        round(
            rainfall_30day,
            2
        ),
        "mm"
    )

    print("\nTerrain:")

    print(
        "Elevation:",
        round(
            terrain["elevation_m"],
            2
        ),
        "m"
    )

    print(
        "Slope:",
        round(
            terrain["slope_deg"],
            2
        ),
        "degrees"
    )

    print(
        "Aspect:",
        round(
            terrain["aspect_deg"],
            2
        ),
        "degrees"
    )

    print(
        "Roughness:",
        round(
            terrain["terrain_roughness"],
            2
        )
    )

    print("\nRainfall flags:")

    print(
        "Heavy rain:",
        heavy_rain_flag
    )

    print(
        "Very heavy rain:",
        very_heavy_rain_flag
    )

    print("\n========== PREDICTION ==========")

    print(
        "Landslide probability:",
        round(
            probability,
            4
        )
    )

    print(
        "Decision threshold:",
        threshold
    )

    print(
        "Risk level:",
        risk_level
    )

    print(
        "Early warning:",
        early_warning
    )

    print(
        "Warning level:",
        warning_level
    )

    print("======================================")


    # ========================================================
    # JSON RESULT
    # ========================================================

    result = {

        "state":
            str(state),

        "district":
            str(district),

        "observation_date":
            prediction_date.strftime(
                "%Y-%m-%d"
            ),

        "rainfall_24h_mm":
            round(
                rainfall_24h,
                2
            ),

        "rainfall_3day_mm":
            round(
                rainfall_3day,
                2
            ),

        "rainfall_7day_mm":
            round(
                rainfall_7day,
                2
            ),

        "rainfall_14day_mm":
            round(
                rainfall_14day,
                2
            ),

        "rainfall_30day_mm":
            round(
                rainfall_30day,
                2
            ),

        "heavy_rain_flag":
            heavy_rain_flag,

        "very_heavy_rain_flag":
            very_heavy_rain_flag,

        "elevation_m":
            round(
                terrain["elevation_m"],
                2
            ),

        "slope_deg":
            round(
                terrain["slope_deg"],
                2
            ),

        "aspect_deg":
            round(
                terrain["aspect_deg"],
                2
            ),

        "terrain_roughness":
            round(
                terrain["terrain_roughness"],
                2
            ),

        "landslide_probability":
            round(
                probability,
                6
            ),

        "risk_level":
            risk_level,

        "early_warning":
            early_warning,

        "warning_level":
            warning_level,

        "decision_threshold":
            threshold,

        "model":
            "landslide_calibrated_v1"
    }


    print("\nJSON RESULT:")

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    return result


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("\n==============================================")
    print("CURRENT RISK ENGINE TEST")
    print("==============================================")

    try:

        result = get_current_risk(
            state="ARUNACHAL PRADESH",
            district="Anjaw"
        )

        print("\nTest completed successfully.")

    except Exception as e:

        print("\nTEST FAILED:")
        print(str(e))
        raise