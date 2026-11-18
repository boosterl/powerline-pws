"""Fetching station data: reading, timeouts, caching and fallbacks."""
import os
import time
import urllib.request
from collections.abc import Callable
from typing import NamedTuple
from urllib.parse import unquote, urlparse

from . import cache
from .parsers import ParseError, StationState

DEFAULT_TIMEOUT = 3.0
DEFAULT_RETRY_INTERVAL = 60.0


class FetchResult(NamedTuple):
    state: StationState | None
    #: Problem to report, if the fetch failed (``state`` may still be a cached fallback).
    error: str | None


def read_source(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Read raw station data from an http(s) url, ``file://`` url or local path."""
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    if parsed.scheme == "file":
        path = unquote(parsed.path)
    elif parsed.scheme == "":
        path = os.path.expanduser(url)
    else:
        raise ValueError(f"unsupported url scheme: {parsed.scheme!r}")
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def fetch_state(
    url: str,
    station_type: str,
    parser: Callable[[str, str], StationState],
    date_format: str,
    timeout: float = DEFAULT_TIMEOUT,
    interval: float = 150,
    retry_interval: float = DEFAULT_RETRY_INTERVAL,
    use_cache: bool = True,
    cache_directory: str | None = None,
    now: float | None = None,
    reader: Callable[[str, float], str] = read_source,
) -> FetchResult:
    """Get the station state, using the disk cache to avoid slow repeated fetches.

    * A recent successful fetch is reused without touching the network.
    * After a failed fetch the network is not retried for ``retry_interval``
      seconds, so an unreachable station costs at most one timeout per period.
    * When a fetch fails the last good state is returned, if there is one; the
      segment's staleness highlighting then shows how old it is.
    """
    now = time.time() if now is None else now
    path = cache.cache_path(url, station_type, cache_directory) if use_cache else None
    entry = cache.load(path) if path else None

    if entry and cache.is_fresh(entry, interval, retry_interval, now):
        return FetchResult(entry.state, None)

    error = None
    state = None
    try:
        raw = reader(url, timeout)
        if not raw or not raw.strip():
            error = "empty response"
        else:
            state = parser(raw, date_format)
    except ParseError as e:
        error = f"malformed or unexpected response ({e})"
    except (OSError, ValueError) as e:  # includes URLError, timeouts, bad schemes
        error = str(e) or type(e).__name__

    if path:
        fallback = entry.state if entry else None
        cache.store(path, cache.CacheEntry(now, state is not None, state or fallback))
    if state is not None:
        return FetchResult(state, None)
    return FetchResult(entry.state if entry else None, f"Failed to get data from {url}: {error}")
