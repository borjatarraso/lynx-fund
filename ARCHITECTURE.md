# Architecture — lynx-fund

A single Python package (`lynx_fund`) that turns a fund identifier into a scored
report, rendered in one of four UI modes. This document describes how the pieces
fit together. For design rationale see `DESIGN.md`; for guidance when editing a
specific area see the per-package `CLAUDE.md` files.

## Dataflow

```
identifier (ticker / ISIN / search term)
        │
        ▼
core.ticker.resolve_identifier ──► rejects non-funds (NotAFundError)
        │  (ticker, isin)
        ▼
core.analyzer.run_progressive_analysis        ◄── cache-first via core.storage
        │   stages, each filling part of the FundReport:
        │     profile ─ core.fetcher.fetch_profile
        │     costs/income/liquidity/performance/allocation/risk
        │           ─ metrics.calculator.calc_*  (+ build_verdict)
        │     news    ─ core.news.fetch_all_news
        │     passive ─ passive_checklist.run_passive_checklist
        │     tips    ─ tips.compose_tips
        ▼
models.FundReport  (one dataclass holding every section)
        │
        ▼
display.render_full_report   ─►  console / interactive / tui / gui
```

`core.fetcher` reads from **yfinance**; `core.news` reads **Yahoo Finance +
Google News RSS**; results are persisted by `core.storage` under `data/`
(production) or `data_test/` (testing).

## Module responsibilities

| Area | Module | Responsibility |
|------|--------|----------------|
| Dispatch | `cli.py` / `__main__.py` | Parse args, select mode, wire storage mode + language |
| Domain types | `models.py` | All dataclasses/enums; `classify_tier(aum)` |
| Resolve | `core/ticker.py` | Identifier → `(ticker, isin)`; fund-only scope guard |
| Fetch | `core/fetcher.py`, `core/news.py` | yfinance + RSS, best-effort decoding |
| Persist | `core/storage.py` | `data/` vs `data_test/`, cache read/write, JSON I/O |
| Analyze | `core/analyzer.py` | Orchestrate stages, cache-first, progress callback |
| Compute | `metrics/calculator.py` | All metric math + `build_verdict` |
| Explain | `metrics/explanations.py` | Metric metadata powering `--explain` |
| Filter | `metrics/relevance.py` | Tier-aware metric emphasis |
| Heuristics | `passive_checklist.py`, `tips.py` | Passive-investor checks & education |
| Render | `display.py` | Rich panels/tables; numeric formatters |
| UI modes | `interactive.py`, `tui/`, `gui/` | REPL, Textual, Tkinter front-ends |

## Import direction (no cycles)

```
cli ──► core.analyzer ──► core.{fetcher,news,storage,ticker}
   │                  └─► metrics.calculator ──► models
   ├──► display ──► models
   ├──► interactive ──► core.*, display, metrics.explanations
   ├──► tui.app ──► core.ticker, tui.themes
   ├──► gui.app ──► core.analyzer, display (runtime, threaded)
   └──► metrics.explanations
```

`core` never imports `metrics` back from `calculator`-consumers in a cycle;
`display` depends only on `models`; UI modes call into `core`/`display`, never
the reverse.

## External dependencies

- **`lynx-investor-core`** (Suite shared lib): `translations.t` (i18n),
  `themes` / `gui_themes` (TUI & Tkinter palettes), `debounce.ClickDebouncer`,
  `author_footer`, `lang_widget`, `plugins.SectorAgent`.
- **yfinance** — fund info, history, holdings, allocation, ISIN search.
- **rich** (console), **textual** (TUI), **tkinter** (GUI, stdlib).
- **feedparser / requests / beautifulsoup4** — news RSS + article fetch.
- **pandas / numpy** — return series & risk statistics.

## Packaging

One distribution, declared in `pyproject.toml`:

- console script `lynx-fund = lynx_fund.__main__:main`
- suite plugin `fund = lynx_fund.plugin:register` under
  `lynx_investor_suite.agents`
- `setuptools.packages.find` includes `lynx_fund*`

Because both entry points key off the `lynx_fund` package path, the package
must stay a single top-level package (see `CLAUDE.md` conventions).
