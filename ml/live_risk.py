import os
import json
import joblib
import numpy as np
import pandas as pd

from datetime import datetime


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

THRESHOLD_FILE = os.path.join(
    BASE_DIR,
    "models",
    "landslide_final_threshold.json"
)


# ============================================================
# FEATURES
# ============================================================
#
# EXACTLY the features used during model training.
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

print("=" * 70)

print(
    "CRISISCORE LIVE LANDSLIDE RISK ENGINE"
)

print("=" * 70)


# ============================================================
# LOAD MODEL
# ============================================================

print(
    "\n[1] Loading calibrated production model..."
)


if not os.path.exists(
    MODEL_FILE
):

    raise FileNotFoundError(

        "Calibrated model not found:\n"
        +
        MODEL_FILE

    )


artifact = joblib.load(
    MODEL_FILE
)


print(
    "Model loaded successfully."
)

print(
    "Model file:",
    MODEL_FILE
)


# ============================================================
# HANDLE MODEL ARTIFACT
# ============================================================

if isinstance(
    artifact,
    dict
):

    if "model" in artifact:

        model = artifact["model"]

    elif "calibrated_model" in artifact:

        model = artifact[
            "calibrated_model"
        ]

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

            raise KeyError(

                "Could not find a prediction "
                "model inside calibrated artifact."

            )

else:

    model = artifact


print(
    "Estimator:",
    type(model).__name__
)


# ============================================================
# LOAD THRESHOLD
# ============================================================

print(
    "\n[2] Loading operational threshold..."
)


#
# Default early warning threshold
#

threshold = 0.30


if os.path.exists(
    THRESHOLD_FILE
):

    try:

        with open(
            THRESHOLD_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            threshold_data = json.load(
                f
            )


        if isinstance(
            threshold_data,
            dict
        ):

            if "threshold" in threshold_data:

                threshold = float(
                    threshold_data[
                        "threshold"
                    ]
                )

            elif "final_threshold" in threshold_data:

                threshold = float(
                    threshold_data[
                        "final_threshold"
                    ]
                )


        elif isinstance(
            threshold_data,
            (int, float)
        ):

            threshold = float(
                threshold_data
            )


    except Exception:

        print(
            "Could not read threshold file."
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
# RISK LEVEL
# ============================================================

def get_risk_level(
    probability
):

    if probability >= 0.60:

        return "HIGH"

    elif probability >= 0.30:

        return "MEDIUM"

    else:

        return "LOW"


# ============================================================
# LIVE PREDICTION
# ============================================================

def predict_live(

    state,

    district,

    rainfall_24h,

    rainfall_3day,

    rainfall_7day,

    rainfall_14day,

    rainfall_30day,

    elevation_m,

    slope_deg,

    aspect_deg,

    terrain_roughness,

    rainfall_previous_day=0.0,

    rainfall_2day_lag=0.0,

    rainfall_3day_lag=0.0,

    rainfall_mm=None,

    prediction_datetime=None

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
    # DATE / TIME
    # ========================================================

    if prediction_datetime is None:

        prediction_datetime = datetime.now()


    if isinstance(
        prediction_datetime,
        str
    ):

        prediction_datetime = pd.to_datetime(
            prediction_datetime
        )


    # ========================================================
    # RAINFALL MM
    # ========================================================

    #
    # In the training dataset:
    #
    # rainfall_mm == daily rainfall measurement
    #

    if rainfall_mm is None:

        rainfall_mm = rainfall_24h


    # ========================================================
    # RAINFALL FLAGS
    # ========================================================

    heavy_rain_flag = int(

        float(rainfall_24h)
        >=
        64.5

    )


    very_heavy_rain_flag = int(

        float(rainfall_24h)
        >=
        115.6

    )


    # ========================================================
    # BUILD EXACT MODEL INPUT
    # ========================================================

    X = pd.DataFrame([{

        "rainfall_mm":
            float(rainfall_mm),

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

        "rainfall_previous_day":
            float(
                rainfall_previous_day
            ),

        "rainfall_2day_lag":
            float(
                rainfall_2day_lag
            ),

        "rainfall_3day_lag":
            float(
                rainfall_3day_lag
            ),

        "heavy_rain_flag":
            heavy_rain_flag,

        "very_heavy_rain_flag":
            very_heavy_rain_flag,

        "elevation_m":
            float(elevation_m),

        "slope_deg":
            float(slope_deg),

        "aspect_deg":
            float(aspect_deg),

        "terrain_roughness":
            float(
                terrain_roughness
            )

    }])


    # ========================================================
    # EXACT FEATURE ORDER
    # ========================================================

    X = X[
        FEATURES
    ]


    # ========================================================
    # VALIDATION
    # ========================================================

    if X.isnull().any().any():

        null_columns = (

            X.columns[
                X.isnull().any()
            ]

            .tolist()

        )

        raise ValueError(

            "NULL values found in model input:\n"
            +
            "\n".join(
                null_columns
            )

        )


    # ========================================================
    # PREDICTION
    # ========================================================

    print(
        "Running calibrated model..."
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


    # ========================================================
    # RISK CLASSIFICATION
    # ========================================================

    risk_level = get_risk_level(
        probability
    )


    early_warning = bool(

        probability
        >=
        threshold

    )


    if risk_level == "HIGH":

        warning_level = "HIGH"

    elif risk_level == "MEDIUM":

        warning_level = "MODERATE"

    else:

        warning_level = "NONE"


    # ========================================================
    # RESULT
    # ========================================================

    result = {

        "state":
            str(state),

        "district":
            str(district),

        "prediction_date":
            prediction_datetime.strftime(
                "%Y-%m-%d"
            ),

        "rainfall_24h_mm":
            round(
                float(rainfall_24h),
                2
            ),

        "rainfall_3day_mm":
            round(
                float(rainfall_3day),
                2
            ),

        "rainfall_7day_mm":
            round(
                float(rainfall_7day),
                2
            ),

        "rainfall_14day_mm":
            round(
                float(rainfall_14day),
                2
            ),

        "rainfall_30day_mm":
            round(
                float(rainfall_30day),
                2
            ),

        "heavy_rain_flag":
            heavy_rain_flag,

        "very_heavy_rain_flag":
            very_heavy_rain_flag,

        "elevation_m":
            round(
                float(elevation_m),
                2
            ),

        "slope_deg":
            round(
                float(slope_deg),
                2
            ),

        "aspect_deg":
            round(
                float(aspect_deg),
                2
            ),

        "terrain_roughness":
            round(
                float(terrain_roughness),
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


    # ========================================================
    # CONSOLE OUTPUT
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


    print("\nTerrain:")

    print(
        "Elevation:",
        elevation_m,
        "m"
    )

    print(
        "Slope:",
        slope_deg,
        "degrees"
    )

    print(
        "Aspect:",
        aspect_deg,
        "degrees"
    )

    print(
        "Roughness:",
        terrain_roughness
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


    return result


# ============================================================
# MANUAL TESTS
# ============================================================

if __name__ == "__main__":


    # ========================================================
    # TEST 1
    # ========================================================

    print(
        "\n\n========== TEST 1: LOW RAINFALL =========="
    )


    result1 = predict_live(

        state=
            "ARUNACHAL PRADESH",

        district=
            "Anjaw",

        rainfall_24h=
            5,

        rainfall_3day=
            10,

        rainfall_7day=
            20,

        rainfall_14day=
            30,

        rainfall_30day=
            50,

        elevation_m=
            1200,

        slope_deg=
            15,

        aspect_deg=
            180,

        terrain_roughness=
            20

    )


    print(
        "\nJSON RESULT:"
    )

    print(
        json.dumps(
            result1,
            indent=2
        )
    )


    # ========================================================
    # TEST 2
    # ========================================================

    print(
        "\n\n========== TEST 2: HEAVY RAINFALL =========="
    )


    result2 = predict_live(

        state=
            "ARUNACHAL PRADESH",

        district=
            "Anjaw",

        rainfall_24h=
            100,

        rainfall_3day=
            220,

        rainfall_7day=
            350,

        rainfall_14day=
            500,

        rainfall_30day=
            700,

        elevation_m=
            1200,

        slope_deg=
            30,

        aspect_deg=
            180,

        terrain_roughness=
            45

    )


    print(
        "\nJSON RESULT:"
    )

    print(
        json.dumps(
            result2,
            indent=2
        )
    )


    # ========================================================
    # TEST 3
    # ========================================================

    print(
        "\n\n========== TEST 3: EXTREME RAINFALL =========="
    )


    result3 = predict_live(

        state=
            "ARUNACHAL PRADESH",

        district=
            "Anjaw",

        rainfall_24h=
            150,

        rainfall_3day=
            350,

        rainfall_7day=
            600,

        rainfall_14day=
            900,

        rainfall_30day=
            1300,

        elevation_m=
            1200,

        slope_deg=
            40,

        aspect_deg=
            180,

        terrain_roughness=
            65

    )


    print(
        "\nJSON RESULT:"
    )

    print(
        json.dumps(
            result3,
            indent=2
        )
    )


    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n")

    print(
        "=" * 70
    )

    print(
        "LIVE RISK ENGINE TEST COMPLETE"
    )

    print(
        "=" * 70
    )