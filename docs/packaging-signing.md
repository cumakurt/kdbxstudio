# Packaging and signing

Trust distribution is part of beating KeePassXC / Bitwarden on install friction.

## AppImage

- Build with `./install.sh --appimage`.
- Sign releases with [minisign](https://jedisct1.github.io/minisign/) or `cosign`:

```bash
minisign -S -m dist/KDBXStudio-x86_64.AppImage -s minisign.key
# publish .minisig next to the AppImage on GitHub Releases
```

## Flatpak

- Manifest scaffold: `packaging/flatpak/com.kdbxstudio.KDBXStudio.yml`
- Next steps for Flathub: finish runtime deps, add AppStream screenshots, submit a PR to flathub/flathub.

## Plugin integrity

- Settings key `plugin_sha256_allowlist` (list of 64-char hex digests).
- When non-empty, `PluginManager.discover()` only loads matching `*_plugin.py` files.
- Compute a digest:

```bash
sha256sum ~/.local/share/kdbxstudio/plugins/my_plugin.py
```

Leave the allowlist empty to keep the current developer-friendly load behaviour.

## Browser host

```bash
python -m kdbxstudio.browser.install_host
```

Installs Chromium/Firefox native-messaging manifests for the stock
KeePassXC-Browser extension (`org.keepassxc.keepassxc_browser`).
`./install.sh` runs this best-effort after the venv install.

Unlock a vault in KDBXStudio (Settings → Enable KeePassXC-Browser integration),
then Connect / Associate in the extension. See [browser-integration.md](browser-integration.md).

If KeePassXC is also installed, disable its browser integration to avoid
conflicting native messaging manifests.
