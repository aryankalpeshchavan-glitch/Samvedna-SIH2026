"""
CRISISCORE - read-only forensic inspection of existing GSI inventory outputs.

Inspects each inventory CSV individually and reports lineage evidence:
row counts, column names, source-page coverage, Slide_No coverage,
state/district/coordinate integrity, History coverage, and duplicates.

It does NOT write, rename, delete, or modify any file, and it does NOT
touch the rainfall/ML pipeline.
"""
import os
import re

import pandas as pd

FILES = [
    "data/processed/landslide/gsi_field_validated_inventory.csv",
    "data/processed/landslide/gsi_field_validated_inventory_raw.csv",
    "data/processed/landslide/gsi_field_validated_inventory_v1_legacy.csv",
    "data/processed/landslide/gsi_ner_inventory_raw.csv",
    "data/processed/landslide/gsi_ner_inventory_raw_v1_legacy.csv",
]


def coord_unpack(lat, lon):
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None


def coord_valid(lat, lon):
    a, b = coord_unpack(lat, lon)
    if a is None or b is None:
        return False
    if not (-90.0 <= a <= 90.0 and -180.0 <= b <= 180.0):
        return False
    if a == 0.0 and b == 0.0:
        return False
    return True


def looks_like_coordinate(text):
    if not text:
        return False
    return bool(re.fullmatch(r"-?\d+\.?\d*", str(text).strip()))


def main():
    report = {}
    for f in FILES:
        print("=" * 74)
        print("FILE:", f)
        if not os.path.exists(f):
            print("  MISSING FILE")
            report[f] = {"exists": False}
            continue
        size = os.path.getsize(f)
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        n_rows = len(df)
        cols = list(df.columns)
        print("  exists:", True)
        print("  size bytes:", size)
        print("  rows:", n_rows, "| columns:", len(cols))
        for c in cols:
            print("     -", repr(c))

        page_col = None
        for cand in ("_page", "source_page", "page"):
            if cand in cols:
                page_col = cand
                break
        pages = None
        if page_col:
            pages = pd.to_numeric(df[page_col], errors="coerce")
            print("  page column found:", page_col)
            print("  min source page:", pages.min())
            print("  max source page:", pages.max())
            print("  unique pages:", sorted(pages.dropna().unique().astype(int)))
            print("  unique page count:", pages.nunique())
        else:
            print("  page column: NONE (no _page / source_page / page)")

        if "slide_no" in cols:
            print("  unique slide_no:", df["slide_no"].nunique())
            print("  empty slide_no count:",
                  (df["slide_no"].str.strip() == "").sum())
        if "state" in cols:
            print("  unique states:", df["state"].nunique())
            vc = df["state"].value_counts()
            print("  rows per state:")
            for s, c in vc.items():
                print("     {:6d}  {}".format(int(c), s))
        if "district" in cols:
            print("  unique districts:", df["district"].nunique())
        if {"latitude", "longitude"}.issubset(set(cols)):
            valid = sum(1 for _, r in df.iterrows()
                        if coord_valid(r["latitude"], r["longitude"]))
            print("  valid coordinate rows:", valid)
            print("  invalid/missing coordinate rows:", n_rows - valid)

        if "state" in cols:
            withslash = df["state"].str.contains("/", regex=False).sum()
            print("  rows where state contains '/':", int(withslash))
        if "district" in cols:
            coord_like = sum(1 for _, r in df.iterrows()
                             if looks_like_coordinate(r["district"]))
            print("  rows where district looks like a coordinate:", coord_like)
        if "history" in cols:
            hist = df["history"].str.strip()
            empty_hist = (hist == "").sum()
            na_hist = hist.str.upper().isin({"NA", "N/A", "NIL", "-", "--"}).sum()
            print("  rows with non-empty History:", int(n_rows - empty_hist))
            print("  rows with empty History:", int(empty_hist))
            print("  rows with NA/NIL History:", int(na_hist))

        dup = df.duplicated().sum()
        print("  exact duplicate rows (all cols):", int(dup))

        info = {
            "exists": True,
            "size_bytes": size,
            "rows": n_rows,
            "columns": cols,
            "page_column": page_col,
            "min_page": int(pages.min()) if pages is not None and len(pages) else None,
            "max_page": int(pages.max()) if pages is not None and len(pages) else None,
            "n_unique_pages": int(pages.nunique()) if pages is not None else None,
            "duplicate_rows": int(dup),
        }
        report[f] = info
        print()

    print("=" * 74)
    print("LINEAGE SUMMARY (evidence-based)")
    print("=" * 74)
    for f, info in report.items():
        if not info["exists"]:
            continue
        print(f)
        print("   rows={} cols={} page_col={} pages={}-{} unique_pages={}".format(
            info["rows"], len(info["columns"]), info["page_column"],
            info["min_page"], info["max_page"], info["n_unique_pages"]))

    print("\n--- Interpretation (driven by numbers, not names) ---")
    for f, i in report.items():
        if not i["exists"]:
            print("  - MISSING:", f)
            continue
        if i["page_column"] is None:
            print("  - {} : NO page column -> OLD fixed-line parser (v1)".format(f))
        elif i["n_unique_pages"] == 904:
            print("  - {} : 904 unique pages -> FULL 904-page extraction".format(f))
        elif i["n_unique_pages"]:
            print("  - {} : {} unique pages ({}..{}) -> PARTIAL/SAMPLE".format(
                f, i["n_unique_pages"], i["min_page"], i["max_page"]))
        else:
            print("  - {} : page column present but unparseable".format(f))


if __name__ == "__main__":
    main()
    print("\nINSPECTION COMPLETE - NO FILES MODIFIED")