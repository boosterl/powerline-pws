"""Tiny on-disk cache so short-lived Powerline processes can reuse station data.

Without ``powerline-daemon`` every status line refresh is a new process, so the
in-memory cache of the threaded segment is lost. This cache survives that.
"""
import contextlib
import hashlib
import json
import os
import tempfile
import time
from typing import Any, NamedTuple

from .parsers import StationState


class CacheEntry(NamedTuple):
    #: Time of the last fetch attempt (success or failure).
    attempted_at: float
    #: Whether that attempt succeeded.
    ok: bool
    #: Last successfully fetched state, if any (may be older than ``attempted_at``).
    state: StationState | None


def cache_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "powerline-pws")


def cache_path(url: str, station_type: str, directory: str | None = None) -> str:
    digest = hashlib.sha1(f"{station_type}\0{url}".encode()).hexdigest()
    return os.path.join(directory or cache_dir(), f"{digest}.json")


def load(path: str) -> CacheEntry | None:
    """Load a cache entry; any problem with the file just means 'no cache'."""
    try:
        with open(path, encoding="utf-8") as handle:
            data: dict[str, Any] = json.load(handle)
        state = data.get("state")
        return CacheEntry(
            float(data["attempted_at"]),
            bool(data["ok"]),
            StationState(dict(state["measurements"]), state["timestamp"]) if state else None,
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def store(path: str, entry: CacheEntry) -> None:
    """Atomically write a cache entry. Failures are ignored (cache is optional)."""
    data = {
        "attempted_at": entry.attempted_at,
        "ok": entry.ok,
        "state": None
        if entry.state is None
        else {"measurements": entry.state.measurements, "timestamp": entry.state.timestamp},
    }
    tmp = None
    try:
        directory = os.path.dirname(path)
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.replace(tmp, path)
    except (OSError, TypeError, ValueError):
        if tmp:
            with contextlib.suppress(OSError):
                os.unlink(tmp)


def is_fresh(entry: CacheEntry, interval: float, retry_interval: float, now: float | None = None) -> bool:
    """Whether the cache entry is recent enough to skip a fetch."""
    age = (time.time() if now is None else now) - entry.attempted_at
    if age < 0:  # clock went backwards
        return False
    return age < (interval if entry.ok else retry_interval)
