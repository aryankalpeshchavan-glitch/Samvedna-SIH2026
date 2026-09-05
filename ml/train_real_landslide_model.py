import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
    brier_score_loss
)

# ============================================================
# CRISISCORE - REAL LANDSLIDE ML TRAINING
# ============================================================

INPUT = "data/processed/ml/real_event_training_dataset_terrain.csv"

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "landslide_calibrated_v1.joblib")
FEATURE_PATH = os.path.join(MODEL_DIR, "feature_schema.json")
METRICS_PATH = os.path.join(MODEL_DIR, "model_metrics.json")

os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 70)
print("CRISISCORE REAL LANDSLIDE ML TRAINING")
print("=" * 70)

# ------------------------------------------------------------
# 1. LOAD DATA
# ------------------------------------------------------------

print("\n[1] Loading dataset...")

df = pd.read_csv(INPUT)

print("Rows:", len(df))
print("Columns:", len(df.columns))

if "landslide_event" not in df.columns:
    raise ValueError("landslide_event column missing")

print("\nLABEL DISTRIBUTION:")
print(df["landslide_event"].value_counts())

# ------------------------------------------------------------
# 2. FEATURES
# ------------------------------------------------------------

features = [
    # Rainfall
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",

    # Rainfall flags
    "heavy_rain_flag",
    "very_heavy_rain_flag",

    # Terrain
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness"
]

missing_features = [c for c in features if c not in df.columns]

if missing_features:
    print("\nMISSING FEATURES:")
    print(missing_features)
    raise ValueError("Required features missing from dataset")

print("\nFEATURES USED:")
for f in features:
    print(" -", f)

# ------------------------------------------------------------
# 3. CLEAN DATA
# ------------------------------------------------------------

print("\n[2] Cleaning data...")

df[features] = df[features].apply(pd.to_numeric, errors="coerce")

before = len(df)

df = df.dropna(subset=features + ["landslide_event"]).copy()

print("Rows before:", before)
print("Rows after :", len(df))
print("Rows removed:", before - len(df))

X = df[features]
y = df["landslide_event"].astype(int)

print("\nFINAL LABEL DISTRIBUTION:")
print(y.value_counts())

# ------------------------------------------------------------
# 4. TRAIN / TEST SPLIT
# ------------------------------------------------------------

print("\n[3] Creating train/test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))

# ------------------------------------------------------------
# 5. BASE MODEL
# ------------------------------------------------------------

print("\n[4] Training Random Forest...")

base_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=12,
    min_samples_leaf=3,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

base_model.fit(X_train, y_train)

print("Random Forest training complete.")

# ------------------------------------------------------------
# 6. RAW MODEL EVALUATION
# ------------------------------------------------------------

print("\n[5] Evaluating raw model...")

raw_pred = base_model.predict(X_test)
raw_prob = base_model.predict_proba(X_test)[:, 1]

raw_metrics = {
    "accuracy": float(accuracy_score(y_test, raw_pred)),
    "precision": float(precision_score(y_test, raw_pred, zero_division=0)),
    "recall": float(recall_score(y_test, raw_pred, zero_division=0)),
    "f1": float(f1_score(y_test, raw_pred, zero_division=0)),
    "roc_auc": float(roc_auc_score(y_test, raw_prob)),
    "pr_auc": float(average_precision_score(y_test, raw_prob)),
    "brier_score": float(brier_score_loss(y_test, raw_prob))
}

print("\nRAW MODEL METRICS")

for k, v in raw_metrics.items():
    print(f"{k:15s}: {v:.4f}")

print("\nCONFUSION MATRIX:")
print(confusion_matrix(y_test, raw_pred))

print("\nCLASSIFICATION REPORT:")
print(classification_report(
    y_test,
    raw_pred,
    target_names=["NO_LANDSLIDE", "LANDSLIDE"],
    zero_division=0
))

# ------------------------------------------------------------
# 7. CALIBRATION
# ------------------------------------------------------------

print("\n[6] Calibrating probability model...")

print("Using sigmoid calibration with 5-fold CV.")

calibrated_model = CalibratedClassifierCV(
    estimator=base_model,
    method="sigmoid",
    cv=5,
    n_jobs=-1
)

calibrated_model.fit(X_train, y_train)

print("Calibration complete.")

# ------------------------------------------------------------
# 8. CALIBRATED EVALUATION
# ------------------------------------------------------------

print("\n[7] Evaluating calibrated model...")

cal_prob = calibrated_model.predict_proba(X_test)[:, 1]
cal_pred = (cal_prob >= 0.50).astype(int)

metrics = {
    "accuracy": float(accuracy_score(y_test, cal_pred)),
    "precision": float(precision_score(y_test, cal_pred, zero_division=0)),
    "recall": float(recall_score(y_test, cal_pred, zero_division=0)),
    "f1": float(f1_score(y_test, cal_pred, zero_division=0)),
    "roc_auc": float(roc_auc_score(y_test, cal_prob)),
    "pr_auc": float(average_precision_score(y_test, cal_prob)),
    "brier_score": float(brier_score_loss(y_test, cal_prob))
}

print("\nCALIBRATED MODEL METRICS")

for k, v in metrics.items():
    print(f"{k:15s}: {v:.4f}")

print("\nCALIBRATED CONFUSION MATRIX:")
print(confusion_matrix(y_test, cal_pred))

print("\nCALIBRATED CLASSIFICATION REPORT:")
print(classification_report(
    y_test,
    cal_pred,
    target_names=["NO_LANDSLIDE", "LANDSLIDE"],
    zero_division=0
))

# ------------------------------------------------------------
# 9. FEATURE IMPORTANCE
# ------------------------------------------------------------

print("\n[8] Feature importance...")

importance = pd.DataFrame({
    "feature": features,
    "importance": base_model.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\nFEATURE IMPORTANCE:")
print(importance.to_string(index=False))

# ------------------------------------------------------------
# 10. RISK THRESHOLDS
# ------------------------------------------------------------

print("\n[9] Risk threshold configuration...")

risk_thresholds = {
    "low_max": 0.30,
    "medium_max": 0.60,
    "high_min": 0.60
}

print("LOW    : probability < 0.30")
print("MEDIUM : 0.30 <= probability < 0.60")
print("HIGH   : probability >= 0.60")

# ------------------------------------------------------------
# 11. SAVE MODEL
# ------------------------------------------------------------

print("\n[10] Saving model...")

joblib.dump(
    calibrated_model,
    MODEL_PATH
)

print("Model saved:")
print(os.path.abspath(MODEL_PATH))

# ------------------------------------------------------------
# 12. SAVE FEATURE SCHEMA
# ------------------------------------------------------------

schema = {
    "model_name": "landslide_calibrated_v1",
    "target": "landslide_event",
    "features": features,
    "risk_thresholds": risk_thresholds,
    "training_rows": int(len(X_train)),
    "testing_rows": int(len(X_test)),
    "dataset_rows": int(len(df)),
    "random_state": 42,
    "calibration_method": "sigmoid",
    "calibration_cv": 5
}

with open(FEATURE_PATH, "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print("Feature schema saved:")
print(os.path.abspath(FEATURE_PATH))

# ------------------------------------------------------------
# 13. SAVE METRICS
# ------------------------------------------------------------

output_metrics = {
    "model": "landslide_calibrated_v1",
    "dataset": INPUT,
    "dataset_rows": int(len(df)),
    "positive_rows": int(y.sum()),
    "negative_rows": int((y == 0).sum()),
    "features": features,
    "raw_model": raw_metrics,
    "calibrated_model": metrics,
    "feature_importance": {
        row["feature"]: float(row["importance"])
        for _, row in importance.iterrows()
    },
    "risk_thresholds": risk_thresholds
}

with open(METRICS_PATH, "w", encoding="utf-8") as f:
    json.dump(output_metrics, f, indent=2)

print("Metrics saved:")
print(os.path.abspath(METRICS_PATH))

# ------------------------------------------------------------
# 14. TEST SAMPLE
# ------------------------------------------------------------

print("\n[11] Testing probability inference...")

sample = X_test.iloc[[0]]

sample_probability = float(
    calibrated_model.predict_proba(sample)[0][1]
)

if sample_probability < 0.30:
    risk = "LOW"
elif sample_probability < 0.60:
    risk = "MEDIUM"
else:
    risk = "HIGH"

print("\nSAMPLE PREDICTION")
print("------------------------------")
print("Probability:", round(sample_probability, 6))
print("Risk level :", risk)
print("------------------------------")

# ------------------------------------------------------------
# COMPLETE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("REAL LANDSLIDE ML MODEL COMPLETE")
print("=" * 70)

print("\nMODEL:")
print(os.path.abspath(MODEL_PATH))

print("\nSCHEMA:")
print(os.path.abspath(FEATURE_PATH))

print("\nMETRICS:")
print(os.path.abspath(METRICS_PATH))

print("\nNext step: connect this model to /risk/current")
print("=" * 70)