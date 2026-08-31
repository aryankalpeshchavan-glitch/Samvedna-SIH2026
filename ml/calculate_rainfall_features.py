import pandas as pd

# Input file
input_file = "data/processed/rainfall/ner_rainfall.csv"

# Output file
output_file = "data/processed/rainfall/ner_rainfall_features.csv"

print("Loading rainfall data...")

df = pd.read_csv(input_file)

# Convert date to datetime
df["date"] = pd.to_datetime(df["date"])

# Make sure data is sorted correctly
df = df.sort_values(
    ["latitude", "longitude", "date"]
)

print("Calculating rainfall features...")

# 24-hour rainfall
df["rainfall_24h"] = df["rainfall_mm"]

# 3-day accumulated rainfall
df["rainfall_3day"] = (
    df.groupby(["latitude", "longitude"])["rainfall_mm"]
      .transform(lambda x: x.rolling(3, min_periods=1).sum())
)

# 7-day accumulated rainfall
df["rainfall_7day"] = (
    df.groupby(["latitude", "longitude"])["rainfall_mm"]
      .transform(lambda x: x.rolling(7, min_periods=1).sum())
)

# Save result
df.to_csv(output_file, index=False)

print("\n========== COMPLETE ==========")
print("Output:", output_file)
print("Rows:", len(df))

print("\nColumns:")
print(df.columns.tolist())

print("\nSample:")
print(
    df[
        [
            "date",
            "latitude",
            "longitude",
            "rainfall_24h",
            "rainfall_3day",
            "rainfall_7day"
        ]
    ].head(15)
)