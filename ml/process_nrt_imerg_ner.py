from pathlib import Path
import geopandas as gpd
import pandas as pd


# ============================================================
# PATHS
# ============================================================

RAINFALL_FILE = Path(
    r"data\processed\rainfall\nrt\imerg_1day_grid.csv"
)

BOUNDARY_FILE = Path(
    r"data\processed\boundaries\ner_districts.geojson"
)

OUTPUT_DIR = Path(
    r"data\processed\rainfall\nrt"
)


# ============================================================
# SETTINGS
# ============================================================

# We use WGS84 because both the IMERG grid and our boundaries
# are represented in latitude/longitude.
CRS = "EPSG:4326"


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("NRT IMERG → NER DISTRICT RAINFALL AGGREGATION")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Check input files
    # --------------------------------------------------------

    if not RAINFALL_FILE.exists():
        raise FileNotFoundError(
            f"Rainfall file not found:\n{RAINFALL_FILE}"
        )

    if not BOUNDARY_FILE.exists():
        raise FileNotFoundError(
            f"Boundary file not found:\n{BOUNDARY_FILE}"
        )

    # --------------------------------------------------------
    # 2. Load NRT rainfall
    # --------------------------------------------------------

    print("\n[1/7] Loading NRT rainfall grid...")

    rainfall = pd.read_csv(RAINFALL_FILE)

    print(f"Rainfall rows: {len(rainfall):,}")
    print(f"Rainfall columns: {rainfall.columns.tolist()}")

    # Make sure rainfall is numeric
    rainfall["latitude"] = pd.to_numeric(
        rainfall["latitude"],
        errors="coerce"
    )

    rainfall["longitude"] = pd.to_numeric(
        rainfall["longitude"],
        errors="coerce"
    )

    rainfall["rainfall_mm"] = pd.to_numeric(
        rainfall["rainfall_mm"],
        errors="coerce"
    )

    # Remove invalid rows
    rainfall = rainfall.dropna(
        subset=[
            "latitude",
            "longitude",
            "rainfall_mm"
        ]
    ).copy()

    # --------------------------------------------------------
    # 3. Read NER boundaries
    # --------------------------------------------------------

    print("\n[2/7] Loading NER district boundaries...")

    districts = gpd.read_file(
        BOUNDARY_FILE
    )

    print(
        f"NER boundary rows: {len(districts)}"
    )

    print(
        f"Boundary CRS: {districts.crs}"
    )

    # --------------------------------------------------------
    # 4. Restrict global rainfall grid to NER bounding box
    # --------------------------------------------------------

    print(
        "\n[3/7] Restricting rainfall grid to NER region..."
    )

    minx, miny, maxx, maxy = districts.total_bounds

    print(
        f"NER bounding box:"
        f"\n  Longitude: {minx:.4f} to {maxx:.4f}"
        f"\n  Latitude:  {miny:.4f} to {maxy:.4f}"
    )

    rainfall_ner = rainfall[
        (rainfall["longitude"] >= minx) &
        (rainfall["longitude"] <= maxx) &
        (rainfall["latitude"] >= miny) &
        (rainfall["latitude"] <= maxy)
    ].copy()

    print(
        f"Global rainfall rows: {len(rainfall):,}"
    )

    print(
        f"NER bounding-box rows: {len(rainfall_ner):,}"
    )

    # --------------------------------------------------------
    # 5. Convert rainfall points to GeoDataFrame
    # --------------------------------------------------------

    print(
        "\n[4/7] Creating rainfall spatial points..."
    )

    rainfall_gdf = gpd.GeoDataFrame(
        rainfall_ner,
        geometry=gpd.points_from_xy(
            rainfall_ner["longitude"],
            rainfall_ner["latitude"]
        ),
        crs=CRS
    )

    # Ensure boundaries use same CRS
    if districts.crs != CRS:
        districts = districts.to_crs(CRS)

    # --------------------------------------------------------
    # 6. Spatial join: rainfall pixel → district
    # --------------------------------------------------------

    print(
        "\n[5/7] Performing spatial join..."
    )

    # Keep only fields needed for aggregation
    district_fields = [
        "state_name",
        "district",
        "stcode",
        "dtcode",
        "geometry"
    ]

    district_fields = [
        c for c in district_fields
        if c in districts.columns
    ]

    district_layer = districts[
        district_fields
    ].copy()

    joined = gpd.sjoin(
        rainfall_gdf,
        district_layer,
        how="inner",
        predicate="within"
    )

    print(
        f"Rainfall points matched to districts: "
        f"{len(joined):,}"
    )

    # --------------------------------------------------------
    # Check spatial matching
    # --------------------------------------------------------

    if len(joined) == 0:
        raise RuntimeError(
            "No rainfall pixels matched any NER district."
        )

    matched_pixels = joined["index_right"].nunique()

    print(
        f"Districts receiving rainfall pixels: "
        f"{matched_pixels}"
    )

    # --------------------------------------------------------
    # 7. Aggregate rainfall by district
    # --------------------------------------------------------

    print(
        "\n[6/7] Calculating district rainfall statistics..."
    )

    grouped = (
        joined
        .groupby(
            [
                "date",
                "state_name",
                "district",
                "stcode",
                "dtcode"
            ],
            dropna=False
        )
        .agg(
            rainfall_mean_mm=(
                "rainfall_mm",
                "mean"
            ),
            rainfall_max_mm=(
                "rainfall_mm",
                "max"
            ),
            rainfall_p95_mm=(
                "rainfall_mm",
                lambda x: x.quantile(0.95)
            ),
            rainfall_pixels=(
                "rainfall_mm",
                "count"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Round values
    # --------------------------------------------------------

    grouped["rainfall_mean_mm"] = (
        grouped["rainfall_mean_mm"]
        .round(2)
    )

    grouped["rainfall_max_mm"] = (
        grouped["rainfall_max_mm"]
        .round(2)
    )

    grouped["rainfall_p95_mm"] = (
        grouped["rainfall_p95_mm"]
        .round(2)
    )

    # --------------------------------------------------------
    # Rename state column for project consistency
    # --------------------------------------------------------

    grouped = grouped.rename(
        columns={
            "state_name": "state"
        }
    )

    # --------------------------------------------------------
    # Save output
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dates = grouped["date"].dropna().unique()

    if len(dates) == 1:
        output_date = str(dates[0])
    else:
        output_date = "latest"

    output_file = (
        OUTPUT_DIR /
        f"ner_district_rainfall_{output_date}.csv"
    )

    print(
        "\n[7/7] Saving district rainfall layer..."
    )

    grouped.to_csv(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("FINAL VALIDATION")
    print("=" * 70)

    print(
        f"\nOutput file:\n{output_file}"
    )

    print(
        f"\nOutput rows: {len(grouped)}"
    )

    print(
        f"Unique districts represented: "
        f"{grouped['district'].nunique()}"
    )

    print(
        f"Dates: "
        f"{grouped['date'].min()} → "
        f"{grouped['date'].max()}"
    )

    print("\nDistrict count by state:")

    print(
        grouped
        .groupby("state")["district"]
        .nunique()
        .sort_index()
        .to_string()
    )

    print("\nRainfall statistics:")

    print(
        grouped[
            [
                "rainfall_mean_mm",
                "rainfall_max_mm",
                "rainfall_p95_mm"
            ]
        ].describe().round(2).to_string()
    )

    print("\nSample output:")

    print(
        grouped.head(15).to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("NRT DISTRICT RAINFALL AGGREGATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()