# lynx_fund — package guidance

The single installed package for lynx-fund. Everything ships under this path as
one distribution; subpackages (`core`, `metrics`, `tui`, `gui`) have their own
`CLAUDE.md`. See the repo-root `CLAUDE.md` for build/test commands and
`ARCHITECTURE.md` for the dataflow.

## Responsibility

Resolve a fund identifier, analyse it, and present a scored report in four UI
modes. This top-level of the package owns **dispatch, domain types, rendering,
and the passive-investor heuristics**; data fetching/storage/analysis live in
`core/`, metric math in `metrics/`.

## Public interface

- `__main__.main()` — the `lynx-fund` console-script entry point.
- `cli.run_cli(argv=None)` / `cli.build_parser()` — argument parsing and mode
  dispatch (`-p/-t` storage mode, `-i/-tui/-x` UI modes, `--search`,
  `--explain`, `--export`, cache flags).
- `models.*` — the dataclasses/enums every other module exchanges
  (`FundReport`, `Verdict`, `CostMetrics`, …) and `classify_tier(aum)`.
- `display.render_full_report(report)` and `render_about()` — console rendering.
- `interactive.run_interactive(args)` — REPL mode.
- `passive_checklist.run_passive_checklist(report)` /
  `tips.compose_tips(report, ...)` — passive-investor checks & education.
- `plugin.register()` — Suite plugin descriptor.

## Module-local conventions

- **Import as `lynx_fund.<module>`.** Don't introduce top-level (sibling)
  packages; the console script and the `lynx_investor_suite.agents` plugin key
  off this package path.
- **`models.py` is the contract.** Add/extend fields there with `None` defaults;
  don't pass ad-hoc dicts between modules.
- **`display.py` depends only on `models`** — keep fetching/compute out of it so
  all four UI modes can reuse it. Render `None` as `—`.
- **User-visible strings use `_t("key", default="English")`** from
  `lynx_investor_core.translations`. No hardcoded English in output.
- New report sections flow through `models` → `metrics`/`core` → `display`, so
  console, interactive, TUI, and GUI all pick them up.
