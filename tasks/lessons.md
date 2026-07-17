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

## Logic polish (2026-07-18)

- Never advertise DnD without wiring drop → `move_entry`; prefer DropOnly on group tree.
- Do not call Qt widget APIs from worker threads — use a Signal owned by the main-window QObject.
- History UI diffs `HistoryView` pairs: put tags/custom/expiry on `HistoryView`, not only `EntryView`.
- Centralize save+backup so auto-lock / quit / tab close cannot skip backups.
- Clipboard `0` means disabled; AutoLock idle `0` must not arm a zero-delay timer.
- Score helpers: put longer length thresholds before shorter `elif` branches.
