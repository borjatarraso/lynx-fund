# Lynx Fund — API reference

## Public entry points

### `lynx_fund.core.analyzer.run_full_analysis(identifier, *, download_news=True, refresh=False)`

Return an `FundReport` for the given ticker or ISIN. Uses the on-disk
cache (in the directory configured by `set_mode`). Raises
`lynx_fund.core.ticker.NotAFundError` when the resolved instrument is
not a fund.

```python
from lynx_fund.core.storage import set_mode
from lynx_fund.core.analyzer import run_full_analysis

set_mode("production")
report = run_full_analysis("SPY")
print(report.profile.ticker, report.profile.aum)
print(report.verdict.verdict, report.verdict.overall_score)
```

### `lynx_fund.core.analyzer.run_progressive_analysis(...)`

Same inputs plus `on_progress: Callable[[str, FundReport], None] | None`.
The callback is invoked after each pipeline stage: `profile`, `costs`,
`income`, `liquidity`, `performance`, `allocation`, `risk`, `verdict`,
`news`, `complete`.

### `lynx_fund.core.ticker.resolve_identifier(identifier) -> (ticker, isin|None)`

Resolves + validates. Raises `NotAFundError` for stocks / mutual funds /
index tickers.

### `lynx_fund.core.ticker.search_etfs(query, limit=10) -> list[dict]`

Free-text search, filtered to ETF quote-type only.

### `lynx_fund.metrics.explanations.get_explanation(key) -> MetricExplanation | None`

Returns human-readable metadata for a metric key. `EXPLANATIONS` is the
full catalogue; `list_keys()` / `by_category()` are convenience helpers.

## Data models

See `lynx_fund/models.py`:

- `FundProfile` — ticker, name, ISIN, category, asset class, family,
  domicile, inception, benchmark, replication, distribution policy,
  AUM, tier.
- `FundReport` — profile + seven optional metric sections + holdings +
  news.
- `FundSizeTier` — enum (`Mega` / `Large` / `Mid` / `Small` / `Micro` /
  `Nano`) based on AUM thresholds.
- `CostMetrics`, `IncomeMetrics`, `LiquidityMetrics`,
  `PerformanceMetrics`, `AllocationMetrics`, `RiskProfile`, `Verdict`,
  `Holding`.

## Storage mode

Every API call reads/writes through `lynx_fund.core.storage`. Set the
mode before calling:

```python
from lynx_fund.core.storage import set_mode
set_mode("production")   # uses data/
set_mode("testing")      # uses data_test/ — never caches
```

## Plugin registration

The tool registers as a Suite agent via `pyproject.toml`:

```toml
[project.entry-points."lynx_investor_suite.agents"]
etf = "lynx_fund.plugin:register"
```

`lynx_fund.plugin.register()` returns a `SectorAgent` descriptor.
