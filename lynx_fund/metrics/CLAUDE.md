# lynx_fund.metrics — package guidance

Pure computation over fetched data: metric math, the verdict score, metric
metadata, and tier-aware relevance. No I/O, no rendering. See `ARCHITECTURE.md`.

## Responsibility

Take yfinance output + holdings and produce the typed metric sections of a
`FundReport`, the 0–100 verdict, the `--explain` metadata, and per-tier metric
emphasis.

## Public interface

- `calculator.calc_costs / calc_income / calc_liquidity / calc_performance /
  calc_allocation / calc_risk` → the matching `models` dataclasses.
- `calculator.build_verdict(report) -> Verdict` — five-category 0–100 score.
- `explanations.EXPLANATIONS` (dict by metric id),
  `explanations.get_explanation(key)`, `explanations.by_category()`.
- `relevance.relevance_for(metric_key, tier) -> Relevance`,
  `relevance.is_critical(key, tier)`.

## Module-local conventions

- **None-tolerant math.** Coerce inputs through the local numeric helpers
  (`_f`, `_pct`) and return `None` for any metric that can't be computed; callers
  and `display` rely on this.
- **Depends only on `models`.** No fetching, storage, or rendering here. If a
  calculation needs new data, add a fetcher in `core` and pass the result in.
- **Verbal assessments are translated.** Risk/verdict prose uses `_t(...)` from
  `lynx_investor_core.translations`; metric ids and category keys stay in
  English (they're identifiers, not display text).
- **Vocabulary is mutual-fund-oriented** (TER, loads, 12b-1, capital-gains
  distributions, manager tenure, persistence) — consistent with the resolver's
  fund-only scope. Keep new metrics in that domain.
- Metric ids in `explanations.py` must match the keys used by `relevance.py` and
  `--explain`; keep them in sync.
