# CrisisCore Data Sources

## ML Feature → Data Source Plan

| Feature | Data Required | Source Type | Status |
|---|---|---|---|
| rainfall_24h | 24-hour rainfall | Weather data | To collect |
| rainfall_3day | 3-day cumulative rainfall | Weather data | To collect |
| rainfall_7day | 7-day cumulative rainfall | Weather data | To collect |
| slope | Terrain slope | DEM/GIS | To derive |
| elevation | Elevation above sea level | DEM/GIS | To collect |
| soil_moisture | Soil moisture | Satellite/weather | To collect |
| distance_from_river | Distance to nearest river | GIS | To derive |
| distance_from_road | Distance to nearest road | GIS | To derive |
| land_surface_temperature | LST | Satellite | To collect |
| built_up_area | Built-up percentage | Satellite/GIS | To derive |
| historical_landslide_count | Previous landslides | Landslide inventory | To calculate |
| landslide | Landslide occurred or not | Landslide inventory | Target |

## Important Rule

No missing value will be replaced with an invented value.

If a feature is unavailable for an event, it will initially remain NULL.

## ML Target

landslide:

0 = No landslide

1 = Landslide
