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
    / "xgboost_operational_thresholds.csv"
)


TARGET = "landslide_24h"


# ============================================================
# LOAD
# ============================================================

print("\n[1/5] Loading validation data...")

validation = pd.read_csv(VALIDATION_PATH)
predictions = pd.read_csv(PREDICTIONS_PATH)

y_true = validation[TARGET].astype(int).to_numpy()
probability = predictions["predicted_probability"].to_numpy()

print("Validation rows:", len(validation))
print("Positive events:", int(y_true.sum()))
print("Maximum predicted probability:", round(probability.max(), 6))
print("Minimum predicted probability:", round(probability.min(), 6))


# ============================================================
# THRESHOLDS
# ============================================================

print("\n[2/5] Building threshold grid...")

# Dense threshold search from 0.01 to maximum prediction.
thresholds = np.unique(
    np.concatenate(
        [
            np.arange(0.001, 0.501, 0.001),
            np.arange(0.50, 1.001, 0.005),
        ]
    )
)

results = []


# ============================================================
# EVALUATE
# ============================================================

print("\n[3/5] Evaluating thresholds...")

for threshold in thresholds:

    prediction = (
        probability >= threshold
    ).astype(int)

    precision = precision_score(
        y_true,
        prediction,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        prediction,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        prediction,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        prediction,
        labels=[0, 1],
    ).ravel()

    alerts = int(prediction.sum())

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
            "true_negatives": int(tn),
        }
    )


df = pd.DataFrame(results)


# ============================================================
# BEST F1
# ============================================================

best_f1 = df.loc[df["f1"].idxmax()]


# ============================================================
# ALERT-BUDGET OPTIONS
# ============================================================

# Practical alert budgets for the validation period.
budgets = [100, 250, 500, 1000, 2000, 5000]

budget_rows = []

for budget in budgets:

    eligible = df[df["alerts"] <= budget]

    if len(eligible) == 0:
        continue

    # Among thresholds respecting the alert budget,
    # choose the one with highest recall.
    best = eligible.sort_values(
        ["recall", "precision"],
        ascending=[False, False],
    ).iloc[0]

    row = best.to_dict()
    row["alert_budget"] = budget

    budget_rows.append(row)


budget_df = pd.DataFrame(budget_rows)


# ============================================================
# TOP RESULTS
# ============================================================

print("\n[4/5] Results")


print("\n========================================")
print("GLOBAL BEST F1")
print("========================================")

print("Threshold:", round(best_f1["threshold"], 4))
print("Precision:", round(best_f1["precision"], 6))
print("Recall:", round(best_f1["recall"], 6))
print("F1:", round(best_f1["f1"], 6))
print("Alerts:", int(best_f1["alerts"]))
print("True positives:", int(best_f1["true_positives"]))
print("False positives:", int(best_f1["false_positives"]))
print("False negatives:", int(best_f1["false_negatives"]))


print("\n========================================")
print("TOP 15 THRESHOLDS BY F1")
print("========================================")

top_f1 = df.sort_values(
    "f1",
    ascending=False,
).head(15)

print(
    top_f1[
        [
            "threshold",
            "precision",
            "recall",
            "f1",
            "alerts",
            "true_positives",
            "false_positives",
            "false_negatives",
        ]
    ].to_string(
        index=False,
        formatters={
            "threshold": "{:.4f}".format,
            "precision": "{:.6f}".format,
            "recall": "{:.6f}".format,
            "f1": "{:.6f}".format,
        },
    )
)


print("\n========================================")
print("ALERT-BUDGET ANALYSIS")
print("========================================")

if len(budget_df) > 0:

    print(
        budget_df[
            [
                "alert_budget",
                "threshold",
                "precision",
                "recall",
                "f1",
                "alerts",
                "true_positives",
                "false_positives",
                "false_negatives",
            ]
        ].to_string(
            index=False,
            formatters={
                "threshold": "{:.4f}".format,
                "precision": "{:.6f}".format,
                "recall": "{:.6f}".format,
                "f1": "{:.6f}".format,
            },
        )
    )


# ============================================================
# SAVE
# ============================================================

print("\n[5/5] Saving results...")

df.to_csv(
    OUTPUT_PATH,
    index=False,
)

print("\nSaved:")
print(OUTPUT_PATH)

print("\nSUCCESS: Operational threshold analysis completed.")