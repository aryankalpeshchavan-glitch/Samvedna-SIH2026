from pathlib import Path

import numpy as np
import pandas as pd

from xgboost import XGBClassifier

from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

TRAIN_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "train.csv"
)

VALID_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml"
    / "splits"
    / "validation.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml"
    / "models"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET = "landslide_24h"


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


# ============================================================
# LOAD DATA
# ============================================================

print("\n[1/9] Loading datasets...")

train = pd.read_csv(TRAIN_FILE)
valid = pd.read_csv(VALID_FILE)

print("Train:", train.shape)
print("Validation:", valid.shape)


# ============================================================
# VALIDATION
# ============================================================

print("\n[2/9] Validating columns...")

required_columns = FEATURES + [TARGET]

for col in required_columns:
    if col not in train.columns:
        raise ValueError(f"Missing training column: {col}")

    if col not in valid.columns:
        raise ValueError(f"Missing validation column: {col}")

print("All required columns present.")


# ============================================================
# PREPARE X / Y
# ============================================================

print("\n[3/9] Preparing features...")

X_train = train[FEATURES].copy()
y_train = train[TARGET].astype(int)

X_valid = valid[FEATURES].copy()
y_valid = valid[TARGET].astype(int)

# Replace infinity
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_valid = X_valid.replace([np.inf, -np.inf], np.nan)

print("Training positives:", int(y_train.sum()))
print("Training negatives:", int((y_train == 0).sum()))

print("Validation positives:", int(y_valid.sum()))
print("Validation negatives:", int((y_valid == 0).sum()))


# ============================================================
# IMPUTATION
# ============================================================

print("\n[4/9] Handling missing values...")

# IMPORTANT:
# Calculate medians ONLY from training data.

train_medians = X_train.median()

X_train = X_train.fillna(train_medians)
X_valid = X_valid.fillna(train_medians)

print(
    "Remaining train missing:",
    int(X_train.isna().sum().sum())
)

print(
    "Remaining validation missing:",
    int(X_valid.isna().sum().sum())
)


# ============================================================
# CLASS WEIGHT
# ============================================================

print("\n[5/9] Calculating class imbalance weight...")

positive_count = int(y_train.sum())
negative_count = int((y_train == 0).sum())

scale_pos_weight = negative_count / positive_count

print(
    "scale_pos_weight:",
    round(scale_pos_weight, 2)
)


# ============================================================
# XGBOOST MODEL
# ============================================================

print("\n[6/9] Training early-stopped XGBoost...")

model = XGBClassifier(
    n_estimators=1000,

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

    eval_set=[
        (X_train, y_train),
        (X_valid, y_valid),
    ],

    verbose=50,
)


# ============================================================
# BEST ITERATION
# ============================================================

print("\n[7/9] Determining best iteration...")

best_iteration = getattr(
    model,
    "best_iteration",
    None
)

best_score = getattr(
    model,
    "best_score",
    None
)

print("Best iteration:", best_iteration)
print("Best validation PR-AUC:", best_score)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

print("\n[8/9] Evaluating validation set...")

valid_probability = model.predict_proba(
    X_valid
)[:, 1]

prediction_05 = (
    valid_probability >= 0.50
).astype(int)


pr_auc = average_precision_score(
    y_valid,
    valid_probability
)

roc_auc = roc_auc_score(
    y_valid,
    valid_probability
)

precision = precision_score(
    y_valid,
    prediction_05,
    zero_division=0
)

recall = recall_score(
    y_valid,
    prediction_05,
    zero_division=0
)

f1 = f1_score(
    y_valid,
    prediction_05,
    zero_division=0
)

cm = confusion_matrix(
    y_valid,
    prediction_05
)


print("\n========================================")
print("EARLY-STOPPED VALIDATION RESULTS")
print("========================================")

print(f"PR-AUC:    {pr_auc:.6f}")
print(f"ROC-AUC:   {roc_auc:.6f}")
print(f"Precision: {precision:.6f}")
print(f"Recall:    {recall:.6f}")
print(f"F1:        {f1:.6f}")

print("\nConfusion Matrix:")
print(cm)


# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

print("\n========================================")
print("THRESHOLD ANALYSIS")
print("========================================")

thresholds = [
    0.001,
    0.002,
    0.005,
    0.01,
    0.02,
    0.03,
    0.05,
    0.075,
    0.10,
    0.15,
    0.20,
    0.30,
    0.40,
    0.50,
]


threshold_results = []


for threshold in thresholds:

    prediction = (
        valid_probability >= threshold
    ).astype(int)

    precision_t = precision_score(
        y_valid,
        prediction,
        zero_division=0
    )

    recall_t = recall_score(
        y_valid,
        prediction,
        zero_division=0
    )

    f1_t = f1_score(
        y_valid,
        prediction,
        zero_division=0
    )

    predicted_alerts = int(
        prediction.sum()
    )

    threshold_results.append(
        {
            "threshold": threshold,
            "precision": precision_t,
            "recall": recall_t,
            "f1": f1_t,
            "predicted_alerts": predicted_alerts,
        }
    )


threshold_df = pd.DataFrame(
    threshold_results
)

print(
    threshold_df.to_string(
        index=False
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n========================================")
print("FEATURE IMPORTANCE")
print("========================================")

importance_df = pd.DataFrame(
    {
        "feature": FEATURES,
        "importance": model.feature_importances_,
    }
).sort_values(
    "importance",
    ascending=False
)

print(
    importance_df.to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n[9/9] Saving model and results...")

MODEL_FILE = (
    OUTPUT_DIR
    / "xgboost_landslide_24h_earlystop.json"
)

model.save_model(MODEL_FILE)


# Validation predictions
prediction_df = valid[
    [
        "date",
        "state",
        "district",
        TARGET,
    ]
].copy()

prediction_df[
    "predicted_probability"
] = valid_probability

prediction_df[
    "prediction_05"
] = prediction_05


PREDICTION_FILE = (
    OUTPUT_DIR
    / "xgboost_earlystop_validation_predictions.csv"
)

prediction_df.to_csv(
    PREDICTION_FILE,
    index=False
)


# Feature importance
IMPORTANCE_FILE = (
    OUTPUT_DIR
    / "xgboost_earlystop_feature_importance.csv"
)

importance_df.to_csv(
    IMPORTANCE_FILE,
    index=False
)


# Threshold results
THRESHOLD_FILE = (
    OUTPUT_DIR
    / "xgboost_earlystop_threshold_analysis.csv"
)

threshold_df.to_csv(
    THRESHOLD_FILE,
    index=False
)


# Model information
MODEL_INFO_FILE = (
    OUTPUT_DIR
    / "xgboost_earlystop_model_info.txt"
)

with open(
    MODEL_INFO_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "CrisisCore XGBoost Landslide 24h Model\n"
    )

    f.write(
        "========================================\n"
    )

    f.write(
        f"Best iteration: {best_iteration}\n"
    )

    f.write(
        f"Best validation PR-AUC: {best_score}\n"
    )

    f.write(
        f"Validation PR-AUC: {pr_auc:.6f}\n"
    )

    f.write(
        f"Validation ROC-AUC: {roc_auc:.6f}\n"
    )

    f.write(
        f"Validation precision @ 0.50: {precision:.6f}\n"
    )

    f.write(
        f"Validation recall @ 0.50: {recall:.6f}\n"
    )

    f.write(
        f"Validation F1 @ 0.50: {f1:.6f}\n"
    )


print("\n========================================")
print("SUCCESS")
print("========================================")

print("\nModel:")
print(MODEL_FILE)

print("\nValidation predictions:")
print(PREDICTION_FILE)

print("\nFeature importance:")
print(IMPORTANCE_FILE)

print("\nThreshold analysis:")
print(THRESHOLD_FILE)

print("\nModel information:")
print(MODEL_INFO_FILE)