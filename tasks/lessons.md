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

## Perf / correctness (2026-07-18)

- Audit must never call `attachment_count(uuid)` per entry — put `attachment_count` on `EntryView` during list.
- Never return the live `_index_cache` list from `all_entries`; always `list(cached)`.
- Attachment list default is metadata-only; use `get_attachment_data` / `include_data=True` for payloads.
- Merge attachments: add-then-delete (with rollback), never delete-first.
- HIBP and manual favicon must not block the UI thread; snapshot entries on main, network in a worker + Signal.
- Password Show state and group-tree selection must reset/restore on entry/group refresh.
- Expiring-soon window is one shared constant (`expiry.EXPIRING_SOON_DAYS`) for audit + search filters.

