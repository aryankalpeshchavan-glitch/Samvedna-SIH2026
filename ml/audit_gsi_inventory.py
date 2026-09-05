import pandas as pd

FILE = r"data\processed\landslide\gsi_field_validated_inventory.csv"

NER_STATES = [
    "ARUNACHAL PRADESH",
    "ASSAM",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "SIKKIM",
    "TRIPURA"
]

print("=" * 60)
print("CRISISCORE - GSI INVENTORY AUDIT")
print("=" * 60)

df = pd.read_csv(FILE)

print("\nTotal rows:", len(df))

print("\nColumns:")
print(list(df.columns))

print("\nMissing values:")
print(df.isna().sum().to_string())

print("\nExact duplicates:", df.duplicated().sum())

print("\nAll states:")
print(df["state"].value_counts().to_string())

ner = df[
    df["state"].isin(NER_STATES)
].copy()

print("\n" + "=" * 60)
print("NER INVENTORY")
print("=" * 60)

print("NER rows:", len(ner))

print("\nNER states:")
print(ner["state"].value_counts().to_string())

print("\nNER districts:", ner["district"].nunique())

valid_coords = (
    pd.to_numeric(ner["latitude"], errors="coerce").between(-90, 90)
    &
    pd.to_numeric(ner["longitude"], errors="coerce").between(-180, 180)
)

print("\nValid NER coordinates:", valid_coords.sum())
print("Invalid NER coordinates:", (~valid_coords).sum())

print("\nHistory values:")
print(
    ner["history"]
    .value_counts(dropna=False)
    .head(30)
    .to_string()
)

OUTPUT = r"data\processed\landslide\gsi_ner_inventory_raw.csv"

ner.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("\nSaved:")
print(OUTPUT)

print("\n" + "=" * 60)
print("STEP 2 COMPLETE")
print("=" * 60)