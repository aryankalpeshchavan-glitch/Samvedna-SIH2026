import pandas as pd
import geopandas as gpd

rainfall_file = r"data\processed\rainfall\ner_district_rainfall.csv"
boundary_file = r"data\raw\boundaries\india_district.geojson"

ner_states = [
    "ARUNACHAL PRADESH",
    "ASSAM",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "SIKKIM",
    "TRIPURA"
]

print("Loading rainfall data...")
rainfall = pd.read_csv(rainfall_file)

print("Loading boundaries...")
gdf = gpd.read_file(boundary_file)

# Standardize state names
gdf["stname"] = gdf["stname"].astype(str).str.strip().str.upper()

# Filter NER
ner_boundary = gdf[gdf["stname"].isin(ner_states)].copy()

# Districts from boundary file
boundary_districts = set(
    ner_boundary["dtname"].astype(str).str.strip()
)

# Districts present in rainfall output
rainfall_districts = set(
    rainfall["district"].astype(str).str.strip()
)

missing = sorted(boundary_districts - rainfall_districts)

print("\n========== MISSING DISTRICTS ==========")
print("Boundary districts:", len(boundary_districts))
print("Rainfall districts:", len(rainfall_districts))
print("Missing districts:", len(missing))

for district in missing:
    state = ner_boundary[
        ner_boundary["dtname"].astype(str).str.strip() == district
    ]["stname"].iloc[0]

    print(f"{state} -> {district}")

print("\n========== COMPLETE ==========")