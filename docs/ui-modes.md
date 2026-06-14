# UI modes

lynx-fund renders the same `FundReport` through four front-ends. All are
dispatched by `lynx_fund/cli.py`; all consume `core.analyzer` + `models` and
differ only in presentation.

| Mode | Flag | Code | Notes |
|------|------|------|-------|
| Console | (default) | `display.render_full_report` | One-shot Rich report |
| Interactive | `-i` | `interactive.run_interactive` | REPL: analyze, refresh, search, cache, explain, about |
| TUI | `-tui` | `tui/app.py` (`run_tui`) | Textual full-screen; theme cycling, About modal |
| GUI | `-x` | `gui/app.py` (`run_gui`) | Tkinter window; threaded analysis, Export, Language |

## Shared rules

- **Source content from `models`/`display`,** not by re-deriving values per
  mode, so the four stay at feature parity.
- **Themes** come from `lynx_investor_core` (plus the house themes in
  `tui/themes.py`); the default is the Bloomberg-dark `lynx-theme`.
- **All visible strings** pass through `_t("key", default="English")` so
  `--language` can translate any mode.

## Examples

```bash
lynx-fund -p VFIAX            # console
lynx-fund -p VFIAX -i         # interactive REPL
lynx-fund -p VFIAX -tui       # Textual TUI
lynx-fund -p VFIAX -x         # Tkinter GUI
```
