# lynx_fund.core — package guidance

Domain layer: turn an identifier into data on disk and into a `FundReport`.
No rendering, no UI. See the package-root `lynx_fund/CLAUDE.md` and
`ARCHITECTURE.md`.

## Responsibility

Resolve/validate fund identifiers, fetch fund + news data from external sources,
persist and cache it, and orchestrate the multi-stage analysis.

## Public interface

- `ticker.resolve_identifier(identifier) -> (ticker, isin|None)`,
  `ticker.search_funds(query, limit)` (alias `search_etfs`),
  `ticker.is_isin(s)`, `ticker.NotAFundError`.
- `fetcher.fetch_info / fetch_profile / fetch_history / fetch_holdings /
  fetch_sector|country|asset_class_breakdown / fetch_benchmark_history`.
- `news.fetch_all_news(ticker, company_name) -> list[NewsArticle]`.
- `storage.set_mode(mode)`, `get_data_root`, `get_company_dir`, `save_json/
  load_json/save_text`, `has_cache`, `load_cached_report`, `drop_cache_*`,
  `list_cached_tickers`, `get_cache_age_hours`, `list_saved_analyses`.
- `analyzer.run_full_analysis(...)` and
  `analyzer.run_progressive_analysis(identifier, *, download_news, verbose,
  refresh, on_progress)`.

## Module-local conventions

- **The scope guard lives here.** `ticker.py` is the single place that decides
  what counts as a fund (MUTUALFUND/OEIC/SICAV/UCITS accepted; everything else
  raises `NotAFundError`). Keep that allow/reject list authoritative; downstream
  code assumes it has run.
- **Best-effort fetching.** `fetcher`/`news` catch upstream/`ImportError`
  failures and return `None` / empty defaults — never let a missing field crash
  the pipeline.
- **All disk I/O goes through `storage`.** Never `open()` data paths directly
  elsewhere; respect the `production` (`data/`) vs `testing` (`data_test/`)
  mode set via `set_mode()`.
- **Cache-first.** `analyzer` checks the cache before fetching; only `refresh`
  bypasses it. Preserve the staged `on_progress` callback contract so the
  TUI/GUI can render partial reports.
- `core` depends on `metrics.calculator` and `models`; it must not import the UI
  layers (`display`, `tui`, `gui`).
