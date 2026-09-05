import joblib
import pandas as pd


MODEL_FILE = r"models\risk_model.pkl"
DATA_FILE = r"data\processed\rainfall\ml_training_dataset.csv"


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

print("Model loaded.")


print("\nLoading dataset...")

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(df["date"])


# Test several districts
districts = [
    "Anjaw",
    "Changlang",
    "East Kameng",
    "East Siang",
    "Kurung Kumey",
    "Lohit"
]


print("\n========== MODEL TEST ==========")


for district in districts:

    district_df = df[
        df["district"].str.lower() == district.lower()
    ].copy()

    if len(district_df) == 0:
        print("\nDistrict:", district)
        print("NOT FOUND")
        continue

    latest = district_df.sort_values("date").iloc[-1]

    X = pd.DataFrame(
        [latest[FEATURES].values],
        columns=FEATURES
    )

    prediction = model.predict(X)[0]

    probabilities = model.predict_proba(X)[0]

    probability_map = {
        int(cls): float(prob)
        for cls, prob in zip(model.classes_, probabilities)
    }

    print("\nDistrict:", latest["district"])
    print("State:", latest["state"])
    print("Date:", latest["date"].date())

    print(
        "Rainfall 24h:",
        round(latest["rainfall_24h"], 2)
    )

    print(
        "Rainfall 3day:",
        round(latest["rainfall_3day"], 2)
    )

    print(
        "Rainfall 7day:",
        round(latest["rainfall_7day"], 2)
    )

    print(
        "Risk:",
        RISK_NAMES[int(prediction)]
    )

    print(
        "LOW probability:",
        round(probability_map.get(0, 0) * 100, 2),
        "%"
    )

    print(
        "MEDIUM probability:",
        round(probability_map.get(1, 0) * 100, 2),
        "%"
    )

    print(
        "HIGH probability:",
        round(probability_map.get(2, 0) * 100, 2),
        "%"
    )

    print("-" * 50)


print("\n========== TEST COMPLETE ==========")