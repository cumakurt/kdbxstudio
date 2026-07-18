# KDBXStudio Enterprise Audit

## Status
- [x] Architecture / SoC / SOLID scan
- [x] Security / KDBX / browser / clipboard / plugins
- [x] Memory / Qt threading / performance
- [x] Code quality / UI / tests
- [x] Report + canvas deliverable
- [x] P0 hardening: browser authz, clipboard, export 0600, tests

## Review
Audit completed 2026-07-18 against `src/kdbxstudio/` (~20k LOC) and `tests/` (~3.1k LOC).

### P0 applied (2026-07-18)
- `browser/protocol.py`: require association for totp/groups/create/lock/generate-password; `_keys_ok` fail-closed
- `security/session.py`: `ClipboardGuard.cancel()` clears clipboard
- `ui/widgets/entry_detail.py`: optional `ClipboardGuard` for custom field copy
- `application/export.py` + `emergency_sheet.write_emergency_html`: chmod 0600
- Tests: association matrix, keys_ok, export perms, cancel clears
