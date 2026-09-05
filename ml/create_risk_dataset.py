import pandas as pd
import os

# ==========================================
# FILE PATHS
# ==========================================

rainfall_file = "data/processed/rainfall/ner_district_rainfall.csv"
output_file = "data/processed/rainfall/risk_prediction_dataset.csv"

print("Loading district rainfall data...")

df = pd.read_csv(rainfall_file)

print("Rainfall rows:", len(df))
print("Columns:", list(df.columns))

# ==========================================
# DATE
# ==========================================

df["date"] = pd.to_datetime(df["date"])

# ==========================================
# CREATE RAINFALL FEATURES
# ==========================================

print("\nCreating risk prediction features...")

# Daily rainfall
df["rainfall_daily"] = df["rainfall_mm"]

# Existing rolling rainfall
df["rainfall_24h"] = df["rainfall_24h"]
df["rainfall_3day"] = df["rainfall_3day"]
df["rainfall_7day"] = df["rainfall_7day"]

# Additional useful rainfall features
df["rainfall_14day"] = (
    df.groupby(["state", "district"])["rainfall_mm"]
      .transform(lambda x: x.rolling(14, min_periods=1).sum())
)

df["rainfall_30day"] = (
    df.groupby(["state", "district"])["rainfall_mm"]
      .transform(lambda x: x.rolling(30, min_periods=1).sum())
)

# ==========================================
# RAINFALL INTENSITY FEATURES
# ==========================================

df["heavy_rain_flag"] = (df["rainfall_24h"] >= 50).astype(int)

df["very_heavy_rain_flag"] = (df["rainfall_24h"] >= 100).astype(int)

# ==========================================
# LAG FEATURES
# ==========================================

group = df.groupby(["state", "district"])["rainfall_mm"]

df["rainfall_previous_day"] = group.shift(1)

df["rainfall_2day_lag"] = group.shift(2)

df["rainfall_3day_lag"] = group.shift(3)

# ==========================================
# CLEAN DATA
# ==========================================

df = df.fillna(0)

# ==========================================
# SELECT FINAL MODEL FEATURES
# ==========================================

final_columns = [
    "date",
    "state",
    "district",

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
    "rainfall_3day_lag"
]

df = df[final_columns]

# ==========================================
# SORT
# ==========================================

df = df.sort_values(
    ["state", "district", "date"]
).reset_index(drop=True)

# ==========================================
# SAVE
# ==========================================

os.makedirs(os.path.dirname(output_file), exist_ok=True)

df.to_csv(output_file, index=False)

# ==========================================
# VALIDATION
# ==========================================

print("\n========== RISK DATASET COMPLETE ==========")

print("Output:", os.path.abspath(output_file))

print("Rows:", len(df))

print("Districts:", df["district"].nunique())

print("States:", df["state"].nunique())

print(
    "Date range:",
    df["date"].min().date(),
    "to",
    df["date"].max().date()
)

print("\nColumns:")
print(list(df.columns))

print("\nMissing values:")
print(df.isnull().sum())

print("\nSample:")
print(df.head(10).to_string(index=False))

print("\n===========================================")