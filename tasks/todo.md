# Code quality + feature verification (2026-07-18)

## Plan

- [x] Audit recent UX features (strength meter, presets, backups, DnD, sorting, quick-copy)
- [x] Fix logic / quality issues found
- [x] Update README to match real behavior
- [x] Run full test suite + E2E; add regressions if needed
- [x] Commit and push

## Review

### Fixes

1. **Password strength** — unreachable `length >= 16` branch ordered correctly.
2. **Favicon** — worker thread emits `Signal` to refresh UI on the GUI thread (no bare `QTimer.singleShot` from worker).
3. **Entry → group DnD** — wired for real (`ENTRY_MIME`); group tree is DropOnly (no fake group rearrange).
4. **History diff** — `HistoryView` now carries tags/custom/expiry; diffs always include those fields.
5. **Backups** — shared `_save_with_backup` / `_save_all_with_backup` for save, lock, quit, tab close, credentials; per-stem cleanup (max 10).
6. **Clipboard timeout 0** — load/save preserve “never clear”; AutoLock ignores idle timeout 0.
7. **Preset rename** — “Passphrase-like” → “Long alphanumeric”.
8. **README** — aligned with DnD, presets, backup scope, clipboard `0`.

### Verify

- ruff / mypy clean
- Full pytest passed (incl. E2E + new `test_logic_quality_fixes.py`)
