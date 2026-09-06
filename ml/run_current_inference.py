from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb

BASE = Path(__file__).resolve().parents[1]

CURRENT_FILE = (
    BASE / "data" / "processed" / "features"
    / "current_ner_risk_features.csv"
)

TERRAIN_FILE = (
    BASE / "data" / "processed" / "terrain"
    / "terrain_district_features.csv"
)

TRAIN_FILE = (
    BASE / "data" / "processed" / "ml"
    / "splits" / "train.csv"
)

MODEL_FILE = (
    BASE / "data" / "processed" / "ml"
    / "models" / "xgboost_landslide_24h_best_trees.json"
)

OUTPUT_FILE = (
    BASE / "data" / "processed" / "ml"
    / "current_ner_risk_predictions.csv"
)

THRESHOLD = 0.87

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
    "rainfall_3day_lag",
    "elevation_mean_m",
    "elevation_min_m",
    "elevation_max_m",
    "elevation_std_m",
    "slope_mean_deg",
    "slope_max_deg",
    "slope_std_deg",
]


def main():

    print("=" * 75)
    print("CRISISCORE - CURRENT NER LANDSLIDE INFERENCE")
    print("=" * 75)

    # ---------------------------------------------------------
    # 1. Load current features
    # ---------------------------------------------------------
    print("\n[1/8] Loading current features...")

    current = pd.read_csv(CURRENT_FILE)
    terrain = pd.read_csv(TERRAIN_FILE)
    train = pd.read_csv(TRAIN_FILE)

    print(f"Current rows : {len(current):,}")
    print(f"Terrain rows : {len(terrain):,}")
    print(f"Train rows   : {len(train):,}")

    # ---------------------------------------------------------
    # 2. Prepare district keys
    # ---------------------------------------------------------
    print("\n[2/8] Preparing district keys...")

    current["district_key"] = (
        current["state"].astype(str).str.strip().str.lower()
        + "_"
        + current["district"].astype(str).str.strip().str.lower()
    )

    terrain["district_key"] = (
        terrain["state"].astype(str).str.strip().str.lower()
        + "_"
        + terrain["district"].astype(str).str.strip().str.lower()
    )

    # ---------------------------------------------------------
    # 3. Merge terrain
    # ---------------------------------------------------------
    print("\n[3/8] Merging terrain features...")

    terrain_cols = [
        "district_key",
        "elevation_mean_m",
        "elevation_min_m",
        "elevation_max_m",
        "elevation_std_m",
        "slope_mean_deg",
        "slope_max_deg",
        "slope_std_deg",
    ]

    terrain_small = terrain[terrain_cols].drop_duplicates(
        subset=["district_key"]
    )

    df = current.merge(
        terrain_small,
        on="district_key",
        how="left"
    )

    print(f"Merged rows: {len(df):,}")
    print(
        "Terrain matched:",
        df["elevation_mean_m"].notna().sum(),
        "/",
        len(df)
    )

    # ---------------------------------------------------------
    # 4. Build exact model features
    # ---------------------------------------------------------
    print("\n[4/8] Building the 17 model features...")

    # Current available rainfall
    df["rainfall_24h"] = pd.to_numeric(
        df["rainfall_24h_mm"],
        errors="coerce"
    )

    # IMPORTANT:
    # Current NRT source contains only one daily observation.
    # Therefore these historical-window features are NOT fabricated.
    unavailable_features = [
        "rainfall_3day",
        "rainfall_7day",
        "rainfall_14day",
        "rainfall_30day",
        "rainfall_previous_day",
        "rainfall_2day_lag",
        "rainfall_3day_lag",
    ]

    for col in unavailable_features:
        df[col] = np.nan

    # Flags cannot honestly be reconstructed from the
    # one-day current snapshot using the historical pipeline.
    df["heavy_rain_flag"] = np.nan
    df["very_heavy_rain_flag"] = np.nan

    # ---------------------------------------------------------
    # 5. Training-only median imputation
    # ---------------------------------------------------------
    print("\n[5/8] Applying training-only median imputation...")

    train_features = train[FEATURES].copy()

    medians = train_features.median(numeric_only=True)

    for col in FEATURES:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        missing = df[col].isna().sum()

        if missing > 0:
            df[col] = df[col].fillna(medians[col])

            print(
                f"  {col}: {missing} values "
                f"filled with training median "
                f"{medians[col]:.4f}"
            )

    # Final missing check
    remaining = df[FEATURES].isna().sum().sum()

    if remaining > 0:
        print("\nERROR: Missing values remain:")
        print(df[FEATURES].isna().sum())
        raise SystemExit(1)

    # ---------------------------------------------------------
    # 6. Load model
    # ---------------------------------------------------------
    print("\n[6/8] Loading final XGBoost model...")

    model = xgb.XGBClassifier()
    model.load_model(MODEL_FILE)

    print("Model loaded successfully.")
    print("Model: xgboost_landslide_24h_best_trees")
    print("Trees: 200")
    print(f"Threshold: {THRESHOLD}")

    # ---------------------------------------------------------
    # 7. Predict
    # ---------------------------------------------------------
    print("\n[7/8] Generating risk probabilities...")

    X = df[FEATURES]

    probabilities = model.predict_proba(X)[:, 1]

    df["risk_probability"] = probabilities

    # Operational threshold selected during validation
    df["risk_level"] = np.where(
        df["risk_probability"] >= THRESHOLD,
        "HIGH",
        "NORMAL"
    )

    df["prediction_horizon"] = "24h"
    df["model_version"] = "xgboost_landslide_24h_200trees"
    df["threshold"] = THRESHOLD

    if "rainfall_date" in df.columns:
        df["prediction_time"] = df["rainfall_date"]
    else:
        df["prediction_time"] = pd.Timestamp.utcnow().isoformat()

    # ---------------------------------------------------------
    # 8. Save backend-ready output
    # ---------------------------------------------------------
    print("\n[8/8] Saving backend-ready predictions...")

    output_cols = [
        "state",
        "district",
        "risk_probability",
        "risk_level",
        "prediction_horizon",
        "model_version",
        "threshold",
        "prediction_time",
    ]

    predictions = df[output_cols].copy()

    predictions = predictions.drop_duplicates(
        subset=["state", "district"],
        keep="last"
    )

    predictions = predictions.sort_values(
        "risk_probability",
        ascending=False
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    predictions.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ---------------------------------------------------------
    # FINAL REPORT
    # ---------------------------------------------------------
    print("\n" + "=" * 75)
    print("CURRENT INFERENCE COMPLETE")
    print("=" * 75)

    print(f"\nDistricts predicted : {len(predictions)}")
    print(f"Output              : {OUTPUT_FILE}")
    print(f"Threshold           : {THRESHOLD}")

    print("\nRisk distribution:")
    print(
        predictions["risk_level"]
        .value_counts()
        .to_string()
    )

    print("\nTop 15 highest-risk districts:")

    print(
        predictions[
            [
                "state",
                "district",
                "risk_probability",
                "risk_level"
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    print("\nProbability statistics:")
    print(
        predictions["risk_probability"]
        .describe()
        .to_string()
    )

    print("\nValidation checks:")

    print(
        "District count:",
        len(predictions)
    )

    print(
        "Duplicate districts:",
        predictions.duplicated(
            subset=["state", "district"]
        ).sum()
    )

    print(
        "Missing probabilities:",
        predictions["risk_probability"].isna().sum()
    )

    print(
        "Probability min:",
        f"{predictions['risk_probability'].min():.6f}"
    )

    print(
        "Probability max:",
        f"{predictions['risk_probability'].max():.6f}"
    )

    print("\nDONE.")


if __name__ == "__main__":
    main()