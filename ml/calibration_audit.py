import pandas as pd


DATA_FILE = r"data\processed\events\landslide_training_samples.csv"


print("\n==============================================")
print(" CRISISCORE - STEP 8 CALIBRATION AUDIT")
print("==============================================")


df = pd.read_csv(DATA_FILE)


for horizon in [24, 48, 72]:

    data = df[
        df["prediction_horizon_hours"] == horizon
    ]

    positives = int(data["target"].sum())
    negatives = int((data["target"] == 0).sum())

    print("\n==============================================")
    print(f"          {horizon}-HOUR CALIBRATION")
    print("==============================================")

    print("Total samples:", len(data))
    print("Positive samples:", positives)
    print("Negative samples:", negatives)

    if positives < 20:

        print("\nSTATUS: NOT READY")

        print(
            "Insufficient positive events for reliable "
            "probability calibration."
        )

    else:

        print("\nSTATUS: READY FOR CALIBRATION")


print("\n==============================================")
print("             AUDIT CONCLUSION")
print("==============================================")

print("""
Probability calibration is NOT performed yet.

Reason:
The real landslide event inventory contains
insufficient precisely dated positive events.

Calibration will be performed after additional
real event data is available.
""")

print("==============================================")
print("       STEP 8 CALIBRATION AUDIT COMPLETE")
print("==============================================")