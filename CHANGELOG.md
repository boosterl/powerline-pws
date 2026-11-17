# Changelog

## Unreleased

- Fix crash on truncated/garbage responses; log a clear error instead.
- Support local files (`file://` or a path) as data source.
- Add `unit_system` / `source_unit_system` (metric or imperial).
- Add `format` string, `icons`, `show_units` and configurable `gradients`
  (new humidity and wind gradients).
- Add staleness detection (`stale_after`, `hide_stale`, `pws_stale` group).
- Add `station_type` and `date_format`; `interval` is configurable per segment.
- Skip missing measurements instead of showing a lone unit.
- Add tests, CI and type hints.
