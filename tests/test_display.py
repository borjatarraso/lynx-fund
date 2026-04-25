"""Display rendering smoke tests."""

from __future__ import annotations

import io

from rich.console import Console

from lynx_fund.display import (
    fmt_bps,
    fmt_int,
    fmt_money,
    fmt_pct,
    fmt_years,
    render_about,
    render_full_report,
)
from lynx_fund.models import (
    AllocationMetrics,
    CostMetrics,
    FundProfile,
    FundReport,
    FundSizeTier,
    Holding,
    IncomeMetrics,
    LiquidityMetrics,
    PerformanceMetrics,
    RiskProfile,
    Verdict,
)


class TestFormatters:
    def test_fmt_pct(self):
        assert fmt_pct(None) == "—"
        assert fmt_pct(0.0123) == "1.23%"
        assert fmt_pct(0.1, 0) == "10%"

    def test_fmt_money(self):
        assert fmt_money(None) == "—"
        assert fmt_money(1.2e12) == "$1.20T"
        assert fmt_money(5.4e9) == "$5.40B"
        assert fmt_money(7.1e6) == "$7.10M"
        assert fmt_money(999) == "$999.00"

    def test_fmt_bps(self):
        assert fmt_bps(None) == "—"
        assert fmt_bps(3.4) == "3.4 bps"

    def test_fmt_int(self):
        assert fmt_int(None) == "—"
        assert fmt_int(1234567) == "1,234,567"

    def test_fmt_years(self):
        assert fmt_years(None) == "—"
        assert fmt_years(10.7) == "10.7 yr"


def _make_report() -> FundReport:
    return FundReport(
        profile=FundProfile(
            ticker="VFIAX", name="Vanguard 500 Index Admiral", aum=500e9,
            tier=FundSizeTier.MEGA, isin="US9229087286",
            category="Large Blend", asset_class="Equity",
            fund_family="Vanguard", domicile="US",
            fund_type="Index Fund", is_index_fund=True,
        ),
        costs=CostMetrics(expense_ratio=0.0004),
        income=IncomeMetrics(dividend_yield=0.013),
        liquidity=LiquidityMetrics(aum=500e9, fund_age_years=33,
                                    minimum_initial_investment=3000),
        performance=PerformanceMetrics(return_1y=0.21, return_5y=0.12, sharpe_3y=0.8),
        allocation=AllocationMetrics(holdings_count=500, top10_concentration=0.32,
                                     herfindahl_sector=0.15,
                                     sector_breakdown=[("Technology", 0.28)],
                                     country_breakdown=[("US", 1.0)],
                                     country_count=1, sector_count=11),
        risk=RiskProfile(volatility_3y=0.16, max_drawdown_3y=-0.25, beta_3y=1.0),
        verdict=Verdict(overall_score=85, verdict="Strong Buy",
                        category_scores={"Costs": 91, "Liquidity": 100}),
        holdings=[Holding(symbol="AAPL", name="Apple", weight=0.07)],
    )


class TestRenderFullReport:
    def test_renders_all_sections(self):
        buf = io.StringIO()
        console = Console(file=buf, width=120, force_terminal=False)
        render_full_report(console, _make_report())
        out = buf.getvalue()
        assert "VFIAX" in out
        assert "Vanguard 500 Index" in out
        assert "Strong Buy" in out
        assert "Costs" in out
        assert "Holdings" in out or "Top" in out

    def test_handles_missing_sections(self):
        r = FundReport(profile=FundProfile(ticker="X", name="X"))
        buf = io.StringIO()
        console = Console(file=buf, width=80, force_terminal=False)
        render_full_report(console, r)
        out = buf.getvalue()
        assert "X" in out  # header renders
        assert "Caution" not in out  # no verdict means no verdict panel


class TestRenderAbout:
    def test_renders(self):
        buf = io.StringIO()
        console = Console(file=buf, width=120, force_terminal=False)
        render_about(console)
        out = buf.getvalue()
        assert "Lynx Fund Analysis" in out
        assert "Funds only" in out or "ETF" in out
