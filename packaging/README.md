# Packaging

## Flatpak

Manifest: `packaging/flatpak/com.kdbxstudio.KDBXStudio.yml`

```bash
flatpak-builder --user --install --force-clean build-dir \
  packaging/flatpak/com.kdbxstudio.KDBXStudio.yml
flatpak run com.kdbxstudio.KDBXStudio
```

Requires KDE Platform/SDK 6.7 runtimes.

## AppImage

Preferred (downloads `appimagetool` if needed and packs the image):

```bash
./install.sh
# → dist/KDBXStudio-x86_64.AppImage
```

AppDir-only scaffold:

```bash
chmod +x packaging/appimage/build_appdir.sh
./packaging/appimage/build_appdir.sh
```

The AppDir embeds a venv with KDBXStudio + PySide6 and uses project icons when present.

## Flathub / AppStream

Metainfo: `assets/metainfo/com.kdbxstudio.KDBXStudio.metainfo.xml`

The Flatpak manifest installs desktop + metainfo + icons. To publish on Flathub,
fork [flathub/flathub](https://github.com/flathub/flathub), add the manifest under
`com.kdbxstudio.KDBXStudio`, and open a PR following Flathub submission guidelines.
This repository does not automate Flathub publication.

**Hardware keys:** YubiKey / challenge-response is not supported by pykeepass yet;
the Settings dialog documents this limitation.

Signed releases: tag `v*` to run `.github/workflows/release.yml` (artifacts on GitHub Releases).
GPG/cosign signing can be added as a follow-up CI step when keys are available.
