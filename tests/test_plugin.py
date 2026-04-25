"""Suite plugin registration tests."""

from __future__ import annotations

from lynx_fund.plugin import register


def test_register_returns_sector_agent():
    agent = register()
    assert agent.name == "lynx-fund"
    assert agent.short_name == "etf"
    assert agent.prog_name == "lynx-fund"
    assert agent.package_module == "lynx_fund"
    assert agent.entry_point_module == "lynx_fund.__main__"
    assert agent.entry_point_function == "main"


def test_tagline_mentions_etf():
    agent = register()
    assert "ETF" in agent.tagline or "Exchange" in agent.tagline
