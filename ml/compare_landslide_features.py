import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
)


INPUT = r"data\processed\ml\final_landslide_ml_dataset.csv"

OUTPUT = r"models\feature_ablation_comparison.json"

TARGET = "landslide_event"


RAINFALL_FEATURES = [
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


def add_features(df):

    df = df.copy()

    df["event_date"] = pd.to_datetime(
        df["event_date"]
    )

    df["month"] = df["event_date"].dt.month
    df["day_of_year"] = df["event_date"].dt.dayofyear

    return df


def evaluate_model(
    name,
    train,
    val,
    test,
    features
):

    print("\n" + "=" * 70)
    print(f"MODEL: {name}")
    print("=" * 70)

    train = train.copy()
    val = val.copy()
    test = test.copy()

    categorical = []

    if "state" in features:

        train["state"] = train["state"].astype("category")
        val["state"] = val["state"].astype("category")
        test["state"] = test["state"].astype("category")

        categorical.append("state")

    if "district" in features:

        train["district"] = train["district"].astype("category")
        val["district"] = val["district"].astype("category")
        test["district"] = test["district"].astype("category")

        categorical.append("district")

    X_train = train[features]
    y_train = train[TARGET].astype(int)

    X_val = val[features]
    y_val = val[TARGET].astype(int)

    X_test = test[features]
    y_test = test[TARGET].astype(int)

    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=300,
        max_leaf_nodes=15,
        max_depth=6,
        min_samples_leaf=15,
        l2_regularization=1.0,
        early_stopping=True,
        categorical_features="from_dtype",
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    val_prob = model.predict_proba(
        X_val
    )[:, 1]

    test_prob = model.predict_proba(
        X_test
    )[:, 1]

    # Use the already selected operational threshold.
    threshold = 0.10

    val_pred = (
        val_prob >= threshold
    ).astype(int)

    test_pred = (
        test_prob >= threshold
    ).astype(int)

    result = {

        "model": name,

        "features": features,

        "threshold": threshold,

        "validation": {
            "roc_auc": float(
                roc_auc_score(
                    y_val,
                    val_prob
                )
            ),

            "average_precision": float(
                average_precision_score(
                    y_val,
                    val_prob
                )
            ),

            "precision": float(
                precision_score(
                    y_val,
                    val_pred,
                    zero_division=0
                )
            ),

            "recall": float(
                recall_score(
                    y_val,
                    val_pred,
                    zero_division=0
                )
            ),

            "f1": float(
                f1_score(
                    y_val,
                    val_pred,
                    zero_division=0
                )
            ),

            "brier": float(
                brier_score_loss(
                    y_val,
                    val_prob
                )
            )
        },

        "test": {
            "roc_auc": float(
                roc_auc_score(
                    y_test,
                    test_prob
                )
            ),

            "average_precision": float(
                average_precision_score(
                    y_test,
                    test_prob
                )
            ),

            "precision": float(
                precision_score(
                    y_test,
                    test_pred,
                    zero_division=0
                )
            ),

            "recall": float(
                recall_score(
                    y_test,
                    test_pred,
                    zero_division=0
                )
            ),

            "f1": float(
                f1_score(
                    y_test,
                    test_pred,
                    zero_division=0
                )
            ),

            "brier": float(
                brier_score_loss(
                    y_test,
                    test_prob
                )
            )
        }
    }

    print("\nValidation:")
    print(json.dumps(
        result["validation"],
        indent=2
    ))

    print("\nTest:")
    print(json.dumps(
        result["test"],
        indent=2
    ))

    return result


def main():

    print("=" * 70)
    print("LANDSLIDE FEATURE ABLATION AUDIT")
    print("=" * 70)

    print("\n[1] Loading dataset...")

    df = pd.read_csv(INPUT)

    df = add_features(df)

    print(
        f"Rows: {len(df)}"
    )

    # ---------------------------------------------------------
    # TEMPORAL SPLIT
    # ---------------------------------------------------------

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

    print(
        f"Train: {len(train)}"
    )

    print(
        f"Validation: {len(val)}"
    )

    print(
        f"Test: {len(test)}"
    )

    # ---------------------------------------------------------
    # MODEL DEFINITIONS
    # ---------------------------------------------------------

    models = {

        "rainfall_only": (
            RAINFALL_FEATURES
            + [
                "month",
                "day_of_year"
            ]
        ),

        "rainfall_state": (
            RAINFALL_FEATURES
            + [
                "state",
                "month",
                "day_of_year"
            ]
        ),

        "rainfall_state_district": (
            RAINFALL_FEATURES
            + [
                "state",
                "district",
                "month",
                "day_of_year"
            ]
        )
    }

    results = {}

    # ---------------------------------------------------------
    # RUN
    # ---------------------------------------------------------

    for name, features in models.items():

        results[name] = evaluate_model(
            name,
            train,
            val,
            test,
            features
        )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    os.makedirs(
        "models",
        exist_ok=True
    )

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        "\nModel                         "
        "Val ROC-AUC    Test ROC-AUC    "
        "Test Recall    Test F1"
    )

    print("-" * 80)

    for name, result in results.items():

        v = result["validation"]
        t = result["test"]

        print(
            f"{name:30s} "
            f"{v['roc_auc']:.3f}          "
            f"{t['roc_auc']:.3f}          "
            f"{t['recall']:.3f}          "
            f"{t['f1']:.3f}"
        )

    print(
        f"\nSaved: {OUTPUT}"
    )


if __name__ == "__main__":
    main()