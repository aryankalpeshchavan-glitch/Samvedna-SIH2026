import geopandas as gpd
import os

file_path = "data/raw/boundaries/india_districts.geojson"

print("=" * 60)
print("DISTRICT BOUNDARY INSPECTION")
print("=" * 60)

print("\nFile:")
print(os.path.abspath(file_path))

if not os.path.exists(file_path):
    print("ERROR: File not found!")
    exit()

print("\nLoading...")

gdf = gpd.read_file(file_path)

print("\nNumber of records:", len(gdf))

print("\nColumns:")
print(gdf.columns.tolist())

print("\nCRS:")
print(gdf.crs)

print("\nGeometry types:")
print(gdf.geometry.geom_type.value_counts())

print("\nNull geometries:")
print(gdf.geometry.isna().sum())

print("\nFirst 5 records:")
print(gdf.head().to_string())

print("\n" + "=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)