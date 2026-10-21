"""Occupancy model v1: how full is a building at a local time, and how do we know. Pure.

Every estimate is {"level": 0-1 or None, "source": ..., "note": ...}, where source is
  closed     posted hours say it's shut (level 0)
  estimated  from scheduled class seats (see class_level)
  typical    from a hand-made curve for libraries, the union and gyms
  unknown    no posted hours and nothing scheduled: we won't guess (level None)
"reported" (student check-ins) arrives in a later milestone.

Steps, in order (matches CLAUDE.md):
  1. Closed per building hours -> 0.
  2. Classes: seats in session this hour / the building's weekly peak seats, times
     a peak-fullness cap and the calendar's class factor (breaks, finals, attendance).
  3. Libraries, union, gyms: max(typical curve, classes).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .academic_calendar import BREAK, EXAMS, OFF_TERM, class_factor, day_status
from .hours import is_open
from .schedule import WEEKDAYS

# Share of capacity a building reaches at its busiest scheduled hour. Classrooms are
# rarely all full at once, and hallways empty out while classes are in. Assumption.
DEFAULT_PEAK_FULLNESS = 0.85
PEAK_FULLNESS: dict[str, float] = {}  # per-building overrides, e.g. {"ESJ": 0.9}

# Hand-made weekday curves (fraction of capacity by hour, 0-23). Assumptions shaped
# by common campus patterns, to be replaced by check-in data. Weekends run at 60%.
TYPICAL_WEEKDAY = {
    "library": [.10, .08, .06, .05, .04, .04, .05, .10, .20, .35, .50, .60,
                .65, .70, .75, .75, .70, .60, .55, .60, .65, .60, .45, .25],
    "union":   [.05, .05, .03, .02, .02, .02, .05, .15, .25, .30, .45, .60,
                .85, .80, .55, .45, .40, .50, .50, .40, .35, .30, .20, .10],
    "gym":     [.05, .02, .01, .01, .01, .10, .30, .45, .35, .25, .25, .30,
                .40, .35, .35, .50, .70, .85, .85, .75, .60, .45, .30, .15],
}
WEEKEND_SCALE = 0.6
# Typical curves on non-teaching days: breaks empty campus out; finals and reading
# day fill the libraries. Applies to every curve type alike for now.
DAY_KIND_SCALE = {BREAK: 0.3, OFF_TERM: 0.3, EXAMS: 1.0}


def class_level(grid: dict | None, code: str, when: datetime, factor: float) -> float | None:
    """Class-driven level for one building, or None if it has no scheduled classes."""
    if not grid or not grid["peak"]:
        return None
    seats = grid["seats"][WEEKDAYS[when.weekday()]][when.hour]
    cap = PEAK_FULLNESS.get(code, DEFAULT_PEAK_FULLNESS)
    return min(seats / grid["peak"], 1.0) * cap * factor


def typical_level(kind: str | None, when: datetime, day_kind: str) -> float | None:
    """Typical-curve level for libraries, the union and gyms; None for other buildings."""
    curve = TYPICAL_WEEKDAY.get(kind or "")
    if curve is None:
        return None
    level = curve[when.hour] * (WEEKEND_SCALE if when.weekday() >= 5 else 1.0)
    return level * DAY_KIND_SCALE.get(day_kind, 1.0)


def estimate(code: str, when: datetime, grids: dict, hours: dict, cal: dict) -> dict:
    """Occupancy of building `code` at naive local time `when`."""
    entry = hours.get(code)
    open_now, hours_note = is_open(entry, when)
    day_kind, day_name = day_status(cal, when.date())
    if open_now is False:
        return {"level": 0.0, "source": "closed", "note": hours_note or "Closed per posted hours"}

    classes = class_level(grids.get(code), code, when, class_factor(cal, when.date()))
    # Only trust a typical curve when posted hours say the doors are open.
    typical = typical_level(entry and entry.get("type"), when, day_kind) if open_now else None

    if typical is not None and (classes is None or typical >= classes):
        return {"level": round(typical, 2), "source": "typical", "note": hours_note}
    if classes:  # scheduled seats imply the building is open, hours or not
        return {"level": round(classes, 2), "source": "estimated", "note": None}
    if open_now:  # open with nothing scheduled
        return {"level": 0.0, "source": "estimated", "note": None}
    why = day_name if day_kind != "teaching" else "No classes scheduled"
    return {"level": None, "source": "unknown",
            "note": f"{why}. {hours_note or 'No posted hours'}."}


def forecast(start: datetime, hours_ahead: int, grids: dict, hours: dict,
             cal: dict) -> dict[str, dict[str, list]]:
    """Hourly estimates from `start` (naive local, on the hour) for every known building.

    Returns {code: {"level": [...], "source": [...], "note": [...], "about": {...}}},
    one slot per hour, so the site only has to index by hours since `start`. `about`
    holds what's true all week: where the hours came from and the building's note.

    Slots step in local wall-clock hours (naive datetimes), so across a DST change the
    site must index by local date and hour, not by elapsed real time.
    """
    out = {}
    for code in sorted(set(grids) | set(hours)):
        rows = [estimate(code, start + timedelta(hours=i), grids, hours, cal)
                for i in range(hours_ahead)]
        out[code] = {key: [r[key] for r in rows] for key in ("level", "source", "note")}
        entry = hours.get(code)
        if entry:
            out[code]["about"] = {k: entry[k] for k in ("name", "type", "source",
                                                        "verified", "note") if k in entry}
    return out


def color(level: float | None) -> str:
    """Map colour bucket: < 0.3 quiet, < 0.55 moderate, else busy."""
    if level is None:
        return "unknown"
    return "quiet" if level < 0.3 else "moderate" if level < 0.55 else "busy"
