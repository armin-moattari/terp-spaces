from datetime import datetime

import pytest

from terp_spaces import occupancy
from terp_spaces.occupancy import DEFAULT_PEAK_FULLNESS, color, estimate

CAL = {
    "classes": {"from": "2026-08-31", "to": "2026-12-11"},
    "no_classes": [{"from": "2026-10-12", "to": "2026-10-13", "name": "Fall Break"}],
    "reading_days": [],
    "finals": {"from": "2026-12-14", "to": "2026-12-21", "name": "Final Exams"},
}
EVERY_DAY = {d: [[8, 22]] for d in ("monday", "tuesday", "wednesday", "thursday",
                                    "friday", "saturday", "sunday")}
HOURS = {"LIB": {"type": "library", "regular": EVERY_DAY, "exceptions": []},
         "SHUT": {"regular": {**EVERY_DAY, "tuesday": []}, "exceptions": []}}


def grid(peak_hour_seats: float, now_seats: float, day="tuesday", hour=11):
    seats = {d: [0.0] * 24 for d in ("monday", "tuesday", "wednesday", "thursday",
                                     "friday", "saturday", "sunday")}
    seats["monday"][10] = peak_hour_seats
    seats[day][hour] = now_seats
    return {"seats": seats, "peak": peak_hour_seats}


GRIDS = {"ESJ": grid(1000, 500), "LIB": grid(100, 100), "SHUT": grid(100, 100)}
TUE_11 = datetime(2026, 9, 1, 11)   # first Tuesday of term: attendance 1.0
TUE_3AM = datetime(2026, 9, 1, 3)
FALL_BREAK = datetime(2026, 10, 13, 11)


def test_classes_scale_by_peak_and_fullness():
    e = estimate("ESJ", TUE_11, GRIDS, HOURS, CAL)
    assert e["source"] == "estimated"
    assert e["level"] == pytest.approx(0.5 * DEFAULT_PEAK_FULLNESS, abs=0.01)


def test_no_hours_and_no_classes_is_unknown_not_closed():
    e = estimate("ESJ", TUE_3AM, GRIDS, HOURS, CAL)
    assert e == {"level": None, "source": "unknown",
                 "note": "No classes scheduled. No posted hours."}


def test_unknown_day_for_a_building_with_some_hours_says_so():
    hours = {"GYM": {"type": "gym", "regular": {**EVERY_DAY, "saturday": None},
                     "exceptions": []}}
    e = estimate("GYM", datetime(2026, 9, 5, 14), {}, hours, CAL)
    assert e["source"] == "unknown"
    assert e["note"] == "No classes scheduled. Hours not posted for this day."


def test_forecast_shape_and_about():
    hours = {**HOURS, "LIB": {**HOURS["LIB"], "name": "Library", "source": "https://x"}}
    out = occupancy.forecast(TUE_3AM, 24, GRIDS, hours, CAL)
    assert set(out) == {"ESJ", "LIB", "SHUT"}
    assert all(len(out[c][k]) == 24 for c in out for k in ("level", "source", "note"))
    assert out["LIB"]["about"] == {"name": "Library", "type": "library", "source": "https://x"}
    assert "about" not in out["ESJ"]


def test_break_zeroes_classes_and_says_why():
    e = estimate("ESJ", FALL_BREAK, GRIDS, HOURS, CAL)
    assert e["source"] == "unknown" and e["note"].startswith("Fall Break")


def test_posted_closure_beats_scheduled_classes():
    e = estimate("SHUT", TUE_11, GRIDS, HOURS, CAL)
    assert e["source"] == "closed" and e["level"] == 0.0


def test_library_takes_max_of_curve_and_classes():
    # Classes at 100% of peak beat the 11am library curve...
    assert estimate("LIB", TUE_11, GRIDS, HOURS, CAL)["source"] == "estimated"
    # ...but at 3pm with no classes, the curve wins.
    e = estimate("LIB", datetime(2026, 9, 1, 15), GRIDS, HOURS, CAL)
    assert e["source"] == "typical"
    assert e["level"] == pytest.approx(occupancy.TYPICAL_WEEKDAY["library"][15])


def test_library_curve_quieter_on_break_and_weekends():
    weekday = estimate("LIB", datetime(2026, 9, 1, 15), {}, HOURS, CAL)["level"]
    on_break = estimate("LIB", datetime(2026, 10, 13, 15), {}, HOURS, CAL)["level"]
    saturday = estimate("LIB", datetime(2026, 9, 5, 15), {}, HOURS, CAL)["level"]
    assert on_break < weekday and saturday < weekday


def test_library_closed_hours_are_closed():
    assert estimate("LIB", TUE_3AM, GRIDS, HOURS, CAL)["source"] == "closed"


@pytest.mark.parametrize("level, bucket", [
    (None, "unknown"), (0.0, "quiet"), (0.29, "quiet"), (0.3, "moderate"),
    (0.54, "moderate"), (0.55, "busy"), (1.0, "busy"),
])
def test_color_buckets(level, bucket):
    assert color(level) == bucket
