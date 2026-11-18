"""Parsers turning the raw text of a weather station into measurements.

A parser is a callable ``parse(raw, date_format) -> StationState``. New station
types can be supported by adding a parser to ``PARSERS``.
"""
import re
import time
from collections.abc import Callable
from typing import NamedTuple

Value = float | str


class ParseError(Exception):
    """Raised when the station data is malformed."""


class StationState(NamedTuple):
    measurements: dict[str, Value]
    #: Seconds since the epoch (station time read as local time), if known.
    timestamp: float | None


# Measurement name -> column in the Cumulus realtime.txt file.
CUMULUS_FIELDS: dict[str, int] = {
    "outTemp": 2,
    "outHumidity": 3,
    "dewpoint": 4,
    "windSpeed_avg": 5,
    "windSpeed": 6,
    "rainRate": 8,
    "dayRain": 9,
    "barometer": 10,
    "windDir_compass": 11,
    "pressure_trend": 18,
    "rain_month": 19,
    "rain_year": 20,
    "rain_yesterday": 21,
    "inTemp": 22,
    "inHumidity": 23,
    "windchill": 24,
    "temperature_trend": 25,
    "outTemp_max": 26,
    "outTemp_min": 28,
    "windSpeed_max": 30,
    "windGust_max": 32,
    "pressure_max": 34,
    "pressure_min": 36,
    "10_min_high_gust": 40,
    "heatindex": 41,
    "humidex": 42,
    "UV": 43,
    "radiation": 45,
    "10min_avg_wind_bearing": 46,
    "rain_hour": 47,
}

DEFAULT_DATE_FORMAT = "%d/%m/%y"


def _to_value(text: str) -> Value:
    try:
        return float(text)
    except ValueError:
        return text


def parse_timestamp(date: str, clock: str, date_format: str = DEFAULT_DATE_FORMAT) -> float | None:
    """Parse the station date and time, returning ``None`` when unparsable.

    Cumulus lets users pick the date separator, so any of ``. / -`` is accepted.
    """
    date = re.sub(r"[./-]", "/", date)
    date_format = re.sub(r"[./-]", "/", date_format)
    try:
        parsed = time.strptime(f"{date} {clock}", f"{date_format} %H:%M:%S")
        return time.mktime(parsed)
    except (ValueError, OverflowError):
        return None


def parse_cumulus(raw: str, date_format: str = DEFAULT_DATE_FORMAT) -> StationState:
    parts = raw.split()
    needed = max(CUMULUS_FIELDS.values()) + 1
    if len(parts) < needed:
        raise ParseError(f"expected at least {needed} fields, got {len(parts)}")
    measurements = {name: _to_value(parts[index]) for name, index in CUMULUS_FIELDS.items()}
    return StationState(measurements, parse_timestamp(parts[0], parts[1], date_format))


PARSERS: dict[str, Callable[[str, str], StationState]] = {
    "cumulus": parse_cumulus,
}
