import xarray as xr
import os

rainfall_folder = "data/raw/rainfall"

files = sorted([
    f for f in os.listdir(rainfall_folder)
    if f.lower().endswith(".nc")
])

print("========== RAINFALL FILES ==========")
print("Total files:", len(files))

for file in files:
    file_path = os.path.join(rainfall_folder, file)

    print("\n----------------------------------------")
    print("File:", file)

    try:
        data = xr.open_dataset(file_path)

        print("Time:", str(data.TIME.values[0]), "to", str(data.TIME.values[-1]))
        print("Number of days:", len(data.TIME))
        print("Latitude:", float(data.LATITUDE.min()), "to", float(data.LATITUDE.max()))
        print("Longitude:", float(data.LONGITUDE.min()), "to", float(data.LONGITUDE.max()))
        print("Rainfall variable:", "RAINFALL")

        data.close()

    except Exception as e:
        print("ERROR:", e)

print("\n========== INSPECTION COMPLETE ==========")