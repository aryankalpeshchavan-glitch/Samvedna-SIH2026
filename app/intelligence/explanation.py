"""
Day 4 — Driver Explanation Layer
==================================
Maps raw ML driver key names to human-readable labels and descriptions.

These labels are static mappings — the ML team owns the driver names.
The backend translates them for the frontend. No causality is claimed
beyond what the model explicitly produces.

Supports real model attributions via get_model_attributions() which
extracts actual feature importances from the prediction service.
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
    "rainfall_14day": {
        "label": "14-day Cumulative Rainfall",
        "description": "Extended rainfall accumulation increases deep soil saturation and slope instability.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_30day": {
        "label": "30-day Cumulative Rainfall",
        "description": "Long-term rainfall accumulation saturates deep soil layers and groundwater.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_mm": {
        "label": "Daily Rainfall",
        "description": "Current daily rainfall measurement.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_previous_day": {
        "label": "Previous Day Rainfall",
        "description": "Rainfall from the previous day, indicating antecedent moisture conditions.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_2day_lag": {
        "label": "2-Day Lag Rainfall",
        "description": "Rainfall from 2 days ago, contributing to cumulative soil saturation.",
        "unit": "mm",
        "category": "hydrology",
    },
    "rainfall_3day_lag": {
        "label": "3-Day Lag Rainfall",
        "description": "Rainfall from 3 days ago, part of the antecedent moisture history.",
        "unit": "mm",
        "category": "hydrology",
    },
    "heavy_rain_flag": {
        "label": "Heavy Rain Flag",
        "description": "Binary indicator: 24h rainfall exceeded 64.5mm (heavy rain threshold).",
        "unit": "flag",
        "category": "hydrology",
    },
    "very_heavy_rain_flag": {
        "label": "Very Heavy Rain Flag",
        "description": "Binary indicator: 24h rainfall exceeded 115.6mm (very heavy rain threshold).",
        "unit": "flag",
        "category": "hydrology",
    },
    "slope": {
        "label": "Terrain Slope",
        "description": "Steeper slopes have higher susceptibility to landslide events.",
        "unit": "degrees",
        "category": "terrain",
    },
    "slope_deg": {
        "label": "Terrain Slope",
        "description": "Steeper slopes have higher susceptibility to landslide events.",
        "unit": "degrees",
        "category": "terrain",
    },
    "slope_mean_deg": {
        "label": "Mean Terrain Slope",
        "description": "Average slope gradient across the district; steeper slopes accelerate debris flows.",
        "unit": "degrees",
        "category": "terrain",
    },
    "slope_max_deg": {
        "label": "Maximum Terrain Slope",
        "description": "Peak steepness gradient indicating presence of high-risk escarpments.",
        "unit": "degrees",
        "category": "terrain",
    },
    "slope_std_deg": {
        "label": "Slope Gradient Variation",
        "description": "Variability in terrain slope reflecting complex undulating geography.",
        "unit": "degrees",
        "category": "terrain",
    },
    "elevation": {
        "label": "Elevation",
        "description": "Elevation influences runoff dynamics and exposure to altitude-related hazards.",
        "unit": "m",
        "category": "terrain",
    },
    "elevation_m": {
        "label": "Elevation",
        "description": "Elevation influences runoff dynamics and exposure to altitude-related hazards.",
        "unit": "m",
        "category": "terrain",
    },
    "elevation_mean_m": {
        "label": "Mean District Elevation",
        "description": "Average altitude influencing precipitation orographic effects.",
        "unit": "m",
        "category": "terrain",
    },
    "elevation_min_m": {
        "label": "Minimum District Elevation",
        "description": "Valley bottom altitude indicating runoff collection zones.",
        "unit": "m",
        "category": "terrain",
    },
    "elevation_max_m": {
        "label": "Peak District Elevation",
        "description": "Highest mountain ridge altitude in district.",
        "unit": "m",
        "category": "terrain",
    },
    "elevation_std_m": {
        "label": "Elevation Relief Variation",
        "description": "Topographical relief indicating vertical potential energy for mass movements.",
        "unit": "m",
        "category": "terrain",
    },
    "aspect": {
        "label": "Slope Aspect",
        "description": "The direction a slope faces affects drainage, moisture retention, and risk.",
        "unit": "degrees",
        "category": "terrain",
    },
    "aspect_deg": {
        "label": "Slope Aspect",
        "description": "The direction a slope faces affects drainage, moisture retention, and risk.",
        "unit": "degrees",
        "category": "terrain",
    },
    "terrain_roughness": {
        "label": "Terrain Roughness",
        "description": "Higher roughness indicates irregular terrain prone to material accumulation.",
        "unit": "index",
        "category": "terrain",
    },
    "soil_moisture": {
        "label": "Soil Moisture",
        "description": "High soil moisture reduces the friction holding material on slopes.",
        "unit": "fraction",
        "category": "soil",
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


def get_model_attributions(
    feature_values: Optional[dict] = None,
) -> Optional[dict[str, float]]:
    """
    Retrieve actual model feature importances from the prediction service.
    Returns the attribution weights dict or None if unavailable.
    These represent the real model drivers, not manually selected fields.
    """
    try:
        from app.services.prediction_service import prediction_service
        if prediction_service.is_available and prediction_service._feature_importances:
            return prediction_service._feature_importances
    except (ImportError, AttributeError):
        pass
    return None


def explain_drivers(
    drivers: list[str],
    feature_values: Optional[dict] = None,
    attributions: Optional[dict[str, float]] = None,
) -> list[dict]:
    """
    Returns human-readable explanations for the provided driver keys.
    Unknown drivers are returned with a safe generic label.
    
    When attributions are provided (actual model feature importances),
    the explanation includes the model's attribution weight for each driver,
    ensuring top_features reflect real model behavior, not just raw values.
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
        if attributions and key in attributions:
            entry["attribution"] = round(attributions[key], 4)
        result.append(entry)
    return result
