import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
)

from sklearn.inspection import permutation_importance
from sklearn.calibration import calibration_curve


INPUT = r"data\processed\ml\final_landslide_ml_dataset.csv"
MODEL_FILE = r"models\landslide_hgb_model.joblib"

OUTPUT_DIR = r"models"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "landslide_model_evaluation.json"
)

TARGET = "landslide_event"


def evaluate_thresholds(y_true, probabilities):

    rows = []

    thresholds = np.arange(0.10, 0.91, 0.05)

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        tn, fp, fn, tp = confusion_matrix(
            y_true,
            predictions,
            labels=[0, 1]
        ).ravel()

        rows.append({
            "threshold": round(float(threshold), 2),
            "accuracy": float(
                accuracy_score(y_true, predictions)
            ),
            "precision": float(
                precision_score(
                    y_true,
                    predictions,
                    zero_division=0
                )
            ),
            "recall": float(
                recall_score(
                    y_true,
                    predictions,
                    zero_division=0
                )
            ),
            "f1": float(
                f1_score(
                    y_true,
                    predictions,
                    zero_division=0
                )
            ),
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp)
        })

    return rows


def main():

    print("=" * 70)
    print("LANDSLIDE MODEL EVALUATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. LOAD DATA
    # ---------------------------------------------------------

    print("\n[1] Loading dataset...")

    df = pd.read_csv(INPUT)

    df["event_date"] = pd.to_datetime(
        df["event_date"]
    )

    df["state"] = df["state"].astype("category")
    df["district"] = df["district"].astype("category")

    df["month"] = df["event_date"].dt.month
    df["day_of_year"] = df["event_date"].dt.dayofyear

    print(f"Rows: {len(df)}")

    # ---------------------------------------------------------
    # 2. LOAD MODEL
    # ---------------------------------------------------------

    print("\n[2] Loading trained model...")

    bundle = joblib.load(MODEL_FILE)

    model = bundle["model"]
    features = bundle["features"]

    print(f"Model: {type(model).__name__}")
    print(f"Features: {len(features)}")

    # ---------------------------------------------------------
    # 3. TEMPORAL SPLIT
    # ---------------------------------------------------------

    print("\n[3] Creating temporal split...")

    train = df[
        df["event_date"] < "2023-01-01"
    ].copy()

    validation = df[
        (df["event_date"] >= "2023-01-01") &
        (df["event_date"] < "2024-01-01")
    ].copy()

    test = df[
        df["event_date"] >= "2024-01-01"
    ].copy()

    print(f"Train:      {len(train)}")
    print(f"Validation: {len(validation)}")
    print(f"Test:       {len(test)}")

    # ---------------------------------------------------------
    # 4. PREDICTIONS
    # ---------------------------------------------------------

    print("\n[4] Generating probabilities...")

    X_val = validation[features]
    y_val = validation[TARGET].astype(int)

    X_test = test[features]
    y_test = test[TARGET].astype(int)

    val_prob = model.predict_proba(X_val)[:, 1]
    test_prob = model.predict_proba(X_test)[:, 1]

    # ---------------------------------------------------------
    # 5. BASELINE METRICS
    # ---------------------------------------------------------

    print("\n[5] Validation metrics at threshold 0.50...")

    val_pred = (
        val_prob >= 0.50
    ).astype(int)

    val_metrics = {
        "accuracy": float(
            accuracy_score(y_val, val_pred)
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
        "brier_score": float(
            brier_score_loss(
                y_val,
                val_prob
            )
        )
    }

    print(json.dumps(
        val_metrics,
        indent=2
    ))

    # ---------------------------------------------------------
    # 6. THRESHOLD ANALYSIS
    # ---------------------------------------------------------

    print("\n[6] Threshold analysis...")

    threshold_results = evaluate_thresholds(
        y_val,
        val_prob
    )

    print(
        "\n"
        "Threshold | Precision | Recall | F1"
    )
    print("-" * 45)

    for row in threshold_results:

        print(
            f"{row['threshold']:9.2f} | "
            f"{row['precision']:9.3f} | "
            f"{row['recall']:6.3f} | "
            f"{row['f1']:5.3f}"
        )

    # Choose threshold by best F1 on validation
    best_threshold = max(
        threshold_results,
        key=lambda x: x["f1"]
    )

    print("\nBEST VALIDATION F1 THRESHOLD:")
    print(json.dumps(
        best_threshold,
        indent=2
    ))

    chosen_threshold = best_threshold[
        "threshold"
    ]

    # ---------------------------------------------------------
    # 7. TEST USING VALIDATION-SELECTED THRESHOLD
    # ---------------------------------------------------------

    print(
        "\n[7] Final test evaluation "
        "using validation-selected threshold..."
    )

    test_pred = (
        test_prob >= chosen_threshold
    ).astype(int)

    test_metrics = {
        "threshold": chosen_threshold,

        "accuracy": float(
            accuracy_score(
                y_test,
                test_pred
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

        "brier_score": float(
            brier_score_loss(
                y_test,
                test_prob
            )
        ),

        "confusion_matrix":
            confusion_matrix(
                y_test,
                test_pred
            ).tolist()
    }

    print(json.dumps(
        test_metrics,
        indent=2
    ))

    # ---------------------------------------------------------
    # 8. CALIBRATION
    # ---------------------------------------------------------

    print("\n[8] Calibration analysis...")

    fraction_positive, mean_probability = (
        calibration_curve(
            y_val,
            val_prob,
            n_bins=10,
            strategy="quantile"
        )
    )

    calibration_results = []

    for predicted, actual in zip(
        mean_probability,
        fraction_positive
    ):

        calibration_results.append({
            "mean_predicted_probability":
                float(predicted),

            "fraction_positive":
                float(actual)
        })

    print(
        json.dumps(
            calibration_results,
            indent=2
        )
    )

    # ---------------------------------------------------------
    # 9. PERMUTATION IMPORTANCE
    # ---------------------------------------------------------

    print("\n[9] Permutation feature importance...")

    permutation = permutation_importance(
        model,
        X_val,
        y_val,
        scoring="roc_auc",
        n_repeats=20,
        random_state=42,
        n_jobs=-1
    )

    importance_results = []

    for feature, mean, std in zip(
        features,
        permutation.importances_mean,
        permutation.importances_std
    ):

        importance_results.append({
            "feature": feature,
            "importance_mean": float(mean),
            "importance_std": float(std)
        })

    importance_results.sort(
        key=lambda x: x["importance_mean"],
        reverse=True
    )

    print(
        "\nFeature importance "
        "(validation ROC-AUC permutation):"
    )

    for item in importance_results:

        print(
            f"{item['feature']:30s} "
            f"{item['importance_mean']:.6f} "
            f"+/- {item['importance_std']:.6f}"
        )

    # ---------------------------------------------------------
    # 10. SAVE
    # ---------------------------------------------------------

    print("\n[10] Saving evaluation report...")

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    results = {
        "model": type(model).__name__,

        "dataset": INPUT,

        "validation_rows": len(validation),

        "test_rows": len(test),

        "validation_metrics_threshold_050":
            val_metrics,

        "threshold_analysis":
            threshold_results,

        "selected_threshold":
            chosen_threshold,

        "test_metrics":
            test_metrics,

        "calibration":
            calibration_results,

        "permutation_importance":
            importance_results
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            indent=2
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()