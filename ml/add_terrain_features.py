import os
import math
import requests
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window


# ============================================================
# CRISISCORE TERRAIN FEATURE ENGINE
# ============================================================

INPUT_FILE = "data/processed/ml/real_event_training_dataset_final.csv"
OUTPUT_FILE = "data/processed/ml/real_event_training_dataset_terrain.csv"

CACHE_DIR = "data/raw/terrain/copernicus_glo90"

BUCKET = "https://copernicus-dem-90m.s3.eu-central-1.amazonaws.com"

TILE_LIST_URL = f"{BUCKET}/tileList.txt"


# ------------------------------------------------------------
# TILE NAME
# ------------------------------------------------------------

def coordinate_to_tile(lat, lon):

    lat_floor = math.floor(lat)
    lon_floor = math.floor(lon)

    if lat_floor >= 0:
        lat_part = f"N{lat_floor:02d}"
    else:
        lat_part = f"S{abs(lat_floor):02d}"

    if lon_floor >= 0:
        lon_part = f"E{lon_floor:03d}"
    else:
        lon_part = f"W{abs(lon_floor):03d}"

    return (
        f"Copernicus_DSM_COG_30_"
        f"{lat_part}_00_"
        f"{lon_part}_00_DEM"
    )


# ------------------------------------------------------------
# DOWNLOAD TILE LIST
# ------------------------------------------------------------

def load_tile_list():

    print("\n[1] Loading Copernicus DEM tile list...")

    response = requests.get(TILE_LIST_URL, timeout=60)
    response.raise_for_status()

    tiles = set()

    for line in response.text.splitlines():

        line = line.strip()

        if line.startswith("Copernicus_DSM_COG_30_"):
            tiles.add(line)

    print("Available DEM tiles:", len(tiles))

    return tiles


# ------------------------------------------------------------
# DEM URL
# ------------------------------------------------------------

def get_dem_url(tile):

    filename = f"{tile}.tif"

    return (
        f"{BUCKET}/"
        f"{tile}/"
        f"{filename}"
    )


# ------------------------------------------------------------
# CACHE / DOWNLOAD
# ------------------------------------------------------------

def get_local_dem(tile):

    os.makedirs(CACHE_DIR, exist_ok=True)

    filename = f"{tile}.tif"

    local_path = os.path.join(CACHE_DIR, filename)

    if os.path.exists(local_path):
        print("Using cached tile:", filename)
        return local_path

    url = get_dem_url(tile)

    print("Downloading:")
    print(url)

    response = requests.get(
        url,
        stream=True,
        timeout=180
    )

    response.raise_for_status()

    with open(local_path, "wb") as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if chunk:
                f.write(chunk)

    print("Saved:", local_path)

    return local_path


# ------------------------------------------------------------
# SAFE DEM VALUE
# ------------------------------------------------------------

def clean_value(value):

    if value is None:
        return np.nan

    try:
        value = float(value)
    except Exception:
        return np.nan

    if not np.isfinite(value):
        return np.nan

    if value < -500:
        return np.nan

    if value > 10000:
        return np.nan

    return value


# ------------------------------------------------------------
# TERRAIN EXTRACTION
# ------------------------------------------------------------

def extract_terrain(dem_path, latitude, longitude):

    try:

        with rasterio.open(dem_path) as src:

            # Convert geographic coordinate to raster coordinate
            row, col = src.index(
                longitude,
                latitude
            )

            # Need a 3x3 neighborhood
            if (
                row < 1
                or col < 1
                or row >= src.height - 1
                or col >= src.width - 1
            ):
                return np.nan, np.nan, np.nan, np.nan

            window = Window(
                col - 1,
                row - 1,
                3,
                3
            )

            elevation = src.read(
                1,
                window=window
            ).astype(float)

            nodata = src.nodata

            if nodata is not None:
                elevation[
                    elevation == nodata
                ] = np.nan

            elevation[
                ~np.isfinite(elevation)
            ] = np.nan

            center = clean_value(
                elevation[1, 1]
            )

            if np.isnan(center):
                return np.nan, np.nan, np.nan, np.nan

            # ------------------------------------------------
            # Pixel dimensions
            # ------------------------------------------------

            transform = src.transform

            pixel_width_deg = abs(
                transform.a
            )

            pixel_height_deg = abs(
                transform.e
            )

            # Convert degrees to approximately metres
            meters_per_degree_lat = 111320.0

            meters_per_degree_lon = (
                111320.0
                * math.cos(
                    math.radians(latitude)
                )
            )

            dx = (
                pixel_width_deg
                * meters_per_degree_lon
            )

            dy = (
                pixel_height_deg
                * meters_per_degree_lat
            )

            if dx <= 0 or dy <= 0:
                return center, np.nan, np.nan, np.nan

            # ------------------------------------------------
            # Check neighborhood
            # ------------------------------------------------

            if np.isnan(elevation).sum() > 0:
                return center, np.nan, np.nan, np.nan

            # ------------------------------------------------
            # Horn slope calculation
            # ------------------------------------------------

            z1 = elevation[0, 0]
            z2 = elevation[0, 1]
            z3 = elevation[0, 2]

            z4 = elevation[1, 0]
            z6 = elevation[1, 2]

            z7 = elevation[2, 0]
            z8 = elevation[2, 1]
            z9 = elevation[2, 2]

            dzdx = (
                (z3 + 2*z6 + z9)
                -
                (z1 + 2*z4 + z7)
            ) / (8.0 * dx)

            dzdy = (
                (z7 + 2*z8 + z9)
                -
                (z1 + 2*z2 + z3)
            ) / (8.0 * dy)

            slope_rad = math.atan(
                math.sqrt(
                    dzdx**2 + dzdy**2
                )
            )

            slope_deg = math.degrees(
                slope_rad
            )

            # ------------------------------------------------
            # Aspect
            # ------------------------------------------------

            aspect_rad = math.atan2(
                -dzdx,
                dzdy
            )

            aspect_deg = math.degrees(
                aspect_rad
            )

            if aspect_deg < 0:
                aspect_deg += 360.0

            # ------------------------------------------------
            # Terrain roughness
            # ------------------------------------------------

            roughness = float(
                np.std(elevation)
            )

            return (
                center,
                slope_deg,
                aspect_deg,
                roughness
            )

    except Exception as e:

        print(
            f"Terrain extraction error "
            f"at {latitude}, {longitude}: {e}"
        )

        return (
            np.nan,
            np.nan,
            np.nan,
            np.nan
        )


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("CRISISCORE TERRAIN FEATURE ENGINE")
print("=" * 70)


# ------------------------------------------------------------
# 1. Load dataset
# ------------------------------------------------------------

print("\n[1] Loading coordinate-enabled dataset...")

df = pd.read_csv(INPUT_FILE)

print("Rows:", len(df))
print("Columns:", len(df.columns))


required = [
    "latitude",
    "longitude",
    "state",
    "district",
    "landslide_event"
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:

    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ------------------------------------------------------------
# 2. Load tile list
# ------------------------------------------------------------

available_tiles = load_tile_list()


# ------------------------------------------------------------
# 3. Determine required tiles
# ------------------------------------------------------------

print("\n[2] Determining required DEM tiles...")

df["dem_tile"] = df.apply(
    lambda r:
        coordinate_to_tile(
            r["latitude"],
            r["longitude"]
        ),
    axis=1
)

required_tiles = sorted(
    df["dem_tile"].dropna().unique()
)

print(
    "Required DEM tiles:",
    len(required_tiles)
)

missing_tiles = [
    tile
    for tile in required_tiles
    if tile not in available_tiles
]

if missing_tiles:

    print("\nWARNING: Missing DEM tiles:")

    for tile in missing_tiles:
        print(tile)

    raise RuntimeError(
        "Some required DEM tiles were not found."
    )


print("\nRequired tiles:")

for tile in required_tiles:
    print(" ", tile)


# ------------------------------------------------------------
# 4. Download required tiles
# ------------------------------------------------------------

print("\n[3] Preparing DEM tiles...")

dem_paths = {}

for i, tile in enumerate(
    required_tiles,
    start=1
):

    print(
        f"\nTile {i}/{len(required_tiles)}"
    )

    dem_paths[tile] = get_local_dem(tile)


# ------------------------------------------------------------
# 5. Extract terrain features
# ------------------------------------------------------------

print("\n[4] Extracting terrain features...")

elevations = []
slopes = []
aspects = []
roughnesses = []

total = len(df)

for i, row in df.iterrows():

    if i % 100 == 0:

        print(
            f"Processing {i}/{total}"
        )

    lat = row["latitude"]
    lon = row["longitude"]

    tile = row["dem_tile"]

    dem_path = dem_paths.get(tile)

    if dem_path is None:

        elevations.append(np.nan)
        slopes.append(np.nan)
        aspects.append(np.nan)
        roughnesses.append(np.nan)

        continue

    (
        elevation,
        slope,
        aspect,
        roughness
    ) = extract_terrain(
        dem_path,
        lat,
        lon
    )

    elevations.append(elevation)
    slopes.append(slope)
    aspects.append(aspect)
    roughnesses.append(roughness)


# ------------------------------------------------------------
# 6. Add features
# ------------------------------------------------------------

df["elevation_m"] = elevations
df["slope_deg"] = slopes
df["aspect_deg"] = aspects
df["terrain_roughness"] = roughnesses


# ------------------------------------------------------------
# 7. Remove helper column
# ------------------------------------------------------------

df.drop(
    columns=["dem_tile"],
    inplace=True
)


# ------------------------------------------------------------
# 8. Validation
# ------------------------------------------------------------

print("\n[5] Terrain validation...")

terrain_columns = [
    "elevation_m",
    "slope_deg",
    "aspect_deg",
    "terrain_roughness"
]

print("\nNULL COUNTS:")

print(
    df[terrain_columns]
    .isna()
    .sum()
)


print("\nTERRAIN SUMMARY:")

print(
    df[terrain_columns]
    .describe()
)


# ------------------------------------------------------------
# 9. Save
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 10. Final report
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TERRAIN-ENABLED DATASET COMPLETE")
print("=" * 70)

print("\nOutput:")
print(
    os.path.abspath(OUTPUT_FILE)
)

print("\nRows:", len(df))
print("Columns:", len(df.columns))

print("\nNEW TERRAIN FEATURES:")

for column in terrain_columns:
    print(
        f"  {column}"
    )

print("\nLANDSLIDE LABEL:")

print(
    df["landslide_event"]
    .value_counts()
)

print("\nSAMPLE TERRAIN DATA:")

print(
    df[
        [
            "state",
            "district",
            "latitude",
            "longitude",
            "elevation_m",
            "slope_deg",
            "aspect_deg",
            "terrain_roughness",
            "landslide_event"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

print("\n" + "=" * 70)
print("SUCCESS")
print("=" * 70)