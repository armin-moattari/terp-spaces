"""Parse Testudo Schedule of Classes HTML into umd.io-shaped section dicts. Pure, no I/O.

Testudo is the source umd.io mirrors, and its seat counts are fresher. Emitting the
same shape as umd.io (string seat counts, `meetings[]` with `days`, `start_time`,
`building`, `room`) means `activity.py` works on either source unchanged.

Page shape (app.testudo.umd.edu/soc/<term>/sections?courseIds=CMSC434):
    div.course-sections#CMSC434
      div.section
        span.section-id, span.section-instructor, span.total-seats-count, ...
        div.class-days-container > div.row   (one row per meeting)
"""
from __future__ import annotations

from bs4 import BeautifulSoup, Tag


def _text(node: Tag, selector: str) -> str:
    """Stripped text of the first match, or "" if the element is absent."""
    found = node.select_one(selector)
    return found.get_text(strip=True) if found else ""


def _meeting(row: Tag) -> dict:
    """One meeting row -> umd.io meeting dict.

    Rows without a building code (online, TBA) get building "" so that
    `activity.in_person_meetings` skips them, matching how umd.io reports them.
    """
    building = _text(row, ".building-code")
    room = _text(row, ".class-room") if building else (
        _text(row, ".class-building") or "TBA").upper()
    return {"days": _text(row, ".section-days"),
            "start_time": _text(row, ".class-start-time"),
            "end_time": _text(row, ".class-end-time"),
            "building": building,
            "room": room}


def parse_sections(html: str, term: str) -> list[dict]:
    """Every section on a Testudo page, in umd.io's section shape."""
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for course in soup.select("div.course-sections"):
        course_id = course.get("id", "")
        for sec in course.select("div.section"):
            number = _text(sec, ".section-id")
            out.append({
                "course": course_id,
                "section_id": f"{course_id}-{number}",
                "semester": term,
                "number": number,
                "seats": _text(sec, ".total-seats-count"),
                "open_seats": _text(sec, ".open-seats-count"),
                "waitlist": _text(sec, ".waitlist-count"),
                "instructors": [i.get_text(strip=True)
                                for i in sec.select(".section-instructor")],
                "meetings": [_meeting(row)
                             for row in sec.select(".class-days-container > .row")],
            })
    return out
