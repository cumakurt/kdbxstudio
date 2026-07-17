# KDBXStudio UI Specification

Developer-facing design system for the Qt6 Linux desktop app.

Version target: **1.0.0**

---

## 1. Design principles

1. **Security-first calm** — Dense data without visual noise; secrets never flash.
2. **Keyboard-native** — Every primary action reachable without the mouse.
3. **One job per region** — Groups | Entries | Detail | Health stay distinct.
4. **Brand teal** — Deep teal + gold accent (from app icon), not purple gradients.
5. **8px grid** — Spacing, radii, and control heights snap to 8.

---

## 2. Brand & color

### Brand

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `brand.primary` | `#1A5C5E` | `#3D9A9C` | Primary actions, focus |
| `brand.primaryHover` | `#0F3D3E` | `#5CB3B5` | Hover |
| `brand.accent` | `#C9A227` | `#E8C547` | Highlights, health “good” |
| `brand.onPrimary` | `#FFFFFF` | `#0A1F20` | Text on primary |

### Surfaces

| Token | Light | Dark |
|-------|-------|------|
| `surface.app` | `#F4F7F7` | `#0E1616` |
| `surface.panel` | `#FFFFFF` | `#152020` |
| `surface.elevated` | `#FFFFFF` | `#1C2A2A` |
| `surface.sunken` | `#E8EEEE` | `#0A1212` |
| `border.subtle` | `#D0DADB` | `#2A3A3A` |
| `border.strong` | `#A8B8B8` | `#3D5050` |

### Text

| Token | Light | Dark |
|-------|-------|------|
| `text.primary` | `#142222` | `#E8F0F0` |
| `text.secondary` | `#4A5C5C` | `#9BB0B0` |
| `text.muted` | `#7A8C8C` | `#6A8080` |
| `text.danger` | `#B42318` | `#F97066` |
| `text.warning` | `#B54708` | `#FDB022` |
| `text.success` | `#027A48` | `#32D583` |

### Semantic (Password Health)

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

---

## 4. Spacing & geometry (8px grid)

- Base unit: **8px**
- Control height: **32px** (compact), **40px** (comfortable)
- Panel padding: **16px**
- Gap between panes: **8px**
- Corner radius: **8px** (controls), **12px** (dialogs)
- Focus ring: 2px `brand.primary`

---

## 5. Iconography

- Target: **Material Symbols Outlined**, 20px optical size
- Fallback: Qt standard theme icons + text labels (always pair icon with text in menus)
- Never rely on color alone for severity (also use labels)

---

## 6. Layout regions

```
┌─────────────────────────────────────────────────────────────┐
│ Menu · Toolbar · DB Tabs · [Search] · [⌘K]                  │
├──────────┬────────────────────┬─────────────────────────────┤
│ Groups   │ Entry list         │ Entry tabs                  │
│ (dock)   │ + filter bar       │ Entry|TOTP|History|…        │
├──────────┴────────────────────┴─────────────────────────────┤
│ Password Health (dock)                                      │
└─────────────────────────────────────────────────────────────┘
```

- Min window: 1024×640
- Groups dock default width: 240
- Entry list flex 2, detail flex 3
- Health dock default height: 180

---

## 7. Component library (Qt mapping)

| Component | Qt | Notes |
|-----------|-----|------|
| App shell | `QMainWindow` + docks | Already present |
| DB tabs | `QTabWidget` | Closable |
| Search field | `QLineEdit` | Universal search |
| Filter chips | `FilterBarWidget` | Checkbox row → evolve to chips |
| Entry table | `QTableWidget` | Row select |
| Command Palette | custom dialog | Ctrl+K / Ctrl+Shift+P |
| Health list | `QTreeWidget` | Severity column |
| Theme toggle | menu / palette | Persisted |

---

## 8. Key screens (wireframes)

### 8.1 Unlock / Create

- Centered card 420× max content on `surface.app`
- Fields: path, password, confirm (create), key file
- Primary CTA full width; secondary “Browse”

### 8.2 Main workspace

- As layout above
- Empty state: illustration + “Open or create a database” + recent list

### 8.3 Command Palette

- Modal 560px wide, top-center
- Fuzzy filter over actions + recent DBs + entry titles (when unlocked)
- Enter runs; Esc closes; ↑↓ navigate

### 8.4 Password Health

- Summary strip + findings list
- Double-click → focus entry

### 8.5 Plugin Center

- Tools → Plugin Center → Marketplace (local catalog) + Installed Plugins
- Built-in catalog is shipped; remote storefront remains out of scope

---

## 9. User flows

1. **First run** → Create DB → Add entry from template → Copy password  
2. **Daily unlock** → Recent → Unlock → Search / Ctrl+K → Copy  
3. **Audit** → Health dock refresh → Jump to weak/duplicate → Fix → Save  
4. **Lock** → Idle / Tools → Lock → Clipboard clear  

---

## 10. Micro-interactions

- Clipboard copy: status bar toast 3s; auto-clear per settings  
- Tab switch: no animation required (instant)  
- Command Palette: 120ms fade optional (QSS opacity)  
- TOTP bar: smooth countdown via 500ms timer  

---

## 11. Accessibility

- Contrast ≥ WCAG AA for text/icons  
- Tab order: search → filters → list → detail  
- Screen reader: set accessible names on icon-only buttons  
- Respect system font scaling where possible  

---

## 12. Theme rules

- Default: follow system if detectable, else **dark** for security tooling familiarity — *implementation default: dark* with explicit Light toggle  
- Persist `theme` in `settings.json`: `system` | `light` | `dark`  
- Charts/health colors stay semantic across themes  

---

## 13. Keyboard map (priority)

| Shortcut | Action |
|----------|--------|
| Ctrl+K / Ctrl+Shift+P | Command Palette |
| Ctrl+F | Focus search |
| Ctrl+O / Ctrl+N / Ctrl+S | Open / New / Save |
| Ctrl+L | Lock |
| Delete | Recycle selected entry |
| F2 | Rename group |

---

## 14. Implementation map

| Spec item | Code |
|-----------|------|
| Tokens | `ui/theme/tokens.py` |
| QSS | `ui/theme/styles.py` |
| Apply | `ui/theme/manager.py` |
| Palette | `ui/dialogs/command_palette.py` |
| Persist | `security/store.py` + `SecuritySettings` or app settings |

---

## 15. Out of scope (later)

- Remote Plugin Marketplace storefront / signed plugin feeds
- Motion design system beyond subtle fades (palette ~140ms fade is in)
- Cloud sync / HIBP breach checks
