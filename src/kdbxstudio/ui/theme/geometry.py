"""Spacing, radius, elevation, and typography geometry tokens."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpacingTokens:
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    xxxl: int = 48


@dataclass(frozen=True)
class RadiusTokens:
    xs: int = 4
    sm: int = 6
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclass(frozen=True)
class ElevationTokens:
    e0: str = "none"
    e1: str = "0 1px 2px rgba(0, 0, 0, 0.16)"
    e2: str = "0 4px 12px rgba(0, 0, 0, 0.24)"
    e3: str = "0 12px 32px rgba(0, 0, 0, 0.32)"


@dataclass(frozen=True)
class TypeScale:
    display: int = 26
    title: int = 18
    subtitle: int = 15
    body: int = 13
    caption: int = 11
    overline: int = 10
    mono: int = 13


@dataclass(frozen=True)
class DensityMetrics:
    control_height: int
    row_height: int
    toolbar_icon: int
    menu_icon: int
    sidebar_width: int


SPACING = SpacingTokens()
RADIUS = RadiusTokens()
TYPE_SCALE = TypeScale()

ELEVATION_DARK = ElevationTokens(
    e0="none",
    e1="0 1px 2px rgba(0, 0, 0, 0.24)",
    e2="0 4px 12px rgba(0, 0, 0, 0.36)",
    e3="0 12px 32px rgba(0, 0, 0, 0.48)",
)
ELEVATION_LIGHT = ElevationTokens(
    e0="none",
    e1="0 1px 2px rgba(0, 0, 0, 0.06)",
    e2="0 4px 12px rgba(0, 0, 0, 0.08)",
    e3="0 12px 32px rgba(0, 0, 0, 0.12)",
)

DENSITY_COMPACT = DensityMetrics(
    control_height=30,
    row_height=32,
    toolbar_icon=18,
    menu_icon=16,
    sidebar_width=220,
)
DENSITY_COMFORTABLE = DensityMetrics(
    control_height=36,
    row_height=38,
    toolbar_icon=20,
    menu_icon=18,
    sidebar_width=240,
)


def elevation_for(appearance: str) -> ElevationTokens:
    return ELEVATION_LIGHT if appearance == "light" else ELEVATION_DARK


def density_metrics(ui_density: str) -> DensityMetrics:
    if (ui_density or "").strip().lower() == "comfortable":
        return DENSITY_COMFORTABLE
    return DENSITY_COMPACT


VALID_UI_SCALE_PERCENTS: frozenset[int] = frozenset(
    {40, 50, 60, 70, 80, 90, 100, 110, 125, 150}
)
VALID_MENU_SIZES: frozenset[str] = frozenset({"small", "medium", "large"})
VALID_WINDOW_RESOLUTIONS: frozenset[str] = frozenset(
    {
        "auto",
        "1024x640",
        "1280x720",
        "1280x800",
        "1440x900",
        "1600x900",
        "1920x1080",
    }
)

WINDOW_RESOLUTION_SIZES: dict[str, tuple[int, int] | None] = {
    "auto": None,
    "1024x640": (1024, 640),
    "1280x720": (1280, 720),
    "1280x800": (1280, 800),
    "1440x900": (1440, 900),
    "1600x900": (1600, 900),
    "1920x1080": (1920, 1080),
}


@dataclass(frozen=True)
class MenuMetrics:
    bar_height: int
    item_pad_y: int
    item_pad_x: int
    item_min_height: int
    font_delta: int


MENU_SMALL = MenuMetrics(
    bar_height=26, item_pad_y=4, item_pad_x=10, item_min_height=24, font_delta=-1
)
MENU_MEDIUM = MenuMetrics(
    bar_height=30, item_pad_y=6, item_pad_x=12, item_min_height=28, font_delta=0
)
MENU_LARGE = MenuMetrics(
    bar_height=36, item_pad_y=8, item_pad_x=16, item_min_height=34, font_delta=1
)


def menu_metrics(menu_size: str) -> MenuMetrics:
    key = (menu_size or "").strip().lower()
    if key == "small":
        return MENU_SMALL
    if key == "large":
        return MENU_LARGE
    return MENU_MEDIUM


def clamp_font_size(value: object) -> int:
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return 13
    try:
        size = int(value)
    except (TypeError, ValueError, OverflowError):
        return 13
    return max(8, min(18, size))


def clamp_ui_scale_percent(value: object) -> int:
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return 100
    try:
        pct = int(value)
    except (TypeError, ValueError, OverflowError):
        return 100
    if pct in VALID_UI_SCALE_PERCENTS:
        return pct
    return min(VALID_UI_SCALE_PERCENTS, key=lambda allowed: abs(allowed - pct))


def normalize_menu_size(value: object) -> str:
    text = str(value or "").strip().lower()
    return text if text in VALID_MENU_SIZES else "medium"


def normalize_window_resolution(value: object) -> str:
    text = str(value or "").strip().lower().replace("×", "x")
    return text if text in VALID_WINDOW_RESOLUTIONS else "auto"


def window_size_for_resolution(value: object) -> tuple[int, int] | None:
    key = normalize_window_resolution(value)
    return WINDOW_RESOLUTION_SIZES.get(key)


def type_scale_for_body(body_px: int) -> TypeScale:
    body = clamp_font_size(body_px)
    return TypeScale(
        display=max(14, body + 13),
        title=max(11, body + 5),
        subtitle=max(10, body + 2),
        body=body,
        caption=max(8, body - 2),
        overline=max(7, body - 3),
        mono=body,
    )
