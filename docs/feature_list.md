# CrisisCore ML Feature List

## Target Variable

### landslide

- 0 = No landslide
- 1 = Landslide

---

## 1. Rainfall Features

### rainfall_24h
Rainfall accumulated during the previous 24 hours.

### rainfall_3day
Cumulative rainfall during the previous 3 days.

### rainfall_7day
Cumulative rainfall during the previous 7 days.

---

## 2. Terrain Features

### slope
Steepness of the terrain in degrees.

### elevation
Height of the location above sea level.

---

## 3. Environmental Features

### soil_moisture
Amount of moisture present in the soil.

---

## 4. Historical Landslide Features

### historical_landslides
Number of previous landslides recorded around the location.

### distance_from_previous_landslide
Distance from the nearest previously recorded landslide.

---

## 5. Geographic Features

### latitude
Latitude of the location.

### longitude
Longitude of the location.

### distance_from_river
Distance from the nearest river.

### distance_from_road
Distance from the nearest road.

---

## 6. Future Features

The following features will be added when verified data is available:

- land_cover
- geology
- rainfall_30day
- population_exposure
- infrastructure_exposure

---

## ML Objective

The model will use environmental, terrain,
rainfall and historical landslide features
to estimate the probability of a landslide.

### Model Output

Landslide probability:

0 to 1

Example:

0.87 = 87% predicted probability