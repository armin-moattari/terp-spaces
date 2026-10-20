"""Parsing helpers for Testudo/umd.io meeting fields. Pure functions, no I/O."""
from __future__ import annotations

import re

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

_DAY_CODES = {"M": "monday", "Tu": "tuesday", "W": "wednesday", "Th": "thursday",
              "F": "friday", "Sa": "saturday", "Su": "sunday"}
# Two-letter codes first so "Tu" is not read as an unknown "T" plus "u".
_DAY_RE = re.compile(r"Tu|Th|Sa|Su|M|W|F")
_TIME_RE = re.compile(r"^\s*(\d{1,2}):(\d{2})\s*(am|pm)\s*$", re.IGNORECASE)


def parse_days(days: str) -> list[str]:
    """'TuTh' -> ['tuesday', 'thursday']. Unknown letters are ignored."""
    return [_DAY_CODES[code] for code in _DAY_RE.findall(days or "")]


def to_hours(time: str) -> float:
    """'11:00am' -> 11.0, '1:45pm' -> 13.75, '12:30am' -> 0.5.

    Raises ValueError on anything else, so bad data is loud rather than silently
    placed at midnight.
    """
    m = _TIME_RE.match(time or "")
    if not m:
        raise ValueError(f"unrecognised time: {time!r}")
    hour, minute, ampm = int(m[1]), int(m[2]), m[3].lower()
    if not (1 <= hour <= 12 and 0 <= minute < 60):
        raise ValueError(f"unrecognised time: {time!r}")
    hour %= 12  # 12am -> 0, 12pm -> 0 before the pm shift
    if ampm == "pm":
        hour += 12
    return hour + minute / 60


def hour_overlaps(start: float, end: float) -> dict[int, float]:
    """Fraction of each clock hour covered by [start, end).

    A class from 9:30 to 10:45 covers half of hour 9 and three quarters of hour 10:
    {9: 0.5, 10: 0.75}. Weighting by overlap keeps a 50-minute class from counting
    as a full hour in two different hours.
    """
    out: dict[int, float] = {}
    for h in range(int(start), min(int(end) + 1, 24)):
        overlap = min(end, h + 1) - max(start, h)
        if overlap > 0:
            out[h] = overlap
    return out
