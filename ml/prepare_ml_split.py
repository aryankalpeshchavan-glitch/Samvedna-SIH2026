from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "landslide_ml_dataset.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ml"
    / "splits"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


TRAIN_FILE = (
    OUTPUT_DIR
    / "train.csv"
)

VALIDATION_FILE = (
    OUTPUT_DIR
    / "validation.csv"
)

TEST_FILE = (
    OUTPUT_DIR
    / "test.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

TARGET = "landslide_24h"

TRAIN_END = 2022
VALIDATION_END = 2024
TEST_YEAR = 2025


# ============================================================
# LOAD DATA
# ============================================================

print(
    "\n[1/7] Loading ML dataset..."
)

df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["date"]
)

print(
    f"Dataset shape: "
    f"{df.shape}"
)

print(
    f"Date range: "
    f"{df['date'].min().date()} -> "
    f"{df['date'].max().date()}"
)


# ============================================================
# BASIC VALIDATION
# ============================================================

print(
    "\n[2/7] Validating dataset..."
)

required_columns = [
    "date",
    "district_key",
    TARGET,
]

missing_columns = [
    c
    for c in required_columns
    if c not in df.columns
]

if missing_columns:

    raise KeyError(
        f"Missing required columns: "
        f"{missing_columns}"
    )


duplicate_count = (
    df
    .duplicated(
        subset=[
            "date",
            "district_key",
        ]
    )
    .sum()
)

print(
    f"Duplicate date-district rows: "
    f"{duplicate_count}"
)

if duplicate_count > 0:

    raise ValueError(
        "Duplicate date-district "
        "rows detected."
    )


# ============================================================
# CREATE YEAR
# ============================================================

df["year"] = (
    df["date"].dt.year
)


# ============================================================
# CREATE SPLITS
# ============================================================

print(
    "\n[3/7] Creating chronological splits..."
)

train = df[
    df["year"] <= TRAIN_END
].copy()

validation = df[
    (
        df["year"] > TRAIN_END
    )
    &
    (
        df["year"] <= VALIDATION_END
    )
].copy()

test = df[
    df["year"] == TEST_YEAR
].copy()


# ============================================================
# CHECK YEAR RANGES
# ============================================================

print(
    "\nTrain:"
)

print(
    f"Rows: {len(train):,}"
)

print(
    f"Dates: "
    f"{train['date'].min().date()} -> "
    f"{train['date'].max().date()}"
)


print(
    "\nValidation:"
)

print(
    f"Rows: {len(validation):,}"
)

print(
    f"Dates: "
    f"{validation['date'].min().date()} -> "
    f"{validation['date'].max().date()}"
)


print(
    "\nTest:"
)

print(
    f"Rows: {len(test):,}"
)

print(
    f"Dates: "
    f"{test['date'].min().date()} -> "
    f"{test['date'].max().date()}"
)


# ============================================================
# CHECK SPLIT COVERAGE
# ============================================================

print(
    "\n[4/7] Checking district coverage..."
)

train_districts = set(
    train["district_key"]
    .unique()
)

validation_districts = set(
    validation["district_key"]
    .unique()
)

test_districts = set(
    test["district_key"]
    .unique()
)

print(
    f"Train districts: "
    f"{len(train_districts)}"
)

print(
    f"Validation districts: "
    f"{len(validation_districts)}"
)

print(
    f"Test districts: "
    f"{len(test_districts)}"
)

print(
    f"Validation districts "
    f"also in train: "
    f"{len(validation_districts & train_districts)}"
)

print(
    f"Test districts "
    f"also in train: "
    f"{len(test_districts & train_districts)}"
)


# ============================================================
# TARGET DISTRIBUTION FUNCTION
# ============================================================

def print_target_stats(
    name,
    data
):

    positives = int(
        data[TARGET].sum()
    )

    negatives = (
        len(data)
        -
        positives
    )

    rate = (
        positives
        /
        len(data)
        *
        100
    )

    print(
        f"\n{name} target distribution:"
    )

    print(
        f"  Total:     {len(data):,}"
    )

    print(
        f"  Positive:  {positives:,}"
    )

    print(
        f"  Negative:  {negatives:,}"
    )

    print(
        f"  Positive %: {rate:.4f}%"
    )


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print(
    "\n[5/7] Checking target distribution..."
)

print_target_stats(
    "TRAIN",
    train
)

print_target_stats(
    "VALIDATION",
    validation
)

print_target_stats(
    "TEST",
    test
)


# ============================================================
# YEAR-BY-YEAR POSITIVES
# ============================================================

print(
    "\nPositive landslide events by year:"
)

year_stats = (
    df
    .groupby("year")[TARGET]
    .agg(
        total_rows="size",
        positive_events="sum",
    )
)

year_stats[
    "positive_rate_percent"
] = (
    year_stats["positive_events"]
    /
    year_stats["total_rows"]
    *
    100
)

print(
    year_stats.to_string()
)


# ============================================================
# CHECK POSITIVES IN EACH SPLIT
# ============================================================

train_positive = int(
    train[TARGET].sum()
)

validation_positive = int(
    validation[TARGET].sum()
)

test_positive = int(
    test[TARGET].sum()
)

if train_positive == 0:

    raise ValueError(
        "TRAIN contains zero "
        "positive samples."
    )

if validation_positive == 0:

    raise ValueError(
        "VALIDATION contains zero "
        "positive samples."
    )

if test_positive == 0:

    raise ValueError(
        "TEST contains zero "
        "positive samples."
    )


# ============================================================
# REMOVE TEMPORARY YEAR COLUMN
# ============================================================

train = train.drop(
    columns=["year"]
)

validation = validation.drop(
    columns=["year"]
)

test = test.drop(
    columns=["year"]
)


# ============================================================
# SAVE SPLITS
# ============================================================

print(
    "\n[6/7] Saving split files..."
)

train.to_csv(
    TRAIN_FILE,
    index=False
)

validation.to_csv(
    VALIDATION_FILE,
    index=False
)

test.to_csv(
    TEST_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print(
    "\n[7/7] Final split summary"
)

print(
    "\nTRAIN"
)

print(
    f"  File: {TRAIN_FILE}"
)

print(
    f"  Rows: {len(train):,}"
)

print(
    f"  Positives: "
    f"{int(train[TARGET].sum()):,}"
)


print(
    "\nVALIDATION"
)

print(
    f"  File: {VALIDATION_FILE}"
)

print(
    f"  Rows: {len(validation):,}"
)

print(
    f"  Positives: "
    f"{int(validation[TARGET].sum()):,}"
)


print(
    "\nTEST"
)

print(
    f"  File: {TEST_FILE}"
)

print(
    f"  Rows: {len(test):,}"
)

print(
    f"  Positives: "
    f"{int(test[TARGET].sum()):,}"
)


print(
    "\nSUCCESS: Chronological ML "
    "splits created."
)