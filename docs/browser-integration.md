# KeePassXC-Browser integration

KDBXStudio speaks the same native-messaging protocol as KeePassXC, so the
**official KeePassXC-Browser** extension can fill logins from an unlocked vault.

## Architecture

1. Browser extension ↔ native messaging host `org.keepassxc.keepassxc_browser`
2. Host (`kdbxstudio-browser-host` / `python -m kdbxstudio.browser.host`) ↔ Unix socket
3. KDBXStudio (`BrowserLocalServer`) runs the encrypted KeePassXC-Browser protocol

Socket paths (Linux):

- `$XDG_RUNTIME_DIR/app/org.keepassxc.KeePassXC/org.keepassxc.KeePassXC.BrowserServer`
- Legacy symlink: `$XDG_RUNTIME_DIR/org.keepassxc.KeePassXC.BrowserServer`
- Fallback: `~/.local/share/kdbxstudio/browser.sock`

Associations are stored in the KDBX Meta CustomData as `KPXC_BROWSER_<id>`
(compatible with KeePassXC). **Save the database** after associating.

## Setup

1. Install KDBXStudio (`./install.sh` installs native messaging manifests when possible).
2. Or install manifests manually:

```bash
python -m kdbxstudio.browser.install_host
# or: Settings → Install browser host manifests…
```

3. Install [KeePassXC-Browser](https://keepassxc.org/docs/KeePassXC_GettingStarted.html#_setup_browser_integration)
   from the Chrome Web Store / Firefox Add-ons.
4. Start KDBXStudio, unlock your database, and keep **Enable KeePassXC-Browser integration** on (Settings).
5. In the extension, click **Connect** / **Associate**, approve the dialog, and name the connection.
6. Save the database so the association persists.

## Supported actions

| Action | Notes |
|--------|--------|
| `change-public-keys` | NaCl box key exchange |
| `get-databasehash` | SHA-256 of root group UUID (KeePassXC-compatible) |
| `associate` / `test-associate` | Prompt + CustomData keys |
| `get-logins` / `get-logins-count` | URL host matching |
| `set-login` | Create or update entry |
| `generate-password` | Desktop generator |
| `get-database-groups` / `create-new-group` | Group tree |
| `get-totp` | Entry OTP |
| `lock-database` | Locks all open vaults (no unlock prompt) |

## Conflict with KeePassXC

Both apps use the host name `org.keepassxc.keepassxc_browser`. Only one
native-messaging JSON should be active for your browser profile.

If KeePassXC is also installed:

- Disable KeePassXC’s browser integration, **or**
- Replace its NativeMessagingHosts JSON with the KDBXStudio one (install_host does this for the current user).

## Troubleshooting

- Extension says “Cannot connect”: unlock a vault in KDBXStudio; confirm Settings → browser integration is enabled.
- Association lost after restart: save the `.kdbx` after connecting.
- Wrong app answers: check `~/.mozilla/native-messaging-hosts/org.keepassxc.keepassxc_browser.json` (or Chromium equivalent) `path` points at `kdbxstudio-browser-host` or the KDBXStudio launcher script.
