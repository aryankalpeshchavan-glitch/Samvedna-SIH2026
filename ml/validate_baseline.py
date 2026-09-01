import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


DATA_FILE = r"data\processed\events\landslide_training_samples.csv"


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


print("\n==============================================")
print(" CRISISCORE - STEP 7 VALIDATION")
print("==============================================")


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

print("\nTotal rows:", len(df))

print(
    "Date range:",
    df["date"].min(),
    "to",
    df["date"].max()
)


# ============================================================
# VALIDATE EACH HORIZON
# ============================================================

for horizon in [24, 48, 72]:

    print("\n==============================================")
    print(f"       {horizon}-HOUR TEMPORAL VALIDATION")
    print("==============================================")


    data = df[
        df["prediction_horizon_hours"] == horizon
    ].copy()


    # --------------------------------------------------------
    # TEMPORAL SPLIT
    #
    # Training: before 2022
    # Testing:  2022 onward
    # --------------------------------------------------------

    train = data[
        data["date"] < "2022-01-01"
    ].copy()


    test = data[
        data["date"] >= "2022-01-01"
    ].copy()


    print("\nTraining rows:", len(train))
    print("Testing rows:", len(test))


    train_positive = int(
        train["target"].sum()
    )

    test_positive = int(
        test["target"].sum()
    )


    print(
        "Training positives:",
        train_positive
    )

    print(
        "Testing positives:",
        test_positive
    )


    # --------------------------------------------------------
    # IMPORTANT SAFETY CHECK
    # --------------------------------------------------------

    if train_positive == 0:

        print(
            "\nWARNING:"
        )

        print(
            "No real landslide events exist in the "
            "training period."
        )

        print(
            "Cannot perform meaningful supervised "
            "landslide validation."
        )

        continue


    if test_positive == 0:

        print(
            "\nWARNING:"
        )

        print(
            "No real landslide events exist in the "
            "testing period."
        )

        print(
            "Accuracy/recall would not represent "
            "real landslide prediction performance."
        )

        continue


    # --------------------------------------------------------
    # LOAD BASELINE MODEL
    # --------------------------------------------------------

    model_file = (
        f"models\\landslide_baseline_{horizon}h.pkl"
    )


    model = joblib.load(
        model_file
    )


    # --------------------------------------------------------
    # PREDICT TEST DATA
    # --------------------------------------------------------

    X_test = test[FEATURES]

    y_test = test["target"]


    predictions = model.predict(
        X_test
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )


    print("\nVALIDATION METRICS")

    print(
        "Accuracy:",
        round(accuracy, 4)
    )

    print(
        "Precision:",
        round(precision, 4)
    )

    print(
        "Recall:",
        round(recall, 4)
    )

    print(
        "F1:",
        round(f1, 4)
    )


    print("\nConfusion Matrix:")

    print(
        confusion_matrix(
            y_test,
            predictions
        )
    )


print("\n==============================================")
print(" STEP 7 VALIDATION COMPLETE")
print("==============================================")