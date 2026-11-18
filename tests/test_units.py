import pytest

from powerline_pws.units import convert


def test_same_system_is_identity():
    assert convert(12.5, "temperature", "metric", "metric") == 12.5


@pytest.mark.parametrize(
    "category,metric,imperial",
    [
        ("temperature", 100.0, 212.0),
        ("speed", 1.609344, 1.0),
        ("rain", 25.4, 1.0),
        ("rain_rate", 25.4, 1.0),
        ("pressure", 33.8638866667, 1.0),
    ],
)
def test_round_trip(category, metric, imperial):
    assert convert(metric, category, "metric", "imperial") == pytest.approx(imperial)
    assert convert(imperial, category, "imperial", "metric") == pytest.approx(metric)


def test_unconvertible_categories_unchanged():
    assert convert(50.0, "relative", "metric", "imperial") == 50.0
    assert convert(3.0, None, "metric", "imperial") == 3.0
