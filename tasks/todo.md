# Code quality analysis (2026-07-17)

## Plan

### Round 1

- [x] Fix attachment DnD symlink guard (`resolve_regular_file`)
- [x] Fix plugin `deactivate` leaving hooks when plugin raises
- [x] Fix CSV import expiry parsing (timezone strip)
- [x] Fix merge `update_existing` omitting expires / expiry_time
- [x] Fix `Cache.__contains__` treating stored `None` as missing
- [x] Tighten `DatabaseManager.update_entry` expiry typing

### Round 2

- [x] Fix `empty_recycle_bin` to purge nested trashed groups/entries
- [x] Fix lock: auto-save dirty sessions; reopen all DB paths
- [x] Fix tab close: Save/Discard/Cancel for dirty sessions
- [x] Fix `restore_history` to restore tags, custom props, expiry, attachments
- [x] Fix merge: copy attachments; apply empty OTP on update
- [x] Harden attachment add (dialog) + Save As basename
- [x] Add regression tests; run ruff / mypy / pytest
- [x] Commit and push

## Review

### Round 1

1. **Security** — DnD used `resolve()` then `is_symlink()`; resolve follows links so the guard never fired. Fixed via `resolve_regular_file()`.
2. **Plugin lifecycle** — Failed `deactivate()` left hooks registered. Hooks cleared before re-raise.
3. **CSV import** — `text[:19]` stripped timezone; full ISO parse used.
4. **Merge expiry** — Updates/adds now copy expiry via `parse_expiry`.
5. **Cache** — `__contains__` no longer treats stored `None` as a miss.
6. **Typing** — `expiry_time: datetime | None`.

### Round 2

1. **High** — `empty_recycle_bin` only deleted top-level bin entries; trashed groups (and their secrets) remained. Now walks nested entries and deletes subgroups.
2. **High** — Auto-lock/`Lock All` discarded dirty sessions and only unlocked `paths[0]`. Now saves dirty DBs first (aborts lock on save failure) and unlocks every path.
3. **Medium** — Tab close closed dirty sessions silently; now Save/Discard/Cancel like File → Close.
4. **Medium** — `restore_history` only restored title/user/pass/url/notes/otp; now also tags, custom properties, expiry, and attachments.
5. **Medium** — Merge dropped attachments; empty source OTP did not clear destination OTP. Both fixed.
6. **Medium** — File-dialog attach skipped symlink/size guards; Save As used raw attachment names (path traversal). Shared `_attach_file` + basename sanitization.

### Deferred

- Split `MainWindow` into controllers
- Fully async HIBP / favicon / update-check workers

### Verify

- 81 tests passed
- ruff / mypy clean
