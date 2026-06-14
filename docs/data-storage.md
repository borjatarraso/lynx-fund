# Data storage & caching

All persistence is owned by `lynx_fund/core/storage.py`. Nothing else should
read or write the data directories directly.

## Modes

`set_mode(mode)` selects the root, held in the module-level `_MODE`:

| Mode | Root | Used by |
|------|------|---------|
| `production` | `data/` | normal runs (`lynx-fund -p`) |
| `testing` | `data_test/` | tests / `-t`; kept separate from real cache |

`cli.py` (and test fixtures in `tests/conftest.py`) call `set_mode()` once at
startup.

## On-disk layout

```
<root>/<TICKER>/
  reports/      saved FundReport JSON snapshots (latest reloaded from cache)
  news/         news_index.json + raw article text
  financials/   reserved (get_financials_dir) — currently unused
```

## Cache behaviour

- `core/analyzer.py` is **cache-first**: it loads a saved report before
  fetching; `--refresh` forces a fresh fetch.
- `get_cache_age_hours()` reports staleness by parsing the stored ISO timestamp.
- Cache management helpers: `has_cache`, `load_cached_report`,
  `list_cached_tickers`, `list_saved_analyses`, `drop_cache_ticker`,
  `drop_cache_all` (surfaced via `--list-cache` / `--drop-cache`).

## Serialization

`save_json` / `load_json` / `save_text` / `save_binary` are the only sanctioned
I/O helpers. Reports serialize the `models` dataclasses to JSON.
