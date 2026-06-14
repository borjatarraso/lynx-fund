# lynx_fund.gui — package guidance

The Tkinter desktop UI mode. One of four front-ends over the shared
`core`/`display` layer. See `ARCHITECTURE.md`.

## Responsibility

Render fund analysis in a Tkinter window: splash, ticker input, scrolled
analysis canvas, and Analyze / Refresh / Export / Language / Quit controls.
Presentation only — analysis comes from `core.analyzer`.

## Public interface

- `app.run_gui(args=None)` — launch the GUI (invoked by `cli.py` for `-x`).

## Module-local conventions

- **Non-blocking analysis.** Long fetches run on a worker thread and post results
  back through a `queue` polled on the Tk main loop — keep new work off the UI
  thread to avoid freezing the window.
- **Debounce user actions.** Buttons go through
  `lynx_investor_core.debounce.ClickDebouncer` (with the shared cooldown
  constants); reuse it rather than rolling your own guard.
- **Themes from the Suite.** Use `lynx_investor_core.gui_themes` (`ThemeCycler`,
  `apply_theme`, `list_user_themes`); the base palette is Catppuccin Mocha.
- **Language toggle** uses `lynx_investor_core.lang_widget.mount_tk_language_button`;
  visible strings go through `_t("key", default="English")`.
- **Call into `core`/`display`, never the reverse.** Domain code must not import
  the GUI.
