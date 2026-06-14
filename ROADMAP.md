# Roadmap — lynx-fund

Known gaps and follow-ups, grounded in the current code (v6.0.0). This is a
list of things observed in the tree, not a feature-marketing plan. Nothing here
has been started unless noted.

## Documentation / naming inconsistencies

- **Scope wording disagrees with the code.** `README.md` and the `about` text in
  `lynx_fund/__init__.py` describe the tool as "Exchange-Traded Fund analysis"
  and say mutual funds are rejected. The resolver (`core/ticker.py`) does the
  opposite: it **accepts** mutual/index funds (MUTUALFUND/OEIC/SICAV/UCITS) and
  **rejects ETFs**. `pyproject.toml`'s description ("Mutual fund / index fund
  analysis") and the metric vocabulary agree with the resolver. The README and
  `about` text should be reconciled to the resolver's behaviour.
- **`search_etfs` alias.** `core/ticker.py` keeps `search_etfs = search_funds`
  for back-compat; callers should migrate to `search_funds` and the alias can be
  retired later.

## Unfinished / placeholder areas

- **`financials/` directory is unused.** `core/storage.py` exposes
  `get_financials_dir()` but nothing currently writes to it.
- **PDF export is optional and untested here.** `pyproject.toml` declares a
  `pdf` extra (`weasyprint`); confirm the export path before relying on it.

## Testing

- Tests run in `testing` storage mode and must not hit the network. When adding
  fetch/news features, extend fixtures in `tests/conftest.py` rather than
  calling yfinance live.

## Project health (Lynx Factory)

- The Factory project-checker only counts **top-level** directories as modules,
  so the internal `core/` `metrics/` `tui/` `gui/` split is invisible to it and
  modularization scores as a single module. Raising that score would require
  promoting subpackages to top-level packages, which would break the console
  script and the suite plugin entry point — intentionally **not** done. The
  scoped `CLAUDE.md` files and these blueprints address the feature-context and
  blueprint dimensions instead.
