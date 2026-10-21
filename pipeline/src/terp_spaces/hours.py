"""Is a building open at a given local time? From building_hours.json. Pure, no I/O.

Answers are three-valued: True (open), False (closed), None (we don't know). None
matters: a building with no posted hours is not "closed", and the map must not say so.

Spans are [open_hour, close_hour] on one date's clock; a close past 24 spills into
the next morning. Stamp's Friday [7, 25.5] means 1:00am Saturday is still open,
so each check also looks at the previous day's spans shifted back by 24 hours.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from .schedule import WEEKDAYS


def _covers(span: dict, day: date) -> bool:
    return date.fromisoformat(span["from"]) <= day <= date.fromisoformat(span["to"])


def spans_on(entry: dict, day: date) -> tuple[list[list[float]] | None, str | None]:
    """(opening spans for `day`, note about that date). Spans None = unknown.

    An exception for the date wins; otherwise regular weekday hours apply while the
    date is inside `valid`. Outside `valid` the posted hours no longer apply, so None.
    The entry's general `note` is about the building, not the date, so it isn't
    returned here; callers show it once per building.
    """
    for exc in entry.get("exceptions", []):
        if _covers(exc, day):
            return exc["spans"], exc.get("note")
    if "valid" in entry and not _covers(entry["valid"], day):
        return None, "Posted hours don't cover this date"
    spans = entry["regular"].get(WEEKDAYS[day.weekday()])
    return spans, (None if spans is not None else "Hours not posted for this day")


def is_open(entry: dict | None, when: datetime) -> tuple[bool | None, str | None]:
    """(open?, note) for a building's hours entry at naive local time `when`."""
    if entry is None:
        return None, None
    hour = when.hour + when.minute / 60
    today, note = spans_on(entry, when.date())
    yesterday, _ = spans_on(entry, when.date() - timedelta(days=1))

    # Last night's late close (e.g. 1:30am) keeps the doors open regardless of today.
    if yesterday and any(s <= hour + 24 < e for s, e in yesterday):
        return True, note
    if today is None:
        return None, note
    return any(s <= hour < e for s, e in today), note
