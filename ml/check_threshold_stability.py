from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

VALIDATION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "validation.csv"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "models"
    / "xgboost_validation_predictions.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "models"
    / "xgboost_threshold_stability.csv"
)


TARGET = "landslide_24h"

# Fine-grained region around the candidate operational threshold.
THRESHOLDS = np.arange(
    0.84,
    0.911,
    0.005
)


# ============================================================
# LOAD
# ============================================================

print("\n[1/4] Loading validation data...")

validation = pd.read_csv(VALIDATION_PATH)
predictions = pd.read_csv(PREDICTIONS_PATH)

y_true = validation[TARGET].astype(int).to_numpy()
probability = predictions["predicted_probability"].to_numpy()

print("Validation rows:", len(validation))
print("Positive events:", int(y_true.sum()))


# ============================================================
# EVALUATE
# ============================================================

print("\n[2/4] Checking threshold stability...")

results = []

for threshold in THRESHOLDS:

    y_pred = (
        probability >= threshold
    ).astype(int)

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    ).ravel()

    alerts = int(y_pred.sum())

    results.append(
        {
            "threshold": threshold,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "alerts": alerts,
            "true_positives": int(tp),
            "false_positives": int(fp),
            "false_negatives": int(fn),
        }
    )


df = pd.DataFrame(results)


# ============================================================
# PRINT
# ============================================================

print("\n========================================")
print("THRESHOLD STABILITY")
print("========================================")

print(
    df.to_string(
        index=False,
        formatters={
            "threshold": "{:.3f}".format,
            "precision": "{:.6f}".format,
            "recall": "{:.6f}".format,
            "f1": "{:.6f}".format,
        },
    )
)


# ============================================================
# BEST POINTS
# ============================================================

best_f1 = df.loc[df["f1"].idxmax()]

# Candidate operational threshold closest to 0.87.
operational = df.iloc[
    (df["threshold"] - 0.870).abs().argmin()
]


print("\n========================================")
print("BEST F1 IN STABILITY RANGE")
print("========================================")

print("Threshold:", round(best_f1["threshold"], 3))
print("Precision:", round(best_f1["precision"], 6))
print("Recall:", round(best_f1["recall"], 6))
print("F1:", round(best_f1["f1"], 6))
print("Alerts:", int(best_f1["alerts"]))


print("\n========================================")
print("CANDIDATE OPERATIONAL THRESHOLD")
print("========================================")

print("Threshold:", round(operational["threshold"], 3))
print("Precision:", round(operational["precision"], 6))
print("Recall:", round(operational["recall"], 6))
print("F1:", round(operational["f1"], 6))
print("Alerts:", int(operational["alerts"]))
print("True positives:", int(operational["true_positives"]))
print("False positives:", int(operational["false_positives"]))
print("False negatives:", int(operational["false_negatives"]))


# ============================================================
# SAVE
# ============================================================

print("\n[3/4] Saving results...")

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# FINAL STATUS
# ============================================================

print("\n[4/4] Complete.")

print(
    "Saved:",
    OUTPUT_PATH,
)

print("\nSUCCESS: Threshold stability check completed.")