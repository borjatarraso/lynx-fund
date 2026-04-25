"""Fund ticker resolution and validation.

Scope guard: only **mutual funds**, **index funds**, and similar
open-ended collective-investment vehicles are accepted. Stocks
(EQUITY), exchange-traded funds (ETF), closed-end funds
(CLOSEDENDFUND), exchange-traded notes (ETN), and bare indices
(INDEX) are rejected with a clear error message that points the user
at the correct Suite tool.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple


class NotAFundError(ValueError):
    """Raised when the resolved instrument is not a mutual / index fund."""


_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}\d$")

# yfinance ``quoteType`` values that we accept. We accept ``MUTUALFUND``
# (the typical value for both actively-managed mutual funds and index
# funds) plus a few European synonyms that some data providers use.
_FUND_QUOTE_TYPES = {"MUTUALFUND", "MUTUAL_FUND", "OEIC", "SICAV", "UCITS"}

_REJECTED_QUOTE_TYPES = {
    "EQUITY":          ("stock",                 "lynx-fundamental"),
    "ETF":             ("Exchange-Traded Fund",  "lynx-etf"),
    "ETN":             ("Exchange-Traded Note",  "lynx-etf"),
    "ETC":             ("Exchange-Traded Commodity", "lynx-etf"),
    "CLOSEDENDFUND":   ("closed-end fund",       "lynx-fundamental"),
    "INDEX":           ("index",                 "(no Suite tool — pick an index fund)"),
    "CURRENCY":        ("currency",              "(no Suite tool)"),
    "CRYPTOCURRENCY":  ("cryptocurrency",        "(no Suite tool)"),
    "FUTURE":          ("futures contract",      "(no Suite tool)"),
    "OPTION":          ("option",                "(no Suite tool)"),
}


def is_isin(identifier: str) -> bool:
    return bool(_ISIN_RE.match((identifier or "").strip().upper()))


def resolve_identifier(identifier: str) -> Tuple[str, Optional[str]]:
    """Resolve a raw identifier to ``(ticker, isin_or_None)``.

    Rejects non-fund instruments by raising :class:`NotAFundError`.
    """
    raw = (identifier or "").strip().upper()
    if not raw:
        raise ValueError("Empty identifier")

    isin: Optional[str] = None
    ticker: str = raw

    if is_isin(raw):
        isin = raw
        resolved = _ticker_from_isin(raw)
        if not resolved:
            raise ValueError(f"Could not resolve ISIN {raw} to a ticker")
        ticker = resolved

    try:
        import yfinance as yf
    except ImportError:
        return ticker, isin

    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        return ticker, isin

    quote_type = str(info.get("quoteType", "")).upper()
    if quote_type and quote_type not in _FUND_QUOTE_TYPES:
        rejected = _REJECTED_QUOTE_TYPES.get(quote_type)
        if rejected:
            kind, where = rejected
            raise NotAFundError(
                f"'{ticker}' is a {kind}, not a mutual / index fund. "
                f"lynx-fund only analyses open-ended mutual funds, index "
                f"funds, OEICs, SICAVs and UCITS funds. Try {where} instead."
            )
        raise NotAFundError(
            f"'{ticker}' has unrecognised quoteType '{quote_type}'. "
            f"lynx-fund only analyses traditional mutual / index funds."
        )

    if isin is None:
        fetched = info.get("isin") or None
        if fetched and is_isin(str(fetched).upper()):
            isin = str(fetched).upper()

    return ticker, isin


def _ticker_from_isin(isin: str) -> Optional[str]:
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        search = yf.Search(isin, max_results=5)
        quotes = getattr(search, "quotes", None) or []
    except Exception:
        return None
    for q in quotes:
        qt = str(q.get("quoteType", "")).upper()
        if qt in _FUND_QUOTE_TYPES:
            symbol = q.get("symbol") or q.get("ticker")
            if symbol:
                return str(symbol).upper()
    return None


def search_funds(query: str, limit: int = 10) -> list[dict]:
    """Search mutual / index funds matching a free-text query.

    Returns a list of ``{symbol, name, exchange, currency}`` dicts.
    """
    try:
        import yfinance as yf
    except ImportError:
        return []
    try:
        search = yf.Search(query, max_results=limit * 3)
        quotes = getattr(search, "quotes", None) or []
    except Exception:
        return []
    out: list[dict] = []
    for q in quotes:
        qt = str(q.get("quoteType", "")).upper()
        if qt not in _FUND_QUOTE_TYPES:
            continue
        out.append({
            "symbol":   q.get("symbol") or q.get("ticker") or "",
            "name":     q.get("shortname") or q.get("longname") or "",
            "exchange": q.get("exchange") or "",
            "currency": q.get("currency") or "",
        })
        if len(out) >= limit:
            break
    return out


# Back-compat alias — early callers may import the fund name.
search_etfs = search_funds
