"""Ticker resolution and fund scope-enforcement tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from lynx_fund.core.ticker import (
    NotAFundError,
    is_isin,
    resolve_identifier,
    search_funds,
)


class TestIsIsin:
    def test_valid_isin_formats(self):
        assert is_isin("IE00B4L5Y983")
        assert is_isin("US78462F1030")
        assert is_isin("us78462f1030")  # lowercased

    def test_invalid(self):
        assert not is_isin("VFIAX")
        assert not is_isin("")
        assert not is_isin("IE00B4L5Y98")  # too short


class TestResolveIdentifier:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            resolve_identifier("")

    def test_mutual_fund_accepted(self):
        fake = MagicMock()
        fake.info = {"quoteType": "MUTUALFUND", "isin": "US9229087286"}
        with patch("yfinance.Ticker", return_value=fake):
            ticker, isin = resolve_identifier("VFIAX")
        assert ticker == "VFIAX"
        assert isin == "US9229087286"

    def test_stock_rejected(self):
        fake = MagicMock()
        fake.info = {"quoteType": "EQUITY"}
        with patch("yfinance.Ticker", return_value=fake):
            with pytest.raises(NotAFundError) as ei:
                resolve_identifier("AAPL")
        assert "stock" in str(ei.value).lower()

    def test_etf_rejected(self):
        fake = MagicMock()
        fake.info = {"quoteType": "ETF"}
        with patch("yfinance.Ticker", return_value=fake):
            with pytest.raises(NotAFundError) as ei:
                resolve_identifier("SPY")
        assert "exchange-traded" in str(ei.value).lower()

    def test_closed_end_fund_rejected(self):
        fake = MagicMock()
        fake.info = {"quoteType": "CLOSEDENDFUND"}
        with patch("yfinance.Ticker", return_value=fake):
            with pytest.raises(NotAFundError) as ei:
                resolve_identifier("PDI")
        assert "closed-end" in str(ei.value).lower()

    def test_index_rejected(self):
        fake = MagicMock()
        fake.info = {"quoteType": "INDEX"}
        with patch("yfinance.Ticker", return_value=fake):
            with pytest.raises(NotAFundError) as ei:
                resolve_identifier("^GSPC")
        assert "index" in str(ei.value).lower()


class TestSearchFunds:
    def test_returns_empty_on_failure(self):
        with patch("yfinance.Search", side_effect=Exception("boom")):
            assert search_funds("anything") == []

    def test_filters_non_fund_quotes(self):
        fake = MagicMock()
        fake.quotes = [
            {"symbol": "AAPL", "shortname": "Apple", "quoteType": "EQUITY"},
            {"symbol": "SPY", "shortname": "SPDR S&P 500", "quoteType": "ETF"},
            {"symbol": "VFIAX", "shortname": "Vanguard 500 Index Admiral",
             "quoteType": "MUTUALFUND",
             "exchange": "NMS", "currency": "USD"},
        ]
        with patch("yfinance.Search", return_value=fake):
            results = search_funds("500 index", limit=5)
        assert len(results) == 1
        assert results[0]["symbol"] == "VFIAX"
