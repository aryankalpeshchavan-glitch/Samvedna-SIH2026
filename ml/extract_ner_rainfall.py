import xarray as xr
import pandas as pd
import os

# Folder containing IMD rainfall files
rainfall_folder = "data/raw/rainfall"

# Output file
output_file = "data/processed/rainfall/ner_rainfall.csv"

# Approximate NER bounding box
# Latitude: 21.5 to 29.5
# Longitude: 88.0 to 97.5
LAT_MIN = 21.5
LAT_MAX = 29.5
LON_MIN = 88.0
LON_MAX = 97.5

all_data = []

files = sorted([
    f for f in os.listdir(rainfall_folder)
    if f.endswith(".nc")
])

print("Rainfall files found:", len(files))

for file in files:

    file_path = os.path.join(rainfall_folder, file)

    print("\nProcessing:", file)

    # Open IMD dataset
    ds = xr.open_dataset(file_path)

    # Select NER geographic region
    ner = ds.sel(
        LATITUDE=slice(LAT_MIN, LAT_MAX),
        LONGITUDE=slice(LON_MIN, LON_MAX)
    )

    # Convert rainfall grid into a table
    df = ner["RAINFALL"].to_dataframe().reset_index()

    # Rename columns
    df = df.rename(columns={
        "TIME": "date",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "RAINFALL": "rainfall_mm"
    })

    # Keep required columns
    df = df[
        ["date", "latitude", "longitude", "rainfall_mm"]
    ]

    all_data.append(df)

    ds.close()

# Combine all years
final_df = pd.concat(all_data, ignore_index=True)

# Remove missing rainfall values
final_df = final_df.dropna(subset=["rainfall_mm"])

# Sort
final_df = final_df.sort_values(
    ["date", "latitude", "longitude"]
)

# Create output directory if needed
os.makedirs(
    os.path.dirname(output_file),
    exist_ok=True
)

# Save
final_df.to_csv(output_file, index=False)

print("\n========== COMPLETE ==========")
print("Rows:", len(final_df))
print("Output:", output_file)

print("\nDate range:")
print(final_df["date"].min(), "to", final_df["date"].max())

print("\nSample:")
print(final_df.head(10))