#!/usr/bin/env bash
# KDBXStudio installer — default: build a portable AppImage.
# Optional: --venv for an editable source install.
set -euo pipefail

readonly APP_NAME="KDBXStudio"
readonly MIN_PYTHON=(3 11)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v readlink >/dev/null 2>&1; then
  SCRIPT_DIR="$(readlink -f "$SCRIPT_DIR")"
fi
readonly SCRIPT_DIR
readonly ROOT="$SCRIPT_DIR"
readonly VENV_DIR="${ROOT}/.venv"
readonly DIST_DIR="${ROOT}/dist"
readonly CACHE_DIR="${ROOT}/.cache"
readonly LOG_DIR="${ROOT}/.install-logs"
readonly TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
readonly LOG_FILE="${LOG_DIR}/install-${TIMESTAMP}.log"

MODE="appimage" # appimage | venv
WITH_DEV=0
WITH_DESKTOP=1
FORCE_VENV=0
ASSUME_YES=0

APPIMAGE_ARCH=""
APPDIR=""
APPIMAGE_OUT=""
APPIMAGETOOL=""

# ── terminal UI ──────────────────────────────────────────────────────────────

if [[ -t 1 ]] && [[ "${NO_COLOR:-}" != "1" ]]; then
  C_RESET=$'\033[0m'
  C_DIM=$'\033[2m'
  C_BOLD=$'\033[1m'
  C_CYAN=$'\033[36m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
else
  C_RESET="" C_DIM="" C_BOLD="" C_CYAN="" C_GREEN="" C_YELLOW="" C_RED=""
fi

say()  { printf '%s\n' "$*"; }
info() { printf '  %s→%s %s\n' "$C_CYAN" "$C_RESET" "$*"; }
ok()   { printf '  %s✓%s %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '  %s!%s %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
die()  { printf '  %s✗%s %s\n' "$C_RED" "$C_RESET" "$*" >&2; exit 1; }

banner() {
  say ""
  say "${C_BOLD}${APP_NAME}${C_RESET} ${C_DIM}installer${C_RESET}"
  say "${C_DIM}$(printf '─%.0s' {1..40})${C_RESET}"
}

usage() {
  cat <<EOF
Usage: ./install.sh [options]

Default: build a portable AppImage under dist/.

Options:
  --appimage      Build AppImage (default)
  --venv          Editable source install into .venv instead
  --dev           Dev extras (implies --venv)
  --no-desktop    Skip desktop entry / ~/.local/bin launcher
  --force         Recreate AppDir / virtualenv from scratch
  -y, --yes       Non-interactive package manager installs
  -h, --help      Show this help

Environment:
  NO_COLOR=1      Disable ANSI colors
EOF
}

# ── helpers ──────────────────────────────────────────────────────────────────

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

ensure_log() {
  mkdir -p "$LOG_DIR"
  {
    echo "=== ${APP_NAME} install ${TIMESTAMP} ==="
    echo "cwd=$PWD"
    echo "root=$ROOT"
    echo "mode=$MODE"
    uname -a || true
  } >"$LOG_FILE"
}

run_quiet() {
  local label="$1"
  shift
  if [[ -t 1 ]]; then
    printf '  %s→%s %s%s…%s' "$C_CYAN" "$C_RESET" "$label" "$C_DIM" "$C_RESET"
  else
    printf '  → %s…\n' "$label"
  fi
  if "$@" >>"$LOG_FILE" 2>&1; then
    if [[ -t 1 ]]; then
      printf '\r  %s✓%s %s\n' "$C_GREEN" "$C_RESET" "$label"
    else
      printf '  ✓ %s\n' "$label"
    fi
    return 0
  fi
  if [[ -t 1 ]]; then
    printf '\r  %s✗%s %s\n' "$C_RED" "$C_RESET" "$label" >&2
  else
    printf '  ✗ %s\n' "$label" >&2
  fi
  printf '\n' >&2
  die "Failed: ${label}. See ${LOG_FILE}"$'\n'"$(tail -n 20 "$LOG_FILE" 2>/dev/null || true)"
}

sudo_if_needed() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  elif need_cmd sudo; then
    if [[ "$ASSUME_YES" -eq 1 ]]; then
      sudo -n "$@" 2>/dev/null || sudo "$@"
    else
      sudo "$@"
    fi
  else
    die "Root privileges required for system packages (install sudo or run as root)."
  fi
}

version_ge() {
  local IFS=.
  local -a a=($1) b=($2)
  local i
  for ((i = 0; i < ${#b[@]}; i++)); do
    local ai="${a[i]:-0}" bi="${b[i]:-0}"
    if ((ai > bi)); then return 0; fi
    if ((ai < bi)); then return 1; fi
  done
  return 0
}

download_file() {
  local url="$1" dest="$2"
  if need_cmd curl; then
    curl -fsSL --retry 3 --retry-delay 1 -o "$dest" "$url"
  elif need_cmd wget; then
    wget -q -O "$dest" "$url"
  else
    return 1
  fi
}

# ── args ─────────────────────────────────────────────────────────────────────

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --appimage) MODE="appimage" ;;
      --venv) MODE="venv" ;;
      --dev) WITH_DEV=1; MODE="venv" ;;
      --no-desktop) WITH_DESKTOP=0 ;;
      --force) FORCE_VENV=1 ;;
      -y|--yes) ASSUME_YES=1 ;;
      -h|--help) usage; exit 0 ;;
      *) die "Unknown option: $1 (try --help)" ;;
    esac
    shift
  done
}

# ── distro detection ─────────────────────────────────────────────────────────

DISTRO_ID=""
DISTRO_LIKE=""
DISTRO_VERSION=""
DISTRO_NAME=""
PKG_FAMILY=""

detect_distro() {
  if [[ ! -f /etc/os-release ]]; then
    die "Cannot detect Linux distribution (/etc/os-release missing)."
  fi
  # shellcheck disable=SC1091
  source /etc/os-release
  DISTRO_ID="${ID:-unknown}"
  DISTRO_LIKE="${ID_LIKE:-}"
  DISTRO_VERSION="${VERSION_ID:-}"
  DISTRO_NAME="${PRETTY_NAME:-$DISTRO_ID}"

  local key="${DISTRO_ID} ${DISTRO_LIKE}"
  case "$key" in
    *debian*|*ubuntu*|*linuxmint*|*pop*|*elementary*|*zorin*|*raspbian*)
      PKG_FAMILY="debian"
      ;;
    *fedora*|*rhel*|*centos*|*rocky*|*almalinux*|*nobara*)
      PKG_FAMILY="rhel"
      ;;
    *arch*|*manjaro*|*endeavouros*|*garuda*)
      PKG_FAMILY="arch"
      ;;
    *suse*|*opensuse*)
      PKG_FAMILY="suse"
      ;;
    *)
      PKG_FAMILY="unknown"
      ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64) APPIMAGE_ARCH="x86_64" ;;
    aarch64|arm64) APPIMAGE_ARCH="aarch64" ;;
    *) die "Unsupported CPU architecture: $(uname -m) (need x86_64 or aarch64)." ;;
  esac
  APPDIR="${DIST_DIR}/KDBXStudio.AppDir"
  APPIMAGE_OUT="${DIST_DIR}/KDBXStudio-${APPIMAGE_ARCH}.AppImage"
  APPIMAGETOOL="${CACHE_DIR}/appimagetool-${APPIMAGE_ARCH}.AppImage"
}

# ── system packages ──────────────────────────────────────────────────────────

can_elevate() {
  if [[ "${EUID}" -eq 0 ]]; then
    return 0
  fi
  need_cmd sudo || return 1
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi
  [[ -t 0 && -t 1 ]]
}

debian_pkg_installed() {
  local status
  status="$(dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true)"
  [[ "$status" == *"install ok installed"* ]]
}

debian_need_one_of() {
  local p first=""
  for p in "$@"; do
    apt-cache show "$p" >/dev/null 2>&1 || continue
    if debian_pkg_installed "$p"; then
      return 0
    fi
    [[ -z "$first" ]] && first="$p"
  done
  [[ -n "$first" ]] && printf '%s\n' "$first"
  return 0
}

python_runtime_ready() {
  pick_python || return 1
  "$PYTHON_BIN" -c 'import venv' >/dev/null 2>&1
}

install_system_packages() {
  case "$PKG_FAMILY" in
    debian)
      local install_list=()
      local needed
      local groups=(
        "python3"
        "python3-venv"
        "python3-pip"
        "libxcb-cursor0"
        "libxkbcommon0"
        "libxkbcommon-x11-0"
        "libegl1"
        "libgl1"
        "libglib2.0-0t64 libglib2.0-0"
        "libdbus-1-3"
        "libfontconfig1"
      )
      local group
      for group in "${groups[@]}"; do
        # shellcheck disable=SC2086
        needed="$(debian_need_one_of $group)"
        [[ -n "$needed" ]] && install_list+=("$needed")
      done
      if ! python_runtime_ready && need_cmd apt-cache; then
        for cand in python3.12 python3.11; do
          if apt-cache show "$cand" >/dev/null 2>&1 && ! debian_pkg_installed "$cand"; then
            install_list+=("$cand")
          fi
          if apt-cache show "${cand}-venv" >/dev/null 2>&1 && ! debian_pkg_installed "${cand}-venv"; then
            install_list+=("${cand}-venv")
          fi
        done
      fi
      if [[ "${#install_list[@]}" -eq 0 ]]; then
        ok "System packages already installed"
        return 0
      fi
      if ! can_elevate; then
        if python_runtime_ready; then
          warn "Optional packages not installed (sudo unavailable): ${install_list[*]}"
          return 0
        fi
        die "Need sudo to install: ${install_list[*]}"
      fi
      run_quiet "Updating package index" sudo_if_needed apt-get update -qq
      run_quiet "Installing system packages" \
        sudo_if_needed apt-get install -y -qq --no-install-recommends "${install_list[@]}"
      ;;
    rhel)
      if python_runtime_ready && ! can_elevate; then
        ok "Python runtime already available — skipping system package install"
        return 0
      fi
      if ! can_elevate; then
        die "Root privileges required to install system packages."
      fi
      local pkgs=(
        python3 python3-pip libxcb libxkbcommon libxkbcommon-x11
        mesa-libGL mesa-libEGL fontconfig
      )
      if need_cmd dnf; then
        run_quiet "Installing system packages" sudo_if_needed dnf install -y -q "${pkgs[@]}"
      elif need_cmd yum; then
        run_quiet "Installing system packages" sudo_if_needed yum install -y -q "${pkgs[@]}"
      else
        die "Neither dnf nor yum found."
      fi
      ;;
    arch)
      if python_runtime_ready && ! can_elevate; then
        ok "Python runtime already available — skipping system package install"
        return 0
      fi
      if ! can_elevate; then
        die "Root privileges required to install system packages."
      fi
      run_quiet "Installing system packages" \
        sudo_if_needed pacman -Sy --noconfirm --needed \
          python python-pip python-virtualenv \
          libxcb libxkbcommon libxkbcommon-x11 mesa fontconfig
      ;;
    suse)
      if python_runtime_ready && ! can_elevate; then
        ok "Python runtime already available — skipping system package install"
        return 0
      fi
      if ! can_elevate; then
        die "Root privileges required to install system packages."
      fi
      run_quiet "Installing system packages" \
        sudo_if_needed zypper --non-interactive --quiet install -y \
          python3 python3-pip python3-venv \
          libxcb1 libxkbcommon0 libxkbcommon-x11-0 \
          Mesa-libGL1 Mesa-libEGL1 fontconfig
      ;;
    *)
      if python_runtime_ready; then
        warn "Unknown distro family — using existing Python runtime."
      else
        die "Unknown distro: install Python ${MIN_PYTHON[0]}.${MIN_PYTHON[1]}+ manually, then re-run."
      fi
      ;;
  esac
}

# ── Python selection ─────────────────────────────────────────────────────────

PYTHON_BIN=""

pick_python() {
  local cand path ver
  for cand in /usr/bin/python3.12 /usr/bin/python3.11 /usr/bin/python3 \
              /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/local/bin/python3; do
    if [[ -x "$cand" ]]; then
      ver="$("$cand" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || true)"
      if [[ -n "$ver" ]] && version_ge "$ver" "${MIN_PYTHON[0]}.${MIN_PYTHON[1]}"; then
        PYTHON_BIN="$cand"
        return 0
      fi
    fi
  done
  for cand in python3.12 python3.11 python3; do
    while IFS= read -r path; do
      [[ -z "$path" ]] && continue
      case "$path" in
        */.venv/*) continue ;;
      esac
      ver="$("$path" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null || true)"
      if [[ -n "$ver" ]] && version_ge "$ver" "${MIN_PYTHON[0]}.${MIN_PYTHON[1]}"; then
        PYTHON_BIN="$path"
        return 0
      fi
    done < <(type -aP "$cand" 2>/dev/null || true)
  done
  return 1
}

# ── venv mode ────────────────────────────────────────────────────────────────

setup_venv() {
  if [[ -d "$VENV_DIR" ]] && [[ "$FORCE_VENV" -eq 1 ]]; then
    info "Removing existing virtualenv${C_DIM}…${C_RESET}"
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    run_quiet "Creating virtual environment" "$PYTHON_BIN" -m venv "$VENV_DIR"
  else
    ok "Virtual environment already present"
  fi

  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
  run_quiet "Upgrading pip" python -m pip install -q --upgrade pip setuptools wheel

  local spec="$ROOT"
  if [[ "$WITH_DEV" -eq 1 ]]; then
    spec="${ROOT}[dev]"
  fi
  run_quiet "Installing ${APP_NAME}" python -m pip install -q -e "${spec}"

  # Best-effort KeePassXC-Browser native messaging manifests
  if python -m kdbxstudio.browser.install_host >>"${LOG_FILE}" 2>&1; then
    ok "Browser native messaging host manifests installed"
  else
    warn "Could not install browser host manifests (run later: python -m kdbxstudio.browser.install_host)"
  fi
}

install_desktop_venv() {
  local bindir="${HOME}/.local/bin"
  local appsdir="${HOME}/.local/share/applications"
  local icondir="${HOME}/.local/share/icons/hicolor"
  local wrapper="${bindir}/kdbxstudio"
  local desktop_src="${ROOT}/assets/kdbxstudio.desktop"
  local desktop_dst="${appsdir}/kdbxstudio.desktop"
  local icon_id="com.kdbxstudio.KDBXStudio"

  mkdir -p "$bindir" "$appsdir"
  cat >"$wrapper" <<EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/kdbxstudio" "\$@"
EOF
  chmod +x "$wrapper"

  if [[ -f "$desktop_src" ]]; then
    sed -e "s|^Exec=.*|Exec=${wrapper} %f|" \
        -e "s|^Icon=.*|Icon=${icon_id}|" \
        "$desktop_src" >"$desktop_dst"
  else
    cat >"$desktop_dst" <<EOF
[Desktop Entry]
Type=Application
Name=KDBXStudio
Comment=Modern Qt6 KDBX password manager
Exec=${wrapper} %f
Icon=${icon_id}
Terminal=false
Categories=Utility;Security;Qt;
MimeType=application/x-keepass2;
StartupNotify=true
EOF
  fi

  local size src dest
  for size in 32 48 64 128 256; do
    src="${ROOT}/assets/icons/kdbxstudio-${size}.png"
    if [[ -f "$src" ]]; then
      dest="${icondir}/${size}x${size}/apps"
      mkdir -p "$dest"
      cp -f "$src" "${dest}/${icon_id}.png"
    fi
  done
  if [[ -f "${ROOT}/assets/kdbxstudio.svg" ]]; then
    mkdir -p "${icondir}/scalable/apps"
    cp -f "${ROOT}/assets/kdbxstudio.svg" "${icondir}/scalable/apps/${icon_id}.svg"
  fi
  if [[ -f "${ROOT}/assets/kdbxstudio.png" ]]; then
    mkdir -p "${icondir}/256x256/apps"
    cp -f "${ROOT}/assets/kdbxstudio.png" "${icondir}/256x256/apps/${icon_id}.png"
  fi

  if need_cmd update-desktop-database; then
    update-desktop-database "${appsdir}" >/dev/null 2>&1 || true
  fi
  if need_cmd gtk-update-icon-cache; then
    gtk-update-icon-cache -f -t "${icondir}" >/dev/null 2>&1 || true
  fi

  ok "Desktop launcher and icons installed"
  if [[ ":$PATH:" != *":${bindir}:"* ]]; then
    warn "Add ${bindir} to PATH to run \`kdbxstudio\` from any shell"
  fi
}

# ── AppImage mode ────────────────────────────────────────────────────────────

ensure_appimagetool() {
  mkdir -p "$CACHE_DIR"
  if [[ -x "$APPIMAGETOOL" ]]; then
    ok "appimagetool ready"
    return 0
  fi
  local url="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage"
  run_quiet "Downloading appimagetool" download_file "$url" "$APPIMAGETOOL"
  chmod +x "$APPIMAGETOOL"
}

build_appdir() {
  mkdir -p "$DIST_DIR"
  if [[ -d "$APPDIR" ]] && [[ "$FORCE_VENV" -eq 1 ]]; then
    rm -rf "$APPDIR"
  fi

  if [[ -d "$APPDIR/usr/venv" ]] && [[ "$FORCE_VENV" -eq 0 ]]; then
    ok "AppDir already present — refreshing install"
  else
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin" \
             "$APPDIR/usr/share/applications" \
             "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    run_quiet "Creating AppDir virtualenv" "$PYTHON_BIN" -m venv "$APPDIR/usr/venv"
  fi

  local app_python="${APPDIR}/usr/venv/bin/python"
  run_quiet "Upgrading pip (AppDir)" "$app_python" -m pip install -q --upgrade pip setuptools wheel
  run_quiet "Installing ${APP_NAME} into AppDir" "$app_python" -m pip install -q "$ROOT"

  cat >"$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/venv/bin:$PATH"
# Prefer bundled Qt plugins from PySide6 when present.
if [[ -d "$HERE/usr/venv/lib" ]]; then
  _pyside="$(find "$HERE/usr/venv/lib" -type d -path '*/PySide6/Qt/plugins' 2>/dev/null | head -n1 || true)"
  if [[ -n "$_pyside" ]]; then
    export QT_PLUGIN_PATH="${_pyside}${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
  fi
fi
exec "$HERE/usr/venv/bin/python" -m kdbxstudio "$@"
EOF
  chmod +x "$APPDIR/AppRun"

  # AppImage desktop entry: Icon basename must match a file in AppDir root.
  cat >"$APPDIR/kdbxstudio.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=KDBXStudio
GenericName=Password Manager
Comment=Modern Qt6 KDBX password manager for Linux (GPL-3.0)
Exec=AppRun %f
Icon=kdbxstudio
Terminal=false
Categories=Utility;Security;Qt;
Keywords=keepass;kdbx;password;security;
StartupNotify=true
MimeType=application/x-keepass2;
StartupWMClass=kdbxstudio
EOF
  cp -f "$APPDIR/kdbxstudio.desktop" "$APPDIR/usr/share/applications/kdbxstudio.desktop"

  local icon_src=""
  if [[ -f "${ROOT}/assets/icons/kdbxstudio-256.png" ]]; then
    icon_src="${ROOT}/assets/icons/kdbxstudio-256.png"
  elif [[ -f "${ROOT}/assets/kdbxstudio.png" ]]; then
    icon_src="${ROOT}/assets/kdbxstudio.png"
  fi
  if [[ -n "$icon_src" ]]; then
    cp -f "$icon_src" "$APPDIR/kdbxstudio.png"
    cp -f "$icon_src" "$APPDIR/usr/share/icons/hicolor/256x256/apps/kdbxstudio.png"
  else
    # appimagetool still expects an icon file; create a tiny placeholder PNG via Python if needed.
    "$PYTHON_BIN" - <<'PY' "$APPDIR/kdbxstudio.png"
import struct, zlib, sys
path = sys.argv[1]
# 1x1 teal PNG
raw = b"\x00" + b"\x14\xb8\xa6\xff"
def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
open(path, "wb").write(png)
PY
    cp -f "$APPDIR/kdbxstudio.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/kdbxstudio.png"
  fi

  cat >"$APPDIR/usr/bin/kdbxstudio" <<'EOF'
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$HERE/AppRun" "$@"
EOF
  chmod +x "$APPDIR/usr/bin/kdbxstudio"

  ok "AppDir prepared"
}

pack_appimage() {
  mkdir -p "$DIST_DIR"
  rm -f "$APPIMAGE_OUT"
  # Avoid FUSE requirement when running appimagetool itself.
  export APPIMAGE_EXTRACT_AND_RUN=1
  export ARCH="$APPIMAGE_ARCH"
  run_quiet "Packing AppImage" \
    env APPIMAGE_EXTRACT_AND_RUN=1 ARCH="$APPIMAGE_ARCH" \
      "$APPIMAGETOOL" --no-appstream "$APPDIR" "$APPIMAGE_OUT"
  chmod +x "$APPIMAGE_OUT"
  ok "AppImage ready: ${APPIMAGE_OUT}"
}

install_appimage_to_bin() {
  local dest="/usr/local/bin/KDBXStudio"
  info "Copying AppImage to ${dest}…"
  sudo_if_needed cp -f "$APPIMAGE_OUT" "$dest"
  sudo_if_needed chmod +x "$dest"
  ok "Installed ${dest}"
}

install_desktop_appimage() {
  local bindir="${HOME}/.local/bin"
  local appsdir="${HOME}/.local/share/applications"
  local icondir="${HOME}/.local/share/icons/hicolor"
  local wrapper="${bindir}/kdbxstudio"
  local desktop_dst="${appsdir}/kdbxstudio.desktop"
  local icon_id="com.kdbxstudio.KDBXStudio"

  mkdir -p "$bindir" "$appsdir"
  cat >"$wrapper" <<EOF
#!/usr/bin/env bash
exec "${APPIMAGE_OUT}" "\$@"
EOF
  chmod +x "$wrapper"

  cat >"$desktop_dst" <<EOF
[Desktop Entry]
Type=Application
Name=KDBXStudio
GenericName=Password Manager
Comment=Modern Qt6 KDBX password manager for Linux (GPL-3.0)
Exec=${wrapper} %f
Icon=${icon_id}
Terminal=false
Categories=Utility;Security;Qt;
Keywords=keepass;kdbx;password;security;
StartupNotify=true
MimeType=application/x-keepass2;
StartupWMClass=kdbxstudio
EOF

  local size src dest
  for size in 32 48 64 128 256; do
    src="${ROOT}/assets/icons/kdbxstudio-${size}.png"
    if [[ -f "$src" ]]; then
      dest="${icondir}/${size}x${size}/apps"
      mkdir -p "$dest"
      cp -f "$src" "${dest}/${icon_id}.png"
    fi
  done
  if [[ -f "${ROOT}/assets/kdbxstudio.png" ]]; then
    mkdir -p "${icondir}/256x256/apps"
    cp -f "${ROOT}/assets/kdbxstudio.png" "${icondir}/256x256/apps/${icon_id}.png"
  fi

  if need_cmd update-desktop-database; then
    update-desktop-database "${appsdir}" >/dev/null 2>&1 || true
  fi

  ok "Desktop launcher points to AppImage"
  if [[ ":$PATH:" != *":${bindir}:"* ]]; then
    warn "Add ${bindir} to PATH to run \`kdbxstudio\` from any shell"
  fi
}

# ── main ─────────────────────────────────────────────────────────────────────

main() {
  parse_args "$@"
  banner
  ensure_log
  detect_arch

  if [[ "$(uname -s)" != "Linux" ]]; then
    die "This installer supports Linux only."
  fi
  if [[ ! -f "${ROOT}/pyproject.toml" ]]; then
    die "Run this script from the KDBXStudio repository root."
  fi

  detect_distro
  ok "Detected ${DISTRO_NAME}${DISTRO_VERSION:+ (${DISTRO_VERSION})} · ${PKG_FAMILY}"
  info "Mode: ${MODE}"

  install_system_packages

  if ! pick_python; then
    die "Python ${MIN_PYTHON[0]}.${MIN_PYTHON[1]}+ is required but was not found."
  fi
  local py_ver
  py_ver="$("$PYTHON_BIN" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
  ok "Using ${PYTHON_BIN} (${py_ver})"

  if [[ "$MODE" == "appimage" ]]; then
    ensure_appimagetool
    build_appdir
    pack_appimage
    install_appimage_to_bin
    if [[ "$WITH_DESKTOP" -eq 1 ]]; then
      install_desktop_appimage
    else
      info "Skipped desktop integration (--no-desktop)"
    fi
    say ""
    say "${C_BOLD}Done.${C_RESET} ${C_DIM}Log: ${LOG_FILE}${C_RESET}"
    say ""
    say "  AppImage: ${C_CYAN}${APPIMAGE_OUT}${C_RESET}"
    say "  Launch:   ${C_CYAN}${APPIMAGE_OUT}${C_RESET}"
    say "  Or:       ${C_CYAN}kdbxstudio${C_RESET}"
    say ""
    return 0
  fi

  setup_venv
  if [[ "$WITH_DESKTOP" -eq 1 ]]; then
    install_desktop_venv
  else
    info "Skipped desktop integration (--no-desktop)"
  fi
  say ""
  say "${C_BOLD}Done.${C_RESET} ${C_DIM}Log: ${LOG_FILE}${C_RESET}"
  say ""
  say "  Launch:  ${C_CYAN}kdbxstudio${C_RESET}"
  say "  Or:      ${C_CYAN}${VENV_DIR}/bin/kdbxstudio${C_RESET}"
  say "  Module:  ${C_DIM}source ${VENV_DIR}/bin/activate && python -m kdbxstudio${C_RESET}"
  say ""
}

main "$@"
