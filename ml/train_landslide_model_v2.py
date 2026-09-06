import os
import json
import joblib
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    classification_report
)

INPUT = r"data\processed\ml\final_landslide_ml_dataset.csv"

MODEL_DIR = r"models"
MODEL_FILE = os.path.join(MODEL_DIR, "landslide_hgb_v2_native_categorical.joblib")
METRICS_FILE = os.path.join(MODEL_DIR, "landslide_model_v2_metrics.json")

TARGET = "landslide_event"

NUMERIC_FEATURES = [
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
    "rainfall_3day_lag",
    "rainfall_risk_score",
]

CATEGORICAL_FEATURES = [
    "state",
    "district",
]

TIME_FEATURES = [
    "month",
    "day_of_year",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + TIME_FEATURES


def evaluate(model, X, y, threshold=0.10):

    prob = model.predict_proba(X)[:, 1]
    pred = (prob >= threshold).astype(int)

    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(
            precision_score(y, pred, zero_division=0)
        ),
        "recall": float(
            recall_score(y, pred, zero_division=0)
        ),
        "f1": float(
            f1_score(y, pred, zero_division=0)
        ),
        "roc_auc": float(
            roc_auc_score(y, prob)
        ),
        "average_precision": float(
            average_precision_score(y, prob)
        ),
        "brier_score": float(
            brier_score_loss(y, prob)
        ),
        "confusion_matrix": confusion_matrix(
            y, pred
        ).tolist()
    }


def main():

    print("=" * 70)
    print("PHASE 3 V2: NATIVE CATEGORICAL LANDSLIDE MODEL")
    print("=" * 70)

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------

    print("\n[1] Loading dataset...")

    df = pd.read_csv(INPUT)

    df["event_date"] = pd.to_datetime(df["event_date"])

    print(f"Rows: {len(df)}")
    print(
        f"Date range: "
        f"{df['event_date'].min().date()} "
        f"to "
        f"{df['event_date'].max().date()}"
    )

    # ---------------------------------------------------------
    # CATEGORICAL TYPES
    # ---------------------------------------------------------

    print("\n[2] Preparing categorical features...")

    df["state"] = df["state"].astype("category")
    df["district"] = df["district"].astype("category")

    df["month"] = df["event_date"].dt.month
    df["day_of_year"] = df["event_date"].dt.dayofyear

    print("State categories:", df["state"].nunique())
    print("District categories:", df["district"].nunique())

    # ---------------------------------------------------------
    # TEMPORAL SPLIT
    # ---------------------------------------------------------

    print("\n[3] Temporal split...")

    train = df[
        df["event_date"] < "2023-01-01"
    ].copy()

    val = df[
        (df["event_date"] >= "2023-01-01") &
        (df["event_date"] < "2024-01-01")
    ].copy()

    test = df[
        df["event_date"] >= "2024-01-01"
    ].copy()

    print(f"Train:      {len(train)}")
    print(f"Validation: {len(val)}")
    print(f"Test:       {len(test)}")

    print("\nClass distribution:")

    print("\nTRAIN:")
    print(train[TARGET].value_counts())

    print("\nVALIDATION:")
    print(val[TARGET].value_counts())

    print("\nTEST:")
    print(test[TARGET].value_counts())

    X_train = train[FEATURES].copy()
    y_train = train[TARGET].astype(int)

    X_val = val[FEATURES].copy()
    y_val = val[TARGET].astype(int)

    X_test = test[FEATURES].copy()
    y_test = test[TARGET].astype(int)

    # ---------------------------------------------------------
    # MODEL
    # ---------------------------------------------------------

    print("\n[4] Training native categorical HGB...")

    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=15,
        max_depth=6,
        min_samples_leaf=15,
        l2_regularization=1.0,
        categorical_features="from_dtype",
        early_stopping=True,
        random_state=42
    )

    model.fit(X_train, y_train)

    print("Model training complete.")

    print("\nCategorical mask:")
    print(model.is_categorical_)

    # ---------------------------------------------------------
    # THRESHOLD SEARCH ON VALIDATION
    # ---------------------------------------------------------

    print("\n[5] Validation threshold analysis...")

    val_prob = model.predict_proba(X_val)[:, 1]

    best_threshold = 0.50
    best_f1 = -1

    print("\nThreshold | Precision | Recall | F1")
    print("---------------------------------------------")

    for threshold in [
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
    ]:

        val_pred = (
            val_prob >= threshold
        ).astype(int)

        precision = precision_score(
            y_val,
            val_pred,
            zero_division=0
        )

        recall = recall_score(
            y_val,
            val_pred,
            zero_division=0
        )

        f1 = f1_score(
            y_val,
            val_pred,
            zero_division=0
        )

        print(
            f"{threshold:9.2f} | "
            f"{precision:9.3f} | "
            f"{recall:6.3f} | "
            f"{f1:5.3f}"
        )

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print("\nBEST VALIDATION THRESHOLD:")
    print(best_threshold)

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    print("\n[6] Validation evaluation...")

    val_metrics = evaluate(
        model,
        X_val,
        y_val,
        best_threshold
    )

    print(
        json.dumps(
            val_metrics,
            indent=2
        )
    )

    # ---------------------------------------------------------
    # TEST
    # ---------------------------------------------------------

    print("\n[7] Final test evaluation...")

    test_metrics = evaluate(
        model,
        X_test,
        y_test,
        best_threshold
    )

    print(
        json.dumps(
            test_metrics,
            indent=2
        )
    )

    print("\nClassification report:")

    test_prob = model.predict_proba(
        X_test
    )[:, 1]

    test_pred = (
        test_prob >= best_threshold
    ).astype(int)

    print(
        classification_report(
            y_test,
            test_pred,
            target_names=[
                "No Landslide",
                "Landslide"
            ],
            zero_division=0
        )
    )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    print("\n[8] Saving model...")

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "time_features": TIME_FEATURES,
            "target": TARGET,
            "threshold": best_threshold,
            "train_date_end": "2022-12-31",
            "validation_year": 2023,
            "test_date_start": "2024-01-01"
        },
        MODEL_FILE
    )

    results = {
        "model": "HistGradientBoostingClassifier",
        "version": "v2_native_categorical",
        "random_state": 42,

        "dataset": INPUT,

        "train_rows": len(train),
        "validation_rows": len(val),
        "test_rows": len(test),

        "features": FEATURES,

        "categorical_features":
            CATEGORICAL_FEATURES,

        "best_validation_threshold":
            best_threshold,

        "validation":
            val_metrics,

        "test":
            test_metrics
    }

    with open(
        METRICS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    print("\nModel:")
    print(MODEL_FILE)

    print("\nMetrics:")
    print(METRICS_FILE)

    print("\n" + "=" * 70)
    print("PHASE 3 V2 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()