import os
import sys
import json
import traceback
import joblib
import numpy as np
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
    classification_report,
)

# ============================================================
# CONFIG
# ============================================================

INPUT = r"data\processed\ml\final_landslide_ml_dataset.csv"

MODEL_DIR = r"models"

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "landslide_hgb_v3.joblib"
)

METRICS_FILE = os.path.join(
    MODEL_DIR,
    "landslide_v3_metrics.json"
)

THRESHOLD_FILE = os.path.join(
    MODEL_DIR,
    "landslide_v3_threshold.json"
)

LOG_FILE = os.path.join(
    MODEL_DIR,
    "landslide_v3_training.log"
)

TARGET = "landslide_event"

RAIN_FEATURES = [
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

FEATURES = (
    RAIN_FEATURES
    + CATEGORICAL_FEATURES
    + TIME_FEATURES
)


# ============================================================
# LOGGING
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)

log_file = open(
    LOG_FILE,
    "w",
    encoding="utf-8"
)


def log(message=""):
    print(message, flush=True)
    log_file.write(str(message) + "\n")
    log_file.flush()


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(y_true, probability, threshold):

    prediction = (
        probability >= threshold
    ).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        prediction,
        labels=[0, 1]
    ).ravel()

    return {
        "threshold": float(threshold),

        "accuracy": float(
            accuracy_score(y_true, prediction)
        ),

        "precision": float(
            precision_score(
                y_true,
                prediction,
                zero_division=0
            )
        ),

        "recall": float(
            recall_score(
                y_true,
                prediction,
                zero_division=0
            )
        ),

        "f1": float(
            f1_score(
                y_true,
                prediction,
                zero_division=0
            )
        ),

        "roc_auc": float(
            roc_auc_score(
                y_true,
                probability
            )
        ),

        "average_precision": float(
            average_precision_score(
                y_true,
                probability
            )
        ),

        "brier_score": float(
            brier_score_loss(
                y_true,
                probability
            )
        ),

        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),

        "confusion_matrix": [
            [int(tn), int(fp)],
            [int(fn), int(tp)]
        ]
    }


# ============================================================
# MAIN
# ============================================================

def main():

    log("=" * 75)
    log("PHASE 3 V3: LANDSLIDE RISK MODEL")
    log("=" * 75)

    log("")
    log("Python:")
    log(sys.version)

    log("")
    log("Starting V3...")
    log("")

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------

    log("[1/10] Loading dataset...")
    log(f"Input: {INPUT}")

    if not os.path.exists(INPUT):
        raise FileNotFoundError(
            f"Dataset not found: {INPUT}"
        )

    df = pd.read_csv(INPUT)

    log(f"Rows: {len(df)}")
    log(f"Columns: {len(df.columns)}")

    required_columns = (
        ["event_date", TARGET]
        + RAIN_FEATURES
        + CATEGORICAL_FEATURES
    )

    missing_columns = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns: "
            + str(missing_columns)
        )

    log("Dataset loaded successfully.")

    # --------------------------------------------------------
    # 2. DATE
    # --------------------------------------------------------

    log("")
    log("[2/10] Preparing dates...")

    df["event_date"] = pd.to_datetime(
        df["event_date"],
        errors="coerce"
    )

    if df["event_date"].isna().any():
        raise ValueError(
            "Invalid event_date values found."
        )

    df["month"] = df["event_date"].dt.month
    df["day_of_year"] = (
        df["event_date"].dt.dayofyear
    )

    log(
        f"Date range: "
        f"{df['event_date'].min().date()} "
        f"to "
        f"{df['event_date'].max().date()}"
    )

    # --------------------------------------------------------
    # 3. CATEGORICAL FEATURES
    # --------------------------------------------------------

    log("")
    log("[3/10] Preparing categorical features...")

    df["state"] = (
        df["state"]
        .astype("string")
        .str.strip()
        .astype("category")
    )

    df["district"] = (
        df["district"]
        .astype("string")
        .str.strip()
        .astype("category")
    )

    log(
        f"States: "
        f"{df['state'].nunique()}"
    )

    log(
        f"Districts: "
        f"{df['district'].nunique()}"
    )

    # --------------------------------------------------------
    # 4. SORT
    # --------------------------------------------------------

    log("")
    log("[4/10] Sorting chronologically...")

    df = df.sort_values(
        "event_date"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # 5. TEMPORAL SPLIT
    # --------------------------------------------------------

    log("")
    log("[5/10] Creating temporal split...")

    train = df[
        df["event_date"] < "2023-01-01"
    ].copy()

    validation = df[
        (df["event_date"] >= "2023-01-01")
        &
        (df["event_date"] < "2024-01-01")
    ].copy()

    test = df[
        df["event_date"] >= "2024-01-01"
    ].copy()

    log(f"Train:      {len(train)}")
    log(f"Validation: {len(validation)}")
    log(f"Test:       {len(test)}")

    log("")
    log("Class distribution:")

    log(
        "TRAIN:\n"
        + str(train[TARGET].value_counts())
    )

    log(
        "\nVALIDATION:\n"
        + str(validation[TARGET].value_counts())
    )

    log(
        "\nTEST:\n"
        + str(test[TARGET].value_counts())
    )

    # --------------------------------------------------------
    # 6. PREPARE X / Y
    # --------------------------------------------------------

    log("")
    log("[6/10] Preparing X and y...")

    X_train = train[FEATURES].copy()
    y_train = train[TARGET].astype(int)

    X_val = validation[FEATURES].copy()
    y_val = validation[TARGET].astype(int)

    X_test = test[FEATURES].copy()
    y_test = test[TARGET].astype(int)

    log(
        f"Training features: "
        f"{X_train.shape}"
    )

    log(
        f"Validation features: "
        f"{X_val.shape}"
    )

    log(
        f"Test features: "
        f"{X_test.shape}"
    )

    # --------------------------------------------------------
    # 7. MODEL
    # --------------------------------------------------------

    log("")
    log("[7/10] Training V3 model...")
    log("This may take a little time.")
    log("")

    categorical_mask = [
        feature in CATEGORICAL_FEATURES
        for feature in FEATURES
    ]

    log(
        "Categorical mask:"
    )

    log(
        str(categorical_mask)
    )

    model = HistGradientBoostingClassifier(
        learning_rate=0.04,
        max_iter=400,
        max_leaf_nodes=15,
        max_depth=6,
        min_samples_leaf=15,
        l2_regularization=2.0,

        categorical_features=categorical_mask,

        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=30,

        random_state=42
    )

    log("Calling model.fit()...")

    model.fit(
        X_train,
        y_train
    )

    log("")
    log("MODEL TRAINING COMPLETE.")

    if hasattr(model, "n_iter_"):
        log(
            f"Iterations used: "
            f"{model.n_iter_}"
        )

    # --------------------------------------------------------
    # 8. VALIDATION
    # --------------------------------------------------------

    log("")
    log("[8/10] Validation evaluation...")

    val_probability = model.predict_proba(
        X_val
    )[:, 1]

    thresholds = [
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.50,
    ]

    best_threshold = 0.50
    best_f1 = -1

    log("")
    log(
        "Threshold | Precision | Recall | F1"
    )
    log("-" * 45)

    threshold_results = []

    for threshold in thresholds:

        metrics = calculate_metrics(
            y_val,
            val_probability,
            threshold
        )

        threshold_results.append(
            metrics
        )

        log(
            f"{threshold:8.2f} | "
            f"{metrics['precision']:9.3f} | "
            f"{metrics['recall']:6.3f} | "
            f"{metrics['f1']:5.3f}"
        )

        if metrics["f1"] > best_f1:

            best_f1 = metrics["f1"]
            best_threshold = threshold

    log("")
    log(
        f"BEST VALIDATION THRESHOLD: "
        f"{best_threshold}"
    )

    validation_metrics = calculate_metrics(
        y_val,
        val_probability,
        best_threshold
    )

    log("")
    log(
        json.dumps(
            validation_metrics,
            indent=2
        )
    )

    # --------------------------------------------------------
    # 9. TEST
    # --------------------------------------------------------

    log("")
    log("[9/10] Final test evaluation...")

    test_probability = model.predict_proba(
        X_test
    )[:, 1]

    test_metrics = calculate_metrics(
        y_test,
        test_probability,
        best_threshold
    )

    log("")
    log(
        json.dumps(
            test_metrics,
            indent=2
        )
    )

    test_prediction = (
        test_probability >= best_threshold
    ).astype(int)

    log("")
    log("Classification report:")

    log(
        classification_report(
            y_test,
            test_prediction,
            target_names=[
                "No Landslide",
                "Landslide"
            ],
            zero_division=0
        )
    )

    # --------------------------------------------------------
    # 10. SAVE
    # --------------------------------------------------------

    log("")
    log("[10/10] Saving V3 artifacts...")

    artifact = {
        "model": model,
        "features": FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "rainfall_features": RAIN_FEATURES,
        "time_features": TIME_FEATURES,
        "target": TARGET,
        "threshold": best_threshold,

        "train_date_end": "2022-12-31",
        "validation_year": 2023,
        "test_date_start": "2024-01-01",

        "state_categories": list(
            df["state"].cat.categories
        ),

        "district_categories": list(
            df["district"].cat.categories
        )
    }

    joblib.dump(
        artifact,
        MODEL_FILE
    )

    results = {
        "model": (
            "HistGradientBoostingClassifier"
        ),

        "version": "v3",

        "random_state": 42,

        "dataset": INPUT,

        "rows": len(df),

        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),

        "features": FEATURES,

        "categorical_features":
            CATEGORICAL_FEATURES,

        "time_features":
            TIME_FEATURES,

        "best_threshold":
            best_threshold,

        "validation":
            validation_metrics,

        "test":
            test_metrics,

        "threshold_analysis":
            threshold_results,

        "model_iterations":
            int(getattr(model, "n_iter_", -1))
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

    with open(
        THRESHOLD_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "threshold": best_threshold,
                "selection_metric": "validation_f1"
            },
            f,
            indent=2
        )

    log("")
    log("=" * 75)
    log("V3 TRAINING COMPLETE")
    log("=" * 75)

    log("")
    log("MODEL:")
    log(MODEL_FILE)

    log("")
    log("METRICS:")
    log(METRICS_FILE)

    log("")
    log("THRESHOLD:")
    log(THRESHOLD_FILE)

    log("")
    log("LOG:")
    log(LOG_FILE)

    log("")
    log("FINAL TEST RESULTS:")
    log(
        f"ROC-AUC:    "
        f"{test_metrics['roc_auc']:.4f}"
    )

    log(
        f"Precision:  "
        f"{test_metrics['precision']:.4f}"
    )

    log(
        f"Recall:     "
        f"{test_metrics['recall']:.4f}"
    )

    log(
        f"F1:         "
        f"{test_metrics['f1']:.4f}"
    )

    log(
        f"Brier:      "
        f"{test_metrics['brier_score']:.4f}"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        log("")
        log("=" * 75)
        log("V3 FAILED")
        log("=" * 75)

        log("")
        log(
            f"ERROR TYPE: "
            f"{type(e).__name__}"
        )

        log(
            f"ERROR: "
            f"{e}"
        )

        log("")
        log("TRACEBACK:")

        traceback.print_exc(
            file=log_file
        )

        traceback.print_exc()

        log("")
        log(
            f"Full error saved to: "
            f"{LOG_FILE}"
        )

        sys.exit(1)

    finally:

        log_file.close()