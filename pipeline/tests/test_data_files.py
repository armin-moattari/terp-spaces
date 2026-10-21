"""Sanity checks on the hand-written JSON in data/umd, so a typo fails CI, not the map."""
import json
from datetime import date
from pathlib import Path

import pytest

from terp_spaces.schedule import WEEKDAYS

DATA = Path(__file__).resolve().parents[2] / "data" / "umd"
HOURS = json.loads((DATA / "building_hours.json").read_text())["buildings"]
CAL = json.loads((DATA / "academic_calendar.json").read_text())


def check_range(span):
    assert date.fromisoformat(span["from"]) <= date.fromisoformat(span["to"]), span


def check_spans(spans):
    if spans is None:
        return
    for s, e in spans:
        assert 0 <= s < e <= 36, spans  # may run past midnight, not past noon next day


def test_calendar_ranges_run_forward_and_in_order():
    for span in [CAL["classes"], CAL["finals"], *CAL["no_classes"], *CAL["reading_days"]]:
        check_range(span)
    assert CAL["classes"]["to"] < CAL["finals"]["from"]


@pytest.mark.parametrize("code", sorted(HOURS))
def test_building_hours_are_well_formed(code):
    entry = HOURS[code]
    assert entry["source"].startswith("https://") and entry["verified"]
    assert set(entry["regular"]) == set(WEEKDAYS)
    for spans in entry["regular"].values():
        check_spans(spans)
    check_range(entry["valid"])
    for exc in entry["exceptions"]:
        check_range(exc)
        check_spans(exc["spans"])
