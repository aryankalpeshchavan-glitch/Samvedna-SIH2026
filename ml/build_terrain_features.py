from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds, Window


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEM_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "terrain"
    / "copernicus_glo90"
)

BOUNDARY_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "boundaries"
    / "gsi_districts"
    / "district_nwic.GeoJSON"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "terrain"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "terrain_district_features.csv"
)


# ============================================================
# NER STATES
# ============================================================

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


# ============================================================
# STATE NORMALIZATION
# ============================================================

def normalize_state(value):

    if pd.isna(value):
        return None

    s = str(value).strip().lower()

    mapping = {
        "arunanchal pradesh": "Arunachal Pradesh",
        "arunachal pradesh": "Arunachal Pradesh",
        "assam": "Assam",
        "manipur": "Manipur",
        "meghalaya": "Meghalaya",
        "mizoram": "Mizoram",
        "nagaland": "Nagaland",
        "sikkim": "Sikkim",
        "tripura": "Tripura",
    }

    return mapping.get(
        s,
        str(value).strip()
    )


# ============================================================
# BUILD DEM TILE INDEX
# ============================================================

def build_dem_index():

    pattern = re.compile(
        r"Copernicus_DSM_COG_30_"
        r"N(\d+)_00_"
        r"E(\d+)_00_DEM\.tif$",
        re.IGNORECASE,
    )

    tiles = []

    for path in sorted(
        DEM_DIR.glob("*.tif")
    ):

        match = pattern.search(
            path.name
        )

        if not match:

            print(
                f"WARNING: Could not parse "
                f"DEM filename: {path.name}"
            )

            continue

        lat = int(
            match.group(1)
        )

        lon = int(
            match.group(2)
        )

        tiles.append(
            {
                "path": path,
                "lat_min": lat,
                "lat_max": lat + 1,
                "lon_min": lon,
                "lon_max": lon + 1,
            }
        )

    return tiles


# ============================================================
# FIND DEM TILES INTERSECTING DISTRICT
# ============================================================

def tiles_for_bounds(
    bounds,
    dem_tiles
):

    minx, miny, maxx, maxy = bounds

    selected = []

    eps = 1e-8

    for tile in dem_tiles:

        intersects = (
            tile["lon_min"]
            <= maxx + eps
            and
            tile["lon_max"]
            >= minx - eps
            and
            tile["lat_min"]
            <= maxy + eps
            and
            tile["lat_max"]
            >= miny - eps
        )

        if intersects:

            selected.append(
                tile
            )

    return selected


# ============================================================
# EXTRACT DATA FROM ONE DEM TILE
# ============================================================

def extract_from_tile(
    src,
    geometry
):

    # --------------------------------------------------------
    # IMPORTANT:
    # geometry.bounds returns:
    #
    # (minx, miny, maxx, maxy)
    #
    # It does NOT return an object with
    # .left/.right/.top/.bottom
    # --------------------------------------------------------

    minx, miny, maxx, maxy = (
        geometry.bounds
    )

    # --------------------------------------------------------
    # Create raster window
    # --------------------------------------------------------

    window = from_bounds(
        minx,
        miny,
        maxx,
        maxy,
        src.transform,
    )

    # --------------------------------------------------------
    # Clip window to raster extent
    # --------------------------------------------------------

    raster_window = Window(
        0,
        0,
        src.width,
        src.height,
    )

    window = window.intersection(
        raster_window
    )

    if (
        window.width <= 0
        or
        window.height <= 0
    ):

        return None, None

    # --------------------------------------------------------
    # Read DEM
    # --------------------------------------------------------

    elevation = src.read(
        1,
        window=window,
        masked=True,
    )

    if elevation.size == 0:

        return None, None

    # --------------------------------------------------------
    # Transform for the selected window
    # --------------------------------------------------------

    transform = (
        src.window_transform(
            window
        )
    )

    # --------------------------------------------------------
    # Mask pixels outside district
    # --------------------------------------------------------

    district_mask = geometry_mask(
        [geometry],
        out_shape=elevation.shape,
        transform=transform,
        invert=True,
    )

    raster_invalid_mask = (
        np.ma.getmaskarray(
            elevation
        )
    )

    valid = (
        ~raster_invalid_mask
        &
        district_mask
    )

    if not np.any(valid):

        return None, None

    # --------------------------------------------------------
    # Elevation values
    # --------------------------------------------------------

    elevation_data = np.asarray(
        elevation.data,
        dtype=float
    )

    elevation_values = (
        elevation_data[valid]
    )

    elevation_values = (
        elevation_values[
            np.isfinite(
                elevation_values
            )
        ]
    )

    if elevation_values.size == 0:

        return None, None

    # ========================================================
    # SLOPE CALCULATION
    # ========================================================

    minx, miny, maxx, maxy = (
        geometry.bounds
    )

    mean_lat = (
        miny + maxy
    ) / 2.0

    # Approximate metres per degree
    meters_per_degree_lat = 111320.0

    meters_per_degree_lon = (
        111320.0
        *
        np.cos(
            np.deg2rad(
                mean_lat
            )
        )
    )

    pixel_width_m = (
        abs(transform.a)
        *
        meters_per_degree_lon
    )

    pixel_height_m = (
        abs(transform.e)
        *
        meters_per_degree_lat
    )

    if (
        pixel_width_m <= 0
        or
        pixel_height_m <= 0
    ):

        return (
            elevation_values,
            np.array([])
        )

    # --------------------------------------------------------
    # Convert masked DEM to NaN
    # --------------------------------------------------------

    dem_float = (
        np.asarray(
            elevation.filled(
                np.nan
            ),
            dtype=float
        )
    )

    # --------------------------------------------------------
    # Calculate elevation gradients
    # --------------------------------------------------------

    grad_y, grad_x = np.gradient(
        dem_float,
        pixel_height_m,
        pixel_width_m,
    )

    # --------------------------------------------------------
    # Gradient -> slope angle
    # --------------------------------------------------------

    slope = np.degrees(
        np.arctan(
            np.sqrt(
                np.square(
                    grad_x
                )
                +
                np.square(
                    grad_y
                )
            )
        )
    )

    slope_valid = (
        valid
        &
        np.isfinite(
            slope
        )
    )

    slope_values = (
        slope[
            slope_valid
        ]
    )

    return (
        elevation_values,
        slope_values
    )


# ============================================================
# MAIN
# ============================================================

print(
    "\n[1/7] Finding DEM tiles..."
)

dem_tiles = build_dem_index()

print(
    f"DEM tiles found: "
    f"{len(dem_tiles)}"
)

if len(dem_tiles) == 0:

    raise RuntimeError(
        "No DEM .tif files found."
    )


# ============================================================
# VALIDATE DEM TILES
# ============================================================

print(
    "\n[2/7] Validating DEM tiles..."
)

valid_dem_tiles = []

for i, tile in enumerate(
    dem_tiles,
    start=1
):

    path = tile["path"]

    try:

        with rasterio.open(
            path
        ) as src:

            # Read small sample
            # to verify the TIFF.

            sample = src.read(
                1,
                out_shape=(
                    1,
                    50,
                    50
                ),
                masked=True,
            )

            if sample.size == 0:

                raise RuntimeError(
                    "Empty raster."
                )

            print(
                f"[{i}/{len(dem_tiles)}] "
                f"{path.name} | "
                f"{src.width}x{src.height} | "
                f"CRS={src.crs}"
            )

            valid_dem_tiles.append(
                tile
            )

    except Exception as e:

        print(
            f"WARNING: DEM tile failed "
            f"validation: {path.name}"
        )

        print(
            f"         {e}"
        )


print(
    f"\nValid DEM tiles: "
    f"{len(valid_dem_tiles)}/"
    f"{len(dem_tiles)}"
)

if len(valid_dem_tiles) == 0:

    raise RuntimeError(
        "No valid DEM tiles available."
    )


# ============================================================
# LOAD DISTRICT BOUNDARIES
# ============================================================

print(
    "\n[3/7] Loading NER district boundaries..."
)

gdf = gpd.read_file(
    BOUNDARY_FILE
)

print(
    f"Boundary rows: "
    f"{len(gdf)}"
)

print(
    f"Boundary CRS: "
    f"{gdf.crs}"
)

if "state_name" not in gdf.columns:

    raise KeyError(
        "Expected 'state_name' "
        "column in boundary file."
    )

if "district" not in gdf.columns:

    raise KeyError(
        "Expected 'district' "
        "column in boundary file."
    )


# ============================================================
# NORMALIZE STATES
# ============================================================

gdf["state_name"] = (
    gdf["state_name"]
    .apply(
        normalize_state
    )
)

gdf = gdf[
    gdf["state_name"]
    .isin(
        NER_STATES
    )
].copy()

print(
    f"NER districts: "
    f"{len(gdf)}"
)


# ============================================================
# REPAIR GEOMETRIES
# ============================================================

invalid_before = (
    ~gdf.geometry.is_valid
).sum()

if invalid_before > 0:

    print(
        f"Invalid geometries "
        f"before repair: "
        f"{invalid_before}"
    )

    gdf["geometry"] = (
        gdf.geometry.make_valid()
    )

invalid_after = (
    ~gdf.geometry.is_valid
).sum()

print(
    f"Invalid geometries "
    f"after repair: "
    f"{invalid_after}"
)


# ============================================================
# PREPARE CRS
# ============================================================

print(
    "\n[4/7] Preparing district geometries..."
)

with rasterio.open(
    valid_dem_tiles[0]["path"]
) as src:

    dem_crs = src.crs

print(
    f"DEM CRS: "
    f"{dem_crs}"
)

if gdf.crs != dem_crs:

    print(
        f"Reprojecting boundaries "
        f"{gdf.crs} -> {dem_crs}"
    )

    gdf = gdf.to_crs(
        dem_crs
    )


# ============================================================
# EXTRACT TERRAIN FEATURES
# ============================================================

print(
    "\n[5/7] Extracting terrain statistics..."
)

results = []

total_districts = len(gdf)

for district_number, (
    idx,
    row
) in enumerate(
    gdf.iterrows(),
    start=1
):

    state = (
        row["state_name"]
    )

    district = (
        str(
            row["district"]
        ).strip()
    )

    geometry = row.geometry

    print(
        f"[{district_number}/"
        f"{total_districts}] "
        f"{state} - "
        f"{district}"
    )

    # --------------------------------------------------------
    # Find DEM tiles
    # --------------------------------------------------------

    matching_tiles = (
        tiles_for_bounds(
            geometry.bounds,
            valid_dem_tiles
        )
    )

    if not matching_tiles:

        print(
            "   WARNING: No DEM tile "
            "intersects this district."
        )

        results.append(
            {
                "state": state,
                "district": district,

                "elevation_mean_m": np.nan,
                "elevation_min_m": np.nan,
                "elevation_max_m": np.nan,
                "elevation_std_m": np.nan,

                "slope_mean_deg": np.nan,
                "slope_max_deg": np.nan,
                "slope_std_deg": np.nan,

                "terrain_grid_cells": 0,
            }
        )

        continue

    district_elevation = []
    district_slope = []

    # --------------------------------------------------------
    # Read each relevant DEM tile
    # --------------------------------------------------------

    for tile in matching_tiles:

        try:

            with rasterio.open(
                tile["path"]
            ) as src:

                elevation_values, slope_values = (
                    extract_from_tile(
                        src,
                        geometry
                    )
                )

                if (
                    elevation_values
                    is not None
                ):

                    district_elevation.append(
                        elevation_values
                    )

                if (
                    slope_values
                    is not None
                    and
                    slope_values.size > 0
                ):

                    district_slope.append(
                        slope_values
                    )

        except Exception as e:

            print(
                f"   WARNING reading "
                f"{tile['path'].name}: "
                f"{e}"
            )

    # --------------------------------------------------------
    # No valid pixels
    # --------------------------------------------------------

    if not district_elevation:

        print(
            "   WARNING: No valid "
            "elevation pixels found."
        )

        results.append(
            {
                "state": state,
                "district": district,

                "elevation_mean_m": np.nan,
                "elevation_min_m": np.nan,
                "elevation_max_m": np.nan,
                "elevation_std_m": np.nan,

                "slope_mean_deg": np.nan,
                "slope_max_deg": np.nan,
                "slope_std_deg": np.nan,

                "terrain_grid_cells": 0,
            }
        )

        continue

    # --------------------------------------------------------
    # Combine pixels from all tiles
    # --------------------------------------------------------

    elevation_values = (
        np.concatenate(
            district_elevation
        )
    )

    if district_slope:

        slope_values = (
            np.concatenate(
                district_slope
            )
        )

    else:

        slope_values = (
            np.array(
                [],
                dtype=float
            )
        )

    # --------------------------------------------------------
    # Terrain statistics
    # --------------------------------------------------------

    result = {

        "state":
            state,

        "district":
            district,

        "elevation_mean_m":
            float(
                np.mean(
                    elevation_values
                )
            ),

        "elevation_min_m":
            float(
                np.min(
                    elevation_values
                )
            ),

        "elevation_max_m":
            float(
                np.max(
                    elevation_values
                )
            ),

        "elevation_std_m":
            float(
                np.std(
                    elevation_values
                )
            ),

        "slope_mean_deg":
            float(
                np.mean(
                    slope_values
                )
            )
            if slope_values.size
            else np.nan,

        "slope_max_deg":
            float(
                np.max(
                    slope_values
                )
            )
            if slope_values.size
            else np.nan,

        "slope_std_deg":
            float(
                np.std(
                    slope_values
                )
            )
            if slope_values.size
            else np.nan,

        "terrain_grid_cells":
            int(
                elevation_values.size
            ),
    }

    results.append(
        result
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

print(
    "\n[6/7] Creating terrain feature table..."
)

terrain_df = pd.DataFrame(
    results
)


# ============================================================
# CREATE DISTRICT KEY
# ============================================================

terrain_df["district_key"] = (
    terrain_df["state"]
    .str.lower()
    .str.strip()
    +
    "|"
    +
    terrain_df["district"]
    .str.lower()
    .str.strip()
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

terrain_df = (
    terrain_df
    .drop_duplicates(
        subset=[
            "district_key"
        ]
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# VALIDATION
# ============================================================

print(
    "\n[7/7] Validating and saving..."
)

print(
    f"Rows: "
    f"{len(terrain_df)}"
)

print(
    f"Columns: "
    f"{len(terrain_df.columns)}"
)


# ============================================================
# MISSING VALUES
# ============================================================

print(
    "\nMissing values:"
)

missing = (
    terrain_df
    .isna()
    .sum()
)

missing = (
    missing[
        missing > 0
    ]
)

if len(missing) > 0:

    print(
        missing.to_string()
    )

else:

    print(
        "None"
    )


# ============================================================
# TERRAIN GRID STATISTICS
# ============================================================

print(
    "\nTerrain grid-cell statistics:"
)

print(
    terrain_df[
        "terrain_grid_cells"
    ].describe()
)


# ============================================================
# ZERO-CELL DISTRICTS
# ============================================================

print(
    "\nDistricts with zero terrain cells:"
)

zero_cells = terrain_df[
    terrain_df[
        "terrain_grid_cells"
    ] == 0
][
    [
        "state",
        "district"
    ]
]

if len(zero_cells) > 0:

    print(
        zero_cells.to_string(
            index=False
        )
    )

else:

    print(
        "None"
    )


# ============================================================
# LOW-CELL DISTRICTS
# ============================================================

print(
    "\nDistricts with fewer than 100 terrain cells:"
)

low_cells = terrain_df[
    terrain_df[
        "terrain_grid_cells"
    ] < 100
][
    [
        "state",
        "district",
        "terrain_grid_cells"
    ]
]

if len(low_cells) > 0:

    print(
        low_cells.to_string(
            index=False
        )
    )

else:

    print(
        "None"
    )


# ============================================================
# STATE COUNTS
# ============================================================

print(
    "\nDistrict count by state:"
)

print(
    terrain_df[
        "state"
    ].value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# SAVE
# ============================================================

terrain_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    "\nSUCCESS: Terrain features "
    "saved to:"
)

print(
    OUTPUT_FILE
)