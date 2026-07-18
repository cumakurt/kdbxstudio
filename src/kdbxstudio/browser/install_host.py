"""Install native messaging manifests for the official KeePassXC-Browser extension."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

# Official KeePassXC-Browser host name — required for the stock extension.
HOST_NAME = "org.keepassxc.keepassxc_browser"

# Published KeePassXC-Browser extension IDs
CHROME_EXTENSION_IDS = [
    "oboonakemofpalcgghocfoadofidjkkk",  # Chrome Web Store
    "jfdjamakanclpjagahiambmhgjmhbpmm",  # Edge
]
FIREFOX_EXTENSION_IDS = [
    "keepassxc-browser@keepassxc.org",
]


def _host_script_path() -> Path:
    which = shutil.which("kdbxstudio-browser-host")
    if which:
        return Path(which)
    xdg = os.environ.get("XDG_DATA_HOME")
    root = Path(xdg) / "kdbxstudio" if xdg else Path.home() / ".local/share/kdbxstudio"
    root.mkdir(parents=True, exist_ok=True)
    launcher = root / "keepassxc-proxy.sh"
    launcher.write_text(
        "#!/bin/sh\n"
        f'exec "{sys.executable}" -m kdbxstudio.browser.host "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    return launcher


def install(*, also_alias: bool = True) -> list[Path]:
    """Install manifests so KeePassXC-Browser talks to KDBXStudio.

    Warning: if KeePassXC is also installed, its manifest may conflict. Prefer
    disabling KeePassXC browser integration while using KDBXStudio, or remove
    the KeePassXC native messaging JSON for this user.
    """
    host = _host_script_path()
    written: list[Path] = []
    chrome_dirs = [
        Path.home() / ".config/google-chrome/NativeMessagingHosts",
        Path.home() / ".config/chromium/NativeMessagingHosts",
        Path.home() / ".config/BraveSoftware/Brave-Browser/NativeMessagingHosts",
        Path.home() / ".config/microsoft-edge/NativeMessagingHosts",
        Path.home() / ".config/vivaldi/NativeMessagingHosts",
    ]
    chrome_manifest = {
        "name": HOST_NAME,
        "description": "KDBXStudio KeePassXC-Browser bridge",
        "path": str(host),
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{ext_id}/" for ext_id in CHROME_EXTENSION_IDS
        ],
    }
    for directory in chrome_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{HOST_NAME}.json"
        path.write_text(json.dumps(chrome_manifest, indent=2) + "\n", encoding="utf-8")
        written.append(path)

    firefox_dir = Path.home() / ".mozilla/native-messaging-hosts"
    firefox_dir.mkdir(parents=True, exist_ok=True)
    ff_manifest = {
        "name": HOST_NAME,
        "description": "KDBXStudio KeePassXC-Browser bridge",
        "path": str(host),
        "type": "stdio",
        "allowed_extensions": FIREFOX_EXTENSION_IDS,
    }
    ff_path = firefox_dir / f"{HOST_NAME}.json"
    ff_path.write_text(json.dumps(ff_manifest, indent=2) + "\n", encoding="utf-8")
    written.append(ff_path)

    if also_alias:
        # Keep our previous host name for tooling / docs.
        alias = "com.kdbxstudio.browser_host"
        for directory in chrome_dirs:
            path = directory / f"{alias}.json"
            payload = {**chrome_manifest, "name": alias}
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            written.append(path)
        alias_ff = firefox_dir / f"{alias}.json"
        alias_ff.write_text(
            json.dumps({**ff_manifest, "name": alias}, indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(alias_ff)
    return written


def main() -> None:
    paths = install()
    print("Installed KeePassXC-Browser native messaging manifests:")
    for path in paths:
        print(f"  {path}")
    print()
    print("Next steps:")
    print("  1. Install the KeePassXC-Browser extension in Firefox/Chrome.")
    print("  2. Start KDBXStudio and unlock your database.")
    print("  3. In the extension, click 'Connect' / 'Associate' and approve the dialog.")
    print("  4. If KeePassXC is also installed, disable its browser integration")
    print("     or remove its conflicting NativeMessagingHosts JSON.")


if __name__ == "__main__":
    main()
