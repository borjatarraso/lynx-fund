# Metrics catalog

What lynx-fund measures, grouped by report section. Math lives in
`lynx_fund/metrics/calculator.py`; per-metric metadata (and the `--explain`
text) in `lynx_fund/metrics/explanations.py`; the typed results in
`lynx_fund/models.py`.

| Section | `calc_*` | Metrics (representative) |
|---------|----------|--------------------------|
| Costs | `calc_costs` | Expense ratio (TER), management fee, bid-ask spread, est. $ cost per $10k/yr, front/back loads, 12b-1 |
| Income | `calc_income` | Trailing dividend yield, SEC 30-day yield, distribution frequency, accumulating vs distributing policy |
| Liquidity / size | `calc_liquidity` | AUM, fund-size tier, avg daily volume, avg daily $ volume, fund age, shares outstanding |
| Performance | `calc_performance` | 1M/3M/YTD/1Y/3Y/5Y/10Y returns, CAGR since inception, Sharpe (1Y/3Y), Sortino (3Y) |
| Allocation | `calc_allocation` | Holdings count, top-10 concentration, Herfindahl (HHI) by sector, sector & country breakdown |
| Risk | `calc_risk` | Volatility (1Y/3Y), max drawdown (3Y), beta (3Y), tracking error / difference vs benchmark, R² |
| Verdict | `build_verdict` | 0–100 score across Costs, Liquidity, Performance, Diversification, Risk |

## Relevance by fund size

`metrics/relevance.py` marks each metric `CRITICAL` / `RELEVANT` / `CONTEXTUAL`
/ `IRRELEVANT` for a given `FundSizeTier` (from `models.classify_tier(aum)`):
e.g. tiny funds de-emphasize Sharpe/Sortino/tracking metrics, large funds
de-emphasize spread.

## Conventions

- Every metric is `None` when it can't be computed; renderers print `—`.
- Metric ids are stable identifiers shared by `explanations.py`, `relevance.py`,
  and `--explain` — keep them in sync.
- Vocabulary is mutual-/index-fund oriented (loads, 12b-1, capital-gains
  distributions, manager tenure, persistence), matching the resolver's scope.
