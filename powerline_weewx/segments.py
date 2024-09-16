from __future__ import (unicode_literals, division, absolute_import, print_function)

from collections import namedtuple

from powerline.lib.url import urllib_read, urllib_urlencode
from powerline.lib.threaded import KwThreadedSegment
from powerline.segments import with_docstring

_WeeWXKey = namedtuple('Key', 'weewx_url')

cumulus_fields = {
    'outTemp': 2,
    'outHumidity': 3,
    'windSpeed_avg': 5,
    'windSpeed': 6,
    'barometer': 10,
    'windDir_compass': 11,
    'UV': 43,
}

parameter_unit_map = {
    'outTemp': 'temperature',
    'outHumidity': 'relative',
    'windSpeed': 'speed',
    'windSpeed_avg': 'speed',
    'barometer': 'pressure',
}

non_numeric_parameters = ["windDir_compass"]


class WeeWXSegment(KwThreadedSegment):
    interval = 150

    @staticmethod
    def key(weewx_url='', **kwargs):
        return _WeeWXKey(weewx_url)

    def compute_state(self, key):
        if not key.weewx_url:
            return None
        url = key.weewx_url
        raw_response = urllib_read(url)
        if not raw_response:
            self.error('Failed to get response')
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
            self.exception('WeeWX returned malformed or unexpected response: {0}', repr(raw_response))
            return None
        return measurements

    @staticmethod
    def render_one(measurements, parameters=None, temp_unit='°C', pressure_unit='mbar', speed_unit='km/h', rain_unit='mm', rain_rate_unit='mm/h', radiation_unit='W/m²', **kwargs):
        unit_map = {
            'temperature': temp_unit,
            'pressure': pressure_unit,
            'speed': speed_unit,
            'relative': '%',
        }
        if not measurements:
            return None
        if not parameters:
            parameters = ["outTemp"]
        groups = list()
        for parameter in parameters[0:-1]:
            groups.append({
                'contents': f"{measurements.get(parameter, '')}{unit_map.get(parameter_unit_map.get(parameter), '')} ",
                'highlight_groups': ['weather'],
            })
        groups.append({
            'contents': f"{measurements.get(parameters[-1], '')}{unit_map.get(parameter_unit_map.get(parameters[-1]), '')}",
            'highlight_groups': ['weather'],
        })
        return groups


weewx = with_docstring(WeeWXSegment(),
'''Return weather from WeeWX.

:param str weewx_url:
    url to the WeeWX instance

Highlight groups used: ``weather_conditions`` or ``weather``, ``weather_temp_gradient`` (gradient) or ``weather``.
''')
