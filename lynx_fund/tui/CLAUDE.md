# lynx_fund.tui — package guidance

The Textual full-screen UI mode. One of four front-ends over the shared
`core`/`display` layer. See `ARCHITECTURE.md`.

## Responsibility

Render fund analysis as an interactive Textual app: ticker input, analysis
view, About modal, and theme cycling. Presentation only — analysis comes from
`core.analyzer`.

## Public interface

- `app.run_tui(initial_ticker=None)` — launch the TUI (invoked by `cli.py` for
  `-tui`).
- `app.LynxFundApp` (Textual `App`), `app.AboutModal` (`ModalScreen`).
- `themes.register_all_themes(app)`, `themes.THEME_NAMES`,
  `themes.LYNX_DARK`, `themes.LYNX_LIGHT`.

## Module-local conventions

- **House themes + Suite themes.** `themes.py` defines the local `LYNX_DARK` /
  `LYNX_LIGHT` and registers the Suite gallery via
  `lynx_investor_core.themes.register_suite_themes()`. Add house themes here;
  don't duplicate Suite themes.
- **Call into `core`, never the reverse.** This package imports
  `core.ticker` (for `NotAFundError`) and runs analysis through `core.analyzer`;
  domain code must not import the TUI.
- **Translate labels.** Modal text, bindings hints, and menu strings use
  `_t("key", default="English")`.
- Keep report content in sync with the other UI modes by sourcing it from
  `models`/`display`, not by re-deriving values here.
