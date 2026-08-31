import pandas as pd

# Input file
input_file = r"data\processed\rainfall\ner_district_rainfall.csv"

print("Loading district rainfall data...")

df = pd.read_csv(input_file)

print("\n========== BASIC INFORMATION ==========")
print("Rows:", len(df))
print("Districts:", df["district"].nunique())
print("States:", df["state"].nunique())

# 7 districts to check
districts = [
    "Anjaw",
    "Changlang",
    "Upper Dibang Valley",
    "East Kameng",
    "East Siang",
    "Kurung Kumey",
    "Lohit"
]

print("\n========== 7-DISTRICT CHECK ==========")

for district in districts:

    temp = df[df["district"].str.strip().str.lower() ==
              district.lower()]

    print("\nDistrict:", district)
    print("Rows:", len(temp))

    if len(temp) > 0:
        print("State:", temp["state"].iloc[0])
        print("Date range:",
              temp["date"].min(),
              "to",
              temp["date"].max())

        print("Missing values:")
        print(temp.isnull().sum().to_string())

        print("\nRainfall statistics:")
        print(
            temp[
                [
                    "rainfall_mm",
                    "rainfall_24h",
                    "rainfall_3day",
                    "rainfall_7day"
                ]
            ].describe().round(2).to_string()
        )

    else:
        print("WARNING: District not found!")

print("\n========== COMPLETE ==========")