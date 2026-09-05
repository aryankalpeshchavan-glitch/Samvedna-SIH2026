def build_features(
    rainfall_24h,
    rainfall_3day,
    rainfall_7day,
    rainfall_14day,
    rainfall_30day,
    rainfall_previous_day=0,
    rainfall_2day_lag=0,
    rainfall_3day_lag=0
):

    # Automatically determine rainfall flags
    heavy_rain_flag = 1 if rainfall_24h >= 50 else 0
    very_heavy_rain_flag = 1 if rainfall_24h >= 100 else 0

    return {
        "rainfall_24h": float(rainfall_24h),
        "rainfall_3day": float(rainfall_3day),
        "rainfall_7day": float(rainfall_7day),
        "rainfall_14day": float(rainfall_14day),
        "rainfall_30day": float(rainfall_30day),

        "heavy_rain_flag": heavy_rain_flag,
        "very_heavy_rain_flag": very_heavy_rain_flag,

        "rainfall_previous_day":
            float(rainfall_previous_day),

        "rainfall_2day_lag":
            float(rainfall_2day_lag),

        "rainfall_3day_lag":
            float(rainfall_3day_lag)
    }