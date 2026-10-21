"""What kind of day a date is, and how much class activity to expect. Pure, no I/O.

Reads the dict loaded from data/umd/academic_calendar.json.

`class_factor` scales a building's scheduled seats for one day:
  0   outside the class period, on holidays, reading days and during finals
      (final exams don't follow the class schedule, so the weekly grid says nothing)
  0-1 on teaching days, by attendance: fewer enrolled students show up as the term
      wears on. This is an assumption, not a measurement, and the UI says so.

A constant attendance factor would do nothing, because occupancy divides by the
building's own weekly peak; only a factor that changes over time moves the result.
"""
from __future__ import annotations

from datetime import date

# Assumed share of enrolled students in the room: full on the first day, sliding
# linearly to this by the last day of classes. Tune once check-ins exist.
END_OF_TERM_ATTENDANCE = 0.75

TEACHING, BREAK, EXAMS, OFF_TERM = "teaching", "break", "exams", "off_term"


def _d(text: str) -> date:
    return date.fromisoformat(text)


def _within(day: date, span: dict) -> bool:
    return _d(span["from"]) <= day <= _d(span["to"])


def day_status(cal: dict, day: date) -> tuple[str, str]:
    """(kind, name): kind is TEACHING, BREAK, EXAMS or OFF_TERM; name feeds UI notes."""
    if _within(day, cal["finals"]):
        return EXAMS, cal["finals"]["name"]
    for span in cal["reading_days"]:
        if _within(day, span):
            return EXAMS, span["name"]
    if not _within(day, cal["classes"]):
        return OFF_TERM, "Outside the semester"
    for span in cal["no_classes"]:
        if _within(day, span):
            return BREAK, span["name"]
    return TEACHING, "Classes in session"


def attendance(cal: dict, day: date) -> float:
    """Assumed fraction of enrolled students attending on a teaching day."""
    start, end = _d(cal["classes"]["from"]), _d(cal["classes"]["to"])
    progress = min(max((day - start).days / max((end - start).days, 1), 0.0), 1.0)
    return 1.0 - (1.0 - END_OF_TERM_ATTENDANCE) * progress


def class_factor(cal: dict, day: date) -> float:
    """Multiplier for a day's scheduled seats: attendance on teaching days, else 0."""
    kind, _ = day_status(cal, day)
    return attendance(cal, day) if kind == TEACHING else 0.0
