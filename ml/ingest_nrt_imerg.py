from pathlib import Path
import rasterio
import numpy as np
import pandas as pd
import re


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RASTER = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "rainfall"
    / "nrt"
    / "20260901"
    / "3B-HHR-E.MS.MRG.3IMERG.20260901-S053000-E055959.0330.V07C.1day.tif"
)

OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "nrt"
    / "imerg_1day_grid.csv"
)

SCALE_FACTOR = 10.0
MISSING_VALUE = 29999


# ---------------------------------------------------------
# EXTRACT OBSERVATION DATE FROM FILENAME
# ---------------------------------------------------------

filename = RASTER.name

# Find an 8-digit date such as 20260901 anywhere in filename
date_match = re.search(r"(?<!\d)(\d{8})(?!\d)", filename)

if not date_match:
    raise ValueError(
        f"Could not find YYYYMMDD date in IMERG filename:\n{filename}"
    )

date_token = date_match.group(1)

OBSERVATION_DATE = pd.to_datetime(
    date_token,
    format="%Y%m%d"
).date()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("NASA IMERG NRT 1-DAY INGESTION")
    print("=" * 60)

    print("\nInput raster:")
    print(RASTER)

    print("\nObservation date:")
    print(OBSERVATION_DATE)

    if not RASTER.exists():
        raise FileNotFoundError(
            f"IMERG raster not found:\n{RASTER}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # READ RASTER
    # -----------------------------------------------------

    with rasterio.open(RASTER) as src:

        data = src.read(1)

        transform = src.transform
        width = src.width
        height = src.height
        bounds = src.bounds
        crs = src.crs
        resolution = src.res

        print("\nRaster information")
        print("-" * 40)
        print(f"Width:       {width}")
        print(f"Height:      {height}")
        print(f"Resolution:  {resolution}")
        print(f"Bounds:      {bounds}")
        print(f"CRS:         {crs}")

    # -----------------------------------------------------
    # HANDLE MISSING VALUES
    # -----------------------------------------------------

    missing_mask = data == MISSING_VALUE

    missing_count = int(missing_mask.sum())
    total_count = data.size

    print("\nData quality")
    print("-" * 40)
    print(f"Total cells:     {total_count:,}")
    print(f"Missing cells:   {missing_count:,}")
    print(
        f"Missing percent: "
        f"{missing_count / total_count * 100:.2f}%"
    )

    # -----------------------------------------------------
    # CONVERT TO MILLIMETERS
    # -----------------------------------------------------

    rainfall_mm = data.astype(np.float32)

    rainfall_mm[missing_mask] = np.nan

    rainfall_mm = rainfall_mm / SCALE_FACTOR

    valid = rainfall_mm[np.isfinite(rainfall_mm)]

    if len(valid) == 0:
        raise ValueError(
            "No valid rainfall values found in the raster."
        )

    print("\nRainfall statistics")
    print("-" * 40)
    print(f"Minimum:  {np.min(valid):.2f} mm")
    print(f"Maximum:  {np.max(valid):.2f} mm")
    print(f"Mean:     {np.mean(valid):.2f} mm")
    print(f"Median:   {np.median(valid):.2f} mm")

    # -----------------------------------------------------
    # CREATE GRID COORDINATES
    # -----------------------------------------------------

    rows, cols = np.indices(rainfall_mm.shape)

    xs, ys = rasterio.transform.xy(
        transform,
        rows,
        cols,
        offset="center"
    )

    longitude = np.asarray(xs)
    latitude = np.asarray(ys)

    # -----------------------------------------------------
    # CREATE DATAFRAME
    # -----------------------------------------------------

    df = pd.DataFrame({
        "date": OBSERVATION_DATE,
        "latitude": latitude.ravel(),
        "longitude": longitude.ravel(),
        "rainfall_mm": rainfall_mm.ravel(),
    })

    # -----------------------------------------------------
    # REMOVE MISSING PIXELS
    # -----------------------------------------------------

    df = df.dropna(subset=["rainfall_mm"]).copy()

    # -----------------------------------------------------
    # METADATA
    # -----------------------------------------------------

    df["source"] = "NASA_GPM_IMERG_EARLY"
    df["product_version"] = "V07C"
    df["accumulation_period"] = "1day"
    df["scale_factor"] = SCALE_FACTOR
    df["missing_value"] = MISSING_VALUE

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    df.to_csv(
        OUTPUT,
        index=False
    )

    # -----------------------------------------------------
    # OUTPUT SUMMARY
    # -----------------------------------------------------

    print("\nOutput")
    print("-" * 40)
    print(f"Observation date: {OBSERVATION_DATE}")
    print(f"Rows saved:       {len(df):,}")
    print(f"File:             {OUTPUT}")

    print("\nOutput columns:")
    print(df.columns.tolist())

    print("\nSample:")
    print(df.head(10).to_string(index=False))

    print("\n" + "=" * 60)
    print("IMERG INGESTION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()