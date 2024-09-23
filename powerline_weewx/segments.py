from __future__ import unicode_literals, division, absolute_import, print_function

from collections import namedtuple

from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring

_WeeWXKey = namedtuple("Key", "weewx_url")

cumulus_fields = {
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

parameter_unit_map = {
    "outTemp": "temperature",
    "outHumidity": "relative",
    "dewpoint": "temperature",
    "windSpeed_avg": "speed",
    "windSpeed": "speed",
    "rainRate": "rain_rate",
    "dayRain": "rain",
    "barometer": "pressure",
    "rain_month": "rain",
    "rain_year": "rain",
    "rain_yesterday": "rain",
    "inTemp": "temperature",
    "inHumidity": "relative",
    "windchill": "temperature",
    "temperature_trend": "temperature",
    "outTemp_max": "temperature",
    "outTemp_min": "temperature",
    "windSpeed_max": "speed",
    "windGust_max": "speed",
    "pressure_max": "pressure",
    "pressure_min": "pressure",
    "10_min_high_gust": "speed",
    "heatindex": "temperature",
    "humidex": "temperature",
    "radiation": "radiation",
    "rain_hour": "rain",
}

non_numeric_parameters = ["windDir_compass"]


class WeeWXSegment(KwThreadedSegment):
    interval = 150

    @staticmethod
    def key(weewx_url="", **kwargs):
        return _WeeWXKey(weewx_url)

    def compute_state(self, key):
        if not key.weewx_url:
            return None
        url = key.weewx_url
        raw_response = urllib_read(url)
        if not raw_response:
            self.error("Failed to get response")
            return None
        parameters = raw_response.split()
        measurements = dict()
        try:
            for parameter, index in cumulus_fields.items():
                if parameter not in non_numeric_parameters:
                    measurements[parameter] = float(parameters[index])
                else:
                    measurements[parameter] = parameters[index]
        except (KeyError, ValueError):
            self.exception(
                "WeeWX returned malformed or unexpected response: {0}",
                repr(raw_response),
            )
            return None
        return measurements

    @staticmethod
    def render_one(
        measurements,
        parameters=None,
        temp_unit="°C",
        pressure_unit="mbar",
        speed_unit="km/h",
        rain_unit="mm",
        rain_rate_unit="mm/h",
        radiation_unit="W/m²",
        **kwargs,
    ):
        unit_map = {
            "pressure": pressure_unit,
            "radiation": radiation_unit,
            "rain": rain_unit,
            "rain_rate": rain_rate_unit,
            "relative": "%",
            "speed": speed_unit,
            "temperature": temp_unit,
        }
        if not measurements:
            return None
        if not parameters:
            parameters = ["outTemp"]
        groups = list()
        for parameter in parameters[0:-1]:
            groups.append(
                {
                    "contents": f"{measurements.get(parameter, '')}{unit_map.get(parameter_unit_map.get(parameter), '')} ",
                    "highlight_groups": ["weather"],
                }
            )
        groups.append(
            {
                "contents": f"{measurements.get(parameters[-1], '')}{unit_map.get(parameter_unit_map.get(parameters[-1]), '')}",
                "highlight_groups": ["weather"],
            }
        )
        return groups


weewx = with_docstring(
    WeeWXSegment(),
    """Return weather from WeeWX.

:param str weewx_url:
    url to the WeeWX instance

Highlight groups used: ``weather_conditions`` or ``weather``, ``weather_temp_gradient`` (gradient) or ``weather``.
""",
)
