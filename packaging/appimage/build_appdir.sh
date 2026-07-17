#!/usr/bin/env bash
# Scaffold an AppDir suitable for appimagetool / python-appimage.
# This does not download AppImage tooling; it prepares the layout.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:-$ROOT/dist/KDBXStudio.AppDir}"

rm -rf "$OUT"
mkdir -p "$OUT/usr/bin" "$OUT/usr/lib" "$OUT/usr/share/applications" "$OUT/usr/share/icons/hicolor/256x256/apps"

python3 -m venv "$OUT/usr/venv"
# shellcheck disable=SC1091
source "$OUT/usr/venv/bin/activate"
pip install -U pip
pip install "$ROOT"

cat > "$OUT/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/venv/bin:$PATH"
exec "$HERE/usr/venv/bin/python" -m kdbxstudio "$@"
EOF
chmod +x "$OUT/AppRun"

# Icons / desktop metadata
if [[ -f "$ROOT/assets/kdbxstudio.png" ]]; then
  cp "$ROOT/assets/kdbxstudio.png" "$OUT/usr/share/icons/hicolor/256x256/apps/kdbxstudio.png"
  cp "$ROOT/assets/kdbxstudio.png" "$OUT/kdbxstudio.png"
else
  printf '' > "$OUT/usr/share/icons/hicolor/256x256/apps/kdbxstudio.png"
  ln -sf usr/share/icons/hicolor/256x256/apps/kdbxstudio.png "$OUT/kdbxstudio.png"
fi

if [[ -f "$ROOT/assets/kdbxstudio.desktop" ]]; then
  cp "$ROOT/assets/kdbxstudio.desktop" "$OUT/usr/share/applications/kdbxstudio.desktop"
else
  cat > "$OUT/usr/share/applications/kdbxstudio.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=KDBXStudio
Comment=Qt6 KDBX password manager
Exec=kdbxstudio
Icon=kdbxstudio
Categories=Utility;Security;
Terminal=false
EOF
fi
ln -sf usr/share/applications/kdbxstudio.desktop "$OUT/kdbxstudio.desktop"

cat > "$OUT/usr/bin/kdbxstudio" <<'EOF'
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$HERE/AppRun" "$@"
EOF
chmod +x "$OUT/usr/bin/kdbxstudio"

echo "AppDir prepared at: $OUT"
echo "Next: install appimagetool and run:"
echo "  appimagetool \"$OUT\" dist/KDBXStudio-x86_64.AppImage"
