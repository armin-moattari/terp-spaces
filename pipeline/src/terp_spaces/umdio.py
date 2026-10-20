"""Thin client for the umd.io v1 API (a JSON mirror of the Testudo schedule)."""
from __future__ import annotations

import time
from typing import Iterator

import requests

BASE = "https://api.umd.io/v1"
USER_AGENT = "terp-spaces/0.1 (student project; github.com/armin-moattari/terp-spaces)"


def iter_sections(term: str, per_page: int = 100, pause_s: float = 0.3,
                  session: requests.Session | None = None) -> Iterator[dict]:
    """Yield every section for a term, one page at a time, pausing between pages."""
    http = session or requests.Session()
    http.headers.setdefault("User-Agent", USER_AGENT)
    page = 1
    while True:
        r = http.get(f"{BASE}/courses/sections",
                     params={"semester": term, "per_page": per_page, "page": page},
                     timeout=30)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            return
        yield from batch
        page += 1
        time.sleep(pause_s)
