"""
CRISISCORE - shared History-cell classifier for the GSI landslide inventory.

Purpose
-------
Classify the raw 'History' cell of a GSI inventory record into coarse audit
buckets so that date coverage can be reported honestly.  This is an
AUDIT-ONLY classification: it does NOT produce a final event date.  Strict
date parsing (with start/end/precision) is a separate, later pipeline stage
that operates only on records that genuinely contain a usable date.

Buckets
-------
EXACT_DATE   - single calendar day with month and year     e.g. "16 May 2016",
              "08.08.2018", "01 July 2007 (03:50 hrs)"
DATE_RANGE   - multi-day or multi-year range               e.g. "16th-17th June 2013",
              "2014-2018", "15-16 May 2022"
MONTH_DATE   - month + year, no exact day                  e.g. "October 2021",
              "1st week of January 2021"
YEAR         - year only (with or without trailing period) e.g. "2018.", "1992"
DESCRIPTIVE  - prose / other                               e.g. "Monsoon, 2024"
NA_OR_EMPTY  - NA, NIL, N/A, -, --, empty
"""
import re

_MONTHS = (
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?"
)

# 08.08.2018 / 15-08-2018 / 16/08/2018 / 08.08.18
_EXACT_NUMERIC = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s*[./-]\s*\d{1,2}(?:st|nd|rd|th)?\s*[./-]\s*"
    r"(?:19|20)?\s*\d{2}\b",
    re.IGNORECASE,
)

# 16 May 2016 / 15th August, 2018 / 01 July 2007 (03:50 hrs)
_EXACT_WORDS = re.compile(
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})\w*\s*(?:,\s*)?"
    rf"(?:19|20)\d{{2}}\b",
    re.IGNORECASE,
)

# 16th-17th June 2013 / 08th and 9th August 2018 / 24th to 26th Sep, 2020
_DAY_RANGE_WORDS = re.compile(
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s*(?:-|–|to|and|&|,\s*)\s*"
    rf"\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})\w*\s*(?:,\s*)?"
    rf"(?:19|20)\d{{2}}\b",
    re.IGNORECASE,
)

# 2014-2018 / 2016-17 / 2014 to 2018 / 2014-2022
_YEAR_RANGE = re.compile(
    r"\b(?:19|20)\d{2}\s*(?:-|–|to)\s*(?:19|20)?\d{2}\b",
    re.IGNORECASE,
)

# March 2021 / October 2021 (month + year, no day)
_MONTH_YEAR = re.compile(
    rf"\b(?:{_MONTHS})\w*\s*(?:,\s*)?(?:19|20)\d{{2}}\b",
    re.IGNORECASE,
)

_YEAR_ONLY = re.compile(r"^\s*(?:19|20)\d{2}\s*\.?\s*$")

_NA_TOKENS = {"NA", "NIL", "N/A", "-", "--", "---", ".", "—", "NONE"}


def _norm_token(s: str) -> str:
    """Collapse whitespace and uppercase a raw cell for NA detection."""
    return "".join(ch for ch in s if not ch.isspace()).upper()


def classify_history(value) -> tuple:
    """Return (bucket, cleaned_representation).

    bucket is one of:
      EXACT_DATE, DATE_RANGE, MONTH_DATE, YEAR, DESCRIPTIVE, NA_OR_EMPTY
    """
    if value is None:
        return "NA_OR_EMPTY", ""
    s = str(value).strip()
    if not s:
        return "NA_OR_EMPTY", s
    if _norm_token(s) in _NA_TOKENS:
        return "NA_OR_EMPTY", s

    # Order matters: NA first, then ranges, then exact days, then month,
    # then year-only, then descriptive.
    if _DAY_RANGE_WORDS.search(s):
        return "DATE_RANGE", s
    if _YEAR_RANGE.search(s):
        return "DATE_RANGE", s
    if _EXACT_WORDS.search(s) or _EXACT_NUMERIC.search(s):
        return "EXACT_DATE", s
    if _MONTH_YEAR.search(s):
        return "MONTH_DATE", s
    if _YEAR_ONLY.match(s):
        return "YEAR", s
    return "DESCRIPTIVE", s