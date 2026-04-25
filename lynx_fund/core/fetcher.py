"""Fund data fetching via yfinance.

yfinance covers most US-domiciled mutual / index funds (e.g. ``VFIAX``,
``FXAIX``, ``VTSAX``, ``SWPPX``) reasonably well. For UCITS / OEICs the
upstream coverage is sparser; the fetcher falls back to ``None`` /
empty defaults so the rest of the pipeline keeps working.

The fetcher populates as many fund-specific fields as the data source
exposes (loads, 12b-1, manager tenure, fund type, soft-close,
minimums) and leaves the rest blank for the calculator and display
layers to handle gracefully.
"""

from __future__ import annotations

from typing import Optional

from lynx_fund.models import FundProfile, Holding, ManagerInfo, classify_tier


# ---------------------------------------------------------------------------
# Top-level fetchers
# ---------------------------------------------------------------------------

def fetch_info(ticker: str) -> dict:
    """Fetch yfinance Ticker.info as a plain dict (best-effort)."""
    try:
        import yfinance as yf
    except ImportError:
        return {}
    try:
        return dict(yf.Ticker(ticker).info or {})
    except Exception:
        return {}


def fetch_profile(ticker: str, info: Optional[dict] = None) -> FundProfile:
    """Build a :class:`FundProfile` from yfinance info."""
    info = info if info is not None else fetch_info(ticker)

    name = (
        info.get("longName")
        or info.get("shortName")
        or info.get("name")
        or ticker
    )
    aum = _coerce_float(info.get("totalAssets") or info.get("netAssets"))
    inception_ts = info.get("fundInceptionDate")
    inception_date = _epoch_to_iso(inception_ts)

    is_index = _infer_is_index_fund(info)
    fund_type = _infer_fund_type(info)
    domicile = info.get("domicile") or info.get("region") or info.get("country")

    # Manager block ----------------------------------------------------------
    managers, avg_tenure, longest_tenure = _extract_managers(info)

    profile = FundProfile(
        ticker=ticker,
        name=str(name),
        category=info.get("category"),
        asset_class=info.get("legalType") or _infer_asset_class(info),
        fund_family=info.get("fundFamily"),
        domicile=domicile,
        inception_date=inception_date,
        exchange=info.get("exchange") or info.get("fullExchangeName"),
        currency=info.get("currency"),
        aum=aum,
        description=info.get("longBusinessSummary") or info.get("description"),
        website=info.get("website"),
        benchmark=info.get("benchmark") or info.get("trackingIndex"),
        distribution_policy=_infer_distribution_policy(info),
        # ── Fund-specific structure ─────────────────────────────────────
        fund_type=fund_type,
        is_index_fund=is_index,
        is_actively_managed=(False if is_index else (True if is_index is False else None)),
        legal_structure=info.get("legalStructure"),
        ucits=_infer_ucits(info, domicile),
        kiid_prr_risk_rating=info.get("kiidRiskRating") or info.get("priipRiskRating"),
        soft_closed=_coerce_bool(info.get("softClosed") or info.get("isSoftClosed")),
        hard_closed=_coerce_bool(info.get("hardClosed") or info.get("isHardClosed")),
        pricing_frequency=info.get("pricingFrequency") or "Daily NAV (forward priced)",
        cutoff_time_local=info.get("cutoffTime"),
        swing_pricing=_coerce_bool(info.get("swingPricing")),
        redemption_gates=_coerce_bool(info.get("redemptionGates")),
        lockup_period_days=_coerce_int(info.get("lockupPeriodDays")),
        # ── Manager(s) ──────────────────────────────────────────────────
        managers=managers,
        avg_manager_tenure_years=avg_tenure,
        longest_manager_tenure_years=longest_tenure,
        manager_of_managers=_coerce_bool(info.get("managerOfManagers")),
        # ── Active/passive signals ──────────────────────────────────────
        active_share=_coerce_float(info.get("activeShare")),
        # ── Operational / governance ────────────────────────────────────
        trustee_or_custodian=info.get("custodian") or info.get("trustee"),
        auditor=info.get("auditor"),
        sponsor_or_advisor=info.get("sponsor") or info.get("advisor"),
        transfer_agent=info.get("transferAgent"),
        morningstar_rating=_coerce_int(info.get("morningstarOverallRating")),
        sustainability_rating=info.get("sustainabilityRating"),
    )
    profile.tier = classify_tier(aum)
    return profile


def fetch_history(ticker: str, period: str = "10y"):
    """Fetch price history as a pandas DataFrame (or None)."""
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        hist = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        if hist is None or hist.empty:
            return None
        return hist
    except Exception:
        return None


def fetch_holdings(ticker: str, info: Optional[dict] = None) -> list[Holding]:
    """Return the fund's top holdings as a list of :class:`Holding`."""
    info = info if info is not None else fetch_info(ticker)
    raw = info.get("holdings") or info.get("topHoldings")
    if isinstance(raw, dict):
        raw = raw.get("holdings") or raw.get("topHoldings") or []
    if not raw:
        return []

    out: list[Holding] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        weight = _coerce_float(
            row.get("holdingPercent")
            or row.get("weight")
            or row.get("percent")
        )
        if weight is not None and weight > 1:
            weight = weight / 100.0
        out.append(Holding(
            symbol=row.get("symbol") or row.get("ticker"),
            name=row.get("holdingName") or row.get("name"),
            weight=weight,
            sector=row.get("sector"),
            country=row.get("country"),
        ))
    return out


def fetch_sector_breakdown(ticker: str, info: Optional[dict] = None) -> list[tuple]:
    info = info if info is not None else fetch_info(ticker)
    raw = info.get("sectorWeightings") or info.get("sector_weightings")
    return _normalise_breakdown(raw)


def fetch_country_breakdown(ticker: str, info: Optional[dict] = None) -> list[tuple]:
    info = info if info is not None else fetch_info(ticker)
    raw = (
        info.get("countryWeightings")
        or info.get("country_weightings")
        or info.get("geoWeightings")
    )
    return _normalise_breakdown(raw)


def fetch_asset_class_breakdown(ticker: str, info: Optional[dict] = None) -> list[tuple]:
    info = info if info is not None else fetch_info(ticker)
    raw = info.get("bondHoldings") or info.get("assetClassWeightings")
    return _normalise_breakdown(raw)


def fetch_benchmark_history(benchmark_ticker: str, period: str = "5y"):
    return fetch_history(benchmark_ticker, period=period)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _coerce_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _coerce_bool(v) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    return None


def _epoch_to_iso(v) -> Optional[str]:
    if v is None:
        return None
    try:
        from datetime import datetime, timezone
        secs = float(v)
        return datetime.fromtimestamp(secs, tz=timezone.utc).date().isoformat()
    except Exception:
        return None


def _infer_asset_class(info: dict) -> Optional[str]:
    cat = (info.get("category") or "").lower()
    if any(k in cat for k in ["bond", "treasury", "fixed income", "credit"]):
        return "Fixed Income"
    if any(k in cat for k in ["commodity", "gold", "silver", "oil"]):
        return "Commodity"
    if any(k in cat for k in ["allocation", "multi-asset", "target"]):
        return "Multi-Asset"
    if any(k in cat for k in ["equity", "stock", "blend", "value", "growth"]):
        return "Equity"
    return None


def _infer_distribution_policy(info: dict) -> Optional[str]:
    name = (info.get("longName") or info.get("shortName") or "").lower()
    if any(k in name for k in [" acc", " accumulating", " accumulation"]):
        return "Accumulating"
    if " dist" in name or " distributing" in name:
        return "Distributing"
    if info.get("dividendYield") or info.get("trailingAnnualDividendYield"):
        return "Distributing"
    return None


def _infer_is_index_fund(info: dict) -> Optional[bool]:
    name = (info.get("longName") or info.get("shortName") or "").lower()
    cat = (info.get("category") or "").lower()
    if any(k in name for k in ("index fund", " idx ", "500 index", "total stock market index")):
        return True
    if any(k in cat for k in ("index", "passive")):
        return True
    return None


def _infer_fund_type(info: dict) -> Optional[str]:
    qt = str(info.get("quoteType", "")).upper()
    if qt in ("MUTUALFUND", "MUTUAL_FUND"):
        if _infer_is_index_fund(info):
            return "Index Fund"
        return "Mutual Fund"
    if qt in ("OEIC", "SICAV", "UCITS"):
        return qt
    if "ucits" in (info.get("longName") or "").lower():
        return "UCITS"
    return None


def _infer_ucits(info: dict, domicile: Optional[str]) -> Optional[bool]:
    name = (info.get("longName") or "").lower()
    if "ucits" in name:
        return True
    eu = {"IE", "LU", "FR", "DE", "ES", "IT", "NL", "BE", "AT"}
    if domicile and domicile.upper() in eu:
        return True
    if domicile and domicile.upper() == "US":
        return False
    return None


def _extract_managers(info: dict) -> tuple[list[ManagerInfo], Optional[float], Optional[float]]:
    raw = info.get("managers") or info.get("fundManagers") or []
    if isinstance(raw, dict):
        raw = [raw]
    managers: list[ManagerInfo] = []
    tenures: list[float] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        tenure = _coerce_float(row.get("tenureYears") or row.get("tenure"))
        if tenure is not None:
            tenures.append(tenure)
        managers.append(ManagerInfo(
            name=str(row.get("name") or ""),
            role=row.get("role"),
            tenure_years=tenure,
            started_on=row.get("startedOn") or row.get("startDate"),
        ))
    avg = sum(tenures) / len(tenures) if tenures else None
    longest = max(tenures) if tenures else None
    return managers, avg, longest


def _normalise_breakdown(raw) -> list[tuple]:
    out: list[tuple] = []
    if not raw:
        return out

    if isinstance(raw, dict):
        for k, v in raw.items():
            w = _coerce_float(v)
            if w is None:
                continue
            if w > 1:
                w = w / 100.0
            out.append((str(k).replace("_", " ").title(), w))
    elif isinstance(raw, list):
        for row in raw:
            if isinstance(row, dict):
                if "name" in row or "sector" in row:
                    label = row.get("name") or row.get("sector") or ""
                    w = _coerce_float(row.get("weight") or row.get("percent"))
                    if w is not None and w > 1:
                        w = w / 100.0
                    if label and w is not None:
                        out.append((str(label), w))
                else:
                    for k, v in row.items():
                        w = _coerce_float(v)
                        if w is None:
                            continue
                        if w > 1:
                            w = w / 100.0
                        out.append((str(k).replace("_", " ").title(), w))
    out.sort(key=lambda kv: kv[1] or 0, reverse=True)
    return out
