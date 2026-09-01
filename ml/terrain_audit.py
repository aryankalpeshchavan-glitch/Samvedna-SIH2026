import os


DATA_DIR = r"data"


TERRAIN_KEYWORDS = [
    "terrain",
    "dem",
    "elevation",
    "slope",
    "aspect",
    "susceptibility",
    "landcover",
    "ndvi"
]


print("\n==============================================")
print(" CRISISCORE - STEP 9 TERRAIN AUDIT")
print("==============================================")


found = []


for root, dirs, files in os.walk(DATA_DIR):

    for filename in files:

        name = filename.lower()

        if any(
            keyword in name
            for keyword in TERRAIN_KEYWORDS
        ):

            found.append(
                os.path.join(root, filename)
            )


print("\nTerrain-related files found:")

if found:

    for file in found:
        print(file)

else:

    print("NONE")


print("\n==============================================")
print("             TERRAIN STATUS")
print("==============================================")


if not found:

    print("""
STATUS: NOT AVAILABLE

Current ML features:
- Rainfall
- Rainfall accumulation
- Rainfall lag features
- Heavy rainfall flags

Terrain features are NOT currently included.

Required future features:
- Elevation
- Slope
- Aspect
- Land cover / vegetation
- Landslide susceptibility

The system will continue using rainfall-based
early warning until terrain data is integrated.
""")

else:

    print("""
Terrain-related data is available.

Further inspection is required before integration.
""")


print("==============================================")
print("       STEP 9 TERRAIN AUDIT COMPLETE")
print("==============================================")