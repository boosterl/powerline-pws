"""Turn station measurements into Powerline segment dictionaries.

This module has no dependency on Powerline itself so it is easy to test.
"""
import string
import time
from collections.abc import Mapping
from typing import Any

from .parsers import StationState, Value
from .units import METRIC, PARAMETER_CATEGORY, UNIT_LABELS, UNIT_SYSTEMS, convert

DIVIDER_GROUP = "background:divider"
UV_MAX = 11

# Gradient defaults: parameter -> (highlight group, minimum, maximum).
# Bounds are always expressed in metric units.
_TEMP = ("pws_temp_gradient", -30.0, 40.0)
_HUMIDITY = ("pws_humidity_gradient", 0.0, 100.0)
_WIND = ("pws_wind_gradient", 0.0, 80.0)
DEFAULT_GRADIENTS: dict[str, tuple[str, float, float]] = {
    "inTemp": _TEMP,
    "outTemp": _TEMP,
    "UV": ("pws_uv_gradient", 0.0, float(UV_MAX)),
    "outHumidity": _HUMIDITY,
    "inHumidity": _HUMIDITY,
    "windSpeed": _WIND,
    "windSpeed_avg": _WIND,
    "windGust_max": _WIND,
}


def gradient_level(value: float, minimum: float, maximum: float) -> float:
    """Map ``value`` to 0-100, clamped. Degenerate ranges give 0."""
    if maximum <= minimum or value <= minimum:
        return 0
    if value >= maximum:
        return 100
    return (value - minimum) * 100.0 / (maximum - minimum)


def _resolve_gradients(
    overrides: Mapping[str, Any] | None, temp_coldest: float, temp_hottest: float
) -> dict[str, tuple[str, float, float]]:
    gradients = dict(DEFAULT_GRADIENTS)
    for name in ("inTemp", "outTemp"):
        gradients[name] = (_TEMP[0], temp_coldest, temp_hottest)
    for name, spec in (overrides or {}).items():
        if not spec:  # null/false disables the gradient
            gradients.pop(name, None)
        elif isinstance(spec, Mapping):
            default = gradients.get(name, (f"pws_{name}_gradient", 0.0, 100.0))
            gradients[name] = (
                spec.get("group", default[0]),
                float(spec.get("min", default[1])),
                float(spec.get("max", default[2])),
            )
        else:
            low, high = spec
            group = gradients.get(name, (f"pws_{name}_gradient",))[0]
            gradients[name] = (group, float(low), float(high))
    return gradients


def format_value(value: Value, spec: str = "") -> str:
    if isinstance(value, float):
        return format(value, spec) if spec else str(round(value, 1))
    try:
        return format(value, spec)
    except ValueError:
        return str(value)


def is_stale(state: StationState, stale_after: float, now: float | None = None) -> bool:
    if not stale_after or state.timestamp is None:
        return False
    return (time.time() if now is None else now) - state.timestamp > stale_after


def build_segments(
    state: StationState | None,
    parameters: list[str] | None = None,
    label: str | None = None,
    format: str | None = None,
    unit_system: str = METRIC,
    source_unit_system: str = METRIC,
    show_units: bool = True,
    unit_overrides: Mapping[str, str] | None = None,
    icons: Mapping[str, str] | None = None,
    gradients: Mapping[str, Any] | None = None,
    temp_coldest: float = -30,
    temp_hottest: float = 40,
    stale_after: float = 900,
    hide_stale: bool = False,
    now: float | None = None,
) -> list[dict[str, Any]] | None:
    """Build the Powerline segments, or ``None`` when nothing should be shown.

    Raises ``ValueError`` for an invalid ``format`` or unit system.
    """
    if unit_system not in UNIT_SYSTEMS or source_unit_system not in UNIT_SYSTEMS:
        raise ValueError(f"unit systems must be one of {UNIT_SYSTEMS}")
    if not state or not state.measurements:
        return None
    stale = is_stale(state, stale_after, now)
    if stale and hide_stale:
        return None

    if not format:
        format = " ".join(f"{{{p}}}" for p in (parameters or ["outTemp"]))
    labels = dict(UNIT_LABELS[unit_system])
    labels.update({k: v for k, v in (unit_overrides or {}).items() if v})
    icons = icons or {}
    gradient_specs = _resolve_gradients(gradients, temp_coldest, temp_hottest)

    segments: list[dict[str, Any]] = []

    def add(contents: str, groups: list[str], level: float | None = None) -> None:
        if stale:
            groups = ["pws_stale"] + groups
        segment: dict[str, Any] = {
            "contents": contents,
            "highlight_groups": groups,
            "divider_highlight_group": DIVIDER_GROUP,
        }
        if level is not None:
            segment["gradient_level"] = level
        segments.append(segment)

    if label:
        add(f"{label} ", ["pws"])

    for literal, field, spec, _conversion in string.Formatter().parse(format):
        if literal:
            add(literal, ["pws"])
        if field is None:
            continue
        value = state.measurements.get(field)
        if value is None:
            continue
        category = PARAMETER_CATEGORY.get(field)
        groups = ["pws"]
        level = None
        if isinstance(value, float):
            gradient = gradient_specs.get(field)
            if gradient:
                metric_value = convert(value, category, source_unit_system, METRIC)
                level = gradient_level(metric_value, gradient[1], gradient[2])
                groups = [gradient[0], "pws"]
            value = convert(value, category, source_unit_system, unit_system)
        contents = icons.get(field, "") + format_value(value, spec)
        if show_units:
            contents += labels.get(category, "")
        add(contents, groups, level)
    return segments or None
