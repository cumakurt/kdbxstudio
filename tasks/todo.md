# README screenshots — 2026-07-18

## Plan

- [x] Sample vault in `scripts/smoke_visual.py` (Work/Personal + weak/dupe/empty/SSH)
- [x] Capture welcome, workspace, search, palette, health, generator
- [x] Export to `assets/screenshots/` (English Studio Dark, isolated XDG config)
- [x] Embed images in README Screenshots section

## Review

- Script forces `XDG_CONFIG_HOME` temp settings (`language=en`, `theme=dark`)
- Workspace shot selects **Work** group (Root has no direct entries)
- Command palette: stop fade + opacity 1, then `grab(palette)` (window grab missed overlay)
- Regenerate: `QT_QPA_PLATFORM=offscreen python scripts/smoke_visual.py`
- Sample password: `demo-pass-123` (artifacts only, gitignored)
