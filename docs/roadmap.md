# KDBXStudio competitive roadmap

Goal: become the best **local KDBX studio on Linux**, then close gaps that keep Bitwarden / KeePassXC / 1Password ahead in daily use.

## Positioning

- **Win now:** multi-DB tabs, Password Health, Command Palette, SSH/PEM, templates, emergency sheet, read-only, save backups, plugins.
- **Must close:** browser fill, hardware keys, sync/conflict UX, large-vault performance, Wayland Auto-Type, distribution trust.
- **Later:** passkeys, mobile companion, Win/macOS (or explicit Linux-only niche).

## Phases

### Phase 0 — Daily-driver parity (current sprint)

| ID | Item | Why | Deliverable |
|----|------|-----|-------------|
| P0-AT | Auto-Type 2.0 | KeePassXC’s #1 Linux habit | `{DELAY=N}`, active-window match, app-wide hotkey, non-blocking initial delay |
| P0-SYNC | External vault change UX | Syncthing/Nextcloud without Bitwarden cloud | `QFileSystemWatcher` + reload / keep / merge prompt |
| P0-BR | Browser bridge | Form fill is table-stakes | KeePassXC-Browser NaCl protocol + native host + stock extension |

### Phase 1 — Trust & scale

| ID | Item | Why | Deliverable |
|----|------|-----|-------------|
| P1-PERF | Entry list model | Large vaults must stay smooth | `QAbstractTableModel` + cheaper row updates |
| P1-PLUG | Plugin integrity | Unsigned `exec` hurts security story | SHA-256 allowlist gate + docs |
| P1-DIST | Distro trust | Install friction loses users | Signing / Flathub notes in `docs/packaging-signing.md` |
| P1-HW | YubiKey / challenge-response | Security-conscious KeePassXC users | Tracked; blocked on pykeepass/libkeepass capability (spike first) |

### Phase 2 — Product language & future

| ID | Item | Why | Deliverable |
|----|------|-----|-------------|
| P2-HEALTH | Health fix wizard | 1Password Watchtower feel | Guided “fix next finding” flow |
| P2-PASSKEY | Passkeys | Industry direction | Spec + storage convention (later) |
| P2-MOBILE | Companion / mobile path | “Everywhere” expectation | Compatibility guide first; app later |
| P2-I18N | Full retranslate | EN/TR depth | Remaining hard-coded strings |
| P2-AUDIT | External security review | Credibility | Process doc when ready |

## Non-goals this sprint

- Shipping a browser extension store listing (use stock KeePassXC-Browser)
- Win/macOS ports
- Hardware key support without library spike

## Success metrics

- Enter Auto-Type from hotkey targets the foreground window’s best matching entry
- Editing a vault on disk while open never silently overwrites Syncthing changes
- `pytest` stays green; new modules covered by unit tests
- Browser host can associate with KeePassXC-Browser and return get-logins for matching URLs
