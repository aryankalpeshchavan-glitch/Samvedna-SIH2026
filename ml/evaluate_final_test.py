from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from xgboost import XGBClassifier


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "train.csv"
)

TEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "test.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "models"
)

OUTPUT_PREDICTIONS = (
    MODEL_DIR
    / "xgboost_final_test_predictions.csv"
)

OUTPUT_RESULTS = (
    MODEL_DIR
    / "xgboost_final_test_results.txt"
)


# ============================================================
# LOCKED MODEL CONFIGURATION
# ============================================================

N_ESTIMATORS = 200
OPERATIONAL_THRESHOLD = 0.870

TARGET = "landslide_24h"


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


# ============================================================
# LOAD DATA
# ============================================================

print("\n[1/8] Loading training and test datasets...")

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)

print("Train:", train.shape)
print("Test:", test.shape)

print(
    "Test date range:",
    test["date"].min(),
    "to",
    test["date"].max(),
)


# ============================================================
# PREPARE FEATURES
# ============================================================

print("\n[2/8] Preparing features...")

X_train = train[FEATURES].copy()
y_train = train[TARGET].astype(int)

X_test = test[FEATURES].copy()
y_test = test[TARGET].astype(int)

print("Number of features:", len(FEATURES))
print("Target:", TARGET)


# ============================================================
# IMPUTATION
# ============================================================

print("\n[3/8] Applying training-only imputation...")

train_medians = X_train.median(numeric_only=True)

X_train = X_train.replace(
    [np.inf, -np.inf],
    np.nan,
)

X_test = X_test.replace(
    [np.inf, -np.inf],
    np.nan,
)

X_train = X_train.fillna(train_medians)
X_test = X_test.fillna(train_medians)

print(
    "Remaining train missing:",
    int(X_train.isna().sum().sum()),
)

print(
    "Remaining test missing:",
    int(X_test.isna().sum().sum()),
)


# ============================================================
# CLASS WEIGHT
# ============================================================

negative_count = int((y_train == 0).sum())
positive_count = int((y_train == 1).sum())

scale_pos_weight = (
    negative_count / positive_count
)

print("\nClass weight:")
print(round(scale_pos_weight, 2))


# ============================================================
# TRAIN LOCKED MODEL
# ============================================================

print("\n[4/8] Training locked 200-tree model...")

model = XGBClassifier(
    n_estimators=N_ESTIMATORS,
    max_depth=4,
    learning_rate=0.03,
    min_child_weight=5,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0.1,
    reg_alpha=0.1,
    reg_lambda=2.0,
    objective="binary:logistic",
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    tree_method="hist",
    random_state=42,
    n_jobs=-1,
)

model.fit(
    X_train,
    y_train,
)

print("Model trained.")


# ============================================================
# TEST PREDICTIONS
# ============================================================

print("\n[5/8] Generating FINAL test predictions...")

test_probability = (
    model.predict_proba(X_test)[:, 1]
)

test_prediction = (
    test_probability >= OPERATIONAL_THRESHOLD
).astype(int)


# ============================================================
# METRICS
# ============================================================

print("\n[6/8] Calculating final metrics...")

pr_auc = average_precision_score(
    y_test,
    test_probability,
)

roc_auc = roc_auc_score(
    y_test,
    test_probability,
)

precision = precision_score(
    y_test,
    test_prediction,
    zero_division=0,
)

recall = recall_score(
    y_test,
    test_prediction,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    test_prediction,
    zero_division=0,
)

tn, fp, fn, tp = confusion_matrix(
    y_test,
    test_prediction,
    labels=[0, 1],
).ravel()

alerts = int(test_prediction.sum())

total = len(y_test)

positive_events = int(y_test.sum())

alert_rate = alerts / total

positive_rate = positive_events / total


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n")
print("=" * 60)
print("FINAL 2025 TEST RESULTS")
print("=" * 60)

print("\nModel configuration")
print("-" * 60)
print("Trees:", N_ESTIMATORS)
print("Max depth: 4")
print("Learning rate: 0.03")
print("Min child weight: 5")
print("Subsample: 0.8")
print("Column sampling: 0.8")
print("Gamma: 0.1")
print("Reg alpha: 0.1")
print("Reg lambda: 2.0")

print("\nLocked operational threshold")
print("-" * 60)
print("Threshold:", OPERATIONAL_THRESHOLD)

print("\nTest dataset")
print("-" * 60)
print("Rows:", total)
print("Positive events:", positive_events)
print("Positive rate:", f"{positive_rate:.6%}")

print("\nPerformance")
print("-" * 60)
print("PR-AUC:", f"{pr_auc:.6f}")
print("ROC-AUC:", f"{roc_auc:.6f}")
print("Precision:", f"{precision:.6f}")
print("Recall:", f"{recall:.6f}")
print("F1:", f"{f1:.6f}")

print("\nConfusion matrix")
print("-" * 60)
print("True negatives :", int(tn))
print("False positives:", int(fp))
print("False negatives:", int(fn))
print("True positives :", int(tp))

print("\nOperational alerts")
print("-" * 60)
print("Alerts:", alerts)
print("Alert rate:", f"{alert_rate:.6%}")


# ============================================================
# SAVE PREDICTIONS
# ============================================================

print("\n[7/8] Saving final predictions...")

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

prediction_output = test[
    [
        "date",
        "state",
        "district",
        TARGET,
    ]
].copy()

prediction_output[
    "predicted_probability"
] = test_probability

prediction_output[
    "alert"
] = test_prediction

prediction_output.to_csv(
    OUTPUT_PREDICTIONS,
    index=False,
)


# ============================================================
# SAVE FINAL REPORT
# ============================================================

with open(
    OUTPUT_RESULTS,
    "w",
    encoding="utf-8",
) as f:

    f.write(
        "CrisisCore Landslide Risk Model - Final Test Results\n"
    )

    f.write("=" * 60 + "\n\n")

    f.write("TEST PERIOD: 2025\n")
    f.write("TARGET: landslide_24h\n\n")

    f.write("LOCKED MODEL\n")
    f.write("-" * 60 + "\n")
    f.write("Model: XGBoost\n")
    f.write(f"Trees: {N_ESTIMATORS}\n")
    f.write("Max depth: 4\n")
    f.write("Learning rate: 0.03\n")
    f.write("Min child weight: 5\n")
    f.write("Subsample: 0.8\n")
    f.write("Column sampling: 0.8\n")
    f.write("Gamma: 0.1\n")
    f.write("Reg alpha: 0.1\n")
    f.write("Reg lambda: 2.0\n")
    f.write(
        f"Operational threshold: "
        f"{OPERATIONAL_THRESHOLD:.3f}\n\n"
    )

    f.write("TEST DATA\n")
    f.write("-" * 60 + "\n")
    f.write(f"Rows: {total}\n")
    f.write(
        f"Positive events: "
        f"{positive_events}\n"
    )
    f.write(
        f"Positive rate: "
        f"{positive_rate:.6%}\n\n"
    )

    f.write("PERFORMANCE\n")
    f.write("-" * 60 + "\n")
    f.write(f"PR-AUC: {pr_auc:.6f}\n")
    f.write(f"ROC-AUC: {roc_auc:.6f}\n")
    f.write(f"Precision: {precision:.6f}\n")
    f.write(f"Recall: {recall:.6f}\n")
    f.write(f"F1: {f1:.6f}\n\n")

    f.write("CONFUSION MATRIX\n")
    f.write("-" * 60 + "\n")
    f.write(f"True negatives: {int(tn)}\n")
    f.write(f"False positives: {int(fp)}\n")
    f.write(f"False negatives: {int(fn)}\n")
    f.write(f"True positives: {int(tp)}\n\n")

    f.write("OPERATIONAL ALERTS\n")
    f.write("-" * 60 + "\n")
    f.write(f"Alerts: {alerts}\n")
    f.write(f"Alert rate: {alert_rate:.6%}\n\n")

    f.write("IMPORTANT\n")
    f.write("-" * 60 + "\n")
    f.write(
        "The model and threshold were selected "
        "using training and validation data.\n"
    )
    f.write(
        "The 2025 test set was not used for model "
        "or threshold selection.\n"
    )
    f.write(
        "These results represent the final held-out "
        "test evaluation.\n"
    )


print("\n[8/8] Complete.")

print("\nSaved predictions:")
print(OUTPUT_PREDICTIONS)

print("\nSaved final report:")
print(OUTPUT_RESULTS)

print("\nSUCCESS: FINAL 2025 TEST EVALUATION COMPLETED.")