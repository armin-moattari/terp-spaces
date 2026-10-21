from datetime import date

import pytest

from terp_spaces.academic_calendar import (BREAK, EXAMS, OFF_TERM, TEACHING,
                                           END_OF_TERM_ATTENDANCE, attendance,
                                           class_factor, day_status)

CAL = {
    "classes": {"from": "2026-08-31", "to": "2026-12-11"},
    "no_classes": [{"from": "2026-10-12", "to": "2026-10-13", "name": "Fall Break"}],
    "reading_days": [{"from": "2026-12-12", "to": "2026-12-12", "name": "Reading Day"}],
    "finals": {"from": "2026-12-14", "to": "2026-12-21", "name": "Final Exams"},
}


@pytest.mark.parametrize("day, kind, name", [
    (date(2026, 10, 20), TEACHING, "Classes in session"),
    (date(2026, 10, 12), BREAK, "Fall Break"),
    (date(2026, 10, 13), BREAK, "Fall Break"),
    (date(2026, 12, 12), EXAMS, "Reading Day"),
    (date(2026, 12, 15), EXAMS, "Final Exams"),
    (date(2026, 8, 30), OFF_TERM, "Outside the semester"),
    (date(2026, 12, 13), OFF_TERM, "Outside the semester"),  # Sunday between them
])
def test_day_status(day, kind, name):
    assert day_status(CAL, day) == (kind, name)


def test_attendance_slides_from_full_to_end_of_term():
    assert attendance(CAL, date(2026, 8, 31)) == pytest.approx(1.0)
    assert attendance(CAL, date(2026, 12, 11)) == pytest.approx(END_OF_TERM_ATTENDANCE)
    mid = attendance(CAL, date(2026, 10, 21))
    assert END_OF_TERM_ATTENDANCE < mid < 1.0


def test_class_factor_is_zero_off_teaching_days():
    assert class_factor(CAL, date(2026, 10, 12)) == 0.0
    assert class_factor(CAL, date(2026, 12, 15)) == 0.0
    assert class_factor(CAL, date(2026, 10, 20)) > 0.0
