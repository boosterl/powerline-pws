import pathlib

import pytest

from powerline_pws import cache
from powerline_pws.parsers import ParseError, StationState
from powerline_pws.source import fetch_state, read_source

STATE = StationState({"outTemp": 1.5}, 100.0)


def parser(raw, date_format):
    if raw == "bad":
        raise ParseError("nope")
    return STATE


class Reader:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = 0

    def __call__(self, url, timeout):
        self.calls += 1
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def fetch(reader, tmp_path, now, **kw):
    return fetch_state("u", "cumulus", parser, "%d/%m/%y", cache_directory=str(tmp_path), now=now, reader=reader, **kw)


def test_success_is_cached_and_reused(tmp_path):
    reader = Reader("ok")
    assert fetch(reader, tmp_path, 1000).state == STATE
    assert fetch(reader, tmp_path, 1100).state == STATE  # within interval, no 2nd read
    assert reader.calls == 1


def test_refetch_after_interval(tmp_path):
    reader = Reader("ok", "ok")
    fetch(reader, tmp_path, 1000)
    fetch(reader, tmp_path, 1200)
    assert reader.calls == 2


def test_failure_falls_back_to_last_good_state(tmp_path):
    reader = Reader("ok", OSError("offline"))
    fetch(reader, tmp_path, 1000)
    result = fetch(reader, tmp_path, 1200)
    assert result.state == STATE
    assert "offline" in result.error


def test_failure_is_not_retried_immediately(tmp_path):
    reader = Reader(OSError("offline"), "ok")
    first = fetch(reader, tmp_path, 1000)
    assert first.state is None and first.error
    again = fetch(reader, tmp_path, 1030)  # inside retry interval
    assert reader.calls == 1
    assert again.state is None and again.error is None
    assert fetch(reader, tmp_path, 1100).state == STATE  # retry window over


def test_parse_error_and_empty_response(tmp_path):
    assert "malformed" in fetch(Reader("bad"), tmp_path, 1000, use_cache=False).error
    assert "empty" in fetch(Reader("  "), tmp_path, 1000, use_cache=False).error


def test_no_cache_always_fetches(tmp_path):
    reader = Reader("ok", "ok")
    fetch(reader, tmp_path, 1000, use_cache=False)
    fetch(reader, tmp_path, 1001, use_cache=False)
    assert reader.calls == 2
    assert not list(tmp_path.iterdir())


def test_corrupt_cache_is_ignored(tmp_path):
    path = cache.cache_path("u", "cumulus", str(tmp_path))
    pathlib.Path(path).write_text("{not json")
    assert fetch(Reader("ok"), tmp_path, 1000).state == STATE


def test_unwritable_cache_dir_is_ignored(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("")
    result = fetch_state("u", "cumulus", parser, "", cache_directory=str(blocker / "sub"), now=1, reader=Reader("ok"))
    assert result.state == STATE


def test_read_local_file(tmp_path):
    path = tmp_path / "rt.txt"
    path.write_text("hello")
    assert read_source(str(path)) == "hello"
    assert read_source(path.as_uri()) == "hello"


def test_unsupported_scheme():
    with pytest.raises(ValueError):
        read_source("ftp://example.com/x")
