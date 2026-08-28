import pandas as pd

file = r"D:\sih project\data\processed\rainfall\ner_district_rainfall.csv"

df = pd.read_csv(file)

districts = [
    "Anjaw",
    "Changlang",
    "Dibang Valley",
    "East Kameng",
    "East Siang",
    "Kurung Kumey",
    "Lohit"
]

print("\n========== 7-DISTRICT CHECK ==========\n")

for district in districts:

    temp = df[df["district"].str.lower() == district.lower()]

    print(f"District: {district}")
    print(f"Rows: {len(temp)}")

    if len(temp) == 0:
        print("WARNING: District not found!")

        if "Dibang" in district:
            print("\nDibang districts actually present:")
            print(
                df[
                    df["district"]
                    .str.contains("Dibang", case=False, na=False)
                ]["district"].unique()
            )

    else:
        print(f"State: {temp['state'].iloc[0]}")
        print(f"Date range: {temp['date'].min()} to {temp['date'].max()}")

        print("Missing values:")
        print(temp.isnull().sum())

    print("-" * 50)

print("\n========== COMPLETE ==========")