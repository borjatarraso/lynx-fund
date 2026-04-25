"""Rules-of-thumb checklist for passive mutual / index fund investors.

Returns a list of :class:`PassiveCheck` records that the display layer
renders as a colour-coded flag table. The checklist mirrors what a
Boglehead / SPIVA-aware investor scans before buying a traditional
fund:

* **TER** — index fund ≤ 0.10%; broad-market active ≤ 0.50%; sector /
  thematic ≤ 0.75%.
* **Sales loads** — none (no front-load, no CDSC). A no-load fund of
  the same strategy almost always exists.
* **12b-1 fee** — ideally zero. ≥ 0.25% is a marketing fee paid out
  of your money.
* **AUM** — ≥ $100M to keep closure risk negligible.
* **Fund age** — ≥ 3 years. A 1-year-old fund's track record is noise.
* **Capital-gains distributions** — ≤ 1% of NAV averaged over 3Y for
  taxable-account holders. > 3%/yr is a serious tax drag.
* **Embedded gains** — ≤ 15% of NAV. Higher = tax-bomb risk on entry.
* **Persistence** — top-quartile in ≥ 2 of the last 5 years.
* **Active share** (active funds only) — ≥ 0.6 to avoid closet indexing.
* **Manager tenure** — ≥ 5 years for active funds (Buffett's heuristic).
* **Tax form** — 1099 (mutual fund) is preferred over K-1 (partnership).
* **Soft-/hard-close** — informational; lets the user know whether they
  can actually buy the fund.
* **Index fund check** — passive index trackers should have low
  tracking error (< 0.5%).
* **Sharpe** — > 0 (beat cash on a risk-adjusted basis).
* **Top-10 concentration** — ≤ 30% for diversified holdings.
* **Holdings count** — ≥ 50 (more for total-market funds).
* **Distribution policy** — declared (Acc / Dist / unknown).

Each check returns a *rule of thumb* string so the user sees both the
fund's value and the threshold itself.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from lynx_fund.models import FundReport, PassiveCheck


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pass(label: str, message: str, rule: str) -> PassiveCheck:
    return PassiveCheck(label=label, status="pass", message=message, rule_of_thumb=rule)


def _warn(label: str, message: str, rule: str) -> PassiveCheck:
    return PassiveCheck(label=label, status="warn", message=message, rule_of_thumb=rule)


def _fail(label: str, message: str, rule: str) -> PassiveCheck:
    return PassiveCheck(label=label, status="fail", message=message, rule_of_thumb=rule)


def _info(label: str, message: str, rule: str = "") -> PassiveCheck:
    return PassiveCheck(label=label, status="info", message=message, rule_of_thumb=rule)


def _na(label: str, rule: str) -> PassiveCheck:
    return PassiveCheck(label=label, status="info",
                        message="No data available — verify on the issuer prospectus.",
                        rule_of_thumb=rule)


def _category_ter_threshold(report: FundReport) -> tuple[float, str]:
    """Pick a TER threshold by fund flavour."""
    if report.profile.is_index_fund:
        return (0.0010, "index fund")
    cat = (report.profile.category or "").lower()
    if any(k in cat for k in ("sector", "thematic", "leveraged", "industry")):
        return (0.0075, "sector / thematic")
    if any(k in cat for k in ("emerging", "frontier", "small")):
        return (0.0085, "emerging / small-cap")
    return (0.0050, "broad-market active")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_ter(report: FundReport) -> PassiveCheck:
    threshold, label = _category_ter_threshold(report)
    rule = f"TER ≤ {threshold * 100:.2f}% for a {label}"
    er = report.costs.expense_ratio if report.costs else None
    if er is None:
        return _na("Expense Ratio (TER)", rule)
    pct = er * 100
    if er <= threshold:
        return _pass("Expense Ratio (TER)",
                     f"{pct:.2f}% — within the {label} threshold.", rule)
    if er <= threshold * 2:
        return _warn("Expense Ratio (TER)",
                     f"{pct:.2f}% — above the {label} threshold; "
                     "compare with the institutional / Admiral share class.",
                     rule)
    return _fail("Expense Ratio (TER)",
                 f"{pct:.2f}% — well above the {label} threshold; "
                 "this drag compounds for decades.", rule)


def _check_front_load(report: FundReport) -> PassiveCheck:
    rule = "No front-end sales load — no-load funds are widely available"
    fl = report.costs.front_load_max if report.costs else None
    if fl is None:
        return _info("Front-End Load",
                     "Not disclosed in this dataset — verify with the prospectus.",
                     rule)
    if fl <= 0:
        return _pass("Front-End Load", "0.00% — no-load fund.", rule)
    if fl <= 0.025:
        return _warn("Front-End Load",
                     f"{fl*100:.2f}% — moderate load; check no-load alternatives.",
                     rule)
    return _fail("Front-End Load",
                 f"{fl*100:.2f}% — direct return drag, almost never justified for retail.",
                 rule)


def _check_deferred_load(report: FundReport) -> PassiveCheck:
    rule = "No back-end / contingent deferred sales charge (CDSC)"
    dl = report.costs.deferred_load_max if report.costs else None
    if dl is None:
        return _info("Deferred Load (CDSC)", "Not disclosed.", rule)
    if dl <= 0:
        return _pass("Deferred Load (CDSC)", "0.00% — no back-end load.", rule)
    return _warn("Deferred Load (CDSC)",
                 f"{dl*100:.2f}% — CDSC schedule; redeem too early and you pay.",
                 rule)


def _check_12b1(report: FundReport) -> PassiveCheck:
    rule = "12b-1 fee = 0% (or close) — marketing fees should not be paid by you"
    fee = report.costs.twelve_b1_fee if report.costs else None
    if fee is None:
        return _info("12b-1 Fee", "Not disclosed.", rule)
    if fee <= 0.0001:
        return _pass("12b-1 Fee", "0.00% — no distribution fee.", rule)
    if fee <= 0.0025:
        return _warn("12b-1 Fee",
                     f"{fee*100:.2f}% — small but observable; check if a no-12b-1 share class exists.",
                     rule)
    return _fail("12b-1 Fee",
                 f"{fee*100:.2f}% — material distribution fee; switch share class if possible.",
                 rule)


def _check_aum(report: FundReport) -> PassiveCheck:
    rule = "AUM ≥ $100M to minimise closure risk"
    aum = (report.liquidity.aum if report.liquidity else None) or report.profile.aum
    if aum is None:
        return _na("Assets Under Management", rule)
    if aum >= 1e9:
        return _pass("Assets Under Management",
                     f"${aum/1e9:.1f}B — deep AUM, closure risk negligible.", rule)
    if aum >= 100e6:
        return _pass("Assets Under Management",
                     f"${aum/1e6:.0f}M — above the $100M closure-risk floor.", rule)
    if aum >= 50e6:
        return _warn("Assets Under Management",
                     f"${aum/1e6:.0f}M — modest size; closures occur in this band.",
                     rule)
    return _fail("Assets Under Management",
                 f"${aum/1e6:.1f}M — high closure risk for buy-and-hold investors.",
                 rule)


def _check_age(report: FundReport) -> PassiveCheck:
    rule = "Fund age ≥ 3 years for an established record"
    age = report.liquidity.fund_age_years if report.liquidity else None
    if age is None:
        return _na("Fund Age", rule)
    if age >= 5:
        return _pass("Fund Age", f"{age:.1f} years — established track record.", rule)
    if age >= 3:
        return _pass("Fund Age", f"{age:.1f} years — meets the 3-year guideline.", rule)
    if age >= 1:
        return _warn("Fund Age",
                     f"{age:.1f} years — under the 3-year guideline; "
                     "performance signals are noisy this early.", rule)
    return _fail("Fund Age",
                 f"{age:.1f} years — too young to evaluate as a passive holding.",
                 rule)


def _check_cap_gains(report: FundReport) -> PassiveCheck:
    rule = "Capital-gain distributions ≤ 1% of NAV (3Y avg) for taxable accounts"
    cgd = report.income.cap_gain_distributions_3y_avg if report.income else None
    if cgd is None:
        return _na("Capital-Gain Distributions", rule)
    pct = cgd * 100
    if cgd <= 0.005:
        return _pass("Capital-Gain Distributions",
                     f"{pct:.2f}%/yr — minimal tax drag.", rule)
    if cgd <= 0.01:
        return _pass("Capital-Gain Distributions",
                     f"{pct:.2f}%/yr — within the passive guideline.", rule)
    if cgd <= 0.03:
        return _warn("Capital-Gain Distributions",
                     f"{pct:.2f}%/yr — material tax drag in taxable accounts.",
                     rule)
    return _fail("Capital-Gain Distributions",
                 f"{pct:.2f}%/yr — large tax drag; consider tax-deferred wrapper.",
                 rule)


def _check_embedded_gain(report: FundReport) -> PassiveCheck:
    rule = "Embedded unrealised gains ≤ 15% of NAV — avoids tax-bomb on entry"
    g = report.income.embedded_unrealised_gain_pct if report.income else None
    if g is None:
        return _info("Embedded Gains",
                     "Not disclosed — check the prospectus' tax exhibits.",
                     rule)
    if g <= 0.10:
        return _pass("Embedded Gains",
                     f"{g*100:.0f}% — low tax-bomb risk on entry.", rule)
    if g <= 0.20:
        return _warn("Embedded Gains",
                     f"{g*100:.0f}% — meaningful unrealised gains; "
                     "if the fund liquidates, you pay tax on prior gains.",
                     rule)
    return _fail("Embedded Gains",
                 f"{g*100:.0f}% — large tax bomb; better held inside a tax-deferred account.",
                 rule)


def _check_persistence(report: FundReport) -> PassiveCheck:
    rule = "Top-quartile in ≥ 2 of the last 5 years (active funds)"
    if report.profile.is_index_fund:
        return _info("Persistence",
                     "Index fund — persistence is automatic if tracking error stays small.",
                     rule)
    score = report.performance.persistence_score if report.performance else None
    top_q = report.performance.top_quartile_periods_5y if report.performance else None
    if score is None and top_q is None:
        return _na("Persistence", rule)
    if top_q is not None:
        if top_q >= 4:
            return _pass("Persistence",
                         f"Top quartile in {top_q}/5 years — exceptional persistence.",
                         rule)
        if top_q >= 2:
            return _pass("Persistence",
                         f"Top quartile in {top_q}/5 years — meets the guideline.",
                         rule)
        if top_q >= 1:
            return _warn("Persistence",
                         f"Top quartile in {top_q}/5 years — only one good year.",
                         rule)
        return _fail("Persistence",
                     "Never finished top quartile in the last 5 years.",
                     rule)
    return _info("Persistence", f"Score {score:.0f}/100.", rule)


def _check_active_share(report: FundReport) -> PassiveCheck:
    rule = "Active share ≥ 0.60 for active funds (avoids closet indexing)"
    if report.profile.is_index_fund:
        return _info("Active Share",
                     "Index fund — active share is by design close to 0.",
                     rule)
    a = (
        report.profile.active_share
        or (report.risk.active_share if report.risk else None)
    )
    if a is None:
        return _na("Active Share", rule)
    if a >= 0.80:
        return _pass("Active Share",
                     f"{a*100:.0f}% — genuinely active.", rule)
    if a >= 0.60:
        return _pass("Active Share",
                     f"{a*100:.0f}% — meets the active-fund guideline.",
                     rule)
    if a >= 0.40:
        return _warn("Active Share",
                     f"{a*100:.0f}% — closet indexer; you pay active fees for near-index returns.",
                     rule)
    return _fail("Active Share",
                 f"{a*100:.0f}% — closet indexer; switch to the index fund.",
                 rule)


def _check_manager_tenure(report: FundReport) -> PassiveCheck:
    rule = "Avg manager tenure ≥ 5 years (longer for active funds)"
    if report.profile.is_index_fund:
        return _info("Manager Tenure",
                     "Index fund — manager identity is largely irrelevant.",
                     rule)
    t = report.profile.avg_manager_tenure_years
    if t is None:
        return _na("Manager Tenure", rule)
    if t >= 10:
        return _pass("Manager Tenure",
                     f"{t:.1f} years — long-tenured, evaluatable record.",
                     rule)
    if t >= 5:
        return _pass("Manager Tenure",
                     f"{t:.1f} years — meets the active-fund guideline.",
                     rule)
    if t >= 2:
        return _warn("Manager Tenure",
                     f"{t:.1f} years — too short to attribute past performance.",
                     rule)
    return _fail("Manager Tenure",
                 f"{t:.1f} years — track record is essentially someone else's.",
                 rule)


def _check_tax_form(report: FundReport) -> PassiveCheck:
    rule = "1099 (mutual fund) preferred over K-1 (partnership)"
    tax_form = report.income.tax_form if report.income else None
    if not tax_form:
        return _info("Tax Form",
                     "Not disclosed — most US mutual funds issue 1099-DIV.",
                     rule)
    if tax_form.upper().startswith("K"):
        return _warn("Tax Form",
                     f"{tax_form} — partnership-style; meaningfully more "
                     "tax paperwork. Confirm before investing in taxable accounts.",
                     rule)
    return _pass("Tax Form", f"{tax_form} — standard mutual-fund tax form.", rule)


def _check_open_to_new(report: FundReport) -> PassiveCheck:
    rule = "Fund is open for new subscriptions"
    if report.liquidity is None:
        return _na("Open to New Investors", rule)
    if report.liquidity.hard_closed:
        return _fail("Open to New Investors",
                     "Fund is HARD-closed — no new subscriptions accepted.",
                     rule)
    if report.liquidity.soft_closed:
        return _warn("Open to New Investors",
                     "Fund is SOFT-closed — new investors blocked but existing holders can add.",
                     rule)
    if report.liquidity.is_open_to_new_investors is False:
        return _warn("Open to New Investors",
                     "Fund is closed to new investors.",
                     rule)
    return _pass("Open to New Investors", "Open for new subscriptions.", rule)


def _check_minimum_investment(report: FundReport) -> PassiveCheck:
    rule = "Minimum initial investment is realistic for your account size"
    m = report.liquidity.minimum_initial_investment if report.liquidity else None
    if m is None:
        return _info("Minimum Investment",
                     "Not disclosed — typical retail mutual-fund minimums are $1k–$3k.",
                     rule)
    if m >= 1_000_000:
        return _info("Minimum Investment",
                     f"${m:,.0f} — institutional share class.",
                     rule)
    if m >= 100_000:
        return _info("Minimum Investment",
                     f"${m:,.0f} — high-net-worth share class.",
                     rule)
    if m >= 3000:
        return _info("Minimum Investment",
                     f"${m:,.0f} — standard retail entry point.",
                     rule)
    return _info("Minimum Investment",
                 f"${m:,.0f} — accessible.",
                 rule)


def _check_index_tracking(report: FundReport) -> PassiveCheck:
    rule = "Index fund: tracking error ≤ 0.50% / 50 bps"
    if not report.profile.is_index_fund:
        return _info("Index Tracking",
                     "Active fund — tracking error is by design > 0.",
                     rule)
    te = report.risk.tracking_error if report.risk else None
    if te is None:
        return _na("Index Tracking", rule)
    pct = te * 100
    if te <= 0.005:
        return _pass("Index Tracking",
                     f"{pct:.2f}% — tight tracking, classic index fund.",
                     rule)
    if te <= 0.01:
        return _warn("Index Tracking",
                     f"{pct:.2f}% — tracking is loose for an index fund.",
                     rule)
    return _fail("Index Tracking",
                 f"{pct:.2f}% — wide gap to benchmark for a stated index fund.",
                 rule)


def _check_top10(report: FundReport) -> PassiveCheck:
    rule = "Top-10 weight ≤ 30% to stay broadly diversified"
    a = report.allocation
    top10 = a.top10_concentration if a else None
    if top10 is None:
        return _na("Top-10 Concentration", rule)
    pct = top10 * 100
    if top10 <= 0.20:
        return _pass("Top-10 Concentration",
                     f"{pct:.1f}% — broadly diversified.", rule)
    if top10 <= 0.30:
        return _pass("Top-10 Concentration",
                     f"{pct:.1f}% — at the diversification ceiling.", rule)
    if top10 <= 0.50:
        return _warn("Top-10 Concentration",
                     f"{pct:.1f}% — concentrated; cap-weighted indexes can drift here.",
                     rule)
    return _fail("Top-10 Concentration",
                 f"{pct:.1f}% — heavily concentrated.", rule)


def _check_holdings_count(report: FundReport) -> PassiveCheck:
    rule = "≥ 50 holdings (more for total-market funds)"
    a = report.allocation
    n = a.holdings_count if a else None
    if n is None:
        return _na("Holdings Count", rule)
    if n >= 500:
        return _pass("Holdings Count",
                     f"{n} holdings — total-market-grade diversification.",
                     rule)
    if n >= 100:
        return _pass("Holdings Count",
                     f"{n} holdings — broadly diversified.", rule)
    if n >= 50:
        return _pass("Holdings Count",
                     f"{n} holdings — meets the diversification guideline.",
                     rule)
    if n >= 25:
        return _warn("Holdings Count",
                     f"{n} holdings — narrow basket; idiosyncratic risk is meaningful.",
                     rule)
    return _fail("Holdings Count",
                 f"{n} holdings — concentrated; closer to single-stock risk than passive.",
                 rule)


def _check_sharpe(report: FundReport) -> PassiveCheck:
    rule = "Sharpe (3Y) > 0 — at least beating cash"
    p = report.performance
    s = p.sharpe_3y if p else None
    if s is None:
        return _na("Sharpe (3Y)", rule)
    if s >= 1.0:
        return _pass("Sharpe (3Y)", f"{s:.2f} — strong risk-adjusted return.", rule)
    if s >= 0.5:
        return _pass("Sharpe (3Y)", f"{s:.2f} — acceptable risk-adjusted return.", rule)
    if s >= 0:
        return _warn("Sharpe (3Y)", f"{s:.2f} — barely beating risk-free.", rule)
    return _fail("Sharpe (3Y)",
                 f"{s:.2f} — underperforming cash on a risk-adjusted basis.",
                 rule)


def _check_max_drawdown(report: FundReport) -> PassiveCheck:
    rule = "Investor must accept the worst observed drawdown"
    r = report.risk
    dd = r.max_drawdown_3y if r else None
    if dd is None:
        return _na("Max Drawdown (3Y)", rule)
    pct = dd * 100
    if dd > -0.10:
        return _pass("Max Drawdown (3Y)",
                     f"{pct:.1f}% — mild; suitable for low-volatility allocations.",
                     rule)
    if dd > -0.20:
        return _info("Max Drawdown (3Y)",
                     f"{pct:.1f}% — typical for diversified equity.", rule)
    if dd > -0.40:
        return _warn("Max Drawdown (3Y)",
                     f"{pct:.1f}% — severe; verify your time horizon survives this.",
                     rule)
    return _fail("Max Drawdown (3Y)",
                 f"{pct:.1f}% — crash-tier loss; not a low-risk holding.",
                 rule)


def _check_distribution_policy(report: FundReport) -> PassiveCheck:
    rule = "Distribution policy declared (Accumulating vs Distributing)"
    pol = report.profile.distribution_policy or (
        report.income.distribution_policy if report.income else None
    )
    if not pol:
        return _info("Distribution Policy",
                     "Not disclosed; if you reinvest dividends manually, either works.",
                     rule)
    pol_lower = pol.lower()
    if "accum" in pol_lower:
        return _pass("Distribution Policy",
                     f"{pol} — best for compounding inside tax-advantaged accounts.",
                     rule)
    if "distribut" in pol_lower:
        return _pass("Distribution Policy",
                     f"{pol} — fits an income-focused strategy.",
                     rule)
    return _info("Distribution Policy", f"{pol} — verify how it suits your goal.", rule)


def _check_ucits(report: FundReport) -> Optional[PassiveCheck]:
    if report.profile.ucits is None:
        return None
    rule = "UCITS-compliant for EU retail eligibility"
    if report.profile.ucits:
        return _pass("UCITS Compliance",
                     "UCITS-compliant — eligible across EU retail brokerages.",
                     rule)
    return _warn("UCITS Compliance",
                 "Not UCITS-compliant — EU retail brokers may not allow this fund.",
                 rule)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

_CHECKS = (
    _check_ter,
    _check_front_load,
    _check_deferred_load,
    _check_12b1,
    _check_aum,
    _check_age,
    _check_cap_gains,
    _check_embedded_gain,
    _check_persistence,
    _check_active_share,
    _check_manager_tenure,
    _check_tax_form,
    _check_open_to_new,
    _check_minimum_investment,
    _check_index_tracking,
    _check_top10,
    _check_holdings_count,
    _check_sharpe,
    _check_max_drawdown,
    _check_distribution_policy,
)

_OPTIONAL_CHECKS = (_check_ucits,)


def run_passive_checklist(report: FundReport) -> List[PassiveCheck]:
    """Run every passive-investor check against *report*."""
    out: List[PassiveCheck] = []
    for fn in _CHECKS:
        try:
            result = fn(report)
        except Exception as exc:  # noqa: BLE001
            result = PassiveCheck(
                label=fn.__name__.replace("_check_", "").replace("_", " ").title(),
                status="info",
                message=f"Check skipped: {exc}",
                rule_of_thumb="",
            )
        out.append(result)

    for fn in _OPTIONAL_CHECKS:
        try:
            result = fn(report)
            if result is not None:
                out.append(result)
        except Exception:
            pass
    return out


def summarize_status(checks: Iterable[PassiveCheck]) -> dict:
    """Return a `{pass, warn, fail, info}` count summary."""
    counts = {"pass": 0, "warn": 0, "fail": 0, "info": 0}
    for c in checks:
        counts[c.status] = counts.get(c.status, 0) + 1
    return counts
