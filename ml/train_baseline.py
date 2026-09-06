import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


INPUT_FILE = r"data\processed\events\landslide_training_samples.csv"

MODEL_DIR = r"models"
MODEL_FILE = os.path.join(
    MODEL_DIR,
    "landslide_baseline_model.pkl"
)


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


print("\n==============================================")
print(" CRISISCORE - STEP 6 BASELINE MODEL")
print("==============================================")


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading training dataset...")

df = pd.read_csv(INPUT_FILE)

print("Rows:", len(df))


# ============================================================
# CHECK FEATURES
# ============================================================

missing_features = [
    f for f in FEATURES
    if f not in df.columns
]

if missing_features:

    raise ValueError(
        f"Missing features: {missing_features}"
    )


# ============================================================
# TRAIN EACH HORIZON SEPARATELY
# ============================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


for horizon in [24, 48, 72]:

    print("\n==============================================")
    print(f"             {horizon}-HOUR MODEL")
    print("==============================================")


    data = df[
        df["prediction_horizon_hours"] == horizon
    ].copy()


    X = data[FEATURES]

    y = data["target"]


    print("\nSamples:", len(data))

    print(
        "Positive:",
        int(y.sum())
    )

    print(
        "Negative:",
        int((y == 0).sum())
    )


    # --------------------------------------------------------
    # IMPORTANT:
    # This is a baseline only.
    # We use class_weight to account for extreme imbalance.
    # --------------------------------------------------------

    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )


    print("\nTraining...")

    model.fit(X, y)


    # --------------------------------------------------------
    # Training-set evaluation
    #
    # This is NOT a validation score.
    # It is only a baseline sanity check.
    # --------------------------------------------------------

    predictions = model.predict(X)


    accuracy = accuracy_score(
        y,
        predictions
    )

    precision = precision_score(
        y,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y,
        predictions,
        zero_division=0
    )


    print("\nBASELINE METRICS")

    print(
        "Accuracy:",
        round(accuracy, 4)
    )

    print(
        "Precision:",
        round(precision, 4)
    )

    print(
        "Recall:",
        round(recall, 4)
    )

    print(
        "F1:",
        round(f1, 4)
    )


    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y,
            predictions
        )
    )


    # --------------------------------------------------------
    # Save model
    # --------------------------------------------------------

    model_file = os.path.join(
        MODEL_DIR,
        f"landslide_baseline_{horizon}h.pkl"
    )


    joblib.dump(
        model,
        model_file
    )


    print(
        "\nModel saved:",
        model_file
    )


print("\n==============================================")
print(" STEP 6 BASELINE TRAINING COMPLETE")
print("==============================================")