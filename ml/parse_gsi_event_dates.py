"""
CRISISCORE - GSI History -> event date parser (STRICT, non-fabricating).

Parses the raw 'history' cell of a GSI inventory record into optional
event dates.  It NEVER invents an exact date from a year-only or range-only
value.  For each record it returns:

  event_date          - datetime.date or None (EXACT_DAY precision only)
  event_date_start    - earliest defensible date (EXACT_DAY, MONTH, YEAR, RANGE)
  event_date_end      - latest defensible date (None for EXACT_DAY)
  date_precision      - EXACT_DAY | MONTH | YEAR | RANGE | UNKNOWN
  date_parse_status   - PARSED | PARTIAL | NONE

Rules (scientific honesty):
  * "2014"            -> YEAR       (event_date None, start 2014-01-01, end 2014-12-31)
  * "2014-2018"       -> RANGE      (event_date None, start 2014-01-01, end 2018-12-31)
  * "October 2021"    -> MONTH      (event_date None, start 2021-10-01, end 2021-10-31)
  * "16 May 2016"     -> EXACT_DAY  (event_date = 2016-05-16, start=end=None)
  * "NA" / ""         -> UNKNOWN    (everything None)
  * "Monsoon, 2024"   -> UNKNOWN    (descriptive: no defensible exact date)

Only EXACT_DAY records are eligible for the 24h/48h/72h supervised target.
"""
import re
from datetime import date

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
    "june": 6, "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}
MONTH_ABBREV = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11,
    "dec": 12,
}


def _month_num(word):
    w = word.lower().rstrip(".")
    if w in MONTHS:
        return MONTHS[w]
    if w in MONTH_ABBREV:
        return MONTH_ABBREV[w]
    return None


def _clean(text):
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text).strip().replace("\u2013", "-").replace("\u2014", "-"))


_MONTH_PAT = r"(jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)"





def parse_event_date(history):
    """Return dict with event_date/start/end/precision/status."""
    hist = _clean(history)
    if not hist or hist.upper() in {"NA", "NIL", "N/A", "-", "--", "—"}:
        return {
            "event_date": None, "event_date_start": None, "event_date_end": None,
            "date_precision": "UNKNOWN", "date_parse_status": "NONE",
        }

    # MULTI-DAY RANGE first: "16th-17th June 2013", "15-16 May 2022",
    # "16 to 17 Aug 2018", "08th and 9th August 2018"
    m = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s*[-–,to&and]+\s*(\d{{1,2}})(?:st|nd|rd|th)?\s+"
        rf"{_MONTH_PAT}[\w.]*\s*,?\s+((?:19|20)\d{{2}})\b",
        hist, flags=re.IGNORECASE,
    )
    if m:
        d1, d2, mon, year = int(m.group(1)), int(m.group(2)), _month_num(m.group(3)), int(m.group(4))
        if 1 <= d1 <= d2 <= 31 and 1 <= mon <= 12:
            try:
                start = date(year, mon, d1)
                end = date(year, mon, d2)
                return {
                    "event_date": start,
                    "event_date_start": start, "event_date_end": end,
                    "date_precision": "RANGE", "date_parse_status": "PARSED",
                }
            except ValueError:
                pass

    # EXACT DAY: full month name + day + year
    m = re.search(
        rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{_MONTH_PAT}[\w.]*\s*,?\s+((?:19|20)\d{{2}})\b",
        hist, flags=re.IGNORECASE,
    )
    if m:
        day, mon, year = int(m.group(1)), _month_num(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= mon <= 12:
            try:
                ev = date(year, mon, day)
                return {
                    "event_date": ev,
                    "event_date_start": ev,
                    "event_date_end": ev,
                    "date_precision": "EXACT_DAY",
                    "date_parse_status": "PARSED",
                }
            except ValueError:
                pass

    # "16.05.2016", "08.08.2018", "15-08-2018", "16/05/2016", "15/8/18"
    m = re.search(r"\b(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*((?:19|20)?\d{2})\b", hist)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        yy = 2000 + y if y < 100 else y
        for day, mon in ((a, b), (b, a)):
            if 1 <= mon <= 12 and 1 <= day <= 31:
                try:
                    ev = date(yy, mon, day)
                    return {
                        "event_date": ev,
                        "event_date_start": ev,
                        "event_date_end": ev,
                        "date_precision": "EXACT_DAY",
                        "date_parse_status": "PARSED",
                    }
                except ValueError:
                    continue

    # MONTH: "October 2021", "July 2018"
    m = re.search(rf"\b{_MONTH_PAT}[\w.]*\s*,?\s+((?:19|20)\d{{2}})\b",
                  hist, flags=re.IGNORECASE)
    if m:
        mon, year = _month_num(m.group(1)), int(m.group(2))
        if 1 <= mon <= 12:
            last = 28 if mon == 2 else (30 if mon in (4, 6, 9, 11) else 31)
            return {
                "event_date": None,
                "event_date_start": date(year, mon, 1),
                "event_date_end": date(year, mon, last),
                "date_precision": "MONTH",
                "date_parse_status": "PARTIAL",
            }

    # YEAR RANGE: "2014-2018", "2016-17", "2014 to 2018"
    m = re.search(r"\b((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)?\d{2})\b", hist)
    if m:
        y1, y2 = int(m.group(1)), int(m.group(2))
        if y2 < 100:
            y2 = y1 - (y1 % 100) + y2
        if y1 <= y2:
            return {
                "event_date": None,
                "event_date_start": date(y1, 1, 1),
                "event_date_end": date(y2, 12, 31),
                "date_precision": "RANGE",
                "date_parse_status": "PARTIAL",
            }

    # YEAR only: "2018", "1992"
    m = re.search(r"\b((?:19|20)\d{2})\b", hist)
    if m:
        y = int(m.group(1))
        return {
            "event_date": None,
            "event_date_start": date(y, 1, 1),
            "event_date_end": date(y, 12, 31),
            "date_precision": "YEAR",
            "date_parse_status": "PARTIAL",
        }

    # Descriptive text (e.g. "Monsoon, 2024") -> no defensible date
    return {
        "event_date": None, "event_date_start": None, "event_date_end": None,
        "date_precision": "UNKNOWN", "date_parse_status": "NONE",
    }
