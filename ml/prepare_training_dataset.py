import pandas as pd
import os

INPUT_FILE = "data/processed/rainfall/risk_prediction_dataset.csv"
OUTPUT_FILE = "data/processed/rainfall/ml_training_dataset.csv"

print("Loading risk prediction dataset...")

df = pd.read_csv(INPUT_FILE)

print("Rows:", len(df))
print("Columns:", list(df.columns))

# Convert date
df["date"] = pd.to_datetime(df["date"])

# Sort properly
df = df.sort_values(
    ["state", "district", "date"]
).reset_index(drop=True)

# --------------------------------------------------
# CREATE RAINFALL RISK SCORE
# --------------------------------------------------

print("\nCreating rainfall risk score...")

df["rainfall_risk_score"] = (
    0.20 * df["rainfall_24h"] +
    0.25 * df["rainfall_3day"] +
    0.30 * df["rainfall_7day"] +
    0.15 * df["rainfall_14day"] +
    0.10 * df["rainfall_30day"]
)

# --------------------------------------------------
# CREATE INITIAL RISK LABEL
# --------------------------------------------------

print("Creating initial risk labels...")

def classify_risk(row):

    score = row["rainfall_risk_score"]

    if score >= 100:
        return "HIGH"

    elif score >= 50:
        return "MEDIUM"

    else:
        return "LOW"


df["risk_class"] = df.apply(classify_risk, axis=1)

# Numeric target for ML
df["risk_label"] = df["risk_class"].map({
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2
})

# --------------------------------------------------
# SAVE
# --------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

df.to_csv(OUTPUT_FILE, index=False)

print("\n========== DAY 3 COMPLETE ==========")

print("Output:", os.path.abspath(OUTPUT_FILE))
print("Rows:", len(df))
print("Districts:", df["district"].nunique())
print("States:", df["state"].nunique())

print("\nRisk distribution:")
print(df["risk_class"].value_counts())

print("\nMissing values:")
print(df.isnull().sum())

print("\nSample:")
print(
    df[
        [
            "date",
            "state",
            "district",
            "rainfall_24h",
            "rainfall_3day",
            "rainfall_7day",
            "rainfall_14day",
            "rainfall_30day",
            "rainfall_risk_score",
            "risk_class",
            "risk_label"
        ]
    ].head(10).to_string(index=False)
)

print("\n====================================")