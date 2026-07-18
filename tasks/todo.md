# Turkish language support — 2026-07-18

## Plan

- [x] Add language setting (default `en`) to app settings
- [x] i18n helper + EN/TR catalogs for UI strings
- [x] Settings dialog: language selector
- [x] Apply language at startup; retranslate shell on change
- [x] Smoke-test EN/TR switch

## Review

- Default language is **English** (`language: "en"` in settings).
- **Tools → Settings… → Language** chooses English or Türkçe.
- Startup (`__main__` / MainWindow) calls `set_language`; menus/toolbar/tray retranslate live on change.
- Catalog: `src/kdbxstudio/i18n/catalog_tr.py` (~350 keys); `tr()` falls back to English for missing keys.
- Tests: `tests/test_i18n.py`
