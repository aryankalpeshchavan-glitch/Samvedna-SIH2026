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
# TREE COUNTS
# ============================================================

TREE_COUNTS = [
    25,
    50,
    75,
    100,
    125,
    150,
    200,
    300,
]


# ============================================================
# LOAD DATA
# ============================================================

print("\n[1/7] Loading datasets...")

train = pd.read_csv(TRAIN_FILE)
valid = pd.read_csv(VALID_FILE)

print("Train:", train.shape)
print("Validation:", valid.shape)


# ============================================================
# PREPARE DATA
# ============================================================

print("\n[2/7] Preparing features...")

X_train = train[FEATURES].copy()
y_train = train[TARGET].astype(int)

X_valid = valid[FEATURES].copy()
y_valid = valid[TARGET].astype(int)

X_train = X_train.replace(
    [np.inf, -np.inf],
    np.nan
)

X_valid = X_valid.replace(
    [np.inf, -np.inf],
    np.nan
)


# ============================================================
# IMPUTATION
# ============================================================

print("\n[3/7] Imputing missing values...")

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

positive_count = int(y_train.sum())
negative_count = int((y_train == 0).sum())

scale_pos_weight = (
    negative_count / positive_count
)

print("\nClass weight:")
print(
    round(scale_pos_weight, 2)
)


# ============================================================
# EXPERIMENT
# ============================================================

print("\n[4/7] Running tree-count experiment...")

results = []

models = {}


for trees in TREE_COUNTS:

    print("\n----------------------------------------")
    print(f"Training model with {trees} trees")
    print("----------------------------------------")

    model = XGBClassifier(
        n_estimators=trees,

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
        verbose=False,
    )


    probability = model.predict_proba(
        X_valid
    )[:, 1]


    prediction = (
        probability >= 0.50
    ).astype(int)


    pr_auc = average_precision_score(
        y_valid,
        probability
    )

    roc_auc = roc_auc_score(
        y_valid,
        probability
    )

    precision = precision_score(
        y_valid,
        prediction,
        zero_division=0
    )

    recall = recall_score(
        y_valid,
        prediction,
        zero_division=0
    )

    f1 = f1_score(
        y_valid,
        prediction,
        zero_division=0
    )


    results.append(
        {
            "trees": trees,
            "pr_auc": pr_auc,
            "roc_auc": roc_auc,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    )


    models[trees] = model


    print(
        f"PR-AUC: {pr_auc:.6f}"
    )

    print(
        f"ROC-AUC: {roc_auc:.6f}"
    )

    print(
        f"Precision: {precision:.6f}"
    )

    print(
        f"Recall: {recall:.6f}"
    )

    print(
        f"F1: {f1:.6f}"
    )


# ============================================================
# RESULTS
# ============================================================

print("\n[5/7] Comparing models...")

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "pr_auc",
    ascending=False
)

print("\n========================================")
print("TREE COUNT COMPARISON")
print("========================================")

print(
    results_df.to_string(
        index=False
    )
)


# ============================================================
# SELECT BEST
# ============================================================

best_trees = int(
    results_df.iloc[0]["trees"]
)

best_pr_auc = float(
    results_df.iloc[0]["pr_auc"]
)

best_model = models[best_trees]


print("\n========================================")
print("BEST MODEL")
print("========================================")

print(
    "Best tree count:",
    best_trees
)

print(
    f"Best validation PR-AUC: {best_pr_auc:.6f}"
)


# ============================================================
# SAVE RESULTS
# ============================================================

print("\n[6/7] Saving experiment results...")

RESULT_FILE = (
    OUTPUT_DIR
    / "xgboost_tree_count_comparison.csv"
)

results_df.to_csv(
    RESULT_FILE,
    index=False
)


# Save selected model
MODEL_FILE = (
    OUTPUT_DIR
    / "xgboost_landslide_24h_best_trees.json"
)

best_model.save_model(
    MODEL_FILE
)


# ============================================================
# SAVE BEST MODEL INFO
# ============================================================

INFO_FILE = (
    OUTPUT_DIR
    / "xgboost_best_tree_model_info.txt"
)

with open(
    INFO_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "CrisisCore XGBoost Tree Count Experiment\n"
    )

    f.write(
        "========================================\n"
    )

    f.write(
        f"Best tree count: {best_trees}\n"
    )

    f.write(
        f"Best validation PR-AUC: {best_pr_auc:.6f}\n"
    )


# ============================================================
# FINISH
# ============================================================

print("\n[7/7] Complete.")

print("\nComparison file:")
print(RESULT_FILE)

print("\nBest model:")
print(MODEL_FILE)

print("\nModel information:")
print(INFO_FILE)

print("\nSUCCESS: Tree-count experiment completed.")