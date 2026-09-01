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


print("Loading model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")


# ------------------------------------------------------------
# Test scenarios
# ------------------------------------------------------------

scenarios = {

    "LOW rainfall": {
        "rainfall_24h": 2,
        "rainfall_3day": 5,
        "rainfall_7day": 10,
        "rainfall_14day": 15,
        "rainfall_30day": 25,
        "heavy_rain_flag": 0,
        "very_heavy_rain_flag": 0,
        "rainfall_previous_day": 2,
        "rainfall_2day_lag": 1,
        "rainfall_3day_lag": 0
    },

    "MEDIUM rainfall": {
        "rainfall_24h": 40,
        "rainfall_3day": 90,
        "rainfall_7day": 140,
        "rainfall_14day": 200,
        "rainfall_30day": 300,
        "heavy_rain_flag": 1,
        "very_heavy_rain_flag": 0,
        "rainfall_previous_day": 35,
        "rainfall_2day_lag": 30,
        "rainfall_3day_lag": 25
    },

    "HIGH rainfall": {
        "rainfall_24h": 120,
        "rainfall_3day": 300,
        "rainfall_7day": 500,
        "rainfall_14day": 700,
        "rainfall_30day": 1000,
        "heavy_rain_flag": 1,
        "very_heavy_rain_flag": 1,
        "rainfall_previous_day": 110,
        "rainfall_2day_lag": 100,
        "rainfall_3day_lag": 90
    }
}


print("\n========== RISK LEVEL TEST ==========")


for name, values in scenarios.items():

    X = pd.DataFrame([values], columns=FEATURES)

    prediction = model.predict(X)[0]

    probabilities = model.predict_proba(X)[0]

    probability_map = {
        int(cls): float(prob)
        for cls, prob in zip(model.classes_, probabilities)
    }

    print("\nScenario:", name)

    print(
        "Risk:",
        RISK_NAMES[int(prediction)]
    )

    print(
        "LOW:",
        round(probability_map.get(0, 0) * 100, 2),
        "%"
    )

    print(
        "MEDIUM:",
        round(probability_map.get(1, 0) * 100, 2),
        "%"
    )

    print(
        "HIGH:",
        round(probability_map.get(2, 0) * 100, 2),
        "%"
    )

    print("-" * 50)


print("\n========== TEST COMPLETE ==========")