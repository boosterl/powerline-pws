"""Unit categories, labels and conversions.

All internal computation (gradients, conversions) goes through metric units:
degC, km/h, hPa, mm, mm/h and W/m2.
"""
from collections.abc import Callable

METRIC = "metric"
IMPERIAL = "imperial"
UNIT_SYSTEMS = (METRIC, IMPERIAL)

UNIT_LABELS: dict[str, dict[str, str]] = {
    METRIC: {
        "temperature": "°C",
        "speed": "km/h",
        "pressure": "mbar",
        "rain": "mm",
        "rain_rate": "mm/h",
        "radiation": "W/m²",
        "relative": "%",
        "bearing": "°",
    },
    IMPERIAL: {
        "temperature": "°F",
        "speed": "mph",
        "pressure": "inHg",
        "rain": "in",
        "rain_rate": "in/h",
        "radiation": "W/m²",
        "relative": "%",
        "bearing": "°",
    },
}

# category -> (imperial -> metric, metric -> imperial)
_CONVERSIONS: dict[str, tuple[Callable[[float], float], Callable[[float], float]]] = {
    "temperature": (lambda f: (f - 32) * 5 / 9, lambda c: c * 9 / 5 + 32),
    "speed": (lambda mph: mph * 1.609344, lambda kmh: kmh / 1.609344),
    "pressure": (lambda inhg: inhg * 33.8638866667, lambda hpa: hpa / 33.8638866667),
    "rain": (lambda i: i * 25.4, lambda mm: mm / 25.4),
    "rain_rate": (lambda i: i * 25.4, lambda mm: mm / 25.4),
}

# measurement name -> unit category
PARAMETER_CATEGORY: dict[str, str] = {
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
    "10min_avg_wind_bearing": "bearing",
    "rain_hour": "rain",
}


def convert(value: float, category: str | None, source: str, target: str) -> float:
    """Convert ``value`` of ``category`` between unit systems."""
    if source == target or category not in _CONVERSIONS:
        return value
    to_metric, from_metric = _CONVERSIONS[category]
    if source == IMPERIAL:
        value = to_metric(value)
    if target == IMPERIAL:
        value = from_metric(value)
    return value
