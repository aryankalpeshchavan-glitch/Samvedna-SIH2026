# CrisisCore

AI-Based Early Warning and Landslide Risk Monitoring System

## Module
Data / ML / SQL

## Day 1 Goal
Build the foundation of the 11-step landslide risk pipeline.

## Current Scope
- Historical landslide data
- Rainfall data
- Database schema
- Feature definition
- Risk probability model

# CrisisCore — Day 2 & Day 3 ML/Data README

## Project
**SIH26001 — AI-Based Early Warning and Landslide Risk Monitoring System in NER**

This README records the completed Data/ML work for **Day 2 and Day 3**, following the project sprint plan.

---

# Day 2 — District-Level Rainfall Aggregation & Risk Dataset Preparation

## Objective
Convert processed rainfall grid data into a **district-level rainfall dataset** for the 8 North-Eastern Region (NER) states and prepare the features required for risk prediction.

## Completed Work

### 1. Rainfall feature dataset
Input:
`data/processed/rainfall/ner_rainfall_features.csv`

Coverage:
- **2015-01-01 to 2025-12-31**
- Daily rainfall
- 24-hour rainfall
- 3-day accumulated rainfall
- 7-day accumulated rainfall

### 2. District boundary data
Boundary file:

`data/raw/boundaries/india_district_imd.geojson`

- **755** district boundary records
- CRS: **EPSG:4326**
- State field: `stname`
- District field: `dtname`

### 3. NER filtering
Filtered to:
1. Arunachal Pradesh
2. Assam
3. Manipur
4. Meghalaya
5. Mizoram
6. Nagaland
7. Sikkim
8. Tripura

Filtered boundary records: **122**

### 4. Spatial assignment
Rainfall grid points were converted to geographic points and assigned to district polygons.

Successfully assigned rainfall records: **1,522,822**

### 5. District-level aggregation
Rainfall was aggregated by:
- Date
- State
- District

Output:

`data/processed/rainfall/ner_district_rainfall.csv`

### Final Day 2 dataset
- **Rows:** 462,070
- **Districts:** 115
- **States:** 8
- **Date range:** 2015-01-01 to 2025-12-31
- **Missing values:** 0

Columns:

```text
date
state
district
rainfall_mm
rainfall_24h
rainfall_3day
rainfall_7day
```

### State-wise district coverage

| State | Districts |
|---|---:|
| Arunachal Pradesh | 25 |
| Assam | 32 |
| Manipur | 13 |
| Meghalaya | 12 |
| Mizoram | 10 |
| Nagaland | 12 |
| Sikkim | 3 |
| Tripura | 8 |
| **Total** | **115** |

### District-name validation
A district-name mismatch was checked for **Dibang Valley**. The boundary dataset contains `Lower Dibang Valley` and `Upper Dibang Valley`, rather than a district named exactly `Dibang Valley`. This was identified during validation.

---

# Day 3 — Risk Prediction Dataset & Initial Risk Labels

## Objective
Prepare a machine-learning-ready dataset from district rainfall data by creating temporal rainfall features and an initial risk target.

## Input

`data/processed/rainfall/ner_district_rainfall.csv`

Input:
- **462,070 rows**
- **115 districts**
- **8 states**

## Features Created

### Rolling rainfall features
- `rainfall_14day`
- `rainfall_30day`

### Heavy rainfall indicators
- `heavy_rain_flag`
- `very_heavy_rain_flag`

### Lag features
- `rainfall_previous_day`
- `rainfall_2day_lag`
- `rainfall_3day_lag`

### Initial risk score
A preliminary:

`rainfall_risk_score`

was calculated from the rainfall-related features.

### Initial risk classification
The score was converted into:
- `LOW`
- `MEDIUM`
- `HIGH`

A numeric `risk_label` was also generated for ML training.

## Output

`data/processed/rainfall/ml_training_dataset.csv`

### Final Day 3 dataset
- **Rows:** 462,070
- **Districts:** 115
- **States:** 8
- **Date range:** 2015-01-01 to 2025-12-31
- **Missing values:** 0

### Risk distribution

| Risk Class | Rows |
|---|---:|
| LOW | 283,208 |
| MEDIUM | 107,132 |
| HIGH | 71,730 |
| **Total** | **462,070** |

## Final columns

```text
date
state
district
rainfall_mm
rainfall_24h
rainfall_3day
rainfall_7day
rainfall_14day
rainfall_30day
heavy_rain_flag
very_heavy_rain_flag
rainfall_previous_day
rainfall_2day_lag
rainfall_3day_lag
rainfall_risk_score
risk_class
risk_label
```

---

# Current Pipeline Status

```text
NetCDF rainfall data
        ↓
NER rainfall extraction
        ↓
Rainfall temporal features
        ↓
District boundary spatial join
        ↓
District-level rainfall aggregation
        ↓
14-day / 30-day features
        ↓
Rainfall flags
        ↓
Lag features
        ↓
Initial rainfall risk score
        ↓
Initial LOW / MEDIUM / HIGH labels
        ↓
ml_training_dataset.csv
```

## Completed

- [x] Rainfall data processing
- [x] NER rainfall feature generation
- [x] District boundary loading
- [x] NER district filtering
- [x] Spatial rainfall-to-district assignment
- [x] District-level daily aggregation
- [x] 14-day and 30-day rainfall features
- [x] Heavy rainfall flags
- [x] Lag features
- [x] Initial rainfall risk score
- [x] Initial LOW/MEDIUM/HIGH labels
- [x] ML training dataset generation
- [x] Missing-value validation
- [x] District/state/date-range validation

## Next ML Stage

The next stage is the **actual risk prediction model**:

1. Train the ML model using `ml_training_dataset.csv`.
2. Evaluate model performance.
3. Calibrate risk probabilities.
4. Generate predicted risk probability and risk class.
5. Prepare prediction output for backend `/risk` API integration.
6. Later integrate the 24-hour rainfall reporting workflow with the backend.

> **Important:** The Day 3 rainfall risk labels are baseline/training targets. They are not yet the final calibrated ML prediction probabilities.

---

# Key Output Files

```text
data/processed/rainfall/
├── ner_rainfall.csv
├── ner_rainfall_features.csv
├── ner_district_rainfall.csv
├── risk_prediction_dataset.csv
└── ml_training_dataset.csv
```

Main file for the next ML stage:

```text
data/processed/rainfall/ml_training_dataset.csv
```

## Validation Result

**462,070 rows × 17 columns**

All 17 columns contain **0 missing values**.

**Day 2 and Day 3 Data/ML preparation is complete.**
