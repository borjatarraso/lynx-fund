# Data sources

Where lynx-fund gets its data. All external access is in `lynx_fund/core/`.

## yfinance (`core/fetcher.py`, `core/ticker.py`)

- **Fund info / profile** — `yf.Ticker(symbol).info`: name, quote type, AUM,
  expense ratio, yields, fund family, inception, manager fields.
- **Price history** — `yf.Ticker(symbol).history(period=...)` for return and
  risk series.
- **Holdings & allocation** — top holdings, sector / country / asset-class
  breakdowns (best-effort; many funds expose only part of this).
- **Identifier search / ISIN resolution** — `yf.Search(...)`, filtered to fund
  quote types (`MUTUALFUND`, `OEIC`, `SICAV`, `UCITS`, …).

The resolver accepts only those fund quote types; stocks, ETFs/ETNs, closed-end
funds and indices raise `NotAFundError`.

## News (`core/news.py`)

- **Yahoo Finance** news for the ticker (via yfinance).
- **Google News RSS** for the fund/company name (via `feedparser`).
- Article bodies fetched with `requests` + parsed with `beautifulsoup4`.
- Results are deduplicated by title similarity and persisted through
  `core/storage.py`.

## Reliability contract

Every fetch is best-effort: on a network error, missing field, or absent
optional dependency it returns `None` / an empty list rather than raising. The
analysis pipeline and renderers are built to tolerate partial data.
