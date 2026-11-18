# Powerline PWS

A [Powerline](https://powerline.readthedocs.io/en/master/#) segment for showing
weather data from your PWS (Personal Weather Station).

![](screenshot.png)

# Installation

## Using pip

```
pip install powerline-pws
```
_Note: since [PEP 668](https://peps.python.org/pep-0668/) installing pip-packages
system-wide isn't supported by default anymore. This behaviour can be
overwritten using the `--break-system-packages`. Do this at your own risk._

## AUR

A PKGBUILD has been created for this package, available on the [AUR](https://aur.archlinux.org/packages/python-powerline-pws).

```
paru -S python-powerline-pws
```

# Configuration

# Configuration

The PWS segment is currently only compatible with the [Cumulus Realtime Format](https://www.cumuluswiki.org/a/Realtime.txt)
(`station_type: "cumulus"`, the default). When your station is using
[WeeWX](https://weewx.com/) for example,
[this](https://github.com/matthewwall/weewx-crt/) excellent extension can be
used for outputting weather data in the CRT-format. Other formats can be added
by registering a parser in `powerline_pws/parsers.py`.

The segment uses some extra highlight groups, defined for example in
`.config/powerline/colorschemes/default.json` (see
[examples/colorschemes-default.json](examples/colorschemes-default.json)):
```
{
    "groups": {
        "pws":                    { "fg": "gray8", "bg": "gray0", "attrs": [] },
        "pws_stale":              { "fg": "gray5", "bg": "gray0", "attrs": ["dim"] },
        "pws_uv_gradient":        { "fg": "green_yellow_orange_red", "bg": "gray0", "attrs": [] },
        "pws_temp_gradient":      { "fg": "blue_red", "bg": "gray0", "attrs": [] },
        "pws_humidity_gradient":  { "fg": "white_red", "bg": "gray0", "attrs": [] },
        "pws_wind_gradient":      { "fg": "green_yellow_red", "bg": "gray0", "attrs": [] }
    }
}
```
Only `pws` is required; gradient groups that are not defined fall back to it.

Activate the segment in your theme, for example in
`.config/powerline/themes/tmux/default.json`:
```
{
    "function": "powerline_pws.pws",
    "args": {
      "pws_url": "<URL_TO_YOUR_PWS>"
    }
}
```
`pws_url` can be an `http(s)` URL, a `file://` URL or a local path. By default
only the outdoor temperature is shown.

## Arguments

| Argument | Default | Description |
|---|---|---|
| `pws_url` | | Location of the station data |
| `station_type` | `"cumulus"` | Format of the station data |
| `parameters` | `["outTemp"]` | Measurements to show, space separated |
| `format` | | Format string, e.g. `"{outTemp:.0f} {outHumidity}"`. Overrides `parameters` |
| `label` | | Text shown before the measurements |
| `unit_system` | `"metric"` | `"metric"` or `"imperial"` |
| `source_unit_system` | `"metric"` | Unit system the station reports in |
| `show_units` | `true` | Append units to values |
| `icons` | `{}` | Symbol before a measurement, e.g. `{"outTemp": "🌡 "}` |
| `gradients` | | Per measurement `[min, max]` (metric) or `{"min", "max", "group"}`; `null` disables |
| `temp_coldest` / `temp_hottest` | `-30` / `40` | Bounds (°C) of the temperature gradient |
| `stale_after` | `900` | Seconds before data is considered stale (`0` disables) |
| `hide_stale` | `false` | Hide the segment when stale instead of using `pws_stale` |
| `date_format` | `"%d/%m/%y"` | `strptime` format of the station date |
| `interval` | `150` | Seconds between updates |
| `timeout` | `3` | Seconds to wait for the station |
| `cache` | `true` | Keep the last data on disk (see below) |
| `silent` | `true` | Log fetch failures at debug instead of error level |
| `temp_unit`, `pressure_unit`, `speed_unit`, `rain_unit`, `rain_rate_unit`, `radiation_unit` | | Override the unit label |

Staleness uses the date/time in the station data, read as local time of the
machine running Powerline.

Available measurements: `outTemp`, `outHumidity`, `dewpoint`, `windSpeed_avg`,
`windSpeed`, `rainRate`, `dayRain`, `barometer`, `windDir_compass`,
`pressure_trend`, `rain_month`, `rain_year`, `rain_yesterday`, `inTemp`,
`inHumidity`, `windchill`, `temperature_trend`, `outTemp_max`, `outTemp_min`,
`windSpeed_max`, `windGust_max`, `pressure_max`, `pressure_min`,
`10_min_high_gust`, `heatindex`, `humidex`, `UV`, `radiation`,
`10min_avg_wind_bearing`, `rain_hour`.

## Examples

Choose measurements:
```
{
    "function": "powerline_pws.pws",
    "args": {
      "pws_url": "<URL_TO_YOUR_PWS>",
      "parameters": ["dayRain", "outTemp", "barometer", "outHumidity"]
    }
}
```

Imperial units with a custom format:
```
{
    "function": "powerline_pws.pws",
    "args": {
      "pws_url": "/var/www/realtime.txt",
      "unit_system": "imperial",
      "format": "{outTemp:.0f} / {windSpeed:.0f}"
    }
}
```

Two stations, each with a label:
```
{
	"function": "powerline_pws.pws",
	"args": {
	  "pws_url": "<URL_TO_PWS_1>",
	  "label": "🏝️",
	  "parameters": ["outTemp", "UV", "outHumidity"]
	}
},
{
	"function": "powerline_pws.pws",
	"args": {
	  "pws_url": "<URL_TO_PWS_2>",
	  "label": "🏠",
	  "parameters": ["inTemp", "outTemp", "barometer", "outHumidity"]
	}
}
```

# Development

```
pip install -e ".[test]"
ruff check .
pytest
```

## Slow or missing network

Fetching has a short `timeout` (3 seconds). The last data is cached in
`$XDG_CACHE_HOME/powerline-pws/` (default `~/.cache/powerline-pws/`), so:

- when Powerline runs without `powerline-daemon` (a new process per refresh),
  the network is only used once per `interval`, and after a failure not again
  for 60 seconds, instead of on every refresh;
- while offline the last known data stays visible, highlighted with
  `pws_stale` once older than `stale_after`.

If tmux shows `<'... powerline ...' not ready>`, the render command is taking
too long: that's tmux's placeholder for a `#(...)` command that has not
produced output yet. Starting `powerline-daemon` also avoids it.
Set `"cache": false` to disable the disk cache, `"silent": false` to log fetch
failures as errors.
