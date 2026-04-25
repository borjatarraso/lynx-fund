"""Data models for Lynx Fund Analysis.

Scope: traditional fund vehicles only — open-ended **mutual funds**,
**index funds**, **UCITS funds**, **OEICs**, **SICAVs**, and similar
collective-investment schemes. Exchange-traded funds (ETFs),
exchange-traded notes (ETNs), single stocks, closed-end funds, and
bare indexes are **rejected at the resolver level** and never reach
these models.

The model surface is purpose-built for the things mutual-fund
investors actually have to evaluate (and that fund investors don't
worry about):

* **Share classes** — A/B/C/I/R/Z/Admiral, with per-class TER, load
  schedule, 12b-1 fee, breakpoints, and minimum investment.
* **Loads & breakpoints** — front-end / back-end / level-load,
  contingent deferred sales charge (CDSC), redemption fees,
  short-term-trading fees.
* **Pricing & access** — once-a-day NAV, forward pricing, order
  cut-off time, swing pricing, redemption gates, lock-up periods,
  minimum initial / subsequent investment, soft-close / hard-close.
* **Manager** — name(s), tenure, manager-of-managers, average
  tenure (key for active funds — Buffett rule of "10-year track").
* **Active vs passive** — active share, R² vs benchmark, style drift
  scores, primary-benchmark adherence.
* **Tax drag** — capital-gains distributions (3Y, 5Y), embedded
  unrealised gains, qualified dividend share, K-1 vs 1099, after-tax
  return projections.
* **Persistence** — top-quartile-in-N-years, rolling-3Y consistency,
  Morningstar / fund-rating-style band.
* **Operational** — trustee / custodian / auditor / sponsor,
  reorganization history, soft-close / hard-close events.

Every field has a sensible default (``None`` / empty list) so existing
call sites and tests keep working as fund-specific data is layered in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Fund size tier classification (based on AUM)
# ---------------------------------------------------------------------------

class FundSizeTier(str, Enum):
    """AUM-based fund classification — same vocabulary as lynx-etf so
    the cross-Suite UI stays consistent."""
    MEGA = "Mega Fund"
    LARGE = "Large Fund"
    MID = "Mid Fund"
    SMALL = "Small Fund"
    MICRO = "Micro Fund"
    NANO = "Nano Fund"


def classify_tier(aum: Optional[float]) -> FundSizeTier:
    """Classify a fund by assets under management (USD)."""
    if aum is None or aum <= 0:
        return FundSizeTier.NANO
    if aum >= 50_000_000_000:
        return FundSizeTier.MEGA
    if aum >= 10_000_000_000:
        return FundSizeTier.LARGE
    if aum >= 1_000_000_000:
        return FundSizeTier.MID
    if aum >= 250_000_000:
        return FundSizeTier.SMALL
    if aum >= 50_000_000:
        return FundSizeTier.MICRO
    return FundSizeTier.NANO


# Keep the old name as an alias so shared core / Suite code that
# references CompanyTier keeps working.
CompanyTier = FundSizeTier


class Relevance(str, Enum):
    CRITICAL = "critical"
    RELEVANT = "relevant"
    CONTEXTUAL = "contextual"
    IRRELEVANT = "irrelevant"


# ---------------------------------------------------------------------------
# Share class (mutual funds frequently have several share classes per fund)
# ---------------------------------------------------------------------------

@dataclass
class ShareClass:
    """One share class of a fund.

    A single mutual fund typically lists multiple share classes that
    differ on TER, load schedule, 12b-1 fee, breakpoints and minimum
    investment. The investor's choice of share class can move
    annualised return by 50–100 bps.
    """
    name: str = ""                            # "A", "I", "Admiral"…
    ticker: Optional[str] = None              # share-class-specific symbol
    isin: Optional[str] = None
    expense_ratio: Optional[float] = None     # decimal (0.0050 = 50 bps)
    front_load_max: Optional[float] = None    # max sales load on purchase
    deferred_load_max: Optional[float] = None # CDSC / back-end load
    twelve_b1_fee: Optional[float] = None     # US distribution fee
    redemption_fee: Optional[float] = None    # short-term-trading fee
    minimum_initial: Optional[float] = None   # USD
    minimum_subsequent: Optional[float] = None
    breakpoints: list = field(default_factory=list)  # [(threshold_usd, load_pct)]
    eligibility: Optional[str] = None         # "Retail", "Institutional", "Retirement"
    is_recommended_for_passive: Optional[bool] = None


# ---------------------------------------------------------------------------
# Manager (one fund can have several)
# ---------------------------------------------------------------------------

@dataclass
class ManagerInfo:
    name: str = ""
    role: Optional[str] = None                # Lead / Co / Assistant
    tenure_years: Optional[float] = None
    started_on: Optional[str] = None
    manages_other_funds: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Fund profile
# ---------------------------------------------------------------------------

@dataclass
class FundProfile:
    ticker: str
    name: str
    isin: Optional[str] = None
    cusip: Optional[str] = None              # US fund identifier
    sedol: Optional[str] = None              # UK / ROW identifier
    category: Optional[str] = None           # "Large Blend", "Intermediate Bond"…
    asset_class: Optional[str] = None        # Equity, Fixed Income, Multi-Asset…
    fund_family: Optional[str] = None        # Vanguard, Fidelity, Schwab…
    domicile: Optional[str] = None           # US, IE, LU, UK…
    inception_date: Optional[str] = None
    exchange: Optional[str] = None           # Usually N/A for mutual funds
    currency: Optional[str] = None
    aum: Optional[float] = None              # USD
    description: Optional[str] = None
    website: Optional[str] = None
    benchmark: Optional[str] = None
    distribution_policy: Optional[str] = None  # Distributing / Accumulating
    tier: FundSizeTier = FundSizeTier.NANO

    # ── Mutual-fund-specific structure / regulation ─────────────────────
    fund_type: Optional[str] = None           # "Mutual Fund", "Index Fund",
                                              # "UCITS", "OEIC", "SICAV"
    is_index_fund: Optional[bool] = None      # passive vs active
    is_actively_managed: Optional[bool] = None
    legal_structure: Optional[str] = None     # "Open-Ended", "Investment Trust"
    ucits: Optional[bool] = None              # UCITS-compliant (EU retail)
    kiid_prr_risk_rating: Optional[int] = None  # 1..7 SRRI for UCITS docs
    soft_closed: Optional[bool] = None        # New investors blocked
    hard_closed: Optional[bool] = None        # Closed to all subscriptions
    pricing_frequency: Optional[str] = None   # "Daily NAV", "Forward priced"
    cutoff_time_local: Optional[str] = None   # e.g. "16:00 ET"
    swing_pricing: Optional[bool] = None      # NAV swings to protect against flows
    redemption_gates: Optional[bool] = None   # Manager can suspend redemptions
    lockup_period_days: Optional[int] = None  # Required holding period

    # ── Manager(s) ───────────────────────────────────────────────────────
    managers: list = field(default_factory=list)        # list[ManagerInfo]
    avg_manager_tenure_years: Optional[float] = None
    longest_manager_tenure_years: Optional[float] = None
    manager_of_managers: Optional[bool] = None
    sub_advisers: list = field(default_factory=list)

    # ── Active vs passive signals ────────────────────────────────────────
    active_share: Optional[float] = None      # 0..1 — > 0.6 = truly active
    style_drift_score: Optional[float] = None # higher = more drift

    # ── Operational / governance ─────────────────────────────────────────
    trustee_or_custodian: Optional[str] = None
    auditor: Optional[str] = None
    sponsor_or_advisor: Optional[str] = None
    transfer_agent: Optional[str] = None
    morningstar_rating: Optional[int] = None  # 1..5 stars
    sustainability_rating: Optional[str] = None


# Alias so shared code that imports CompanyProfile finds the fund type.
CompanyProfile = FundProfile


# ---------------------------------------------------------------------------
# Cost metrics — fund-flavoured (loads, 12b-1, breakpoints, TCO)
# ---------------------------------------------------------------------------

@dataclass
class CostMetrics:
    """Fees and the realistic full cost-of-ownership of holding the fund."""
    expense_ratio: Optional[float] = None     # net TER, decimal
    gross_expense_ratio: Optional[float] = None
    management_fee: Optional[float] = None
    performance_fee: Optional[float] = None
    twelve_b1_fee: Optional[float] = None     # US distribution fee
    other_expenses: Optional[float] = None
    front_load_max: Optional[float] = None    # decimal (0.0575 = 5.75%)
    deferred_load_max: Optional[float] = None # CDSC / back-end load
    redemption_fee: Optional[float] = None
    short_term_trading_fee: Optional[float] = None
    portfolio_turnover_pct: Optional[float] = None
    estimated_cost_10k_year1: Optional[float] = None  # USD
    estimated_cost_10k_year10: Optional[float] = None
    total_cost_of_ownership_bps: Optional[float] = None  # ER + load amortised
    has_breakpoints: Optional[bool] = None    # Loads decline at thresholds


@dataclass
class IncomeMetrics:
    """Dividend, distribution and tax-flavour signals.

    Mutual funds are notably *less* tax-efficient tha funds because they
    must distribute realised gains annually. We surface those distributions
    explicitly so the investor sees the real tax drag.
    """
    dividend_yield: Optional[float] = None
    sec_yield_30d: Optional[float] = None
    distribution_frequency: Optional[str] = None
    distribution_policy: Optional[str] = None
    yoy_distribution_change: Optional[float] = None
    qualified_dividend_pct: Optional[float] = None
    cap_gain_distributions_3y_avg: Optional[float] = None
    cap_gain_distributions_5y_avg: Optional[float] = None
    embedded_unrealised_gain_pct: Optional[float] = None
    tax_efficiency_score: Optional[float] = None
    tax_form: Optional[str] = None               # "1099", "K-1"
    after_tax_return_3y: Optional[float] = None
    after_tax_return_5y: Optional[float] = None


@dataclass
class LiquidityMetrics:
    """Size, accessibility and stability of the fund."""
    aum: Optional[float] = None
    fund_age_years: Optional[float] = None
    minimum_initial_investment: Optional[float] = None
    minimum_subsequent_investment: Optional[float] = None
    is_open_to_new_investors: Optional[bool] = None
    soft_closed: Optional[bool] = None
    hard_closed: Optional[bool] = None
    pricing_frequency: Optional[str] = None
    cutoff_time_local: Optional[str] = None
    swing_pricing: Optional[bool] = None
    redemption_gates: Optional[bool] = None
    lockup_period_days: Optional[int] = None
    redemption_window_days: Optional[int] = None
    net_flows_1y: Optional[float] = None
    net_flows_3y: Optional[float] = None
    closure_risk: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Return history, capture, persistence, manager-tenure-weighted returns."""
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_ytd: Optional[float] = None
    return_1y: Optional[float] = None
    return_3y: Optional[float] = None
    return_5y: Optional[float] = None
    return_10y: Optional[float] = None
    cagr_since_inception: Optional[float] = None
    return_since_manager_change: Optional[float] = None
    sharpe_1y: Optional[float] = None
    sharpe_3y: Optional[float] = None
    sortino_3y: Optional[float] = None
    calmar_3y: Optional[float] = None
    info_ratio_3y: Optional[float] = None
    treynor_3y: Optional[float] = None
    alpha_3y: Optional[float] = None             # Jensen's alpha vs benchmark
    up_capture_3y: Optional[float] = None
    down_capture_3y: Optional[float] = None
    best_quarter: Optional[float] = None
    worst_quarter: Optional[float] = None
    recovery_days_from_max_dd: Optional[int] = None
    calendar_returns: list = field(default_factory=list)
    # ── Persistence — does the fund stay good? ─────────────────────────
    quartile_history: list = field(default_factory=list)
    top_quartile_periods_5y: Optional[int] = None
    persistence_score: Optional[float] = None
    # ── Load-adjusted returns (returns net of front-load drag) ──────────
    load_adjusted_return_1y: Optional[float] = None
    load_adjusted_return_5y: Optional[float] = None
    load_adjusted_return_10y: Optional[float] = None


@dataclass
class AllocationMetrics:
    """Sector / geo / currency / market-cap composition + bond allocation."""
    holdings_count: Optional[int] = None
    effective_holdings: Optional[float] = None
    top1_concentration: Optional[float] = None
    top5_concentration: Optional[float] = None
    top10_concentration: Optional[float] = None
    top25_concentration: Optional[float] = None
    cash_pct: Optional[float] = None                  # idle cash drag
    herfindahl_sector: Optional[float] = None
    herfindahl_holdings: Optional[float] = None
    sector_breakdown: list = field(default_factory=list)
    country_breakdown: list = field(default_factory=list)
    currency_breakdown: list = field(default_factory=list)
    asset_class_breakdown: list = field(default_factory=list)
    market_cap_breakdown: list = field(default_factory=list)
    style_box: Optional[str] = None
    country_count: Optional[int] = None
    sector_count: Optional[int] = None
    # ── Bond-fund-specific ──────────────────────────────────────────────
    duration_years: Optional[float] = None
    yield_to_maturity: Optional[float] = None
    avg_credit_rating: Optional[str] = None
    credit_quality_breakdown: list = field(default_factory=list)
    avg_coupon: Optional[float] = None
    avg_maturity_years: Optional[float] = None


@dataclass
class RiskProfile:
    """Volatility, drawdown, tail risk, tracking quality (active vs index)."""
    volatility_1y: Optional[float] = None
    volatility_3y: Optional[float] = None
    max_drawdown_3y: Optional[float] = None
    beta_3y: Optional[float] = None
    beta_vs_benchmark: Optional[float] = None
    correlation_sp500_3y: Optional[float] = None
    tracking_error: Optional[float] = None
    tracking_difference: Optional[float] = None
    r_squared: Optional[float] = None
    downside_deviation_3y: Optional[float] = None
    var_95_1y: Optional[float] = None
    cvar_95_1y: Optional[float] = None
    skewness_3y: Optional[float] = None
    kurtosis_3y: Optional[float] = None
    # ── Active-fund-specific ────────────────────────────────────────────
    active_share: Optional[float] = None              # 0..1
    style_drift: Optional[float] = None
    consistency_score: Optional[float] = None         # 0..100


@dataclass
class ESGProfile:
    """Sustainability metadata — funds disclose less tha funds typically."""
    score: Optional[float] = None
    sfdr_article: Optional[int] = None
    sustainability_rating: Optional[str] = None
    carbon_intensity: Optional[float] = None
    controversy_score: Optional[float] = None
    exclusions: list = field(default_factory=list)


@dataclass
class Verdict:
    """Overall assessment of the fund."""
    overall_score: float = 0.0
    verdict: str = ""
    summary: str = ""
    category_scores: dict = field(default_factory=dict)
    strengths: list = field(default_factory=list)
    risks: list = field(default_factory=list)
    tier_note: str = ""
    suitable_for: list = field(default_factory=list)


@dataclass
class PassiveCheck:
    """One pass/warn/fail line in the passive-investor checklist."""
    label: str
    status: str = "warn"
    message: str = ""
    rule_of_thumb: str = ""


@dataclass
class Holding:
    """A single holding line."""
    symbol: Optional[str] = None
    name: Optional[str] = None
    weight: Optional[float] = None
    sector: Optional[str] = None
    country: Optional[str] = None


@dataclass
class NewsArticle:
    title: str
    url: str
    published: Optional[str] = None
    source: Optional[str] = None
    summary: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class MetricExplanation:
    key: str
    full_name: str
    description: str
    why_used: str
    formula: str
    category: str  # costs, income, liquidity, performance, allocation, risk, manager


@dataclass
class FundReport:
    """Complete fund analysis."""
    profile: FundProfile
    share_classes: list = field(default_factory=list)  # list[ShareClass]
    costs: Optional[CostMetrics] = None
    income: Optional[IncomeMetrics] = None
    liquidity: Optional[LiquidityMetrics] = None
    performance: Optional[PerformanceMetrics] = None
    allocation: Optional[AllocationMetrics] = None
    risk: Optional[RiskProfile] = None
    esg: Optional[ESGProfile] = None
    verdict: Optional[Verdict] = None
    holdings: list = field(default_factory=list)
    news: list = field(default_factory=list)
    passive_checklist: list = field(default_factory=list)
    tips: list = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())


# Wire-compat alias — legacy code and cached JSON may reference this name.
AnalysisReport = FundReport
