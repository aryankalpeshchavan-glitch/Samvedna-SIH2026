from pathlib import Path
import re

import h5py
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import Transformer


# ============================================================
# CrisisCore - SMAP L4 V008 Soil Moisture Extraction
# NER district-level processing
# ============================================================

PROJECT_ROOT = Path(r"D:\sih project")

SMAP_DIR = PROJECT_ROOT / "data" / "raw" / "soil" / "smap_l4"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "soil"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_GRID = OUTPUT_DIR / "smap_ner_grid.csv"
OUTPUT_DISTRICT = OUTPUT_DIR / "smap_current_district_soil_moisture.csv"


# ------------------------------------------------------------
# NER bounding box
# ------------------------------------------------------------
# Approximate NER extent:
# longitude: 88E - 98E
# latitude : 21N - 30N

MIN_LON = 88.0
MAX_LON = 98.0
MIN_LAT = 21.0
MAX_LAT = 30.0


# ------------------------------------------------------------
# District boundary source
# ------------------------------------------------------------

BOUNDARY_CANDIDATES = [
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "gsi_districts" / "district_nwic.GeoJSON",
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "india_districts.geojson",
    PROJECT_ROOT / "data" / "raw" / "boundaries" / "india_district_imd.geojson",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def decode_value(value):
    """Decode HDF5 byte attributes."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def extract_timestamp(filename):
    """
    Extract SMAP timestamp.

    Example:
    SMAP_L4_SM_gph_20260902T223000_Vv8011_001.h5

    -> 2026-09-02 22:30:00 UTC
    """

    match = re.search(r"(\d{8}T\d{6})", filename)

    if not match:
        raise ValueError(
            f"Could not extract timestamp from filename: {filename}"
        )

    return pd.to_datetime(
        match.group(1),
        format="%Y%m%dT%H%M%S",
        utc=True
    )


def find_boundary_file():
    for path in BOUNDARY_CANDIDATES:
        if path.exists():
            print(f"\nBoundary file:")
            print(path)
            return path

    raise FileNotFoundError(
        "No district boundary file found.\n"
        "Checked:\n" +
        "\n".join(str(p) for p in BOUNDARY_CANDIDATES)
    )


def find_column(gdf, candidates):
    """
    Find a likely column using case-insensitive matching.
    """

    normalized = {
        str(col).strip().lower(): col
        for col in gdf.columns
    }

    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]

    return None


def load_ner_boundaries():
    print("\n[1] Loading NER district boundaries...")

    boundary_path = Path("data/raw/boundaries/gsi_districts/district_nwic.GeoJSON")

    if not boundary_path.exists():
        raise FileNotFoundError(
            f"Boundary file not found: {boundary_path}"
        )

    gdf = gpd.read_file(boundary_path)

    print(f"Boundary rows: {len(gdf)}")
    print(f"Boundary CRS: {gdf.crs}")
    print(f"Boundary columns: {list(gdf.columns)}")

    # ---------------------------------------------------------
    # Detect state and district columns
    # ---------------------------------------------------------
    if "state_name" in gdf.columns:
        state_col = "state_name"
    elif "state" in gdf.columns:
        state_col = "state"
    else:
        raise KeyError(
            "Could not find a state column. "
            f"Available columns: {list(gdf.columns)}"
        )

    if "district" in gdf.columns:
        district_col = "district"
    elif "ds_name" in gdf.columns:
        district_col = "ds_name"
    else:
        raise KeyError(
            "Could not find a district column. "
            f"Available columns: {list(gdf.columns)}"
        )

    print(f"Using state column: {state_col}")
    print(f"Using district column: {district_col}")

    # ---------------------------------------------------------
    # NER states
    # ---------------------------------------------------------
    ner_states = {
        "assam": "Assam",
        "arunachal pradesh": "Arunachal Pradesh",
        "arunanchal pradesh": "Arunachal Pradesh",  # SOURCE SPELLING
        "manipur": "Manipur",
        "meghalaya": "Meghalaya",
        "mizoram": "Mizoram",
        "nagaland": "Nagaland",
        "sikkim": "Sikkim",
        "tripura": "Tripura",
    }

    # ---------------------------------------------------------
    # Normalize state names
    # ---------------------------------------------------------
    gdf["state_original"] = gdf[state_col].astype(str).str.strip()

    gdf["state_normalized"] = (
        gdf["state_original"]
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # Explicitly fix source spelling:
    # Arunanchal Pradesh -> Arunachal Pradesh
    gdf["state_normalized"] = gdf["state_normalized"].replace(
        {
            "arunanchal pradesh": "arunachal pradesh"
        }
    )

    # ---------------------------------------------------------
    # Filter NER
    # ---------------------------------------------------------
    gdf = gdf[
        gdf["state_normalized"].isin(ner_states.keys())
    ].copy()

    # Convert to canonical state names
    gdf["state"] = gdf["state_normalized"].map(ner_states)

    # Canonical district name
    gdf["district"] = (
        gdf[district_col]
        .astype(str)
        .str.strip()
    )

    # ---------------------------------------------------------
    # Fix geometries instead of simply dropping invalid ones
    # ---------------------------------------------------------
    print("\nChecking geometries...")

    null_geom = gdf.geometry.isna().sum()
    empty_geom = gdf.geometry.is_empty.sum()
    invalid_geom = (~gdf.geometry.is_valid).sum()

    print(f"Null geometries: {null_geom}")
    print(f"Empty geometries: {empty_geom}")
    print(f"Invalid geometries: {invalid_geom}")

    # Remove only truly missing/empty geometries
    gdf = gdf[
        gdf.geometry.notna() &
        ~gdf.geometry.is_empty
    ].copy()

    # Repair invalid geometries
    invalid_mask = ~gdf.geometry.is_valid

    if invalid_mask.any():
        print(
            f"Repairing {invalid_mask.sum()} invalid geometries..."
        )

        try:
            gdf.loc[invalid_mask, "geometry"] = (
                gdf.loc[invalid_mask, "geometry"].make_valid()
            )
        except AttributeError:
            # Fallback for older Shapely versions
            gdf.loc[invalid_mask, "geometry"] = (
                gdf.loc[invalid_mask, "geometry"].buffer(0)
            )

    # Remove anything that remained unusable
    gdf = gdf[
        gdf.geometry.notna() &
        ~gdf.geometry.is_empty
    ].copy()

    # ---------------------------------------------------------
    # CRS
    # ---------------------------------------------------------
    if gdf.crs is None:
        raise ValueError("Boundary CRS is missing.")

    print(f"\nBoundary CRS before transform: {gdf.crs}")

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    print(f"Boundary CRS after transform: {gdf.crs}")

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------
    print("\nNER boundary summary:")
    print(
        gdf.groupby("state")
        .size()
        .sort_index()
    )

    print(f"\nNER states: {gdf['state'].nunique()}")
    print(f"NER districts: {gdf['district'].nunique()}")
    print(f"NER boundary rows: {len(gdf)}")

    expected_states = {
        "Assam",
        "Arunachal Pradesh",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Sikkim",
        "Tripura",
    }

    actual_states = set(gdf["state"].unique())

    missing_states = expected_states - actual_states

    if missing_states:
        raise ValueError(
            f"Missing NER states after filtering: {missing_states}"
        )

    print("\n✓ All 8 NER states successfully mapped.")

    return gdf

def get_ease_transformer():
    """
    SMAP L4 uses the EASE-Grid 2.0 global projection.

    EPSG:6933:
        WGS84 / NSIDC EASE-Grid 2.0 Global

    Returns:
        geographic -> EASE transformer
        EASE -> geographic transformer
    """

    to_ease = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:6933",
        always_xy=True
    )

    to_geo = Transformer.from_crs(
        "EPSG:6933",
        "EPSG:4326",
        always_xy=True
    )

    return to_ease, to_geo


def get_bbox_window(x, y):
    """
    Determine the SMAP array window covering the NER bounding box.

    HDF5 array shape:
        y = rows
        x = columns
    """

    to_ease, _ = get_ease_transformer()

    # Transform geographic corners to EASE coordinates
    x1, y1 = to_ease.transform(MIN_LON, MIN_LAT)
    x2, y2 = to_ease.transform(MAX_LON, MAX_LAT)

    min_x = min(x1, x2)
    max_x = max(x1, x2)
    min_y = min(y1, y2)
    max_y = max(y1, y2)

    print("\nNER EASE-Grid bounding box:")
    print(f"X: {min_x:.2f} -> {max_x:.2f}")
    print(f"Y: {min_y:.2f} -> {max_y:.2f}")

    # x is normally increasing
    x_mask = (x >= min_x) & (x <= max_x)

    # y may be increasing OR decreasing depending on dataset
    y_mask = (y >= min_y) & (y <= max_y)

    x_indices = np.where(x_mask)[0]
    y_indices = np.where(y_mask)[0]

    if len(x_indices) == 0 or len(y_indices) == 0:
        raise ValueError(
            "NER bounding box does not intersect the SMAP grid."
        )

    x_start = x_indices.min()
    x_end = x_indices.max() + 1

    y_start = y_indices.min()
    y_end = y_indices.max() + 1

    print("\nSMAP extraction window:")
    print(f"Rows: {y_start}:{y_end}")
    print(f"Cols: {x_start}:{x_end}")
    print(
        f"Window size: "
        f"{y_end - y_start} x {x_end - x_start}"
    )

    return (
        x_start,
        x_end,
        y_start,
        y_end
    )


def read_smap_file(file_path):
    """
    Read one SMAP L4 HDF5 file.

    Returns a dataframe containing NER grid cells.
    """

    print("\n" + "=" * 75)
    print(f"Processing: {file_path.name}")
    print("=" * 75)

    observation_time = extract_timestamp(file_path.name)

    print(f"Observation time: {observation_time}")

    with h5py.File(file_path, "r") as f:

        # ----------------------------------------------------
        # Coordinate arrays
        # ----------------------------------------------------

        x = f["x"][:]
        y = f["y"][:]

        print(f"x shape: {x.shape}")
        print(f"y shape: {y.shape}")

        # ----------------------------------------------------
        # Determine NER window
        # ----------------------------------------------------

        (
            x_start,
            x_end,
            y_start,
            y_end
        ) = get_bbox_window(x, y)

        x_subset = x[x_start:x_end]
        y_subset = y[y_start:y_end]

        # ----------------------------------------------------
        # Read only NER portion
        # ----------------------------------------------------

        dataset_names = [
            "sm_surface",
            "sm_rootzone",
            "sm_profile",
            "sm_surface_wetness",
            "sm_rootzone_wetness",
            "sm_profile_wetness",
            "sm_surface_pctl",
            "sm_rootzone_pctl",
            "sm_profile_pctl",
        ]

        arrays = {}

        for name in dataset_names:

            dataset_path = f"Geophysical_Data/{name}"

            if dataset_path not in f:
                print(f"WARNING: {dataset_path} not found")
                continue

            ds = f[dataset_path]

            arrays[name] = ds[
                y_start:y_end,
                x_start:x_end
            ]

            print(
                f"{name:<25} "
                f"{arrays[name].shape}"
            )

        if "sm_surface" not in arrays:
            raise ValueError(
                "sm_surface not found in SMAP file."
            )

        # ----------------------------------------------------
        # Create mesh
        # ----------------------------------------------------

        xx, yy = np.meshgrid(
            x_subset,
            y_subset
        )

        # ----------------------------------------------------
        # Convert EASE coordinates to lat/lon
        # ----------------------------------------------------

        _, to_geo = get_ease_transformer()

        lon, lat = to_geo.transform(
            xx,
            yy
        )

        # ----------------------------------------------------
        # Flatten
        # ----------------------------------------------------

        data = {
            "observation_time": np.full(
                xx.size,
                observation_time
            ),

            "x": xx.ravel(),
            "y": yy.ravel(),

            "latitude": lat.ravel(),
            "longitude": lon.ravel(),
        }

        for name, array in arrays.items():
            data[name] = array.ravel()

        df = pd.DataFrame(data)

        # ----------------------------------------------------
        # Valid SMAP surface moisture
        # ----------------------------------------------------

        # SMAP valid range:
        # 0.0 -> 0.9 m3/m3
        #
        # Anything outside this is treated as missing.

        for name in [
            "sm_surface",
            "sm_rootzone",
            "sm_profile"
        ]:
            if name in df.columns:
                df[name] = pd.to_numeric(
                    df[name],
                    errors="coerce"
                )

                df.loc[
                    (df[name] < 0) |
                    (df[name] > 0.9),
                    name
                ] = np.nan

        # Wetness
        for name in [
            "sm_surface_wetness",
            "sm_rootzone_wetness",
            "sm_profile_wetness"
        ]:
            if name in df.columns:
                df[name] = pd.to_numeric(
                    df[name],
                    errors="coerce"
                )

                df.loc[
                    (df[name] < 0) |
                    (df[name] > 1),
                    name
                ] = np.nan

        # Percentiles
        for name in [
            "sm_surface_pctl",
            "sm_rootzone_pctl",
            "sm_profile_pctl"
        ]:
            if name in df.columns:
                df[name] = pd.to_numeric(
                    df[name],
                    errors="coerce"
                )

                df.loc[
                    (df[name] < 0) |
                    (df[name] > 100),
                    name
                ] = np.nan

        # ----------------------------------------------------
        # Geographic NER filter
        # ----------------------------------------------------

        df = df[
            (df["longitude"] >= MIN_LON) &
            (df["longitude"] <= MAX_LON) &
            (df["latitude"] >= MIN_LAT) &
            (df["latitude"] <= MAX_LAT)
        ].copy()

        # Need at least surface moisture
        df = df[
            df["sm_surface"].notna()
        ].copy()

        print(
            f"\nValid NER grid cells: {len(df):,}"
        )

        return df


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 75)
    print("CrisisCore - SMAP L4 V008 Soil Moisture")
    print("NER extraction and district aggregation")
    print("=" * 75)

    # --------------------------------------------------------
    # Find HDF5 files
    # --------------------------------------------------------

    smap_files = sorted(
        SMAP_DIR.glob("*.h5")
    )

    if not smap_files:
        raise FileNotFoundError(
            f"No SMAP HDF5 files found in:\n{SMAP_DIR}"
        )

    print(
        f"\nSMAP HDF5 files found: {len(smap_files)}"
    )

    for f in smap_files:
        print(
            f"  {f.name} "
            f"({f.stat().st_size / 1024 / 1024:.1f} MB)"
        )

    # --------------------------------------------------------
    # Load boundaries
    # --------------------------------------------------------

    boundaries = load_ner_boundaries()

    # --------------------------------------------------------
    # Process SMAP files
    # --------------------------------------------------------

    all_grid = []

    for file_path in smap_files:

        try:
            df = read_smap_file(file_path)

            all_grid.append(df)

        except Exception as e:

            print(
                f"\nERROR processing {file_path.name}:"
            )
            print(e)
            raise

    if not all_grid:
        raise RuntimeError(
            "No SMAP data was successfully processed."
        )

    grid_df = pd.concat(
        all_grid,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Save grid-level NER data
    # --------------------------------------------------------

    grid_df.to_csv(
        OUTPUT_GRID,
        index=False
    )

    print("\n" + "=" * 75)
    print("NER GRID EXTRACTION COMPLETE")
    print("=" * 75)

    print(
        f"\nGrid rows: {len(grid_df):,}"
    )

    print(
        f"Observation times: "
        f"{grid_df['observation_time'].nunique()}"
    )

    print(
        f"\nSaved:"
        f"\n{OUTPUT_GRID}"
    )

    # --------------------------------------------------------
    # Spatial join to districts
    # --------------------------------------------------------

    print("\nCreating spatial points...")

    geometry = [
        Point(lon, lat)
        for lon, lat in zip(
            grid_df["longitude"],
            grid_df["latitude"]
        )
    ]

    grid_gdf = gpd.GeoDataFrame(
        grid_df,
        geometry=geometry,
        crs="EPSG:4326"
    )

    print("Performing district spatial join...")

    joined = gpd.sjoin(
        grid_gdf,
        boundaries,
        how="inner",
        predicate="within"
    )

    print(
        f"Grid cells matched to districts: "
        f"{len(joined):,}"
    )

    # --------------------------------------------------------
    # District aggregation
    # --------------------------------------------------------

    moisture_columns = [
        "sm_surface",
        "sm_rootzone",
        "sm_profile",
        "sm_surface_wetness",
        "sm_rootzone_wetness",
        "sm_profile_wetness",
        "sm_surface_pctl",
        "sm_rootzone_pctl",
        "sm_profile_pctl",
    ]

    existing_columns = [
        col
        for col in moisture_columns
        if col in joined.columns
    ]

    print(
        "\nAggregating:"
    )

    for col in existing_columns:
        print(f"  {col}")

    grouped = (
        joined
        .groupby(
            [
                "observation_time",
                "state",
                "district"
            ],
            dropna=False
        )
        [existing_columns]
        .agg(
            [
                "mean",
                "median",
                "min",
                "max",
                "std"
            ]
        )
    )

    # Flatten multi-index columns
    grouped.columns = [
        f"{col}_{stat}"
        for col, stat in grouped.columns
    ]

    district_df = grouped.reset_index()

    # --------------------------------------------------------
    # Grid-cell count
    # --------------------------------------------------------

    counts = (
        joined
        .groupby(
            [
                "observation_time",
                "state",
                "district"
            ]
        )
        .size()
        .reset_index(
            name="soil_moisture_grid_cells"
        )
    )

    district_df = district_df.merge(
        counts,
        on=[
            "observation_time",
            "state",
            "district"
        ],
        how="left"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    district_df.to_csv(
        OUTPUT_DISTRICT,
        index=False
    )

    print("\n" + "=" * 75)
    print("DISTRICT SOIL MOISTURE COMPLETE")
    print("=" * 75)

    print(
        f"\nDistrict rows: "
        f"{len(district_df):,}"
    )

    print(
        f"Unique states: "
        f"{district_df['state'].nunique()}"
    )

    print(
        f"Unique districts: "
        f"{district_df['district'].nunique()}"
    )

    print(
        f"Observation timestamps: "
        f"{district_df['observation_time'].nunique()}"
    )

    print(
        "\nState counts:"
    )

    print(
        district_df
        .groupby("state")
        .size()
        .sort_values(ascending=False)
    )

    print(
        f"\nSaved district dataset:"
        f"\n{OUTPUT_DISTRICT}"
    )

    print("\n" + "=" * 75)
    print("SOIL MOISTURE PIPELINE COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()