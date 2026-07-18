# KeePassXC-like visual depth — 2026-07-18

## Plan

- [x] Differentiate light `surface_elevated` from `surface_panel` (tokens + ui-spec)
- [x] QSS: pane roles, chrome strips, stronger splitters, dock framing, focus borders
- [x] ObjectNames on workspace regions (toolbar strip, search/filter, panes)
- [x] Verify offscreen smoke + theme tests; regenerate README shots

## Review

Depth via **surface steps + borders** (no drop shadows):

- App canvas → elevated chrome (menu/toolbar/search) → panel lists → elevated detail
- 3px splitter handles with hover accent; dock title elevated + strong border
- Flush pane layout; density only pads `#workspaceChrome`
- Light Studio / Catppuccin Latte: elevated ≠ panel

Verification: `tests/test_theme_palette.py` 15 passed; full suite + `smoke_visual.py` OK.
