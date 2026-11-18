from collections import namedtuple

from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring

from .parsers import DEFAULT_DATE_FORMAT, PARSERS
from .render import build_segments
from .source import DEFAULT_RETRY_INTERVAL, DEFAULT_TIMEOUT, fetch_state

_PWSKey = namedtuple("Key", "pws_url station_type date_format timeout cache silent")

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


class PWSSegment(KwThreadedSegment):
    # Can be overridden per segment with the ``interval`` argument.
    interval = 150

    @staticmethod
    def key(
        pws_url="",
        station_type="cumulus",
        date_format=DEFAULT_DATE_FORMAT,
        timeout=DEFAULT_TIMEOUT,
        cache=True,
        silent=True,
        **kwargs,
    ):
        return _PWSKey(pws_url, station_type, date_format, timeout, cache, silent)

    def compute_state(self, key):
        if not key.pws_url:
            return None
        parser = PARSERS.get(key.station_type)
        if parser is None:
            self.error("Unknown station_type {0!r}, expected one of {1}", key.station_type, sorted(PARSERS))
            return None
        result = fetch_state(
            key.pws_url,
            key.station_type,
            parser,
            key.date_format,
            timeout=key.timeout,
            interval=self.interval,
            retry_interval=DEFAULT_RETRY_INTERVAL,
            use_cache=key.cache,
        )
        if result.error:
            # Network trouble is expected on a laptop; keep it quiet unless asked.
            (self.debug if key.silent else self.error)(result.error)
        return result.state

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
:param float timeout:
    Seconds to wait for the station before giving up (default 3)
:param bool cache:
    Keep the last data in ``$XDG_CACHE_HOME/powerline-pws`` so that short-lived
    Powerline processes (no ``powerline-daemon``) do not fetch on every refresh,
    and can show the last known data while offline (default ``true``)
:param bool silent:
    Log fetch failures at debug level instead of error level (default ``true``)
:param str temp_unit:
    Override the temperature unit label (also ``pressure_unit``, ``speed_unit``,
    ``rain_unit``, ``rain_rate_unit`` and ``radiation_unit``)

Divider highlight group used: ``background:divider``.

Highlight groups used: ``pws_stale`` (when data is stale),
``pws_temp_gradient``, ``pws_uv_gradient``, ``pws_humidity_gradient``,
``pws_wind_gradient`` (gradients) or ``pws``.
""",
)
