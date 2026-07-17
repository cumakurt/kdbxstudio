#!/usr/bin/env bash
# Prepare an AppDir for appimagetool.
# Prefer the top-level installer (builds AppImage end-to-end):
#   ./install.sh
# This script only scaffolds the AppDir tree.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
if command -v readlink >/dev/null 2>&1; then
  ROOT="$(readlink -f "$ROOT")"
fi
OUT="${1:-$ROOT/dist/KDBXStudio.AppDir}"

rm -rf "$OUT"
mkdir -p "$OUT/usr/bin" "$OUT/usr/share/applications" \
         "$OUT/usr/share/icons/hicolor/256x256/apps"

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv "$OUT/usr/venv"
"$OUT/usr/venv/bin/python" -m pip install -q --upgrade pip setuptools wheel
"$OUT/usr/venv/bin/python" -m pip install -q "$ROOT"

cat > "$OUT/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/venv/bin:$PATH"
if [[ -d "$HERE/usr/venv/lib" ]]; then
  _pyside="$(find "$HERE/usr/venv/lib" -type d -path '*/PySide6/Qt/plugins' 2>/dev/null | head -n1 || true)"
  if [[ -n "$_pyside" ]]; then
    export QT_PLUGIN_PATH="${_pyside}${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
  fi
fi
exec "$HERE/usr/venv/bin/python" -m kdbxstudio "$@"
EOF
chmod +x "$OUT/AppRun"

cat > "$OUT/kdbxstudio.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=KDBXStudio
Comment=Modern Qt6 KDBX password manager
Exec=AppRun %f
Icon=kdbxstudio
Categories=Utility;Security;Qt;
Terminal=false
MimeType=application/x-keepass2;
StartupNotify=true
EOF
cp -f "$OUT/kdbxstudio.desktop" "$OUT/usr/share/applications/kdbxstudio.desktop"

if [[ -f "$ROOT/assets/icons/kdbxstudio-256.png" ]]; then
  cp -f "$ROOT/assets/icons/kdbxstudio-256.png" "$OUT/kdbxstudio.png"
elif [[ -f "$ROOT/assets/kdbxstudio.png" ]]; then
  cp -f "$ROOT/assets/kdbxstudio.png" "$OUT/kdbxstudio.png"
else
  printf '' > "$OUT/kdbxstudio.png"
fi
cp -f "$OUT/kdbxstudio.png" "$OUT/usr/share/icons/hicolor/256x256/apps/kdbxstudio.png"

cat > "$OUT/usr/bin/kdbxstudio" <<'EOF'
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$HERE/AppRun" "$@"
EOF
chmod +x "$OUT/usr/bin/kdbxstudio"

echo "AppDir prepared at: $OUT"
echo "Next: ./install.sh   (or: appimagetool \"$OUT\" dist/KDBXStudio-x86_64.AppImage)"
