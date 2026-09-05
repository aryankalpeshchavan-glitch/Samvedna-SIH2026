import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from risk_predictor import RiskPredictor


predictor = RiskPredictor()


low_rainfall = {
    "rainfall_24h": 2,
    "rainfall_3day": 5,
    "rainfall_7day": 10,
    "rainfall_14day": 15,
    "rainfall_30day": 25,
    "heavy_rain_flag": 0,
    "very_heavy_rain_flag": 0,
    "rainfall_previous_day": 2,
    "rainfall_2day_lag": 1,
    "rainfall_3day_lag": 0
}


medium_rainfall = {
    "rainfall_24h": 20,
    "rainfall_3day": 50,
    "rainfall_7day": 80,
    "rainfall_14day": 120,
    "rainfall_30day": 200,
    "heavy_rain_flag": 1,
    "very_heavy_rain_flag": 0,
    "rainfall_previous_day": 18,
    "rainfall_2day_lag": 15,
    "rainfall_3day_lag": 12
}


high_rainfall = {
    "rainfall_24h": 120,
    "rainfall_3day": 300,
    "rainfall_7day": 500,
    "rainfall_14day": 700,
    "rainfall_30day": 1000,
    "heavy_rain_flag": 1,
    "very_heavy_rain_flag": 1,
    "rainfall_previous_day": 110,
    "rainfall_2day_lag": 100,
    "rainfall_3day_lag": 90
}


tests = {
    "LOW RAINFALL": low_rainfall,
    "MEDIUM RAINFALL": medium_rainfall,
    "HIGH RAINFALL": high_rainfall
}


print("\n========== RISK PREDICTOR TEST ==========")


for name, data in tests.items():

    print("\nScenario:", name)

    result = predictor.predict(data)

    print("Risk class:", result["risk_class"])
    print("Risk score:", result["risk_score"], "/ 100")
    print("Risk probability:", result["risk_probability"], "%")
    print("Model confidence:", result["confidence"], "%")

    print("Early warning:", result["early_warning"])
    print("Warning level:", result["warning_level"])

    print("LOW probability:",
          result["probabilities"]["LOW"], "%")

    print("MEDIUM probability:",
          result["probabilities"]["MEDIUM"], "%")

    print("HIGH probability:",
          result["probabilities"]["HIGH"], "%")

    print("Rainfall risk score:",
          result["rainfall_risk_score"])

    print("Model:",
          result["model_type"],
          result["model_version"])

    print("-" * 50)


print("\n========== TEST COMPLETE ==========")