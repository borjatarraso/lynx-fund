# CLAUDE.md — lynx-fund

Project-level guidance for agents working in this repo. Keep it terse; see the
per-package `CLAUDE.md` files and the blueprint docs for detail.

## What this is

`lynx-fund` is a command-line tool that analyses **open-ended mutual funds and
index funds** (MUTUALFUND / OEIC / SICAV / UCITS). It fetches fund data from
yfinance, computes cost / income / liquidity / performance / allocation / risk
metrics, scores a 0–100 verdict, and renders a report in four UI modes
(console, interactive REPL, Textual TUI, Tkinter GUI). It is one agent of the
**Lince Investor Suite** and depends on the shared `lynx-investor-core` package.

**Scope guard:** stocks, ETFs/ETNs, closed-end funds, and bare indices are
**rejected** at the resolver (`lynx_fund/core/ticker.py`) with an error pointing
to the right Suite tool. That file is the source of truth for what is accepted —
note that `README.md` and `lynx_fund/__init__.py`'s `about` text currently
describe the scope as "ETFs", which contradicts the code (see `ROADMAP.md`).

## Layout

```
lynx_fund/            the package (single installed distribution)
  cli.py              argparse dispatcher — the entry point for every mode
  __main__.py         `lynx-fund` console script → cli.run_cli
  models.py           dataclasses/enums for the whole report
  display.py          Rich console renderer
  passive_checklist.py / tips.py   passive-investor heuristics & education
  interactive.py      REPL mode
  core/               domain logic: ticker resolve, fetch, news, storage, analyze
  metrics/            metric calculators, explanations (--explain), relevance
  tui/                Textual TUI + house themes
  gui/                Tkinter GUI
tests/                pytest suite (mirrors the modules)
docs/                 reference docs (API, data sources, storage, metrics)
data/  data_test/     on-disk cache (production / testing); owned by core.storage
```

See `ARCHITECTURE.md` for the dataflow and import direction, `DESIGN.md` for the
rationale behind the key decisions, and `ROADMAP.md` for known gaps.

## Build / test / run

```bash
pip install -e .            # editable install (pulls lynx-investor-core, yfinance, …)
pytest                      # full suite (config in pyproject.toml: testpaths=tests)
pytest tests/test_cli.py    # one file
lynx-fund -p VFIAX          # production analysis (cache-first)
lynx-fund -p VFIAX --refresh   # force fresh fetch
lynx-fund -p -i             # interactive REPL    (-tui / -x for TUI / GUI)
lynx-fund --explain expense_ratio
```

Network calls go through yfinance; tests must not hit the network — use the
`testing` storage mode / fixtures (see `tests/conftest.py`).

## Conventions for agents

- **Don't break the package boundary.** Everything ships as the single
  `lynx_fund` package; imports are `lynx_fund.<sub>...`. Do not promote
  subpackages to top-level dirs or rename the package — it breaks the console
  script and the `lynx_investor_suite.agents` plugin entry point in
  `pyproject.toml`.
- **Best-effort data.** Fetchers and calculators return `None` / empty rather
  than raising when upstream data is missing. Preserve that — renderers expect
  `None` and print `—`.
- **Cache-first.** `core.analyzer` reads disk before fetching; only `--refresh`
  bypasses it. All disk I/O goes through `core.storage`, never raw `open()`.
- **i18n.** User-facing strings go through `t()` from
  `lynx_investor_core.translations` (imported as `_t`), with an English default:
  `_t("key", default="English")`. Don't hardcode user-visible English.
- **No new heavy deps.** Reuse `lynx-investor-core` (themes, debounce, footer,
  language widget) instead of reimplementing.
- Keep the four UI modes at feature parity when changing report content.

<!-- LYNX-EP-NOTE:BEGIN -->

## Entry-point card — keep it current

This project carries `index.ep.md` (and `index.ep.html`), the standard card
that answers what this is, where to look first, and how to run it. Every
project in `~/claude/` has one in the same shape, so jumping between them
does not mean re-learning where to look.

**When work here changes any of the following, refresh the card:**

- what the project is or does (title, one-line purpose, description)
- the file someone should open first
- the command that starts it
- the top-level layout or where the documentation lives

Refresh it with:

```bash
python3 ~/claude/lynx_factory/web/tools/gen_ep_index.py --only <this-project>
```

That regenerates from this repo's own README/CLAUDE.md plus the Lynx Factory
ledger — it does not invent anything, so fixing the card usually means fixing
the README first. The README's ownership footer is refreshed by the same
command.

To hand-write a card and stop it being regenerated, set `ep_locked: true` in
its front matter.

<!-- LYNX-EP-NOTE:END -->
