# GSI NER Final Dataset Audit

## Sources
- **NER inventory (v2)**: `data\processed\landslide\gsi_field_validated_inventory_v2.csv` (11023 records, 8 NER states)
- **Rainfall**: `risk_prediction_dataset.csv` (462,070 rows, 2015-01-01 to 2025-12-31)
- **Boundaries**: `india_districts.geojson` (EPSG:4326)

## Record counts
- Total NER records: 11023
- Exact-date events: 1465
- Events inside 2015-2025: 1269

## Temporal classification
- DATE_RANGE: 62
- DESCRIPTIVE: 6887
- EXACT_DATE: 1471
- MONTH_DATE: 474
- NA_OR_EMPTY: 1
- YEAR: 2128
- EXACT_DAY: 1465
- MONTH: 469
- RANGE: 61
- UNKNOWN: 6865
- YEAR: 2163

## Rainfall join-readiness
- State-matched: 1465
- District name-matched: 1246
- Spatially matched: 164
- Joinable (all criteria): 1223
- Unmatched: 55

## ML readiness
- Flag: READY
- Strategy: class_weight=balanced + temporal split
- Leakage: temporal split, no future data in predictors

## Honesty checks
- Event date ONLY assigned when precision == EXACT_DAY
- No fabricated dates, no synthetic positives
