from __future__ import unicode_literals, division, absolute_import, print_function

from collections import namedtuple

from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring

_PWSKey = namedtuple("Key", "pws_url")

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

gradient_calculators = {
    "inTemp": PWSSegment.temperature_gradient,
    "outTemp": PWSSegment.temperature_gradient,
    "UV": PWSSegment.ultraviolet_gradient,
}

gradient_map = {
    "inTemp": "pws_temp_gradient",
    "outTemp": "pws_temp_gradient",
    "UV": "pws_uv_gradient",
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


class PWSSegment(KwThreadedSegment):
    interval = 150

    @staticmethod
    def key(pws_url="", **kwargs):
        return _PWSKey(pws_url)

    def compute_state(self, key):
        if not key.pws_url:
            return None
        url = key.pws_url
        raw_response = urllib_read(url)
        if not raw_response:
            self.error("Failed to get response")
            return None
        parameters = raw_response.split()
        measurements = dict()
        try:
            for parameter, index in cumulus_fields.items():
                measurements[parameter] = self.map_measurement(parameters[index])
        except (KeyError, ValueError):
            self.exception(
                "PWS returned malformed or unexpected response: {0} {1}",
                repr(raw_response),
                parameter,
            )
            return None
        return measurements

    @staticmethod
    def map_measurement(measurement):
        try:
            return float(measurement)
        except ValueError:
            return measurement

    @staticmethod
    def render_one(
        measurements,
        parameters=None,
        label=None,
        temp_unit="°C",
        temp_coldest=-30,
        temp_hottest=40,
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
        if label:
            groups.append(
                {
                    "contents": f"{label} ",
                    "highlight_groups": ["pws"],
                    "divider_highlight_group": "background:divider",
                }
            )
        for parameter in parameters:
            last = parameter == parameters[-1]
            group = {
                "contents": f"{measurements.get(parameter, '')}{unit_map.get(parameter_unit_map.get(parameter), '')}{'' if last else ' '}",
                "highlight_groups": [gradient_map.get(parameter), "pws"],
                "divider_highlight_group": "background:divider",
            }
            gradient_calculator = gradient_calculators.get(parameter)
            if gradient_calculator:
                group["gradient_level"] = gradient_calculator(
                    measurements.get(parameter, 0),
                    temp_coldest=temp_coldest,
                    temp_hottest=temp_hottest,
                )
            groups.append(group)
        return groups

    @staticmethod
    def temperature_gradient(temperature, **kwargs):
        temp_coldest = kwargs.get("temp_coldest", -30)
        temp_hottest = kwargs.get("temp_hottest", 40)
        if temperature <= temp_coldest:
            return 0
        if temperature >= temp_hottest:
            return 100
        return (temperature - temp_coldest) * 100.0 / (temp_hottest - temp_coldest)

    @staticmethod
    def ultraviolet_gradient(index, **kwargs):
        if index >= 11:
            return 100
        return index * (100 / 11)


pws = with_docstring(
    PWSSegment(),
    """Return weather from PWS.

:param str pws_url:
    url to the PWS instance

:param str label:
    Optional label to display next to the segment

Divider highlight group used: ``background:divider``.

Highlight groups used: ``pws``, ``pws_uv_gradient`` (gradient) or ``pws``.
""",
)
