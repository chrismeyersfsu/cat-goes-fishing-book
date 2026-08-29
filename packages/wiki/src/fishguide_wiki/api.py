"""Every byte that comes off the network comes through here.

Owns: the wiki's MediaWiki endpoint, the User-Agent, retry/backoff,
inter-request throttling, and `continue` paging.

Never: interprets a response body (parse.py does that) or touches the
filesystem (download.py does that).

Callers rely on `query()` yielding one raw response dict per API page,
already following `continue`, and on `_get` being the single seam tests
monkeypatch to run offline.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator

API = "https://cat-goes-fishing.fandom.com/api.php"
WIKI = "https://cat-goes-fishing.fandom.com/wiki/"
USER_AGENT = "fishguide-art-fetch/0.1 (+https://github.com/chrismeyersfsu/cat-goes-fishing-book)"

DELAY = 0.34  # polite gap between requests, seconds
RETRIES = 4
TIMEOUT = 30

# MediaWiki caps a multi-title query at 50 titles for anonymous clients.
TITLE_BATCH = 50

_last_request = 0.0


def _get(url: str) -> bytes:
    """The one network call in this package. Tests monkeypatch this."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _throttle() -> None:
    global _last_request
    wait = DELAY - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


def fetch(url: str) -> bytes:
    """`_get` plus throttling and retry on transient failures."""
    for attempt in range(RETRIES):
        _throttle()
        try:
            return _get(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            status = getattr(exc, "code", None)
            retryable = status is None or status == 429 or status >= 500
            if not retryable or attempt == RETRIES - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def get_json(params: dict[str, str]) -> dict:
    """One API call, decoded. `format=json` is added for you."""
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.loads(fetch(url))


def query(params: dict[str, str]) -> Iterator[dict]:
    """Yield each response page of an API query, following `continue`."""
    cont: dict[str, str] = {}
    while True:
        data = get_json({**params, **cont})
        yield data
        if "continue" not in data:
            return
        cont = dict(data["continue"])


def batched_titles(titles: list[str]) -> Iterator[list[str]]:
    """Split titles into API-legal chunks."""
    for i in range(0, len(titles), TITLE_BATCH):
        yield titles[i : i + TITLE_BATCH]


def page_url(title: str) -> str:
    return WIKI + urllib.parse.quote(title.replace(" ", "_"))
