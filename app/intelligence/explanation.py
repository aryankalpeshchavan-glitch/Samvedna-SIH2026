"""
Day 4 — Driver Explanation Layer
===================================
Maps raw ML driver key names to human-readable labels and descriptions.

These labels are static mappings — the ML team owns the driver names.
The backend translates them for the frontend. No causality is claimed
beyond what the model explicitly produces.
"""
from typing import Optional

DRIVER_LABELS: dict[str, dict] = {
    "rainfall_24h": {
        "label": "24-hour Rainfall",
        "description": "High rainfall in the last 24 hours significantly increases landslide and flood risk.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_7day": {
        "label": "7-day Cumulative Rainfall",
        "description": "High cumulative rainfall over the last 7 days saturates soil and raises risk.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_3day": {
        "label": "3-day Cumulative Rainfall",
        "description": "Elevated rainfall over the last 3 days contributes to soil saturation.",
        "unit": "mm",
        "category": "hydrology",
    },
    "slope": {
        "label": "Terrain Slope",
        "description": "Steeper slopes have higher susceptibility to landslide events.",
        "unit": "degrees",
        "category": "terrain",
    },
    "soil_moisture": {
        "label": "Soil Moisture",
        "description": "High soil moisture reduces the friction holding material on slopes.",
        "unit": "fraction",
        "category": "soil",
    },
    "elevation": {
        "label": "Elevation",
        "description": "Elevation influences runoff dynamics and exposure to altitude-related hazards.",
        "unit": "m",
        "category": "terrain",
    },
    "aspect": {
        "label": "Slope Aspect",
        "description": "The direction a slope faces affects drainage, moisture retention, and risk.",
        "unit": "degrees",
        "category": "terrain",
    },
    "ndvi": {
        "label": "Vegetation Cover (NDVI)",
        "description": "Low vegetation density reduces ground anchoring and increases erosion risk.",
        "unit": "index",
        "category": "land_cover",
    },
    "soil_type": {
        "label": "Soil Type",
        "description": "Certain soil types (e.g. expansive clays) are more prone to failure under saturation.",
        "unit": "class",
        "category": "soil",
    },
    "distance_to_stream": {
        "label": "Distance to Stream",
        "description": "Proximity to streams increases flood and debris flow exposure.",
        "unit": "m",
        "category": "hydrology",
    },
    "historical_landslides": {
        "label": "Historical Landslide Frequency",
        "description": "Areas with prior landslide events have higher susceptibility.",
        "unit": "count",
        "category": "historical",
    },
}


def explain_drivers(
    drivers: list[str],
    feature_values: Optional[dict] = None,
) -> list[dict]:
    """
    Returns human-readable explanations for the provided driver keys.
    Unknown drivers are returned with a safe generic label.
    """
    result = []
    for key in drivers:
        meta = DRIVER_LABELS.get(key)
        if meta:
            entry = {
                "key": key,
                "label": meta["label"],
                "description": meta["description"],
                "unit": meta.get("unit"),
                "category": meta.get("category"),
            }
        else:
            # Safe fallback — never crash on unknown driver
            entry = {
                "key": key,
                "label": key.replace("_", " ").title(),
                "description": f"Model driver: {key}",
                "unit": None,
                "category": "other",
            }
        if feature_values and key in feature_values:
            entry["value"] = feature_values[key]
        result.append(entry)
    return result
