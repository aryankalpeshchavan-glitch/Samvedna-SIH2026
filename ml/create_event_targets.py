import os
import re
import pandas as pd


EVENT_FILE = r"data\processed\audit\real_landslide_events.csv"
RAINFALL_FILE = r"data\processed\rainfall\ml_training_dataset.csv"

OUTPUT_DIR = r"data\processed\events"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "landslide_event_targets.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("\n==============================================")
print("   CRISISCORE - STEP 3 TARGET CREATION")
print("==============================================")


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading real landslide events...")

events = pd.read_csv(EVENT_FILE)

print("Event rows:", len(events))


print("\nLoading rainfall dataset...")

rainfall = pd.read_csv(RAINFALL_FILE)

print("Rainfall rows:", len(rainfall))


events.columns = events.columns.str.strip().str.lower()
rainfall.columns = rainfall.columns.str.strip().str.lower()


# ============================================================
# DATE PARSER
# ============================================================

def parse_event_date(value):

    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    # 15-16 May 2022
    match = re.fullmatch(
        r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+"
        r"(20\d{2})",
        text,
        flags=re.IGNORECASE
    )

    if match:

        day = match.group(2)
        month = match.group(3)
        year = match.group(4)

        return pd.to_datetime(
            f"{day} {month} {year}",
            errors="coerce"
        )

    # 16 May 2022
    match = re.fullmatch(
        r"(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|"
        r"September|October|November|December)\s+"
        r"(20\d{2})",
        text,
        flags=re.IGNORECASE
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        return pd.to_datetime(
            f"{day} {month} {year}",
            errors="coerce"
        )

    # YYYY-MM-DD
    if re.fullmatch(r"20\d{2}-\d{1,2}-\d{1,2}", text):

        return pd.to_datetime(
            text,
            errors="coerce"
        )

    # DD-MM-YYYY
    match = re.fullmatch(
        r"(\d{1,2})-(\d{1,2})-(20\d{2})",
        text
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        return pd.to_datetime(
            f"{year}-{month}-{day}",
            errors="coerce"
        )

    # DD/MM/YYYY
    match = re.fullmatch(
        r"(\d{1,2})/(\d{1,2})/(20\d{2})",
        text
    )

    if match:

        day = match.group(1)
        month = match.group(2)
        year = match.group(3)

        return pd.to_datetime(
            f"{year}-{month}-{day}",
            errors="coerce"
        )

    # Year only or year range = unusable
    return pd.NaT


# ============================================================
# PARSE EVENTS
# ============================================================

print("\nParsing event dates...")

events["event_date"] = events["date"].apply(
    parse_event_date
)


print("\nEvent date parsing:")

print(
    "Usable event dates:",
    events["event_date"].notna().sum()
)

print(
    "Ambiguous/unusable dates:",
    events["event_date"].isna().sum()
)


print("\nParsed events:")

print(
    events[
        [
            "event_id",
            "date",
            "event_date",
            "state",
            "district"
        ]
    ].to_string(index=False)
)


# ============================================================
# PREPARE RAINFALL
# ============================================================

print("\nPreparing rainfall data...")


rainfall["date"] = pd.to_datetime(
    rainfall["date"],
    errors="coerce"
)


rainfall["state_key"] = (
    rainfall["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)


rainfall["district_key"] = (
    rainfall["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)


events["state_key"] = (
    events["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)


events["district_key"] = (
    events["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)


rainfall = rainfall[
    rainfall["date"].notna()
].copy()


# ============================================================
# TARGET COLUMNS
# ============================================================

rainfall["landslide_24h"] = 0
rainfall["landslide_48h"] = 0
rainfall["landslide_72h"] = 0


# ============================================================
# MATCH EVENTS
# ============================================================

print("\nMatching real landslide events...")

matched_events = 0


for _, event in events.iterrows():

    if pd.isna(event["event_date"]):
        continue


    district = event["district_key"]


    # Skip events without a known district
    if district in ["nan", "none", "", "na"]:
        print(
            "Skipping",
            event["event_id"],
            "- district unavailable"
        )
        continue


    state = event["state_key"]
    event_date = event["event_date"]


    location_mask = (
        (rainfall["state_key"] == state)
        &
        (rainfall["district_key"] == district)
    )


    if not location_mask.any():

        print(
            "No rainfall match:",
            event["event_id"],
            state,
            district
        )

        continue


    # ========================================================
    # EARLY-WARNING TARGET
    #
    # At rainfall date T:
    #
    # 24h = event occurs from T+1 to T+24h
    # 48h = event occurs from T+1 to T+48h
    # 72h = event occurs from T+1 to T+72h
    #
    # Therefore event date itself and preceding rainfall
    # observations become predictors for the event.
    # ========================================================


    # 24-hour target
    mask_24h = (
        location_mask
        &
        (rainfall["date"] >= event_date - pd.Timedelta(days=1))
        &
        (rainfall["date"] < event_date)
    )


    # 48-hour target
    mask_48h = (
        location_mask
        &
        (rainfall["date"] >= event_date - pd.Timedelta(days=2))
        &
        (rainfall["date"] < event_date)
    )


    # 72-hour target
    mask_72h = (
        location_mask
        &
        (rainfall["date"] >= event_date - pd.Timedelta(days=3))
        &
        (rainfall["date"] < event_date)
    )


    rainfall.loc[
        mask_24h,
        "landslide_24h"
    ] = 1


    rainfall.loc[
        mask_48h,
        "landslide_48h"
    ] = 1


    rainfall.loc[
        mask_72h,
        "landslide_72h"
    ] = 1


    matched_events += 1


    print(
        "Matched:",
        event["event_id"],
        "|",
        event["state"],
        "|",
        event["district"],
        "|",
        event_date.date()
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n==============================================")
print("             TARGET SUMMARY")
print("==============================================")


print(
    "\nMatched events:",
    matched_events
)


print(
    "24h positive samples:",
    int(rainfall["landslide_24h"].sum())
)


print(
    "48h positive samples:",
    int(rainfall["landslide_48h"].sum())
)


print(
    "72h positive samples:",
    int(rainfall["landslide_72h"].sum())
)


# ============================================================
# DISTRIBUTION
# ============================================================

for target in [
    "landslide_24h",
    "landslide_48h",
    "landslide_72h"
]:

    print("\n" + target + ":")

    print(
        rainfall[target]
        .value_counts()
        .sort_index()
    )


# ============================================================
# SAVE
# ============================================================

print("\nSaving target dataset...")

rainfall.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nOutput:")
print(OUTPUT_FILE)


print("\n==============================================")
print("          STEP 3 COMPLETE")
print("==============================================")