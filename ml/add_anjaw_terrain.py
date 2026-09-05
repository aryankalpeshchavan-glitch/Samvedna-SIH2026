import os
import glob
import numpy as np
import pandas as pd
import rasterio
from rasterio.merge import merge
from rasterio.transform import rowcol


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

TERRAIN_DATASET = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_event_training_dataset_terrain.csv"
)

DEM_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "terrain",
    "copernicus_glo90"
)


# ============================================================
# ANJAW REFERENCE COORDINATE
# ============================================================

LATITUDE = 28.06549
LONGITUDE = 96.82878


print("=" * 70)
print("CRISISCORE - ADD ANJAW TERRAIN FEATURE")
print("=" * 70)


# ============================================================
# LOAD TERRAIN DATASET
# ============================================================

print("\n[1] Loading terrain dataset...")

df = pd.read_csv(TERRAIN_DATASET)

print("Rows before:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# CHECK IF ANJAW ALREADY EXISTS
# ============================================================

existing = df[
    (df["state"].astype(str).str.upper() == "ARUNACHAL PRADESH")
    &
    (df["district"].astype(str).str.lower() == "anjaw")
]

if not existing.empty:

    print("\nAnjaw already exists.")
    print(existing.to_string(index=False))

    raise SystemExit(0)


# ============================================================
# FIND DEM TILES
# ============================================================

print("\n[2] Searching DEM tiles...")

dem_files = glob.glob(
    os.path.join(
        DEM_DIR,
        "*.tif"
    )
)

print("DEM files found:", len(dem_files))


if not dem_files:

    raise FileNotFoundError(
        f"No DEM tiles found in:\n{DEM_DIR}"
    )


# ============================================================
# FIND TILE CONTAINING ANJAW
# ============================================================

print("\n[3] Finding DEM tile for Anjaw...")

target_tile = None

for tif in dem_files:

    try:

        with rasterio.open(tif) as src:

            bounds = src.bounds

            if (
                bounds.left <= LONGITUDE <= bounds.right
                and
                bounds.bottom <= LATITUDE <= bounds.top
            ):

                target_tile = tif
                break

    except Exception:
        continue


if target_tile is None:

    raise ValueError(
        "Could not find a DEM tile covering Anjaw."
    )


print("DEM tile:")
print(target_tile)


# ============================================================
# OPEN DEM
# ============================================================

print("\n[4] Reading DEM...")

with rasterio.open(target_tile) as src:

    elevation_array = src.read(1)

    transform = src.transform

    nodata = src.nodata

    crs = src.crs

    row, col = rowcol(
        transform,
        LONGITUDE,
        LATITUDE
    )

    print("CRS:", crs)
    print("Pixel row:", row)
    print("Pixel col:", col)


# ============================================================
# ELEVATION
# ============================================================

if (
    row < 0
    or
    col < 0
    or
    row >= elevation_array.shape[0]
    or
    col >= elevation_array.shape[1]
):

    raise ValueError(
        "Anjaw coordinate falls outside DEM raster."
    )


elevation = float(
    elevation_array[row, col]
)


if nodata is not None and elevation == nodata:

    raise ValueError(
        "DEM returned NoData for Anjaw coordinate."
    )


print("Elevation:", elevation, "m")


# ============================================================
# CALCULATE LOCAL SLOPE / ASPECT
# ============================================================

print("\n[5] Calculating terrain derivatives...")


window_size = 5

r0 = max(0, row - window_size)
r1 = min(
    elevation_array.shape[0],
    row + window_size + 1
)

c0 = max(0, col - window_size)
c1 = min(
    elevation_array.shape[1],
    col + window_size + 1
)


window = elevation_array[
    r0:r1,
    c0:c1
].astype(float)


# Remove nodata values

if nodata is not None:

    window[
        window == nodata
    ] = np.nan


# Pixel resolution

with rasterio.open(target_tile) as src:

    pixel_x = abs(src.transform.a)
    pixel_y = abs(src.transform.e)


# Convert degrees to approximate metres

meters_per_degree_lat = 111320.0

meters_per_degree_lon = (
    111320.0 *
    np.cos(
        np.radians(LATITUDE)
    )
)

pixel_width_m = (
    pixel_x *
    meters_per_degree_lon
)

pixel_height_m = (
    pixel_y *
    meters_per_degree_lat
)


# Gradient

gradient_y, gradient_x = np.gradient(
    window,
    pixel_height_m,
    pixel_width_m
)


# Center pixel

center_r = row - r0
center_c = col - c0


dzdx = gradient_x[
    center_r,
    center_c
]

dzdy = gradient_y[
    center_r,
    center_c
]


# ============================================================
# SLOPE
# ============================================================

slope_deg = np.degrees(
    np.arctan(
        np.sqrt(
            dzdx ** 2 +
            dzdy ** 2
        )
    )
)


# ============================================================
# ASPECT
# ============================================================

aspect_deg = (
    np.degrees(
        np.arctan2(
            -dzdx,
            dzdy
        )
    )
    + 360
) % 360


# ============================================================
# TERRAIN ROUGHNESS
# ============================================================

roughness = float(
    np.nanstd(window)
)


print("Slope:", slope_deg)
print("Aspect:", aspect_deg)
print("Roughness:", roughness)


# ============================================================
# BUILD ANJAW ROW
# ============================================================

anjaw_row = {

    "state":
        "ARUNACHAL PRADESH",

    "district":
        "anjaw",

    "latitude":
        LATITUDE,

    "longitude":
        LONGITUDE,

    "elevation_m":
        elevation,

    "slope_deg":
        slope_deg,

    "aspect_deg":
        aspect_deg,

    "terrain_roughness":
        roughness
}


# ============================================================
# PRESERVE ALL EXISTING COLUMNS
# ============================================================

for column in df.columns:

    if column not in anjaw_row:

        anjaw_row[column] = np.nan


anjaw_df = pd.DataFrame(
    [anjaw_row],
    columns=df.columns
)


# ============================================================
# APPEND
# ============================================================

print("\n[6] Adding Anjaw...")

df_final = pd.concat(
    [
        df,
        anjaw_df
    ],
    ignore_index=True
)


# ============================================================
# SAVE
# ============================================================

df_final.to_csv(
    TERRAIN_DATASET,
    index=False
)


print("\n[7] Validation...")

check = df_final[
    (df_final["state"].astype(str).str.upper()
     == "ARUNACHAL PRADESH")
    &
    (df_final["district"].astype(str).str.lower()
     == "anjaw")
]


print(check[
    [
        "state",
        "district",
        "latitude",
        "longitude",
        "elevation_m",
        "slope_deg",
        "aspect_deg",
        "terrain_roughness"
    ]
].to_string(index=False))


print("\nRows after:", len(df_final))


print("\n" + "=" * 70)
print("ANJAW TERRAIN FEATURE ADDED SUCCESSFULLY")
print("=" * 70)