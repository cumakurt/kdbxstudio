# KDBXStudio

**Modern, open-source Qt6 KDBX password manager for Linux.**

KDBXStudio is a KeePass-compatible desktop vault focused on a calm, keyboard-first
workspace: multi-database tabs, password health auditing, plugins, and rich entry
tools (TOTP, attachments, SSH/certificates) — without cloud lock-in. Works with the
stock **KeePassXC-Browser** extension for form fill.

| | |
|---|---|
| **Version** | 1.0.0 |
| **License** | [GPL-3.0-or-later](LICENSE) |
| **Platform** | Linux (Qt6 / PySide6) |
| **Python** | 3.11+ |
| **Install** | `./install.sh` → AppImage |
| **Repository** | [github.com/cumakurt/kdbxstudio](https://github.com/cumakurt/kdbxstudio) |

---

## Table of contents

- [Author](#author)
- [Screenshots](#screenshots)
- [Features](#features)
- [Why KDBXStudio?](#why-kdbxstudio)
- [Requirements](#requirements)
- [Installation](#installation)
- [Browser integration](#browser-integration)
- [Usage](#usage)
- [Keyboard shortcuts](#keyboard-shortcuts)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Development](#development)
- [Packaging](#packaging)
- [Documentation](#documentation)
- [Security notes](#security-notes)
- [License](#license)

---

## Author

**Cuma KURT** — [cumakurt@gmail.com](mailto:cumakurt@gmail.com)

[LinkedIn](https://www.linkedin.com/in/cuma-kurt-34414917/) ·
[GitHub](https://github.com/cumakurt/kdbxstudio)

Copyright (C) 2026 Cuma KURT.

---

## Screenshots

Generate local UI captures with the visual smoke script:

```bash
QT_QPA_PLATFORM=offscreen python scripts/smoke_visual.py
```

Outputs (gitignored) land under `artifacts/visual/`: welcome screen, workspace,
search, command palette, certificates tab, password generator, and a sample
`.kdbx` for manual testing.

---

## Features

### Vault & databases

- Open and create **KDBX 4.x** databases (master password and optional key file)
- **Multi-database** tabs — work on several vaults in one window
- Save, close, and lock all open databases
- Database properties (version, **KDF**, encryption) and **change master credentials**
- **Recent databases** on the welcome screen
- **Recycle Bin** with empty-bin support
- **CSV import / export** (export warns that secrets leave the vault in clear text)
- **Merge** another `.kdbx` into the active vault
- **Emergency sheet** (printable HTML) for offline backup of selected/all entries
- **External file watch** — prompt to reload when Syncthing / Nextcloud changes the vault on disk

### Workspace

- Dockable **Groups** tree
- **Password Health** window (Tools → Password Health…) with severity findings, Fix next, and open-entry actions
- Fast entry list (`QTableView` model) + detail split view (resizable), optional **favicon** icons
- Entry tabs: **Entry**, **TOTP**, **History** (with field diff), **Attachments**, **Certificates / SSH**
- **Expiry countdown** — visual indicator showing days until entry expires
- Welcome dashboard when no vault is open (Open / Create / Command Palette)
- System **tray** (show / lock / quit) — closing the window quits the app; tray icon can still show/hide or lock
- Compact / comfortable density
- **Theme styles**: Studio Dark/Light, System, plus Nord, Dracula, Tokyo Night, Catppuccin (Mocha/Latte), Solarized Dark, One Dark, Gruvbox Dark
- **UI language**: English (default) or Turkish — Tools → Settings… → Language

### Entries & secrets

- Title, username, password, URL, notes, custom fields, **tags**, **expiry**
- **New Entry** dialog collects all common fields (including TOTP) and saves in one step
- **Password strength meter** — real-time visual feedback (Very Weak → Strong)
- **Auto-Type 2.0** on Linux (`xdotool` / `ydotool` / `wtype`): `{DELAY=N}`, active-window match, configurable sequence and initial delay
- **Move entry** between groups (dialog or drag entry onto a group in the tree)
- **Multi-select delete** — select one or many entries (`Ctrl`/`Shift`+click, `Ctrl+A`); `Delete` → Recycle Bin, `Shift+Delete` → permanent
- **Contextual icons**: URL / title / PEM / template type → login, email, API, SSH, bank, Wi‑Fi, …
- Field-leading icons; action icons for Show / Copy / Generate / Save
- **Markdown / JSON** notes preview (valid HTML with `<ul>` lists)
- **Secret templates**: Login, API Key, SSH, Certificate, Secure Note, Bank Card
- **Password generator** with entropy estimate, secure clipboard copy, and presets
  (Strong, PIN, Memorable, Complex, Long alphanumeric, Short)
- **TOTP** live codes and countdown (6 and 8 digit support, timer only when active)
- Entry **history** list, restore, and field diff (including tags, custom fields, expiry)
- Attachments (add / delete / **save as** / **drag-and-drop**) with text / PDF preview
- PEM / OpenSSH **certificate and SSH inspector**; optional **ssh-add** to agent

### Search & audit

- Inverted-index **full-text search** (includes tags)
- Filter chips: URL, custom/OTP, weak / empty / duplicates, **expired**, **expiring soon**, Recycle Bin, tag/group text
- **Password Health** audit: empty, weak, low entropy, duplicates, missing / reused usernames,
  **expired / expiring soon**, optional **HIBP** (k-anonymity, off UI thread)
- **Health score** percentage with theme-aware progress bar
- **Expiry warnings** — visual alerts for expired and expiring entries
- **Database statistics** — total entries, groups, URLs, TOTP, tags, attachments, custom fields
- Double-click a finding to jump to the entry
- Plugin hook `search.rank` for ranking tweaks
- Command Palette jumps to entries and common actions

### Browser & updates

- **KeePassXC-Browser** compatible bridge (NaCl associate, get-logins, set-login, TOTP, groups, lock)
- Native messaging host install via `./install.sh` or Settings → Install browser host manifests…
- Optional **update check** against GitHub (Releases → tags → repository version on `main`)
- Tools → **Check for Updates…** shows installed vs GitHub version and source

### Security session

- Clipboard copy with **auto-clear timeout** (all copy paths use ClipboardGuard)
- **True idle auto-lock** (input activity) + optional minimize / tray
- Clear clipboard on lock
- **Read-only session** mode
- Best-effort `SecureString` wipe for in-memory master password on close / lock
- **Atomic settings write** with `chmod 0600` permissions
- Input validation on timeout and theme settings
- Optional **plugin SHA-256 allowlist** for integrity gating

### Extensibility & desktop polish

- Plugin SDK + discoverable `*_plugin.py` modules (hooks cleared on deactivate)
- **Isolated plugin callbacks** — one plugin error does not block others
- Built-in **Plugin Marketplace** (local / built-in catalog)
- Command Palette (`Ctrl+K` / `Ctrl+Shift+P`)
- Persistable **window layout** (View → Save Layout / Reset Layout)
- App icon, `.desktop` entry, AppStream metainfo
- One-shot **`install.sh`**: distro detection, deps, portable **AppImage**, browser host manifests
- Flatpak packaging scaffold

---

## Why KDBXStudio?

| Feature | KDBXStudio | KeePassXC | Bitwarden |
|---------|-----------|-----------|-----------|
| KeePass KDBX 4.x | ✓ | ✓ | ✓ |
| Multi-database tabs | ✓ | ✗ | ✗ |
| Password health audit | ✓ (built-in) | ✓ | ✓ |
| HIBP k-anonymity | ✓ | ✓ | ✓ |
| TOTP live display | ✓ | ✓ | ✓ |
| Quick copy shortcuts | ✓ (Ctrl+U/B/T) | ✓ | ✓ |
| Password strength meter | ✓ (real-time) | ✓ | ✓ |
| Password generator presets | ✓ | ✗ | ✓ |
| Plugin system | ✓ | ✗ | ✓ (extensions) |
| Command Palette | ✓ | ✗ | ✗ |
| Emergency sheet | ✓ | ✗ | ✗ |
| PEM / SSH inspector | ✓ | ✗ | ✗ |
| Secret templates | ✓ | ✗ | ✗ |
| Auto-Type (Linux) | ✓ | ✓ | ✗ |
| KeePassXC-Browser | ✓ | ✓ | ✗ |
| Theme styles (10+) | ✓ | limited | limited |
| System tray lock | ✓ | ✓ | ✓ |
| Read-only mode | ✓ | ✗ | ✗ |
| Database backup on save | ✓ | ✗ | ✗ |
| Entry sorting | ✓ | ✓ | ✓ |
| Drag entry onto group | ✓ | ✗ | ✗ |
| Flatpak + AppImage | ✓ | ✓ | ✓ |
| Open source | GPL-3.0 | GPL-2.0 | GPL-3.0 |

Competitive roadmap: [docs/roadmap.md](docs/roadmap.md).
KeePassXC-Browser setup: [docs/browser-integration.md](docs/browser-integration.md).

---

## Requirements

- **OS:** Linux desktop (`x86_64` or `aarch64`)
- **Python:** 3.11 or newer (for building / development)
- **Libraries:** `pykeepass`, `PySide6` (Qt6), `PyNaCl` (browser crypto) — pulled by `install.sh` / pip
- **Network:** first AppImage build downloads `appimagetool` into `.cache/`; optional update check / HIBP / favicons
- **Optional fonts:** Inter (system UI font if installed)
- **Optional Auto-Type backends:** `xdotool`, `ydotool`, or `wtype`

---

## Installation

### Quick install (AppImage — recommended)

```bash
git clone https://github.com/cumakurt/kdbxstudio.git
cd kdbxstudio
chmod +x install.sh
./install.sh
```

The installer detects your Linux distribution, installs any missing system
packages quietly, builds a portable **AppImage** under `dist/`, and (unless
`--no-desktop`) registers a desktop launcher plus `~/.local/bin/kdbxstudio`.
When using `--venv` / `--dev`, it also installs KeePassXC-Browser native messaging
manifests (best-effort).

| Option | Effect |
|--------|--------|
| `--appimage` | Build AppImage (default) |
| `--venv` | Editable source install into `.venv` instead |
| `--dev` | Dev extras (implies `--venv`) |
| `--no-desktop` | Skip desktop entry, icons, and user launcher |
| `--force` | Recreate AppDir / virtualenv from scratch |
| `-y` / `--yes` | Non-interactive package manager installs |

Detailed output is written under `.install-logs/` (gitignored).
`appimagetool` is cached under `.cache/`.

### Run (AppImage)

```bash
./dist/KDBXStudio-x86_64.AppImage
# or after desktop integration:
kdbxstudio
```

### From source (development)

```bash
./install.sh --dev
# or manually:
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m kdbxstudio.browser.install_host   # KeePassXC-Browser manifests
python -m kdbxstudio
```

---

## Browser integration

KDBXStudio speaks the KeePassXC-Browser protocol so the **official extension** can
fill logins from an unlocked vault.

1. Install native messaging manifests (`install.sh --venv` / Settings button / `python -m kdbxstudio.browser.install_host`).
2. Install [KeePassXC-Browser](https://keepassxc.org/docs/KeePassXC_GettingStarted.html#_setup_browser_integration).
3. Unlock a database in KDBXStudio (Settings → Enable KeePassXC-Browser integration).
4. In the extension, Connect / Associate, then **Save** the vault.

Full guide: [docs/browser-integration.md](docs/browser-integration.md).
If KeePassXC is also installed, disable its browser integration to avoid conflicting
`org.keepassxc.keepassxc_browser` manifests.

---

## Usage

### First run

1. Launch KDBXStudio → welcome card appears.
2. **Create Database…** or **Open Database…** (or pick a recent path).
3. Unlock with master password and optional key file.
4. Add an entry (Entry → Add, or **New from Template…**).
5. Copy password with the Copy action; clipboard clears after the configured timeout.

### Daily workflow

1. Open a recent vault or use File → Open.
2. Browse **Groups**, search with the search box (`Ctrl+F`), or Command Palette (`Ctrl+K`).
3. Edit the entry; Save entry then File → Save to persist the KDBX file.
4. Open **Tools → Password Health…** for weak / duplicate / empty secrets.
5. Pick a theme under **View → Theme** (or Settings).
6. Lock with Tools → Lock All Databases (`Ctrl+L`) when stepping away.
7. Optionally use **Tools → Check for Updates…** to compare with GitHub.

### Sample vault (automated)

The smoke script builds a demo database and exercises the UI offscreen:

```bash
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen python scripts/smoke_visual.py
```

Demo file written to `artifacts/visual/sample.kdbx` (password: `demo-pass-123`).

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` / `Ctrl+Shift+P` | Command Palette |
| `Ctrl+F` | Focus universal search |
| `Ctrl+O` | Open database |
| `Ctrl+N` | New database |
| `Ctrl+S` | Save (with automatic backup) |
| `Ctrl+L` | Lock all databases |
| `Ctrl+U` | Quick copy username |
| `Ctrl+B` | Quick copy password |
| `Ctrl+Shift+U` | Quick copy URL |
| `Ctrl+T` | Quick copy TOTP code |
| `Ctrl+Shift+V` / `Ctrl+Alt+A` | Auto-Type selected entry |
| `Delete` | Move selected entr(y/ies) to Recycle Bin |
| `Shift+Delete` | Permanently delete selected entr(y/ies) |
| `Ctrl+A` | Select all entries in the list |
| `F2` | Rename selected group |
| `Ctrl+Q` | Quit (standard) |

---

## Configuration

Preferences are stored under XDG config:

```text
~/.config/kdbxstudio/settings.json
```

Notable settings:

| Key | Meaning | Default |
|-----|---------|---------|
| `theme` | Theme id: `system`, `dark`, `light`, `nord`, `dracula`, `tokyo-night`, `catppuccin-mocha`, `catppuccin-latte`, `solarized-dark`, `one-dark`, `gruvbox-dark` | `dark` |
| `language` | UI language: `en` (default) \| `tr` | `en` |
| `ui_density` | `compact` \| `comfortable` | `compact` |
| `clipboard_timeout_ms` | Clipboard auto-clear delay (`0` = never clear; otherwise min 1000) | `15000` |
| `auto_lock_timeout_ms` | Idle lock delay (min: 0 = disabled) | `300000` |
| `auto_lock_enabled` | Enable / disable idle lock | `true` |
| `clear_clipboard_on_lock` | Wipe clipboard when locking | `true` |
| `minimize_on_lock` | Minimize (and tray-hide) on lock | `false` |
| `hibp_enabled` | HIBP k-anonymity checks during audit | `false` |
| `autotype_sequence` | Auto-Type token sequence | `{USERNAME}{TAB}{PASSWORD}{ENTER}` |
| `autotype_match_window` | Match Auto-Type to active window | `true` |
| `autotype_initial_delay_ms` | Delay before Auto-Type starts | `500` |
| `watch_database_files` | Watch open vaults for external changes | `true` |
| `browser_integration_enabled` | KeePassXC-Browser local server | `true` |
| `plugin_sha256_allowlist` | Optional list of allowed plugin digests | `[]` |
| `check_updates_on_start` | Compare installed version with GitHub on launch | `true` |
| `start_minimized_to_tray` | Start hidden in the system tray | `false` |
| `read_only` | Open databases in read-only mode | `false` |
| `window_geometry` / `window_state` | Saved layout (base64) | `""` |
| `recent_databases` | Recent vault paths | `[]` |

Use **Tools → Settings…** for the interactive dialog.

---

## Architecture

```text
UI            MainWindow, dialogs, widgets, theme (QSS + tokens), icons
Application   DatabaseManager, SearchEngine, AuditEngine, PluginManager,
              Browser bridge, file watch, Auto-Type, CSV I/O, update check
Core          pykeepass wrapper, crypto helpers, cache, TOTP, PEM, password generator
Browser       KeePassXC-Browser protocol (NaCl), native messaging host
Security      Settings store (atomic write, chmod 0600), clipboard guard, auto-lock
Plugins       SDK (isolated callbacks), marketplace catalog, built-in plugins
```

Source layout:

```text
src/kdbxstudio/
  __main__.py          Application entry
  application/         Session orchestration
  browser/             KeePassXC-Browser host + protocol
  core/                KDBX and crypto primitives
  security/            Preferences and session guards
  plugins/             SDK + builtins + marketplace
  ui/                  Qt shell, theme, dialogs, widgets
assets/                Icons, desktop file, AppStream
packaging/             Flatpak + AppImage helpers
docs/                  Specs, roadmap, browser & packaging notes
tests/                 Unit and pytest-qt smoke tests
scripts/               Visual smoke / sample DB helper
install.sh             AppImage builder / optional venv installer
```

---

## Development

### Quality checks

```bash
source .venv/bin/activate
QT_QPA_PLATFORM=offscreen pytest
ruff check src tests
mypy
```

### Useful paths

| Path | Role |
|------|------|
| [`docs/ui-specification.md`](docs/ui-specification.md) | Design tokens and UX rules |
| [`docs/roadmap.md`](docs/roadmap.md) | Competitive roadmap |
| [`docs/browser-integration.md`](docs/browser-integration.md) | KeePassXC-Browser setup |
| [`docs/packaging-signing.md`](docs/packaging-signing.md) | Signing / Flathub notes |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI: ruff, mypy, pytest |
| [`.github/workflows/release.yml`](.github/workflows/release.yml) | Release artifacts on `v*` tags |

### Plugins

Built-in plugins live under `src/kdbxstudio/plugins/builtin/`. Drop-in modules named
`*_plugin.py` that expose `create_plugin()` can be discovered via the plugin manager.
Browse and activate from **Tools → Plugin Center**.

---

## Packaging

See [`packaging/README.md`](packaging/README.md) and [`docs/packaging-signing.md`](docs/packaging-signing.md).

### Flatpak

```bash
flatpak-builder --user --install --force-clean build-dir \
  packaging/flatpak/com.kdbxstudio.KDBXStudio.yml
flatpak run com.kdbxstudio.KDBXStudio
```

App ID: `com.kdbxstudio.KDBXStudio` (KDE Platform/SDK 6.7).

### AppImage

```bash
./install.sh                 # default path
# → dist/KDBXStudio-x86_64.AppImage   (or …-aarch64.AppImage)
./install.sh --venv          # editable .venv instead of AppImage
./install.sh --dev           # development extras (implies --venv)
```

### Releases

Tag a version (`v1.0.0`, …) to trigger GitHub Actions release artifacts.
The in-app update checker prefers published Releases, then tags, then the
version declared on `main`.

---

## Documentation

- [UI specification](docs/ui-specification.md) — colors, typography, layout, shortcuts
- [Roadmap](docs/roadmap.md) — competitive phases and deliverables
- [Browser integration](docs/browser-integration.md) — KeePassXC-Browser
- [Packaging & signing](docs/packaging-signing.md) — AppImage / Flatpak trust
- [COPYRIGHT](COPYRIGHT) — copyright and contact block
- [Packaging](packaging/README.md) — Flatpak / AppImage notes
- [`install.sh`](install.sh) — recommended AppImage installer

---

## Security notes

- Secrets remain **local**; there is no built-in cloud sync.
- All clipboard operations use **ClipboardGuard** with auto-clear timeout.
- **Atomic settings write** with `chmod 0600` prevents corruption and unauthorized access.
- **Automatic database backup** before every save path (manual save, auto-lock, quit,
  tab close, credential change). Backups live under `.kdbxstudio-backups/` next to the
  vault; up to 10 files are kept **per database stem**.
- Clipboard and auto-lock reduce shoulder-surfing and idle exposure — tune timeouts to your threat model.
  Set `clipboard_timeout_ms` to `0` to disable clipboard auto-clear.
- CSV export writes passwords and OTP material in **plain text**; treat export files as highly sensitive.
- Master password handling uses best-effort memory wipe; Python runtimes cannot guarantee zero residual copies.
- Plugin callbacks are **isolated** — one plugin error does not affect others.
- Optional **plugin SHA-256 allowlist** rejects unsigned drop-ins when configured.
- Favicon downloads are **size-limited** (64 KiB) and fetched asynchronously.
- Browser association keys are stored in KDBX Meta CustomData (`KPXC_BROWSER_*`); save after Connect.
- Input validation on all settings values prevents malformed configuration.
- Prefer a strong master password, optional key file, and regular encrypted backups of your `.kdbx` files.

---

## License

Copyright (C) 2026 Cuma KURT \<cumakurt@gmail.com\>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but **WITHOUT ANY
WARRANTY**; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

Full license text: [`LICENSE`](LICENSE) · notice: [`COPYRIGHT`](COPYRIGHT)

---

## Links

- Homepage / source: [https://github.com/cumakurt/kdbxstudio](https://github.com/cumakurt/kdbxstudio)
- Issues: [https://github.com/cumakurt/kdbxstudio/issues](https://github.com/cumakurt/kdbxstudio/issues)
- Author LinkedIn: [cuma-kurt-34414917](https://www.linkedin.com/in/cuma-kurt-34414917/)
- Email: [cumakurt@gmail.com](mailto:cumakurt@gmail.com)
