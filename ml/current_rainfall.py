import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DATASET = r"data\processed\rainfall\risk_prediction_dataset.csv"


# ============================================================
# LOAD LATEST RAINFALL
# ============================================================

def get_latest_rainfall(state, district):

    print("Loading rainfall dataset...")

    df = pd.read_csv(DATASET)

    print(f"Rows: {len(df)}")

    # Convert date column
    df["date"] = pd.to_datetime(df["date"])

    # Clean state and district names
    df["state"] = df["state"].astype(str).str.strip()
    df["district"] = df["district"].astype(str).str.strip()

    state_clean = state.strip().upper()
    district_clean = district.strip().lower()

    # Filter requested location
    data = df[
        (df["state"].str.upper() == state_clean) &
        (df["district"].str.lower() == district_clean)
    ].copy()

    if data.empty:
        raise ValueError(
            f"District not found: {state}, {district}"
        )

    # Sort chronologically
    data = data.sort_values("date")

    # Latest available observation
    latest = data.iloc[-1]

    return {
        "state": state,
        "district": district,
        "observation_date": latest["date"].strftime("%Y-%m-%d"),

        "rainfall_24h": float(latest["rainfall_24h"]),
        "rainfall_3day": float(latest["rainfall_3day"]),
        "rainfall_7day": float(latest["rainfall_7day"]),
        "rainfall_14day": float(latest["rainfall_14day"]),
        "rainfall_30day": float(latest["rainfall_30day"]),

        "heavy_rain_flag": int(
            latest["heavy_rain_flag"]
        ),

        "very_heavy_rain_flag": int(
            latest["very_heavy_rain_flag"]
        ),

        "rainfall_previous_day": float(
            latest["rainfall_previous_day"]
        ),

        "rainfall_2day_lag": float(
            latest["rainfall_2day_lag"]
        ),

        "rainfall_3day_lag": float(
            latest["rainfall_3day_lag"]
        )
    }


# ============================================================
# MAIN TEST
# ============================================================

if __name__ == "__main__":

    print("\n==============================================")
    print("        CURRENT RAINFALL INPUT")
    print("==============================================")

    STATE = "ARUNACHAL PRADESH"
    DISTRICT = "Anjaw"

    try:

        result = get_latest_rainfall(
            STATE,
            DISTRICT
        )

        print("\nState:", result["state"])
        print("District:", result["district"])
        print(
            "Observation date:",
            result["observation_date"]
        )

        print("\nRainfall:")
        print(
            "24h:",
            round(result["rainfall_24h"], 4),
            "mm"
        )

        print(
            "3day:",
            round(result["rainfall_3day"], 4),
            "mm"
        )

        print(
            "7day:",
            round(result["rainfall_7day"], 4),
            "mm"
        )

        print(
            "14day:",
            round(result["rainfall_14day"], 4),
            "mm"
        )

        print(
            "30day:",
            round(result["rainfall_30day"], 4),
            "mm"
        )

        print("\nRainfall flags:")
        print(
            "Heavy rain:",
            result["heavy_rain_flag"]
        )

        print(
            "Very heavy rain:",
            result["very_heavy_rain_flag"]
        )

        print("\nLag features:")
        print(
            "Previous day:",
            round(result["rainfall_previous_day"], 4),
            "mm"
        )

        print(
            "2-day lag:",
            round(result["rainfall_2day_lag"], 4),
            "mm"
        )

        print(
            "3-day lag:",
            round(result["rainfall_3day_lag"], 4),
            "mm"
        )

        print("\n==============================================")
        print("CURRENT RAINFALL INPUT READY")
        print("==============================================")

    except Exception as e:

        print("\nERROR:")
        print(str(e))