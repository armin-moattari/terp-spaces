from datetime import datetime

from terp_spaces.hours import is_open, spans_on

# Shaped like Stamp: late Friday close, an exception day, a TBD day, a valid range.
UNION = {
    "valid": {"from": "2026-08-27", "to": "2026-12-20"},
    "note": "regular note",
    "regular": {"monday": [[7, 24]], "tuesday": [[7, 24]], "wednesday": [[7, 24]],
                "thursday": [[7, 24]], "friday": [[7, 25.5]], "saturday": [[8, 25.5]],
                "sunday": [[11, 24]]},
    "exceptions": [
        {"from": "2026-10-12", "to": "2026-10-12", "spans": [], "note": "Fall Break"},
        {"from": "2026-11-28", "to": "2026-11-28", "spans": None, "note": "TBD"},
    ],
}


def at(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi)


def test_regular_hours():
    # The building's general note is per-building, not per-hour, so it isn't echoed.
    assert is_open(UNION, at(2026, 10, 20, 12)) == (True, None)  # Tuesday noon
    assert is_open(UNION, at(2026, 10, 20, 6, 59))[0] is False  # before 7am


def test_late_close_spills_into_next_morning():
    # Friday Oct 23 runs to 1:30am Saturday.
    assert is_open(UNION, at(2026, 10, 24, 1, 15))[0] is True
    assert is_open(UNION, at(2026, 10, 24, 1, 30))[0] is False
    assert is_open(UNION, at(2026, 10, 24, 7))[0] is False      # Saturday opens at 8


def test_closing_time_is_exclusive():
    assert is_open(UNION, at(2026, 10, 25, 23, 59))[0] is True  # Sunday to midnight
    assert is_open(UNION, at(2026, 10, 26, 0, 0))[0] is False   # Monday 12am


def test_exception_closed_all_day_with_note():
    assert is_open(UNION, at(2026, 10, 12, 12)) == (False, "Fall Break")


def test_tbd_day_is_unknown_not_closed():
    assert is_open(UNION, at(2026, 11, 28, 12)) == (None, "TBD")


def test_late_close_still_counts_on_a_tbd_morning():
    # Friday Nov 27 has regular hours to 1:30am; the TBD Saturday shouldn't hide that.
    assert is_open(UNION, at(2026, 11, 28, 1))[0] is True


def test_outside_valid_range_is_unknown():
    open_now, note = is_open(UNION, at(2027, 2, 1, 12))
    assert open_now is None and "don't cover" in note


def test_null_weekday_is_unknown():
    gym = {"regular": {"saturday": None}, "exceptions": []}
    assert spans_on(gym, at(2026, 10, 24, 12).date()) == (None, "Hours not posted for this day")
    assert is_open(gym, at(2026, 10, 24, 12))[0] is None


def test_no_entry_is_unknown():
    assert is_open(None, at(2026, 10, 20, 12)) == (None, None)
