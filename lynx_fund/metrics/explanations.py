"""Fund metric explanations — powers the ``--explain`` CLI output.

Mutual-fund and index-fund investors care about a slightly different
vocabulary than ETF investors — sales loads, 12b-1 fees, capital-gains
distributions, manager tenure, persistence — so the explanation set
reflects that.
"""

from __future__ import annotations

from lynx_fund.models import MetricExplanation


EXPLANATIONS: dict[str, MetricExplanation] = {
    # ── Costs ───────────────────────────────────────────────────────────
    "expense_ratio": MetricExplanation(
        key="expense_ratio",
        full_name="Expense Ratio (TER)",
        description=(
            "Annual cost the fund charges as a percentage of assets. "
            "Deducted continuously from NAV — you never see the bill."
        ),
        why_used=(
            "The single strongest predictor of long-term fund "
            "underperformance (S&P SPIVA, multi-decade studies). "
            "Compounds against you every year you hold."
        ),
        formula="TER = Annual fund operating expenses / Average NAV",
        category="costs",
    ),
    "gross_expense_ratio": MetricExplanation(
        key="gross_expense_ratio",
        full_name="Gross Expense Ratio",
        description=(
            "Total operating cost before any fee waivers or "
            "reimbursements from the manager."
        ),
        why_used=(
            "If gross > net, the fund is being subsidised — verify the "
            "waiver isn't temporary."
        ),
        formula="Gross ER (no waivers applied)",
        category="costs",
    ),
    "front_load_max": MetricExplanation(
        key="front_load_max",
        full_name="Front-End Sales Load",
        description=(
            "One-time sales charge paid when you buy. Common in "
            "A-shares of US mutual funds; up to 5.75% historically."
        ),
        why_used=(
            "Direct, immediate hit to returns. No-load funds are widely "
            "available for most strategies — paying a load is rarely "
            "justified for retail investors."
        ),
        formula="Charged on purchase amount; reduces invested principal",
        category="costs",
    ),
    "deferred_load_max": MetricExplanation(
        key="deferred_load_max",
        full_name="Deferred Sales Load (CDSC)",
        description=(
            "Back-end load that declines the longer you hold the fund."
        ),
        why_used=(
            "B-share structure trade-off vs A-shares; usually inferior "
            "to no-load institutional shares."
        ),
        formula="CDSC = Σ(decline schedule × redemption amount)",
        category="costs",
    ),
    "twelve_b1_fee": MetricExplanation(
        key="twelve_b1_fee",
        full_name="12b-1 Distribution Fee",
        description=(
            "US mutual-fund distribution / marketing fee, taken from "
            "the fund (so investors pay it)."
        ),
        why_used=(
            "≥ 0.25% on an index fund is a red flag — the fund is "
            "paying salespeople with your money."
        ),
        formula="12b-1 fee × NAV (charged annually)",
        category="costs",
    ),
    "portfolio_turnover_pct": MetricExplanation(
        key="portfolio_turnover_pct",
        full_name="Portfolio Turnover",
        description=(
            "Annual fraction of the fund's holdings that get bought "
            "and sold."
        ),
        why_used=(
            "High turnover = trading-cost drag and capital-gain "
            "distributions for taxable investors. Index funds are "
            "typically < 10%; high-turnover active funds can exceed 100%."
        ),
        formula="min(buys, sells) / avg AUM, annualised",
        category="costs",
    ),
    "total_cost_of_ownership_bps": MetricExplanation(
        key="total_cost_of_ownership_bps",
        full_name="Total Cost of Ownership",
        description=(
            "TER plus front-load amortised over a 10-year hold plus any "
            "extra 12b-1 not already inside the TER."
        ),
        why_used=(
            "The realistic 'all-in' cost. Compare TCO across share "
            "classes — institutional shares often save 50+ bps."
        ),
        formula="TER + (Front-load / 10) + 12b-1 outside TER",
        category="costs",
    ),

    # ── Income / tax ─────────────────────────────────────────────────────
    "dividend_yield": MetricExplanation(
        key="dividend_yield",
        full_name="Trailing Dividend Yield",
        description=(
            "Sum of the past 12 months of distributions divided by the "
            "current NAV."
        ),
        why_used="Primary income signal for income-focused funds.",
        formula="Yield = Σ(trailing 12m distributions) / NAV",
        category="income",
    ),
    "sec_yield_30d": MetricExplanation(
        key="sec_yield_30d",
        full_name="SEC 30-Day Yield",
        description="Standardised SEC yield — primary income metric for US bond funds.",
        why_used="Comparable across funds; forward-looking vs trailing yield.",
        formula="(Σ income − expenses) / (NAV × shares outstanding), annualised",
        category="income",
    ),
    "qualified_dividend_pct": MetricExplanation(
        key="qualified_dividend_pct",
        full_name="Qualified Dividend Share",
        description=(
            "Fraction of the distribution that qualifies for the lower "
            "long-term-cap-gains tax rate (US)."
        ),
        why_used=(
            "Higher = better after-tax yield in a taxable account."
        ),
        formula="Qualified dividends / Total dividends",
        category="income",
    ),
    "cap_gain_distributions_3y_avg": MetricExplanation(
        key="cap_gain_distributions_3y_avg",
        full_name="Capital-Gain Distributions (3Y avg)",
        description=(
            "Annualised capital-gain distributions paid out, as a "
            "percent of NAV."
        ),
        why_used=(
            "The single biggest tax-efficiency difference between "
            "mutual funds and ETFs. High-turnover active funds "
            "distribute 2-5% of NAV every year — taxable each year."
        ),
        formula="Σ(cap-gains paid out / NAV) over 3 years, averaged",
        category="income",
    ),
    "embedded_unrealised_gain_pct": MetricExplanation(
        key="embedded_unrealised_gain_pct",
        full_name="Embedded Unrealised Gains",
        description=(
            "Unrealised capital gains held inside the fund relative to NAV."
        ),
        why_used=(
            "Tax-bomb risk: if the fund liquidates a winning position, "
            "you pay tax on gains that accrued before you bought in."
        ),
        formula="Unrealised gains / NAV",
        category="income",
    ),
    "tax_efficiency_score": MetricExplanation(
        key="tax_efficiency_score",
        full_name="Tax-Efficiency Score (0-100)",
        description=(
            "Composite score blending qualified-dividend share, "
            "capital-gain-distribution history, and embedded gains."
        ),
        why_used=(
            "Quick proxy for 'how much of the headline return survives "
            "the IRS'."
        ),
        formula="60 + qd*30 − cgd*700 − max(0, embedded−10%)*75",
        category="income",
    ),

    # ── Liquidity / access ──────────────────────────────────────────────
    "aum": MetricExplanation(
        key="aum",
        full_name="Assets Under Management",
        description="Total market value of assets held in the fund.",
        why_used=(
            "Below $250M → risk of closure. Below $50M → acute risk. "
            "Larger AUM generally = more stable expenses."
        ),
        formula="AUM = NAV × shares outstanding",
        category="liquidity",
    ),
    "fund_age_years": MetricExplanation(
        key="fund_age_years",
        full_name="Fund Age (years)",
        description="Years since the fund's inception.",
        why_used="Seasoned funds have longer track records. New funds are less proven.",
        formula="Today − Inception",
        category="liquidity",
    ),
    "minimum_initial_investment": MetricExplanation(
        key="minimum_initial_investment",
        full_name="Minimum Initial Investment",
        description=(
            "USD amount required to open a position in this share class."
        ),
        why_used=(
            "Institutional shares often require $10k-$1M minimums but "
            "carry 30-50 bps lower TER — worth the gating in tax-"
            "advantaged accounts via fund-of-funds wrappers."
        ),
        formula="Issuer-set; varies by share class",
        category="liquidity",
    ),
    "soft_closed": MetricExplanation(
        key="soft_closed",
        full_name="Soft Close Status",
        description=(
            "Fund stopped accepting new investors but lets existing "
            "shareholders continue contributing."
        ),
        why_used=(
            "Often a *positive* signal — manager protects capacity to "
            "preserve performance. Cannot start a new position once closed."
        ),
        formula="Issuer-disclosed",
        category="liquidity",
    ),
    "swing_pricing": MetricExplanation(
        key="swing_pricing",
        full_name="Swing Pricing",
        description=(
            "Fund adjusts the daily NAV up or down depending on net "
            "flow direction, charging trading costs to the trader, not "
            "the long-term holder."
        ),
        why_used="Protects buy-and-hold investors from flow-driven dilution.",
        formula="NAV ± swing factor × |net flows|",
        category="liquidity",
    ),
    "redemption_gates": MetricExplanation(
        key="redemption_gates",
        full_name="Redemption Gates",
        description=(
            "Fund manager has the discretion to limit or suspend "
            "redemptions during stressed conditions."
        ),
        why_used=(
            "Material risk for less-liquid asset classes (high-yield, "
            "emerging markets, real estate)."
        ),
        formula="Disclosed in prospectus",
        category="liquidity",
    ),

    # ── Performance ─────────────────────────────────────────────────────
    "return_1y": MetricExplanation(
        key="return_1y",
        full_name="Total Return — 1 Year",
        description="Total return (NAV + distributions) over the past 12 months.",
        why_used="Short-horizon momentum; noise-prone, never evaluate in isolation.",
        formula="(NAV_today + reinvested distributions) / NAV_1y − 1",
        category="performance",
    ),
    "return_5y": MetricExplanation(
        key="return_5y",
        full_name="Total Return — 5 Year CAGR",
        description="Compound annual growth rate over 5 years.",
        why_used="Long-enough window to smooth out short-term noise.",
        formula="(NAV_now / NAV_5y_ago) ^ (1/5) − 1",
        category="performance",
    ),
    "load_adjusted_return_5y": MetricExplanation(
        key="load_adjusted_return_5y",
        full_name="Load-Adjusted 5Y Return",
        description=(
            "5-year return reduced by the front-load amortised over the holding period."
        ),
        why_used=(
            "The honest figure for A-share investors. A 5.75% load on a "
            "10% return becomes ~3.7% over 5 years."
        ),
        formula="(1 + return_5y) × (1 − front_load)^(1/5) − 1",
        category="performance",
    ),
    "alpha_3y": MetricExplanation(
        key="alpha_3y",
        full_name="Jensen's Alpha (3Y)",
        description=(
            "Annualised excess return after adjusting for the fund's "
            "beta exposure to the benchmark."
        ),
        why_used=(
            "Pure manager skill (or not). Persistently positive alpha "
            "is rare; most active funds deliver negative alpha after fees."
        ),
        formula="α = R_fund − [R_f + β × (R_bench − R_f)]",
        category="performance",
    ),
    "info_ratio_3y": MetricExplanation(
        key="info_ratio_3y",
        full_name="Information Ratio (3Y)",
        description=(
            "Active return per unit of tracking error. Active-fund equivalent of Sharpe."
        ),
        why_used="≥ 0.5 is elite; ≥ 0.25 is good; ≤ 0 = not adding value.",
        formula="(R_fund − R_bench) / Tracking Error",
        category="performance",
    ),
    "persistence_score": MetricExplanation(
        key="persistence_score",
        full_name="Persistence Score (0-100)",
        description=(
            "% of the last 5 calendar years the fund finished in the top peer quartile."
        ),
        why_used=(
            "S&P SPIVA: under 5% of top-quartile active funds stay "
            "top-quartile across 5 years. Persistence is rare."
        ),
        formula="(top-quartile years in last 5) / 5 × 100",
        category="performance",
    ),
    "sharpe_3y": MetricExplanation(
        key="sharpe_3y",
        full_name="Sharpe Ratio (3Y)",
        description="Excess return per unit of total volatility.",
        why_used="Normalises return by risk — comparable across funds.",
        formula="(Annual return − Risk-free rate) / Annual volatility",
        category="performance",
    ),
    "sortino_3y": MetricExplanation(
        key="sortino_3y",
        full_name="Sortino Ratio (3Y)",
        description="Excess return per unit of downside volatility only.",
        why_used="Penalises painful drawdowns only, not upside volatility.",
        formula="(Annual return − Risk-free rate) / Downside deviation",
        category="performance",
    ),

    # ── Allocation ──────────────────────────────────────────────────────
    "top10_concentration": MetricExplanation(
        key="top10_concentration",
        full_name="Top-10 Concentration",
        description="Sum of weights of the 10 largest holdings.",
        why_used="High top-10 → exposure driven by a few names rather than a broad index.",
        formula="Σ(weight of 10 largest holdings)",
        category="allocation",
    ),
    "herfindahl_sector": MetricExplanation(
        key="herfindahl_sector",
        full_name="Sector HHI",
        description="Herfindahl–Hirschman Index over sector weights. 1/N is perfectly balanced.",
        why_used="Detects sector concentration — a diversified equity fund should have low HHI.",
        formula="HHI = Σ(weight²)",
        category="allocation",
    ),
    "holdings_count": MetricExplanation(
        key="holdings_count",
        full_name="Number of Holdings",
        description="How many underlying positions the fund holds.",
        why_used="More positions generally means lower single-name risk.",
        formula="count(holdings)",
        category="allocation",
    ),
    "cash_pct": MetricExplanation(
        key="cash_pct",
        full_name="Cash %",
        description="Fraction of fund assets held in cash or money-market instruments.",
        why_used=(
            "Idle cash is return drag for equity funds. Active managers "
            "sometimes hold 5%+ as 'dry powder'; for index funds, > 1% "
            "is a tracking-error risk."
        ),
        formula="Cash / Total assets",
        category="allocation",
    ),
    "duration_years": MetricExplanation(
        key="duration_years",
        full_name="Effective Duration (years)",
        description=(
            "Sensitivity of the bond fund's NAV to a 1% change in yields."
        ),
        why_used=(
            "Duration 7 ⇒ a 1% rise in yields drops NAV ~7%. The single "
            "most important number for a bond-fund investor."
        ),
        formula="Σ(weighted duration of holdings)",
        category="allocation",
    ),

    # ── Risk ─────────────────────────────────────────────────────────────
    "volatility_3y": MetricExplanation(
        key="volatility_3y",
        full_name="Annualised Volatility (3Y)",
        description="Standard deviation of daily log returns, scaled to one year.",
        why_used="Primary risk metric — lets you size positions responsibly.",
        formula="σ(log returns) × √252",
        category="risk",
    ),
    "max_drawdown_3y": MetricExplanation(
        key="max_drawdown_3y",
        full_name="Max Drawdown (3Y)",
        description="Largest peak-to-trough decline in the past 3 years.",
        why_used="Measures how painful the worst drawdown has been.",
        formula="min((NAV_t − NAV_peak) / NAV_peak) for t in window",
        category="risk",
    ),
    "beta_3y": MetricExplanation(
        key="beta_3y",
        full_name="Beta (3Y)",
        description="Sensitivity of returns vs the benchmark.",
        why_used="β ≈ 1 tracks the market; β > 1 amplifies; β < 1 dampens.",
        formula="Cov(R_fund, R_bench) / Var(R_bench)",
        category="risk",
    ),
    "tracking_error": MetricExplanation(
        key="tracking_error",
        full_name="Tracking Error",
        description="Annualised stdev of return differences vs benchmark.",
        why_used=(
            "For *index funds* this should be tiny (< 50 bps). For "
            "active funds, larger TE means larger active bets."
        ),
        formula="σ(R_fund − R_bench) × √252",
        category="risk",
    ),
    "active_share": MetricExplanation(
        key="active_share",
        full_name="Active Share",
        description=(
            "Fraction of the fund's portfolio that differs from the benchmark."
        ),
        why_used=(
            "Below 0.6 = closet indexing — paying active fees for "
            "near-index exposure. Above 0.8 = genuinely active."
        ),
        formula="0.5 × Σ |w_fund_i − w_bench_i|",
        category="risk",
    ),
    "var_95_1y": MetricExplanation(
        key="var_95_1y",
        full_name="1-day Value at Risk (95%)",
        description=(
            "The 5th-percentile worst single-day return over the past year."
        ),
        why_used=(
            "Quick proxy for tail-risk: 'how bad does a really bad day "
            "look?'."
        ),
        formula="5th percentile of daily returns",
        category="risk",
    ),

    # ── Manager ──────────────────────────────────────────────────────────
    "avg_manager_tenure_years": MetricExplanation(
        key="avg_manager_tenure_years",
        full_name="Average Manager Tenure (years)",
        description=(
            "Average number of years the current managers have run the fund."
        ),
        why_used=(
            "Buffett's '10-year rule' — a track record under 10 years "
            "is hard to distinguish from luck. For active funds this is "
            "a critical signal; for index funds it's largely cosmetic."
        ),
        formula="mean(manager.tenure_years)",
        category="manager",
    ),
}


def get_explanation(key: str):
    return EXPLANATIONS.get(key)


def list_keys() -> list[str]:
    return sorted(EXPLANATIONS.keys())


def by_category() -> dict[str, list]:
    buckets: dict[str, list] = {}
    for e in EXPLANATIONS.values():
        buckets.setdefault(e.category, []).append(e)
    for v in buckets.values():
        v.sort(key=lambda m: m.full_name)
    return buckets
