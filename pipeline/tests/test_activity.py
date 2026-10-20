import pytest

from terp_spaces.activity import building_grids, enrolled, merge_intervals, room_busy

# Shapes copied from real umd.io responses (2026-10-20).
CMSC434 = {"section_id": "CMSC434-0101", "seats": "52", "open_seats": "2",
           "meetings": [{"days": "TuTh", "room": "1207", "building": "IRB",
                         "start_time": "11:00am", "end_time": "12:15pm"}]}
HYBRID = {"section_id": "AAAS100-0101", "seats": "40", "open_seats": "0",
          "meetings": [{"days": "MW", "room": "0103", "building": "KEY",
                        "start_time": "11:00am", "end_time": "11:50am"},
                       {"days": "F", "room": "ONLINE", "building": "",
                        "start_time": "11:00am", "end_time": "11:50am"}]}


def test_enrolled_handles_strings_and_bad_data():
    assert enrolled(CMSC434) == 50
    assert enrolled({"seats": "10", "open_seats": "12"}) == 0
    assert enrolled({"seats": None}) == 0


def test_building_grid_weights_partial_hours():
    g = building_grids([CMSC434])["IRB"]
    assert g["seats"]["tuesday"][11] == pytest.approx(50.0)
    assert g["seats"]["tuesday"][12] == pytest.approx(12.5)  # 15 of 60 minutes
    assert g["seats"]["monday"][11] == 0
    assert g["peak"] == pytest.approx(50.0)


def test_online_meetings_are_skipped():
    grids = building_grids([HYBRID])
    assert set(grids) == {"KEY"}
    assert grids["KEY"]["seats"]["friday"][11] == 0


def test_room_busy_and_cross_listed_merge():
    twin = {**CMSC434, "section_id": "CMSC734-0101"}
    rooms = room_busy([CMSC434, twin])
    assert rooms["IRB1207"]["tuesday"] == [[11.0, 12.25]]
    assert "monday" not in rooms["IRB1207"]


def test_merge_intervals():
    assert merge_intervals([[13, 14], [9, 10], [9.5, 11], [14, 15]]) == [[9, 11], [13, 15]]
