import pytest

from terp_spaces.schedule import hour_overlaps, parse_days, to_hours


@pytest.mark.parametrize("codes, expected", [
    ("MWF", ["monday", "wednesday", "friday"]),
    ("TuTh", ["tuesday", "thursday"]),
    ("MTuWThF", ["monday", "tuesday", "wednesday", "thursday", "friday"]),
    ("SaSu", ["saturday", "sunday"]),
    ("", []),
])
def test_parse_days(codes, expected):
    assert parse_days(codes) == expected


@pytest.mark.parametrize("text, hours", [
    ("11:00am", 11.0), ("1:45pm", 13.75), ("12:00pm", 12.0),
    ("12:30am", 0.5), ("9:30am", 9.5), (" 5:15PM ", 17.25),
])
def test_to_hours(text, hours):
    assert to_hours(text) == pytest.approx(hours)


@pytest.mark.parametrize("bad", ["", "noon", "13:00pm", "9:75am", "11:00"])
def test_to_hours_rejects_garbage(bad):
    with pytest.raises(ValueError):
        to_hours(bad)


def test_hour_overlaps_partial_hours():
    assert hour_overlaps(9.5, 10.75) == pytest.approx({9: 0.5, 10: 0.75})


def test_hour_overlaps_class_ending_on_the_hour():
    # 10:00-11:00 must not leak a zero-length slot into hour 11
    assert hour_overlaps(10.0, 11.0) == {10: 1.0}
