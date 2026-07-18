# GitHub version / update check — 2026-07-18

## Plan

- [x] Fallback chain: Release → releases list → tags → repo `__init__.py` / `pyproject.toml`
- [x] Semver compare with pad (`1.0` == `1.0.0`)
- [x] Tools → Check for Updates dialog shows installed vs GitHub + source
- [x] Startup notifies only when update available
- [x] Tests (unit + live)

## Review

Repo currently has **no GitHub Releases**; check correctly falls back to
`main` source version (`1.0.0`). After you publish `v*` releases, those take priority.

Verification: `QT_QPA_PLATFORM=offscreen pytest -q` → **130 passed**
