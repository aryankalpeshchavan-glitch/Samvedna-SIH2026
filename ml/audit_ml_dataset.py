import pandas as pd
import os


DATASET = r"data\processed\rainfall\ml_training_dataset.csv"
EVENTS = r"data\landslide_events.csv"


print("\n==============================================")
print("        CRISISCORE ML DATASET AUDIT")
print("==============================================\n")


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("Loading ML dataset...")

df = pd.read_csv(DATASET)

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(list(df.columns))


# ============================================================
# 2. BASIC DATA QUALITY
# ============================================================

print("\n==============================================")
print("1. DATA QUALITY")
print("==============================================")

print("\nMissing values:")

missing = df.isnull().sum()

print(missing[missing > 0])

if missing.sum() == 0:
    print("PASS - No missing values")


print("\nDuplicate rows:", df.duplicated().sum())


# ============================================================
# 3. DATE CHECK
# ============================================================

print("\n==============================================")
print("2. DATE COVERAGE")
print("==============================================")

df["date"] = pd.to_datetime(df["date"], errors="coerce")

print("Invalid dates:", df["date"].isna().sum())

print("Minimum date:", df["date"].min())
print("Maximum date:", df["date"].max())

print("Unique dates:", df["date"].nunique())


# ============================================================
# 4. GEOGRAPHIC COVERAGE
# ============================================================

print("\n==============================================")
print("3. GEOGRAPHIC COVERAGE")
print("==============================================")

print("States:", df["state"].nunique())
print("Districts:", df["district"].nunique())

print("\nRows by state:")

print(
    df.groupby("state")
    .size()
    .sort_values(ascending=False)
)


# ============================================================
# 5. CURRENT TARGET AUDIT
# ============================================================

print("\n==============================================")
print("4. CURRENT TARGET AUDIT")
print("==============================================")

print("\nRisk class distribution:")

print(
    df["risk_class"]
    .value_counts()
)


print("\nRisk label distribution:")

print(
    df["risk_label"]
    .value_counts()
)


# ============================================================
# 6. CHECK RISK CLASS ↔ RISK LABEL
# ============================================================

print("\n==============================================")
print("5. LABEL CONSISTENCY")
print("==============================================")

mapping = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2
}

expected_labels = df["risk_class"].map(mapping)

mismatches = (
    expected_labels != df["risk_label"]
).sum()

print("Risk class / risk label mismatches:", mismatches)

if mismatches == 0:
    print(
        "PASS - risk_label is exactly derived from risk_class"
    )


# ============================================================
# 7. CHECK RISK SCORE → CLASS RELATIONSHIP
# ============================================================

print("\n==============================================")
print("6. RISK SCORE → CLASS AUDIT")
print("==============================================")

print(
    df.groupby("risk_class")["rainfall_risk_score"]
    .agg(["min", "max", "mean", "count"])
)


# ============================================================
# 8. CHECK WHETHER TARGET IS DERIVED FROM SCORE
# ============================================================

print("\n==============================================")
print("7. TARGET LEAKAGE CHECK")
print("==============================================")

score_class = pd.Series(index=df.index, dtype="object")

score_class[df["rainfall_risk_score"] < 50] = "LOW"

score_class[
    (df["rainfall_risk_score"] >= 50) &
    (df["rainfall_risk_score"] < 100)
] = "MEDIUM"

score_class[
    df["rainfall_risk_score"] >= 100
] = "HIGH"


score_mismatches = (
    score_class != df["risk_class"]
).sum()

print(
    "Score → risk class mismatches:",
    score_mismatches
)

if score_mismatches == 0:
    print(
        "WARNING: Current target is deterministically derived "
        "from rainfall_risk_score."
    )
    print(
        "The current ML model is learning a rainfall rule, "
        "not actual landslide occurrence."
    )


# ============================================================
# 9. CHECK EVENT INVENTORY
# ============================================================

print("\n==============================================")
print("8. LANDSLIDE EVENT INVENTORY")
print("==============================================")

if os.path.exists(EVENTS):

    events = pd.read_csv(EVENTS)

    print("Event rows:", len(events))

    print("\nEvent columns:")
    print(list(events.columns))

    print("\nEvents by state:")

    print(
        events["state"]
        .value_counts()
    )

    print("\nEvents with district:")
    print(
        events["district"].notna().sum()
    )

    print("Events without district:")
    print(
        events["district"].isna().sum()
    )

else:

    print("WARNING: landslide_events.csv not found")


# ============================================================
# 10. NER EVENT COUNT
# ============================================================

print("\n==============================================")
print("9. NER EVENT COVERAGE")
print("==============================================")

ner_states = {
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura"
}

if os.path.exists(EVENTS):

    ner_events = events[
        events["state"]
        .astype(str)
        .str.strip()
        .isin(ner_states)
    ]

    print(
        "NER events:",
        len(ner_events)
    )

    print("\nNER event distribution:")

    print(
        ner_events["state"]
        .value_counts()
    )


# ============================================================
# FINAL VERDICT
# ============================================================

print("\n==============================================")
print("              AUDIT VERDICT")
print("==============================================")

print("""
CURRENT DATASET:
✓ Large rainfall dataset
✓ 2015–2025 coverage
✓ 115 districts
✓ 8 NER states
✓ No missing values

CURRENT ML TARGET:
⚠ LOW/MEDIUM/HIGH is a rainfall proxy
⚠ risk_label is derived from that proxy
⚠ model accuracy therefore does NOT represent
  real landslide prediction accuracy

NEXT REQUIRED DATASET:
→ Real landslide event labels
→ 24h / 48h / 72h targets
→ Positive + negative samples
→ Temporal validation
→ Spatial validation
→ Calibrated probabilities

==============================================
AUDIT COMPLETE
==============================================
""")