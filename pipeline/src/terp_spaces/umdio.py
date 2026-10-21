"""Thin client for the umd.io v1 API (a JSON mirror of the Testudo schedule).

umd.io is slow (often 5-15 s per page) and sometimes returns a transient 500, so
the client retries with backoff and caches every page on disk. A run that dies on
page 69 resumes from page 69, and re-running while checking data costs no requests.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable, Iterator

import requests

BASE = "https://api.umd.io/v1"
USER_AGENT = "terp-spaces/0.1 (student project; github.com/armin-moattari/terp-spaces)"

# Waits before each retry. Long on purpose: a struggling server needs breathing room.
RETRY_WAITS_S = (5, 15, 45)
# A fall term is ~150 pages of 100; this only guards against a never-empty API.
MAX_PAGES = 500

log = logging.getLogger(__name__)


def _retryable(err: requests.RequestException) -> bool:
    """Server errors, rate limits and dropped connections may pass; 4xx won't."""
    if isinstance(err, requests.HTTPError) and err.response is not None:
        status = err.response.status_code
        return status >= 500 or status == 429
    return isinstance(err, (requests.ConnectionError, requests.Timeout))


def fetch_page(http: requests.Session, term: str, page: int, per_page: int,
               sleep: Callable[[float], None] = time.sleep) -> list[dict]:
    """GET one page of sections, retrying transient failures per RETRY_WAITS_S."""
    for attempt in range(len(RETRY_WAITS_S) + 1):
        try:
            r = http.get(f"{BASE}/courses/sections",
                         params={"semester": term, "per_page": per_page, "page": page},
                         timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as err:
            if attempt == len(RETRY_WAITS_S) or not _retryable(err):
                raise
            wait = RETRY_WAITS_S[attempt]
            log.warning("page %d failed (%s); retrying in %ds", page, err, wait)
            sleep(wait)
    raise AssertionError("unreachable")


def iter_sections(term: str, per_page: int = 100, pause_s: float = 0.3,
                  session: requests.Session | None = None,
                  cache_dir: Path | None = None,
                  sleep: Callable[[float], None] = time.sleep) -> Iterator[dict]:
    """Yield every section for a term, one page at a time, pausing between requests.

    With `cache_dir`, each page is read from / written to
    `cache_dir/<term>/page-NNNN.json`. The empty page that marks the end is cached
    too, so a fully cached term makes no requests. Delete the folder to refresh.
    """
    http = session or requests.Session()
    http.headers.setdefault("User-Agent", USER_AGENT)
    term_dir = cache_dir / term if cache_dir else None
    if term_dir:
        term_dir.mkdir(parents=True, exist_ok=True)

    for page in range(1, MAX_PAGES + 1):
        cached = term_dir / f"page-{page:04d}.json" if term_dir else None
        if cached and cached.exists():
            batch = json.loads(cached.read_text())
            log.info("page %d: %d sections (cached)", page, len(batch))
        else:
            batch = fetch_page(http, term, page, per_page, sleep=sleep)
            if cached:
                cached.write_text(json.dumps(batch))
            log.info("page %d: %d sections", page, len(batch))
            sleep(pause_s)
        if not batch:
            return
        yield from batch
    raise RuntimeError(f"umd.io returned more than {MAX_PAGES} pages for {term}; "
                       "is the semester filter being ignored?")
