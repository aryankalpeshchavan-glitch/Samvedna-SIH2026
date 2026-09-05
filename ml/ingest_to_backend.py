"""
Ingest Krishna ML risk dataset into AJ backend RiskZone API.
Reads data/processed/rainfall/risk_prediction_dataset.csv
and POSTs to /risk for each district/date.
"""
import os, csv, json, sys, time
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dataset = os.path.join(BASE_DIR, "data", "processed", "rainfall", "risk_prediction_dataset.csv")
API = os.getenv("API_URL", "http://localhost:8000")
TOKEN = os.getenv("API_TOKEN", "")

if not os.path.exists(dataset):
    print(f"Dataset not found: {dataset}")
    print("Run ml/create_risk_dataset.py first (requires data/raw/rainfall RF25 files)")
    sys.exit(1)

headers = {"Content-Type": "application/json"}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

# For demo, just create a few RiskZones
with open(dataset) as f:
    reader = csv.DictReader(f)
    rows = list(reader)[:20]
    print(f"Ingesting {len(rows)} rows to {API}/risk ...")
    for r in rows:
        # Use rainfall_24h as proxy for risk_score
        try:
            score = min(0.95, max(0.05, float(r.get("rainfall_24h", 10))/200))
        except:
            score = 0.3
        payload = {
            "lat": 26.14,
            "lng": 91.73,
            "risk_score": score,
            "horizon_hours": 24,
            "top_features": {k: float(r.get(k, 0) or 0) for k in ["rainfall_24h","rainfall_7day","heavy_rain_flag"]},
            "data_label": "synthetic"
        }
        try:
            resp = requests.post(f"{API}/risk", json=payload, headers=headers, timeout=5)
            print(f" -> {r['district']} {r['date']} risk={score:.2f} status={resp.status_code}")
        except Exception as e:
            print(f" -> failed {e}")
        time.sleep(0.1)
print("Done. Check GET /risk")
