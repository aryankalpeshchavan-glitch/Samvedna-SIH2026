from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
    roc_auc_score,
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

VALIDATION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "validation.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "models"
)

MODEL_PATH = MODEL_DIR / "xgboost_landslide_24h_best_trees.json"

OUTPUT_THRESHOLD = MODEL_DIR / "xgboost_threshold_comparison.csv"
OUTPUT_INFO = MODEL_DIR / "xgboost_selected_threshold.txt"
OUTPUT_PREDICTIONS = MODEL_DIR / "xgboost_validation_predictions.csv"


# ============================================================
# FEATURES
# ============================================================

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

TARGET = "landslide_24h"


# ============================================================
# OPERATIONAL THRESHOLDS
# ============================================================

THRESHOLDS = [
    0.001,
    0.002,
    0.005,
    0.010,
    0.015,
    0.020,
    0.030,
    0.040,
    0.050,
    0.075,
    0.100,
    0.150,
    0.200,
    0.250,
    0.300,
    0.400,
    0.500,
]


# ============================================================
# LOAD DATA
# ============================================================

print("\n[1/7] Loading datasets...")

train = pd.read_csv(TRAIN_PATH)
validation = pd.read_csv(VALIDATION_PATH)

print("Train:", train.shape)
print("Validation:", validation.shape)


# ============================================================
# PREPARE FEATURES
# ============================================================

print("\n[2/7] Preparing features...")

X_train = train[FEATURES].copy()
y_train = train[TARGET].astype(int)

X_val = validation[FEATURES].copy()
y_val = validation[TARGET].astype(int)

print("Features:", len(FEATURES))
print("Target:", TARGET)


# ============================================================
# IMPUTE USING TRAINING MEDIANS
# ============================================================

print("\n[3/7] Imputing missing values...")

train_medians = X_train.median(numeric_only=True)

X_train = X_train.fillna(train_medians)
X_val = X_val.fillna(train_medians)

X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_val = X_val.replace([np.inf, -np.inf], np.nan)

X_train = X_train.fillna(train_medians)
X_val = X_val.fillna(train_medians)

print("Remaining train missing:", int(X_train.isna().sum().sum()))
print("Remaining validation missing:", int(X_val.isna().sum().sum()))


# ============================================================
# CLASS WEIGHT
# ============================================================

negative_count = int((y_train == 0).sum())
positive_count = int((y_train == 1).sum())

scale_pos_weight = negative_count / positive_count

print("\nClass weight:")
print(round(scale_pos_weight, 2))


# ============================================================
# TRAIN FINAL VALIDATION-SELECTION MODEL
# ============================================================

print("\n[4/7] Training 200-tree model...")

model = XGBClassifier(
    n_estimators=200,
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

model.fit(X_train, y_train)

print("Model trained.")


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

print("\n[5/7] Generating validation predictions...")

val_probability = model.predict_proba(X_val)[:, 1]

pr_auc = average_precision_score(y_val, val_probability)
roc_auc = roc_auc_score(y_val, val_probability)

print("Validation PR-AUC:", round(pr_auc, 6))
print("Validation ROC-AUC:", round(roc_auc, 6))


# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

print("\n[6/7] Optimizing operational threshold...")

results = []

for threshold in THRESHOLDS:

    prediction = (val_probability >= threshold).astype(int)

    precision = precision_score(
        y_val,
        prediction,
        zero_division=0,
    )

    recall = recall_score(
        y_val,
        prediction,
        zero_division=0,
    )

    f1 = f1_score(
        y_val,
        prediction,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        y_val,
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


results_df = pd.DataFrame(results)

# Sort by F1 to identify the mathematical optimum.
best_f1_row = results_df.loc[
    results_df["f1"].idxmax()
]

# Also identify useful operational points.
best_precision_row = results_df.loc[
    results_df["precision"].idxmax()
]

best_recall_row = results_df.loc[
    results_df["recall"].idxmax()
]


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n========================================")
print("THRESHOLD COMPARISON")
print("========================================")

print(
    results_df.to_string(
        index=False,
        formatters={
            "threshold": "{:.3f}".format,
            "precision": "{:.6f}".format,
            "recall": "{:.6f}".format,
            "f1": "{:.6f}".format,
        },
    )
)

print("\n========================================")
print("BEST F1 THRESHOLD")
print("========================================")

print(
    "Threshold:",
    best_f1_row["threshold"],
)

print(
    "Precision:",
    round(best_f1_row["precision"], 6),
)

print(
    "Recall:",
    round(best_f1_row["recall"], 6),
)

print(
    "F1:",
    round(best_f1_row["f1"], 6),
)

print(
    "Alerts:",
    int(best_f1_row["alerts"]),
)

print(
    "True positives:",
    int(best_f1_row["true_positives"]),
)

print(
    "False positives:",
    int(best_f1_row["false_positives"]),
)

print(
    "False negatives:",
    int(best_f1_row["false_negatives"]),
)


# ============================================================
# SAVE RESULTS
# ============================================================

print("\nSaving threshold results...")

MODEL_DIR.mkdir(parents=True, exist_ok=True)

results_df.to_csv(
    OUTPUT_THRESHOLD,
    index=False,
)

prediction_output = validation[
    ["date", "state", "district", TARGET]
].copy()

prediction_output["predicted_probability"] = val_probability

prediction_output.to_csv(
    OUTPUT_PREDICTIONS,
    index=False,
)


# ============================================================
# SAVE SELECTED THRESHOLD INFO
# ============================================================

selected_threshold = float(best_f1_row["threshold"])

with open(OUTPUT_INFO, "w", encoding="utf-8") as f:

    f.write("CrisisCore Landslide 24h XGBoost Threshold Selection\n")
    f.write("=" * 60 + "\n\n")

    f.write("Target: landslide_24h\n")
    f.write("Model: XGBoost\n")
    f.write("Trees: 200\n")
    f.write("Validation period: 2023-2024\n\n")

    f.write(f"Validation PR-AUC: {pr_auc:.6f}\n")
    f.write(f"Validation ROC-AUC: {roc_auc:.6f}\n\n")

    f.write(f"Selected threshold: {selected_threshold:.3f}\n")
    f.write(
        f"Precision: {best_f1_row['precision']:.6f}\n"
    )
    f.write(
        f"Recall: {best_f1_row['recall']:.6f}\n"
    )
    f.write(
        f"F1: {best_f1_row['f1']:.6f}\n"
    )
    f.write(
        f"Alerts: {int(best_f1_row['alerts'])}\n"
    )
    f.write(
        f"True positives: {int(best_f1_row['true_positives'])}\n"
    )
    f.write(
        f"False positives: {int(best_f1_row['false_positives'])}\n"
    )
    f.write(
        f"False negatives: {int(best_f1_row['false_negatives'])}\n"
    )

    f.write("\nOperational notes:\n")
    f.write(
        "Threshold selected using validation data only.\n"
    )
    f.write(
        "The 2025 test set remains untouched.\n"
    )
    f.write(
        "Final test evaluation must be performed only after "
        "model and threshold are locked.\n"
    )


print("\n========================================")
print("COMPLETE")
print("========================================")

print(
    "Threshold comparison:",
    OUTPUT_THRESHOLD,
)

print(
    "Selected threshold:",
    OUTPUT_INFO,
)

print(
    "Validation predictions:",
    OUTPUT_PREDICTIONS,
)

print("\nSUCCESS: Threshold optimization completed.")