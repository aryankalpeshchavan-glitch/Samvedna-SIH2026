import os
import re
import pandas as pd


EVENT_TARGET_FILE = r"data\processed\events\landslide_event_targets.csv"
EVENT_FILE = r"data\processed\audit\real_landslide_events.csv"

OUTPUT_FILE = r"data\processed\events\real_event_rainfall_joined.csv"


print("\n==============================================")
print(" CRISISCORE - STEP 4 EVENT + RAINFALL JOIN")
print("==============================================")


# ------------------------------------------------------------
# Load files
# ------------------------------------------------------------

targets = pd.read_csv(EVENT_TARGET_FILE)
events = pd.read_csv(EVENT_FILE)

print("\nTarget rows:", len(targets))
print("Real events:", len(events))


# ------------------------------------------------------------
# Parse event date
# ------------------------------------------------------------

def parse_date(value):

    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()

    # Example: 15-16 May 2022
    match = re.fullmatch(
        r"\d{1,2}\s*[-–]\s*(\d{1,2})\s+"
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

    return pd.NaT


events["event_date"] = events["date"].apply(parse_date)


dated_events = events[
    events["event_date"].notna()
].copy()


print("\nDated events:", len(dated_events))

print(
    dated_events[
        ["event_id", "event_date", "state", "district"]
    ].to_string(index=False)
)


# ------------------------------------------------------------
# Prepare target data
# ------------------------------------------------------------

targets["date"] = pd.to_datetime(
    targets["date"],
    errors="coerce"
)


targets["state_key"] = (
    targets["state"]
    .astype(str)
    .str.strip()
    .str.upper()
)


targets["district_key"] = (
    targets["district"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# ------------------------------------------------------------
# Select real positive rows
# ------------------------------------------------------------

positive = targets[
    (targets["landslide_24h"] == 1)
    |
    (targets["landslide_48h"] == 1)
    |
    (targets["landslide_72h"] == 1)
].copy()


print("\nPositive target rows:", len(positive))


# ------------------------------------------------------------
# Join positive rows with dated events
# ------------------------------------------------------------

joined_rows = []


for _, event in dated_events.iterrows():

    state = str(event["state"]).strip().upper()

    district = str(event["district"]).strip().lower()

    event_date = event["event_date"]


    matching = positive[
        (positive["state_key"] == state)
        &
        (positive["district_key"] == district)
    ].copy()


    for _, row in matching.iterrows():

        output = row.to_dict()

        output["event_id"] = event["event_id"]

        output["event_date"] = event_date

        output["event_state"] = event["state"]

        output["event_district"] = event["district"]

        output["hours_before_event"] = (
            event_date - row["date"]
        ).total_seconds() / 3600

        joined_rows.append(output)


# ------------------------------------------------------------
# Create output
# ------------------------------------------------------------

joined = pd.DataFrame(joined_rows)


print("\n==============================================")
print("             JOIN SUMMARY")
print("==============================================")


print("Joined rows:", len(joined))


if len(joined) > 0:

    print(
        "Unique events:",
        joined["event_id"].nunique()
    )

    print("\nJoined data:")

    columns = [
        "event_id",
        "event_date",
        "date",
        "event_state",
        "event_district",
        "rainfall_mm",
        "rainfall_24h",
        "rainfall_3day",
        "rainfall_7day",
        "landslide_24h",
        "landslide_48h",
        "landslide_72h",
        "hours_before_event"
    ]

    columns = [
        c for c in columns
        if c in joined.columns
    ]

    print(
        joined[columns]
        .sort_values("date")
        .to_string(index=False)
    )


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


joined.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nOutput:")
print(OUTPUT_FILE)


print("\n==============================================")
print("             STEP 4 COMPLETE")
print("==============================================")