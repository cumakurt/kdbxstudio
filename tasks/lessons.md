# Lessons

## Code quality (2026-07-17)

- Never check `Path.is_symlink()` after `resolve()` — resolve follows links; reject symlinks first.
- Recycle Bin emptying must walk subgroups; KeePass trashes groups as nested folders under the bin.
- Lock/close paths must treat dirty sessions like quit: save or confirm before discarding memory state.
- Merge and history restore must copy the full entry surface (expiry, OTP including empty, attachments, tags, custom props), not only the obvious string fields.
- Attachment UX: same guards for DnD and file dialog; always use `Path(name).name` for stored/default filenames.

## E2E verification (2026-07-17)

- Keep `DatabaseManager` method signatures in sync with `KdbxDatabase` (e.g. `add_entry` tags/expiry/custom).
- Declare every runtime import in `pyproject.toml` (`pyotp` for TOTP).
- Prefer `search(query, entry_filter=…)` or allow `search(EntryFilter)` — do not assume callers only pass strings.
- Seed audit scenarios *before* recycling entries that contribute to reused-username / empty-password counts.
- Attachment mutations must invalidate search/index caches, not only fire listeners.
