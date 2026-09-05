import os
import re
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

GSI_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "landslide",
    "gsi_ner_exact_date_events.csv"
)

RAINFALL_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "rainfall",
    "risk_prediction_dataset.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "ml",
    "real_landslide_event_dataset.csv"
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = value.replace("&", "and")

    value = re.sub(
        r"[^a-z0-9\s\-]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def normalize_state(value):

    value = clean_text(value)

    aliases = {
        "arunachal": "arunachal pradesh",
        "arunachal pradesh": "arunachal pradesh",
        "assam": "assam",
        "manipur": "manipur",
        "meghalaya": "meghalaya",
        "mizoram": "mizoram",
        "nagaland": "nagaland",
        "sikkim": "sikkim",
        "tripura": "tripura",
    }

    return aliases.get(
        value,
        value
    )


def normalize_district(value):

    value = clean_text(value)

    aliases = {

        # Assam
        "kamrup (metro)": "kamrup metropolitan",
        "kamrup metro": "kamrup metropolitan",
        "kamrup metropolitan": "kamrup metropolitan",

        "dima hasao (n.c. hills)": "dima hasao",
        "dima hasao (nc hills)": "dima hasao",
        "dima hasao": "dima hasao",

        # Manipur
        "tamenlong": "tamenglong",
        "tamenglong district": "tamenglong",

        # Meghalaya
        "ri-bhoi": "ri bhoi",
        "ri bhoi": "ri bhoi",

        # Mizoram
        "siaha": "saiha",
        "saiha": "saiha",

        # Sikkim
        "north sikkim": "mangan",
        "mangan": "mangan",

        "east sikkim": "gangtok",
        "gangtok": "gangtok",
        "gangtok district": "gangtok",

        "south sikkim": "namchi",
        "namchi": "namchi",

        "west sikkim": "gyalshing",
        "west district": "gyalshing",
        "gyalshing": "gyalshing",

    }

    return aliases.get(
        value,
        value
    )


# ============================================================
# START
# ============================================================

print("=" * 70)
print("BUILDING REAL GSI EVENT DATASET")
print("=" * 70)


# ============================================================
# 1. LOAD GSI
# ============================================================

print("\n[1] Loading GSI events...")

if not os.path.exists(GSI_FILE):

    raise FileNotFoundError(
        f"GSI file not found:\n{GSI_FILE}"
    )

gsi = pd.read_csv(
    GSI_FILE
)

print(
    "GSI rows:",
    len(gsi)
)


# ============================================================
# 2. LOAD RAINFALL
# ============================================================

print("\n[2] Loading rainfall dataset...")

if not os.path.exists(RAINFALL_FILE):

    raise FileNotFoundError(
        f"Rainfall file not found:\n{RAINFALL_FILE}"
    )

rainfall = pd.read_csv(
    RAINFALL_FILE
)

print(
    "Rainfall rows:",
    len(rainfall)
)


# ============================================================
# 3. PREPARE DATES
# ============================================================

print("\n[3] Preparing dates...")

gsi["event_date"] = pd.to_datetime(
    gsi["event_date"],
    errors="coerce"
)

rainfall["date"] = pd.to_datetime(
    rainfall["date"],
    errors="coerce"
)


# Only 2015-2025 because rainfall dataset covers this period
gsi = gsi[
    (gsi["event_date"].dt.year >= 2015) &
    (gsi["event_date"].dt.year <= 2025)
].copy()


print(
    "GSI events 2015-2025:",
    len(gsi)
)


# ============================================================
# 4. NORMALIZE KEYS
# ============================================================

print("\n[4] Normalizing state/district names...")


gsi["state_key"] = gsi["state"].apply(
    normalize_state
)

gsi["district_key"] = gsi["district"].apply(
    normalize_district
)


rainfall["state_key"] = rainfall["state"].apply(
    normalize_state
)

rainfall["district_key"] = rainfall["district"].apply(
    normalize_district
)


print("\nSample normalized GSI districts:")

print(
    gsi[
        [
            "state",
            "district",
            "district_key"
        ]
    ]
    .drop_duplicates()
    .head(30)
    .to_string(index=False)
)


# ============================================================
# 5. CHECK RAINFALL COLUMNS
# ============================================================

print("\n[5] Checking rainfall columns...")


required_rainfall = [
    "date",
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
]


missing = [
    col
    for col in required_rainfall
    if col not in rainfall.columns
]


if missing:

    raise ValueError(
        "Missing rainfall columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# 6. CREATE CLEAN RAINFALL TABLE
# ============================================================

rainfall_small = rainfall[
    required_rainfall
    + [
        "state_key",
        "district_key"
    ]
].copy()


# Ensure one rainfall record per
# date + state + district

rainfall_small = rainfall_small.drop_duplicates(
    subset=[
        "date",
        "state_key",
        "district_key"
    ],
    keep="first"
)


print(
    "Unique rainfall rows:",
    len(rainfall_small)
)


# ============================================================
# 7. CREATE GSI JOIN TABLE
# ============================================================

gsi_small = gsi[
    [
        "event_id",
        "event_date",
        "state",
        "district",
        "latitude",
        "longitude",
        "state_key",
        "district_key"
    ]
].copy()


# ============================================================
# 8. JOIN
# ============================================================

print("\n[6] Joining GSI events with rainfall...")


joined = gsi_small.merge(
    rainfall_small,
    left_on=[
        "event_date",
        "state_key",
        "district_key"
    ],
    right_on=[
        "date",
        "state_key",
        "district_key"
    ],
    how="inner",
    validate="many_to_one",
    suffixes=(
        "_gsi",
        "_rainfall"
    )
)


print(
    "\nREAL EVENTS JOINED TO RAINFALL:",
    len(joined)
)


# ============================================================
# 9. REMOVE JOIN-ONLY COLUMNS
# ============================================================

joined = joined.drop(
    columns=[
        "date",
        "state_key",
        "district_key",
        "state_rainfall",
        "district_rainfall"
    ],
    errors="ignore"
)


# ============================================================
# 10. CREATE REAL EVENT LABEL
# ============================================================

print("\n[7] Creating real landslide labels...")


# Every row is a confirmed GSI event.
joined["landslide_event"] = 1


# ============================================================
# 11. VERIFY STATE/DISTRICT
# ============================================================

# Because state/district from GSI were explicitly retained,
# these must exist here.

if "state" not in joined.columns:

    print("\nAVAILABLE COLUMNS AFTER JOIN:")

    print(
        "\n".join(
            joined.columns
        )
    )

    raise ValueError(
        "GSI state column was not preserved after join."
    )


if "district" not in joined.columns:

    print("\nAVAILABLE COLUMNS AFTER JOIN:")

    print(
        "\n".join(
            joined.columns
        )
    )

    raise ValueError(
        "GSI district column was not preserved after join."
    )


# ============================================================
# 12. FINAL COLUMNS
# ============================================================

final_columns = [
    "event_id",
    "event_date",
    "state",
    "district",
    "latitude",
    "longitude",
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "heavy_rain_flag",
    "very_heavy_rain_flag",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
    "landslide_event"
]


# ============================================================
# 13. FINAL COLUMN CHECK
# ============================================================

missing_final = [
    col
    for col in final_columns
    if col not in joined.columns
]


if missing_final:

    print("\nAVAILABLE COLUMNS:")

    print(
        "\n".join(
            joined.columns
        )
    )

    raise ValueError(
        "\nMissing final columns:\n"
        + "\n".join(missing_final)
    )


final = joined[
    final_columns
].copy()


# ============================================================
# 14. NUMERIC CLEANING
# ============================================================

numeric_columns = [
    "latitude",
    "longitude",
    "rainfall_mm",
    "rainfall_24h",
    "rainfall_3day",
    "rainfall_7day",
    "rainfall_14day",
    "rainfall_30day",
    "rainfall_previous_day",
    "rainfall_2day_lag",
    "rainfall_3day_lag",
]


for column in numeric_columns:

    final[column] = pd.to_numeric(
        final[column],
        errors="coerce"
    )


# ============================================================
# 15. CLEAN FLAGS
# ============================================================

final["heavy_rain_flag"] = (
    pd.to_numeric(
        final["heavy_rain_flag"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)


final["very_heavy_rain_flag"] = (
    pd.to_numeric(
        final["very_heavy_rain_flag"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
)


final["landslide_event"] = 1


# ============================================================
# 16. REMOVE DUPLICATE EVENTS
# ============================================================

before = len(final)


final = final.drop_duplicates(
    subset=["event_id"],
    keep="first"
)


removed = before - len(final)


print(
    "\nDuplicate events removed:",
    removed
)


# ============================================================
# 17. SAVE
# ============================================================

print("\n[8] Saving dataset...")


os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


final.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 18. FINAL REPORT
# ============================================================

print("\n" + "=" * 70)
print("REAL GSI EVENT DATASET COMPLETE")
print("=" * 70)


print(
    "\nOutput file:",
    OUTPUT_FILE
)


print(
    "Rows:",
    len(final)
)


print(
    "Columns:",
    len(final.columns)
)


print("\nFINAL COLUMNS:")

print(
    "\n".join(
        final.columns
    )
)


print("\nLANDSLIDE EVENT LABEL:")

print(
    final[
        "landslide_event"
    ].value_counts()
    .to_string()
)


print("\nJOINED EVENTS BY YEAR:")

print(
    final[
        "event_date"
    ]
    .dt.year
    .value_counts()
    .sort_index()
    .to_string()
)


print("\nJOINED EVENTS BY STATE:")

print(
    final[
        "state"
    ]
    .value_counts()
    .to_string()
)


print("\nSAMPLE:")

print(
    final.head(10).to_string(
        index=False
    )
)


print("\n" + "=" * 70)
print("SUCCESS")
print("=" * 70)