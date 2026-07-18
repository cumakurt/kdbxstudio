# Premium Desktop UI Redesign — 2026-07-18

## Plan

- [x] Spec v2 + token/elevation/spacing/typography
- [x] Accent overlay + settings persist
- [x] Material-style icon kit + category map (QPainter outlined, no QtSvg)
- [x] Motion helpers + styles.py rewrite
- [x] Shell: menus, toolbar, sidebar, grid, chrome
- [x] Entry detail / empty / unlock / palette polish
- [x] All dialogs + settings accent UI
- [x] Dashboard card elevation + chart series cleanup
- [x] Tests + smoke + review
- [x] Colorful auto group icons (name heuristics: Internet/Windows/Linux/…)
- [x] Entry list colorful badges + URL favicon prefetch (original site icons)

## Review

Premium design system v2 shipped:

- **Tokens:** 8px spacing/radius scale, density-aware control heights, typography 13px body
- **Accent:** Studio Dark/Light accept teal/blue/purple/green/orange/red; community palettes unchanged
- **Icons:** Outlined QPainter kit (~64 glyphs) for chrome, menus, categories; Qt SP_* fallback only
- **Group icons:** Colorful badge icons auto-assigned from group names (Internet, Windows, Linux, SSH, Docker, Cloud, …)
- **Entry icons:** Same colorful badges by kind; cached site favicons preferred for URLs (prefetch on list load)
- **Motion:** `fade_in` / `slide_in` 120–180ms OutCubic; command palette uses `MotionDuration.NORMAL`
- **Shell:** Icon menus/toolbar/context; sidebar selection accent bar; chip filters; density DataGrid
- **Dialogs:** Shared `DialogShell`; Settings accent swatches; form dialogs primary CTA + spacing
- **Charts:** Brand-safe series palette (no purple-first)

Verification: group + entry icon heuristics tests green.
