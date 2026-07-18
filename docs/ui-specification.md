# KDBXStudio UI Specification

Developer-facing design system for the Qt6 Linux desktop app.

Version target: **2.0.0** (Premium Desktop)

---

## 1. Design principles

1. **Security-first calm** — Dense data without visual noise; secrets never flash.
2. **Keyboard-native** — Every primary action reachable without the mouse.
3. **One job per region** — Groups | Entries | Detail | Health stay distinct.
4. **Brand teal default** — Deep teal primary; user-selectable accent on Studio themes.
5. **8px grid** — Spacing, radii, and control heights snap to 8.
6. **Premium commercial quality** — No KeePassXC / Win32 form aesthetics; one design language everywhere.

---

## 2. Brand & color

### Brand (Studio Dark / Light defaults)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `brand.primary` | `#1A5C5E` | `#3D9A9C` | Primary actions, focus (overridden by accent) |
| `brand.primaryHover` | `#0F3D3E` | `#5CB3B5` | Hover |
| `brand.accent` | `#C9A227` | `#E8C547` | Gold highlight (semantic highlight) |
| `brand.onPrimary` | `#FFFFFF` | `#0A1F20` | Text on primary |

### User accent

Persisted as `settings.accent`. Overlays `brand.primary` / hover / focus on **every** theme (surfaces stay theme-specific).

| Id | Dark primary | Dark hover | Light primary | Light hover |
|----|--------------|------------|---------------|-------------|
| `teal` (default) | `#3D9A9C` | `#5CB3B5` | `#1A5C5E` | `#0F3D3E` |
| `blue` | `#5B8DEF` | `#7AA3F5` | `#2563EB` | `#1D4ED8` |
| `purple` | `#A78BFA` | `#C4B5FD` | `#7C3AED` | `#6D28D9` |
| `green` | `#34D399` | `#6EE7B7` | `#059669` | `#047857` |
| `orange` | `#FB923C` | `#FDBA74` | `#EA580C` | `#C2410C` |
| `red` | `#F87171` | `#FCA5A5` | `#DC2626` | `#B91C1C` |

### Surfaces

| Token | Light | Dark |
|-------|-------|------|
| `surface.app` | `#E8EEEE` | `#0B1212` |
| `surface.panel` | `#FFFFFF` | `#152020` |
| `surface.elevated` | `#F2F6F6` | `#1E2C2C` |
| `surface.sunken` | `#DCE4E4` | `#080E0E` |
| `border.subtle` | `#C2CECE` | `#2A3A3A` |
| `border.strong` | `#8FA3A3` | `#455858` |

### Depth model

- **Workspace panes:** flat border depth — app → elevated chrome → panel lists → elevated detail.
- **Cards / dialogs / menus / command palette:** soft elevation (`e1` / `e2`) plus subtle border.

### Elevation

| Level | Dark shadow | Light shadow | Usage |
|-------|-------------|--------------|--------|
| `e0` | none | none | Panels, trees, tables |
| `e1` | `0 1px 3px rgba(0,0,0,0.22)` | `0 1px 3px rgba(0,0,0,0.08)` | Cards, unlock card |
| `e2` | `0 8px 24px rgba(0,0,0,0.36)` | `0 8px 24px rgba(0,0,0,0.12)` | Dialogs, menus, palette |

### Text

| Token | Light | Dark |
|-------|-------|------|
| `text.primary` | `#142222` | `#E8F0F0` |
| `text.secondary` | `#4A5C5C` | `#9BB0B0` |
| `text.muted` | `#7A8C8C` | `#6A8080` |
| `text.danger` | `#B42318` | `#F97066` |
| `text.warning` | `#B54708` | `#FDB022` |
| `text.success` | `#027A48` | `#32D583` |

### Semantic severity

| Severity | Color |
|----------|-------|
| critical | `text.danger` |
| warning | `text.warning` |
| info | `brand.primary` |
| ok | `text.success` |

---

## 3. Typography

Prefer **Inter** when installed; fall back to `Noto Sans`, then `Sans Serif`.

| Role | Size | Weight | Line |
|------|------|--------|------|
| Display | 24px | 600 | 32 |
| Title | 18px | 600 | 24 |
| Body | 13px | 400 | 20 |
| Body strong | 13px | 600 | 20 |
| Caption | 11px | 500 | 16 |
| Mono (secrets) | 13px | 500 | 20 | `JetBrains Mono`, `Ui Mono`, `monospace` |

App default font size: **13px** (body).

---

## 4. Spacing & geometry (8px grid)

| Token | Value |
|-------|-------|
| `space.xs` | 4 |
| `space.sm` | 8 |
| `space.md` | 16 |
| `space.lg` | 24 |
| `space.xl` | 32 |
| `radius.sm` | 6 |
| `radius.md` | 8 |
| `radius.lg` | 12 |
| `radius.xl` | 16 |
| Control height | 32 compact / 40 comfortable |
| Panel padding | 16 |
| Pane gap | 8 |
| Focus ring | 2px `focus_ring` |

`ui_density` (`compact` | `comfortable`) drives control heights and row heights in QSS.

---

## 5. Iconography

- **Material Symbols Outlined**, 20px optical (toolbar/menus), 16px compact lists
- Tint from `text.primary` / `brand.primary`; never hard-coded black-only chrome
- Fallback: Qt `SP_*` only when a glyph is missing
- Always pair icon with text in menus; icon-only controls need accessible names
- Category icons: Server, Cloud, VPN, SSH, Certificate, Docker, Kubernetes, Linux, Windows, API, Database, WiFi, Identity, Crypto, Website, License, Attachment, OTP

---

## 6. Motion

Controlled motion system (120–180ms). No heavy Material ripple.

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `instant` | 0 | — | Tab content |
| `fast` | 120ms | OutCubic | Hover polish, tooltips |
| `normal` | 160ms | OutCubic | Fade-in, panel open, palette |
| `slow` | 180ms | OutCubic | Dialog show |

Helpers: `fade_in`, `slide_in`. Micro-interaction: hover fill + pressed feedback via QSS.

---

## 7. Layout regions

```
┌─────────────────────────────────────────────────────────────┐
│ Menu · Toolbar · DB Tabs · [Search] · [⌘K]                  │
├──────────┬────────────────────┬─────────────────────────────┤
│ Groups   │ Entry list         │ Entry tabs                  │
│ (dock)   │ + filter chips     │ Entry|TOTP|History|…        │
└──────────┴────────────────────┴─────────────────────────────┘

Security Dashboard → Tools menu → separate resizable window
```

- Min window: 1024×640
- Groups dock default width: 240
- Entry list flex 2, detail flex 3
- Security Dashboard dialog default size: 1280×800

---

## 8. Component contracts

| Primitive | Contract |
|-----------|----------|
| Button | `cssClass`: `primary` \| `secondary` \| `ghost` \| `danger` |
| Dialog shell | Icon title + optional subtitle + body + Secondary / Primary footer |
| Card | `radius.lg` + elevation `e1`; hover → `e2` |
| Chip / Badge | Filter chips; sidebar counters |
| Form field | Label + control + helper/error |
| Password / OTP | Mono + reveal; strength tone |
| Empty state | Title + supporting text + primary CTA |
| Menu / context | Icon + label + shortcut; rounded hover; elevation `e2` |
| DataGrid | Density row height, alternating rows, hover, sticky header, sort, column hide |
| Sidebar tree | Selection accent bar, hover, modern category icons |

---

## 9. Key screens

### 9.1 Unlock / Create

Centered card (~420px), elevation `e1`, icon title, primary CTA full width.

### 9.2 Main workspace

As layout above. Empty state: title + recent list + Open / Create.

### 9.3 Command Palette

Modal 560px, top-center, `normal` fade, icon rows + shortcuts, fuzzy filter.

### 9.4 Security Dashboard

Panel grid, KPI/gauge/charts, card elevation, soft hover.

### 9.5 Settings

Theme + **accent swatches** (Studio only) + density + security options.

---

## 10. Accessibility

- Contrast ≥ WCAG AA for text/icons
- Tab order: search → filters → list → detail
- Icon-only buttons: accessible names
- Severity: color + label

---

## 11. Theme rules

- Default: **Studio Dark** (`dark`)
- Persist `theme`: `system` | `dark` | `light` | community ids
- Persist `accent`: `teal` | `blue` | `purple` | `green` | `orange` | `red`
- Accent overlays brand colors on every theme (surfaces stay theme-specific)
- Charts use semantic `tone` colors

---

## 12. Keyboard map (priority)

| Shortcut | Action |
|----------|--------|
| Ctrl+K / Ctrl+Shift+P | Command Palette |
| Ctrl+F | Focus search |
| Ctrl+O / Ctrl+N / Ctrl+S | Open / New / Save |
| Ctrl+L | Lock |
| Delete | Recycle selected entry |
| F2 | Rename group |

---

## 13. Implementation map

| Spec item | Code |
|-----------|------|
| Color / theme tokens | `ui/theme/tokens.py` |
| Accent overlay | `ui/theme/accent.py` |
| Geometry | `ui/theme/geometry.py` |
| Motion | `ui/theme/motion.py` |
| QSS | `ui/theme/styles.py` |
| Apply | `ui/theme/manager.py` |
| Icons | `ui/icons/` |
| Persist | `security/settings.py` + store |

---

## 14. Out of scope (later)

- Remote Plugin Marketplace storefront / signed plugin feeds
- Health fix wizard
- Cloud sync
- YubiKey / hardware challenge-response
- Flathub publication (manifest scaffold only)
