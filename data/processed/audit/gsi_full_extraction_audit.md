# GSI Full-Extraction Audit

## PDF
- path: data\raw\landslide\landslide_report.pdf
- size_bytes: 315565262
- page_count: 904
- pages_processed: 904
- pages_with_records: 904
- pages_with_no_detected_table: []
- pages_with_extraction_errors: []

## Row counts
- raw_rows: 36071
- cleaned_rows: 36071
- exact_duplicates_removed: 0
- ner_rows: 11023

## Geography
- states: 23
- districts: 284

## Coordinates
- valid_coordinates: 36070
- missing_latitude: 0
- missing_longitude: 1
- invalid_latitude: 0
- invalid_longitude: 0
- out_of_range_coordinates: 0

## Identifiers
- missing_slide_no: 4
- malformed_slide_no: 904
- duplicate_slide_no: 350

## History
- exact_date: 4930
- month_date: 1157
- year_only: 6950
- date_range: 486
- descriptive: 150
- na_or_empty: 22398

## Data integrity
- state_contains_slash: 0
- state_slide_no_like: 0
- district_coordinate_like: 0
- skipped_rows_by_reason: {'title_blob': 1, 'header': 904}
- expected_columns_ok: True

## Provenance
- script: ml/extract_gsi_inventory.py
- script_hash: c1420aeeaac4
- version: v2-find_tables
- full_run: True
- timestamp_utc: 2026-08-31T20:14:19.241374+00:00
- extraction_seconds: 188.1

## Coverage note
Extracted row count reflects rows physically present in the PDF and successfully parsed. The BhuSanket portal advertises ~36,072 records; the PDF shown here may be an older snapshot.