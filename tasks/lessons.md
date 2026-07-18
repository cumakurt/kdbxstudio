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

## Unlock dialog Enter (2026-07-18)

- In Qt dialogs, `QPushButton` defaults to `autoDefault=True`; Enter activates Browse instead of Unlock. Set `setAutoDefault(False)` on Browse/… buttons and keep only Ok as default; also wire password `returnPressed` → accept.

## Roadmap foundations (2026-07-18)

- Auto-Type window match must sample the *previous* non-app window; ApplicationShortcuts focus us first.
- Self-saves must `ignore_briefly` on `QFileSystemWatcher` or Syncthing prompts fire on every Save.
- `QTableView` has no `setUniformRowHeights` — use header default section size instead.
- Browser fill needs a running unlocked vault + socket bridge; native host alone is not enough.

## Recycle Bin visibility (2026-07-18)

- Selecting Recycle Bin must list entries **recursively** — KeePass stores trashed groups as nested folders; `group.entries` alone hides nested secrets.
- After Move to Recycle Bin, select the bin in the UI so the user immediately sees trashed items.
- When the bin group is selected, do not re-run search filters that exclude `in_recycle_bin`.

- Audit must never call `attachment_count(uuid)` per entry — put `attachment_count` on `EntryView` during list.
- Never return the live `_index_cache` list from `all_entries`; always `list(cached)`.
- Attachment list default is metadata-only; use `get_attachment_data` / `include_data=True` for payloads.
- Merge attachments: add-then-delete (with rollback), never delete-first.
- HIBP and manual favicon must not block the UI thread; snapshot entries on main, network in a worker + Signal.
- Password Show state and group-tree selection must reset/restore on entry/group refresh.
- Expiring-soon window is one shared constant (`expiry.EXPIRING_SOON_DAYS`) for audit + search filters.

## Browser protocol authz (2026-07-18)

- Encrypted browser actions that read secrets or mutate the vault (`get-totp`, `get-database-groups`, `create-new-group`, `lock-database`, `generate-password`) must call `_require_associated` (or equivalent).
- `_keys_ok` must fail closed: empty `keys` without top-level `id`/`key` → `False`, never `True`.
- All clipboard copies of secrets (including custom fields) must go through `ClipboardGuard`; `cancel()` must clear, not only stop the timer.
- Exports that contain secrets (CSV, emergency HTML) must `chmod` to `0600` after write.

