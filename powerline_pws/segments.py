import os
from collections import namedtuple
from urllib.parse import unquote, urlparse

from powerline.lib.threaded import KwThreadedSegment
from powerline.lib.url import urllib_read
from powerline.segments import with_docstring

from .parsers import DEFAULT_DATE_FORMAT, PARSERS, ParseError
from .render import build_segments

_PWSKey = namedtuple("Key", "pws_url station_type date_format")

# Legacy per-category unit label arguments.
_UNIT_ARGS = {
    "temperature": "temp_unit",
    "pressure": "pressure_unit",
    "speed": "speed_unit",
    "rain": "rain_unit",
    "rain_rate": "rain_rate_unit",
    "radiation": "radiation_unit",
}
_RENDER_ARGS = (
    "parameters", "label", "format", "unit_system", "source_unit_system",
    "show_units", "icons", "gradients", "temp_coldest", "temp_hottest",
    "stale_after", "hide_stale",
)  # fmt: skip


def read_source(url):
    """Read the station data from an http(s) url, ``file://`` url or local path."""
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        return urllib_read(url)
    if parsed.scheme == "file":
        path = unquote(parsed.path)
    elif parsed.scheme == "":
        path = os.path.expanduser(url)
    else:
        raise ValueError(f"unsupported url scheme: {parsed.scheme!r}")
    with open(path, encoding="utf-8") as handle:
        return handle.read()


class PWSSegment(KwThreadedSegment):
    # Can be overridden per segment with the ``interval`` argument.
    interval = 150

    @staticmethod
    def key(pws_url="", station_type="cumulus", date_format=DEFAULT_DATE_FORMAT, **kwargs):
        return _PWSKey(pws_url, station_type, date_format)

    def compute_state(self, key):
        if not key.pws_url:
            return None
        parser = PARSERS.get(key.station_type)
        if parser is None:
            self.error("Unknown station_type {0!r}, expected one of {1}", key.station_type, sorted(PARSERS))
            return None
        try:
            raw_response = read_source(key.pws_url)
        except (OSError, ValueError) as e:
            self.error("Failed to read {0}: {1}", key.pws_url, e)
            return None
        if not raw_response:
            self.error("Failed to get response")
            return None
        try:
            return parser(raw_response, key.date_format)
        except ParseError as e:
            self.error("PWS returned malformed or unexpected response ({0}): {1}", e, repr(raw_response))
            return None

    def render_one(self, state, **kwargs):
        options = {name: kwargs[name] for name in _RENDER_ARGS if name in kwargs}
        options["unit_overrides"] = {category: kwargs.get(arg) for category, arg in _UNIT_ARGS.items()}
        try:
            return build_segments(state, **options)
        except (ValueError, TypeError, KeyError) as e:
            self.error("Invalid PWS segment configuration: {0}", e)
            return None


pws = with_docstring(
    PWSSegment(),
    """Return weather from a PWS (personal weather station).

:param str pws_url:
    http(s) url, ``file://`` url or local path of the station data
:param str station_type:
    Format of the station data. Currently only ``cumulus`` (default).
:param list parameters:
    Measurements to show, e.g. ``["outTemp", "UV"]``. Default ``["outTemp"]``.
:param str format:
    Format string such as ``"{outTemp} {outHumidity}"``. Overrides ``parameters``.
    A format spec can be used for numbers, e.g. ``"{outTemp:.0f}"``.
:param str label:
    Optional label to display before the measurements
:param str unit_system:
    ``metric`` (default) or ``imperial``
:param str source_unit_system:
    Unit system the station reports in, ``metric`` (default) or ``imperial``
:param bool show_units:
    Append units to values (default ``true``)
:param dict icons:
    Symbol to put before a measurement, e.g. ``{"outTemp": "T "}``
:param dict gradients:
    Per measurement ``[min, max]`` (metric units) or
    ``{"min": .., "max": .., "group": ..}``; ``null`` disables a gradient
:param int temp_coldest:
    Temperature (°C) at the cold end of the temperature gradient (default -30)
:param int temp_hottest:
    Temperature (°C) at the hot end of the temperature gradient (default 40)
:param int stale_after:
    Seconds after which the station data is considered stale (default 900,
    ``0`` disables). The station timestamp is read as local time.
:param bool hide_stale:
    Hide the segment instead of highlighting it when data is stale
:param str date_format:
    ``strptime`` date format of the station date (default ``%d/%m/%y``)
:param int interval:
    Seconds between updates (default 150)
:param str temp_unit:
    Override the temperature unit label (also ``pressure_unit``, ``speed_unit``,
    ``rain_unit``, ``rain_rate_unit`` and ``radiation_unit``)

Divider highlight group used: ``background:divider``.

Highlight groups used: ``pws_stale`` (when data is stale),
``pws_temp_gradient``, ``pws_uv_gradient``, ``pws_humidity_gradient``,
``pws_wind_gradient`` (gradients) or ``pws``.
""",
)
