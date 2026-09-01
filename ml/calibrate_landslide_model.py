import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix,
)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.frozen import FrozenEstimator


# ============================================================
# CONFIG
# ============================================================

DATASET = r"data\processed\ml\final_landslide_ml_dataset.csv"

BASE_MODEL = r"models\landslide_hgb_v2_native_categorical.joblib"

OUTPUT_MODEL = r"models\landslide_calibrated_v1.joblib"
OUTPUT_METRICS = r"models\landslide_calibration_metrics.json"
OUTPUT_CURVE = r"models\landslide_calibration_curve.json"
OUTPUT_THRESHOLD = r"models\landslide_final_threshold.json"


TARGET = "landslide_event"

THRESHOLD = 0.10


# ============================================================
# LOGGING
# ============================================================

def log(message=""):
    print(message, flush=True)


# ============================================================
# METRICS
# ============================================================

def evaluate(y_true, probabilities, threshold):

    predictions = (probabilities >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[0, 1]
    ).ravel()

    return {
        "threshold": float(threshold),
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
        "roc_auc": float(
            roc_auc_score(y_true, probabilities)
        ),
        "average_precision": float(
            average_precision_score(
                y_true,
                probabilities
            )
        ),
        "brier_score": float(
            brier_score_loss(
                y_true,
                probabilities
            )
        ),
        "log_loss": float(
            log_loss(
                y_true,
                probabilities,
                labels=[0, 1]
            )
        ),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    log("=" * 70)
    log("PHASE 4: LANDSLIDE PROBABILITY CALIBRATION")
    log("=" * 70)

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------

    log("\n[1/8] Loading dataset...")

    df = pd.read_csv(DATASET)

    df["event_date"] = pd.to_datetime(
        df["event_date"]
    )

    log(f"Rows: {len(df)}")

    # --------------------------------------------------------
    # 2. PREPARE FEATURES
    # --------------------------------------------------------

    log("\n[2/8] Preparing features...")

    df["state"] = df["state"].astype("category")
    df["district"] = df["district"].astype("category")

    df["month"] = df["event_date"].dt.month
    df["day_of_year"] = df["event_date"].dt.dayofyear

    # IMPORTANT:
    # Must match the V2 model feature order.

    features = [
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
        "state",
        "district",
        "month",
        "day_of_year",
    ]

    # --------------------------------------------------------
    # 3. TEMPORAL SPLIT
    # --------------------------------------------------------

    log("\n[3/8] Creating temporal split...")

    df = df.sort_values("event_date").reset_index(drop=True)

    train = df[
        df["event_date"] < "2023-01-01"
    ].copy()

    calibration = df[
        (df["event_date"] >= "2023-01-01") &
        (df["event_date"] < "2024-01-01")
    ].copy()

    test = df[
        df["event_date"] >= "2024-01-01"
    ].copy()

    log(f"Train:       {len(train)}")
    log(f"Calibration: {len(calibration)}")
    log(f"Test:        {len(test)}")

    X_cal = calibration[features].copy()
    y_cal = calibration[TARGET].astype(int)

    X_test = test[features].copy()
    y_test = test[TARGET].astype(int)

    # --------------------------------------------------------
    # 4. LOAD V2 MODEL
    # --------------------------------------------------------

    log("\n[4/8] Loading V2 model...")

    package = joblib.load(BASE_MODEL)

    base_model = package["model"]

    log(f"Model type: {type(base_model).__name__}")

    # --------------------------------------------------------
    # 5. BASELINE PROBABILITIES
    # --------------------------------------------------------

    log("\n[5/8] Generating baseline probabilities...")

    calibration_base_prob = base_model.predict_proba(
        X_cal
    )[:, 1]

    test_base_prob = base_model.predict_proba(
        X_test
    )[:, 1]

    before_calibration = evaluate(
        y_test,
        test_base_prob,
        THRESHOLD
    )

    log("\nBASELINE TEST:")
    log(json.dumps(
        before_calibration,
        indent=2
    ))

    # --------------------------------------------------------
    # 6. CALIBRATE
    # --------------------------------------------------------

    log("\n[6/8] Fitting sigmoid calibration...")
    log("Calibration data is kept separate from training.")

    # FrozenEstimator prevents the already-trained V2
    # classifier from being retrained.
    #
    # Sigmoid is selected because calibration set = 141 rows.

    calibrated = CalibratedClassifierCV(
        FrozenEstimator(base_model),
        method="sigmoid"
    )

    calibrated.fit(
        X_cal,
        y_cal
    )

    log("Calibration complete.")

    # --------------------------------------------------------
    # 7. EVALUATE
    # --------------------------------------------------------

    log("\n[7/8] Evaluating calibrated model...")

    calibrated_test_prob = calibrated.predict_proba(
        X_test
    )[:, 1]

    after_calibration = evaluate(
        y_test,
        calibrated_test_prob,
        THRESHOLD
    )

    log("\nCALIBRATED TEST:")
    log(json.dumps(
        after_calibration,
        indent=2
    ))

    # --------------------------------------------------------
    # CALIBRATION CURVE
    # --------------------------------------------------------

    log("\nGenerating calibration curve...")

    prob_true, prob_pred = calibration_curve(
        y_test,
        calibrated_test_prob,
        n_bins=10,
        strategy="quantile"
    )

    curve = []

    for predicted, actual in zip(
        prob_pred,
        prob_true
    ):
        curve.append({
            "mean_predicted_probability": float(
                predicted
            ),
            "fraction_positive": float(
                actual
            )
        })

    # --------------------------------------------------------
    # SAVE EVERYTHING
    # --------------------------------------------------------

    log("\n[8/8] Saving production artifacts...")

    os.makedirs(
        os.path.dirname(OUTPUT_MODEL),
        exist_ok=True
    )

    # Model package
    joblib.dump(
        {
            "model": calibrated,
            "features": features,
            "target": TARGET,
            "base_model": BASE_MODEL,
            "calibration_method": "sigmoid",
            "calibration_period": "2023",
            "test_period": "2024-2025",
            "threshold": THRESHOLD,
            "version": "calibrated_v1",
        },
        OUTPUT_MODEL
    )

    # Metrics
    metrics = {
        "version": "calibrated_v1",

        "base_model": BASE_MODEL,

        "calibration_method": "sigmoid",

        "calibration_rows": len(calibration),

        "test_rows": len(test),

        "threshold": THRESHOLD,

        "before_calibration": before_calibration,

        "after_calibration": after_calibration,

        "improvement": {
            "brier_score_change":
                float(
                    before_calibration["brier_score"]
                    -
                    after_calibration["brier_score"]
                ),

            "log_loss_change":
                float(
                    before_calibration["log_loss"]
                    -
                    after_calibration["log_loss"]
                ),
        }
    }

    with open(
        OUTPUT_METRICS,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metrics,
            f,
            indent=2
        )

    # Calibration curve
    with open(
        OUTPUT_CURVE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            curve,
            f,
            indent=2
        )

    # Threshold
    threshold_data = {
        "version": "calibrated_v1",
        "threshold": THRESHOLD,
        "selection_basis":
            "V2 validation F1 optimization",
        "threshold_source":
            "2023 validation period",
        "warning":
            "Threshold is an ML operating point, "
            "not a scientifically validated hazard boundary."
    }

    with open(
        OUTPUT_THRESHOLD,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            threshold_data,
            f,
            indent=2
        )

    # --------------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------------

    log("\n" + "=" * 70)
    log("PHASE 4 COMPLETE")
    log("=" * 70)

    log("\nCALIBRATED MODEL:")
    log(OUTPUT_MODEL)

    log("\nMETRICS:")
    log(OUTPUT_METRICS)

    log("\nCALIBRATION CURVE:")
    log(OUTPUT_CURVE)

    log("\nTHRESHOLD:")
    log(OUTPUT_THRESHOLD)

    log("\nFINAL TEST RESULTS:")

    log(
        f"ROC-AUC:    "
        f"{after_calibration['roc_auc']:.4f}"
    )

    log(
        f"Precision:  "
        f"{after_calibration['precision']:.4f}"
    )

    log(
        f"Recall:     "
        f"{after_calibration['recall']:.4f}"
    )

    log(
        f"F1:         "
        f"{after_calibration['f1']:.4f}"
    )

    log(
        f"Brier:      "
        f"{after_calibration['brier_score']:.4f}"
    )

    log(
        f"Log Loss:   "
        f"{after_calibration['log_loss']:.4f}"
    )

    log("\n" + "=" * 70)
    log("READY FOR LIVE INFERENCE")
    log("=" * 70)


if __name__ == "__main__":
    main()