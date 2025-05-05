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

# Configuration

The PWS segment is currently only compatible with the [Cumulus Realtime Format](https://www.cumuluswiki.org/a/Realtime.txt)
format. When your station is using [WeeWX](https://weewx.com/) for example,
[this](https://github.com/matthewwall/weewx-crt/) excellent extension can be
used for outputting weather data in the CRT-format.

The segment also uses some extra highlight groups. These highlight groups can be
easily defined in for example `.config/powerline/colorschemes/default.json`:
```
{
    "groups": {
        "pws":                    { "fg": "gray8", "bg": "gray0", "attrs": [] },
        "pws_uv_gradient":        { "fg": "green_yellow_orange_red", "bg": "gray0", "attrs": [] },
        "pws_temp_gradient":      { "fg": "blue_red", "bg": "gray0", "attrs": [] }
    }
}
```

After this you can activate the segment by adding it to your segment
configuration, for example in `.config/powerline/themes/tmux/default.json`:
```
{
    "function": "powerline_pws.pws",
    "args": {
      "pws_url": "<URL_TO_YOUR_PWS>"
    }
}
```

The minimum configuration needs a url to your PWS. This will only show the
outdoor temperature. You can define which measurements to show using the
`parameters`-parameter:
```
{
    "function": "powerline_pws.pws",
    "args": {
      "pws_url": "<URL_TO_YOUR_PWS>",
      "parameters": ["dayRain", "outTemp", "barometer", "outHumidity"]
    }
}
```

In this example, the segment is configured two times to show different data from
different weather stations. A label is added to every station to be able to
distinguish the data:
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
