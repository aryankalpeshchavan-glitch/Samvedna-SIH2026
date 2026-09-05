import joblib
import pandas as pd


MODEL_FILE = r"models\risk_model.pkl"


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


RISK_NAMES = {
    0: "LOW",
    1: "MEDIUM",
    2: "HIGH"
}


def calculate_rainfall_score(data):

    score = (
        0.35 * data["rainfall_24h"] +
        0.25 * data["rainfall_3day"] +
        0.20 * data["rainfall_7day"] +
        0.10 * data["rainfall_14day"] +
        0.10 * data["rainfall_30day"]
    )

    return float(score)


def calculate_risk_score(probabilities):

    low_probability = probabilities[0]
    medium_probability = probabilities[1]
    high_probability = probabilities[2]

    risk_score = (
        (low_probability * 0) +
        (medium_probability * 50) +
        (high_probability * 100)
    )

    return float(risk_score)


def get_warning(risk_class, risk_score):

    if risk_class == "HIGH" or risk_score >= 70:

        return {
            "early_warning": True,
            "warning_level": "HIGH"
        }

    elif risk_class == "MEDIUM" or risk_score >= 40:

        return {
            "early_warning": True,
            "warning_level": "WATCH"
        }

    else:

        return {
            "early_warning": False,
            "warning_level": "NONE"
        }


class RiskPredictor:

    def __init__(self):

        self.model = joblib.load(MODEL_FILE)

        print("Risk model loaded successfully.")


    def predict(self, rainfall_data):

        missing = [
            feature
            for feature in FEATURES
            if feature not in rainfall_data
        ]

        if missing:

            raise ValueError(
                f"Missing required features: {missing}"
            )


        X = pd.DataFrame(
            [rainfall_data],
            columns=FEATURES
        )


        prediction = self.model.predict(X)[0]

        probabilities = self.model.predict_proba(X)[0]

        risk_class = RISK_NAMES[int(prediction)]

        confidence = float(max(probabilities))

        risk_score = calculate_risk_score(
            probabilities
        )

        rainfall_score = calculate_rainfall_score(
            rainfall_data
        )

        warning = get_warning(
            risk_class,
            risk_score
        )


        return {

            "risk_class": risk_class,

            "risk_score": round(
                risk_score, 2
            ),

            "risk_probability": round(
                probabilities[int(prediction)] * 100,
                2
            ),

            "confidence": round(
                confidence * 100,
                2
            ),

            "early_warning":
                warning["early_warning"],

            "warning_level":
                warning["warning_level"],

            "rainfall_risk_score":
                round(rainfall_score, 2),

            "probabilities": {

                "LOW": round(
                    probabilities[0] * 100,
                    2
                ),

                "MEDIUM": round(
                    probabilities[1] * 100,
                    2
                ),

                "HIGH": round(
                    probabilities[2] * 100,
                    2
                )
            },

            "model_type":
                "RandomForestClassifier",

            "model_version":
                "v1"
        }