import joblib
import pandas as pd


# ============================================================
# MODEL
# ============================================================

MODEL_FILE = r"models\risk_model.pkl"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag"
]


# ============================================================
# RISK CLASS
# ============================================================

RISK_NAMES = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH"
}


# ============================================================
# RISK SCORE
# Same score concept used in Day 3
# ============================================================

def calculate_risk_score(data):

    score = (
        0.35 * data["rainfall_24h"] +
        0.25 * data["rainfall_3day"] +
        0.20 * data["rainfall_7day"] +
        0.10 * data["rainfall_14day"] +
        0.10 * data["rainfall_30day"]
    )

    return float(score)


# ============================================================
# PREDICTOR
# ============================================================

class RiskPredictor:

    def __init__(self):

        self.model = joblib.load(MODEL_FILE)

        print("Risk model loaded successfully.")


    def predict(self, rainfall_data):

        # ----------------------------------------------------
        # Check required features
        # ----------------------------------------------------

        missing = [
            feature
            for feature in FEATURES
            if feature not in rainfall_data
        ]

        if missing:

            raise ValueError(
                f"Missing required features: {missing}"
            )


        # ----------------------------------------------------
        # Create model input
        # ----------------------------------------------------

        X = pd.DataFrame(
            [rainfall_data],
            columns=FEATURES
        )


        # ----------------------------------------------------
        # Model prediction
        # ----------------------------------------------------

        prediction = self.model.predict(X)[0]


        # ----------------------------------------------------
        # Model confidence
        # ----------------------------------------------------

        probabilities = self.model.predict_proba(X)[0]

        confidence = float(max(probabilities))


        # ----------------------------------------------------
        # Risk class
        # ----------------------------------------------------

        risk_class = RISK_NAMES[int(prediction)]


        # ----------------------------------------------------
        # Rainfall risk score
        # ----------------------------------------------------

        risk_score = calculate_risk_score(rainfall_data)


        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        return {

            "risk_class": risk_class,

            "rainfall_risk_score": round(
                risk_score,
                2
            ),

            "confidence": round(
                confidence,
                4
            ),

            "model_type": "RandomForestClassifier",

            "model_version": "v1"

        }