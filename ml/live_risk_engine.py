import os
import json
import joblib
import pandas as pd


# ============================================================
# CRISISCORE - LIVE RISK ENGINE
# ============================================================

print("=" * 70)
print("CRISISCORE LIVE LANDSLIDE RISK ENGINE")
print("=" * 70)


# ============================================================
# PATH CONFIGURATION
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

THRESHOLD_FILE = os.path.join(
    BASE_DIR,
    "models",
    "landslide_final_threshold.json"
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
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
    "state",
    "district",
    "month",
    "day_of_year"
]


# ============================================================
# LOAD CALIBRATED MODEL
# ============================================================

print("\n[1] Loading calibrated production model...")

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        f"\nCalibrated model not found:\n{MODEL_FILE}"
    )

artifact = joblib.load(MODEL_FILE)

# Your joblib may contain either:
# {
#     "model": calibrated_model
# }
# OR the estimator directly.

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
                    "Using estimator stored under:",
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


print("Model loaded successfully.")
print("Model file:", MODEL_FILE)
print("Estimator:", type(model).__name__)


# ============================================================
# LOAD OPERATIONAL THRESHOLD
# ============================================================

print("\n[2] Loading operational threshold...")

threshold = 0.10

if os.path.exists(THRESHOLD_FILE):

    with open(
        THRESHOLD_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        threshold_data = json.load(f)

    if isinstance(threshold_data, dict):

        if "threshold" in threshold_data:

            threshold = float(
                threshold_data["threshold"]
            )

        elif "decision_threshold" in threshold_data:

            threshold = float(
                threshold_data["decision_threshold"]
            )

    elif isinstance(
        threshold_data,
        (int, float)
    ):

        threshold = float(
            threshold_data
        )

else:

    print(
        "Threshold file not found."
        " Using default threshold = 0.10"
    )


print(
    "Decision threshold:",
    threshold
)


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_risk(probability):

    if probability >= 0.50:

        return "HIGH"

    elif probability >= threshold:

        return "MEDIUM"

    else:

        return "LOW"


# ============================================================
# LIVE PREDICTION FUNCTION
# ============================================================

def predict_live(
    state,
    district,
    rainfall_24h,
    rainfall_3day,
    rainfall_7day,
    rainfall_14day,
    rainfall_30day,
    rainfall_previous_day=0.0,
    rainfall_2day_lag=0.0,
    rainfall_3day_lag=0.0,
    rainfall_risk_score=0.0,
    prediction_date=None
):

    print(
        "\n----------------------------------------"
    )

    print(
        "Preparing live prediction..."
    )

    print(
        "----------------------------------------"
    )


    # ========================================================
    # DATE
    # ========================================================

    if prediction_date is None:

        prediction_date = pd.Timestamp.now()

    else:

        prediction_date = pd.Timestamp(
            prediction_date
        )


    month = int(
        prediction_date.month
    )

    day_of_year = int(
        prediction_date.dayofyear
    )


    # ========================================================
    # RAINFALL FLAGS
    # ========================================================

    heavy_rain_flag = int(
        float(rainfall_24h) >= 64.5
    )

    very_heavy_rain_flag = int(
        float(rainfall_24h) >= 115.6
    )


    # ========================================================
    # BUILD INPUT ROW
    # ========================================================

    prediction_row = pd.DataFrame(
        [{
            "rainfall_mm":
                float(rainfall_24h),

            "rainfall_24h":
                float(rainfall_24h),

            "rainfall_3day":
                float(rainfall_3day),

            "rainfall_7day":
                float(rainfall_7day),

            "rainfall_14day":
                float(rainfall_14day),

            "rainfall_30day":
                float(rainfall_30day),

            "heavy_rain_flag":
                heavy_rain_flag,

            "very_heavy_rain_flag":
                very_heavy_rain_flag,

            "rainfall_previous_day":
                float(rainfall_previous_day),

            "rainfall_2day_lag":
                float(rainfall_2day_lag),

            "rainfall_3day_lag":
                float(rainfall_3day_lag),

            "rainfall_risk_score":
                float(rainfall_risk_score),

            "state":
                state,

            "district":
                district,

            "month":
                month,

            "day_of_year":
                day_of_year
        }]
    )


    # ========================================================
    # CHECK FEATURES
    # ========================================================

    missing_features = [
        feature
        for feature in FEATURES
        if feature not in prediction_row.columns
    ]

    if missing_features:

        raise ValueError(
            "Missing model features:\n"
            + "\n".join(missing_features)
        )


    # ========================================================
    # MATCH CATEGORICAL FEATURES
    # ========================================================

    # Native categorical HGB requires state/district
    # to be represented consistently with training.

    try:

        if hasattr(
            model,
            "categorical_features"
        ):

            # Use string/object values.
            #
            # The calibrated production model should
            # already contain the fitted estimator and
            # its expected feature structure.

            prediction_row["state"] = (
                prediction_row["state"].astype(str)
            )

            prediction_row["district"] = (
                prediction_row["district"].astype(str)
            )

    except Exception:

        pass


    # ========================================================
    # SELECT FEATURES
    # ========================================================

    X = prediction_row[FEATURES]


    # ========================================================
    # MODEL PREDICTION
    # ========================================================

    print(
        "Running calibrated model..."
    )

    probabilities = model.predict_proba(X)


    if probabilities.shape[1] < 2:

        raise ValueError(
            "Model does not contain a binary "
            "landslide probability output."
        )


    probability = float(
        probabilities[0][1]
    )


    # Safety clamp

    probability = max(
        0.0,
        min(
            1.0,
            probability
        )
    )


    # ========================================================
    # RISK CLASS
    # ========================================================

    risk_level = classify_risk(
        probability
    )


    # ========================================================
    # EARLY WARNING
    # ========================================================

    early_warning = (
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

    print(
        "\n======================================"
    )

    print(
        "       LIVE RISK PREDICTION"
    )

    print(
        "======================================"
    )

    print(
        "State:",
        state
    )

    print(
        "District:",
        district
    )

    print(
        "Prediction date:",
        prediction_date.strftime(
            "%Y-%m-%d"
        )
    )


    print("\nRainfall:")

    print(
        "24h:",
        rainfall_24h,
        "mm"
    )

    print(
        "3day:",
        rainfall_3day,
        "mm"
    )

    print(
        "7day:",
        rainfall_7day,
        "mm"
    )

    print(
        "14day:",
        rainfall_14day,
        "mm"
    )

    print(
        "30day:",
        rainfall_30day,
        "mm"
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


    print("\nModel:")

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

    print(
        "======================================"
    )


    # ========================================================
    # JSON RESULT
    # ========================================================

    result = {

        "state":
            state,

        "district":
            district,

        "prediction_date":
            prediction_date.strftime(
                "%Y-%m-%d"
            ),

        "rainfall_24h_mm":
            float(rainfall_24h),

        "rainfall_3day_mm":
            float(rainfall_3day),

        "rainfall_7day_mm":
            float(rainfall_7day),

        "rainfall_14day_mm":
            float(rainfall_14day),

        "rainfall_30day_mm":
            float(rainfall_30day),

        "heavy_rain_flag":
            heavy_rain_flag,

        "very_heavy_rain_flag":
            very_heavy_rain_flag,

        "rainfall_previous_day":
            float(rainfall_previous_day),

        "rainfall_2day_lag":
            float(rainfall_2day_lag),

        "rainfall_3day_lag":
            float(rainfall_3day_lag),

        "rainfall_risk_score":
            float(rainfall_risk_score),

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
# TEST 1 — LOW RAINFALL
# ============================================================

print(
    "\n\n========== TEST 1: LOW RAINFALL =========="
)

result1 = predict_live(

    state="ARUNACHAL PRADESH",

    district="Anjaw",

    rainfall_24h=5,

    rainfall_3day=10,

    rainfall_7day=20,

    rainfall_14day=30,

    rainfall_30day=50
)


# ============================================================
# TEST 2 — HEAVY RAINFALL
# ============================================================

print(
    "\n\n========== TEST 2: HEAVY RAINFALL =========="
)

result2 = predict_live(

    state="ARUNACHAL PRADESH",

    district="Anjaw",

    rainfall_24h=100,

    rainfall_3day=220,

    rainfall_7day=350,

    rainfall_14day=500,

    rainfall_30day=700
)


# ============================================================
# TEST 3 — EXTREME RAINFALL
# ============================================================

print(
    "\n\n========== TEST 3: EXTREME RAINFALL =========="
)

result3 = predict_live(

    state="ARUNACHAL PRADESH",

    district="Anjaw",

    rainfall_24h=150,

    rainfall_3day=350,

    rainfall_7day=600,

    rainfall_14day=900,

    rainfall_30day=1300
)


# ============================================================
# COMPLETE
# ============================================================

print(
    "\n\n"
    + "=" * 70
)

print(
    "LIVE RISK ENGINE TEST COMPLETE"
)

print(
    "=" * 70
)