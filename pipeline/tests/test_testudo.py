"""Testudo parser tests against a saved page (fixtures/testudo_cmsc434.html, 2026-10-20)."""
from pathlib import Path

import pytest

from terp_spaces.activity import building_grids
from terp_spaces.testudo import parse_sections

FIXTURE = (Path(__file__).parent / "fixtures" / "testudo_cmsc434.html").read_text()


@pytest.fixture(scope="module")
def sections():
    return parse_sections(FIXTURE, "202608")


def test_finds_every_section(sections):
    assert [s["section_id"] for s in sections] == [
        "CMSC434-0101", "CMSC434-0201", "CMSC434-0301"]
    assert all(s["course"] == "CMSC434" and s["semester"] == "202608" for s in sections)


def test_first_section_matches_page(sections):
    s = sections[0]
    assert (s["seats"], s["open_seats"], s["waitlist"]) == ("54", "1", "0")
    assert s["instructors"] == ["Evan Golub"]
    assert s["meetings"] == [{"days": "TuTh", "start_time": "11:00am",
                              "end_time": "12:15pm", "building": "IRB", "room": "1207"}]


def test_output_feeds_activity_unchanged(sections):
    # 54 seats - 1 open = 53 enrolled in IRB on Tuesday 11:00-12:00.
    grid = building_grids(sections[:1])["IRB"]
    assert grid["seats"]["tuesday"][11] == pytest.approx(53.0)


def test_meeting_without_building_is_marked_not_in_person():
    # Hand-written: the saved page has only in-person meetings, so this checks the
    # fallback path rather than real Testudo markup for online sections.
    html = """<div class="course-sections" id="TEST100"><div class="section">
      <span class="section-id">0101</span>
      <div class="class-days-container"><div class="row">
        <span class="class-building">Online</span>
      </div></div></div></div>"""
    [sec] = parse_sections(html, "202608")
    assert sec["meetings"][0]["building"] == ""
    assert sec["meetings"][0]["room"] == "ONLINE"
    assert building_grids([sec]) == {}
