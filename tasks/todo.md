# End-to-end feature verification (2026-07-17)

## Plan

- [x] Build sample-DB E2E suite covering every application-layer feature
- [x] Run suite + existing tests; record failures
- [x] Fix bugs found during E2E
- [x] Re-run full verification; document per-feature results in Review

## Review

### Bugs fixed this pass

1. **`DatabaseManager.add_entry` API gap** — Did not forward `tags`, `custom_properties`, `expires`, `expiry_time` that `KdbxDatabase.add_entry` already supports. Templates/UI worked only via a second `update_entry`. Fixed forwarding.
2. **Missing `pyotp` dependency** — TOTP imports `pyotp` but it was not declared in `pyproject.toml`. Added `pyotp>=2.9`.
3. **`SearchEngine.search(EntryFilter)` footgun** — First arg was typed as `str` only; passing a filter raised `AttributeError` on `.strip()`. Now accepts `str | EntryFilter`.
4. **Attachment cache invalidation** — `add_attachment` / `delete_attachment` now invalidate the entry index cache (not only notify).

### Per-feature verification (sample DB E2E)

| Area | Result | How verified |
|------|--------|--------------|
| Create DB (password + keyfile) | PASS | `test_e2e_sample_database_feature_matrix` |
| Open / invalid credentials | PASS | same |
| Save / dirty / save_all / close_all | PASS | same |
| Multi-session tabs | PASS | same |
| Database info (version/KDF/counts) | PASS | same |
| Change password + clear keyfile | PASS | same |
| Save-as path | PASS | same |
| Groups add / nested / permanent delete | PASS | same |
| Entries CRUD + tags/expiry/custom/OTP | PASS | same |
| Move entry between groups | PASS | same |
| Trash / empty recycle / permanent delete | PASS | same |
| Attachments add/list/save-as | PASS | same |
| History list / diff / restore | PASS | same |
| Search full-text | PASS | same |
| Filters: tag, group, URL, OTP/custom, weak, dupes, expired, min length, recycle | PASS | same |
| TOTP live code + `looks_like_otp` | PASS | same |
| Audit: expired, expiring, weak, duplicate, reused username, empty | PASS | same |
| HIBP (mocked) | PASS | same |
| CSV export/import (otp, tags, custom) | PASS | same |
| Merge + attachments | PASS | same |
| Emergency sheet (mask passwords) | PASS | same |
| Templates list + apply custom defaults | PASS | same |
| Password generator + entropy | PASS | same |
| Auto-Type expand + backend detect | PASS | expand; backend may be None |
| PEM inspect | PASS | same |
| SSH agent availability probe | PASS | callable (env-dependent) |
| Favicon host normalize | PASS | same |
| Plugin discover (builtin) + activate/deactivate | PASS | same |
| Marketplace catalog | PASS | same |
| Settings + recent databases | PASS | same |
| Clipboard auto-clear | PASS | `test_e2e_clipboard_and_autolock_qt` |
| Idle auto-lock signal | PASS | same |
| MainWindow + sample DB open | PASS | `test_e2e_gui_main_window_with_sample` |

### GUI-only / env-dependent (not fully automated)

| Feature | Status | Notes |
|---------|--------|-------|
| Auto-Type into focused window | SKIP | Needs display + xdotool/ydotool/wtype |
| Live HIBP network | MOCKED | k-anonymity path covered with patch |
| Live favicon download | PARTIAL | host normalize only; network fetch unmocked |
| ssh-add to agent | PARTIAL | `agent_available()` probed |
| Tray / minimize-on-lock UX | PARTIAL | settings persist; visual via `smoke_visual.py` |
| DnD attachments / PDF preview | PARTIAL | path helpers + prior quality tests |
| Command palette / theme / docks | PRIOR | existing GUI smoke + hybrid UI tests |
| Update check (GitHub) | SKIP | network |

### Verify

- **84 tests passed** (incl. 3 new E2E)
- ruff / mypy clean
- Suite: `tests/test_e2e_feature_matrix.py`
