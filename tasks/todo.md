# Deep code/perf audit — fix and verify (2026-07-18)

## Plan

- [x] Core: EntryView `attachment_count`, UUID indexes, lazy attachment data, SecureString/close wipe, shared expiry constant
- [x] App: audit O(n²)+session_id, cache list copy, merge attachments, HIBP in-memory cache, ssh_agent tempfile
- [x] UI: password Show leak, group select restore, refresh/search preserve, HIBP worker, favicon thread, filter clear, strength stylesheet
- [x] Tests: targeted tests + full offscreen pytest + e2e matrix + UI smoke
- [x] Review section when done

## Review

### Fixes landed
- **Audit O(n²):** `EntryView.attachment_count` filled in `list_entries`; audit no longer calls `attachment_count` per UUID.
- **UUID indexes** on `KdbxDatabase` for entry/group lookup; recycle UUID + group path cache during listing.
- **Lazy attachments:** `list_attachments(include_data=False)` by default; `get_attachment_data` for preview/save-as.
- **Cache safety:** `all_entries` always returns a list copy.
- **Audit session:** `list_groups(session_id)` for multi-DB health stats.
- **Merge:** add-then-delete attachment sync with rollback on failure.
- **HIBP:** process-local LRU memory cache + batched disk flush; Password Health runs HIBP off the UI thread.
- **SSH agent:** `mkstemp` + `0o600` + shred before unlink.
- **Credentials:** save syncs from `SecureString`; `close()` clears PyKeePass password/keyfile.
- **Expiry:** shared `EXPIRING_SOON_DAYS` (14) for audit + search filters.
- **UI:** password Show resets on entry change; group tree `select_uuid`; refresh preserves search/filters; search clear (×) re-runs; filter clear single emit; strength stylesheet only on band change; manual favicon threaded.

### Verification
- `QT_QPA_PLATFORM=offscreen pytest -q` → **104 passed**
- `scripts/smoke_visual.py` → OK (empty dashboard, workspace, search, palette, certs, generator)
- New coverage: `tests/test_perf_correctness_fixes.py`
