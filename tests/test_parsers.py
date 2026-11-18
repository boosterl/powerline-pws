import time

import pytest

from powerline_pws.parsers import CUMULUS_FIELDS, ParseError, parse_cumulus, parse_timestamp


def realtime(date="18/10/08", clock="16:03:45", **overrides):
    fields = ["0"] * 52
    fields[0], fields[1] = date, clock
    fields[CUMULUS_FIELDS["windDir_compass"]] = "NNW"
    for name, value in overrides.items():
        fields[CUMULUS_FIELDS[name]] = str(value)
    return " ".join(fields)


def test_parses_numbers_and_strings():
    state = parse_cumulus(realtime(outTemp="8.4", outHumidity="84"))
    assert state.measurements["outTemp"] == 8.4
    assert state.measurements["outHumidity"] == 84.0
    assert state.measurements["windDir_compass"] == "NNW"


def test_timestamp():
    state = parse_cumulus(realtime())
    expected = time.mktime(time.strptime("2008-10-18 16:03:45", "%Y-%m-%d %H:%M:%S"))
    assert state.timestamp == expected


@pytest.mark.parametrize("date", ["18.10.08", "18-10-08"])
def test_other_date_separators(date):
    assert parse_timestamp(date, "16:03:45") is not None


def test_bad_timestamp_is_none():
    assert parse_cumulus(realtime(date="garbage")).timestamp is None


def test_truncated_response_raises():
    with pytest.raises(ParseError):
        parse_cumulus("18/10/08 16:03:45 8.4 84")


def test_garbage_raises():
    with pytest.raises(ParseError):
        parse_cumulus("<html>error</html>")
