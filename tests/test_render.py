import pytest

from powerline_pws.parsers import StationState
from powerline_pws.render import build_segments, gradient_level

NOW = 1_000_000.0


def state(timestamp=NOW, **measurements):
    return StationState(dict(measurements), timestamp)


def contents(segments):
    return "".join(s["contents"] for s in segments)


def test_default_shows_outtemp_with_gradient():
    (seg,) = build_segments(state(outTemp=10.0), now=NOW)
    assert seg["contents"] == "10.0°C"
    assert seg["highlight_groups"] == ["pws_temp_gradient", "pws"]
    assert seg["gradient_level"] == pytest.approx(40 * 100 / 70)


def test_parameters_are_space_separated():
    segs = build_segments(state(outTemp=1.0, outHumidity=80.0), parameters=["outTemp", "outHumidity"], now=NOW)
    assert contents(segs) == "1.0°C 80.0%"


def test_label():
    segs = build_segments(state(outTemp=1.0), label="X", now=NOW)
    assert contents(segs) == "X 1.0°C"


def test_format_string_and_spec():
    segs = build_segments(state(outTemp=12.345, outHumidity=70.0), format="T={outTemp:.0f} H={outHumidity}", now=NOW)
    assert contents(segs) == "T=12°C H=70.0%"


def test_missing_parameter_is_skipped_not_unit_only():
    segs = build_segments(state(outTemp=1.0), parameters=["outTemp", "nope"], now=NOW)
    assert "nope" not in contents(segs)
    assert contents(segs).startswith("1.0°C")


def test_only_missing_parameters_hides_segment():
    assert build_segments(state(outTemp=1.0), parameters=["nope"], now=NOW) is None


def test_invalid_format_raises():
    with pytest.raises(ValueError):
        build_segments(state(outTemp=1.0), format="{outTemp", now=NOW)


def test_no_state():
    assert build_segments(None) is None
    assert build_segments(StationState({}, None)) is None


def test_imperial_display():
    segs = build_segments(state(outTemp=100.0, windSpeed=1.609344), parameters=["outTemp", "windSpeed"], unit_system="imperial", now=NOW)
    assert contents(segs) == "212.0°F 1.0mph"


def test_gradient_uses_metric_value_for_imperial_source():
    (seg,) = build_segments(state(outTemp=104.0), source_unit_system="imperial", now=NOW)
    assert seg["gradient_level"] == pytest.approx(100)
    assert seg["contents"] == "104.0°F"


def test_unit_override_and_hide_units():
    (seg,) = build_segments(state(outTemp=1.0), unit_overrides={"temperature": "C"}, now=NOW)
    assert seg["contents"] == "1.0C"
    (seg,) = build_segments(state(outTemp=1.0), show_units=False, now=NOW)
    assert seg["contents"] == "1.0"


def test_icons():
    (seg,) = build_segments(state(outTemp=1.0), icons={"outTemp": "T "}, now=NOW)
    assert seg["contents"] == "T 1.0°C"


def test_string_values_do_not_crash_gradients():
    (seg,) = build_segments(state(outTemp="n/a"), now=NOW)
    assert seg["contents"] == "n/a°C"
    assert "gradient_level" not in seg


def test_custom_and_disabled_gradients():
    gradients = {"barometer": [980, 1040], "outTemp": None}
    segs = build_segments(state(outTemp=5.0, barometer=1010.0), parameters=["outTemp", "barometer"], gradients=gradients, now=NOW)
    assert segs[0]["highlight_groups"] == ["pws"]
    baro = segs[-1]
    assert baro["highlight_groups"] == ["pws_barometer_gradient", "pws"]
    assert baro["gradient_level"] == pytest.approx(50)


def test_stale_highlight_and_hide():
    old = NOW - 3600
    (seg,) = build_segments(state(timestamp=old, outTemp=1.0), now=NOW)
    assert seg["highlight_groups"][0] == "pws_stale"
    assert build_segments(state(timestamp=old, outTemp=1.0), hide_stale=True, now=NOW) is None
    (seg,) = build_segments(state(timestamp=old, outTemp=1.0), stale_after=0, now=NOW)
    assert seg["highlight_groups"][0] != "pws_stale"


def test_unknown_timestamp_is_never_stale():
    (seg,) = build_segments(state(timestamp=None, outTemp=1.0), now=NOW)
    assert "pws_stale" not in seg["highlight_groups"]


@pytest.mark.parametrize(
    "value,expected", [(-50, 0), (-30, 0), (5, 50), (40, 100), (99, 100)]
)
def test_gradient_level(value, expected):
    assert gradient_level(value, -30, 40) == pytest.approx(expected)


def test_degenerate_gradient_range():
    assert gradient_level(5, 10, 10) == 0
