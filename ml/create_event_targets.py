from pathlib import Path
import re
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

GSI_FILE = Path(
    "data/processed/landslide/gsi_field_validated_inventory_v2.csv"
)

RAINFALL_FILE = Path(
    "data/processed/rainfall/ml_training_dataset.csv"
)

OUTPUT_FILE = Path(
    "data/processed/events/landslide_event_targets.csv"
)

NER_STATES = {
    "ASSAM",
    "ARUNACHAL PRADESH",
    "MANIPUR",
    "MEGHALAYA",
    "MIZORAM",
    "NAGALAND",
    "SIKKIM",
    "TRIPURA",
}

START_DATE = pd.Timestamp("2015-01-01")
END_DATE = pd.Timestamp("2025-12-31")


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_state(x):
    if pd.isna(x):
        return ""
    return str(x).strip().upper()


def normalize_district(x):
    if pd.isna(x):
        return ""

    s = str(x).strip().lower()

    # Basic punctuation/spacing normalization
    s = s.replace("–", "-")
    s = s.replace("—", "-")
    s = re.sub(r"\s+", " ", s)

    # Known safe spelling/format variants
    aliases = {
        "dima hasao (n.c. hills)": "dima hasao",
        "ri-bhoi": "ribhoi",
        "eastern-west khasi hill": "eastern west khasi hills",
        "siaha": "saiha",

        # Sikkim historical/name variants
        "east sikkim": "east district",
        "east sikkim (near kaabi)": "east district",
        "gangtok district": "east district",
        "pakyong": "east district",

        "north sikkim": "north district",
        "mangan": "north district",

        "south sikkim": "south district",
        "namchi": "south district",

        "west sikkim": "west district",
        "gyalshing": "west district",
        "geyzing": "west district",
        "soreng": "west district",
    }

    return aliases.get(s, s)


# ============================================================
# EXACT-DATE PARSER
# ============================================================

MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
    r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
    r"Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)

EXACT_DATE_PATTERN = re.compile(
    rf"\b"
    rf"(\d{{1,2}})(?:st|nd|rd|th)?"
    rf"\s+"
    rf"({MONTH_PATTERN})\.?"
    rf"\s+"
    rf"(20\d{{2}})"
    rf"\b",
    re.IGNORECASE,
)


def parse_exact_date(history):
    """
    Extract one defensible exact calendar date.

    We deliberately reject:
      - date ranges
      - month-only dates
      - year-only dates
      - descriptive/reactivation histories containing
        multiple historical dates

    If a string contains a clear exact date plus a time,
    the date is accepted.
    """

    if pd.isna(history):
        return pd.NaT

    text = str(history).strip()

    if not text or text.lower() in {"nan", "nil", "na", "n/a"}:
        return pd.NaT

    # Reject explicit ranges.
    if re.search(
        r"\d{1,2}(?:st|nd|rd|th)?\s*[-–—]\s*"
        r"\d{1,2}(?:st|nd|rd|th)?",
        text,
        re.IGNORECASE,
    ):
        return pd.NaT

    if re.search(
        r"\d{1,2}(?:st|nd|rd|th)?\s+(?:to|-|–|—)\s*"
        r"\d{1,2}",
        text,
        re.IGNORECASE,
    ):
        return pd.NaT

    matches = list(EXACT_DATE_PATTERN.finditer(text))

    # Require exactly one date occurrence.
    if len(matches) != 1:
        return pd.NaT

    match = matches[0]

    day = int(match.group(1))
    month = match.group(2)
    year = int(match.group(3))

    # Convert month name safely.
    try:
        date_text = f"{day} {month} {year}"
        return pd.to_datetime(date_text, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("CRISISCORE — GSI EVENT TARGET BUILDER")
print("=" * 70)

print("\nLoading GSI inventory...")
gsi = pd.read_csv(GSI_FILE)

print("GSI rows:", len(gsi))

print("\nLoading rainfall dataset...")
rain = pd.read_csv(RAINFALL_FILE)

print("Rainfall rows:", len(rain))


# ============================================================
# NORMALIZE GSI
# ============================================================

gsi["state_key"] = gsi["state"].apply(normalize_state)
gsi["district_key"] = gsi["district"].apply(normalize_district)

gsi = gsi[gsi["state_key"].isin(NER_STATES)].copy()

print("\nNER GSI rows:", len(gsi))


# ============================================================
# PARSE EVENT DATES
# ============================================================

print("\nParsing GSI history dates...")

gsi["event_date"] = gsi["history"].apply(parse_exact_date)

print(
    "Exact-date records:",
    gsi["event_date"].notna().sum()
)

# Keep only dates inside rainfall training period.
gsi = gsi[
    gsi["event_date"].notna()
    & (gsi["event_date"] >= START_DATE)
    & (gsi["event_date"] <= END_DATE)
].copy()

print(
    "Exact-date records inside 2015-2025:",
    len(gsi)
)


# ============================================================
# NORMALIZE RAINFALL DATA
# ============================================================

rain["date"] = pd.to_datetime(
    rain["date"],
    errors="coerce"
)

rain["state_key"] = rain["state"].apply(normalize_state)
rain["district_key"] = rain["district"].apply(normalize_district)

rain = rain[
    rain["state_key"].isin(NER_STATES)
].copy()


# ============================================================
# REMOVE OLD PROXY COLUMNS
# ============================================================

proxy_columns = [
    "rainfall_risk_score",
    "risk_class",
    "risk_label",
]

proxy_columns_present = [
    c for c in proxy_columns
    if c in rain.columns
]

if proxy_columns_present:
    print(
        "\nDropping legacy proxy columns:",
        proxy_columns_present
    )

    rain = rain.drop(
        columns=proxy_columns_present
    )


# ============================================================
# BUILD EVENT-DAY LOOKUP
# ============================================================

event_keys = (
    gsi[
        [
            "state_key",
            "district_key",
            "event_date",
        ]
    ]
    .dropna(subset=["event_date"])
    .drop_duplicates()
)

print(
    "\nUnique GSI state+district+event-date combinations:",
    len(event_keys)
)


# ============================================================
# CREATE FUTURE TARGETS
# ============================================================

print("\nCreating 24/48/72 hour targets...")

rain["landslide_24h"] = 0
rain["landslide_48h"] = 0
rain["landslide_72h"] = 0


# ------------------------------------------------------------
# 24h:
# Prediction date T is positive if an event occurs on T+1.
# ------------------------------------------------------------

events_24 = event_keys.copy()
events_24["prediction_date"] = (
    events_24["event_date"] - pd.Timedelta(days=1)
)

keys_24 = set(
    zip(
        events_24["state_key"],
        events_24["district_key"],
        events_24["prediction_date"],
    )
)


# ------------------------------------------------------------
# 48h:
# Prediction date T is positive if an event occurs
# on T+1 OR T+2.
# ------------------------------------------------------------

events_48_a = event_keys.copy()
events_48_a["prediction_date"] = (
    events_48_a["event_date"] - pd.Timedelta(days=1)
)

events_48_b = event_keys.copy()
events_48_b["prediction_date"] = (
    events_48_b["event_date"] - pd.Timedelta(days=2)
)

keys_48 = set(
    zip(
        events_48_a["state_key"],
        events_48_a["district_key"],
        events_48_a["prediction_date"],
    )
)

keys_48.update(
    zip(
        events_48_b["state_key"],
        events_48_b["district_key"],
        events_48_b["prediction_date"],
    )
)


# ------------------------------------------------------------
# 72h:
# Prediction date T is positive if an event occurs
# on T+1, T+2 OR T+3.
# ------------------------------------------------------------

keys_72 = set()

for offset in [1, 2, 3]:
    temp = event_keys.copy()

    temp["prediction_date"] = (
        temp["event_date"]
        - pd.Timedelta(days=offset)
    )

    keys_72.update(
        zip(
            temp["state_key"],
            temp["district_key"],
            temp["prediction_date"],
        )
    )


# ============================================================
# APPLY TARGETS
# ============================================================

rain_keys = list(
    zip(
        rain["state_key"],
        rain["district_key"],
        rain["date"],
    )
)

rain["landslide_24h"] = [
    int(k in keys_24)
    for k in rain_keys
]

rain["landslide_48h"] = [
    int(k in keys_48)
    for k in rain_keys
]

rain["landslide_72h"] = [
    int(k in keys_72)
    for k in rain_keys
]


# ============================================================
# TARGET SUMMARY
# ============================================================

print("\nTARGET DISTRIBUTIONS")

for col in [
    "landslide_24h",
    "landslide_48h",
    "landslide_72h",
]:
    counts = rain[col].value_counts().sort_index()

    print(f"\n{col}")
    print(counts.to_string())


# ============================================================
# MATCHING SUMMARY
# ============================================================

rain_key_set = set(
    zip(
        rain["state_key"],
        rain["district_key"],
    )
)

gsi_key_set = set(
    zip(
        gsi["state_key"],
        gsi["district_key"],
    )
)

print("\n" + "=" * 70)
print("MATCHING SUMMARY")
print("=" * 70)

print(
    "GSI state+district keys:",
    len(gsi_key_set)
)

print(
    "Rainfall state+district keys:",
    len(rain_key_set)
)

print(
    "Matching keys:",
    len(gsi_key_set & rain_key_set)
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

rain.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:")
print(OUTPUT_FILE)

print("\nFinal shape:", rain.shape)

print("\nFinal columns:")
print("\n".join(rain.columns))

print("\nDONE.")