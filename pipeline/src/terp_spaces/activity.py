"""Turn umd.io section records into building and room activity. Pure, no I/O."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .schedule import WEEKDAYS, hour_overlaps, parse_days, to_hours

NOT_A_ROOM = {"", "ONLINE", "TBA"}


def enrolled(section: dict) -> int:
    """Students enrolled = seats - open seats (umd.io sends both as strings)."""
    try:
        return max(int(section["seats"]) - int(section["open_seats"]), 0)
    except (KeyError, TypeError, ValueError):
        return 0


def in_person_meetings(section: dict) -> Iterable[dict]:
    """Meetings with a real building, room and time (skips ONLINE / TBA)."""
    for m in section.get("meetings") or []:
        if m.get("building") and m.get("room") not in NOT_A_ROOM and m.get("start_time"):
            yield m


def building_grids(sections: Iterable[dict]) -> dict[str, dict]:
    """Per building code: hourly enrolled-seat grid per weekday, plus the weekly peak.

    Returns {"IRB": {"seats": {"monday": [24 floats], ...}, "peak": float}}.
    """
    grids: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {d: [0.0] * 24 for d in WEEKDAYS})
    for sec in sections:
        n = enrolled(sec)
        if not n:
            continue
        for m in in_person_meetings(sec):
            start, end = to_hours(m["start_time"]), to_hours(m["end_time"])
            for day in parse_days(m.get("days", "")):
                for hour, frac in hour_overlaps(start, end).items():
                    grids[m["building"]][day][hour] += n * frac
    return {
        code: {
            "seats": {d: [round(v, 1) for v in hrs] for d, hrs in grid.items()},
            "peak": round(max(max(hrs) for hrs in grid.values()), 1),
        }
        for code, grid in grids.items()
    }


def merge_intervals(spans: list[list[float]]) -> list[list[float]]:
    """Merge overlapping or touching [start, end] spans.

    Cross-listed sections (e.g. CMSC434 and a grad version) share a room at the same
    time; merging keeps them from showing as two bookings.
    """
    merged: list[list[float]] = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return merged


def room_busy(sections: Iterable[dict]) -> dict[str, dict[str, list[list[float]]]]:
    """Per room ("IRB1207"): weekday -> merged list of [start_hour, end_hour] busy spans.

    A room with no span is not necessarily unlocked, only unscheduled.
    """
    rooms: dict[str, dict[str, list[list[float]]]] = defaultdict(lambda: defaultdict(list))
    for sec in sections:
        for m in in_person_meetings(sec):
            span = [round(to_hours(m["start_time"]), 3), round(to_hours(m["end_time"]), 3)]
            for day in parse_days(m.get("days", "")):
                rooms[m["building"] + m["room"]][day].append(span)
    return {room: {day: merge_intervals(spans) for day, spans in days.items()}
            for room, days in rooms.items()}
