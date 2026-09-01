import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_predictor import RiskPredictor


predictor = RiskPredictor()


print("\n======================================")
print("       CURRENT RAINFALL RISK TEST")
print("======================================")

state = input("Enter state: ").strip()
district = input("Enter district: ").strip()

print("\nEnter CURRENT rainfall values:")

rainfall_24h = float(input("Rainfall 24h (mm): "))
rainfall_3day = float(input("Rainfall 3day (mm): "))
rainfall_7day = float(input("Rainfall 7day (mm): "))
rainfall_14day = float(input("Rainfall 14day (mm): "))
rainfall_30day = float(input("Rainfall 30day (mm): "))

heavy_rain_flag = int(
    input("Heavy rain flag (0/1): ")
)

very_heavy_rain_flag = int(
    input("Very heavy rain flag (0/1): ")
)

rainfall_previous_day = float(
    input("Previous day rainfall (mm): ")
)

rainfall_2day_lag = float(
    input("2-day lag rainfall (mm): ")
)

rainfall_3day_lag = float(
    input("3-day lag rainfall (mm): ")
)


rainfall_data = {

    "rainfall_24h": rainfall_24h,
    "rainfall_3day": rainfall_3day,
    "rainfall_7day": rainfall_7day,
    "rainfall_14day": rainfall_14day,
    "rainfall_30day": rainfall_30day,

    "heavy_rain_flag": heavy_rain_flag,
    "very_heavy_rain_flag": very_heavy_rain_flag,

    "rainfall_previous_day":
        rainfall_previous_day,

    "rainfall_2day_lag":
        rainfall_2day_lag,

    "rainfall_3day_lag":
        rainfall_3day_lag
}


result = predictor.predict(rainfall_data)


print("\n======================================")
print("           EARLY WARNING")
print("======================================")

print("State:", state)
print("District:", district)

print("\nRisk class:")
print(result["risk_class"])

print(
    "Risk score:",
    result["risk_score"],
    "/ 100"
)

print(
    "Risk probability:",
    result["risk_probability"],
    "%"
)

print(
    "Model confidence:",
    result["confidence"],
    "%"
)

print(
    "Early warning:",
    result["early_warning"]
)

print(
    "Warning level:",
    result["warning_level"]
)

print("\n======================================")