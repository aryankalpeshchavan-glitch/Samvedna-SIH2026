from pathlib import Path
import geopandas as gpd


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT = Path(
    r"data\raw\boundaries\gsi_districts\district_nwic.GeoJSON"
)

OUTPUT_DIR = Path(
    r"data\processed\boundaries"
)

OUTPUT = OUTPUT_DIR / "ner_districts.geojson"


# ---------------------------------------------------------
# NORTH EASTERN REGION STATES
# ---------------------------------------------------------

NER_STATES = {
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
}


# ---------------------------------------------------------
# NORMALIZE STATE NAMES
# ---------------------------------------------------------

def normalize_state(value):
    """
    Normalize state names so that minor formatting differences
    do not prevent matching.

    The GSI/NWIC dataset contains:
        Arunanchal Pradesh

    while the correct project name is:
        Arunachal Pradesh
    """

    if value is None:
        return ""

    value = " ".join(
        str(value).strip().upper().split()
    )

    # Dataset typo
    if value == "ARUNANCHAL PRADESH":
        return "ARUNACHAL PRADESH"

    return value


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("NER DISTRICT BOUNDARY PREPARATION")
    print("=" * 60)

    # -----------------------------------------------------
    # Check input
    # -----------------------------------------------------

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Boundary file not found:\n{INPUT}"
        )

    print("\nLoading district boundaries...")
    print(f"Input: {INPUT}")

    # -----------------------------------------------------
    # Read GeoJSON
    # -----------------------------------------------------

    gdf = gpd.read_file(INPUT)

    print(f"\nTotal districts: {len(gdf)}")
    print(f"Original CRS: {gdf.crs}")

    print("\nAvailable columns:")
    print(gdf.columns.tolist())

    # -----------------------------------------------------
    # Normalize state names
    # -----------------------------------------------------

    gdf["state_clean"] = (
        gdf["state_name"]
        .apply(normalize_state)
    )

    ner_states_clean = {
        normalize_state(state)
        for state in NER_STATES
    }

    # -----------------------------------------------------
    # Filter NER
    # -----------------------------------------------------

    ner = gdf[
        gdf["state_clean"].isin(ner_states_clean)
    ].copy()

    print(
        f"\nNER districts found: {len(ner)}"
    )

    # -----------------------------------------------------
    # District count by state
    # -----------------------------------------------------

    print("\nDistrict count by state:")

    state_counts = (
        ner.groupby("state_clean")
        .size()
        .sort_index()
    )

    print(state_counts.to_string())

    # -----------------------------------------------------
    # Check all 8 NER states
    # -----------------------------------------------------

    found_states = set(
        ner["state_clean"].unique()
    )

    missing_states = (
        ner_states_clean - found_states
    )

    print("\nNER state validation:")

    if missing_states:
        print("WARNING - Missing states:")
        for state in sorted(missing_states):
            print(f"  ❌ {state}")
    else:
        print("✅ All 8 NER states found.")

    # -----------------------------------------------------
    # Check geometries
    # -----------------------------------------------------

    print("\nGeometry validation:")

    missing_geometry = ner.geometry.isna().sum()
    empty_geometry = ner.geometry.is_empty.sum()

    print(
        f"Missing geometries: {missing_geometry}"
    )

    print(
        f"Empty geometries: {empty_geometry}"
    )

    # -----------------------------------------------------
    # Fix invalid geometries if necessary
    # -----------------------------------------------------

    invalid_count = (
        (~ner.geometry.is_valid).sum()
    )

    print(
        f"Invalid geometries: {invalid_count}"
    )

    if invalid_count > 0:
        print(
            "Fixing invalid geometries..."
        )

        try:
            ner["geometry"] = (
                ner.geometry.make_valid()
            )
        except AttributeError:
            # Compatibility fallback
            ner["geometry"] = (
                ner.geometry.buffer(0)
            )

        print("✅ Geometry repair completed.")

    # -----------------------------------------------------
    # Convert CRS to WGS84
    # -----------------------------------------------------

    print(
        "\nConverting CRS to EPSG:4326..."
    )

    ner = ner.to_crs("EPSG:4326")

    print(
        f"Final CRS: {ner.crs}"
    )

    # -----------------------------------------------------
    # Keep useful columns only
    # -----------------------------------------------------

    keep_columns = [
        "id",
        "objectid",
        "state",
        "stcode",
        "district",
        "dtcode",
        "state_name",
        "src_agency",
        "geometry",
    ]

    # Only keep columns that actually exist
    keep_columns = [
        col for col in keep_columns
        if col in ner.columns
    ]

    ner = ner[keep_columns]

    # -----------------------------------------------------
    # Create output directory
    # -----------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Save GeoJSON
    # -----------------------------------------------------

    print(
        "\nSaving NER boundary layer..."
    )

    ner.to_file(
        OUTPUT,
        driver="GeoJSON"
    )

    print(
        f"Saved: {OUTPUT}"
    )

    # -----------------------------------------------------
    # Final verification
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("FINAL VALIDATION")
    print("=" * 60)

    print(
        f"Final rows: {len(ner)}"
    )

    print(
        f"Final CRS: {ner.crs}"
    )

    print("\nFinal NER states:")

    final_states = sorted(
        ner["state_name"].unique()
    )

    for state in final_states:
        print(f"  ✅ {state}")

    print("\nDistrict count by state:")

    final_counts = (
        ner.groupby("state_name")
        .size()
        .sort_index()
    )

    print(
        final_counts.to_string()
    )

    print("\nOutput file:")
    print(OUTPUT)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()