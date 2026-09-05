import sys
import os
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_predictor import RiskPredictor


DATASET = r"data\processed\rainfall\risk_prediction_dataset.csv"


def generate_report(state, district):

    print("\nLoading rainfall dataset...")

    df = pd.read_csv(DATASET)

    # Find requested district
    district_data = df[
        (df["state"].str.upper() == state.upper()) &
        (df["district"].str.lower() == district.lower())
    ].copy()

    if district_data.empty:
        raise ValueError(
            f"District not found: {state}, {district}"
        )

    # Get latest available rainfall observation
    district_data["date"] = pd.to_datetime(
        district_data["date"]
    )

    latest = district_data.sort_values(
        "date"
    ).iloc[-1]

    predictor = RiskPredictor()

    rainfall_data = {

        "rainfall_24h":
            float(latest["rainfall_24h"]),

        "rainfall_3day":
            float(latest["rainfall_3day"]),

        "rainfall_7day":
            float(latest["rainfall_7day"]),

        "rainfall_14day":
            float(latest["rainfall_14day"]),

        "rainfall_30day":
            float(latest["rainfall_30day"]),

        "heavy_rain_flag":
            int(latest["heavy_rain_flag"]),

        "very_heavy_rain_flag":
            int(latest["very_heavy_rain_flag"]),

        "rainfall_previous_day":
            float(latest["rainfall_previous_day"]),

        "rainfall_2day_lag":
            float(latest["rainfall_2day_lag"]),

        "rainfall_3day_lag":
            float(latest["rainfall_3day_lag"])
    }

    result = predictor.predict(rainfall_data)

    # ==============================
    # REPORT
    # ==============================

    report = {

        "report_type":
            "24_HOUR_RISK_REPORT",

        "generated_at":
            datetime.now().isoformat(),

        "state":
            state,

        "district":
            district,

        "observation_date":
            latest["date"].strftime("%Y-%m-%d"),

        "rainfall": {

            "rainfall_24h":
                rainfall_data["rainfall_24h"],

            "rainfall_3day":
                rainfall_data["rainfall_3day"],

            "rainfall_7day":
                rainfall_data["rainfall_7day"],

            "rainfall_14day":
                rainfall_data["rainfall_14day"],

            "rainfall_30day":
                rainfall_data["rainfall_30day"]
        },

        "risk": {

            "risk_class":
                result["risk_class"],

            "risk_score":
                result["risk_score"],

            "risk_probability":
                result["risk_probability"],

            "model_confidence":
                result["confidence"]
        },

        "warning": {

            "early_warning":
                result["early_warning"],

            "warning_level":
                result["warning_level"]
        }
    }

    return report


if __name__ == "__main__":

    import json

    print("\n======================================")
    print("       24-HOUR RISK REPORT")
    print("======================================")

    report = generate_report(
        "ARUNACHAL PRADESH",
        "Anjaw"
    )

    # Create reports directory
    reports_dir = r"data\reports"
    os.makedirs(reports_dir, exist_ok=True)

    # Save JSON report
    output_file = os.path.join(
        reports_dir,
        "anjaw_latest_risk_report.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            report,
            f,
            indent=4
        )

    print("\nState:", report["state"])
    print("District:", report["district"])
    print(
        "Observation date:",
        report["observation_date"]
    )

    print("\nRisk:")
    print(
        "Class:",
        report["risk"]["risk_class"]
    )
    print(
        "Score:",
        report["risk"]["risk_score"],
        "/ 100"
    )
    print(
        "Probability:",
        report["risk"]["risk_probability"],
        "%"
    )
    print(
        "Model confidence:",
        report["risk"]["model_confidence"],
        "%"
    )

    print("\nWarning:")
    print(
        "Early warning:",
        report["warning"]["early_warning"]
    )
    print(
        "Warning level:",
        report["warning"]["warning_level"]
    )

    print("\nReport saved:")
    print(output_file)

    print("\n======================================")
    print("       REPORT GENERATION COMPLETE")
    print("======================================")