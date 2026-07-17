# KDBXStudio

**Modern, open-source Qt6 KDBX password manager for Linux.**

KDBXStudio is a KeePass-compatible desktop vault focused on a calm, keyboard-first
workspace: multi-database tabs, password health auditing, plugins, and rich entry
tools (TOTP, attachments, SSH/certificates) — without cloud lock-in.

| | |
|---|---|
| **Version** | 1.0.0 |
| **License** | [GPL-3.0-or-later](LICENSE) |
| **Platform** | Linux (Qt6 / PySide6) |
| **Python** | 3.11+ |
| **Repository** | [github.com/cumakurt/kdbxstudio](https://github.com/cumakurt/kdbxstudio) |

---

## Table of contents

- [Author](#author)
- [Screenshots](#screenshots)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
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
- Database properties and **change master credentials**
- **Recent databases** on the welcome screen
- **Recycle Bin** with empty-bin support
- **CSV import / export** (export warns that secrets leave the vault in clear text)

### Workspace

- Dockable **Groups** tree and **Password Health** panel
- Entry list + detail split view (resizable)
- Entry tabs: **Entry**, **TOTP**, **History**, **Attachments**, **Certificates / SSH**
- Welcome dashboard when no vault is open (Open / Create / Command Palette)
- Compact light / dark / system themes with brand teal accents

### Entries & secrets

- Title, username, password, URL, notes, custom fields
- **Contextual icons**: URL / title / PEM / template type → login, email, API, SSH, bank, Wi‑Fi, …
- Field-leading icons for title, username, password, URL; action icons for Show / Copy / Generate / Save
- **Markdown / JSON** notes preview
- **Secret templates**: Login, API Key, SSH, Certificate, Secure Note, Bank Card
- **Password generator** with entropy estimate
- **TOTP** live codes and countdown
- Entry **history** list and restore
- Attachments (add / delete) with text / PDF preview where applicable
- PEM / OpenSSH **certificate and SSH inspector**

### Search & audit

- Inverted-index **full-text search**
- Filter chips: URL, custom fields, weak / empty passwords, duplicates, Recycle Bin
- **Password Health** audit: empty, weak, low entropy, duplicates, missing / reused usernames
- Double-click a finding to jump to the entry
- Plugin hook `search.rank` for ranking tweaks

### Security session

- Clipboard copy with **auto-clear timeout**
- **Idle auto-lock** (configurable)
- Clear clipboard on lock
- **Read-only session** mode
- Best-effort `SecureString` wipe for in-memory master password on close / lock

### Extensibility & desktop polish

- Plugin SDK + discoverable `*_plugin.py` modules
- Built-in **Plugin Marketplace** (local / built-in catalog)
- Command Palette (`Ctrl+K` / `Ctrl+Shift+P`)
- Persistable **window layout** (View → Save Layout / Reset Layout)
- App icon, `.desktop` entry, AppStream metainfo
- Flatpak and AppImage packaging scaffolds

---

## Requirements

- **OS:** Linux desktop
- **Python:** 3.11 or newer
- **Libraries:** `pykeepass`, `PySide6` (Qt6)
- **Optional fonts:** Inter (system UI font if installed)

---

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/cumakurt/kdbxstudio.git
cd kdbxstudio
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Run

```bash
python -m kdbxstudio
# or, after install:
kdbxstudio
```

Pass a `.kdbx` path via your desktop environment / MIME association when using the
installed `.desktop` file (`assets/kdbxstudio.desktop`).

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
4. Check **Password Health** for weak / duplicate / empty secrets.
5. Lock with Tools → Lock All Databases (`Ctrl+L`) when stepping away.

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
| `Ctrl+S` | Save |
| `Ctrl+L` | Lock all databases |
| `Delete` | Move selected entry to Recycle Bin |
| `F2` | Rename selected group |
| `Ctrl+Q` | Quit (standard) |

---

## Configuration

Preferences are stored under XDG config:

```text
~/.config/kdbxstudio/settings.json
```

Notable settings:

| Key | Meaning |
|-----|---------|
| `theme` | `dark` \| `light` \| `system` |
| `clipboard_timeout_ms` | Clipboard auto-clear delay |
| `auto_lock_timeout_ms` | Idle lock delay |
| `auto_lock_enabled` | Enable / disable idle lock |
| `clear_clipboard_on_lock` | Wipe clipboard when locking |
| `read_only` | Open databases in read-only mode |
| `window_geometry` / `window_state` | Saved layout (base64) |
| `recent_databases` | Recent vault paths |

Use **Tools → Settings…** for the interactive dialog.

---

## Architecture

```text
UI            MainWindow, dialogs, widgets, theme (QSS + tokens), icons
Application   DatabaseManager, SearchEngine, AuditEngine, PluginManager, CSV I/O, templates
Core          pykeepass wrapper, crypto helpers, cache, TOTP, PEM, password generator
Security      Settings store, clipboard guard, auto-lock, read-only flag
Plugins       SDK, marketplace catalog, built-in plugins
```

Source layout:

```text
src/kdbxstudio/
  __main__.py          Application entry
  application/         Session orchestration
  core/                KDBX and crypto primitives
  security/            Preferences and session guards
  plugins/             SDK + builtins + marketplace
  ui/                  Qt shell, theme, dialogs, widgets
assets/                Icons, desktop file, AppStream, fonts
packaging/             Flatpak + AppImage
docs/                  UI specification
tests/                 Unit and pytest-qt smoke tests
scripts/               Visual smoke / sample DB helper
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
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | CI: ruff, mypy, pytest |
| [`.github/workflows/release.yml`](.github/workflows/release.yml) | Release artifacts on `v*` tags |

### Plugins

Built-in plugins live under `src/kdbxstudio/plugins/builtin/`. Drop-in modules named
`*_plugin.py` that expose `create_plugin()` can be discovered via the plugin manager.
Browse and activate from **Tools → Plugin Center**.

---

## Packaging

See [`packaging/README.md`](packaging/README.md) for full details.

### Flatpak

```bash
flatpak-builder --user --install --force-clean build-dir \
  packaging/flatpak/com.kdbxstudio.KDBXStudio.yml
flatpak run com.kdbxstudio.KDBXStudio
```

App ID: `com.kdbxstudio.KDBXStudio` (KDE Platform/SDK 6.7).

### AppImage

```bash
chmod +x packaging/appimage/build_appdir.sh
./packaging/appimage/build_appdir.sh
appimagetool dist/KDBXStudio.AppDir dist/KDBXStudio-x86_64.AppImage
```

### Releases

Tag a version (`v1.0.0`, …) to trigger GitHub Actions release artifacts.

---

## Documentation

- [UI specification](docs/ui-specification.md) — colors, typography, layout, shortcuts
- [COPYRIGHT](COPYRIGHT) — copyright and contact block
- [Packaging](packaging/README.md) — Flatpak / AppImage notes

---

## Security notes

- Secrets remain **local**; there is no built-in cloud sync.
- Clipboard and auto-lock reduce shoulder-surfing and idle exposure — tune timeouts to your threat model.
- CSV export writes passwords and OTP material in **plain text**; treat export files as highly sensitive.
- Master password handling uses best-effort memory wipe; Python runtimes cannot guarantee zero residual copies.
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
