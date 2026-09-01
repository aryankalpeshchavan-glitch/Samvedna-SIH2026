import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix


# ============================================================
# PATHS
# ============================================================

DATA_FILE = r"data\processed\rainfall\ml_training_dataset.csv"
MODEL_DIR = r"models"
MODEL_FILE = os.path.join(MODEL_DIR, "risk_model.pkl")
METADATA_FILE = os.path.join(MODEL_DIR, "model_metadata.json")


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
    "rainfall_3day_lag"
]

TARGET = "risk_label"


# ============================================================
# LOAD DATA
# ============================================================

print("Loading ML training dataset...")

df = pd.read_csv(DATA_FILE)

print("Rows:", len(df))
print("Columns:", list(df.columns))


# ============================================================
# VALIDATION
# ============================================================

print("\nChecking required columns...")

required_columns = FEATURES + [TARGET]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    print("ERROR: Missing columns:")
    print(missing_columns)
    raise SystemExit(1)

print("All required columns found.")


# ============================================================
# PREPARE DATA
# ============================================================

X = df[FEATURES]
y = df[TARGET]

print("\nFeature shape:", X.shape)
print("Target shape:", y.shape)

print("\nRisk distribution:")
print(df["risk_class"].value_counts())


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

print("\nSplitting data...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# ============================================================
# TRAIN RANDOM FOREST
# ============================================================

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

model.fit(X_train, y_train)

print("Training complete.")


# ============================================================
# EVALUATION
# ============================================================

print("\n========== MODEL EVALUATION ==========")

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\nAccuracy:", round(accuracy, 4))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["LOW", "MEDIUM", "HIGH"],
        digits=4
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

print("\n========== FEATURE IMPORTANCE ==========")

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print(importance.to_string(index=False))


# ============================================================
# SAVE MODEL
# ============================================================

os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(model, MODEL_FILE)

print("\nModel saved:")
print(MODEL_FILE)


# ============================================================
# SAVE METADATA
# ============================================================

metadata = {
    "model_type": "RandomForestClassifier",
    "model_version": "v1",
    "training_dataset": DATA_FILE,
    "target": TARGET,
    "features": FEATURES,
    "classes": {
        "0": "LOW",
        "1": "MEDIUM",
        "2": "HIGH"
    },
    "training_rows": int(len(X_train)),
    "testing_rows": int(len(X_test)),
    "accuracy": float(accuracy)
}

with open(METADATA_FILE, "w") as f:
    json.dump(metadata, f, indent=4)

print("Metadata saved:")
print(METADATA_FILE)

print("\n==========================================")
print("DAY 4 - MODEL TRAINING COMPLETE")
print("==========================================")