"""
CRISISCORE - GSI FIELD-VALIDATED LANDSLIDE INVENTORY EXTRACTION (v2)
====================================================================
Full 904-page extraction using PyMuPDF page.find_tables() (no OCR).

v2 differs from v1 (legacy fixed-offset line parser in
ml/extract_gsi_inventory_v1_legacy_backup.py): it reads table columns via
find_tables(), correctly handling multi-line cells and continuation-table
layouts that caused v1 to leak Slide_No values into the State column.

Outputs:
  data/processed/landslide/gsi_field_validated_inventory_raw.csv  (full raw)
  data/processed/landslide/gsi_field_validated_inventory_v2.csv   (cleaned)
  data/processed/landslide/gsi_ner_inventory_v2.csv              (NER subset)
  data/processed/audit/gsi_full_extraction_audit.json
  data/processed/audit/gsi_full_extraction_audit.md

Conservative cleaning:
  * normalize whitespace and column names
  * convert latitude/longitude to numeric where possible
  * uppercase state names
  * remove ONLY exact duplicate records
  * preserve original History text verbatim
  * preserve source_page for every row
  * invalid/missing coordinates are KEPT (flagged in the audit)
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone

import pymupdf
import pandas as pd

PDF_FILE = r"data\raw\landslide\landslide_report.pdf"
OUTPUT_DIR = r"data\processed\landslide"
AUDIT_DIR = r"data\processed\audit"
RAW_FILE = os.path.join(OUTPUT_DIR, "gsi_field_validated_inventory_raw.csv")
CLEAN_FILE = os.path.join(OUTPUT_DIR, "gsi_field_validated_inventory_v2.csv")
NER_FILE = os.path.join(OUTPUT_DIR, "gsi_ner_inventory_v2.csv")
AUDIT_JSON = os.path.join(AUDIT_DIR, "gsi_full_extraction_audit.json")
AUDIT_MD = os.path.join(AUDIT_DIR, "gsi_full_extraction_audit.md")

EXPECTED_COLUMNS = [
    "sl_no",
    "slide_no",
    "state",
    "district",
    "slide_name",
    "nh_sh_location",
    "latitude",
    "longitude",
    "material",
    "movement_type",
    "history",
]
PAGE_COL = "source_page"
OUTPUT_COLUMNS = EXPECTED_COLUMNS + [PAGE_COL]

NER_STATES = {
    "ARUNACHAL PRADESH", "ASSAM", "MANIPUR", "MEGHALAYA",
    "MIZORAM", "NAGALAND", "SIKKIM", "TRIPURA",
}

def script_hash() -> str:
    """Short SHA-256 of this script for lineage/audit records."""
    try:
        with open(os.path.abspath(__file__), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except OSError:
        return "unknown"


def clean_cell(value):
    """Normalise a table cell: strip, collapse embedded newlines."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip()
    return " ".join(x.strip() for x in text.splitlines() if x.strip())


def is_valid_coordinate_pair(lat, lon):
    """True if lat/lon parse to numbers within geographic bounds.

    (0,0) is treated as invalid - almost certainly missing/placeholder.
    """
    try:
        latf = float(lat)
        lonf = float(lon)
    except (TypeError, ValueError):
        return False
    if not (-90.0 <= latf <= 90.0):
        return False
    if not (-180.0 <= lonf <= 180.0):
        return False
    if latf == 0.0 and lonf == 0.0:
        return False
    return True


def is_header_row(raw_row):
    """True if the row looks like a (repeated) table header."""
    joined = " ".join(str(c).lower() for c in raw_row if c is not None)
    return ("sl.no" in joined and "slide" in joined) or (
        "history" in joined and "latitude" in joined
    )


def extract_page(page, page_no):
    """Extract inventory records from a single PDF page via find_tables.

    Returns (records, skipped) where records is a list of dicts with the
    11 inventory fields plus page_no, and skipped is a list of dicts with
    the reason a raw row was not accepted as a record.

    Rows with sl_no that is not an integer or with empty state are
    considered structurally invalid and are reported in `skipped`.
    Rows with invalid/missing coordinates are KEPT (the audit flags them).
    """
    records = []
    skipped = []
    tables = page.find_tables()
    for table in tables.tables:
        for raw_row in table.extract():
            if is_header_row(raw_row):
                skipped.append({"page": page_no, "reason": "header"})
                continue
            non_empty = [clean_cell(c) for c in raw_row if clean_cell(c)]
            if not non_empty:
                skipped.append({"page": page_no, "reason": "empty_row"})
                continue
            if len(non_empty) == 1 and len(non_empty[0]) > 30:
                skipped.append({"page": page_no, "reason": "title_blob"})
                continue
            cells = [clean_cell(c) for c in raw_row]
            if len(cells) < len(EXPECTED_COLUMNS):
                cells.extend([""] * (len(EXPECTED_COLUMNS) - len(cells)))
            cells = cells[: len(EXPECTED_COLUMNS)]
            record = dict(zip(EXPECTED_COLUMNS, cells))
            if not record["sl_no"].isdigit():
                skipped.append({"page": page_no, "reason": "non_numeric_sl_no"})
                continue
            if not record["state"].strip():
                skipped.append({"page": page_no, "reason": "empty_state"})
                continue
            record[PAGE_COL] = page_no
            records.append(record)
    return records, skipped

def run(args):
    print("=" * 70)
    print("CRISISCORE - GSI INVENTORY EXTRACTION v2 (find_tables)")
    print("=" * 70)
    print("Script hash:", script_hash())

    if not os.path.exists(PDF_FILE):
        raise FileNotFoundError(f"PDF not found: {PDF_FILE}")

    pdf_size = os.path.getsize(PDF_FILE)
    start = time.time()
    doc = pymupdf.open(PDF_FILE)
    n_pages = len(doc)
    print("Total pages:", n_pages)

    if args.pages:
        page_selection = [int(p) for p in args.pages.split(",") if p.strip()]
    elif args.max_pages:
        page_selection = list(range(1, args.max_pages + 1))
    else:
        page_selection = list(range(1, n_pages + 1))
    page_selection = sorted(set(page_selection))
    full_run = len(page_selection) == n_pages

    print(f"Processing {len(page_selection)} pages |",
          "FULL RUN" if full_run else "PARTIAL RUN")

    raw_rows = []
    skipped_log = []
    pages_with_records = Counter()
    pages_no_table = []
    page_errors = []

    for page_no in page_selection:
        page = doc[page_no - 1]
        try:
            records, skipped = extract_page(page, page_no)
        except Exception as exc:  # pragma: no cover - defensive
            page_errors.append({"page": page_no, "error": str(exc)})
            continue
        raw_rows.extend(records)
        skipped_log.extend(skipped)
        if records:
            pages_with_records[page_no] = len(records)
        else:
            pages_no_table.append(page_no)
        if page_no % 50 == 0 or page_no == page_selection[-1]:
            print(f"  processed {page_no} | records so far: {len(raw_rows)}")

    doc.close()

    print("\nRaw records extracted:", len(raw_rows))
    print("Skipped raw rows:", len(skipped_log))
    print("Pages with records:", len(pages_with_records))
    print("Pages with no table rows:", len(pages_no_table))
    print("Page errors:", len(page_errors))

    if not raw_rows:
        raise RuntimeError("No records extracted - check parser.")

    # -----------------------------------------------------------------
    # Build raw dataframe (preserve everything; page column included)
    # -----------------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(AUDIT_DIR, exist_ok=True)
    raw_df = pd.DataFrame(raw_rows)
    raw_df = raw_df[OUTPUT_COLUMNS].copy()
    raw_df.to_csv(RAW_FILE, index=False, encoding="utf-8-sig")
    print("\nRAW saved:", RAW_FILE, "rows:", len(raw_df))

    # -----------------------------------------------------------------
    # Conservative cleaning for the v2 inventory
    # -----------------------------------------------------------------
    clean = raw_df.copy()
    clean["latitude"] = pd.to_numeric(clean["latitude"], errors="coerce")
    clean["longitude"] = pd.to_numeric(clean["longitude"], errors="coerce")
    for col in ["slide_no", "state", "district", "slide_name",
                "nh_sh_location", "material", "movement_type", "history"]:
        clean[col] = clean[col].astype(str).str.strip()
    clean["state"] = clean["state"].str.upper()

    n_before_dedup = len(clean)
    clean = clean.drop_duplicates()
    n_dups = n_before_dedup - len(clean)

    # numeric sl_no for stable sorting
    clean["_sl_no_int"] = pd.to_numeric(clean["sl_no"], errors="coerce")
    clean = clean.sort_values(
        [PAGE_COL, "_sl_no_int"]
    ).drop(columns=["_sl_no_int"]).reset_index(drop=True)

    clean.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
    print("CLEAN saved:", CLEAN_FILE, "rows:", len(clean),
          "| exact dups removed:", n_dups)

    # -----------------------------------------------------------------
    # NER subset
    # -----------------------------------------------------------------
    ner = clean[clean["state"].isin(NER_STATES)].copy()
    ner.to_csv(NER_FILE, index=False, encoding="utf-8-sig")
    print("NER saved:", NER_FILE, "rows:", len(ner))

    audit = build_audit(
        raw_df=raw_df,
        clean=clean,
        ner=ner,
        n_dups=n_dups,
        n_pages=n_pages,
        pdf_size=pdf_size,
        page_selection=page_selection,
        full_run=full_run,
        pages_with_records=pages_with_records,
        pages_no_table=pages_no_table,
        page_errors=page_errors,
        skipped_log=skipped_log,
        start=start,
    )
    write_audit_files(audit)
    print_summary(audit)
    return audit


def coord_flags(df):
    """Return dict of boolean Series for coordinate validation."""
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    lat_missing = pd.isna(lat)
    lon_missing = pd.isna(lon)
    lat_invalid = (~lat_missing) & ~lat.between(-90, 90)
    lon_invalid = (~lon_missing) & ~lon.between(-180, 180)
    out_of_range = lat_invalid | lon_invalid
    valid = (
        (~lat_missing) & (~lon_missing) & (~out_of_range)
        & ~((lat == 0) & (lon == 0))
    )
    return {
        "lat": lat, "lon": lon,
        "lat_missing": lat_missing, "lon_missing": lon_missing,
        "lat_invalid": lat_invalid, "lon_invalid": lon_invalid,
        "out_of_range": out_of_range, "valid": valid,
    }


SLIDE_NO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/\-._]*$")


def classify_history(value):
    """Re-classify a raw History cell (audit only, no date invention)."""
    import gsi_history_classify as hc
    return hc.classify_history(value)[0]


def build_audit(raw_df, clean, ner, n_dups, n_pages, pdf_size,
                page_selection, full_run, pages_with_records,
                pages_no_table, page_errors, skipped_log, start):
    flags = coord_flags(clean)

    states = clean["state"].value_counts().to_dict()
    districts = clean["district"].value_counts().to_dict()

    slide_missing = int((clean["slide_no"].astype(str).str.strip() == "").sum())
    slide_malformed = int(
        (~clean["slide_no"].astype(str).map(
            lambda v: bool(SLIDE_NO_RE.match(v.strip()))
        )).sum()
    )
    slide_dup = int(
        clean["slide_no"][clean["slide_no"].astype(str).str.strip() != ""]
        .duplicated().sum()
    )

    hist_buckets = Counter(
        classify_history(v) if str(v).strip() else "NA_OR_EMPTY"
        for v in clean["history"]
    )

    state_slash = int(clean["state"].astype(str).str.contains("/").sum())
    coord_like_re = re.compile(r"^-?\d+(\.\d+)?([Ee][+-]?\d+)?$")
    district_coord_like = int(
        clean["district"].astype(str).str.strip().map(
            lambda v: bool(coord_like_re.match(v))
        ).sum()
    )
    state_slide_like = int(
        clean["state"].astype(str).str.contains("/", regex=False).sum()
    )
    skipped_reasons = Counter(s["reason"] for s in skipped_log)

    expected_cols_ok = list(clean.columns) == [
        "sl_no", "slide_no", "state", "district", "slide_name",
        "nh_sh_location", "latitude", "longitude", "material",
        "movement_type", "history", "source_page",
    ]
    return {
        "pdf": {
            "path": str(PDF_FILE),
            "size_bytes": pdf_size,
            "page_count": n_pages,
            "pages_processed": len(page_selection),
            "pages_with_records": int(len(pages_with_records)),
            "pages_with_no_detected_table": pages_no_table,
            "pages_with_extraction_errors": page_errors,
        },
        "row_counts": {
            "raw_rows": int(len(raw_df)),
            "cleaned_rows": int(len(clean)),
            "exact_duplicates_removed": int(n_dups),
            "ner_rows": int(len(ner)),
        },
        "geography": {
            "state_count": len(states),
            "district_count": len(districts),
            "rows_per_state": {k: int(v) for k, v in sorted(
                states.items(), key=lambda x: -x[1])},
            "rows_per_district": {k: int(v) for k, v in sorted(
                districts.items(), key=lambda x: -x[1])},
        },
        "coordinates": {
            "valid_coordinates": int(flags["valid"].sum()),
            "missing_latitude": int(flags["lat_missing"].sum()),
            "missing_longitude": int(flags["lon_missing"].sum()),
            "invalid_latitude": int(flags["lat_invalid"].sum()),
            "invalid_longitude": int(flags["lon_invalid"].sum()),
            "out_of_range_coordinates": int(flags["out_of_range"].sum()),
        },
        "identifiers": {
            "missing_slide_no": slide_missing,
            "malformed_slide_no": slide_malformed,
            "duplicate_slide_no": slide_dup,
        },
        "history": {
            "exact_date": int(hist_buckets.get("EXACT_DATE", 0)),
            "month_date": int(hist_buckets.get("MONTH_DATE", 0)),
            "year_only": int(hist_buckets.get("YEAR", 0)),
            "date_range": int(hist_buckets.get("DATE_RANGE", 0)),
            "descriptive": int(hist_buckets.get("DESCRIPTIVE", 0)),
            "na_or_empty": int(hist_buckets.get("NA_OR_EMPTY", 0)),
        },
        "data_integrity": {
            "state_contains_slash": state_slash,
            "state_slide_no_like": state_slide_like,
            "district_coordinate_like": district_coord_like,
            "skipped_rows_by_reason": {k: int(v) for k, v in
                                       skipped_reasons.items()},
            "expected_columns_ok": bool(expected_cols_ok),
        },
        "provenance": {
            "script": "ml/extract_gsi_inventory.py",
            "script_hash": script_hash(),
            "version": "v2-find_tables",
            "full_run": bool(full_run),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "extraction_seconds": round(time.time() - start, 1),
        },
        "coverage_note": (
            "Extracted row count reflects rows physically present in the "
            "PDF and successfully parsed. The BhuSanket portal advertises "
            "~36,072 records; the PDF shown here may be an older snapshot."
        ),
    }


def write_audit_files(audit):
    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    lines = []
    lines.append("# GSI Full-Extraction Audit")
    lines.append("")
    lines.append("## PDF")
    for k, v in audit["pdf"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Row counts")
    for k, v in audit["row_counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Geography")
    lines.append(f"- states: {audit['geography']['state_count']}")
    lines.append(f"- districts: {audit['geography']['district_count']}")
    lines.append("")
    lines.append("## Coordinates")
    for k, v in audit["coordinates"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Identifiers")
    for k, v in audit["identifiers"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## History")
    for k, v in audit["history"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Data integrity")
    for k, v in audit["data_integrity"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Provenance")
    for k, v in audit["provenance"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Coverage note")
    lines.append(audit["coverage_note"])
    with open(AUDIT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def print_summary(audit):
    print("\n" + "=" * 70)
    print("FULL EXTRACTION SUMMARY")
    print("=" * 70)
    for k, v in audit["row_counts"].items():
        print(f"  {k}: {v}")
    print("  states:", audit["geography"]["state_count"])
    print("  districts:", audit["geography"]["district_count"])
    print("  valid coords:", audit["coordinates"]["valid_coordinates"])
    print("  NA/empty history:", audit["history"]["na_or_empty"])
    print("  exact dates:", audit["history"]["exact_date"])
    print("  audit json:", AUDIT_JSON)
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Extract GSI field-validated landslide inventory (v2)."
    )
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Only process the first N pages.")
    parser.add_argument("--pages", type=str, default=None,
                        help="Comma-separated page numbers to process.")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    sys.exit(main())
