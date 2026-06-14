# Design notes — lynx-fund

The reasoning behind the choices that aren't obvious from reading a single file.
These are descriptive of the code as it stands today, not aspirational.

## Strict fund-only scope

`core/ticker.py` accepts only `MUTUALFUND` / `MUTUAL_FUND` / `OEIC` / `SICAV` /
`UCITS` quote types and rejects everything else (stocks, ETFs, ETNs, closed-end
funds, indices, currencies, crypto, futures, options) with a `NotAFundError`
that names the correct Suite tool. The rationale: each Suite agent owns one
instrument class, so the resolver is the single gate that keeps lynx-fund's
vocabulary (loads, 12b-1, capital-gains distributions, manager tenure) coherent.
The metric and explanation vocabulary in `metrics/` and `models.py` assumes this
guard has already run.

## Best-effort, None-tolerant pipeline

Every fetcher and calculator returns `None` (or an empty list / default
dataclass) when upstream data is missing, instead of raising. This keeps a
partial fund — common for small or foreign funds — renderable: `display.py`
prints `—` for `None`. Consequence to preserve: never assume a metric is
populated; guard before arithmetic, and keep new calculators on the same
None-fallback contract.

## Cache-first analysis with progressive stages

`core/analyzer.py` runs the analysis as ordered stages (profile → costs → … →
news → complete) and checks the on-disk cache before fetching. It accepts an
`on_progress(stage, report)` callback so the TUI/GUI can paint partial results
as they arrive. `--refresh` is the only way to bypass the cache. This is why all
persistence is funnelled through `core/storage.py` — the cache key (ticker dir)
must be computed in exactly one place.

## Two storage modes, global switch

`core/storage.py` keeps a module-level `_MODE` (`production` → `data/`,
`testing` → `data_test/`), set once by `cli.py` / fixtures via `set_mode()`.
Tests run in `testing` mode so they never touch the production cache and never
require the network. Disk layout per ticker: `<ROOT>/<TICKER>/{reports,news,
financials}/`.

## i18n by indirection

All user-visible strings pass through `t()` from
`lynx_investor_core.translations` (imported as `_t`) with an English default
argument. This lets `--language` translate rendered output without forking the
renderers. The default keeps English working even if a key is missing from a
translation table.

## Four UI modes over one core

`cli.py` dispatches to console (`display`), interactive (`interactive.py`),
Textual (`tui/`), and Tkinter (`gui/`). All four consume the same
`models.FundReport` and the same `core.analyzer`; they differ only in
presentation. Report-content changes should land in `models` + `metrics` +
`display` so every mode benefits, rather than in a single front-end.

## Suite integration

Shared concerns — themes, button debouncing, export footers, the language
widget, plugin registration — live in `lynx-investor-core` and are imported,
not reimplemented. `plugin.py` exposes the agent to the Suite via the
`lynx_investor_suite.agents` entry-point group.
