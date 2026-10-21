"""umd.io client tests with a fake session: paging, retries, and the page cache."""
import pytest
import requests

from terp_spaces import umdio
from terp_spaces.umdio import fetch_page, iter_sections

SEC = {"section_id": "CMSC434-0101"}


class FakeResponse:
    def __init__(self, status: int, body=None):
        self.status_code, self._body = status, body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)

    def json(self):
        return self._body


class FakeSession:
    """Replays scripted responses and records which pages were requested."""

    def __init__(self, responses):
        self.responses, self.pages, self.headers = list(responses), [], {}

    def get(self, url, params, timeout):
        self.pages.append(params["page"])
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


def no_sleep(_seconds):
    pass


def test_pages_until_empty_and_sets_user_agent():
    http = FakeSession([FakeResponse(200, [SEC, SEC]), FakeResponse(200, [SEC]),
                        FakeResponse(200, [])])
    assert len(list(iter_sections("202608", session=http, sleep=no_sleep))) == 3
    assert http.pages == [1, 2, 3]
    assert http.headers["User-Agent"] == umdio.USER_AGENT


def test_retries_transient_500_then_succeeds():
    waits = []
    http = FakeSession([FakeResponse(500), FakeResponse(200, [SEC])])
    assert fetch_page(http, "202608", 69, 100, sleep=waits.append) == [SEC]
    assert waits == [umdio.RETRY_WAITS_S[0]]


def test_retries_dropped_connection():
    http = FakeSession([requests.ConnectionError("reset"), FakeResponse(200, [SEC])])
    assert fetch_page(http, "202608", 1, 100, sleep=no_sleep) == [SEC]


def test_gives_up_after_all_retries():
    http = FakeSession([FakeResponse(503)] * (len(umdio.RETRY_WAITS_S) + 1))
    with pytest.raises(requests.HTTPError):
        fetch_page(http, "202608", 1, 100, sleep=no_sleep)
    assert len(http.pages) == len(umdio.RETRY_WAITS_S) + 1


def test_client_errors_fail_fast():
    http = FakeSession([FakeResponse(404)])
    with pytest.raises(requests.HTTPError):
        fetch_page(http, "202608", 1, 100, sleep=no_sleep)
    assert http.pages == [1]  # no retry: a 404 won't fix itself


def test_cache_resumes_where_a_crash_left_off(tmp_path):
    # First run: page 1 lands, page 2 fails hard.
    crash = FakeSession([FakeResponse(200, [SEC]), FakeResponse(404)])
    with pytest.raises(requests.HTTPError):
        list(iter_sections("202608", session=crash, cache_dir=tmp_path, sleep=no_sleep))
    # Second run starts at page 2; page 1 comes from disk.
    resume = FakeSession([FakeResponse(200, [SEC]), FakeResponse(200, [])])
    assert len(list(iter_sections("202608", session=resume, cache_dir=tmp_path,
                                  sleep=no_sleep))) == 2
    assert resume.pages == [2, 3]
    # Third run: fully cached, no requests at all.
    offline = FakeSession([])
    assert len(list(iter_sections("202608", session=offline, cache_dir=tmp_path,
                                  sleep=no_sleep))) == 2
    assert offline.pages == []


def test_never_empty_api_hits_page_cap(monkeypatch):
    monkeypatch.setattr(umdio, "MAX_PAGES", 3)
    http = FakeSession([FakeResponse(200, [SEC])] * 3)
    with pytest.raises(RuntimeError, match="more than 3 pages"):
        list(iter_sections("202608", session=http, sleep=no_sleep))
